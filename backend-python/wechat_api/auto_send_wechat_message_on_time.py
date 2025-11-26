from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import and_
from models import *
import datetime
from wechat_api.send_message_api import send_massage_to_users
import requests
from production.scheduling import scheduling_status_converter

def send_message_to_production(app):
    with app.app_context():
        query = (
            db.session.query(Order, OrderShoe, Shoe, OrderShoeProductionInfo)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
            .join(
                OrderShoeProductionInfo,
                OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(OrderStatus, OrderStatus.order_id == Order.order_id)
            .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
            .filter(OrderStatus.order_current_status >= 9)
            .filter(OrderShoeStatus.current_status >= 17)
            .order_by(Order.order_rid)
            .distinct()
            .all()
        )
        cut_amount = 0
        sew_amount = 0
        pre_sew_amount = 0
        mold_amount = 0
        for row in query:
            order, order_shoe, shoe, production_info = row
            scheduling_status = scheduling_status_converter(production_info)
            if scheduling_status == "裁断未排期":
                cut_amount += 1
            elif scheduling_status == "预备未排期":
                pre_sew_amount += 1
            elif scheduling_status == "针车未排期":
                sew_amount += 1
            elif scheduling_status == "成型未排期":
                mold_amount += 1

        # 构造通知内容
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_message = (
            f"生产流程状态定时通知\n"
            f"当前时间：{current_time}\n"
            f"当前裁断未排期订单数：{cut_amount}\n"
            f"当前预备未排期订单数：{pre_sew_amount}\n"
            f"当前针车未排期订单数：{sew_amount}\n"
            f"当前成型未排期订单数：{mold_amount}\n"
            f"请相关人员及时处理！\n"
            f"如果有任何问题，请联系相关负责人！"
        )

        send_massage_to_users(status_message, "070d09bbc28c2cec22535b7ec5d1316b|Wang|ZhongGuiKang|55232b966e1a1348da858dc23135274a|JinKaiXin|WangJinMing|ZouYuanDong")


def send_message_to_all(app):
    with app.app_context():
        business_order_pending_submit_status = (
            db.session.query(Order, OrderStatus)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(
                and_(
                    OrderStatus.order_current_status == 6,
                    OrderStatus.order_status_value == 0,
                    )
                )
            .all()
        )
        business_order_pending_approval_status = (
            db.session.query(Order, OrderStatus)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(
                and_(
                    OrderStatus.order_current_status == 6,
                    OrderStatus.order_status_value == 1,
                    )
                )
            .all()
        )
        order_approval_status = (
            db.session.query(Order, OrderStatus)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(OrderStatus.order_current_status == 7)
            .all()
        )
        production_instruction_status = (
            db.session.query(Order, OrderStatus, OrderShoe, OrderShoeStatus)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(
                and_(
                    OrderStatus.order_current_status == 9,
                    OrderShoeStatus.current_status == 0,
                )
            )
            .all()
        )
        first_usage_input_status = (
            db.session.query(Order, OrderStatus, OrderShoe, OrderShoeStatus)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(
                and_(
                    OrderStatus.order_current_status == 9,
                    OrderShoeStatus.current_status == 4,
                )
            )
            .all()
        )
        second_usage_input_status = (
            db.session.query(Order, OrderStatus, OrderShoe, OrderShoeStatus)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(
                and_(
                    OrderStatus.order_current_status == 9,
                    OrderShoeStatus.current_status == 11,
                )
            )
            .all()
        )
        first_purchase_status = (
            db.session.query(Order, OrderStatus, OrderShoe, OrderShoeStatus)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(
                and_(
                    OrderStatus.order_current_status == 9,
                    OrderShoeStatus.current_status == 6,
                )
            )
            .all()
        )
        second_purchase_status = (
            db.session.query(Order, OrderStatus, OrderShoe, OrderShoeStatus)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(
                and_(
                    OrderStatus.order_current_status == 9,
                    OrderShoeStatus.current_status == 7,
                )
            )
            .all()
        )
        craft_sheet_status = (
            db.session.query(Order, OrderStatus, OrderShoe, OrderShoeStatus)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(
                and_(
                    OrderStatus.order_current_status == 9,
                    OrderShoeStatus.current_status == 9,
                )
            )
            .all()
        )

        # 构造通知内容
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_message = (
            f"采购流程状态定时通知\n"
            f"当前时间：{current_time}\n"
            f"当前业务员创建未提交订单数：{len(business_order_pending_submit_status)}\n"
            f"当前业务经理未审批订单数：{len(business_order_pending_approval_status)}\n"
            f"当前总经理待审批订单数：{len(order_approval_status)}\n"
            f"当前投产指令单创建订单数：{len(production_instruction_status)}\n"
            f"当前面料用量填写订单数：{len(first_usage_input_status)}\n"
            f"当前一次采购创建订单数：{len(first_purchase_status)}\n"
            f"当前总仓采购创建订单数：{len(second_purchase_status)}\n"
            f"当前工艺单创建订单数：{len(craft_sheet_status)}\n"
            f"当前二次BOM用量填写订单数：{len(second_usage_input_status)}\n"
            f"请相关人员及时处理！\n"
            f"如果有任何问题，请联系相关负责人！"
        )

        send_massage_to_users(status_message, "070d09bbc28c2cec22535b7ec5d1316b|Wang|ZhongGuiKang|55232b966e1a1348da858dc23135274a|FanJianMing|XieShuWa|YangShuYao")


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
    scheduler.start()
