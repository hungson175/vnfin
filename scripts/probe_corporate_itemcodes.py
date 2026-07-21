#!/usr/bin/env python3
"""Manually-invoked LIVE probe for #198 (corporate statement routing/mislabel +
pagination). THREE independent legs, each stating exactly what it proves:

  LEG A — RAW template-identity (bypasses the adapter): queries VNDirect
  ``modelType`` 1/2/3 directly and checks provider-only accounting identities to
  EXACT VND (integer residual == 0), on two observed identity-bearing balance
  periods plus the newest income/cash-flow period. Proves *which template is which*
  and *which itemCodes participate in which identity* WITHOUT depending on the
  library's (currently inverted) routing. (Period COMPLETENESS is LEG C's job; LEG
  A asserts identity consistency, not that every line of a period is present.)

  LEG B — ADAPTER routing regression: calls the public
  ``VNDirectFundamentalSource`` and asserts the FULL provenance tuple
  ``(statement_type, is_bank, model_type, source)`` on the returned report AND
  that the headline codes resolve. POST-FIX this PASSES (BALANCE->modelType 1,
  INCOME->modelType 2); against pre-fix master it FAILED by design (BALANCE
  routed to modelType 2, INCOME to modelType 1). Asserting the tuple (not just
  code presence) blocks a false PASS from a report tagged 999/998.

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

Exit 0 only if every LEG A identity (two observed identity-bearing periods) holds exact-VND, LEG B
resolves the correct tuple + headline codes for every ticker, and LEG C's adapter set equals the raw
oracle set. Observed live 2026-07-21, POST-FIX (FPT/VIC/HPG/VNM): LEG A, LEG B, and LEG C all PASS —
the #198 routing + pagination fix has shipped, so the full three-leg live PASS is now the observed
state (VIC's newest annual balance reproduces its complete 142-item fiscal-date group). Honest note:
against pre-fix (inverted) master LEG B and LEG C FAILED by design (BALANCE routed to modelType 2,
INCOME to modelType 1, and the single-page fetch truncated VIC's balance); LEG A passed pre-fix too
(it bypasses the adapter).
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from decimal import Decimal

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_CANON_DIGITS = re.compile(r"[1-9]\d*|0")
_TWO53 = 2 ** 53  # at/above this magnitude a float cannot hold an integer VND value exactly


def _canonical_int(x):
    """STRICT canonical non-negative integer key, mirroring the adapter's
    ``canonical_provider_key`` / ``_parse_model_type`` contract but Decimal-aware
    (the probe parses JSON numbers as ``Decimal``): a non-bool ``int``, an integral
    finite ``float``/``Decimal`` (``11000.0`` ok, ``1.9`` / ``11000.9`` rejected),
    or a canonical digit string (``"11000"``/``"0"``; no leading zero, sign, or
    padding). Everything else (bool, fractional, NaN, negative, container, None)
    -> ``None`` (reviewer R18)."""
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x if x >= 0 else None
    if isinstance(x, float):
        return int(x) if math.isfinite(x) and x >= 0 and x == int(x) else None
    if isinstance(x, Decimal):
        return int(x) if x.is_finite() and x >= 0 and x == x.to_integral_value() else None
    if isinstance(x, str) and _CANON_DIGITS.fullmatch(x):
        return int(x)
    return None


def _valid_iso(fd):
    """Exact unpadded YYYY-MM-DD AND a real calendar date (rejects 2025-99-99)."""
    if not isinstance(fd, str) or not _ISO_DATE.fullmatch(fd):
        return False
    try:
        datetime.strptime(fd, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _row_identity_ok(row, sym, model):
    """A raw row must carry the requested symbol / ANNUAL cadence / EXACT template
    before it may certify semantics or enter the oracle (reviewer R16.3 + R18).
    Model uses the strict canonical parser — ``True`` / ``1.9`` / ``Decimal('1.9')``
    are NOT model 1."""
    code = row.get("code")
    if not isinstance(code, str) or code.strip().upper() != sym:
        return False
    if row.get("reportType") != "ANNUAL":
        return False
    return _canonical_int(row.get("modelType")) == model

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


def _bucket(env, fd, *, sym, model):
    """{itemCode(str): Decimal VND} for one fiscalDate — only rows whose raw
    identity (code/reportType/modelType) matches the request (reviewer R16.3)."""
    out = {}
    for row in env.get("data") or []:
        if row.get("fiscalDate") != fd or not _row_identity_ok(row, sym, model):
            continue
        c, val = _canonical_int(row.get("itemCode")), row.get("numericValue")
        if c is None or val is None:                       # strict itemCode: 11000.9 rejected (R18)
            continue
        out[str(c)] = val if isinstance(val, Decimal) else Decimal(str(val))
    return out


def _distinct_dates(env, *, sym, model):
    """Distinct valid-calendar fiscalDates from identity-matching rows only."""
    dates = []
    for row in env.get("data") or []:
        fd = row.get("fiscalDate")
        if _valid_iso(fd) and _row_identity_ok(row, sym, model) and fd not in dates:
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
    # balance: require two observed identity-bearing distinct fiscalDates and check the balance
    # IDENTITY on each (reviewer R10 requires >=2 dates). NOTE (reviewer R13): this
    # proves the identity holds on two identity-BEARING periods (the headline codes
    # are present and consistent), NOT that every line of each period is complete —
    # period COMPLETENESS is LEG C's oracle. Dates reported as observed, not
    # hard-coded year labels.
    bal_env = _raw_fetch(sym, 1)
    bal_dates = _distinct_dates(bal_env, sym=sym, model=1)
    if len(bal_dates) < 2:
        print(f"  LEG A FAIL: need 2 observed identity-bearing balance periods, saw {bal_dates}")
        return False
    for fd in bal_dates[:2]:
        print(f"  modelType 1 = BALANCE (fd={fd})")
        ok = _check_ids(_bucket(bal_env, fd, sym=sym, model=1), _BAL_IDS, label=fd) and ok
    # income + cashflow: newest only
    for model, name, ids in ((2, "INCOME", _INC_IDS), (3, "CASHFLOW", _CF_IDS)):
        env = _raw_fetch(sym, model)
        dates = _distinct_dates(env, sym=sym, model=model)
        if not dates:
            print(f"  LEG A FAIL: no {name} period")
            return False
        fd = dates[0]
        print(f"  modelType {model} = {name} (fd={fd})")
        ok = _check_ids(_bucket(env, fd, sym=sym, model=model), ids, label=fd) and ok
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
    (reviewer R9 + R13 + R16). Returns (newest_fd, {code: Decimal}) or None on ANY
    defect. Validates the fetched PREFIX up to and including the boundary page (NOT
    every declared historical page — only enough to prove the newest group complete):
    every row carries the requested identity (code/ANNUAL/model — R16.3) and a real
    calendar ISO date (R16.2); within that prefix dates are strictly descending and
    contiguous (a date, once left, may never reappear — a newest-date reappearance
    fails); `currentPage`/`totalPages` are raw non-bool ints (`2.0 != 2` fails);
    duplicate newest-group codes fail. The newest group is 'complete' only once a
    STRICTLY-OLDER date is observed (not merely 'different') or a validated final
    page is exhausted; the full boundary page is scanned to catch a reappearance."""
    page, cached_tp, newest_fd, last_fd = 1, None, None, None
    closed, oracle, complete = set(), {}, False
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
        elif "totalPages" in env:
            tp = env["totalPages"]
            if not _is_raw_int(tp) or tp != cached_tp:  # raw-int BEFORE equality (2.0 != 2)
                return None
        for row in data:
            if not isinstance(row, dict):
                return None
            fd, val = row.get("fiscalDate"), row.get("numericValue")
            c = _canonical_int(row.get("itemCode"))        # strict: 11000.9 rejected (R18)
            # R16.2: real calendar date (rejects 2025-99-99); R16.3 + R18: raw identity must match request.
            if not _valid_iso(fd) or c is None or val is None:
                return None
            if not _row_identity_ok(row, sym, model):
                return None
            if newest_fd is None:
                newest_fd = fd
            if fd != last_fd:                       # date changed in the raw stream
                if fd in closed:
                    return None                     # reappearance of a closed date (incl. newest_fd)
                if last_fd is not None:
                    if fd >= last_fd:
                        return None                 # not strictly descending -> higher/equal/malformed
                    closed.add(last_fd)             # previous date group closes
                last_fd = fd
            if fd == newest_fd:
                key = str(c)
                if key in oracle:
                    return None                     # duplicate code within the newest group
                oracle[key] = val if isinstance(val, Decimal) else Decimal(str(val))
            # an older date does NOT break: keep scanning so a later newest_fd row
            # (a reappearance) is caught by the `fd in closed` check above.
        if newest_fd in closed:                     # a strictly-older date superseded the newest group
            complete = True
            break
        if cp >= cached_tp:                         # validated final page exhausted, newest group only
            complete = True
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
    # Fail closed if any value is non-integral or its MAGNITUDE reaches float's
    # exact-integer boundary (|v| >= 2**53, both signs): the adapter stored
    # LineItem.value as a float, so Decimal(str(value)) cannot restore lost precision
    # and an adjacent 1-VND value could alias to the same float (reviewer R13 + R16.1).
    bad = sorted(c for c, v in oracle.items() if v != v.to_integral_value() or abs(v) >= _TWO53)
    if bad:
        print(f"  FAIL closed: non-integral or |value|>=2**53, unverifiable via float adapter: {bad[:5]}")
        return False
    reports = src.get_financials("VIC", StatementType.BALANCE, Period.ANNUAL, is_bank=False, limit=1)
    if not reports:
        print("  adapter: NO REPORTS -> FAIL")
        return False
    r = reports[0]
    adapter = {li.item_code: li.value for li in r.items}
    date_ok = str(r.fiscal_date) == newest_fd
    codes_ok = set(adapter) == set(oracle)
    # EXACT compare via Decimal(str(...)) — never float() both sides (R9); guarded
    # against precision loss by the 2**53 fail-closed check above (R13).
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
    print(f"\nLEG A raw identities (two observed identity-bearing balance periods + income + cashflow): "
          f"{'PASS' if leg_a else 'FAIL'}")
    print(f"LEG B adapter routing tuple                           : {'PASS (post-fix)' if leg_b else 'FAIL (pre-fix inverted master fails by design)'}")
    print(f"LEG C pagination completeness oracle                  : {'PASS (post-fix)' if leg_c else 'FAIL (pre-fix single-page fetch truncates by design)'}")
    print(f"VERDICT: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
