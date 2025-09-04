#!/usr/bin/env python3
"""
Test script for Google Gemini integration
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import google.generativeai as genai
    from src.core.config import config
    
    print("✅ Google Generative AI imported successfully")
    
    # Test if Gemini API key is configured
    if config.gemini_api_key and config.gemini_api_key != "your-gemini-api-key-here":
        try:
            genai.configure(api_key=config.gemini_api_key)
            model = genai.GenerativeModel(config.gemini_model)  # Use configured model
            
            # Test simple generation
            response = model.generate_content("Say hello")
            print(f"✅ Gemini API test successful: {response.text}")
            
        except Exception as e:
            print(f"⚠️ Gemini API test failed: {e}")
            print("💡 Please set a valid GEMINI_API_KEY in your .env file")
    else:
        print("⚠️ Gemini API key not configured in .env file")
        print("💡 Add GEMINI_API_KEY=your-actual-key to .env file")
    
    # Test embedding engine initialization
    from src.search.embedding_engine import EmbeddingGenerator
    embedding_gen = EmbeddingGenerator()
    print(f"✅ Embedding engine initialized with type: {embedding_gen.embedding_type}")
    
    # Test chatbot initialization
    from src.storage.storage_manager import StorageManager
    from src.search.search_engine import SearchEngine
    from src.ai.scope_chatbot import ScopeAwareChatbot
    
    storage_manager = StorageManager()
    search_engine = SearchEngine()
    chatbot = ScopeAwareChatbot(storage_manager, search_engine)
    print(f"✅ Chatbot initialized with LLM client: {chatbot.llm_client}")
    
    print("\n🎉 All components initialized successfully!")
    print("\n📋 Configuration Summary:")
    print(f"   - OpenAI enabled: {config.use_openai}")
    print(f"   - Gemini fallback enabled: {config.use_gemini_fallback}")
    print(f"   - OpenAI embeddings: {config.use_openai_embeddings}")
    print(f"   - Embedding fallback: {config.embedding_fallback}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install google-generativeai")
except Exception as e:
    print(f"❌ Error: {e}")
