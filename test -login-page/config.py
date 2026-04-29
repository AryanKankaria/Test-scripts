"""
Database and Application Configuration
"""

import os
from datetime import timedelta

DB_TYPE = "postgresql"
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "script-test-db"
SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# Flask Configuration
SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-change-this-in-production"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# JWT Configuration (Flask-JWT-Extended)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "jwt-secret-key-change-this-in-production"
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# Server Configuration
DEBUG = True
HOST = "127.0.0.1"
PORT = 5000
