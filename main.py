"""
Main application entry point for Smart Knowledge Repository
"""
import os
import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core.config import config
from src.storage.storage_manager import StorageManager
from src.crawlers.web_scraper import WebScraper


def setup_logging():
    """Configure logging for the application"""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )


def setup_directories():
    """Create necessary directories"""
    directories = [
        'data',
        'data/embeddings',
        'data/backups',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def main():
    """Main application entry point"""
    print("🧠 Smart Knowledge Repository")
    print("=" * 50)
    
    # Setup
    setup_logging()
    setup_directories()
    
    # Initialize components
    storage_manager = StorageManager()
    web_scraper = WebScraper()
    
    print("✅ System initialized successfully!")
    print(f"📊 Database: {config.sqlite_db_path}")
    print(f"🔍 Embedding model: {config.embedding_model}")
    
    # Get statistics
    stats = storage_manager.get_statistics()
    print(f"📄 Documents: {stats.get('documents', {}).get('active', 0)}")
    print(f"🏷️ Categories: {stats.get('categories', 0)}")
    
    print("\n🚀 Ready to serve!")
    print("Run the following command to start the application:")
    print("  Streamlit UI: streamlit run src/ui/streamlit_app.py")
    print("\n💡 The Streamlit app provides:")
    print("  • AI-powered chat interface")
    print("  • Advanced search capabilities") 
    print("  • Document management")
    print("  • Analytics dashboard")
    print("  • All features in one unified interface")


if __name__ == "__main__":
    main()
