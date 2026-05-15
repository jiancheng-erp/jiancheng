"""
材料同步修改 (Material Batch Edit)
===================================

设计原则
--------
1. **以投产指令单 (production_instruction_item) 为根**：每条 PI 项是材料定义的源点。
   工艺单项 (craft_sheet_item)、BOM 项 (bom_item) 通过 `production_instruction_item_id`
   FK 反向链接到 PI 项；采购订单项 (purchase_order_item) 通过 `bom_item_id` 反向链接到 BOM 项。

2. **始终全量联动**：用户不再勾选文档类型。一次操作沿 PI → CraftSheet/BOM → PO 链路
   全部更新，避免链路上 material_id 因历史更新而漂移导致漏改。

3. **范围 (scope)**：
   - `color` ：仅当前配色 (order_shoe_type_id)。
   - `shoe`  ：整鞋款 (order_shoe_id)，所有配色下相同 material_id 的 PI 项一起改。

4. **供应商变化 → 自动拆分 purchase_divide_order**：
   `purchase_divide_order` 在系统中本就按"供应商"分组（rid 后 4 位 = supplier_id）。
   当替换后的新材料供应商与原 PO 项所在的 pdo 供应商不一致时，把该 PO 项移到
   同一 `purchase_order` 下、对应新供应商的 pdo（若不存在则按既有 rid 约定新建）。

5. **链路追踪 + 兜底匹配**：优先按 FK 链路追踪。链路缺失（历史脏数据）时按
   (order_shoe_id, [order_shoe_type_id], material_id=旧) 做兜底匹配。

主要接口
--------
GET  /material/search-order-shoes              订单/鞋款搜索
GET  /material/ordershoe-color-types           列出配色 (order_shoe_type)
GET  /material/ordershoe-materials             获取该订单鞋款下所有材料（按 material_id 聚合）
POST /material/batch-edit-materials/preview    预览：列出将被更新的记录数 & 供应商变化告警
POST /material/batch-edit-materials            执行同步修改
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import text, bindparam
from app_config import db
from models import (
    Material,
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
)

material_batch_edit_bp = Blueprint("material_batch_edit_bp", __name__)


# ===========================================================================
# 1. 基础查询：订单 / 配色
# ===========================================================================

@material_batch_edit_bp.route("/material/search-order-shoes", methods=["GET"])
def search_order_shoes():
    keyword = request.args.get("keyword", "", type=str).strip()
    if not keyword:
        return jsonify({"result": []}), 200

    sql = text("""
        SELECT os.order_shoe_id, o.order_rid, s.shoe_rid, os.customer_product_name
        FROM order_shoe os
        JOIN `order` o ON o.order_id = os.order_id
        JOIN shoe s ON s.shoe_id = os.shoe_id
        WHERE o.order_rid LIKE :kw OR s.shoe_rid LIKE :kw
        ORDER BY o.order_rid, s.shoe_rid
        LIMIT 50
    """)
    rows = db.session.execute(sql, {"kw": f"%{keyword}%"}).fetchall()
    return jsonify({"result": [
        {
            "orderShoeId": r[0],
            "orderRid": r[1],
            "shoeRid": r[2],
            "customerProductName": r[3] or "",
        }
        for r in rows
    ]})


@material_batch_edit_bp.route("/material/ordershoe-color-types", methods=["GET"])
def get_ordershoe_color_types():
    order_shoe_id = request.args.get("orderShoeId", 0, type=int)
    if not order_shoe_id:
        return jsonify({"error": "缺少 orderShoeId 参数"}), 400

    sql = text("""
        SELECT ost.order_shoe_type_id, c.color_name, ost.customer_color_name
        FROM order_shoe_type ost
        JOIN shoe_type st ON st.shoe_type_id = ost.shoe_type_id
        JOIN color c ON c.color_id = st.color_id
        WHERE ost.order_shoe_id = :osid
        ORDER BY ost.order_shoe_type_id
    """)
    rows = db.session.execute(sql, {"osid": order_shoe_id}).fetchall()
    return jsonify({"result": [
        {
            "orderShoeTypeId": r[0],
            "colorName": r[1] or "",
            "customerColorName": r[2] or "",
        }
        for r in rows
    ]})


# ===========================================================================
# 2. 材料一览：按 material_id 聚合，并展开各文档记录
# ===========================================================================

@material_batch_edit_bp.route("/material/ordershoe-materials", methods=["GET"])
def get_ordershoe_materials():
    """
    返回:
    [
      {
        materialId, materialName, supplierName, materialSecondType,
        colorPresence: [orderShoeTypeId, ...],  # 该材料在哪些配色出现
        items: [ ...4 类文档行... ],
      },
      ...
    ]
    """
    order_shoe_id = request.args.get("orderShoeId", 0, type=int)
    order_shoe_type_id = request.args.get("orderShoeTypeId", 0, type=int)
    if not order_shoe_id:
        return jsonify({"error": "缺少 orderShoeId 参数"}), 400

    items = []

    # 1) 投产指令单
    pi_sql = """
        SELECT pii.production_instruction_item_id, pii.material_id, m.material_name,
               s.supplier_name, pii.material_model, pii.material_specification,
               pii.color, pii.material_type, pii.material_second_type,
               pii.remark, pii.department_id, pii.order_shoe_type_id
        FROM production_instruction_item pii
        JOIN production_instruction pi ON pi.production_instruction_id = pii.production_instruction_id
        JOIN material m ON m.material_id = pii.material_id
        LEFT JOIN supplier s ON s.supplier_id = m.material_supplier
        WHERE pi.order_shoe_id = :osid
    """
    params = {"osid": order_shoe_id}
    if order_shoe_type_id:
        pi_sql += " AND pii.order_shoe_type_id = :ostid"
        params["ostid"] = order_shoe_type_id
    for r in db.session.execute(text(pi_sql), params).fetchall():
        items.append({
            "docType": "production_instruction_item", "docLabel": "投产指令单",
            "itemId": r[0], "materialId": r[1], "materialName": r[2] or "",
            "supplierName": r[3] or "", "materialModel": r[4] or "",
            "materialSpecification": r[5] or "", "color": r[6] or "",
            "materialType": r[7] or "", "materialSecondType": r[8] or "",
            "remark": r[9] or "", "departmentId": r[10],
            "orderShoeTypeId": r[11], "linkRootId": r[0],
        })

    # 2) 工艺单
    cs_sql = """
        SELECT csi.craft_sheet_item_id, csi.material_id, m.material_name,
               s.supplier_name, csi.material_model, csi.material_specification,
               csi.color, csi.material_type, csi.material_second_type,
               csi.craft_name, csi.department_id, csi.production_instruction_item_id,
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
    for r in db.session.execute(text(cs_sql), cs_params).fetchall():
        items.append({
            "docType": "craft_sheet_item", "docLabel": "工艺单",
            "itemId": r[0], "materialId": r[1], "materialName": r[2] or "",
            "supplierName": r[3] or "", "materialModel": r[4] or "",
            "materialSpecification": r[5] or "", "color": r[6] or "",
            "materialType": r[7] or "", "materialSecondType": r[8] or "",
            "craftName": r[9] or "", "departmentId": r[10],
            "productionInstructionItemId": r[11], "orderShoeTypeId": r[12],
            "linkRootId": r[11],
        })

    # 3) BOM
    bom_sql = """
        SELECT bi.bom_item_id, bi.material_id, m.material_name,
               s.supplier_name, bi.material_model, bi.material_specification,
               bi.bom_item_color, bi.department_id, bi.material_second_type,
               bi.craft_name, bi.production_instruction_item_id,
               b.bom_type, b.order_shoe_type_id
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
    for r in db.session.execute(text(bom_sql), bom_params).fetchall():
        items.append({
            "docType": "bom_item",
            "docLabel": "BOM(一次)" if r[11] == 0 else "BOM(二次)",
            "itemId": r[0], "materialId": r[1], "materialName": r[2] or "",
            "supplierName": r[3] or "", "materialModel": r[4] or "",
            "materialSpecification": r[5] or "", "color": r[6] or "",
            "departmentId": r[7], "materialSecondType": r[8] or "",
            "craftName": r[9] or "", "productionInstructionItemId": r[10],
            "bomType": r[11], "orderShoeTypeId": r[12],
            "linkRootId": r[10],
        })

    # 4) 采购订单
    po_sql = """
        SELECT poi.purchase_order_item_id, poi.material_id, m.material_name,
               s.supplier_name, poi.material_model, poi.material_specification,
               poi.color, poi.craft_name, poi.remark, poi.bom_item_id,
               b.order_shoe_type_id, pdo.purchase_divide_order_id,
               pdo.purchase_divide_order_rid, po.purchase_order_id,
               po.purchase_order_rid
        FROM purchase_order_item poi
        JOIN purchase_divide_order pdo ON pdo.purchase_divide_order_id = poi.purchase_divide_order_id
        JOIN purchase_order po ON po.purchase_order_id = pdo.purchase_order_id
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
    for r in db.session.execute(text(po_sql), po_params).fetchall():
        items.append({
            "docType": "purchase_order_item", "docLabel": "采购订单",
            "itemId": r[0], "materialId": r[1], "materialName": r[2] or "",
            "supplierName": r[3] or "", "materialModel": r[4] or "",
            "materialSpecification": r[5] or "", "color": r[6] or "",
            "craftName": r[7] or "", "remark": r[8] or "",
            "bomItemId": r[9], "orderShoeTypeId": r[10],
            "purchaseDivideOrderId": r[11], "purchaseDivideOrderRid": r[12] or "",
            "purchaseOrderId": r[13], "purchaseOrderRid": r[14] or "",
            "linkRootId": r[9],
        })

    # 按 material_id 聚合
    grouped = {}
    for it in items:
        mid = it["materialId"]
        if mid not in grouped:
            grouped[mid] = {
                "materialId": mid,
                "materialName": it["materialName"],
                "supplierName": it["supplierName"],
                "materialSecondType": it.get("materialSecondType", ""),
                "items": [],
                "colorPresence": set(),
            }
        if it.get("orderShoeTypeId"):
            grouped[mid]["colorPresence"].add(it["orderShoeTypeId"])
        grouped[mid]["items"].append(it)

    result = []
    for g in grouped.values():
        g["colorPresence"] = sorted(g["colorPresence"])
        result.append(g)

    result.sort(key=lambda x: x["materialName"])
    return jsonify({"result": result})


# ===========================================================================
# 3. 预览 & 执行：同步修改
# ===========================================================================

def _resolve_targets(order_shoe_id, scope, order_shoe_type_id, material_id):
    """
    根据范围确定本次操作要更新的目标集合（以 PI item 为根）。

    Returns: dict {
        "pi_item_ids":   [int],   # PI 项 id（链路根）
        "cs_item_ids":   [int],   # 由 PI 项链路找到 + 兜底匹配 的工艺单项
        "bom_item_ids":  [int],   # 由 PI 项链路找到 + 兜底匹配 的 BOM 项
        "po_item_ids":   [int],   # 由 BOM 项链路找到 + 兜底匹配 的采购单项
        "scope_ostids":  [int],   # 本次操作覆盖的配色集合（用于兜底匹配）
    }
    """
    # 1) PI item 候选：order_shoe_id × material_id × scope
    pi_sql = """
        SELECT pii.production_instruction_item_id, pii.order_shoe_type_id
        FROM production_instruction_item pii
        JOIN production_instruction pi ON pi.production_instruction_id = pii.production_instruction_id
        WHERE pi.order_shoe_id = :osid AND pii.material_id = :mid
    """
    p = {"osid": order_shoe_id, "mid": material_id}
    if scope == "color":
        pi_sql += " AND pii.order_shoe_type_id = :ostid"
        p["ostid"] = order_shoe_type_id
    pi_rows = db.session.execute(text(pi_sql), p).fetchall()
    pi_item_ids = [r[0] for r in pi_rows]
    scope_ostids = sorted({r[1] for r in pi_rows if r[1] is not None})

    # 若 scope=color 但 PI item 缺失，仍以选中的 ostid 作为兜底匹配范围
    if scope == "color" and order_shoe_type_id and order_shoe_type_id not in scope_ostids:
        scope_ostids.append(order_shoe_type_id)

    # 2) 工艺单：链路 + 兜底
    cs_item_ids = set()
    if pi_item_ids:
        rows = db.session.execute(text("""
            SELECT craft_sheet_item_id FROM craft_sheet_item
            WHERE production_instruction_item_id IN :pids
        """).bindparams(bindparam("pids", expanding=True)),
        {"pids": pi_item_ids}).fetchall()
        cs_item_ids.update(r[0] for r in rows)

    cs_fallback_sql = """
        SELECT csi.craft_sheet_item_id
        FROM craft_sheet_item csi
        JOIN craft_sheet cs ON cs.craft_sheet_id = csi.craft_sheet_id
        WHERE cs.order_shoe_id = :osid AND csi.material_id = :mid
    """
    cs_p = {"osid": order_shoe_id, "mid": material_id}
    if scope == "color":
        cs_fallback_sql += " AND csi.order_shoe_type_id = :ostid"
        cs_p["ostid"] = order_shoe_type_id
    for r in db.session.execute(text(cs_fallback_sql), cs_p).fetchall():
        cs_item_ids.add(r[0])

    # 3) BOM：链路 + 兜底
    bom_item_ids = set()
    if pi_item_ids:
        rows = db.session.execute(text("""
            SELECT bom_item_id FROM bom_item
            WHERE production_instruction_item_id IN :pids
        """).bindparams(bindparam("pids", expanding=True)),
        {"pids": pi_item_ids}).fetchall()
        bom_item_ids.update(r[0] for r in rows)

    bom_fallback_sql = """
        SELECT bi.bom_item_id
        FROM bom_item bi
        JOIN bom b ON b.bom_id = bi.bom_id
        JOIN total_bom tb ON tb.total_bom_id = b.total_bom_id
        WHERE tb.order_shoe_id = :osid AND bi.material_id = :mid
    """
    bom_p = {"osid": order_shoe_id, "mid": material_id}
    if scope == "color":
        bom_fallback_sql += " AND b.order_shoe_type_id = :ostid"
        bom_p["ostid"] = order_shoe_type_id
    for r in db.session.execute(text(bom_fallback_sql), bom_p).fetchall():
        bom_item_ids.add(r[0])

    # 4) PO：链路 (via bom_item) + 兜底（同 order_shoe 内 material_id 匹配）
    po_item_ids = set()
    if bom_item_ids:
        rows = db.session.execute(text("""
            SELECT purchase_order_item_id FROM purchase_order_item
            WHERE bom_item_id IN :bids
        """).bindparams(bindparam("bids", expanding=True)),
        {"bids": list(bom_item_ids)}).fetchall()
        po_item_ids.update(r[0] for r in rows)

    # PO 兜底匹配：通过 purchase_order.order_shoe_id 限定，再用 material_id 匹配；
    # scope=color 时通过 bom_item -> bom.order_shoe_type_id 关联限定（若 bom_item_id 缺失则放过）
    po_fallback_sql = """
        SELECT poi.purchase_order_item_id
        FROM purchase_order_item poi
        JOIN purchase_divide_order pdo ON pdo.purchase_divide_order_id = poi.purchase_divide_order_id
        JOIN purchase_order po ON po.purchase_order_id = pdo.purchase_order_id
        LEFT JOIN bom_item bi ON bi.bom_item_id = poi.bom_item_id
        LEFT JOIN bom b ON b.bom_id = bi.bom_id
        WHERE po.order_shoe_id = :osid AND poi.material_id = :mid
    """
    po_p = {"osid": order_shoe_id, "mid": material_id}
    if scope == "color":
        # 仅当 bom 关联且配色一致；或 bom 关联缺失（无法判定配色，宽松通过）
        po_fallback_sql += " AND (b.order_shoe_type_id = :ostid OR poi.bom_item_id IS NULL)"
        po_p["ostid"] = order_shoe_type_id
    for r in db.session.execute(text(po_fallback_sql), po_p).fetchall():
        po_item_ids.add(r[0])

    return {
        "pi_item_ids": pi_item_ids,
        "cs_item_ids": sorted(cs_item_ids),
        "bom_item_ids": sorted(bom_item_ids),
        "po_item_ids": sorted(po_item_ids),
        "scope_ostids": scope_ostids,
    }


def _get_supplier_id_of_material(material_id):
    if not material_id:
        return None
    row = db.session.execute(
        text("SELECT material_supplier FROM material WHERE material_id = :mid"),
        {"mid": material_id},
    ).first()
    return row[0] if row else None


def _validate_payload(data):
    order_shoe_id = data.get("orderShoeId")
    material_id = data.get("materialId")
    scope = data.get("scope") or "color"
    order_shoe_type_id = data.get("orderShoeTypeId") or 0

    if not order_shoe_id or not material_id:
        return None, ("缺少 orderShoeId 或 materialId", 400)
    if scope not in ("color", "shoe"):
        return None, ("scope 必须为 'color' 或 'shoe'", 400)
    if scope == "color" and not order_shoe_type_id:
        return None, ("配色范围需要提供 orderShoeTypeId", 400)

    new_material_id = data.get("newMaterialId") or None
    new_model = data.get("newModel")
    new_spec = data.get("newSpecification")
    new_color = data.get("newColor")

    if not new_material_id and new_model is None and new_spec is None and new_color is None:
        return None, ("没有要修改的字段（请填写新材料 / 型号 / 规格 / 颜色 中的至少一项）", 400)

    if new_material_id:
        new_mat = Material.query.get(new_material_id)
        if not new_mat:
            return None, (f"新材料 ID {new_material_id} 不存在", 404)

    return {
        "order_shoe_id": int(order_shoe_id),
        "material_id": int(material_id),
        "scope": scope,
        "order_shoe_type_id": int(order_shoe_type_id) if order_shoe_type_id else 0,
        "new_material_id": int(new_material_id) if new_material_id else None,
        "new_model": new_model,
        "new_spec": new_spec,
        "new_color": new_color,
    }, None


@material_batch_edit_bp.route("/material/batch-edit-materials/preview", methods=["POST"])
def preview_batch_edit():
    """
    预览同步修改影响范围（不写库）。
    返回各表受影响行数 + 供应商变化告警 + PO 拆分预测。
    """
    args, err = _validate_payload(request.get_json() or {})
    if err:
        return jsonify({"error": err[0]}), err[1]

    t = _resolve_targets(
        args["order_shoe_id"], args["scope"],
        args["order_shoe_type_id"], args["material_id"],
    )

    # 供应商变化检测
    old_supplier_id = _get_supplier_id_of_material(args["material_id"])
    new_supplier_id = (
        _get_supplier_id_of_material(args["new_material_id"])
        if args["new_material_id"] else old_supplier_id
    )
    supplier_changed = bool(args["new_material_id"]) and (old_supplier_id != new_supplier_id)

    # PO 拆分预测：当前受影响的 po_items 中，已在新供应商的 pdo 之外的需要被搬走
    po_split_count = 0
    pdo_supplier_breakdown = []
    if t["po_item_ids"]:
        rows = db.session.execute(text("""
            SELECT pdo.purchase_divide_order_id, pdo.purchase_divide_order_rid,
                   po.purchase_order_rid, COUNT(poi.purchase_order_item_id) AS cnt
            FROM purchase_order_item poi
            JOIN purchase_divide_order pdo
              ON pdo.purchase_divide_order_id = poi.purchase_divide_order_id
            JOIN purchase_order po ON po.purchase_order_id = pdo.purchase_order_id
            WHERE poi.purchase_order_item_id IN :pids
            GROUP BY pdo.purchase_divide_order_id, pdo.purchase_divide_order_rid,
                     po.purchase_order_rid
        """).bindparams(bindparam("pids", expanding=True)),
        {"pids": t["po_item_ids"]}).fetchall()
        for r in rows:
            pdo_supplier_breakdown.append({
                "purchaseDivideOrderId": r[0],
                "purchaseDivideOrderRid": r[1],
                "purchaseOrderRid": r[2],
                "itemCount": int(r[3]),
            })
        if supplier_changed:
            po_split_count = len(t["po_item_ids"])

    # 新/旧材料展示信息
    def _mat_info(mid):
        if not mid:
            return None
        row = db.session.execute(text("""
            SELECT m.material_id, m.material_name, s.supplier_name, s.supplier_id
            FROM material m
            LEFT JOIN supplier s ON s.supplier_id = m.material_supplier
            WHERE m.material_id = :mid
        """), {"mid": mid}).first()
        if not row:
            return None
        return {"materialId": row[0], "materialName": row[1] or "",
                "supplierName": row[2] or "", "supplierId": row[3]}

    return jsonify({
        "scopeOstids": t["scope_ostids"],
        "counts": {
            "production_instruction_item": len(t["pi_item_ids"]),
            "craft_sheet_item": len(t["cs_item_ids"]),
            "bom_item": len(t["bom_item_ids"]),
            "purchase_order_item": len(t["po_item_ids"]),
        },
        "supplierChanged": supplier_changed,
        "oldMaterial": _mat_info(args["material_id"]),
        "newMaterial": _mat_info(args["new_material_id"]) if args["new_material_id"] else None,
        "poSplitCount": po_split_count,
        "pdoBreakdown": pdo_supplier_breakdown,
    })


@material_batch_edit_bp.route("/material/batch-edit-materials", methods=["POST"])
def batch_edit_materials():
    """
    执行同步修改：始终全量联动 PI + 工艺单 + BOM + 采购订单。
    若新材料供应商变化 → 自动将受影响 PO 项搬移到新供应商对应的 purchase_divide_order。
    """
    args, err = _validate_payload(request.get_json() or {})
    if err:
        return jsonify({"error": err[0]}), err[1]

    t = _resolve_targets(
        args["order_shoe_id"], args["scope"],
        args["order_shoe_type_id"], args["material_id"],
    )

    new_material_id = args["new_material_id"]
    new_model = args["new_model"]
    new_spec = args["new_spec"]
    new_color = args["new_color"]

    old_supplier_id = _get_supplier_id_of_material(args["material_id"])
    new_supplier_id = (
        _get_supplier_id_of_material(new_material_id) if new_material_id else old_supplier_id
    )
    supplier_changed = bool(new_material_id) and (old_supplier_id != new_supplier_id)

    counts = {"production_instruction_item": 0, "craft_sheet_item": 0,
              "bom_item": 0, "purchase_order_item": 0}
    split_log = []

    try:
        # -------- PI --------
        if t["pi_item_ids"]:
            vals = {}
            if new_material_id: vals[ProductionInstructionItem.material_id] = new_material_id
            if new_model is not None: vals[ProductionInstructionItem.material_model] = new_model
            if new_spec is not None: vals[ProductionInstructionItem.material_specification] = new_spec
            if new_color is not None: vals[ProductionInstructionItem.color] = new_color
            if vals:
                counts["production_instruction_item"] = (
                    ProductionInstructionItem.query
                    .filter(ProductionInstructionItem.production_instruction_item_id.in_(t["pi_item_ids"]))
                    .update(vals, synchronize_session=False)
                )

        # -------- CraftSheet --------
        if t["cs_item_ids"]:
            vals = {}
            if new_material_id: vals[CraftSheetItem.material_id] = new_material_id
            if new_model is not None: vals[CraftSheetItem.material_model] = new_model
            if new_spec is not None: vals[CraftSheetItem.material_specification] = new_spec
            if new_color is not None: vals[CraftSheetItem.color] = new_color
            if vals:
                counts["craft_sheet_item"] = (
                    CraftSheetItem.query
                    .filter(CraftSheetItem.craft_sheet_item_id.in_(t["cs_item_ids"]))
                    .update(vals, synchronize_session=False)
                )

        # -------- BOM --------
        if t["bom_item_ids"]:
            vals = {}
            if new_material_id: vals[BomItem.material_id] = new_material_id
            if new_model is not None: vals[BomItem.material_model] = new_model
            if new_spec is not None: vals[BomItem.material_specification] = new_spec
            if new_color is not None: vals[BomItem.bom_item_color] = new_color
            if vals:
                counts["bom_item"] = (
                    BomItem.query
                    .filter(BomItem.bom_item_id.in_(t["bom_item_ids"]))
                    .update(vals, synchronize_session=False)
                )

        # -------- PurchaseOrderItem (含供应商拆分) --------
        if t["po_item_ids"]:
            vals = {}
            if new_material_id: vals[PurchaseOrderItem.material_id] = new_material_id
            if new_model is not None: vals[PurchaseOrderItem.material_model] = new_model
            if new_spec is not None: vals[PurchaseOrderItem.material_specification] = new_spec
            if new_color is not None: vals[PurchaseOrderItem.color] = new_color
            if vals:
                counts["purchase_order_item"] = (
                    PurchaseOrderItem.query
                    .filter(PurchaseOrderItem.purchase_order_item_id.in_(t["po_item_ids"]))
                    .update(vals, synchronize_session=False)
                )

            # 供应商变化 → 把受影响 PO 项搬到新供应商对应的 pdo
            if supplier_changed and new_supplier_id:
                split_log = _resplit_po_items_by_supplier(
                    t["po_item_ids"], new_supplier_id
                )

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"批量修改失败: {str(e)}"}), 500

    total = sum(counts.values())
    return jsonify({
        "message": f"同步修改完成，共更新 {total} 条记录",
        "totalUpdated": total,
        "counts": counts,
        "supplierChanged": supplier_changed,
        "splitLog": split_log,
    })


def _resplit_po_items_by_supplier(po_item_ids, new_supplier_id):
    """
    对受影响的 purchase_order_item 按其当前所在的 purchase_order 进行分组，
    把每条 item 从原 pdo 搬到同一 purchase_order 下、对应 new_supplier_id 的 pdo
    （rid 约定: purchase_order_rid + supplier_id.zfill(4)；若不存在则按既有约定新建）。

    Returns: list of moves: [{ poItemId, fromPdoRid, toPdoRid, purchaseOrderRid }]
    """
    moves = []
    if not po_item_ids or not new_supplier_id:
        return moves

    rows = db.session.execute(text("""
        SELECT poi.purchase_order_item_id,
               pdo.purchase_divide_order_id,
               pdo.purchase_divide_order_rid,
               pdo.purchase_divide_order_type,
               pdo.shipment_address,
               pdo.shipment_deadline,
               po.purchase_order_id,
               po.purchase_order_rid
        FROM purchase_order_item poi
        JOIN purchase_divide_order pdo
          ON pdo.purchase_divide_order_id = poi.purchase_divide_order_id
        JOIN purchase_order po
          ON po.purchase_order_id = pdo.purchase_order_id
        WHERE poi.purchase_order_item_id IN :pids
    """).bindparams(bindparam("pids", expanding=True)),
    {"pids": list(po_item_ids)}).fetchall()

    supplier_suffix = str(new_supplier_id).zfill(4)
    pdo_cache = {}  # (purchase_order_id, supplier_suffix) -> target pdo_id

    for r in rows:
        (po_item_id, src_pdo_id, src_pdo_rid, pdo_type,
         ship_addr, ship_deadline, purchase_order_id, po_rid) = r

        if src_pdo_rid and src_pdo_rid.endswith(supplier_suffix):
            # 已在目标 pdo 中，无需搬移
            continue

        # 计算目标 rid：优先用 purchase_order_rid + supplier 后缀
        base_rid = po_rid or (src_pdo_rid[:-4] if src_pdo_rid and len(src_pdo_rid) > 4 else "")
        target_rid = base_rid + supplier_suffix

        cache_key = (purchase_order_id, supplier_suffix)
        if cache_key in pdo_cache:
            target_pdo_id = pdo_cache[cache_key]
        else:
            # 查找同 purchase_order 下、目标 rid 是否已存在
            existing = db.session.execute(text("""
                SELECT purchase_divide_order_id FROM purchase_divide_order
                WHERE purchase_order_id = :poid
                  AND purchase_divide_order_rid = :rid
            """), {"poid": purchase_order_id, "rid": target_rid}).first()

            if existing:
                target_pdo_id = existing[0]
            else:
                # 新建目标 pdo
                new_pdo = PurchaseDivideOrder(
                    purchase_order_id=purchase_order_id,
                    purchase_divide_order_rid=target_rid,
                    purchase_divide_order_type=pdo_type or "N",
                    shipment_address=ship_addr,
                    shipment_deadline=ship_deadline,
                )
                db.session.add(new_pdo)
                db.session.flush()
                target_pdo_id = new_pdo.purchase_divide_order_id
            pdo_cache[cache_key] = target_pdo_id

        # 搬移 PO 项到目标 pdo
        db.session.execute(text("""
            UPDATE purchase_order_item
               SET purchase_divide_order_id = :tpdo
             WHERE purchase_order_item_id = :pid
        """), {"tpdo": target_pdo_id, "pid": po_item_id})

        moves.append({
            "poItemId": po_item_id,
            "fromPdoId": src_pdo_id,
            "fromPdoRid": src_pdo_rid,
            "toPdoId": target_pdo_id,
            "toPdoRid": target_rid,
            "purchaseOrderRid": po_rid,
        })

    return moves
