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
               pii.remark, pii.department_id, pii.order_shoe_type_id, pii.zipper_pair_id,
               m.material_category
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
            "zipperPairId": r[12],
            "materialCategory": r[13],
        })

    # 2) 工艺单
    cs_sql = """
        SELECT csi.craft_sheet_item_id, csi.material_id, m.material_name,
               s.supplier_name, csi.material_model, csi.material_specification,
               csi.color, csi.material_type, csi.material_second_type,
               csi.craft_name, csi.department_id, csi.production_instruction_item_id,
               csi.order_shoe_type_id, csi.unit_usage, csi.total_usage, csi.zipper_pair_id
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
            "unitUsage": float(r[13]) if r[13] is not None else None,
            "totalUsage": float(r[14]) if r[14] is not None else None,
            "linkRootId": r[11],
            "zipperPairId": r[15],
        })

    # 3) BOM
    bom_sql = """
        SELECT bi.bom_item_id, bi.material_id, m.material_name,
               s.supplier_name, bi.material_model, bi.material_specification,
               bi.bom_item_color, bi.department_id, bi.material_second_type,
               bi.craft_name, bi.production_instruction_item_id,
               b.bom_type, b.order_shoe_type_id, bi.total_usage, bi.zipper_pair_id
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
            "totalUsage": float(r[13]) if r[13] is not None else None,
            "linkRootId": r[10],
            "zipperPairId": r[14],
        })

    # 建立 PI 的 (material_id, model, spec, color) → order_shoe_type_id 查找表
    # 用于给采购单条目补充 order_shoe_type_id
    pi_ost_lookup = {}
    for it in items:
        if it["docType"] != "production_instruction_item":
            continue
        key = (it["materialId"], it["materialModel"], it["materialSpecification"], it["color"])
        if key not in pi_ost_lookup:
            pi_ost_lookup[key] = it["orderShoeTypeId"]

    # 4) 采购订单 — 直接查采购单，用 PI 查找表补 order_shoe_type_id
    po_sql = """
        SELECT poi.purchase_order_item_id, poi.material_id, m.material_name,
               s.supplier_name, poi.material_model, poi.material_specification,
               poi.color, poi.craft_name, poi.remark, poi.bom_item_id,
               pdo.purchase_divide_order_id,
               pdo.purchase_divide_order_rid, po.purchase_order_id,
               po.purchase_order_rid
        FROM purchase_order_item poi
        JOIN purchase_divide_order pdo ON pdo.purchase_divide_order_id = poi.purchase_divide_order_id
        JOIN purchase_order po ON po.purchase_order_id = pdo.purchase_order_id
        JOIN material m ON m.material_id = poi.material_id
        LEFT JOIN supplier s ON s.supplier_id = m.material_supplier
        WHERE po.order_shoe_id = :osid
    """
    po_params = {"osid": order_shoe_id}
    for r in db.session.execute(text(po_sql), po_params).fetchall():
        mat_key = (r[1], r[4] or "", r[5] or "", r[6] or "")
        ost_id = pi_ost_lookup.get(mat_key)
        if order_shoe_type_id and ost_id != order_shoe_type_id:
            continue
        items.append({
            "docType": "purchase_order_item", "docLabel": "采购订单",
            "itemId": r[0], "materialId": r[1], "materialName": r[2] or "",
            "supplierName": r[3] or "", "materialModel": r[4] or "",
            "materialSpecification": r[5] or "", "color": r[6] or "",
            "craftName": r[7] or "", "remark": r[8] or "",
            "bomItemId": r[9], "orderShoeTypeId": ost_id,
            "purchaseDivideOrderId": r[10], "purchaseDivideOrderRid": r[11] or "",
            "purchaseOrderId": r[12], "purchaseOrderRid": r[13] or "",
            "linkRootId": r[9],
        })

    # 按 material_id 聚合
    grouped = {}
    for it in items:
        mid = it["materialId"]
        model = it.get("materialModel") or ""
        spec = it.get("materialSpecification") or ""
        gkey = (mid, model, spec)
        if gkey not in grouped:
            grouped[gkey] = {
                "materialId": mid,
                "materialName": it["materialName"],
                "supplierName": it["supplierName"],
                "materialSecondType": it.get("materialSecondType", ""),
                "materialCategory": it.get("materialCategory", 0),
                "groupModel": model,
                "groupSpec": spec,
                "items": [],
                "colorPresence": set(),
            }
        if it.get("orderShoeTypeId"):
            grouped[gkey]["colorPresence"].add(it["orderShoeTypeId"])
        grouped[gkey]["items"].append(it)

    result = []
    for g in grouped.values():
        g["colorPresence"] = sorted(g["colorPresence"])
        result.append(g)

    result.sort(key=lambda x: (x["materialName"], x["groupModel"], x["groupSpec"]))
    return jsonify({"result": result})


# ===========================================================================
# 3. 预览 & 执行：同步修改
# ===========================================================================

def _resolve_targets(order_shoe_id, scope, order_shoe_type_id, material_id,
                     group_model=None, group_spec=None):
    """
    根据范围确定本次操作要更新的目标集合（以 PI item 为根）。
    group_model / group_spec: 若指定，则兜底匹配时额外限定 material_model / material_specification，
    使操作仅影响同名材料下特定型号/规格的记录。

    Returns: dict {
        "pi_item_ids":   [int],   # PI 项 id（链路根）
        "cs_item_ids":   [int],   # 由 PI 项链路找到 + 兜底匹配 的工艺单项
        "bom_item_ids":  [int],   # 由 PI 项链路找到 + 兜底匹配 的 BOM 项
        "po_item_ids":   [int],   # 由 BOM 项链路找到 + 兜底匹配 的采购单项
        "scope_ostids":  [int],   # 本次操作覆盖的配色集合（用于兜底匹配）
    }
    """
    def _model_clause(alias="pii"):
        """生成 model/spec 过滤子句及参数（仅在 group_model/spec 不为 None 时添加）。"""
        clause, extra = "", {}
        if group_model is not None:
            clause += f" AND ({alias}.material_model = :gmodel OR ({alias}.material_model IS NULL AND :gmodel = ''))"
            extra["gmodel"] = group_model
        if group_spec is not None:
            clause += f" AND ({alias}.material_specification = :gspec OR ({alias}.material_specification IS NULL AND :gspec = ''))"
            extra["gspec"] = group_spec
        return clause, extra

    # 1) PI item 候选：order_shoe_id × material_id × scope × [model/spec]
    mc, mp = _model_clause("pii")
    pi_sql = f"""
        SELECT pii.production_instruction_item_id, pii.order_shoe_type_id
        FROM production_instruction_item pii
        JOIN production_instruction pi ON pi.production_instruction_id = pii.production_instruction_id
        WHERE pi.order_shoe_id = :osid AND pii.material_id = :mid{mc}
    """
    p = {"osid": order_shoe_id, "mid": material_id, **mp}
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

    cmc, cmp = _model_clause("csi")
    cs_fallback_sql = f"""
        SELECT csi.craft_sheet_item_id
        FROM craft_sheet_item csi
        JOIN craft_sheet cs ON cs.craft_sheet_id = csi.craft_sheet_id
        WHERE cs.order_shoe_id = :osid AND csi.material_id = :mid{cmc}
    """
    cs_p = {"osid": order_shoe_id, "mid": material_id, **cmp}
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

    bmc, bmp = _model_clause("bi")
    # BOM 用 bom_item_color 作为颜色列，model/spec 列名相同
    bom_fallback_sql = f"""
        SELECT bi.bom_item_id
        FROM bom_item bi
        JOIN bom b ON b.bom_id = bi.bom_id
        JOIN total_bom tb ON tb.total_bom_id = b.total_bom_id
        WHERE tb.order_shoe_id = :osid AND bi.material_id = :mid{bmc}
    """
    bom_p = {"osid": order_shoe_id, "mid": material_id, **bmp}
    if scope == "color":
        bom_fallback_sql += " AND b.order_shoe_type_id = :ostid"
        bom_p["ostid"] = order_shoe_type_id
    for r in db.session.execute(text(bom_fallback_sql), bom_p).fetchall():
        bom_item_ids.add(r[0])

    # 4) PO：链路 (via bom_item) + 兜底（同 order_shoe 内 material_id 匹配）
    po_item_ids = set()
    if bom_item_ids:
        # 链路查找时同样限定 material_id + model/spec，防止数据不一致时跨组误删
        lmc, lmp = _model_clause("poi")
        rows = db.session.execute(
            text(f"""
                SELECT poi.purchase_order_item_id FROM purchase_order_item poi
                WHERE poi.bom_item_id IN :bids
                  AND poi.material_id = :mid{lmc}
            """).bindparams(bindparam("bids", expanding=True)),
            {"bids": list(bom_item_ids), "mid": material_id, **lmp}
        ).fetchall()
        po_item_ids.update(r[0] for r in rows)

    # PO 兜底匹配：通过 purchase_order.order_shoe_id 限定，再用 material_id 匹配；
    # scope=color 时通过 bom_item -> bom.order_shoe_type_id 关联限定（若 bom_item_id 缺失则放过）
    pmc, pmp = _model_clause("poi")
    po_fallback_sql = f"""
        SELECT poi.purchase_order_item_id
        FROM purchase_order_item poi
        JOIN purchase_divide_order pdo ON pdo.purchase_divide_order_id = poi.purchase_divide_order_id
        JOIN purchase_order po ON po.purchase_order_id = pdo.purchase_order_id
        LEFT JOIN bom_item bi ON bi.bom_item_id = poi.bom_item_id
        LEFT JOIN bom b ON b.bom_id = bi.bom_id
        WHERE po.order_shoe_id = :osid AND poi.material_id = :mid{pmc}
    """
    po_p = {"osid": order_shoe_id, "mid": material_id, **pmp}
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
        "group_model": data.get("groupModel"),   # None = no filter; "" = explicit empty
        "group_spec": data.get("groupSpec"),
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
        group_model=args.get("group_model"),
        group_spec=args.get("group_spec"),
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
        group_model=args.get("group_model"),
        group_spec=args.get("group_spec"),
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


# ===========================================================================
# 6. 查询配色尺码数量（用于添加材料时展示）
# ===========================================================================

@material_batch_edit_bp.route("/material/ordershoetype-batch-info", methods=["GET"])
def get_ordershoetype_batch_info():
    """
    返回某 order_shoe_type_id 下所有批次的尺码数量，以及汇总合计。
    用于添加材料时展示当前配色的尺码表。
    """
    from models import OrderShoeBatchInfo
    order_shoe_type_id = request.args.get("orderShoeTypeId", 0, type=int)
    if not order_shoe_type_id:
        return jsonify({"error": "缺少 orderShoeTypeId"}), 400

    rows = (
        OrderShoeBatchInfo.query
        .filter_by(order_shoe_type_id=order_shoe_type_id)
        .all()
    )

    SIZES = list(range(34, 47))
    batches = []
    totals = {s: 0 for s in SIZES}
    grand_total = 0
    for r in rows:
        batch = {"name": r.name, "total": r.total_amount or 0}
        for s in SIZES:
            v = getattr(r, f"size_{s}_amount") or 0
            batch[str(s)] = v
            totals[s] += v
        grand_total += batch["total"]
        batches.append(batch)

    return jsonify({
        "batches": batches,
        "totals": {str(s): totals[s] for s in SIZES},
        "grandTotal": grand_total,
    })


# ===========================================================================
# 7. 删除材料（从指定鞋款的所有文档中移除该材料的所有记录）
# ===========================================================================

@material_batch_edit_bp.route("/material/batch-delete-material", methods=["POST"])
def batch_delete_material():
    """
    从某订单鞋款下的所有文档（PI / CraftSheet / BOM / PurchaseOrderItem）
    中删除指定 material_id 的记录。

    Body: { orderShoeId, materialId, scope, orderShoeTypeId(可选) }
    """
    data = request.get_json() or {}
    order_shoe_id = data.get("orderShoeId")
    material_id = data.get("materialId")
    scope = data.get("scope", "shoe")  # "shoe" | "color"
    order_shoe_type_id = data.get("orderShoeTypeId")

    if not order_shoe_id or not material_id:
        return jsonify({"error": "缺少必填参数 orderShoeId / materialId"}), 400
    if scope == "color" and not order_shoe_type_id:
        return jsonify({"error": "scope=color 时必须提供 orderShoeTypeId"}), 400

    t = _resolve_targets(order_shoe_id, scope, order_shoe_type_id, material_id,
                         group_model=data.get("groupModel"),
                         group_spec=data.get("groupSpec"))

    # 对于删除操作，采购订单项单独解析，不使用 _resolve_targets 的兜底匹配，
    # 只删除严格通过 BOM 链路找到且与本组材料信息完全匹配的采购订单项。
    # 这防止数据不一致时（如 POI.bom_item_id 指向错误组的 BOM 项）误删其他组的采购订单项。
    group_model = data.get("groupModel")
    group_spec = data.get("groupSpec")

    safe_po_ids = set()
    if t["bom_item_ids"]:
        # 严格 INNER JOIN：POI 必须指向目标 BOM 项，且 POI 自身的 material_id/model/spec
        # 以及 BOM 项的 material_id/model/spec 均须与本组一致，双重验证。
        poi_clause, poi_p = "", {}
        bi_clause, bi_p = "", {}
        if group_model is not None:
            poi_clause += " AND (poi.material_model = :poi_gm OR (poi.material_model IS NULL AND :poi_gm = ''))"
            bi_clause  += " AND (bi.material_model  = :bi_gm  OR (bi.material_model  IS NULL AND :bi_gm  = ''))"
            poi_p["poi_gm"] = group_model
            bi_p["bi_gm"]   = group_model
        if group_spec is not None:
            poi_clause += " AND (poi.material_specification = :poi_gs OR (poi.material_specification IS NULL AND :poi_gs = ''))"
            bi_clause  += " AND (bi.material_specification  = :bi_gs  OR (bi.material_specification  IS NULL AND :bi_gs  = ''))"
            poi_p["poi_gs"] = group_spec
            bi_p["bi_gs"]   = group_spec

        rows = db.session.execute(
            text(f"""
                SELECT poi.purchase_order_item_id
                FROM purchase_order_item poi
                JOIN bom_item bi ON bi.bom_item_id = poi.bom_item_id
                WHERE poi.bom_item_id IN :del_bids
                  AND poi.material_id = :del_mid{poi_clause}
                  AND bi.material_id  = :del_mid{bi_clause}
            """).bindparams(bindparam("del_bids", expanding=True)),
            {"del_bids": t["bom_item_ids"], "del_mid": int(material_id), **poi_p, **bi_p}
        ).fetchall()
        safe_po_ids.update(r[0] for r in rows)

    # 用严格解析结果覆盖 _resolve_targets 给出的宽松集合
    t["po_item_ids"] = sorted(safe_po_ids)
    counts = {}
    try:
        if t["po_item_ids"]:
            counts["purchase_order_item"] = (
                PurchaseOrderItem.query
                .filter(PurchaseOrderItem.purchase_order_item_id.in_(t["po_item_ids"]))
                .delete(synchronize_session=False)
            )
        if t["bom_item_ids"]:
            counts["bom_item"] = (
                BomItem.query
                .filter(BomItem.bom_item_id.in_(t["bom_item_ids"]))
                .delete(synchronize_session=False)
            )
        if t["cs_item_ids"]:
            counts["craft_sheet_item"] = (
                CraftSheetItem.query
                .filter(CraftSheetItem.craft_sheet_item_id.in_(t["cs_item_ids"]))
                .delete(synchronize_session=False)
            )
        if t["pi_item_ids"]:
            counts["production_instruction_item"] = (
                ProductionInstructionItem.query
                .filter(ProductionInstructionItem.production_instruction_item_id.in_(t["pi_item_ids"]))
                .delete(synchronize_session=False)
            )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"删除失败: {str(e)}"}), 500

    total = sum(counts.values())
    return jsonify({"message": f"已删除 {total} 条记录", "counts": counts})


# ===========================================================================
# 7. 新增材料（PI + BOM + 采购订单项）
# ===========================================================================

@material_batch_edit_bp.route("/material/batch-add-material", methods=["POST"])
def batch_add_material():
    """
    向指定鞋款新增一条材料，联动写入：
      1. production_instruction_item
      2. bom_item（关联到 bom_type=0 的一次 BOM）
      3. purchase_order_item（关联到该鞋款对应供应商的 purchase_divide_order）

    Body: {
        orderShoeId,
        orderShoeTypeId,          # 必填
        materialId,               # 必填
        materialModel, materialSpecification, color,
        unitUsage,                # 单位用量（写入 bom_item.unit_usage）
        approvalAmount,           # 核定用量（写入 purchase_order_item.approval_amount & bom_item.total_usage）
        remark
    }
    """
    from models import OrderShoeType, Material
    data = request.get_json() or {}
    order_shoe_id = data.get("orderShoeId")
    material_id = data.get("materialId")
    order_shoe_type_id = data.get("orderShoeTypeId")
    if not order_shoe_id or not material_id or not order_shoe_type_id:
        return jsonify({"error": "缺少必填参数 orderShoeId / materialId / orderShoeTypeId"}), 400

    unit_usage = float(data.get("unitUsage") or 0)
    approval_amount = float(data.get("approvalAmount") or 0)
    mat_model = data.get("materialModel") or ""
    mat_spec = data.get("materialSpecification") or ""
    color = data.get("color") or ""
    remark = data.get("remark") or ""

    # 取材料信息（供应商）
    material = Material.query.filter_by(material_id=material_id).first()
    if not material:
        return jsonify({"error": "未找到材料"}), 404

    # 1. 找投产指令单
    pi = ProductionInstruction.query.filter_by(order_shoe_id=order_shoe_id).first()
    if not pi:
        return jsonify({"error": "未找到该鞋款的投产指令单"}), 404

    # 2. 找一次 BOM（bom_type=0, order_shoe_type_id）
    bom = (
        Bom.query
        .filter_by(order_shoe_type_id=order_shoe_type_id, bom_type=0)
        .first()
    )
    if not bom:
        return jsonify({"error": f"未找到 orderShoeTypeId={order_shoe_type_id} 的一次BOM，请先生成BOM"}), 404

    # 3. 找该鞋款的一次采购分单（按材料供应商匹配 rid 后缀）
    supplier_id = material.material_supplier
    supplier_suffix = str(supplier_id).zfill(4)

    pdo_row = db.session.execute(text("""
        SELECT pdo.purchase_divide_order_id, pdo.purchase_divide_order_rid, po.purchase_order_id
        FROM purchase_divide_order pdo
        JOIN purchase_order po ON po.purchase_order_id = pdo.purchase_order_id
        WHERE po.order_shoe_id = :osid
          AND pdo.purchase_divide_order_rid LIKE :suffix
        ORDER BY po.purchase_order_id DESC
        LIMIT 1
    """), {"osid": order_shoe_id, "suffix": f"%{supplier_suffix}"}).first()

    try:
        # --- PI item ---
        pi_item = ProductionInstructionItem(
            production_instruction_id=pi.production_instruction_id,
            material_id=material_id,
            order_shoe_type_id=order_shoe_type_id,
            material_model=mat_model,
            material_specification=mat_spec,
            color=color,
            is_pre_purchase=False,
            material_type="A",
            material_second_type="",
            department_id=1,
            remark=remark,
        )
        db.session.add(pi_item)
        db.session.flush()

        # --- BOM item ---
        bom_item = BomItem(
            bom_id=bom.bom_id,
            material_id=material_id,
            material_model=mat_model,
            material_specification=mat_spec,
            bom_item_color=color,
            unit_usage=unit_usage,
            total_usage=approval_amount,
            department_id=1,
            bom_item_add_type="0",
            material_second_type="",
            production_instruction_item_id=pi_item.production_instruction_item_id,
            remark=remark,
            size_type="E",
        )
        db.session.add(bom_item)
        db.session.flush()

        # --- PurchaseOrderItem（若找到 PDO）---
        po_item_id = None
        if pdo_row:
            po_item = PurchaseOrderItem(
                purchase_divide_order_id=pdo_row[0],
                bom_item_id=bom_item.bom_item_id,
                material_id=material_id,
                material_model=mat_model,
                material_specification=mat_spec,
                color=color,
                purchase_amount=approval_amount,
                approval_amount=approval_amount,
                remark=remark,
            )
            db.session.add(po_item)
            db.session.flush()
            po_item_id = po_item.purchase_order_item_id

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"新增失败: {str(e)}"}), 500

    return jsonify({
        "message": "新增成功" + ("" if pdo_row else "（未找到对应采购分单，仅写入PI和BOM）"),
        "piItemId": pi_item.production_instruction_item_id,
        "bomItemId": bom_item.bom_item_id,
        "poItemId": po_item_id,
    })


# ===========================================================================
# 8-extra. 同步不一致材料（工艺单有但投产指令单缺失的配色 → 创建 PI 项并建立链接）
# ===========================================================================

@material_batch_edit_bp.route("/material/sync-inconsistent-material", methods=["POST"])
def sync_inconsistent_material():
    """
    对不一致材料执行同步：找到工艺单中存在但投产指令单缺失配色的记录，
    为每个缺失配色：
      1. 创建 ProductionInstructionItem
      2. 将该 ost_id 下所有未链接的工艺单项关联到新 PI 项
      3. 若该 ost_id 的一次 BOM 中已有该材料+型号+规格的 BOM 项，更新其 PI 链接；
         若无，则从工艺单项的用量数据创建 BOM 项（unit_usage/total_usage）

    Body: { orderShoeId, materialId, groupModel, groupSpec }
    Returns: { message, created, details: [{ostId, piItemId, bomAction}] }
    """
    data = request.get_json() or {}
    order_shoe_id = data.get("orderShoeId")
    material_id = data.get("materialId")
    group_model = data.get("groupModel")   # None 表示不过滤
    group_spec = data.get("groupSpec")

    if not order_shoe_id or not material_id:
        return jsonify({"error": "缺少 orderShoeId 或 materialId"}), 400

    def _mf(alias):
        """生成 model/spec 过滤子句"""
        clause, extra = "", {}
        if group_model is not None:
            clause += (f" AND ({alias}.material_model = :gmodel"
                       f" OR ({alias}.material_model IS NULL AND :gmodel = ''))")
            extra["gmodel"] = group_model
        if group_spec is not None:
            clause += (f" AND ({alias}.material_specification = :gspec"
                       f" OR ({alias}.material_specification IS NULL AND :gspec = ''))")
            extra["gspec"] = group_spec
        return clause, extra

    # 1) PI 中已有的 ost_ids（取完整字段，后续 PI→CS 创建时需要）
    pi_mc, pi_mp = _mf("pii")
    pi_rows = db.session.execute(text(f"""
        SELECT pii.production_instruction_item_id, pii.order_shoe_type_id,
               pii.material_model, pii.material_specification,
               pii.color, pii.material_type, pii.material_second_type,
               pii.department_id, pii.remark
        FROM production_instruction_item pii
        JOIN production_instruction pi ON pi.production_instruction_id = pii.production_instruction_id
        WHERE pi.order_shoe_id = :osid AND pii.material_id = :mid{pi_mc}
    """), {"osid": order_shoe_id, "mid": material_id, **pi_mp}).fetchall()
    pi_ost_ids = {r[1] for r in pi_rows}
    pi_rows_by_ost = {r[1]: r for r in pi_rows}

    # 2) 工艺单中所有该材料组的项（含用量字段）
    cs_mc, cs_mp = _mf("csi")
    cs_rows = db.session.execute(text(f"""
        SELECT csi.craft_sheet_item_id, csi.order_shoe_type_id,
               csi.material_model, csi.material_specification,
               csi.color, csi.material_type, csi.material_second_type,
               csi.department_id, csi.remark, csi.unit_usage,
               csi.total_usage, csi.craft_name
        FROM craft_sheet_item csi
        JOIN craft_sheet cs ON cs.craft_sheet_id = csi.craft_sheet_id
        WHERE cs.order_shoe_id = :osid AND csi.material_id = :mid{cs_mc}
    """), {"osid": order_shoe_id, "mid": material_id, **cs_mp}).fetchall()

    # 分组：每个缺失 ost_id → 第一条作为模板；收集该 ost_id 的全部 cs_item_ids
    cs_ost_ids = {r[1] for r in cs_rows}   # 工艺单已有的 ost_ids
    template_by_ost = {}   # ost_id -> cs_row (模板，仅 CS 有而 PI 无的)
    cs_ids_by_ost = {}     # ost_id -> [craft_sheet_item_id, ...]
    for r in cs_rows:
        ost_id = r[1]
        if ost_id not in pi_ost_ids:
            if ost_id not in template_by_ost:
                template_by_ost[ost_id] = r
            cs_ids_by_ost.setdefault(ost_id, []).append(r[0])

    # PI 有但工艺单缺失的 ost_ids
    pi_missing_from_cs = {ost_id: row for ost_id, row in pi_rows_by_ost.items()
                          if ost_id not in cs_ost_ids}

    if not template_by_ost and not pi_missing_from_cs:
        return jsonify({
            "message": "无需同步，该材料各配色在投产指令单和工艺单中均已一致",
            "created": 0,
            "details": [],
        })

    # 3) 取投产指令单头
    pi_head = ProductionInstruction.query.filter_by(order_shoe_id=order_shoe_id).first()
    if not pi_head:
        return jsonify({"error": "未找到该鞋款的投产指令单"}), 404

    created = []
    try:
        for ost_id, tmpl in sorted(template_by_ost.items()):
            # --- 3a. 创建 PI 项 ---
            pi_item = ProductionInstructionItem(
                production_instruction_id=pi_head.production_instruction_id,
                material_id=int(material_id),
                order_shoe_type_id=ost_id,
                material_model=tmpl[2] or "",
                material_specification=tmpl[3] or "",
                color=tmpl[4] or "",
                material_type=tmpl[5] or "A",
                material_second_type=tmpl[6] or "",
                department_id=tmpl[7] or 1,
                is_pre_purchase=False,
                remark=tmpl[8] or "",
            )
            db.session.add(pi_item)
            db.session.flush()
            pi_item_id = pi_item.production_instruction_item_id

            # --- 3b. 链接工艺单项 → 新 PI 项 ---
            for cs_id in cs_ids_by_ost.get(ost_id, []):
                db.session.execute(text("""
                    UPDATE craft_sheet_item
                    SET production_instruction_item_id = :pi_id
                    WHERE craft_sheet_item_id = :cs_id
                      AND (production_instruction_item_id IS NULL OR production_instruction_item_id = 0)
                """), {"pi_id": pi_item_id, "cs_id": cs_id})

            # --- 3c. BOM 同步：找一次 BOM (bom_type=0) ---
            bom = Bom.query.filter_by(order_shoe_type_id=ost_id, bom_type=0).first()
            bom_action = "skipped_no_bom"

            if bom:
                # 查该 BOM 中是否已有该材料+型号+规格的条目
                bom_mc, bom_mp = _mf("bi")
                existing_bom_items = db.session.execute(text(f"""
                    SELECT bi.bom_item_id FROM bom_item bi
                    WHERE bi.bom_id = :bid AND bi.material_id = :mid{bom_mc}
                """), {"bid": bom.bom_id, "mid": material_id, **bom_mp}).fetchall()

                if existing_bom_items:
                    # 已有 BOM 项 → 更新 production_instruction_item_id 链接
                    for (bom_item_id,) in existing_bom_items:
                        db.session.execute(text("""
                            UPDATE bom_item
                            SET production_instruction_item_id = :pi_id
                            WHERE bom_item_id = :bid
                              AND (production_instruction_item_id IS NULL OR production_instruction_item_id = 0)
                        """), {"pi_id": pi_item_id, "bid": bom_item_id})
                    bom_action = f"linked_{len(existing_bom_items)}_bom_items"
                else:
                    # 无 BOM 项 → 从工艺单用量创建
                    unit_usage = float(tmpl[9] or 0)
                    total_usage = float(tmpl[10] or 0)
                    craft_name = tmpl[11] or ""
                    new_bom_item = BomItem(
                        bom_id=bom.bom_id,
                        material_id=int(material_id),
                        material_model=tmpl[2] or "",
                        material_specification=tmpl[3] or "",
                        bom_item_color=tmpl[4] or "",
                        unit_usage=unit_usage,
                        total_usage=total_usage,
                        department_id=tmpl[7] or 1,
                        bom_item_add_type="0",
                        material_second_type=tmpl[6] or "",
                        craft_name=craft_name,
                        production_instruction_item_id=pi_item_id,
                        remark=tmpl[8] or "",
                        size_type="E",
                    )
                    db.session.add(new_bom_item)
                    bom_action = "created_bom_item"

            created.append({
                "ostId": ost_id,
                "piItemId": pi_item_id,
                "bomAction": bom_action,
            })

        # ===== 方向二：投产指令单有但工艺单缺失 → 创建工艺单项 =====
        cs_created_count = 0
        if pi_missing_from_cs:
            cs_head = CraftSheet.query.filter_by(order_shoe_id=order_shoe_id).first()
            if cs_head:
                for ost_id, pi_row in sorted(pi_missing_from_cs.items()):
                    cs_item = CraftSheetItem(
                        craft_sheet_id=cs_head.craft_sheet_id,
                        material_id=int(material_id),
                        department_id=pi_row[7] or 1,
                        material_specification=pi_row[3] or "",
                        material_model=pi_row[2] or "",
                        color=pi_row[4] or "",
                        material_type=pi_row[5] or "A",
                        material_second_type=pi_row[6] or "",
                        order_shoe_type_id=ost_id,
                        remark=pi_row[8] or "",
                        production_instruction_item_id=pi_row[0],
                    )
                    db.session.add(cs_item)
                    cs_created_count += 1

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"同步失败: {str(e)}"}), 500

    parts = []
    if created:
        parts.append(f"工艺单→投产指令单：{len(created)} 个配色")
    if cs_created_count:
        parts.append(f"投产指令单→工艺单：{cs_created_count} 个配色")
    return jsonify({
        "message": f"同步成功，{'；'.join(parts)}",
        "created": len(created),
        "csCreated": cs_created_count,
        "details": created,
    })


# ===========================================================================
# 8-extra-2. 补充缺失的一次BOM项（用量由调用方填写）
# ===========================================================================

@material_batch_edit_bp.route("/material/create-missing-bom-items", methods=["POST"])
def create_missing_bom_items():
    """
    为一次BOM中缺失的配色创建 BOM 项，并链接到对应的 PI 项。

    Body: {
        orderShoeId,
        materialId,
        groupModel,   # None = 不过滤
        groupSpec,
        items: [{ ostId, unitUsage, totalUsage }]
    }
    """
    data = request.get_json() or {}
    order_shoe_id = data.get("orderShoeId")
    material_id = data.get("materialId")
    group_model = data.get("groupModel")
    group_spec = data.get("groupSpec")
    items_payload = data.get("items") or []

    if not order_shoe_id or not material_id or not items_payload:
        return jsonify({"error": "缺少必填参数 orderShoeId / materialId / items"}), 400

    def _mf(alias):
        clause, extra = "", {}
        if group_model is not None:
            clause += (f" AND ({alias}.material_model = :gmodel"
                       f" OR ({alias}.material_model IS NULL AND :gmodel = ''))")
            extra["gmodel"] = group_model
        if group_spec is not None:
            clause += (f" AND ({alias}.material_specification = :gspec"
                       f" OR ({alias}.material_specification IS NULL AND :gspec = ''))")
            extra["gspec"] = group_spec
        return clause, extra

    # PI 项：按 ost_id 索引，用于取 material_model/spec/color/dept/second_type
    pi_mc, pi_mp = _mf("pii")
    pi_rows = db.session.execute(text(f"""
        SELECT pii.production_instruction_item_id, pii.order_shoe_type_id,
               pii.material_model, pii.material_specification,
               pii.color, pii.material_second_type, pii.department_id
        FROM production_instruction_item pii
        JOIN production_instruction pi ON pi.production_instruction_id = pii.production_instruction_id
        WHERE pi.order_shoe_id = :osid AND pii.material_id = :mid{pi_mc}
    """), {"osid": order_shoe_id, "mid": material_id, **pi_mp}).fetchall()
    pi_by_ost = {r[1]: r for r in pi_rows}

    created = []
    try:
        for entry in items_payload:
            ost_id = entry.get("ostId")
            unit_usage = float(entry.get("unitUsage") or 0)
            total_usage = float(entry.get("totalUsage") or 0)

            bom = Bom.query.filter_by(order_shoe_type_id=ost_id, bom_type=0).first()
            if not bom:
                continue  # 该配色的 BOM 单据尚未创建，跳过

            pi_row = pi_by_ost.get(ost_id)
            pi_item_id = pi_row[0] if pi_row else None

            new_item = BomItem(
                bom_id=bom.bom_id,
                material_id=int(material_id),
                material_model=group_model if group_model is not None else (pi_row[2] if pi_row else ""),
                material_specification=group_spec if group_spec is not None else (pi_row[3] if pi_row else ""),
                bom_item_color=pi_row[4] if pi_row else "",
                unit_usage=unit_usage,
                total_usage=total_usage,
                department_id=pi_row[6] if pi_row else 1,
                bom_item_add_type="0",
                material_second_type=pi_row[5] if pi_row else "",
                production_instruction_item_id=pi_item_id,
                size_type="E",
            )
            db.session.add(new_item)
            db.session.flush()
            created.append({"ostId": ost_id, "bomItemId": new_item.bom_item_id})

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"创建失败: {str(e)}"}), 500

    if not created:
        return jsonify({"message": "未能创建任何BOM项（可能相关配色的一次BOM单据尚未创建）", "created": 0, "details": []})
    return jsonify({
        "message": f"已为 {len(created)} 个配色创建一次BOM项",
        "created": len(created),
        "details": created,
    })


# ===========================================================================
# 8-extra-3. 补充缺失的采购订单项
# ===========================================================================

@material_batch_edit_bp.route("/material/create-missing-po-items", methods=["POST"])
def create_missing_po_items():
    """
    为采购订单中缺失的配色创建 PurchaseOrderItem，并链接到对应的 BOM 项。

    Body: {
        orderShoeId,
        materialId,
        groupModel,   # None = 不过滤
        groupSpec,
        items: [{ ostId, purchaseAmount }]
    }
    """
    from models import Material
    data = request.get_json() or {}
    order_shoe_id = data.get("orderShoeId")
    material_id = data.get("materialId")
    group_model = data.get("groupModel")
    group_spec = data.get("groupSpec")
    items_payload = data.get("items") or []

    if not order_shoe_id or not material_id or not items_payload:
        return jsonify({"error": "缺少必填参数 orderShoeId / materialId / items"}), 400

    # 取材料供应商（用于匹配采购分单）
    material = Material.query.filter_by(material_id=material_id).first()
    if not material:
        return jsonify({"error": "未找到材料"}), 404
    supplier_id = material.material_supplier
    supplier_suffix = str(supplier_id).zfill(4)

    def _mf(alias):
        clause, extra = "", {}
        if group_model is not None:
            clause += (f" AND ({alias}.material_model = :gmodel"
                       f" OR ({alias}.material_model IS NULL AND :gmodel = ''))")
            extra["gmodel"] = group_model
        if group_spec is not None:
            clause += (f" AND ({alias}.material_specification = :gspec"
                       f" OR ({alias}.material_specification IS NULL AND :gspec = ''))")
            extra["gspec"] = group_spec
        return clause, extra

    # BOM 项：按 ost_id 索引（取 bom_type=0 一次BOM）
    bi_mc, bi_mp = _mf("bi")
    bom_rows = db.session.execute(text(f"""
        SELECT bi.bom_item_id, b.order_shoe_type_id,
               bi.material_model, bi.material_specification, bi.bom_item_color,
               bi.material_second_type, bi.department_id, bi.total_usage
        FROM bom_item bi
        JOIN bom b ON b.bom_id = bi.bom_id
        WHERE b.order_shoe_type_id IN :ost_ids
          AND b.bom_type = 0
          AND bi.material_id = :mid{bi_mc}
    """).bindparams(bindparam("ost_ids", expanding=True)),
    {
        "ost_ids": [e["ostId"] for e in items_payload],
        "mid": material_id,
        **bi_mp,
    }).fetchall()
    bom_by_ost = {r[1]: r for r in bom_rows}

    created = []
    skipped = []
    try:
        for entry in items_payload:
            ost_id = entry.get("ostId")
            purchase_amount = float(entry.get("purchaseAmount") or 0)
            size_amounts = entry.get("sizeAmounts") or {}

            bom_row = bom_by_ost.get(ost_id)
            if not bom_row:
                skipped.append({"ostId": ost_id, "reason": "未找到对应一次BOM项"})
                continue

            # 找该 ost_id 对应的采购分单（按供应商后缀匹配）
            pdo_row = db.session.execute(text("""
                SELECT pdo.purchase_divide_order_id
                FROM purchase_divide_order pdo
                JOIN purchase_order po ON po.purchase_order_id = pdo.purchase_order_id
                WHERE po.order_shoe_id = :osid
                  AND pdo.purchase_divide_order_rid LIKE :suffix
                ORDER BY po.purchase_order_id DESC
                LIMIT 1
            """), {"osid": order_shoe_id, "suffix": f"%{supplier_suffix}"}).first()

            if not pdo_row:
                skipped.append({"ostId": ost_id, "reason": "未找到对应供应商的采购分单"})
                continue

            po_item = PurchaseOrderItem(
                purchase_divide_order_id=pdo_row[0],
                bom_item_id=bom_row[0],
                material_id=int(material_id),
                material_model=bom_row[2] or "",
                material_specification=bom_row[3] or "",
                color=bom_row[4] or "",
                purchase_amount=purchase_amount,
                approval_amount=purchase_amount,
            )
            # 尺码材料：写入各尺码数量
            for s in range(34, 47):
                v = size_amounts.get(str(s))
                if v is not None:
                    setattr(po_item, f"size_{s}_purchase_amount", int(v))
            db.session.add(po_item)
            db.session.flush()
            created.append({"ostId": ost_id, "poItemId": po_item.purchase_order_item_id})

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"创建失败: {str(e)}"}), 500

    msg = f"已为 {len(created)} 个配色创建采购订单项"
    if skipped:
        msg += f"，{len(skipped)} 个配色跳过（{skipped[0]['reason']}）"
    return jsonify({"message": msg, "created": len(created), "details": created, "skipped": skipped})


# ===========================================================================
# 8-extra-3. 批量设置拉链/拉头配对组编号
# ===========================================================================

@material_batch_edit_bp.route("/material/set-zipper-pair-ids", methods=["POST"])
def set_zipper_pair_ids():
    """
    批量更新 production_instruction_item / craft_sheet_item / bom_item 的 zipper_pair_id。

    Body: {
        items: [
            { docType: "production_instruction_item"|"craft_sheet_item"|"bom_item",
              itemId: int,
              zipperPairId: int|null }
        ]
    }
    """
    data = request.get_json() or {}
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "items 不能为空"}), 400

    updated = 0
    try:
        for entry in items:
            doc_type = entry.get("docType")
            item_id = entry.get("itemId")
            pair_id = entry.get("zipperPairId")   # None = 清除

            if not item_id:
                continue

            if doc_type == "production_instruction_item":
                db.session.execute(text("""
                    UPDATE production_instruction_item
                    SET zipper_pair_id = :pid
                    WHERE production_instruction_item_id = :iid
                """), {"pid": pair_id, "iid": item_id})
                updated += 1
            elif doc_type == "craft_sheet_item":
                db.session.execute(text("""
                    UPDATE craft_sheet_item
                    SET zipper_pair_id = :pid
                    WHERE craft_sheet_item_id = :iid
                """), {"pid": pair_id, "iid": item_id})
                updated += 1
            elif doc_type == "bom_item":
                db.session.execute(text("""
                    UPDATE bom_item
                    SET zipper_pair_id = :pid
                    WHERE bom_item_id = :iid
                """), {"pid": pair_id, "iid": item_id})
                updated += 1

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"更新失败: {str(e)}"}), 500

    return jsonify({"message": f"已更新 {updated} 条记录的配对组编号", "updated": updated})


# ===========================================================================
# 8. 检查材料链路对齐
# ===========================================================================

@material_batch_edit_bp.route("/material/check-material-links", methods=["GET"])
def check_material_links():
    """
    检查某订单鞋款下材料文档的FK链路是否对齐（不检查工艺单）：
    - BomItem(type=0, add='0').production_instruction_item_id → PI item 的 material_id 一致
      （仅检查已有对应采购订单项的BOM项；尚未下采购订单的材料自动忽略）
    - PurchaseOrderItem.bom_item_id → BomItem 的 material_id 一致
      （bom_item_id 为空视为采购订单未填写，忽略）

    对不对齐的条目，若存在唯一候选则标记 canAutoFix=True 及 suggestedLinkId。
    """
    order_shoe_id = request.args.get("orderShoeId", 0, type=int)
    if not order_shoe_id:
        return jsonify({"error": "缺少 orderShoeId"}), 400

    # ── PI items ─────────────────────────────────────────────────────────────
    pi_rows = db.session.execute(text("""
        SELECT pii.production_instruction_item_id, pii.material_id,
               pii.order_shoe_type_id, m.material_name
        FROM production_instruction_item pii
        JOIN production_instruction pi
          ON pi.production_instruction_id = pii.production_instruction_id
        JOIN material m ON m.material_id = pii.material_id
        WHERE pi.order_shoe_id = :osid
    """), {"osid": order_shoe_id}).fetchall()

    pi_id_to_info = {}   # pi_id → {material_id, ost_id, material_name}
    pi_by_mat_ost = {}   # (material_id, ost_id) → [pi_id, ...]
    for pi_id, mat_id, ost_id, mat_name in pi_rows:
        pi_id_to_info[pi_id] = {
            "material_id": mat_id, "ost_id": ost_id,
            "material_name": mat_name or "",
        }
        pi_by_mat_ost.setdefault((mat_id, ost_id), []).append(pi_id)

    # ── BomItem (一次, add_type='0') ─────────────────────────────────────────
    bom_rows = db.session.execute(text("""
        SELECT bi.bom_item_id, bi.material_id, b.order_shoe_type_id,
               bi.production_instruction_item_id, m.material_name
        FROM bom_item bi
        JOIN bom b ON b.bom_id = bi.bom_id
        JOIN total_bom tb ON tb.total_bom_id = b.total_bom_id
        JOIN material m ON m.material_id = bi.material_id
        WHERE tb.order_shoe_id = :osid
          AND b.bom_type = 0
          AND bi.bom_item_add_type = '0'
    """), {"osid": order_shoe_id}).fetchall()

    bom_id_to_mat = {}   # bom_id → material_id
    bom_by_mat_ost = {}  # (material_id, ost_id) → [bom_id, ...]
    # PI item IDs that have at least one first-BOM item pointing to them
    pi_ids_with_bom = set()
    for bom_id, mat_id, ost_id, pi_link_id, mat_name in bom_rows:
        bom_id_to_mat[bom_id] = mat_id
        bom_by_mat_ost.setdefault((mat_id, ost_id or 0), []).append(bom_id)
        if pi_link_id:
            pi_ids_with_bom.add(pi_link_id)

    # ── PurchaseOrderItem ────────────────────────────────────────────────────
    po_rows = db.session.execute(text("""
        SELECT poi.purchase_order_item_id, poi.material_id, poi.bom_item_id,
               b.order_shoe_type_id, m.material_name
        FROM purchase_order_item poi
        JOIN purchase_divide_order pdo
          ON pdo.purchase_divide_order_id = poi.purchase_divide_order_id
        JOIN purchase_order po ON po.purchase_order_id = pdo.purchase_order_id
        JOIN material m ON m.material_id = poi.material_id
        LEFT JOIN bom_item bi ON bi.bom_item_id = poi.bom_item_id
        LEFT JOIN bom b ON b.bom_id = bi.bom_id
        WHERE po.order_shoe_id = :osid
    """), {"osid": order_shoe_id}).fetchall()

    # BOM项目中已有采购订单项的 bom_item_id 集合（用于过滤未下采购订单的BOM项）
    bom_ids_with_poi = {
        bom_link_id
        for _, _, bom_link_id, _, _ in po_rows
        if bom_link_id
    }

    # ── 属性一致性检查用的补充查询（单独查以免改动现有元组解包） ─────────────────
    attr_pi = db.session.execute(text("""
        SELECT pii.material_id, pii.order_shoe_type_id,
               pii.material_model, pii.material_specification, pii.color,
               m.material_name
        FROM production_instruction_item pii
        JOIN production_instruction pi
          ON pi.production_instruction_id = pii.production_instruction_id
        JOIN material m ON m.material_id = pii.material_id
        WHERE pi.order_shoe_id = :osid
    """), {"osid": order_shoe_id}).fetchall()

    attr_csi = db.session.execute(text("""
        SELECT csi.material_id, csi.order_shoe_type_id,
               csi.material_model, csi.material_specification, csi.color,
               m.material_name
        FROM craft_sheet_item csi
        JOIN craft_sheet cs ON cs.craft_sheet_id = csi.craft_sheet_id
        JOIN material m ON m.material_id = csi.material_id
        WHERE cs.order_shoe_id = :osid
    """), {"osid": order_shoe_id}).fetchall()

    attr_bom = db.session.execute(text("""
        SELECT bi.material_id, b.order_shoe_type_id,
               bi.material_model, bi.material_specification, bi.bom_item_color,
               m.material_name
        FROM bom_item bi
        JOIN bom b ON b.bom_id = bi.bom_id
        JOIN total_bom tb ON tb.total_bom_id = b.total_bom_id
        JOIN material m ON m.material_id = bi.material_id
        WHERE tb.order_shoe_id = :osid
          AND b.bom_type = 0
          AND bi.bom_item_add_type = '0'
    """), {"osid": order_shoe_id}).fetchall()

    # (material_id, ost_id) → { combos: set, mat_name, has_pi, has_csi }
    attr_map = {}
    def _attr_key(mat_id, ost_id):
        k = (mat_id, ost_id)
        if k not in attr_map:
            attr_map[k] = {"combos": set(), "mat_name": "", "has_pi": False, "has_csi": False}
        return attr_map[k]

    for mat_id, ost_id, model, spec, color, mat_name in attr_pi:
        e = _attr_key(mat_id, ost_id)
        e["combos"].add((model or "", spec or "", color or ""))
        e["mat_name"] = mat_name or ""
        e["has_pi"] = True

    for mat_id, ost_id, model, spec, color, mat_name in attr_csi:
        e = _attr_key(mat_id, ost_id)
        e["combos"].add((model or "", spec or "", color or ""))
        e["mat_name"] = mat_name or ""
        e["has_csi"] = True

    for mat_id, ost_id, model, spec, color, mat_name in attr_bom:
        e = _attr_key(mat_id, ost_id)
        e["combos"].add((model or "", spec or "", color or ""))
        e["mat_name"] = mat_name or ""

    # ── 检查 ─────────────────────────────────────────────────────────────────
    issues = []

    def _issue(doc_type, doc_label, item_id, mat_id, mat_name, ost_id,
               issue_type, description, candidates):
        can_fix = len(candidates) == 1
        return {
            "docType": doc_type, "docLabel": doc_label,
            "itemId": item_id,
            "materialId": mat_id, "materialName": mat_name,
            "orderShoeTypeId": ost_id,
            "issueType": issue_type,
            "description": description,
            "canAutoFix": can_fix,
            "suggestedLinkId": candidates[0] if can_fix else None,
            "candidateCount": len(candidates),
        }

    # PI → BOM（投产指令单中的材料在一次BOM中不存在）
    for pi_id, pi_info in pi_id_to_info.items():
        if pi_id not in pi_ids_with_bom:
            issues.append(_issue(
                "production_instruction_item", "投产指令单",
                pi_id, pi_info["material_id"], pi_info["material_name"],
                pi_info["ost_id"],
                "missing_bom",
                "该材料在一次BOM中无对应记录，需重新同步或手动添加BOM项",
                [],  # 无法自动修复（需创建BOM项）
            ))

    # BOM → PI（仅检查已有对应采购订单项的BOM项）
    for bom_id, mat_id, ost_id, pi_link_id, mat_name in bom_rows:
        if bom_id not in bom_ids_with_poi:
            continue  # 该材料尚未下采购订单，跳过
        if not pi_link_id:
            cands = pi_by_mat_ost.get((mat_id, ost_id), [])
            issues.append(_issue("bom_item", "BOM(一次)", bom_id,
                mat_id, mat_name or "", ost_id,
                "missing_link", "BOM项缺少PI链接", cands))
        else:
            pi_info = pi_id_to_info.get(pi_link_id)
            if pi_info is None:
                cands = pi_by_mat_ost.get((mat_id, ost_id), [])
                issues.append(_issue("bom_item", "BOM(一次)", bom_id,
                    mat_id, mat_name or "", ost_id,
                    "broken_link", f"链接的PI项#{pi_link_id}已不存在", cands))
            elif pi_info["material_id"] != mat_id:
                cands = pi_by_mat_ost.get((mat_id, ost_id), [])
                issues.append(_issue("bom_item", "BOM(一次)", bom_id,
                    mat_id, mat_name or "", ost_id,
                    "wrong_material",
                    f"PI#{pi_link_id}材料不匹配(PI材料ID:{pi_info['material_id']})", cands))

    # POI → BOM（bom_item_id 为空视为采购订单未填写，忽略；仅检查已填写的链接）
    for poi_id, mat_id, bom_link_id, ost_id, mat_name in po_rows:
        if not bom_link_id:
            continue  # 采购订单项未关联BOM，视为未填写，跳过
        linked_mat = bom_id_to_mat.get(bom_link_id)
        if linked_mat is None:
            cands = [bid for bid, mid in bom_id_to_mat.items() if mid == mat_id]
            issues.append(_issue("purchase_order_item", "采购订单", poi_id,
                mat_id, mat_name or "", ost_id,
                "broken_link", f"链接的BOM项#{bom_link_id}已不存在", cands))
        elif linked_mat != mat_id:
            cands = [bid for bid, mid in bom_id_to_mat.items() if mid == mat_id]
            issues.append(_issue("purchase_order_item", "采购订单", poi_id,
                mat_id, mat_name or "", ost_id,
                "wrong_material",
                f"BOM#{bom_link_id}材料不匹配(BOM材料ID:{linked_mat})", cands))

    # ── 属性一致性检查（型号/规格/颜色跨文档是否一致）─────────────────────────
    # 按 material_id 聚合所有 ost_id 的 combo，同一材料在不同配色下属性可以不同，
    # 但同一 (material_id, ost_id) 下 PI/工艺单/BOM 之间属性必须一致。
    # 另外检查：工艺单有记录但投产指令单没有的情况。
    reported_attr = set()  # (mat_id, ost_id) 防重复
    for (mat_id, ost_id), e in attr_map.items():
        if (mat_id, ost_id) in reported_attr:
            continue

        # 工艺单有 但 PI 没有
        if e["has_csi"] and not e["has_pi"]:
            reported_attr.add((mat_id, ost_id))
            issues.append(_issue(
                "craft_sheet_item", "工艺单", None,
                mat_id, e["mat_name"], ost_id,
                "extra_craft_item",
                "工艺单有该材料记录，但投产指令单没有对应项",
                [],
            ))
            continue  # attr_mismatch 也会存在，但 extra_craft_item 已能描述

        # 属性不一致（同一 material_id+ost_id 下有多个不同 model/spec/color 组合）
        if len(e["combos"]) > 1:
            reported_attr.add((mat_id, ost_id))
            parts = [
                f"型号:{m or '空'}/规格:{s or '空'}/颜色:{c or '空'}"
                for m, s, c in sorted(e["combos"])
            ]
            issues.append(_issue(
                "attr_mismatch", "属性不一致", None,
                mat_id, e["mat_name"], ost_id,
                "attr_mismatch",
                "各文档间属性不一致: " + " | ".join(parts),
                [],
            ))

    auto_fixable = sum(1 for i in issues if i["canAutoFix"])
    return jsonify({
        "issues": issues,
        "totalIssues": len(issues),
        "autoFixableCount": auto_fixable,
    })


# ===========================================================================
# 9. 修复材料链路
# ===========================================================================

@material_batch_edit_bp.route("/material/fix-material-links", methods=["POST"])
def fix_material_links():
    """
    按传入的 fixes 列表更新 FK 字段。

    Body: { fixes: [{ docType, itemId, newLinkId }, ...] }
    - craft_sheet_item  → production_instruction_item_id = newLinkId
    - bom_item          → production_instruction_item_id = newLinkId
    - purchase_order_item → bom_item_id = newLinkId
    """
    data = request.get_json() or {}
    fixes = data.get("fixes", [])
    if not fixes:
        return jsonify({"error": "fixes 不能为空"}), 400

    applied = 0
    try:
        for fix in fixes:
            doc_type = fix.get("docType")
            item_id = fix.get("itemId")
            new_link_id = fix.get("newLinkId")
            if not item_id or not new_link_id:
                continue
            if doc_type == "craft_sheet_item":
                CraftSheetItem.query.filter_by(
                    craft_sheet_item_id=item_id
                ).update({"production_instruction_item_id": new_link_id},
                         synchronize_session=False)
                applied += 1
            elif doc_type == "bom_item":
                BomItem.query.filter_by(bom_item_id=item_id).update(
                    {"production_instruction_item_id": new_link_id},
                    synchronize_session=False)
                applied += 1
            elif doc_type == "purchase_order_item":
                PurchaseOrderItem.query.filter_by(
                    purchase_order_item_id=item_id
                ).update({"bom_item_id": new_link_id}, synchronize_session=False)
                applied += 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"修复失败: {str(e)}"}), 500

    return jsonify({"message": f"已修复 {applied} 条记录", "applied": applied})

