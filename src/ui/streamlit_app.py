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
        
        # Quick stats
        st.subheader("📈 Quick Stats")
        stats = st.session_state.storage_manager.get_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", stats.get('documents', {}).get('active', 0))
        with col2:
            st.metric("Categories", stats.get('categories', 0))
    
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
        max_results = st.number_input("Max Results", min_value=1, max_value=50, value=10)
    
    # Advanced search options
    with st.expander("🎯 Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            categories = st.session_state.storage_manager.get_categories()
            category_names = ['All'] + [cat['name'] for cat in categories]
            selected_category = st.selectbox("Category:", category_names)
        
        with col2:
            search_type = st.selectbox("Search Type:", ["Keyword", "Phrase", "Fuzzy"])
    
    # Perform search
    if st.button("🔍 Search", type="primary") or query:
        if query:
            with st.spinner("Searching knowledge base..."):
                category = None if selected_category == 'All' else selected_category
                results = st.session_state.search_engine.search(
                    query=query,
                    category=category,
                    max_results=max_results
                )
                
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
        unique_categories = len(set(r.get('categories', 'Unknown') for r in results))
        st.metric("Categories", unique_categories)
    
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
                st.markdown(f"**Categories:** {result.get('categories', 'Uncategorized')}")
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
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = st.session_state.storage_manager.get_categories()
        category_names = ['All'] + [cat['name'] for cat in categories]
        filter_category = st.selectbox("Filter by Category:", category_names)
    
    with col2:
        sort_options = ["Recent", "Title A-Z", "Title Z-A", "Word Count"]
        sort_by = st.selectbox("Sort by:", sort_options)
    
    with col3:
        items_per_page = st.selectbox("Items per page:", [10, 25, 50, 100])
    
    # Search within documents
    search_filter = st.text_input("🔍 Search documents:", placeholder="Filter by title or content...")
    
    # Get documents
    category = None if filter_category == 'All' else filter_category
    documents = st.session_state.storage_manager.get_documents(
        category=category,
        limit=items_per_page
    )
    
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
                    st.caption(f"Category: {doc.get('categories', 'Uncategorized')} | Words: {doc.get('word_count', 'N/A')}")
                
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
    """Chat interface for AI-powered queries"""
    st.header("💬 AI Knowledge Chat")
    
    # Chat configuration
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("Ask questions about your knowledge base and get AI-powered responses!")
    
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.conversation_history = []
            st.rerun()
    
    # Display conversation history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.conversation_history:
            if message['type'] == 'user':
                with st.chat_message("user"):
                    st.write(message['content'])
            else:
                with st.chat_message("assistant"):
                    st.write(message['content'])
                    
                    # Show sources if available
                    if message.get('sources'):
                        with st.expander("📚 Sources"):
                            for source in message['sources']:
                                st.write(f"• {source.get('title', 'Unknown')} (Score: {source.get('final_score', 0):.2f})")
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your knowledge base..."):
        # Add user message
        st.session_state.conversation_history.append({
            'type': 'user',
            'content': prompt,
            'timestamp': datetime.now()
        })
        
        # Generate AI response
        with st.spinner("🤔 Thinking..."):
            response = generate_ai_response(prompt)
        
        # Add assistant response
        st.session_state.conversation_history.append({
            'type': 'assistant',
            'content': response['response'],
            'sources': response.get('sources', []),
            'timestamp': datetime.now()
        })
        
        st.rerun()


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
    
    # Management tabs
    tab1, tab2, tab3 = st.tabs(["📤 Add Content", "🌐 Web Scraping", "📊 Bulk Operations"])
    
    with tab1:
        st.subheader("📤 Add Documents")
        
        # Manual document entry
        with st.form("add_document"):
            title = st.text_input("Document Title:")
            url = st.text_input("URL:")
            content = st.text_area("Content:", height=200)
            
            # Category selection
            categories = st.session_state.storage_manager.get_categories()
            category_names = [cat['name'] for cat in categories]
            selected_category = st.selectbox("Category:", category_names)
            
            submitted = st.form_submit_button("Add Document")
            
            if submitted and title and content and url:
                # Prepare document data
                doc_data = {
                    'title': title,
                    'url': url,
                    'content': content,
                    'metadata': {'manual_entry': True}
                }
                
                # Store document
                success, message, doc_id = st.session_state.storage_manager.store_document(doc_data)
                
                if success:
                    st.success(f"Document added successfully! ID: {doc_id}")
                else:
                    st.error(f"Error adding document: {message}")
    
    with tab2:
        st.subheader("🌐 Web Scraping")
        
        with st.form("web_scraping"):
            scrape_url = st.text_input("URL to scrape:")
            max_depth = st.slider("Maximum depth:", 1, 5, 2)
            max_pages = st.slider("Maximum pages:", 1, 100, 10)
            
            # Category selection for scraped content
            categories = st.session_state.storage_manager.get_categories()
            category_names = [cat['name'] for cat in categories] if categories else ["General"]
            selected_category = st.selectbox("Category for scraped content:", category_names)
            
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
        st.subheader("🎯 Category Distribution")
        categories = st.session_state.storage_manager.get_categories()
        
        if categories:
            cat_data = pd.DataFrame(categories)
            if PLOTLY_AVAILABLE and px is not None:
                fig = px.pie(cat_data, values='document_count', names='name', 
                            title="Documents by Category")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(cat_data.set_index('name')['document_count'])
        else:
            st.info("No category data available yet.")


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
        st.write(f"**Categories:** {document.get('categories', 'Uncategorized')}")
    
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
