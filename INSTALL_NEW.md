# Smart Knowledge Repository - Installation Guide

## Quick Start (Minimal Dependencies)

The Smart Knowledge Repository is designed to work with minimal dependencies for core functionality. Follow these steps to get started:

### 1. Prerequisites
- Python 3.8 or higher
- Git (optional, for cloning)

### 2. Basic Installation

```bash
# Clone or download the repository
git clone <your-repo-url> smart_knowledge_repository
cd smart_knowledge_repository

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install only essential dependencies
pip install streamlit
```

### 3. Start the Application

```bash
# Initialize the system (creates database and directories)
python main.py

# Start the web interface
streamlit run src/ui/streamlit_app.py
```

The application will be available at: http://localhost:8501

## Full Feature Installation

For complete functionality including web scraping, AI features, and analytics:

### 1. Install All Dependencies

```bash
# Install all optional dependencies
pip install -r requirements.txt
```

### 2. Optional AI Features

For AI-powered search and chatbot features:

```bash
pip install sentence-transformers transformers torch
```

### 3. Web Scraping Features

For automated web content crawling:

```bash
pip install aiohttp beautifulsoup4 lxml
```

### 4. Advanced Analytics

For enhanced charts and data visualization:

```bash
pip install plotly pandas numpy
```

## Configuration

### Environment Variables

Create a `.env` file in the project root for custom configuration:

```env
# Database settings
SQLITE_DB_PATH=data/knowledge.db
VECTOR_DB_PATH=data/embeddings/
BACKUP_PATH=data/backups/

# AI/ML settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DIMENSION=384
CHUNK_SIZE=500

# Search settings
MAX_RESULTS=10
SIMILARITY_THRESHOLD=0.7

# Web scraping settings
MAX_CONCURRENT_REQUESTS=5
CRAWL_DELAY=1.0
REQUEST_TIMEOUT=30

# Security
SECRET_KEY=your-secret-key-change-in-production

# UI settings
DEBUG=false
```

### Directory Structure

The application automatically creates these directories:
- `data/` - Database files and backups
- `logs/` - Application logs
- `data/embeddings/` - Vector embeddings storage
- `data/backups/` - Database backups

## Features Available

### Core Features (No External Dependencies)
- ✅ Document storage and management
- ✅ SQLite database with full-text search
- ✅ Basic categorization
- ✅ Streamlit web interface
- ✅ Data validation and security
- ✅ Search and browse functionality

### Enhanced Features (With Optional Dependencies)
- 🔗 **Web Scraping** (`aiohttp`, `beautifulsoup4`)
  - Automated content crawling
  - Link discovery and following
  - Content extraction and cleaning

- 🧠 **AI Features** (`sentence-transformers`, `transformers`)
  - Semantic search with embeddings
  - AI-powered chatbot
  - Automatic content categorization
  - Domain-aware responses

- 📊 **Analytics** (`plotly`, `pandas`)
  - Interactive charts and graphs
  - Search analytics dashboard
  - Usage statistics

- 🌐 **Language Support** (`langdetect`)
  - Multi-language content detection
  - Language-specific processing

## Usage Examples

### 1. Adding Documents

```python
# Via Web Interface
# Navigate to "Data Management" → "Add Document"
# Fill in title, content, and category

# Via API (when available)
from src.storage.storage_manager import StorageManager
storage = StorageManager()
storage.add_document("Title", "Content", "technology")
```

### 2. Searching Content

```python
# Via Web Interface
# Use the search box on the main page

# Via Search Engine
from src.search.search_engine import SearchEngine
search = SearchEngine()
results = search.search("machine learning")
```

### 3. Web Scraping (Optional)

```python
# Via Web Interface
# Navigate to "Data Management" → "Web Scraping"

# Via Code
from src.crawlers.web_scraper import WebScraper
scraper = WebScraper()
# Note: Requires aiohttp and beautifulsoup4
```

## Troubleshooting

### Common Issues

1. **ImportError for optional dependencies**
   - The system gracefully handles missing dependencies
   - Features requiring missing packages will be disabled
   - Install specific packages as needed

2. **Database connection issues**
   - Check if `data/` directory exists and is writable
   - Verify SQLite permissions

3. **Port already in use (8501)**
   ```bash
   streamlit run src/ui/streamlit_app.py --server.port 8502
   ```

4. **Module import errors**
   - Ensure you're running from the project root directory
   - Activate your virtual environment

### Logs and Debugging

- Application logs are stored in `logs/`
- Enable debug mode: set `DEBUG=true` in `.env`
- Check browser console for frontend issues

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Adding New Features

1. Follow the modular structure in `src/`
2. Add tests in `tests/`
3. Update documentation
4. Ensure graceful degradation for optional dependencies

## Deployment

### Production Considerations

1. **Security**
   - Change the default `SECRET_KEY`
   - Review and configure access controls
   - Validate all input data

2. **Performance**
   - Consider using a proper web server (nginx, apache)
   - Implement caching for frequent searches
   - Monitor resource usage

3. **Backup**
   - Regular database backups are automatic
   - Configure backup retention policy
   - Test restoration procedures

### Docker Deployment (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "src/ui/streamlit_app.py", "--server.address", "0.0.0.0"]
```

```bash
docker build -t smart-knowledge-repo .
docker run -p 8501:8501 smart-knowledge-repo
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs in the `logs/` directory
3. Create an issue in the project repository

## License

See LICENSE file for details.
