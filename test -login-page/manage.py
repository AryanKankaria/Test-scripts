"""
Database migration configuration using Flask-Migrate
"""

from flask import Flask
from flask_migrate import Migrate
from app import app
from models import db

# Initialize migrations
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()
