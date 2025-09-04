"""
Unit tests for database manager
"""
import unittest
import tempfile
import os
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Mock config to use test database
        self.mock_config = MagicMock()
        self.mock_config.sqlite_db_path = self.db_path
        
        with patch('src.core.database.config', self.mock_config):
            self.db_manager = DatabaseManager()
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        try:
            os.unlink(self.db_path)
        except OSError:
            pass
    
    def test_initialization(self):
        """Test database manager initialization"""
        self.assertIsNotNone(self.db_manager.db_path)
        self.assertIsInstance(self.db_manager.db_path, str)
    
    def test_get_connection(self):
        """Test database connection"""
        conn = self.db_manager.get_connection()
        
        self.assertIsNotNone(conn)
        self.assertIsInstance(conn, sqlite3.Connection)
        
        # Test that connection works
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
        
        conn.close()
    
    def test_execute_query(self):
        """Test query execution"""
        # Test successful query
        result = self.db_manager.execute_query("SELECT 1 as test")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 1)
    
    def test_execute_query_with_params(self):
        """Test query execution with parameters"""
        # Create a test table
        self.db_manager.execute_query("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Insert data with parameters
        self.db_manager.execute_query(
            "INSERT INTO test_table (name) VALUES (?)",
            ("test_name",)
        )
        
        # Query with parameters
        result = self.db_manager.execute_query(
            "SELECT name FROM test_table WHERE name = ?",
            ("test_name",)
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "test_name")
    
    def test_execute_query_error_handling(self):
        """Test query error handling"""
        # Test invalid SQL
        result = self.db_manager.execute_query("INVALID SQL QUERY")
        self.assertEqual(result, [])
    
    def test_execute_non_query(self):
        """Test non-query execution (INSERT, UPDATE, DELETE)"""
        # Create table
        success = self.db_manager.execute_non_query("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        self.assertTrue(success)
        
        # Insert data
        success = self.db_manager.execute_non_query(
            "INSERT INTO test_table (name) VALUES (?)",
            ("test_name",)
        )
        self.assertTrue(success)
        
        # Verify data exists
        result = self.db_manager.execute_query("SELECT COUNT(*) FROM test_table")
        self.assertEqual(result[0][0], 1)
    
    def test_execute_non_query_error_handling(self):
        """Test non-query error handling"""
        # Test invalid SQL
        success = self.db_manager.execute_non_query("INVALID SQL")
        self.assertFalse(success)
    
    def test_get_table_info(self):
        """Test table information retrieval"""
        # Create a test table
        self.db_manager.execute_query("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Test table exists check
        # This would require implementing a get_table_info method
        # For now, just test that we can query the table
        result = self.db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
        )
        self.assertEqual(len(result), 1)
    
    def test_database_file_creation(self):
        """Test that database file is created"""
        # Database file should exist after initialization
        self.assertTrue(os.path.exists(self.db_path))
        
        # File should be a valid SQLite database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
        conn.close()
    
    def test_close_connection(self):
        """Test connection closing"""
        # Get a connection first
        conn = self.db_manager.get_connection()
        self.assertIsNotNone(conn)
        
        # Close the database manager
        self.db_manager.close()
        
        # After closing, the connection should be closed
        # We can't easily test this without accessing internals
        # So we'll just verify close() doesn't raise an exception
        self.assertTrue(True)  # If we get here, close() worked
    
    def test_transaction_handling(self):
        """Test transaction handling"""
        # Create table
        self.db_manager.execute_non_query("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Test that changes are committed
        self.db_manager.execute_non_query(
            "INSERT INTO test_table (name) VALUES (?)",
            ("test_name",)
        )
        
        # Verify in a new connection that data is there
        new_db = DatabaseManager()
        with patch('src.core.database.config', self.mock_config):
            result = new_db.execute_query("SELECT COUNT(*) FROM test_table")
            self.assertEqual(result[0][0], 1)
        new_db.close()
    
    def test_concurrent_connections(self):
        """Test multiple simultaneous connections"""
        conn1 = self.db_manager.get_connection()
        conn2 = self.db_manager.get_connection()
        
        # Both connections should work
        cursor1 = conn1.cursor()
        cursor2 = conn2.cursor()
        
        cursor1.execute("SELECT 1")
        cursor2.execute("SELECT 2")
        
        result1 = cursor1.fetchone()
        result2 = cursor2.fetchone()
        
        self.assertEqual(result1[0], 1)
        self.assertEqual(result2[0], 2)
        
        conn1.close()
        conn2.close()


class TestDatabaseManagerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_invalid_database_path(self):
        """Test handling of invalid database path"""
        mock_config = MagicMock()
        mock_config.sqlite_db_path = "/invalid/path/that/does/not/exist/test.db"
        
        with patch('src.core.database.config', mock_config):
            # Should handle the error gracefully
            db_manager = DatabaseManager()
            # The exact behavior depends on implementation
            self.assertIsNotNone(db_manager)
    
    def test_none_parameters(self):
        """Test handling of None parameters"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            db_path = temp_db.name
        
        mock_config = MagicMock()
        mock_config.sqlite_db_path = db_path
        
        with patch('src.core.database.config', mock_config):
            db_manager = DatabaseManager()
            
            # Test with None parameters
            result = db_manager.execute_query("SELECT 1", None)
            self.assertEqual(len(result), 1)
            
            db_manager.close()
        
        os.unlink(db_path)


if __name__ == '__main__':
    unittest.main()
