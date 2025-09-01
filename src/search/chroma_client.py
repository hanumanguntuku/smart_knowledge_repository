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
    """ChromaDB client for vector operations with domain-specific collections"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.collections = {}
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
            
            # Initialize domain collections
            self._initialize_collections()
            self.available = True
            self.logger.info(f"ChromaDB initialized successfully at {config.chroma_persist_directory}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            self.available = False
    
    def _initialize_collections(self):
        """Initialize collections for different domains"""
        domains = ["technology", "business", "science", "healthcare", "education", "general"]
        
        for domain in domains:
            try:
                collection_name = f"knowledge_base_{domain}"
                
                # Get or create collection
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"domain": domain, "hnsw:space": config.chroma_distance_metric}
                )
                
                self.collections[domain] = collection
                self.logger.debug(f"Initialized collection for domain: {domain}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize collection for domain {domain}: {e}")
    
    def get_collection_for_domain(self, domain: str):
        """Get ChromaDB collection for specific domain"""
        if not self.available:
            return None
            
        domain = domain.lower() if domain else "general"
        
        # Default to general if domain not found
        if domain not in self.collections:
            domain = "general"
            
        return self.collections.get(domain)
    
    def add_embeddings(self, 
                      document_id: int, 
                      chunks: List[Dict], 
                      embeddings: List[List[float]], 
                      domain: str = "general") -> bool:
        """Add embeddings to ChromaDB collection"""
        if not self.available or not chunks or not embeddings:
            return False
        
        try:
            collection = self.get_collection_for_domain(domain)
            if not collection:
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
                    'domain': domain,
                    'length': len(chunk['text']),
                    'embedding_model': config.embedding_model
                }
                metadatas.append(metadata)
            
            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            self.logger.info(f"Added {len(chunks)} embeddings for document {document_id} to {domain} collection")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add embeddings to ChromaDB: {e}")
            return False
    
    def search_similar(self, 
                      query_embedding: List[float], 
                      domain: str = None, 
                      limit: int = 10,
                      where_filter: Dict = None) -> List[Dict]:
        """Search for similar embeddings in ChromaDB"""
        if not self.available:
            return []
        
        try:
            results = []
            
            # Search in specific domain or all domains
            domains_to_search = [domain] if domain else self.collections.keys()
            
            for search_domain in domains_to_search:
                collection = self.get_collection_for_domain(search_domain)
                if not collection:
                    continue
                
                # Perform similarity search
                search_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=where_filter,
                    include=['documents', 'metadatas', 'distances']
                )
                
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
                            'domain': search_results['metadatas'][0][i]['domain'],
                            'metadata': search_results['metadatas'][0][i]
                        }
                        results.append(result)
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to search ChromaDB: {e}")
            return []
    
    def delete_document_embeddings(self, document_id: int, domain: str = None) -> bool:
        """Delete all embeddings for a specific document"""
        if not self.available:
            return False
        
        try:
            domains_to_clean = [domain] if domain else self.collections.keys()
            
            for search_domain in domains_to_clean:
                collection = self.get_collection_for_domain(search_domain)
                if not collection:
                    continue
                
                # Find all chunks for this document
                results = collection.get(
                    where={"document_id": document_id},
                    include=['ids']
                )
                
                if results['ids']:
                    collection.delete(ids=results['ids'])
                    self.logger.info(f"Deleted {len(results['ids'])} embeddings for document {document_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete embeddings for document {document_id}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Dict]:
        """Get statistics for all collections"""
        if not self.available:
            return {}
        
        stats = {}
        for domain, collection in self.collections.items():
            try:
                count = collection.count()
                stats[domain] = {
                    'document_count': count,
                    'collection_name': collection.name
                }
            except Exception as e:
                stats[domain] = {'error': str(e)}
        
        return stats
    
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
