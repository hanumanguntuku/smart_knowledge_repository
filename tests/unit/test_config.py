"""
Unit tests for core configuration module
"""
import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.config import Settings, load_config, config


class TestSettings(unittest.TestCase):
    """Test cases for Settings class"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_default_settings(self):
        """Test default configuration values"""
        settings = Settings()
        
        # Test defaults
        self.assertEqual(settings.app_name, "Smart Knowledge Repository")
        self.assertEqual(settings.app_version, "1.0.0")
        self.assertFalse(settings.debug)
        self.assertEqual(settings.sqlite_db_path, "data/knowledge.db")
        self.assertEqual(settings.embedding_model, "all-MiniLM-L6-v2")
        self.assertEqual(settings.chunk_size, 500)
        self.assertEqual(settings.chunk_overlap, 50)
    
    def test_environment_override(self):
        """Test environment variable overrides"""
        # Set environment variables
        os.environ["APP_NAME"] = "Test Repository"
        os.environ["DEBUG"] = "true"
        os.environ["SQLITE_DB_PATH"] = "/tmp/test.db"
        os.environ["CHUNK_SIZE"] = "1000"
        
        settings = Settings()
        
        # Test overrides
        self.assertEqual(settings.app_name, "Test Repository")
        self.assertTrue(settings.debug)
        self.assertEqual(settings.sqlite_db_path, "/tmp/test.db")
        self.assertEqual(settings.chunk_size, 1000)
    
    def test_boolean_conversion(self):
        """Test boolean environment variable conversion"""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("1", False),  # Non-true values are false
            ("", False)
        ]
        
        for env_value, expected in test_cases:
            with self.subTest(env_value=env_value):
                os.environ["DEBUG"] = env_value
                settings = Settings()
                self.assertEqual(settings.debug, expected)
    
    def test_integer_conversion(self):
        """Test integer environment variable conversion"""
        os.environ["CHUNK_SIZE"] = "750"
        os.environ["CHUNK_OVERLAP"] = "25"
        
        settings = Settings()
        
        self.assertEqual(settings.chunk_size, 750)
        self.assertEqual(settings.chunk_overlap, 25)
    
    def test_invalid_integer_fallback(self):
        """Test integer fallback for invalid values"""
        os.environ["CHUNK_SIZE"] = "invalid"
        
        settings = Settings()
        
        # Should fall back to default
        self.assertEqual(settings.chunk_size, 500)
    
    def test_knowledge_domains(self):
        """Test knowledge domains configuration"""
        settings = Settings()
        
        # Test that knowledge domains are properly configured
        self.assertIsInstance(settings.knowledge_domains, dict)
        self.assertIn("technology", settings.knowledge_domains)
        self.assertIn("business", settings.knowledge_domains)
        self.assertIn("science", settings.knowledge_domains)
        
        # Test that domains contain keyword lists
        for domain, keywords in settings.knowledge_domains.items():
            self.assertIsInstance(keywords, list)
            self.assertGreater(len(keywords), 0)
    
    def test_create_directories(self):
        """Test directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "test_db.db"
            
            os.environ["SQLITE_DB_PATH"] = str(test_path)
            
            settings = Settings()
            settings.create_directories()
            
            # Directory should be created
            self.assertTrue(test_path.parent.exists())
    
    @patch('src.core.config.load_dotenv')
    def test_dotenv_loading(self, mock_load_dotenv):
        """Test .env file loading"""
        # Test that load_dotenv is called
        Settings()
        mock_load_dotenv.assert_called_once()
    
    def test_load_config_function(self):
        """Test load_config function"""
        config_instance = load_config()
        
        self.assertIsInstance(config_instance, Settings)
        self.assertEqual(config_instance.app_name, "Smart Knowledge Repository")
    
    def test_global_config_instance(self):
        """Test global config instance"""
        self.assertIsInstance(config, Settings)
        self.assertEqual(config.app_name, "Smart Knowledge Repository")


class TestConfigEnvironmentHandling(unittest.TestCase):
    """Test environment handling edge cases"""
    
    def test_missing_dotenv_import(self):
        """Test graceful handling when python-dotenv is not available"""
        with patch('src.core.config.load_dotenv', side_effect=ImportError):
            # Should not raise an exception
            settings = Settings()
            self.assertIsInstance(settings, Settings)
    
    def test_openai_configuration(self):
        """Test OpenAI configuration"""
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["OPENAI_MODEL"] = "gpt-4"
        
        settings = Settings()
        
        # These might be accessed through the config
        self.assertTrue(hasattr(settings, 'app_name'))  # Basic test that it loads
    
    def test_chroma_configuration(self):
        """Test ChromaDB configuration"""
        settings = Settings()
        
        # Test that basic chroma settings exist
        self.assertTrue(hasattr(settings, 'chunk_size'))
        self.assertTrue(hasattr(settings, 'embedding_model'))


if __name__ == '__main__':
    unittest.main()
