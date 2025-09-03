"""
Advanced Context Manager for Smart Knowledge Repository
Handles conversation context optimization, reference resolution, and follow-up processing
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from src.storage.conversation_storage import ConversationStorageManager


class ConversationContextManager:
    """Manages conversation context and provides intelligent follow-up handling"""
    
    def __init__(self, max_context_length: int = 4000):
        self.max_context_length = max_context_length
        self.conversation_storage = ConversationStorageManager()
        self.logger = logging.getLogger(__name__)
        
        # Common reference patterns
        self.reference_patterns = [
            r'\b(that|this|it|they|them|those|these)\b',
            r'\b(the (previous|last|earlier) (one|document|article|result))\b',
            r'\b(what (about|of) (that|this|it))\b',
            r'\b(tell me more)\b',
            r'\b(elaborate|expand|continue)\b',
            r'\b(more (details|information|info))\b'
        ]
        
        # Follow-up intent patterns
        self.follow_up_patterns = {
            'clarification': [r'\bwhat (do you )?mean\b', r'\bcan you clarify\b', r'\bexplain\b'],
            'elaboration': [r'\btell me more\b', r'\bmore (details|info)\b', r'\belaborate\b'],
            'related': [r'\bwhat about\b', r'\bhow about\b', r'\brelated to\b'],
            'comparison': [r'\bcompare\b', r'\bdifference\b', r'\bversus\b', r'\bvs\b'],
            'example': [r'\bexample\b', r'\binstance\b', r'\bfor example\b']
        }
    
    def analyze_query_context(self, query: str, thread_id: int, session_id: str) -> Dict:
        """Analyze query for context dependencies and follow-up intents"""
        try:
            # Get recent conversation history
            context_messages = self.conversation_storage.get_optimized_context(
                thread_id, self.max_context_length
            )
            
            analysis = {
                'is_follow_up': False,
                'intent_type': 'new_query',
                'references_previous': False,
                'resolved_query': query,
                'context_needed': False,
                'relevant_context': [],
                'confidence': 1.0
            }
            
            if not context_messages:
                return analysis
            
            # Check for reference patterns
            has_references = any(
                re.search(pattern, query.lower()) 
                for pattern in self.reference_patterns
            )
            
            if has_references:
                analysis['references_previous'] = True
                analysis['is_follow_up'] = True
                analysis['context_needed'] = True
                
                # Get the most recent assistant response for context
                recent_assistant_messages = [
                    msg for msg in context_messages[-5:] 
                    if msg['role'] == 'assistant'
                ]
                
                if recent_assistant_messages:
                    analysis['relevant_context'] = recent_assistant_messages[-1:]
                    analysis['resolved_query'] = self._resolve_references(
                        query, recent_assistant_messages[-1]
                    )
            
            # Classify follow-up intent
            analysis['intent_type'] = self._classify_intent(query)
            
            # Determine if context is needed
            if analysis['intent_type'] != 'new_query' or has_references:
                analysis['context_needed'] = True
                analysis['relevant_context'] = context_messages[-3:]  # Last 3 messages
            
            # Calculate confidence based on clarity of references
            analysis['confidence'] = self._calculate_confidence(query, has_references)
            
            self.logger.info(f"🔍 Query analysis: {analysis['intent_type']}, "
                           f"follow-up: {analysis['is_follow_up']}, "
                           f"confidence: {analysis['confidence']:.2f}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing query context: {e}")
            return {
                'is_follow_up': False,
                'intent_type': 'new_query',
                'references_previous': False,
                'resolved_query': query,
                'context_needed': False,
                'relevant_context': [],
                'confidence': 0.5
            }
    
    def _resolve_references(self, query: str, last_response: Dict) -> str:
        """Resolve pronouns and references in the query"""
        try:
            resolved = query
            last_content = last_response.get('content', '')
            
            # Extract key topics from last response
            topics = self._extract_topics(last_content)
            
            # Simple reference resolution
            replacements = {
                r'\bthat\b': topics[0] if topics else 'the topic',
                r'\bthis\b': topics[0] if topics else 'the subject',
                r'\bit\b': topics[0] if topics else 'the item',
                r'\bthe previous (one|document|article|result)\b': topics[0] if topics else 'the previous item'
            }
            
            for pattern, replacement in replacements.items():
                resolved = re.sub(pattern, replacement, resolved, flags=re.IGNORECASE)
            
            # Handle "tell me more" type queries
            if re.search(r'\btell me more\b', query.lower()):
                if topics:
                    resolved = f"Tell me more about {topics[0]}"
                else:
                    resolved = "Provide more details about the previous topic"
            
            self.logger.info(f"🔗 Reference resolution: '{query}' → '{resolved}'")
            return resolved
            
        except Exception as e:
            self.logger.error(f"❌ Error resolving references: {e}")
            return query
    
    def _extract_topics(self, text: str, max_topics: int = 3) -> List[str]:
        """Extract main topics from text"""
        try:
            # Simple topic extraction based on capitalized words and phrases
            words = text.split()
            topics = []
            
            # Look for capitalized words (potential proper nouns)
            capitalized = [word.strip('.,!?') for word in words if word[0].isupper() and len(word) > 2]
            topics.extend(capitalized[:2])
            
            # Look for quoted terms
            quoted = re.findall(r'"([^"]+)"', text)
            topics.extend(quoted[:2])
            
            # Look for technical terms (words with numbers or special chars)
            technical = re.findall(r'\b[A-Z][a-z]*[A-Z][a-z]*\b', text)  # CamelCase
            topics.extend(technical[:1])
            
            # Remove duplicates and limit
            unique_topics = list(dict.fromkeys(topics))[:max_topics]
            
            return unique_topics
            
        except Exception:
            return []
    
    def _classify_intent(self, query: str) -> str:
        """Classify the intent of the query"""
        query_lower = query.lower()
        
        for intent, patterns in self.follow_up_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                return intent
        
        return 'new_query'
    
    def _calculate_confidence(self, query: str, has_references: bool) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 1.0
        
        # Reduce confidence for very short queries
        if len(query.split()) < 3:
            confidence -= 0.2
        
        # Reduce confidence for ambiguous references
        ambiguous_terms = ['that', 'this', 'it', 'them']
        ambiguous_count = sum(1 for term in ambiguous_terms if term in query.lower())
        confidence -= ambiguous_count * 0.1
        
        # Increase confidence for clear follow-up indicators
        clear_indicators = ['tell me more', 'elaborate', 'explain', 'what about']
        if any(indicator in query.lower() for indicator in clear_indicators):
            confidence += 0.2
        
        return max(0.1, min(1.0, confidence))
    
    def build_context_prompt(self, query: str, context_analysis: Dict, 
                           search_results: List[Dict] = None) -> str:
        """Build an enhanced prompt with conversation context"""
        try:
            prompt_parts = []
            
            # Add conversation context if needed
            if context_analysis['context_needed'] and context_analysis['relevant_context']:
                prompt_parts.append("Previous Conversation Context:")
                for msg in context_analysis['relevant_context']:
                    role = msg['role'].title()
                    content = msg['content'][:500]  # Limit context length
                    prompt_parts.append(f"{role}: {content}")
                prompt_parts.append("")
            
            # Add current query
            resolved_query = context_analysis['resolved_query']
            if context_analysis['is_follow_up']:
                prompt_parts.append(f"Follow-up Query ({context_analysis['intent_type']}): {resolved_query}")
            else:
                prompt_parts.append(f"Query: {resolved_query}")
            
            # Add search results if available
            if search_results:
                prompt_parts.append("\nRelevant Knowledge:")
                for i, result in enumerate(search_results[:3], 1):
                    title = result.get('title', 'Unknown')
                    content = result.get('content', '')[:300]
                    score = result.get('final_score', 0)
                    prompt_parts.append(f"{i}. {title} (Score: {score:.2f})")
                    prompt_parts.append(f"   {content}...")
                    prompt_parts.append("")
            
            # Add instructions based on intent
            instructions = self._get_intent_instructions(context_analysis['intent_type'])
            if instructions:
                prompt_parts.append(f"Instructions: {instructions}")
            
            enhanced_prompt = "\n".join(prompt_parts)
            
            self.logger.info(f"🎯 Built enhanced prompt ({len(enhanced_prompt)} chars)")
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error(f"❌ Error building context prompt: {e}")
            return query
    
    def _get_intent_instructions(self, intent_type: str) -> str:
        """Get specific instructions based on intent type"""
        instructions = {
            'clarification': "Provide a clear explanation focusing on clarifying the previous response.",
            'elaboration': "Expand on the previous response with additional details and examples.",
            'related': "Discuss related topics and connections to the previous conversation.",
            'comparison': "Compare and contrast the topics being discussed.",
            'example': "Provide specific examples and use cases.",
            'new_query': "Provide a comprehensive response based on available knowledge."
        }
        
        return instructions.get(intent_type, instructions['new_query'])
    
    def summarize_conversation(self, thread_id: int, max_length: int = 200) -> str:
        """Generate a summary of the conversation"""
        try:
            messages = self.conversation_storage.get_conversation_history(thread_id, limit=20)
            
            if not messages:
                return "Empty conversation"
            
            # Extract key topics and themes
            user_queries = [msg['content'] for msg in messages if msg['role'] == 'user']
            assistant_responses = [msg['content'] for msg in messages if msg['role'] == 'assistant']
            
            # Simple summarization
            topics = []
            for query in user_queries:
                topics.extend(self._extract_topics(query, max_topics=2))
            
            unique_topics = list(dict.fromkeys(topics))[:5]
            
            if unique_topics:
                summary = f"Discussion about {', '.join(unique_topics[:3])}"
                if len(unique_topics) > 3:
                    summary += f" and {len(unique_topics) - 3} other topics"
            else:
                summary = f"Conversation with {len(user_queries)} questions"
            
            summary += f" ({len(messages)} messages)"
            
            # Truncate if too long
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Error summarizing conversation: {e}")
            return "Conversation summary unavailable"
    
    def suggest_follow_up_questions(self, last_response: Dict, context: List[Dict]) -> List[str]:
        """Suggest relevant follow-up questions"""
        try:
            suggestions = []
            content = last_response.get('content', '')
            sources = last_response.get('sources', [])
            
            # Extract topics for suggestions
            topics = self._extract_topics(content)
            
            # Generate topic-based suggestions
            if topics:
                suggestions.append(f"Tell me more about {topics[0]}")
                if len(topics) > 1:
                    suggestions.append(f"How does {topics[0]} relate to {topics[1]}?")
                suggestions.append(f"What are some examples of {topics[0]}?")
            
            # Source-based suggestions
            if sources:
                suggestions.append("What other information is available on this topic?")
                suggestions.append("Can you find related documents?")
            
            # General follow-up suggestions
            suggestions.extend([
                "Can you elaborate on this?",
                "What are the implications of this?",
                "Are there any alternatives?"
            ])
            
            # Return unique suggestions, limited to 5
            unique_suggestions = list(dict.fromkeys(suggestions))[:5]
            
            self.logger.info(f"💡 Generated {len(unique_suggestions)} follow-up suggestions")
            return unique_suggestions
            
        except Exception as e:
            self.logger.error(f"❌ Error generating follow-up suggestions: {e}")
            return []
