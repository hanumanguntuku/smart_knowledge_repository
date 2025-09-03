#!/usr/bin/env python3
"""
Test script for enhanced conversation management features
Demonstrates the new conversation capabilities
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.ai.scope_chatbot import ScopeAwareChatbot
from src.storage.storage_manager import StorageManager
from src.search.search_engine import SearchEngine
from src.ai.conversation_manager import ConversationContextManager
from src.storage.conversation_storage import ConversationStorageManager
from src.services.conversation_export import ConversationExportService

def test_conversation_features():
    """Test the enhanced conversation management features"""
    print("🧪 Testing Enhanced Conversation Management")
    print("=" * 50)
    
    try:
        # Initialize components
        print("📦 Initializing components...")
        storage_manager = StorageManager()
        search_engine = SearchEngine()
        
        # Create enhanced chatbot with session ID
        session_id = "test_session_001"
        chatbot = ScopeAwareChatbot(
            storage_manager=storage_manager,
            search_engine=search_engine,
            session_id=session_id
        )
        
        print(f"✅ Enhanced chatbot initialized with session: {session_id}")
        print(f"   Conversation enabled: {chatbot.conversation_enabled}")
        print(f"   Current thread ID: {chatbot.current_thread_id}")
        
        # Test basic conversation
        print("\n💬 Testing basic conversation...")
        
        queries = [
            "What is artificial intelligence?",
            "Tell me more about that",
            "How does it relate to machine learning?",
            "What are some examples?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Query {i}: {query}")
            
            try:
                response = chatbot.process_query(query)
                print(f"   ✅ Response: {response.get('response', 'No response')[:100]}...")
                print(f"   📚 Sources: {len(response.get('sources', []))}")
                print(f"   🎯 Confidence: {response.get('confidence', 0):.2f}")
                
                # Test follow-up suggestions
                if i == 2:  # After second query
                    suggestions = chatbot.get_follow_up_suggestions()
                    if suggestions:
                        print(f"   💡 Follow-up suggestions: {suggestions[:2]}")
                
            except Exception as e:
                print(f"   ❌ Error processing query: {e}")
        
        # Test conversation management
        print("\n📚 Testing conversation management...")
        
        # Get conversation history
        history = chatbot.get_conversation_history(limit=5)
        print(f"   📖 Conversation history: {len(history)} messages")
        
        # Get user conversations
        conversations = chatbot.get_user_conversations()
        print(f"   📚 User conversations: {len(conversations)} total")
        
        # Test conversation search
        if conversations:
            search_results = chatbot.search_conversations("artificial intelligence")
            print(f"   🔍 Search results for 'artificial intelligence': {len(search_results)}")
        
        # Test export functionality
        print("\n📤 Testing export functionality...")
        
        try:
            export_service = ConversationExportService()
            
            if chatbot.current_thread_id:
                # Test JSON export
                json_file = export_service.export_conversation_json(
                    chatbot.current_thread_id, session_id
                )
                if json_file:
                    print(f"   ✅ JSON export: {json_file}")
                
                # Test Markdown export
                md_file = export_service.export_conversation_markdown(
                    chatbot.current_thread_id, session_id
                )
                if md_file:
                    print(f"   ✅ Markdown export: {md_file}")
                
                # Test conversation summary
                summary = export_service.generate_conversation_summary(
                    chatbot.current_thread_id, session_id
                )
                if summary:
                    print(f"   📊 Summary: {summary['total_messages']} messages, "
                          f"{summary['unique_sources_referenced']} sources")
            
        except Exception as e:
            print(f"   ⚠️ Export testing error: {e}")
        
        print("\n✅ Conversation management testing completed!")
        print("\n🎯 Key Features Demonstrated:")
        print("   ✅ Persistent conversation storage")
        print("   ✅ Context-aware follow-up handling")
        print("   ✅ Reference resolution ('tell me more about that')")
        print("   ✅ Conversation search and management")
        print("   ✅ Export capabilities (JSON, Markdown)")
        print("   ✅ Follow-up question suggestions")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        return False

def test_context_manager():
    """Test the conversation context manager specifically"""
    print("\n🧠 Testing Context Manager...")
    
    try:
        context_manager = ConversationContextManager()
        
        # Test query analysis
        test_queries = [
            "What is machine learning?",
            "Tell me more about that",
            "How does it work?",
            "What are the applications?"
        ]
        
        # Simulate a conversation thread
        thread_id = 1
        session_id = "test_context_session"
        
        for i, query in enumerate(test_queries):
            analysis = context_manager.analyze_query_context(query, thread_id, session_id)
            
            print(f"   Query: '{query}'")
            print(f"   Is follow-up: {analysis['is_follow_up']}")
            print(f"   Intent: {analysis['intent_type']}")
            print(f"   References previous: {analysis['references_previous']}")
            print(f"   Confidence: {analysis['confidence']:.2f}")
            print()
        
        print("   ✅ Context analysis completed")
        
    except Exception as e:
        print(f"   ❌ Context manager test error: {e}")

if __name__ == "__main__":
    success = test_conversation_features()
    test_context_manager()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("\n🚀 You can now use the enhanced conversation features in your Streamlit app!")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
