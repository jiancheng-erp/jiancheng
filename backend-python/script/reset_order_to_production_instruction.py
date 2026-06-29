"""
把一张订单整体重置回「投产指令单」阶段，从头重做，同时**保留已入库记录**。

适用场景
--------
某订单已推进到入库阶段、并已入库部分材料，但发现**整单材料都有问题**，需要从
投产指令单开始重做。此时：
- 系统 UI 的「退回」流程只在 [0,4,6/7,9,11,13] 这些阶段可用（见
  ``shared_apis/revert_order.py`` 的 FLOW 列表），订单到了入库阶段已超出范围，
  无法用 UI 退回；
- 「重新编辑投产指令单」流程在整单材料都换掉时，会删除全部采购明细，导致已入库的
  ``material_storage`` 失去关联（孤儿）。

本脚本绕过上述限制，安全地把订单 order_shoe 重置回投产指令单初始状态：
1. **断链**：把本单 ``material_storage.purchase_order_item_id`` 置空（实物库存、入库
   历史、应付账款都不动，只断开对即将删除的采购明细的引用）；
2. **删除文档链**（仅本单 order_shoe / order_shoe_type 范围）：投产指令单、一/二次
   BOM、总BOM、工艺单、采购单/分单/明细、物资采购明细；
3. **重置状态**：把 ``order_shoe_status`` 重置为初始的 (current_status=0,
   current_status_value=0, revert_info=NULL)，并把 order_shoe 的上传状态位清零。

之后操作
--------
重置完成后，开发部按**正常**「上传投产指令单」流程从头重做即可（此时
``current_status==0``，系统会新建一份全新的投产指令单）。已入库的实物仍在仓库中、
按 (spu_material_id, order_shoe_id) 关联本订单鞋型，可继续用于本单生产。

**绝不触碰（保留）**：
- ``material_storage`` 的库存数量、``material_storage_size_detail``
- ``inbound_record`` / ``inbound_record_detail``（入库历史）
- ``outbound_record``（出库历史）
- 应付账款 / 会计记录
- ``total_purchase_order``（跨订单汇总，仅删除本单的分采购单）

安全
----
默认 **dry-run**，只打印将要断链/删除/重置的内容，不改数据库。确认无误后，必须同时
加 ``--apply`` 和 ``--confirm <订单号>``（且与 --order 一致）才真正提交。
**强烈建议执行前先备份数据库。**

用法（在 backend-python 目录下）::

    python script/reset_order_to_production_instruction.py --order K26-0317
    python script/reset_order_to_production_instruction.py --order K26-0317 --apply --confirm K26-0317
"""

import argparse
import os
import sys
from collections import defaultdict

# 允许从 backend-python 目录直接运行：把项目根目录加入模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 在导入 config / app 之前加载 .env
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from config import ProductionConfig
from models import (
    Order,
    OrderShoe,
    OrderShoeStatus,
    OrderShoeType,
    Shoe,
    ProductionInstruction,
    ProductionInstructionItem,
    Bom,
    BomItem,
    TotalBom,
    CraftSheet,
    CraftSheetItem,
    PurchaseOrder,
    PurchaseDivideOrder,
    PurchaseOrderItem,
    AssetsPurchaseOrderItem,
    MaterialStorage,
)


def _gather(order_rid):
    """收集本订单需要处理的所有实体 id 与对象，返回上下文 dict。"""
    order = db.session.query(Order).filter(Order.order_rid == order_rid).first()
    if not order:
        return None

    order_id = order.order_id

    order_shoes = (
        db.session.query(OrderShoe).filter(OrderShoe.order_id == order_id).all()
    )
    order_shoe_ids = [os_.order_shoe_id for os_ in order_shoes]

    order_shoe_types = (
        db.session.query(OrderShoeType)
        .filter(OrderShoeType.order_shoe_id.in_(order_shoe_ids))
        .all()
        if order_shoe_ids
        else []
    )
    order_shoe_type_ids = [ost.order_shoe_type_id for ost in order_shoe_types]

    # ── 采购链 ────────────────────────────────────────────────────────────
    purchase_orders = (
        db.session.query(PurchaseOrder)
        .filter(PurchaseOrder.order_id == order_id)
        .all()
    )
    purchase_order_ids = [po.purchase_order_id for po in purchase_orders]

    divide_orders = (
        db.session.query(PurchaseDivideOrder)
        .filter(PurchaseDivideOrder.purchase_order_id.in_(purchase_order_ids))
        .all()
        if purchase_order_ids
        else []
    )
    divide_order_ids = [d.purchase_divide_order_id for d in divide_orders]

    purchase_order_items = (
        db.session.query(PurchaseOrderItem)
        .filter(PurchaseOrderItem.purchase_divide_order_id.in_(divide_order_ids))
        .all()
        if divide_order_ids
        else []
    )
    purchase_order_item_ids = [
        p.purchase_order_item_id for p in purchase_order_items
    ]

    assets_items = (
        db.session.query(AssetsPurchaseOrderItem)
        .filter(
            AssetsPurchaseOrderItem.purchase_divide_order_id.in_(divide_order_ids)
        )
        .all()
        if divide_order_ids
        else []
    )

    # ── BOM / 工艺单 / 投产指令单 ─────────────────────────────────────────
    boms = (
        db.session.query(Bom)
        .filter(Bom.order_shoe_type_id.in_(order_shoe_type_ids))
        .all()
        if order_shoe_type_ids
        else []
    )
    bom_ids = [b.bom_id for b in boms]
    bom_items = (
        db.session.query(BomItem).filter(BomItem.bom_id.in_(bom_ids)).all()
        if bom_ids
        else []
    )

    total_boms = (
        db.session.query(TotalBom)
        .filter(TotalBom.order_shoe_id.in_(order_shoe_ids))
        .all()
        if order_shoe_ids
        else []
    )

    craft_sheets = (
        db.session.query(CraftSheet)
        .filter(CraftSheet.order_shoe_id.in_(order_shoe_ids))
        .all()
        if order_shoe_ids
        else []
    )
    craft_sheet_ids = [c.craft_sheet_id for c in craft_sheets]
    craft_sheet_items = (
        db.session.query(CraftSheetItem)
        .filter(CraftSheetItem.craft_sheet_id.in_(craft_sheet_ids))
        .all()
        if craft_sheet_ids
        else []
    )

    production_instructions = (
        db.session.query(ProductionInstruction)
        .filter(ProductionInstruction.order_shoe_id.in_(order_shoe_ids))
        .all()
        if order_shoe_ids
        else []
    )
    pi_ids = [pi.production_instruction_id for pi in production_instructions]
    pi_items = (
        db.session.query(ProductionInstructionItem)
        .filter(ProductionInstructionItem.production_instruction_id.in_(pi_ids))
        .all()
        if pi_ids
        else []
    )

    # ── 待断链的库存（已入库、且引用了本单采购明细）──────────────────────
    po_item_id_set = set(purchase_order_item_ids)
    storages = (
        db.session.query(MaterialStorage)
        .filter(MaterialStorage.order_shoe_id.in_(order_shoe_ids))
        .all()
        if order_shoe_ids
        else []
    )
    storages_to_detach = [
        s
        for s in storages
        if s.purchase_order_item_id is not None
        and s.purchase_order_item_id in po_item_id_set
    ]
    # 引用了「本单之外」采购明细的库存（异常情况，单独提示，不处理）
    storages_foreign_link = [
        s
        for s in storages
        if s.purchase_order_item_id is not None
        and s.purchase_order_item_id not in po_item_id_set
    ]

    # ── 状态 ──────────────────────────────────────────────────────────────
    statuses = (
        db.session.query(OrderShoeStatus)
        .filter(OrderShoeStatus.order_shoe_id.in_(order_shoe_ids))
        .all()
        if order_shoe_ids
        else []
    )

    return {
        "order": order,
        "order_shoes": order_shoes,
        "order_shoe_ids": order_shoe_ids,
        "order_shoe_types": order_shoe_types,
        "order_shoe_type_ids": order_shoe_type_ids,
        "purchase_orders": purchase_orders,
        "divide_orders": divide_orders,
        "purchase_order_items": purchase_order_items,
        "assets_items": assets_items,
        "boms": boms,
        "bom_items": bom_items,
        "total_boms": total_boms,
        "craft_sheets": craft_sheets,
        "craft_sheet_items": craft_sheet_items,
        "production_instructions": production_instructions,
        "pi_items": pi_items,
        "storages": storages,
        "storages_to_detach": storages_to_detach,
        "storages_foreign_link": storages_foreign_link,
        "statuses": statuses,
    }


def _report(ctx, order_rid):
    order = ctx["order"]
    print(f"订单 {order_rid}（order_id={order.order_id}）重置预览\n")

    # 鞋型
    shoe_rid_map = {
        s.shoe_id: s.shoe_rid
        for s in db.session.query(Shoe)
        .filter(Shoe.shoe_id.in_([os_.shoe_id for os_ in ctx["order_shoes"]]))
        .all()
    }
    print(f"order_shoe 数: {len(ctx['order_shoes'])}")
    for os_ in ctx["order_shoes"]:
        print(
            f"  - order_shoe_id={os_.order_shoe_id} 鞋型={shoe_rid_map.get(os_.shoe_id, '?')}"
        )
    print(f"order_shoe_type 数: {len(ctx['order_shoe_types'])}\n")

    print("将要【删除】的文档链：")
    print(f"  投产指令单 ProductionInstruction : {len(ctx['production_instructions'])}")
    print(f"    └ 明细 ProductionInstructionItem: {len(ctx['pi_items'])}")
    print(f"  BOM（一/二次）Bom               : {len(ctx['boms'])}")
    print(f"    └ 明细 BomItem                 : {len(ctx['bom_items'])}")
    print(f"  总BOM TotalBom                  : {len(ctx['total_boms'])}")
    print(f"  工艺单 CraftSheet               : {len(ctx['craft_sheets'])}")
    print(f"    └ 明细 CraftSheetItem          : {len(ctx['craft_sheet_items'])}")
    print(f"  采购单 PurchaseOrder            : {len(ctx['purchase_orders'])}")
    print(f"    └ 分采购单 PurchaseDivideOrder : {len(ctx['divide_orders'])}")
    print(f"    └ 采购明细 PurchaseOrderItem   : {len(ctx['purchase_order_items'])}")
    print(f"    └ 物资采购明细 AssetsItem      : {len(ctx['assets_items'])}\n")

    print("将要【断链】的已入库库存（仅置空 purchase_order_item_id，数量保留）：")
    if not ctx["storages_to_detach"]:
        print("  （无）")
    for s in ctx["storages_to_detach"]:
        print(
            f"  - material_storage_id={s.material_storage_id} "
            f"spu_material_id={s.spu_material_id} "
            f"已入库={s.inbound_amount} 现存={s.current_amount} "
            f"原 purchase_order_item_id={s.purchase_order_item_id}"
        )
    print()

    if ctx["storages_foreign_link"]:
        print("⚠ 以下库存引用了【本单之外】的采购明细，脚本不会处理，请人工确认：")
        for s in ctx["storages_foreign_link"]:
            print(
                f"  - material_storage_id={s.material_storage_id} "
                f"purchase_order_item_id={s.purchase_order_item_id}"
            )
        print()

    print("将要【重置】的状态：")
    print(f"  order_shoe_status 行数: {len(ctx['statuses'])} → 每个 order_shoe 重置为一行 (current_status=0, current_status_value=0, revert_info=NULL)")
    for st in ctx["statuses"]:
        print(
            f"  - order_shoe_status_id={st.order_shoe_status_id} "
            f"order_shoe_id={st.order_shoe_id} "
            f"当前 current_status={st.current_status}, value={st.current_status_value}"
        )
    print()

    print("将要【保留】（绝不修改）：material_storage 数量明细、inbound_record(_detail) 入库历史、")
    print("出库历史、应付账款/会计记录、total_purchase_order 汇总单。")


def _apply(ctx):
    """执行断链 / 删除 / 重置。调用方负责 commit。"""
    # 1) 断链：置空已入库库存对采购明细的引用（保留库存数量）
    detached = 0
    for s in ctx["storages_to_detach"]:
        s.purchase_order_item_id = None
        detached += 1

    # 2) 删除文档链（子表先删）
    def _del_all(objs):
        n = 0
        for o in objs:
            db.session.delete(o)
            n += 1
        return n

    counts = {}
    counts["purchase_order_item"] = _del_all(ctx["purchase_order_items"])
    counts["assets_purchase_order_item"] = _del_all(ctx["assets_items"])
    counts["purchase_divide_order"] = _del_all(ctx["divide_orders"])
    counts["purchase_order"] = _del_all(ctx["purchase_orders"])
    counts["craft_sheet_item"] = _del_all(ctx["craft_sheet_items"])
    counts["craft_sheet"] = _del_all(ctx["craft_sheets"])
    counts["bom_item"] = _del_all(ctx["bom_items"])
    counts["bom"] = _del_all(ctx["boms"])
    counts["total_bom"] = _del_all(ctx["total_boms"])
    counts["production_instruction_item"] = _del_all(ctx["pi_items"])
    counts["production_instruction"] = _del_all(ctx["production_instructions"])
    db.session.flush()

    # 3) 重置状态：删除旧状态行，按 order_shoe 重建初始单行 (0, 0)
    _del_all(ctx["statuses"])
    db.session.flush()
    for os_ in ctx["order_shoes"]:
        db.session.add(
            OrderShoeStatus(
                order_shoe_id=os_.order_shoe_id,
                current_status=0,
                current_status_value=0,
                revert_info=None,
            )
        )
        # 清零上传状态位，回到初始
        os_.production_order_upload_status = "0"
        os_.process_sheet_upload_status = "0"
    db.session.flush()

    return detached, counts


def main():
    parser = argparse.ArgumentParser(
        description="把订单重置回投产指令单阶段（保留已入库记录）。默认 dry-run。"
    )
    parser.add_argument("--order", required=True, help="订单号，如 K26-0317")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际执行（默认仅预演）。必须同时提供 --confirm。",
    )
    parser.add_argument(
        "--confirm",
        default="",
        help="二次确认：必须与 --order 完全一致才会执行。",
    )
    args = parser.parse_args()

    app = create_app(ProductionConfig)
    with app.app_context():
        ctx = _gather(args.order)
        if ctx is None:
            print(f"未找到订单：{args.order}")
            return

        _report(ctx, args.order)

        if not args.apply:
            print("\n[DRY-RUN] 未做任何修改。确认无误后执行：")
            print(
                f"  python script/reset_order_to_production_instruction.py "
                f"--order {args.order} --apply --confirm {args.order}"
            )
            print("⚠ 执行前请先备份数据库。")
            return

        if args.confirm != args.order:
            print(
                f"\n[已取消] --confirm（{args.confirm!r}）与 --order（{args.order!r}）不一致，"
                "为安全起见未执行任何修改。"
            )
            return

        try:
            detached, counts = _apply(ctx)
            db.session.commit()
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            print(f"\n[失败] 已回滚，未改动数据库：{exc}")
            raise

        print("\n[已执行并提交]")
        print(f"  断链库存: {detached} 条")
        for k, v in counts.items():
            print(f"  删除 {k}: {v}")
        print("  状态已重置为投产指令单阶段 (current_status=0, value=0)")
        print("\n下一步：开发部按正常「上传投产指令单」流程从头重做本单。")


if __name__ == "__main__":
    main()
