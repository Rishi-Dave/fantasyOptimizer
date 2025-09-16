"""
Webhook system for real-time fantasy football updates.
"""

from .breaking_news import breaking_news_processor, webhook_simulator

__all__ = ['breaking_news_processor', 'webhook_simulator']