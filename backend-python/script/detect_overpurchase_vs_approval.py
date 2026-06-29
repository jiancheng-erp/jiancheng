"""
检测「采购订单采购数量远大于核定用量」的异常采购行。

背景
----
``purchase_order_item`` 表中每条采购明细都带有：
- ``approval_amount``       —— 核定用量（依据 BOM 总用量核定，应为合理需求量）
- ``purchase_amount``       —— 下单采购数量
- ``adjust_purchase_amount``—— 调整后采购数量（多次下发/补单时使用）

实际下单数量按现网约定取「调整数量优先，否则用原采购数量」：
``effective = adjust_purchase_amount if adjust_purchase_amount else purchase_amount``
（见 ``logistics/multiissue_purchase_order.py``）。

当某个材料的实际采购数量远大于核定用量时，往往意味着：录入单位/数量错误、
重复下单、核定用量缺失（按 0 核定却仍下了大单）等问题，需要人工复核。

检测规则
--------
对每条采购明细计算 ``effective`` 与 ``approval``：
1. ``approval > 0`` 且 ``effective >= approval * ratio`` 且
   ``effective - approval >= min_excess`` —— 标记为「超采」。
2. ``approval <= 0`` 且 ``effective > 0`` —— 标记为「无核定却采购」
   （比值视为无穷大；可用 ``--include-zero-approval`` 控制是否纳入，默认纳入）。

``ratio``（默认 3.0）控制「远大于」的倍数阈值；``min_excess`` 过滤掉数量很小、
比值虽高但绝对差很小的噪声行。

本脚本为**只读**检测，不修改任何数据。可选 ``--csv`` 导出结果。

用法（在 backend-python 目录下）::

    python script/detect_overpurchase_vs_approval.py
    python script/detect_overpurchase_vs_approval.py --ratio 2 --min-excess 50
    python script/detect_overpurchase_vs_approval.py --orders K24001,K24002
    python script/detect_overpurchase_vs_approval.py --csv overpurchase.csv
"""

import argparse
import csv
import os
import sys
from decimal import Decimal, InvalidOperation

# 允许从 backend-python 目录直接运行：把项目根目录加入模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 在导入 config / app 之前加载 .env，确保 ProductionConfig 能读到数据库等环境变量
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from config import ProductionConfig
from models import (
    Material,
    Order,
    OrderShoe,
    PurchaseDivideOrder,
    PurchaseOrder,
    PurchaseOrderItem,
    Shoe,
    Supplier,
)

_PURCHASE_TYPE_LABEL = {"N": "一次采购", "S": "二次采购"}


def _dec(value) -> Decimal:
    """把任意值安全转成 Decimal；None / 非法值按 0 处理。"""
    if value is None:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(0)


def _effective_amount(item: PurchaseOrderItem) -> Decimal:
    """实际下单数量：调整数量优先，否则用原采购数量。"""
    adjust = _dec(item.adjust_purchase_amount)
    if adjust != 0:
        return adjust
    return _dec(item.purchase_amount)


def _collect_rows(order_rids):
    """拉取采购明细及其订单/鞋型/材料/供应商信息。

    返回 list[dict]，每个 dict 含报告所需字段。
    """
    query = (
        db.session.query(
            PurchaseOrderItem,
            PurchaseOrder.purchase_order_rid,
            PurchaseOrder.purchase_order_type,
            Order.order_rid,
            Shoe.shoe_rid,
            OrderShoe.customer_product_name,
            Material.material_name,
            Supplier.supplier_name,
        )
        .join(
            PurchaseDivideOrder,
            PurchaseDivideOrder.purchase_divide_order_id
            == PurchaseOrderItem.purchase_divide_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseOrder.purchase_order_id
            == PurchaseDivideOrder.purchase_order_id,
        )
        .outerjoin(Order, Order.order_id == PurchaseOrder.order_id)
        .outerjoin(OrderShoe, OrderShoe.order_shoe_id == PurchaseOrder.order_shoe_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .outerjoin(Material, Material.material_id == PurchaseOrderItem.material_id)
        .outerjoin(Supplier, Supplier.supplier_id == Material.material_supplier)
    )

    if order_rids:
        query = query.filter(Order.order_rid.in_(order_rids))

    rows = []
    for (
        item,
        purchase_order_rid,
        purchase_order_type,
        order_rid,
        shoe_rid,
        customer_product_name,
        material_name,
        supplier_name,
    ) in query.all():
        rows.append(
            {
                "item": item,
                "purchase_order_rid": purchase_order_rid,
                "purchase_type": _PURCHASE_TYPE_LABEL.get(
                    purchase_order_type, purchase_order_type or "?"
                ),
                "order_rid": order_rid or "",
                "shoe_rid": shoe_rid or "",
                "customer_product_name": customer_product_name or "",
                "material_name": material_name or "",
                "supplier_name": supplier_name or "",
            }
        )
    return rows


def _evaluate(rows, ratio, min_excess, min_approval, include_zero_approval):
    """筛出超采行，附上比值，按比值降序排序。"""
    ratio = Decimal(str(ratio))
    min_excess = Decimal(str(min_excess))
    min_approval = Decimal(str(min_approval))

    flagged = []
    for row in rows:
        item = row["item"]
        approval = _dec(item.approval_amount)
        effective = _effective_amount(item)

        if approval > 0:
            if approval < min_approval:
                continue
            excess = effective - approval
            if effective >= approval * ratio and excess >= min_excess:
                row["approval"] = approval
                row["effective"] = effective
                row["excess"] = excess
                row["ratio"] = effective / approval
                row["reason"] = "超采"
                flagged.append(row)
        else:
            # 无核定用量（核定为 0），却下了采购
            if include_zero_approval and effective > 0 and effective >= min_excess:
                row["approval"] = approval
                row["effective"] = effective
                row["excess"] = effective
                row["ratio"] = None  # 比值无穷大
                row["reason"] = "无核定却采购"
                flagged.append(row)

    # 无核定（ratio=None）的排在最前，其余按比值降序
    flagged.sort(
        key=lambda r: (r["ratio"] is not None, -(r["ratio"] or Decimal(0))),
    )
    return flagged


def _fmt_num(value) -> str:
    """去掉多余小数零，便于阅读。"""
    if value is None:
        return ""
    d = _dec(value)
    d = d.normalize()
    text = format(d, "f")
    return text


def _print_report(flagged, limit):
    if not flagged:
        print("未发现采购数量远大于核定用量的异常行。")
        return

    print(f"共发现 {len(flagged)} 条疑似超采记录：\n")

    shown = flagged if limit <= 0 else flagged[:limit]
    header = (
        f"{'订单号':<12} {'鞋型':<14} {'采购单号':<22} {'类型':<6} "
        f"{'材料名称':<22} {'核定':>10} {'采购':>10} {'倍数':>8}  原因"
    )
    print(header)
    print("-" * len(header))
    for row in shown:
        ratio_text = "∞" if row["ratio"] is None else f"{float(row['ratio']):.2f}x"
        print(
            f"{row['order_rid']:<12} {row['shoe_rid']:<14} "
            f"{row['purchase_order_rid']:<22} {row['purchase_type']:<6} "
            f"{row['material_name']:<22} "
            f"{_fmt_num(row['approval']):>10} {_fmt_num(row['effective']):>10} "
            f"{ratio_text:>8}  {row['reason']}"
        )

    if limit > 0 and len(flagged) > limit:
        print(f"\n… 仅显示前 {limit} 条，共 {len(flagged)} 条。使用 --limit 0 查看全部。")


def _export_csv(flagged, csv_path):
    fieldnames = [
        "order_rid",
        "shoe_rid",
        "customer_product_name",
        "purchase_order_rid",
        "purchase_type",
        "supplier_name",
        "material_name",
        "material_model",
        "material_specification",
        "color",
        "approval_amount",
        "effective_purchase_amount",
        "excess",
        "ratio",
        "reason",
        "purchase_order_item_id",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in flagged:
            item = row["item"]
            writer.writerow(
                {
                    "order_rid": row["order_rid"],
                    "shoe_rid": row["shoe_rid"],
                    "customer_product_name": row["customer_product_name"],
                    "purchase_order_rid": row["purchase_order_rid"],
                    "purchase_type": row["purchase_type"],
                    "supplier_name": row["supplier_name"],
                    "material_name": row["material_name"],
                    "material_model": item.material_model or "",
                    "material_specification": item.material_specification or "",
                    "color": item.color or "",
                    "approval_amount": _fmt_num(row["approval"]),
                    "effective_purchase_amount": _fmt_num(row["effective"]),
                    "excess": _fmt_num(row["excess"]),
                    "ratio": "" if row["ratio"] is None else f"{float(row['ratio']):.4f}",
                    "reason": row["reason"],
                    "purchase_order_item_id": item.purchase_order_item_id,
                }
            )
    print(f"\n已导出 {len(flagged)} 条记录到：{csv_path}")


def main():
    parser = argparse.ArgumentParser(
        description="检测采购订单采购数量远大于核定用量的异常行（只读）。"
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=3.0,
        help="判定「远大于」的倍数阈值：采购数量 >= 核定用量 * ratio 即标记（默认 3.0）。",
    )
    parser.add_argument(
        "--min-excess",
        type=float,
        default=0.0,
        help="最小绝对超出量（采购 - 核定）阈值，过滤数量很小的噪声行（默认 0）。",
    )
    parser.add_argument(
        "--min-approval",
        type=float,
        default=0.0,
        help="只检测核定用量 >= 该值的行（默认 0，即不限制）。",
    )
    parser.add_argument(
        "--orders",
        type=str,
        default="",
        help="仅检测指定订单号，逗号分隔，如 K24001,K24002。",
    )
    parser.add_argument(
        "--include-zero-approval",
        dest="include_zero_approval",
        action="store_true",
        default=True,
        help="包含「核定用量为 0 却有采购」的行（默认包含）。",
    )
    parser.add_argument(
        "--exclude-zero-approval",
        dest="include_zero_approval",
        action="store_false",
        help="排除「核定用量为 0 却有采购」的行。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="最多打印多少条（默认 50；设为 0 表示全部）。",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="把全部结果导出到指定 CSV 文件路径。",
    )
    args = parser.parse_args()

    order_rids = [r.strip() for r in args.orders.split(",") if r.strip()]

    app = create_app(ProductionConfig)
    with app.app_context():
        rows = _collect_rows(order_rids)
        flagged = _evaluate(
            rows,
            ratio=args.ratio,
            min_excess=args.min_excess,
            min_approval=args.min_approval,
            include_zero_approval=args.include_zero_approval,
        )

        print(
            f"扫描采购明细 {len(rows)} 条；阈值 ratio={args.ratio}, "
            f"min_excess={args.min_excess}, min_approval={args.min_approval}"
            + (f", 订单过滤={order_rids}" if order_rids else "")
            + "\n"
        )
        _print_report(flagged, args.limit)

        if args.csv and flagged:
            _export_csv(flagged, args.csv)


if __name__ == "__main__":
    main()
