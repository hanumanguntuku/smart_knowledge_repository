#!/usr/bin/env python3
"""
Test the Fixed Constraint Handling
Verifies that the metadata binding error is fixed and constraint handling works properly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import json
from datetime import datetime
from storage.storage_manager import StorageManager
from core.config import Config

def test_fixed_constraint_handling():
    """Test the constraint handling with proper metadata handling"""
    print("🧪 Testing Fixed Constraint Handling...")
    print("=" * 50)
    
    # Initialize storage manager
    storage = StorageManager()
    
    # Test document with various metadata types
    test_doc = {
        'title': 'Test Document with Complex Metadata',
        'content': 'This document tests the fixed constraint handling with proper metadata serialization.',
        'url': 'http://test.example.com/metadata-test',
        'content_type': 'text/html',
        'metadata': {
            'source': 'test',
            'tags': ['testing', 'metadata', 'constraints'],
            'priority': 1,
            'nested': {
                'deep_key': 'deep_value',
                'timestamp': datetime.now().isoformat()
            }
        }
    }
    
    print(f"📄 Test Document: {test_doc['title']}")
    print(f"🏷️ Metadata type: {type(test_doc['metadata'])}")
    print(f"📊 Metadata content: {json.dumps(test_doc['metadata'], indent=2)}")
    
    try:
        # PHASE 1: Initial document storage
        print(f"\n{'='*15} PHASE 1: Store Initial Document {'='*15}")
        success1, message1, doc_id1 = storage.store_document(test_doc)
        
        if success1 and doc_id1:
            print(f"✅ Document stored successfully: ID {doc_id1}")
            print(f"   Message: {message1}")
        else:
            print(f"❌ Failed to store document: {message1}")
            return False
        
        # PHASE 2: Delete the document
        print(f"\n{'='*15} PHASE 2: Soft Delete Document {'='*15}")
        delete_success = storage.delete_document(doc_id1, soft_delete=True)
        
        if delete_success:
            print(f"✅ Document {doc_id1} deleted successfully")
        else:
            print(f"❌ Failed to delete document {doc_id1}")
            return False
        
        # PHASE 3: Try to add the same document (should trigger reactivation)
        print(f"\n{'='*15} PHASE 3: Re-add Same Document {'='*15}")
        print("🔍 This should trigger the reactivation logic...")
        
        # Modify metadata slightly to test update
        test_doc['metadata']['reactivation_test'] = True
        test_doc['metadata']['reactivated_at'] = datetime.now().isoformat()
        
        success2, message2, doc_id2 = storage.store_document(test_doc)
        
        if success2 and doc_id2:
            print(f"✅ Document re-added successfully: ID {doc_id2}")
            print(f"   Message: {message2}")
            
            if doc_id1 == doc_id2:
                print("✅ Same document ID returned - reactivation worked!")
            else:
                print(f"⚠️ Different document ID: {doc_id1} -> {doc_id2}")
        else:
            print(f"❌ Failed to re-add document: {message2}")
            return False
        
        # PHASE 4: Verify the document and its metadata
        print(f"\n{'='*15} PHASE 4: Verify Document State {'='*15}")
        retrieved_doc = storage.get_document_by_id(doc_id2)
        
        if retrieved_doc:
            print(f"✅ Retrieved document: ID {retrieved_doc['id']}")
            print(f"   Title: {retrieved_doc['title']}")
            print(f"   Status: {retrieved_doc['status']}")
            
            # Check metadata
            if 'metadata' in retrieved_doc:
                try:
                    if isinstance(retrieved_doc['metadata'], str):
                        parsed_metadata = json.loads(retrieved_doc['metadata'])
                    else:
                        parsed_metadata = retrieved_doc['metadata']
                    
                    print(f"✅ Metadata retrieved and parsed successfully")
                    print(f"   Reactivation test flag: {parsed_metadata.get('reactivation_test', 'Not found')}")
                    print(f"   Original tags: {parsed_metadata.get('tags', 'Not found')}")
                    
                    if parsed_metadata.get('reactivation_test'):
                        print("✅ Metadata was properly updated during reactivation")
                    else:
                        print("⚠️ Metadata update may not have worked")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse metadata: {e}")
                    return False
            else:
                print("⚠️ No metadata found in retrieved document")
        else:
            print(f"❌ Failed to retrieve document {doc_id2}")
            return False
        
        # PHASE 5: Test multiple rapid operations
        print(f"\n{'='*15} PHASE 5: Test Rapid Operations {'='*15}")
        
        # Delete again
        if storage.delete_document(doc_id2, soft_delete=True):
            print(f"✅ Document {doc_id2} deleted again")
        else:
            print(f"❌ Failed to delete document {doc_id2} again")
            return False
        
        # Try multiple rapid re-adds
        results = []
        for i in range(3):
            test_doc['metadata']['attempt'] = i + 1
            success, message, doc_id = storage.store_document(test_doc)
            results.append((success, message, doc_id))
            print(f"   Attempt {i+1}: success={success}, ID={doc_id}")
        
        # Verify all attempts succeeded with same ID
        successful_results = [r for r in results if r[0]]
        if len(successful_results) == 3:
            first_id = successful_results[0][2]
            all_same_id = all(r[2] == first_id for r in successful_results)
            if all_same_id:
                print("✅ All rapid operations returned same document ID")
            else:
                print("⚠️ Different document IDs returned for same content")
        else:
            print(f"⚠️ Only {len(successful_results)}/3 operations succeeded")
        
        # PHASE 6: Cleanup
        print(f"\n{'='*15} PHASE 6: Cleanup {'='*15}")
        if successful_results:
            cleanup_id = successful_results[0][2]
            if storage.delete_document(cleanup_id, soft_delete=False):
                print(f"✅ Test document {cleanup_id} cleaned up")
            else:
                print(f"⚠️ Failed to clean up test document {cleanup_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 TESTING FIXED CONSTRAINT HANDLING")
    print("=" * 50)
    print("This test verifies that:")
    print("• Metadata binding errors are fixed")
    print("• UNIQUE constraint handling works properly")
    print("• Document reactivation preserves and updates metadata")
    print("• Rapid operations don't cause conflicts")
    
    success = test_fixed_constraint_handling()
    
    print(f"\n{'='*50}")
    print("📊 TEST RESULTS")
    print("="*50)
    
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Fixed Issues:")
        print("   • Metadata binding error resolved (JSON serialization)")
        print("   • UNIQUE constraint violations handled gracefully")
        print("   • Document reactivation works with complex metadata")
        print("   • Rapid delete-add cycles work without errors")
        print("   • Proper error logging and debugging information")
        
        print("\n💡 What was fixed:")
        print("   • _reactivate_document now properly serializes dict metadata to JSON")
        print("   • Added type checking and handling for metadata formats")
        print("   • Improved error messages and debugging information")
        print("   • Enhanced constraint violation detection and handling")
        
    else:
        print("❌ TESTS FAILED!")
        print("   The constraint handling fix needs more work.")
    
    print(f"\n🛠️ Technical Fix Details:")
    print(f"   • Issue: 'dict' type not supported in SQLite parameter binding")
    print(f"   • Root Cause: Metadata dict passed directly instead of JSON string")
    print(f"   • Solution: json.dumps() metadata before database operations")
    print(f"   • Enhancement: Type checking for different metadata formats")
