"""
修复历史二次采购订单中「厂家未合并」的分采购订单。

背景
----
二次采购订单按「厂家」拆分为分采购订单（purchase_divide_order），一个厂家在同一张
采购订单下应只对应一张分采购订单，其编号规则为
``父采购单RID + 厂家ID(4位补零)``（见 ``save_purchase``）。

早期「编辑时更改厂家」的逻辑只改了采购项的 inbound 材料，却没有把采购项迁移到对应
厂家的分采购订单，导致：
- 采购项停留在原厂家的分采购订单里（厂家不匹配）；
- 同一厂家的采购项分散在多张分采购订单里（未合并）。

本脚本按每张二次采购订单，把采购项按其真实厂家（inbound_material_id → material →
material_supplier）重新归并到符合命名规则的分采购订单中；不存在则新建，原分采购订单
若因迁出而变空则删除。

安全
----
默认 **dry-run**，只打印将要迁移/新建/删除的内容，不改数据库。确认无误后，必须同时
加 ``--apply`` 和 ``--confirm YES`` 才真正提交。
默认只处理 **已保存(状态=1)** 的二次采购订单（仍可编辑、尚未下发）；如需处理全部状态，
加 ``--all-status``。可用 ``--order <采购单RID>`` 只处理单张订单。
**强烈建议执行前先备份数据库。**

用法（在 backend-python 目录下）::

    python script/fix_unmerged_second_purchase_divide_orders.py
    python script/fix_unmerged_second_purchase_divide_orders.py --order 0120260804...S
    python script/fix_unmerged_second_purchase_divide_orders.py --apply --confirm YES
"""

import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from config import ProductionConfig
from models import (
    Material,
    PurchaseOrder,
    PurchaseDivideOrder,
    PurchaseOrderItem,
    Supplier,
)

SECOND_PO_TYPE = "S"
SAVED_STATUS = "1"


def _supplier_of(material_id, material_supplier_cache):
    """返回材料对应厂家ID；带缓存。"""
    if material_id is None:
        return None
    if material_id in material_supplier_cache:
        return material_supplier_cache[material_id]
    mat = (
        db.session.query(Material)
        .filter(Material.material_id == material_id)
        .first()
    )
    supplier_id = mat.material_supplier if mat else None
    material_supplier_cache[material_id] = supplier_id
    return supplier_id


def _plan_for_purchase_order(po, material_supplier_cache, supplier_name_cache):
    """为单张采购订单计算归并方案。

    返回 dict：
      moves:   [(item, from_rid, to_rid, supplier_id)]
      creates: [to_rid]                       需要新建的分采购订单编号
      deletes: [rid]                          迁空后需删除的分采购订单编号
    不修改数据库。
    """
    divide_orders = (
        db.session.query(PurchaseDivideOrder)
        .filter(PurchaseDivideOrder.purchase_order_id == po.purchase_order_id)
        .all()
    )
    divide_by_id = {d.purchase_divide_order_id: d for d in divide_orders}
    rid_to_divide = {d.purchase_divide_order_rid: d for d in divide_orders}

    items = (
        db.session.query(PurchaseOrderItem)
        .filter(
            PurchaseOrderItem.purchase_divide_order_id.in_(list(divide_by_id.keys()))
        )
        .all()
        if divide_by_id
        else []
    )

    # 迁移后每张分采购订单剩余采购项数（用于判断是否变空）
    remaining_count = defaultdict(int)
    for it in items:
        remaining_count[it.purchase_divide_order_id] += 1

    moves = []
    creates = []
    planned_rids = set(rid_to_divide.keys())

    for it in items:
        resolved_material_id = it.inbound_material_id or it.material_id
        supplier_id = _supplier_of(resolved_material_id, material_supplier_cache)
        if supplier_id is None:
            continue
        target_rid = po.purchase_order_rid + str(supplier_id).zfill(4)
        current_divide = divide_by_id.get(it.purchase_divide_order_id)
        current_rid = current_divide.purchase_divide_order_rid if current_divide else None
        if current_rid == target_rid:
            continue

        if target_rid not in planned_rids:
            creates.append(target_rid)
            planned_rids.add(target_rid)
        moves.append((it, current_rid, target_rid, supplier_id))
        # 更新剩余计数：从原分单迁出
        if it.purchase_divide_order_id in remaining_count:
            remaining_count[it.purchase_divide_order_id] -= 1

    deletes = [
        divide_by_id[did].purchase_divide_order_rid
        for did, cnt in remaining_count.items()
        if cnt == 0
    ]

    # 供应商名称缓存（仅用于报告可读性）
    for _, _, _, sid in moves:
        if sid not in supplier_name_cache:
            sup = (
                db.session.query(Supplier)
                .filter(Supplier.supplier_id == sid)
                .first()
            )
            supplier_name_cache[sid] = sup.supplier_name if sup else str(sid)

    return {"moves": moves, "creates": creates, "deletes": deletes}


def _apply_plan(po, plan, divide_defaults):
    """执行归并方案；调用方负责 commit。"""
    # 现有分采购订单编号 → 对象
    rid_to_divide = {
        d.purchase_divide_order_rid: d
        for d in db.session.query(PurchaseDivideOrder).filter(
            PurchaseDivideOrder.purchase_order_id == po.purchase_order_id
        )
    }
    # 先新建需要的分采购订单
    for rid in plan["creates"]:
        if rid in rid_to_divide:
            continue
        new_divide = PurchaseDivideOrder(
            purchase_divide_order_rid=rid,
            purchase_order_id=po.purchase_order_id,
            purchase_divide_order_type=divide_defaults["type"],
            purchase_order_remark=divide_defaults["remark"],
            purchase_order_environmental_request=divide_defaults["env"],
            shipment_address=divide_defaults["address"],
            shipment_deadline=divide_defaults["deadline"],
            total_purchase_order_id=divide_defaults["total_po_id"],
        )
        db.session.add(new_divide)
        db.session.flush()
        rid_to_divide[rid] = new_divide

    # 迁移采购项
    for item, _from_rid, to_rid, _sid in plan["moves"]:
        item.purchase_divide_order_id = rid_to_divide[to_rid].purchase_divide_order_id
    db.session.flush()

    # 删除迁空的分采购订单
    for rid in plan["deletes"]:
        divide = (
            db.session.query(PurchaseDivideOrder)
            .filter(
                PurchaseDivideOrder.purchase_order_id == po.purchase_order_id,
                PurchaseDivideOrder.purchase_divide_order_rid == rid,
            )
            .first()
        )
        if not divide:
            continue
        still_has = (
            db.session.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.purchase_divide_order_id
                == divide.purchase_divide_order_id
            )
            .count()
        )
        if still_has == 0:
            db.session.delete(divide)
    db.session.flush()


def _divide_defaults(po):
    """新建分采购订单时沿用同订单下已有分单的默认信息。"""
    sample = (
        db.session.query(PurchaseDivideOrder)
        .filter(PurchaseDivideOrder.purchase_order_id == po.purchase_order_id)
        .first()
    )
    return {
        "type": sample.purchase_divide_order_type if sample else "N",
        "remark": sample.purchase_order_remark if sample else "",
        "env": sample.purchase_order_environmental_request if sample else "",
        "address": sample.shipment_address if sample else "",
        "deadline": sample.shipment_deadline if sample else "",
        "total_po_id": sample.total_purchase_order_id if sample else None,
    }


def main():
    parser = argparse.ArgumentParser(
        description="修复二次采购订单中厂家未合并的分采购订单。默认 dry-run。"
    )
    parser.add_argument("--order", default="", help="只处理指定采购单RID")
    parser.add_argument(
        "--all-status",
        action="store_true",
        help="处理全部状态（默认仅处理已保存/状态=1 的订单）",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际执行（默认仅预演）。必须同时提供 --confirm YES。",
    )
    parser.add_argument("--confirm", default="", help="二次确认：需为 YES 才会执行。")
    args = parser.parse_args()

    app = create_app(ProductionConfig)
    with app.app_context():
        query = db.session.query(PurchaseOrder).filter(
            PurchaseOrder.purchase_order_type == SECOND_PO_TYPE
        )
        if args.order:
            query = query.filter(PurchaseOrder.purchase_order_rid == args.order)
        if not args.all_status:
            query = query.filter(PurchaseOrder.purchase_order_status == SAVED_STATUS)
        purchase_orders = query.all()

        material_supplier_cache = {}
        supplier_name_cache = {}

        total_moves = total_creates = total_deletes = 0
        affected_orders = 0

        for po in purchase_orders:
            plan = _plan_for_purchase_order(
                po, material_supplier_cache, supplier_name_cache
            )
            if not plan["moves"] and not plan["creates"] and not plan["deletes"]:
                continue

            affected_orders += 1
            total_moves += len(plan["moves"])
            total_creates += len(plan["creates"])
            total_deletes += len(plan["deletes"])

            print(f"\n采购单 {po.purchase_order_rid} (状态={po.purchase_order_status})：")
            for rid in plan["creates"]:
                print(f"  [新建分采购订单] {rid}")
            for item, from_rid, to_rid, sid in plan["moves"]:
                sup_name = supplier_name_cache.get(sid, sid)
                print(
                    f"  [迁移] 采购项 {item.purchase_order_item_id} "
                    f"({from_rid} → {to_rid})  厂家={sup_name}"
                )
            for rid in plan["deletes"]:
                print(f"  [删除空分采购订单] {rid}")

            if args.apply and args.confirm == "YES":
                _apply_plan(po, plan, _divide_defaults(po))

        print(
            f"\n汇总：受影响采购单 {affected_orders} 张，"
            f"迁移采购项 {total_moves} 条，新建分单 {total_creates} 张，"
            f"删除空分单 {total_deletes} 张。"
        )

        if not args.apply:
            print("\n[DRY-RUN] 未做任何修改。确认无误后执行：")
            print(
                "  python script/fix_unmerged_second_purchase_divide_orders.py "
                "--apply --confirm YES"
            )
            print("⚠ 执行前请先备份数据库。")
            return

        if args.confirm != "YES":
            print("\n[已取消] --confirm 非 YES，为安全起见未执行任何修改。")
            return

        try:
            db.session.commit()
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            print(f"\n[失败] 已回滚，未改动数据库：{exc}")
            raise
        print("\n[已执行并提交]")


if __name__ == "__main__":
    main()
