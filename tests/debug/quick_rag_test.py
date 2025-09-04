#!/usr/bin/env python3
"""
Quick test script to add some URLs and test the RAG system with Gemini embeddings
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from crawlers.web_scraper import WebScraper
from search.embedding_engine import EmbeddingEngine
from ai.scope_chatbot import ScopeChatbot

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Add some test URLs and test the RAG system"""
    
    print("🔄 Quick RAG Test with Gemini Embeddings")
    print("=" * 50)
    
    # Test URLs
    test_urls = [
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://en.wikipedia.org/wiki/Machine_learning",
        "https://en.wikipedia.org/wiki/Natural_language_processing"
    ]
    
    # Initialize components
    print("1️⃣ Initializing components...")
    scraper = WebScraper()
    embedding_engine = EmbeddingEngine()
    chatbot = ScopeChatbot()
    
    print(f"   Embedding type: {embedding_engine.embedding_type}")
    
    # Scrape and process URLs
    print("2️⃣ Scraping test URLs...")
    for i, url in enumerate(test_urls, 1):
        print(f"   Processing {i}/{len(test_urls)}: {url}")
        try:
            # Scrape the URL
            success = scraper.scrape_url(url)
            if success:
                print(f"   ✅ Successfully scraped: {url}")
            else:
                print(f"   ❌ Failed to scrape: {url}")
        except Exception as e:
            print(f"   ❌ Error scraping {url}: {e}")
    
    # Test the RAG system
    print("3️⃣ Testing RAG system...")
    test_query = "What is artificial intelligence?"
    print(f"   Query: '{test_query}'")
    
    try:
        response = chatbot.generate_response(test_query)
        print(f"   ✅ Response generated!")
        print(f"   Response preview: {response['response'][:200]}...")
        print(f"   Sources found: {len(response.get('sources', []))}")
        print(f"   Scope: {response.get('scope', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Error generating response: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Quick test complete!")

if __name__ == "__main__":
    main()
