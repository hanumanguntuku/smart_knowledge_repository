"""
Check if embeddings exist in ChromaDB for stored documents
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.search.chroma_client import chroma_client

def check_chromadb_collections():
    """Check ChromaDB collections in detail"""
    print("🔍 Checking ChromaDB Collections")
    print("=" * 50)
    
    if not chroma_client.is_available():
        print("❌ ChromaDB not available!")
        return
    
    # Get collection stats
    stats = chroma_client.get_collection_stats()
    
    for domain, stat in stats.items():
        print(f"\n📁 Collection: {domain}")
        print(f"   Document count: {stat['document_count']}")
        
        if stat['document_count'] > 0:
            try:
                # Get collection
                collection = chroma_client.get_collection_for_domain(domain)
                if collection:
                    # Get all items
                    results = collection.get(limit=stat['document_count'])
                    
                    print(f"   Found {len(results['ids'])} embeddings:")
                    for i, (doc_id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents'])):
                        print(f"     {i+1}. ID: {doc_id}")
                        if metadata:
                            print(f"        Document ID: {metadata.get('document_id', 'Unknown')}")
                            print(f"        Domain: {metadata.get('domain', 'Unknown')}")
                        print(f"        Text: {document[:100] if document else 'No text'}...")
                        print()
                else:
                    print("   Could not access collection")
            except Exception as e:
                print(f"   Error accessing collection: {e}")
        else:
            print("   No embeddings found")

def main():
    check_chromadb_collections()

if __name__ == "__main__":
    main()
