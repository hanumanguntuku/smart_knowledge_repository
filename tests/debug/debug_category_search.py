"""
Debug category filtering in storage manager search
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def debug_category_search():
    """Test storage manager search with different category filters"""
    print("🔍 Debugging Category Search")
    print("=" * 50)
    
    try:
        from src.storage.storage_manager import StorageManager
        
        storage_manager = StorageManager()
        query = "artificial intelligence"
        
        print(f"Testing query: '{query}'")
        
        # Test 1: No category filter
        print("\n1. Search with NO category filter:")
        results_no_cat = storage_manager.search_documents(query, category=None, limit=5)
        print(f"   Results: {len(results_no_cat)}")
        for result in results_no_cat:
            print(f"     - {result['title']}")
        
        # Test 2: General category filter
        print("\n2. Search with category='General':")
        results_general = storage_manager.search_documents(query, category="General", limit=5)
        print(f"   Results: {len(results_general)}")
        for result in results_general:
            print(f"     - {result['title']}")
        
        # Test 3: Technology category filter
        print("\n3. Search with category='Technology':")
        results_tech = storage_manager.search_documents(query, category="Technology", limit=5)
        print(f"   Results: {len(results_tech)}")
        for result in results_tech:
            print(f"     - {result['title']}")
        
        # Test 4: Check available categories
        print("\n4. Available categories in database:")
        from src.core.database import db
        categories = db.execute_query("SELECT * FROM categories")
        for cat in categories:
            print(f"     - {cat['name']} (id: {cat['id']})")
        
        # Test 5: Test with optimized query from domain detector
        print("\n5. Testing with domain analysis:")
        from src.ai.scope_chatbot import DomainDetector
        domain_detector = DomainDetector()
        query_analysis = domain_detector.analyze_query("What is artificial intelligence?")
        print(f"   Domain: {query_analysis['domain']}")
        print(f"   Optimized query: {query_analysis['optimized_query']}")
        
        # Use the actual logic from scope analysis
        category = query_analysis['domain'].title() if query_analysis['domain'] != 'general' else None
        print(f"   Category for search: {category}")
        
        scope_results = storage_manager.search_documents(
            query_analysis['optimized_query'], 
            category=category, 
            limit=5
        )
        print(f"   Scope analysis results: {len(scope_results)}")
        for result in scope_results:
            print(f"     - {result['title']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    debug_category_search()

if __name__ == "__main__":
    main()
