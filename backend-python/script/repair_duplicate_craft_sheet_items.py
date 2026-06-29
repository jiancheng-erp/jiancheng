"""
批量修复「二次用量下发后从采购退回改投产指令单，再次下发导致工艺单材料重复」的问题。

背景
----
二次用量下发（``/secondbom/issueboms``）会依据「二次BOM」为每个 BOM 行生成一条
``after_usage_symbol='1'`` 的工艺单快照，并删除 ``after_usage_symbol='0'`` 的下发前行。
生成的快照行不带 ``production_instruction_item_id``。

当订单从采购退回、重新编辑投产指令单时，旧逻辑按 ``production_instruction_item_id``
匹配工艺单行，但下发快照行该字段为 NULL，匹配不到，于是把所有材料当成新行重复插入
（重复行用量为 0），再次下发后快照层再翻倍。结果：工艺单中每个材料出现两遍。

修复原理
--------
``after_usage_symbol='1'`` 的工艺单快照与「二次BOM」是一一对应关系（下发时按二次BOM
逐行生成）。因此凡是无法对应到当前二次BOM行的 ``after_usage_symbol='1'`` 工艺单行，
都是退回前残留的陈旧副本（包括烫底工艺被修改后、craft_name 已变化的旧行），应当删除。

本脚本按「订单鞋型 + 材料标识(材料/型号/规格/颜色/工艺名) 」把现存的下发快照行与当前
二次BOM行做匹配：
- 每个二次BOM行最多保留一条对应的工艺单快照行（多出的视为重复，删除）；
- 没有任何二次BOM行可对应的快照行（孤立/陈旧），删除；
- 若该鞋型的二次BOM尚未下发（bom_status != '3'），则其下发快照行本不该存在，全部删除；
- ``after_usage_symbol='0'`` 的下发前行不受影响。

保留策略：同一标识有多条候选时，保留 craft_sheet_item_id 最大（最新、含再次下发后的
正确用量）的一条，删除较旧的重复行。

安全
----
默认 **dry-run**，只打印将要删除的行，不修改数据库。确认无误后加 ``--apply`` 才真正提交。
可用 ``--orders RID1,RID2`` 仅处理指定订单。

用法（在 backend-python 目录下）::

    python script/repair_duplicate_craft_sheet_items.py            # 预演，仅报告
    python script/repair_duplicate_craft_sheet_items.py --orders K24001,K24002
    python script/repair_duplicate_craft_sheet_items.py --apply    # 实际执行
"""

import argparse
import os
import sys
from collections import defaultdict

# 允许从 backend-python 目录直接运行：把项目根目录加入模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 在导入 config / app 之前加载 .env，确保 ProductionConfig 能读到数据库等环境变量
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from config import ProductionConfig
from models import (
    Order,
    OrderShoe,
    Shoe,
    OrderShoeType,
    Bom,
    BomItem,
    CraftSheet,
    CraftSheetItem,
    ProductionInstruction,
    ProductionInstructionItem,
)

# 二次BOM「已下发」状态码（见 issue_boms 中 bom.bom_status = "3"）
SECOND_BOM_ISSUED_STATUS = "3"


def _norm(value) -> str:
    """把 None 与空白统一为去空格字符串，便于匹配比较。"""
    if value is None:
        return ""
    return str(value).strip()


def _is_zero_usage(item) -> bool:
    """该工艺单行是否「用量为 0」（单位用量与核定用量均为空或 0）。

    用户规则：用量非为 0 的材料一律不删除——这类行可能是手工补录的真实用量，
    必须保留；本脚本只清理 0 用量的多余/陈旧行。
    """
    def _is_zero(value) -> bool:
        if value is None:
            return True
        try:
            return float(value) == 0
        except (TypeError, ValueError):
            return False

    return _is_zero(item.unit_usage) and _is_zero(item.total_usage)


def _identity_key(material_id, material_model, material_specification, color, craft_name):
    return (
        material_id,
        _norm(material_model),
        _norm(material_specification),
        _norm(color),
        _norm(craft_name),
    )


def _expected_keys_for_order_shoe_type(order_shoe_type_id):
    """返回该鞋型当前二次BOM行的标识 Counter；若二次BOM未下发则返回空。"""
    expected = defaultdict(int)

    second_boms = (
        db.session.query(Bom)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 1)
        .all()
    )
    for bom in second_boms:
        if _norm(bom.bom_status) != SECOND_BOM_ISSUED_STATUS:
            # 未下发：本不该有下发快照行
            continue
        bom_items = (
            db.session.query(BomItem).filter(BomItem.bom_id == bom.bom_id).all()
        )
        for bi in bom_items:
            key = _identity_key(
                bi.material_id,
                bi.material_model,
                bi.material_specification,
                bi.bom_item_color,
                bi.craft_name,
            )
            expected[key] += 1
    return expected


def _is_second_bom_issued(order_shoe_type_id) -> bool:
    """该鞋型的二次BOM是否已下发（bom_status='3'）。"""
    second_boms = (
        db.session.query(Bom)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 1)
        .all()
    )
    return any(_norm(b.bom_status) == SECOND_BOM_ISSUED_STATUS for b in second_boms)


def _plan_craft_sheet(craft_sheet):
    """返回 (to_delete_items, kept_count)：该工艺单需删除的重复/陈旧行列表。

    按鞋型分别判断二次BOM是否已下发：
    - 已下发：工艺单应只保留与二次BOM一一对应的 ``after_usage_symbol=1`` 快照行；
      多余/孤立的快照行删除，残留的 ``after_usage_symbol=0`` 下发前行（0 用量重复）
      也应全部删除。
    - 未下发：``after_usage_symbol=1`` 快照行是旧下发残留，应删除；保留当前的
      ``after_usage_symbol=0`` 下发前行。
    """
    snapshot_items = (
        db.session.query(CraftSheetItem)
        .filter(
            CraftSheetItem.craft_sheet_id == craft_sheet.craft_sheet_id,
            CraftSheetItem.after_usage_symbol == 1,
        )
        # 最新的优先保留（含再次下发后修正的用量）
        .order_by(CraftSheetItem.craft_sheet_item_id.desc())
        .all()
    )
    pre_items = (
        db.session.query(CraftSheetItem)
        .filter(
            CraftSheetItem.craft_sheet_id == craft_sheet.craft_sheet_id,
            CraftSheetItem.after_usage_symbol == 0,
        )
        .all()
    )

    # 按鞋型分组
    snapshot_by_ost = defaultdict(list)
    for item in snapshot_items:
        snapshot_by_ost[item.order_shoe_type_id].append(item)
    pre_by_ost = defaultdict(list)
    for item in pre_items:
        pre_by_ost[item.order_shoe_type_id].append(item)

    to_delete = []
    kept = 0
    for order_shoe_type_id in set(snapshot_by_ost) | set(pre_by_ost):
        snaps = snapshot_by_ost.get(order_shoe_type_id, [])
        pres = pre_by_ost.get(order_shoe_type_id, [])

        if _is_second_bom_issued(order_shoe_type_id):
            # 已下发：保留与二次BOM对应的快照行
            remaining = _expected_keys_for_order_shoe_type(order_shoe_type_id)
            # snaps 已按 id 降序：最新的先认领对应的二次BOM行
            for item in snaps:
                key = _identity_key(
                    item.material_id,
                    item.material_model,
                    item.material_specification,
                    item.color,
                    item.craft_name,
                )
                if remaining.get(key, 0) > 0:
                    remaining[key] -= 1
                    kept += 1
                else:
                    to_delete.append(item)
            # 残留的下发前行（0 用量重复）全部删除
            to_delete.extend(pres)
        else:
            # 未下发：快照行是旧下发残留，删除；保留当前下发前行
            to_delete.extend(snaps)
            kept += len(pres)

    # 用户规则：以投产指令单为准，但用量非为 0 的材料一律不删除。
    # 这里统一过滤——只删除 0 用量行，任何带真实用量的行都保留。
    protected = [item for item in to_delete if not _is_zero_usage(item)]
    to_delete = [item for item in to_delete if _is_zero_usage(item)]
    kept += len(protected)
    return to_delete, kept


def _pi_craft_targets(order_shoe_id):
    """收集投产指令单中「显式指定了工艺名」的材料，作为工艺名权威来源。

    返回:
        by_identity: {order_shoe_type_id: {(material_id, model, spec, color): pre_craft_name}}
                     —— 供工艺单 ``after_usage_symbol=1`` 行按材料标识匹配（其不带 piid）。
        by_piid:     {production_instruction_item_id: pre_craft_name}
                     —— 供二次BOM行按 production_instruction_item_id 精确匹配。

    只收集 ``pre_craft_name`` 非空的项：投产指令单留空工艺（如普通材料、被拆成多条
    明细工艺的面料）不应覆盖 BOM/工艺单中更细的工艺名，避免误改。烫底这类由投产指令单
    明确指定工艺的材料才会被纳入。
    """
    pis = (
        db.session.query(ProductionInstruction)
        .filter(ProductionInstruction.order_shoe_id == order_shoe_id)
        .all()
    )
    pi_ids = [p.production_instruction_id for p in pis]
    by_identity = defaultdict(dict)
    by_piid = {}
    if not pi_ids:
        return by_identity, by_piid

    items = (
        db.session.query(ProductionInstructionItem)
        .filter(ProductionInstructionItem.production_instruction_id.in_(pi_ids))
        .all()
    )
    for it in items:
        if not _norm(it.pre_craft_name):
            continue
        ident = (
            it.material_id,
            _norm(it.material_model),
            _norm(it.material_specification),
            _norm(it.color),
        )
        by_identity[it.order_shoe_type_id][ident] = it.pre_craft_name
        by_piid[it.production_instruction_item_id] = it.pre_craft_name
    return by_identity, by_piid


def _plan_craft_name_syncs(craft_sheet):
    """规划「工艺名以投产指令单为准」的更新（只改工艺名，不删行、不动用量）。

    返回 update 列表，元素为 dict：{kind, obj, old, new, desc}。
    - 工艺单：匹配 ``after_usage_symbol=1`` 行（按材料标识，要求该标识唯一，避免误改
      被拆成多条的面料工艺）。
    - 二次BOM：按 ``production_instruction_item_id`` 匹配（要求该 piid 唯一对应一行）。
    """
    order_shoe_id = craft_sheet.order_shoe_id
    by_identity, by_piid = _pi_craft_targets(order_shoe_id)
    updates = []
    if not by_identity and not by_piid:
        return updates

    # —— 工艺单 after_usage_symbol=1 行 ——
    snaps = (
        db.session.query(CraftSheetItem)
        .filter(
            CraftSheetItem.craft_sheet_id == craft_sheet.craft_sheet_id,
            CraftSheetItem.after_usage_symbol == 1,
        )
        .all()
    )
    snap_groups = defaultdict(list)
    for it in snaps:
        ident = (
            it.material_id,
            _norm(it.material_model),
            _norm(it.material_specification),
            _norm(it.color),
        )
        snap_groups[(it.order_shoe_type_id, ident)].append(it)
    for ost_id, idents in by_identity.items():
        for ident, craft in idents.items():
            rows = snap_groups.get((ost_id, ident), [])
            if len(rows) == 1 and _norm(rows[0].craft_name) != _norm(craft):
                updates.append(
                    {
                        "kind": "craft_sheet_item",
                        "obj": rows[0],
                        "id": rows[0].craft_sheet_item_id,
                        "old": rows[0].craft_name,
                        "new": craft,
                        "desc": f"ost={rows[0].order_shoe_type_id} mid={rows[0].material_id} model={rows[0].material_model!r}",
                    }
                )

    # —— 二次BOM 行 ——
    bom_items = (
        db.session.query(BomItem)
        .join(Bom, BomItem.bom_id == Bom.bom_id)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(OrderShoeType.order_shoe_id == order_shoe_id, Bom.bom_type == 1)
        .all()
    )
    bom_by_piid = defaultdict(list)
    for bi in bom_items:
        if bi.production_instruction_item_id is not None:
            bom_by_piid[bi.production_instruction_item_id].append(bi)
    for piid, craft in by_piid.items():
        rows = bom_by_piid.get(piid, [])
        if len(rows) == 1 and _norm(rows[0].craft_name) != _norm(craft):
            updates.append(
                {
                    "kind": "bom_item",
                    "obj": rows[0],
                    "id": rows[0].bom_item_id,
                    "old": rows[0].craft_name,
                    "new": craft,
                    "desc": f"bom_id={rows[0].bom_id} mid={rows[0].material_id} model={rows[0].material_model!r}",
                }
            )
    return updates


def _craft_sheet_query(order_rids):
    """返回 (CraftSheet, Order, Shoe) 列表，可按订单 RID 过滤。"""
    query = (
        db.session.query(CraftSheet, Order, Shoe)
        .join(OrderShoe, CraftSheet.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
    )
    if order_rids:
        query = query.filter(Order.order_rid.in_(order_rids))
    return query.all()


def run(order_rids, apply_changes):
    rows = _craft_sheet_query(order_rids)
    print(f"扫描工艺单数量：{len(rows)}")

    affected_count = 0
    total_delete = 0
    total_update = 0

    for craft_sheet, order, shoe in rows:
        to_delete, kept = _plan_craft_sheet(craft_sheet)
        craft_updates = _plan_craft_name_syncs(craft_sheet)
        if not to_delete and not craft_updates:
            continue

        affected_count += 1
        total_delete += len(to_delete)
        total_update += len(craft_updates)
        print(
            f"\n[受影响] 订单 {order.order_rid} / 鞋型 {shoe.shoe_rid} "
            f"craft_sheet_id={craft_sheet.craft_sheet_id} "
            f"保留下发快照行 {kept} 条，删除重复/陈旧 {len(to_delete)} 条，"
            f"工艺名以投产指令单为准更新 {len(craft_updates)} 条："
        )
        for item in to_delete:
            print(
                f"    - [删除] id={item.craft_sheet_item_id} ost={item.order_shoe_type_id} "
                f"sym={item.after_usage_symbol} "
                f"material_id={item.material_id} model={_norm(item.material_model)!r} "
                f"spec={_norm(item.material_specification)!r} color={_norm(item.color)!r} "
                f"craft={_norm(item.craft_name)!r} total_usage={item.total_usage}"
            )
            if apply_changes:
                db.session.delete(item)
        for upd in craft_updates:
            print(
                f"    - [改工艺] {upd['kind']} id={upd['id']} {upd['desc']} "
                f"工艺名 {_norm(upd['old'])!r} -> {_norm(upd['new'])!r}"
            )
            if apply_changes:
                upd["obj"].craft_name = upd["new"]

    print(
        f"\n汇总：受影响工艺单 {affected_count} 张，"
        f"计划删除重复下发快照行 {total_delete} 条，"
        f"计划更新工艺名 {total_update} 条。"
    )

    if not apply_changes:
        print("当前为预演模式（dry-run），未修改数据库。确认无误后加 --apply 执行。")
        return

    if total_delete == 0 and total_update == 0:
        print("无需修改。")
        return

    db.session.commit()
    print("已提交修改。")


def main():
    parser = argparse.ArgumentParser(
        description="批量修复工艺单下发快照重复（二次用量退回再下发导致材料翻倍）"
    )
    parser.add_argument(
        "--orders",
        default="",
        help="仅处理指定订单 RID，逗号分隔；留空表示全部订单。",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际执行删除并提交。不加该参数时为预演（dry-run）。",
    )
    args = parser.parse_args()

    order_rids = [r.strip() for r in args.orders.split(",") if r.strip()]

    # 直接使用 config.py 中的 ProductionConfig（连接生产数据库）
    app = create_app(ProductionConfig)
    with app.app_context():
        try:
            run(order_rids, args.apply)
        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    sys.exit(main())
