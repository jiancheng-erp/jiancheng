import json
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request,
)
import redis
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Database configuration
config_path = os.path.join(os.path.dirname(__file__), 'backend_config.json')

with open(config_path, "r") as config_file:
    config = json.load(config_file)

# Set up database URI
db_username = config["db_username"]
db_password = config["db_password"]
db_name = config["db_name"]
db_host = config["db_host"]

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set secret keys and other app configurations
app.secret_key = config["secret_key"]
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
    days=config["session_lifetime_days"]
)

# Serializer for URL-safe tokens
serializer = URLSafeTimedSerializer(app.secret_key)

# JWT configuration
app.config["JWT_SECRET_KEY"] = config["jwt_secret_key"]
jwt = JWTManager(app)

# Set up Redis client
redis_client = redis.StrictRedis(
    host=config["redis_host"],
    port=config["redis_port"],
    db=config["redis_db"],
    decode_responses=True,
)

# Initialize database
db = SQLAlchemy(app)

# List of public routes that do not require authentication
open_routes = [
    "/login",
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
    "/multiissue/downloadtotalpurchaseorder",
    "/logistics/downloadlastpurchaseorders",
    "/logistics/downloadpackagepurchaseorders",
]


@app.before_request
def authenticate():
    # Skip authentication for open routes
    if request.path not in open_routes:
        try:
            # Use the JWT method to verify the token automatically
            verify_jwt_in_request()
        except Exception as e:
            # Handle failed authentication (e.g., invalid or expired token)
            return jsonify({"msg": "Authentication required", "error": str(e)}), 401


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]

    # Check if the `jti` exists in Redis
    token_in_redis = redis_client.get(jti)

    # If the token is not found in Redis, it's considered revoked
    return token_in_redis is None
