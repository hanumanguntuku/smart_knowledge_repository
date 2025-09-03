#!/usr/bin/env python3
"""
Test Gemini embeddings specifically
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
    
    print("🔍 Testing Gemini Embeddings Specifically...")
    print(f"Gemini API Key: {config.gemini_api_key[:20]}..." if config.gemini_api_key else "No key")
    print(f"Use Gemini Fallback: {config.use_gemini_fallback}")
    
    if config.gemini_api_key and config.gemini_api_key != "your-gemini-api-key-here":
        try:
            genai.configure(api_key=config.gemini_api_key)
            
            # Test embedding generation
            print("🧪 Testing Gemini embedding generation...")
            result = genai.embed_content(
                model="models/embedding-001",
                content="This is a test for embedding generation"
            )
            print(f"✅ Gemini embedding successful! Dimension: {len(result['embedding'])}")
            print(f"Sample values: {result['embedding'][:5]}...")
            
        except Exception as e:
            print(f"❌ Gemini embedding test failed: {e}")
            print(f"Error type: {type(e)}")
    else:
        print("❌ No valid Gemini API key configured")
    
    # Test the embedding engine initialization specifically
    print("\n🔍 Testing Embedding Engine Initialization...")
    from src.search.embedding_engine import EmbeddingGenerator, GEMINI_AVAILABLE
    
    print(f"GEMINI_AVAILABLE: {GEMINI_AVAILABLE}")
    print(f"Config use_openai_embeddings: {config.use_openai_embeddings}")
    print(f"Config use_gemini_fallback: {config.use_gemini_fallback}")
    
    # Force Gemini-only initialization
    print("\n🔧 Testing forced Gemini initialization...")
    embedding_gen = EmbeddingGenerator()
    embedding_gen._setup_gemini_embeddings()
    print(f"Embedding type after Gemini setup: {embedding_gen.embedding_type}")
    
    if embedding_gen.embedding_type == "gemini":
        # Test actual embedding generation
        print("🧪 Testing embedding generation through engine...")
        try:
            test_embedding = embedding_gen._generate_embedding("test text")
            if test_embedding is not None:
                print(f"✅ Generated embedding with shape: {test_embedding.shape}")
            else:
                print("❌ Failed to generate embedding - returned None")
        except Exception as e:
            print(f"❌ Exception during embedding generation: {e}")
            import traceback
            traceback.print_exc()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
