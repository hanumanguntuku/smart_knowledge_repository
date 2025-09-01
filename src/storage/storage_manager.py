"""
Storage management module for documents and metadata with ChromaDB integration
"""
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from ..core.database import db
from ..processors.data_validator import DataValidator
from ..search.embedding_engine import EmbeddingGenerator


class StorageManager:
    """Manages document storage and retrieval with ChromaDB embeddings"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = DataValidator()
        self.embedding_generator = EmbeddingGenerator()
    
    def store_document(self, document_data: Dict) -> Tuple[bool, str, Optional[int]]:
        """Store a document in the database"""
        try:
            # Validate document
            validation_result = self.validator.validate_document(document_data)
            
            if not validation_result.is_valid:
                error_msg = f"Validation failed: {'; '.join(validation_result.errors)}"
                self.logger.error(error_msg)
                return False, error_msg, None
            
            # Check for duplicates
            existing_doc = self._check_duplicate(validation_result.normalized_data['content_hash'])
            if existing_doc:
                self.logger.info(f"Duplicate document found: {existing_doc['url']}")
                return False, f"Document already exists: {existing_doc['title']}", existing_doc['id']
            
            # Insert document
            doc_id = self._insert_document(validation_result.normalized_data)
            
            # Auto-categorize
            domain = self._auto_categorize_document(doc_id, validation_result.normalized_data)
            
            # Generate embeddings automatically
            self._generate_embeddings_async(doc_id, validation_result.normalized_data, domain)
            
            self.logger.info(f"Stored document {doc_id}: {validation_result.normalized_data['title']}")
            return True, "Document stored successfully", doc_id
            
        except Exception as e:
            error_msg = f"Error storing document: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, None
    
    def _check_duplicate(self, content_hash: str) -> Optional[Dict]:
        """Check if document with same content hash exists"""
        query = "SELECT * FROM documents WHERE content_hash = ? AND status = 'active'"
        results = db.execute_query(query, (content_hash,))
        return results[0] if results else None
    
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
    
    def _auto_categorize_document(self, doc_id: int, data: Dict) -> str:
        """Automatically categorize document based on content and return domain"""
        content = data['content'].lower()
        title = data['title'].lower()
        text_to_analyze = f"{title} {content}"
        
        # Simple keyword-based categorization
        category_keywords = {
            'Technology': ['ai', 'artificial intelligence', 'machine learning', 'software', 'programming', 'computer', 'technology'],
            'Business': ['business', 'strategy', 'management', 'finance', 'marketing', 'sales', 'company'],
            'Science': ['research', 'study', 'experiment', 'analysis', 'scientific', 'data', 'hypothesis'],
            'Healthcare': ['health', 'medical', 'medicine', 'treatment', 'patient', 'diagnosis', 'therapy'],
            'Education': ['education', 'learning', 'teaching', 'student', 'course', 'training', 'academic']
        }
        
        # Calculate scores for each category
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if score > 0:
                category_scores[category] = score / len(keywords)
        
        assigned_category = "General"  # Default category
        domain = "general"  # Default domain for ChromaDB
        
        # Assign to best matching category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[best_category]
            assigned_category = best_category
            domain = best_category.lower()
            
            # Get category ID
            category_query = "SELECT id FROM categories WHERE name = ?"
            category_result = db.execute_query(category_query, (best_category,))
            
            if category_result:
                category_id = category_result[0]['id']
                
                # Insert category relationship
                rel_query = """
                    INSERT INTO document_categories (document_id, category_id, confidence, assigned_by)
                    VALUES (?, ?, ?, 'auto')
                """
                db.execute_insert(rel_query, (doc_id, category_id, confidence))
        else:
            # Assign to 'General' category
            category_query = "SELECT id FROM categories WHERE name = 'General'"
            category_result = db.execute_query(category_query)
            
            if category_result:
                category_id = category_result[0]['id']
                rel_query = """
                    INSERT INTO document_categories (document_id, category_id, confidence, assigned_by)
                    VALUES (?, ?, ?, 'auto')
                """
                db.execute_insert(rel_query, (doc_id, category_id, 0.5))
        
        self.logger.debug(f"Categorized document {doc_id} as '{assigned_category}' (domain: {domain})")
        return domain
    
    def _generate_embeddings_async(self, doc_id: int, data: Dict, domain: str):
        """Generate embeddings for the document asynchronously"""
        try:
            # Generate embeddings in background
            self.embedding_generator.generate_embeddings_for_document(
                document_id=doc_id,
                content=data['content'],
                title=data['title'],
                domain=domain
            )
            self.logger.debug(f"Initiated embedding generation for document {doc_id}")
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings for document {doc_id}: {e}")
            # Don't fail the entire storage operation if embeddings fail
    
    def get_documents(self, category: str = None, status: str = 'active', 
                     limit: int = 100, offset: int = 0) -> List[Dict]:
        """Retrieve documents with optional filtering"""
        if category and category != 'All':
            query = """
                SELECT d.*, c.name as category_name, dc.confidence
                FROM documents d
                JOIN document_categories dc ON d.id = dc.document_id
                JOIN categories c ON dc.category_id = c.id
                WHERE d.status = ? AND c.name = ?
                ORDER BY d.created_at DESC
                LIMIT ? OFFSET ?
            """
            params = (status, category, limit, offset)
        else:
            query = """
                SELECT d.*, 
                       (SELECT GROUP_CONCAT(c.name) 
                        FROM document_categories dc 
                        JOIN categories c ON dc.category_id = c.id 
                        WHERE dc.document_id = d.id) as categories
                FROM documents d
                WHERE d.status = ?
                ORDER BY d.created_at DESC
                LIMIT ? OFFSET ?
            """
            params = (status, limit, offset)
        
        return db.execute_query(query, params)
    
    def search_documents(self, query: str, category: str = None, limit: int = 10) -> List[Dict]:
        """Basic keyword search in documents"""
        search_term = f"%{query}%"
        
        if category and category != 'All':
            sql_query = """
                SELECT d.*, c.name as category_name,
                       (CASE 
                        WHEN d.title LIKE ? THEN 3
                        WHEN d.content LIKE ? THEN 1
                        ELSE 0 
                       END) as relevance_score
                FROM documents d
                JOIN document_categories dc ON d.id = dc.document_id
                JOIN categories c ON dc.category_id = c.id
                WHERE (d.title LIKE ? OR d.content LIKE ?) 
                AND c.name = ? AND d.status = 'active'
                ORDER BY relevance_score DESC, d.created_at DESC
                LIMIT ?
            """
            params = (search_term, search_term, search_term, search_term, category, limit)
        else:
            sql_query = """
                SELECT d.*,
                       (CASE 
                        WHEN d.title LIKE ? THEN 3
                        WHEN d.content LIKE ? THEN 1
                        ELSE 0 
                       END) as relevance_score,
                       (SELECT GROUP_CONCAT(c.name) 
                        FROM document_categories dc 
                        JOIN categories c ON dc.category_id = c.id 
                        WHERE dc.document_id = d.id) as categories
                FROM documents d
                WHERE (d.title LIKE ? OR d.content LIKE ?) 
                AND d.status = 'active'
                ORDER BY relevance_score DESC, d.created_at DESC
                LIMIT ?
            """
            params = (search_term, search_term, search_term, search_term, limit)
        
        return db.execute_query(sql_query, params)
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Get specific document by ID"""
        query = """
            SELECT d.*,
                   (SELECT GROUP_CONCAT(c.name) 
                    FROM document_categories dc 
                    JOIN categories c ON dc.category_id = c.id 
                    WHERE dc.document_id = d.id) as categories
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
            else:
                # Hard delete - remove all related data
                db.execute_update("DELETE FROM embeddings WHERE document_id = ?", (doc_id,))
                db.execute_update("DELETE FROM document_categories WHERE document_id = ?", (doc_id,))
                rows_affected = db.execute_update("DELETE FROM documents WHERE id = ?", (doc_id,))
            
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
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
        
        # Category counts
        cat_stats = db.execute_query("SELECT COUNT(*) as count FROM categories")
        stats['categories'] = cat_stats[0]['count'] if cat_stats else 0
        
        # Recent activity
        recent_docs = db.execute_query("""
            SELECT COUNT(*) as count
            FROM documents
            WHERE created_at >= datetime('now', '-7 days')
        """)
        stats['recent_documents'] = recent_docs[0]['count'] if recent_docs else 0
        
        return stats
