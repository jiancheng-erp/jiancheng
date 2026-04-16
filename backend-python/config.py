"""Application configuration for different environments"""
import os
from datetime import timedelta

class Config:
    """Base configuration shared across all environments"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get('SESSION_LIFETIME_DAYS', 7)))
    
    # CORS
    JSON_SORT_KEYS = False
    
    # Redis
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-key-change-in-production')
    
    # Wechat
    WECHAT_TEST_MODE = True
    FILE_STORAGE_PATH = os.environ.get('FILE_STORAGE_PATH')
    IMAGE_STORAGE_PATH = os.environ.get('IMAGE_STORAGE_PATH')
    IMAGE_UPLOAD_PATH = os.environ.get('IMAGE_UPLOAD_PATH')

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    
    # Database - Use environment variables or local config file
    db_username = os.environ.get('DB_USERNAME', 'jiancheng_dev1')
    db_password = os.environ.get('DB_PASSWORD', '123456Ab')
    db_name = os.environ.get('DB_NAME', 'jiancheng')
    db_host = os.environ.get('DB_HOST', 'rm-wz9e6065n2281l3i56o.mysql.rds.aliyuncs.com')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}"
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # In production, all secrets MUST be set via environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    # Database - Must use environment variables
    db_username = os.environ.get('DB_USERNAME')
    db_password = os.environ.get('DB_PASSWORD')
    db_name = os.environ.get('DB_NAME')
    db_host = os.environ.get('DB_HOST')
    
    
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}"
    SQLALCHEMY_ECHO = False
    
    def __init__(self):
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production!")
        if not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY environment variable must be set in production!")
        if not all([db_username, db_password, db_name, db_host]):
            raise ValueError("Database environment variables must be set in production!")    

class TestingConfig(Config):
    """Testing environment configuration - uses in-memory SQLite"""
    DEBUG = True
    TESTING = True
    
    # Use SQLite for tests (no external DB needed)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    
    # Disable JWT for easier testing
    JWT_ALGORITHM = 'HS256'
    
    # Disable Redis for tests
    REDIS_HOST = None


def get_config():
    """Get configuration based on FLASK_ENV environment variable"""
    env = os.environ.get('FLASK_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig


# Create config instance
config = get_config()
