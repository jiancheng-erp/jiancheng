from collections import defaultdict
from sqlalchemy.orm import joinedload
from models import (
    BomItem,
    Bom,
    Material,
    OrderShoeBatchInfo,
    PurchaseOrderItem,
    SizeMaterialStorage,
    ProductionInstructionItem,
)
from sqlalchemy import or_


def refresh_correct_size_material_amount_in_bom(app, db):
    with app.app_context():
        # Step 1: 查询需要更新的 BomItem（add_type='0' 且 bom_status=6 且 材料为 size 材料）
        rows = (
            db.session.query(
                BomItem,
                Bom.order_shoe_type_id.label("order_shoe_type_id")
            )
            .join(Bom, BomItem.bom_id == Bom.bom_id)
            .join(Material, Material.material_id == BomItem.material_id)
            .filter(
                BomItem.bom_item_add_type == '0',
                Bom.bom_status == '6',
                Material.material_category == 1,
            )
            .all()
        )

        # 收集所有 order_shoe_type_id
        order_shoe_type_ids = list(set(order_shoe_type_id for _, order_shoe_type_id in rows))

        # Step 2: 查询所有相关 OrderShoeBatchInfo 并按 order_shoe_type_id 分组
        batch_infos = db.session.query(OrderShoeBatchInfo).filter(
            OrderShoeBatchInfo.order_shoe_type_id.in_(order_shoe_type_ids)
        ).all()

        batch_grouped = defaultdict(list)
        for b in batch_infos:
            batch_grouped[b.order_shoe_type_id].append(b)

        # Step 3: 查询所有与 BomItem 相关联的 PurchaseOrderItem
        bom_item_ids = [bom_item.bom_item_id for bom_item, _ in rows]
        po_items = db.session.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.bom_item_id.in_(bom_item_ids)
        ).all()
        po_map = defaultdict(list)
        for po in po_items:
            po_map[po.bom_item_id].append(po)

        # Step 4: 更新 BomItem 和 PurchaseOrderItem
        for bom_item, order_shoe_type_id in rows:
            total_usage = 0
            batches = batch_grouped.get(order_shoe_type_id, [])

            for size in range(34, 47):
                size_attr = f"size_{size}_amount"
                usage_attr = f"size_{size}_total_usage"
                po_attr = f"size_{size}_purchase_amount"

                values = [
                    getattr(batch, size_attr, None)
                    for batch in batches
                ]

                if all(v is None for v in values):
                    setattr(bom_item, usage_attr, None)
                    # Update PO Items
                    for po in po_map.get(bom_item.bom_item_id, []):
                        setattr(po, po_attr, None)
                else:
                    summed = sum(v for v in values if v is not None)
                    setattr(bom_item, usage_attr, summed)
                    total_usage += summed
                    for po in po_map.get(bom_item.bom_item_id, []):
                        setattr(po, po_attr, summed)

            bom_item.total_usage = total_usage

        # Step 5: 更新 SizeMaterialStorage
        production_items = db.session.query(ProductionInstructionItem).filter(
            ProductionInstructionItem.order_shoe_type_id.in_(order_shoe_type_ids)
        ).all()
        prod_id_to_order_map = {p.production_instruction_item_id: p.order_shoe_type_id for p in production_items}

        storages = db.session.query(SizeMaterialStorage).filter(
            SizeMaterialStorage.production_instruction_item_id.in_(prod_id_to_order_map.keys())
        ).all()

        for storage in storages:
            order_shoe_type_id = prod_id_to_order_map.get(storage.production_instruction_item_id)
            if order_shoe_type_id is None:
                continue
            batches = batch_grouped.get(order_shoe_type_id, [])

            for size in range(34, 47):
                size_attr = f"size_{size}_amount"
                inbound_attr = f"size_{size}_estimated_inbound_amount"

                values = [
                    getattr(batch, size_attr, None)
                    for batch in batches
                ]

                if all(v is None for v in values):
                    setattr(storage, inbound_attr, None)
                else:
                    summed = sum(v for v in values if v is not None)
                    setattr(storage, inbound_attr, summed)

        db.session.commit()