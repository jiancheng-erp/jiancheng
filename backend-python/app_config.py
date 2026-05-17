# app_config.py - Deprecated: Use app.py instead
# This file is kept for backward compatibility with existing imports
# New code should import from app.py

import warnings
from flask_sqlalchemy import SQLAlchemy

warnings.warn(
    "app_config.py is deprecated. Import from app.py instead: from app import create_app, db",
    DeprecationWarning,
    stacklevel=2
)

# Re-export db for backward compatibility
# This allows: from app_config import db
db = SQLAlchemy()


def create_app(config_override=None):
    """Deprecated: Use app.py instead. This function is kept for backward compatibility."""
    warnings.warn(
        "create_app from app_config is deprecated. Use create_app from app.py instead",
        DeprecationWarning,
        stacklevel=2
    )
    from app import create_app as new_create_app
    return new_create_app(config_override)
