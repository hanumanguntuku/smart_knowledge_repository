"""
Test exact same parameters the chatbot uses
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_exact_chatbot_params():
    """Test with exact same parameters the chatbot scope analysis uses"""
    print("🔍 Testing Exact Chatbot Parameters")
    print("=" * 50)
    
    try:
        from src.storage.storage_manager import StorageManager
        
        storage_manager = StorageManager()
        
        # Simulate what the chatbot does
        query = "What is artificial intelligence?"
        
        # Step 1: Domain analysis (simplified)
        domain = "general"  # This is what we observed
        domain_confidence = 0.0  # This is what we observed
        
        # Step 2: Query optimization (simplified)
        optimized_query = "what is artificial intelligence?"  # lowercase version
        
        # Step 3: Category determination
        category = domain.title() if domain != 'general' else None
        print(f"Original query: '{query}'")
        print(f"Optimized query: '{optimized_query}'")
        print(f"Domain: '{domain}'")
        print(f"Category: {category}")
        
        # Step 4: Call storage manager with exact same params
        print(f"\nCalling storage_manager.search_documents('{optimized_query}', category={category}, limit=5)")
        
        relevant_docs = storage_manager.search_documents(
            optimized_query, 
            category=category, 
            limit=5
        )
        
        print(f"Results: {len(relevant_docs)}")
        for i, doc in enumerate(relevant_docs, 1):
            print(f"  {i}. {doc['title']}")
            print(f"     Relevance: {doc.get('relevance_score', 'No score')}")
        
        # Step 5: Test with different query variations
        print(f"\n" + "=" * 30)
        print("Testing Query Variations:")
        
        test_queries = [
            "artificial intelligence",
            "What is artificial intelligence?",
            "what is artificial intelligence?",
            "AI",
            "artificial",
            "intelligence"
        ]
        
        for test_q in test_queries:
            results = storage_manager.search_documents(test_q, category=None, limit=3)
            print(f"'{test_q}': {len(results)} results")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    test_exact_chatbot_params()

if __name__ == "__main__":
    main()
