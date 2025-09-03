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

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

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
        """Initialize embedding model with OpenAI primary and Gemini fallback"""
        try:
            # Strategy 1: Use OpenAI embeddings (primary)
            if config.use_openai_embeddings and OPENAI_AVAILABLE and config.openai_api_key:
                self.logger.info("🔄 Attempting to use OpenAI embeddings...")
                self._setup_openai_embeddings()
                
            # Strategy 2: Use Gemini as AI fallback
            elif config.use_gemini_fallback and GEMINI_AVAILABLE and config.gemini_api_key:
                self.logger.info("🔄 Using Gemini embeddings as primary...")
                self._setup_gemini_embeddings()
                
            # Strategy 3: Local embeddings as last resort
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                self.model = SentenceTransformer(config.embedding_model)
                self.embedding_type = "sentence_transformer"
                self.logger.warning("⚠️ Using local embeddings - AI providers not available")
                
            else:
                self.logger.error("❌ No embedding provider available")
                self.embedding_type = None
                
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            # Force fallback to Gemini if initialization fails
            if GEMINI_AVAILABLE and config.gemini_api_key:
                self.logger.info("🔄 Forcing fallback to Gemini due to initialization failure...")
                self._setup_gemini_embeddings()
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                self.model = SentenceTransformer(config.embedding_model)
                self.embedding_type = "sentence_transformer"
                self.logger.info("↩️ Final fallback to local embeddings")
            else:
                self.embedding_type = None
    
    def _setup_openai_embeddings(self):
        """Setup OpenAI embeddings with quota-aware fallback"""
        try:
            openai.api_key = config.openai_api_key
            self.embedding_type = "openai"
            self.logger.info("✅ Using OpenAI embeddings (primary)")
            
            # Test with a simple embedding to detect quota issues
            self._test_openai_embeddings()
            
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "insufficient_quota" in error_msg:
                self.logger.warning(f"⚠️ OpenAI quota exceeded, falling back to Gemini")
                self._fallback_to_gemini()
            elif "rate_limit" in error_msg.lower():
                self.logger.warning(f"⚠️ OpenAI rate limit reached, falling back to Gemini")
                self._fallback_to_gemini()
            else:
                self.logger.error(f"❌ OpenAI embeddings setup failed: {e}")
                self._fallback_to_gemini()
    
    def _setup_gemini_embeddings(self):
        """Setup Google Gemini embeddings"""
        try:
            if not GEMINI_AVAILABLE:
                raise ImportError("google-generativeai not installed")
                
            genai.configure(api_key=config.gemini_api_key)
            self.embedding_type = "gemini"
            self.logger.info("✅ Using Google Gemini embeddings")
            
        except Exception as e:
            self.logger.error(f"❌ Gemini embeddings setup failed: {e}")
            self._fallback_to_local()
    
    def _test_openai_embeddings(self):
        """Test OpenAI embeddings to detect quota issues early"""
        try:
            # Try a minimal test embedding
            import openai
            client = openai.OpenAI(api_key=config.openai_api_key)
            client.embeddings.create(
                model="text-embedding-ada-002",
                input="test"
            )
            self.openai_client = client
            
        except Exception as e:
            if "quota" in str(e).lower():
                raise e  # Re-raise quota errors
            else:
                self.logger.warning(f"OpenAI test failed: {e}")
    
    def _fallback_to_gemini(self):
        """Fallback to Gemini when OpenAI fails"""
        if config.use_gemini_fallback and GEMINI_AVAILABLE and config.gemini_api_key:
            self._setup_gemini_embeddings()
        else:
            self._fallback_to_local()
    
    def _fallback_to_local(self):
        """Final fallback to local embeddings"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.model = SentenceTransformer(config.embedding_model)
            self.embedding_type = "sentence_transformer"
            self.logger.info("↩️ Falling back to local embeddings")
        else:
            self.logger.error("❌ No embedding provider available")
            self.embedding_type = None
    
    def _generate_gemini_embedding_fallback(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding using Gemini as fallback when OpenAI fails"""
        try:
            if GEMINI_AVAILABLE and config.gemini_api_key:
                import google.generativeai as genai
                genai.configure(api_key=config.gemini_api_key)
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text
                )
                return np.array(result['embedding'])
            else:
                self.logger.error("❌ Gemini not available for fallback")
                return None
        except Exception as e:
            self.logger.error(f"❌ Gemini embedding fallback failed: {e}")
            return None
    
    def generate_embeddings_for_document(self, document_id: int, content: str, title: str = "") -> bool:
        """Generate and store embeddings for a document using ChromaDB"""
        if not self.embedding_type:
            self.logger.warning("No embedding model available")
            return False
        
        try:
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
                    embeddings=embeddings
                )
                
                if success:
                    self.logger.info(f"Generated {len(chunks)} embeddings for document {document_id}")
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
            
            elif self.embedding_type == "gemini":
                # Use Google Gemini embeddings
                import google.generativeai as genai
                genai.configure(api_key=config.gemini_api_key)
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text
                )
                return np.array(result['embedding'])
            
            elif self.embedding_type == "sentence_transformer":
                return self.model.encode(text, convert_to_numpy=True)
            
        except Exception as e:
            error_msg = str(e).lower()
            self.logger.error(f"Failed to generate embedding: {e}")
            
            # Enhanced quota and error handling with fallback
            if self.embedding_type == "openai" and any(keyword in error_msg for keyword in ["quota", "exceeded", "limit", "insufficient_quota"]):
                self.logger.warning("⚠️ OpenAI quota exceeded during embedding, falling back to Gemini")
                return self._generate_gemini_embedding_fallback(text)
            elif self.embedding_type == "openai" and any(keyword in error_msg for keyword in ["rate_limit", "rate limit", "too many requests"]):
                self.logger.warning("⚠️ OpenAI rate limit reached during embedding, falling back to Gemini")
                return self._generate_gemini_embedding_fallback(text)
            elif self.embedding_type == "gemini" and any(keyword in error_msg for keyword in ["quota", "exceeded", "limit", "resource_exhausted"]):
                self.logger.warning("⚠️ Gemini quota exceeded during embedding, falling back to sentence transformer")
                return self._generate_sentence_transformer_fallback(text)
            
            return None
    
    def _generate_gemini_embedding_fallback(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding using Gemini as fallback when OpenAI fails"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key)
            result = genai.embed_content(
                model="models/embedding-001",
                content=text
            )
            self.logger.info("✅ Successfully generated embedding using Gemini fallback")
            return np.array(result['embedding'])
        except Exception as e:
            self.logger.error(f"❌ Gemini embedding fallback also failed: {e}")
            return self._generate_sentence_transformer_fallback(text)
    
    def _generate_sentence_transformer_fallback(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding using sentence transformer as final fallback"""
        try:
            if not hasattr(self, 'fallback_model'):
                from sentence_transformers import SentenceTransformer
                self.fallback_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.info("Initialized sentence transformer fallback model")
            
            embedding = self.fallback_model.encode(text, convert_to_numpy=True)
            self.logger.info("✅ Successfully generated embedding using sentence transformer fallback")
            return embedding
        except Exception as e:
            self.logger.error(f"❌ All embedding methods failed: {e}")
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
    
    def search_similar_chunks(self, query: str, limit: int = 10, threshold: float = None) -> List[Dict]:
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
