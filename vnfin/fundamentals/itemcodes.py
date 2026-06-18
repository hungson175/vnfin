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
    "12000": "Doanh thu hoạt động tài chính",  # financial income
    "12100": "Chi phí tài chính",  # financial expenses
    "13000": "Chi phí bán hàng",  # selling expenses
    "13100": "Chi phí quản lý doanh nghiệp",  # general & admin expenses
    "14000": "Lợi nhuận thuần từ hoạt động kinh doanh",  # operating profit
    "20000": "Lợi nhuận trước thuế",  # profit before tax
    "21000": "Lợi nhuận sau thuế",  # profit after tax (net income)
    "21100": "Lợi nhuận sau thuế của cổ đông công ty mẹ",  # NPAT attributable to parent
    "22000": "Lãi cơ bản trên cổ phiếu",  # basic earnings per share (EPS)
    # Balance sheet (modelType 2)
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
    # Cash flow (modelType 3)
    "31000": "Lưu chuyển tiền từ hoạt động kinh doanh",  # operating cash flow
    "32000": "Lưu chuyển tiền từ hoạt động đầu tư",  # investing cash flow
    "33000": "Lưu chuyển tiền từ hoạt động tài chính",  # financing cash flow
    "34000": "Lưu chuyển tiền thuần trong kỳ",  # net change in cash
    "35000": "Tiền và tương đương tiền cuối kỳ",  # cash at end of period
}

# Bank (modelType 101 income / 102 balance / 103 cashflow) — headline lines.
_BANK = {
    # Income statement (modelType 102)
    "22070": "Thu nhập lãi thuần",  # net interest income
    "22080": "Lãi/lỗ thuần từ hoạt động dịch vụ",  # net fee & commission income
    "22120": "Tổng thu nhập hoạt động",  # total operating income
    "22130": "Chi phí hoạt động",  # operating expenses
    "22150": "Chi phí dự phòng rủi ro tín dụng",  # credit loss provision expense
    "22160": "Lợi nhuận trước thuế",  # profit before tax
    "421601": "Lợi nhuận sau thuế",  # profit after tax (net income)
    # Balance sheet (modelType 101)
    "411600": "Cho vay khách hàng",  # loans to customers
    "412000": "Tổng tài sản",  # total assets
    "413100": "Tiền gửi của khách hàng",  # customer deposits
    "414000": "Tổng nợ phải trả",  # total liabilities
    "415000": "Vốn chủ sở hữu",  # owners' equity
    # Cash flow (modelType 103)
    "431000": "Lưu chuyển tiền từ hoạt động kinh doanh",  # operating cash flow
    "432000": "Lưu chuyển tiền từ hoạt động đầu tư",  # investing cash flow
    "433000": "Lưu chuyển tiền từ hoạt động tài chính",  # financing cash flow
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
