"""
Database and Application Configuration
Update these values with your database details
"""

import os
from datetime import timedelta

# Database Configuration
# Supported: sqlite, postgresql, mysql
DB_TYPE = "postgresql"  # Change this to your DB type

# For SQLite (local)
# if DB_TYPE == "sqlite":
#     SQLALCHEMY_DATABASE_URI = "sqlite:///login_app.db"

# For PostgreSQL
if DB_TYPE == "postgresql":
    DB_USER = "postgres"
    DB_PASSWORD = "1234"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "script-test-db"
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# For MySQL
# elif DB_TYPE == "mysql":
#     DB_USER = "your_username"
#     DB_PASSWORD = "your_password"
#     DB_HOST = "localhost"
#     DB_PORT = "3306"
#     DB_NAME = "login_db"
#     SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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
