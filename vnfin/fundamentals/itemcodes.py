"""Small client-side itemCode -> human name map for the most common lines.

VNDirect's ``/v4/financial_statements`` rows carry only a numeric ``itemCode``
(e.g. 11000) with no label. We ship a compact, clean-room map of the most
common corporate (modelType 1/2/3) and bank (101/102/103) line items so the
typed ``LineItem.name`` is human-readable. Unknown codes fall back to
``"item_<code>"``. The map intentionally covers only headline lines — it is not
a full chart of accounts.

These itemCode->name pairings were derived only from VNDirect's own API
responses and the public Vietnamese accounting statement structure; no vnstock
or derivative material was consulted.
"""
from __future__ import annotations

# Corporate (modelType 1 income / 2 balance / 3 cashflow) — headline lines.
_CORPORATE = {
    # Income statement (modelType 1)
    "11000": "Doanh thu thuần",  # net revenue
    "11100": "Giá vốn hàng bán",  # cost of goods sold
    "11200": "Lợi nhuận gộp",  # gross profit
    "20000": "Lợi nhuận trước thuế",  # profit before tax
    "21000": "Lợi nhuận sau thuế",  # profit after tax
    # Balance sheet (modelType 2)
    "23000": "Tài sản ngắn hạn",  # current assets
    "24000": "Tài sản dài hạn",  # long-term assets
    "25000": "Tổng tài sản",  # total assets
    "30000": "Nợ phải trả",  # total liabilities
    "40000": "Vốn chủ sở hữu",  # owners' equity
    # Cash flow (modelType 3)
    "31000": "Lưu chuyển tiền từ hoạt động kinh doanh",  # operating cash flow
    "32000": "Lưu chuyển tiền từ hoạt động đầu tư",  # investing cash flow
    "33000": "Lưu chuyển tiền từ hoạt động tài chính",  # financing cash flow
}

# Bank (modelType 101 income / 102 balance / 103 cashflow) — headline lines.
_BANK = {
    "22070": "Thu nhập lãi thuần",  # net interest income
    "421601": "Lợi nhuận sau thuế",  # profit after tax
    "412000": "Tổng tài sản",  # total assets
}


def item_name(item_code: str, *, is_bank: bool = False) -> str:
    """Best-effort human name for a numeric statement itemCode."""
    code = str(item_code)
    if is_bank and code in _BANK:
        return _BANK[code]
    if code in _CORPORATE:
        return _CORPORATE[code]
    if code in _BANK:
        return _BANK[code]
    return f"item_{code}"
