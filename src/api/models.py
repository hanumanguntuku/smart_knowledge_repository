"""
Pydantic models for Smart Knowledge Repository API
"""
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for chat queries"""
    query: str
    context: Optional[Dict[str, Any]] = None


class Citation(BaseModel):
    """Citation model"""
    id: int
    title: str
    url: Optional[str] = None
    score: float
    excerpt: str


class QueryResponse(BaseModel):
    """Response model for chat queries"""
    response: str
    sources: List[str]
    citations: List[Citation]
    confidence: float
    knowledge_gaps: List[str]
    scope: str
    domain: str
    intent: str
    query_analysis: Dict[str, Any]


class SearchRequest(BaseModel):
    """Request model for search queries"""
    query: str
    category: Optional[str] = None
    max_results: int = 10
    search_type: str = "hybrid"
    min_score: Optional[float] = None


class SearchResult(BaseModel):
    """Search result model"""
    title: str
    content: str
    url: Optional[str] = None
    category: str
    content_type: str
    score: float
    created_at: Optional[str] = None


class SearchResponse(BaseModel):
    """Response model for search queries"""
    results: List[Dict[str, Any]]  # Using Dict for flexibility
    total_count: int
    query: str
    search_type: str


class DocumentRequest(BaseModel):
    """Request model for adding documents"""
    title: str
    content: str
    url: Optional[str] = None
    category: str = "General"
    content_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Response model for document operations"""
    document_id: int
    message: str
    title: str


class SystemStats(BaseModel):
    """System statistics model"""
    documents_count: int
    categories_count: int
    total_queries: int
    system_health: str
    last_updated: datetime


class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    components: Dict[str, bool]


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str
    error_type: str
    timestamp: str
