"""
Database management module for Smart Knowledge Repository
"""
import sqlite3
import json
import logging
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from .config import config


class DatabaseManager:
    """Database manager for SQLite operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.sqlite_db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Execute schema
        with self.get_connection() as conn:
            schema_path = "schemas/database_schema.sql"
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
                self.logger.info("Database initialized successfully")
            else:
                self.logger.warning(f"Schema file not found: {schema_path}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results as dictionaries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Execute insert query and return last row id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute update/delete query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount


# Global database instance
db = DatabaseManager()
