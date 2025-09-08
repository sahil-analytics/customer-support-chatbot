"""
Performance metrics collection and analysis for the chatbot
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import os

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and analyzes chatbot performance metrics"""
    
    def __init__(self):
        self.metrics_data = defaultdict(list)
        self.daily_stats = defaultdict(dict)
        self.feedback_data = []
        
    async def record_interaction(
        self,
        user_id: str,
        message: str,
        response: str,
        response_time: float,
        intent: str,
        escalated: bool,
        timestamp: Optional[datetime] = None
    ):
        """Record a chatbot interaction for metrics"""
        
        if timestamp is None:
            timestamp = datetime.now()
        
        interaction = {
            "user_id": user_id,
            "message_length": len(message),
            "response_length": len(response),
            "response_time": response_time,
            "intent": intent,
            "escalated": escalated,
            "timestamp": timestamp.isoformat(),
            "date": timestamp.date().isoformat(),
            "hour": timestamp.hour
        }
        
        self.metrics_data["interactions"].append(interaction)
        
        # Update daily stats
        date_key = timestamp.date().isoformat()
        if date_key not in self.daily_stats:
            self.daily_stats[date_key] = {
                "total_interactions": 0,
                "total_response_time": 0,
                "escalations": 0,
                "intents": Counter(),
                "hourly_distribution": Counter()
            }
        
        daily = self.daily_stats[date_key]
        daily["total_interactions"] += 1
        daily["total_response_time"] += response_time
        daily["escalations"] += 1 if escalated else 0
        daily["intents"][intent] += 1
        daily["hourly_distribution"][timestamp.hour] += 1
        
        logger.debug(f"Recorded interaction for user {user_id}, intent: {intent}")
    
    async def record_feedback(
        self,
        user_id: str,
        rating: int,
        feedback: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        """Record user feedback"""
        
        if timestamp is None:
            timestamp = datetime.now()
        
        feedback_entry = {
            "user_id": user_id,
            "rating": rating,
            "feedback": feedback,
            "timestamp": timestamp.isoformat(),
            "date": timestamp.date().isoformat()
        }
        
        self.feedback_data.append(feedback_entry)
        logger.info(f"Recorded feedback from user {user_id}: {rating}/5")
    
    async def get_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive metrics for the specified period"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Filter interactions for the period
        period_interactions = [
            interaction for interaction in self.metrics_data["interactions"]
            if start_date <= datetime.fromisoformat(interaction["timestamp"]).date() <= end_date
        ]
        
        # Filter feedback for the period
        period_feedback = [
            feedback for feedback in self.feedback_data
            if start_date <= datetime.fromisoformat(feedback["timestamp"]).date() <= end_date
        ]
        
        if not period_interactions:
            return self._empty_metrics(days)
        
        # Calculate basic metrics
        total_interactions = len(period_interactions)
        total_response_time = sum(i["response_time"] for i in period_interactions)
        average_response_time = total_response_time / total_interactions if total_interactions > 0 else 0
        
        escalations = sum(1 for i in period_interactions if i["escalated"])
        escalation_rate = (escalations / total_interactions) * 100 if total_interactions > 0 else 0
        
        # Intent analysis
        intent_counts = Counter(i["intent"] for i in period_interactions)
        
        # Hourly distribution
        hourly_counts = Counter(i["hour"] for i in period_interactions)
        
        # User engagement
        unique_users = len(set(i["user_id"] for i in period_interactions))
        avg_interactions_per_user = total_interactions / unique_users if unique_users > 0 else 0
        
        # Feedback analysis
        feedback_metrics = self._analyze_feedback(period_feedback)
        
        # Daily breakdown
        daily_breakdown = self._get_daily_breakdown(period_interactions, start_date, end_date)
        
        # Performance percentiles
        response_times = [i["response_time"] for i in period_interactions]
        response_times.sort()
        
        percentiles = {}
        if response_times:
            percentiles = {
                "p50": self._percentile(response_times, 50),
                "p90": self._percentile(response_times, 90),
                "p95": self._percentile(response_times, 95),
                "p99": self._percentile(response_times, 99)
            }
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "overview": {
                "total_interactions": total_interactions,
                "unique_users": unique_users,
                "average_response_time": round(average_response_time, 2),
                "escalation_rate": round(escalation_rate, 2),
                "avg_interactions_per_user": round(avg_interactions_per_user, 1)
            },
            "performance": {
                "response_time_percentiles": percentiles,
                "total_escalations": escalations,
                "success_rate": round(100 - escalation_rate, 2)
            },
            "intent_analysis": {
                "top_intents": dict(intent_counts.most_common(10)),
                "intent_distribution": dict(intent_counts)
            },
            "temporal_analysis": {
                "hourly_distribution": dict(hourly_counts),
                "peak_hour": hourly_counts.most_common(1)[0][0] if hourly_counts else None,
                "daily_breakdown": daily_breakdown
            },
            "feedback": feedback_metrics,
            "quality_indicators": {
                "avg_message_length": round(sum(i["message_length"] for i in period_interactions) / total_interactions, 1),
                "avg_response_length": round(sum(i["response_length"] for i in period_interactions) / total_interactions, 1),
                "response_consistency": self._calculate_consistency(period_interactions)
            }
        }
    
    def _empty_metrics(self, days: int) -> Dict[str, Any]:
        """Return empty metrics structure when no data available"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "overview": {
                "total_interactions": 0,
                "unique_users": 0,
                "average_response_time": 0,
                "escalation_rate": 0,
                "avg_interactions_per_user": 0
            },
            "performance": {
                "response_time_percentiles": {},
                "total_escalations": 0,
                "success_rate": 0
            },
            "intent_analysis": {
                "top_intents": {},
                "intent_distribution": {}
            },
            "temporal_analysis": {
                "hourly_distribution": {},
                "peak_hour": None,
                "daily_breakdown": []
            },
            "feedback": {
                "average_rating": 0,
                "total_feedback": 0,
                "rating_distribution": {}
            },
            "quality_indicators": {
                "avg_message_length": 0,
                "avg_response_length": 0,
                "response_consistency": 0
            }
        }
    
    def _analyze_feedback(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Analyze user feedback data"""
        
        if not feedback_data:
            return {
                "average_rating": 0,
                "total_feedback": 0,
                "rating_distribution": {},
                "satisfaction_rate": 0
            }
        
        ratings = [f["rating"] for f in feedback_data]
        rating_counts = Counter(ratings)
        
        average_rating = sum(ratings) / len(ratings)
        satisfaction_rate = (sum(1 for r in ratings if r >= 4) / len(ratings)) * 100
        
        return {
            "average_rating": round(average_rating, 2),
            "total_feedback": len(feedback_data),
            "rating_distribution": dict(rating_counts),
            "satisfaction_rate": round(satisfaction_rate, 2),
            "recent_feedback": [
                {
                    "rating": f["rating"],
                    "feedback": f["feedback"],
                    "timestamp": f["timestamp"]
                }
                for f in sorted(feedback_data, key=lambda x: x["timestamp"], reverse=True)[:5]
            ]
        }
    
    def _get_daily_breakdown(self, interactions: List[Dict], start_date, end_date) -> List[Dict]:
        """Get daily breakdown of metrics"""
        
        daily_data = defaultdict(lambda: {
            "interactions": 0,
            "escalations": 0,
            "total_response_time": 0,
            "unique_users": set()
        })
        
        for interaction in interactions:
            date = datetime.fromisoformat(interaction["timestamp"]).date().isoformat()
            daily_data[date]["interactions"] += 1
            daily_data[date]["total_response_time"] += interaction["response_time"]
            daily_data[date]["unique_users"].add(interaction["user_id"])
            
            if interaction["escalated"]:
                daily_data[date]["escalations"] += 1
        
        # Create complete daily breakdown
        current_date = start_date
        breakdown = []
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            data = daily_data[date_str]
            
            avg_response_time = (
                data["total_response_time"] / data["interactions"] 
                if data["interactions"] > 0 else 0
            )
            
            breakdown.append({
                "date": date_str,
                "interactions": data["interactions"],
                "unique_users": len(data["unique_users"]),
                "escalations": data["escalations"],
                "avg_response_time": round(avg_response_time, 2),
                "escalation_rate": round((data["escalations"] / data["interactions"]) * 100, 2) if data["interactions"] > 0 else 0
            })
            
            current_date += timedelta(days=1)
        
        return breakdown
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        
        if not data:
            return 0
        
        index = (percentile / 100) * (len(data) - 1)
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(data) - 1)
        
        if lower_index == upper_index:
            return round(data[lower_index], 2)
        
        # Linear interpolation
        weight = index - lower_index
        value = data[lower_index] * (1 - weight) + data[upper_index] * weight
        
        return round(value, 2)
    
    def _calculate_consistency(self, interactions: List[Dict]) -> float:
        """Calculate response consistency metric"""
        
        if len(interactions) < 2:
            return 100.0
        
        response_times = [i["response_time"] for i in interactions]
        mean_time = sum(response_times) / len(response_times)
        
        # Calculate coefficient of variation (lower = more consistent)
        if mean_time == 0:
            return 100.0
        
        variance = sum((t - mean_time) ** 2 for t in response_times) / len(response_times)
        std_dev = variance ** 0.5
        cv = std_dev / mean_time
        
        # Convert to consistency score (0-100, higher = more consistent)
        consistency = max(0, 100 - (cv * 100))
        
        return round(consistency, 1)
    
    async def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics for monitoring dashboard"""
        
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        
        # Last hour stats
        hour_interactions = [
            i for i in self.metrics_data["interactions"]
            if datetime.fromisoformat(i["timestamp"]) >= last_hour
        ]
        
        # Last 24 hour stats
        day_interactions = [
            i for i in self.metrics_data["interactions"]
            if datetime.fromisoformat(i["timestamp"]) >= last_24h
        ]
        
        return {
            "current_time": now.isoformat(),
            "last_hour": {
                "interactions": len(hour_interactions),
                "escalations": sum(1 for i in hour_interactions if i["escalated"]),
                "avg_response_time": round(
                    sum(i["response_time"] for i in hour_interactions) / len(hour_interactions), 2
                ) if hour_interactions else 0
            },
            "last_24h": {
                "interactions": len(day_interactions),
                "unique_users": len(set(i["user_id"] for i in day_interactions)),
                "escalations": sum(1 for i in day_interactions if i["escalated"]),
                "top_intents": dict(Counter(i["intent"] for i in day_interactions).most_common(5))
            },
            "system_health": {
                "status": "healthy",
                "uptime_hours": 24,  # This would be calculated from actual startup time
                "total_conversations": len(set(i["user_id"] for i in self.metrics_data["interactions"]))
            }
        }
    
    def export_metrics(self, filepath: str, days: int = 30) -> bool:
        """Export metrics data to JSON file"""
        
        try:
            metrics = await self.get_metrics(days)
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "raw_interactions": self.metrics_data["interactions"][-1000:],  # Last 1000 interactions
                "feedback_data": self.feedback_data[-100:]  # Last 100 feedback entries
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Metrics exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return False
    
    def clear_old_data(self, days_to_keep: int = 90):
        """Clean up old metrics data to prevent memory issues"""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Filter interactions
        self.metrics_data["interactions"] = [
            i for i in self.metrics_data["interactions"]
            if datetime.fromisoformat(i["timestamp"]) >= cutoff_date
        ]
        
        # Filter feedback
        self.feedback_data = [
            f for f in self.feedback_data
            if datetime.fromisoformat(f["timestamp"]) >= cutoff_date
        ]
        
        # Clean daily stats
        cutoff_date_str = cutoff_date.date().isoformat()
        self.daily_stats = {
            date: stats for date, stats in self.daily_stats.items()
            if date >= cutoff_date_str
        }
        
        logger.info(f"Cleaned metrics data older than {days_to_keep} days