# services/finished_outbound_export.py
# -*- coding: utf-8 -*-
import os
import io
from datetime import datetime
from decimal import Decimal

from openpyxl import load_workbook

from app_config import db
from models import (
    OrderShoe,
    OrderShoeBatchInfo,
    PackagingInfo,
    ShoeOutboundRecord,
    ShoeOutboundRecordDetail,
    FinishedShoeStorage,
    OrderShoeType,
    Order,
    Customer,
    Shoe,
    Color,
    ShoeType,
)


def generate_finished_outbound_excel(
    template_path: str,
    outbound_record_ids=None,
    outbound_rids=None,
):
    """
    生成成品出库的出货清单 Excel 文件（基于模板），
    按客户排序，并对相同客户行的【客户】列进行合并。

    :param template_path: 模板文件的绝对路径
    :param outbound_record_ids: 出库记录主键列表（list[int]）
    :param outbound_rids: 出库批次号列表（list[str]）
    :return: (BytesIO 对象, 下载文件名)
    :raises FileNotFoundError: 模板不存在
    :raises ValueError: 未找到记录
    """
    outbound_record_ids = outbound_record_ids or []
    outbound_rids = outbound_rids or []

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在: {template_path}")

    if not outbound_record_ids and not outbound_rids:
        raise ValueError("至少需要提供 outbound_record_ids 或 outbound_rids 之一")

    # ========= 查询数据 =========
    query = (
        db.session.query(
            ShoeOutboundRecord,
            ShoeOutboundRecordDetail,
            FinishedShoeStorage,
            OrderShoeType,
            OrderShoe,
            Order,
            Customer,
            Shoe,
            Color,
        )
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.shoe_outbound_record_id == ShoeOutboundRecord.shoe_outbound_record_id,
        )
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id == ShoeOutboundRecordDetail.finished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        # ⚠️ 这里原来是 Order.order_id == OrderShoeType.order_shoe_id，应该是 order_id == OrderShoe.order_id
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
    )

    if outbound_record_ids:
        query = query.filter(ShoeOutboundRecord.shoe_outbound_record_id.in_(outbound_record_ids))

    if outbound_rids:
        query = query.filter(ShoeOutboundRecord.shoe_outbound_rid.in_(outbound_rids))

    rows = query.all()
    if not rows:
        raise ValueError("未找到对应的出库记录")

    # ========= 先组装成“干净”的记录列表，方便排序 =========
    record_list = []
    for (
        outbound,      # ShoeOutboundRecord
        detail,        # ShoeOutboundRecordDetail
        finished,      # FinishedShoeStorage
        ost,           # OrderShoeType
        oss,           # OrderShoe
        order,         # Order
        customer,      # Customer
        shoe,          # Shoe
        color,         # Color
    ) in rows:

        # 客户
        customer_name = getattr(customer, "customer_brand", None) or getattr(customer, "customer_name", "")

        # 发货时间（出库时间）
        if outbound.outbound_datetime:
            ship_date = outbound.outbound_datetime.strftime("%Y-%m-%d")
        else:
            ship_date = ""

        # 型体号（通常是客户型号）
        style_no_customer = getattr(oss, "customer_product_name", None) or getattr(oss, "customer_shoe_type", "")

        # 颜色
        color_name = getattr(color, "color_name", None) or getattr(ost, "color_name", "")

        # 工厂型号
        factory_style_no = getattr(shoe, "shoe_rid", None) or getattr(ost, "shoe_rid", "")

        # 发货数量（双）
        if detail.outbound_amount:
            qty_pairs = detail.outbound_amount
        else:
            qty_pairs = (
                (detail.size_34_amount or 0) +
                (detail.size_35_amount or 0) +
                (detail.size_36_amount or 0) +
                (detail.size_37_amount or 0) +
                (detail.size_38_amount or 0) +
                (detail.size_39_amount or 0) +
                (detail.size_40_amount or 0) +
                (detail.size_41_amount or 0) +
                (detail.size_42_amount or 0) +
                (detail.size_43_amount or 0) +
                (detail.size_44_amount or 0) +
                (detail.size_45_amount or 0) +
                (detail.size_46_amount or 0)
            )

        # 单价
        unit_price: Decimal = ost.unit_price or Decimal("0.000")

        # 发货金额 = 数量 * 单价
        amount: Decimal = (Decimal(qty_pairs) * unit_price).quantize(Decimal("0.01"))

        # 工厂名：视业务调整
        factory_name = "浙江健诚鞋业集团有限公司"

        record_list.append(
            {
                "customer_name": customer_name,
                "ship_date": ship_date,
                "style_no_customer": style_no_customer,
                "color_name": color_name,
                "factory_style_no": factory_style_no,
                "qty_pairs": qty_pairs,
                "unit_price": unit_price,
                "amount": amount,
                "factory_name": factory_name,
            }
        )

    # ========= 对相同客户排序（必要时可加多字段） =========
    # 按：客户 -> 发货时间 -> 工厂型号 -> 颜色 -> 型体号 排序
    record_list.sort(
        key=lambda r: (
            r["customer_name"] or "",
            r["ship_date"] or "",
            r["factory_style_no"] or "",
            r["color_name"] or "",
            r["style_no_customer"] or "",
        )
    )

    # ========= 加载模板 =========
    wb = load_workbook(template_path)
    ws = wb["出货单"]  # 模板中的 sheet 名

    # 表头在第 2 行，数据从第 3 行开始
    start_row = 3

    # 1）先计算每个客户的起止行（在 sheet 中的行号）
    groups = []  # [(customer_name, start_row, end_row), ...]
    prev_customer = None
    group_start = None

    for idx, rec in enumerate(record_list):
        customer_name = rec["customer_name"]
        if customer_name != prev_customer:
            # 关闭上一组
            if prev_customer is not None:
                groups.append((prev_customer,
                               start_row + group_start,
                               start_row + idx - 1))
            # 新开一组
            prev_customer = customer_name
            group_start = idx

    # 别忘了最后一组
    if prev_customer is not None and group_start is not None:
        groups.append((prev_customer,
                       start_row + group_start,
                       start_row + len(record_list) - 1))

    # 2）写入数据：只在组首行写客户名，其它行不写客户列
    for offset, rec in enumerate(record_list):
        row_idx = start_row + offset

        customer_name = rec["customer_name"]
        ship_date = rec["ship_date"]
        style_no_customer = rec["style_no_customer"]
        color_name = rec["color_name"]
        factory_style_no = rec["factory_style_no"]
        qty_pairs = rec["qty_pairs"]
        unit_price = rec["unit_price"]
        amount = rec["amount"]
        factory_name = rec["factory_name"]

        # 判断当前行是不是该客户分组的起始行
        is_group_start = False
        for cname, g_start, g_end in groups:
            if cname == customer_name and g_start == row_idx:
                is_group_start = True
                break

        # 只有组首行写客户名
        if is_group_start:
            ws.cell(row=row_idx, column=1, value=customer_name)

        ws.cell(row=row_idx, column=2, value=ship_date)          # 发货时间
        ws.cell(row=row_idx, column=3, value=style_no_customer)  # 型体号
        ws.cell(row=row_idx, column=4, value=color_name)         # 颜色
        ws.cell(row=row_idx, column=5, value=factory_style_no)   # 工厂型号
        ws.cell(row=row_idx, column=6, value=qty_pairs)          # 发货数量（双）
        ws.cell(row=row_idx, column=7, value=float(unit_price))  # 单价
        ws.cell(row=row_idx, column=8, value=float(amount))      # 发货金额
        ws.cell(row=row_idx, column=9, value=factory_name)       # 工厂

    # 3）统一合并客户列（第 1 列）
    from openpyxl.utils import get_column_letter
    col = 1  # 客户列
    for cname, g_start, g_end in groups:
        if g_start < g_end:
            ws.merge_cells(
                start_row=g_start, start_column=col,
                end_row=g_end, end_column=col
            )

    # ========= 保存到内存并返回 =========
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"出货清单_{now_str}.xlsx"

    return output, filename
