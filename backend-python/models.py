from app_config import db
import enum
from sqlalchemy import Enum


class ProductionTeam(enum.Enum):
    CUTTING = "裁断"
    PRE_SEWING = "针车预备"
    SEWING = "针车"
    MOLDING = "成型"


class BomItem(db.Model):
    __tablename__ = "bom_item"
    bom_item_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    material_id = db.Column(
        db.BigInteger, db.ForeignKey("material.material_id"), nullable=False
    )
    unit_usage = db.Column(db.Numeric(10, 5), nullable=False)
    total_usage = db.Column(db.Numeric(10, 5), nullable=False)
    department = db.Column(
        db.Integer, db.ForeignKey("department.department_id"), nullable=True
    )
    remark = db.Column(db.String(100), nullable=True)
    bom_id = db.Column(db.BigInteger, db.ForeignKey("bom.bom_id"), nullable=False)
    bom_item_color = db.Column(
        db.Integer, db.ForeignKey("color.color_id"), nullable=True
    )

    def __repr__(self):
        return f"<BomItem(bom_item_id={self.bom_item_id})>"


class Bom(db.Model):
    __tablename__ = "bom"
    bom_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    bom_rid = db.Column(db.String(80), nullable=False)
    bom_type = db.Column(db.Integer, nullable=False)
    order_shoe_id = db.Column(
        db.BigInteger, db.ForeignKey("order_shoe.order_shoe_id"), nullable=False
    )

    def __repr__(self):
        return f"<Bom(bom_id={self.bom_id})>"


class Character(db.Model):
    __tablename__ = "character"
    character_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    character_name = db.Column(db.String(40), nullable=False)

    def __repr__(self):
        return f"<Character(character_id={self.character_id})>"


class Color(db.Model):
    __tablename__ = "color"
    color_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    color_name = db.Column(db.String(30), nullable=False)
    color_en_name = db.Column(db.String(50), nullable=True)
    color_sp_name = db.Column(db.String(50), nullable=True)
    color_it_name = db.Column(db.String(40), nullable=True)

    def __repr__(self):
        return f"<Color(color_id={self.color_id})>"


class Customer(db.Model):
    __tablename__ = "customer"
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Customer(customer_id={self.customer_id})>"


class QuantityReportItem(db.Model):
    __tablename__ = "quantity_report_item"
    report_id = db.Column(
        db.BigInteger,
        db.ForeignKey("quantity_report.report_id"),
        primary_key=True,
        nullable=False,
    )
    order_shoe_batch_info_id = db.Column(
        db.BigInteger,
        db.ForeignKey("order_shoe_batch_info.order_shoe_batch_info_id"),
        primary_key=True,
        nullable=False,
    )
    amount = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<QuantityReportItem(report_id={self.report_id}, order_shoe_batch_info_id={self.order_shoe_batch_info_id})>"


class QuantityReport(db.Model):
    __tablename__ = "quantity_report"
    report_id = db.Column(
        db.BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    order_shoe_id = db.Column(
        db.BigInteger, db.ForeignKey("order_shoe.order_shoe_id"), nullable=True
    )
    team = db.Column(db.String(10), nullable=False)
    creation_date = db.Column(db.Date, nullable=True)
    submission_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.SmallInteger, nullable=True)
    rejection_reason = db.Column(db.String(40))

    def __repr__(self):
        return f"<QuantityReport(report_id={self.report_id})>"


class Department(db.Model):
    __tablename__ = "department"
    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    department_name = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<Department(department_id={self.department_id})>"


class Material(db.Model):
    __tablename__ = "material"
    material_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    material_name = db.Column(db.String(60), nullable=False)
    material_type_id = db.Column(db.BigInteger, nullable=False)
    material_unit = db.Column(db.String(4), nullable=True)
    material_supplier = db.Column(db.Integer, nullable=False)
    shoe_part_id = db.Column(
        db.Integer, db.ForeignKey("shoe_part.shoe_part_id"), nullable=False
    )
    material_creation_date = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"<Material(material_id={self.material_id})>"


class MaterialType(db.Model):
    __tablename__ = "material_type"
    material_type_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    material_type_name = db.Column(db.String(50), nullable=False)
    material_category = db.Column(db.SmallInteger, nullable=False, default=0)
    warehouse_id = db.Column(
        db.Integer,
        db.ForeignKey("material_warehouse.material_warehouse_id"),
        nullable=False,
    )

    def __repr__(self):
        return f"<MaterialType(material_type_id={self.material_type_id})>"

    def __name__(self):
        return "MaterialType"


class Event(db.Model):
    __tablename__ = "event"
    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.staff_id"), nullable=False)
    handle_time = db.Column(db.DateTime, nullable=False)
    operation_id = db.Column(
        db.Integer, db.ForeignKey("operation.operation_id"), nullable=False
    )
    event_order_id = db.Column(db.BigInteger, nullable=True)
    event_order_shoe_id = db.Column(db.BigInteger, nullable=True)

    def __repr__(self):
        return f"<Event(event_id={self.event_id})>"


class MaterialStorage(db.Model):
    __tablename__ = "material_storage"

    material_storage_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    order_shoe_id = db.Column(db.BigInteger)
    material_id = db.Column(db.BigInteger, nullable=False)
    estimated_inbound_amount = db.Column(db.DECIMAL(10, 5))
    actual_inbound_amount = db.Column(db.DECIMAL(10, 5))
    current_amount = db.Column(db.DECIMAL(10, 5), nullable=False)
    unit_price = db.Column(db.DECIMAL(10, 2))
    material_specification = db.Column(db.String(40), nullable=False)
    material_outsource_status = db.Column(db.CHAR(1), default="0", nullable=False)
    material_outsource_outbound_date = db.Column(db.Date)
    material_storage_color = db.Column(db.Integer, db.ForeignKey("color.color_id"))

    def __repr__(self):
        return f"<MaterialStorage(material_storage_id={self.material_storage_id})>"

    def __name__(self):
        return "MaterialStorage"


class Operation(db.Model):
    __tablename__ = "operation"
    operation_id = db.Column(db.Integer, primary_key=True)
    operation_name = db.Column(db.String(40), nullable=False)
    operation_type = db.Column(db.Integer, nullable=False, default=0)
    operation_modified_status = db.Column(db.Integer, nullable=True)
    operation_modified_value = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<Operation(operation_id={self.operation_id})>"

    def __name__(self):
        return "Operation"


class Order(db.Model):
    __tablename__ = "order"
    order_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_rid = db.Column(db.String(40), nullable=False, unique=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customer.customer_id"), nullable=False
    )

    def __repr__(self):
        return f"<Order(order_id={self.order_id})>"

    def __name__(self):
        return "Order"


class OrderShoeStatus(db.Model):
    __tablename__ = "order_shoe_status"
    order_shoe_status_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    order_shoe_id = db.Column(
        db.BigInteger, db.ForeignKey("order_shoe.order_shoe_id"), nullable=False
    )
    current_status = db.Column(
        db.Integer,
        db.ForeignKey("order_shoe_status_reference.status_id"),
        nullable=False,
    )
    current_status_value = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<OrderShoeStatus(order_shoe_status_id={self.order_shoe_status_id})>"


class OrderShoeBatchInfo(db.Model):
    __tablename__ = "order_shoe_batch_info"
    order_shoe_batch_info_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    name = db.Column(db.String(20), nullable=False)
    color_id = db.Column(db.Integer, db.ForeignKey("color.color_id"), nullable=False)
    total_amount = db.Column(db.Integer, nullable=True)
    cutting_amount = db.Column(db.Integer, nullable=True)
    pre_sewing_amount = db.Column(db.Integer, nullable=True)
    sewing_amount = db.Column(db.Integer, nullable=True)
    molding_amount = db.Column(db.Integer, nullable=True)
    size_34_amount = db.Column(db.Integer, nullable=True)
    size_35_amount = db.Column(db.Integer, nullable=True)
    size_36_amount = db.Column(db.Integer, nullable=True)
    size_37_amount = db.Column(db.Integer, nullable=True)
    size_38_amount = db.Column(db.Integer, nullable=True)
    size_39_amount = db.Column(db.Integer, nullable=True)
    size_40_amount = db.Column(db.Integer, nullable=True)
    size_41_amount = db.Column(db.Integer, nullable=True)
    size_42_amount = db.Column(db.Integer, nullable=True)
    size_43_amount = db.Column(db.Integer, nullable=True)
    size_44_amount = db.Column(db.Integer, nullable=True)
    size_45_amount = db.Column(db.Integer, nullable=True)
    size_46_amount = db.Column(db.Integer, nullable=True)
    order_shoe_id = db.Column(
        db.BigInteger, db.ForeignKey("order_shoe.order_shoe_id"), nullable=False
    )

    def __repr__(self):
        return f"<OrderShoeBatchInfo(order_shoe_batch_info_id={self.order_shoe_batch_info_id})>"

    def __name__(self):
        return "OrderShoeBatchInfo"


class OrderShoe(db.Model):
    __tablename__ = "order_shoe"
    order_shoe_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    shoe_id = db.Column(db.Integer, db.ForeignKey("shoe.shoe_id"), nullable=False)
    order_id = db.Column(db.BigInteger, db.ForeignKey("order.order_id"), nullable=False)
    customer_product_name = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"<OrderShoe(order_shoe_id={self.order_shoe_id})>"

    def __name__(self):
        return "OrderShoe"


class OutsourceInfo(db.Model):
    __tablename__ = "outsource_info"

    outsource_info_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    outsource_type = db.Column(db.String(20), nullable=False)
    factory_id = db.Column(
        db.BigInteger, db.ForeignKey("outsource_factory.factory_id"), nullable=True
    )
    outsource_amount = db.Column(db.Integer, nullable=False)
    outsource_start_date = db.Column(db.Date, nullable=True)
    outsource_end_date = db.Column(db.Date, nullable=True)
    approval_status = db.Column(db.Boolean, nullable=False)
    deadline_date = db.Column(db.Date, nullable=True)
    semifinished_estimated_outbound_date = db.Column(db.Date, nullable=True)
    semifinished_required = db.Column(db.Boolean, nullable=True)
    material_delivery_date = db.Column(db.Date, nullable=True)
    order_shoe_id = db.Column(
        db.BigInteger, db.ForeignKey("order_shoe.order_shoe_id"), nullable=False
    )


class OutsourceFactory(db.Model):
    __tablename__ = "outsource_factory"
    factory_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    factory_name = db.Column(db.String(50), nullable=False)


class OrderShoeProductionInfo(db.Model):
    __tablename__ = "order_shoe_production_info"

    production_info_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    cutting_line_group = db.Column(db.String(30), nullable=True)
    pre_sewing_line_group = db.Column(db.String(30), nullable=True)
    sewing_line_group = db.Column(db.String(30), nullable=True)
    molding_line_group = db.Column(db.String(30), nullable=True)
    is_cutting_outsourced = db.Column(db.Boolean, nullable=True)
    is_sewing_outsourced = db.Column(db.Boolean, nullable=True)
    is_molding_outsourced = db.Column(db.Boolean, nullable=True)
    cutting_start_date = db.Column(db.Date, nullable=True)
    cutting_end_date = db.Column(db.Date, nullable=True)
    sewing_start_date = db.Column(db.Date, nullable=True)
    sewing_end_date = db.Column(db.Date, nullable=True)
    molding_start_date = db.Column(db.Date, nullable=True)
    molding_end_date = db.Column(db.Date, nullable=True)
    pre_sewing_start_date = db.Column(db.Date, nullable=True)
    pre_sewing_end_date = db.Column(db.Date, nullable=True)
    is_material_arrived = db.Column(db.Boolean, nullable=False)
    order_shoe_id = db.Column(
        db.BigInteger, db.ForeignKey("order_shoe.order_shoe_id"), nullable=False
    )


class OrderShoeStatusReference(db.Model):
    __tablename__ = "order_shoe_status_reference"
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(40), nullable=False)

    def __repr__(self):
        return f"<OrderShoeStatusReference(status_id={self.status_id})>"

    def __name__(self):
        return "OrderShoeStatusReference"


class OrderStatus(db.Model):
    __tablename__ = "order_status"
    order_status_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_current_status = db.Column(
        db.Integer,
        db.ForeignKey("order_status_reference.order_status_id"),
        nullable=False,
    )
    order_status_value = db.Column(db.Integer, nullable=False)
    order_id = db.Column(db.BigInteger, db.ForeignKey("order.order_id"), nullable=False)

    def __repr__(self):
        return f"<OrderStatus(order_status_id={self.order_status_id})>"

    def __name__(self):
        return "OrderStatus"


class OrderStatusReference(db.Model):
    __tablename__ = "order_status_reference"
    order_status_id = db.Column(db.Integer, primary_key=True)
    order_status_name = db.Column(db.String(40), nullable=False)

    def __repr__(self):
        return f"<OrderStatusReference(order_status_id={self.order_status_id})>"

    def __name__(self):
        return "OrderStatusReference"


class ProcedureReference(db.Model):
    __tablename__ = "procedure_reference"
    procedure_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    procedure_name = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(10), nullable=True)
    current_price = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<ProcedureReference(procedure_id={self.procedure_id})>"

    def __name__(self):
        return "ProcedureReference"


class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_item"
    purchase_order_item_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    bom_item_id = db.Column(
        db.BigInteger, db.ForeignKey("bom_item.bom_item_id"), nullable=False
    )
    purchase_divide_order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("purchase_divide_order.purchase_divide_order_id"),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<PurchaseOrderItem(purchase_order_item_id={self.purchase_order_item_id})>"
        )

    def __name__(self):
        return "PurchaseOrderItem"


class PurchaseDivideOrder(db.Model):
    __tablename__ = "purchase_divide_order"
    purchase_divide_order_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    purchase_order_id = db.Column(
        db.BigInteger, db.ForeignKey("purchase_order.purchase_order_id"), nullable=False
    )
    purchase_divide_order_rid = db.Column(
        db.Integer, db.ForeignKey("order.order_rid"), nullable=True
    )

    def __repr__(self):
        return f"<PurchaseDivideOrder(purchase_divide_order_id={self.purchase_divide_order_id})>"


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_order"
    purchase_order_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    bom_id = db.Column(db.BigInteger, db.ForeignKey("bom.bom_id"), nullable=True)
    purchase_order_rid = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<PurchaseOrder(purchase_order_id={self.purchase_order_id})>"


class SemifinishedShoeStorage(db.Model):
    __tablename__ = "semifinished_shoe_storage"

    semifinished_shoe_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    semifinished_inbound_date = db.Column(db.Date, nullable=False)
    order_shoe_id = db.Column(db.BigInteger, nullable=False)
    semifinished_amount = db.Column(db.Integer)
    semifinished_type = db.Column(db.String(1), nullable=False)
    semifinished_status = db.Column(db.String(1))


class Shoe(db.Model):
    __tablename__ = "shoe"
    shoe_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shoe_rid = db.Column(db.String(20), nullable=False)
    shoe_image_url = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<Shoe(shoe_id={self.shoe_id})>"

    def __name__(self):
        return "Shoe"


class ShoePart(db.Model):
    __tablename__ = "shoe_part"
    shoe_part_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shoe_part_name = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"<ShoePart(shoe_part_id={self.shoe_part_id})>"

    def __name__(self):
        return "ShoePart"


class ShoeInboundRecord(db.Model):
    __tablename__ = "shoe_inbound_record"
    shoe_inbound_record_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    shoe_inbound_rid = db.Column(db.String(60), nullable=True)
    inbound_amount = db.Column(db.Integer, nullable=True)
    inbound_date = db.Column(db.Date, nullable=False)
    inbound_type = db.Column(
        db.CHAR(1), nullable=False, default="P", comment="P: 自产\nO: 外包"
    )
    semifinished_shoe_storage_id = db.Column(
        db.BigInteger,
        db.ForeignKey("semifinished_shoe_storage.semifinished_shoe_id"),
        nullable=True,
    )
    finished_shoe_storage_id = db.Column(
        db.BigInteger,
        db.ForeignKey("finished_shoe_storage.finished_shoe_id"),
        nullable=True,
    )


class ShoeOutboundRecord(db.Model):
    __tablename__ = "shoe_outbound_record"
    shoe_outbound_record_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    shoe_outbound_rid = db.Column(db.String(60), nullable=True)
    outbound_amount = db.Column(db.Integer, nullable=True)
    outbound_date = db.Column(db.Date, nullable=False)
    outbound_address = db.Column(db.String(100), nullable=True)
    outbound_type = db.Column(
        db.CHAR(1), nullable=False, default="P", comment="P: 自产\nO: 外包"
    )
    outbound_department = db.Column(db.CHAR(1), nullable=True)
    picker = db.Column(db.String(15), nullable=True)
    semifinished_shoe_storage_id = db.Column(
        db.BigInteger,
        db.ForeignKey("semifinished_shoe_storage.semifinished_shoe_id"),
        nullable=True,
    )
    finished_shoe_storage_id = db.Column(
        db.BigInteger,
        db.ForeignKey("finished_shoe_storage.finished_shoe_id"),
        nullable=True,
    )


class Staff(db.Model):
    __tablename__ = "staff"
    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    staff_name = db.Column(db.String(20), nullable=False)
    character_id = db.Column(
        db.Integer, db.ForeignKey("character.character_id"), nullable=False
    )
    department_id = db.Column(
        db.Integer, db.ForeignKey("department.department_id"), nullable=False
    )

    def __repr__(self):
        return f"<Staff(staff_id={self.staff_id})>"

    def __name__(self):
        return "Staff"


class Supplier(db.Model):
    __tablename__ = "supplier"
    supplier_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supplier_name = db.Column(db.String(50), nullable=False)
    supplier_type = db.Column(db.String(1), nullable=False)

    def __repr__(self):
        return f"<Supplier(supplier_id={self.supplier_id})>"

    def __name__(self):
        return "Supplier"


class SizeMaterialStorage(db.Model):
    __tablename__ = "size_material_storage"
    size_material_storage_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    size_material_specification = db.Column(db.String(40), nullable=False)
    size_34_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_35_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_36_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_37_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_38_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_39_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_40_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_41_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_42_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_43_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_44_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_45_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_46_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    total_estimated_inbound_amount = db.Column(db.Integer, nullable=True)
    size_34_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_35_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_36_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_37_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_38_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_39_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_40_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_41_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_42_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_43_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_44_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_45_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    size_46_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    total_actual_inbound_amount = db.Column(db.Integer, nullable=True)
    material_outsource_status = db.Column(db.String(1), nullable=True, default="N")
    size_34_current_amount = db.Column(db.Integer, nullable=True)
    size_35_current_amount = db.Column(db.Integer, nullable=True)
    size_36_current_amount = db.Column(db.Integer, nullable=True)
    size_37_current_amount = db.Column(db.Integer, nullable=True)
    size_38_current_amount = db.Column(db.Integer, nullable=True)
    size_39_current_amount = db.Column(db.Integer, nullable=True)
    size_40_current_amount = db.Column(db.Integer, nullable=True)
    size_41_current_amount = db.Column(db.Integer, nullable=True)
    size_42_current_amount = db.Column(db.Integer, nullable=True)
    size_43_current_amount = db.Column(db.Integer, nullable=True)
    size_44_current_amount = db.Column(db.Integer, nullable=True)
    size_45_current_amount = db.Column(db.Integer, nullable=True)
    size_46_current_amount = db.Column(db.Integer, nullable=True)
    total_current_amount = db.Column(db.Integer, nullable=True)
    size_storage_type = db.Column(db.String(1), nullable=False, default="E")
    material_outsource_date = db.Column(db.Date, nullable=True)
    material_id = db.Column(
        db.BigInteger, db.ForeignKey("material.material_id"), nullable=False
    )
    size_material_color = db.Column(
        db.Integer, db.ForeignKey("color.color_id"), nullable=True
    )
    order_shoe_id = db.Column(
        db.BigInteger, db.ForeignKey("order_shoe.order_shoe_id"), nullable=True
    )
    unit_price = db.Column(db.Numeric(10, 2), nullable=True)

    def __repr__(self):
        return f"<SizeMaterialStorage {self.size_material_specification}>"


class UnitPriceReportDetail(db.Model):
    __tablename__ = "unit_price_report_detail"
    report_id = db.Column(
        db.BigInteger,
        db.ForeignKey("unit_price_report.report_id"),
        primary_key=True,
        nullable=False,
    )
    row_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
    )
    procedure_id = db.Column(
        db.BigInteger,
        db.ForeignKey("procedure_reference.procedure_id"),
        primary_key=True,
        nullable=False,
    )
    price = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(600), nullable=True)

    def __repr__(self):
        return f"<UnitPriceReportDetail(report_id={self.report_id}, row_id={self.row_id}, procedure_id={self.procedure_id}, note={self.note})>"


class UnitPriceReport(db.Model):
    __tablename__ = "unit_price_report"
    report_id = db.Column(
        db.BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    order_shoe_id = db.Column(
        db.BigInteger, db.ForeignKey("order_shoe.order_shoe_id"), nullable=False
    )
    submission_date = db.Column(db.Date, nullable=True)
    team = db.Column(db.String(10), nullable=True)
    status = db.Column(db.SmallInteger, nullable=False)
    rejection_reason = db.Column(db.String(40), nullable=True)

    def __repr__(self):
        return f"<UnitPriceReport(report_id={self.report_id})>"

    def to_dict(obj):
        """Convert SQLAlchemy object to dictionary."""
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


class MaterialWarehouse(db.Model):
    __tablename__ = "material_warehouse"
    material_warehouse_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    material_warehouse_name = db.Column(db.String(20), nullable=False)
    material_warehouse_creation_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"<Warehouse(material_warehouse_id={self.material_warehouse_id})>"


class FinishedShoeStorage(db.Model):
    __tablename__ = "finished_shoe_storage"
    finished_shoe_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    finished_inbound_date = db.Column(db.Date, nullable=False)
    order_shoe_id = db.Column(
        db.BigInteger, db.ForeignKey("order_shoe.order_shoe_id"), nullable=False
    )
    finished_amount = db.Column(db.Integer, nullable=False)
    finished_type = db.Column(db.CHAR(1), nullable=False)
    finished_status = db.Column(
        db.CHAR(1), nullable=True, comment="0：未发货\n1：已发货"
    )


class InboundRecord(db.Model):
    __tablename__ = "inbound_record"
    inbound_record_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    inbound_rid = db.Column(db.String(50), nullable=True)
    inbound_amount = db.Column(db.DECIMAL(10, 5))
    size_34_inbound_amount = db.Column(db.Integer, nullable=True)
    size_35_inbound_amount = db.Column(db.Integer, nullable=True)
    size_36_inbound_amount = db.Column(db.Integer, nullable=True)
    size_37_inbound_amount = db.Column(db.Integer, nullable=True)
    size_38_inbound_amount = db.Column(db.Integer, nullable=True)
    size_39_inbound_amount = db.Column(db.Integer, nullable=True)
    size_40_inbound_amount = db.Column(db.Integer, nullable=True)
    size_41_inbound_amount = db.Column(db.Integer, nullable=True)
    size_42_inbound_amount = db.Column(db.Integer, nullable=True)
    size_43_inbound_amount = db.Column(db.Integer, nullable=True)
    size_44_inbound_amount = db.Column(db.Integer, nullable=True)
    size_45_inbound_amount = db.Column(db.Integer, nullable=True)
    size_46_inbound_amount = db.Column(db.Integer, nullable=True)
    inbound_date = db.Column(db.Date, nullable=False)
    inbound_type = db.Column(db.String(1), nullable=False)
    material_storage_id = db.Column(
        db.BigInteger,
        db.ForeignKey("material_storage.material_storage_id"),
        nullable=True,
    )
    size_material_storage_id = db.Column(
        db.BigInteger,
        db.ForeignKey("size_material_storage.size_material_storage_id"),
        nullable=True,
    )

    def __repr__(self):
        return f"<InboundRecord {self.inbound_rid}>"


class OutboundRecord(db.Model):
    __tablename__ = "outbound_record"
    outbound_record_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    outbound_rid = db.Column(db.String(60), nullable=False)
    outbound_amount = db.Column(db.DECIMAL(10, 5))
    size_34_outbound_amount = db.Column(db.Integer, nullable=True)
    size_35_outbound_amount = db.Column(db.Integer, nullable=True)
    size_36_outbound_amount = db.Column(db.Integer, nullable=True)
    size_37_outbound_amount = db.Column(db.Integer, nullable=True)
    size_38_outbound_amount = db.Column(db.Integer, nullable=True)
    size_39_outbound_amount = db.Column(db.Integer, nullable=True)
    size_40_outbound_amount = db.Column(db.Integer, nullable=True)
    size_41_outbound_amount = db.Column(db.Integer, nullable=True)
    size_42_outbound_amount = db.Column(db.Integer, nullable=True)
    size_43_outbound_amount = db.Column(db.Integer, nullable=True)
    size_44_outbound_amount = db.Column(db.Integer, nullable=True)
    size_45_outbound_amount = db.Column(db.Integer, nullable=True)
    size_46_outbound_amount = db.Column(db.Integer, nullable=True)
    outbound_date = db.Column(db.Date, nullable=False)
    outbound_type = db.Column(db.String(1), nullable=False)
    outbound_department = db.Column(db.String(1), nullable=True)
    picker = db.Column(db.String(15), nullable=True)
    outbound_address = db.Column(db.String(100), nullable=True)
    material_storage_id = db.Column(
        db.BigInteger,
        db.ForeignKey("material_storage.material_storage_id"),
        nullable=True,
    )
    size_material_storage_id = db.Column(
        db.BigInteger,
        db.ForeignKey("size_material_storage.size_material_storage_id"),
        nullable=True,
    )

    def __repr__(self):
        return f"<OutboundRecord {self.outbound_rid}>"
