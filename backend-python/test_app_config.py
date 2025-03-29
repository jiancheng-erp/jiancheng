# app_config.py
import json
import os
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, verify_jwt_in_request
import redis

def create_app(config_override):
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.config.from_mapping(config_override)
    return app
