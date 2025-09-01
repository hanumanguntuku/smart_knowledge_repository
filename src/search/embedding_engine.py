"""
Vector embedding system for semantic search with ChromaDB integration
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
import sqlite3
import pickle
import logging
from pathlib import Path

# Optional imports for different embedding models
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..core.config import config
from ..core.database import DatabaseManager
from .chroma_client import chroma_client


class EmbeddingGenerator:
    """Generate and manage document embeddings for semantic search with ChromaDB"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = DatabaseManager()
        self.chroma = chroma_client
        self.model = None
        self.embedding_type = None
        self._initialize_embedding_model()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model based on configuration"""
        try:
            # Prefer SentenceTransformers over OpenAI for embeddings (more reliable and free)
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.model = SentenceTransformer(config.embedding_model)
                self.embedding_type = "sentence_transformer"
                self.logger.info(f"Using SentenceTransformer: {config.embedding_model}")
            elif config.use_openai and OPENAI_AVAILABLE and config.openai_api_key:
                openai.api_key = config.openai_api_key
                self.embedding_type = "openai"
                self.logger.info("Using OpenAI embeddings")
            else:
                self.logger.warning("No embedding model available. Semantic search disabled.")
                self.embedding_type = None
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            self.embedding_type = None
    
    def generate_embeddings_for_document(self, document_id: int, content: str, title: str = "", domain: str = "general") -> bool:
        """Generate and store embeddings for a document using ChromaDB"""
        if not self.embedding_type:
            self.logger.warning("No embedding model available")
            return False
        
        try:
            # Get document metadata for domain classification
            doc_metadata = self._get_document_metadata(document_id)
            if doc_metadata:
                domain = self._classify_domain(content, title, doc_metadata.get('domain', 'general'))
            
            # Split content into chunks
            chunks = self._split_into_chunks(content, title)
            
            # Generate embeddings for each chunk
            embeddings = []
            for chunk in chunks:
                embedding = self._generate_embedding(chunk['text'])
                if embedding is not None:
                    embeddings.append(embedding.tolist())  # Convert to list for ChromaDB
            
            # Store in ChromaDB
            if embeddings and self.chroma.is_available():
                success = self.chroma.add_embeddings(
                    document_id=document_id,
                    chunks=chunks,
                    embeddings=embeddings,
                    domain=domain
                )
                
                if success:
                    self.logger.info(f"Generated {len(chunks)} embeddings for document {document_id} in domain '{domain}'")
                    return True
                else:
                    self.logger.error(f"Failed to store embeddings in ChromaDB for document {document_id}")
                    return False
            else:
                self.logger.error("ChromaDB not available - cannot store embeddings")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings for document {document_id}: {e}")
            return False
    
    def _get_document_metadata(self, document_id: int) -> Optional[Dict]:
        """Get document metadata from SQLite"""
        try:
            result = self.db.execute_query(
                "SELECT title, domain, content_type FROM documents WHERE id = ?", 
                (document_id,)
            )
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Failed to get document metadata: {e}")
            return None
    
    def _classify_domain(self, content: str, title: str, current_domain: str = "general") -> str:
        """Classify document domain based on content"""
        # Use existing domain if already classified
        if current_domain and current_domain != "general":
            return current_domain.lower()
        
        # Simple keyword-based domain classification
        text_to_analyze = f"{title} {content}".lower()
        
        domain_keywords = {
            'technology': ['ai', 'artificial intelligence', 'machine learning', 'software', 'programming', 'computer', 'technology', 'algorithm', 'data science'],
            'business': ['business', 'strategy', 'management', 'finance', 'marketing', 'sales', 'company', 'revenue', 'profit'],
            'science': ['research', 'study', 'experiment', 'analysis', 'scientific', 'hypothesis', 'methodology', 'results'],
            'healthcare': ['health', 'medical', 'medicine', 'treatment', 'patient', 'diagnosis', 'therapy', 'clinical'],
            'education': ['education', 'learning', 'teaching', 'student', 'course', 'training', 'academic', 'curriculum']
        }
        
        # Count keyword matches for each domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if score > 0:
                domain_scores[domain] = score
        
        # Return domain with highest score, or general if no clear match
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return "general"
    
    def _split_into_chunks(self, content: str, title: str = "") -> List[Dict]:
        chunks = []
        
        # Add title as first chunk if available
        if title.strip():
            chunks.append({
                'text': title,
                'type': 'title',
                'position': 0
            })
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_chunk = ""
        chunk_position = len(chunks)
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > config.chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'type': 'content',
                    'position': chunk_position
                })
                current_chunk = paragraph
                chunk_position += 1
            else:
                current_chunk += ("\n\n" if current_chunk else "") + paragraph
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'type': 'content',
                'position': chunk_position
            })
        
        return chunks
    
    def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a text chunk"""
        try:
            if self.embedding_type == "openai":
                # Use new OpenAI client API (v1.0+)
                import openai
                client = openai.OpenAI(api_key=config.openai_api_key)
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                return np.array(response.data[0].embedding)
            
            elif self.embedding_type == "sentence_transformer":
                return self.model.encode(text, convert_to_numpy=True)
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def _store_embedding(self, document_id: int, chunk_id: int, chunk: Dict, embedding: np.ndarray):
        """Store embedding in database"""
        embedding_blob = pickle.dumps(embedding)
        
        self.db.execute_update("""
            INSERT OR REPLACE INTO embeddings 
            (document_id, chunk_id, chunk_text, chunk_position, embedding, embedding_model, embedding_metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            f"{document_id}_{chunk_id}",
            chunk['text'],
            chunk['position'],
            embedding_blob,
            config.embedding_model,
            pickle.dumps({'type': chunk['type'], 'length': len(chunk['text'])})
        ))
    
    def search_similar_chunks(self, query: str, domain: str = None, limit: int = 10, threshold: float = None) -> List[Dict]:
        """Search for similar chunks using ChromaDB"""
        if not self.embedding_type:
            self.logger.warning("No embedding model available for search")
            return []
        
        if not self.chroma.is_available():
            self.logger.error("ChromaDB not available - cannot perform semantic search")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if query_embedding is None:
                return []
            
            # ChromaDB search
            results = self.chroma.search_similar(
                query_embedding=query_embedding.tolist(),
                domain=domain,
                limit=limit
            )
            
            # Enhance results with document metadata from SQLite
            enhanced_results = []
            for result in results:
                # Apply threshold if specified
                if threshold and result['similarity'] < threshold:
                    continue
                    
                # Get additional document metadata
                doc_metadata = self._get_document_metadata(result['document_id'])
                if doc_metadata:
                    result.update({
                        'title': doc_metadata.get('title', 'Unknown Document'),
                        'url': doc_metadata.get('url', ''),
                        'content_type': doc_metadata.get('content_type', 'text')
                    })
                
                enhanced_results.append(result)
            
            self.logger.debug(f"ChromaDB search returned {len(enhanced_results)} results for query: {query[:50]}...")
            return enhanced_results
                
        except Exception as e:
            self.logger.error(f"Failed to search similar chunks: {e}")
            return []
    
    def generate_embeddings_for_all_documents(self):
        """Generate embeddings for all documents that don't have them"""
        if not self.chroma.is_available():
            self.logger.error("ChromaDB not available - cannot generate embeddings")
            return 0
            
        # Get documents that might need embeddings
        documents = self.db.execute_query("""
            SELECT id, title, content, domain
            FROM documents 
            WHERE status = 'active'
        """)
        
        success_count = 0
        for doc in documents:
            # Check if document already has embeddings in ChromaDB
            existing = self.chroma.search_similar(
                query_embedding=[0.0] * 384,  # Dummy embedding to check existence
                domain=doc.get('domain', 'general'),
                limit=1,
                where_filter={'document_id': doc['id']}
            )
            
            # Generate embeddings if none exist
            if not existing:
                if self.generate_embeddings_for_document(
                    doc['id'], 
                    doc['content'], 
                    doc['title'],
                    doc.get('domain', 'general')
                ):
                    success_count += 1
        
        self.logger.info(f"Generated ChromaDB embeddings for {success_count}/{len(documents)} documents")
        return success_count
    
    def delete_document_embeddings(self, document_id: int, domain: str = None) -> bool:
        """Delete all embeddings for a document from ChromaDB"""
        if not self.chroma.is_available():
            self.logger.error("ChromaDB not available - cannot delete embeddings")
            return False
            
        return self.chroma.delete_document_embeddings(document_id, domain)
    
    def get_embedding_stats(self) -> Dict:
        """Get statistics about ChromaDB embeddings storage"""
        stats = {'chromadb': {}, 'status': 'unknown'}
        
        # ChromaDB stats
        if self.chroma.is_available():
            stats['chromadb'] = self.chroma.get_collection_stats()
            stats['status'] = 'chromadb_available'
        else:
            stats['status'] = 'chromadb_unavailable'
        
        return stats
    
    def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a text chunk"""
        try:
            if self.embedding_type == "openai":
                # Use new OpenAI client API (v1.0+)
                import openai
                client = openai.OpenAI(api_key=config.openai_api_key)
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                return np.array(response.data[0].embedding)
            
            elif self.embedding_type == "sentence_transformer":
                return self.model.encode(text, convert_to_numpy=True)
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return None
