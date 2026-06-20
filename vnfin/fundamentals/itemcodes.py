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
# Corporate: 1=income, 2=balance, 3=cashflow. Bank: 101=balance, 102=income,
# 103=cashflow. A code is only ever looked up inside its own template; there is
# no cross-template fallback (see ``item_name`` below).
_NAMES_BY_MODEL_TYPE: dict[int, dict[str, str]] = {
    # ----- Corporate income statement (modelType 1) ----------------------- #
    1: {
        "11000": "Doanh thu thuần",  # net revenue
        "11100": "Giá vốn hàng bán",  # cost of goods sold
        "11200": "Lợi nhuận gộp",  # gross profit
        "12000": "Doanh thu hoạt động tài chính",  # financial income
        "12100": "Chi phí tài chính",  # financial expenses
        "13000": "Chi phí bán hàng",  # selling expenses
        "13100": "Chi phí quản lý doanh nghiệp",  # general & admin expenses
        "14000": "Lợi nhuận thuần từ hoạt động kinh doanh",  # operating profit
        "20000": "Lợi nhuận trước thuế",  # profit before tax
        "21000": "Lợi nhuận sau thuế",  # profit after tax (net income)
        "21100": "Lợi nhuận sau thuế của cổ đông công ty mẹ",  # NPAT to parent
        "22000": "Lãi cơ bản trên cổ phiếu",  # basic earnings per share (EPS)
    },
    # ----- Corporate balance sheet (modelType 2) -------------------------- #
    2: {
        "23000": "Tài sản ngắn hạn",  # current assets
        "23100": "Tiền và tương đương tiền",  # cash and cash equivalents
        "23200": "Đầu tư tài chính ngắn hạn",  # short-term financial investments
        "23300": "Các khoản phải thu ngắn hạn",  # short-term receivables
        "23400": "Hàng tồn kho",  # inventories
        "24000": "Tài sản dài hạn",  # long-term assets
        "24100": "Tài sản cố định",  # fixed assets
        "25000": "Tổng tài sản",  # total assets
        "30000": "Nợ phải trả",  # total liabilities
        "30100": "Nợ ngắn hạn",  # current liabilities
        "30200": "Nợ dài hạn",  # long-term liabilities
        "40000": "Vốn chủ sở hữu",  # owners' equity
        "40100": "Vốn góp của chủ sở hữu",  # paid-in / contributed capital
        "40200": "Lợi nhuận sau thuế chưa phân phối",  # retained earnings
        "49000": "Tổng nguồn vốn",  # total resources (liabilities + equity)
    },
    # ----- Corporate cash flow (modelType 3) ------------------------------ #
    3: {
        "31000": "Lưu chuyển tiền từ hoạt động kinh doanh",  # operating cash flow
        "32000": "Lưu chuyển tiền từ hoạt động đầu tư",  # investing cash flow
        "33000": "Lưu chuyển tiền từ hoạt động tài chính",  # financing cash flow
        "34000": "Lưu chuyển tiền thuần trong kỳ",  # net change in cash
        "35000": "Tiền và tương đương tiền cuối kỳ",  # cash at end of period
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
