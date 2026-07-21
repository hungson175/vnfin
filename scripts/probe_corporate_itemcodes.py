#!/usr/bin/env python3
"""Manually-invoked LIVE probe for #198 (corporate statement routing/mislabel +
pagination). Two independent legs, each stating exactly what it proves:

  LEG A — RAW template-identity (bypasses the adapter): queries VNDirect
  ``modelType`` 1/2/3 directly and checks provider-only accounting identities to
  EXACT VND (integer residual == 0). This proves *which template is which* and
  *which itemCodes participate in which identity* WITHOUT depending on the
  library's (currently inverted) routing. This is the load-bearing evidence.

  LEG B — ADAPTER regression: calls the public ``VNDirectFundamentalSource``
  routing path. On current ``master`` it FAILS by design (BALANCE requests
  modelType 2 = real income; INCOME requests modelType 1 = real balance,
  truncated to the single-page budget). Post-#198 (routing + pagination fix) it
  must PASS. This proves the *shipped adapter* is fixed — it does not, by
  itself, prove the semantics (LEG A does that).

  LEG C — PAGINATION: reproduces the partial-period truncation and the
  page-1-only metadata quirk (page >=2 omits totalPages/totalElements). Its
  result GATES the exit code post-fix (pre-fix it documents the bug).

Clean-room: only the project's own VNDirect api-finfo endpoint + adapter; no
vnstock / no derived material. Gated like scripts/probe_bank_itemcodes.py — NOT
collected by pytest.

    VNFIN_LIVE=1 ./.venv/bin/python scripts/probe_corporate_itemcodes.py

Exit 0 only if (LEG A) every raw balance/income/cashflow identity holds to
EXACT VND on every ticker AND (LEG B) the adapter resolves the headline codes
under the correct statement AND (LEG C) the multi-page fetch returns the
complete newest period. Confirmed live 2026-07-20/2026-07-21 (FPT/VIC/HPG/VNM).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

_TICKERS = ("FPT", "VIC", "HPG", "VNM")
_BASE = "https://api-finfo.vndirect.com.vn/v4/financial_statements"
_UA = {"User-Agent": os.environ.get("VNFIN_UA", "Mozilla/5.0 vnfin-oss-probe")}

# Retained-code identities checked to EXACT VND (integer residual == 0). An
# equality proves the operands participate in the relationship; the OFFICIAL
# filing cross-check in docs/design/corporate-itemcodes-probe-20260720.md is
# what names each operand ("current assets", "operating cash flow", ...).
_BAL_IDS = (  # modelType 1 = balance
    ("13000+14000==12700", ("13000", "14000"), "12700"),
    ("11000+12000==12700", ("11000", "12000"), "12700"),
    ("13100+13300==13000", ("13100", "13300"), "13000"),
    ("14100+14300==14000", ("14100", "14300"), "14000"),
    ("11100+11200+11300+11400+11500==11000",
     ("11100", "11200", "11300", "11400", "11500"), "11000"),
)
_INC_IDS = (  # modelType 2 = income
    ("21001-22100==23100", ("21001", "-22100"), "23100"),
    ("23800-22070==23003", ("23800", "-22070"), "23003"),
    ("23000+23500==23003", ("23000", "23500"), "23003"),
)
_CF_IDS = (  # modelType 3 = cashflow (reviewer B4 identities)
    ("32000+33000+34000==35000", ("32000", "33000", "34000"), "35000"),
    ("35000+36000+36100==37000", ("35000", "36000", "36100"), "37000"),
)


def _raw_fetch(sym, model, *, size=300, page=None):
    params = {
        "q": f"code:{sym}~reportType:ANNUAL~modelType:{model}",
        "sort": "fiscalDate:desc",
        "size": str(size),
    }
    if page is not None:
        params["page"] = str(page)
    url = _BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=25) as resp:  # noqa: S310 (trusted host)
        return json.load(resp)


def _latest_bucket(env):
    """{code(str): int VND} for the newest fiscalDate in the raw envelope."""
    data = env.get("data") or []
    if not data:
        return {}, None
    fd = data[0]["fiscalDate"]
    out = {}
    for row in data:
        if row.get("fiscalDate") != fd:
            continue
        code, val = row.get("itemCode"), row.get("numericValue")
        if code is None or val is None:
            continue
        out[str(int(code))] = int(val) if float(val).is_integer() else val
    return out, fd


def _check_ids(bucket, ids):
    """Every identity holds to EXACT VND (integer residual == 0)? Returns bool."""
    ok = True
    for label, addends, rhs in ids:
        vals = []
        missing = False
        for a in addends:
            neg = a.startswith("-")
            v = bucket.get(a[1:] if neg else a)
            if v is None:
                missing = True
                break
            vals.append(-v if neg else v)
        r = bucket.get(rhs)
        if missing or r is None:
            print(f"    {label}: SKIP (a retained code is absent)")
            ok = False
            continue
        residual = sum(vals) - r
        verdict = "EXACT" if residual == 0 else f"MISMATCH residual={residual}"
        print(f"    {label}: {verdict}")
        ok = ok and residual == 0
    return ok


def leg_a_raw(sym):
    print(f"=== LEG A raw template-identity: {sym} ===")
    ok = True
    for model, name, ids in ((1, "BALANCE", _BAL_IDS), (2, "INCOME", _INC_IDS),
                             (3, "CASHFLOW", _CF_IDS)):
        bucket, fd = _latest_bucket(_raw_fetch(sym, model))
        print(f"  modelType {model} = {name} (fd={fd}, n={len(bucket)})")
        ok = _check_ids(bucket, ids) and ok
    return ok


def leg_b_adapter(src, sym, StatementType, Period):
    """Adapter regression: BALANCE must resolve 12700/13000/14000; INCOME must
    resolve 21001/23800/23003. On inverted master these are absent -> FAIL."""
    print(f"=== LEG B adapter regression: {sym} ===")
    bal = src.get_financials(sym, StatementType.BALANCE, Period.ANNUAL, is_bank=False, limit=1)
    inc = src.get_financials(sym, StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=1)
    if not bal or not inc:
        print(f"  NO REPORTS (bal={bool(bal)} inc={bool(inc)})")
        return False
    b, i = bal[0], inc[0]
    bal_ok = None not in (b.get("12700"), b.get("13000"), b.get("14000"))
    inc_ok = None not in (i.get("21001"), i.get("23800"), i.get("23003"))
    print(f"  BALANCE model_type={b.model_type} headline_resolves={bal_ok}")
    print(f"  INCOME  model_type={i.model_type} headline_resolves={inc_ok}")
    return bal_ok and inc_ok


def leg_c_pagination(src, StatementType, Period):
    """GATES exit post-fix: the adapter must return VIC's COMPLETE newest annual
    balance period (>=142 line items, incl. 14000). Also documents the raw
    single-page truncation + page->=2 metadata omission the fix must handle."""
    print("=== LEG C pagination completeness (VIC balance) ===")
    # Raw evidence of the bug + metadata quirk (informational).
    p1 = _raw_fetch("VIC", 1, size=80, page=1)
    p2 = _raw_fetch("VIC", 1, size=80, page=2)
    p1_keys = sorted(k for k in p1 if k != "data")
    p2_keys = sorted(k for k in p2 if k != "data")
    print(f"  raw page1 envelope keys={p1_keys} (totalPages={p1.get('totalPages')})")
    print(f"  raw page2 envelope keys={p2_keys} (omits totalPages/totalElements)")
    # Adapter completeness (GATING): post-fix must return the full newest period.
    reports = src.get_financials("VIC", StatementType.BALANCE, Period.ANNUAL, is_bank=False, limit=1)
    if not reports:
        print("  adapter: NO REPORTS -> FAIL")
        return False
    r = reports[0]
    n, eq = len(r.items), r.get("14000")
    complete = n >= 142 and eq is not None
    print(f"  adapter newest-period n_items={n} owners_equity(14000)={eq!r} "
          f"-> {'COMPLETE (post-fix)' if complete else 'PARTIAL (pre-fix bug)'}")
    return complete


def main() -> int:
    if os.environ.get("VNFIN_LIVE") != "1":
        print("refusing to hit the network: set VNFIN_LIVE=1 to run this live probe", file=sys.stderr)
        return 2

    from vnfin.fundamentals.models import Period, StatementType
    from vnfin.fundamentals.vndirect import VNDirectFundamentalSource

    src = VNDirectFundamentalSource()

    leg_a = all(leg_a_raw(sym) for sym in _TICKERS)
    leg_b = all(leg_b_adapter(src, sym, StatementType, Period) for sym in _TICKERS)
    leg_c = leg_c_pagination(src, StatementType, Period)

    all_ok = leg_a and leg_b and leg_c
    print(f"\nLEG A raw identities : {'PASS' if leg_a else 'FAIL'}")
    print(f"LEG B adapter routing: {'PASS' if leg_b else 'FAIL (expected on inverted master)'}")
    print(f"LEG C pagination     : {'PASS' if leg_c else 'FAIL (expected pre-fix)'}")
    print(f"VERDICT: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
