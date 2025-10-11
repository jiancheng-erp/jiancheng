from typing import List
from flask import Blueprint, jsonify, request, send_file, current_app
from sqlalchemy.dialects.mysql import insert
import datetime
from app_config import db
from models import *
import os
from api_utility import randomIdGenerater
from event_processor import EventProcessor
from file_locations import IMAGE_STORAGE_PATH, FILE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from general_document.bom import generate_excel_file
from collections import defaultdict
from shared_apis.batch_info_type import get_order_batch_type_helper
from constants import SHOESIZERANGE
from sqlalchemy.sql.expression import case, func
from sqlalchemy.orm import aliased
from sqlalchemy import and_, case, func, text, literal
from logger import logger
from script.sync_second_bom_to_poi import sync_for_ost_ids

second_bom_bp = Blueprint("second_bom_bp", __name__)


@second_bom_bp.route("/secondbom/getnewbomid", methods=["GET"])
def get_new_bom_id():
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    bom_id = current_time_stamp + random_string + "F"
    return jsonify({"bomId": bom_id})


@second_bom_bp.route("/secondbom/getordershoes", methods=["GET"])
def get_order_second_bom():
    order_id = request.args.get("orderid")

    # Querying the necessary data with joins and filters
    entities = (
        db.session.query(
            Order,
            OrderShoe,
            OrderShoeType,
            Shoe,
            ShoeType,
            Color,
            Bom,
            TotalBom,
            PurchaseOrder,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .outerjoin(
            Bom, OrderShoeType.order_shoe_type_id == Bom.order_shoe_type_id
        )  # Assuming BOM is optional
        .outerjoin(TotalBom, Bom.total_bom_id == TotalBom.total_bom_id)
        .outerjoin(PurchaseOrder, PurchaseOrder.bom_id == TotalBom.total_bom_id)
        .filter(Order.order_id == order_id)
        .all()
    )

    logger.debug(entities)

    # Initialize the result list
    result_dict = {}

    # Loop through the entities to build the result
    for entity in entities:
        (
            order,
            order_shoe,
            order_shoe_type,
            shoe,
            shoe_type,
            color,
            bom,
            total_bom,
            purchase_order,
        ) = entity
        status_string = ""
        statuses = (
            db.session.query(OrderShoeStatus, OrderShoeStatusReference)
            .join(
                OrderShoeStatusReference,
                OrderShoeStatus.current_status == OrderShoeStatusReference.status_id,
            )
            .filter(OrderShoeStatus.order_shoe_id == order_shoe.order_shoe_id)
            .all()
        )
        for status in statuses:
            status_string = (
                status_string + status.OrderShoeStatusReference.status_name + " "
            )

        # Grouping by shoe_rid (inheritId) to avoid duplicate shoes
        # Initialize the result dictionary for the shoe if not already present
        if shoe.shoe_rid not in result_dict:
            result_dict[shoe.shoe_rid] = {
                "orderId": order.order_rid,
                "orderShoeId": order_shoe.order_shoe_id,
                "inheritId": shoe.shoe_rid,
                "status": status_string,
                "customerId": order_shoe.customer_product_name,
                "designer": shoe.shoe_designer,
                "editter": order_shoe.adjust_staff,
                "typeInfos": [],  # Initialize list for type info (colors, etc.)
                "colorSet": set(),  # Initialize set to track colors and prevent duplicate entries
            }

        # Check if this color already exists in typeInfos
        existing_entry = next(
            (
                info
                for info in result_dict[shoe.shoe_rid]["typeInfos"]
                if info["color"] == color.color_name
            ),
            None,
        )

        # Prepare BOM and PurchaseOrder details
        first_bom_id = None
        first_bom_status = "未填写"
        first_purchase_order_id = None
        first_purchase_order_status = "未填写"
        second_bom_id = None
        second_bom_status = "未填写"
        second_purchase_order_id = None
        second_purchase_order_status = "未填写"

        # Set BOM details based on bom_type
        if bom:
            if bom.bom_type == 0:
                first_bom_id = bom.bom_rid
                first_bom_status = {
                    "1": "材料已保存",
                    "2": "材料已提交",
                    "3": "等待用量填写",
                    "4": "用量填写已保存",
                    "5": "用量填写已提交",
                    "6": "用量填写已下发",
                }.get(bom.bom_status, "未填写")
            elif bom.bom_type == 1:
                second_bom_id = bom.bom_rid
                second_bom_status = {"1": "已保存", "2": "已提交", "3": "已下发"}.get(
                    bom.bom_status, "未填写"
                )

        # Set PurchaseOrder details based on purchase_order_type
        if purchase_order:
            if purchase_order.purchase_order_type == "F":
                first_purchase_order_id = purchase_order.purchase_order_rid
                first_purchase_order_status = {
                    "1": "已保存",
                    "2": "已提交",
                    "3": "已下发",
                }.get(purchase_order.purchase_order_status, "未填写")
            elif purchase_order.purchase_order_type == "S":
                second_purchase_order_id = purchase_order.purchase_order_rid
                second_purchase_order_status = {
                    "1": "已保存",
                    "2": "已提交",
                    "3": "已下发",
                }.get(purchase_order.purchase_order_status, "未填写")

        # If the color entry already exists, update it with BOM details
        if existing_entry:
            logger.debug(existing_entry)
            # Update only if fields are not already filled to prevent overwriting
            if first_bom_id and existing_entry.get("firstBomId") == "未填写":
                existing_entry["firstBomId"] = first_bom_id
                existing_entry["firstBomStatus"] = first_bom_status
                existing_entry["firstPurchaseOrderId"] = first_purchase_order_id
                existing_entry["firstPurchaseOrderStatus"] = first_purchase_order_status

            if second_bom_id and existing_entry.get("secondBomId") == "未填写":
                existing_entry["secondBomId"] = second_bom_id
                existing_entry["secondBomStatus"] = second_bom_status
                existing_entry["secondPurchaseOrderId"] = second_purchase_order_id
                existing_entry["secondPurchaseOrderStatus"] = (
                    second_purchase_order_status
                )
        else:
            # If the color doesn't exist, create a new entry in typeInfos
            result_dict[shoe.shoe_rid]["typeInfos"].append(
                {
                    "orderShoeTypeId": order_shoe_type.order_shoe_type_id,
                    "orderShoeRid": shoe.shoe_rid,
                    "color": color.color_name,
                    "image": (
                        IMAGE_STORAGE_PATH + shoe_type.shoe_image_url
                        if shoe_type.shoe_image_url
                        else None
                    ),
                    "firstBomId": first_bom_id if first_bom_id else "未填写",
                    "firstBomStatus": first_bom_status,
                    "firstPurchaseOrderId": (
                        first_purchase_order_id if first_purchase_order_id else "未填写"
                    ),
                    "firstPurchaseOrderStatus": first_purchase_order_status,
                    "secondBomId": second_bom_id if second_bom_id else "未填写",
                    "secondBomStatus": second_bom_status,
                    "secondPurchaseOrderId": (
                        second_purchase_order_id
                        if second_purchase_order_id
                        else "未填写"
                    ),
                    "secondPurchaseOrderStatus": second_purchase_order_status,
                }
            )

        # Add the color to colorSet to prevent future duplicates
        result_dict[shoe.shoe_rid]["colorSet"].add(color.color_name)

    # Remove the colorSet before returning the result
    for shoe_rid in result_dict:
        result_dict[shoe_rid].pop("colorSet")

    # Convert result_dict to a list of values
    result = list(result_dict.values())

    return jsonify(result)


@second_bom_bp.route("/secondbom/getcurrentbom", methods=["GET"])
def get_current_bom():
    order_shoe_type_id = request.args.get("ordershoetypeid")
    bom = (
        db.session.query(Bom, OrderShoeType)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == "1")
        .first()
    )
    bom_id = bom.Bom.bom_id
    result = {
        "bomId": bom.Bom.bom_rid,
    }
    return jsonify(result)



@second_bom_bp.route("/secondbom/getcurrentbomitem", methods=["GET"])
def get_current_bom_item():
    # 1) 参数 & 类型
    order_shoe_type_id = request.args.get("ordershoetypeid")
    try:
        order_shoe_type_id = int(order_shoe_type_id)
    except (TypeError, ValueError):
        return jsonify([])

    # 2) 二次 BOM（bom_type = 1）——拿到 bom_id
    bom_id = (
        db.session.query(Bom.bom_id)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 1)
        .scalar()
    )
    if not bom_id:
        return jsonify([])

    # 3) 仅用于“排序”的 Craft 子查询（不含 color；同一 (m_id, m_model, m_spec) 取任一 material_type）
    csi_type_sub = (
        db.session.query(
            CraftSheetItem.material_id.label("m_id"),
            CraftSheetItem.material_model.label("m_model"),
            CraftSheetItem.material_specification.label("m_spec"),
            CraftSheetItem.order_shoe_type_id.label("ostid"),
            func.min(CraftSheetItem.material_type).label("mt"),  # 取最小保证确定性
        )
        .filter(CraftSheetItem.order_shoe_type_id == order_shoe_type_id)
        .group_by(
            CraftSheetItem.material_id,
            CraftSheetItem.material_model,
            CraftSheetItem.material_specification,
            CraftSheetItem.order_shoe_type_id,
        )
    ).subquery("csi_type_sub")

    # 4) 首 BOM（bom_type = 0）单位用量一次性取回，按 (material_id, model, spec) 聚合
    first_bom_sub = (
        db.session.query(
            BomItem.material_id.label("fb_m_id"),
            BomItem.material_model.label("fb_m_model"),
            BomItem.material_specification.label("fb_m_spec"),
            func.max(BomItem.unit_usage).label("first_unit_usage"),
        )
        .join(Bom, BomItem.bom_id == Bom.bom_id)
        .filter(
            Bom.order_shoe_type_id == order_shoe_type_id,
            Bom.bom_type == 0,
        )
        .group_by(
            BomItem.material_id,
            BomItem.material_model,
            BomItem.material_specification,
        )
    ).subquery("first_bom_sub")

    # 5) 排序桶：基于 Craft 的 material_type（缺失放到最后）
    sort_bucket = case(
        (csi_type_sub.c.mt == "S", 1),
        (csi_type_sub.c.mt == "I", 2),
        (csi_type_sub.c.mt == "A", 3),
        (csi_type_sub.c.mt == "O", 4),
        (csi_type_sub.c.mt == "M", 5),
        (csi_type_sub.c.mt == "H", 6),
        else_=literal(7),
    ).label("sort_bucket")

    # 6) 主查询：连接“排序子表”和“首 BOM 用量子表”
    #    连接表达式使用 IFNULL 与上面子表保持一致；若你把空串统一为 NULL，可改为 NULL-safe 等号 <=>（见下方注释）。
    q = (
        db.session.query(
            BomItem,
            Material,
            MaterialType,
            Department,
            Supplier,
            first_bom_sub.c.first_unit_usage.label("first_bom_usage"),
            sort_bucket,
        )
        .select_from(BomItem)
        .join(Material, BomItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .outerjoin(Department, BomItem.department_id == Department.department_id)
        .outerjoin(Supplier, Material.material_supplier == Supplier.supplier_id)
        .outerjoin(
            csi_type_sub,
            and_(
                csi_type_sub.c.m_id == BomItem.material_id,
                func.ifnull(csi_type_sub.c.m_model, "") == func.ifnull(BomItem.material_model, ""),
                func.ifnull(csi_type_sub.c.m_spec,  "") == func.ifnull(BomItem.material_specification, ""),
                csi_type_sub.c.ostid == order_shoe_type_id,
            ),
        )
        .outerjoin(
            first_bom_sub,
            and_(
                first_bom_sub.c.fb_m_id == BomItem.material_id,
                func.ifnull(first_bom_sub.c.fb_m_model, "") == func.ifnull(BomItem.material_model, ""),
                func.ifnull(first_bom_sub.c.fb_m_spec,  "") == func.ifnull(BomItem.material_specification, ""),
            ),
        )
        .filter(BomItem.bom_id == bom_id)
        .order_by(
            sort_bucket.asc(),
            Supplier.supplier_name.asc(),
            Material.material_name.asc(),
            BomItem.bom_item_id.asc(),  # 稳定兜底
        )
    )

    bom_rows = q.all()

    # 7) order_id -> size names
    order_id = (
        db.session.query(Order.order_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
        .scalar()
    )
    shoe_size_names = get_order_batch_type_helper(order_id) or []

    # 8) 组装结果
    result = []
    for bom_item, material, material_type, department, supplier, first_bom_usage, _sort_bucket in bom_rows:
        sizeInfo = []
        for i, sz in enumerate(shoe_size_names):
            index = i + 34
            val = getattr(bom_item, f"size_{index}_total_usage")
            sizeInfo.append({
                "size": sz["label"],
                "approvalAmount": val if val else 0.0,
            })

        result.append({
            "bomItemId": bom_item.bom_item_id,
            "materialName": material.material_name,
            "materialType": material_type.material_type_name,
            "materialModel": bom_item.material_model,
            "materialSpecification": bom_item.material_specification,
            "supplierName": supplier.supplier_name if supplier else None,
            "firstBomUsage": first_bom_usage or 0.0,
            "useDepart": department.department_id if department else None,
            "pairs": bom_item.pairs or 0.0,
            "craftName": bom_item.craft_name,
            "unitUsage": (bom_item.unit_usage if bom_item.unit_usage else (0.0 if material.material_category == 0 else None)),
            "approvalUsage": bom_item.total_usage or 0.0,
            "unit": material.material_unit,
            "color": bom_item.bom_item_color,
            "comment": bom_item.remark,
            "materialCategory": material.material_category,
            "sizeInfo": sizeInfo,
        })

    return jsonify(result)


@second_bom_bp.route("/secondbom/savebom", methods=["POST"])
def save_bom_usage():
    bom_rid = request.json.get("bomRid")
    bom_items = request.json.get("bomItems")
    bom = db.session.query(Bom).filter(Bom.bom_rid == bom_rid).first()
    bom.bom_status = "1"
    db.session.flush()
    for bom_item in bom_items:
        if not bom_item["bomItemId"]:
            material_id = (
                db.session.query(Material, Supplier)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .filter(
                    Material.material_name == bom_item["materialName"],
                    Supplier.supplier_name == bom_item["supplierName"],
                )
                .first()
                .Material.material_id
            )
            bom_item_entity = BomItem(
                bom_id=bom.bom_id,
                material_id=material_id,
                unit_usage=bom_item["unitUsage"],
                total_usage=bom_item["approvalUsage"],
                department_id=bom_item["useDepart"],
                material_model=(
                    bom_item["materialModel"] if bom_item["materialModel"] else ""
                ),
                remark=bom_item["comment"],
                material_specification=(
                    bom_item["materialSpecification"]
                    if bom_item["materialSpecification"]
                    else ""
                ),
                bom_item_add_type=1,
                bom_item_color=bom_item["color"] if bom_item["color"] else None,
                pairs=bom_item["pairs"] if bom_item["pairs"] else 0.00,
            )
            for i in range(len(bom_item["sizeInfo"])):
                name = i + 34
                setattr(
                    bom_item_entity,
                    f"size_{name}_total_usage",
                    bom_item["sizeInfo"][i]["approvalAmount"],
                )
            db.session.add(bom_item_entity)
            db.session.flush()
            bom_item["bomItemId"] = bom_item_entity.bom_item_id
        else:
            entity = (
                db.session.query(BomItem)
                .filter(BomItem.bom_item_id == bom_item["bomItemId"])
                .first()
            )
            for i in range(len(bom_item["sizeInfo"])):
                setattr(
                    entity,
                    f"size_{i}_total_usage",
                    bom_item["sizeInfo"][i]["approvalAmount"],
                )
            entity.total_usage = bom_item["approvalUsage"]
            entity.unit_usage = bom_item["unitUsage"]
            entity.remark = bom_item["comment"] if bom_item["comment"] else ""
            entity.department_id = bom_item["useDepart"]
            entity.material_model = (
                bom_item["materialModel"] if bom_item["materialModel"] else None
            )
            entity.material_specification = (
                bom_item["materialSpecification"]
                if bom_item["materialSpecification"]
                else None
            )
            entity.bom_item_color = bom_item["color"] if bom_item["color"] else None
            entity.bom_item_add_type = 1
            entity.pairs = bom_item["pairs"] if bom_item["pairs"] else 0.00
            db.session.flush()
    order_shoe_status = (
        db.session.query(OrderShoeStatus)
        .join(OrderShoe, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == bom.order_shoe_type_id)
        .filter(OrderShoeStatus.current_status == 11)
        .first()
    )
    order_shoe_status.current_status_value = 1
    db.session.commit()
    return jsonify({"status": "success"})


@second_bom_bp.route("/secondbom/editbom", methods=["POST"])
def edit_bom():
    bom_rid = request.json.get("bomId")
    bom_data = request.json.get("bomData")
    bom_id = Bom.query.filter(Bom.bom_rid == bom_rid, Bom.bom_type == 1).first().bom_id
    logger.debug(bom_data)
    for item in bom_data:
        material_id = (
            db.session.query(Material, Supplier)
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(
                Material.material_name == item["materialName"],
                Supplier.supplier_name == item["supplierName"],
            )
            .first()
            .Material.material_id
        )
        bom_item = (
            db.session.query(BomItem)
            .filter(BomItem.bom_item_id == item["bomItemId"])
            .first()
        )
        bom_item.material_id = material_id
        bom_item.unit_usage = item["unitUsage"]
        bom_item.total_usage = item["approvalUsage"]
        bom_item.pairs = item["pairs"]
        length = min(len(SHOESIZERANGE), len(item["sizeInfo"]))
        for i in range(length):
            db_size = i + 34
            setattr(
                bom_item,
                f"size_{db_size}_total_usage",
                item["sizeInfo"][i]["approvalAmount"],
            )
        db.session.flush()
    db.session.commit()
    return jsonify({"status": "success"})


@second_bom_bp.route("/secondbom/submitbom", methods=["POST"])
def submit_bom():
    order_rid = request.json.get("orderid")
    order_shoe_rid = request.json.get("ordershoerid")
    order_shoe_type_id = request.json.get("ordershoetypeid")
    bom = (
        db.session.query(Bom, OrderShoeType, OrderShoe)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 1)
        .first()
    )
    order_shoe_id = bom.OrderShoe.order_shoe_id
    bom_id = bom.Bom.bom_id
    bom.Bom.bom_status = 2
    db.session.commit()

    return jsonify({"status": "success"})


@second_bom_bp.route("/secondbom/issueboms", methods=["POST"])
def issue_boms():
    payload = request.get_json(silent=True) or {}
    order_rid = payload.get("orderId")
    order_shoe_rids = payload.get("orderShoeIds") or []
    colors_matrix = payload.get("colors") or []

    if not order_rid or not order_shoe_rids:
        return jsonify({"message": "orderId or orderShoeIds missing"}), 400

    order = db.session.query(Order).filter(Order.order_rid == order_rid).first()
    if not order:
        return jsonify({"message": f"order {order_rid} not found"}), 404
    order_id = order.order_id

    material_dict = defaultdict(lambda: {"total_usage": 0})
    series_data = []
    affected_ost_ids: List[int] = []   # ★ 本次下发涉及的 ost，后面只同步这些

    for idx, order_shoe_rid in enumerate(order_shoe_rids):
        color_list = colors_matrix[idx] if idx < len(colors_matrix) else []

        entities = (
            db.session.query(OrderShoe, Shoe)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .filter(OrderShoe.order_id == order_id, Shoe.shoe_rid == order_shoe_rid)
            .first()
        )
        if not entities:
            logger.warning(f"[issue_boms] order_shoe_rid={order_shoe_rid} not found under order {order_rid}")
            continue

        order_shoe_id = entities.OrderShoe.order_shoe_id

        craft_sheet = (
            db.session.query(CraftSheet)
            .filter(CraftSheet.order_shoe_id == order_shoe_id)
            .first()
        )
        if not craft_sheet:
            return jsonify({"message": f"craft sheet not found for {order_shoe_rid}"}), 400
        craft_sheet_id = craft_sheet.craft_sheet_id

        entities.OrderShoe.process_sheet_upload_status = "3"

        current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
        random_string = randomIdGenerater(6)
        total_bom_rid = current_time_stamp + random_string + "TS"
        total_bom = TotalBom(total_bom_rid=total_bom_rid, order_shoe_id=order_shoe_id)
        db.session.add(total_bom)
        db.session.flush()

        for color_item in color_list:
            # 定位 ost
            ost_row = (
                db.session.query(Order, OrderShoe, Shoe, ShoeType, OrderShoeType, Color)
                .join(OrderShoe, Order.order_id == OrderShoe.order_id)
                .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
                .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
                .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
                .join(Color, ShoeType.color_id == Color.color_id)
                .filter(
                    Order.order_rid == order_rid,
                    Shoe.shoe_rid == order_shoe_rid,
                    Color.color_name == color_item,
                )
                .first()
            )
            if not ost_row:
                logger.warning(f"[issue_boms] ost not found for shoe_rid={order_shoe_rid}, color={color_item}")
                continue

            order_shoe_type_id = ost_row.OrderShoeType.order_shoe_type_id
            affected_ost_ids.append(order_shoe_type_id)  # ★ 纳入本次处理范围

            # 置二次BOM为“已下发”并挂 total_bom
            bom = (
                db.session.query(Bom)
                .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 1)
                .first()
            )
            if not bom:
                logger.warning(f"[issue_boms] second BOM missing for ost={order_shoe_type_id}")
                continue

            bom.bom_status = "3"
            bom.total_bom_id = total_bom.total_bom_id
            db.session.flush()

            # ====== 原 CraftSheetItem & 导出数据收集逻辑 ======
            bom_id = bom.bom_id
            bom_items = (
                db.session.query(BomItem, Material, MaterialType, Supplier, Department)
                .join(Material, Material.material_id == BomItem.material_id)
                .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .outerjoin(Department, Department.department_id == BomItem.department_id)
                .filter(BomItem.bom_id == bom_id)
                .all()
            )
            for bom_item in bom_items:
                # logger.debug(
                #     bom_item.Material.material_name,
                #     bom_item.BomItem.material_model,
                #     bom_item.BomItem.material_specification,
                #     craft_sheet_id,
                # )
                craft_sheet_item = (
                    db.session.query(CraftSheetItem)
                    .filter(
                        CraftSheetItem.craft_sheet_id == craft_sheet_id,
                        CraftSheetItem.order_shoe_type_id == order_shoe_type_id,
                        CraftSheetItem.material_id == bom_item.Material.material_id,
                        func.coalesce(CraftSheetItem.material_model, '') == func.coalesce(bom_item.BomItem.material_model, ''),
                        func.coalesce(CraftSheetItem.material_specification, '') == func.coalesce(bom_item.BomItem.material_specification, ''),
                        func.coalesce(CraftSheetItem.color, '') == func.coalesce(bom_item.BomItem.bom_item_color, ''),
                        CraftSheetItem.after_usage_symbol == 0,
                    )
                    .first()
                )
                if craft_sheet_item:
                    new_craft_sheet_item = CraftSheetItem(
                        craft_sheet_id=craft_sheet_id,
                        material_id=craft_sheet_item.material_id,
                        material_model=craft_sheet_item.material_model,
                        material_specification=craft_sheet_item.material_specification,
                        color=craft_sheet_item.color,
                        remark=craft_sheet_item.remark,
                        department_id=craft_sheet_item.department_id,
                        material_type=craft_sheet_item.material_type,
                        order_shoe_type_id=order_shoe_type_id,
                        material_second_type=craft_sheet_item.material_second_type,
                        craft_name=bom_item.BomItem.craft_name,
                        pairs=bom_item.BomItem.pairs,
                        unit_usage=bom_item.BomItem.unit_usage,
                        total_usage=bom_item.BomItem.total_usage,
                        after_usage_symbol=1,
                    )
                    db.session.add(new_craft_sheet_item)
                    db.session.flush()

                key = (
                    bom_item.MaterialType.material_type_name,
                    bom_item.Material.material_name,
                    bom_item.BomItem.material_model,
                    bom_item.BomItem.material_specification,
                    bom_item.Supplier.supplier_name,
                    bom_item.BomItem.bom_item_color,
                )
                if key not in material_dict:
                    material_dict[key] = {
                        "材料类型": bom_item.MaterialType.material_type_name,
                        "材料名称": bom_item.Material.material_name,
                        "材料型号": bom_item.BomItem.material_model,
                        "材料规格": bom_item.BomItem.material_specification,
                        "颜色": bom_item.BomItem.bom_item_color,
                        "单位": bom_item.Material.material_unit,
                        "厂家名称": bom_item.Supplier.supplier_name,
                        "单位用量": (bom_item.BomItem.unit_usage or ""),
                        "核定用量": 0,
                        "使用工段": (bom_item.Department.department_name if bom_item.Department else ""),
                        "备注": bom_item.BomItem.remark,
                    }
                material_dict[key]["核定用量"] += bom_item.BomItem.total_usage

        # 清理“发放前”的 craft_sheet_item
        before_usage_craft_sheet_items = (
            db.session.query(CraftSheetItem)
            .filter(
                CraftSheetItem.craft_sheet_id == craft_sheet_id,
                CraftSheetItem.after_usage_symbol == 0,
            )
            .all()
        )
        for item in before_usage_craft_sheet_items:
            db.session.delete(item)

        # 导出 Excel 所需数据
        index = 1
        for material_info in material_dict.values():
            material_info["序号"] = index
            series_data.append(material_info)
            index += 1

        secondbom_dir = os.path.join(FILE_STORAGE_PATH, order_rid, order_shoe_rid, "secondbom")
        os.makedirs(secondbom_dir, exist_ok=True)

        image_save_path = os.path.join(secondbom_dir, "shoe_image.jpg")
        logger.debug(image_save_path)

        shoe_directory = os.path.join(IMAGE_UPLOAD_PATH, "shoe", order_shoe_rid)
        folders = [f for f in os.listdir(shoe_directory) if os.path.isdir(os.path.join(shoe_directory, f))]
        if folders:
            first_folder = folders[0]
            image_path = os.path.join(IMAGE_UPLOAD_PATH, "shoe", order_shoe_rid, first_folder, "shoe_image.jpg")
        else:
            image_path = os.path.join(IMAGE_UPLOAD_PATH, "shoe", order_shoe_rid, "shoe_image.jpg")

        generate_excel_file(
            FILE_STORAGE_PATH + "/BOM-V1.0-temp.xlsx",
            os.path.join(secondbom_dir, "二次BOM表.xlsx"),
            {
                "order_id": order_rid,
                "last_type": "",
                "input_person": "",
                "order_finish_time": db.session.query(Order).filter(Order.order_rid == order_rid).first().end_date,
                "inherit_id": order_shoe_rid,
                "customer_id": db.session.query(OrderShoe).filter(OrderShoe.order_shoe_id == order_shoe_id).first().customer_product_name,
            },
            series_data,
            image_path,
            image_save_path,
        )

        # 触发事件
        processor: EventProcessor = current_app.config.get("event_processor")
        if processor:
            event_list = []
            try:
                for operation_id in [60, 61, 62, 63]:
                    event = Event(
                        staff_id=1,
                        handle_time=datetime.datetime.now(),
                        operation_id=operation_id,
                        event_order_id=order_id,
                        event_order_shoe_id=order_shoe_id,
                    )
                    processor.processEvent(event)
                    event_list.append(event)
            except Exception as e:
                logger.exception(f"[issue_boms] event processing failed: {e}")
                return jsonify({"message": "failed"}), 400
            db.session.add_all(event_list)

        db.session.flush()


    affected_ost_ids = list({int(x) for x in affected_ost_ids})
    new_bom_cnt, new_poitem_cnt = sync_for_ost_ids(db.session, affected_ost_ids, dry_run=False)
    logger.info(f"[issue_boms] synced ost={len(affected_ost_ids)}; new primary BOM items={new_bom_cnt}, new PO items={new_poitem_cnt}")

    db.session.commit()
    return jsonify({"status": "success"})



@second_bom_bp.route("/secondbom/download", methods=["GET"])
def download_bom():
    order_shoe_rid = request.args.get("ordershoerid")
    order_id = request.args.get("orderid")
    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid)
    file_path = os.path.join(folder_path, "secondbom", "二次BOM表.xlsx")
    new_name = order_id + "-" + order_shoe_rid + "_二次BOM表.xlsx"
    return send_file(file_path, as_attachment=True, download_name=new_name)
