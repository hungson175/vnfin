"""Index data sources — clean-room, composed over the existing price stack.

Two families:

(a) Index VALUE history. The VN broker TradingView-UDF chart feeds serve index
    OHLCV the same way they serve stocks, EXCEPT index values are quoted in
    *points* (e.g. VNINDEX close ~1290.67), not thousands of VND. The stock
    adapters apply ``PRICE_SCALE = 1000.0`` (thousands-of-VND -> VND), which would
    silently corrupt index values by 1000x. The index adapters here subclass the
    broker UDF adapters and override only what differs for indices:
      - ``PRICE_SCALE = 1.0`` (values are already in points),
      - ``CURRENCY = "points"`` (an index level is not a money amount),
      - ``ADJUSTMENT_POLICY = RAW`` (index levels are not split/dividend adjusted),
      - per-source symbol aliasing (canonical -> provider symbol),
      - a distinct ``NAME`` so failover diagnostics are unambiguous.
    Everything else (transport, UDF parsing, tz, structural validation, failover
    safety) is inherited unchanged from ``vnfin.sources.udf.UDFSource``. The price
    sources themselves are NOT modified — this is pure composition/subclassing.

(b) Index CONSTITUENTS (members). ``IndexConstituentsSource`` reads the public SSI
    iboard-query group endpoint, which returns the current member list per index
    group. It does NOT expose per-stock weights, so weights stay ``None`` (never
    fabricated). See ``docs/sources/indices-constituents.md`` for provenance.

Endpoints discovered against each provider's own server + the public TradingView
UDF protocol (see docs/research/2026-06-18-indices.md). VNStock and all
derivatives were excluded from research per the clean-room rule.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from ..exceptions import EmptyData, InvalidData
from ..models import AdjustmentPolicy
from ..sources.ssi import SSIiBoardSource
from ..sources.vndirect import VNDirectSource
from ..sources.vps import VPSSource
from ..transport import DEFAULT_UA, HttpDataSource
from .._contracts import canonical_security_symbol, reject_duplicate, require_present
from ..validation import validate_non_empty_string
from .models import IndexConstituents, IndexMember

# Canonical index symbol -> provider-specific symbol, per source. Only entries that
# differ from the canonical uppercase form need listing; anything else passes through.
_VPS_ALIASES = {"UPCOM": "UPCOMINDEX", "VNALLSHARE": "VNALL"}
_SSI_ALIASES = {"UPCOM": "UPCOMINDEX", "VNALLSHARE": "VNALL"}
_VNDIRECT_ALIASES = {"UPCOMINDEX": "UPCOM", "VNALLSHARE": "VNALL", "HNXINDEX": "HNXINDEX"}


class _IndexUDFMixin:
    """Shared overrides that turn a stock UDF adapter into an index-value adapter."""

    PRICE_SCALE = 1.0  # index values are in points already — never x1000
    ADJUSTMENT_POLICY = AdjustmentPolicy.RAW  # index levels are not adjusted
    VALUE_UNIT = "points"  # an index level is points, not a money amount
    CURRENCY = "points"  # kept "points" for backward compatibility (not money)
    unit = "points"  # failover unit guard: index sources are points, never VND
    ALIASES: dict = {}
    # Issue #162: a D1 index source result must expose exactly one bar per calendar
    # date. Unlike the equity default (#66: ANY duplicate timestamp -> raise), an index
    # source DEDUPES an IDENTICAL same-date duplicate (keep first; flag a warning) while
    # a CONFLICTING same-date bar still raises InvalidData inside the source path so the
    # failover client tries the next source. The actual dedupe/raise happens in the
    # shared UDF parse (it sets ``self._dedup_occurred``); the index-specific warning
    # token is attached in get_history below.
    _DEDUPE_IDENTICAL_DUPLICATE_BARS = True

    def normalize_symbol(self, symbol: str) -> str:
        canon = symbol.strip().upper()
        return self.ALIASES.get(canon, canon)

    def get_history(self, symbol, interval, start, end):
        # Scale guard (B2): indices are POINTS, not VND. The equity UDF adapters
        # apply PRICE_SCALE=1000.0 (thousands-of-VND -> VND); applying that to an
        # index would silently inflate levels 1000x into plausible-but-wrong values
        # — worse than an error. Refuse to serve an index from a non-point-scaled
        # source: raise a stable InvalidData (a VnfinError) so failover/diagnostics
        # surface the misconfiguration instead of corrupting data.
        if self.PRICE_SCALE != 1.0:
            raise InvalidData(
                f"{self.name}: index source must be POINT-scaled (PRICE_SCALE=1.0), "
                f"got {self.PRICE_SCALE} — indices are points, not VND"
            )
        hist = super().get_history(symbol, interval, start, end)
        # Issue #64: the public symbol must be the canonical symbol the caller asked
        # for, not the provider alias actually sent in the request. provider_symbol
        # already records the alias.
        canonical = symbol.strip().upper()
        if hist.symbol != canonical:
            hist = replace(hist, symbol=canonical)
        # An index level is in POINTS, not VND money. State the explicit unit on the
        # typed result: value_unit="points". ``currency`` historically also carries
        # "points" here (callers/tests rely on it), so keep both consistent. (frozen
        # dataclass -> replace; the equity base sets value_unit/currency="VND".)
        if hist.value_unit != self.VALUE_UNIT or hist.currency != self.CURRENCY:
            hist = replace(hist, value_unit=self.VALUE_UNIT, currency=self.CURRENCY)
        # Issue #162: if the shared UDF parse deduped an identical same-date duplicate
        # (see ``_DEDUPE_IDENTICAL_DUPLICATE_BARS``), surface it as an explicit warning
        # token so the one-bar-per-date reduction is never silent. (A conflicting
        # same-date bar already raised InvalidData inside the parse — the source path —
        # so it never reaches here.)
        if getattr(self, "_dedup_occurred", False):
            hist = replace(
                hist,
                warnings=tuple(hist.warnings) + ("deduped_duplicate_daily_index_bars",),
            )
        return hist


class VPSIndexSource(_IndexUDFMixin, VPSSource):
    """VPS histdatafeed index-value adapter — deepest history, widest symbol set."""

    NAME = "vps_index"
    ALIASES = _VPS_ALIASES


class SSIIndexSource(_IndexUDFMixin, SSIiBoardSource):
    """SSI iBoard index-value adapter (enveloped UDF). UPCOM via SSI is unreliable."""

    NAME = "ssi_index"
    ALIASES = _SSI_ALIASES


class VNDirectIndexSource(_IndexUDFMixin, VNDirectSource):
    """VNDIRECT dchart index-value adapter — shallower history, good cross-check."""

    NAME = "vndirect_index"
    ALIASES = _VNDIRECT_ALIASES


# --------------------------------------------------------------------------- #
# (b) Constituents
# --------------------------------------------------------------------------- #

# Canonical index name -> SSI iboard-query group token. Most are identical; the
# full-exchange membership groups are case-sensitive (HNXIndex, not HNXINDEX).
_GROUP_ALIASES = {
    "HNXINDEX": "HNXIndex",
}


class IndexConstituentsSource(HttpDataSource):
    """Current index membership from the public SSI iBoard query group endpoint.

        GET https://iboard-query.ssi.com.vn/stock/group/{GROUP}

    Returns ``{"code":"SUCCESS","data":[{stockSymbol,exchange,...}, ...]}``. One
    object per member. Per-stock index *weights* are not exposed here and are left
    ``None`` (never fabricated). Injectable ``http_get`` mirrors the price sources.
    """

    NAME = "ssi_iboard_query"
    BASE_URL = "https://iboard-query.ssi.com.vn"
    GROUP_PATH = "/stock/group"

    @property
    def name(self) -> str:
        return self.NAME

    def normalize_group(self, group: str) -> str:
        canon = group.strip().upper()
        return _GROUP_ALIASES.get(canon, canon)

    def get_constituents(self, index: str) -> IndexConstituents:
        # Issue #75: the index selector is a canonical security/index identifier —
        # reject non-string/bytes/blank/whitespace/punctuation/internal-space before
        # any URL construction; normalize padded/lowercase (e.g. " vn30 " -> "VN30").
        index = canonical_security_symbol(index, "index")
        group = self.normalize_group(index)
        url = f"{self.BASE_URL}{self.GROUP_PATH}/{group}"
        headers = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}

        parsed = self._request_json(url, params=None, headers=headers)

        if not isinstance(parsed, dict):
            raise InvalidData(f"{self.name}: unexpected response shape")

        # Issue #54: require the provider success envelope. Missing, null, or
        # non-success codes are treated as malformed data (InvalidData), never as
        # an implicit success.
        code = parsed.get("code")
        if code != "SUCCESS":
            raise InvalidData(f"{self.name}: code={code}")

        data = parsed.get("data")
        if not isinstance(data, list):
            raise InvalidData(f"{self.name}: 'data' is not a list")
        if not data:
            raise EmptyData(f"{self.name}: no members for group {group}")

        members: list[IndexMember] = []
        seen: set[str] = set()
        for i, row in enumerate(data):
            if not isinstance(row, dict):
                raise InvalidData(f"{self.name}: member {i} is not an object")
            # Issue #30: stockSymbol is a public security identifier — a malformed
            # non-blank shape (internal space/slash/punctuation/newline/digit-first)
            # must fail closed, not just be stripped/uppercased. Canonicalize then
            # dedup on the canonical form ("fake1" and "FAKE1" collide).
            sym = canonical_security_symbol(
                require_present(row, "stockSymbol", f"{self.name} member {i} stockSymbol"),
                f"{self.name} member {i} stockSymbol",
            )
            reject_duplicate(sym, seen, f"{self.name} member {i} symbol")
            exchange = self._optional_member_str(row, "exchange", i, "exchange")
            company_name = self._member_company_name(row, i)
            isin = self._optional_member_str(row, "isin", i, "isin")
            members.append(
                IndexMember(
                    symbol=sym,
                    exchange=exchange.upper() if exchange else None,
                    company_name=company_name,
                    isin=isin,
                    weight=None,  # not exposed by this endpoint — never fabricated
                )
            )

        return IndexConstituents(
            index=index,  # already canonical from canonical_security_symbol above
            source=self.name,
            members=tuple(members),
            provider_group=group,
            fetched_at_utc=datetime.now(timezone.utc),
            as_of=None,
            warnings=("weights_not_available: SSI group endpoint exposes membership only",),
        )

    @staticmethod
    def _optional_member_str(row: dict, key: str, member_i: int, field_name: str) -> str | None:
        if key not in row:
            return None
        raw = row.get(key)
        if raw is None or raw == "":
            return None
        if not isinstance(raw, str):
            raise InvalidData(
                f"{IndexConstituentsSource.NAME}: member {member_i} malformed {field_name}"
            )
        stripped = raw.strip()
        return stripped or None

    @classmethod
    def _member_company_name(cls, row: dict, member_i: int) -> str | None:
        for key in ("companyNameEn", "companyNameVi"):
            if key not in row:
                continue
            raw = row.get(key)
            if raw is None or raw == "":
                continue
            if not isinstance(raw, str):
                raise InvalidData(
                    f"{cls.NAME}: member {member_i} malformed {key}"
                )
            stripped = raw.strip()
            if stripped:
                return stripped
        return None
