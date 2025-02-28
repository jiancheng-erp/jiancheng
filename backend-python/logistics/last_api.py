from flask import Blueprint, jsonify, request
import datetime
from app_config import app, db
from models import *
from constants import SHOESIZERANGE
from api_utility import randomIdGenerater
from decimal import Decimal
from operator import itemgetter
from sqlalchemy.exc import SQLAlchemyError
from itertools import groupby
import os
from general_document.purchase_divide_order import generate_excel_file
from general_document.size_purchase_divide_order import generate_size_excel_file
from constants import SHOESIZERANGE
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH

last_api_bp = Blueprint("last_api", __name__)

@last_api_bp.route("/logistics/getnewlastpurchaseorderid", methods=["GET"])
def get_new_last_purchase_order_id():
    department = "01"
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    new_id = department + current_time_stamp + random_string + "L"
    return jsonify({"purchaseOrderRid": new_id})