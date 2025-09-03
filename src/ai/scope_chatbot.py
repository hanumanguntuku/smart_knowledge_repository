"""
Scope-aware chatbot with domain detection and LLM integration
Enhanced with conversation management and context optimization
"""
import re
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum
from datetime import datetime
from ..core.config import config

# Import conversation management components
try:
    from .conversation_manager import ConversationContextManager
    CONVERSATION_MANAGER_AVAILABLE = True
except ImportError:
    CONVERSATION_MANAGER_AVAILABLE = False

try:
    from ..storage.conversation_storage import ConversationStorageManager
    CONVERSATION_STORAGE_AVAILABLE = True
except ImportError:
    CONVERSATION_STORAGE_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)

# Optional LLM imports - graceful degradation if not available
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

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class QueryScope(Enum):
    """Query scope classification"""
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    PARTIAL_SCOPE = "partial_scope"
    CLARIFICATION_NEEDED = "clarification_needed"


class DomainDetector:
    """Detects query domain, intent, and extracts entities"""
    
    def __init__(self, knowledge_domains: Dict[str, List[str]]):
        self.knowledge_domains = knowledge_domains
        self.domain_keywords = self._build_keyword_map()
        self.intent_patterns = self._build_intent_patterns()
    
    def _build_keyword_map(self) -> Dict[str, List[str]]:
        """Build keyword map for domains"""
        return {domain: [kw.lower() for kw in keywords] 
                for domain, keywords in self.knowledge_domains.items()}
    
    def _build_intent_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for intent classification"""
        return {
            'factual': ['what is', 'define', 'explain', 'describe', 'tell me about'],
            'comparison': ['compare', 'difference', 'versus', 'vs', 'better than', 'similar'],
            'how_to': ['how to', 'how can', 'steps to', 'guide', 'tutorial'],
            'list': ['list', 'examples', 'types of', 'kinds of', 'show me'],
            'analysis': ['analyze', 'evaluate', 'assess', 'review', 'opinion'],
            'recommendation': ['recommend', 'suggest', 'best', 'should i', 'which']
        }
    
    def analyze_query(self, query: str) -> Dict:
        """Comprehensive query analysis including domain, intent, and entities"""
        domain, domain_confidence = self.detect_query_domain(query)
        intent, intent_confidence = self.classify_intent(query)
        entities = self.extract_entities(query)
        optimized_query = self.optimize_query(query, entities)
        
        return {
            'domain': domain,
            'domain_confidence': domain_confidence,
            'intent': intent,
            'intent_confidence': intent_confidence,
            'entities': entities,
            'optimized_query': optimized_query,
            'original_query': query
        }
    
    def classify_intent(self, query: str) -> Tuple[str, float]:
        """Classify the intent of the query"""
        query_lower = query.lower()
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in query_lower:
                    score += 1
            intent_scores[intent_type] = score / len(patterns) if patterns else 0
        
        if not intent_scores or max(intent_scores.values()) == 0:
            return 'factual', 0.5  # Default intent
        
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]
        
        return best_intent, confidence
    
    def extract_entities(self, query: str) -> List[Dict]:
        """Extract named entities from query"""
        entities = []
        
        # Simple rule-based entity extraction
        # Capitalized words (potential proper nouns)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', query)
        for word in capitalized_words:
            if len(word) > 2:
                entities.append({
                    'text': word,
                    'type': 'PROPER_NOUN',
                    'confidence': 0.6
                })
        
        # Technical terms (common patterns)
        tech_patterns = [
            r'\b(?:API|SQL|HTML|CSS|JavaScript|Python|React|Django|Flask|AI|ML)\b',
            r'\b(?:machine learning|artificial intelligence|deep learning|neural network)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match,
                    'type': 'TECHNOLOGY',
                    'confidence': 0.8
                })
        
        # Remove duplicates
        unique_entities = []
        seen = set()
        for entity in entities:
            if entity['text'].lower() not in seen:
                seen.add(entity['text'].lower())
                unique_entities.append(entity)
        
        return unique_entities
    
    def optimize_query(self, query: str, entities: List[Dict]) -> str:
        """Optimize query for better search results"""
        # Extract key terms from entities first
        key_terms = [entity['text'] for entity in entities]
        
        # Extended stop words including question words for keyword search
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'what', 'is', 'are', 'how', 'when', 'where', 'why', 'which', 'who', 'whom', 'whose',
            'can', 'could', 'would', 'should', 'might', 'may', 'will', 'shall', 'do', 'does', 'did',
            'tell', 'me', 'about', 'explain', 'describe', 'define'
        }
        
        words = query.lower().split()
        
        # Keep important terms, prioritize entities
        optimized_words = []
        for word in words:
            # Keep if it's part of an entity
            if any(word in entity['text'].lower() for entity in entities):
                optimized_words.append(word)
            # Keep if it's not a stop word and is substantial
            elif word not in stop_words and len(word) > 2:
                optimized_words.append(word)
        
        # If we have entities, prioritize them
        if key_terms:
            # Use the longest/most specific entity terms
            entity_terms = sorted(key_terms, key=len, reverse=True)
            optimized = ' '.join(entity_terms[:2])  # Use top 2 most specific entities
        else:
            optimized = ' '.join(optimized_words)
        
        # Fallback to original if optimization resulted in empty string
        return optimized if optimized.strip() else query.lower()
    
    def detect_query_domain(self, query: str) -> Tuple[str, float]:
        """Detect the primary domain of a query"""
        query_lower = query.lower()
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            domain_scores[domain] = score / len(keywords) if keywords else 0
        
        if not domain_scores or max(domain_scores.values()) == 0:
            return 'general', 0.0
        
        best_domain = max(domain_scores, key=domain_scores.get)
        confidence = domain_scores[best_domain]
        
        return best_domain, confidence


class ScopeAwareChatbot:
    """Chatbot with scope awareness, domain detection, and LLM integration"""
    
    def __init__(self, storage_manager, search_engine, session_id: str = None):
        self.storage_manager = storage_manager
        self.search_engine = search_engine
        self.domain_detector = DomainDetector(config.knowledge_domains)
        self.conversation_context = []
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize conversation management if available
        if CONVERSATION_MANAGER_AVAILABLE and CONVERSATION_STORAGE_AVAILABLE:
            self.context_manager = ConversationContextManager()
            self.conversation_storage = ConversationStorageManager()
            self.conversation_enabled = True
            self.current_thread_id = self.conversation_storage.get_or_create_active_thread(self.session_id)
            logger.info(f"✅ Conversation management enabled for session {self.session_id}")
        else:
            self.context_manager = None
            self.conversation_storage = None
            self.conversation_enabled = False
            self.current_thread_id = None
            logger.warning("⚠️ Conversation management not available - using basic mode")
        
        # Initialize LLM
        self.llm_client = self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize LLM client with OpenAI primary and Gemini fallback"""
        # Try OpenAI first
        if config.use_openai and OPENAI_AVAILABLE and config.openai_api_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=config.openai_api_key)
                logger.info("✅ OpenAI LLM client initialized")
                return "openai"
            except Exception as e:
                logger.warning(f"⚠️ OpenAI initialization failed: {e}")
                
        # Fallback to Gemini
        if config.use_gemini_fallback and GEMINI_AVAILABLE and config.gemini_api_key:
            try:
                genai.configure(api_key=config.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(config.gemini_model)
                logger.info("✅ Gemini LLM client initialized as fallback")
                return "gemini"
            except Exception as e:
                logger.warning(f"⚠️ Gemini initialization failed: {e}")
                
        # Local transformer fallback
        elif TRANSFORMERS_AVAILABLE:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(config.local_llm_model)
                self.model = AutoModelForCausalLM.from_pretrained(config.local_llm_model)
                return "local"
            except Exception as e:
                print(f"Failed to load local model: {e}")
                return None
        else:
            return None
        
    def process_query(self, query: str, user_context: Dict = None) -> Dict:
        """Process user query with enhanced analysis and response generation"""
        try:
            # Enhanced conversation context analysis if available
            if self.conversation_enabled and self.context_manager:
                context_analysis = self.context_manager.analyze_query_context(
                    query, self.current_thread_id, self.session_id
                )
                
                # Use resolved query if available
                enhanced_query = context_analysis.get('resolved_query', query)
                
                # Save user message to conversation
                self.conversation_storage.save_message(
                    self.current_thread_id, 'user', query, 
                    metadata={'context_analysis': context_analysis}
                )
            else:
                enhanced_query = query
                context_analysis = {'context_needed': False, 'is_follow_up': False}
            
            # Enhanced query analysis
            query_analysis = self.domain_detector.analyze_query(enhanced_query)
            
            # Analyze scope based on enhanced analysis
            scope_result = self._analyze_query_scope_enhanced(enhanced_query, query_analysis)
            
            # Update conversation context early for better context resolution
            self._add_to_conversation_context('user', query, query_analysis)
            
            if scope_result['scope'] == QueryScope.OUT_OF_SCOPE:
                response = self._handle_out_of_scope_query(enhanced_query, scope_result)
            elif scope_result['scope'] == QueryScope.CLARIFICATION_NEEDED:
                response = self._request_clarification(enhanced_query, scope_result)
            else:
                response = self._handle_in_scope_query_enhanced(enhanced_query, scope_result, query_analysis, user_context)
            
            # Save assistant response to conversation if available
            if self.conversation_enabled and self.conversation_storage:
                self.conversation_storage.save_message(
                    self.current_thread_id, 'assistant', response.get('response', ''),
                    sources=response.get('sources', []),
                    metadata={
                        'confidence': response.get('confidence', 0),
                        'citations': response.get('citations', []),
                        'context_analysis': context_analysis
                    }
                )
            
            # Add assistant response to context
            self._add_to_conversation_context('assistant', response.get('response', ''), {
                'sources': response.get('sources', []),
                'confidence': response.get('confidence', 0),
                'citations': response.get('citations', [])
            })
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            return {
                'response': "I apologize, but I encountered an error processing your request. Please try again.",
                'sources': [],
                'confidence': 0.0,
                'scope': QueryScope.OUT_OF_SCOPE,
                'error': str(e)
            }
    
    def _analyze_query_scope_enhanced(self, query: str, query_analysis: Dict) -> Dict:
        """Enhanced scope analysis using query understanding"""
        domain = query_analysis['domain']
        confidence = query_analysis['domain_confidence']
        
        # Use optimized query for better search
        optimized_query = query_analysis['optimized_query']
        
        # Use SEMANTIC SEARCH instead of keyword search for scope analysis
        # This allows finding relevant documents based on meaning, not just exact text matches
        relevant_docs = self.search_engine.search(
            query=optimized_query,
            max_results=5,
            search_type="semantic"  # Use pure semantic search for better relevance
        )
        
        # Enhanced scope determination - lower threshold since semantic search is better
        if len(relevant_docs) > 0:
            # Check semantic similarity scores to determine scope
            max_score = max([doc.get('semantic_score', 0) for doc in relevant_docs], default=0)
            
            if max_score > 0.7:  # High semantic similarity
                scope = QueryScope.IN_SCOPE
            elif max_score > 0.4:  # Medium semantic similarity
                scope = QueryScope.PARTIAL_SCOPE
            elif len(relevant_docs) > 0:  # Some results found
                scope = QueryScope.PARTIAL_SCOPE
            else:
                scope = QueryScope.OUT_OF_SCOPE
        else:
            scope = QueryScope.OUT_OF_SCOPE
        
        return {
            'scope': scope,
            'domain': domain,
            'confidence': confidence,
            'relevant_docs_count': len(relevant_docs),
            'intent': query_analysis['intent'],
            'intent_confidence': query_analysis['intent_confidence'],
            'entities': query_analysis['entities'],
            'optimized_query': optimized_query,
            'max_semantic_score': max([doc.get('semantic_score', 0) for doc in relevant_docs], default=0)
        }
    
    def _handle_in_scope_query_enhanced(self, query: str, scope_result: Dict, 
                                      query_analysis: Dict, user_context: Dict) -> Dict:
        """Enhanced in-scope query handling with better search and citations"""
        # Perform enhanced search using hybrid approach
        
        # Try different search strategies based on intent
        search_strategy = self._determine_search_strategy(query_analysis['intent'])
        
        search_results = self.search_engine.search(
            query=scope_result['optimized_query'],
            max_results=8,  # Get more results for better context
            search_type=search_strategy
        )
        
        # Generate enhanced response with proper citations
        response_data = self._generate_enhanced_response(
            query, search_results, scope_result, query_analysis, user_context
        )
        
        return {
            'response': response_data['response'],
            'sources': response_data['sources'],
            'citations': response_data['citations'],
            'confidence': response_data['confidence'],
            'knowledge_gaps': response_data['knowledge_gaps'],
            'scope': scope_result['scope'].value,
            'domain': scope_result['domain'],
            'intent': scope_result['intent'],
            'search_strategy': search_strategy,
            'query_analysis': query_analysis
        }
    
    def _determine_search_strategy(self, intent: str) -> str:
        """Determine best search strategy based on query intent"""
        intent_strategies = {
            'factual': 'hybrid',      # Best overall results
            'comparison': 'semantic',  # Need conceptual understanding
            'how_to': 'fulltext',     # Procedural content
            'list': 'fulltext',       # Structured content
            'analysis': 'semantic',   # Conceptual understanding
            'recommendation': 'hybrid' # Combined approach
        }
        
        return intent_strategies.get(intent, 'hybrid')
    
    def _format_source(self, result: Dict) -> Dict:
        """Format search result as source with citation information"""
        # Get the best available score
        score = (result.get('final_score') or 
                result.get('semantic_score') or 
                result.get('relevance_score') or 
                result.get('score', 0))
        
        return {
            'title': result.get('title', 'Unknown Document'),
            'url': result.get('url', ''),
            'domain': result.get('domain', 'general'),
            'excerpt': result.get('best_chunk', result.get('content', ''))[:200] + '...',
            'score': score,
            'doc_id': result.get('id', result.get('document_id', ''))
        }
    
    def _generate_enhanced_response(self, query: str, search_results: List[Dict],
                                  scope_result: Dict, query_analysis: Dict, 
                                  user_context: Dict) -> Dict:
        """Generate enhanced response with proper citations and knowledge gap detection"""
        if not search_results:
            return {
                'response': "I couldn't find specific information about your question in my knowledge base.",
                'sources': [],
                'citations': [],
                'confidence': 0.0,
                'knowledge_gaps': ['No relevant documents found']
            }
        
        # Prepare context with citation tracking
        context_data = self._prepare_context_with_citations(search_results, query)
        
        # Check for knowledge gaps
        knowledge_gaps = self._identify_knowledge_gaps(query_analysis, search_results)
        
        # Calculate confidence based on search results and coverage
        confidence = self._calculate_response_confidence(search_results, query_analysis)
        
        # Generate response using LLM with enhanced prompts
        if self.llm_client == "openai":
            response = self._generate_openai_response_enhanced(
                query, context_data, scope_result, query_analysis
            )
        elif self.llm_client == "gemini":
            response = self._generate_gemini_response(
                query, context_data, scope_result, query_analysis
            )
        elif self.llm_client == "local":
            response = self._generate_local_llm_response_enhanced(
                query, context_data, scope_result, query_analysis
            )
        else:
            response = self._generate_enhanced_fallback_response(
                query, context_data, scope_result, query_analysis
            )
        
        # Add knowledge gap warnings if necessary
        if knowledge_gaps:
            gap_warning = f"\n\n⚠️ **Knowledge Gaps**: {', '.join(knowledge_gaps)}"
            response += gap_warning
        
        return {
            'response': response,
            'sources': [self._format_source(result) for result in search_results],
            'citations': context_data['citations'],
            'confidence': confidence,
            'knowledge_gaps': knowledge_gaps
        }
    
    def _prepare_context_with_citations(self, search_results: List[Dict], query: str) -> Dict:
        """Prepare context data with proper citation tracking"""
        context_parts = []
        citations = []
        
        for i, result in enumerate(search_results[:5], 1):  # Top 5 results
            # Extract key information
            content = result.get('content', '')[:500]  # Limit content length
            title = result.get('title', 'Untitled Document')
            url = result.get('url', '')
            score = result.get('score', 0)
            
            # Create citation
            citation = {
                'id': i,
                'title': title,
                'url': url,
                'score': score,
                'excerpt': content[:100] + '...' if len(content) > 100 else content
            }
            citations.append(citation)
            
            # Add to context with citation marker
            context_part = f"[{i}] {title}: {content}"
            context_parts.append(context_part)
        
        return {
            'context': '\n\n'.join(context_parts),
            'citations': citations,
            'total_sources': len(search_results)
        }
    
    def _identify_knowledge_gaps(self, query_analysis: Dict, search_results: List[Dict]) -> List[str]:
        """Identify potential knowledge gaps in the available information"""
        gaps = []
        
        # Check entity coverage
        entities = query_analysis.get('entities', [])
        covered_entities = set()
        
        for result in search_results:
            content = result.get('content', '').lower()
            for entity in entities:
                # Handle entity as dictionary with 'text' field
                entity_text = entity.get('text', '') if isinstance(entity, dict) else str(entity)
                if entity_text.lower() in content:
                    covered_entities.add(entity_text.lower())
        
        # Find uncovered entities
        uncovered_entities = []
        for entity in entities:
            entity_text = entity.get('text', '') if isinstance(entity, dict) else str(entity)
            if entity_text.lower() not in covered_entities:
                uncovered_entities.append(entity_text)
        
        if uncovered_entities:
            gaps.append(f"Limited information about: {', '.join(uncovered_entities)}")
        
        # Check result quality
        if search_results:
            # Get the best available score from each result
            scores = []
            for r in search_results:
                score = (r.get('final_score') or 
                        r.get('semantic_score') or 
                        r.get('relevance_score') or 
                        r.get('score', 0))
                scores.append(score)
            
            avg_score = sum(scores) / len(scores) if scores else 0
            # Adjusted threshold: 0.15 for semantic similarity (more realistic)
            if avg_score < 0.15:
                gaps.append("Search results have low relevance scores")
        
        # Check result diversity
        domains = set(r.get('category', 'unknown').lower() for r in search_results)
        if len(domains) == 1 and query_analysis.get('intent') == 'comparison':
            gaps.append("Limited perspective - results from single domain")
        
        return gaps
    
    def _calculate_response_confidence(self, search_results: List[Dict], 
                                     query_analysis: Dict) -> float:
        """Calculate confidence score for the response"""
        if not search_results:
            return 0.0
        
        # Base confidence from search results
        avg_score = sum(r.get('score', 0) for r in search_results) / len(search_results)
        
        # Adjust based on intent match
        intent_confidence = query_analysis.get('intent_confidence', 0.5)
        
        # Adjust based on number of quality results
        quality_results = len([r for r in search_results if r.get('score', 0) > 0.5])
        result_factor = min(quality_results / 3, 1.0)  # Ideal: 3+ quality results
        
        # Combine factors
        confidence = (avg_score * 0.4 + intent_confidence * 0.3 + result_factor * 0.3)
        
        return min(max(confidence, 0.0), 1.0)  # Clamp to [0, 1]
    
    def _generate_openai_response_enhanced(self, query: str, context_data: Dict,
                                         scope_result: Dict, query_analysis: Dict) -> str:
        """Generate enhanced response using OpenAI with better prompting"""
        try:
            # Create enhanced system prompt
            system_prompt = f"""You are a knowledgeable assistant that answers questions based ONLY on the provided context. 

Guidelines:
1. Answer using ONLY information from the provided context
2. Include citation numbers [1], [2], etc. when referencing sources
3. If the context doesn't contain enough information, clearly state this
4. Be concise but comprehensive
5. For {query_analysis['intent']} queries, focus on providing {self._get_intent_guidance(query_analysis['intent'])}

Context with citations:
{context_data['context']}

Remember: Use citations [1], [2], etc. when referencing specific information."""

            user_prompt = f"""Query: {query}
Intent: {query_analysis['intent']}
Domain: {scope_result['domain']}

Please provide a comprehensive answer based on the context provided, including proper citations."""

            response = self.openai_client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Handle specific OpenAI errors gracefully
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["insufficient_quota", "quota", "exceeded", "limit"]):
                logger.warning(f"⚠️ OpenAI quota exceeded, falling back to Gemini")
                return self._generate_gemini_response(query, context_data, scope_result, query_analysis)
            elif any(keyword in error_msg for keyword in ["rate_limit", "rate limit", "too many requests"]):
                logger.warning(f"⚠️ OpenAI rate limit reached, falling back to Gemini")
                return self._generate_gemini_response(query, context_data, scope_result, query_analysis)
            elif "api_key" in error_msg or "authentication" in error_msg:
                logger.warning(f"⚠️ OpenAI authentication issue, falling back to Gemini")
                return self._generate_gemini_response(query, context_data, scope_result, query_analysis)
            else:
                logger.error(f"❌ OpenAI response generation failed: {e}")
                return self._generate_gemini_response(query, context_data, scope_result, query_analysis)
    
    def _generate_local_llm_response_enhanced(self, query: str, context_data: Dict,
                                            scope_result: Dict, query_analysis: Dict) -> str:
        """Generate enhanced response using local LLM"""
        try:
            from transformers import pipeline
            
            if not hasattr(self, '_qa_pipeline'):
                self._qa_pipeline = pipeline(
                    "question-answering",
                    model="distilbert-base-cased-distilled-squad",
                    return_tensors="pt"
                )
            
            # Use the pipeline for basic QA
            result = self._qa_pipeline(
                question=query,
                context=context_data['context'][:1000]  # Limit context for local model
            )
            
            base_answer = result['answer']
            confidence = result['score']
            
            # Enhance with citation information
            enhanced_response = f"{base_answer}\n\nBased on {len(context_data['citations'])} sources in our knowledge base."
            
            if confidence < 0.5:
                enhanced_response += "\n\n⚠️ Note: This answer has lower confidence. Please verify with additional sources."
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Local LLM response generation failed: {e}")
            return self._generate_enhanced_fallback_response(query, context_data, scope_result, query_analysis)
    
    def _generate_enhanced_fallback_response(self, query: str, context_data: Dict,
                                           scope_result: Dict, query_analysis: Dict) -> str:
        """Generate enhanced fallback response when LLMs are unavailable"""
        if not context_data['citations']:
            return "I couldn't find relevant information in my knowledge base to answer your question."
        
        # Extract key information from top results
        top_result = context_data['citations'][0]
        response_parts = []
        
        # Intent-specific response formatting
        intent = query_analysis['intent']
        
        if intent == 'factual':
            response_parts.append(f"Based on my knowledge base, here's what I found about your question:")
        elif intent == 'how_to':
            response_parts.append(f"Here are the steps/information I found related to your request:")
        elif intent == 'comparison':
            response_parts.append(f"Here's a comparison based on available information:")
        else:
            response_parts.append(f"Based on my search, here's the relevant information:")
        
        # Add content summary
        response_parts.append(f"\n{top_result['excerpt']}")
        
        # Add source information
        if len(context_data['citations']) == 1:
            response_parts.append(f"\nSource: {top_result['title']} [1]")
        else:
            response_parts.append(f"\nFound {len(context_data['citations'])} relevant sources. See citations [1]-[{len(context_data['citations'])}] for details.")
        
        # Add confidence indicator
        avg_score = sum(c['score'] for c in context_data['citations']) / len(context_data['citations'])
        if avg_score < 0.5:
            response_parts.append("\n\n⚠️ Note: Search results have moderate relevance. Consider refining your question.")
        
        return ''.join(response_parts)
    
    def _generate_gemini_response(self, query: str, context_data: Dict,
                                scope_result: Dict, query_analysis: Dict) -> str:
        """Generate response using Google Gemini when OpenAI fails"""
        try:
            if not hasattr(self, 'gemini_model'):
                # Initialize Gemini if not already done
                if GEMINI_AVAILABLE and config.gemini_api_key:
                    genai.configure(api_key=config.gemini_api_key)
                    self.gemini_model = genai.GenerativeModel(config.gemini_model)
                else:
                    return self._generate_enhanced_fallback_response(query, context_data, scope_result, query_analysis)
            
            # Build context from search results
            context_text = ""
            if context_data['citations']:
                context_text = "\n\n".join([
                    f"Document: {c['title']}\nContent: {c['excerpt']}\nSource: {c['url']}"
                    for c in context_data['citations'][:3]  # Top 3 results
                ])
            
            # Create prompt for Gemini
            system_instruction = f"""You are an AI assistant with access to a knowledge base. 
            Answer the user's question based on the provided context. Be accurate, helpful, and cite sources.
            
            Query Intent: {query_analysis['intent']}
            Query Domain: {query_analysis['domain']}
            Scope: {scope_result['scope']}"""
            
            user_prompt = f"""Question: {query}
            
            Context from knowledge base:
            {context_text}
            
            Please provide a comprehensive answer based on the context provided, including proper citations."""
            
            # Generate response using Gemini
            full_prompt = f"{system_instruction}\n\n{user_prompt}"
            response = self.gemini_model.generate_content(full_prompt)
            
            logger.info("✅ Generated response using Gemini (OpenAI fallback)")
            return response.text
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle specific Gemini quota/rate limit errors with detailed detection
            if any(keyword in error_msg for keyword in ["quota", "exceeded", "limit", "resource_exhausted", "insufficient_quota"]):
                logger.error(f"❌ Gemini quota/rate limit exceeded: {e}")
                return self._generate_enhanced_fallback_response(query, context_data, scope_result, query_analysis)
            elif any(keyword in error_msg for keyword in ["safety", "blocked", "content_filter", "harmful"]):
                logger.warning(f"⚠️ Gemini content safety filter triggered: {e}")
                return "I apologize, but I cannot provide a response to this query due to content safety policies. Please rephrase your question."
            elif any(keyword in error_msg for keyword in ["api_key", "authentication", "unauthorized", "permission"]):
                logger.error(f"❌ Gemini authentication issue: {e}")
                return self._generate_enhanced_fallback_response(query, context_data, scope_result, query_analysis)
            elif any(keyword in error_msg for keyword in ["invalid_argument", "bad_request", "malformed"]):
                logger.error(f"❌ Gemini invalid request: {e}")
                return self._generate_enhanced_fallback_response(query, context_data, scope_result, query_analysis)
            elif any(keyword in error_msg for keyword in ["timeout", "deadline", "timed_out"]):
                logger.warning(f"⚠️ Gemini request timeout: {e}")
                return "I apologize, but the request timed out. Please try again with a shorter question."
            else:
                logger.error(f"❌ Gemini response generation failed with unexpected error: {e}")
                return self._generate_enhanced_fallback_response(query, context_data, scope_result, query_analysis)
    
    def _get_intent_guidance(self, intent: str) -> str:
        """Get response guidance based on query intent"""
        guidance = {
            'factual': 'direct, factual information with supporting details',
            'how_to': 'step-by-step instructions or procedures',
            'comparison': 'comparative analysis highlighting similarities and differences',
            'list': 'organized lists or structured information',
            'analysis': 'analytical insights and interpretations',
            'recommendation': 'actionable recommendations with reasoning'
        }
        return guidance.get(intent, 'comprehensive and relevant information')
    
    def _add_to_conversation_context(self, role: str, content: str, metadata: Dict = None):
        """Add message to conversation context with metadata"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.conversation_context.append(message)
        
        # Manage context window (keep last 20 messages)
        if len(self.conversation_context) > 20:
            self.conversation_context = self.conversation_context[-20:]
    
    def get_conversation_history(self, format_type: str = 'json') -> Union[List[Dict], str]:
        """Get conversation history in specified format"""
        if format_type == 'json':
            return self.conversation_context
        elif format_type == 'markdown':
            return self._format_conversation_as_markdown()
        elif format_type == 'text':
            return self._format_conversation_as_text()
        else:
            return self.conversation_context
    
    def _format_conversation_as_markdown(self) -> str:
        """Format conversation history as markdown"""
        markdown_parts = ["# Conversation History\n"]
        
        for i, message in enumerate(self.conversation_context, 1):
            role = message['role'].title()
            content = message['content']
            timestamp = message['timestamp']
            
            markdown_parts.append(f"## {i}. {role} ({timestamp})\n")
            markdown_parts.append(f"{content}\n")
            
            # Add metadata if available
            if message.get('metadata'):
                metadata = message['metadata']
                if metadata.get('sources'):
                    markdown_parts.append(f"**Sources**: {len(metadata['sources'])} documents\n")
                if metadata.get('confidence'):
                    markdown_parts.append(f"**Confidence**: {metadata['confidence']:.2f}\n")
            
            markdown_parts.append("\n---\n\n")
        
        return ''.join(markdown_parts)
    
    def _format_conversation_as_text(self) -> str:
        """Format conversation history as plain text"""
        text_parts = []
        
        for message in self.conversation_context:
            role = message['role'].upper()
            content = message['content']
            timestamp = message['timestamp']
            
            text_parts.append(f"[{timestamp}] {role}: {content}\n")
        
        return '\n'.join(text_parts)
    
    def clear_conversation_context(self):
        """Clear conversation history"""
        self.conversation_context = []
    
    def export_conversation(self, file_path: str, format_type: str = 'json'):
        """Export conversation to file"""
        try:
            import json
            
            if format_type == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.conversation_context, f, indent=2, ensure_ascii=False)
            elif format_type == 'markdown':
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._format_conversation_as_markdown())
            elif format_type == 'text':
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._format_conversation_as_text())
            
            logger.info(f"Conversation exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export conversation: {e}")
            return False
        
        # Add knowledge gap warnings if necessary
        if knowledge_gaps:
            gap_warning = f"\n\n⚠️ **Knowledge Gaps**: {', '.join(knowledge_gaps)}"
            response += gap_warning
        
        return {
            'response': response,
            'sources': [self._format_source(result) for result in search_results],
            'citations': context_data['citations'],
            'confidence': confidence,
            'knowledge_gaps': knowledge_gaps
        }
    
    def _analyze_query_scope(self, query: str) -> Dict:
        """Analyze if query is within knowledge scope"""
        domain, confidence = self.domain_detector.detect_query_domain(query)
        
        # Check if we have relevant documents in this domain
        relevant_docs = self.storage_manager.search_documents(
            query, limit=5
        )
        
        if confidence > 0.7 and relevant_docs:
            scope = QueryScope.IN_SCOPE
        elif confidence > 0.3 and relevant_docs:
            scope = QueryScope.PARTIAL_SCOPE
        elif confidence < 0.3:
            scope = QueryScope.OUT_OF_SCOPE
        else:
            scope = QueryScope.CLARIFICATION_NEEDED
        
        return {
            'scope': scope,
            'domain': domain,
            'confidence': confidence,
            'relevant_docs_count': len(relevant_docs)
        }
    
    def _handle_in_scope_query(self, query: str, scope_result: Dict, 
                              user_context: Dict) -> Dict:
        """Handle queries within knowledge scope"""
        # Perform search
        search_results = self.search_engine.search(
            query=query,
            max_results=5
        )
        
        # Generate context-aware response
        response = self._generate_contextual_response(
            query, search_results, scope_result, user_context
        )
        
        # Update conversation context
        self._update_conversation_context(query, response, search_results)
        
        return {
            'response': response,
            'sources': search_results,
            'scope': scope_result['scope'].value,
            'domain': scope_result['domain'],
            'confidence': scope_result['confidence']
        }
    
    def _handle_out_of_scope_query(self, query: str, scope_result: Dict) -> Dict:
        """Handle out-of-scope queries with helpful suggestions"""
        # Find closest available domains
        available_domains = list(config.knowledge_domains.keys())
        suggestions = self._generate_domain_suggestions(query, available_domains)
        
        response = f"""I don't have information about that topic in my current knowledge base. 

However, I can help you with questions about:
{chr(10).join(['• ' + domain.title() for domain in available_domains])}

Here are some suggested questions you could ask:
{chr(10).join(['• ' + suggestion for suggestion in suggestions])}

Would you like to ask about any of these topics instead?"""
        
        return {
            'response': response,
            'sources': [],
            'scope': QueryScope.OUT_OF_SCOPE.value,
            'suggestions': suggestions,
            'available_domains': available_domains
        }
    
    def _request_clarification(self, query: str, scope_result: Dict) -> Dict:
        """Request clarification for ambiguous queries"""
        response = f"""I need a bit more context to help you better. Your question seems to touch on {scope_result['domain']} topics, but I'd like to clarify:

Could you be more specific about:
• What specific aspect interests you most?
• Are you looking for general information or something technical?
• Do you have a particular use case in mind?

This will help me provide more relevant information from my knowledge base."""
        
        return {
            'response': response,
            'sources': [],
            'scope': QueryScope.CLARIFICATION_NEEDED.value,
            'domain': scope_result['domain'],
            'confidence': scope_result['confidence']
        }
    
    def _generate_contextual_response(self, query: str, search_results: List[Dict],
                                    scope_result: Dict, user_context: Dict) -> str:
        """Generate AI response using retrieved knowledge (RAG implementation)"""
        if not search_results:
            return "I couldn't find specific information about your question in my knowledge base."
        
        # Prepare context from retrieved documents (Retrieval part of RAG)
        context_content = self._prepare_context(search_results, query)
        
        # Generate response using LLM (Generation part of RAG)
        if self.llm_client == "openai":
            response = self._generate_openai_response(query, context_content, scope_result)
        elif self.llm_client == "local":
            response = self._generate_local_llm_response(query, context_content, scope_result)
        else:
            # Fallback to simple response if no LLM available
            response = self._generate_simple_response(query, context_content, scope_result)
        
        return response
    
    def _prepare_context(self, search_results: List[Dict], query: str) -> str:
        """Prepare context from retrieved documents"""
        # Sort by relevance score
        sorted_results = sorted(search_results, key=lambda x: x.get('score', 0), reverse=True)
        
        # Combine top relevant content with metadata
        context_parts = []
        for i, result in enumerate(sorted_results[:3]):  # Top 3 results
            title = result.get('title', 'Unknown Document')
            content = result.get('content', '')
            score = result.get('score', 0)
            
            # Truncate content to relevant sections
            relevant_content = self._extract_relevant_sections(content, query)
            
            context_parts.append(f"""
Document {i+1}: "{title}" (Relevance: {score:.2f})
Content: {relevant_content}
""")
        
        return "\n".join(context_parts)
    
    def _extract_relevant_sections(self, content: str, query: str, max_length: int = 300) -> str:
        """Extract most relevant sections from content based on query"""
        # Simple keyword-based extraction
        query_words = query.lower().split()
        sentences = content.split('.')
        
        # Score sentences based on query word overlap
        sentence_scores = []
        for sentence in sentences:
            score = sum(1 for word in query_words if word in sentence.lower())
            sentence_scores.append((sentence.strip(), score))
        
        # Sort by score and take top sentences
        top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:3]
        relevant_text = '. '.join([s[0] for s in top_sentences if s[0]])
        
        # Truncate if too long
        if len(relevant_text) > max_length:
            relevant_text = relevant_text[:max_length] + "..."
        
        return relevant_text
    
    def _generate_openai_response(self, query: str, context: str, scope_result: Dict) -> str:
        """Generate response using OpenAI GPT"""
        try:
            system_prompt = self._build_system_prompt(scope_result['domain'])
            user_prompt = self._build_user_prompt(query, context)
            
            response = openai.ChatCompletion.create(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_simple_response(query, context, scope_result)
    
    def _generate_local_llm_response(self, query: str, context: str, scope_result: Dict) -> str:
        """Generate response using local transformer model"""
        try:
            prompt = self._build_local_prompt(query, context, scope_result['domain'])
            
            # Tokenize input
            inputs = self.tokenizer.encode(prompt, return_tensors='pt', max_length=512, truncation=True)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + config.max_tokens,
                    temperature=config.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part
            generated_text = response[len(prompt):].strip()
            
            return generated_text if generated_text else self._generate_simple_response(query, context, scope_result)
            
        except Exception as e:
            print(f"Local LLM error: {e}")
            return self._generate_simple_response(query, context, scope_result)
    
    def _build_system_prompt(self, domain: str) -> str:
        """Build system prompt for OpenAI"""
        return f"""You are a knowledgeable assistant specializing in {domain} topics. 
        
Your role is to:
1. Answer questions based ONLY on the provided context from the knowledge base
2. Be accurate and helpful while staying within the scope of available information
3. If the context doesn't contain enough information, clearly state this
4. Provide specific references to the source documents when possible
5. Keep responses concise but informative

Always base your answers on the retrieved context and cite your sources."""
    
    def _build_user_prompt(self, query: str, context: str) -> str:
        """Build user prompt for OpenAI"""
        return f"""Context from knowledge base:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above. If the context doesn't contain sufficient information to answer the question, please state this clearly."""
    
    def _build_local_prompt(self, query: str, context: str, domain: str) -> str:
        """Build prompt for local LLM"""
        return f"""Context: {context[:500]}...

Question: {query}

Answer based on the context:"""
    
    def _generate_simple_response(self, query: str, context: str, scope_result: Dict) -> str:
        """Fallback simple response generation when no LLM is available"""
        # Enhanced simple response with better text processing
        sentences = []
        
        # Extract sentences from context
        for line in context.split('\n'):
            if 'Content:' in line:
                content = line.split('Content:')[1].strip()
                sentences.extend([s.strip() for s in content.split('.') if s.strip()])
        
        # Filter relevant sentences
        query_words = set(query.lower().split())
        relevant_sentences = []
        
        for sentence in sentences[:10]:  # Limit processing
            sentence_words = set(sentence.lower().split())
            overlap = len(query_words.intersection(sentence_words))
            if overlap > 0:
                relevant_sentences.append((sentence, overlap))
        
        # Sort by relevance and take top sentences
        relevant_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in relevant_sentences[:3]]
        
        if top_sentences:
            response = f"""Based on the information in my knowledge base:

{'. '.join(top_sentences)}.

This information comes from {len(scope_result.get('relevant_docs_count', 0))} relevant document(s) in my {scope_result['domain']} knowledge domain."""
        else:
            response = "I found some relevant documents, but couldn't extract specific information to answer your question. You may want to browse the full documents for more details."
        
        return response
    
    def _synthesize_answer(self, query: str, context: str) -> str:
        """Synthesize answer from context (simplified version)"""
        # This is a simplified implementation
        # In production, you would use a proper LLM here
        
        sentences = context.split('.')[:3]  # Take first 3 sentences
        return '. '.join(sentences).strip() + '.'
    
    def _generate_domain_suggestions(self, query: str, domains: List[str]) -> List[str]:
        """Generate suggested questions for available domains"""
        suggestions = []
        for domain in domains[:3]:  # Limit to top 3
            if domain == 'technology':
                suggestions.append("How does machine learning work?")
            elif domain == 'business':
                suggestions.append("What are effective business strategies?")
            elif domain == 'science':
                suggestions.append("What are the latest research findings?")
            elif domain == 'healthcare':
                suggestions.append("What are common treatment approaches?")
            elif domain == 'education':
                suggestions.append("What are effective learning methods?")
        
        return suggestions
    
    def _update_conversation_context(self, query: str, response: str, sources: List[Dict]):
        """Update conversation context"""
        interaction = {
            'query': query,
            'response': response,
            'sources': [s.get('title', 'Unknown') for s in sources],
            'timestamp': datetime.now().isoformat()
        }
        self.conversation_context.append(interaction)
        
        # Keep only recent history
        if len(self.conversation_context) > 10:
            self.conversation_context = self.conversation_context[-10:]

    def get_response(self, query: str) -> str:
        """Main method to get response to user query (for Streamlit interface)"""
        try:
            # Process the query using the enhanced pipeline
            result = self.process_query(query)
            
            # Return just the response text for simple interfaces
            return result.get('response', "I couldn't process your query. Please try again.")
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, I encountered an error while processing your question. Please try again."

    # Conversation Management Methods
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Get conversation history for current thread"""
        if not self.conversation_enabled:
            return self.conversation_context[-limit:]
        
        try:
            return self.conversation_storage.get_conversation_history(self.current_thread_id, limit)
        except Exception as e:
            logger.error(f"❌ Error getting conversation history: {e}")
            return []
    
    def start_new_conversation(self, title: str = None) -> bool:
        """Start a new conversation thread"""
        if not self.conversation_enabled:
            self.conversation_context = []
            return True
        
        try:
            self.current_thread_id = self.conversation_storage.create_conversation_thread(
                self.session_id, title
            )
            return self.current_thread_id is not None
        except Exception as e:
            logger.error(f"❌ Error starting new conversation: {e}")
            return False
    
    def get_user_conversations(self, limit: int = 20) -> List[Dict]:
        """Get all conversations for current user"""
        if not self.conversation_enabled:
            return []
        
        try:
            return self.conversation_storage.get_user_conversations(self.session_id, limit)
        except Exception as e:
            logger.error(f"❌ Error getting user conversations: {e}")
            return []
    
    def switch_conversation(self, thread_id: int) -> bool:
        """Switch to a different conversation thread"""
        if not self.conversation_enabled:
            return False
        
        try:
            # Verify thread belongs to current session
            conversations = self.get_user_conversations()
            valid_thread = any(conv['id'] == thread_id for conv in conversations)
            
            if valid_thread:
                self.current_thread_id = thread_id
                logger.info(f"🔄 Switched to conversation thread {thread_id}")
                return True
            else:
                logger.warning(f"❌ Unauthorized access to thread {thread_id}")
                return False
        except Exception as e:
            logger.error(f"❌ Error switching conversation: {e}")
            return False
    
    def delete_conversation(self, thread_id: int) -> bool:
        """Delete a conversation thread"""
        if not self.conversation_enabled:
            return False
        
        try:
            success = self.conversation_storage.delete_conversation(thread_id, self.session_id)
            
            # If current conversation was deleted, create new one
            if success and thread_id == self.current_thread_id:
                self.current_thread_id = self.conversation_storage.get_or_create_active_thread(self.session_id)
            
            return success
        except Exception as e:
            logger.error(f"❌ Error deleting conversation: {e}")
            return False
    
    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search conversations by content"""
        if not self.conversation_enabled:
            return []
        
        try:
            return self.conversation_storage.search_conversations(self.session_id, query, limit)
        except Exception as e:
            logger.error(f"❌ Error searching conversations: {e}")
            return []
    
    def get_follow_up_suggestions(self) -> List[str]:
        """Get follow-up question suggestions based on last response"""
        if not self.conversation_enabled or not self.context_manager:
            return []
        
        try:
            history = self.get_conversation_history(limit=5)
            if not history:
                return []
            
            # Get last assistant response
            assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
            if not assistant_messages:
                return []
            
            last_response = assistant_messages[-1]
            return self.context_manager.suggest_follow_up_questions(last_response, history)
        except Exception as e:
            logger.error(f"❌ Error getting follow-up suggestions: {e}")
            return []
