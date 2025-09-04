"""
Tests for search engine functionality
"""
import unittest
from src.search.search_engine import SearchEngine
from src.storage.storage_manager import StorageManager


class TestSearchEngine(unittest.TestCase):
    """Test cases for SearchEngine"""
    
    def setUp(self):
        """Set up test environment"""
        self.search_engine = SearchEngine()
        self.search_engine.logger.disabled = True
    
    def test_clean_query(self):
        """Test query cleaning functionality"""
        query = "What is AI???"
        clean_query = self.search_engine._clean_query(query)
        
        self.assertEqual(clean_query, "what is ai")
    
    def test_empty_query(self):
        """Test search with empty query"""
        results = self.search_engine.search("")
        
        self.assertEqual(len(results), 0)
    
    def test_text_match_score(self):
        """Test text matching score calculation"""
        query_terms = {"machine", "learning"}
        text = "machine learning is a subset of artificial intelligence"
        
        score = self.search_engine._calculate_text_match_score(query_terms, text)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1.0)
    
    def test_quality_score(self):
        """Test document quality score calculation"""
        document = {
            'title': 'A Well Written Article',
            'word_count': 500,
            'domain': 'wikipedia.org'
        }
        
        score = self.search_engine._calculate_quality_score(document)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1.0)


if __name__ == '__main__':
    unittest.main()
