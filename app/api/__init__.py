"""
API Module

Contains REST API routes and WebSocket endpoints for the chatbot application.
Provides endpoints for chat functionality, analytics, and system management.
"""

from .routes import router as api_router
from .websocket import router as websocket_router

__all__ = [
    "api_router",
    "websocket_router"
]