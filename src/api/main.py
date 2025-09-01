"""
FastAPI main application for Smart Knowledge Repository
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import logging
from datetime import datetime

from ..core.database import DatabaseManager
from ..storage.storage_manager import StorageManager
from ..search.search_engine import SearchEngine
from ..ai.scope_chatbot import ScopeAwareChatbot
from ..crawlers.web_scraper import WebScraper
from .models import (
    QueryRequest, QueryResponse, SearchRequest, SearchResponse,
    DocumentRequest, DocumentResponse, SystemStats
)

# Setup logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Smart Knowledge Repository API",
    description="AI-powered knowledge management with advanced RAG capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components - initialized on startup
db_manager: Optional[DatabaseManager] = None
storage_manager: Optional[StorageManager] = None
search_engine: Optional[SearchEngine] = None
chatbot: Optional[ScopeAwareChatbot] = None
web_scraper: Optional[WebScraper] = None


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global db_manager, storage_manager, search_engine, chatbot, web_scraper
    
    try:
        logger.info("Initializing Smart Knowledge Repository API...")
        
        # Initialize core components
        db_manager = DatabaseManager()
        storage_manager = StorageManager(db_manager)
        search_engine = SearchEngine(db_manager)
        web_scraper = WebScraper()
        
        # Initialize AI chatbot
        chatbot = ScopeAwareChatbot(storage_manager, search_engine)
        
        logger.info("✅ API components initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize API components: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Smart Knowledge Repository API...")


def get_storage_manager() -> StorageManager:
    """Dependency to get storage manager"""
    if storage_manager is None:
        raise HTTPException(status_code=500, detail="Storage manager not initialized")
    return storage_manager


def get_search_engine() -> SearchEngine:
    """Dependency to get search engine"""
    if search_engine is None:
        raise HTTPException(status_code=500, detail="Search engine not initialized")
    return search_engine


def get_chatbot() -> ScopeAwareChatbot:
    """Dependency to get chatbot"""
    if chatbot is None:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    return chatbot


def get_web_scraper() -> WebScraper:
    """Dependency to get web scraper"""
    if web_scraper is None:
        raise HTTPException(status_code=500, detail="Web scraper not initialized")
    return web_scraper


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": db_manager is not None,
            "storage": storage_manager is not None,
            "search": search_engine is not None,
            "chatbot": chatbot is not None,
            "scraper": web_scraper is not None
        }
    }


# System information endpoint
@app.get("/system/stats", response_model=SystemStats)
async def get_system_stats(storage: StorageManager = Depends(get_storage_manager)):
    """Get system statistics"""
    try:
        stats = storage.get_statistics()
        return SystemStats(
            documents_count=stats.get('documents', {}).get('active', 0),
            categories_count=stats.get('categories', 0),
            total_queries=0,  # This would come from usage tracking
            system_health="healthy",
            last_updated=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat endpoints
@app.post("/chat/query", response_model=QueryResponse)
async def process_chat_query(
    request: QueryRequest,
    chatbot: ScopeAwareChatbot = Depends(get_chatbot)
):
    """Process a chat query using the AI chatbot"""
    try:
        response = chatbot.process_query(request.query, request.context)
        
        return QueryResponse(
            response=response.get('response', ''),
            sources=response.get('sources', []),
            citations=response.get('citations', []),
            confidence=response.get('confidence', 0.0),
            knowledge_gaps=response.get('knowledge_gaps', []),
            scope=response.get('scope', 'unknown'),
            domain=response.get('domain', 'general'),
            intent=response.get('intent', 'unknown'),
            query_analysis=response.get('query_analysis', {})
        )
        
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/history")
async def get_chat_history(
    format_type: str = "json",
    chatbot: ScopeAwareChatbot = Depends(get_chatbot)
):
    """Get chat conversation history"""
    try:
        history = chatbot.get_conversation_history(format_type)
        return {"history": history, "format": format_type}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat/history")
async def clear_chat_history(chatbot: ScopeAwareChatbot = Depends(get_chatbot)):
    """Clear chat conversation history"""
    try:
        chatbot.clear_conversation_context()
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Search endpoints
@app.post("/search", response_model=SearchResponse)
async def search_knowledge_base(
    request: SearchRequest,
    search_engine: SearchEngine = Depends(get_search_engine)
):
    """Search the knowledge base"""
    try:
        results = search_engine.search(
            query=request.query,
            category=request.category,
            max_results=request.max_results,
            search_type=request.search_type
        )
        
        # Filter by minimum score if specified
        if request.min_score:
            results = [r for r in results if r.get('score', 0) >= request.min_score]
        
        return SearchResponse(
            results=results,
            total_count=len(results),
            query=request.query,
            search_type=request.search_type
        )
        
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Document management endpoints
@app.post("/documents", response_model=DocumentResponse)
async def add_document(
    request: DocumentRequest,
    storage: StorageManager = Depends(get_storage_manager)
):
    """Add a new document to the knowledge base"""
    try:
        document_id = storage.store_document(
            title=request.title,
            content=request.content,
            url=request.url,
            category=request.category,
            content_type=request.content_type,
            metadata=request.metadata
        )
        
        return DocumentResponse(
            document_id=document_id,
            message="Document added successfully",
            title=request.title
        )
        
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def get_documents(
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    storage: StorageManager = Depends(get_storage_manager)
):
    """Get documents from the knowledge base"""
    try:
        documents = storage.get_documents(
            category=category,
            limit=limit,
            offset=offset
        )
        
        return {
            "documents": documents,
            "limit": limit,
            "offset": offset,
            "category": category
        }
        
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/categories")
async def get_categories(storage: StorageManager = Depends(get_storage_manager)):
    """Get available document categories"""
    try:
        categories = storage.get_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Web scraping endpoints
@app.post("/scrape")
async def scrape_url(
    url: str,
    category: str = "General",
    scraper: WebScraper = Depends(get_web_scraper),
    storage: StorageManager = Depends(get_storage_manager)
):
    """Scrape a URL and add to knowledge base"""
    try:
        # Scrape the URL using the scrape_website method
        documents = await scraper.scrape_website(url, max_depth=1)
        
        if documents:
            # Store the first document (the main page)
            doc = documents[0]
            document_id = storage.store_document(
                title=doc.title,
                content=doc.content,
                url=doc.url,
                category=category,
                content_type='webpage'
            )
            
            return {
                "message": "URL scraped and stored successfully",
                "document_id": document_id,
                "title": doc.title,
                "url": doc.url,
                "documents_found": len(documents)
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to scrape URL")
            
    except Exception as e:
        logger.error(f"Error scraping URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Smart Knowledge Repository API",
        "version": "1.0.0",
        "description": "AI-powered knowledge management with advanced RAG capabilities",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
