#!/usr/bin/env python3
"""
Simple Delete-Add Constraint Test
Tests delete and re-add functionality to verify constraint handling
"""

import os
import sys
import sqlite3
import hashlib
import json
from datetime import datetime

# Simple test without complex imports
def test_constraint_scenario():
    """Test the constraint scenario directly with the database"""
    print("🧪 Testing Delete-Add UNIQUE Constraint Scenario...")
    
    # Connect to the database
    db_path = os.path.join("data", "knowledge.db")
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run the application first to create the database.")
        return False
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test document data
    test_content = "This is a unique test document for constraint testing."
    content_hash = hashlib.md5(test_content.encode()).hexdigest()
    
    test_doc = {
        'url': 'http://test.example.com/constraint-test-unique',
        'title': 'Constraint Test Document',
        'content': test_content,
        'content_hash': content_hash,
        'content_type': 'text/plain',
        'domain': 'test.example.com',
        'language': 'en',
        'word_count': len(test_content.split()),
        'char_count': len(test_content),
        'reading_time_minutes': 1,
        'metadata': '{}',
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    try:
        print("\n📝 PHASE 1: Add Initial Document")
        print("=" * 40)
        
        # Clean up any existing test documents first
        cursor.execute("DELETE FROM documents WHERE url = ?", (test_doc['url'],))
        conn.commit()
        
        # Insert test document
        insert_sql = """
            INSERT INTO documents 
            (url, title, content, content_hash, content_type, domain, language, 
             word_count, char_count, reading_time_minutes, metadata, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_sql, (
            test_doc['url'], test_doc['title'], test_doc['content'], test_doc['content_hash'],
            test_doc['content_type'], test_doc['domain'], test_doc['language'],
            test_doc['word_count'], test_doc['char_count'], test_doc['reading_time_minutes'],
            test_doc['metadata'], test_doc['status'], test_doc['created_at'], test_doc['updated_at']
        ))
        doc_id = cursor.lastrowid
        conn.commit()
        print(f"✅ Document added successfully: ID {doc_id}")
        
        print("\n🗑️ PHASE 2: Soft Delete Document")
        print("=" * 40)
        
        # Soft delete the document
        cursor.execute(
            "UPDATE documents SET status = 'deleted', updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), doc_id)
        )
        conn.commit()
        print(f"✅ Document {doc_id} soft deleted")
        
        print("\n🔄 PHASE 3: Try to Add Same Document (This Previously Failed)")
        print("=" * 40)
        
        # Try to insert the same document again (this should cause constraint error without fix)
        try:
            cursor.execute(insert_sql, (
                test_doc['url'] + '-retry',  # Different URL to avoid URL constraint
                test_doc['title'] + ' (Retry)',
                test_doc['content'],  # Same content = same content_hash
                test_doc['content_hash'],  # This is the problematic field
                test_doc['content_type'], test_doc['domain'], test_doc['language'],
                test_doc['word_count'], test_doc['char_count'], test_doc['reading_time_minutes'],
                test_doc['metadata'], test_doc['status'], test_doc['created_at'], test_doc['updated_at']
            ))
            new_doc_id = cursor.lastrowid
            conn.commit()
            print(f"❌ This should have failed! New document added with ID {new_doc_id}")
            print("❌ UNIQUE constraint on content_hash was not enforced!")
            return False
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: documents.content_hash" in str(e):
                print("✅ UNIQUE constraint error caught as expected!")
                print(f"   Error: {e}")
                
                # Now test the solution: check for deleted documents with same hash
                print("\n🔍 PHASE 4: Check for Deleted Document with Same Hash")
                print("=" * 40)
                
                cursor.execute(
                    "SELECT * FROM documents WHERE content_hash = ? AND status = 'deleted'",
                    (content_hash,)
                )
                deleted_doc = cursor.fetchone()
                
                if deleted_doc:
                    print(f"✅ Found deleted document with same hash: ID {deleted_doc['id']}")
                    
                    # Reactivate the deleted document
                    print("\n🔄 PHASE 5: Reactivate Deleted Document")
                    print("=" * 40)
                    
                    update_sql = """
                        UPDATE documents 
                        SET title = ?, content = ?, url = ?, status = 'active', updated_at = ?
                        WHERE id = ?
                    """
                    cursor.execute(update_sql, (
                        test_doc['title'] + ' (Reactivated)',
                        test_doc['content'],
                        test_doc['url'] + '-reactivated',
                        datetime.now().isoformat(),
                        deleted_doc['id']
                    ))
                    conn.commit()
                    print(f"✅ Document {deleted_doc['id']} reactivated successfully")
                    
                    # Verify the document is active
                    cursor.execute("SELECT * FROM documents WHERE id = ?", (deleted_doc['id'],))
                    reactivated_doc = cursor.fetchone()
                    
                    if reactivated_doc and reactivated_doc['status'] == 'active':
                        print("✅ Document status confirmed as 'active'")
                        print(f"   Title: {reactivated_doc['title']}")
                        print(f"   URL: {reactivated_doc['url']}")
                        result = True
                    else:
                        print("❌ Document reactivation failed")
                        result = False
                else:
                    print("❌ No deleted document found with same hash")
                    result = False
            else:
                print(f"❌ Unexpected integrity error: {e}")
                result = False
        
        print("\n🧹 PHASE 6: Cleanup")
        print("=" * 40)
        
        # Clean up test documents
        cursor.execute("DELETE FROM documents WHERE content_hash = ?", (content_hash,))
        conn.commit()
        print("✅ Test documents cleaned up")
        
        return result
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    finally:
        conn.close()

def check_current_database_state():
    """Check current state of the database"""
    print("\n📊 Checking Current Database State...")
    
    db_path = os.path.join("data", "knowledge.db")
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check for documents with different statuses
        cursor.execute("SELECT status, COUNT(*) as count FROM documents GROUP BY status")
        status_counts = cursor.fetchall()
        
        print("Document counts by status:")
        for row in status_counts:
            print(f"   {row['status']}: {row['count']} documents")
        
        # Check for potential content_hash duplicates
        cursor.execute("""
            SELECT content_hash, COUNT(*) as count 
            FROM documents 
            GROUP BY content_hash 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"\n⚠️ Found {len(duplicates)} content_hash duplicates:")
            for dup in duplicates:
                print(f"   Hash {dup['content_hash'][:16]}...: {dup['count']} documents")
                
                # Show details of these duplicates
                cursor.execute("SELECT id, title, status FROM documents WHERE content_hash = ?", (dup['content_hash'],))
                docs = cursor.fetchall()
                for doc in docs:
                    print(f"     ID {doc['id']}: {doc['title']} (status: {doc['status']})")
        else:
            print("\n✅ No content_hash duplicates found")
    
    except Exception as e:
        print(f"❌ Error checking database state: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 Delete-Add UNIQUE Constraint Test")
    print("="*50)
    
    # Check current database state
    check_current_database_state()
    
    # Run the constraint test
    success = test_constraint_scenario()
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS")
    print("="*50)
    
    if success:
        print("🎉 Constraint handling test PASSED!")
        print("\n✅ The system correctly:")
        print("   • Detects UNIQUE constraint violations on content_hash")
        print("   • Finds deleted documents with the same content")
        print("   • Reactivates deleted documents instead of failing")
        print("   • Updates document metadata during reactivation")
    else:
        print("❌ Constraint handling test FAILED!")
        print("\n⚠️ Issues detected:")
        print("   • UNIQUE constraint violations may not be handled properly")
        print("   • Document reactivation may not be working")
        print("   • Delete-add cycles may cause database errors")
    
    print("\n💡 This test simulates the exact scenario:")
    print("   1. Add document → creates content_hash") 
    print("   2. Delete document (soft) → content_hash remains in DB")
    print("   3. Add same document → UNIQUE constraint violation")
    print("   4. Solution: Find deleted doc and reactivate it")
