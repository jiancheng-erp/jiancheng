from flask import Blueprint, jsonify, request
from sqlalchemy import text, and_
from app_config import db
from models import (
    Material,
    MaterialType,
    Supplier,
    BomItem,
    Bom,
    TotalBom,
    PurchaseOrderItem,
    PurchaseDivideOrder,
    PurchaseOrder,
    ProductionInstruction,
    ProductionInstructionItem,
    CraftSheet,
    CraftSheetItem,
    Order,
    OrderShoe,
    Shoe,
)

material_batch_edit_bp = Blueprint("material_batch_edit_bp", __name__)


@material_batch_edit_bp.route("/material/search-order-shoes", methods=["GET"])
def search_order_shoes():
    """
    根据订单号或鞋型号搜索订单-鞋款列表
    参数: keyword (模糊搜索订单号或鞋型号)
    """
    keyword = request.args.get("keyword", "", type=str).strip()
    if not keyword:
        return jsonify({"result": []}), 200

    sql = text("""
        SELECT
            os.order_shoe_id,
            o.order_rid,
            s.shoe_rid,
            os.customer_product_name
        FROM order_shoe os
        JOIN `order` o ON o.order_id = os.order_id
        JOIN shoe s ON s.shoe_id = os.shoe_id
        WHERE o.order_rid LIKE :kw OR s.shoe_rid LIKE :kw
        ORDER BY o.order_rid, s.shoe_rid
        LIMIT 50
    """)
    rows = db.session.execute(sql, {"kw": f"%{keyword}%"}).fetchall()
    result = [
        {
            "orderShoeId": r[0],
            "orderRid": r[1],
            "shoeRid": r[2],
            "customerProductName": r[3] or "",
        }
        for r in rows
    ]
    return jsonify({"result": result})


@material_batch_edit_bp.route("/material/ordershoe-color-types", methods=["GET"])
def get_ordershoe_color_types():
    """
    获取指定 order_shoe_id 下的所有配色 (OrderShoeType)，含颜色名称
    """
    order_shoe_id = request.args.get("orderShoeId", 0, type=int)
    if not order_shoe_id:
        return jsonify({"error": "缺少 orderShoeId 参数"}), 400

    sql = text("""
        SELECT
            ost.order_shoe_type_id,
            c.color_name,
            ost.customer_color_name
        FROM order_shoe_type ost
        JOIN shoe_type st ON st.shoe_type_id = ost.shoe_type_id
        JOIN color c ON c.color_id = st.color_id
        WHERE ost.order_shoe_id = :osid
        ORDER BY ost.order_shoe_type_id
    """)
    rows = db.session.execute(sql, {"osid": order_shoe_id}).fetchall()
    result = [
        {
            "orderShoeTypeId": r[0],
            "colorName": r[1] or "",
            "customerColorName": r[2] or "",
        }
        for r in rows
    ]
    return jsonify({"result": result})


@material_batch_edit_bp.route("/material/ordershoe-materials", methods=["GET"])
def get_ordershoe_materials():
    """
    获取指定 order_shoe_id + order_shoe_type_id（配色）对应的所有文档材料信息。
    跨四张表查询：投产指令单、工艺单、BOM、采购订单
    按配色级别精确过滤材料。
    """
    order_shoe_id = request.args.get("orderShoeId", 0, type=int)
    order_shoe_type_id = request.args.get("orderShoeTypeId", 0, type=int)
    if not order_shoe_id:
        return jsonify({"error": "缺少 orderShoeId 参数"}), 400

    materials = []

    # 1. 投产指令单 — 按 order_shoe_type_id 过滤
    pi_sql = """
        SELECT
            pii.production_instruction_item_id AS item_id,
            pii.material_id,
            m.material_name,
            s.supplier_name,
            pii.material_model,
            pii.material_specification,
            pii.color,
            pii.material_type,
            pii.material_second_type,
            pii.remark,
            pii.department_id,
            pii.order_shoe_type_id
        FROM production_instruction_item pii
        JOIN production_instruction pi
            ON pi.production_instruction_id = pii.production_instruction_id
        JOIN material m ON m.material_id = pii.material_id
        LEFT JOIN supplier s ON s.supplier_id = m.material_supplier
        WHERE pi.order_shoe_id = :osid
    """
    params = {"osid": order_shoe_id}
    if order_shoe_type_id:
        pi_sql += " AND pii.order_shoe_type_id = :ostid"
        params["ostid"] = order_shoe_type_id
    pi_sql += " ORDER BY pii.material_type, m.material_name"

    pi_items = db.session.execute(text(pi_sql), params).fetchall()
    for r in pi_items:
        materials.append({
            "docType": "production_instruction_item",
            "docLabel": "投产指令单",
            "itemId": r[0],
            "materialId": r[1],
            "materialName": r[2] or "",
            "supplierName": r[3] or "",
            "materialModel": r[4] or "",
            "materialSpecification": r[5] or "",
            "color": r[6] or "",
            "materialType": r[7] or "",
            "materialSecondType": r[8] or "",
            "remark": r[9] or "",
            "departmentId": r[10],
            "orderShoeTypeId": r[11],
        })

    # 2. 工艺单 — 按 order_shoe_type_id 过滤
    cs_sql = """
        SELECT
            csi.craft_sheet_item_id AS item_id,
            csi.material_id,
            m.material_name,
            s.supplier_name,
            csi.material_model,
            csi.material_specification,
            csi.color,
            csi.material_type,
            csi.material_second_type,
            csi.craft_name,
            csi.department_id,
            csi.production_instruction_item_id,
            csi.order_shoe_type_id
        FROM craft_sheet_item csi
        JOIN craft_sheet cs ON cs.craft_sheet_id = csi.craft_sheet_id
        JOIN material m ON m.material_id = csi.material_id
        LEFT JOIN supplier s ON s.supplier_id = m.material_supplier
        WHERE cs.order_shoe_id = :osid
    """
    cs_params = {"osid": order_shoe_id}
    if order_shoe_type_id:
        cs_sql += " AND csi.order_shoe_type_id = :ostid"
        cs_params["ostid"] = order_shoe_type_id
    cs_sql += " ORDER BY csi.material_type, m.material_name"

    cs_items = db.session.execute(text(cs_sql), cs_params).fetchall()
    for r in cs_items:
        materials.append({
            "docType": "craft_sheet_item",
            "docLabel": "工艺单",
            "itemId": r[0],
            "materialId": r[1],
            "materialName": r[2] or "",
            "supplierName": r[3] or "",
            "materialModel": r[4] or "",
            "materialSpecification": r[5] or "",
            "color": r[6] or "",
            "materialType": r[7] or "",
            "materialSecondType": r[8] or "",
            "craftName": r[9] or "",
            "departmentId": r[10],
            "productionInstructionItemId": r[11],
            "orderShoeTypeId": r[12],
        })

    # 3. BOM — 通过 bom.order_shoe_type_id 过滤
    bom_sql = """
        SELECT
            bi.bom_item_id AS item_id,
            bi.material_id,
            m.material_name,
            s.supplier_name,
            bi.material_model,
            bi.material_specification,
            bi.bom_item_color AS color,
            bi.department_id,
            bi.material_second_type,
            bi.craft_name,
            bi.production_instruction_item_id,
            b.bom_type,
            b.order_shoe_type_id
        FROM bom_item bi
        JOIN bom b ON b.bom_id = bi.bom_id
        JOIN total_bom tb ON tb.total_bom_id = b.total_bom_id
        JOIN material m ON m.material_id = bi.material_id
        LEFT JOIN supplier s ON s.supplier_id = m.material_supplier
        WHERE tb.order_shoe_id = :osid
    """
    bom_params = {"osid": order_shoe_id}
    if order_shoe_type_id:
        bom_sql += " AND b.order_shoe_type_id = :ostid"
        bom_params["ostid"] = order_shoe_type_id
    bom_sql += " ORDER BY b.bom_type, m.material_name"

    bom_items = db.session.execute(text(bom_sql), bom_params).fetchall()
    for r in bom_items:
        bom_type_label = "一次BOM" if r[11] == 0 else "二次BOM"
        materials.append({
            "docType": "bom_item",
            "docLabel": f"BOM({bom_type_label})",
            "itemId": r[0],
            "materialId": r[1],
            "materialName": r[2] or "",
            "supplierName": r[3] or "",
            "materialModel": r[4] or "",
            "materialSpecification": r[5] or "",
            "color": r[6] or "",
            "departmentId": r[7],
            "materialSecondType": r[8] or "",
            "craftName": r[9] or "",
            "productionInstructionItemId": r[10],
            "bomType": r[11],
            "orderShoeTypeId": r[12],
        })

    # 4. 采购订单 — 通过 bom_item -> bom.order_shoe_type_id 过滤
    po_sql = """
        SELECT
            poi.purchase_order_item_id AS item_id,
            poi.material_id,
            m.material_name,
            s.supplier_name,
            poi.material_model,
            poi.material_specification,
            poi.color,
            poi.craft_name,
            poi.remark,
            poi.bom_item_id,
            b.order_shoe_type_id
        FROM purchase_order_item poi
        JOIN purchase_divide_order pdo
            ON pdo.purchase_divide_order_id = poi.purchase_divide_order_id
        JOIN purchase_order po
            ON po.purchase_order_id = pdo.purchase_order_id
        JOIN material m ON m.material_id = poi.material_id
        LEFT JOIN supplier s ON s.supplier_id = m.material_supplier
        LEFT JOIN bom_item bi ON bi.bom_item_id = poi.bom_item_id
        LEFT JOIN bom b ON b.bom_id = bi.bom_id
        WHERE po.order_shoe_id = :osid
    """
    po_params = {"osid": order_shoe_id}
    if order_shoe_type_id:
        po_sql += " AND b.order_shoe_type_id = :ostid"
        po_params["ostid"] = order_shoe_type_id
    po_sql += " ORDER BY m.material_name"

    po_items = db.session.execute(text(po_sql), po_params).fetchall()
    for r in po_items:
        materials.append({
            "docType": "purchase_order_item",
            "docLabel": "采购订单",
            "itemId": r[0],
            "materialId": r[1],
            "materialName": r[2] or "",
            "supplierName": r[3] or "",
            "materialModel": r[4] or "",
            "materialSpecification": r[5] or "",
            "color": r[6] or "",
            "craftName": r[7] or "",
            "remark": r[8] or "",
            "bomItemId": r[9],
            "orderShoeTypeId": r[10],
        })

    # 按 material_id 分组返回
    grouped = {}
    for item in materials:
        mid = item["materialId"]
        if mid not in grouped:
            grouped[mid] = {
                "materialId": mid,
                "materialName": item["materialName"],
                "supplierName": item["supplierName"],
                "items": [],
            }
        grouped[mid]["items"].append(item)

    result = sorted(grouped.values(), key=lambda x: x["materialName"])
    return jsonify({"result": result})


@material_batch_edit_bp.route("/material/batch-edit-materials", methods=["POST"])
def batch_edit_materials():
    """
    批量编辑材料属性，同步更新指定配色下所有相关文档。

    请求体:
    {
        "orderShoeId": 123,
        "orderShoeTypeId": 456,        // 配色 ID，精确到颜色级别
        "materialId": 789,
        "newMaterialId": 111,           // 可选: 替换为另一个材料
        "newModel": "新型号",
        "newSpecification": "新规格",
        "newColor": "新颜色",
        "docTypes": ["production_instruction_item", "craft_sheet_item",
                     "bom_item", "purchase_order_item"]
    }
    """
    data = request.get_json()
    order_shoe_id = data.get("orderShoeId")
    order_shoe_type_id = data.get("orderShoeTypeId")
    material_id = data.get("materialId")
    new_material_id = data.get("newMaterialId")
    new_model = data.get("newModel")
    new_spec = data.get("newSpecification")
    new_color = data.get("newColor")
    doc_types = data.get("docTypes", [
        "production_instruction_item",
        "craft_sheet_item",
        "bom_item",
        "purchase_order_item",
    ])

    if not order_shoe_id or not material_id:
        return jsonify({"error": "缺少 orderShoeId 或 materialId"}), 400

    if new_model is None and new_spec is None and new_color is None and not new_material_id:
        return jsonify({"error": "没有需要修改的字段"}), 400

    if new_material_id:
        new_mat = Material.query.get(new_material_id)
        if not new_mat:
            return jsonify({"error": f"新材料 ID {new_material_id} 不存在"}), 404

    total_updated = 0
    update_details = {}

    try:
        if "production_instruction_item" in doc_types:
            count = _update_production_instruction_items(
                order_shoe_id, order_shoe_type_id, material_id,
                new_material_id, new_model, new_spec, new_color
            )
            total_updated += count
            update_details["投产指令单"] = count

        if "craft_sheet_item" in doc_types:
            count = _update_craft_sheet_items(
                order_shoe_id, order_shoe_type_id, material_id,
                new_material_id, new_model, new_spec, new_color
            )
            total_updated += count
            update_details["工艺单"] = count

        if "bom_item" in doc_types:
            count = _update_bom_items(
                order_shoe_id, order_shoe_type_id, material_id,
                new_material_id, new_model, new_spec, new_color
            )
            total_updated += count
            update_details["BOM"] = count

        if "purchase_order_item" in doc_types:
            count = _update_purchase_order_items(
                order_shoe_id, order_shoe_type_id, material_id,
                new_material_id, new_model, new_spec, new_color
            )
            total_updated += count
            update_details["采购订单"] = count

        db.session.commit()

        detail_str = ", ".join(f"{k}: {v}条" for k, v in update_details.items() if v > 0)
        return jsonify({
            "message": f"同步修改完成，共更新 {total_updated} 条记录 ({detail_str})",
            "totalUpdated": total_updated,
            "details": update_details,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"批量修改失败: {str(e)}"}), 500


def _build_update_values(model_cls, new_material_id, new_model, new_spec, new_color, color_col="color"):
    """构建更新字段字典"""
    vals = {}
    if new_material_id:
        vals[model_cls.material_id] = new_material_id
    if new_model is not None:
        vals[model_cls.material_model] = new_model
    if new_spec is not None:
        vals[model_cls.material_specification] = new_spec
    if new_color is not None:
        color_attr = getattr(model_cls, color_col)
        vals[color_attr] = new_color
    return vals


def _update_production_instruction_items(
    order_shoe_id, order_shoe_type_id, material_id,
    new_material_id, new_model, new_spec, new_color
):
    """更新投产指令单中的材料 — 按配色过滤"""
    pi_ids = db.session.execute(text(
        "SELECT production_instruction_id FROM production_instruction WHERE order_shoe_id = :osid"
    ), {"osid": order_shoe_id}).fetchall()

    if not pi_ids:
        return 0

    pi_id_list = [r[0] for r in pi_ids]
    conditions = [
        ProductionInstructionItem.production_instruction_id.in_(pi_id_list),
        ProductionInstructionItem.material_id == material_id,
    ]
    if order_shoe_type_id:
        conditions.append(
            ProductionInstructionItem.order_shoe_type_id == order_shoe_type_id
        )

    vals = _build_update_values(
        ProductionInstructionItem, new_material_id, new_model, new_spec, new_color
    )
    if not vals:
        return 0

    return ProductionInstructionItem.query.filter(
        and_(*conditions)
    ).update(vals, synchronize_session=False)


def _update_craft_sheet_items(
    order_shoe_id, order_shoe_type_id, material_id,
    new_material_id, new_model, new_spec, new_color
):
    """更新工艺单中的材料 — 按配色过滤"""
    cs_ids = db.session.execute(text(
        "SELECT craft_sheet_id FROM craft_sheet WHERE order_shoe_id = :osid"
    ), {"osid": order_shoe_id}).fetchall()

    if not cs_ids:
        return 0

    cs_id_list = [r[0] for r in cs_ids]
    conditions = [
        CraftSheetItem.craft_sheet_id.in_(cs_id_list),
        CraftSheetItem.material_id == material_id,
    ]
    if order_shoe_type_id:
        conditions.append(CraftSheetItem.order_shoe_type_id == order_shoe_type_id)

    vals = _build_update_values(
        CraftSheetItem, new_material_id, new_model, new_spec, new_color
    )
    if not vals:
        return 0

    return CraftSheetItem.query.filter(
        and_(*conditions)
    ).update(vals, synchronize_session=False)


def _update_bom_items(
    order_shoe_id, order_shoe_type_id, material_id,
    new_material_id, new_model, new_spec, new_color
):
    """更新BOM中的材料 — 按配色过滤"""
    bom_sql = """
        SELECT b.bom_id FROM bom b
        JOIN total_bom tb ON tb.total_bom_id = b.total_bom_id
        WHERE tb.order_shoe_id = :osid
    """
    bom_params = {"osid": order_shoe_id}
    if order_shoe_type_id:
        bom_sql += " AND b.order_shoe_type_id = :ostid"
        bom_params["ostid"] = order_shoe_type_id

    bom_ids = db.session.execute(text(bom_sql), bom_params).fetchall()
    if not bom_ids:
        return 0

    bom_id_list = [r[0] for r in bom_ids]
    conditions = [
        BomItem.bom_id.in_(bom_id_list),
        BomItem.material_id == material_id,
    ]
    vals = _build_update_values(
        BomItem, new_material_id, new_model, new_spec, new_color,
        color_col="bom_item_color"
    )
    if not vals:
        return 0

    return BomItem.query.filter(
        and_(*conditions)
    ).update(vals, synchronize_session=False)


def _update_purchase_order_items(
    order_shoe_id, order_shoe_type_id, material_id,
    new_material_id, new_model, new_spec, new_color
):
    """更新采购订单中的材料 — 通过 bom_item -> bom 按配色过滤"""
    # 先找到该配色下的所有 bom_item_id
    bom_item_sql = """
        SELECT bi.bom_item_id FROM bom_item bi
        JOIN bom b ON b.bom_id = bi.bom_id
        JOIN total_bom tb ON tb.total_bom_id = b.total_bom_id
        WHERE tb.order_shoe_id = :osid AND bi.material_id = :mid
    """
    bp = {"osid": order_shoe_id, "mid": material_id}
    if order_shoe_type_id:
        bom_item_sql += " AND b.order_shoe_type_id = :ostid"
        bp["ostid"] = order_shoe_type_id

    bom_item_ids = db.session.execute(text(bom_item_sql), bp).fetchall()

    if not bom_item_ids:
        # 如果没有关联 bom_item，退回到通过 purchase_order.order_shoe_id 过滤
        pdo_ids = db.session.execute(text("""
            SELECT pdo.purchase_divide_order_id
            FROM purchase_divide_order pdo
            JOIN purchase_order po ON po.purchase_order_id = pdo.purchase_order_id
            WHERE po.order_shoe_id = :osid
        """), {"osid": order_shoe_id}).fetchall()
        if not pdo_ids:
            return 0
        pdo_id_list = [r[0] for r in pdo_ids]
        conditions = [
            PurchaseOrderItem.purchase_divide_order_id.in_(pdo_id_list),
            PurchaseOrderItem.material_id == material_id,
        ]
    else:
        bom_item_id_list = [r[0] for r in bom_item_ids]
        conditions = [
            PurchaseOrderItem.bom_item_id.in_(bom_item_id_list),
        ]

    vals = _build_update_values(
        PurchaseOrderItem, new_material_id, new_model, new_spec, new_color
    )
    if not vals:
        return 0

    return PurchaseOrderItem.query.filter(
        and_(*conditions)
    ).update(vals, synchronize_session=False)
