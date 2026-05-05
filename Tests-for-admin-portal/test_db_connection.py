import pytest
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'admin_portal_test')


class TestDatabaseConnection:

    def test_can_connect_to_database(self, db_connection):
        assert db_connection is not None
        assert not db_connection.closed

    def test_can_execute_query(self, db_cursor):
        db_cursor.execute('SELECT 1')
        result = db_cursor.fetchone()
        assert result == (1,)

    def test_can_query_admin_portal_users_table(self, db_cursor):
        db_cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'admin_portal_users'"
        )
        result = db_cursor.fetchone()
        assert result is not None
        assert result[0] == 'admin_portal_users'

    def test_can_query_admin_portal_token_blacklist_table(self, db_cursor):
        db_cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'admin_portal_token_blacklist'"
        )
        result = db_cursor.fetchone()
        assert result is not None

    def test_can_query_admin_portal_password_reset_tokens_table(self, db_cursor):
        db_cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'admin_portal_password_reset_tokens'"
        )
        result = db_cursor.fetchone()
        assert result is not None

    def test_can_query_admin_action_audit_logs_table(self, db_cursor):
        db_cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'admin_action_audit_logs'"
        )
        result = db_cursor.fetchone()
        assert result is not None

    def test_admin_users_table_has_correct_columns(self, db_cursor):
        db_cursor.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'admin_portal_users' ORDER BY ordinal_position"
        )
        columns = [col[0] for col in db_cursor.fetchall()]
        required_columns = ['id', 'email', 'password_hash', 'name', 'role', 'is_active', 'last_login_at', 'created_at', 'updated_at']
        for col in required_columns:
            assert col in columns

    def test_can_count_admin_users(self, db_cursor):
        db_cursor.execute("SELECT COUNT(*) FROM admin_portal_users")
        result = db_cursor.fetchone()
        assert result[0] >= 0

    def test_can_query_active_admin_users(self, db_cursor):
        db_cursor.execute("SELECT COUNT(*) FROM admin_portal_users WHERE is_active = true")
        result = db_cursor.fetchone()
        assert result is not None
        assert result[0] >= 0

    def test_can_query_audit_logs(self, db_cursor):
        db_cursor.execute("SELECT COUNT(*) FROM admin_action_audit_logs")
        result = db_cursor.fetchone()
        assert result is not None
        assert result[0] >= 0

    def test_transaction_rollback_works(self, db_transaction):
        cursor = db_transaction.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM admin_portal_token_blacklist")
        count_before = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO admin_portal_token_blacklist (jti, expires_at) VALUES (%s, now() + interval '1 hour')",
            ('test-jti-rollback',)
        )
        
        db_transaction.rollback()
        
        cursor.execute("SELECT COUNT(*) FROM admin_portal_token_blacklist WHERE jti = 'test-jti-rollback'")
        result = cursor.fetchone()
        assert result[0] == 0
        
        cursor.close()

    def test_database_user_exists(self, db_cursor):
        db_cursor.execute("SELECT 1 FROM admin_portal_users LIMIT 1")
        result = db_cursor.fetchone()
        if result is None:
            pytest.skip("No test users in database")

    def test_database_connection_pool_reusable(self, db_connection):
        assert db_connection is not None
        
        cursor1 = db_connection.cursor()
        cursor1.execute("SELECT 1")
        result1 = cursor1.fetchone()
        cursor1.close()
        
        cursor2 = db_connection.cursor()
        cursor2.execute("SELECT 2")
        result2 = cursor2.fetchone()
        cursor2.close()
        
        assert result1 == (1,)
        assert result2 == (2,)

    def test_database_credentials_valid(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT current_user")
        user = cursor.fetchone()[0]
        cursor.close()
        assert user is not None
        assert len(user) > 0
