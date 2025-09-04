"""
ChromaDB Migration and Management Script
Migrate existing SQLite embeddings to ChromaDB and manage vector storage
"""
import sys
import os
import logging
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.search.embedding_engine import EmbeddingGenerator
from src.search.chroma_client import chroma_client
from src.core.config import config


def setup_logging():
    """Setup logging for migration script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/chromadb_migration.log')
        ]
    )


def check_chromadb_status():
    """Check ChromaDB installation and availability"""
    print("🔍 Checking ChromaDB Status...")
    
    if chroma_client.is_available():
        print("✅ ChromaDB is available and running")
        stats = chroma_client.get_collection_stats()
        print(f"📊 Collections: {list(stats.keys())}")
        for domain, stat in stats.items():
            print(f"   - {domain}: {stat.get('document_count', 0)} embeddings")
        return True
    else:
        print("❌ ChromaDB is not available")
        return False


def migrate_sqlite_to_chromadb():
    """Generate embeddings for all documents (no SQLite migration needed)"""
    print("\n🚀 Generating embeddings for all documents in ChromaDB...")
    
    embedding_generator = EmbeddingGenerator()
    count = embedding_generator.generate_embeddings_for_all_documents()
    
    if count > 0:
        print(f"✅ Generation completed successfully!")
        print(f"📦 Generated embeddings for {count} documents")
    else:
        print("ℹ️  No new embeddings needed - all documents already have embeddings")
    
    return {'success': True, 'generated_documents': count}


def generate_missing_embeddings():
    """Generate embeddings for documents that don't have them"""
    print("\n🧠 Generating missing embeddings...")
    
    embedding_generator = EmbeddingGenerator()
    count = embedding_generator.generate_embeddings_for_all_documents()
    
    print(f"✅ Generated embeddings for {count} documents")
    return count


def test_chromadb_search():
    """Test ChromaDB search functionality"""
    print("\n🔍 Testing ChromaDB Search...")
    
    embedding_generator = EmbeddingGenerator()
    
    # Test queries
    test_queries = [
        "artificial intelligence",
        "machine learning", 
        "business strategy",
        "medical research",
        "education system"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Testing query: '{query}'")
        results = embedding_generator.search_similar_chunks(
            query=query,
            limit=3
        )
        
        if results:
            print(f"📊 Found {len(results)} results:")
            for i, result in enumerate(results[:2], 1):
                print(f"   {i}. {result.get('title', 'Unknown')} (similarity: {result['similarity']:.3f})")
                print(f"      Domain: {result.get('domain', 'unknown')}")
                print(f"      Preview: {result['chunk_text'][:100]}...")
        else:
            print("   No results found")


def backup_chromadb():
    """Create a backup of ChromaDB"""
    print("\n💾 Creating ChromaDB backup...")
    
    backup_path = config.backup_path
    success = chroma_client.backup_collections(backup_path)
    
    if success:
        print(f"✅ Backup created successfully in {backup_path}")
    else:
        print("❌ Backup failed")
    
    return success


def show_embedding_stats():
    """Show comprehensive embedding statistics"""
    print("\n📊 Embedding Statistics:")
    
    embedding_generator = EmbeddingGenerator()
    stats = embedding_generator.get_embedding_stats()
    
    print(f"Status: {stats['status']}")
    
    if 'chromadb' in stats:
        print("\nChromaDB Collections:")
        for domain, data in stats['chromadb'].items():
            if isinstance(data, dict) and 'document_count' in data:
                print(f"  - {domain}: {data['document_count']} embeddings")
    
    if 'sqlite' in stats:
        print(f"\nSQLite Fallback: {stats['sqlite'].get('total_embeddings', 0)} embeddings")


def main():
    """Main migration and management function"""
    print("🎯 ChromaDB Migration & Management Tool")
    print("=" * 50)
    
    setup_logging()
    
    # Check if ChromaDB is available
    if not check_chromadb_status():
        print("\n❌ ChromaDB is not available. Please install it first:")
        print("   pip install chromadb>=0.4.15")
        return
    
    print("\nAvailable actions:")
    print("1. Generate embeddings for all documents")
    print("2. Generate missing embeddings")
    print("3. Test ChromaDB search")
    print("4. Show embedding statistics")
    print("5. Create ChromaDB backup")
    print("6. Run all (generate + test)")
    print("0. Exit")
    
    try:
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == '1':
            migrate_sqlite_to_chromadb()  # Now generates embeddings
        elif choice == '2':
            generate_missing_embeddings()
        elif choice == '3':
            test_chromadb_search()
        elif choice == '4':
            show_embedding_stats()
        elif choice == '5':
            backup_chromadb()
        elif choice == '6':
            print("\n🚀 Running complete setup...")
            migrate_sqlite_to_chromadb()  # Generate embeddings
            generate_missing_embeddings()  # Generate any missing ones
            test_chromadb_search()
            show_embedding_stats()
            backup_chromadb()
        elif choice == '0':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logging.error(f"Migration script error: {e}")


if __name__ == "__main__":
    main()
