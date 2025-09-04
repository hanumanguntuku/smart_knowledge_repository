"""
Simple test to verify the chatbot works with the Streamlit interface
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_chatbot_simple():
    """Test the chatbot with simple initialization"""
    print("🤖 Testing Chatbot with Streamlit Interface")
    print("=" * 50)
    
    try:
        from src.ai.scope_chatbot import ScopeAwareChatbot
        from src.storage.storage_manager import StorageManager
        from src.search.search_engine import SearchEngine
        
        # Initialize components like Streamlit does
        print("Initializing components...")
        storage_manager = StorageManager()
        search_engine = SearchEngine()
        chatbot = ScopeAwareChatbot(storage_manager, search_engine)
        
        print("✅ Chatbot initialized successfully")
        
        # Test queries
        test_queries = [
            "What is artificial intelligence?",
            "Tell me about machine learning",
            "How does AI work?",
            "Explain deep learning"
        ]
        
        for query in test_queries:
            print(f"\n🔎 Testing: '{query}'")
            try:
                response = chatbot.get_response(query)
                print(f"✅ Response received ({len(response)} characters)")
                print(f"Preview: {response[:150]}..." if len(response) > 150 else response)
                
                if "I don't have information" in response:
                    print("⚠️  Generic 'no information' response - this suggests search isn't finding documents")
                else:
                    print("✅ Custom response generated - RAG is working!")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_search_results():
    """Debug the search engine to see what it's finding"""
    print("\n🔍 Debugging Search Engine")
    print("=" * 50)
    
    try:
        from src.search.search_engine import SearchEngine
        
        search_engine = SearchEngine()
        
        test_query = "artificial intelligence"
        print(f"Testing search for: '{test_query}'")
        
        results = search_engine.search(
            query=test_query,
            max_results=5
        )
        
        print(f"Search returned {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Title: {result.get('title', 'No title')}")
            print(f"     Score: {result.get('score', 'No score')}")
            print(f"     Content preview: {result.get('content', '')[:100]}...")
            print()
            
        if not results:
            print("❌ No search results found - this explains the generic responses")
            print("💡 Check if embeddings exist and search is working")
        else:
            print("✅ Search is finding documents")
            
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Search engine error: {e}")
        return False

def main():
    """Run complete test"""
    print("🚀 Complete RAG Chatbot Test")
    print("=" * 50)
    
    # Test search first
    search_works = debug_search_results()
    
    # Test chatbot
    chatbot_works = test_chatbot_simple()
    
    print("\n📋 Diagnosis:")
    print(f"  Search Engine: {'✅ Working' if search_works else '❌ Issues'}")
    print(f"  Chatbot: {'✅ Working' if chatbot_works else '❌ Issues'}")
    
    if not search_works:
        print("\n💡 Recommendation:")
        print("  The issue is likely that search isn't finding your documents.")
        print("  This causes the chatbot to give generic 'no information' responses.")
        print("  Check if:")
        print("    1. Documents are in the database")
        print("    2. Embeddings exist in ChromaDB")
        print("    3. Search configuration is correct")

if __name__ == "__main__":
    main()
