import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import and_

from models import *
from production.scheduling import scheduling_status_converter
from wechat_api.send_message_api import send_configurable_message


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
            .join(
                OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id
            )
            .filter(Order.order_type == "N")
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
        for _, _, _, production_info in query:
            scheduling_status = scheduling_status_converter(production_info)
            if scheduling_status == "裁断未排期":
                cut_amount += 1
            elif scheduling_status == "预备未排期":
                pre_sew_amount += 1
            elif scheduling_status == "针车未排期":
                sew_amount += 1
            elif scheduling_status == "成型未排期":
                mold_amount += 1

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_message = (
            "生产流程状态定时通知\n"
            "当前时间：{current_time}\n"
            "当前裁断未排期订单数：{cut_amount}\n"
            "当前预备未排期订单数：{pre_sew_amount}\n"
            "当前针车未排期订单数：{sew_amount}\n"
            "当前成型未排期订单数：{mold_amount}\n"
            "请相关人员及时处理！\n"
            "如有任何问题，请联系相关负责人。"
        )

        send_configurable_message(
            "production_status_cron",
            status_message,
            "070d09bbc28c2cec22535b7ec5d1316b|Wang|ZhongGuiKang|55232b966e1a1348da858dc23135274a|JinKaiXin|WangJinMing|ZouYuanDong",
            context={
                "current_time": current_time,
                "cut_amount": cut_amount,
                "pre_sew_amount": pre_sew_amount,
                "sew_amount": sew_amount,
                "mold_amount": mold_amount,
            },
        )


def send_message_to_all(app):
    with app.app_context():
        order_approval_status = (
            db.session.query(Order, OrderStatus)
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(OrderStatus.order_current_status == 7)
            .all()
        )
        production_instruction_status = (
            db.session.query(Order, OrderStatus, OrderShoe, OrderShoeStatus)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(
                OrderShoeStatus,
                OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id,
            )
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
            .join(
                OrderShoeStatus,
                OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id,
            )
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
            .join(
                OrderShoeStatus,
                OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id,
            )
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
            .join(
                OrderShoeStatus,
                OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id,
            )
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
            .join(
                OrderShoeStatus,
                OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id,
            )
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
            .join(
                OrderShoeStatus,
                OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id,
            )
            .join(OrderStatus, Order.order_id == OrderStatus.order_id)
            .filter(
                and_(
                    OrderStatus.order_current_status == 9,
                    OrderShoeStatus.current_status == 9,
                )
            )
            .all()
        )

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_message = (
            "采购流程状态定时通知\n"
            "当前时间：{current_time}\n"
            "当前总经理待审批订单数：{order_approval_count}\n"
            "当前投产指令单创建订单数：{production_instruction_count}\n"
            "当前面料用量填写订单数：{first_usage_input_count}\n"
            "当前一次采购创建订单数：{first_purchase_count}\n"
            "当前总仓采购创建订单数：{second_purchase_count}\n"
            "当前工艺单创建订单数：{craft_sheet_count}\n"
            "当前二次BOM用量填写订单数：{second_usage_input_count}\n"
            "请相关人员及时处理！\n"
            "如有任何问题，请联系相关负责人。"
        )

        send_configurable_message(
            "purchase_status_cron",
            status_message,
            "070d09bbc28c2cec22535b7ec5d1316b|Wang|ZhongGuiKang|55232b966e1a1348da858dc23135274a|FanJianMing|XieShuWa|YangShuYao",
            context={
                "current_time": current_time,
                "order_approval_count": len(order_approval_status),
                "production_instruction_count": len(production_instruction_status),
                "first_usage_input_count": len(first_usage_input_status),
                "first_purchase_count": len(first_purchase_status),
                "second_purchase_count": len(second_purchase_status),
                "craft_sheet_count": len(craft_sheet_status),
                "second_usage_input_count": len(second_usage_input_status),
            },
        )


def send_massage_to_business(app):
    with app.app_context():
        manager1 = (
            db.session.query(Order, OrderShoe, Shoe, Customer, OrderStatus)
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(Customer, Order.customer_id == Customer.customer_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .filter(
                Order.supervisor_id == 10,
                OrderStatus.order_current_status == 6,
                OrderStatus.order_status_value == 1,
            )
            .all()
        )
        manager2 = (
            db.session.query(Order, OrderShoe, Shoe, Customer, OrderStatus)
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(Customer, Order.customer_id == Customer.customer_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .filter(
                Order.supervisor_id == 24,
                OrderStatus.order_current_status == 6,
                OrderStatus.order_status_value == 1,
            )
            .all()
        )
        manager3 = (
            db.session.query(Order, OrderShoe, Shoe, Customer, OrderStatus)
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(Customer, Order.customer_id == Customer.customer_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .filter(
                Order.supervisor_id == 30,
                OrderStatus.order_current_status == 6,
                OrderStatus.order_status_value == 1,
            )
            .all()
        )
        pre_create_orders_for_manager1 = (
            db.session.query(Order, OrderShoe, Shoe, Customer, OrderStatus)
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(Customer, Order.customer_id == Customer.customer_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .filter(
                Order.supervisor_id == 10,
                OrderStatus.order_current_status == 6,
                OrderStatus.order_status_value == 0,
            )
            .all()
        )
        pre_create_orders_for_manager2 = (
            db.session.query(Order, OrderShoe, Shoe, Customer, OrderStatus)
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(Customer, Order.customer_id == Customer.customer_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .filter(
                Order.supervisor_id == 24,
                OrderStatus.order_current_status == 6,
                OrderStatus.order_status_value == 0,
            )
            .all()
        )
        pre_create_orders_for_manager3 = (
            db.session.query(Order, OrderShoe, Shoe, Customer, OrderStatus)
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(Customer, Order.customer_id == Customer.customer_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .filter(
                Order.supervisor_id == 30,
                OrderStatus.order_current_status == 6,
                OrderStatus.order_status_value == 0,
            )
            .all()
        )

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_message = (
            "业务流程状态定时通知\n"
            "当前时间：{current_time}\n"
            "待业务经理审批订单数：{manager1_pending}\n"
            "待业务经理审批订单数：{manager2_pending}\n"
            "待业务经理审批订单数：{manager3_pending}\n"
            "订单创建待提交审批订单数（业务经理1）：{manager1_pre_create}\n"
            "订单创建待提交审批订单数（业务经理2）：{manager2_pre_create}\n"
            "订单创建待提交审批订单数（业务经理3）：{manager3_pre_create}\n"
            "请相关人员及时处理！\n"
            "如有任何问题，请联系相关负责人。"
        )
        status_message_for_manager = (
            "业务流程状态定时通知\n"
            "您的身份是业务经理\n"
            "当前时间：{current_time}\n"
            "待审批订单数：{pending}\n"
            "订单创建待提交审批订单数：{pre_create}\n"
            "请及时处理！"
        )

        send_configurable_message(
            "business_status_all",
            status_message,
            "070d09bbc28c2cec22535b7ec5d1316b|55232b966e1a1348da858dc23135274a",
            context={
                "current_time": current_time,
                "manager1_pending": len(manager1),
                "manager2_pending": len(manager2),
                "manager3_pending": len(manager3),
                "manager1_pre_create": len(pre_create_orders_for_manager1),
                "manager2_pre_create": len(pre_create_orders_for_manager2),
                "manager3_pre_create": len(pre_create_orders_for_manager3),
            },
        )
        send_configurable_message(
            "business_status_manager1",
            status_message_for_manager,
            "utopa.",
            context={
                "current_time": current_time,
                "pending": len(manager1),
                "pre_create": len(pre_create_orders_for_manager1),
            },
        )
        send_configurable_message(
            "business_status_manager2",
            status_message_for_manager,
            "ellen",
            context={
                "current_time": current_time,
                "pending": len(manager2),
                "pre_create": len(pre_create_orders_for_manager2),
            },
        )
        send_configurable_message(
            "business_status_manager3",
            status_message_for_manager,
            "55232b966e1a1348da858dc23135274a",
            context={
                "current_time": current_time,
                "pending": len(manager3),
                "pre_create": len(pre_create_orders_for_manager3),
            },
        )


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=send_message_to_all,
        trigger="cron",
        hour=9,
        minute=0,
        args=[app],
        id="morning_status_message",
    )
    scheduler.add_job(
        func=send_message_to_all,
        trigger="cron",
        hour=12,
        minute=0,
        args=[app],
        id="noon_status_message",
    )
    scheduler.add_job(
        func=send_message_to_all,
        trigger="cron",
        hour=18,
        minute=0,
        args=[app],
        id="evening_status_message",
    )
    scheduler.add_job(
        func=send_message_to_production,
        trigger="cron",
        hour=9,
        minute=0,
        args=[app],
        id="production_morning_status_message",
    )
    scheduler.add_job(
        func=send_message_to_production,
        trigger="cron",
        hour=12,
        minute=0,
        args=[app],
        id="production_noon_status_message",
    )
    scheduler.add_job(
        func=send_message_to_production,
        trigger="cron",
        hour=18,
        minute=0,
        args=[app],
        id="production_evening_status_message",
    )
    scheduler.add_job(
        func=send_massage_to_business,
        trigger="cron",
        hour=9,
        minute=0,
        args=[app],
        id="business_morning_status_message",
    )
    scheduler.add_job(
        func=send_massage_to_business,
        trigger="cron",
        hour=12,
        minute=0,
        args=[app],
        id="business_afternoon_status_message",
    )
    scheduler.add_job(
        func=send_massage_to_business,
        trigger="cron",
        hour=18,
        minute=0,
        args=[app],
        id="business_evening_status_message",
    )
    scheduler.start()
