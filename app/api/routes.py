"""
API routes for the customer support chatbot
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.chatbot.core import CustomerSupportChatbot
from app.analytics.insights import BusinessInsightsAnalyzer
from app.analytics.metrics import MetricsCollector

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize components
chatbot = CustomerSupportChatbot()
insights_analyzer = BusinessInsightsAnalyzer()
metrics_collector = MetricsCollector()

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    user_id: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    intent: str
    entities: Dict[str, Any]
    response_type: str
    response_time: float
    escalated: bool
    timestamp: str
    confidence: Optional[float] = None

class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class ConversationHistory(BaseModel):
    user_id: str
    messages: List[ConversationMessage]
    summary: Dict[str, Any]

class AnalyticsRequest(BaseModel):
    days: int = 7
    user_id: Optional[str] = None
    intent_filter: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """
    Main chat endpoint for interacting with the bot
    """
    try:
        # Process the message
        result = await chatbot.process_message(
            message=request.message,
            user_id=request.user_id,
            context=request.context
        )
        
        # Collect metrics
        await metrics_collector.record_interaction(
            user_id=request.user_id,
            message=request.message,
            response=result["response"],
            response_time=result["response_time"],
            intent=result["intent"],
            escalated=result["escalated"]
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conversations/{user_id}", response_model=ConversationHistory)
async def get_conversation_history(user_id: str):
    """
    Get conversation history for a specific user
    """
    try:
        history = chatbot.get_conversation_history(user_id)
        summary = chatbot.get_conversation_summary(user_id)
        
        messages = [
            ConversationMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            )
            for msg in history
        ]
        
        return ConversationHistory(
            user_id=user_id,
            messages=messages,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving conversation history")

@router.delete("/conversations/{user_id}")
async def clear_conversation_history(user_id: str):
    """
    Clear conversation history for a specific user
    """
    try:
        success = chatbot.clear_conversation_history(user_id)
        if success:
            return {"message": f"Conversation history cleared for user {user_id}"}
        else:
            return {"message": f"No conversation history found for user {user_id}"}
            
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        raise HTTPException(status_code=500, detail="Error clearing conversation history")

@router.get("/analytics/insights")
async def get_business_insights(
    days: int = Query(7, description="Number of days to analyze"),
    user_id: Optional[str] = Query(None, description="Filter by specific user"),
    intent_filter: Optional[str] = Query(None, description="Filter by intent")
):
    """
    Get business insights from customer interactions
    """
    try:
        insights = await insights_analyzer.generate_insights(
            days=days,
            user_id=user_id,
            intent_filter=intent_filter
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail="Error generating business insights")

@router.get("/analytics/metrics")
async def get_performance_metrics(
    days: int = Query(7, description="Number of days to analyze")
):
    """
    Get performance metrics for the chatbot
    """
    try:
        metrics = await metrics_collector.get_metrics(days=days)
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics")

@router.get("/analytics/trends")
async def get_conversation_trends(
    days: int = Query(30, description="Number of days to analyze")
):
    """
    Get conversation trends and patterns
    """
    try:
        trends = await insights_analyzer.analyze_trends(days=days)
        return trends
        
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing conversation trends")

@router.get("/analytics/sentiment")
async def get_sentiment_analysis(
    days: int = Query(7, description="Number of days to analyze")
):
    """
    Get sentiment analysis of customer conversations
    """
    try:
        sentiment_data = await insights_analyzer.analyze_sentiment(days=days)
        return sentiment_data
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing sentiment")

@router.post("/analytics/feedback")
async def submit_feedback(
    user_id: str,
    rating: int = Query(..., ge=1, le=5, description="Rating from 1-5"),
    feedback: Optional[str] = None
):
    """
    Submit user feedback for a conversation
    """
    try:
        await metrics_collector.record_feedback(
            user_id=user_id,
            rating=rating,
            feedback=feedback,
            timestamp=datetime.now()
        )
        
        return {"message": "Feedback recorded successfully"}
        
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail="Error recording feedback")

@router.get("/knowledge-base/search")
async def search_knowledge_base(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Maximum number of results")
):
    """
    Search the knowledge base for relevant information
    """
    try:
        # This is a simple implementation - in production you might use
        # vector search or more sophisticated matching
        results = []
        kb = chatbot.knowledge_base
        
        query_lower = query.lower()
        
        for faq in kb.get("faqs", []):
            question_lower = faq["question"].lower()
            answer_lower = faq["answer"].lower()
            
            # Simple keyword matching
            if any(word in question_lower or word in answer_lower 
                   for word in query_lower.split() if len(word) > 3):
                results.append({
                    "question": faq["question"],
                    "answer": faq["answer"],
                    "relevance_score": 0.8  # In production, calculate actual relevance
                })
        
        # Sort by relevance and limit results
        results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Error searching knowledge base")

@router.get("/status")
async def get_system_status():
    """
    Get system status and health information
    """
    try:
        # Get basic system stats
        total_conversations = len(chatbot.conversation_memory)
        
        # Get recent metrics
        recent_metrics = await metrics_collector.get_metrics(days=1)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_conversations": total_conversations,
            "daily_metrics": recent_metrics,
            "system_info": {
                "model": chatbot.openai_client.model,
                "version": "1.0.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.post("/admin/reset-conversation/{user_id}")
async def admin_reset_conversation(user_id: str):
    """
    Admin endpoint to reset a user's conversation
    """
    try:
        success = chatbot.clear_conversation_history(user_id)
        
        return {
            "success": success,
            "message": f"Conversation reset for user {user_id}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        raise HTTPException(status_code=500, detail="Error resetting conversation")

@router.get("/admin/export-data")
async def export_conversation_data(
    days: int = Query(7, description="Number of days to export"),
    format: str = Query("json", description="Export format (json, csv)")
):
    """
    Export conversation data for analysis
    """
    try:
        # In a production system, you'd export from a database
        # This is a simplified version for demonstration
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "period_days": days,
            "conversations": [],
            "summary": await metrics_collector.get_metrics(days=days)
        }
        
        # Add conversation data (in production, this would come from database)
        for user_id, history in chatbot.conversation_memory.items():
            export_data["conversations"].append({
                "user_id": user_id,
                "messages": history,
                "summary": chatbot.get_conversation_summary(user_id)
            })
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail="Error exporting conversation data")