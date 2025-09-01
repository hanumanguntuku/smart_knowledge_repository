"""
Test OpenAI integration and LLM functionality
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config

def test_openai_configuration():
    """Test OpenAI configuration"""
    print("🔧 Testing OpenAI Configuration")
    print("=" * 50)
    
    print(f"OpenAI API Key Set: {'✅' if config.openai_api_key else '❌'}")
    if config.openai_api_key:
        print(f"API Key (masked): {config.openai_api_key[:8]}...{config.openai_api_key[-4:]}")
    else:
        print("❌ No OpenAI API key found!")
        
    print(f"OpenAI Model: {config.openai_model}")
    print(f"Use OpenAI: {config.use_openai}")
    print(f"Max Tokens: {config.max_tokens}")
    print(f"Temperature: {config.temperature}")
    
    return bool(config.openai_api_key)

def test_openai_import():
    """Test if OpenAI package is available and working"""
    print("\n📦 Testing OpenAI Package")
    print("=" * 50)
    
    try:
        import openai
        print("✅ OpenAI package imported successfully")
        print(f"OpenAI version: {openai.__version__}")
        
        # Test client initialization
        if config.openai_api_key:
            try:
                client = openai.OpenAI(api_key=config.openai_api_key)
                print("✅ OpenAI client initialized successfully")
                return client
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {e}")
                return None
        else:
            print("❌ No API key available for client initialization")
            return None
            
    except ImportError as e:
        print(f"❌ OpenAI package not available: {e}")
        return None

def test_openai_api_call(client):
    """Test actual OpenAI API call"""
    print("\n🌐 Testing OpenAI API Call")
    print("=" * 50)
    
    if not client:
        print("❌ No OpenAI client available")
        return False
        
    try:
        # Test simple completion
        print("Making test API call...")
        
        response = client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond with exactly 'API test successful' if you receive this message."},
                {"role": "user", "content": "This is a test message to verify the API connection."}
            ],
            max_tokens=20,
            temperature=0.1
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            print(f"✅ API call successful!")
            print(f"Response: {content}")
            print(f"Model used: {response.model}")
            print(f"Tokens used: {response.usage.total_tokens if response.usage else 'Unknown'}")
            return True
        else:
            print("❌ API call returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check for common API issues
        if "authentication" in str(e).lower():
            print("💡 Possible issue: Invalid API key")
        elif "rate" in str(e).lower():
            print("💡 Possible issue: Rate limit exceeded")
        elif "model" in str(e).lower():
            print("💡 Possible issue: Model not available or incorrect model name")
        elif "quota" in str(e).lower():
            print("💡 Possible issue: API quota exceeded")
            
        return False

def test_chatbot_integration():
    """Test the chatbot with OpenAI integration"""
    print("\n🤖 Testing Chatbot Integration")
    print("=" * 50)
    
    try:
        from src.ai.scope_chatbot import ScopeAwareChatbot
        from src.storage.storage_manager import StorageManager
        from src.search.search_engine import SearchEngine
        
        # Initialize components
        storage_manager = StorageManager()
        search_engine = SearchEngine()
        
        # Initialize chatbot
        chatbot = ScopeAwareChatbot(storage_manager, search_engine)
        print("✅ Chatbot initialized successfully")
        
        # Test chatbot response
        test_query = "What is artificial intelligence?"
        print(f"Testing query: '{test_query}'")
        
        response = chatbot.get_response(test_query)
        print(f"✅ Chatbot response received:")
        print(f"Response: {response[:200]}..." if len(response) > 200 else response)
        
        return True
        
    except Exception as e:
        print(f"❌ Chatbot test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test if environment variables are set correctly"""
    print("\n🌍 Testing Environment Variables")
    print("=" * 50)
    
    env_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'USE_OPENAI': os.getenv('USE_OPENAI'),
        'OPENAI_MODEL': os.getenv('OPENAI_MODEL')
    }
    
    for var, value in env_vars.items():
        if value:
            if var == 'OPENAI_API_KEY':
                print(f"{var}: {value[:8]}...{value[-4:]} ✅")
            else:
                print(f"{var}: {value} ✅")
        else:
            print(f"{var}: Not set ❌")
    
    # Check if we should set USE_OPENAI to true
    if config.openai_api_key and not config.use_openai:
        print("\n💡 Suggestion: You have an API key but USE_OPENAI is False")
        print("   Consider setting USE_OPENAI=true in your environment")

def main():
    """Run all OpenAI tests"""
    print("🚀 OpenAI Integration Test Suite")
    print("=" * 50)
    
    # Test configuration
    has_api_key = test_openai_configuration()
    
    # Test environment variables
    test_environment_variables()
    
    # Test OpenAI package
    client = test_openai_import()
    
    if has_api_key and client:
        # Test API call
        api_success = test_openai_api_call(client)
        
        if api_success:
            # Test chatbot integration
            chatbot_success = test_chatbot_integration()
            
            if chatbot_success:
                print("\n🎉 All tests passed! OpenAI integration is working correctly.")
            else:
                print("\n⚠️ API works but chatbot integration has issues.")
        else:
            print("\n❌ API call failed. Check your API key and network connection.")
    else:
        print("\n❌ Cannot test API without valid configuration.")
        
    print("\n📋 Summary:")
    print(f"  - API Key: {'✅' if has_api_key else '❌'}")
    print(f"  - OpenAI Package: {'✅' if client else '❌'}")
    if has_api_key and client:
        print(f"  - API Call: Testing required")
        print(f"  - Chatbot: Testing required")

if __name__ == "__main__":
    main()
