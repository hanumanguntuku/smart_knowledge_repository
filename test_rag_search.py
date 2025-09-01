"""
Test script to debug RAG search functionality
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.search.chroma_client import chroma_client
from src.search.embedding_engine import EmbeddingGenerator
from src.ai.scope_chatbot import ScopeChatbot
from src.core.database import DatabaseManager

def test_chromadb_contents():
    """Check what's actually stored in ChromaDB"""
    print("🔍 Testing ChromaDB Contents")
    print("=" * 50)
    
    if not chroma_client.is_available():
        print("❌ ChromaDB not available!")
        return False
    
    # Get collection stats
    stats = chroma_client.get_collection_stats()
    print("Collection Stats:")
    for domain, stat in stats.items():
        print(f"  - {domain}: {stat['document_count']} documents")
        
        # Get actual data from collection
        if stat['document_count'] > 0:
            print(f"    Checking {domain} collection contents...")
            try:
                # Get collection
                collection = chroma_client.get_collection(domain)
                
                # Get all documents in collection
                results = collection.get(limit=10)  # Get first 10 documents
                
                print(f"    Collection has {len(results['ids'])} entries:")
                for i, (doc_id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents'])):
                    print(f"      {i+1}. ID: {doc_id}")
                    print(f"         Metadata: {metadata}")
                    print(f"         Text preview: {document[:100]}...")
                    print()
                    
            except Exception as e:
                print(f"    Error accessing {domain} collection: {e}")
    
    return True

def test_database_documents():
    """Check what documents are in the SQLite database"""
    print("\n📊 Testing SQLite Database Contents")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        
        # Get all documents
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, url, domain, created_at, content_length, status 
                FROM documents 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            docs = cursor.fetchall()
            
        print(f"Found {len(docs)} documents in SQLite:")
        for doc in docs:
            doc_id, title, url, domain, created_at, content_length, status = doc
            print(f"  - ID: {doc_id}")
            print(f"    Title: {title}")
            print(f"    URL: {url}")
            print(f"    Domain: {domain}")
            print(f"    Status: {status}")
            print(f"    Content Length: {content_length}")
            print(f"    Created: {created_at}")
            print()
            
        return docs
        
    except Exception as e:
        print(f"Error accessing database: {e}")
        return []

def test_embedding_search():
    """Test the embedding search functionality"""
    print("\n🔍 Testing Embedding Search")
    print("=" * 50)
    
    try:
        embedding_gen = EmbeddingGenerator()
        
        # Test queries
        test_queries = [
            "artificial intelligence",
            "machine learning",
            "AI technology",
            "neural networks",
            "computer science"
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            
            # Search in all domains
            for domain in ['technology', 'general', 'science']:
                try:
                    results = embedding_gen.search_similar_chunks(
                        query=query,
                        domain=domain,
                        limit=3
                    )
                    
                    print(f"  {domain} domain: {len(results)} results")
                    for i, result in enumerate(results, 1):
                        print(f"    {i}. Similarity: {result['similarity']:.3f}")
                        print(f"       Text: {result['chunk_text'][:100]}...")
                        
                except Exception as e:
                    print(f"  {domain} domain: Error - {e}")
                    
    except Exception as e:
        print(f"Error in embedding search: {e}")

def test_chatbot_response():
    """Test the chatbot RAG response"""
    print("\n🤖 Testing Chatbot RAG Response")
    print("=" * 50)
    
    try:
        chatbot = ScopeChatbot()
        
        test_queries = [
            "What is artificial intelligence?",
            "Tell me about machine learning",
            "Explain AI technology"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            try:
                response = chatbot.get_response(query)
                print(f"Response: {response}")
                print()
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Error initializing chatbot: {e}")

def main():
    """Run all tests"""
    print("🚀 RAG System Debug Test")
    print("=" * 50)
    
    # Test ChromaDB contents
    chromadb_ok = test_chromadb_contents()
    
    # Test SQLite database
    docs = test_database_documents()
    
    if chromadb_ok and docs:
        # Test embedding search
        test_embedding_search()
        
        # Test chatbot
        test_chatbot_response()
    else:
        print("❌ Basic storage tests failed. Cannot proceed with search tests.")

if __name__ == "__main__":
    main()
