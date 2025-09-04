#!/usr/bin/env python3
"""
Test Conversation Storage NOT NULL Constraint Fix

This script tests the enhanced conversation storage to ensure that
NOT NULL constraint violations on thread_id are properly handled.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.storage.conversation_storage import ConversationStorageManager
from src.ai.scope_chatbot import ScopeAwareChatbot
from src.storage.storage_manager import StorageManager
from src.search.chroma_client import ChromaDBClient

def test_conversation_storage_constraints():
    """Test conversation storage constraint handling"""
    print("🧪 Testing Conversation Storage NOT NULL Constraint Fix")
    print("=" * 60)
    
    # Test 1: Direct ConversationStorageManager
    print("\n📄 Test 1: Direct ConversationStorageManager")
    try:
        conv_storage = ConversationStorageManager()
        
        # Test thread creation
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        thread_id = conv_storage.get_or_create_active_thread(session_id)
        
        print(f"Thread ID: {thread_id} (Type: {type(thread_id)})")
        
        if thread_id and isinstance(thread_id, int) and thread_id > 0:
            print("✅ Thread creation successful")
            
            # Test message saving
            success = conv_storage.save_message(
                thread_id, 'user', 'Test message to verify constraints are working'
            )
            
            if success:
                print("✅ Message saved successfully")
            else:
                print("❌ Message save failed")
        else:
            print(f"❌ Thread creation failed: {thread_id}")
            
    except Exception as e:
        print(f"❌ ConversationStorageManager test failed: {e}")
    
    # Test 2: Save message with None thread_id (should fail gracefully)
    print("\n📄 Test 2: Save message with None thread_id")
    try:
        conv_storage = ConversationStorageManager()
        success = conv_storage.save_message(None, 'user', 'This should fail gracefully')
        
        if not success:
            print("✅ None thread_id properly rejected")
        else:
            print("❌ None thread_id was accepted (this is bad)")
            
    except Exception as e:
        print(f"❌ None thread_id test error: {e}")
    
    # Test 3: Save message with invalid thread_id (should fail gracefully)
    print("\n📄 Test 3: Save message with invalid thread_id")
    try:
        conv_storage = ConversationStorageManager()
        success = conv_storage.save_message(99999, 'user', 'This should fail gracefully')
        
        if not success:
            print("✅ Invalid thread_id properly rejected")
        else:
            print("❌ Invalid thread_id was accepted (this is bad)")
            
    except Exception as e:
        print(f"❌ Invalid thread_id test error: {e}")
    
    # Test 4: ScopeAwareChatbot integration
    print("\n📄 Test 4: ScopeAwareChatbot integration")
    try:
        storage_manager = StorageManager()
        search_engine = ChromaDBClient()
        
        chatbot = ScopeAwareChatbot(
            storage_manager, 
            search_engine, 
            session_id=f"chatbot_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        print(f"Conversation enabled: {chatbot.conversation_enabled}")
        print(f"Current thread ID: {chatbot.current_thread_id}")
        
        if chatbot.conversation_enabled and chatbot.current_thread_id:
            print("✅ Chatbot conversation initialization successful")
            
            # Test query processing (this should not cause NOT NULL constraint errors)
            response = chatbot.process_query("What is ERP implementation?")
            
            if response and 'response' in response:
                print("✅ Query processing successful without constraint errors")
            else:
                print("❌ Query processing failed")
        else:
            print("⚠️ Chatbot conversation disabled or no thread ID")
            
    except Exception as e:
        print(f"❌ Chatbot integration test failed: {e}")
    
    # Test 5: Emergency fallback scenarios
    print("\n📄 Test 5: Emergency fallback scenarios")
    try:
        conv_storage = ConversationStorageManager()
        
        # Test with invalid session
        invalid_session = ""
        thread_id = conv_storage.get_or_create_active_thread(invalid_session)
        
        print(f"Thread ID for empty session: {thread_id}")
        
        if thread_id and isinstance(thread_id, int) and thread_id > 0:
            print("✅ Emergency fallback working")
            
            # Try to save a message to this fallback thread
            success = conv_storage.save_message(
                thread_id, 'assistant', 'Emergency fallback test message'
            )
            
            if success:
                print("✅ Message saved to fallback thread")
            else:
                print("❌ Failed to save to fallback thread")
        else:
            print("❌ Emergency fallback failed")
            
    except Exception as e:
        print(f"❌ Emergency fallback test error: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Conversation Storage Constraint Test Complete")

if __name__ == "__main__":
    test_conversation_storage_constraints()
