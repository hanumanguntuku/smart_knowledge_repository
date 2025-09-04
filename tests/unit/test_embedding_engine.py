"""
Unit tests for embedding engine
"""
import unittest
import numpy as np
from unittest.mock import patch, MagicMock, Mock
import tempfile
import os

from src.search.embedding_engine import EmbeddingEngine


class TestEmbeddingEngine(unittest.TestCase):
    """Test cases for EmbeddingEngine"""
    
    def setUp(self):
        """Set up test environment"""
        self.embedding_engine = EmbeddingEngine()
        # Disable logging for tests
        self.embedding_engine.logger.disabled = True
    
    def test_initialization(self):
        """Test embedding engine initialization"""
        self.assertIsNotNone(self.embedding_engine)
        self.assertIsNotNone(self.embedding_engine.model)
        
    def test_generate_embeddings_basic(self):
        """Test basic embedding generation"""
        test_texts = ["This is a test document", "Another test document"]
        
        embeddings = self.embedding_engine.generate_embeddings(test_texts)
        
        # Should return embeddings for each text
        self.assertEqual(len(embeddings), len(test_texts))
        
        # Each embedding should be a numpy array
        for embedding in embeddings:
            self.assertIsInstance(embedding, np.ndarray)
            # sentence-transformers all-MiniLM-L6-v2 produces 384-dimensional embeddings
            self.assertEqual(len(embedding), 384)
    
    def test_generate_embeddings_single_text(self):
        """Test embedding generation for single text"""
        test_text = "Single test document"
        
        embeddings = self.embedding_engine.generate_embeddings([test_text])
        
        self.assertEqual(len(embeddings), 1)
        self.assertIsInstance(embeddings[0], np.ndarray)
        self.assertEqual(len(embeddings[0]), 384)
    
    def test_generate_embeddings_empty_list(self):
        """Test embedding generation for empty list"""
        embeddings = self.embedding_engine.generate_embeddings([])
        
        self.assertEqual(len(embeddings), 0)
        self.assertIsInstance(embeddings, list)
    
    def test_generate_embeddings_none_input(self):
        """Test embedding generation with None input"""
        embeddings = self.embedding_engine.generate_embeddings(None)
        
        self.assertEqual(len(embeddings), 0)
        self.assertIsInstance(embeddings, list)
    
    def test_generate_embeddings_empty_strings(self):
        """Test embedding generation with empty strings"""
        test_texts = ["", " ", "   "]
        
        embeddings = self.embedding_engine.generate_embeddings(test_texts)
        
        # Should still generate embeddings, even for empty/whitespace strings
        self.assertEqual(len(embeddings), len(test_texts))
        for embedding in embeddings:
            self.assertIsInstance(embedding, np.ndarray)
            self.assertEqual(len(embedding), 384)
    
    def test_generate_single_embedding(self):
        """Test single embedding generation"""
        test_text = "Test document for single embedding"
        
        embedding = self.embedding_engine.generate_single_embedding(test_text)
        
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(len(embedding), 384)
    
    def test_generate_single_embedding_empty(self):
        """Test single embedding generation with empty text"""
        embedding = self.embedding_engine.generate_single_embedding("")
        
        # Should still return an embedding
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(len(embedding), 384)
    
    def test_similarity_calculation(self):
        """Test similarity calculation between embeddings"""
        text1 = "artificial intelligence machine learning"
        text2 = "AI and ML technologies"
        text3 = "cooking recipes and food"
        
        emb1 = self.embedding_engine.generate_single_embedding(text1)
        emb2 = self.embedding_engine.generate_single_embedding(text2)
        emb3 = self.embedding_engine.generate_single_embedding(text3)
        
        # Calculate cosine similarities
        sim_1_2 = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        sim_1_3 = np.dot(emb1, emb3) / (np.linalg.norm(emb1) * np.linalg.norm(emb3))
        
        # Similar texts should have higher similarity than dissimilar texts
        self.assertGreater(sim_1_2, sim_1_3)
        
        # Similarities should be between -1 and 1
        self.assertGreaterEqual(sim_1_2, -1)
        self.assertLessEqual(sim_1_2, 1)
        self.assertGreaterEqual(sim_1_3, -1)
        self.assertLessEqual(sim_1_3, 1)
    
    def test_batch_processing(self):
        """Test batch processing of multiple texts"""
        # Generate a larger batch of texts
        test_texts = [f"Test document number {i}" for i in range(50)]
        
        embeddings = self.embedding_engine.generate_embeddings(test_texts)
        
        self.assertEqual(len(embeddings), 50)
        for embedding in embeddings:
            self.assertIsInstance(embedding, np.ndarray)
            self.assertEqual(len(embedding), 384)
    
    def test_consistency(self):
        """Test that same text produces same embeddings"""
        test_text = "Consistency test document"
        
        embedding1 = self.embedding_engine.generate_single_embedding(test_text)
        embedding2 = self.embedding_engine.generate_single_embedding(test_text)
        
        # Should be exactly the same (or very close due to floating point precision)
        np.testing.assert_array_almost_equal(embedding1, embedding2, decimal=6)
    
    @patch('src.search.embedding_engine.SentenceTransformer')
    def test_model_loading_error(self, mock_sentence_transformer):
        """Test handling of model loading errors"""
        # Make the model initialization fail
        mock_sentence_transformer.side_effect = Exception("Model loading failed")
        
        # Should handle the error gracefully
        with self.assertLogs(level='ERROR'):
            engine = EmbeddingEngine()
            self.assertIsNone(engine.model)
    
    def test_special_characters(self):
        """Test embedding generation with special characters"""
        test_texts = [
            "Text with émojis 🚀 and spëcial chars",
            "Math symbols: ∑ ∫ ∂ ∆",
            "Mixed: Hello 世界! Здравствуй мир!",
            "Symbols: @#$%^&*()_+-=[]{}|;':\",./<>?"
        ]
        
        embeddings = self.embedding_engine.generate_embeddings(test_texts)
        
        self.assertEqual(len(embeddings), len(test_texts))
        for embedding in embeddings:
            self.assertIsInstance(embedding, np.ndarray)
            self.assertEqual(len(embedding), 384)
    
    def test_very_long_text(self):
        """Test embedding generation with very long text"""
        # Create a very long text (longer than typical model limits)
        long_text = "This is a very long text. " * 1000  # ~25,000 characters
        
        embedding = self.embedding_engine.generate_single_embedding(long_text)
        
        # Should still work (model will likely truncate)
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(len(embedding), 384)
    
    def test_unicode_handling(self):
        """Test Unicode text handling"""
        unicode_texts = [
            "Chinese: 你好世界",
            "Arabic: مرحبا بالعالم",
            "Russian: Привет мир",
            "Japanese: こんにちは世界",
            "Emoji: 🌍🌎🌏 Hello World! 👋"
        ]
        
        embeddings = self.embedding_engine.generate_embeddings(unicode_texts)
        
        self.assertEqual(len(embeddings), len(unicode_texts))
        for embedding in embeddings:
            self.assertIsInstance(embedding, np.ndarray)
            self.assertEqual(len(embedding), 384)


class TestEmbeddingEngineIntegration(unittest.TestCase):
    """Integration tests for EmbeddingEngine"""
    
    def setUp(self):
        """Set up test environment"""
        self.embedding_engine = EmbeddingEngine()
        self.embedding_engine.logger.disabled = True
    
    def test_semantic_similarity_detection(self):
        """Test that semantically similar texts have higher similarity"""
        # Pairs of similar texts
        similar_pairs = [
            ("dog", "puppy"),
            ("car", "automobile"),
            ("happy", "joyful"),
            ("big", "large"),
            ("fast", "quick")
        ]
        
        # Dissimilar text
        dissimilar_text = "mathematics equation"
        
        for text1, text2 in similar_pairs:
            with self.subTest(pair=(text1, text2)):
                emb1 = self.embedding_engine.generate_single_embedding(text1)
                emb2 = self.embedding_engine.generate_single_embedding(text2)
                emb_dissimilar = self.embedding_engine.generate_single_embedding(dissimilar_text)
                
                # Calculate similarities
                sim_similar = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                sim_dissimilar = np.dot(emb1, emb_dissimilar) / (np.linalg.norm(emb1) * np.linalg.norm(emb_dissimilar))
                
                # Similar texts should have higher similarity
                self.assertGreater(sim_similar, sim_dissimilar)
    
    def test_domain_specific_similarities(self):
        """Test similarities in specific domains"""
        tech_texts = [
            "artificial intelligence and machine learning",
            "neural networks and deep learning",
            "computer programming and software development"
        ]
        
        business_texts = [
            "marketing strategy and sales growth",
            "financial planning and budget management", 
            "human resources and employee management"
        ]
        
        tech_embeddings = self.embedding_engine.generate_embeddings(tech_texts)
        business_embeddings = self.embedding_engine.generate_embeddings(business_texts)
        
        # Calculate average similarity within domains
        tech_similarities = []
        for i in range(len(tech_embeddings)):
            for j in range(i+1, len(tech_embeddings)):
                sim = np.dot(tech_embeddings[i], tech_embeddings[j]) / (
                    np.linalg.norm(tech_embeddings[i]) * np.linalg.norm(tech_embeddings[j])
                )
                tech_similarities.append(sim)
        
        # Calculate similarity across domains
        cross_similarities = []
        for tech_emb in tech_embeddings:
            for business_emb in business_embeddings:
                sim = np.dot(tech_emb, business_emb) / (
                    np.linalg.norm(tech_emb) * np.linalg.norm(business_emb)
                )
                cross_similarities.append(sim)
        
        avg_within_domain = np.mean(tech_similarities)
        avg_cross_domain = np.mean(cross_similarities)
        
        # Within-domain similarity should be higher than cross-domain
        self.assertGreater(avg_within_domain, avg_cross_domain)


if __name__ == '__main__':
    unittest.main()
