#!/usr/bin/env python3
"""
Smart Knowledge Repository - Setup Script
Automated setup and installation helper
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"📋 {description}")
    print(f"💻 Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(f"📤 Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"📤 Error details: {e.stderr.strip()}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"📤 Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version OK: {version.major}.{version.minor}.{version.micro}")
    return True


def create_virtual_environment():
    """Create and activate virtual environment"""
    print("\n🔧 Setting up virtual environment...")
    
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    # Activation command depends on OS
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    print(f"📋 To activate virtual environment, run: {activate_cmd}")
    return pip_cmd


def install_minimal_dependencies(pip_cmd):
    """Install minimal dependencies for basic functionality"""
    print("\n📦 Installing minimal dependencies...")
    
    minimal_packages = [
        "streamlit",
    ]
    
    for package in minimal_packages:
        if not run_command(f"{pip_cmd} install {package}", f"Installing {package}"):
            print(f"⚠️ Failed to install {package}, continuing...")
    
    return True


def install_optional_dependencies(pip_cmd):
    """Install optional dependencies for enhanced features"""
    print("\n📦 Installing optional dependencies...")
    
    optional_packages = {
        "Web Scraping": ["aiohttp", "beautifulsoup4", "lxml"],
        "AI Features": ["sentence-transformers", "transformers"],
        "Analytics": ["plotly", "pandas", "numpy"],
        "Language Detection": ["langdetect"],
        "Data Validation": ["pydantic", "pydantic-settings"],
    }
    
    for category, packages in optional_packages.items():
        print(f"\n🔧 {category}:")
        for package in packages:
            if not run_command(f"{pip_cmd} install {package}", f"Installing {package}"):
                print(f"⚠️ Failed to install {package}, feature may be limited")


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "data",
        "data/backups",
        "data/embeddings",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")


def create_env_file():
    """Create example .env file"""
    print("\n⚙️ Creating example configuration file...")
    
    env_content = """# Smart Knowledge Repository Configuration
# Copy this to .env and customize as needed

# Database settings
SQLITE_DB_PATH=data/knowledge.db
VECTOR_DB_PATH=data/embeddings/
BACKUP_PATH=data/backups/

# AI/ML settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DIMENSION=384
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Search settings
MAX_RESULTS=10
SIMILARITY_THRESHOLD=0.7
SEARCH_TIMEOUT=30

# Web scraping settings
MAX_CRAWL_DEPTH=3
CRAWL_DELAY=1.0
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30

# Security settings
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# UI settings
STREAMLIT_PORT=8501
DEBUG=false

# Feature toggles
ENABLE_CONTENT_VALIDATION=true
ENABLE_ANALYTICS=true
MAX_FILE_SIZE_MB=100
ANALYTICS_RETENTION_DAYS=90
"""
    
    with open(".env.example", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env.example")
    print("📋 Copy to .env and customize: cp .env.example .env")


def test_installation():
    """Test if the installation works"""
    print("\n🧪 Testing installation...")
    
    if not run_command("python main.py", "Testing system initialization"):
        print("❌ System test failed!")
        return False
    
    print("✅ System test passed!")
    return True


def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Activate virtual environment:")
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("\n2. Start the application:")
    print("   python main.py")
    print("\n3. Launch web interface:")
    print("   streamlit run src/ui/streamlit_app.py")
    print("\n4. Open browser to: http://localhost:8501")
    
    print("\n📖 For more information, see INSTALL_NEW.md")


def main():
    """Main setup function"""
    print("🧠 Smart Knowledge Repository - Setup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    pip_cmd = create_virtual_environment()
    if not pip_cmd:
        print("❌ Failed to create virtual environment!")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create configuration file
    create_env_file()
    
    # Ask user about installation type
    print("\n🤔 Choose installation type:")
    print("1. Minimal (basic functionality, no external dependencies)")
    print("2. Full (all features, requires internet connection)")
    
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice in ["1", "2"]:
            break
        print("Please enter 1 or 2")
    
    # Install dependencies
    install_minimal_dependencies(pip_cmd)
    
    if choice == "2":
        install_optional_dependencies(pip_cmd)
    
    # Test installation
    test_installation()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
