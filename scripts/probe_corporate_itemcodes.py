#!/usr/bin/env python3
"""Manually-invoked LIVE probe: which VNDirect modelType is corporate balance vs income,
and what are the real headline itemCodes (#198 P0 statement-routing/mislabel fix)?

Issue #198 (reviewer triage-202607202156-issue198-corporate-fundamentals.md): the shipped
`_CORP_MODEL` (`vnfin/fundamentals/vndirect.py`) routes corporate INCOME->modelType 1 and
BALANCE->modelType 2. This probe independently re-derives, from the provider's OWN data plus
internal accounting identities, which template is which and which itemCodes carry which
canonical concept — mirroring the #157 bank probe (`scripts/probe_bank_itemcodes.py`).

Clean-room: VNDirect api-finfo adapter only (the project's own clean-room source); no vnstock.
Gated like scripts/diagnostics_live.py / scripts/probe_bank_itemcodes.py — NOT collected by
pytest.

    VNFIN_LIVE=1 ./.venv/bin/python scripts/probe_corporate_itemcodes.py

Exit 0 only if every ticker's balance identity (13000+14000==12700) holds exactly and every
income identity (21001-22100==23100; 23800-22070==23003; 23000+23500==23003) holds exactly.

**Pre-fix (current `master`) this script FAILS by design** — `get_financials(..., BALANCE)`
requests modelType 2 (real income, 25 items) and `get_financials(..., INCOME)` requests
modelType 1 (real balance, truncated to the 80-row single-page budget), so none of the
headline codes resolve on either side. Confirmed live 2026-07-20 (FPT/VIC/HPG/VNM annual).
Post-fix (#198 routing + pagination correction) this script is the regression check and must
report PASS.
"""
from __future__ import annotations

import os
import sys

_TICKERS = ("FPT", "VIC", "HPG", "VNM")
_TRILLION = 1e12


def _latest_bucket(reports_by_code, latest_fd):
    return {code: v for (fd, code), v in reports_by_code.items() if fd == latest_fd}


def _probe_ticker(src, sym, StatementType, Period):
    ok = True
    print(f"=== {sym} ===")

    # --- raw statement rows, one call per requested modelType (1=?, 2=?) via the source's
    # own template-agnostic path is not exposed publicly, so we hit both templates directly
    # using the source's internal single-page fetch (limit generous so we see one full period).
    bal_reports = src.get_financials(sym, StatementType.BALANCE, Period.ANNUAL, is_bank=False, limit=1)
    inc_reports = src.get_financials(sym, StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=1)
    if not bal_reports or not inc_reports:
        print(f"  NO REPORTS (bal={bal_reports!r} inc={inc_reports!r})")
        return False
    bal, inc = bal_reports[0], inc_reports[0]
    print(f"  balance  model_type={bal.model_type} fiscal_date={bal.fiscal_date} n_items={len(bal.items)}")
    print(f"  income   model_type={inc.model_type} fiscal_date={inc.fiscal_date} n_items={len(inc.items)}")

    a, liab, eq = bal.get("12700"), bal.get("13000"), bal.get("14000")
    if None in (a, liab, eq):
        print(f"  balance identity: SKIP (a={a} liab={liab} eq={eq} — a code is missing)")
        ok = False
    else:
        diff = (liab + eq) - a
        rel = abs(diff) / a if a else 1.0
        verdict = "OK" if rel < 1e-6 else "MISMATCH"
        print(f"  balance identity 13000+14000-12700 = {diff / _TRILLION:+.6f} T (rel {rel:.2e}) {verdict}")
        ok = ok and rel < 1e-6

    rev, cogs, gp = inc.get("21001"), inc.get("22100"), inc.get("23100")
    pbt, tax, pat_total, pat_parent, pat_nci = (
        inc.get("23800"), inc.get("22070"), inc.get("23003"), inc.get("23000"), inc.get("23500"),
    )
    if None in (rev, cogs, gp):
        print(f"  gross-profit identity: SKIP (rev={rev} cogs={cogs} gp={gp})")
        ok = False
    else:
        d = (rev - cogs) - gp
        print(f"  gross-profit identity 21001-22100-23100 = {d:+.2f} {'OK' if d == 0 else 'MISMATCH'}")
        ok = ok and d == 0
    if None in (pbt, tax, pat_total):
        print(f"  PAT identity: SKIP (pbt={pbt} tax={tax} pat_total={pat_total})")
        ok = False
    else:
        d = (pbt - tax) - pat_total
        print(f"  PAT identity 23800-22070-23003 = {d:+.2f} {'OK' if d == 0 else 'MISMATCH'}")
        ok = ok and d == 0
    if None in (pat_parent, pat_nci, pat_total):
        print(f"  PAT split identity: SKIP (parent={pat_parent} nci={pat_nci} total={pat_total})")
        ok = False
    else:
        d = (pat_parent + pat_nci) - pat_total
        print(f"  PAT split identity 23000+23500-23003 = {d:+.2f} {'OK' if d == 0 else 'MISMATCH'}")
        ok = ok and d == 0

    print(f"  values (T VND): assets={a/_TRILLION if a else None} liab={liab/_TRILLION if liab else None} "
          f"eq={eq/_TRILLION if eq else None} rev={rev/_TRILLION if rev else None} "
          f"pbt={pbt/_TRILLION if pbt else None} pat_total={pat_total/_TRILLION if pat_total else None} "
          f"pat_parent={pat_parent/_TRILLION if pat_parent else None}")
    return ok


def _probe_pagination(src, StatementType, Period):
    """Reproduce the reported partial-period bug: size=80 (limit=1 budget) truncates VIC's
    142-line-item newest annual balance period, silently dropping 14000 (owners' equity)."""
    print("=== pagination (single-page size=80, VIC balance) ===")
    reports = src.get_financials("VIC", StatementType.BALANCE, Period.ANNUAL, is_bank=False, limit=1)
    if not reports:
        print("  NO REPORTS")
        return False
    r = reports[0]
    n = len(r.items)
    eq = r.get("14000")
    print(f"  n_items={n} owners_equity(14000)={eq!r}")
    if n < 142 or eq is None:
        print("  CONFIRMED: single-page fetch returns a PARTIAL period (owners' equity silently missing)")
        return True
    print("  NOT reproduced (adapter or provider behavior changed)")
    return False


def main() -> int:
    if os.environ.get("VNFIN_LIVE") != "1":
        print("refusing to hit the network: set VNFIN_LIVE=1 to run this live probe", file=sys.stderr)
        return 2

    from vnfin.fundamentals.models import Period, StatementType
    from vnfin.fundamentals.vndirect import VNDirectFundamentalSource

    src = VNDirectFundamentalSource()
    all_ok = True
    for sym in _TICKERS:
        all_ok &= _probe_ticker(src, sym, StatementType, Period)
    _probe_pagination(src, StatementType, Period)  # informational only, not gating exit code

    print(f"\nVERDICT: {'PASS — model 1 = balance, model 2 = income, headline codes confirmed' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
