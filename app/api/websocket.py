"""
WebSocket endpoint for real-time chat functionality
"""

import json
import logging
from typing import Dict, List
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.chatbot.core import CustomerSupportChatbot

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chatbot = CustomerSupportChatbot()
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user: {user_id}")
        
        # Send welcome message
        welcome_message = {
            "type": "system",
            "message": "Connected to customer support chat. How can I help you today?",
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        await self.send_personal_message(welcome_message, user_id)
    
    def disconnect(self, user_id: str):
        """Remove connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user: {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")
                    self.disconnect(user_id)
    
    async def handle_message(self, message_data: dict, user_id: str):
        """Process incoming message and generate response"""
        try:
            user_message = message_data.get("message", "")
            
            if not user_message.strip():
                return
            
            # Send typing indicator
            typing_message = {
                "type": "typing",
                "message": "Bot is typing...",
                "timestamp": datetime.now().isoformat()
            }
            await self.send_personal_message(typing_message, user_id)
            
            # Process message with chatbot
            response_data = await self.chatbot.process_message(
                message=user_message,
                user_id=user_id
            )
            
            # Send bot response
            bot_message = {
                "type": "bot",
                "message": response_data["response"],
                "timestamp": response_data["timestamp"],
                "intent": response_data["intent"],
                "response_time": response_data["response_time"],
                "escalated": response_data["escalated"]
            }
            
            await self.send_personal_message(bot_message, user_id)
            
            # If escalated, send additional info
            if response_data["escalated"]:
                escalation_info = {
                    "type": "escalation",
                    "message": "This conversation has been flagged for human agent review.",
                    "timestamp": datetime.now().isoformat(),
                    "support_info": {
                        "email": "support@yourcompany.com",
                        "phone": "1-800-123-4567"
                    }
                }
                await self.send_personal_message(escalation_info, user_id)
            
        except Exception as e:
            logger.error(f"Error handling message from {user_id}: {e}")
            
            error_message = {
                "type": "error",
                "message": "I'm having trouble processing your message. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
            await self.send_personal_message(error_message, user_id)
    
    def get_active_connections_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    async def broadcast_system_message(self, message: str):
        """Send system message to all connected users"""
        system_message = {
            "type": "system",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected_users = []
        
        for user_id, websocket in self.active_connections.items():
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(system_message))
                else:
                    disconnected_users.append(user_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)

# Global connection manager instance
manager = ConnectionManager()

@router.websocket("/ws/chat/{user_id}")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat
    
    Args:
        websocket: WebSocket connection
        user_id: Unique identifier for the user
    """
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Wait for message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                # Handle plain text messages
                message_data = {"message": data, "type": "text"}
            
            # Log received message (without sensitive data)
            from app.chatbot.utils import mask_sensitive_data
            masked_message = mask_sensitive_data(message_data.get("message", ""))
            logger.info(f"Received message from {user_id}: {masked_message[:100]}...")
            
            # Handle different message types
            message_type = message_data.get("type", "chat")
            
            if message_type == "chat":
                await manager.handle_message(message_data, user_id)
            
            elif message_type == "typing":
                # Handle typing indicators (optional feature)
                pass
            
            elif message_type == "ping":
                # Handle ping for connection keep-alive
                pong_message = {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(pong_message, user_id)
            
            elif message_type == "feedback":
                # Handle user feedback
                rating = message_data.get("rating")
                feedback_text = message_data.get("feedback", "")
                
                # Log feedback (in production, store in database)
                logger.info(f"Feedback from {user_id}: rating={rating}, text={feedback_text[:50]}...")
                
                thanks_message = {
                    "type": "system",
                    "message": "Thank you for your feedback! It helps us improve our service.",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(thanks_message, user_id)
            
            elif message_type == "get_history":
                # Send conversation history
                history = manager.chatbot.get_conversation_history(user_id)
                
                history_message = {
                    "type": "history",
                    "data": history,
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(history_message, user_id)
            
            elif message_type == "clear_history":
                # Clear conversation history
                success = manager.chatbot.clear_conversation_history(user_id)
                
                clear_message = {
                    "type": "system",
                    "message": "Conversation history cleared." if success else "No history to clear.",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(clear_message, user_id)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}")
        manager.disconnect(user_id)
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)

@router.websocket("/ws/admin")
async def websocket_admin_endpoint(websocket: WebSocket):
    """
    Admin WebSocket endpoint for monitoring and management
    """
    
    # In production, add authentication here
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            command = message_data.get("command")
            
            if command == "get_stats":
                # Send current statistics
                stats = {
                    "type": "stats",
                    "data": {
                        "active_connections": manager.get_active_connections_count(),
                        "total_users": len(manager.chatbot.conversation_memory),
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await websocket.send_text(json.dumps(stats))
            
            elif command == "broadcast":
                # Broadcast message to all users
                message = message_data.get("message", "")
                if message:
                    await manager.broadcast_system_message(message)
                    
                    confirm = {
                        "type": "confirmation",
                        "message": f"Broadcasted to {manager.get_active_connections_count()} users",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(confirm))
    
    except WebSocketDisconnect:
        logger.info("Admin WebSocket disconnected")
    
    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")

# Health check endpoint for WebSocket service
@router.get("/ws/health")
async def websocket_health():
    """Health check for WebSocket service"""
    return {
        "status": "healthy",
        "active_connections": manager.get_active_connections_count(),
        "timestamp": datetime.now().isoformat()
    }