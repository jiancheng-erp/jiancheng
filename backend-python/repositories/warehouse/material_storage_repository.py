from models import *
from domain.dto.MaterialStorageDTO import MaterialStorageDTO
from app_config import db
from constants import SHOESIZERANGE
from sqlalchemy import func

class MaterialStorageRepository:

    def get_material_storages(self, param: MaterialStorageDTO):
        query1 = (
            db.session.query(
                SPUMaterial.material_model,
                SPUMaterial.material_specification,
                SPUMaterial.color,
                Material.material_id,
                Material.material_name,
                Material.material_category,
                MaterialType.material_type_name,
                Supplier.supplier_name,
                Order.order_id,
                Order.order_rid,
                OrderShoe.order_shoe_id,
                Shoe.shoe_rid,
                func.coalesce(PurchaseOrderItem.purchase_amount, 0).label('purchase_amount'),
                MaterialStorage.inbound_amount,
                MaterialStorage.current_amount,
                MaterialStorage.average_price,
                MaterialStorage.actual_inbound_unit,
                MaterialStorage.unit_price,
                MaterialStorage.material_storage_id,
                MaterialStorage.shoe_size_columns,
            )
            .join(
                SPUMaterial, MaterialStorage.spu_material_id == SPUMaterial.spu_material_id
            )
            .join(Material, Material.material_id == SPUMaterial.material_id)
            .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
            .join(Supplier, Supplier.supplier_id == Material.material_supplier)
            .outerjoin(OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
            .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .outerjoin(Order, OrderShoe.order_id == Order.order_id)
            .outerjoin(
                PurchaseOrderItem,
                MaterialStorage.purchase_order_item_id
                == PurchaseOrderItem.purchase_order_item_id,
            )
            .filter(MaterialStorage.current_amount > 0)
        )

        for i in range(len(SHOESIZERANGE)):
            current_size_column = f"size_{SHOESIZERANGE[i]}_current_amount"
            query1 = query1.add_columns(func.coalesce(getattr(MaterialStorage, current_size_column), 0).label(current_size_column))
            estimated_size_column = f"size_{SHOESIZERANGE[i]}_purchase_amount"
            query1 = query1.add_columns(func.coalesce(getattr(PurchaseOrderItem, estimated_size_column), 0).label(estimated_size_column))
            actual_size_column = f"size_{SHOESIZERANGE[i]}_inbound_amount"
            query1 = query1.add_columns(func.coalesce(getattr(MaterialStorage, actual_size_column), 0).label(actual_size_column))

        if param.material_name:
            query1 = query1.filter(Material.material_name.ilike(f"%{param.material_name}%"))

        if param.material_specification:
            query1 = query1.filter(
                SPUMaterial.material_specification.ilike(f"%{param.material_specification}%")
            )
        if param.material_model:
            query1 = query1.filter(
                SPUMaterial.material_model.ilike(f"%{param.material_model}%")
            )
        if param.material_color:
            query1 = query1.filter(
                SPUMaterial.color.ilike(f"%{param.material_color}%")
            )
        if param.supplier_name:
            query1 = query1.filter(
                Supplier.supplier_name.ilike(f"%{param.supplier_name}%")
            )
        
        if param.is_non_order_material == 1:
            query1 = query1.filter(
                MaterialStorage.order_id.is_(None), MaterialStorage.order_shoe_id.is_(None)
            )
        else:
            if param.order_rid:
                query1 = query1.filter(Order.order_rid.ilike(f"%{param.order_rid}%"))
            if param.shoe_rid:
                query1 = query1.filter(Shoe.shoe_rid.ilike(f"%{param.shoe_rid}%"))

        count_result = (
            query1.with_entities(
                func.count(func.distinct(MaterialStorage.material_storage_id))
            )
            .scalar()
        )
        response = query1.distinct().limit(param.page_size).offset((param.page - 1) * param.page_size).all()
        return response, count_result