from sqlalchemy.orm import joinedload
from models import BomItem, Bom, Material, OrderShoeBatchInfo
from collections import defaultdict


def refresh_correct_size_material_amount_in_bom(app, db):
    with app.app_context():
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

        # Step 2: Collect all relevant order_shoe_type_ids
        order_shoe_type_ids = list(set(order_shoe_type_id for _, order_shoe_type_id in rows))

        # Step 3: Query and group OrderShoeBatchInfo by order_shoe_type_id
        batch_infos = db.session.query(OrderShoeBatchInfo).filter(
            OrderShoeBatchInfo.order_shoe_type_id.in_(order_shoe_type_ids)
        ).all()

        batch_grouped = defaultdict(list)
        for b in batch_infos:
            batch_grouped[b.order_shoe_type_id].append(b)

        # Step 4: Process and update each BomItem
        for bom_item, order_shoe_type_id in rows:
            total_usage = 0
            for size in range(34, 47):
                size_attr = f"size_{size}_amount"
                usage_attr = f"size_{size}_total_usage"

                values = [
                    getattr(batch, size_attr, None)
                    for batch in batch_grouped.get(order_shoe_type_id, [])
                ]

                # If all are None, set to None; else sum non-Nones
                if all(v is None for v in values):
                    setattr(bom_item, usage_attr, None)
                else:
                    summed = sum(v for v in values if v is not None)
                    setattr(bom_item, usage_attr, summed)
                    total_usage += summed

            bom_item.total_usage = total_usage

        db.session.commit()
