"""
Regenerate embeddings for existing documents
"""
import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.search.embedding_engine import EmbeddingGenerator
from src.core.database import DatabaseManager

def regenerate_embeddings_for_document(doc_id: int):
    """Regenerate embeddings for a specific document"""
    print(f"🔄 Regenerating embeddings for document {doc_id}")
    
    try:
        # Get document from database
        db = DatabaseManager()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, content, domain 
                FROM documents 
                WHERE id = ?
            """, (doc_id,))
            
            doc = cursor.fetchone()
            
        if not doc:
            print(f"❌ Document {doc_id} not found in database")
            return False
            
        doc_id, title, content, domain = doc
        print(f"   Title: {title[:100]}...")
        print(f"   Domain: {domain}")
        print(f"   Content length: {len(content)} characters")
        
        # Generate embeddings
        embedding_gen = EmbeddingGenerator()
        
        success = embedding_gen.generate_embeddings_for_document(
            document_id=doc_id,
            content=content,
            title=title,
            domain=domain
        )
        
        if success:
            print(f"✅ Successfully generated embeddings for document {doc_id}")
            return True
        else:
            print(f"❌ Failed to generate embeddings for document {doc_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error regenerating embeddings for document {doc_id}: {e}")
        return False

def regenerate_all_missing_embeddings():
    """Find and regenerate embeddings for all documents missing them"""
    print("🔍 Finding documents missing embeddings")
    
    try:
        # Get all documents from database
        db = DatabaseManager()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, domain 
                FROM documents 
                ORDER BY id
            """)
            
            docs = cursor.fetchall()
            
        print(f"Found {len(docs)} total documents")
        
        # Check which ones have embeddings in ChromaDB
        from src.search.chroma_client import chroma_client
        
        # Get all embedding document IDs from ChromaDB
        embedding_doc_ids = set()
        stats = chroma_client.get_collection_stats()
        
        for domain, stat in stats.items():
            if stat['document_count'] > 0:
                collection = chroma_client.get_collection_for_domain(domain)
                if collection:
                    results = collection.get(limit=stat['document_count'])
                    for metadata in results['metadatas']:
                        if metadata and 'document_id' in metadata:
                            embedding_doc_ids.add(metadata['document_id'])
        
        print(f"Documents with embeddings: {sorted(embedding_doc_ids)}")
        
        # Find missing embeddings
        missing_embeddings = []
        for doc_id, title, domain in docs:
            if doc_id not in embedding_doc_ids:
                missing_embeddings.append((doc_id, title, domain))
                
        print(f"Documents missing embeddings: {len(missing_embeddings)}")
        
        if missing_embeddings:
            for doc_id, title, domain in missing_embeddings:
                print(f"  - Document {doc_id}: {title[:50]}... (domain: {domain})")
                
            # Ask user to proceed
            print(f"\n🚀 Regenerating embeddings for {len(missing_embeddings)} documents...")
            
            success_count = 0
            for doc_id, title, domain in missing_embeddings:
                if regenerate_embeddings_for_document(doc_id):
                    success_count += 1
                    
            print(f"\n✅ Successfully regenerated embeddings for {success_count}/{len(missing_embeddings)} documents")
            
        else:
            print("✅ All documents already have embeddings")
            
    except Exception as e:
        print(f"❌ Error in regenerate_all_missing_embeddings: {e}")

def main():
    print("🔧 Embedding Regeneration Tool")
    print("=" * 50)
    
    regenerate_all_missing_embeddings()
    
    print("\n🔍 Final ChromaDB Stats:")
    from src.search.chroma_client import chroma_client
    stats = chroma_client.get_collection_stats()
    for domain, stat in stats.items():
        if stat['document_count'] > 0:
            print(f"  {domain}: {stat['document_count']} documents")

if __name__ == "__main__":
    main()
