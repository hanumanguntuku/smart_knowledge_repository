"""
Storage management module for documents and metadata with ChromaDB integration
"""
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from ..core.database import db
from ..processors.data_validator import DataValidator
from ..search.embedding_engine import EmbeddingGenerator


class StorageManager:
    """Manages document storage and retrieval with ChromaDB embeddings"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = DataValidator()
        self.embedding_generator = EmbeddingGenerator()
    
    def store_document(self, document_data: Dict, skip_url_validation: bool = False) -> Tuple[bool, str, Optional[int]]:
        """Store a document in the database"""
        try:
            # Validate document with optional URL validation skip
            if skip_url_validation:
                validation_result = self._validate_document_relaxed(document_data)
            else:
                validation_result = self.validator.validate_document(document_data)
            
            if not validation_result.is_valid:
                error_msg = f"Validation failed: {'; '.join(validation_result.errors)}"
                self.logger.error(error_msg)
                return False, error_msg, None
            
            # Check for duplicates - both content_hash and URL
            existing_doc = self._check_duplicate(validation_result.normalized_data['content_hash'])
            if existing_doc:
                self.logger.info(f"Duplicate document found by content: {existing_doc['title']} (ID: {existing_doc['id']})")
                return True, f"Document already exists: {existing_doc['title']}", existing_doc['id']
            
            # Check for URL duplicates
            url_duplicate = self._check_url_duplicate(validation_result.normalized_data['url'])
            if url_duplicate:
                self.logger.info(f"Duplicate document found by URL: {url_duplicate['title']} (ID: {url_duplicate['id']})")
                return True, f"Document already exists: {url_duplicate['title']}", url_duplicate['id']
            
            # Insert document with duplicate handling
            try:
                doc_id = self._insert_document(validation_result.normalized_data)
            except Exception as db_error:
                error_msg = str(db_error)
                self.logger.info(f"🔍 Database operation error: {error_msg}")
                
                # More comprehensive constraint error detection
                if any(phrase in error_msg for phrase in [
                    "UNIQUE constraint failed: documents.content_hash",
                    "UNIQUE constraint failed: documents.url", 
                    "UNIQUE constraint failed",
                    "constraint failed",
                    "integrity error"
                ]):
                    self.logger.info(f"🔍 UNIQUE constraint violation detected: {error_msg}")
                    
                    # Check specific constraint type and handle accordingly
                    if "documents.url" in error_msg:
                        self.logger.info("🔍 URL constraint violation detected")
                        # Check for deleted document with same URL
                        deleted_doc = self._check_deleted_url_duplicate(validation_result.normalized_data['url'])
                        if deleted_doc:
                            self.logger.info(f"🔄 Found deleted document with same URL, reactivating: {deleted_doc['title']}")
                            success = self._reactivate_document(deleted_doc['id'], validation_result.normalized_data)
                            if success:
                                self.logger.info(f"✅ Successfully reactivated document {deleted_doc['id']}")
                                return True, f"Document reactivated: {deleted_doc['title']}", deleted_doc['id']
                        
                        # Handle race condition - document was inserted between check and insert
                        existing_doc = self._check_url_duplicate(validation_result.normalized_data['url'])
                        if existing_doc:
                            self.logger.info(f"Document already exists by URL (race condition): {existing_doc['title']}")
                            return True, f"Document already exists: {existing_doc['title']}", existing_doc['id']
                    
                    elif "documents.content_hash" in error_msg or "content_hash" in error_msg:
                        self.logger.info("🔍 Content hash constraint violation detected")
                        # Check if there's a deleted document with same content_hash
                        deleted_doc = self._check_deleted_duplicate(validation_result.normalized_data['content_hash'])
                        if deleted_doc:
                            self.logger.info(f"🔄 Found deleted document with same content, reactivating: {deleted_doc['title']}")
                            success = self._reactivate_document(deleted_doc['id'], validation_result.normalized_data)
                            if success:
                                self.logger.info(f"✅ Successfully reactivated document {deleted_doc['id']}")
                                return True, f"Document reactivated: {deleted_doc['title']}", deleted_doc['id']
                        
                        # Handle race condition - document was inserted between check and insert
                        existing_doc = self._check_duplicate(validation_result.normalized_data['content_hash'])
                        if existing_doc:
                            self.logger.info(f"Document already exists by content (race condition): {existing_doc['title']}")
                            return True, f"Document already exists: {existing_doc['title']}", existing_doc['id']
                    
                    else:
                        # Generic constraint violation - check both types
                        self.logger.info("🔍 Generic constraint violation - checking both URL and content hash")
                        
                        # Check for deleted documents by both criteria
                        deleted_by_content = self._check_deleted_duplicate(validation_result.normalized_data['content_hash'])
                        deleted_by_url = self._check_deleted_url_duplicate(validation_result.normalized_data['url'])
                        
                        target_doc = deleted_by_content or deleted_by_url
                        if target_doc:
                            self.logger.info(f"🔄 Found deleted document, reactivating: {target_doc['title']}")
                            success = self._reactivate_document(target_doc['id'], validation_result.normalized_data)
                            if success:
                                self.logger.info(f"✅ Successfully reactivated document {target_doc['id']}")
                                return True, f"Document reactivated: {target_doc['title']}", target_doc['id']
                        
                        # Check for active documents by both criteria
                        existing_by_content = self._check_duplicate(validation_result.normalized_data['content_hash'])
                        existing_by_url = self._check_url_duplicate(validation_result.normalized_data['url'])
                        
                        existing_doc = existing_by_content or existing_by_url
                        if existing_doc:
                            self.logger.info(f"Document already exists (race condition): {existing_doc['title']}")
                            return True, f"Document already exists: {existing_doc['title']}", existing_doc['id']
                    
                    # If no deleted or active document found, this is an unexpected constraint violation
                    self.logger.error(f"❌ Unexpected UNIQUE constraint violation: {error_msg}")
                    self.logger.error(f"❌ Content hash causing issue: {validation_result.normalized_data['content_hash']}")
                    
                    # Try to force reactivation by searching more broadly
                    self.logger.info("🔍 Searching for any document with same content hash...")
                    try:
                        from ..core.database import db
                        all_docs_query = "SELECT * FROM documents WHERE content_hash = ?"
                        all_docs = db.execute_query(all_docs_query, (validation_result.normalized_data['content_hash'],))
                        if all_docs:
                            self.logger.info(f"Found {len(all_docs)} documents with same hash:")
                            for doc in all_docs:
                                self.logger.info(f"  ID {doc['id']}: '{doc['title']}' (status: {doc['status']})")
                            
                            # Try to reactivate the first deleted one found
                            deleted_docs = [doc for doc in all_docs if doc['status'] == 'deleted']
                            if deleted_docs:
                                target_doc = deleted_docs[0]
                                self.logger.info(f"🔄 Attempting to reactivate document {target_doc['id']}")
                                success = self._reactivate_document(target_doc['id'], validation_result.normalized_data)
                                if success:
                                    return True, f"Document reactivated: {target_doc['title']}", target_doc['id']
                    except Exception as search_error:
                        self.logger.error(f"Error during broad search: {search_error}")
                    
                    return False, f"Database constraint error: {error_msg}", None
                
                # Re-raise if it's a different database error
                self.logger.error(f"❌ Non-constraint database error: {error_msg}")
                raise db_error
            
            # Generate embeddings automatically  
            self._generate_embeddings_async(doc_id, validation_result.normalized_data)
            
            self.logger.info(f"Stored document {doc_id}: {validation_result.normalized_data['title']}")
            return True, "Document stored successfully", doc_id
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ Outer exception handler caught: {error_msg}")
            
            # Check if this is a constraint error that wasn't handled
            if any(phrase in error_msg for phrase in [
                "UNIQUE constraint failed: documents.content_hash",
                "UNIQUE constraint failed: documents.url",
                "UNIQUE constraint failed",
                "constraint failed"
            ]):
                self.logger.error("🚨 CONSTRAINT ERROR IN OUTER HANDLER - This should have been caught earlier!")
                self.logger.error(f"Content hash: {validation_result.normalized_data.get('content_hash', 'Unknown') if 'validation_result' in locals() else 'Validation not completed'}")
                return False, f"Database constraint error: {error_msg}", None
            
            # For other errors, return the original error message
            return False, f"Error storing document: {error_msg}", None
    
    def _check_duplicate(self, content_hash: str) -> Optional[Dict]:
        """Check if document with same content hash exists"""
        query = "SELECT * FROM documents WHERE content_hash = ? AND status = 'active'"
        results = db.execute_query(query, (content_hash,))
        return results[0] if results else None
    
    def _check_url_duplicate(self, url: str) -> Optional[Dict]:
        """Check if document with same URL exists"""
        query = "SELECT * FROM documents WHERE url = ? AND status = 'active'"
        results = db.execute_query(query, (url,))
        return results[0] if results else None
    
    def _check_deleted_duplicate(self, content_hash: str) -> Optional[Dict]:
        """Check if a deleted document with same content hash exists"""
        query = "SELECT * FROM documents WHERE content_hash = ? AND status = 'deleted'"
        results = db.execute_query(query, (content_hash,))
        return results[0] if results else None
    
    def _check_deleted_url_duplicate(self, url: str) -> Optional[Dict]:
        """Check if a deleted document with same URL exists"""
        query = "SELECT * FROM documents WHERE url = ? AND status = 'deleted'"
        results = db.execute_query(query, (url,))
        return results[0] if results else None
    
    def _reactivate_document(self, doc_id: int, updated_data: Dict) -> bool:
        """Reactivate a deleted document with updated data"""
        try:
            # Ensure metadata is properly formatted
            if 'metadata' in updated_data and isinstance(updated_data['metadata'], dict):
                metadata_json = json.dumps(updated_data.get('metadata', {}))
            elif 'metadata' in updated_data and isinstance(updated_data['metadata'], str):
                metadata_json = updated_data['metadata']  # Already JSON string
            else:
                metadata_json = json.dumps({})
                
            query = """
                UPDATE documents 
                SET url = ?, title = ?, content = ?, content_type = ?, domain = ?,
                    language = ?, word_count = ?, char_count = ?, reading_time_minutes = ?,
                    metadata = ?, status = 'active', updated_at = ?
                WHERE id = ?
            """
            params = (
                updated_data['url'], updated_data['title'], updated_data['content'], 
                updated_data['content_type'], updated_data['domain'], updated_data['language'],
                updated_data['word_count'], updated_data['char_count'], updated_data['reading_time_minutes'],
                metadata_json, datetime.now().isoformat(), doc_id
            )
            
            self.logger.debug(f"Reactivating document {doc_id} with params: {[type(p).__name__ for p in params]}")
            rows_affected = db.execute_update(query, params)
            
            if rows_affected > 0:
                # Regenerate embeddings for reactivated document
                self._generate_embeddings_async(doc_id, updated_data)
                self.logger.info(f"✅ Successfully reactivated document {doc_id}")
                return True
            else:
                self.logger.error(f"❌ No rows affected when reactivating document {doc_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error reactivating document {doc_id}: {e}")
            # Log parameter types for debugging
            if 'params' in locals():
                param_types = [f"{i}: {type(p).__name__}" for i, p in enumerate(params)]
                self.logger.error(f"Parameter types: {param_types}")
            return False
    
    def _insert_document(self, data: Dict) -> int:
        """Insert document into database"""
        query = """
            INSERT INTO documents (
                url, title, content, content_hash, content_type, domain,
                language, word_count, char_count, reading_time_minutes,
                metadata, scrape_metadata, created_at, updated_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            data['url'],
            data['title'],
            data['content'],
            data['content_hash'],
            data['content_type'],
            data['domain'],
            data['language'],
            data['word_count'],
            data['char_count'],
            data['reading_time_minutes'],
            json.dumps(data.get('metadata', {})),
            json.dumps(data.get('scrape_metadata', {})),
            data['created_at'],
            data['updated_at'],
            data['status']
        )
        
        return db.execute_insert(query, params)
    
    def _generate_embeddings_async(self, doc_id: int, data: Dict):
        """Generate embeddings for the document asynchronously"""
        try:
            # Generate embeddings in background
            self.embedding_generator.generate_embeddings_for_document(
                document_id=doc_id,
                content=data['content'],
                title=data['title']
            )
            self.logger.debug(f"Initiated embedding generation for document {doc_id}")
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings for document {doc_id}: {e}")
            # Don't fail the entire storage operation if embeddings fail
    
    def get_documents(self, status: str = 'active', 
                     limit: int = 500, offset: int = 0) -> List[Dict]:
        """Retrieve documents with optional filtering"""
        query = """
            SELECT d.*
            FROM documents d
            WHERE d.status = ?
            ORDER BY d.created_at DESC
            LIMIT ? OFFSET ?
        """
        params = (status, limit, offset)
        
        return db.execute_query(query, params)
    
    def search_documents(self, query: str, limit: int = 50) -> List[Dict]:
        """Basic keyword search in documents"""
        search_term = f"%{query}%"
        
        sql_query = """
            SELECT d.*
            FROM documents d
            WHERE d.status = 'active' 
            AND (d.title LIKE ? OR d.content LIKE ?)
            ORDER BY d.created_at DESC
            LIMIT ?
        """
        params = (search_term, search_term, limit)
        
        return db.execute_query(sql_query, params)
    
    def get_categories(self) -> List[Dict]:
        """Get all categories with document counts (deprecated - returns empty list)"""
        return []
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Get specific document by ID"""
        query = """
            SELECT d.*
            FROM documents d
            WHERE d.id = ?
        """
        results = db.execute_query(query, (doc_id,))
        return results[0] if results else None
    
    def update_document(self, doc_id: int, updates: Dict) -> bool:
        """Update document fields"""
        try:
            # Build dynamic update query
            update_fields = []
            params = []
            
            allowed_fields = ['title', 'content', 'metadata', 'status']
            
            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    if field == 'metadata':
                        params.append(json.dumps(value))
                    else:
                        params.append(value)
            
            if not update_fields:
                return False
            
            # Add updated_at timestamp
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(doc_id)
            
            query = f"UPDATE documents SET {', '.join(update_fields)} WHERE id = ?"
            rows_affected = db.execute_update(query, tuple(params))
            
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating document {doc_id}: {e}")
            return False
    
    def delete_document(self, doc_id: int, soft_delete: bool = True) -> bool:
        """Delete document (soft or hard delete)"""
        try:
            if soft_delete:
                query = "UPDATE documents SET status = 'deleted', updated_at = ? WHERE id = ?"
                params = (datetime.now().isoformat(), doc_id)
                rows_affected = db.execute_update(query, params)
                
                # Also remove from ChromaDB to free up vector storage
                if hasattr(self, 'chroma_client') and self.chroma_client:
                    try:
                        self.chroma_client.delete_document_embeddings(doc_id)
                    except Exception as chroma_error:
                        self.logger.warning(f"⚠️ Failed to remove embeddings from ChromaDB: {chroma_error}")
                        
            else:
                # Hard delete - remove all related data
                db.execute_update("DELETE FROM embeddings WHERE document_id = ?", (doc_id,))
                db.execute_update("DELETE FROM document_categories WHERE document_id = ?", (doc_id,))
                
                # Remove from ChromaDB
                if hasattr(self, 'chroma_client') and self.chroma_client:
                    try:
                        self.chroma_client.delete_document_embeddings(doc_id)
                    except Exception as chroma_error:
                        self.logger.warning(f"⚠️ Failed to remove embeddings from ChromaDB: {chroma_error}")
                
                rows_affected = db.execute_update("DELETE FROM documents WHERE id = ?", (doc_id,))
            
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def cleanup_old_deleted_documents(self, days_old: int = 30) -> int:
        """Permanently delete documents that have been soft-deleted for more than specified days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            # Get old deleted documents
            query = "SELECT id FROM documents WHERE status = 'deleted' AND updated_at < ?"
            old_deleted = db.execute_query(query, (cutoff_date,))
            
            count = 0
            for doc in old_deleted:
                if self.delete_document(doc['id'], soft_delete=False):
                    count += 1
                    
            self.logger.info(f"✅ Cleaned up {count} old deleted documents")
            return count
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old deleted documents: {e}")
            return 0
    
    def get_categories(self) -> List[Dict]:
        """Get all categories"""
        query = """
            SELECT c.*, 
                   COUNT(dc.document_id) as document_count
            FROM categories c
            LEFT JOIN document_categories dc ON c.id = dc.category_id
            LEFT JOIN documents d ON dc.document_id = d.id AND d.status = 'active'
            GROUP BY c.id
            ORDER BY c.name
        """
        return db.execute_query(query)
    
    def create_category(self, name: str, description: str = None, 
                       parent_id: int = None, color: str = '#6366f1') -> int:
        """Create new category"""
        query = """
            INSERT INTO categories (name, description, parent_id, color)
            VALUES (?, ?, ?, ?)
        """
        return db.execute_insert(query, (name, description, parent_id, color))
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        # Document counts
        doc_stats = db.execute_query("""
            SELECT status, COUNT(*) as count
            FROM documents
            GROUP BY status
        """)
        stats['documents'] = {row['status']: row['count'] for row in doc_stats}
        
        # Content statistics
        content_stats = db.execute_query("""
            SELECT 
                SUM(word_count) as total_words,
                SUM(char_count) as total_characters,
                AVG(word_count) as avg_words_per_doc,
                COUNT(DISTINCT domain) as unique_domains
            FROM documents 
            WHERE status = 'active'
        """)
        if content_stats and content_stats[0]:
            stats.update({
                'total_words': content_stats[0]['total_words'] or 0,
                'total_characters': content_stats[0]['total_characters'] or 0,
                'avg_words_per_doc': round(content_stats[0]['avg_words_per_doc'] or 0, 1),
                'unique_domains': content_stats[0]['unique_domains'] or 0
            })
        
        # Recent activity
        recent_docs = db.execute_query("""
            SELECT COUNT(*) as count
            FROM documents
            WHERE created_at >= datetime('now', '-7 days')
        """)
        stats['recent_documents'] = recent_docs[0]['count'] if recent_docs else 0
        
        return stats

    def _validate_document_relaxed(self, document_data: Dict):
        """Relaxed validation for manual entries and file uploads"""
        from ..processors.data_validator import ValidationResult
        
        errors = []
        warnings = []
        normalized_data = document_data.copy()
        
        # Title validation (required)
        title = document_data.get('title', '').strip()
        if not title:
            errors.append("Title is required")
        elif len(title) < 3:
            errors.append("Title must be at least 3 characters")
        else:
            normalized_data['title'] = title[:200]  # Limit length
        
        # Content validation (relaxed minimum)
        content = document_data.get('content', '').strip()
        if not content:
            errors.append("Content is required")
        elif len(content) < 10:  # Much more relaxed than 50
            errors.append("Content must be at least 10 characters")
        else:
            normalized_data['content'] = content
        
        # URL handling (relaxed - can be any format)
        url = document_data.get('url', '').strip()
        if not url:
            # Generate a placeholder URL for manual entries
            url = f"manual://document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        normalized_data['url'] = url
        
        # Generate required fields
        import hashlib
        normalized_data['content_hash'] = hashlib.md5(
            normalized_data['content'].encode('utf-8')
        ).hexdigest()
        
        normalized_data['content_type'] = document_data.get('content_type', 'text/plain')
        normalized_data['domain'] = 'general'
        normalized_data['language'] = 'en'
        
        # Content metrics
        words = normalized_data['content'].split()
        normalized_data['word_count'] = len(words)
        normalized_data['char_count'] = len(normalized_data['content'])
        normalized_data['reading_time_minutes'] = max(1, len(words) // 200)
        
        # Metadata
        metadata = document_data.get('metadata', {})
        metadata['validation_type'] = 'relaxed'
        normalized_data['metadata'] = metadata
        normalized_data['scrape_metadata'] = '{}'
        
        # Timestamps
        now = datetime.now().isoformat()
        normalized_data['created_at'] = now
        normalized_data['updated_at'] = now
        normalized_data['status'] = 'active'
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_data=normalized_data if len(errors) == 0 else None
        )
