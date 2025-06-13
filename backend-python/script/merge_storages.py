from collections import defaultdict
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload
import json

from models import *


def merge_storages(app, db):
    old_ms_new_ms_mapping = {}
    size_ms_mapping = {}

    def display_sync_info(stage):
        old_material_storage_count = len(db.session.query(OldMaterialStorage).all())
        old_size_material_storage_count = len(
            db.session.query(OldSizeMaterialStorage).all()
        )
        new_material_storage_count = len(db.session.query(MaterialStorage).all())
        print("Stage " + str(stage) + " started.")
        print(
            "old material storage has number of "
            + str(old_material_storage_count)
            + " of records"
        )
        print(
            "old size material storage has number of "
            + str(old_size_material_storage_count)
            + " of records"
        )
        print(
            "new material storage has number of "
            + str(new_material_storage_count)
            + " of records"
        )

    with app.app_context():

        # insert purchase_order_item_id to material_storage and # size_material_storage
        print(
            "Inserting purchase_order_item_id to material_storage"
        )
        response = (
            db.session.query(PurchaseOrder, PurchaseOrderItem, OldMaterialStorage)
            .join(
                PurchaseDivideOrder,
                PurchaseDivideOrder.purchase_order_id
                == PurchaseOrder.purchase_order_id,
            )
            .join(
                PurchaseOrderItem,
                PurchaseOrderItem.purchase_divide_order_id == PurchaseDivideOrder.purchase_divide_order_id,
            )
            .join(
                OldMaterialStorage,
                and_(
                    OldMaterialStorage.material_id == PurchaseOrderItem.inbound_material_id,
                    func.coalesce(OldMaterialStorage.material_model, '') == func.coalesce(PurchaseOrderItem.material_model, ''),
                    func.coalesce(OldMaterialStorage.material_specification, '') == func.coalesce(PurchaseOrderItem.material_specification, ''),
                    func.coalesce(OldMaterialStorage.material_storage_color, '') == func.coalesce(PurchaseOrderItem.color, ''),
                    OldMaterialStorage.actual_inbound_unit == PurchaseOrderItem.inbound_unit,
                    OldMaterialStorage.order_id == PurchaseOrder.order_id,
                    OldMaterialStorage.order_shoe_id == PurchaseOrder.order_shoe_id,
                ),
            )
            .all()
        )
        for row in response:
            _, purchase_order_item, old_material_storage = row
            old_material_storage.purchase_order_item_id = purchase_order_item.purchase_order_item_id
            db.session.flush()


        # insert purchase_order_item_id to material_storage and # size_material_storage
        print(
            "Inserting purchase_order_item_id size_material_storage"
        )
        response = (
            db.session.query(PurchaseOrder, PurchaseOrderItem, OldSizeMaterialStorage)
            .join(
                PurchaseDivideOrder,
                PurchaseDivideOrder.purchase_order_id
                == PurchaseOrder.purchase_order_id,
            )
            .join(
                PurchaseOrderItem,
                PurchaseOrderItem.purchase_divide_order_id == PurchaseDivideOrder.purchase_divide_order_id,
            )
            .join(
                OldSizeMaterialStorage,
                and_(
                    OldSizeMaterialStorage.material_id == PurchaseOrderItem.inbound_material_id,
                    func.coalesce(OldSizeMaterialStorage.size_material_model, '') == func.coalesce(PurchaseOrderItem.material_model, ''),
                    func.coalesce(OldSizeMaterialStorage.size_material_specification, '') == func.coalesce(PurchaseOrderItem.material_specification, ''),
                    func.coalesce(OldSizeMaterialStorage.size_material_color, '') == func.coalesce(PurchaseOrderItem.color, ''),
                    OldSizeMaterialStorage.actual_inbound_unit == PurchaseOrderItem.inbound_unit,
                    OldSizeMaterialStorage.order_id == PurchaseOrder.order_id,
                    OldSizeMaterialStorage.order_shoe_id == PurchaseOrder.order_shoe_id,
                ),
            )
            .all()
        )
        for row in response:
            _, purchase_order_item, old_material_storage = row
            old_material_storage.purchase_order_item_id = purchase_order_item.purchase_order_item_id
            db.session.flush()


        # sync old material storage
        display_sync_info(1)
        attr_names = [
            "order_id",
            "order_shoe_id",
            "spu_material_id",
            "current_amount",
            "unit_price",
            "material_outsource_status",
            "material_outsource_date",
            "material_estimated_arrival_date",
            "spu_material_id",
            "actual_inbound_unit",
            "craft_name",
            "average_price",
            "material_storage_status",
            "purchase_order_item_id",
        ]
        count = 0
        old_storages = db.session.query(OldMaterialStorage).all()
        total = str(len(old_storages))
        for entity in old_storages:
            if count % 100 == 0:
                print(str(count) + " / " + total)
            new_entity = MaterialStorage()
            for attr in attr_names:
                setattr(
                    new_entity,
                    attr,
                    getattr(entity, attr) if getattr(entity, attr) else None,
                )
            new_entity.inbound_amount = (
                entity.actual_inbound_amount if entity.actual_inbound_amount else 0
            )
            db.session.add(new_entity)
            db.session.flush()
            old_ms_new_ms_mapping[entity.material_storage_id] = (
                new_entity.material_storage_id
            )
            count += 1
        display_sync_info(2)

        attr_names = [
            "order_id",
            "order_shoe_id",
            "spu_material_id",
            "size_34_current_amount",
            "size_35_current_amount",
            "size_36_current_amount",
            "size_37_current_amount",
            "size_38_current_amount",
            "size_39_current_amount",
            "size_40_current_amount",
            "size_41_current_amount",
            "size_42_current_amount",
            "size_43_current_amount",
            "size_44_current_amount",
            "size_45_current_amount",
            "size_46_current_amount",
            "size_34_inbound_amount",
            "size_35_inbound_amount",
            "size_36_inbound_amount",
            "size_37_inbound_amount",
            "size_38_inbound_amount",
            "size_39_inbound_amount",
            "size_40_inbound_amount",
            "size_41_inbound_amount",
            "size_42_inbound_amount",
            "size_43_inbound_amount",
            "size_44_inbound_amount",
            "size_45_inbound_amount",
            "size_46_inbound_amount",
            "unit_price",
            "material_outsource_status",
            "material_outsource_date",
            "material_estimated_arrival_date",
            "craft_name",
            "average_price",
            "material_storage_status",
            "actual_inbound_unit",
            "shoe_size_columns",
            "purchase_order_item_id",
        ]
        count = 0
        total = str(len(db.session.query(OldSizeMaterialStorage).all()))
        for entity in db.session.query(OldSizeMaterialStorage).all():
            if count % 100 == 0:
                print(str(count) + " / " + total)
            new_entity = MaterialStorage()
            for attr in attr_names:
                setattr(
                    new_entity,
                    attr,
                    getattr(entity, attr) if getattr(entity, attr) else None,
                )
            new_entity.inbound_amount = (
                entity.total_actual_inbound_amount
                if entity.total_actual_inbound_amount
                else 0
            )
            new_entity.current_amount = (
                entity.total_current_amount if entity.total_current_amount else 0
            )
            db.session.add(new_entity)
            db.session.flush()
            size_ms_mapping[entity.size_material_storage_id] = (
                new_entity.material_storage_id
            )
            count += 1
        display_sync_info(3)
        total = str(len(db.session.query(InboundRecordDetail).all()))
        count = 0
        for entity, _ in (
            db.session.query(InboundRecordDetail, InboundRecord)
            .join(
                InboundRecord,
                InboundRecord.inbound_record_id
                == InboundRecordDetail.inbound_record_id,
            )
            .all()
        ):
            if count % 100 == 0:
                print(str(count) + " / " + total)
            if entity.material_storage_id == None:
                entity.material_storage_id = size_ms_mapping[
                    entity.size_material_storage_id
                ]
            else:
                entity.material_storage_id = old_ms_new_ms_mapping[
                    entity.material_storage_id
                ]
            db.session.flush()
            count += 1
        db.session.commit()
