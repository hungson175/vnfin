"""Offline unit tests for the upstream health-monitoring core (``vnfin/_health.py``).

The harness probes upstream providers and reports a typed :class:`SourceHealth` per probe.
It is **monitoring**, not a CI gate: probes never raise; failures become a status. These tests
inject fake fetchers + synthetic data (no network) and verify status classification,
schema-drift detection, value-sanity, secret redaction, and the STATUS.md / JSON renderers.
"""
from __future__ import annotations

import datetime as dt
import json

from vnfin._health import (
    HealthStatus,
    Probe,
    SchemaSpec,
    SourceHealth,
    check_schema,
    default_probes,
    fx_probes,
    render_status_md,
    run_all,
    run_probe,
    to_status_json,
)

_NOW = dt.datetime(2026, 6, 18, 3, 0, 0, tzinfo=dt.timezone.utc)


def _probe(fetch, *, schema=None, value_check=None, value_desc="value in band"):
    return Probe(
        domain="prices",
        source="ssi",
        probe_id="prices/ssi/FPT",
        fetch=fetch,
        schema=schema,
        value_check=value_check,
        value_desc=value_desc,
    )


# --------------------------------------------------------------------------- #
# check_schema (required paths + types)
# --------------------------------------------------------------------------- #
def test_check_schema_all_present_ok():
    spec = SchemaSpec(required=(("rates.VND", (int, float)), ("base_code", str)))
    ok, problems = check_schema({"rates": {"VND": 26000.0}, "base_code": "USD"}, spec)
    assert ok and problems == []


def test_check_schema_missing_key_reports():
    spec = SchemaSpec(required=(("rates.VND", (int, float)),))
    ok, problems = check_schema({"rates": {"USD": 1}}, spec)
    assert not ok and any("rates.VND" in p for p in problems)


def test_check_schema_wrong_type_reports():
    spec = SchemaSpec(required=(("rates.VND", (int, float)),))
    ok, problems = check_schema({"rates": {"VND": "twenty-six-k"}}, spec)
    assert not ok and any("rates.VND" in p for p in problems)


def test_check_schema_list_index_path():
    spec = SchemaSpec(required=(("data.0.close", (int, float)),))
    ok, problems = check_schema({"data": [{"close": 72.3}]}, spec)
    assert ok and problems == []


def test_check_schema_list_index_out_of_range_reports():
    spec = SchemaSpec(required=(("data.0.close", (int, float)),))
    ok, problems = check_schema({"data": []}, spec)
    assert not ok


# --------------------------------------------------------------------------- #
# run_probe status classification
# --------------------------------------------------------------------------- #
def test_run_probe_ok():
    spec = SchemaSpec(required=(("rates.VND", (int, float)),))
    h = run_probe(
        _probe(lambda: {"rates": {"VND": 26000.0}}, schema=spec,
               value_check=lambda d: 1000 < d["rates"]["VND"] < 1_000_000),
        now=_NOW,
    )
    assert h.status is HealthStatus.OK
    assert h.reachable is True and h.schema_ok is True and h.value_sane is True
    assert h.latency_ms is not None and h.latency_ms >= 0
    assert h.checked_at_utc == _NOW
    assert h.error_type is None


def test_run_probe_schema_drift_is_degraded():
    spec = SchemaSpec(required=(("rates.VND", (int, float)),))
    h = run_probe(_probe(lambda: {"rates": {"USD": 1}}, schema=spec), now=_NOW)
    assert h.status is HealthStatus.DEGRADED
    assert h.reachable is True and h.schema_ok is False


def test_run_probe_value_out_of_band_is_degraded():
    h = run_probe(
        _probe(lambda: {"rates": {"VND": 3.0}},
               value_check=lambda d: 1000 < d["rates"]["VND"] < 1_000_000),
        now=_NOW,
    )
    assert h.status is HealthStatus.DEGRADED
    assert h.value_sane is False


def test_run_probe_exception_is_down():
    def boom():
        raise RuntimeError("connection reset")

    h = run_probe(_probe(boom), now=_NOW)
    assert h.status is HealthStatus.DOWN
    assert h.reachable is False
    assert h.error_type == "RuntimeError"
    assert "connection reset" in h.note
    assert h.schema_ok is None and h.value_sane is None


def test_run_probe_403_is_host_blocked():
    class Blocked(Exception):
        status_code = 403

    def blocked():
        raise Blocked("forbidden from this datacenter IP")

    h = run_probe(_probe(blocked), now=_NOW)
    assert h.status is HealthStatus.HOST_BLOCKED
    assert h.reachable is False


def test_run_probe_redacts_secret_in_note():
    def leaky():
        raise RuntimeError("GET https://api/x?api_key=SUPERSECRET123 failed")

    h = run_probe(_probe(leaky), now=_NOW)
    assert "SUPERSECRET123" not in h.note
    assert "REDACTED" in h.note


# --------------------------------------------------------------------------- #
# run_all + renderers
# --------------------------------------------------------------------------- #
def test_run_all_one_health_per_probe_stable_order():
    probes = [
        _probe(lambda: {"rates": {"VND": 26000.0}}),
        Probe(domain="crypto", source="binance", probe_id="crypto/binance/BTC",
              fetch=lambda: {"price": 60000}, schema=None, value_check=None, value_desc=""),
    ]
    healths = run_all(probes, now=_NOW)
    assert [h.probe_id for h in healths] == ["prices/ssi/FPT", "crypto/binance/BTC"]


def test_render_status_md_has_rows_and_no_secret():
    h = run_probe(
        _probe(lambda: (_ for _ in ()).throw(RuntimeError("token=ABCSECRET in url"))),
        now=_NOW,
    )
    md = render_status_md([h], generated_at=_NOW)
    assert "prices/ssi/FPT" in md
    assert "ABCSECRET" not in md
    assert "down" in md.lower()


def test_to_status_json_is_serialisable_and_sanitised():
    h = run_probe(
        _probe(lambda: (_ for _ in ()).throw(RuntimeError("api_key=LEAK999 boom"))),
        now=_NOW,
    )
    payload = to_status_json([h], generated_at=_NOW)
    data = json.loads(payload)  # must be valid JSON
    assert "LEAK999" not in payload
    assert data["probes"][0]["probe_id"] == "prices/ssi/FPT"
    assert data["probes"][0]["checked_at_utc"] == _NOW.isoformat()


# --------------------------------------------------------------------------- #
# default probe set (construction only — no network in CI)
# --------------------------------------------------------------------------- #
def test_default_probes_constructed_without_network():
    probes = default_probes()
    # exact critical set: one source per key domain
    assert {p.domain for p in probes} == {
        "prices",
        "fundamentals",
        "gold",
        "crypto",
        "macro",
    }
    assert {p.probe_id for p in probes} == {
        "prices/ssi/FPT",
        "fundamentals/vndirect/FPT",
        "gold/btmc/spot",
        "crypto/binance/BTCUSDT",
        "macro/worldbank/VNM-CPI",
    }
    # each probe is well-formed
    for p in probes:
        assert p.domain and p.source and p.probe_id and callable(p.fetch)


def test_fx_probe_is_opt_in_not_in_default():
    # FX providers are rate-limited -> FX must NOT be in the routine scheduled set
    assert all(p.domain != "fx" for p in default_probes())
    fxp = fx_probes()
    assert len(fxp) == 1 and fxp[0].domain == "fx"
    assert fxp[0].probe_id == "fx/open_er_api/USD-VND"
