"""
Database Initialization and Utility Script
Run this to initialize the database and create demo users
"""

import sys
from app import app, db
from models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize the database and create tables"""
    with app.app_context():
        try:
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("✓ Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Error creating database tables: {e}")
            return False


def create_demo_user(username="testuser", email="test@example.com", password="testpass123"):
    """Create a demo user for testing"""
    with app.app_context():
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                logger.warning(f"✓ Demo user '{username}' already exists")
                return False
            
            # Create new demo user
            demo_user = User(username=username, email=email)
            demo_user.set_password(password)
            
            db.session.add(demo_user)
            db.session.commit()
            
            logger.info(f"✓ Demo user '{username}' created successfully")
            logger.info(f"  Username: {username}")
            logger.info(f"  Email: {email}")
            logger.info(f"  Password: {password}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"✗ Error creating demo user: {e}")
            return False


def list_all_users():
    """List all users in the database"""
    with app.app_context():
        try:
            users = User.query.all()
            if not users:
                logger.info("No users found in database")
                return []
            
            logger.info(f"Found {len(users)} user(s):")
            for user in users:
                logger.info(f"  - {user.username} ({user.email}) - Active: {user.is_active}")
            return users
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []


def delete_all_users():
    """Delete all users from the database (for testing)"""
    with app.app_context():
        try:
            count = User.query.delete()
            db.session.commit()
            logger.info(f"✓ Deleted {count} user(s) from database")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"✗ Error deleting users: {e}")
            return False


def delete_database():
    """Drop all database tables"""
    with app.app_context():
        try:
            logger.warning("Dropping all database tables...")
            db.drop_all()
            logger.info("✓ All database tables dropped")
            return True
        except Exception as e:
            logger.error(f"✗ Error dropping database tables: {e}")
            return False


def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 2:
        print("Database Utility Script")
        print("Usage: python db_utils.py [command]")
        print("\nCommands:")
        print("  init          - Initialize database and create tables")
        print("  demo          - Create a demo user (testuser/testpass123)")
        print("  list          - List all users")
        print("  delete-all    - Delete all users (for testing)")
        print("  drop          - Drop all database tables")
        print("  reset         - Drop all tables and reinitialize (WARNING: deletes all data)")
        return

    command = sys.argv[1].lower()

    if command == "init":
        init_database()
    
    elif command == "demo":
        init_database()
        create_demo_user()
    
    elif command == "list":
        list_all_users()
    
    elif command == "delete-all":
        confirm = input("Are you sure you want to delete all users? (yes/no): ")
        if confirm.lower() == "yes":
            delete_all_users()
        else:
            logger.info("Operation cancelled")
    
    elif command == "drop":
        confirm = input("Are you sure you want to drop all database tables? (yes/no): ")
        if confirm.lower() == "yes":
            delete_database()
        else:
            logger.info("Operation cancelled")
    
    elif command == "reset":
        confirm = input("Are you sure? This will DELETE ALL DATA. Type 'reset' to confirm: ")
        if confirm == "reset":
            delete_database()
            init_database()
            create_demo_user()
            logger.info("✓ Database reset complete")
        else:
            logger.info("Operation cancelled")
    
    else:
        logger.error(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
