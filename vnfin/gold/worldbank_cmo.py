"""World Bank CMO "Pink Sheet" annual gold source (issue #185).

Serves **annual** world-gold (XAU/USD, USD per troy ounce) history from the World Bank
Commodity Markets "Pink Sheet" historical-data ``.xlsx`` distribution. This is the
annual-history source that the #178 ``world_reference_history_vnd`` synthesis uses for
its world-gold leg: CMO annual gold IS "spot average of daily rates" (LBMA-sourced) —
already an annual average of daily spot — so it preserves the synthesis's
``annual-avg × annual-avg`` basis exactly while working from a datacenter host (unlike
the daily CurrencyApi/Stooq legs, which are sparse/anti-bot-blocked server-side).

Design: ``docs/design/issue-185-annual-world-gold-source.md`` (D1–D6, gate notes N1/N2).
Provenance/contract/attribution: ``docs/sources/cmo-gold-annual.md``.

Standalone **history** source (inherits :class:`~vnfin.transport.HttpDataSource`, NOT
``GoldSource``) — mirroring :class:`~vnfin.fx.history_worldbank.WorldBankFXHistorySource`.
CMO is annual-history-only; it is fetched DIRECTLY (it must NOT be a peer inside the
daily ``FailoverGoldClient``, whose 50% weekday-coverage gate would wrongly reject an
annual series).

xlsx parsing uses **stdlib only** (``zipfile`` + ``xml.etree.ElementTree``) — no
openpyxl/pandas — so the core synthesis works out-of-the-box server-side. The parser is
scoped to exactly CMO's shape; anything unexpected fails safe as ``InvalidData``.

Error discipline (gate note N2): every recoverable failure raises a
:class:`~vnfin.exceptions.SourceError` SUBCLASS (``SourceUnavailable`` /
``InvalidData`` / ``EmptyData``) so the synthesis ``except SourceError`` fallback
engages; a genuine programmer bug propagates (fails loud).

License: World Bank Commodity Markets data is **CC-BY 4.0** — attribution
"Source: The World Bank — Commodity Markets (Pink Sheet)". Runtime-fetch only; no
bundled provider rows (the committed test fixture is a test asset, not a shipped dataset).

Clean-room: endpoint, sheet name, split-header layout and units were learned only from
the World Bank's own server. Zero vnstock.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from .._contracts.worldbank_cmo import (
    _CMO_ANNUAL_URLS,
    _USD_PER_OZ,
    MetalSpec,
    parse_cmo_annual,
)
from ..exceptions import EmptyData, InvalidData, SourceError, SourceUnavailable
from ..transport import HttpDataSource
from ..validation import validate_date_range
from .models import GoldBar, GoldHistory

# ``_CMO_ANNUAL_URLS`` is re-exported from the shared parser so existing imports of
# ``vnfin.gold.worldbank_cmo._CMO_ANNUAL_URLS`` (tests/test_no_secrets.py:79,
# tests/test_worldbank_cmo_gold.py:29) keep resolving to the same literal value. The
# no-secrets allowlist is BY VALUE, so the URL living in ``_contracts`` is still covered.
__all__ = ["WorldBankCmoGoldSource", "_CMO_ANNUAL_URLS", "_parse_cmo_annual_gold"]

#: GATE NOTE N1 — plausible gold band (USD/oz). A parsed value outside this is a gross
#: misparse (wrong column / mis-resolved shared-string index), never a legitimate value
#: (1960 ≈ 35, 2025 ≈ 3441). The split-header text match is the primary defense; this
#: magnitude guard is the backstop so a misparse can never feed the synthesis.
_GOLD_MIN_USD_OZ = 20.0
_GOLD_MAX_USD_OZ = 10000.0

#: The gold per-metal spec fed to the shared :func:`parse_cmo_annual`. Band unchanged.
_GOLD_SPEC = MetalSpec(
    product="XAU",
    name_row="Gold",
    min_usd_oz=_GOLD_MIN_USD_OZ,
    max_usd_oz=_GOLD_MAX_USD_OZ,
)


def _parse_cmo_annual_gold(raw: bytes) -> dict:
    """Parse the CMO annual-prices xlsx bytes into ``{year: usd_per_oz}`` (gold).

    Thin delegator to the shared, domain-neutral :func:`parse_cmo_annual` with the GOLD
    :data:`_GOLD_SPEC` — gold's observable output is byte-for-byte identical to the
    pre-extraction parser. Kept as a module-level function so ``_fetch_annual`` calls it
    locally (the existing test monkeypatch of
    ``vnfin.gold.worldbank_cmo._parse_cmo_annual_gold`` still applies).
    """
    return parse_cmo_annual(raw, _GOLD_SPEC)


class WorldBankCmoGoldSource(HttpDataSource):
    """Annual world-gold (XAU/USD) history from the World Bank CMO Pink Sheet xlsx.

    ``http_get(url, params, headers) -> response bytes`` is injectable so unit tests
    never touch the network (an injected stub returns the xlsx bytes directly).
    """

    NAME = "worldbank_cmo_gold"

    def __init__(self, http_get=None, timeout: float = 25.0):
        super().__init__(http_get=http_get, timeout=timeout)

    @property
    def name(self) -> str:
        return self.NAME

    def get_history(self, start: date, end: date) -> GoldHistory:
        """Fetch the CMO annual gold series and emit one Jan-1 ``GoldBar`` per year in
        the inclusive ``[start.year, end.year]`` span.

        Validates bounds fail-closed BEFORE any network call. Iterates
        :data:`_CMO_ANNUAL_URLS` in order: a per-URL transport/non-xlsx/parse failure
        falls through to the next; all-fail → :class:`~vnfin.exceptions.SourceUnavailable`.
        Returns ``GoldHistory(product="XAU", unit="USD/oz", ...)``. No years in span →
        :class:`~vnfin.exceptions.EmptyData`. Every recoverable failure is a
        :class:`~vnfin.exceptions.SourceError` subclass (N2).
        """
        lo, hi = validate_date_range(start, end, name="worldbank_cmo_gold.history")

        annual = self._fetch_annual()  # {year: usd_per_oz}

        lo_year, hi_year = lo.year, hi.year
        bars = [
            GoldBar(date=date(year, 1, 1), price=price)
            for year, price in sorted(annual.items())
            if lo_year <= year <= hi_year
        ]
        if not bars:
            raise EmptyData(
                f"{self.NAME}: no annual gold observations in {lo_year}..{hi_year}"
            )
        return GoldHistory(
            product="XAU",
            unit=_USD_PER_OZ,
            value_unit=_USD_PER_OZ,
            currency="USD",
            source=self.NAME,
            bars=tuple(bars),
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _fetch_annual(self) -> dict:
        """Try each vintage URL in order; return ``{year: usd_per_oz}`` from the first
        that fetches + parses. A per-URL ``SourceError`` (transport/non-xlsx/parse/
        out-of-band) is recorded and the next URL is tried; all-fail →
        ``SourceUnavailable`` carrying the per-URL reasons. A non-``SourceError``
        propagates (N2: a programmer bug fails loud)."""
        reasons = []
        for url in _CMO_ANNUAL_URLS:
            try:
                raw = self._request_bytes(url)
                return _parse_cmo_annual_gold(raw)
            except SourceError as exc:
                reasons.append(f"{url}: {type(exc).__name__}: {exc}")
                continue
        joined = "; ".join(reasons) or "no CMO URLs configured"
        raise SourceUnavailable(f"{self.NAME}: all CMO annual URLs failed -> {joined}")
