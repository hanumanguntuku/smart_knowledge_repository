"""
Debug semantic search scores
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def debug_semantic_scores():
    """Debug why semantic search scores are 0"""
    print("🔍 Debugging Semantic Search Scores")
    print("=" * 50)
    
    try:
        from src.search.search_engine import SearchEngine
        from src.search.embedding_engine import EmbeddingGenerator
        from src.search.chroma_client import ChromaDBClient, chroma_client
        
        # Test each component separately
        query = "What is artificial intelligence?"
        
        # 1. Test ChromaDB directly
        print("1. Testing ChromaDB directly:")
        if chroma_client.is_available():
            print("   ChromaDB available: ✅")
            # Test a collection
            try:
                collection = chroma_client.get_collection("general")
                print(f"   General collection exists: ✅")
                
                # Query the collection directly
                results = collection.query(
                    query_texts=[query],
                    n_results=3
                )
                print(f"   Raw ChromaDB results: {len(results.get('ids', [[]])[0])} documents")
                if results.get('distances'):
                    distances = results['distances'][0]
                    print(f"   Raw distances: {distances}")
                    # Convert distances to similarity scores (1 - distance for cosine similarity)
                    similarities = [1 - d for d in distances]
                    print(f"   Converted similarities: {similarities}")
                    
            except Exception as e:
                print(f"   Collection error: {e}")
        else:
            print("   ChromaDB not available: ❌")
        
        # 2. Test EmbeddingGenerator
        print("\n2. Testing EmbeddingGenerator:")
        embedding_gen = EmbeddingGenerator()
        
        try:
            similar_chunks = embedding_gen.search_similar_chunks(
                query=query,
                domain="general",
                limit=3
            )
            print(f"   EmbeddingGenerator results: {len(similar_chunks)}")
            for i, chunk in enumerate(similar_chunks, 1):
                print(f"     {i}. Similarity: {chunk.get('similarity', 'No similarity')}")
                print(f"        Document ID: {chunk.get('document_id', 'No doc ID')}")
                print(f"        Title: {chunk.get('title', 'No title')}")
        except Exception as e:
            print(f"   EmbeddingGenerator error: {e}")
        
        # 3. Test SearchEngine
        print("\n3. Testing SearchEngine:")
        search_engine = SearchEngine()
        
        # Test semantic search
        semantic_results = search_engine.search(
            query=query,
            search_type="semantic",
            max_results=3
        )
        print(f"   SearchEngine semantic results: {len(semantic_results)}")
        for i, result in enumerate(semantic_results, 1):
            print(f"     {i}. Title: {result.get('title', 'No title')}")
            print(f"        Semantic score: {result.get('semantic_score', 'No semantic score')}")
            print(f"        Score: {result.get('score', 'No score')}")
            print(f"        Final score: {result.get('final_score', 'No final score')}")
            print(f"        Relevance score: {result.get('relevance_score', 'No relevance score')}")
            print(f"        Similarity score: {result.get('similarity_score', 'No similarity score')}")
        
        # 4. Test hybrid search  
        print("\n4. Testing SearchEngine hybrid search:")
        hybrid_results = search_engine.search(
            query=query,
            search_type="hybrid",
            max_results=3
        )
        print(f"   SearchEngine hybrid results: {len(hybrid_results)}")
        for i, result in enumerate(hybrid_results, 1):
            print(f"     {i}. Title: {result.get('title', 'No title')}")
            print(f"        Final score: {result.get('final_score', 'No final score')}")
            print(f"        All scores: {[(k, v) for k, v in result.items() if 'score' in k.lower()]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    debug_semantic_scores()

if __name__ == "__main__":
    main()
