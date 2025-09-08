"""
Main FastAPI application for Customer Support Chatbot
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.routes import router as api_router
from app.api.websocket import router as websocket_router
from app.models.database import init_database
from app.config.settings import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Customer Support Chatbot...")
    init_database()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Customer Support Chatbot...")

# Create FastAPI app
app = FastAPI(
    title="Customer Support Chatbot",
    description="Generative AI-powered customer support chatbot with business insights",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(websocket_router)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main chat interface"""
    static_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    
    if os.path.exists(static_path):
        with open(static_path, "r") as f:
            return HTMLResponse(content=f.read())
    
    # Fallback HTML if static file doesn't exist
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Customer Support Chatbot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin-bottom: 10px; background: #fafafa; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user-message { background: #007bff; color: white; text-align: right; }
            .bot-message { background: #e9ecef; color: #333; }
            .input-container { display: flex; gap: 10px; }
            #messageInput { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            #sendButton { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            #sendButton:hover { background: #0056b3; }
            .typing { font-style: italic; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Customer Support Chatbot</h1>
            <div id="chatContainer" class="chat-container">
                <div class="message bot-message">
                    Hello! I'm your AI customer support assistant. How can I help you today?
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="Type your message..." />
                <button id="sendButton">Send</button>
            </div>
        </div>

        <script>
            const chatContainer = document.getElementById('chatContainer');
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');

            let userId = 'user_' + Math.random().toString(36).substr(2, 9);

            function addMessage(message, isUser = false) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
                messageDiv.textContent = message;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            function showTyping() {
                const typingDiv = document.createElement('div');
                typingDiv.className = 'message bot-message typing';
                typingDiv.textContent = 'Bot is typing...';
                typingDiv.id = 'typing';
                chatContainer.appendChild(typingDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            function hideTyping() {
                const typingDiv = document.getElementById('typing');
                if (typingDiv) {
                    typingDiv.remove();
                }
            }

            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;

                addMessage(message, true);
                messageInput.value = '';
                showTyping();

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            user_id: userId
                        })
                    });

                    const data = await response.json();
                    hideTyping();
                    
                    if (response.ok) {
                        addMessage(data.response);
                    } else {
                        addMessage('Sorry, I encountered an error. Please try again.');
                    }
                } catch (error) {
                    hideTyping();
                    addMessage('Connection error. Please check your internet connection.');
                }
            }

            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Focus on input
            messageInput.focus();
        </script>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "customer-support-chatbot",
        "version": "1.0.0"
    }

@app.get("/health/db")
async def db_health_check():
    """Database health check"""
    try:
        from app.models.database import test_connection
        await test_connection()
        return {"database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="info"
    )