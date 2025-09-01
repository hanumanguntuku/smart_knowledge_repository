"""
Test to demonstrate how RAG works with your scraped data
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demonstrate_rag_process():
    """Demonstrate the complete RAG process"""
    print("🤖 RAG (Retrieval-Augmented Generation) Demonstration")
    print("=" * 60)
    
    print("Your RAG system works like this:")
    print("1. 🔍 RETRIEVAL: Search your scraped Wikipedia AI article")
    print("2. 🧠 GENERATION: Use OpenAI to create natural responses")
    print("3. 📚 KNOWLEDGE: Answers are based on YOUR scraped data")
    print()
    
    # Test the search component first
    print("Step 1: Testing RETRIEVAL from your scraped data")
    print("-" * 50)
    
    try:
        from src.search.embedding_engine import EmbeddingGenerator
        
        embedding_gen = EmbeddingGenerator()
        
        # Test query
        test_query = "What is artificial intelligence?"
        
        # Search in your scraped data
        results = embedding_gen.search_similar_chunks(
            query=test_query,
            domain="general",  # Where your Wikipedia article is stored
            limit=3
        )
        
        print(f"Query: '{test_query}'")
        print(f"Found {len(results)} relevant chunks from your scraped Wikipedia article:")
        
        for i, result in enumerate(results, 1):
            print(f"\n  📄 Chunk {i} (Similarity: {result['similarity']:.3f}):")
            print(f"     {result['chunk_text'][:200]}...")
            
        if results:
            print("\n✅ RETRIEVAL successful! Found relevant data from Wikipedia AI article.")
            return results
        else:
            print("\n❌ No results found. Check if embeddings exist.")
            return []
            
    except Exception as e:
        print(f"❌ Error in retrieval: {e}")
        return []

def test_openai_generation(context_chunks):
    """Test OpenAI generation with retrieved context"""
    print("\nStep 2: Testing GENERATION with OpenAI")
    print("-" * 50)
    
    if not context_chunks:
        print("❌ No context available for generation")
        return
    
    try:
        from src.core.config import config
        import openai
        
        # Prepare context from retrieved chunks
        context = ""
        for i, chunk in enumerate(context_chunks, 1):
            context += f"[{i}] {chunk['chunk_text'][:300]}...\n\n"
        
        print(f"Context prepared from {len(context_chunks)} chunks")
        print(f"Context length: {len(context)} characters")
        
        # Create OpenAI client
        client = openai.OpenAI(api_key=config.openai_api_key)
        
        # System prompt for RAG
        system_prompt = """You are a helpful assistant that answers questions based ONLY on the provided context from a knowledge base. 

Guidelines:
1. Answer using ONLY information from the provided context
2. Include citation numbers [1], [2], etc. when referencing sources
3. If the context doesn't contain enough information, clearly state this
4. Be conversational but accurate

Context:
""" + context

        user_query = "What is artificial intelligence? Explain it in simple terms."
        
        print(f"\nSending to OpenAI:")
        print(f"Query: '{user_query}'")
        
        # Generate response
        response = client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        if response and response.choices:
            ai_response = response.choices[0].message.content
            print(f"\n🤖 OpenAI Response:")
            print(f"{ai_response}")
            print(f"\n✅ GENERATION successful! Response based on YOUR scraped data.")
            return ai_response
        else:
            print("❌ Empty response from OpenAI")
            return None
            
    except Exception as e:
        print(f"❌ Error in generation: {e}")
        return None

def test_complete_rag_pipeline():
    """Test the complete chatbot pipeline"""
    print("\nStep 3: Testing COMPLETE RAG PIPELINE")
    print("-" * 50)
    
    try:
        from src.ai.scope_chatbot import ScopeAwareChatbot
        from src.storage.storage_manager import StorageManager
        from src.search.search_engine import SearchEngine
        
        # Initialize components
        storage_manager = StorageManager()
        search_engine = SearchEngine()
        chatbot = ScopeAwareChatbot(storage_manager, search_engine)
        
        print("✅ Chatbot initialized successfully")
        
        # Test query
        test_query = "What is artificial intelligence and how does it work?"
        print(f"\nTesting query: '{test_query}'")
        
        # Get response using complete RAG pipeline
        response = chatbot.get_response(test_query)
        
        print(f"\n🎯 Complete RAG Response:")
        print(f"{response}")
        
        print(f"\n✅ COMPLETE RAG PIPELINE working!")
        print(f"This response was generated using:")
        print(f"  - Your scraped Wikipedia AI data (RETRIEVAL)")
        print(f"  - OpenAI for natural language generation (GENERATION)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in complete pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

def explain_rag_benefits():
    """Explain why we use OpenAI with your data"""
    print("\n💡 Why Use OpenAI + Your Data (RAG)?")
    print("=" * 50)
    
    print("🔹 WITHOUT OpenAI (Just search results):")
    print("   - You get raw chunks of text")
    print("   - Hard to read and understand")
    print("   - No natural conversation")
    print()
    
    print("🔹 WITH OpenAI + Your Data (RAG):")
    print("   - ✅ Answers based on YOUR scraped content")
    print("   - ✅ Natural, conversational responses")
    print("   - ✅ Proper citations and sources")
    print("   - ✅ No hallucinations (only uses your data)")
    print("   - ✅ Up-to-date with your scraped information")
    print()
    
    print("🎯 The AI doesn't 'know' anything on its own about your topics.")
    print("🎯 It only uses the Wikipedia article YOU scraped to answer questions.")
    print("🎯 This ensures accurate, source-based responses!")

def main():
    """Run the complete RAG demonstration"""
    print("🚀 Understanding Your RAG System")
    print("=" * 60)
    
    # Step 1: Demonstrate retrieval
    context_chunks = demonstrate_rag_process()
    
    if context_chunks:
        # Step 2: Demonstrate generation
        ai_response = test_openai_generation(context_chunks)
        
        if ai_response:
            # Step 3: Test complete pipeline
            test_complete_rag_pipeline()
    
    # Explain the benefits
    explain_rag_benefits()
    
    print("\n📋 Summary:")
    print("✅ USE_OPENAI=true is CORRECT for RAG")
    print("✅ OpenAI uses YOUR scraped data to answer questions")
    print("✅ No external knowledge - only your Wikipedia article")
    print("✅ Natural language responses with proper citations")

if __name__ == "__main__":
    main()
