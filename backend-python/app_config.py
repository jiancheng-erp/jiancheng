# app_config.py
import json
import os
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from flask_jwt_extended import JWTManager, verify_jwt_in_request
import redis

WECHAT_TEST_MODE = True

# Create an uninitialized db instance.
db = SQLAlchemy()

def create_app(config_override=None):
    app = Flask(__name__)
    CORS(app, supports_credentials=True)

    # Load configuration from file or use an override.
    if config_override:
        app.config.from_mapping(config_override)
    else:
        config_path = os.path.join(os.path.dirname(__file__), 'backend_config.json')
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
        # Set up database URI and other configs
        db_username = config["db_username"]
        db_password = config["db_password"]
        db_name = config["db_name"]
        db_host = config["db_host"]
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}"
        )
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.secret_key = config["secret_key"]
        app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
            days=config["session_lifetime_days"]
        )
        app.config["JWT_SECRET_KEY"] = config["jwt_secret_key"]
        # Save Redis configuration for later use.
        app.config["REDIS_HOST"] = config["redis_host"]
        app.config["REDIS_PORT"] = config["redis_port"]
        app.config["REDIS_DB"] = config["redis_db"]

    # Initialize database
    db.init_app(app)

    # Set up serializer, JWT, and Redis.
    jwt = JWTManager(app)
    redis_client = redis.StrictRedis(
        host=app.config.get("REDIS_HOST"),
        port=app.config.get("REDIS_PORT"),
        db=app.config.get("REDIS_DB"),
        decode_responses=True,
    )
    app.redis_client = redis_client

    # Define open routes that do not require authentication.
    open_routes = [
        "/login",
        "/favicon.ico",
        "/devproductionorder/download",
        "/orderimport/downloadorderdoc",
        "/processsheet/download",
        "/firstbom/download",
        "/secondbom/download",
        "/firstpurchase/downloadpurchaseorderzip",
        "/firstpurchase/downloadmaterialstatistics",
        "/secondpurchase/downloadpurchaseorderzip",
        "/secondpurchase/downloadmaterialstatistics",
        "/production/downloadproductionform",
        "/production/downloadbatchinfo",
        "/headmanager/getcostinfo",
        "/headmanager/getorderstatusinfo",
        "/headmanager/getmaterialpriceinfo",
        "/headmanager/getmaterialinboundcurve",
        "/headmanager/financialstatus",
        "/headmanager/getordershoetimeline",
        "/devproductionorder/downloadproductioninstruction",
        "/devproductionorder/downloadpicnotes",
        "/logistics/downloadassetzip",
        "/craftsheet/downloadcraftsheet",
        "/order/exportorder",
        "/order/exportproductionorder",
        "/multiissue/downloadtotalpurchaseorder",
        "/logistics/downloadlastpurchaseorders",
        "/logistics/downloadpackagepurchaseorders",
    ]

    @app.before_request
    def authenticate():
        if request.path not in open_routes:
            try:
                verify_jwt_in_request()
            except Exception as e:
                return jsonify({"msg": "Authentication required", "error": str(e)}), 401

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token_in_redis = redis_client.get(jti)
        return token_in_redis is None

    return app
