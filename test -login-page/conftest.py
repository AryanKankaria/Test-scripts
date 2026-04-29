"""
Pytest configuration - ISOLATES TESTS FROM PRODUCTION DATABASE
"""
import pytest
import sys
import os
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create temporary database FIRST
test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')

# CRITICAL: Override config BEFORE importing app
import config
config.SQLALCHEMY_DATABASE_URI = f'sqlite:///{test_db_path}'


@pytest.fixture(scope='session')
def test_app():
    """Get Flask app configured for testing with SQLite"""
    # Now import app (will use modified config)
    from app import app, db
    
    # Additional test config
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
    
    with app.app_context():
        # Create all tables in SQLite
        db.create_all()
        yield app
    
    # Cleanup
    try:
        os.close(test_db_fd)
        os.unlink(test_db_path)
    except:
        pass


@pytest.fixture(scope='function')
def client(test_app):
    """Fresh test client for each test"""
    return test_app.test_client()


@pytest.fixture(scope='function', autouse=True)
def clean_db(test_app):
    """Clear all data before each test"""
    from models import db, User
    
    with test_app.app_context():
        # Delete all users before test
        db.session.query(User).delete()
        db.session.commit()
        yield
        # Cleanup after test
        db.session.rollback()


@pytest.fixture(scope='function')
def app_context(test_app):
    """Application context for each test"""
    with test_app.app_context():
        yield test_app


@pytest.fixture(scope='function')
def db_session(test_app):
    """Database session for each test"""
    from models import db
    
    with test_app.app_context():
        yield db
        db.session.rollback()




