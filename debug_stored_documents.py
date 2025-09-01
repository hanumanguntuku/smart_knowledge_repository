"""
Debug what's actually stored in the database
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_stored_documents():
    """Check what's actually in the database"""
    print("🗃️ Debugging Stored Documents")
    print("=" * 50)
    
    try:
        from src.core.database import db
        
        # Get all documents
        query = """
            SELECT d.id, d.title, d.url, d.status,
                   SUBSTR(d.content, 1, 100) as content_preview,
                   (SELECT GROUP_CONCAT(c.name) 
                    FROM document_categories dc 
                    JOIN categories c ON dc.category_id = c.id 
                    WHERE dc.document_id = d.id) as categories
            FROM documents d
            ORDER BY d.created_at DESC
        """
        
        documents = db.execute_query(query)
        print(f"Total documents in database: {len(documents)}")
        
        for doc in documents:
            print(f"\nDocument ID: {doc['id']}")
            print(f"Title: {doc['title']}")
            print(f"URL: {doc['url']}")
            print(f"Status: {doc['status']}")
            print(f"Categories: {doc.get('categories', 'None')}")
            print(f"Content preview: {doc.get('content_preview', 'No content')}")
            
        # Test keyword search with different patterns
        print("\n" + "=" * 50)
        print("Testing Keyword Search Patterns:")
        
        test_queries = [
            "artificial intelligence",
            "artificial",
            "intelligence", 
            "AI",
            "machine learning",
            "Wikipedia"
        ]
        
        for test_query in test_queries:
            search_term = f"%{test_query}%"
            sql_query = """
                SELECT d.id, d.title,
                       (CASE 
                        WHEN d.title LIKE ? THEN 3
                        WHEN d.content LIKE ? THEN 1
                        ELSE 0 
                       END) as relevance_score
                FROM documents d
                WHERE (d.title LIKE ? OR d.content LIKE ?) 
                AND d.status = 'active'
                ORDER BY relevance_score DESC
                LIMIT 3
            """
            params = (search_term, search_term, search_term, search_term)
            results = db.execute_query(sql_query, params)
            print(f"\nQuery '{test_query}': {len(results)} results")
            for result in results:
                print(f"  - {result['title']} (score: {result['relevance_score']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    debug_stored_documents()

if __name__ == "__main__":
    main()
