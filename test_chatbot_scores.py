"""
Test the chatbot with detailed score output
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_chatbot_scores():
    """Test chatbot and show detailed score information"""
    print("🤖 Testing Chatbot with Score Details")
    print("=" * 50)
    
    try:
        from src.ai.scope_chatbot import ScopeAwareChatbot
        from src.storage.storage_manager import StorageManager
        from src.search.search_engine import SearchEngine
        
        # Initialize components
        storage_manager = StorageManager()
        search_engine = SearchEngine()
        chatbot = ScopeAwareChatbot(storage_manager, search_engine)
        
        query = "What is artificial intelligence?"
        print(f"Testing query: '{query}'")
        
        # Get the complete response
        result = chatbot.process_query(query)
        
        print(f"\n📝 Response: {result['response'][:200]}...")
        print(f"\n🔍 Scope: {result['scope']}")
        print(f"📊 Confidence: {result.get('confidence', 'N/A')}")
        
        print(f"\n📚 Sources ({len(result.get('sources', []))}):")
        for i, source in enumerate(result.get('sources', []), 1):
            print(f"  {i}. {source.get('title', 'No title')}")
            print(f"     Score: {source.get('score', 'No score'):.4f}")
            print(f"     URL: {source.get('url', 'No URL')}")
            print(f"     Excerpt: {source.get('excerpt', 'No excerpt')[:100]}...")
            print()
        
        knowledge_gaps = result.get('knowledge_gaps', [])
        if knowledge_gaps:
            print(f"⚠️ Knowledge Gaps:")
            for gap in knowledge_gaps:
                print(f"   • {gap}")
        else:
            print("✅ No knowledge gaps detected!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    test_chatbot_scores()

if __name__ == "__main__":
    main()
