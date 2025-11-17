from apscheduler.schedulers.background import BackgroundScheduler
from wechat_api.auto_send_wechat_message_on_time import *
from schedules.material_storage_snapshot_schedule import *


# 启动调度器函数（在主程序中调用）
def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=send_message_to_all,
        trigger='cron',
        hour=9, minute=0,
        args=[app],
        id='morning_status_message'
    )
    scheduler.add_job(
        func=send_message_to_all,
        trigger='cron',
        hour=12, minute=0,
        args=[app],
        id='noon_status_message'
    )
    scheduler.add_job(
        func=send_message_to_all,
        trigger='cron',
        hour=18, minute=0,
        args=[app],
        id='evening_status_message'
    )
    scheduler.add_job(
        func=send_message_to_production,
        trigger='cron',
        hour=9, minute=0,
        args=[app],
        id='production_morning_status_message'
    )
    scheduler.add_job(
        func=send_message_to_production,
        trigger='cron',
        hour=12, minute=0,
        args=[app],
        id='production_noon_status_message'
    )
    scheduler.add_job(
        func=send_message_to_production,
        trigger='cron',
        hour=18, minute=0,
        args=[app],
        id='production_evening_status_message'
    )
    # 每月 1 号 00:05 执行一次
    scheduler.add_job(
        func=snapshot_material_storage,
        trigger="cron",
        day=1,
        hour=0,
        minute=5,
        second=0,
        args=[app],
        id="material_storage_snapshot",
        replace_existing=True,
    )

    # 每天 00:05 执行一次
    scheduler.add_job(
        func=snapshot_daily_storage_change,
        trigger="cron",
        hour=0,
        minute=5,
        second=0,
        args=[app],
        id="daily_storage_change_snapshot",
        replace_existing=True,
    )
    scheduler.start()
