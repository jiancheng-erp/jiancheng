"""Pytest configuration and fixtures for the entire test suite"""
import os
import pytest
from flask import Flask
from config import TestingConfig
from app import create_app, db


@pytest.fixture(scope='session')
def app():
    """
    Create application for the whole test session.
    Uses TestingConfig which uses SQLite in-memory database.
    """
    # Set testing environment
    os.environ['FLASK_ENV'] = 'testing'
    
    # Create app with testing config
    app = create_app(TestingConfig)
    
    # Create all database tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """
    Test client for making HTTP requests to the app.
    Scope is 'function' so a fresh client is created for each test.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """
    Database session for direct database access in tests.
    Uses the same test database as the app.
    Rollback after each test to maintain isolation.
    """
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        session = db.Session(bind=connection)
        
        yield session
        
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def runner(app):
    """
    CLI test runner for testing Flask CLI commands.
    """
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def auth_headers(client):
    """
    Create a test user and return JWT auth headers.
    This allows tests to make authenticated requests.
    """
    # For now, create a mock token (tests should be independent of auth)
    # In a real app, you would create a test user and generate a real token
    return {
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
    }


# Database fixtures
@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    from models import User
    
    user = User(
        user_name='testuser',
        user_passwd='hashedpassword',
        staff_id=1
    )
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def sample_bom(db_session):
    """Create a sample BOM for testing"""
    from models import Bom
    
    bom = Bom(
        bom_rid='TEST-BOM-001',
        bom_type=1,
        order_shoe_type_id=1
    )
    db_session.add(bom)
    db_session.commit()
    
    return bom


# Test utilities
def cleanup_db(app):
    """Helper to clean up database between tests"""
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
