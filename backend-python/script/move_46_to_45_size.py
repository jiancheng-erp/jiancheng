from collections import defaultdict
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import json

from models import (
    PackagingInfo,
    OrderShoeBatchInfo,
    BatchInfoType,
    Order,
    OrderShoe,
    OrderShoeType,
    Bom,
    BomItem,
    PurchaseOrderItem,
    SizeMaterialStorage,
    OrderShoeProductionAmount,
    FinishedShoeStorage,
    SemifinishedShoeStorage,
    InboundRecordDetail
)

def fix_us_male_size_data(app, db):
    check_log = []

    def log_change(table, row_id, field, before, after):
        if before != after:
            check_log.append({
                "table": table,
                "id": row_id,
                "field": field,
                "before": before,
                "after": after
            })

    with app.app_context():
        # Step 1: PackagingInfo
        packaging_infos = PackagingInfo.query.filter_by(packaging_info_locale="US男").all()
        packaging_ids = []
        for p in packaging_infos:
            if p.size_46_ratio is not None:
                log_change("PackagingInfo", p.packaging_info_id, "size_45_ratio", p.size_45_ratio, p.size_46_ratio)
                log_change("PackagingInfo", p.packaging_info_id, "size_46_ratio", p.size_46_ratio, 0)
                p.size_45_ratio = p.size_46_ratio
                p.size_46_ratio = 0
                print(f"[PackagingInfo] ID {p.packaging_info_id}: 46→45")
            packaging_ids.append(p.packaging_info_id)

        # Step 2: OrderShoeBatchInfo
        batches = OrderShoeBatchInfo.query.filter(
            OrderShoeBatchInfo.packaging_info_id.in_(packaging_ids)
        ).all()
        for b in batches:
            if b.size_46_amount is not None:
                log_change("OrderShoeBatchInfo", b.order_shoe_batch_info_id, "size_45_amount", b.size_45_amount, b.size_46_amount)
                log_change("OrderShoeBatchInfo", b.order_shoe_batch_info_id, "size_46_amount", b.size_46_amount, 0)
                b.size_45_amount = b.size_46_amount
                b.size_46_amount = 0
                print(f"[BatchInfo] ID {b.order_shoe_batch_info_id}: 46→45")

        # Step 3: Order.order_size_table
        us_batch_ids = [
            b.batch_info_type_id for b in BatchInfoType.query.filter_by(batch_info_type_name="US男").all()
        ]
        orders = Order.query.filter(Order.batch_info_type_id.in_(us_batch_ids)).all()
        bom_item_ids_to_update = []

        for order in orders:
            if order.order_size_table:
                try:
                    size_data = json.loads(order.order_size_table)
                    original_data = json.loads(order.order_size_table)
                    changed = False
                    for k, v in size_data.items():
                        if isinstance(v, list):
                            if "12.5" in v:
                                v.remove("12.5")
                                changed = True
                                if "14" not in v:
                                    v.append("14")
                                    changed = True
                    if changed:
                        log_change("Order", order.order_id, "order_size_table", original_data, size_data)
                        order.order_size_table = json.dumps(size_data, ensure_ascii=False)
                        print(f"[OrderSizeTable] Order {order.order_id} modified.")
                except json.JSONDecodeError:
                    print(f"[OrderSizeTable] Invalid JSON in Order {order.order_id}")

        # Step 4: BomItem
        for order in orders:
            shoes = OrderShoe.query.filter_by(order_id=order.order_id).all()
            for shoe in shoes:
                types = OrderShoeType.query.filter_by(order_shoe_id=shoe.order_shoe_id).all()
                for t in types:
                    boms = Bom.query.filter_by(order_shoe_type_id=t.order_shoe_type_id).all()
                    for bom in boms:
                        bom_items = BomItem.query.filter_by(bom_id=bom.bom_id).all()
                        for item in bom_items:
                            if item.size_46_total_usage is not None:
                                log_change("BomItem", item.bom_item_id, "size_45_total_usage", item.size_45_total_usage, item.size_46_total_usage)
                                log_change("BomItem", item.bom_item_id, "size_46_total_usage", item.size_46_total_usage, 0)
                                item.size_45_total_usage = item.size_46_total_usage
                                item.size_46_total_usage = 0
                                print(f"[BomItem] ID {item.bom_item_id}: 46→45")
                            bom_item_ids_to_update.append(item.bom_item_id)

                    # Step 7: OrderShoeProductionAmount
                    prod_amounts = OrderShoeProductionAmount.query.filter_by(order_shoe_type_id=t.order_shoe_type_id).all()
                    for pa in prod_amounts:
                        if pa.size_46_production_amount is not None:
                            log_change("OrderShoeProductionAmount", pa.order_shoe_production_amount_id, "size_45_production_amount", pa.size_45_production_amount, pa.size_46_production_amount)
                            log_change("OrderShoeProductionAmount", pa.order_shoe_production_amount_id, "size_46_production_amount", pa.size_46_production_amount, 0)
                            pa.size_45_production_amount = pa.size_46_production_amount
                            pa.size_46_production_amount = 0

                    # Step 8: Finished & Semifinished Shoe Storage
                    for StorageModel, name, id_field in [
                        (FinishedShoeStorage, "FinishedShoeStorage", "finished_shoe_id"),
                        (SemifinishedShoeStorage, "SemifinishedShoeStorage", "semifinished_shoe_id")
                    ]:
                        storages = StorageModel.query.filter_by(order_shoe_type_id=t.order_shoe_type_id).all()
                        for s in storages:
                            sid = getattr(s, id_field)
                            if s.size_46_actual_amount is not None:
                                log_change(name, sid, "size_45_actual_amount", s.size_45_actual_amount, s.size_46_actual_amount)
                                log_change(name, sid, "size_46_actual_amount", s.size_46_actual_amount, 0)
                                s.size_45_actual_amount = s.size_46_actual_amount
                                s.size_46_actual_amount = 0
                            if s.size_46_estimated_amount is not None:
                                log_change(name, sid, "size_45_estimated_amount", s.size_45_estimated_amount, s.size_46_estimated_amount)
                                log_change(name, sid, "size_46_estimated_amount", s.size_46_estimated_amount, 0)
                                s.size_45_estimated_amount = s.size_46_estimated_amount
                                s.size_46_estimated_amount = 0
                            if s.size_46_amount is not None:
                                log_change(name, sid, "size_45_amount", s.size_45_amount, s.size_46_amount)
                                log_change(name, sid, "size_46_amount", s.size_46_amount, 0)
                                s.size_45_amount = s.size_46_amount
                                s.size_46_amount = 0

        # Step 5: PurchaseOrderItem
        if bom_item_ids_to_update:
            pois = PurchaseOrderItem.query.filter(
                PurchaseOrderItem.bom_item_id.in_(bom_item_ids_to_update)
            ).all()
            for po in pois:
                if po.size_46_purchase_amount is not None:
                    log_change("PurchaseOrderItem", po.purchase_order_item_id, "size_45_purchase_amount", po.size_45_purchase_amount, po.size_46_purchase_amount)
                    log_change("PurchaseOrderItem", po.purchase_order_item_id, "size_46_purchase_amount", po.size_46_purchase_amount, 0)
                    po.size_45_purchase_amount = po.size_46_purchase_amount
                    po.size_46_purchase_amount = 0
                    print(f"[POItem] ID {po.purchase_order_item_id}: 46→45")

        # Step 6: SizeMaterialStorage
        sms_entries = SizeMaterialStorage.query.filter_by(size_storage_type="US男").all()
        for s in sms_entries:
            sid = s.size_material_storage_id
            modified = False

            if s.size_46_estimated_inbound_amount is not None:
                log_change("SizeMaterialStorage", sid, "size_45_estimated_inbound_amount", s.size_45_estimated_inbound_amount, s.size_46_estimated_inbound_amount)
                log_change("SizeMaterialStorage", sid, "size_46_estimated_inbound_amount", s.size_46_estimated_inbound_amount, 0)
                s.size_45_estimated_inbound_amount = s.size_46_estimated_inbound_amount
                s.size_46_estimated_inbound_amount = 0
                modified = True

            if s.size_46_actual_inbound_amount is not None:
                log_change("SizeMaterialStorage", sid, "size_45_actual_inbound_amount", s.size_45_actual_inbound_amount, s.size_46_actual_inbound_amount)
                log_change("SizeMaterialStorage", sid, "size_46_actual_inbound_amount", s.size_46_actual_inbound_amount, 0)
                s.size_45_actual_inbound_amount = s.size_46_actual_inbound_amount
                s.size_46_actual_inbound_amount = 0
                modified = True

            if s.size_46_current_amount is not None:
                log_change("SizeMaterialStorage", sid, "size_45_current_amount", s.size_45_current_amount, s.size_46_current_amount)
                log_change("SizeMaterialStorage", sid, "size_46_current_amount", s.size_46_current_amount, 0)
                s.size_45_current_amount = s.size_46_current_amount
                s.size_46_current_amount = 0
                modified = True

            if s.shoe_size_columns:
                try:
                    col = s.shoe_size_columns
                    if isinstance(col, str):
                        col = json.loads(col)
                    if isinstance(col, list):
                        original = list(col)
                        if "12.5" in col:
                            col.remove("12.5")
                            if "14" not in col:
                                col.append("14")
                        if original != col:
                            log_change("SizeMaterialStorage", sid, "shoe_size_columns", original, col)
                            s.shoe_size_columns = json.dumps(col, ensure_ascii=False)
                            modified = True
                except Exception as e:
                    print(f"[SMS] ID {sid}: Error handling shoe_size_columns: {e}")

            if modified:
                print(f"[SMS] ID {sid}: updated.")

        # Step 9: InboundRecordDetail
        records = InboundRecordDetail.query.join(SizeMaterialStorage, InboundRecordDetail.size_material_storage_id == SizeMaterialStorage.size_material_storage_id).filter(
            SizeMaterialStorage.size_storage_type == "US男"
        ).all()
        for r in records:
            if r.size_46_inbound_amount is not None:
                log_change("InboundRecordDetail", r.id, "size_45_inbound_amount", r.size_45_inbound_amount, r.size_46_inbound_amount)
                log_change("InboundRecordDetail", r.id, "size_46_inbound_amount", r.size_46_inbound_amount, 0)
                r.size_45_inbound_amount = r.size_46_inbound_amount
                r.size_46_inbound_amount = 0

        db.session.commit()

        with open("us_male_size_check_log.json", "w", encoding="utf-8") as f:
            json.dump(check_log, f, indent=2, ensure_ascii=False)

        print("✅ All updates for 'US男' complete. Log saved to us_male_size_check_log.json")
