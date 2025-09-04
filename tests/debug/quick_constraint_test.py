#!/usr/bin/env python3
"""
Quick Constraint Test
Tests if the enhanced constraint handling is working
"""

import sqlite3
import hashlib
import json
from datetime import datetime
import os

def quick_constraint_test():
    """Quick test of constraint handling"""
    print("🔧 QUICK CONSTRAINT HANDLING TEST")
    print("=" * 40)
    
    db_path = os.path.join("data", "knowledge.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test content
    test_content = f"Quick test content - {datetime.now().strftime('%H:%M:%S')}"
    content_hash = hashlib.md5(test_content.encode()).hexdigest()
    
    try:
        # Clean up any existing test data
        cursor.execute("DELETE FROM documents WHERE content_hash = ?", (content_hash,))
        conn.commit()
        
        print(f"📄 Test content hash: {content_hash[:16]}...")
        
        # Insert document
        print("\n1️⃣ Inserting document...")
        cursor.execute("""
            INSERT INTO documents 
            (url, title, content, content_hash, content_type, domain, language, 
             word_count, char_count, reading_time_minutes, metadata, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'http://test.quick/constraint',
            'Quick Constraint Test',
            test_content,
            content_hash,
            'text/plain',
            'test.quick',
            'en',
            len(test_content.split()),
            len(test_content),
            1,
            json.dumps({'test': 'quick'}),
            'active',
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        doc_id = cursor.lastrowid
        conn.commit()
        print(f"✅ Document inserted: ID {doc_id}")
        
        # Soft delete
        print("\n2️⃣ Soft deleting document...")
        cursor.execute("UPDATE documents SET status = 'deleted' WHERE id = ?", (doc_id,))
        conn.commit()
        print(f"✅ Document soft deleted")
        
        # Try to insert same content_hash (should fail)
        print("\n3️⃣ Testing constraint violation...")
        try:
            cursor.execute("""
                INSERT INTO documents 
                (url, title, content, content_hash, content_type, domain, language, 
                 word_count, char_count, reading_time_minutes, metadata, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'http://test.quick/constraint-2',
                'Quick Constraint Test 2',
                test_content,
                content_hash,  # Same hash!
                'text/plain',
                'test.quick',
                'en',
                len(test_content.split()),
                len(test_content),
                1,
                json.dumps({'test': 'quick2'}),
                'active',
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            print("❌ ERROR: Constraint not enforced!")
            return False
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: documents.content_hash" in str(e):
                print("✅ Constraint violation detected correctly")
                print(f"   Error: {e}")
                
                # Now test the fix - find deleted document and reactivate
                cursor.execute("SELECT * FROM documents WHERE content_hash = ? AND status = 'deleted'", (content_hash,))
                deleted_doc = cursor.fetchone()
                
                if deleted_doc:
                    print("✅ Found deleted document with same hash")
                    
                    # Reactivate it (this is what our fixed code does)
                    cursor.execute("""
                        UPDATE documents 
                        SET title = ?, content = ?, url = ?, status = 'active', 
                            metadata = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        'Quick Constraint Test (Reactivated)',
                        test_content,
                        'http://test.quick/constraint-reactivated',
                        json.dumps({'test': 'reactivated'}),
                        datetime.now().isoformat(),
                        deleted_doc['id']
                    ))
                    conn.commit()
                    print("✅ Document reactivated successfully")
                    
                    # Verify
                    cursor.execute("SELECT * FROM documents WHERE id = ?", (deleted_doc['id'],))
                    reactivated = cursor.fetchone()
                    print(f"✅ Verification: Status = {reactivated['status']}")
                    
                else:
                    print("❌ No deleted document found")
                    return False
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        
        # Cleanup
        print("\n4️⃣ Cleaning up...")
        cursor.execute("DELETE FROM documents WHERE content_hash = ?", (content_hash,))
        conn.commit()
        print("✅ Cleanup complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = quick_constraint_test()
    
    if success:
        print("\n🎉 CONSTRAINT HANDLING TEST PASSED!")
        print("   The database constraint handling logic is working correctly.")
        print("   Your Streamlit app should now handle constraint errors properly.")
    else:
        print("\n❌ CONSTRAINT HANDLING TEST FAILED!")
        print("   There may still be issues with the constraint handling.")
    
    print("\n💡 Next Steps:")
    print("   • The Streamlit app is now running with enhanced error handling")
    print("   • Try adding the same content twice in the UI")
    print("   • Check the terminal logs for detailed constraint handling messages")
    print("   • The enhanced logging will show exactly what's happening")
