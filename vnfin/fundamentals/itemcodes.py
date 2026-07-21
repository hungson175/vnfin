"""Small client-side itemCode -> human name map for the most common lines.

VNDirect's ``/v4/financial_statements`` rows carry only a numeric ``itemCode``
(e.g. 11000) with no label. We ship a compact, clean-room map of the most
common corporate (modelType 1/2/3) and bank (101/102/103) line items so the
typed ``LineItem.name`` is human-readable. Unknown codes fall back to
``"item_<code>"``. The map intentionally covers only headline lines — it is not
a full chart of accounts.

The same numeric code means *different* things across statement templates
(corporate vs bank, income vs balance), so lookups are keyed on ``model_type``:
a code is resolved only inside its own statement template, never via a
cross-template fallback. An unmapped code returns the honest raw ``item_<code>``
rather than a guessed (and possibly wrong) label. See
``docs/design/bank-fundamentals-itemcodes.md`` for the mapping rationale and
``docs/design/bank-itemcodes-probe-20260620.md`` for the identity-proven bank
anchors (#157).

These itemCode->name pairings were derived only from VNDirect's own API
responses and the public Vietnamese accounting statement structure; no vnstock
or derivative material was consulted.
"""
from __future__ import annotations

# Per-statement-template maps keyed on ``model_type`` (the authoritative key).
# Corporate: 1=balance, 2=income, 3=cashflow (#198 live-probe-verified). Bank:
# 101=balance, 102=income, 103=cashflow. A code is only ever looked up inside
# its own template; there is
# no cross-template fallback (see ``item_name`` below).
_NAMES_BY_MODEL_TYPE: dict[int, dict[str, str]] = {
    # ----- Corporate BALANCE sheet (modelType 1) -------------------------- #
    # Live-probe- + official-filing-verified (#198); only individually
    # official-correlated labels are named. Aggregate-only sub-lines
    # (11200/11300/11400/11500) stay raw ``item_<code>``.
    1: {
        "12700": "Tổng cộng tài sản",  # total assets
        "13000": "Nợ phải trả",  # total liabilities
        "14000": "Vốn chủ sở hữu",  # owners' equity
        "11000": "Tài sản ngắn hạn",  # current assets
        "12000": "Tài sản dài hạn",  # non-current assets
        "13100": "Nợ ngắn hạn",  # current liabilities
        "13300": "Nợ dài hạn",  # long-term liabilities
        "11100": "Tiền và các khoản tương đương tiền",  # cash & equivalents
    },
    # ----- Corporate INCOME statement (modelType 2) ----------------------- #
    2: {
        "21001": "Doanh thu thuần",  # net revenue
        "22100": "Giá vốn hàng bán",  # cost of goods sold
        "23100": "Lợi nhuận gộp",  # gross profit
        "23800": "Tổng lợi nhuận kế toán trước thuế",  # profit before tax
        "22070": "Chi phí thuế TNDN",  # income tax expense
        "23003": "Lợi nhuận sau thuế TNDN",  # profit after tax (total consolidated)
        "23000": "LNST của cổ đông công ty mẹ",  # PAT attributable to parent
        "23500": "LNST của cổ đông không kiểm soát",  # PAT attributable to NCI
    },
    # ----- Corporate CASH FLOW (modelType 3) ------------------------------ #
    3: {
        "32000": "Lưu chuyển tiền thuần từ HĐ kinh doanh",  # operating
        "33000": "Lưu chuyển tiền thuần từ HĐ đầu tư",  # investing
        "34000": "Lưu chuyển tiền thuần từ HĐ tài chính",  # financing
        "35000": "Lưu chuyển tiền thuần trong kỳ",  # net change in cash
        "36000": "Tiền và tương đương tiền đầu kỳ",  # cash at beginning of period
        "36100": "Ảnh hưởng của thay đổi tỷ giá",  # FX effect
        "37000": "Tiền và tương đương tiền cuối kỳ",  # cash at end of period
    },
    # ----- Bank balance sheet (modelType 101) — verified headline set ----- #
    101: {
        "12700": "Tổng tài sản",  # total assets
        "13000": "Nợ phải trả",  # total liabilities
        "14000": "Vốn chủ sở hữu",  # total equity
        "412000": "Cho vay khách hàng",  # customer loans
        "413300": "Tiền gửi của khách hàng",  # customer deposits
    },
    # ----- Bank income statement (modelType 102) — verified headline set -- #
    102: {
        "23800": "Lợi nhuận trước thuế",  # profit before tax (PBT)
        "23000": "Lợi nhuận sau thuế",  # profit after tax (PAT)
        "421900": "Thu nhập lãi thuần",  # net interest income (NII)
    },
    # ----- Bank cash flow (modelType 103) — FULLY RAW in v1 --------------- #
    # Even standard aggregates are unreliable for banks; every bank cashflow
    # line stays raw ``item_<code>`` (reviewer Q3, deferred).
    103: {},
}


def item_name(item_code: str, *, model_type: int | None = None) -> str:
    """Best-effort human name for a numeric statement itemCode.

    The label is resolved only within the statement template identified by
    ``model_type``. A code absent from that template (or a ``None``/unknown
    ``model_type``) returns the honest raw ``"item_<code>"`` — never a guessed
    or cross-template label.
    """
    code = str(item_code)
    table = _NAMES_BY_MODEL_TYPE.get(model_type)
    if table and code in table:
        return table[code]
    return f"item_{code}"
