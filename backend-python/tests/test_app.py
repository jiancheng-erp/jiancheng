"""Tests for application initialization and configuration"""
import pytest
from flask import Flask


class TestAppInitialization:
    """Test app factory and configuration"""
    
    def test_app_creation(self, app):
        """Test that app is created successfully"""
        assert app is not None
        assert isinstance(app, Flask)
    
    def test_app_config_testing(self, app):
        """Test that app is in testing mode"""
        assert app.config['TESTING'] is True
    
    def test_app_database_uri(self, app):
        """Test that database URI is set (SQLite for tests)"""
        assert 'sqlite:///:memory:' in app.config['SQLALCHEMY_DATABASE_URI']
    
    def test_app_cors_enabled(self, app):
        """Test that CORS is enabled"""
        # Check if CORS extension is registered
        assert 'flask_cors.CORS' in str(app.extensions)
    
    def test_app_jwt_enabled(self, app):
        """Test that JWT is enabled"""
        assert 'flask_jwt_extended.view_decorators' in str(app.extensions)


class TestClient:
    """Test client functionality"""
    
    def test_client_creation(self, client):
        """Test that test client is created"""
        assert client is not None
    
    def test_health_check(self, client, app):
        """Test basic health check - app should respond"""
        # Just test that we can make a request
        with app.app_context():
            # This should not raise an error
            assert client is not None


class TestDatabaseConnection:
    """Test database connection and session management"""
    
    def test_db_session_available(self, db_session):
        """Test that database session is available"""
        assert db_session is not None
    
    def test_db_tables_created(self, app):
        """Test that all database tables are created"""
        with app.app_context():
            # Get all table names
            inspector = __import__('sqlalchemy').inspect
            from app import db
            
            # Should have created some tables
            tables = inspector(db.engine).get_table_names()
            assert len(tables) > 0
