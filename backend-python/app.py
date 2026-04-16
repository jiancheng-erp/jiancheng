"""Application factory for Flask app creation and initialization"""
import os
from decimal import Decimal
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request
from flask.json.provider import DefaultJSONProvider
import redis

from config import get_config
# Import db from app_config for backward compatibility with models.py
# This ensures all code uses the same db instance
from app_config import db


def create_app(config=None):
    """
    Application factory: Creates and configures Flask app
    
    Args:
        config: Optional config class to override environment-based config
        
    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        config_obj = get_config()
    else:
        config_obj = config
    
    app.config.from_object(config_obj)
    
    # Enable CORS
    CORS(app, supports_credentials=True)
    
    # Initialize database (db instance from app_config)
    db.init_app(app)
    
    # Setup JWT
    jwt = JWTManager(app)
    
    # Setup Redis (if not testing)
    if app.config.get('REDIS_HOST'):
        try:
            redis_client = redis.StrictRedis(
                host=app.config.get('REDIS_HOST'),
                port=app.config.get('REDIS_PORT'),
                db=app.config.get('REDIS_DB'),
                decode_responses=True,
            )
            # Test connection
            redis_client.ping()
            app.redis_client = redis_client
        except Exception as e:
            print(f"Warning: Could not connect to Redis: {e}")
            app.redis_client = None
    else:
        app.redis_client = None
    
    # Define open routes that do not require authentication
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
        "/forecastsheet/downloadexcel"
    ]
    
    # JWT error handlers
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return identity
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if token has been revoked (logged out)"""
        jti = jwt_payload["jti"]
        if not app.redis_client:
            return False  # Can't revoke without Redis, allow token
        token_in_redis = app.redis_client.get(jti)
        return token_in_redis is not None  # True if token is revoked
    
    @app.before_request
    def authenticate():
        """Authenticate requests using JWT"""
        if not app.config.get('TESTING'):  # Skip auth in tests
            if request.path not in open_routes:
                try:
                    verify_jwt_in_request()
                except Exception as e:
                    return jsonify({"msg": str(e)}), 401
    
    # Handle Decimal serialization for prices/quantities
    def decimal_to_str(d: Decimal) -> str:
        """Convert Decimal to string without scientific notation or trailing zeros"""
        return format(d.normalize(), 'f')
    
    class CustomJSONProvider(DefaultJSONProvider):
        """Custom JSON encoder that handles Decimal types"""
        def default(self, o):
            if isinstance(o, Decimal):
                return decimal_to_str(o)
            return super().default(o)
    
    app.json = CustomJSONProvider(app)
    
    # Create database tables in app context
    with app.app_context():
        db.create_all()
    
    return app
