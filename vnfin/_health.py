"""Upstream source-health monitoring core (private, opt-in).

This is **monitoring**, not a CI gate. It probes the third-party providers ``vnfin`` depends
on and reports a typed :class:`SourceHealth` per probe describing reachability, schema
conformance, value sanity, and latency. Probes **never raise** — any failure becomes a status
(``down`` / ``host_blocked`` / ``degraded``) so a scheduled run can summarise health without
crashing.

It is intentionally **private** (``vnfin._health``, not part of the stable public surface — see
``docs/stability.md``). The thin CLI ``scripts/healthcheck.py`` wraps it; the live network run is
opt-in (like ``live_tests/``) and must never run in CI. ``STATUS.md`` is generated from a
sanitised, timestamped JSON snapshot and is **not** auto-pushed.

Two probe styles:

* **adapter probes** — ``fetch`` returns a typed result from a public adapter; ``value_check``
  asserts it is non-empty / in-band. Parse-breaking upstream drift surfaces as an exception
  (``down``); silent unit drift surfaces as ``value_sane=False`` (``degraded``).
* **raw probes** — ``fetch`` returns parsed JSON; a :class:`SchemaSpec` of required paths/types
  detects schema drift before it breaks parsing.
"""
from __future__ import annotations

import datetime as dt
import enum
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .transport import redact_secrets


class HealthStatus(enum.Enum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"
    HOST_BLOCKED = "host_blocked"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class SourceHealth:
    domain: str
    source: str
    probe_id: str
    status: HealthStatus
    reachable: bool | None
    schema_ok: bool | None
    value_sane: bool | None
    latency_ms: float | None
    checked_at_utc: dt.datetime
    error_type: str | None
    note: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SchemaSpec:
    """Required ``(path, type-or-types)`` pairs a raw-JSON response must satisfy.

    ``path`` uses dotted tokens; a numeric token indexes a list, e.g. ``"data.0.close"``.
    """

    required: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True)
class Probe:
    domain: str
    source: str
    probe_id: str
    fetch: Callable[[], Any]
    schema: SchemaSpec | None = None
    value_check: Callable[[Any], bool] | None = None
    value_desc: str = ""


# --------------------------------------------------------------------------- #
# schema checking
# --------------------------------------------------------------------------- #
def _get_path(data: Any, path: str) -> Any:
    cur = data
    for token in path.split("."):
        if isinstance(cur, (list, tuple)) and token.lstrip("-").isdigit():
            cur = cur[int(token)]
        elif isinstance(cur, dict):
            cur = cur[token]
        else:
            raise TypeError(f"cannot descend into {type(cur).__name__} at {token!r}")
    return cur


def check_schema(data: Any, spec: SchemaSpec) -> tuple[bool, list[str]]:
    """Return ``(ok, problems)``: ``ok`` is True iff every required path exists with the
    expected type. ``problems`` lists human-readable drift descriptions (never secrets)."""
    problems: list[str] = []
    for path, types in spec.required:
        try:
            val = _get_path(data, path)
        except (KeyError, IndexError, TypeError):
            problems.append(f"missing path: {path}")
            continue
        if types is not None and not isinstance(val, types):
            problems.append(f"wrong type at {path}: got {type(val).__name__}")
    return (not problems, problems)


# --------------------------------------------------------------------------- #
# probe execution
# --------------------------------------------------------------------------- #
def _is_host_blocked(exc: BaseException) -> bool:
    for attr in ("status_code", "status", "code"):
        v = getattr(exc, attr, None)
        if isinstance(v, int) and v in (403, 451):
            return True
    v = getattr(getattr(exc, "response", None), "status_code", None)
    if isinstance(v, int) and v in (403, 451):
        return True
    msg = str(exc).lower()
    return any(s in msg for s in ("403", "451", "forbidden", "blocked"))


def _now(now: dt.datetime | None) -> dt.datetime:
    return now if now is not None else dt.datetime.now(dt.timezone.utc)


def run_probe(probe: Probe, *, now: dt.datetime | None = None) -> SourceHealth:
    """Run one probe and classify it. Never raises."""
    when = _now(now)
    metadata: dict[str, Any] = {}
    t0 = time.perf_counter()
    try:
        data = probe.fetch()
    except Exception as exc:  # monitoring: classify, never propagate
        latency = round((time.perf_counter() - t0) * 1000.0, 1)
        blocked = _is_host_blocked(exc)
        return SourceHealth(
            domain=probe.domain,
            source=probe.source,
            probe_id=probe.probe_id,
            status=HealthStatus.HOST_BLOCKED if blocked else HealthStatus.DOWN,
            reachable=False,
            schema_ok=None,
            value_sane=None,
            latency_ms=latency,
            checked_at_utc=when,
            error_type=type(exc).__name__,
            note=redact_secrets(str(exc)) or "",
            metadata=metadata,
        )
    latency = round((time.perf_counter() - t0) * 1000.0, 1)

    schema_ok: bool | None = None
    if probe.schema is not None:
        try:
            schema_ok, problems = check_schema(data, probe.schema)
        except Exception as exc:  # a malformed spec must degrade, never raise
            schema_ok = False
            problems = [f"schema check error: {type(exc).__name__}"]
        if problems:
            metadata["schema_problems"] = redact_secrets("; ".join(problems))

    value_sane: bool | None = None
    if probe.value_check is not None:
        try:
            value_sane = bool(probe.value_check(data))
        except Exception as exc:
            value_sane = False
            metadata["value_error"] = type(exc).__name__

    notes: list[str] = []
    status = HealthStatus.OK
    if schema_ok is False:
        status = HealthStatus.DEGRADED
        notes.append("schema drift")
    if value_sane is False:
        status = HealthStatus.DEGRADED
        notes.append("value out of band")
    note = "; ".join(notes) if notes else (probe.value_desc or "ok")

    # Report the ACTUAL serving source when the typed result exposes one (the
    # probe may run a failover client, so the bar/quote can come from a backup —
    # don't mislabel it as the primary). Falls back to the probe's declared source.
    actual_source = probe.source
    result_source = getattr(data, "source", None)
    if isinstance(result_source, str) and result_source:
        actual_source = result_source

    return SourceHealth(
        domain=probe.domain,
        source=actual_source,
        probe_id=probe.probe_id,
        status=status,
        reachable=True,
        schema_ok=schema_ok,
        value_sane=value_sane,
        latency_ms=latency,
        checked_at_utc=when,
        error_type=None,
        note=redact_secrets(note),
        metadata=metadata,
    )


def run_all(probes: list[Probe], *, now: dt.datetime | None = None) -> list[SourceHealth]:
    when = _now(now)
    return [run_probe(p, now=when) for p in probes]


# --------------------------------------------------------------------------- #
# renderers (sanitised)
# --------------------------------------------------------------------------- #
def _b(x: bool | None) -> str:
    return "—" if x is None else ("yes" if x else "no")


def render_status_md(healths: list[SourceHealth], *, generated_at: dt.datetime | None = None) -> str:
    ts = _now(generated_at).isoformat()
    lines = [
        "# vnfin upstream source health",
        "",
        f"_Generated {ts} · monitoring only, not a CI gate (see `docs/stability.md`)._",
        "",
        "| Domain | Source | Probe | Status | Reachable | Schema | Value | Latency (ms) | Note |",
        "|--------|--------|-------|--------|-----------|--------|-------|--------------|------|",
    ]
    for h in healths:
        lat = "" if h.latency_ms is None else h.latency_ms
        lines.append(
            f"| {h.domain} | {h.source} | {h.probe_id} | {h.status.value} "
            f"| {_b(h.reachable)} | {_b(h.schema_ok)} | {_b(h.value_sane)} | {lat} "
            f"| {redact_secrets(h.note)} |"
        )
    return "\n".join(lines) + "\n"


def to_status_json(healths: list[SourceHealth], *, generated_at: dt.datetime | None = None) -> str:
    import json

    payload = {
        "generated_at": _now(generated_at).isoformat(),
        "probes": [
            {
                "domain": h.domain,
                "source": h.source,
                "probe_id": h.probe_id,
                "status": h.status.value,
                "reachable": h.reachable,
                "schema_ok": h.schema_ok,
                "value_sane": h.value_sane,
                "latency_ms": h.latency_ms,
                "checked_at_utc": h.checked_at_utc.isoformat(),
                "error_type": h.error_type,
                "note": redact_secrets(h.note),
                "metadata": {k: redact_secrets(str(v)) for k, v in h.metadata.items()},
            }
            for h in healths
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# the critical default probe set (adapter-level; lazy, no network at import)
# --------------------------------------------------------------------------- #
def _nonempty(obj: Any) -> bool:
    try:
        return len(obj) > 0
    except TypeError:
        return obj is not None


def default_probes(*, http_get: Any = None, timeout: float = 25.0) -> list[Probe]:
    """A small, multi-domain critical probe set covering one source per key domain.

    Adapter-level: each ``fetch`` calls a public facade so the probe exercises the exact
    code path users rely on. Constructing the probes touches no network; only
    :func:`run_probe`/:func:`run_all` does.
    """
    import vnfin

    def _recent(days: int) -> tuple[dt.date, dt.date]:
        end = dt.date.today()
        return end - dt.timedelta(days=days), end

    # Each probe targets the PRIMARY single source (source()/vn()), not the failover
    # client, so a probe diagnoses whether THAT specific source is healthy (and its
    # label is honest — a failover client could be served by a backup and mislabel it).
    # Cross-source failover behaviour is validated by the live cross-source tests.
    def _fetch_prices() -> Any:
        start, end = _recent(30)
        return vnfin.prices.source(http_get=http_get, timeout=timeout).get_history(
            "FPT", interval=vnfin.Interval.D1, start=start, end=end
        )

    def _fetch_crypto() -> Any:
        start, end = _recent(10)
        return vnfin.crypto.source(http_get=http_get, timeout=timeout).get_klines(
            "BTCUSDT", vnfin.Interval.D1, start, end
        )

    def _fetch_macro() -> Any:
        return vnfin.macro.source(http_get=http_get, timeout=timeout).get_indicator(
            "VNM", vnfin.macro.MacroIndicator.CPI
        )

    def _fetch_fundamentals() -> Any:
        # NB: the SOURCE.get_financials requires ENUMS (only the module-level
        # get_financials coerces strings) — passing strings raises AttributeError.
        return vnfin.fundamentals.source(http_get=http_get, timeout=timeout).get_financials(
            "FPT", vnfin.fundamentals.StatementType.INCOME, vnfin.fundamentals.Period.ANNUAL
        )

    def _fetch_gold() -> Any:
        return vnfin.gold.vn("btmc", http_get=http_get, timeout=timeout).get_quotes()

    return [
        Probe(
            domain="prices", source="ssi", probe_id="prices/ssi/FPT", fetch=_fetch_prices,
            value_check=lambda h: len(h.bars) > 0 and 1_000 < h.bars[-1].close < 10_000_000,
            value_desc="FPT daily close in VND band",
        ),
        Probe(
            domain="fundamentals", source="vndirect", probe_id="fundamentals/vndirect/FPT",
            fetch=_fetch_fundamentals, value_check=_nonempty,
            value_desc="FPT income statement non-empty",
        ),
        Probe(
            domain="gold", source="btmc", probe_id="gold/btmc/spot", fetch=_fetch_gold,
            value_check=lambda q: len(q) > 0, value_desc="BTMC spot quotes non-empty",
        ),
        Probe(
            domain="crypto", source="binance", probe_id="crypto/binance/BTCUSDT",
            fetch=_fetch_crypto,
            value_check=lambda h: len(h.bars) > 0 and 1_000 < h.bars[-1].close < 10_000_000,
            value_desc="BTCUSDT daily close in USD band",
        ),
        Probe(
            domain="macro", source="worldbank", probe_id="macro/worldbank/VNM-CPI",
            fetch=_fetch_macro, value_check=_nonempty,
            value_desc="Vietnam CPI series non-empty",
        ),
    ]


def fx_probes(*, http_get: Any = None, timeout: float = 25.0) -> list[Probe]:
    """OPT-IN FX probe set, kept OUT of :func:`default_probes`.

    The FX providers rate-limit aggressively (open.er-api 429s if hit more than once/day;
    Vietcombank asks for ≤1 request / 5 min), so FX must not be part of a routine scheduled
    sweep. Use this only from a cached / infrequent monitor path (e.g. the healthcheck CLI's
    ``--fx`` flag).
    """
    import vnfin

    def _fetch_fx() -> Any:
        return vnfin.fx.source(http_get=http_get, timeout=timeout).get_rate("USD")

    return [
        Probe(
            domain="fx", source="open_er_api", probe_id="fx/open_er_api/USD-VND",
            fetch=_fetch_fx,
            value_check=lambda r: 15_000 < r.rate < 40_000,  # plausible USD/VND band
            value_desc="USD/VND in plausible band",
        ),
    ]
