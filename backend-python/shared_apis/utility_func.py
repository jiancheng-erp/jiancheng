from typing import Optional
def normalize_currency(cur: Optional[str]) -> str:
    if not cur:
        return "CNY"
    c = str(cur).strip().upper()
    if c in ("CNY", "RMB"):
        return "CNY"
    if c in ("USD", "USA", "美金"):
        return "USD"
    if c == "EUR":
        return "EUR"
    return c
def normalize_category_by_batch_type(batch_name: Optional[str]) -> str:
    if not batch_name:
        return "其它"
    name = str(batch_name).strip()
    if "男" in name:
        return "男鞋"
    if "女" in name:
        return "女鞋"
    if "童" in name:
        return "童鞋"
    return "其它"

