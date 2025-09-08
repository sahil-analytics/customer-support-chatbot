"""
OpenAI API client for generating chatbot responses
"""

import logging
from typing import List, Dict, Any, Optional
import openai
from openai import AsyncOpenAI
import tiktoken

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class OpenAIClient:
    """Client for interacting with OpenAI API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")  # Fallback encoding
        
    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate a response using OpenAI GPT model
        
        Args:
            message: The current user message
            conversation_history: Previous conversation messages
            system_prompt: System instruction for the AI
            temperature: Response randomness (0-1)
            
        Returns:
            Generated response string
        """
        
        try:
            # Prepare messages for OpenAI API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (limit to prevent token overflow)
            history_messages = self._prepare_conversation_history(conversation_history)
            messages.extend(history_messages)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Check token count and truncate if necessary
            messages = self._manage_token_count(messages)
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # Log usage for monitoring
            if response.usage:
                logger.info(
                    f"OpenAI API usage - Prompt tokens: {response.usage.prompt_tokens}, "
                    f"Completion tokens: {response.usage.completion_tokens}, "
                    f"Total tokens: {response.usage.total_tokens}"
                )
            
            return generated_text
            
        except openai.RateLimitError:
            logger.error("OpenAI API rate limit exceeded")
            return "I'm experiencing high demand right now. Please try again in a moment."
            
        except openai.AuthenticationError:
            logger.error("OpenAI API authentication failed")
            return "I'm having trouble connecting to my AI service. Please contact support."
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return "I'm experiencing technical difficulties. Please try again or contact support."
            
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI client: {e}")
            return "I apologize for the inconvenience. Please try again or contact our support team."
    
    def _prepare_conversation_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert conversation history to OpenAI message format"""
        messages = []
        
        for msg in history:
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return messages
    
    def _manage_token_count(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Manage token count to stay within model limits"""
        
        # Rough token estimation (more accurate would use tiktoken properly)
        total_tokens = sum(len(msg["content"].split()) * 1.3 for msg in messages)
        
        # Reserve tokens for response
        max_input_tokens = 4000 - self.max_tokens  # Conservative limit
        
        # If we're over the limit, remove older messages
        while total_tokens > max_input_tokens and len(messages) > 2:
            # Keep system message and remove oldest user/assistant messages
            if messages[1]["role"] in ["user", "assistant"]:
                removed_msg = messages.pop(1)
                total_tokens -= len(removed_msg["content"].split()) * 1.3
        
        return messages
    
    async def generate_summary(self, conversation: List[Dict[str, str]]) -> str:
        """Generate a summary of a conversation"""
        
        if not conversation:
            return "No conversation to summarize."
        
        # Prepare conversation text
        conversation_text = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in conversation
        ])
        
        summary_prompt = """
        Please provide a concise summary of this customer support conversation, 
        including the main issue, actions taken, and outcome. Focus on key points 
        that would be useful for business insights and future reference.
        
        Conversation:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": summary_prompt},
                    {"role": "user", "content": conversation_text}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return "Unable to generate conversation summary."
    
    async def classify_sentiment(self, message: str) -> Dict[str, Any]:
        """Classify the sentiment of a customer message"""
        
        sentiment_prompt = """
        Analyze the sentiment of this customer message. Respond with a JSON object containing:
        - sentiment: one of "positive", "neutral", "negative"
        - confidence: a score from 0 to 1
        - emotions: list of detected emotions (e.g., ["frustrated", "polite"])
        
        Message: 
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sentiment_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse as JSON, fallback to basic analysis
            try:
                import json
                return json.loads(result_text)
            except:
                # Fallback sentiment analysis
                if any(word in message.lower() for word in ["angry", "frustrated", "terrible", "awful", "hate"]):
                    return {"sentiment": "negative", "confidence": 0.8, "emotions": ["frustrated"]}
                elif any(word in message.lower() for word in ["great", "excellent", "love", "amazing", "perfect"]):
                    return {"sentiment": "positive", "confidence": 0.8, "emotions": ["satisfied"]}
                else:
                    return {"sentiment": "neutral", "confidence": 0.6, "emotions": ["neutral"]}
                    
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"sentiment": "neutral", "confidence": 0.5, "emotions": ["unknown"]}
    
    async def extract_topics(self, message: str) -> List[str]:
        """Extract key topics from a customer message"""
        
        topic_prompt = """
        Extract the main topics or categories from this customer support message.
        Return only the topics as a comma-separated list (e.g., "billing, refund, order status").
        Focus on actionable business categories.
        
        Message:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": topic_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            topics_text = response.choices[0].message.content.strip()
            topics = [topic.strip() for topic in topics_text.split(",")]
            
            return topics[:5]  # Limit to 5 topics
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return ["general_inquiry"]
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # Fallback: rough estimation
            return len(text.split()) * 1.3