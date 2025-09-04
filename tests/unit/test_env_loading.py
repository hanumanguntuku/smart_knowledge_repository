"""
Test if .env file is being loaded correctly
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_env_loading():
    """Test if .env file is loaded"""
    print("🔍 Testing .env File Loading")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = project_root / ".env"
    print(f"Looking for .env file at: {env_file}")
    
    if env_file.exists():
        print("✅ .env file found")
        
        # Read .env file content
        with open(env_file, 'r') as f:
            content = f.read()
        
        print(f"✅ .env file content ({len(content)} characters):")
        print("-" * 30)
        # Mask sensitive values
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                if 'OPENAI_API_KEY' in line:
                    key, value = line.split('=', 1)
                    if value and len(value) > 8:
                        print(f"{key}={value[:8]}...{value[-4:]}")
                    else:
                        print(f"{key}={value}")
                else:
                    print(line)
            elif line.strip():
                print(line)
        print("-" * 30)
    else:
        print("❌ .env file not found")
        return False
    
    # Test config loading
    print("\n🔧 Testing Configuration Loading")
    print("=" * 50)
    
    try:
        from src.core.config import config
        
        print(f"OpenAI API Key: {'✅ Set' if config.openai_api_key else '❌ Not set'}")
        if config.openai_api_key:
            print(f"API Key (masked): {config.openai_api_key[:8]}...{config.openai_api_key[-4:]}")
        
        print(f"Use OpenAI: {config.use_openai}")
        print(f"OpenAI Model: {config.openai_model}")
        print(f"Max Tokens: {config.max_tokens}")
        print(f"Temperature: {config.temperature}")
        
        return bool(config.openai_api_key)
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

def test_openai_with_config():
    """Test OpenAI with loaded configuration"""
    print("\n🤖 Testing OpenAI with Loaded Config")
    print("=" * 50)
    
    try:
        from src.core.config import config
        
        if not config.openai_api_key:
            print("❌ No OpenAI API key in config")
            return False
        
        if not config.use_openai:
            print("⚠️ USE_OPENAI is set to False")
            print("💡 Set USE_OPENAI=true in your .env file to enable OpenAI")
            return False
        
        # Test OpenAI import and client
        import openai
        
        client = openai.OpenAI(api_key=config.openai_api_key)
        
        print("Making test API call...")
        response = client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {"role": "user", "content": "Respond with exactly: 'Configuration test successful'"}
            ],
            max_tokens=10,
            temperature=0
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            print(f"✅ OpenAI API call successful!")
            print(f"Response: {content}")
            print(f"Model: {response.model}")
            return True
        else:
            print("❌ Empty response from OpenAI")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        return False

def main():
    print("🚀 .env Configuration Test")
    print("=" * 50)
    
    # Test .env loading
    env_loaded = test_env_loading()
    
    if env_loaded:
        # Test OpenAI
        openai_works = test_openai_with_config()
        
        if openai_works:
            print("\n🎉 Everything is working correctly!")
            print("Your .env file is loaded and OpenAI is configured properly.")
        else:
            print("\n⚠️ .env file loads but OpenAI has issues.")
    else:
        print("\n❌ .env file is not loading properly.")
        print("💡 Make sure you have a .env file in the project root with:")
        print("OPENAI_API_KEY=your_actual_api_key")
        print("USE_OPENAI=true")

if __name__ == "__main__":
    main()
