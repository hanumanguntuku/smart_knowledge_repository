"""
Conversation Export Service for Smart Knowledge Repository
Handles conversation export in multiple formats and sharing capabilities
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid

# Optional PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from src.storage.conversation_storage import ConversationStorageManager


class ConversationExportService:
    """Handles conversation export and sharing functionality"""
    
    def __init__(self):
        self.conversation_storage = ConversationStorageManager()
        self.logger = logging.getLogger(__name__)
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
    
    def export_conversation_json(self, thread_id: int, session_id: str) -> Optional[str]:
        """Export conversation as JSON file"""
        try:
            # Get conversation metadata
            conversations = self.conversation_storage.get_user_conversations(session_id, limit=100)
            conversation_meta = next((c for c in conversations if c['id'] == thread_id), None)
            
            if not conversation_meta:
                self.logger.error(f"❌ Conversation {thread_id} not found")
                return None
            
            # Get conversation messages
            messages = self.conversation_storage.get_conversation_history(thread_id)
            
            # Build export data
            export_data = {
                'conversation_id': thread_id,
                'session_id': session_id,
                'title': conversation_meta.get('title', 'Untitled Conversation'),
                'created_at': conversation_meta.get('created_at'),
                'updated_at': conversation_meta.get('updated_at'),
                'total_messages': len(messages),
                'exported_at': datetime.now().isoformat(),
                'messages': messages,
                'metadata': {
                    'export_version': '1.0',
                    'exporter': 'Smart Knowledge Repository'
                }
            }
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{thread_id}_{timestamp}.json"
            filepath = self.export_dir / filename
            
            # Write JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Exported conversation {thread_id} to {filename}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error exporting conversation as JSON: {e}")
            return None
    
    def export_conversation_markdown(self, thread_id: int, session_id: str) -> Optional[str]:
        """Export conversation as Markdown file"""
        try:
            # Get conversation metadata
            conversations = self.conversation_storage.get_user_conversations(session_id, limit=100)
            conversation_meta = next((c for c in conversations if c['id'] == thread_id), None)
            
            if not conversation_meta:
                self.logger.error(f"❌ Conversation {thread_id} not found")
                return None
            
            # Get conversation messages
            messages = self.conversation_storage.get_conversation_history(thread_id)
            
            # Build markdown content
            markdown_lines = []
            
            # Header
            title = conversation_meta.get('title', 'Untitled Conversation')
            markdown_lines.append(f"# {title}\n")
            markdown_lines.append(f"**Conversation ID:** {thread_id}")
            markdown_lines.append(f"**Created:** {conversation_meta.get('created_at', 'Unknown')}")
            markdown_lines.append(f"**Total Messages:** {len(messages)}")
            markdown_lines.append(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            markdown_lines.append("\n---\n")
            
            # Messages
            for i, message in enumerate(messages, 1):
                role = message['role'].title()
                content = message['content']
                timestamp = message.get('timestamp', 'Unknown')
                
                markdown_lines.append(f"## {role} Message {i}")
                markdown_lines.append(f"**Time:** {timestamp}")
                markdown_lines.append("")
                markdown_lines.append(content)
                
                # Add sources if available
                sources = message.get('sources', [])
                if sources and role == 'Assistant':
                    markdown_lines.append("\n**Sources:**")
                    for j, source in enumerate(sources, 1):
                        if isinstance(source, dict):
                            title = source.get('title', 'Unknown Source')
                            url = source.get('url', '')
                            score = source.get('score', 'N/A')
                            markdown_lines.append(f"{j}. **{title}** (Score: {score})")
                            if url:
                                markdown_lines.append(f"   - URL: {url}")
                        else:
                            markdown_lines.append(f"{j}. {source}")
                
                markdown_lines.append("\n---\n")
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            filename = f"conversation_{safe_title}_{timestamp}.md"
            filepath = self.export_dir / filename
            
            # Write markdown file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(markdown_lines))
            
            self.logger.info(f"✅ Exported conversation {thread_id} to {filename}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error exporting conversation as Markdown: {e}")
            return None
    
    def export_conversation_pdf(self, thread_id: int, session_id: str) -> Optional[str]:
        """Export conversation as PDF file (requires reportlab)"""
        if not PDF_AVAILABLE:
            self.logger.warning("❌ PDF export not available - reportlab not installed")
            return None
        
        try:
            # Get conversation metadata
            conversations = self.conversation_storage.get_user_conversations(session_id, limit=100)
            conversation_meta = next((c for c in conversations if c['id'] == thread_id), None)
            
            if not conversation_meta:
                self.logger.error(f"❌ Conversation {thread_id} not found")
                return None
            
            # Get conversation messages
            messages = self.conversation_storage.get_conversation_history(thread_id)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = conversation_meta.get('title', 'Untitled Conversation')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            filename = f"conversation_{safe_title}_{timestamp}.pdf"
            filepath = self.export_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
            )
            
            message_style = ParagraphStyle(
                'MessageStyle',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=20,
                spaceAfter=12,
            )
            
            # Title page
            story.append(Paragraph(title, title_style))
            story.append(Paragraph(f"Conversation ID: {thread_id}", styles['Normal']))
            story.append(Paragraph(f"Created: {conversation_meta.get('created_at', 'Unknown')}", styles['Normal']))
            story.append(Paragraph(f"Total Messages: {len(messages)}", styles['Normal']))
            story.append(Paragraph(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
            
            # Messages
            for i, message in enumerate(messages, 1):
                role = message['role'].title()
                content = message['content']
                timestamp = message.get('timestamp', 'Unknown')
                
                # Message header
                story.append(Paragraph(f"{role} Message {i}", styles['Heading2']))
                story.append(Paragraph(f"Time: {timestamp}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
                
                # Message content
                # Escape HTML characters and handle long text
                content_escaped = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(content_escaped, message_style))
                
                # Add sources if available
                sources = message.get('sources', [])
                if sources and role == 'Assistant':
                    story.append(Paragraph("Sources:", styles['Heading3']))
                    for j, source in enumerate(sources, 1):
                        if isinstance(source, dict):
                            source_text = f"{j}. {source.get('title', 'Unknown Source')} (Score: {source.get('score', 'N/A')})"
                            story.append(Paragraph(source_text, styles['Normal']))
                
                story.append(Spacer(1, 0.3*inch))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"✅ Exported conversation {thread_id} to {filename}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error exporting conversation as PDF: {e}")
            return None
    
    def create_shareable_link(self, thread_id: int, session_id: str, expiry_hours: int = 24) -> Optional[str]:
        """Create a shareable link for a conversation"""
        try:
            # Generate unique share ID
            share_id = str(uuid.uuid4())
            
            # Store share information (in a real implementation, you'd store this in a database)
            share_data = {
                'share_id': share_id,
                'thread_id': thread_id,
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now().timestamp() + expiry_hours * 3600),
                'access_count': 0
            }
            
            # Save share data to file (temporary implementation)
            share_file = self.export_dir / f"share_{share_id}.json"
            with open(share_file, 'w') as f:
                json.dump(share_data, f)
            
            # Generate shareable URL (replace with your actual domain)
            share_url = f"https://your-domain.com/shared/{share_id}"
            
            self.logger.info(f"✅ Created shareable link for conversation {thread_id}")
            return share_url
            
        except Exception as e:
            self.logger.error(f"❌ Error creating shareable link: {e}")
            return None
    
    def generate_conversation_summary(self, thread_id: int, session_id: str) -> Optional[Dict]:
        """Generate a comprehensive conversation summary"""
        try:
            # Get conversation data
            conversations = self.conversation_storage.get_user_conversations(session_id, limit=100)
            conversation_meta = next((c for c in conversations if c['id'] == thread_id), None)
            
            if not conversation_meta:
                return None
            
            messages = self.conversation_storage.get_conversation_history(thread_id)
            
            # Analyze conversation
            user_messages = [m for m in messages if m['role'] == 'user']
            assistant_messages = [m for m in messages if m['role'] == 'assistant']
            
            # Extract topics and sources
            all_sources = []
            for msg in assistant_messages:
                sources = msg.get('sources', [])
                if isinstance(sources, list):
                    all_sources.extend(sources)
            
            unique_sources = len(set(source.get('title', '') if isinstance(source, dict) else str(source) 
                                   for source in all_sources))
            
            # Generate summary
            summary = {
                'conversation_id': thread_id,
                'title': conversation_meta.get('title', 'Untitled'),
                'duration': conversation_meta.get('updated_at'),
                'total_messages': len(messages),
                'user_questions': len(user_messages),
                'assistant_responses': len(assistant_messages),
                'unique_sources_referenced': unique_sources,
                'total_characters': sum(len(m['content']) for m in messages),
                'avg_response_length': sum(len(m['content']) for m in assistant_messages) / max(len(assistant_messages), 1),
                'topics_discussed': self._extract_conversation_topics(messages),
                'key_sources': self._get_top_sources(all_sources),
                'generated_at': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Error generating conversation summary: {e}")
            return None
    
    def _extract_conversation_topics(self, messages: List[Dict], max_topics: int = 5) -> List[str]:
        """Extract main topics from conversation"""
        try:
            # Simple topic extraction based on common words
            all_text = " ".join(m['content'] for m in messages if m['role'] == 'user')
            
            # Basic keyword extraction (in production, use proper NLP)
            words = all_text.lower().split()
            
            # Filter for meaningful words (length > 3, not common words)
            common_words = {'what', 'how', 'when', 'where', 'why', 'can', 'could', 'would', 'should', 'the', 'and', 'or', 'but'}
            meaningful_words = [w for w in words if len(w) > 3 and w not in common_words]
            
            # Count frequency
            word_freq = {}
            for word in meaningful_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Return top topics
            topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [topic[0] for topic in topics[:max_topics]]
            
        except Exception:
            return []
    
    def _get_top_sources(self, sources: List, max_sources: int = 5) -> List[Dict]:
        """Get most frequently referenced sources"""
        try:
            source_freq = {}
            
            for source in sources:
                if isinstance(source, dict):
                    title = source.get('title', 'Unknown')
                    if title in source_freq:
                        source_freq[title]['count'] += 1
                    else:
                        source_freq[title] = {
                            'title': title,
                            'url': source.get('url', ''),
                            'count': 1
                        }
            
            # Sort by frequency
            top_sources = sorted(source_freq.values(), key=lambda x: x['count'], reverse=True)
            return top_sources[:max_sources]
            
        except Exception:
            return []
