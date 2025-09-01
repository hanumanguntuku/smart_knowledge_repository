# Code Architecture Reference

## Key Classes & Methods

### ChromaDB Integration
```python
# src/search/chroma_client.py
class ChromaDBClient:
    - __init__(): Initialize with persistent storage
    - add_embeddings(): Store embeddings in domain collections
    - search_similar(): Vector similarity search
    - get_collection_for_domain(): Domain-specific collections
    - delete_document_embeddings(): Remove embeddings

# src/search/embedding_engine.py
class EmbeddingGenerator:
    - generate_embeddings_for_document(): Main embedding pipeline
    - search_similar_chunks(): ChromaDB search with metadata enhancement
    - _classify_domain(): Auto-domain classification
    - _generate_embedding(): OpenAI/SentenceTransformer embedding
```

### Storage Pipeline
```python
# src/storage/storage_manager.py
class StorageManager:
    - store_document(): Store doc + auto-generate embeddings
    - _auto_categorize_document(): Keyword-based categorization
    - _generate_embeddings_async(): Background embedding generation

# src/search/search_engine.py
class SearchEngine:
    - search(): Hybrid fulltext + semantic search
    - _semantic_search(): ChromaDB domain-filtered search
    - _map_category_to_domain(): Category → domain mapping
```

## Configuration
```python
# src/core/config.py
chroma_persist_directory = "data/chroma_db"
chroma_distance_metric = "l2"
use_domain_collections = True
embedding_model = "all-MiniLM-L6-v2"
chunk_size = 500
similarity_threshold = 0.7
```

## Database Schema
```sql
-- SQLite (metadata only)
documents: id, url, title, content, domain, created_at
categories: id, name, description, color
document_categories: document_id, category_id, confidence

-- ChromaDB Collections
knowledge_base_technology, knowledge_base_business, 
knowledge_base_science, knowledge_base_healthcare,
knowledge_base_education, knowledge_base_general
```

## Import Structure
```python
from src.search.chroma_client import chroma_client
from src.search.embedding_engine import EmbeddingGenerator
from src.storage.storage_manager import StorageManager
from src.core.config import config
```
