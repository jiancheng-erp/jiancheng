from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from app_config import db
from models import (
    ShoeOutboundRecord,
    ShoeOutboundRecordDetail,
    ShoeOutboundApply,
    ShoeOutboundApplyDetail,
    FinishedShoeStorage,
    OrderShoeType,
    OrderShoe,
    Order,
    OrderShoeBatchInfo,
    PackagingInfo,
)
from sqlalchemy import or_, func


def _generate_apply_rid_from_record(record: ShoeOutboundRecord) -> str:
    """
    给历史出库单生成一个申请单号：
    可以用原 shoe_outbound_rid 做前缀，防止冲突。
    """
    base = (record.shoe_outbound_rid or "FORUNKNOWN").replace(" ", "").replace(":", "").replace("-", "")
    return f"SOA_BACKFILL_{base}"[:40]  # 最长 40 字符


def _get_order_id_for_detail(detail: ShoeOutboundRecordDetail) -> int | None:
    """
    通过 finished_shoe_storage_id -> FinishedShoeStorage -> OrderShoeType -> OrderShoe -> Order
    反推订单 id。
    """
    if not detail.finished_shoe_storage_id:
        return None

    storage: FinishedShoeStorage = FinishedShoeStorage.query.get(detail.finished_shoe_storage_id)
    if not storage:
        return None

    ost: OrderShoeType = OrderShoeType.query.get(storage.order_shoe_type_id)
    if not ost:
        return None

    os: OrderShoe = OrderShoe.query.get(ost.order_shoe_id)
    if not os:
        return None

    return os.order_id


def _pick_batch_for_order_shoe_type(order_shoe_type_id: int):
    """
    根据 order_shoe_type_id 选一条“主配码”记录：
    - 如果只有 1 条配码，直接用；
    - 多条配码：暂时按 order_shoe_batch_info_id 升序取第一条。
      （后续如果你想按数量、名称等更细的逻辑再调整）
    返回 (batch_info, packaging_info) 或 (None, None)
    """
    if not order_shoe_type_id:
        return None, None

    batch_list: list[OrderShoeBatchInfo] = (
        OrderShoeBatchInfo.query
        .filter_by(order_shoe_type_id=order_shoe_type_id)
        .order_by(OrderShoeBatchInfo.order_shoe_batch_info_id.asc())
        .all()
    )
    if not batch_list:
        return None, None

    batch = batch_list[0]   # 简单起见，取第一条
    pkg = None
    if batch.packaging_info_id:
        pkg = PackagingInfo.query.get(batch.packaging_info_id)

    return batch, pkg


def backfill_outbound_apply_from_records(
    app,
    default_business_staff_id: int,
    default_warehouse_staff_id: int | None = None,
    default_gm_staff_id: int | None = None,
    dry_run: bool = True,
):
    """
    从历史的 ShoeOutboundRecord / Detail 自动补一张 ShoeOutboundApply / Detail：

    - 只处理没有 apply_id 的出库记录；
    - 每张出库单 => 一张申请单（状态 = 4 已完成出库）；
    - 明细 total_pairs = outbound_amount（整数，保持你的约束）；
    - carton_count 允许为小数：
        * 如果能找到配码 & 包装方案，则 carton_count = total_pairs / pairs_per_carton (保留 2 位小数)
        * 否则 carton_count = 0, pairs_per_carton = 0
    - 尽量补上：
        * order_shoe_batch_info_id
        * packaging_info_id
    """
    with app.app_context():
        q = (
            db.session.query(ShoeOutboundRecord)
            .filter(
                or_(
                    ShoeOutboundRecord.apply_id == None,
                    ShoeOutboundRecord.apply_id == 0,
                ),
                ShoeOutboundRecord.shoe_outbound_rid.like("%FOR%"),
            )
            .order_by(ShoeOutboundRecord.shoe_outbound_record_id)
        )

        records = q.all()
        print(f"找到需要补录申请单的出库记录: {len(records)} 条")

        created_apply_count = 0
        created_detail_count = 0

        for record in records:
            details = (
                ShoeOutboundRecordDetail.query
                .filter_by(shoe_outbound_record_id=record.shoe_outbound_record_id)
                .all()
            )
            if not details:
                print(f"出库记录 {record.shoe_outbound_record_id} 无明细，跳过")
                continue

            # 找出这张出库单涉及到的所有订单
            order_ids = set()
            for d in details:
                oid = _get_order_id_for_detail(d)
                if oid:
                    order_ids.add(oid)

            if not order_ids:
                print(f"出库记录 {record.shoe_outbound_record_id} 无法识别所属订单，跳过")
                continue

            # 选一个“主订单”填到 apply.order_id（目前字段非空，只能选一个）
            main_order_id = min(order_ids)

            # 校验主订单存在
            main_order = Order.query.get(main_order_id)
            if not main_order:
                print(f"主订单 {main_order_id} 不存在，跳过记录 {record.shoe_outbound_record_id}")
                continue

            apply_rid = _generate_apply_rid_from_record(record)
            print(
                f"为出库记录 {record.shoe_outbound_record_id} 创建申请单 {apply_rid}，"
                f"主订单 {main_order_id}，涉及订单 {order_ids}"
            )

            outbound_dt = record.outbound_datetime or datetime.now()

            apply_obj = ShoeOutboundApply(
                apply_rid=apply_rid,
                order_id=main_order_id,
                business_staff_id=default_business_staff_id,
                gm_staff_id=default_gm_staff_id,
                warehouse_staff_id=default_warehouse_staff_id,
                status=4,  # 已完成出库
                remark=(record.remark or "") + "\n[系统补录申请单]",
                expected_outbound_datetime=outbound_dt,
                actual_outbound_datetime=outbound_dt,
                outbound_record_id=record.shoe_outbound_record_id,
            )
            db.session.add(apply_obj)
            db.session.flush()  # 拿 apply_id

            # 生成明细
            for d in details:
                storage: FinishedShoeStorage | None = None
                if d.finished_shoe_storage_id:
                    storage = FinishedShoeStorage.query.get(d.finished_shoe_storage_id)

                # 反推 order_shoe_type_id（从 storage 中拿，detail 里没有字段）
                order_shoe_type_id = None
                if storage:
                    order_shoe_type_id = storage.order_shoe_type_id

                if not storage or not order_shoe_type_id:
                    print(
                        f"  - 明细 {d.record_detail_id} 无法关联成品仓记录或鞋型，跳过该明细"
                    )
                    continue

                total_pairs = int(d.outbound_amount or 0)
                if total_pairs <= 0:
                    print(
                        f"  - 明细 {d.record_detail_id} 出库双数为 0，跳过该明细"
                    )
                    continue

                # ====== 核心：根据 order_shoe_type_id 找配码 + 包装方案 ======
                batch_info, pkg = _pick_batch_for_order_shoe_type(order_shoe_type_id)

                order_shoe_batch_info_id = batch_info.order_shoe_batch_info_id if batch_info else None
                packaging_info_id = batch_info.packaging_info_id if batch_info else None

                # pairs_per_carton：优先用包装方案的 total_quantity_ratio
                pairs_per_carton = 0
                if pkg and getattr(pkg, "total_quantity_ratio", None):
                    pairs_per_carton = int(pkg.total_quantity_ratio or 0)

                # carton_count 允许为小数，但 total_pairs 必须是整数
                carton_count_dec = Decimal("0.00")
                if pairs_per_carton and pairs_per_carton > 0:
                    carton_count_dec = (Decimal(total_pairs) / Decimal(pairs_per_carton)).quantize(
                        Decimal("0.00"), rounding=ROUND_HALF_UP
                    )

                if not batch_info:
                    print(
                        f"  - 明细 {d.record_detail_id} 找不到配码信息，只能补 total_pairs，"
                        f"carton_count=0, pairs_per_carton=0"
                    )

                detail_obj = ShoeOutboundApplyDetail(
                    apply_id=apply_obj.apply_id,
                    finished_shoe_storage_id=storage.finished_shoe_id,
                    order_shoe_type_id=order_shoe_type_id,
                    order_shoe_batch_info_id=order_shoe_batch_info_id,
                    packaging_info_id=packaging_info_id,

                    carton_count=carton_count_dec,   # DECIMAL(10,2)
                    pairs_per_carton=pairs_per_carton,
                    total_pairs=total_pairs,          # 保持整数

                    remark=(d.remark or "") + " [历史出库明细补录]",
                )
                db.session.add(detail_obj)
                created_detail_count += 1

            # 出库记录反向关联申请单
            record.apply_id = apply_obj.apply_id

            created_apply_count += 1

        if dry_run:
            print(
                f"[Dry Run] 计划创建申请单 {created_apply_count} 条，"
                f"明细 {created_detail_count} 条，不提交数据库"
            )
            db.session.rollback()
        else:
            db.session.commit()
            print(
                f"[OK] 已创建申请单 {created_apply_count} 条，"
                f"明细 {created_detail_count} 条"
            )
