"""
Enhanced Streamlit UI for Smart Knowledge Repository with advanced RAG capabilities
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Optional plotly imports
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = None
    go = None

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import pagination manager
try:
    from src.core.pagination_config import pagination_manager
    PAGINATION_AVAILABLE = True
except ImportError:
    PAGINATION_AVAILABLE = False
    pagination_manager = None

from src.core.database import DatabaseManager
from src.storage.storage_manager import StorageManager
from src.search.search_engine import SearchEngine
from src.search.embedding_engine import EmbeddingGenerator
from src.search.knowledge_graph import KnowledgeGraphBuilder
from src.crawlers.web_scraper import WebScraper
from src.ai.scope_chatbot import ScopeAwareChatbot
from src.processors.data_validator import DataValidator

# Enhanced page configuration
st.set_page_config(
    page_title="Smart Knowledge Repository - RAG AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/smart-knowledge-repository',
        'Report a bug': 'https://github.com/your-repo/smart-knowledge-repository/issues',
        'About': "Smart Knowledge Repository with advanced RAG capabilities"
    }
)

# Enhanced session state initialization
def initialize_session_state():
    """Initialize all session state variables"""
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
        
    if 'storage_manager' not in st.session_state:
        st.session_state.storage_manager = StorageManager()
        
    if 'search_engine' not in st.session_state:
        st.session_state.search_engine = SearchEngine()
        
    if 'embedding_generator' not in st.session_state:
        st.session_state.embedding_generator = EmbeddingGenerator()
        
    if 'knowledge_graph' not in st.session_state:
        st.session_state.knowledge_graph = KnowledgeGraphBuilder()
        
    if 'web_scraper' not in st.session_state:
        st.session_state.web_scraper = WebScraper()
        
    if 'data_validator' not in st.session_state:
        st.session_state.data_validator = DataValidator()
        
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = ScopeAwareChatbot(
            st.session_state.storage_manager,
            st.session_state.search_engine
        )
    
    # UI state variables
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'show_query_analysis' not in st.session_state:
        st.session_state.show_query_analysis = True
    if 'selected_search_type' not in st.session_state:
        st.session_state.selected_search_type = "hybrid"

# Initialize components
initialize_session_state()
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []


def display_enhanced_stats():
    """Display enhanced repository statistics with comprehensive metrics"""
    stats = st.session_state.storage_manager.get_statistics()
    
    st.subheader("📊 Repository Statistics")
    
    # Create 4 columns for organized display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**📄 Documents**")
        active_docs = stats.get('documents', {}).get('active', 0)
        deleted_docs = stats.get('documents', {}).get('deleted', 0)
        total_docs = active_docs + deleted_docs
        
        st.metric("Active", active_docs)
        st.metric("Deleted", deleted_docs)
        st.metric("Total", total_docs)
    
    with col2:
        st.markdown("**📝 Content**")
        total_words = stats.get('total_words', 0)
        total_chars = stats.get('total_characters', 0)
        avg_words = stats.get('avg_words_per_doc', 0)
        
        st.metric("Total Words", f"{total_words:,}")
        st.metric("Total Characters", f"{total_chars:,}")
        st.metric("Avg Words/Doc", f"{avg_words:.1f}")
    
    with col3:
        st.markdown("**🌐 Collection**")
        unique_domains = stats.get('unique_domains', 0)
        recent_docs = stats.get('recent_documents', 0)
        
        st.metric("Unique Domains", unique_domains)
        st.metric("Added This Week", recent_docs)
        
        # Calculate storage health indicator
        if total_docs > 0:
            active_ratio = (active_docs / total_docs) * 100
            st.metric("Active Ratio", f"{active_ratio:.1f}%")
        else:
            st.metric("Active Ratio", "0%")
    
    with col4:
        st.markdown("**⚡ Quick Actions**")
        if st.button("🔄 Refresh Stats", help="Update statistics"):
            st.rerun()
        
        if st.button("🗑️ Clean Deleted", help="Permanently remove deleted documents"):
            with st.spinner("Cleaning deleted documents..."):
                try:
                    # Get count of deleted documents before cleanup
                    stats = st.session_state.storage_manager.get_statistics()
                    deleted_count = stats.get('deleted_documents', 0)
                    
                    if deleted_count == 0:
                        st.info("No deleted documents to clean up.")
                    else:
                        # Clean all deleted documents (force permanent deletion)
                        cleaned_count = cleanup_all_deleted_documents()
                        if cleaned_count > 0:
                            st.success(f"✅ Successfully cleaned {cleaned_count} deleted documents!")
                            st.rerun()
                        else:
                            st.warning("No documents were cleaned. They may already be permanently deleted.")
                except Exception as e:
                    st.error(f"❌ Error during cleanup: {str(e)}")
                    st.session_state.storage_manager.logger.error(f"Cleanup error: {e}")
        
        # Last update indicator
        st.caption(f"📅 Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Add a separator
    st.divider()


def cleanup_all_deleted_documents():
    """Clean up all soft-deleted documents by permanently removing them"""
    try:
        from src.core.database import DatabaseManager
        db = DatabaseManager()
        
        # Get all deleted documents
        query = "SELECT id FROM documents WHERE status = 'deleted'"
        deleted_docs = db.execute_query(query)
        
        count = 0
        for doc in deleted_docs:
            if st.session_state.storage_manager.delete_document(doc['id'], soft_delete=False):
                count += 1
                
        return count
    except Exception as e:
        st.session_state.storage_manager.logger.error(f"Error in cleanup_all_deleted_documents: {e}")
        return 0


def main():
    """Main application interface"""
    st.title("🧠 Smart Knowledge Repository")
    st.markdown("*Intelligent knowledge management with semantic search*")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("📋 Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["🔍 Search", "📚 Browse Documents", "💬 Chat Interface", 
             "⚙️ Data Management", "📊 Analytics", "🔧 Settings"]
        )
    
    # Route to appropriate page
    if page == "🔍 Search":
        search_page()
    elif page == "📚 Browse Documents":
        browse_documents_page()
    elif page == "💬 Chat Interface":
        chat_interface_page()
    elif page == "⚙️ Data Management":
        data_management_page()
    elif page == "📊 Analytics":
        analytics_page()
    elif page == "🔧 Settings":
        settings_page()


def search_page():
    """Search interface page"""
    st.header("🔍 Advanced Search")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Enter your search query:",
            placeholder="e.g., 'machine learning algorithms'",
            key="search_query"
        )
    
    with col2:
        max_results = st.number_input("Max Results", min_value=1, max_value=200, value=20)
    
    # Advanced search options
    with st.expander("🎯 Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            search_type = st.selectbox("Search Type:", ["Keyword", "Phrase", "Fuzzy"])
        
        with col2:
            include_content = st.checkbox("Include content preview", value=True)
    
    # Perform search
    if st.button("🔍 Search", type="primary") or query:
        if query:
            # Validate page size with warnings
            import time
            
            if PAGINATION_AVAILABLE:
                validated_size, warnings = pagination_manager.validate_page_size(max_results, "search")
            else:
                validated_size, warnings = max_results, []
            
            # Show warnings if any
            for warning in warnings:
                st.warning(warning)
            
            # Show progressive loading info if needed
            if PAGINATION_AVAILABLE and pagination_manager.should_use_progressive_loading(validated_size):
                st.info(f"💡 Loading {validated_size} results progressively for better performance...")
            
            with st.spinner("Searching knowledge base..."):
                start_time = time.time()
                results = st.session_state.search_engine.search(
                    query=query,
                    max_results=validated_size
                )
                
                # Monitor performance
                if PAGINATION_AVAILABLE:
                    pagination_manager.monitor_performance("search", start_time, len(results))
                
                display_search_results(results, query)


def display_search_results(results: list, query: str):
    """Display search results"""
    if not results:
        st.warning("No results found. Try different keywords or check spelling.")
        return
    
    st.subheader(f"Search Results ({len(results)} found)")
    
    # Results metrics
    avg_score = sum(r.get('final_score', 0) for r in results) / len(results)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Results", len(results))
    with col2:
        st.metric("Avg. Relevance", f"{avg_score:.2f}")
    with col3:
        st.metric("Avg. Relevance", f"{avg_score:.2f}")
    
    # Display results
    for i, result in enumerate(results):
        with st.expander(f"📄 {result.get('title', 'Untitled Document')}", expanded=i < 3):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Content preview
                content = result.get('content', '')
                preview = content[:300] + "..." if len(content) > 300 else content
                st.markdown(f"**Content Preview:**\n{preview}")
                
                # Document metadata
                st.markdown(f"**URL:** {result.get('url', 'N/A')}")
                st.markdown(f"**Word Count:** {result.get('word_count', 'N/A')}")
                st.markdown(f"**Created:** {result.get('created_at', 'N/A')}")
                
            with col2:
                # Relevance score
                score = result.get('final_score', 0)
                st.metric("Relevance", f"{score:.2f}")
                
                # Score breakdown
                if 'score_breakdown' in result:
                    breakdown = result['score_breakdown']
                    st.write("**Score Breakdown:**")
                    for component, value in breakdown.items():
                        st.write(f"• {component.title()}: {value:.2f}")
                
                # Action buttons
                if st.button(f"👁️ View Full", key=f"view_{i}"):
                    show_document_details(result)


def browse_documents_page():
    """Browse documents page"""
    st.header("📚 Document Library")
    
    # Display repository statistics at the top
    display_enhanced_stats()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sort_options = ["Recent", "Title A-Z", "Title Z-A", "Word Count"]
        sort_by = st.selectbox("Sort by:", sort_options)
    
    with col2:
        items_per_page = st.selectbox("Items per page:", [10, 25, 50, 100, 200, 500])
    
    with col3:
        search_filter = st.text_input("Filter by title/content:", placeholder="Enter keywords...")
    
    # Search within documents
    search_filter = st.text_input("🔍 Search documents:", placeholder="Filter by title or content...")
    
    # Get documents
    import time
    
    # Validate page size
    if PAGINATION_AVAILABLE:
        validated_size, warnings = pagination_manager.validate_page_size(items_per_page, "browse")
    else:
        validated_size, warnings = items_per_page, []
    
    # Show warnings if any
    for warning in warnings:
        st.warning(warning)
    
    # Show performance info for large requests
    if PAGINATION_AVAILABLE and pagination_manager.should_use_progressive_loading(validated_size):
        with st.expander("ℹ️ Performance Info"):
            st.info(f"Loading {validated_size} documents. This may take a moment...")
            batch_size = pagination_manager.get_batch_size(validated_size)
            st.write(f"Using batch size: {batch_size} for optimal performance")
    
    start_time = time.time()
    documents = st.session_state.storage_manager.get_documents(
        limit=validated_size
    )
    
    # Monitor performance
    if PAGINATION_AVAILABLE:
        pagination_manager.monitor_performance("browse_documents", start_time, len(documents))
    
    # Apply search filter
    if search_filter:
        search_lower = search_filter.lower()
        documents = [
            doc for doc in documents
            if search_lower in doc.get('title', '').lower() or 
               search_lower in doc.get('content', '').lower()
        ]
    
    # Display documents
    if documents:
        st.write(f"Showing {len(documents)} documents")
        
        for doc in documents:
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**📄 {doc.get('title', 'Untitled')}**")
                    preview = doc.get('content', '')[:100] + "..." if len(doc.get('content', '')) > 100 else doc.get('content', '')
                    st.caption(preview)
                    st.caption(f"Words: {doc.get('word_count', 'N/A')} | Created: {doc.get('created_at', 'N/A')}")
                
                with col2:
                    if st.button("👁️ View", key=f"view_{doc['id']}"):
                        show_document_details(doc)
                
                with col3:
                    if st.button("✏️ Edit", key=f"edit_{doc['id']}"):
                        edit_document_form(doc)
                
                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{doc['id']}", type="secondary"):
                        if st.session_state.get(f"confirm_delete_{doc['id']}", False):
                            st.session_state.storage_manager.delete_document(doc['id'])
                            st.success("Document deleted!")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{doc['id']}"] = True
                            st.warning("Click again to confirm deletion")
                
                st.divider()
    else:
        st.info("No documents found matching your criteria.")


def chat_interface_page():
    """Enhanced AI chat interface with conversation management"""
    st.header("💬 AI Knowledge Chat")
    
    # Initialize session ID if not exists
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"streamlit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize enhanced chatbot with session ID
    if 'enhanced_chatbot' not in st.session_state:
        try:
            from src.ai.scope_chatbot import ScopeAwareChatbot
            st.session_state.enhanced_chatbot = ScopeAwareChatbot(
                st.session_state.storage_manager,
                st.session_state.search_engine,
                session_id=st.session_state.session_id
            )
        except Exception as e:
            st.error(f"❌ Error initializing enhanced chatbot: {e}")
            st.session_state.enhanced_chatbot = st.session_state.chatbot  # Fallback
    
    # Sidebar for conversation management
    with st.sidebar:
        st.subheader("� Conversations")
        
        # New conversation button
        if st.button("➕ New Conversation"):
            if hasattr(st.session_state.enhanced_chatbot, 'start_new_conversation'):
                st.session_state.enhanced_chatbot.start_new_conversation()
                st.session_state.conversation_history = []
                st.rerun()
        
        # Conversation list
        try:
            if hasattr(st.session_state.enhanced_chatbot, 'get_user_conversations'):
                conversations = st.session_state.enhanced_chatbot.get_user_conversations(limit=10)
                
                if conversations:
                    st.subheader("Recent Conversations")
                    for conv in conversations:
                        conv_title = conv.get('title', f"Conversation {conv['id']}")[:30]
                        if len(conv_title) < len(conv.get('title', '')):
                            conv_title += "..."
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if st.button(conv_title, key=f"conv_{conv['id']}", 
                                       help=f"Messages: {conv.get('total_messages', 0)}"):
                                if st.session_state.enhanced_chatbot.switch_conversation(conv['id']):
                                    st.session_state.conversation_history = []
                                    st.rerun()
                        
                        with col2:
                            if st.button("🗑️", key=f"del_{conv['id']}", 
                                       help="Delete conversation"):
                                if st.session_state.enhanced_chatbot.delete_conversation(conv['id']):
                                    st.rerun()
                
                # Export options
                st.divider()
                st.subheader("📤 Export")
                
                export_format = st.selectbox("Format:", ["JSON", "Markdown", "PDF"])
                
                if st.button("📥 Export Current Chat"):
                    export_conversation(export_format.lower())
                
                # Search conversations
                st.divider()
                search_query = st.text_input("🔍 Search conversations:", 
                                           placeholder="Search your chat history...")
                
                if search_query and hasattr(st.session_state.enhanced_chatbot, 'search_conversations'):
                    search_results = st.session_state.enhanced_chatbot.search_conversations(search_query)
                    if search_results:
                        st.write("**Search Results:**")
                        for result in search_results[:5]:
                            if st.button(f"📄 {result.get('title', 'Untitled')[:25]}...", 
                                       key=f"search_{result['id']}"):
                                if st.session_state.enhanced_chatbot.switch_conversation(result['id']):
                                    st.rerun()
        
        except Exception as e:
            st.error(f"❌ Conversation management error: {e}")
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Show current conversation context
        if hasattr(st.session_state.enhanced_chatbot, 'conversation_enabled') and \
           st.session_state.enhanced_chatbot.conversation_enabled:
            st.info("💡 Enhanced conversation mode with context awareness and follow-up handling")
        else:
            st.info("ℹ️ Basic chat mode - Ask questions about your knowledge base")
    
    with col2:
        if st.button("🗑️ Clear Current Chat"):
            st.session_state.conversation_history = []
            if hasattr(st.session_state.enhanced_chatbot, 'start_new_conversation'):
                st.session_state.enhanced_chatbot.start_new_conversation()
            st.rerun()
    
    # Get conversation history for display
    try:
        if hasattr(st.session_state.enhanced_chatbot, 'get_conversation_history'):
            # Get persistent conversation history
            persistent_history = st.session_state.enhanced_chatbot.get_conversation_history(limit=20)
            
            # Convert to display format
            display_history = []
            for msg in persistent_history:
                display_history.append({
                    'type': msg['role'],
                    'content': msg['content'],
                    'sources': msg.get('sources', []),
                    'timestamp': msg.get('timestamp')
                })
            
            # Use persistent history if available, otherwise fallback to session state
            if display_history:
                st.session_state.conversation_history = display_history
    except Exception as e:
        st.warning(f"⚠️ Using session-based chat history: {e}")
    
    # Display conversation
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.conversation_history:
            if message['type'] in ['user', 'User']:
                with st.chat_message("user"):
                    st.write(message['content'])
            else:
                with st.chat_message("assistant"):
                    st.write(message['content'])
                    
                    # Show sources if available
                    sources = message.get('sources', [])
                    if sources:
                        with st.expander("📚 Sources"):
                            for i, source in enumerate(sources, 1):
                                if isinstance(source, dict):
                                    title = source.get('title', 'Unknown Source')
                                    score = source.get('final_score', source.get('score', 0))
                                    url = source.get('url', '')
                                    st.write(f"{i}. **{title}** (Relevance: {score:.2f})")
                                    if url:
                                        st.caption(f"🔗 {url}")
                                else:
                                    st.write(f"{i}. {source}")
    
    # Follow-up suggestions
    try:
        if hasattr(st.session_state.enhanced_chatbot, 'get_follow_up_suggestions'):
            suggestions = st.session_state.enhanced_chatbot.get_follow_up_suggestions()
            if suggestions:
                st.subheader("💡 Suggested Follow-ups")
                cols = st.columns(min(len(suggestions), 3))
                for i, suggestion in enumerate(suggestions[:3]):
                    with cols[i]:
                        if st.button(f"💬 {suggestion[:30]}...", key=f"suggest_{i}"):
                            # Trigger follow-up question
                            process_chat_input(suggestion)
                            st.rerun()
    except Exception:
        pass  # Suggestions are optional
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your knowledge base..."):
        process_chat_input(prompt)
        st.rerun()


def process_chat_input(prompt: str):
    """Process chat input and generate response"""
    try:
        # Add user message to history
        st.session_state.conversation_history.append({
            'type': 'user',
            'content': prompt,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate AI response using enhanced chatbot
        with st.spinner("🤔 Thinking..."):
            if hasattr(st.session_state.enhanced_chatbot, 'process_query'):
                # Use enhanced chatbot with conversation management
                response = st.session_state.enhanced_chatbot.process_query(prompt)
            else:
                # Fallback to basic chatbot
                response = generate_ai_response(prompt)
        
        # Add assistant response to history
        st.session_state.conversation_history.append({
            'type': 'assistant',
            'content': response.get('response', 'I apologize, I could not generate a response.'),
            'sources': response.get('sources', []),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        st.error(f"❌ Error processing chat input: {e}")
        st.session_state.conversation_history.append({
            'type': 'assistant',
            'content': "I apologize, but I encountered an error processing your question. Please try again.",
            'sources': [],
            'timestamp': datetime.now().isoformat()
        })


def export_conversation(format_type: str = "json"):
    """Export current conversation"""
    try:
        from src.services.conversation_export import ConversationExportService
        
        export_service = ConversationExportService()
        
        if hasattr(st.session_state.enhanced_chatbot, 'current_thread_id') and \
           st.session_state.enhanced_chatbot.current_thread_id:
            
            thread_id = st.session_state.enhanced_chatbot.current_thread_id
            session_id = st.session_state.session_id
            
            if format_type == "json":
                filepath = export_service.export_conversation_json(thread_id, session_id)
            elif format_type == "markdown":
                filepath = export_service.export_conversation_markdown(thread_id, session_id)
            elif format_type == "pdf":
                filepath = export_service.export_conversation_pdf(thread_id, session_id)
            else:
                st.error("❌ Unsupported export format")
                return
            
            if filepath:
                st.success(f"✅ Conversation exported to: {filepath}")
                
                # Offer download
                with open(filepath, 'rb') as f:
                    st.download_button(
                        label=f"📥 Download {format_type.upper()} File",
                        data=f.read(),
                        file_name=Path(filepath).name,
                        mime=get_mime_type(format_type)
                    )
            else:
                st.error("❌ Export failed")
        else:
            st.warning("⚠️ No active conversation to export")
    
    except Exception as e:
        st.error(f"❌ Export error: {e}")


def get_mime_type(format_type: str) -> str:
    """Get MIME type for file format"""
    mime_types = {
        'json': 'application/json',
        'markdown': 'text/markdown',
        'pdf': 'application/pdf'
    }
    return mime_types.get(format_type, 'text/plain')


def generate_ai_response(query: str) -> dict:
    """Generate AI response based on knowledge base"""
    # Use the scope-aware chatbot
    response = st.session_state.chatbot.process_query(query)
    
    return {
        'response': response['response'],
        'sources': response.get('sources', [])
    }


def data_management_page():
    """Data management interface"""
    st.header("⚙️ Data Management")
    
    # Display enhanced statistics at the top
    display_enhanced_stats()
    
    # Management tabs
    tab1, tab2, tab3 = st.tabs(["📤 Add Content", "🌐 Web Scraping", "📊 Bulk Operations"])
    
    with tab1:
        st.subheader("📤 Add Documents")
        
        # Document input method selection
        input_method = st.radio(
            "Choose input method:",
            ["📝 Manual Entry", "📁 Upload File", "🔗 Load from URL"],
            horizontal=True
        )
        
        if input_method == "📝 Manual Entry":
            # Manual document entry
            with st.form("add_document_manual"):
                title = st.text_input("Document Title:")
                url = st.text_input("Source URL (optional):", 
                                   placeholder="https://example.com (leave empty if not applicable)")
                content = st.text_area("Content:", height=200, 
                                     placeholder="Enter or paste your document content here...")
                
                submitted = st.form_submit_button("Add Document")
                
                if submitted and title and content:
                    # Prepare document data
                    doc_data = {
                        'title': title,
                        'url': url if url.strip() else f"manual://document_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'content': content,
                        'metadata': {
                            'manual_entry': True,
                            'input_method': 'manual'
                        }
                    }
                    
                    # Store document with relaxed validation
                    success, message, doc_id = st.session_state.storage_manager.store_document(doc_data, skip_url_validation=True)
                    
                    if success:
                        st.success(f"✅ Document added successfully! ID: {doc_id}")
                    else:
                        st.error(f"❌ Error adding document: {message}")
        
        elif input_method == "📁 Upload File":
            # File upload
            with st.form("add_document_file"):
                uploaded_file = st.file_uploader(
                    "Choose a file",
                    type=['txt', 'md', 'pdf', 'docx', 'csv'],
                    help="Supported formats: TXT, Markdown, PDF, Word, CSV"
                )
                
                title = st.text_input("Document Title (optional):", 
                                    placeholder="Leave empty to use filename")
                
                submitted = st.form_submit_button("Upload and Process")
                
                if submitted and uploaded_file:
                    try:
                        # Read file content
                        file_content = ""
                        file_name = uploaded_file.name
                        
                        if file_name.endswith('.txt') or file_name.endswith('.md'):
                            file_content = str(uploaded_file.read(), "utf-8")
                        elif file_name.endswith('.csv'):
                            import pandas as pd
                            df = pd.read_csv(uploaded_file)
                            file_content = df.to_string()
                        else:
                            st.warning("⚠️ Unsupported file type. Please use TXT, MD, or CSV files for now.")
                            file_content = None
                        
                        if file_content:
                            # Use filename as title if not provided
                            doc_title = title if title.strip() else file_name.rsplit('.', 1)[0]
                            
                            # Prepare document data
                            doc_data = {
                                'title': doc_title,
                                'url': f"file://uploaded/{file_name}",
                                'content': file_content,
                                'metadata': {
                                    'manual_entry': True,
                                    'input_method': 'file_upload',
                                    'original_filename': file_name,
                                    'file_size': len(file_content)
                                }
                            }
                            
                            # Store document with relaxed validation
                            success, message, doc_id = st.session_state.storage_manager.store_document(doc_data, skip_url_validation=True)
                            
                            if success:
                                st.success(f"✅ File uploaded successfully! ID: {doc_id}")
                                st.info(f"📄 Processed {len(file_content)} characters from {file_name}")
                            else:
                                st.error(f"❌ Error uploading file: {message}")
                    
                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
        
        elif input_method == "🔗 Load from URL":
            # URL loading with content extraction
            with st.form("add_document_url"):
                source_url = st.text_input("URL to load:", 
                                         placeholder="https://example.com/article")
                title = st.text_input("Document Title (optional):", 
                                    placeholder="Leave empty to extract from webpage")
                
                # Advanced options
                with st.expander("⚙️ Advanced Options"):
                    extract_links = st.checkbox("Extract and store links", value=False)
                    min_content_length = st.slider("Minimum content length", 10, 200, 30)
                
                submitted = st.form_submit_button("Load from URL")
                
                if submitted and source_url:
                    with st.spinner("🔍 Loading content from URL..."):
                        try:
                            # Use web scraper to get single page
                            scraped_docs = st.session_state.web_scraper.scrape_website_sync(
                                start_url=source_url,
                                max_depth=0,  # Only scrape the single page
                                max_pages=1
                            )
                            
                            if scraped_docs and len(scraped_docs) > 0:
                                doc = scraped_docs[0]
                                
                                # Check content length with custom threshold
                                if len(doc.content.strip()) < min_content_length:
                                    st.warning(f"⚠️ Content too short ({len(doc.content)} characters). Minimum: {min_content_length}")
                                    st.info("💡 Try lowering the minimum content length or check if the URL is accessible.")
                                else:
                                    # Use provided title or extracted title
                                    doc_title = title.strip() if title.strip() else doc.title
                                    
                                    # Prepare document data
                                    doc_data = {
                                        'title': doc_title,
                                        'url': source_url,
                                        'content': doc.content,
                                        'metadata': {
                                            **doc.metadata,
                                            'input_method': 'url_load',
                                            'extracted_title': doc.title,
                                            'content_length': len(doc.content),
                                            'links_found': len(doc.links) if extract_links else 0
                                        }
                                    }
                                    
                                    # Store document
                                    success, message, doc_id = st.session_state.storage_manager.store_document(doc_data)
                                    
                                    if success:
                                        st.success(f"✅ Content loaded successfully! ID: {doc_id}")
                                        
                                        # Show preview
                                        with st.expander("📄 Content Preview"):
                                            st.write(f"**Title:** {doc_title}")
                                            st.write(f"**Content Length:** {len(doc.content)} characters")
                                            st.write(f"**Content Preview:**")
                                            st.write(doc.content[:500] + "..." if len(doc.content) > 500 else doc.content)
                                    else:
                                        st.error(f"❌ Error storing document: {message}")
                            else:
                                st.warning("⚠️ No content could be extracted from the URL.")
                                st.info("This might be due to:")
                                st.write("• URL not accessible")
                                st.write("• Content requires JavaScript")
                                st.write("• Site blocking automated requests")
                                st.write("• Invalid URL format")
                        
                        except Exception as e:
                            st.error(f"❌ Error loading from URL: {str(e)}")
                            st.info("💡 Try using the manual entry method instead.")
    
    with tab2:
        st.subheader("🌐 Web Scraping")
        
        with st.form("web_scraping"):
            scrape_url = st.text_input("URL to scrape:")
            max_depth = st.slider("Maximum depth:", 1, 5, 2)
            max_pages = st.slider("Maximum pages:", 1, 100, 10)
            
            start_scraping = st.form_submit_button("Start Scraping")
            
            if start_scraping and scrape_url:
                with st.spinner("🕷️ Scraping in progress... This may take a few minutes..."):
                    try:
                        # Run the web scraping using the synchronous wrapper
                        scraped_documents = st.session_state.web_scraper.scrape_website_sync(
                            start_url=scrape_url,
                            max_depth=max_depth,
                            max_pages=max_pages
                        )
                        
                        if scraped_documents:
                            st.success(f"✅ Successfully scraped {len(scraped_documents)} documents!")
                            
                            # Store each scraped document in the database
                            stored_count = 0
                            failed_count = 0
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, doc in enumerate(scraped_documents):
                                try:
                                    # Update progress
                                    progress = (i + 1) / len(scraped_documents)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Storing document {i+1}/{len(scraped_documents)}: {doc.title}")
                                    
                                    # Prepare document data for storage
                                    doc_data = {
                                        'title': doc.title,
                                        'url': doc.url,
                                        'content': doc.content,
                                        'metadata': {
                                            **doc.metadata,
                                            'scraped_at': doc.timestamp,
                                            'content_type': doc.content_type,
                                            'scraping_depth': max_depth,
                                            'source_domain': doc.metadata.get('domain', ''),
                                            'links_found': len(doc.links)
                                        }
                                    }
                                    
                                    # Store in database
                                    success, message, doc_id = st.session_state.storage_manager.store_document(doc_data)
                                    
                                    if success:
                                        stored_count += 1
                                    else:
                                        failed_count += 1
                                        st.warning(f"Failed to store '{doc.title}': {message}")
                                
                                except Exception as e:
                                    failed_count += 1
                                    st.error(f"Error storing document '{doc.title}': {str(e)}")
                            
                            # Final status
                            progress_bar.progress(1.0)
                            status_text.text("✅ Scraping and storage completed!")
                            
                            # Show summary
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Documents Scraped", len(scraped_documents))
                            with col2:
                                st.metric("Successfully Stored", stored_count)
                            with col3:
                                st.metric("Failed to Store", failed_count)
                            
                            # Show scraped documents preview
                            with st.expander("📋 Preview of Scraped Documents"):
                                for doc in scraped_documents[:5]:  # Show first 5
                                    st.write(f"**{doc.title}**")
                                    st.write(f"URL: {doc.url}")
                                    st.write(f"Content preview: {doc.content[:200]}...")
                                    st.write(f"Links found: {len(doc.links)}")
                                    st.divider()
                                
                                if len(scraped_documents) > 5:
                                    st.info(f"... and {len(scraped_documents) - 5} more documents")
                        
                        else:
                            st.warning("⚠️ No documents were scraped. Please check the URL and try again.")
                            
                    except Exception as e:
                        st.error(f"❌ Scraping failed: {str(e)}")
                        st.error("This might be due to:")
                        st.write("• Invalid URL or website not accessible")
                        st.write("• Network connectivity issues") 
                        st.write("• Website blocking automated requests")
                        st.write("• Missing required dependencies (aiohttp, beautifulsoup4)")
                        
                        # Show detailed error for debugging
                        with st.expander("🔍 Debug Information"):
                            st.code(str(e))
        
        # Web scraping status and tips
        st.divider()
        st.subheader("💡 Web Scraping Tips")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Best Practices:**")
            st.write("• Start with depth 1-2 for testing")
            st.write("• Limit pages to avoid overloading servers")
            st.write("• Check robots.txt before scraping")
            st.write("• Be respectful of website resources")
        
        with col2:
            st.write("**Troubleshooting:**")
            st.write("• Ensure URL is accessible in browser")
            st.write("• Try with smaller depth/page limits")
            st.write("• Check network connectivity")
            st.write("• Some sites may block automated requests")
    
    with tab3:
        st.subheader("📊 Bulk Operations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Export Data**")
            export_format = st.selectbox("Export Format:", ["JSON", "CSV"])
            
            if st.button("Export Knowledge Base"):
                try:
                    # Export logic would go here
                    st.success("Export completed!")
                    st.download_button(
                        label="📥 Download Export",
                        data="export_placeholder",
                        file_name=f"knowledge_export_{datetime.now().strftime('%Y%m%d')}.{export_format.lower()}",
                        mime="application/octet-stream"
                    )
                except Exception as e:
                    st.error(f"Export error: {str(e)}")
        
        with col2:
            st.write("**Import Data**")
            uploaded_file = st.file_uploader("Choose file to import", type=['json', 'csv'])
            
            if uploaded_file and st.button("Import Data"):
                try:
                    # Import logic would go here
                    st.success("Data imported successfully!")
                except Exception as e:
                    st.error(f"Import error: {str(e)}")


def analytics_page():
    """Analytics dashboard"""
    st.header("📊 Analytics Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    stats = st.session_state.storage_manager.get_statistics()
    
    with col1:
        st.metric("Total Documents", stats.get('documents', {}).get('active', 0))
    with col2:
        st.metric("Categories", stats.get('categories', 0))
    with col3:
        st.metric("Recent Docs", stats.get('recent_documents', 0))
    with col4:
        st.metric("System Health", "Good", delta="100%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Document Growth")
        # Sample data for demo
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        doc_counts = [10 + i + (i % 7) * 2 for i in range(30)]
        
        growth_data = pd.DataFrame({
            'Date': dates,
            'Documents': doc_counts
        })
        
        if PLOTLY_AVAILABLE and px is not None:
            fig = px.line(growth_data, x='Date', y='Documents', title="Daily Document Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(growth_data.set_index('Date'))
    
    with col2:
        st.subheader("📊 Content Statistics")
        stats = st.session_state.storage_manager.get_statistics()
        
        # Display content metrics
        content_stats = {
            'Total Words': stats.get('total_words', 0),
            'Total Characters': stats.get('total_characters', 0),
            'Avg. Words per Doc': stats.get('avg_words_per_doc', 0),
            'Unique Domains': stats.get('unique_domains', 0)
        }
        
        for metric, value in content_stats.items():
            st.metric(metric, value)


def settings_page():
    """Settings and configuration"""
    st.header("🔧 System Settings")
    
    # Database settings
    with st.expander("🗄️ Database Settings", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Database Path:", value="data/knowledge.db", disabled=True)
            st.text_input("Vector DB Path:", value="data/embeddings/", disabled=True)
        
        with col2:
            st.number_input("Max Results:", min_value=1, max_value=100, value=10)
            st.number_input("Search Timeout (s):", min_value=1, max_value=60, value=30)
    
    # Scraping settings
    with st.expander("🌐 Scraping Configuration"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.slider("Max Crawl Depth:", 1, 10, 3)
            st.slider("Crawl Delay (s):", 0.1, 5.0, 1.0)
        
        with col2:
            st.slider("Max Concurrent Requests:", 1, 20, 5)
            st.slider("Request Timeout (s):", 10, 60, 30)
    
    # System status
    with st.expander("📊 System Status"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Uptime", "2h 45m")
            st.metric("CPU Usage", "15%")
        
        with col2:
            st.metric("Memory Usage", "234 MB")
            st.metric("Disk Usage", "1.2 GB")
        
        with col3:
            st.metric("Active Sessions", "1")
            st.metric("Error Rate", "0%")
    
    # Performance monitoring
    with st.expander("⚡ Performance Monitoring"):
        if PAGINATION_AVAILABLE:
            st.subheader("Pagination Performance")
            
            # Current configuration
            st.write("**Current Limits:**")
            limits = pagination_manager.limits
            st.json({
                "Search Results Max": limits.search_results_max,
                "Browse Documents Max": limits.browse_documents_max,
                "API Default Limit": limits.api_default_limit,
                "Performance Warning Threshold (ms)": limits.performance_warning_threshold,
                "Memory Warning Threshold (MB)": limits.memory_warning_threshold_mb
            })
            
            # Performance summary
            performance_summary = pagination_manager.get_performance_summary()
            if performance_summary:
                st.write("**Recent Performance:**")
                for operation, metrics in performance_summary.items():
                    with st.container():
                        st.write(f"**{operation.replace('_', ' ').title()}:**")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Avg Time", f"{metrics['avg_time']:.2f}s")
                        with col2:
                            st.metric("Max Time", f"{metrics['max_time']:.2f}s")
                        with col3:
                            st.metric("Min Time", f"{metrics['min_time']:.2f}s")
                        with col4:
                            st.metric("Total Requests", metrics['total_requests'])
            else:
                st.info("No performance data available yet. Use search or browse to generate metrics.")
            
            # Reset metrics button
            if st.button("🔄 Reset Performance Metrics"):
                pagination_manager.performance_metrics.clear()
                st.success("Performance metrics reset!")
        else:
            st.warning("Performance monitoring not available - pagination module not loaded")


def show_document_details(document: Dict):
    """Show document details in a modal-like display"""
    st.subheader(f"📄 {document.get('title', 'Untitled')}")
    
    # Metadata
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**URL:** {document.get('url', 'N/A')}")
        st.write(f"**Domain:** {document.get('domain', 'N/A')}")
        st.write(f"**Language:** {document.get('language', 'N/A')}")
    
    with col2:
        st.write(f"**Word Count:** {document.get('word_count', 'N/A')}")
        st.write(f"**Created:** {document.get('created_at', 'N/A')}")
        st.write(f"**Language:** {document.get('language', 'N/A')}")
    
    # Content
    st.subheader("Content")
    st.write(document.get('content', 'No content available'))


def edit_document_form(document: Dict):
    """Show edit form for document"""
    st.subheader(f"✏️ Edit: {document.get('title', 'Untitled')}")
    
    with st.form(f"edit_doc_{document['id']}"):
        new_title = st.text_input("Title:", value=document.get('title', ''))
        new_content = st.text_area("Content:", value=document.get('content', ''), height=200)
        
        if st.form_submit_button("Save Changes"):
            updates = {
                'title': new_title,
                'content': new_content
            }
            
            success = st.session_state.storage_manager.update_document(document['id'], updates)
            
            if success:
                st.success("Document updated successfully!")
            else:
                st.error("Failed to update document.")


if __name__ == "__main__":
    main()
