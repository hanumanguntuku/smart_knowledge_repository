"""
Debug the chatbot's query processing pipeline
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def debug_chatbot_pipeline():
    """Debug each step of the chatbot pipeline"""
    print("🔍 Debugging Chatbot Pipeline")
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
        
        # Step 1: Test domain detection
        print("\n1. Domain Detection:")
        domain_analysis = chatbot.domain_detector.analyze_query(query)
        print(f"   Domain: {domain_analysis['domain']}")
        print(f"   Confidence: {domain_analysis['domain_confidence']}")
        print(f"   Intent: {domain_analysis['intent']}")
        print(f"   Optimized query: {domain_analysis['optimized_query']}")
        
        # Step 2: Test scope analysis
        print("\n2. Scope Analysis:")
        scope_result = chatbot._analyze_query_scope_enhanced(query, domain_analysis)
        print(f"   Scope: {scope_result['scope']}")
        print(f"   Domain: {scope_result['domain']}")
        print(f"   Relevant docs count: {scope_result['relevant_docs_count']}")
        
        # Step 3: Test storage manager search
        print("\n3. Storage Manager Search:")
        storage_results = storage_manager.search_documents(
            query=domain_analysis['optimized_query'],
            limit=5
        )
        print(f"   Storage results: {len(storage_results)}")
        for i, result in enumerate(storage_results[:3], 1):
            print(f"     {i}. {result.get('title', 'No title')}")
        
        # Step 4: Test search engine
        print("\n4. Search Engine:")
        search_results = search_engine.search(
            query=domain_analysis['optimized_query'],
            max_results=5
        )
        print(f"   Search results: {len(search_results)}")
        for i, result in enumerate(search_results[:3], 1):
            print(f"     {i}. {result.get('title', 'No title')}")
            print(f"        Score: {result.get('score', 'No score')}")
        
        # Step 5: Test LLM client
        print("\n5. LLM Client:")
        print(f"   LLM client type: {chatbot.llm_client}")
        if hasattr(chatbot, 'openai_client'):
            print(f"   OpenAI client available: {chatbot.openai_client is not None}")
        
        # Step 6: Full pipeline
        print("\n6. Full Pipeline:")
        try:
            result = chatbot.process_query(query)
            print(f"   Result type: {type(result)}")
            print(f"   Response: {result.get('response', 'No response')[:100]}...")
            print(f"   Sources: {len(result.get('sources', []))}")
            print(f"   Scope: {result.get('scope', 'No scope')}")
        except Exception as e:
            print(f"   Pipeline error: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    debug_chatbot_pipeline()

if __name__ == "__main__":
    main()
