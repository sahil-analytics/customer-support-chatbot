"""
Database models and connection setup
"""

import logging
from datetime import datetime
from typing import Optional, AsyncGenerator
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, 
    JSON, ForeignKey, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import relationship, sessionmaker

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database base class
Base = declarative_base()

class Conversation(Base):
    """Conversation model for storing chat sessions"""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    conversation_id = Column(String(200), unique=True, index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_messages = Column(Integer, default=0)
    escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime, nullable=True)
    user_satisfaction = Column(Float, nullable=True)  # 1-5 rating
    summary = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """Individual messages within conversations"""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    intent = Column(String(50), nullable=True)
    entities = Column(JSON, nullable=True)
    response_time = Column(Float, nullable=True)  # seconds
    confidence = Column(Float, nullable=True)  # AI confidence score
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class UserFeedback(Base):
    """User feedback and ratings"""
    
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 scale
    feedback_text = Column(Text, nullable=True)
    feedback_type = Column(String(50), default="general")  # general, complaint, compliment
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="feedback")

class AnalyticsEvent(Base):
    """Analytics events for tracking system performance"""
    
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=True)
    conversation_id = Column(String(200), index=True, nullable=True)
    event_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, nullable=True)

# Database engine and session management
class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self):
        self.database_url = settings.database_url
        self.engine = None
        self.async_session_maker = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Setup database engine"""
        if self.database_url.startswith("sqlite"):
            # SQLite setup
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False}
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
        elif self.database_url.startswith("postgresql"):
            # PostgreSQL setup
            async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            self.engine = create_async_engine(async_url)
            self.async_session_maker = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            
            # Also create sync engine for initial setup
            self.sync_engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.sync_engine)
        
        logger.info(f"Database engine configured for: {self.database_url.split('://')[0]}")
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        if self.async_session_maker:
            async with self.async_session_maker() as session:
                yield session
        else:
            raise NotImplementedError("Async sessions not available for SQLite")
    
    def get_sync_session(self):
        """Get synchronous database session"""
        return self.SessionLocal()

# Global database manager instance
db_manager = DatabaseManager()

async def init_database():
    """Initialize database tables"""
    try:
        if settings.database_url.startswith("sqlite"):
            # SQLite - create tables synchronously
            Base.metadata.create_all(bind=db_manager.engine)
            logger.info("SQLite database tables created successfully")
            
        elif settings.database_url.startswith("postgresql"):
            # PostgreSQL - create tables asynchronously
            async with db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("PostgreSQL database tables created successfully")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def get_database():
    """Dependency for getting database session"""
    if settings.database_url.startswith("postgresql"):
        async for session in db_manager.get_async_session():
            yield session
    else:
        # For SQLite, use sync session in a thread-safe way
        session = db_manager.get_sync_session()
        try:
            yield session
        finally:
            session.close()

async def test_connection() -> bool:
    """Test database connection"""
    try:
        if settings.database_url.startswith("sqlite"):
            session = db_manager.get_sync_session()
            session.execute("SELECT 1")
            session.close()
            
        elif settings.database_url.startswith("postgresql"):
            async with db_manager.engine.begin() as conn:
                await conn.execute("SELECT 1")
                
        logger.info("Database connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

# Utility functions for database operations
class ConversationService:
    """Service class for conversation database operations"""
    
    @staticmethod
    def create_conversation(session, user_id: str, conversation_id: str) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            user_id=user_id,
            conversation_id=conversation_id,
            started_at=datetime.utcnow()
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        return conversation
    
    @staticmethod
    def add_message(session, conversation_id: int, role: str, content: str, 
                   intent: str = None, entities: dict = None, 
                   response_time: float = None, confidence: float = None) -> Message:
        """Add a message to conversation"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            intent=intent,
            entities=entities,
            response_time=response_time,
            confidence=confidence,
            timestamp=datetime.utcnow()
        )
        session.add(message)
        session.commit()
        session.refresh(message)
        
        # Update conversation message count
        conversation = session.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.total_messages += 1
            session.commit()
        
        return message
    
    @staticmethod
    def add_feedback(session, conversation_id: int, user_id: str, 
                    rating: int, feedback_text: str = None) -> UserFeedback:
        """Add user feedback"""
        feedback = UserFeedback(
            conversation_id=conversation_id,
            user_id=user_id,
            rating=rating,
            feedback_text=feedback_text,
            created_at=datetime.utcnow()
        )
        session.add(feedback)
        session.commit()
        session.refresh(feedback)
        return feedback

class AnalyticsService:
    """Service class for analytics database operations"""
    
    @staticmethod
    def log_event(session, event_type: str, user_id: str = None, 
                 conversation_id: str = None, event_data: dict = None):
        """Log an analytics event"""
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            conversation_id=conversation_id,
            event_data=event_data,
            timestamp=datetime.utcnow()
        )
        session.add(event)
        session.commit()
        return event