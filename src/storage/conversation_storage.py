"""
Enhanced Conversation Storage Manager for Smart Knowledge Repository
Handles persistent conversation storage, context management, and conversation analytics
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from src.core.database import DatabaseManager


class ConversationStorageManager:
    """Manages conversation persistence and context optimization"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.logger = logging.getLogger(__name__)
        self.max_context_tokens = 4000
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure conversation tables exist"""
        try:
            # The tables should already exist from schema, but let's verify
            self.db.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_threads'")
            self.logger.info("✅ Conversation tables verified")
        except Exception as e:
            self.logger.error(f"❌ Error verifying conversation tables: {e}")
    
    def create_conversation_thread(self, session_id: str, title: str = None) -> Optional[int]:
        """Create a new conversation thread"""
        try:
            if not title:
                title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            query = """
            INSERT INTO conversation_threads (session_id, title, created_at, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            result = self.db.execute_query(query, (session_id, title))
            
            if result:
                thread_id = self.db.get_last_insert_id()
                self.logger.info(f"✅ Created conversation thread {thread_id} for session {session_id}")
                return thread_id
            
        except Exception as e:
            self.logger.error(f"❌ Error creating conversation thread: {e}")
        
        return None
    
    def get_or_create_active_thread(self, session_id: str) -> int:
        """Get the most recent conversation thread for a session or create a new one"""
        try:
            # Look for recent conversation (within last 24 hours)
            query = """
            SELECT id FROM conversation_threads 
            WHERE session_id = ? AND updated_at > datetime('now', '-1 day')
            ORDER BY updated_at DESC LIMIT 1
            """
            result = self.db.execute_query(query, (session_id,))
            
            if result and len(result) > 0:
                thread_id = result[0]['id']
                self.logger.info(f"📋 Using existing thread {thread_id} for session {session_id}")
                return thread_id
            
            # Create new thread if none found
            thread_id = self.create_conversation_thread(session_id)
            return thread_id if thread_id else 1  # Fallback
            
        except Exception as e:
            self.logger.error(f"❌ Error getting active thread: {e}")
            return 1  # Fallback to thread 1
    
    def save_message(self, thread_id: int, role: str, content: str, 
                    sources: List[Dict] = None, metadata: Dict = None) -> bool:
        """Save a message to the conversation thread"""
        try:
            sources_json = json.dumps(sources if sources else [])
            metadata_json = json.dumps(metadata if metadata else {})
            
            query = """
            INSERT INTO conversation_messages (thread_id, role, content, sources, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            result = self.db.execute_query(query, (thread_id, role, content, sources_json, metadata_json))
            
            if result is not None:
                # Update thread message count and timestamp
                self._update_thread_stats(thread_id)
                self.logger.info(f"💬 Saved {role} message to thread {thread_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error saving message: {e}")
        
        return False
    
    def get_conversation_history(self, thread_id: int, limit: int = 50) -> List[Dict]:
        """Get conversation history for a thread"""
        try:
            query = """
            SELECT role, content, sources, metadata, timestamp
            FROM conversation_messages 
            WHERE thread_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
            """
            
            messages = self.db.execute_query(query, (thread_id, limit))
            
            if messages:
                # Parse JSON fields
                for message in messages:
                    try:
                        message['sources'] = json.loads(message['sources']) if message['sources'] else []
                        message['metadata'] = json.loads(message['metadata']) if message['metadata'] else {}
                    except json.JSONDecodeError:
                        message['sources'] = []
                        message['metadata'] = {}
                
                self.logger.info(f"📖 Retrieved {len(messages)} messages from thread {thread_id}")
                return messages
            
        except Exception as e:
            self.logger.error(f"❌ Error getting conversation history: {e}")
        
        return []
    
    def get_user_conversations(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get all conversation threads for a user session"""
        try:
            query = """
            SELECT id, title, summary, total_messages, created_at, updated_at
            FROM conversation_threads 
            WHERE session_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """
            
            conversations = self.db.execute_query(query, (session_id, limit))
            
            if conversations:
                self.logger.info(f"📚 Retrieved {len(conversations)} conversations for session {session_id}")
                return conversations
            
        except Exception as e:
            self.logger.error(f"❌ Error getting user conversations: {e}")
        
        return []
    
    def get_optimized_context(self, thread_id: int, max_tokens: int = None) -> List[Dict]:
        """Get optimized conversation context within token limits"""
        try:
            max_tokens = max_tokens or self.max_context_tokens
            
            # Get recent messages
            messages = self.get_conversation_history(thread_id, limit=50)
            
            if not messages:
                return []
            
            # Simple token estimation (approximately 4 chars per token)
            optimized_messages = []
            current_tokens = 0
            
            # Start from most recent and work backwards
            for message in reversed(messages):
                estimated_tokens = len(message['content']) // 4
                
                if current_tokens + estimated_tokens > max_tokens:
                    break
                
                optimized_messages.insert(0, message)
                current_tokens += estimated_tokens
            
            # Always include at least the last 2 messages if available
            if len(optimized_messages) < 2 and len(messages) >= 2:
                optimized_messages = messages[-2:]
            
            self.logger.info(f"🎯 Optimized context: {len(optimized_messages)} messages (~{current_tokens} tokens)")
            return optimized_messages
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing context: {e}")
            return []
    
    def update_conversation_title(self, thread_id: int, title: str) -> bool:
        """Update conversation title"""
        try:
            query = "UPDATE conversation_threads SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            result = self.db.execute_query(query, (title, thread_id))
            
            if result is not None:
                self.logger.info(f"📝 Updated title for thread {thread_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error updating conversation title: {e}")
        
        return False
    
    def delete_conversation(self, thread_id: int, session_id: str) -> bool:
        """Delete a conversation thread (with permission check)"""
        try:
            # Verify ownership
            query = "SELECT session_id FROM conversation_threads WHERE id = ?"
            result = self.db.execute_query(query, (thread_id,))
            
            if not result or result[0]['session_id'] != session_id:
                self.logger.warning(f"❌ Unauthorized deletion attempt for thread {thread_id}")
                return False
            
            # Delete thread (messages will cascade delete)
            query = "DELETE FROM conversation_threads WHERE id = ?"
            result = self.db.execute_query(query, (thread_id,))
            
            if result is not None:
                self.logger.info(f"🗑️ Deleted conversation thread {thread_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error deleting conversation: {e}")
        
        return False
    
    def search_conversations(self, session_id: str, query: str, limit: int = 10) -> List[Dict]:
        """Search conversations by content"""
        try:
            search_query = """
            SELECT DISTINCT t.id, t.title, t.summary, t.created_at, t.updated_at,
                   m.content as matched_content
            FROM conversation_threads t
            JOIN conversation_messages m ON t.id = m.thread_id
            WHERE t.session_id = ? AND (
                t.title LIKE ? OR 
                t.summary LIKE ? OR 
                m.content LIKE ?
            )
            ORDER BY t.updated_at DESC
            LIMIT ?
            """
            
            search_term = f"%{query}%"
            results = self.db.execute_query(search_query, 
                                          (session_id, search_term, search_term, search_term, limit))
            
            if results:
                self.logger.info(f"🔍 Found {len(results)} conversations matching '{query}'")
                return results
            
        except Exception as e:
            self.logger.error(f"❌ Error searching conversations: {e}")
        
        return []
    
    def _update_thread_stats(self, thread_id: int):
        """Update thread statistics"""
        try:
            # Count messages and update timestamp
            query = """
            UPDATE conversation_threads 
            SET total_messages = (
                SELECT COUNT(*) FROM conversation_messages WHERE thread_id = ?
            ), updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            self.db.execute_query(query, (thread_id, thread_id))
            
        except Exception as e:
            self.logger.error(f"❌ Error updating thread stats: {e}")
    
    def get_conversation_analytics(self, session_id: str) -> Dict:
        """Get analytics for user conversations"""
        try:
            # Get basic stats
            stats_query = """
            SELECT 
                COUNT(*) as total_conversations,
                SUM(total_messages) as total_messages,
                AVG(total_messages) as avg_messages_per_conversation,
                MAX(updated_at) as last_activity
            FROM conversation_threads 
            WHERE session_id = ?
            """
            
            stats = self.db.execute_query(stats_query, (session_id,))
            
            if stats and len(stats) > 0:
                analytics = stats[0]
                
                # Get recent activity (last 7 days)
                recent_query = """
                SELECT COUNT(*) as recent_conversations
                FROM conversation_threads 
                WHERE session_id = ? AND created_at > datetime('now', '-7 days')
                """
                
                recent = self.db.execute_query(recent_query, (session_id,))
                if recent:
                    analytics['recent_conversations'] = recent[0]['recent_conversations']
                
                self.logger.info(f"📊 Generated analytics for session {session_id}")
                return analytics
                
        except Exception as e:
            self.logger.error(f"❌ Error getting conversation analytics: {e}")
        
        return {
            'total_conversations': 0,
            'total_messages': 0,
            'avg_messages_per_conversation': 0,
            'recent_conversations': 0,
            'last_activity': None
        }
