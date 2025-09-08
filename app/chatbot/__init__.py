"""
Chatbot Core Module

Contains the main chatbot logic, OpenAI integration, and utility functions
for processing customer support conversations.
"""

from .core import CustomerSupportChatbot
from .openai_client import OpenAIClient
from .utils import (
    classify_intent,
    extract_entities,
    should_escalate,
    sanitize_message,
    format_response
)

__all__ = [
    "CustomerSupportChatbot",
    "OpenAIClient", 
    "classify_intent",
    "extract_entities",
    "should_escalate",
    "sanitize_message",
    "format_response"
]