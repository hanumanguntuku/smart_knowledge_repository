"""
Simple RAG diagnostic script
"""
import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_database():
    """Check SQLite database contents"""
    try:
        db_path = project_root / "data" / "knowledge.db"
        print(f"Checking database at: {db_path}")
        
        if not db_path.exists():
            print("❌ Database file does not exist!")
            return
            
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check documents table
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        print(f"📊 Total documents in database: {doc_count}")
        
        if doc_count > 0:
            # Get document details
            cursor.execute("""
                SELECT id, title, url, domain, status, content_length
                FROM documents 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            docs = cursor.fetchall()
            print("\n📋 Recent documents:")
            for doc in docs:
                doc_id, title, url, domain, status, content_length = doc
                print(f"  - ID: {doc_id}")
                print(f"    Title: {title[:50]}...")
                print(f"    URL: {url}")
                print(f"    Domain: {domain}")
                print(f"    Status: {status}")
                print(f"    Content Length: {content_length}")
                print()
                
        conn.close()
        return doc_count > 0
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_chromadb():
    """Check ChromaDB collections"""
    try:
        chroma_dir = project_root / "data" / "chroma_db"
        print(f"\n🔍 Checking ChromaDB directory: {chroma_dir}")
        
        if not chroma_dir.exists():
            print("❌ ChromaDB directory does not exist!")
            return False
            
        # List files in ChromaDB directory
        for item in chroma_dir.iterdir():
            if item.is_file():
                print(f"  File: {item.name} ({item.stat().st_size} bytes)")
            elif item.is_dir():
                print(f"  Directory: {item.name}/")
                # List collection directories
                for subitem in item.iterdir():
                    if subitem.is_file():
                        print(f"    File: {subitem.name} ({subitem.stat().st_size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB check error: {e}")
        return False

def main():
    print("🔧 Simple RAG Diagnostic")
    print("=" * 40)
    
    # Check database
    has_docs = check_database()
    
    # Check ChromaDB
    has_chroma = check_chromadb()
    
    print(f"\n📋 Summary:")
    print(f"  Documents in SQLite: {'✅' if has_docs else '❌'}")
    print(f"  ChromaDB directory: {'✅' if has_chroma else '❌'}")
    
    if has_docs and not has_chroma:
        print("\n💡 Issue: Documents exist but ChromaDB might be empty")
        print("   This would cause the RAG to return no results")
        
    if not has_docs:
        print("\n💡 Issue: No documents in database")
        print("   You need to scrape some URLs first")

if __name__ == "__main__":
    main()
