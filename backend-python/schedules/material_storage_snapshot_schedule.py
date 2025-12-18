from __future__ import annotations

from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

from logger import logger
from app_config import db

# 统一用 generate_material_storage_snapshot 的口径生成快照（回放聚合）
from script.generate_material_storage_snapshot import generate_material_storage_snapshot

BEIJING_TZ = "Asia/Shanghai"


def _prev_month_end() -> date:
    """返回本地时区下上个月最后一天的日期"""
    today_local = datetime.now(ZoneInfo(BEIJING_TZ)).date()
    first_day_this_month = today_local.replace(day=1)
    return first_day_this_month - timedelta(days=1)


def update_material_storage_snapshot(app):
    """
    每天更新过往一年的 material_storage_snapshot 和 material_storage_size_detail_snapshot 数据，
    确保财务审核完入库/出库后数据的准确性。

    实现：对最近 12 个“月末快照日”逐月重算并 upsert（只更新变化的行，必要时清理已不应存在的行）。
    """
    latest_month_end = _prev_month_end()

    # 最近 12 个月末（含 latest_month_end）
    month_ends: list[date] = []
    d = latest_month_end
    for _ in range(12):
        month_ends.append(d)
        d = d.replace(day=1) - timedelta(days=1)  # 上一个月末

    for d in month_ends:
        logger.info(f"🧾 upsert 月末快照: snapshot_date={d}")
        generate_material_storage_snapshot(
            app,
            db,
            str(d),
            upsert=True,
            cleanup_removed=True,
        )

    logger.info(f"✅ 过去 12 个月月末快照 upsert 完成 (latest={latest_month_end})")


# def snapshot_material_storage(app):
#     """
#     生成“上个月月末”快照。

#     说明：不要直接把当前 material_storage/material_storage_size_detail copy 到 snapshot
#     （因为当前表会随审核变化），应按 snapshot_date 的口径实时回放聚合，然后写入 snapshot 表。
#     """
#     snapshot_date = _prev_month_end()
#     logger.info(f"📸 生成月末快照：snapshot_date={snapshot_date}")
#     generate_material_storage_snapshot(app, db, str(snapshot_date), upsert=True, cleanup_removed=True)
#     logger.info(f"✅ 月末快照完成：snapshot_date={snapshot_date}")
