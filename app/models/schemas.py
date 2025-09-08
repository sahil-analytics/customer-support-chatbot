"""
Pydantic schemas for API request/response models
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator

# Conversation schemas
class ConversationBase(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    conversation_id: str = Field(..., description="Unique conversation identifier")

class ConversationCreate(ConversationBase):
    metadata: Optional[Dict[str, Any]] = None

class ConversationResponse(ConversationBase):
    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_messages: int = 0
    escalated: bool = False
    escalated_at: Optional[datetime] = None
    user_satisfaction: Optional[float] = None
    summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ConversationSummary(BaseModel):
    conversation_id: str
    user_id: str
    message_count: int
    duration_minutes: Optional[float] = None
    escalated: bool
    satisfaction_rating: Optional[float] = None
    main_topics: List[str] = []
    sentiment: Optional[str] = None

# Message schemas
class MessageBase(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message content")

class MessageCreate(MessageBase):
    conversation_id: int
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'assistant']:
            raise ValueError('Role must be either "user" or "assistant"')
        return v

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    timestamp: datetime
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Feedback schemas
class FeedbackBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    feedback_text: Optional[str] = Field(None, max_length=1000)

class FeedbackCreate(FeedbackBase):
    conversation_id: int
    user_id: str
    feedback_type: str = "general"

class FeedbackResponse(FeedbackBase):
    id: int
    conversation_id: int
    user_id: str
    feedback_type: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Analytics schemas
class AnalyticsEventBase(BaseModel):
    event_type: str = Field(..., description="Type of analytics event")
    event_data: Optional[Dict[str, Any]] = None

class AnalyticsEventCreate(AnalyticsEventBase):
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AnalyticsEventResponse(AnalyticsEventBase):
    id: int
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Chat API schemas
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    user_id: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    conversation_id: str
    intent: str
    entities: Dict[str, Any] = {}
    response_type: str = "ai_response"
    response_time: float
    escalated: bool = False
    confidence: Optional[float] = None
    timestamp: datetime
    suggestions: List[str] = []

# Analytics response schemas
class ConversationMetrics(BaseModel):
    total_conversations: int
    active_conversations: int
    average_messages_per_conversation: float
    average_response_time: float
    escalation_rate: float
    user_satisfaction_average: Optional[float] = None

class IntentAnalytics(BaseModel):
    intent: str
    count: int
    percentage: float
    average_resolution_time: float
    escalation_rate: float

class SentimentAnalytics(BaseModel):
    positive: int
    neutral: int  
    negative: int
    total: int
    sentiment_score: float  # -1 to 1

class BusinessInsights(BaseModel):
    period_days: int
    total_interactions: int
    metrics: ConversationMetrics
    top_intents: List[IntentAnalytics]
    sentiment_breakdown: SentimentAnalytics
    peak_hours: List[int]  # Hours of day with most activity
    common_escalation_reasons: List[str]
    recommendations: List[str]

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str = Field(..., description="Message type: 'user_message', 'bot_response', 'typing', 'error'")
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class WebSocketResponse(BaseModel):
    type: str
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime
    user_id: str
    conversation_id: str

# Knowledge base schemas
class KnowledgeBaseEntry(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    keywords: List[str] = []
    confidence: Optional[float] = None

class KnowledgeBaseSearch(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, le=20)
    category: Optional[str] = None

class KnowledgeBaseResult(BaseModel):
    question: str
    answer: str
    relevance_score: float
    category: Optional[str] = None

# System status schemas
class SystemHealth(BaseModel):
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    components: Dict[str, str]  # component_name: status
    metrics: Optional[Dict[str, Any]] = None
    errors: List[str] = []

class SystemMetrics(BaseModel):
    uptime_seconds: float
    total_requests: int
    requests_per_second: float
    average_response_time: float
    error_rate: float
    active_connections: int
    memory_usage_mb: float
    cpu_usage_percent: float

# Export schemas
class ConversationExport(BaseModel):
    conversations: List[ConversationResponse]
    messages: List[MessageResponse]
    feedback: List[FeedbackResponse]
    analytics: List[AnalyticsEventResponse]
    export_metadata: Dict[str, Any]

# Configuration schemas
class ChatbotConfig(BaseModel):
    max_context_messages: int = 10
    max_response_length: int = 500
    temperature: float = 0.7
    escalation_keywords: List[str] = []
    business_hours: Dict[str, Any] = {}
    supported_languages: List[str] = ["en"]

class BusinessInfo(BaseModel):
    company_name: str
    support_email: str
    support_phone: str
    support_hours: str
    website: Optional[str] = None
    social_media: Optional[Dict[str, str]] = None