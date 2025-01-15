from flask import Blueprint, jsonify, request
from models import *
from api_utility import to_camel, to_snake


from app_config import app, db

batch_type_bp = Blueprint("batch_type_bp", __name__)


