"""
Test RAG search functionality after embedding regeneration
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ai.scope_chatbot import ScopeAwareChatbot
from src.search.embedding_engine import EmbeddingGenerator

def test_embedding_search():
    """Test embedding search directly"""
    print("🔍 Testing Embedding Search")
    print("=" * 50)
    
    embedding_gen = EmbeddingGenerator()
    
    test_queries = [
        "What is artificial intelligence?",
        "machine learning algorithms",
        "neural networks deep learning",
        "AI applications",
        "computer science technology"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        
        # Search across domains
        for domain in ['general', 'technology']:
            try:
                results = embedding_gen.search_similar_chunks(
                    query=query,
                    domain=domain,
                    limit=3
                )
                
                print(f"  📁 {domain} domain: {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"    {i}. Similarity: {result['similarity']:.3f}")
                    print(f"       Doc ID: {result.get('document_id', 'Unknown')}")
                    print(f"       Text: {result['chunk_text'][:100]}...")
                    
            except Exception as e:
                print(f"  ❌ Error in {domain}: {e}")

def test_chatbot_responses():
    """Test the complete RAG chatbot"""
    print("\n🤖 Testing RAG Chatbot")
    print("=" * 50)
    
    try:
        chatbot = ScopeAwareChatbot()
        
        test_queries = [
            "What is artificial intelligence?",
            "Tell me about machine learning",
            "How does deep learning work?",
            "What are AI applications?",
            "Explain neural networks"
        ]
        
        for query in test_queries:
            print(f"\n❓ Question: {query}")
            try:
                response = chatbot.get_response(query)
                print(f"🤖 Response: {response}")
                print()
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")

def main():
    print("🚀 RAG Functionality Test")
    print("=" * 50)
    
    # Test embedding search
    test_embedding_search()
    
    # Test chatbot responses
    test_chatbot_responses()

if __name__ == "__main__":
    main()
