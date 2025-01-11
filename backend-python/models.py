from app_config import db


class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(50), nullable=False)
    user_passwd = db.Column(db.String(50), nullable=False)
    staff_id = db.Column(
        db.Integer,
    )


class BomItem(db.Model):
    __tablename__ = "bom_item"
    bom_item_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    material_variant_id = db.Column(
        db.BigInteger,
    )
    unit_usage = db.Column(db.Numeric(10, 5), nullable=False)
    total_usage = db.Column(db.Numeric(10, 5), nullable=False)
    department_id = db.Column(
        db.Integer,
    )
    material_specification = db.Column(db.String(50), nullable=True)
    bom_item_add_type = db.Column(db.String(1), nullable=False)
    remark = db.Column(db.String(100), nullable=True)
    bom_id = db.Column(db.BigInteger)
    size_34_total_usage = db.Column(db.Integer, nullable=True)
    size_35_total_usage = db.Column(db.Integer, nullable=True)
    size_36_total_usage = db.Column(db.Integer, nullable=True)
    size_37_total_usage = db.Column(db.Integer, nullable=True)
    size_38_total_usage = db.Column(db.Integer, nullable=True)
    size_39_total_usage = db.Column(db.Integer, nullable=True)
    size_40_total_usage = db.Column(db.Integer, nullable=True)
    size_41_total_usage = db.Column(db.Integer, nullable=True)
    size_42_total_usage = db.Column(db.Integer, nullable=True)
    size_43_total_usage = db.Column(db.Integer, nullable=True)
    size_44_total_usage = db.Column(db.Integer, nullable=True)
    size_45_total_usage = db.Column(db.Integer, nullable=True)
    size_46_total_usage = db.Column(db.Integer, nullable=True)
    size_type = db.Column(db.String(1), nullable=False, default="E")
    material_second_type = db.Column(db.String(10), nullable=True)
    craft_name = db.Column(db.String(200), nullable=True)
    pairs = db.Column(db.DECIMAL(10, 5), nullable=True)
    production_instruction_item_id = db.Column(db.BigInteger, nullable=True)

    def __repr__(self):
        return f"<BomItem(bom_item_id={self.bom_item_id})>"


class Bom(db.Model):
    __tablename__ = "bom"
    bom_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    bom_rid = db.Column(db.String(80), nullable=False)
    bom_type = db.Column(db.Integer, nullable=False)
    order_shoe_type_id = db.Column(
        db.BigInteger,
    )
    bom_status = db.Column(db.String(1), nullable=True)
    total_bom_id = db.Column(db.BigInteger, nullable=True)

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
    customer_brand = db.Column(db.String(25), nullable=True)

    def __repr__(self):
        return f"<Customer(customer_id={self.customer_id})>"


class Message(db.Model):
    __tablename__ = "message"
    message_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, nullable=False, index=True)
    receiver_id = db.Column(db.Integer, nullable=False, index=True)
    content = db.Column(db.String(100), nullable=True)
    send_datetime = db.Column(db.DateTime)
    is_viewed = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Message {self.message_id}>"


class QuantityReportItem(db.Model):
    __tablename__ = "quantity_report_item"
    quantity_report_item_id = db.Column(
        db.BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    quantity_report_id = db.Column(db.BigInteger, nullable=False)
    order_shoe_type_id = db.Column(db.BigInteger, nullable=False)
    report_amount = db.Column(db.Integer, default=0)
    production_line_id = db.Column(db.Integer)

    def __repr__(self):
        return f"<QuantityReportItem(report_id={self.quantity_report_item_id}>"


class QuantityReport(db.Model):
    __tablename__ = "quantity_report"
    report_id = db.Column(
        db.BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    order_shoe_id = db.Column(
        db.BigInteger,
    )
    team = db.Column(db.String(10), nullable=False)
    creation_date = db.Column(db.Date, nullable=True)
    submission_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.SmallInteger, nullable=True)
    rejection_reason = db.Column(db.String(40))
    total_report_amount = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<QuantityReport(report_id={self.report_id})>"


class Department(db.Model):
    __tablename__ = "department"
    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    department_name = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<Department(department_id={self.department_id})>"


class MaterialVariant(db.Model):
    __tablename__ = "material_variant"
    material_variant_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    material_model = db.Column(db.String(60), nullable=True)
    material_id = db.Column(db.Integer, nullable=False)
    material_unit = db.Column(db.String(4), nullable=True)
    material_supplier = db.Column(db.Integer, nullable=False)
    material_category = db.Column(db.SmallInteger, nullable=False, default=0)
    color = db.Column(db.String(20), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("material_supplier", "material_model", "material_specification","color", "material_id", name="unq_material"),
    )

    def __repr__(self):
        return f"<MaterialVariant(material_variant_id={self.material_variant_id})>"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Material(db.Model):
    __tablename__ = "material"
    material_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    material_type_id = db.Column(db.Integer, nullable=False)
    material_default_unit = db.Column(db.String(4), nullable=False)
    material_name = db.Column(db.String(50), nullable=False)
    material_creation_date = db.Column(db.Date, nullable=True)
    material_category = db.Column(db.SmallInteger, nullable=False, default=0)

    def __repr__(self):
        return f"<Material(material_id={self.material_id})>"

    def __name__(self):
        return "Material"
    

class MaterialType(db.Model):
    __tablename__ = "material_type"
    material_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    material_type_name = db.Column(db.String(20), nullable=False)
    warehouse_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<MaterialType(material_type_id={self.material_type_id})>"


class Event(db.Model):
    __tablename__ = "event"
    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    staff_id = db.Column(db.Integer)
    handle_time = db.Column(db.DateTime, nullable=False)
    operation_id = db.Column(
        db.Integer,
    )
    event_order_id = db.Column(db.BigInteger, nullable=True)
    event_order_shoe_id = db.Column(db.BigInteger, nullable=True)
    event_type = db.Column(db.SmallInteger, default=0)

    def __repr__(self):
        return f"<Event(event_id={self.event_id})>"


class MaterialStorage(db.Model):
    __tablename__ = "material_storage"

    material_storage_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    order_id = db.Column(db.BigInteger)
    order_shoe_id = db.Column(db.BigInteger)
    material_variant_id = db.Column(db.BigInteger, nullable=False)
    material_specification = db.Column(db.String(50), nullable=True)
    estimated_inbound_amount = db.Column(
        db.DECIMAL(10, 5),
        default=0,
    )
    actual_inbound_amount = db.Column(
        db.DECIMAL(10, 5),
        default=0,
    )
    current_amount = db.Column(db.DECIMAL(10, 5), default=0, nullable=False)
    unit_price = db.Column(db.DECIMAL(10, 2), nullable=False, default=0.00)
    material_outsource_status = db.Column(db.SmallInteger, default=0, nullable=False)
    material_outsource_outbound_date = db.Column(db.Date)
    purchase_divide_order_id = db.Column(db.BigInteger)
    material_estimated_arrival_date = db.Column(db.Date)
    material_storage_status = db.Column(db.SmallInteger, default=0)
    department_id = db.Column(db.Integer)

    craft_name = db.Column(db.String(200), nullable=True)
    composite_unit_cost = db.Column(db.DECIMAL(10, 2), default=0.00)
    production_instruction_item_id = db.Column(db.BigInteger, nullable=True)

    def __repr__(self):
        return f"<MaterialStorage(material_storage_id={self.material_storage_id})>"

    def __name__(self):
        return "MaterialStorage"
    
    def to_dict(obj):
        """Convert SQLAlchemy object to dictionary."""
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


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
    order_cid = db.Column(db.String(40), nullable=True, unique=True)
    batch_info_type_id = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(
        db.Integer,
    )
    salesman_id = db.Column(db.Integer,nullable=False)
    production_list_upload_status = db.Column(db.String(1), nullable=True)
    amount_list_upload_status = db.Column(db.String(1), nullable=True)
    batch_info_type_id = db.Column(db.Integer, nullable=False)
    supervisor_id = db.Column(db.Integer)
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
        db.BigInteger,
    )
    current_status = db.Column(
        db.Integer,
        nullable=False,
    )
    current_status_value = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<OrderShoeStatus(order_shoe_status_id={self.order_shoe_status_id})>"


class OutsourceBatchInfo(db.Model):
    __tablename__ = "outsource_batch_info"
    outsource_batch_info_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    order_shoe_type_id = db.Column(db.BigInteger, nullable=False)
    total_outsource_amount = db.Column(db.Integer, default=0)
    size_34_outsource_amount = db.Column(db.Integer, default=0)
    size_35_outsource_amount = db.Column(db.Integer, default=0)
    size_36_outsource_amount = db.Column(db.Integer, default=0)
    size_37_outsource_amount = db.Column(db.Integer, default=0)
    size_38_outsource_amount = db.Column(db.Integer, default=0)
    size_39_outsource_amount = db.Column(db.Integer, default=0)
    size_40_outsource_amount = db.Column(db.Integer, default=0)
    size_41_outsource_amount = db.Column(db.Integer, default=0)
    size_42_outsource_amount = db.Column(db.Integer, default=0)
    size_43_outsource_amount = db.Column(db.Integer, default=0)
    size_44_outsource_amount = db.Column(db.Integer, default=0)
    size_45_outsource_amount = db.Column(db.Integer, default=0)
    size_46_outsource_amount = db.Column(db.Integer, default=0)
    outsource_info_id = db.Column(db.Integer, nullable=False)
    is_product_arrived = db.Column(db.SmallInteger, nullable=False)


class PackagingInfo(db.Model):
    __tablename__ = "packaging_info"

    customer_id = db.Column(db.Integer, nullable=False)
    packaging_info_name = db.Column(db.String(15), nullable=False, unique=True)
    packaging_info_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    batch_info_type_id = db.Column(db.Integer, nullable=False)
    packaging_info_locale = db.Column(db.String(10), nullable=False)
    batch_info_type_id = db.Column(db.Integer, nullable=True)
    size_34_ratio = db.Column(db.Integer, nullable=True)
    size_35_ratio = db.Column(db.Integer, nullable=True)
    size_36_ratio = db.Column(db.Integer, nullable=True)
    size_37_ratio = db.Column(db.Integer, nullable=True)
    size_38_ratio = db.Column(db.Integer, nullable=True)
    size_39_ratio = db.Column(db.Integer, nullable=True)
    size_40_ratio = db.Column(db.Integer, nullable=True)
    size_41_ratio = db.Column(db.Integer, nullable=True)
    size_42_ratio = db.Column(db.Integer, nullable=True)
    size_43_ratio = db.Column(db.Integer, nullable=True)
    size_44_ratio = db.Column(db.Integer, nullable=True)
    size_45_ratio = db.Column(db.Integer, nullable=True)
    size_46_ratio = db.Column(db.Integer, nullable=True)
    total_quantity_ratio = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<PackagingInfo(packaging_info_id={self.packaging_info_id})>"

    def __name__(self):
        return "PackagingInfo"


class OrderShoeBatchInfo(db.Model):
    __tablename__ = "order_shoe_batch_info"
    order_shoe_batch_info_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    name = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Integer, nullable=True)
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
    packaging_info_id = db.Column(db.Integer, nullable=True)
    packaging_info_quantity = db.Column(db.Integer, nullable=True)
    order_shoe_type_id = db.Column(
        db.BigInteger,
    )
    price_per_pair = db.Column(db.DECIMAL(10, 2), nullable=True)
    total_price = db.Column(db.DECIMAL(10, 2), nullable=True)
    currency_type = db.Column(db.String(3), nullable=True)

    def __repr__(self):
        return f"<OrderShoeBatchInfo(order_shoe_batch_info_id={self.order_shoe_batch_info_id})>"

    def __name__(self):
        return "OrderShoeBatchInfo"


class OrderShoeProductionAmount(db.Model):
    __tablename__ = "order_shoe_production_amount"
    order_shoe_production_amount_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    size_34_production_amount = db.Column(db.Integer, default=0)
    size_35_production_amount = db.Column(db.Integer, default=0)
    size_36_production_amount = db.Column(db.Integer, default=0)
    size_37_production_amount = db.Column(db.Integer, default=0)
    size_38_production_amount = db.Column(db.Integer, default=0)
    size_39_production_amount = db.Column(db.Integer, default=0)
    size_40_production_amount = db.Column(db.Integer, default=0)
    size_41_production_amount = db.Column(db.Integer, default=0)
    size_42_production_amount = db.Column(db.Integer, default=0)
    size_43_production_amount = db.Column(db.Integer, default=0)
    size_44_production_amount = db.Column(db.Integer, default=0)
    size_45_production_amount = db.Column(db.Integer, default=0)
    size_46_production_amount = db.Column(db.Integer, default=0)
    total_production_amount = db.Column(db.Integer, default=0)
    production_team = db.Column(db.SmallInteger, nullable=False)
    order_shoe_type_id = db.Column(db.BigInteger)

    def __repr__(self):
        return f"<OrderShoeProductionAmount(order_shoe_production_amount_id={self.order_shoe_production_amount_id})>"

    def __name__(self):
        return "OrderShoeProductionAmount"


class OrderShoe(db.Model):
    __tablename__ = "order_shoe"
    order_shoe_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, nullable=False)
    shoe_id = db.Column(db.Integer, nullable=False)
    adjust_staff = db.Column(db.String(10), nullable=True)
    process_sheet_upload_status = db.Column(db.String(1), nullable=True)
    production_order_upload_status = db.Column(db.String(1), nullable=True)
    customer_product_name = db.Column(db.String(50), nullable=False)
    business_technical_remark = db.Column(db.String(100), nullable=True)
    business_material_remark = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<OrderShoe(order_shoe_id={self.order_shoe_id})>"

    def __name__(self):
        return "OrderShoe"


class OutsourceInfo(db.Model):
    __tablename__ = "outsource_info"

    outsource_info_id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True
    )
    outsource_type = db.Column(db.String(20), nullable=False)
    factory_id = db.Column(db.Integer, nullable=False)
    outsource_amount = db.Column(db.Integer, nullable=False)
    outsource_start_date = db.Column(db.Date, nullable=True)
    outsource_end_date = db.Column(db.Date, nullable=True)
    outsource_status = db.Column(db.SmallInteger, nullable=False)
    deadline_date = db.Column(db.Date, nullable=True)
    semifinished_estimated_outbound_date = db.Column(db.Date, nullable=True)
    semifinished_required = db.Column(db.Boolean, nullable=False)
    material_required = db.Column(db.Boolean, nullable=False)
    material_estimated_outbound_date = db.Column(db.Date, nullable=True)
    rejection_reason = db.Column(db.String(50), nullable=True)
    order_shoe_id = db.Column(db.BigInteger)
    outbound_counter = db.Column(db.SmallInteger, default=0)
    total_cost = db.Column(db.Numeric(10, 2), nullable=True)


class OutsourceCostDetail(db.Model):
    __tablename__ = "outsource_cost_detail"

    outsource_cost_detail_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True, nullable=False
    )
    item_name = db.Column(db.String(50), nullable=True)
    item_cost = db.Column(db.Numeric(10, 2), default=0)
    item_total_cost = db.Column(db.Numeric(10, 2), default=0)
    outsource_info_id = db.Column(db.Integer, nullable=False)
    remark = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<OutsourceCostDetail(id={self.outsource_cost_detail_id}, iteam_name={self.iteam_name}, item_cost={self.item_cost})>"


class OutsourceFactory(db.Model):
    __tablename__ = "outsource_factory"
    factory_id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True
    )
    factory_name = db.Column(db.String(50), nullable=False)
    is_deleted = db.Column(db.Boolean, default=0, nullable=False)


class OrderShoeProductionInfo(db.Model):
    __tablename__ = "order_shoe_production_info"

    production_info_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    cutting_line_group = db.Column(db.String(30), nullable=True)
    pre_sewing_line_group = db.Column(db.String(30), nullable=True)
    sewing_line_group = db.Column(db.String(30), nullable=True)
    molding_line_group = db.Column(db.String(30), nullable=True)
    is_cutting_outsourced = db.Column(db.SmallInteger, nullable=True)
    is_sewing_outsourced = db.Column(db.SmallInteger, nullable=True)
    is_molding_outsourced = db.Column(db.SmallInteger, nullable=True)
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
        db.BigInteger,
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
        nullable=False,
    )
    order_status_value = db.Column(db.Integer, nullable=False)
    order_id = db.Column(db.BigInteger)

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
        db.BigInteger,
    )
    purchase_divide_order_id = db.Column(
        db.BigInteger,
        nullable=False,
    )
    purchase_amount = db.Column(db.Numeric(10, 5), nullable=False)
    size_34_purchase_amount = db.Column(db.Integer, nullable=True)
    size_35_purchase_amount = db.Column(db.Integer, nullable=True)
    size_36_purchase_amount = db.Column(db.Integer, nullable=True)
    size_37_purchase_amount = db.Column(db.Integer, nullable=True)
    size_38_purchase_amount = db.Column(db.Integer, nullable=True)
    size_39_purchase_amount = db.Column(db.Integer, nullable=True)
    size_40_purchase_amount = db.Column(db.Integer, nullable=True)
    size_41_purchase_amount = db.Column(db.Integer, nullable=True)
    size_42_purchase_amount = db.Column(db.Integer, nullable=True)
    size_43_purchase_amount = db.Column(db.Integer, nullable=True)
    size_44_purchase_amount = db.Column(db.Integer, nullable=True)
    size_45_purchase_amount = db.Column(db.Integer, nullable=True)
    size_46_purchase_amount = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return (
            f"<PurchaseOrderItem(purchase_order_item_id={self.purchase_order_item_id})>"
        )

    def __name__(self):
        return "PurchaseOrderItem"


class AssetsPurchaseOrderItem(db.Model):
    __tablename__ = "assets_purchase_order_item"

    assets_purchase_order_item_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    material_variant_id = db.Column(db.BigInteger)
    remark = db.Column(db.String(50), nullable=True)
    purchase_divide_order_id = db.Column(db.BigInteger)
    purchase_amount = db.Column(db.Numeric(10, 5), nullable=True)
    material_specification = db.Column(db.String(50), nullable=True)
    size_34_purchase_amount = db.Column(db.Integer, nullable=True)
    size_35_purchase_amount = db.Column(db.Integer, nullable=True)
    size_36_purchase_amount = db.Column(db.Integer, nullable=True)
    size_37_purchase_amount = db.Column(db.Integer, nullable=True)
    size_38_purchase_amount = db.Column(db.Integer, nullable=True)
    size_39_purchase_amount = db.Column(db.Integer, nullable=True)
    size_40_purchase_amount = db.Column(db.Integer, nullable=True)
    size_41_purchase_amount = db.Column(db.Integer, nullable=True)
    size_42_purchase_amount = db.Column(db.Integer, nullable=True)
    size_43_purchase_amount = db.Column(db.Integer, nullable=True)
    size_44_purchase_amount = db.Column(db.Integer, nullable=True)
    size_45_purchase_amount = db.Column(db.Integer, nullable=True)
    size_46_purchase_amount = db.Column(db.Integer, nullable=True)
    size_type = db.Column(db.String(10), nullable=False, default="E")
    craft_name = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<AssetsPurchaseOrderItem(assets_purchase_order_item_id={self.assets_purchase_order_item_id})>"


class PurchaseDivideOrder(db.Model):
    __tablename__ = "purchase_divide_order"
    purchase_divide_order_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    purchase_order_id = db.Column(
        db.BigInteger,
    )
    purchase_divide_order_rid = db.Column(
        db.Integer,
    )
    purchase_divide_order_type = db.Column(db.String(1), nullable=False)
    purchase_order_remark = db.Column(db.String(100), nullable=True)
    purchase_order_environmental_request = db.Column(db.String(100), nullable=True)
    shipment_address = db.Column(db.String(100), nullable=True)
    shipment_deadline = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<PurchaseDivideOrder(purchase_divide_order_id={self.purchase_divide_order_id})>"


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_order"
    purchase_order_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    bom_id = db.Column(db.BigInteger)
    purchase_order_rid = db.Column(db.String(50), nullable=False)
    purchase_order_type = db.Column(db.String(1), nullable=False)
    purchase_order_issue_date = db.Column(db.Date, nullable=False)
    order_id = db.Column(db.BigInteger)
    order_shoe_id = db.Column(db.BigInteger)
    purchase_order_status = db.Column(db.String(1), nullable=True)

    def __repr__(self):
        return f"<PurchaseOrder(purchase_order_id={self.purchase_order_id})>"


class SemifinishedShoeStorage(db.Model):
    __tablename__ = "semifinished_shoe_storage"

    semifinished_shoe_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    semifinished_inbound_datetime = db.Column(db.DateTime)
    order_shoe_type_id = db.Column(db.BigInteger, nullable=False)
    semifinished_estimated_amount = db.Column(db.Integer, default=0, nullable=False)
    semifinished_actual_amount = db.Column(db.Integer, default=0, nullable=False)
    semifinished_amount = db.Column(db.Integer, default=0, nullable=False)
    semifinished_status = db.Column(db.SmallInteger)
    semifinished_object = db.Column(db.SmallInteger)


class Shoe(db.Model):
    __tablename__ = "shoe"
    shoe_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shoe_rid = db.Column(db.String(60), nullable=False)
    shoe_designer = db.Column(db.String(10), nullable=True)
    shoe_department_id = db.Column(db.String(10), nullable=True)
    def __repr__(self):
        return f"<Shoe(shoe_id={self.shoe_id})>"

    def __name__(self):
        return "Shoe"


class ShoeInboundRecord(db.Model):
    __tablename__ = "shoe_inbound_record"
    shoe_inbound_record_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    shoe_inbound_rid = db.Column(db.String(60), nullable=True)
    inbound_amount = db.Column(db.Integer, nullable=True)
    inbound_revenue = db.Column(db.DECIMAL(10, 2), nullable=True)
    subsequent_stock = db.Column(db.Integer, nullable=True)
    subsequent_revenue = db.Column(db.DECIMAL(10, 2), nullable=True)
    inbound_datetime = db.Column(db.DateTime, nullable=False)
    inbound_type = db.Column(db.SmallInteger, nullable=False, default=0, comment="0: 自产\n1: 外包")
    semifinished_shoe_storage_id = db.Column(db.BigInteger, nullable=True)
    finished_shoe_storage_id = db.Column(db.BigInteger, nullable=True)
    outsource_info_id = db.Column(db.Integer, nullable=True)
    remark = db.Column(db.String(40), nullable=True)


class ShoeOutboundRecord(db.Model):
    __tablename__ = "shoe_outbound_record"
    shoe_outbound_record_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    shoe_outbound_rid = db.Column(db.String(60), nullable=True)
    outbound_amount = db.Column(db.Integer, nullable=True)
    outbound_revenue = db.Column(db.DECIMAL(10, 2), nullable=True)
    subsequent_stock = db.Column(db.Integer, nullable=True)
    subsequent_revenue = db.Column(db.DECIMAL(10, 2), nullable=True)
    outbound_datetime = db.Column(db.DateTime, nullable=False)
    outbound_type = db.Column(db.SmallInteger, nullable=False, default=0)
    picker = db.Column(db.String(15), nullable=True)
    semifinished_shoe_storage_id = db.Column(db.BigInteger, nullable=True)
    finished_shoe_storage_id = db.Column(db.BigInteger, nullable=True)
    outsource_info_id = db.Column(db.Integer, nullable=True)
    remark = db.Column(db.String(40), nullable=True)


class Staff(db.Model):
    __tablename__ = "staff"
    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    staff_name = db.Column(db.String(20), nullable=False)
    character_id = db.Column(
        db.Integer,
    )
    department_id = db.Column(
        db.Integer,
    )
    staff_status = db.Column(db.SmallInteger, nullable=False, default=0)
    id_number = db.Column(db.String(18), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)

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
    size_34_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_35_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_36_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_37_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_38_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_39_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_40_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_41_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_42_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_43_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_44_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_45_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_46_estimated_inbound_amount = db.Column(db.Integer, default=0)
    total_estimated_inbound_amount = db.Column(db.Integer, default=0)
    size_34_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_35_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_36_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_37_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_38_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_39_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_40_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_41_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_42_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_43_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_44_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_45_actual_inbound_amount = db.Column(db.Integer, default=0)
    size_46_actual_inbound_amount = db.Column(db.Integer, default=0)
    total_actual_inbound_amount = db.Column(db.Integer, default=0)
    material_outsource_status = db.Column(db.SmallInteger, default=0, nullable=False)
    size_34_current_amount = db.Column(db.Integer, default=0)
    size_35_current_amount = db.Column(db.Integer, default=0)
    size_36_current_amount = db.Column(db.Integer, default=0)
    size_37_current_amount = db.Column(db.Integer, default=0)
    size_38_current_amount = db.Column(db.Integer, default=0)
    size_39_current_amount = db.Column(db.Integer, default=0)
    size_40_current_amount = db.Column(db.Integer, default=0)
    size_41_current_amount = db.Column(db.Integer, default=0)
    size_42_current_amount = db.Column(db.Integer, default=0)
    size_43_current_amount = db.Column(db.Integer, default=0)
    size_44_current_amount = db.Column(db.Integer, default=0)
    size_45_current_amount = db.Column(db.Integer, default=0)
    size_46_current_amount = db.Column(db.Integer, default=0)
    total_current_amount = db.Column(db.Integer, default=0)
    size_storage_type = db.Column(db.String(10), nullable=False, default="E")
    material_outsource_date = db.Column(db.Date, nullable=True)
    material_variant_id = db.Column(
        db.BigInteger,
    )
    department_id = db.Column(
        db.Integer,
    )
    material_specification = db.Column(db.String(50), nullable=True)
    order_id = db.Column(db.BigInteger)
    order_shoe_id = db.Column(db.BigInteger)
    unit_price = db.Column(db.Numeric(10, 2), nullable=True, default=0.00)
    purchase_divide_order_id = db.Column(db.BigInteger)
    material_estimated_arrival_date = db.Column(db.Date)
    material_storage_status = db.Column(db.SmallInteger, default=0)
    craft_name = db.Column(db.String(200), nullable=True)
    production_instruction_item_id = db.Column(db.BigInteger, nullable=True)

    def __repr__(self):
        return f"<SizeMaterialStorage {self.size_material_specification}>"
    
    def to_dict(obj):
        """Convert SQLAlchemy object to dictionary."""
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


class UnitPriceReportDetail(db.Model):
    __tablename__ = "unit_price_report_detail"
    report_id = db.Column(
        db.BigInteger,
        primary_key=True,
        nullable=False,
    )
    row_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
    )
    procedure_name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    note = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<UnitPriceReportDetail(report_id={self.report_id}, row_id={self.row_id}, procedure_name={self.procedure_name}, note={self.note})>"


class UnitPriceReport(db.Model):
    __tablename__ = "unit_price_report"
    report_id = db.Column(
        db.BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    order_shoe_id = db.Column(
        db.BigInteger,
    )
    submission_date = db.Column(db.Date, nullable=True)
    team = db.Column(db.String(10), nullable=True)
    status = db.Column(db.SmallInteger, nullable=False)
    rejection_reason = db.Column(db.String(40), nullable=True)
    price_sum = db.Column(db.DECIMAL(10, 2), default=0)

    def __repr__(self):
        return f"<UnitPriceReport(report_id={self.report_id})>"

    def to_dict(obj):
        """Convert SQLAlchemy object to dictionary."""
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


class UnitPriceReportTemplate(db.Model):
    __tablename__ = "unit_price_report_template"
    template_id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True
    )
    shoe_id = db.Column(db.Integer, nullable=False)
    team = db.Column(db.SmallInteger, nullable=False)


class ReportTemplateDetail(db.Model):
    __tablename__ = "report_template_detail"
    report_template_id = db.Column(db.Integer, primary_key=True, nullable=False)
    row_id = db.Column(db.Integer, primary_key=True, nullable=False)
    procedure_name = db.Column(db.String(50), nullable=True)
    price = db.Column(db.Float, nullable=True)
    note = db.Column(db.String(100), nullable=True)


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
    finished_inbound_datetime = db.Column(db.DateTime, nullable=False)
    order_shoe_type_id = db.Column(
        db.BigInteger,
    )
    finished_estimated_amount = db.Column(db.Integer, default=0, nullable=False)
    finished_actual_amount = db.Column(db.Integer, default=0, nullable=False)
    finished_amount = db.Column(db.Integer, default=0, nullable=False)
    finished_status = db.Column(
        db.SmallInteger,
        nullable=True,
    )


class BatchInfoType(db.Model):
    __tablename__ = "batch_info_type"
    batch_info_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_info_type_name = db.Column(db.String(10), nullable=False)
    batch_info_type_usage = db.Column(db.Integer, nullable=False)
    size_34_name = db.Column(db.String(5), nullable=True)
    size_35_name = db.Column(db.String(5), nullable=True)
    size_36_name = db.Column(db.String(5), nullable=True)
    size_37_name = db.Column(db.String(5), nullable=True)
    size_38_name = db.Column(db.String(5), nullable=True)
    size_39_name = db.Column(db.String(5), nullable=True)
    size_40_name = db.Column(db.String(5), nullable=True)
    size_41_name = db.Column(db.String(5), nullable=True)
    size_42_name = db.Column(db.String(5), nullable=True)
    size_43_name = db.Column(db.String(5), nullable=True)
    size_44_name = db.Column(db.String(5), nullable=True)
    size_45_name = db.Column(db.String(5), nullable=True)
    size_46_name = db.Column(db.String(2), nullable=True)

    def __repr__(self):
        return f"<BatchInfoType(batch_info_type_id={self.batch_info_type_id}, batch_info_type_name='{self.batch_info_type_name}')>"


class InboundRecord(db.Model):
    __tablename__ = "inbound_record"
    inbound_record_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    inbound_rid = db.Column(db.String(50), nullable=True)
    inbound_batch_id = db.Column(db.Integer, nullable=True)
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
    inbound_datetime = db.Column(db.DateTime, nullable=False)
    inbound_type = db.Column(db.SmallInteger, nullable=False)
    material_storage_id = db.Column(db.BigInteger, nullable=True)
    size_material_storage_id = db.Column(db.BigInteger, nullable=True)
    remark = db.Column(db.String(40), nullable=True)

    def __repr__(self):
        return f"<InboundRecord {self.inbound_rid}>"


class OutboundRecord(db.Model):
    __tablename__ = "outbound_record"
    outbound_record_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    outbound_rid = db.Column(db.String(60))
    outbound_batch_id = db.Column(db.Integer)
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
    outbound_datetime = db.Column(db.DateTime, nullable=False)
    outbound_type = db.Column(db.SmallInteger, nullable=False)
    outbound_department = db.Column(db.String(1), nullable=True)
    picker = db.Column(db.String(15), nullable=True)
    outbound_address = db.Column(db.String(100), nullable=True)
    material_storage_id = db.Column(
        db.BigInteger,
        nullable=True,
    )
    size_material_storage_id = db.Column(
        db.BigInteger,
        nullable=True,
    )
    outsource_info_id = db.Column(db.Integer, nullable=True)
    order_shoe_id = db.Column(db.BigInteger, nullable=True)
    remark = db.Column(db.String(40), nullable=True)
    composite_supplier_id = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<OutboundRecord {self.outbound_rid}>"


class DefaultBom(db.Model):
    __tablename__ = "default_bom"
    default_bom_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    bom_rid = db.Column(db.String(80), nullable=False)
    bom_type = db.Column(db.Integer, nullable=False)
    shoe_id = db.Column(db.Integer, nullable=False)
    bom_status = db.Column(db.String(1), nullable=True)
    bom_id = db.Column(db.BigInteger, nullable=False)

    def __repr__(self):
        return f"<DefaultBom(default_bom_id={self.default_bom_id})>"


class DefaultBomItem(db.Model):
    __tablename__ = "default_bom_item"
    default_bom_item_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    default_bom_id = db.Column(db.BigInteger, nullable=False)
    department_id = db.Column(db.Integer, nullable=False)
    remark = db.Column(db.String(50), nullable=True)
    material_specification = db.Column(db.String(50), nullable=True)
    material_model = db.Column(db.String(50), nullable=True)
    material_variant_id = db.Column(db.BigInteger, nullable=False)

    def __repr__(self):
        return f"<DefaultBomItem(default_bom_item_id={self.default_bom_item_id})>"


class ShoeType(db.Model):
    __tablename__ = "shoe_type"
    shoe_type_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    shoe_image_url = db.Column(db.String(100), nullable=True)
    color_id = db.Column(db.Integer, nullable=False)
    shoe_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<ShoeType(shoe_type_id={self.shoe_type_id})>"


class OrderShoeType(db.Model):
    __tablename__ = "order_shoe_type"
    order_shoe_type_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    shoe_type_id = db.Column(db.BigInteger, nullable=False)
    order_shoe_id = db.Column(db.BigInteger, nullable=False)
    cutting_amount = db.Column(db.Integer, default=0)
    pre_sewing_amount = db.Column(db.Integer, default=0)
    sewing_amount = db.Column(db.Integer, default=0)
    molding_amount = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.DECIMAL(10, 2), default=0)
    customer_color_name = db.Column(db.String(10), default="")
    currency_type = db.Column(db.String(4), nullable=True, default="")

    def __repr__(self):
        return f"<OrderShoeType(order_shoe_type_id={self.order_shoe_type_id})>"


class TotalBom(db.Model):
    __tablename__ = "total_bom"
    total_bom_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    total_bom_rid = db.Column(db.String(50), nullable=False)
    order_shoe_id = db.Column(db.BigInteger, nullable=False)

    def __repr__(self):
        return f"<TotalBom(total_bom_id={self.total_bom_id})>"


class ProductionInstruction(db.Model):
    __tablename__ = "production_instruction"
    production_instruction_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    order_shoe_id = db.Column(db.BigInteger, nullable=False)
    production_instruction_rid = db.Column(db.String(50), nullable=False)
    production_instruction_status = db.Column(db.String(1), nullable=False)
    origin_size = db.Column(db.String(5), nullable=True)
    size_range = db.Column(db.String(10), nullable=True)
    size_difference = db.Column(db.String(15), nullable=True)
    last_type = db.Column(db.String(20), nullable=True)
    burn_sole_craft = db.Column(db.String(100), nullable=True)
    craft_remark = db.Column(db.String(150), nullable=True)

    def __repr__(self):
        return f"<ProductionInstruction(production_instruction_id={self.production_instruction_id})>"


class ProductionInstructionItem(db.Model):
    __tablename__ = "production_instruction_item"
    production_instruction_item_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True
    )
    production_instruction_id = db.Column(db.BigInteger, nullable=False)
    material_variant_id = db.Column(db.BigInteger, nullable=False)
    material_specification = db.Column(db.String(50), nullable=True)
    remark = db.Column(db.String(50), nullable=True)
    department_id = db.Column(db.Integer, nullable=False)
    is_pre_purchase = db.Column(db.Boolean, nullable=False)
    material_type = db.Column(db.String(1), nullable=False)
    order_shoe_type_id = db.Column(db.BigInteger, nullable=False)
    material_second_type = db.Column(db.String(10), nullable=False)
    pre_craft_name = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<ProductionInstructionItem(production_instruction_item_id={self.production_instruction_item_id})>"

class CraftSheet(db.Model):
    __tablename__ = "craft_sheet"
    craft_sheet_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    craft_sheet_rid = db.Column(db.String(40), nullable=False)
    order_shoe_id = db.Column(db.BigInteger, nullable=False)
    cut_die_staff = db.Column(db.String(20), nullable=True)
    production_remark = db.Column(db.String(50), nullable=True)
    cutting_special_process = db.Column(db.String(150), nullable=True)
    sewing_special_process = db.Column(db.String(150), nullable=True)
    molding_special_process = db.Column(db.String(200), nullable=True)
    post_processing_comment = db.Column(db.String(300), nullable=True)
    oily_glue = db.Column(db.String(300), nullable=True)
    cut_die_img_path = db.Column(db.String(100), nullable=True)
    pic_note_img_path = db.Column(db.String(100), nullable=True)
    craft_sheet_status = db.Column(db.String(1), nullable=False)
    reviewer = db.Column(db.String(20), nullable=True)
    def __repr__(self):
        return f"<CraftSheet(craft_sheet_id={self.craft_sheet_id})>"

class CraftSheetItem(db.Model):
    __tablename__ = "craft_sheet_item"
    craft_sheet_item_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    craft_sheet_id = db.Column(db.BigInteger, nullable=False)
    material_variant_id = db.Column(db.BigInteger, nullable=False)
    material_specification = db.Column(db.String(50), nullable=True)
    department_id = db.Column(db.Integer, nullable=False)
    material_type = db.Column(db.String(1), nullable=False)
    material_second_type = db.Column(db.String(10), nullable=False)
    order_shoe_type_id = db.Column(db.BigInteger, nullable=False)
    remark = db.Column(db.String(50), nullable=True)
    craft_name = db.Column(db.String(200), nullable=True)
    material_source = db.Column(db.String(1), nullable=True)
    pairs = db.Column(db.DECIMAL(10, 5), nullable=True)
    unit_usage = db.Column(db.DECIMAL(10, 5), nullable=True)
    total_usage = db.Column(db.DECIMAL(10, 5), nullable=True)
    after_usage_symbol = db.Column(db.String(1), nullable=True)
    production_instruction_item_id = db.Column(db.BigInteger, nullable=True)
    def __repr__(self):
        return f"<CraftSheetItem(craft_sheet_item_id={self.craft_sheet_item_id})>"
    
class ProductionLine(db.Model):
    __tablename__ = "production_line"

    production_line_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    production_line_name = db.Column(db.String(15), nullable=False)
    production_team = db.Column(db.String(10), nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=0)

    def __repr__(self):
        return f"<ProductionLine(production_line_id={self.production_line_id})>"
