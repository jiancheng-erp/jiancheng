"""
检测「货已全部出库、订单主状态却没推进到『订单完成』」的断链订单（只读）。

背景
----
系统里有两套并行的状态：
- **订单主状态** ``order_status.order_current_status`` —— 由事件流(EventProcessor)
  一步步推进，最终到 18「订单完成」。
- **生产/出库状态** —— 前端「生产状态」列，是根据排产信息(OrderShoeProductionInfo)
  与实际出库记录(ShoeOutboundRecordDetail) **动态计算** 出来的，与主状态无关。

正常流程下，成品全部入库完成会触发 operation [18,19,20,21] 把订单从
「生产流程(9)」推到「业务部确认(11)」；出库全部完成会触发 operation 22~35
把订单从 11 一路推到 18「订单完成」。
``processOrderEvent`` 要求「当前状态必须与 operation 目标状态严格对齐」，
一旦某一步没触发（分批入库、退回干预、直接出库绕过入库事件等），后续推进事件
会全部作废，订单主状态就会 **卡死在中间某个节点**，而右侧「生产状态」却已显示
「已全部出库」。

本脚本复刻前端「生产状态」的判定逻辑，找出：
    生产状态 = 已全部出库（实际出库量 >= 核定/预计量）
    但 order_current_status < 18（未到订单完成）
的订单，并给出卡在哪一步的诊断，便于人工修复。

本脚本为 **只读** 检测，不修改任何数据。可选 ``--csv`` 导出结果。

用法（在 backend-python 目录下）::

    python script/detect_stuck_finished_orders.py
    python script/detect_stuck_finished_orders.py --orders K26-0692,K26-0743
    python script/detect_stuck_finished_orders.py --csv stuck_orders.csv
    python script/detect_stuck_finished_orders.py --include-partial   # 连「部分出库」也一并列出
"""

import argparse
import csv
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
from api_utility import estimate_status_converter
from event_processor import ORDERSTATUSNAMELIST
from models import (
    Customer,
    FinishedShoeStorage,
    Order,
    OrderShoe,
    OrderShoeProductionInfo,
    OrderShoeType,
    OrderStatus,
    Shoe,
    ShoeOutboundRecordDetail,
)

# 订单完成对应的主状态 id（ORDERSTATUSNAMELIST[18] == "订单完成"）
ORDER_FINISHED_STATUS_ID = 18


def _status_name(status_id):
    if status_id is None:
        return "无"
    if 0 <= status_id < len(ORDERSTATUSNAMELIST):
        return ORDERSTATUSNAMELIST[status_id]
    return str(status_id)


def _diagnose(order_current_status):
    """根据卡住的主状态给出断链诊断。"""
    s = order_current_status
    if s is None:
        return "订单无主状态记录"
    if s < 9:
        return "尚未进入生产流程(9)，主状态明显滞后"
    if s == 9:
        return "停在『生产流程(9)』：成品入库完成事件(9→11)未触发"
    if s == 10:
        return "停在『生产结束确认(10)』：业务部确认(→11)未触发"
    if 11 <= s < ORDER_FINISHED_STATUS_ID:
        return f"已到『{_status_name(s)}({s})』：出库完成事件(22~35)未把订单推到订单完成"
    return "已是订单完成或之后"


def _shoe_production_status(pi, inbound_done, estimated, outbound):
    """复刻前端『生产状态』判定（忽略『出库审核中』的细分，不影响是否已全部出库）。"""
    if pi is None:
        return "未排产"
    estimated_status = estimate_status_converter(pi)
    if estimated_status != "生产已结束":
        return estimated_status
    if not inbound_done:
        return "成型"
    if outbound > 0 and estimated > 0 and outbound >= estimated:
        return "已全部出库"
    if outbound > 0:
        return f"部分出库(已出{outbound}/{estimated})"
    return "待成品出库"


def _collect(order_rids):
    """返回每个订单的聚合诊断信息 list[dict]。"""
    order_query = db.session.query(Order, OrderStatus, Customer).outerjoin(
        OrderStatus, OrderStatus.order_id == Order.order_id
    ).outerjoin(Customer, Customer.customer_id == Order.customer_id)
    if order_rids:
        order_query = order_query.filter(Order.order_rid.in_(order_rids))
    orders = order_query.all()
    if not orders:
        return []

    order_ids = [o.order_id for o, _, _ in orders]

    # order_shoe -> order_id，及 order_shoe -> shoe_rid
    shoe_rows = (
        db.session.query(OrderShoe.order_shoe_id, OrderShoe.order_id, Shoe.shoe_rid)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(OrderShoe.order_id.in_(order_ids))
        .all()
    )
    shoes_by_order = defaultdict(list)
    for os_id, o_id, shoe_rid in shoe_rows:
        shoes_by_order[o_id].append(os_id)
    all_shoe_ids = [row[0] for row in shoe_rows]
    if not all_shoe_ids:
        all_shoe_ids = [-1]

    # 生产信息
    prod_infos = {
        pi.order_shoe_id: pi
        for pi in db.session.query(OrderShoeProductionInfo).filter(
            OrderShoeProductionInfo.order_shoe_id.in_(all_shoe_ids)
        )
    }

    # 预计量（核定入库量） & 是否所有成品库存都已完成出库(finished_status==2) & 入库完成
    estimated_map = defaultdict(int)
    status2_map = defaultdict(lambda: {"total": 0, "status2": 0, "inbound_done": 0})
    fss_rows = (
        db.session.query(
            OrderShoe.order_shoe_id,
            FinishedShoeStorage.finished_estimated_amount,
            FinishedShoeStorage.finished_status,
        )
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .filter(OrderShoe.order_shoe_id.in_(all_shoe_ids))
        .all()
    )
    for os_id, est, fstatus in fss_rows:
        estimated_map[os_id] += int(est or 0)
        bucket = status2_map[os_id]
        bucket["total"] += 1
        if fstatus == 2:
            bucket["status2"] += 1
        if (fstatus or 0) >= 1:
            bucket["inbound_done"] += 1

    # 实际出库量
    outbound_map = defaultdict(int)
    ob_rows = (
        db.session.query(
            OrderShoe.order_shoe_id,
            db.func.coalesce(db.func.sum(ShoeOutboundRecordDetail.outbound_amount), 0),
        )
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .filter(OrderShoe.order_shoe_id.in_(all_shoe_ids))
        .group_by(OrderShoe.order_shoe_id)
        .all()
    )
    for os_id, total in ob_rows:
        outbound_map[os_id] = int(total or 0)

    results = []
    for order, order_status, customer in orders:
        os_ids = shoes_by_order.get(order.order_id, [])
        cur_status = order_status.order_current_status if order_status else None

        shoe_statuses = []
        total_estimated = 0
        total_outbound = 0
        total_storage = 0
        total_status2 = 0
        for os_id in os_ids:
            est = estimated_map.get(os_id, 0)
            ob = outbound_map.get(os_id, 0)
            bucket = status2_map.get(os_id, {"total": 0, "status2": 0, "inbound_done": 0})
            inbound_done = bucket["inbound_done"] > 0
            ps = _shoe_production_status(prod_infos.get(os_id), inbound_done, est, ob)
            shoe_statuses.append(ps)
            total_estimated += est
            total_outbound += ob
            total_storage += bucket["total"]
            total_status2 += bucket["status2"]

        has_shoe = len(shoe_statuses) > 0
        all_shipped = has_shoe and all(s == "已全部出库" for s in shoe_statuses)
        any_shipped = any(s == "已全部出库" for s in shoe_statuses)
        all_status2 = total_storage > 0 and total_status2 == total_storage

        results.append(
            {
                "order_rid": order.order_rid or "",
                "customer_name": customer.customer_name if customer else "",
                "order_current_status": cur_status,
                "order_current_status_name": _status_name(cur_status),
                "shoe_statuses": shoe_statuses,
                "all_shipped": all_shipped,
                "any_shipped": any_shipped,
                "all_storage_status2": all_status2,
                "storage_status2_ratio": f"{total_status2}/{total_storage}",
                "total_estimated": total_estimated,
                "total_outbound": total_outbound,
                "diagnosis": _diagnose(cur_status),
            }
        )
    return results


def _evaluate(rows, include_partial):
    """筛出断链订单：已全部出库(或含部分出库) 但 order_current_status < 18。"""
    flagged = []
    for r in rows:
        cur = r["order_current_status"]
        if cur is not None and cur >= ORDER_FINISHED_STATUS_ID:
            continue  # 已到订单完成，正常
        if r["all_shipped"]:
            r["flag_reason"] = "全部出库但未完成"
            flagged.append(r)
        elif include_partial and r["any_shipped"]:
            r["flag_reason"] = "部分鞋型已全部出库但未完成"
            flagged.append(r)
    # 越接近尾声(主状态越大)越可能是纯断链，排前面；同状态按出库量降序
    flagged.sort(
        key=lambda r: (
            -(r["order_current_status"] if r["order_current_status"] is not None else -1),
            -r["total_outbound"],
        )
    )
    return flagged


def _print_report(flagged, limit):
    if not flagged:
        print("未发现『已全部出库但订单未完成』的断链订单。")
        return

    print(f"共发现 {len(flagged)} 个疑似断链订单：\n")
    header = (
        f"{'订单号':<14} {'客户':<16} {'当前主状态':<18} "
        f"{'预计':>8} {'出库':>8} {'出库完成库存':>12}  诊断"
    )
    print(header)
    print("-" * len(header))
    shown = flagged if limit <= 0 else flagged[:limit]
    for r in shown:
        status_col = f"{r['order_current_status_name']}({r['order_current_status']})"
        print(
            f"{r['order_rid']:<14} {r['customer_name']:<16} {status_col:<18} "
            f"{r['total_estimated']:>8} {r['total_outbound']:>8} "
            f"{r['storage_status2_ratio']:>12}  {r['diagnosis']}"
        )
    if limit > 0 and len(flagged) > limit:
        print(f"\n… 仅显示前 {limit} 条，共 {len(flagged)} 条。使用 --limit 0 查看全部。")


def _export_csv(flagged, csv_path):
    fieldnames = [
        "order_rid",
        "customer_name",
        "order_current_status",
        "order_current_status_name",
        "flag_reason",
        "total_estimated",
        "total_outbound",
        "storage_status2_ratio",
        "all_storage_status2",
        "shoe_statuses",
        "diagnosis",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in flagged:
            writer.writerow(
                {
                    "order_rid": r["order_rid"],
                    "customer_name": r["customer_name"],
                    "order_current_status": r["order_current_status"],
                    "order_current_status_name": r["order_current_status_name"],
                    "flag_reason": r.get("flag_reason", ""),
                    "total_estimated": r["total_estimated"],
                    "total_outbound": r["total_outbound"],
                    "storage_status2_ratio": r["storage_status2_ratio"],
                    "all_storage_status2": r["all_storage_status2"],
                    "shoe_statuses": " / ".join(r["shoe_statuses"]),
                    "diagnosis": r["diagnosis"],
                }
            )
    print(f"\n已导出 {len(flagged)} 条记录到：{csv_path}")


def main():
    parser = argparse.ArgumentParser(
        description="检测『已全部出库但订单主状态未推进到订单完成』的断链订单（只读）。"
    )
    parser.add_argument(
        "--orders",
        type=str,
        default="",
        help="仅检测指定订单号，逗号分隔，如 K26-0692,K26-0743。",
    )
    parser.add_argument(
        "--include-partial",
        action="store_true",
        default=False,
        help="同时列出『部分鞋型已全部出库但订单未完成』的订单（默认只看全部出库）。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="最多打印多少条（默认 50；设为 0 表示全部）。",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="把全部结果导出到指定 CSV 文件路径。",
    )
    args = parser.parse_args()

    order_rids = [r.strip() for r in args.orders.split(",") if r.strip()]

    app = create_app(ProductionConfig)
    with app.app_context():
        rows = _collect(order_rids)
        flagged = _evaluate(rows, include_partial=args.include_partial)

        print(
            f"扫描订单 {len(rows)} 个"
            + (f"，订单过滤={order_rids}" if order_rids else "")
            + f"；判定：生产状态=已全部出库 且 order_current_status < {ORDER_FINISHED_STATUS_ID}(订单完成)\n"
        )
        _print_report(flagged, args.limit)

        if args.csv and flagged:
            _export_csv(flagged, args.csv)


if __name__ == "__main__":
    main()
