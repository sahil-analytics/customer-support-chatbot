"""
Configuration settings for the customer support chatbot
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    
    # OpenAI settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    max_tokens: int = Field(default=500, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./chatbot.db", env="DATABASE_URL")
    
    # Redis settings (optional)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Chatbot behavior settings
    max_context_messages: int = Field(default=10, env="MAX_CONTEXT_MESSAGES")
    max_response_length: int = Field(default=500, env="MAX_RESPONSE_LENGTH")
    enable_context_memory: bool = Field(default=True, env="ENABLE_CONTEXT_MEMORY")
    
    # Analytics settings
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    analytics_retention_days: int = Field(default=90, env="ANALYTICS_RETENTION_DAYS")
    
    # Business settings
    company_name: str = Field(default="Your Company", env="COMPANY_NAME")
    support_email: str = Field(default="support@yourcompany.com", env="SUPPORT_EMAIL")
    support_phone: str = Field(default="1-800-123-4567", env="SUPPORT_PHONE")
    support_hours: str = Field(default="9 AM - 6 PM EST, Monday-Friday", env="SUPPORT_HOURS")
    
    # Security settings
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Escalation settings
    escalation_keywords: list = Field(
        default=["speak to human", "manager", "complaint", "frustrated", "angry"],
        env="ESCALATION_KEYWORDS"
    )
    auto_escalate_after_messages: int = Field(default=5, env="AUTO_ESCALATE_AFTER_MESSAGES")
    
    # Performance settings
    response_timeout_seconds: int = Field(default=30, env="RESPONSE_TIMEOUT_SECONDS")
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Business hours configuration
BUSINESS_HOURS_CONFIG = {
    "timezone": "UTC",
    "days": {
        "monday": {"start": "09:00", "end": "17:00"},
        "tuesday": {"start": "09:00", "end": "17:00"},
        "wednesday": {"start": "09:00", "end": "17:00"},
        "thursday": {"start": "09:00", "end": "17:00"},
        "friday": {"start": "09:00", "end": "17:00"},
        "saturday": {"start": "10:00", "end": "14:00"},
        "sunday": {"closed": True}
    }
}

# Intent classification mappings
INTENT_MAPPINGS = {
    "order_status": ["track", "order", "shipping", "delivery", "status"],
    "billing": ["bill", "charge", "payment", "invoice", "refund"],
    "returns": ["return", "exchange", "defective", "damaged"],
    "account": ["password", "login", "account", "profile", "settings"],
    "product_info": ["product", "item", "specification", "details", "features"],
    "complaint": ["complaint", "dissatisfied", "problem", "issue", "frustrated"],
    "compliment": ["great", "excellent", "amazing", "satisfied", "happy"],
    "general": ["help", "support", "question", "information"]
}

# Response templates for common scenarios
RESPONSE_TEMPLATES = {
    "greeting": [
        "Hello! I'm here to help you with any questions or concerns. How can I assist you today?",
        "Hi there! Welcome to customer support. What can I help you with?",
        "Greetings! I'm your AI assistant. How may I help you today?"
    ],
    "escalation": [
        "I understand you'd like to speak with a human representative. Let me connect you with our support team.",
        "I'll escalate this to one of our human agents who can provide more specialized assistance.",
        "Let me transfer you to a human agent who can better help with your specific situation."
    ],
    "clarification": [
        "Could you please provide more details about your issue?",
        "I want to make sure I understand correctly. Could you elaborate on that?",
        "To better assist you, could you please provide more information?"
    ],
    "closing": [
        "Is there anything else I can help you with today?",
        "I hope I was able to resolve your concern. Do you have any other questions?",
        "Thank you for contacting support. Is there anything else you need assistance with?"
    ]
}

# Knowledge base categories
KNOWLEDGE_BASE_CATEGORIES = [
    "orders",
    "shipping",
    "billing",
    "returns",
    "products",
    "account",
    "technical",
    "general"
]

# Analytics configuration
ANALYTICS_CONFIG = {
    "track_sentiment": True,
    "track_topics": True,
    "track_response_time": True,
    "track_user_satisfaction": True,
    "generate_daily_reports": True,
    "alert_on_negative_sentiment": True,
    "alert_threshold": 0.3  # Alert if negative sentiment > 30%
}