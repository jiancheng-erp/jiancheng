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
    FinishedShoeStorage,
    OrderShoeType,
    Order,
    Customer,
    Shoe,
    Color,
    ShoeType,
    ShoeOutboundApply,
    ShoeOutboundApplyDetail,
)


def generate_finished_outbound_excel(
    template_path: str,
    outbound_record_ids=None,
    outbound_rids=None,
):
    """
    生成成品出库《出货清单》Excel（基于最新模板）：
    - 列：客户 / 商标 / 预计发货时间 / 实际发货时间 / 型体号 / 颜色 / 工厂型号 / 配码
           发货数量（双）/ 对/件 / 件数 / 单价 / 发货金额
    - 按客户排序，并对相同客户的【客户】列做合并
    - 粒度：一条 ShoeOutboundApplyDetail = Excel 表中一行
      （同一个 apply_id 下有多条 detail，会全部列出）
    - 说明：不再依赖出库明细（ShoeOutboundRecordDetail），
      只用出库记录选择 apply，再按申请明细展开。
    """
    outbound_record_ids = outbound_record_ids or []
    outbound_rids = outbound_rids or []

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在: {template_path}")

    if not outbound_record_ids and not outbound_rids:
        raise ValueError("至少需要提供 outbound_record_ids 或 outbound_rids 之一")

    # ========= 先筛出需要的出库记录 =========
    q_record = db.session.query(ShoeOutboundRecord)

    if outbound_record_ids:
        q_record = q_record.filter(
            ShoeOutboundRecord.shoe_outbound_record_id.in_(outbound_record_ids)
        )

    if outbound_rids:
        q_record = q_record.filter(
            ShoeOutboundRecord.shoe_outbound_rid.in_(outbound_rids)
        )

    records = q_record.all()
    if not records:
        raise ValueError("未找到对应的出库记录")

    # 拿到涉及到的 apply_id 列表（排除为 None 的）
    apply_ids = {r.apply_id for r in records if r.apply_id}
    if not apply_ids:
        raise ValueError("这些出库记录没有关联任何申请单（apply_id 为空）")

    # ========= 按申请明细为粒度查询 =========
    query = (
        db.session.query(
            ShoeOutboundRecord,      # 0 出库头，用于拿出库时间
            ShoeOutboundApply,       # 1 申请头
            ShoeOutboundApplyDetail, # 2 申请明细（一行）
            FinishedShoeStorage,     # 3 成品仓
            OrderShoeType,           # 4 订单鞋型
            OrderShoe,               # 5 订单鞋款
            Order,                   # 6 订单
            Customer,                # 7 客户
            Shoe,                    # 8 鞋（工厂型号）
            ShoeType,                # 9 鞋型（含 color_id）
            Color,                   # 10 颜色
            OrderShoeBatchInfo,      # 11 配码
            PackagingInfo,           # 12 包装方案
        )
        # 从出库头开始，确保数据范围受 outbound_record_ids / rids 控制
        .join(
            ShoeOutboundApply,
            ShoeOutboundApply.apply_id == ShoeOutboundRecord.apply_id,
        )
        .join(
            ShoeOutboundApplyDetail,
            ShoeOutboundApplyDetail.apply_id == ShoeOutboundApply.apply_id,
        )
        .outerjoin(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id
            == ShoeOutboundApplyDetail.finished_shoe_storage_id,
        )
        .outerjoin(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id
            == ShoeOutboundApplyDetail.order_shoe_type_id,
        )
        .outerjoin(
            OrderShoe,
            OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id,
        )
        .outerjoin(
            Order,
            Order.order_id == OrderShoe.order_id,
        )
        .outerjoin(
            Customer,
            Customer.customer_id == Order.customer_id,
        )
        .outerjoin(
            ShoeType,
            ShoeType.shoe_type_id == OrderShoeType.shoe_type_id,
        )
        .outerjoin(
            Shoe,
            Shoe.shoe_id == ShoeType.shoe_id,
        )
        .outerjoin(
            Color,
            Color.color_id == ShoeType.color_id,
        )
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_batch_info_id
            == ShoeOutboundApplyDetail.order_shoe_batch_info_id,
        )
        .outerjoin(
            PackagingInfo,
            PackagingInfo.packaging_info_id == ShoeOutboundApplyDetail.packaging_info_id,
        )
        .filter(ShoeOutboundApply.apply_id.in_(apply_ids))
    )

    # 再把 record 过滤条件带进来，避免一个 apply 被多次导出（理论上 1:1，这里保险起见）
    if outbound_record_ids:
        query = query.filter(
            ShoeOutboundRecord.shoe_outbound_record_id.in_(outbound_record_ids)
        )
    if outbound_rids:
        query = query.filter(
            ShoeOutboundRecord.shoe_outbound_rid.in_(outbound_rids)
        )

    rows = query.all()
    if not rows:
        raise ValueError("未找到对应的申请明细记录")

    # ========= 整理为“干净记录”列表 =========
    record_list = []

    for (
        outbound,      # ShoeOutboundRecord
        apply_obj,     # ShoeOutboundApply
        apply_detail,  # ShoeOutboundApplyDetail
        finished,      # FinishedShoeStorage | None
        ost,           # OrderShoeType | None
        oss,           # OrderShoe | None
        order,         # Order | None
        customer,      # Customer | None
        shoe,          # Shoe | None
        shoe_type,     # ShoeType | None
        color,         # Color | None
        batch_info,    # OrderShoeBatchInfo | None
        pkg,           # PackagingInfo | None
    ) in rows:
        # ======== 客户 & 商标 ========
        customer_name = getattr(customer, "customer_name", "") or ""
        customer_brand = getattr(customer, "customer_brand", "") or ""

        # ======== 预计 / 实际发货时间 ========
        expected_dt = None
        if apply_obj and apply_obj.expected_outbound_datetime:
            expected_dt = apply_obj.expected_outbound_datetime

        # 实际发货时间：优先用申请里的 actual_outbound_datetime，没有就用出库记录上的时间
        actual_dt = None
        if apply_obj and apply_obj.actual_outbound_datetime:
            actual_dt = apply_obj.actual_outbound_datetime
        elif outbound and outbound.outbound_datetime:
            actual_dt = outbound.outbound_datetime

        expected_date_str = expected_dt.strftime("%Y-%m-%d") if expected_dt else ""
        actual_date_str = actual_dt.strftime("%Y-%m-%d") if actual_dt else ""

        # ======== 型体号（客户型号） & 颜色 & 工厂型号 & 配码 ========
        style_no_customer = ""
        if oss:
            style_no_customer = (
                getattr(oss, "customer_product_name", None)
                or getattr(oss, "customer_shoe_type", "")
                or ""
            )
        color_name = getattr(color, "color_name", "") or ""
        factory_style_no = getattr(shoe, "shoe_rid", "") or ""
        batch_name = getattr(batch_info, "name", "") if batch_info else ""

        # ======== 对/件 & 件数（箱数可为小数） ========
        pairs_per_carton = None
        carton_count = None
        if apply_detail:
            if apply_detail.pairs_per_carton is not None:
                pairs_per_carton = int(apply_detail.pairs_per_carton or 0)
            if apply_detail.carton_count is not None:
                carton_count = float(apply_detail.carton_count)

        # ======== 发货数量（双） ========
        # 业务规则：最后双数必须为整数
        # 优先用申请明细里的 total_pairs，其次 carton_count * pairs_per_carton
        qty_pairs = 0
        if apply_detail and apply_detail.total_pairs:
            qty_pairs = int(apply_detail.total_pairs or 0)
        elif pairs_per_carton is not None and carton_count is not None:
            qty_pairs = int(round(pairs_per_carton * carton_count))

        # ======== 单价 & 发货金额 ========
        unit_price = Decimal("0.000")
        if ost and ost.unit_price is not None:
            unit_price = ost.unit_price
        amount: Decimal = (Decimal(qty_pairs) * unit_price).quantize(Decimal("0.01"))

        # 工厂名（如果模板有这一列，可以使用；目前保留字段）
        factory_name = "浙江健诚鞋业集团有限公司"

        record_list.append(
            {
                "customer_name": customer_name,
                "customer_brand": customer_brand,
                "expected_date": expected_date_str,
                "actual_date": actual_date_str,
                "style_no_customer": style_no_customer,
                "color_name": color_name,
                "factory_style_no": factory_style_no,
                "batch_name": batch_name,
                "qty_pairs": qty_pairs,
                "pairs_per_carton": pairs_per_carton,
                "carton_count": carton_count,
                "unit_price": unit_price,
                "amount": amount,
                "factory_name": factory_name,
            }
        )

    # ========= 排序：客户 -> 商标 -> 实际发货时间 -> 工厂型号 -> 颜色 -> 型体号 -> 配码 =========
    record_list.sort(
        key=lambda r: (
            r["customer_name"] or "",
            r["customer_brand"] or "",
            r["actual_date"] or "",
            r["factory_style_no"] or "",
            r["color_name"] or "",
            r["style_no_customer"] or "",
            r["batch_name"] or "",
        )
    )

    # ========= 加载模板 =========
    wb = load_workbook(template_path)
    ws = wb["出货单"]  # 模板中的 sheet 名

    # 模板第 2 行是表头，数据从第 3 行开始
    start_row = 3

    # 1）计算每个客户在 sheet 中的起止行（用于合并“客户”列）
    groups = []  # [(customer_name, start_row, end_row), ...]
    prev_customer = None
    group_start_idx = None

    for idx, rec in enumerate(record_list):
        cname = rec["customer_name"]
        if cname != prev_customer:
            if prev_customer is not None and group_start_idx is not None:
                groups.append(
                    (
                        prev_customer,
                        start_row + group_start_idx,
                        start_row + idx - 1,
                    )
                )
            prev_customer = cname
            group_start_idx = idx

    if prev_customer is not None and group_start_idx is not None:
        groups.append(
            (
                prev_customer,
                start_row + group_start_idx,
                start_row + len(record_list) - 1,
            )
        )

    # 2）写入数据（列号基于最新模板）：
    #   A: 客户
    #   B: 商标
    #   C: 预计发货时间
    #   D: 实际发货时间
    #   E: 型体号
    #   F: 颜色
    #   G: 工厂型号
    #   H: 配码
    #   I: 发货数量（双）
    #   J: 对/件
    #   K: 件数
    #   L: 单价
    #   M: 发货金额
    for offset, rec in enumerate(record_list):
        row_idx = start_row + offset

        cname = rec["customer_name"]
        brand = rec["customer_brand"]
        expected_date = rec["expected_date"]
        actual_date = rec["actual_date"]
        style_no_customer = rec["style_no_customer"]
        color_name = rec["color_name"]
        factory_style_no = rec["factory_style_no"]
        batch_name = rec["batch_name"]
        qty_pairs = rec["qty_pairs"]
        pairs_per_carton = rec["pairs_per_carton"]
        carton_count = rec["carton_count"]
        unit_price = rec["unit_price"]
        amount = rec["amount"]

        # 判断当前行是否是该客户分组起始行
        is_group_start = False
        for gcname, g_start, g_end in groups:
            if gcname == cname and g_start == row_idx:
                is_group_start = True
                break

        if is_group_start:
            ws.cell(row=row_idx, column=1, value=cname)
        ws.cell(row=row_idx, column=2, value=brand)

        ws.cell(row=row_idx, column=3, value=expected_date)
        ws.cell(row=row_idx, column=4, value=actual_date)
        ws.cell(row=row_idx, column=5, value=style_no_customer)
        ws.cell(row=row_idx, column=6, value=color_name)
        ws.cell(row=row_idx, column=7, value=factory_style_no)
        ws.cell(row=row_idx, column=8, value=batch_name)
        ws.cell(row=row_idx, column=9, value=qty_pairs)

        if pairs_per_carton is not None:
            ws.cell(row=row_idx, column=10, value=int(pairs_per_carton))
        if carton_count is not None:
            ws.cell(row=row_idx, column=11, value=float(carton_count))

        ws.cell(row=row_idx, column=12, value=float(unit_price))
        ws.cell(row=row_idx, column=13, value=float(amount))

    # 3）统一合并“客户”列（第 1 列）
    for cname, g_start, g_end in groups:
        if g_start < g_end:
            ws.merge_cells(
                start_row=g_start,
                start_column=1,
                end_row=g_end,
                end_column=1,
            )

    # ========= 输出到内存 =========
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"出货清单_{now_str}.xlsx"

    return output, filename
