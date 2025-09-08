#!/usr/bin/env python3
"""
Quick start script for Customer Support Chatbot
This script sets up the environment and starts the application
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def create_env_file():
    """Create .env file if it doesn't exist"""
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        print("📝 Creating .env file...")
        
        if env_example_path.exists():
            # Copy from example
            with open(env_example_path, 'r') as f:
                content = f.read()
        else:
            # Create basic .env content
            content = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
MAX_TOKENS=500
TEMPERATURE=0.7

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
DATABASE_URL=sqlite:///./chatbot.db

# Chatbot Settings
MAX_CONTEXT_MESSAGES=10
ENABLE_ANALYTICS=True

# Business Information
COMPANY_NAME=Your Company
SUPPORT_EMAIL=support@yourcompany.com
SUPPORT_PHONE=1-800-123-4567
"""
        
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("✅ .env file created")
        print("⚠️  Please update the OPENAI_API_KEY in .env file before continuing")
        
        # Check if OpenAI API key is set
        if "your_openai_api_key_here" in content:
            api_key = input("\n🔑 Enter your OpenAI API Key (or press Enter to set it later): ").strip()
            if api_key:
                # Update the .env file
                with open(env_path, 'r') as f:
                    updated_content = f.read().replace("your_openai_api_key_here", api_key)
                
                with open(env_path, 'w') as f:
                    f.write(updated_content)
                
                print("✅ OpenAI API key updated in .env file")

def create_directories():
    """Create necessary directories"""
    
    directories = [
        "data",
        "data/conversation_logs",
        "logs",
        "app/static"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("📁 Created necessary directories")

def create_knowledge_base():
    """Create initial knowledge base"""
    
    kb_path = Path("data/knowledge_base.json")
    
    if not kb_path.exists():
        print("📚 Creating knowledge base...")
        
        knowledge_base = {
            "faqs": [
                {
                    "question": "How do I track my order?",
                    "answer": "You can track your order by logging into your account and viewing the order status, or by using the tracking number sent to your email. If you need help finding your tracking information, I can assist you with that."
                },
                {
                    "question": "What is your return policy?",
                    "answer": "We offer a 30-day return policy for most items. Items must be in original condition with tags attached. Returns are free for defective items, and there's a small restocking fee for other returns. Would you like help starting a return?"
                },
                {
                    "question": "How do I cancel my order?",
                    "answer": "You can cancel your order within 1 hour of placing it by contacting customer service or through your account dashboard. After 1 hour, the order enters processing and cannot be cancelled, but you can return it once received."
                },
                {
                    "question": "How long does shipping take?",
                    "answer": "Standard shipping takes 3-5 business days, expedited shipping takes 1-2 business days, and overnight shipping delivers the next business day. Shipping times may vary during peak seasons."
                },
                {
                    "question": "Do you offer international shipping?",
                    "answer": "Yes, we ship to most countries worldwide. International shipping typically takes 7-14 business days and may be subject to customs fees determined by your country."
                }
            ],
            "escalation_keywords": [
                "speak to human", "human agent", "real person", "manager", 
                "supervisor", "complaint", "frustrated", "angry", "terrible service"
            ],
            "business_info": {
                "company_name": "Your Company",
                "support_hours": "9 AM - 6 PM EST, Monday-Friday",
                "support_email": "support@yourcompany.com",
                "support_phone": "1-800-123-4567",
                "website": "https://yourcompany.com"
            }
        }
        
        with open(kb_path, 'w') as f:
            json.dump(knowledge_base, f, indent=2)
        
        print("✅ Knowledge base created")

def install_dependencies():
    """Install required packages"""
    
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def check_openai_key():
    """Check if OpenAI API key is configured"""
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "your_openai_api_key_here":
        print("\n⚠️  OpenAI API key not configured!")
        print("Please set your OPENAI_API_KEY in the .env file")
        print("You can get an API key from: https://platform.openai.com/api-keys")
        
        choice = input("\nDo you want to enter your API key now? (y/n): ").lower().strip()
        if choice == 'y':
            api_key = input("Enter your OpenAI API Key: ").strip()
            if api_key:
                # Update .env file
                env_path = Path(".env")
                with open(env_path, 'r') as f:
                    content = f.read()
                
                # Replace the API key line
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('OPENAI_API_KEY='):
                        lines[i] = f'OPENAI_API_KEY={api_key}'
                        break
                
                with open(env_path, 'w') as f:
                    f.write('\n'.join(lines))
                
                print("✅ OpenAI API key updated!")
                return True
        
        return False
    
    print("✅ OpenAI API key configured")
    return True

def start_application():
    """Start the FastAPI application"""
    
    print("\n🚀 Starting Customer Support Chatbot...")
    print("📊 The application will be available at: http://localhost:8000")
    print("📚 API documentation will be at: http://localhost:8000/docs")
    print("\n💡 Tips:")
    print("  - Press Ctrl+C to stop the server")
    print("  - Set DEBUG=False in .env for production")
    print("  - Check logs/ directory for application logs")
    print("\n" + "="*50)
    
    try:
        # Import and run the application
        from app.main import app
        import uvicorn
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        host = os.getenv("APP_HOST", "0.0.0.0")
        port = int(os.getenv("APP_PORT", 8000))
        debug = os.getenv("DEBUG", "True").lower() == "true"
        
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Chatbot stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print("Please check your configuration and try again.")

def main():
    """Main setup and run function"""
    
    print("🤖 Customer Support Chatbot - Setup & Run")
    print("="*50)
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   (The directory containing the 'app' folder)")
        sys.exit(1)
    
    # Setup steps
    create_directories()
    create_env_file()
    create_knowledge_base()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed. Please install dependencies manually:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Check OpenAI configuration
    if not check_openai_key():
        print("\n⚠️  Cannot start without OpenAI API key. Please configure it and run again.")
        sys.exit(1)
    
    print("\n✅ Setup completed successfully!")
    
    # Ask if user wants to start the application
    choice = input("\nDo you want to start the application now? (y/n): ").lower().strip()
    if choice == 'y':
        start_application()
    else:
        print("\n📝 To start the application later, run:")
        print("   python run.py")
        print("   or")
        print("   python -m app.main")

if __name__ == "__main__":
    main()