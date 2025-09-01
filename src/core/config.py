"""
Core configuration module for Smart Knowledge Repository
"""
import os
import json
from typing import List, Dict
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    # python-dotenv not available, skip loading
    pass


class Settings:
    """Configuration settings for the Smart Knowledge Repository"""
    
    def __init__(self):
        # Application settings
        self.app_name = os.getenv("APP_NAME", "Smart Knowledge Repository")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Database settings
        self.sqlite_db_path = os.getenv("SQLITE_DB_PATH", "data/knowledge.db")
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", "data/embeddings/")  # Legacy for fallback
        self.backup_path = os.getenv("BACKUP_PATH", "data/backups/")
        
        # ChromaDB settings
        self.chroma_persist_directory = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")
        self.chroma_distance_metric = os.getenv("CHROMA_DISTANCE_METRIC", "l2")  # l2, cosine, ip
        self.use_domain_collections = os.getenv("USE_DOMAIN_COLLECTIONS", "true").lower() == "true"
        self.chroma_batch_size = int(os.getenv("CHROMA_BATCH_SIZE", "100"))
        
        # Vector embedding settings
        self.use_chromadb = os.getenv("USE_CHROMADB", "true").lower() == "true"
        
        # AI/ML settings
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.vector_dimension = int(os.getenv("VECTOR_DIMENSION", "384"))
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
        
        # LLM settings for chatbot
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.use_openai = os.getenv("USE_OPENAI", "false").lower() == "true"
        self.local_llm_model = os.getenv("LOCAL_LLM_MODEL", "microsoft/DialoGPT-medium")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "500"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # Search settings
        self.max_results = int(os.getenv("MAX_RESULTS", "10"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
        self.search_timeout = int(os.getenv("SEARCH_TIMEOUT", "30"))
        
        # Crawling settings
        self.max_crawl_depth = int(os.getenv("MAX_CRAWL_DEPTH", "3"))
        self.crawl_delay = float(os.getenv("CRAWL_DELAY", "1.0"))
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
        # Security settings
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
        # Supported languages and domains
        self.supported_languages = self._parse_list(os.getenv("SUPPORTED_LANGUAGES", "en,es,fr,de"))
        self.knowledge_domains = self._parse_knowledge_domains(os.getenv("KNOWLEDGE_DOMAINS", ""))
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated string into list"""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def _parse_knowledge_domains(self, value: str) -> Dict[str, List[str]]:
        """Parse knowledge domains from JSON string or return defaults"""
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # Default knowledge domains
        return {
            "technology": ["AI", "machine learning", "software", "programming", "computer"],
            "business": ["strategy", "management", "finance", "marketing", "sales"],
            "science": ["research", "experiment", "hypothesis", "data", "analysis"],
            "healthcare": ["medical", "health", "treatment", "diagnosis", "patient"],
            "education": ["learning", "teaching", "student", "curriculum", "academic"]
        }
    
    def _ensure_directories(self):
        """Create necessary directories"""
        import os
        directories = [
            os.path.dirname(self.sqlite_db_path),
            self.vector_db_path,  # Keep for fallback
            self.backup_path,
            self.chroma_persist_directory,  # ChromaDB storage
            "logs"
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)


def load_config() -> Settings:
    """Load configuration from environment and defaults"""
    return Settings()


# Global config instance
config = load_config()
