"""
Analytics package for customer support chatbot

This package provides business intelligence and performance analytics
for customer support conversations and chatbot performance.
"""

from app.analytics.insights import BusinessInsightsAnalyzer
from app.analytics.metrics import MetricsCollector

__all__ = [
    "BusinessInsightsAnalyzer",
    "MetricsCollector"
]

__version__ = "1.0.0"