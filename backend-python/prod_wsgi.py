"""WSGI entry point for production deployment with Gunicorn/uWSGI"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Import after environment is loaded
from app import create_app
from blueprints import register_blueprints

def create_application():
    """Create and configure the Flask application for WSGI servers"""
    app = create_app()
    register_blueprints(app)
    return app

# Create the WSGI application
app = create_application()

if __name__ == '__main__':
    # This should NOT be used in production - use gunicorn instead
    # gunicorn -w 4 -b 0.0.0.0:8000 prod_wsgi:app
    app.run(host='0.0.0.0', port=8000, debug=False)
