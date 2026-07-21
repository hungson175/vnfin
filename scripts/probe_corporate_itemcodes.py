#!/usr/bin/env python3
"""Manually-invoked LIVE probe for #198 (corporate statement routing/mislabel +
pagination). THREE independent legs, each stating exactly what it proves:

  LEG A — RAW template-identity (bypasses the adapter): queries VNDirect
  ``modelType`` 1/2/3 directly and checks provider-only accounting identities to
  EXACT VND (integer residual == 0), on the newest AND second-newest (FY2024)
  balance period. Proves *which template is which* and *which itemCodes
  participate in which identity* WITHOUT depending on the library's (currently
  inverted) routing. Load-bearing evidence.

  LEG B — ADAPTER routing regression: calls the public
  ``VNDirectFundamentalSource`` and asserts the FULL provenance tuple
  ``(statement_type, is_bank, model_type, source)`` on the returned report AND
  that the headline codes resolve. On current ``master`` this FAILS by design
  (BALANCE routes to modelType 2, INCOME to modelType 1). Asserting the tuple
  (not just code presence) blocks a false PASS from a report tagged 999/998.

  LEG C — PAGINATION completeness ORACLE: builds a FINITE, VALIDATED, fail-closed
  raw oracle of VIC's newest annual balance fiscal-date group (caps at page-1
  ``totalPages``, validates ``currentPage`` identity, rejects a premature-empty /
  malformed / duplicate-code / out-of-order page, and certifies completeness only
  once a lower date is seen or a validated final page is exhausted), then requires
  the adapter to reproduce that date and its ``itemCode -> value`` set EXACTLY
  (``Decimal``, never lossy ``float``). No magic 142 threshold; a truncated raw
  oracle fails rather than certifying a partial as complete.

Every leg's assertions affect the exit code, and every ticker is evaluated even
after an earlier failure (no short-circuit).

Clean-room: only the project's own VNDirect api-finfo endpoint + adapter; no
vnstock / no derived material. Gated like scripts/probe_bank_itemcodes.py — NOT
collected by pytest.

    VNFIN_LIVE=1 ./.venv/bin/python scripts/probe_corporate_itemcodes.py

Exit 0 only if every LEG A identity (both years) holds exact-VND, LEG B resolves
the correct tuple + headline codes for every ticker, and LEG C's adapter set
equals the raw oracle set. Confirmed live 2026-07-20/2026-07-21 (FPT/VIC/HPG/VNM).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from decimal import Decimal

_TICKERS = ("FPT", "VIC", "HPG", "VNM")
_BASE = "https://api-finfo.vndirect.com.vn/v4/financial_statements"
_UA = {"User-Agent": os.environ.get("VNFIN_UA", "Mozilla/5.0 vnfin-oss-probe")}

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
        # parse_float=Decimal keeps VND values EXACT (some exceed float's 2**53
        # integer-exact range; a 1-VND diff must never compare equal — reviewer R9).
        return json.loads(resp.read().decode("utf-8"), parse_float=Decimal)


def _is_raw_int(x):
    """Raw, non-bool int (JSON currentPage/totalPages arrive as int)."""
    return isinstance(x, int) and not isinstance(x, bool)


def _bucket(env, fd):
    """{itemCode(str): Decimal VND} for one fiscalDate in a raw envelope (exact)."""
    out = {}
    for row in env.get("data") or []:
        if row.get("fiscalDate") != fd:
            continue
        code, val = row.get("itemCode"), row.get("numericValue")
        if code is None or val is None:
            continue
        out[str(int(code))] = val if isinstance(val, Decimal) else Decimal(str(val))
    return out


def _distinct_dates(env):
    dates = []
    for row in env.get("data") or []:
        fd = row.get("fiscalDate")
        if fd and fd not in dates:
            dates.append(fd)
    return dates


def _check_ids(bucket, ids, *, label):
    ok = True
    for name, addends, rhs in ids:
        vals, missing = [], False
        for a in addends:
            neg = a.startswith("-")
            v = bucket.get(a[1:] if neg else a)
            if v is None:
                missing = True
                break
            vals.append(-v if neg else v)
        r = bucket.get(rhs)
        if missing or r is None:
            print(f"    [{label}] {name}: SKIP (a retained code is absent)")
            ok = False
            continue
        residual = sum(vals) - r
        print(f"    [{label}] {name}: {'EXACT' if residual == 0 else f'MISMATCH residual={residual}'}")
        ok = ok and residual == 0
    return ok


def leg_a_raw(sym):
    print(f"=== LEG A raw template-identity: {sym} ===")
    ok = True
    # balance: require EXACTLY two complete periods (reviewer R10) — the two
    # newest distinct fiscalDates, reported by their actual dates (not hard-coded
    # year labels). Fewer than two -> FAIL (cannot claim the 8-check evidence).
    bal_env = _raw_fetch(sym, 1)
    bal_dates = _distinct_dates(bal_env)
    if len(bal_dates) < 2:
        print(f"  LEG A FAIL: need 2 balance periods, saw {bal_dates}")
        return False
    for fd in bal_dates[:2]:
        print(f"  modelType 1 = BALANCE (fd={fd})")
        ok = _check_ids(_bucket(bal_env, fd), _BAL_IDS, label=fd) and ok
    # income + cashflow: newest only
    for model, name, ids in ((2, "INCOME", _INC_IDS), (3, "CASHFLOW", _CF_IDS)):
        env = _raw_fetch(sym, model)
        dates = _distinct_dates(env)
        if not dates:
            print(f"  LEG A FAIL: no {name} period")
            return False
        fd = dates[0]
        print(f"  modelType {model} = {name} (fd={fd})")
        ok = _check_ids(_bucket(env, fd), ids, label=fd) and ok
    return ok


def leg_b_adapter(src, sym, StatementType, Period):
    """Assert the exact provenance tuple, not just code presence, so a report
    tagged with a bogus model_type (999/998) cannot false-PASS."""
    print(f"=== LEG B adapter routing regression: {sym} ===")
    ok = True
    for st, want_model, heads in (
        (StatementType.BALANCE, 1, ("12700", "13000", "14000")),
        (StatementType.INCOME, 2, ("21001", "23800", "23003")),
    ):
        reports = src.get_financials(sym, st, Period.ANNUAL, is_bank=False, limit=1)
        if not reports:
            print(f"  {st.value}: NO REPORTS -> FAIL")
            ok = False
            continue
        r = reports[0]
        tuple_ok = (
            r.statement_type == st and r.is_bank is False
            and r.model_type == want_model and r.source == "vndirect"
        )
        heads_ok = all(r.get(c) is not None for c in heads)
        print(f"  {st.value}: tuple=({r.statement_type.value},{r.is_bank},{r.model_type},{r.source}) "
              f"expect(...,False,{want_model},vndirect) tuple_ok={tuple_ok} headline_resolves={heads_ok}")
        ok = ok and tuple_ok and heads_ok
    return ok


def _raw_newest_group_oracle(sym, model, *, page_size=80):
    """Finite, validated, fail-closed raw oracle of the NEWEST fiscalDate group
    (reviewer R9). Returns (newest_fd, {code: Decimal}) or None on any defect:
    premature-empty/malformed page, duplicate code, bad/undeclared totalPages,
    currentPage!=page, or inconsistent date order. The group is 'complete' only
    once a LOWER date is observed or a VALIDATED final page is exhausted."""
    page, cached_tp, newest_fd, oracle, complete = 1, None, None, {}, False
    while True:
        env = _raw_fetch(sym, model, size=page_size, page=page)
        data = env.get("data")
        if not isinstance(data, list) or not data:
            return None  # premature empty / malformed -> cannot certify completeness
        cp = env.get("currentPage")
        if not _is_raw_int(cp) or cp != page:
            return None
        if page == 1:
            cached_tp = env.get("totalPages")
            if not _is_raw_int(cached_tp) or cached_tp < 1:
                return None
        elif "totalPages" in env and env["totalPages"] != cached_tp:
            return None
        for row in data:
            if not isinstance(row, dict):
                return None
            fd, code, val = row.get("fiscalDate"), row.get("itemCode"), row.get("numericValue")
            if fd is None or code is None or val is None:
                return None
            if newest_fd is None:
                newest_fd = fd
            if fd != newest_fd:
                complete = True  # a lower date proves the newest group closed
                break
            c = str(int(code))
            if c in oracle:
                return None  # duplicate code within the group
            oracle[c] = val if isinstance(val, Decimal) else Decimal(str(val))
        if complete:
            break
        if cp >= cached_tp:
            complete = True  # validated final page exhausted with no lower date
            break
        page += 1
    if not complete or not oracle:
        return None
    return newest_fd, oracle


def leg_c_pagination(src, StatementType, Period):
    """Completeness ORACLE: build a finite validated raw oracle of VIC's newest
    annual balance date group, then require the adapter to reproduce that date
    and its full itemCode->value set EXACTLY (Decimal, not lossy float)."""
    print("=== LEG C pagination completeness oracle (VIC balance) ===")
    built = _raw_newest_group_oracle("VIC", 1)
    if built is None:
        print("  oracle: could not build a validated complete newest-date group -> FAIL")
        return False
    newest_fd, oracle = built
    print(f"  oracle: newest_fd={newest_fd} complete_group_size={len(oracle)}")
    reports = src.get_financials("VIC", StatementType.BALANCE, Period.ANNUAL, is_bank=False, limit=1)
    if not reports:
        print("  adapter: NO REPORTS -> FAIL")
        return False
    r = reports[0]
    adapter = {li.item_code: li.value for li in r.items}
    date_ok = str(r.fiscal_date) == newest_fd
    codes_ok = set(adapter) == set(oracle)
    # EXACT compare via Decimal(str(...)) — never float() both sides (R9).
    values_ok = all(Decimal(str(adapter[c])) == oracle[c] for c in oracle if c in adapter)
    missing = sorted(set(oracle) - set(adapter))
    print(f"  adapter newest={r.fiscal_date} n_items={len(adapter)} date_ok={date_ok} "
          f"codes_ok={codes_ok} values_ok={values_ok} missing_from_adapter={missing[:8]}")
    return date_ok and codes_ok and values_ok


def main() -> int:
    if os.environ.get("VNFIN_LIVE") != "1":
        print("refusing to hit the network: set VNFIN_LIVE=1 to run this live probe", file=sys.stderr)
        return 2

    from vnfin.fundamentals.models import Period, StatementType
    from vnfin.fundamentals.vndirect import VNDirectFundamentalSource

    src = VNDirectFundamentalSource()

    # Materialize (not all(generator)) so every ticker is evaluated even on failure.
    leg_a = all([leg_a_raw(sym) for sym in _TICKERS])
    leg_b = all([leg_b_adapter(src, sym, StatementType, Period) for sym in _TICKERS])
    leg_c = leg_c_pagination(src, StatementType, Period)

    all_ok = leg_a and leg_b and leg_c
    print(f"\nLEG A raw identities (2yr balance + income + cashflow): {'PASS' if leg_a else 'FAIL'}")
    print(f"LEG B adapter routing tuple                           : {'PASS' if leg_b else 'FAIL (expected on inverted master)'}")
    print(f"LEG C pagination completeness oracle                  : {'PASS' if leg_c else 'FAIL (expected pre-fix)'}")
    print(f"VERDICT: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
