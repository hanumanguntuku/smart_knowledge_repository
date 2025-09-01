# Smart Knowledge Repository

An intelligent knowledge management system that demonstrates advanced data collection, storage optimization, intelligent retrieval, and scope-aware AI interactions.

## Features

- 🌐 **Structured Web Scraping**: Automated content discovery and extraction
- 🗄️ **Smart Storage**: SQLite database with JSON support and vector embeddings
- 🔍 **Semantic Search**: Advanced search with relevance scoring
- 🤖 **AI-Powered Chat**: Context-aware responses using stored knowledge
- 📊 **Analytics Dashboard**: Usage insights and knowledge base statistics
- 🎯 **Scope Management**: Domain-aware query handling
- 📱 **Multi-View Interface**: Search, Browse, Chat, and Management views

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/smart-knowledge-repository.git
cd smart-knowledge-repository

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Configuration

1. Copy `.env.example` to `.env` and update settings:
```bash
cp .env.example .env
```

2. Initialize the database:
```bash
python src/main.py
```

### Run the Application

#### Streamlit UI (Recommended)
```bash
streamlit run src/ui/streamlit_app.py
```

#### FastAPI Backend (Optional)
```bash
uvicorn src.api.main:app --reload
```

## Project Structure

```
smart-knowledge-repository/
├── src/
│   ├── core/              # Core configuration and database
│   ├── storage/           # Data storage and management
│   ├── crawlers/          # Web scraping and content extraction
│   ├── processors/        # Text processing and validation
│   ├── search/            # Search engine and relevance scoring
│   ├── ai/               # AI context management and scope handling
│   └── ui/               # Streamlit user interface
├── schemas/              # Database schemas
├── tests/               # Unit and integration tests
├── data/               # Database and embeddings storage
└── logs/               # Application logs
```

## Usage

### 1. Adding Content

**Web Scraping:**
- Navigate to Data Management → Web Scraping
- Enter a URL to scrape
- Set maximum depth and pages
- Start scraping process

**Manual Upload:**
- Go to Data Management → Add Content
- Fill in document details
- Submit to add to knowledge base

### 2. Searching Knowledge

**Basic Search:**
- Use the Search page
- Enter keywords or phrases
- Filter by category
- View relevance-scored results

**AI Chat:**
- Go to Chat Interface
- Ask natural language questions
- Get context-aware responses with sources

### 3. Managing Knowledge

**Browse Documents:**
- View all documents by category
- Filter and sort options
- Edit or delete documents

**Analytics:**
- Monitor usage patterns
- View search trends
- Analyze knowledge coverage

## Configuration

### Environment Variables

Create a `.env` file with:

```env
# Database
SQLITE_DB_PATH=data/knowledge.db
VECTOR_DB_PATH=data/embeddings/

# AI/ML
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Scraping
MAX_CRAWL_DEPTH=3
CRAWL_DELAY=1.0
MAX_CONCURRENT_REQUESTS=5

# Security
SECRET_KEY=your-secret-key-here
```

### Customization

#### Adding New Categories
```python
# In src/storage/storage_manager.py
storage_manager.create_category(
    name="Custom Category",
    description="Your category description",
    color="#custom-color"
)
```

#### Custom Domain Keywords
```python
# In src/core/config.py
knowledge_domains = {
    "your_domain": ["keyword1", "keyword2", "keyword3"]
}
```

## API Documentation

### Search Documents
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "max_results": 10}'
```

### Add Document
```bash
curl -X POST "http://localhost:8000/documents" \
  -H "Content-Type: application/json" \
  -d '{"title": "Document Title", "content": "Document content...", "url": "https://example.com"}'
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
```bash
# Linting
flake8 src/

# Type checking
mypy src/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Architecture

### Data Flow
1. **Content Ingestion**: Web scraping or manual upload
2. **Validation**: Data validation and normalization
3. **Storage**: SQLite database with metadata
4. **Indexing**: Vector embeddings generation
5. **Search**: Hybrid keyword + semantic search
6. **AI Processing**: Context-aware response generation

### Security Features
- Input validation and sanitization
- SQL injection prevention
- Rate limiting for scraping
- Secure file handling

## Performance

### Optimization Tips
- Regular database maintenance
- Vector index optimization
- Content chunking strategies
- Caching frequently accessed data

### Monitoring
- Built-in analytics dashboard
- Search performance metrics
- Storage utilization tracking
- Error logging and monitoring

## Troubleshooting

### Common Issues

**Database locked error:**
```bash
# Stop all running instances and restart
pkill -f streamlit
streamlit run src/ui/streamlit_app.py
```

**Import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**Slow search performance:**
```bash
# Rebuild search index
python -c "from src.storage.storage_manager import StorageManager; StorageManager().rebuild_index()"
```

## License

MIT License - see LICENSE file for details.

## Support

- 📖 Documentation: [Wiki](https://github.com/yourusername/smart-knowledge-repository/wiki)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/smart-knowledge-repository/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/smart-knowledge-repository/discussions)

## Roadmap

- [ ] Advanced AI integration (GPT, Claude)
- [ ] Real-time collaboration features
- [ ] Advanced visualization tools
- [ ] Mobile application
- [ ] Multi-language support
- [ ] Cloud deployment options
