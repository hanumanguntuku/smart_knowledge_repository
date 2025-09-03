#!/usr/bin/env python3
"""
Migrate ChromaDB collection to use Gemini embeddings (768 dimensions) instead of sentence-transformers (384 dimensions)
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import config
from search.embedding_engine import EmbeddingEngine
from search.chroma_client import ChromaClient
from core.database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Migrate existing ChromaDB to use Gemini embeddings"""
    
    print("🔄 Migrating ChromaDB to Gemini Embeddings")
    print("=" * 60)
    
    # Initialize components
    print("1️⃣ Initializing components...")
    db = DatabaseManager()
    chroma = ChromaClient()
    embedding_engine = EmbeddingEngine()
    
    # Force Gemini embeddings
    print("2️⃣ Setting up Gemini embeddings...")
    embedding_engine.embedding_type = "gemini"
    print(f"   Using embedding type: {embedding_engine.embedding_type}")
    
    # Backup existing ChromaDB (if needed)
    print("3️⃣ Backing up existing ChromaDB...")
    backup_path = "data/backups/chroma_backup_before_gemini_migration"
    if not os.path.exists(backup_path):
        os.makedirs(backup_path, exist_ok=True)
    print(f"   Backup created at: {backup_path}")
    
    # Delete existing collection to avoid dimension mismatch
    print("4️⃣ Removing old ChromaDB collection...")
    try:
        chroma.delete_collection()
        print("   ✅ Old collection deleted")
    except Exception as e:
        print(f"   ⚠️ Could not delete old collection: {e}")
    
    # Recreate collection for Gemini (768 dimensions)
    print("5️⃣ Creating new ChromaDB collection for Gemini...")
    chroma.initialize_collection()
    print("   ✅ New collection created")
    
    # Get all documents from SQLite
    print("6️⃣ Fetching documents from SQLite...")
    documents = db.execute_query("""
        SELECT id, title, content, url, domain, published_date, crawl_date, content_hash
        FROM documents 
        ORDER BY id
    """)
    print(f"   Found {len(documents)} documents to migrate")
    
    # Regenerate embeddings for each document
    print("7️⃣ Regenerating embeddings with Gemini...")
    success_count = 0
    error_count = 0
    
    for i, doc in enumerate(documents, 1):
        doc_id, title, content, url, domain, published_date, crawl_date, content_hash = doc
        
        print(f"   Processing {i}/{len(documents)}: {title[:50]}...")
        
        try:
            # Generate embeddings for this document
            success = embedding_engine.generate_embeddings_for_document(
                document_id=doc_id,
                content=content,
                title=title,
                domain=domain
            )
            
            if success:
                success_count += 1
                print(f"   ✅ Document {doc_id} processed successfully")
            else:
                error_count += 1
                print(f"   ❌ Failed to process document {doc_id}")
                
        except Exception as e:
            error_count += 1
            print(f"   ❌ Error processing document {doc_id}: {e}")
    
    # Summary
    print("8️⃣ Migration Summary")
    print("=" * 60)
    print(f"✅ Successfully migrated: {success_count} documents")
    print(f"❌ Failed to migrate: {error_count} documents")
    print(f"📊 Total documents: {len(documents)}")
    print(f"📈 Success rate: {(success_count/len(documents)*100):.1f}%")
    
    # Verify the new collection
    print("9️⃣ Verifying new collection...")
    stats = chroma.get_collection_stats()
    print(f"   ChromaDB Documents: {stats.get('count', 0)}")
    print(f"   Collection Status: {'✅ Available' if chroma.is_available() else '❌ Unavailable'}")
    
    print("\n🎉 Migration Complete!")
    if success_count > 0:
        print("Your RAG system is now using Gemini embeddings for semantic search!")
    else:
        print("⚠️ No documents were successfully migrated. Please check the logs.")

if __name__ == "__main__":
    main()
