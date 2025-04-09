
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from models import *
from api_utility import to_camel, to_snake, db_obj_to_res, format_datetime, accounting_audit_status_converter


from app_config import db
accounting_term_management_bp = Blueprint("accounting_term_management_bp", __name__)


@accounting_term_management_bp.route('/accounting_term/get_term', methods=["GET"])
def get_all_terms():
    return
@accounting_term_management_bp.route('/accounting_term/add_term', methods=["POST"])
def add_term():
    return