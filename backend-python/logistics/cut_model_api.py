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

cut_model_api_bp = Blueprint("cut_model_api", __name__)