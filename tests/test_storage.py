"""
Tests for storage manager functionality
"""
import unittest
import tempfile
import os
from src.storage.storage_manager import StorageManager
from src.core.database import DatabaseManager


class TestStorageManager(unittest.TestCase):
    """Test cases for StorageManager"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize test database
        self.db_manager = DatabaseManager(self.db_path)
        self.storage_manager = StorageManager()
        # Override the database path for testing
        self.storage_manager.validator.logger.disabled = True
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_store_valid_document(self):
        """Test storing a valid document"""
        doc_data = {
            'title': 'Test Document',
            'url': 'https://example.com/test',
            'content': 'This is a test document with enough content to pass validation.',
            'metadata': {'test': True}
        }
        
        success, message, doc_id = self.storage_manager.store_document(doc_data)
        
        self.assertTrue(success)
        self.assertIsNotNone(doc_id)
        self.assertIn("success", message.lower())
    
    def test_store_invalid_document(self):
        """Test storing an invalid document"""
        doc_data = {
            'title': '',  # Invalid empty title
            'url': 'invalid-url',  # Invalid URL
            'content': 'Short'  # Too short content
        }
        
        success, message, doc_id = self.storage_manager.store_document(doc_data)
        
        self.assertFalse(success)
        self.assertIsNone(doc_id)
        self.assertIn("validation failed", message.lower())
    
    def test_search_documents(self):
        """Test document search functionality"""
        # First store a test document
        doc_data = {
            'title': 'Machine Learning Guide',
            'url': 'https://example.com/ml-guide',
            'content': 'This is a comprehensive guide about machine learning algorithms and techniques.',
            'metadata': {}
        }
        
        self.storage_manager.store_document(doc_data)
        
        # Search for the document
        results = self.storage_manager.search_documents('machine learning')
        
        self.assertGreater(len(results), 0)
        self.assertIn('machine learning', results[0]['title'].lower())
    
    def test_get_categories(self):
        """Test getting categories"""
        categories = self.storage_manager.get_categories()
        
        # Should have default categories
        self.assertGreater(len(categories), 0)
        category_names = [cat['name'] for cat in categories]
        self.assertIn('Technology', category_names)
    
    def test_duplicate_detection(self):
        """Test duplicate document detection"""
        doc_data = {
            'title': 'Duplicate Test',
            'url': 'https://example.com/duplicate',
            'content': 'This is a test document for duplicate detection functionality.',
            'metadata': {}
        }
        
        # Store document first time
        success1, message1, doc_id1 = self.storage_manager.store_document(doc_data)
        self.assertTrue(success1)
        
        # Try to store same document again
        success2, message2, doc_id2 = self.storage_manager.store_document(doc_data)
        self.assertFalse(success2)
        self.assertIn("already exists", message2.lower())


if __name__ == '__main__':
    unittest.main()
