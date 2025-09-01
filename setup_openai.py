"""
Setup script to configure OpenAI API key and test integration
"""
import os
import sys
from pathlib import Path

def setup_openai_config():
    """Interactive setup for OpenAI configuration"""
    print("🔧 OpenAI Configuration Setup")
    print("=" * 50)
    
    print("To use the AI chatbot, you need an OpenAI API key.")
    print("You can get one from: https://platform.openai.com/api-keys")
    print()
    
    # Check if user wants to set up API key
    setup_choice = input("Do you want to set up your OpenAI API key now? (y/n): ").lower().strip()
    
    if setup_choice != 'y':
        print("Setup cancelled. You can set up the API key later.")
        return False
    
    # Get API key from user
    api_key = input("\nEnter your OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Setup cancelled.")
        return False
    
    if not api_key.startswith("sk-"):
        print("⚠️ Warning: OpenAI API keys typically start with 'sk-'")
        continue_choice = input("Continue anyway? (y/n): ").lower().strip()
        if continue_choice != 'y':
            return False
    
    # Create .env file
    env_file = Path.cwd() / ".env"
    
    env_content = f"""# OpenAI Configuration
OPENAI_API_KEY={api_key}
USE_OPENAI=true
OPENAI_MODEL=gpt-4o-mini

# Other settings
DEBUG=false
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Configuration saved to {env_file}")
        print("\n📋 To use the configuration:")
        print("1. Restart your application")
        print("2. Or load the .env file in your code")
        
        # Set environment variables for current session
        os.environ['OPENAI_API_KEY'] = api_key
        os.environ['USE_OPENAI'] = 'true'
        os.environ['OPENAI_MODEL'] = 'gpt-4o-mini'
        
        print("✅ Environment variables set for current session")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False

def test_api_key_manually():
    """Test API key with a simple call"""
    print("\n🧪 Testing API Key")
    print("=" * 30)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found in environment")
        return False
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        
        print("Making test API call...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'Hello, API test successful!' and nothing else."}
            ],
            max_tokens=20,
            temperature=0
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            print(f"✅ API Test Successful!")
            print(f"Response: {content}")
            return True
        else:
            print("❌ Empty response from API")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        
        # Provide specific error guidance
        error_str = str(e).lower()
        if "authentication" in error_str or "unauthorized" in error_str:
            print("💡 Issue: Invalid API key")
            print("   - Check if your API key is correct")
            print("   - Ensure your OpenAI account has credits")
        elif "rate" in error_str:
            print("💡 Issue: Rate limit exceeded")
            print("   - Wait a moment and try again")
        elif "quota" in error_str or "billing" in error_str:
            print("💡 Issue: Account/billing problem")
            print("   - Check your OpenAI account billing status")
        elif "model" in error_str:
            print("💡 Issue: Model access problem")
            print("   - Try using 'gpt-3.5-turbo' instead")
        
        return False

def create_env_template():
    """Create a template .env file"""
    env_template = Path.cwd() / ".env.template"
    
    template_content = """# Smart Knowledge Repository Configuration Template
# Copy this to .env and fill in your values

# OpenAI Configuration (for AI chatbot)
OPENAI_API_KEY=your_openai_api_key_here
USE_OPENAI=true
OPENAI_MODEL=gpt-4o-mini

# Application Settings
DEBUG=false
APP_NAME=Smart Knowledge Repository

# Database Settings
SQLITE_DB_PATH=data/knowledge.db
CHROMA_PERSIST_DIR=data/chroma_db

# Search Settings
MAX_RESULTS=10
SIMILARITY_THRESHOLD=0.7

# Embedding Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
"""
    
    try:
        with open(env_template, 'w') as f:
            f.write(template_content)
        print(f"✅ Template created: {env_template}")
    except Exception as e:
        print(f"❌ Failed to create template: {e}")

def main():
    print("🚀 OpenAI Setup and Test Tool")
    print("=" * 50)
    
    # Check current status
    current_key = os.getenv('OPENAI_API_KEY')
    if current_key:
        print(f"Current API key found: {current_key[:8]}...{current_key[-4:]}")
        test_choice = input("Test current API key? (y/n): ").lower().strip()
        if test_choice == 'y':
            if test_api_key_manually():
                print("🎉 Your API key is working!")
                return
            else:
                print("❌ Current API key is not working")
    
    # Setup new configuration
    if setup_openai_config():
        # Test the new configuration
        test_api_key_manually()
    
    # Create template for future reference
    create_env_template()
    
    print("\n📖 Next Steps:")
    print("1. Make sure your .env file is in the project root")
    print("2. Restart your Streamlit application")
    print("3. Try asking the AI chatbot a question")

if __name__ == "__main__":
    main()
