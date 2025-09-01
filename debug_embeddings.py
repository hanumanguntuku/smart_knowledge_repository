"""
Debug script to test embedding generation manually
"""
import sys
import os
import logging
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.search.embedding_engine import EmbeddingGenerator
from src.search.chroma_client import chroma_client
from src.core.config import config

def setup_logging():
    """Setup logging for debug script"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_embedding_components():
    """Test each component of the embedding system"""
    print("🔍 Testing Embedding Components\n")
    
    # Test 1: ChromaDB Client
    print("1. Testing ChromaDB Client...")
    print(f"   ChromaDB Available: {chroma_client.is_available()}")
    if chroma_client.is_available():
        stats = chroma_client.get_collection_stats()
        print(f"   Collections: {list(stats.keys())}")
        for domain, stat in stats.items():
            print(f"   - {domain}: {stat}")
    else:
        print("   ❌ ChromaDB not available!")
        return False
    
    # Test 2: Configuration
    print("\n2. Testing Configuration...")
    print(f"   Embedding Model: {config.embedding_model}")
    print(f"   ChromaDB Directory: {config.chroma_persist_directory}")
    print(f"   Use ChromaDB: {config.use_chromadb}")
    print(f"   Use Domain Collections: {config.use_domain_collections}")
    print(f"   Chunk Size: {config.chunk_size}")
    
    # Test 3: Embedding Generator
    print("\n3. Testing Embedding Generator...")
    embedding_gen = EmbeddingGenerator()
    print(f"   Embedding Type: {embedding_gen.embedding_type}")
    print(f"   Model Available: {embedding_gen.model is not None}")
    print(f"   ChromaDB Available: {embedding_gen.chroma.is_available()}")
    
    # Test 4: Generate Test Embedding
    print("\n4. Testing Embedding Generation...")
    test_text = "This is a test document about artificial intelligence and machine learning."
    
    try:
        embedding = embedding_gen._generate_embedding(test_text)
        if embedding is not None:
            print(f"   ✅ Generated embedding with shape: {embedding.shape}")
            return True
        else:
            print("   ❌ Failed to generate embedding")
            return False
    except Exception as e:
        print(f"   ❌ Error generating embedding: {e}")
        return False

def test_document_embedding():
    """Test complete document embedding process"""
    print("\n🧪 Testing Complete Document Embedding Process\n")
    
    embedding_gen = EmbeddingGenerator()
    
    # Test document data
    test_doc_id = 999999  # Use a test ID that won't conflict
    test_content = """
    Artificial Intelligence (AI) is a branch of computer science that aims to create 
    intelligent machines that can perform tasks that typically require human intelligence. 
    These tasks include learning, reasoning, problem-solving, perception, and language understanding.
    
    Machine Learning is a subset of AI that focuses on the development of algorithms and 
    statistical models that enable computers to improve their performance on a specific 
    task through experience without being explicitly programmed.
    
    Deep Learning is a subset of machine learning that uses artificial neural networks 
    with multiple layers to model and understand complex patterns in data.
    """
    
    test_title = "Test Document: Artificial Intelligence Overview"
    test_domain = "technology"
    
    print(f"Test Document ID: {test_doc_id}")
    print(f"Test Title: {test_title}")
    print(f"Test Domain: {test_domain}")
    print(f"Content Length: {len(test_content)} characters")
    
    # Test embedding generation
    try:
        success = embedding_gen.generate_embeddings_for_document(
            document_id=test_doc_id,
            content=test_content,
            title=test_title,
            domain=test_domain
        )
        
        if success:
            print("✅ Document embedding generation successful!")
            
            # Check ChromaDB
            stats = chroma_client.get_collection_stats()
            print(f"\nChromaDB Stats after embedding:")
            for domain, stat in stats.items():
                print(f"   - {domain}: {stat}")
            
            # Test search
            print("\nTesting search for generated embeddings...")
            results = embedding_gen.search_similar_chunks(
                query="machine learning artificial intelligence",
                domain="technology",
                limit=3
            )
            
            print(f"Search Results: {len(results)} found")
            for i, result in enumerate(results, 1):
                print(f"   {i}. Similarity: {result['similarity']:.3f}")
                print(f"      Text preview: {result['chunk_text'][:100]}...")
            
            return True
        else:
            print("❌ Document embedding generation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error in document embedding: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debug function"""
    setup_logging()
    
    print("🚀 ChromaDB Embedding Debug Script")
    print("=" * 50)
    
    # Test components
    component_test = test_embedding_components()
    
    if component_test:
        # Test document embedding
        doc_test = test_document_embedding()
        
        if doc_test:
            print("\n🎉 All tests passed! Embedding system is working correctly.")
        else:
            print("\n❌ Document embedding test failed.")
    else:
        print("\n❌ Component tests failed. Check your setup.")

if __name__ == "__main__":
    main()
