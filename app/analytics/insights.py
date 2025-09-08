"""
Business insights analyzer for customer support data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import json
import asyncio

from app.chatbot.utils import classify_intent
from app.chatbot.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

class BusinessInsightsAnalyzer:
    """
    Analyzes customer support conversations to generate business insights
    """
    
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.conversation_data = []  # In production, this would be from database
        
    async def generate_insights(
        self,
        days: int = 7,
        user_id: Optional[str] = None,
        intent_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive business insights from customer interactions
        
        Args:
            days: Number of days to analyze
            user_id: Filter by specific user (optional)
            intent_filter: Filter by intent (optional)
            
        Returns:
            Dictionary containing various insights
        """
        
        try:
            # Get conversation data (in production, query from database)
            conversations = await self._get_conversation_data(days, user_id, intent_filter)
            
            if not conversations:
                return {
                    "period": f"Last {days} days",
                    "total_conversations": 0,
                    "insights": "No conversations found for the specified period."
                }
            
            # Generate various insights
            insights = {
                "period": f"Last {days} days",
                "generated_at": datetime.now().isoformat(),
                "total_conversations": len(conversations),
                "summary": await self._generate_executive_summary(conversations),
                "intent_analysis": self._analyze_intents(conversations),
                "sentiment_trends": await self._analyze_sentiment_trends(conversations),
                "response_performance": self._analyze_response_performance(conversations),
                "escalation_analysis": self._analyze_escalations(conversations),
                "customer_satisfaction": self._analyze_satisfaction(conversations),
                "common_issues": await self._identify_common_issues(conversations),
                "recommendations": await self._generate_recommendations(conversations),
                "time_patterns": self._analyze_time_patterns(conversations),
                "topic_clustering": await self._analyze_topics(conversations)
            }
            
            logger.info(f"Generated insights for {len(conversations)} conversations")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                "error": "Failed to generate insights",
                "details": str(e)
            }
    
    async def _get_conversation_data(
        self,
        days: int,
        user_id: Optional[str] = None,
        intent_filter: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve conversation data for analysis"""
        
        # This is a mock implementation
        # In production, this would query your database
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Sample conversation data
        sample_conversations = [
            {
                "user_id": "user_001",
                "messages": [
                    {"role": "user", "content": "I need to track my order #ABC123", "timestamp": "2024-01-15T10:30:00"},
                    {"role": "assistant", "content": "I can help you track your order. Let me look that up.", "timestamp": "2024-01-15T10:30:15"}
                ],
                "intent": "order_status",
                "sentiment": "neutral",
                "resolved": True,
                "response_time": 2.5,
                "escalated": False,
                "satisfaction_rating": 4
            },
            {
                "user_id": "user_002", 
                "messages": [
                    {"role": "user", "content": "This product is defective and I want a refund!", "timestamp": "2024-01-15T14:22:00"},
                    {"role": "assistant", "content": "I understand your frustration. Let me help with the return process.", "timestamp": "2024-01-15T14:22:10"}
                ],
                "intent": "returns",
                "sentiment": "negative",
                "resolved": True,
                "response_time": 1.8,
                "escalated": True,
                "satisfaction_rating": 3
            }
        ]
        
        # Filter based on criteria
        filtered_conversations = []
        for conv in sample_conversations:
            if user_id and conv["user_id"] != user_id:
                continue
            if intent_filter and conv["intent"] != intent_filter:
                continue
            filtered_conversations.append(conv)
        
        return filtered_conversations
    
    async def _generate_executive_summary(self, conversations: List[Dict]) -> str:
        """Generate high-level executive summary"""
        
        total_conversations = len(conversations)
        avg_response_time = sum(conv.get("response_time", 0) for conv in conversations) / max(total_conversations, 1)
        escalation_rate = sum(1 for conv in conversations if conv.get("escalated", False)) / max(total_conversations, 1) * 100
        resolution_rate = sum(1 for conv in conversations if conv.get("resolved", False)) / max(total_conversations, 1) * 100
        
        summary = f"""
        Executive Summary:
        
        • Total customer interactions: {total_conversations}
        • Average response time: {avg_response_time:.1f} seconds
        • Resolution rate: {resolution_rate:.1f}%
        • Escalation rate: {escalation_rate:.1f}%
        
        Key Performance Indicators show {"excellent" if escalation_rate < 10 else "good" if escalation_rate < 20 else "needs improvement"} 
        customer service performance with most issues being resolved automatically.
        """
        
        return summary.strip()
    
    def _analyze_intents(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze distribution of customer intents"""
        
        intent_counts = Counter(conv.get("intent", "unknown") for conv in conversations)
        total = len(conversations)
        
        intent_analysis = {
            "total_interactions": total,
            "intent_distribution": dict(intent_counts),
            "intent_percentages": {
                intent: (count / total * 100) if total > 0 else 0
                for intent, count in intent_counts.items()
            },
            "top_intents": intent_counts.most_common(5)
        }
        
        return intent_analysis
    
    async def _analyze_sentiment_trends(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment trends over time"""
        
        sentiment_counts = Counter(conv.get("sentiment", "neutral") for conv in conversations)
        total = len(conversations)
        
        sentiment_analysis = {
            "overall_sentiment_distribution": dict(sentiment_counts),
            "sentiment_percentages": {
                sentiment: (count / total * 100) if total > 0 else 0
                for sentiment, count in sentiment_counts.items()
            },
            "negative_sentiment_rate": (sentiment_counts.get("negative", 0) / total * 100) if total > 0 else 0,
            "positive_sentiment_rate": (sentiment_counts.get("positive", 0) / total * 100) if total > 0 else 0
        }
        
        # Alert if negative sentiment is high
        if sentiment_analysis["negative_sentiment_rate"] > 30:
            sentiment_analysis["alert"] = "High negative sentiment detected - review customer satisfaction measures"
        
        return sentiment_analysis
    
    def _analyze_response_performance(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze chatbot response performance"""
        
        response_times = [conv.get("response_time", 0) for conv in conversations if conv.get("response_time")]
        
        if not response_times:
            return {"error": "No response time data available"}
        
        avg_response_time = sum(response_times) / len(response_times)
        fast_responses = sum(1 for rt in response_times if rt < 2.0)
        slow_responses = sum(1 for rt in response_times if rt > 10.0)
        
        performance_analysis = {
            "average_response_time": round(avg_response_time, 2),
            "median_response_time": round(sorted(response_times)[len(response_times)//2], 2),
            "fast_responses_under_2s": fast_responses,
            "slow_responses_over_10s": slow_responses,
            "performance_score": round((fast_responses / len(response_times) * 100), 1)
        }
        
        return performance_analysis
    
    def _analyze_escalations(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze escalation patterns"""
        
        escalated_convs = [conv for conv in conversations if conv.get("escalated", False)]
        escalation_rate = len(escalated_convs) / len(conversations) * 100 if conversations else 0
        
        # Analyze escalation reasons by intent
        escalation_by_intent = defaultdict(int)
        for conv in escalated_convs:
            escalation_by_intent[conv.get("intent", "unknown")] += 1
        
        escalation_analysis = {
            "total_escalations": len(escalated_convs),
            "escalation_rate": round(escalation_rate, 1),
            "escalations_by_intent": dict(escalation_by_intent),
            "escalation_triggers": ["frustrated", "angry", "manager", "complaint"]  # Common triggers
        }
        
        if escalation_rate > 20:
            escalation_analysis["recommendation"] = "High escalation rate - consider improving bot responses"
        
        return escalation_analysis
    
    def _analyze_satisfaction(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze customer satisfaction metrics"""
        
        ratings = [conv.get("satisfaction_rating") for conv in conversations if conv.get("satisfaction_rating")]
        
        if not ratings:
            return {"message": "No satisfaction ratings available"}
        
        avg_rating = sum(ratings) / len(ratings)
        rating_distribution = Counter(ratings)
        
        satisfaction_analysis = {
            "average_rating": round(avg_rating, 2),
            "total_ratings": len(ratings),
            "rating_distribution": dict(rating_distribution),
            "satisfaction_rate": sum(1 for r in ratings if r >= 4) / len(ratings) * 100,
            "dissatisfaction_rate": sum(1 for r in ratings if r <= 2) / len(ratings) * 100
        }
        
        return satisfaction_analysis
    
    async def _identify_common_issues(self, conversations: List[Dict]) -> List[Dict[str, Any]]:
        """Identify most common customer issues"""
        
        # Analyze common phrases and issues
        issue_keywords = {
            "Order Issues": ["order", "shipping", "delivery", "track", "delayed"],
            "Payment Problems": ["payment", "charge", "bill", "refund", "money"],
            "Product Defects": ["defective", "broken", "damaged", "wrong", "missing"],
            "Account Issues": ["login", "password", "account", "access", "username"],
            "Return Requests": ["return", "exchange", "refund", "send back"]
        }
        
        issue_counts = defaultdict(int)
        
        for conv in conversations:
            for message in conv.get("messages", []):
                if message["role"] == "user":
                    content = message["content"].lower()
                    for issue_category, keywords in issue_keywords.items():
                        if any(keyword in content for keyword in keywords):
                            issue_counts[issue_category] += 1
        
        # Sort by frequency
        common_issues = [
            {
                "issue": issue,
                "frequency": count,
                "percentage": round(count / len(conversations) * 100, 1)
            }
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return common_issues[:10]  # Top 10 issues
    
    async def _generate_recommendations(self, conversations: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Analyze escalation rate
        escalation_rate = sum(1 for conv in conversations if conv.get("escalated", False)) / len(conversations) * 100
        if escalation_rate > 15:
            recommendations.append("Consider expanding the knowledge base to handle more queries automatically")
        
        # Analyze response times
        response_times = [conv.get("response_time", 0) for conv in conversations if conv.get("response_time")]
        if response_times and sum(response_times) / len(response_times) > 5:
            recommendations.append("Optimize response generation to improve response times")
        
        # Analyze sentiment
        negative_sentiment = sum(1 for conv in conversations if conv.get("sentiment") == "negative")
        if negative_sentiment > len(conversations) * 0.3:
            recommendations.append("Review negative interactions to improve customer satisfaction")
        
        # Analyze common intents
        intent_counts = Counter(conv.get("intent", "unknown") for conv in conversations)
        top_intent = intent_counts.most_common(1)[0] if intent_counts else None
        if top_intent and top_intent[1] > len(conversations) * 0.4:
            recommendations.append(f"Focus on improving responses for {top_intent[0]} queries - they represent {top_intent[1]/len(conversations)*100:.1f}% of interactions")
        
        # Default recommendations if no specific issues found
        if not recommendations:
            recommendations = [
                "Continue monitoring customer interactions for emerging patterns",
                "Consider implementing proactive customer outreach for high-value customers",
                "Regularly update knowledge base with new product information"
            ]
        
        return recommendations
    
    def _analyze_time_patterns(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation timing patterns"""
        
        hour_distribution = defaultdict(int)
        day_distribution = defaultdict(int)
        
        for conv in conversations:
            # Get timestamp from first message
            first_message = conv.get("messages", [{}])[0]
            timestamp_str = first_message.get("timestamp", "")
            
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    hour_distribution[timestamp.hour] += 1
                    day_distribution[timestamp.strftime("%A")] += 1
                except ValueError:
                    continue
        
        # Find peak hours and days
        peak_hour = max(hour_distribution.items(), key=lambda x: x[1]) if hour_distribution else (12, 0)
        peak_day = max(day_distribution.items(), key=lambda x: x[1]) if day_distribution else ("Monday", 0)
        
        time_analysis = {
            "hourly_distribution": dict(hour_distribution),
            "daily_distribution": dict(day_distribution),
            "peak_hour": f"{peak_hour[0]}:00 with {peak_hour[1]} conversations",
            "peak_day": f"{peak_day[0]} with {peak_day[1]} conversations",
            "business_hours_conversations": sum(
                count for hour, count in hour_distribution.items() if 9 <= hour <= 17
            ),
            "after_hours_conversations": sum(
                count for hour, count in hour_distribution.items() if hour < 9 or hour > 17
            )
        }
        
        return time_analysis
    
    async def _analyze_topics(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation topics using AI"""
        
        # Extract all user messages
        user_messages = []
        for conv in conversations:
            for message in conv.get("messages", []):
                if message["role"] == "user":
                    user_messages.append(message["content"])
        
        if not user_messages:
            return {"topics": [], "message": "No user messages found"}
        
        try:
            # Use OpenAI to extract topics from a sample of messages
            sample_messages = user_messages[:50]  # Analyze first 50 messages
            combined_text = " | ".join(sample_messages)
            
            topics = await self.openai_client.extract_topics(combined_text)
            
            topic_analysis = {
                "discovered_topics": topics,
                "total_messages_analyzed": len(sample_messages),
                "topic_extraction_method": "AI-powered"
            }
            
            return topic_analysis
            
        except Exception as e:
            logger.error(f"Error in topic analysis: {e}")
            return {
                "topics": ["general_support", "product_inquiries", "order_management"],
                "message": "Used fallback topic classification",
                "error": str(e)
            }
    
    async def analyze_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze trends over time"""
        
        try:
            conversations = await self._get_conversation_data(days)
            
            # Group conversations by day
            daily_stats = defaultdict(lambda: {
                "conversations": 0,
                "escalations": 0,
                "avg_response_time": 0,
                "sentiment_positive": 0,
                "sentiment_negative": 0
            })
            
            for conv in conversations:
                # Extract date from first message
                first_message = conv.get("messages", [{}])[0]
                timestamp_str = first_message.get("timestamp", "")
                
                if timestamp_str:
                    try:
                        date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).date()
                        date_str = date.isoformat()
                        
                        daily_stats[date_str]["conversations"] += 1
                        if conv.get("escalated", False):
                            daily_stats[date_str]["escalations"] += 1
                        if conv.get("sentiment") == "positive":
                            daily_stats[date_str]["sentiment_positive"] += 1
                        elif conv.get("sentiment") == "negative":
                            daily_stats[date_str]["sentiment_negative"] += 1
                        
                        # Add response time
                        rt = conv.get("response_time", 0)
                        current_avg = daily_stats[date_str]["avg_response_time"]
                        count = daily_stats[date_str]["conversations"]
                        daily_stats[date_str]["avg_response_time"] = (current_avg * (count - 1) + rt) / count
                        
                    except ValueError:
                        continue
            
            trends = {
                "period": f"Last {days} days",
                "daily_statistics": dict(daily_stats),
                "trend_summary": {
                    "total_days_analyzed": len(daily_stats),
                    "average_daily_conversations": sum(stats["conversations"] for stats in daily_stats.values()) / max(len(daily_stats), 1),
                    "peak_conversation_day": max(daily_stats.items(), key=lambda x: x[1]["conversations"])[0] if daily_stats else None
                }
            }
            
            return trends