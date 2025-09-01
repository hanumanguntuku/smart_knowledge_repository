# Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for version control)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/smart-knowledge-repository.git
cd smart-knowledge-repository
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Additional Dependencies

For NLP processing:
```bash
python -m spacy download en_core_web_sm
```

For better text processing:
```bash
python -m nltk.downloader punkt stopwords
```

### 5. Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` file with your settings:
```env
# Database
SQLITE_DB_PATH=data/knowledge.db
VECTOR_DB_PATH=data/embeddings/

# AI/ML
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500

# Security
SECRET_KEY=your-secure-secret-key
```

### 6. Initialize Database

```bash
python main.py
```

### 7. Start the Application

#### Option A: Streamlit UI (Recommended)
```bash
streamlit run src/ui/streamlit_app.py
```

#### Option B: FastAPI Backend
```bash
uvicorn src.api.main:app --reload
```

## Verification

1. Open your browser to `http://localhost:8501` (Streamlit) or `http://localhost:8000` (FastAPI)
2. You should see the Smart Knowledge Repository interface
3. Try adding a test document to verify everything works

## Troubleshooting

### Common Issues

**1. Module Import Errors**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**2. Database Connection Issues**
```bash
# Check if data directory exists
mkdir -p data

# Run database initialization
python main.py
```

**3. Port Already in Use**
```bash
# For Streamlit (default port 8501)
streamlit run src/ui/streamlit_app.py --server.port 8502

# For FastAPI (default port 8000)
uvicorn src.api.main:app --port 8001
```

**4. Permission Issues**
```bash
# On macOS/Linux, ensure proper permissions
chmod +x main.py
chmod -R 755 data/
```

## Development Setup

For development work:

```bash
# Install development dependencies
pip install pytest flake8 black mypy

# Run tests
python -m pytest tests/

# Code formatting
black src/

# Linting
flake8 src/

# Type checking
mypy src/
```

## Docker Installation (Alternative)

If you prefer Docker:

```dockerfile
# Dockerfile is available in the repository
docker build -t smart-knowledge-repo .
docker run -p 8501:8501 smart-knowledge-repo
```

## Next Steps

After installation:

1. Read the [User Guide](USER_GUIDE.md)
2. Check out [API Documentation](API.md)
3. Review [Configuration Options](CONFIG.md)
4. Explore [Example Use Cases](EXAMPLES.md)
