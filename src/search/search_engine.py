"""
Search engine module with relevance scoring and hybrid search
"""
import re
from typing import List, Dict, Optional
from ..storage.storage_manager import StorageManager
from .embedding_engine import EmbeddingGenerator
import logging


class SearchEngine:
    """Hybrid search engine with full-text and semantic search"""
    
    def __init__(self):
        self.storage_manager = StorageManager()
        self.embedding_generator = EmbeddingGenerator()
        self.logger = logging.getLogger(__name__)
    
    def search(self, query: str, category: str = None, max_results: int = 10, 
               search_type: str = "hybrid") -> List[Dict]:
        """Perform hybrid search combining full-text and semantic search"""
        if not query or not query.strip():
            return []
        
        # Clean and prepare query
        clean_query = self._clean_query(query)
        
        results = []
        
        if search_type in ["hybrid", "fulltext"]:
            # Perform full-text search
            fulltext_results = self.storage_manager.search_documents(
                clean_query, category=category, limit=max_results * 2
            )
            results.extend(self._add_search_type(fulltext_results, "fulltext"))
        
        if search_type in ["hybrid", "semantic"]:
            # Perform semantic search
            semantic_results = self._semantic_search(query, category, max_results)
            results.extend(self._add_search_type(semantic_results, "semantic"))
        
        # Combine and rank results
        if search_type == "hybrid" and results:
            results = self._combine_hybrid_results(results, clean_query)
        else:
            # Enhanced relevance scoring for single search type
            results = self._calculate_relevance_scores(clean_query, results)
        
        # Sort by relevance and limit results
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        # Remove duplicates while preserving order
        seen_docs = set()
        unique_results = []
        for result in results:
            doc_id = result.get('id')
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_results.append(result)
        
        return unique_results[:max_results]
    
    def _semantic_search(self, query: str, category: str = None, limit: int = 10) -> List[Dict]:
        """Perform semantic search using ChromaDB embeddings with domain filtering"""
        try:
            # Map category to domain for ChromaDB search
            domain = self._map_category_to_domain(category) if category else None
            
            # Get similar chunks with domain filtering
            similar_chunks = self.embedding_generator.search_similar_chunks(
                query=query,
                domain=domain,
                limit=limit * 3  # Get more chunks to group by document
            )
            
            # Group chunks by document and aggregate scores
            doc_scores = {}
            for chunk in similar_chunks:
                doc_id = chunk['document_id']
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        'id': doc_id,
                        'title': chunk.get('title', 'Unknown Document'),
                        'url': chunk.get('url', ''),
                        'domain': chunk.get('domain', 'general'),
                        'content': '',
                        'semantic_score': 0,
                        'best_chunk': chunk['chunk_text'],
                        'chunk_count': 0,
                        'similarity_score': chunk['similarity']  # Add similarity for debugging
                    }
                
                # Aggregate semantic scores (weighted by position)
                position_weight = 1.0 / (chunk['chunk_position'] + 1)
                doc_scores[doc_id]['semantic_score'] += chunk['similarity'] * position_weight
                doc_scores[doc_id]['chunk_count'] += 1
                
                # Keep the best chunk excerpt
                if chunk['similarity'] > 0.8:  # High similarity threshold
                    doc_scores[doc_id]['best_chunk'] = chunk['chunk_text'][:300] + "..."
            
            # Convert to list and normalize scores
            results = list(doc_scores.values())
            for result in results:
                # Normalize by chunk count to avoid bias toward longer documents
                result['semantic_score'] = result['semantic_score'] / max(result['chunk_count'], 1)
                result['relevance_score'] = result['semantic_score']  # For compatibility
                
                # Get full document content if needed
                if not result['content']:
                    doc_data = self.storage_manager.get_document_by_id(result['id'])
                    if doc_data:
                        result['content'] = doc_data.get('content', '')
            
            return results
            
        except Exception as e:
            self.logger.error(f"Semantic search failed: {e}")
            return []
    
    def _map_category_to_domain(self, category: str) -> str:
        """Map category names to ChromaDB domain names"""
        if not category:
            return None
            
        category_mapping = {
            'Technology': 'technology',
            'Business': 'business', 
            'Science': 'science',
            'Healthcare': 'healthcare',
            'Education': 'education',
            'General': 'general'
        }
        
        return category_mapping.get(category, category.lower())
    
    def _combine_hybrid_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Combine and score results from both full-text and semantic search"""
        # Group results by document ID
        combined_docs = {}
        
        for result in results:
            doc_id = result['id']
            search_type = result['search_type']
            
            if doc_id not in combined_docs:
                combined_docs[doc_id] = {
                    'id': doc_id,
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'url': result.get('url', ''),
                    'domain': result.get('domain', ''),
                    'fulltext_score': 0,
                    'semantic_score': 0,
                    'search_types': set()
                }
            
            # Add scores from different search types
            if search_type == 'fulltext':
                combined_docs[doc_id]['fulltext_score'] = result.get('relevance_score', 0)
                combined_docs[doc_id]['search_types'].add('fulltext')
            elif search_type == 'semantic':
                combined_docs[doc_id]['semantic_score'] = result.get('semantic_score', 0)
                combined_docs[doc_id]['search_types'].add('semantic')
                # Use best chunk if available
                if 'best_chunk' in result:
                    combined_docs[doc_id]['best_chunk'] = result['best_chunk']
        
        # Calculate hybrid scores
        hybrid_results = []
        for doc_data in combined_docs.values():
            # Hybrid scoring: combine full-text and semantic scores
            fulltext_weight = 0.4
            semantic_weight = 0.6
            
            # Bonus for appearing in both search types
            multi_type_bonus = 1.2 if len(doc_data['search_types']) > 1 else 1.0
            
            hybrid_score = (
                doc_data['fulltext_score'] * fulltext_weight +
                doc_data['semantic_score'] * semantic_weight
            ) * multi_type_bonus
            
            doc_data['final_score'] = hybrid_score
            doc_data['score_breakdown'] = {
                'fulltext': doc_data['fulltext_score'],
                'semantic': doc_data['semantic_score'],
                'hybrid': hybrid_score,
                'multi_type_bonus': multi_type_bonus
            }
            
            hybrid_results.append(doc_data)
        
        return hybrid_results
    
    def _add_search_type(self, results: List[Dict], search_type: str) -> List[Dict]:
        """Add search type metadata to results"""
        for result in results:
            result['search_type'] = search_type
        return results
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize search query"""
        # Remove special characters, convert to lowercase
        clean = re.sub(r'[^\w\s]', ' ', query.lower())
        # Remove extra whitespace
        clean = ' '.join(clean.split())
        return clean
    
    def _calculate_relevance_scores(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Calculate enhanced relevance scores"""
        query_terms = set(query.split())
        
        for doc in documents:
            # Basic relevance from database query
            base_score = doc.get('relevance_score', 0)
            
            # Title matching score
            title_score = self._calculate_text_match_score(
                query_terms, doc.get('title', '').lower()
            )
            
            # Content matching score  
            content_score = self._calculate_text_match_score(
                query_terms, doc.get('content', '').lower()
            )
            
            # Document quality score
            quality_score = self._calculate_quality_score(doc)
            
            # Calculate final weighted score
            final_score = (
                base_score * 0.3 +
                title_score * 0.4 +
                content_score * 0.2 +
                quality_score * 0.1
            )
            
            doc['final_score'] = final_score
            doc['score_breakdown'] = {
                'base': base_score,
                'title': title_score,
                'content': content_score,
                'quality': quality_score
            }
        
        return documents
    
    def _calculate_text_match_score(self, query_terms: set, text: str) -> float:
        """Calculate text matching score"""
        if not text or not query_terms:
            return 0.0
        
        text_words = set(text.split())
        matches = len(query_terms.intersection(text_words))
        
        # Normalize by query length
        score = matches / len(query_terms) if query_terms else 0
        
        # Bonus for phrase matching
        query_phrase = ' '.join(query_terms)
        if query_phrase in text:
            score *= 1.5
        
        return min(score, 1.0)
    
    def _calculate_quality_score(self, document: Dict) -> float:
        """Calculate document quality score"""
        score = 0.5  # Base score
        
        # Word count factor
        word_count = document.get('word_count', 0)
        if 100 <= word_count <= 2000:
            score += 0.3
        elif word_count > 50:
            score += 0.1
        
        # Title quality
        title = document.get('title', '')
        if len(title) > 10 and not title.isupper():
            score += 0.1
        
        # Domain credibility
        domain = document.get('domain', '')
        if any(ext in domain for ext in ['.edu', '.gov', '.org']):
            score += 0.1
        
        return min(score, 1.0)
