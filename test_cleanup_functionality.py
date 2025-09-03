#!/usr/bin/env python3
"""
Test script to verify the cleanup functionality for deleted documents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.storage.storage_manager import StorageManager
from src.core.database import DatabaseManager

def test_cleanup_functionality():
    """Test the cleanup functionality"""
    print("🧪 Testing Document Cleanup Functionality")
    print("=" * 50)
    
    # Initialize managers
    storage_manager = StorageManager()
    db = DatabaseManager()
    
    try:
        # Get initial statistics
        print("📊 Initial Repository Statistics:")
        stats = storage_manager.get_statistics()
        print(f"  Active Documents: {stats.get('active_documents', 0)}")
        print(f"  Deleted Documents: {stats.get('deleted_documents', 0)}")
        print(f"  Total Documents: {stats.get('total_documents', 0)}")
        
        # Add a test document
        print("\n📝 Adding test document...")
        test_content = "This is a test document for cleanup functionality testing."
        document_data = {
            'title': "Test Cleanup Document",
            'content': test_content,
            'source': "test",
            'metadata': {"test": True}
        }
        success, message, doc_id = storage_manager.store_document(document_data)
        print(f"  ✅ Added document: {success}, Message: {message}, ID: {doc_id}")
        
        # Soft delete the document
        print("\n🗑️ Soft deleting test document...")
        if doc_id:
            success = storage_manager.delete_document(doc_id, soft_delete=True)
            print(f"  ✅ Soft deletion successful: {success}")
        else:
            print("  ❌ No document ID to delete")
        
        # Check updated statistics
        print("\n📊 Statistics after soft deletion:")
        stats = storage_manager.get_statistics()
        print(f"  Active Documents: {stats.get('active_documents', 0)}")
        print(f"  Deleted Documents: {stats.get('deleted_documents', 0)}")
        print(f"  Total Documents: {stats.get('total_documents', 0)}")
        
        # Test cleanup of old deleted documents
        print("\n🧹 Testing cleanup of deleted documents...")
        initial_deleted = stats.get('deleted_documents', 0)
        
        # Get all deleted documents
        query = "SELECT id FROM documents WHERE status = 'deleted'"
        deleted_docs = db.execute_query(query)
        
        cleaned_count = 0
        for doc in deleted_docs:
            if storage_manager.delete_document(doc['id'], soft_delete=False):
                cleaned_count += 1
        
        print(f"  ✅ Cleaned up {cleaned_count} deleted documents")
        
        # Final statistics
        print("\n📊 Final Repository Statistics:")
        stats = storage_manager.get_statistics()
        print(f"  Active Documents: {stats.get('active_documents', 0)}")
        print(f"  Deleted Documents: {stats.get('deleted_documents', 0)}")
        print(f"  Total Documents: {stats.get('total_documents', 0)}")
        
        print("\n✅ Cleanup functionality test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_cleanup_functionality()
