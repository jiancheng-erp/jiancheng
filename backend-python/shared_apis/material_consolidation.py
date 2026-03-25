from flask import Blueprint, jsonify, request
from sqlalchemy import text, and_
from app_config import db
from models import (
    Material,
    MaterialType,
    Supplier,
    BomItem,
    PurchaseOrderItem,
    AssetsPurchaseOrderItem,
    ProductionInstructionItem,
    CraftSheetItem,
    SPUMaterial,
    WarehouseMissingPurchaseRecordItem,
)

material_consolidation_bp = Blueprint("material_consolidation_bp", __name__)

# ── 颜色字段名映射（BomItem 的颜色列名不一样） ──
_COLOR_COL = {
    "bom_item": "bom_item_color",
    "purchase_order_item": "color",
    "assets_purchase_order_item": "color",
    "production_instruction_item": "color",
    "craft_sheet_item": "color",
    "spu_material": "color",
    "warehouse_missing_purchase_record_item": "color",
}

_TABLE_MODELS = [
    ("bom_item", BomItem),
    ("purchase_order_item", PurchaseOrderItem),
    ("assets_purchase_order_item", AssetsPurchaseOrderItem),
    ("production_instruction_item", ProductionInstructionItem),
    ("craft_sheet_item", CraftSheetItem),
    ("spu_material", SPUMaterial),
    ("warehouse_missing_purchase_record_item", WarehouseMissingPurchaseRecordItem),
]


def _normalize(s: str) -> str:
    """标准化字符串用于相似度比较：统一小写、去除空白、全角转半角"""
    if not s:
        return ""
    return s.strip().lower().replace(" ", "").replace("\u3000", "").replace("\t", "")


def _fast_similar(a: str, b: str) -> bool:
    """快速判断两个已归一化的字符串是否相似（归一化后相同即视为相似）"""
    return a == b and a != ""


@material_consolidation_bp.route("/material/variants", methods=["GET"])
def get_material_variants():
    """
    使用原生 SQL 高效查询材料变体，包含颜色字段和相似度标记。
    """
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 50, type=int)
    search_name = request.args.get("materialName", "", type=str).strip()
    search_supplier = request.args.get("supplierName", "", type=str).strip()
    search_type = request.args.get("materialType", "", type=str).strip()
    show_all = request.args.get("showAll", "false", type=str).lower() == "true"

    # ── 第 1 步：用原生 SQL 一次性查出按 material_id 分组的变体 ──
    # 每张源表一个 SELECT，用 UNION ALL 合并，然后 GROUP BY
    union_parts = []
    for tbl, _ in _TABLE_MODELS:
        color_col = _COLOR_COL[tbl]
        union_parts.append(
            f"SELECT material_id, "
            f"COALESCE(material_model,'') AS mm, "
            f"COALESCE(material_specification,'') AS ms, "
            f"COALESCE({color_col},'') AS mc, "
            f"'{tbl}' AS src, COUNT(*) AS cnt "
            f"FROM {tbl} WHERE material_id IS NOT NULL "
            f"GROUP BY material_id, mm, ms, mc"
        )

    union_sql = " UNION ALL ".join(union_parts)

    # 第 2 步：先筛选出符合条件的 material_id，同时做 server-side 分页
    where_clauses = []
    params = {}
    if search_name:
        where_clauses.append("m.material_name LIKE :sname")
        params["sname"] = f"%{search_name}%"
    if search_supplier:
        where_clauses.append("s.supplier_name LIKE :ssup")
        params["ssup"] = f"%{search_supplier}%"
    if search_type:
        where_clauses.append("mt.material_type_name LIKE :stype")
        params["stype"] = f"%{search_type}%"

    where_str = (" AND " + " AND ".join(where_clauses)) if where_clauses else ""

    # 统计每个 material_id 有多少不同的 (model, spec, color) 组合
    # 只对有多变体的材料做详细查询
    count_sql = f"""
        SELECT v.material_id, COUNT(DISTINCT CONCAT(v.mm,'|||',v.ms,'|||',v.mc)) AS vc
        FROM ({union_sql}) v
        JOIN material m ON m.material_id = v.material_id
        LEFT JOIN supplier s ON s.supplier_id = m.material_supplier
        LEFT JOIN material_type mt ON mt.material_type_id = m.material_type_id
        WHERE 1=1 {where_str}
        GROUP BY v.material_id
        {"" if show_all else "HAVING vc >= 2"}
        ORDER BY vc DESC
    """
    count_rows = db.session.execute(text(count_sql), params).fetchall()
    total = len(count_rows)

    start = (page - 1) * page_size
    paged_ids = [r[0] for r in count_rows[start : start + page_size]]

    if not paged_ids:
        return jsonify({"result": [], "total": total})

    # 第 3 步：只查询当前页 material_id 的详细变体数据
    id_placeholders = ",".join(str(int(mid)) for mid in paged_ids)
    detail_sql = f"""
        SELECT v.material_id, v.mm, v.ms, v.mc, v.src, v.cnt,
               m.material_name, mt.material_type_name, s.supplier_name
        FROM ({union_sql}) v
        JOIN material m ON m.material_id = v.material_id
        LEFT JOIN supplier s ON s.supplier_id = m.material_supplier
        LEFT JOIN material_type mt ON mt.material_type_id = m.material_type_id
        WHERE v.material_id IN ({id_placeholders})
        ORDER BY v.material_id, v.mm, v.ms, v.mc
    """
    detail_rows = db.session.execute(text(detail_sql)).fetchall()

    # 第 4 步：在 Python 中按 material_id 分组
    materials_map = {}
    for row in detail_rows:
        mid = row[0]
        if mid not in materials_map:
            materials_map[mid] = {
                "materialId": mid,
                "materialName": row[6] or "",
                "materialType": row[7] or "",
                "supplierName": row[8] or "",
                "variants": {},
            }
        vkey = (row[1] or "", row[2] or "", row[3] or "")
        mat = materials_map[mid]
        if vkey not in mat["variants"]:
            mat["variants"][vkey] = {
                "materialModel": vkey[0],
                "materialSpecification": vkey[1],
                "color": vkey[2],
                "sources": {},
                "totalRefs": 0,
            }
        variant = mat["variants"][vkey]
        variant["sources"][row[4]] = row[5]
        variant["totalRefs"] += row[5]

    # 第 5 步：转换并计算相似度
    # 保持 count_rows 的排序顺序
    id_order = {mid: idx for idx, mid in enumerate(paged_ids)}
    result = []
    for mat in materials_map.values():
        variants_list = sorted(mat["variants"].values(), key=lambda v: -v["totalRefs"])
        total_variant_count = len(variants_list)
        # 限制返回的变体数，防止响应过大
        if total_variant_count > 100:
            variants_list = variants_list[:100]
        mat["variants"] = variants_list
        mat["variantCount"] = total_variant_count

        # 相似度分组：找出归一化后相同但原文不同的变体对
        similar_groups = []
        n = len(variants_list)
        if 2 <= n <= 30:
            # 按归一化后的 (model, spec, color) 分桶
            norm_buckets = {}
            for idx, vi in enumerate(variants_list):
                nkey = (
                    _normalize(vi["materialModel"]),
                    _normalize(vi["materialSpecification"]),
                    _normalize(vi["color"]),
                )
                norm_buckets.setdefault(nkey, []).append(idx)
            for nkey, indices in norm_buckets.items():
                if len(indices) >= 2:
                    for ii in range(len(indices)):
                        for jj in range(ii + 1, len(indices)):
                            similar_groups.append({
                                "indexA": indices[ii],
                                "indexB": indices[jj],
                                "similarity": 0.95,
                            })
        mat["similarPairs"] = similar_groups
        mat["_order"] = id_order.get(mat["materialId"], 9999)
        result.append(mat)

    result.sort(key=lambda m: m["_order"])
    for m in result:
        del m["_order"]

    return jsonify({"result": result, "total": total})


def _build_union_sql():
    """构建 UNION ALL 子查询 SQL"""
    parts = []
    for tbl, _ in _TABLE_MODELS:
        cc = _COLOR_COL[tbl]
        parts.append(
            f"SELECT material_id, "
            f"COALESCE(material_model,'') AS mm, "
            f"COALESCE(material_specification,'') AS ms, "
            f"COALESCE({cc},'') AS mc, "
            f"'{tbl}' AS src, COUNT(*) AS cnt "
            f"FROM {tbl} WHERE material_id IS NOT NULL "
            f"GROUP BY material_id, mm, ms, mc"
        )
    return " UNION ALL ".join(parts)


@material_consolidation_bp.route("/material/variants/<int:material_id>", methods=["GET"])
def get_material_variant_detail(material_id):
    """
    获取单个材料的所有变体，支持分页、搜索和相似度匹配。
    参数：
      page, pageSize  - 分页
      keyword         - 搜索型号/规格/颜色
      matchModel      - 自动匹配：标准型号
      matchSpec       - 自动匹配：标准规格
      matchColor      - 自动匹配：标准颜色
    """
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 50, type=int)
    keyword = request.args.get("keyword", "", type=str).strip()
    match_model = request.args.get("matchModel", "", type=str).strip()
    match_spec = request.args.get("matchSpec", "", type=str).strip()
    match_color = request.args.get("matchColor", "", type=str).strip()

    union_sql = _build_union_sql()

    # 查出该材料所有变体
    detail_sql = f"""
        SELECT v.mm, v.ms, v.mc, v.src, v.cnt
        FROM ({union_sql}) v
        WHERE v.material_id = :mid
        ORDER BY v.mm, v.ms, v.mc
    """
    rows = db.session.execute(text(detail_sql), {"mid": material_id}).fetchall()

    # 按 (model, spec, color) 分组
    variants_map = {}
    for row in rows:
        vkey = (row[0] or "", row[1] or "", row[2] or "")
        if vkey not in variants_map:
            variants_map[vkey] = {
                "materialModel": vkey[0],
                "materialSpecification": vkey[1],
                "color": vkey[2],
                "sources": {},
                "totalRefs": 0,
            }
        v = variants_map[vkey]
        v["sources"][row[3]] = row[4]
        v["totalRefs"] += row[4]

    variants_list = sorted(variants_map.values(), key=lambda v: -v["totalRefs"])

    # 如果有自动匹配参数，计算相似度分
    has_match = match_model or match_spec or match_color
    if has_match:
        norm_target_m = _normalize(match_model)
        norm_target_s = _normalize(match_spec)
        norm_target_c = _normalize(match_color)
        for v in variants_list:
            nm = _normalize(v["materialModel"])
            ns = _normalize(v["materialSpecification"])
            nc = _normalize(v["color"])
            # 完全相同 = 标准本身，不标记
            if nm == norm_target_m and ns == norm_target_s and nc == norm_target_c:
                v["similarScore"] = 0
                continue
            score = 0
            # 各字段归一化后相同得分
            if norm_target_m and nm == norm_target_m:
                score += 40
            if norm_target_s and ns == norm_target_s:
                score += 40
            if norm_target_c and nc == norm_target_c:
                score += 20
            # 部分包含关系也给分
            if norm_target_m and nm and (norm_target_m in nm or nm in norm_target_m) and nm != norm_target_m:
                score += 20
            if norm_target_s and ns and (norm_target_s in ns or ns in norm_target_s) and ns != norm_target_s:
                score += 20
            if norm_target_c and nc and (norm_target_c in nc or nc in norm_target_c) and nc != norm_target_c:
                score += 10
            v["similarScore"] = score
        # 按相似度降序排列
        variants_list.sort(key=lambda v: (-v.get("similarScore", 0), -v["totalRefs"]))

    # 关键字搜索过滤
    if keyword:
        kw = keyword.lower()
        variants_list = [
            v for v in variants_list
            if kw in (v["materialModel"] or "").lower()
            or kw in (v["materialSpecification"] or "").lower()
            or kw in (v["color"] or "").lower()
        ]

    total_variants = len(variants_list)
    start = (page - 1) * page_size
    paged = variants_list[start : start + page_size]

    return jsonify({"variants": paged, "total": total_variants})


@material_consolidation_bp.route(
    "/material/merge-variants", methods=["POST"]
)
def merge_material_variants():
    """
    合并材料变体：将旧的 (model, spec, color) 统一替换为新值。
    请求体：
    {
        "materialId": 123,
        "newModel": "1.0mm",
        "newSpecification": "头层牛皮",
        "newColor": "黑色",
        "oldVariants": [
            {"materialModel": "1.0MM", "materialSpecification": "头层牛皮", "color": "黑色"},
            {"materialModel": "1.0 mm", "materialSpecification": "头层牛皮 ", "color": "黑"}
        ]
    }
    """
    data = request.get_json()
    material_id = data.get("materialId")
    new_model = (data.get("newModel") or "").strip()
    new_spec = (data.get("newSpecification") or "").strip()
    new_color = (data.get("newColor") or "").strip()
    old_variants = data.get("oldVariants", [])

    if not material_id or not old_variants:
        return jsonify({"error": "缺少必要参数"}), 400

    total_updated = 0
    try:
        for old_v in old_variants:
            old_model = (old_v.get("materialModel") or "").strip()
            old_spec = (old_v.get("materialSpecification") or "").strip()
            old_color = (old_v.get("color") or "").strip()

            # 跳过与目标完全相同的
            if old_model == new_model and old_spec == new_spec and old_color == new_color:
                continue

            for tbl_name, Model in _TABLE_MODELS:
                color_attr_name = _COLOR_COL[tbl_name]
                color_attr = getattr(Model, color_attr_name)

                # 构建 WHERE 条件
                conditions = [Model.material_id == material_id]

                if old_model:
                    conditions.append(Model.material_model == old_model)
                else:
                    conditions.append(
                        (Model.material_model == None)
                        | (Model.material_model == "")
                    )

                if old_spec:
                    conditions.append(Model.material_specification == old_spec)
                else:
                    conditions.append(
                        (Model.material_specification == None)
                        | (Model.material_specification == "")
                    )

                if old_color:
                    conditions.append(color_attr == old_color)
                else:
                    conditions.append(
                        (color_attr == None) | (color_attr == "")
                    )

                update_vals = {
                    Model.material_model: new_model if new_model else None,
                    Model.material_specification: new_spec if new_spec else None,
                    color_attr: new_color if new_color else None,
                }

                updated = (
                    Model.query.filter(and_(*conditions))
                    .update(update_vals, synchronize_session=False)
                )
                total_updated += updated

        db.session.commit()
        return jsonify(
            {"message": f"合并完成，共更新 {total_updated} 条记录", "updatedCount": total_updated}
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"合并失败: {str(e)}"}), 500


@material_consolidation_bp.route(
    "/material/rename", methods=["POST"]
)
def rename_material():
    """
    修改材料名称（material 主表）
    请求体：
    {
        "materialId": 123,
        "newName": "新材料名"
    }
    """
    data = request.get_json()
    material_id = data.get("materialId")
    new_name = (data.get("newName") or "").strip()

    if not material_id or not new_name:
        return jsonify({"error": "缺少必要参数"}), 400

    try:
        mat = Material.query.get(material_id)
        if not mat:
            return jsonify({"error": "材料不存在"}), 404

        # 检查唯一约束：同供应商下不能重名
        existing = Material.query.filter(
            Material.material_supplier == mat.material_supplier,
            Material.material_name == new_name,
            Material.material_id != material_id,
        ).first()
        if existing:
            return jsonify(
                {"error": f"同供应商下已存在名为 '{new_name}' 的材料 (ID={existing.material_id})"}
            ), 409

        old_name = mat.material_name
        mat.material_name = new_name
        db.session.commit()
        return jsonify(
            {"message": f"材料名称已从 '{old_name}' 修改为 '{new_name}'"}
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"修改失败: {str(e)}"}), 500
