"""
Database Models Module

Contains database models and schemas for storing conversation data,
user interactions, and analytics information.
"""

from .database import (
    init_database,
    get_database,
    test_connection,
    Conversation,
    Message,
    UserFeedback,
    AnalyticsEvent
)
from .schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    FeedbackCreate,
    FeedbackResponse,
    AnalyticsEventCreate
)

__all__ = [
    # Database functions
    "init_database",
    "get_database", 
    "test_connection",
    
    # Database models
    "Conversation",
    "Message", 
    "UserFeedback",
    "AnalyticsEvent",
    
    # Pydantic schemas
    "ConversationCreate",
    "ConversationResponse",
    "MessageCreate",
    "MessageResponse", 
    "FeedbackCreate",
    "FeedbackResponse",
    "AnalyticsEventCreate"
]