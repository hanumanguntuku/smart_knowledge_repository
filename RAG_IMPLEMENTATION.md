# 🧠 RAG (Retrieval-Augmented Generation) Implementation Guide

## 📋 Overview

The Smart Knowledge Repository implements **RAG (Retrieval-Augmented Generation)** to provide intelligent, context-aware responses based on your stored knowledge base. This document explains how RAG works in the codebase and how to configure different LLM backends.

## 🔍 What is RAG?

**RAG** combines two key components:
1. **Retrieval**: Finding relevant information from a knowledge base
2. **Generation**: Using an LLM to generate coherent responses based on retrieved context

## 🏗️ RAG Implementation Architecture

### 📁 File Structure
```
src/ai/scope_chatbot.py          # Main RAG implementation
src/core/config.py               # LLM configuration settings
src/search/search_engine.py     # Document retrieval system
src/storage/storage_manager.py  # Knowledge base storage
```

## 🔄 RAG Flow in the Code

### 1. **Query Processing** 
**Location**: `src/ai/scope_chatbot.py` - `process_query()` method

```python
def process_query(self, query: str, user_context: Dict = None) -> Dict:
    # Step 1: Analyze query scope and domain
    scope_result = self._analyze_query_scope(query)
    
    # Step 2: Route to appropriate handler
    if scope_result['scope'] == QueryScope.IN_SCOPE:
        return self._handle_in_scope_query(query, scope_result, user_context)
```

### 2. **Document Retrieval** 
**Location**: `src/ai/scope_chatbot.py` - `_handle_in_scope_query()` method

```python
def _handle_in_scope_query(self, query: str, scope_result: Dict, user_context: Dict) -> Dict:
    # RETRIEVAL: Search relevant documents
    category = scope_result['domain'].title() if scope_result['domain'] != 'general' else None
    search_results = self.search_engine.search(
        query=query,
        category=category,
        max_results=5  # Top 5 most relevant documents
    )
    
    # Generate response using retrieved context
    response = self._generate_contextual_response(query, search_results, scope_result, user_context)
```

### 3. **Context Preparation**
**Location**: `src/ai/scope_chatbot.py` - `_prepare_context()` method

```python
def _prepare_context(self, search_results: List[Dict], query: str) -> str:
    # Sort by relevance score
    sorted_results = sorted(search_results, key=lambda x: x.get('score', 0), reverse=True)
    
    # Extract relevant sections from top documents
    context_parts = []
    for result in sorted_results[:3]:  # Top 3 results
        title = result.get('title', 'Unknown Document')
        content = result.get('content', '')
        
        # Extract most relevant sections
        relevant_content = self._extract_relevant_sections(content, query)
        context_parts.append(f'Document: "{title}"\nContent: {relevant_content}')
    
    return "\n".join(context_parts)
```

### 4. **LLM Response Generation**
**Location**: `src/ai/scope_chatbot.py` - `_generate_contextual_response()` method

```python
def _generate_contextual_response(self, query: str, search_results: List[Dict], 
                                scope_result: Dict, user_context: Dict) -> str:
    # Prepare context from retrieved documents (RETRIEVAL)
    context_content = self._prepare_context(search_results, query)
    
    # Generate response using LLM (GENERATION)
    if self.llm_client == "openai":
        response = self._generate_openai_response(query, context_content, scope_result)
    elif self.llm_client == "local":
        response = self._generate_local_llm_response(query, context_content, scope_result)
    else:
        response = self._generate_simple_response(query, context_content, scope_result)
    
    return response
```

## 🛠️ LLM Integration Options

### Option 1: OpenAI GPT (Recommended for Production)

**Configuration** (`.env` file):
```env
USE_OPENAI=true
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
MAX_TOKENS=500
TEMPERATURE=0.7
```

**Implementation**: `_generate_openai_response()` method
```python
def _generate_openai_response(self, query: str, context: str, scope_result: Dict) -> str:
    system_prompt = f"You are a knowledgeable assistant specializing in {scope_result['domain']} topics."
    user_prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer based on the context:"
    
    response = openai.ChatCompletion.create(
        model=config.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=config.max_tokens,
        temperature=config.temperature
    )
    
    return response.choices[0].message.content.strip()
```

### Option 2: Local Transformer Models

**Configuration** (`.env` file):
```env
USE_OPENAI=false
LOCAL_LLM_MODEL=microsoft/DialoGPT-medium
MAX_TOKENS=500
TEMPERATURE=0.7
```

**Implementation**: `_generate_local_llm_response()` method
```python
def _generate_local_llm_response(self, query: str, context: str, scope_result: Dict) -> str:
    prompt = f"Context: {context}\nQuestion: {query}\nAnswer:"
    
    inputs = self.tokenizer.encode(prompt, return_tensors='pt', max_length=512, truncation=True)
    
    with torch.no_grad():
        outputs = self.model.generate(
            inputs,
            max_length=inputs.shape[1] + config.max_tokens,
            temperature=config.temperature,
            do_sample=True
        )
    
    response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response[len(prompt):].strip()
```

### Option 3: Fallback Simple Response (No LLM Required)

**Implementation**: `_generate_simple_response()` method
- Extracts and ranks sentences from retrieved context
- Uses keyword matching for relevance
- Provides basic but functional responses

## 🎯 RAG Quality Improvements

### 1. **Better Context Retrieval**
```python
def _extract_relevant_sections(self, content: str, query: str, max_length: int = 300) -> str:
    # Keyword-based sentence ranking
    query_words = query.lower().split()
    sentences = content.split('.')
    
    # Score sentences by query word overlap
    sentence_scores = [(sentence, sum(1 for word in query_words if word in sentence.lower())) 
                      for sentence in sentences]
    
    # Return top-scored sentences
    top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:3]
    return '. '.join([s[0].strip() for s in top_sentences if s[0].strip()])
```

### 2. **Domain-Specific Prompts**
```python
def _build_system_prompt(self, domain: str) -> str:
    return f"""You are a knowledgeable assistant specializing in {domain} topics.
    
Your role is to:
1. Answer questions based ONLY on the provided context
2. Be accurate and cite your sources
3. If context is insufficient, clearly state this
4. Keep responses concise but informative"""
```

### 3. **Conversation Context**
```python
def _update_conversation_context(self, query: str, response: str, sources: List[Dict]):
    interaction = {
        'query': query,
        'response': response,
        'sources': [s.get('title', 'Unknown') for s in sources],
        'timestamp': datetime.now().isoformat()
    }
    self.conversation_context.append(interaction)
    
    # Keep only recent history (last 10 interactions)
    if len(self.conversation_context) > 10:
        self.conversation_context = self.conversation_context[-10:]
```

## ⚙️ Configuration Options

### Environment Variables
```env
# LLM Backend Choice
USE_OPENAI=true                    # Use OpenAI GPT models
OPENAI_API_KEY=sk-...             # Your OpenAI API key
OPENAI_MODEL=gpt-3.5-turbo        # GPT model to use

# Local Model Settings
LOCAL_LLM_MODEL=microsoft/DialoGPT-medium  # HuggingFace model

# Generation Parameters
MAX_TOKENS=500                     # Maximum response length
TEMPERATURE=0.7                    # Creativity level (0.0-1.0)

# Retrieval Settings
MAX_RESULTS=5                      # Documents to retrieve
SIMILARITY_THRESHOLD=0.7           # Minimum relevance score
```

### Code Configuration (`src/core/config.py`)
```python
# LLM settings for chatbot
self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
self.use_openai = os.getenv("USE_OPENAI", "false").lower() == "true"
self.local_llm_model = os.getenv("LOCAL_LLM_MODEL", "microsoft/DialoGPT-medium")
self.max_tokens = int(os.getenv("MAX_TOKENS", "500"))
self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
```

## 🚀 Setup Instructions

### 1. **Install Dependencies**
```bash
# For OpenAI integration
pip install openai tiktoken

# For local models
pip install transformers torch

# Or install all
pip install -r requirements.txt
```

### 2. **Configure Environment**
Create `.env` file:
```env
# Choose your LLM backend
USE_OPENAI=true
OPENAI_API_KEY=your_api_key_here

# Or use local models
USE_OPENAI=false
LOCAL_LLM_MODEL=microsoft/DialoGPT-medium
```

### 3. **Test RAG System**
```python
from src.ai.scope_chatbot import ScopeAwareChatbot
from src.storage.storage_manager import StorageManager
from src.search.search_engine import SearchEngine

# Initialize components
storage = StorageManager()
search = SearchEngine()
chatbot = ScopeAwareChatbot(storage, search)

# Test RAG
response = chatbot.process_query("What is machine learning?")
print(response['response'])
```

## 📊 RAG Performance Metrics

### Evaluation Criteria
1. **Relevance**: How well retrieved documents match the query
2. **Accuracy**: How factually correct the generated response is
3. **Completeness**: How comprehensive the answer is
4. **Source Attribution**: How well sources are cited

### Monitoring
- Check `logs/` for RAG operation logs
- Monitor response times and quality
- Track user satisfaction with generated responses

## 🎯 Advanced RAG Features

### 1. **Multi-Document Reasoning**
The system can combine information from multiple documents to answer complex questions.

### 2. **Domain-Aware Responses**
Responses are tailored to the detected domain (technology, business, science, etc.).

### 3. **Scope Detection**
Automatically detects if a question is within the knowledge base scope.

### 4. **Graceful Degradation**
Falls back to simpler methods if LLM is unavailable.

## 🔧 Customization

### Adding New LLM Backends
1. Add configuration in `src/core/config.py`
2. Implement generation method in `ScopeAwareChatbot`
3. Update `_initialize_llm()` method
4. Test with your knowledge base

### Improving Retrieval
1. Enhance `_extract_relevant_sections()` method
2. Add semantic similarity scoring
3. Implement re-ranking algorithms
4. Use vector embeddings for better matching

### Custom Prompts
1. Modify `_build_system_prompt()` for domain-specific behavior
2. Customize `_build_user_prompt()` for better context formatting
3. Add conversation history to prompts

## 🎉 Summary

The RAG implementation in Smart Knowledge Repository provides:

- ✅ **Complete RAG Pipeline**: Retrieval → Context → Generation
- ✅ **Multiple LLM Backends**: OpenAI, Local models, Fallback
- ✅ **Domain Awareness**: Specialized responses by topic
- ✅ **Scope Detection**: Handles out-of-scope queries gracefully
- ✅ **Conversation Context**: Maintains chat history
- ✅ **Source Attribution**: Cites retrieved documents
- ✅ **Graceful Degradation**: Works without expensive LLM APIs

This creates a powerful, knowledge-grounded AI assistant that can provide accurate, contextual responses based on your specific domain knowledge!
