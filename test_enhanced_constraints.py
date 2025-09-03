#!/usr/bin/env python3
"""
Test Enhanced UNIQUE Constraint Handling

This script tests the enhanced duplicate detection and constraint handling
that checks for both URL and content_hash duplicates.
"""

import os
import sys
import json
import hashlib
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.storage.storage_manager import StorageManager
from src.core.database import db

def create_test_document(url, title, content, domain="test.com"):
    """Create a test document with calculated content_hash"""
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    return {
        'url': url,
        'title': title,
        'content': content,
        'content_hash': content_hash,
        'content_type': 'text/html',
        'domain': domain,
        'language': 'en',
        'word_count': len(content.split()),
        'char_count': len(content),
        'reading_time_minutes': max(1, len(content.split()) // 200),
        'metadata': {'test': True, 'created_by': 'test_script'}
    }

def test_constraint_handling():
    """Test various constraint violation scenarios"""
    print("🧪 Testing Enhanced UNIQUE Constraint Handling")
    print("=" * 50)
    
    storage_manager = StorageManager()
    
    # Test Document 1: Base document
    print("\n📄 Test 1: Storing base document")
    doc1 = create_test_document(
        url="https://example.com/test1",
        title="Test Document 1", 
        content="This is test content for document 1. It contains enough text to pass validation requirements. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    )
    
    success, message, doc_id = storage_manager.store_document(doc1)
    print(f"Result: {success}, Message: {message}, ID: {doc_id}")
    
    if success:
        print("✅ Base document stored successfully")
        base_doc_id = doc_id
    else:
        print("❌ Failed to store base document")
        return
    
    # Test Document 2: Same URL (should detect duplicate)
    print("\n📄 Test 2: Storing document with same URL")
    doc2 = create_test_document(
        url="https://example.com/test1",  # Same URL
        title="Test Document 1 Updated",
        content="This is different content but same URL. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris."
    )
    
    success, message, doc_id = storage_manager.store_document(doc2)
    print(f"Result: {success}, Message: {message}, ID: {doc_id}")
    
    if success and "already exists" in message:
        print("✅ URL duplicate correctly detected")
    else:
        print("❌ URL duplicate not detected properly")
    
    # Test Document 3: Same content_hash (should detect duplicate)
    print("\n📄 Test 3: Storing document with same content hash")
    doc3 = create_test_document(
        url="https://example.com/test3",  # Different URL
        title="Different Title",
        content="This is test content for document 1. It contains enough text to pass validation requirements. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."  # Same content as doc1
    )
    
    success, message, doc_id = storage_manager.store_document(doc3)
    print(f"Result: {success}, Message: {message}, ID: {doc_id}")
    
    if success and "already exists" in message:
        print("✅ Content hash duplicate correctly detected")
    else:
        print("❌ Content hash duplicate not detected properly")
    
    # Test Document 4: Delete and re-add scenario
    print("\n📄 Test 4: Delete document and try to re-add")
    
    # First, delete the base document
    try:
        delete_query = "UPDATE documents SET status = 'deleted' WHERE id = ?"
        db.execute_query(delete_query, (base_doc_id,))
        print(f"✅ Deleted document {base_doc_id}")
    except Exception as e:
        print(f"❌ Failed to delete document: {e}")
        return
    
    # Try to add the same document again (should reactivate)
    doc4 = create_test_document(
        url="https://example.com/test1",  # Same URL as deleted doc
        title="Test Document 1 Reactivated",
        content="This is test content for document 1. It contains enough text to pass validation requirements. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."  # Same content
    )
    
    success, message, doc_id = storage_manager.store_document(doc4)
    print(f"Result: {success}, Message: {message}, ID: {doc_id}")
    
    if success and ("reactivated" in message or doc_id == base_doc_id):
        print("✅ Document reactivation works correctly")
    else:
        print("❌ Document reactivation failed")
    
    # Test Document 5: Different URL, deleted content hash reactivation  
    print("\n📄 Test 5: Different URL with deleted content hash")
    
    # Delete the document again
    try:
        delete_query = "UPDATE documents SET status = 'deleted' WHERE id = ?"
        db.execute_query(delete_query, (base_doc_id,))
        print(f"✅ Deleted document {base_doc_id} again")
    except Exception as e:
        print(f"❌ Failed to delete document: {e}")
        return
    
    # Try to add with different URL but same content hash
    doc5 = create_test_document(
        url="https://different.com/test",  # Different URL
        title="Different Title for Same Content",
        content="This is test content for document 1. It contains enough text to pass validation requirements. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."  # Same content hash
    )
    
    success, message, doc_id = storage_manager.store_document(doc5)
    print(f"Result: {success}, Message: {message}, ID: {doc_id}")
    
    if success and ("reactivated" in message or doc_id == base_doc_id):
        print("✅ Content hash reactivation works correctly")
    else:
        print("❌ Content hash reactivation failed")
    
    # Test Document 6: Completely new document
    print("\n📄 Test 6: Storing completely new document")
    doc6 = create_test_document(
        url="https://new.com/unique",
        title="Unique Document",
        content="This is completely unique content that has never been seen before"
    )
    
    success, message, doc_id = storage_manager.store_document(doc6)
    print(f"Result: {success}, Message: {message}, ID: {doc_id}")
    
    if success and "stored successfully" in message:
        print("✅ New document stored correctly")
    else:
        print("❌ Failed to store new document")
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Summary")
    
    # Check final state of documents
    try:
        query = "SELECT id, url, title, status, content_hash FROM documents ORDER BY id"
        docs = db.execute_query(query)
        
        print(f"\n📊 Final database state ({len(docs)} documents):")
        for doc in docs:
            print(f"  ID {doc['id']}: {doc['title'][:30]}... (Status: {doc['status']})")
            print(f"    URL: {doc['url']}")
            print(f"    Hash: {doc['content_hash'][:16]}...")
    except Exception as e:
        print(f"❌ Error checking final state: {e}")

if __name__ == "__main__":
    test_constraint_handling()
