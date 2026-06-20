#!/usr/bin/env python3
"""Manually-invoked LIVE probe: do PRIVATE banks share the SOCB bank itemCodes?

Issue #157 (bank-mislabel) base-layer Q1 gate. The corrected per-model_type bank
chart-of-accounts was anchor-verified on state-owned banks (VCB/CTG/BID). Before
shipping a per-model_type map we must confirm a PRIVATE bank uses the SAME numeric
itemCodes with the same meanings — otherwise the map silently mislabels a whole
bank class. Cheap insurance.

Clean-room: VNDirect api-finfo adapter only (the project's own clean-room source);
no vnstock. Gated like scripts/diagnostics_live.py — NOT collected by pytest.

    VNFIN_LIVE=1 ./.venv/bin/python scripts/probe_bank_itemcodes.py

Prints, per bank, the value (VND trillion) of each code-of-interest under the bank
balance (modelType 101) and income (modelType 102) templates, the accounting
identity check (13000 total-liabilities + 14000 total-equity == 12700 total-assets),
and any code-of-interest that is MISSING for that bank. Exit 0 only if every probed
bank exposes every code-of-interest AND the identity holds within rounding.
"""
from __future__ import annotations

import os
import sys

# SOCB controls (anchor-verified) + the private-bank Q1 targets.
_CONTROL_BANKS = ("VCB", "CTG")
_PRIVATE_BANKS = ("VPB", "ACB")

# Corrected (design-doc) bank codes under each template.
_BALANCE_CODES = {  # modelType 101
    "12700": "total assets",
    "13000": "total liabilities",
    "14000": "total equity",
    "412000": "customer loans",
    "413300": "customer deposits",
}
_INCOME_CODES = {  # modelType 102
    "23800": "profit before tax",
    "23000": "profit after tax",
    "421900": "net interest income",
}

_TRILLION = 1e12


def _latest(reports):
    """Return the most recent FinancialReport (API sorts fiscalDate desc)."""
    return reports[0] if reports else None


def _probe_bank(src, sym, StatementType, Period):
    from vnfin.fundamentals.models import StatementType as _ST  # noqa: F401

    bal = _latest(src.get_financials(sym, StatementType.BALANCE, Period.ANNUAL, is_bank=True, limit=2))
    inc = _latest(src.get_financials(sym, StatementType.INCOME, Period.ANNUAL, is_bank=True, limit=2))
    if bal is None or inc is None:
        print(f"  {sym}: NO REPORTS (bal={bal!r} inc={inc!r})")
        return False

    ok = True
    print(f"  {sym}  (balance mt={bal.model_type} {bal.fiscal_date} | income mt={inc.model_type} {inc.fiscal_date})")
    missing = []
    for code, label in _BALANCE_CODES.items():
        v = bal.get(code)
        if v is None:
            missing.append(f"{code}({label})")
            print(f"      bal {code:>7} {label:<20} MISSING")
        else:
            print(f"      bal {code:>7} {label:<20} {v / _TRILLION:>12,.2f} T")
    for code, label in _INCOME_CODES.items():
        v = inc.get(code)
        if v is None:
            missing.append(f"{code}({label})")
            print(f"      inc {code:>7} {label:<20} MISSING")
        else:
            print(f"      inc {code:>7} {label:<20} {v / _TRILLION:>12,.2f} T")

    # Accounting identity: liabilities + equity == total assets.
    a, liab, eq = bal.get("12700"), bal.get("13000"), bal.get("14000")
    if None in (a, liab, eq):
        print("      identity: SKIP (a code is missing)")
        ok = False
    else:
        diff = (liab + eq) - a
        rel = abs(diff) / a if a else 1.0
        verdict = "OK" if rel < 1e-6 else "MISMATCH"
        print(f"      identity 13000+14000-12700 = {diff / _TRILLION:+.4f} T  (rel {rel:.2e})  {verdict}")
        ok = ok and rel < 1e-6

    if missing:
        print(f"      >>> MISSING codes-of-interest: {', '.join(missing)}")
        ok = False
    return ok


def main() -> int:
    if os.environ.get("VNFIN_LIVE") != "1":
        print("refusing to hit the network: set VNFIN_LIVE=1 to run this live probe", file=sys.stderr)
        return 2

    from vnfin.fundamentals.models import Period, StatementType
    from vnfin.fundamentals.vndirect import VNDirectFundamentalSource

    src = VNDirectFundamentalSource()
    all_ok = True
    print("=== CONTROL (SOCB, anchor-verified) ===")
    for sym in _CONTROL_BANKS:
        all_ok &= _probe_bank(src, sym, StatementType, Period)
    print("\n=== Q1 TARGETS (PRIVATE banks) ===")
    for sym in _PRIVATE_BANKS:
        all_ok &= _probe_bank(src, sym, StatementType, Period)

    print(f"\nVERDICT: {'PASS — private banks share the SOCB bank itemCodes' if all_ok else 'FAIL — code map does NOT generalize as-is'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
