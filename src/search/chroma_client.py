"""
ChromaDB client wrapper for vector embeddings storage and retrieval
"""
import logging
import uuid
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

from ..core.config import config


class ChromaDBClient:
    """ChromaDB client for vector operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.collection = None
        self.available = False
        
        if CHROMADB_AVAILABLE:
            self._initialize_client()
        else:
            self.logger.warning("ChromaDB not available. Vector operations will use fallback.")
    
    def _initialize_client(self):
        """Initialize ChromaDB client with persistent storage"""
        try:
            # Create ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=config.chroma_persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            
            # Initialize main collection
            self.initialize_collection()
            self.available = True
            self.logger.info(f"ChromaDB initialized successfully at {config.chroma_persist_directory}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            self.available = False
    
    def initialize_collection(self):
        """Initialize main collection"""
        try:
            collection_name = "knowledge_base"
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": config.chroma_distance_metric}
            )
            
            self.logger.debug(f"Initialized main collection: {collection_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize collection: {e}")
    
    def delete_collection(self):
        """Delete the collection to start fresh"""
        if not self.available or not self.client:
            return
        
        try:
            self.client.delete_collection("knowledge_base")
            self.collection = None
            self.logger.info("Deleted existing ChromaDB collection")
        except Exception as e:
            self.logger.debug(f"Collection might not exist: {e}")
    
    def add_embeddings(self, 
                      document_id: int, 
                      chunks: List[Dict], 
                      embeddings: List[List[float]]) -> bool:
        """Add embeddings to ChromaDB collection"""
        if not self.available or not chunks or not embeddings:
            return False
        
        try:
            if not self.collection:
                return False
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"doc_{document_id}_chunk_{i}"
                ids.append(chunk_id)
                documents.append(chunk['text'])
                
                metadata = {
                    'document_id': document_id,
                    'chunk_position': chunk['position'],
                    'chunk_type': chunk['type'],
                    'length': len(chunk['text']),
                    'embedding_model': config.embedding_model
                }
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            self.logger.info(f"Added {len(chunks)} embeddings for document {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add embeddings to ChromaDB: {e}")
            return False
    
    def search_similar(self, 
                      query_embedding: List[float], 
                      limit: int = 10,
                      where_filter: Dict = None) -> List[Dict]:
        """Search for similar embeddings in ChromaDB"""
        if not self.available:
            return []
        
        try:
            if not self.collection:
                return []
            
            # Perform similarity search
            search_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter,
                include=['documents', 'metadatas', 'distances']
            )
            
            results = []
            # Process results
            if search_results['ids'] and search_results['ids'][0]:
                for i, chunk_id in enumerate(search_results['ids'][0]):
                    distance = search_results['distances'][0][i]
                    
                    # Convert distance to similarity score (for L2 distance)
                    # For L2: smaller distance = higher similarity
                    similarity = 1.0 / (1.0 + distance)
                    
                    result = {
                        'chunk_id': chunk_id,
                        'document_id': search_results['metadatas'][0][i]['document_id'],
                        'chunk_text': search_results['documents'][0][i],
                        'chunk_position': search_results['metadatas'][0][i]['chunk_position'],
                        'similarity': similarity,
                        'distance': distance,
                        'metadata': search_results['metadatas'][0][i]
                    }
                    results.append(result)
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to search ChromaDB: {e}")
            return []
    
    def delete_document_embeddings(self, document_id: int) -> bool:
        """Delete all embeddings for a specific document"""
        if not self.available or not self.collection:
            return False
        
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id},
                include=['ids']
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                self.logger.info(f"Deleted {len(results['ids'])} embeddings for document {document_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete embeddings for document {document_id}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics for the main collection"""
        if not self.available or not self.collection:
            return {}
        
        try:
            count = self.collection.count()
            return {
                'document_count': count,
                'collection_name': self.collection.name
            }
        except Exception as e:
            return {'error': str(e)}
    
    def backup_collections(self, backup_path: str) -> bool:
        """Backup ChromaDB collections"""
        # ChromaDB automatically persists data, but we can create explicit backups
        try:
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(backup_path) / f"chroma_backup_{timestamp}"
            
            # Copy the entire ChromaDB directory
            shutil.copytree(config.chroma_persist_directory, backup_dir)
            
            self.logger.info(f"ChromaDB backup created at {backup_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup ChromaDB: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if ChromaDB is available and functioning"""
        return self.available and self.client is not None


# Global ChromaDB client instance
chroma_client = ChromaDBClient()
