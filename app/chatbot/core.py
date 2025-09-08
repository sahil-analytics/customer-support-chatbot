"""
Core chatbot logic for customer support
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from app.chatbot.openai_client import OpenAIClient
from app.chatbot.utils import classify_intent, extract_entities, should_escalate
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CustomerSupportChatbot:
    """
    Main chatbot class that handles customer support conversations
    """
    
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.conversation_memory: Dict[str, List[Dict]] = {}
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from file"""
        try:
            with open("data/knowledge_base.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Knowledge base file not found, using default responses")
            return {
                "faqs": [
                    {
                        "question": "How do I track my order?",
                        "answer": "You can track your order by logging into your account and viewing the order status, or by using the tracking number sent to your email."
                    },
                    {
                        "question": "What is your return policy?",
                        "answer": "We offer a 30-day return policy for most items. Items must be in original condition with tags attached."
                    },
                    {
                        "question": "How do I cancel my order?",
                        "answer": "You can cancel your order within 1 hour of placing it by contacting customer service or through your account dashboard."
                    }
                ],
                "escalation_keywords": ["speak to human", "manager", "complaint", "frustrated", "angry"],
                "business_info": {
                    "company_name": "Your Company",
                    "support_hours": "9 AM - 6 PM EST, Monday-Friday",
                    "support_email": "support@yourcompany.com",
                    "support_phone": "1-800-123-4567"
                }
            }
    
    async def process_message(
        self, 
        message: str, 
        user_id: str, 
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a customer message and generate response
        
        Args:
            message: Customer's message
            user_id: Unique user identifier
            context: Additional context information
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Track conversation start time
            start_time = datetime.now()
            
            # Get or initialize conversation history
            if user_id not in self.conversation_memory:
                self.conversation_memory[user_id] = []
            
            # Add user message to history
            self.conversation_memory[user_id].append({
                "role": "user",
                "content": message,
                "timestamp": start_time.isoformat()
            })
            
            # Keep only recent messages (memory management)
            max_history = settings.max_context_messages
            if len(self.conversation_memory[user_id]) > max_history:
                self.conversation_memory[user_id] = self.conversation_memory[user_id][-max_history:]
            
            # Classify intent and extract entities
            intent = classify_intent(message, self.knowledge_base)
            entities = extract_entities(message)
            
            # Check if escalation is needed
            escalate = should_escalate(message, self.conversation_memory[user_id], self.knowledge_base)
            
            if escalate:
                response_text = await self._handle_escalation(user_id, intent)
                response_type = "escalation"
            else:
                # Generate AI response
                response_text = await self._generate_response(message, user_id, intent, entities)
                response_type = "ai_response"
            
            # Add bot response to history
            self.conversation_memory[user_id].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare response
            result = {
                "response": response_text,
                "user_id": user_id,
                "intent": intent,
                "entities": entities,
                "response_type": response_type,
                "response_time": response_time,
                "escalated": escalate,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.9  # This would come from your AI model in production
            }
            
            logger.info(f"Processed message for user {user_id}, intent: {intent}, response_time: {response_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment or contact our support team directly.",
                "user_id": user_id,
                "intent": "error",
                "entities": {},
                "response_type": "error",
                "response_time": 0,
                "escalated": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _generate_response(
        self, 
        message: str, 
        user_id: str, 
        intent: str, 
        entities: Dict
    ) -> str:
        """Generate AI response using OpenAI"""
        
        # Check knowledge base first
        kb_response = self._check_knowledge_base(message, intent)
        if kb_response:
            return kb_response
        
        # Prepare conversation context
        conversation_history = self.conversation_memory.get(user_id, [])
        
        # Create system prompt
        system_prompt = self._create_system_prompt(intent, entities)
        
        # Generate response using OpenAI
        response = await self.openai_client.generate_response(
            message=message,
            conversation_history=conversation_history,
            system_prompt=system_prompt
        )
        
        return response
    
    def _check_knowledge_base(self, message: str, intent: str) -> Optional[str]:
        """Check if we have a direct answer in knowledge base"""
        message_lower = message.lower()
        
        for faq in self.knowledge_base.get("faqs", []):
            question_lower = faq["question"].lower()
            if any(word in message_lower for word in question_lower.split() if len(word) > 3):
                return faq["answer"]
        
        return None
    
    def _create_system_prompt(self, intent: str, entities: Dict) -> str:
        """Create system prompt based on intent and entities"""
        
        base_prompt = f"""
        You are a helpful customer support assistant for {self.knowledge_base['business_info']['company_name']}.
        
        Your role is to:
        - Provide accurate, helpful, and friendly customer support
        - Be empathetic and understanding
        - Offer specific solutions when possible
        - Ask clarifying questions if needed
        - Escalate to human agents when appropriate
        
        Business Information:
        - Support Hours: {self.knowledge_base['business_info']['support_hours']}
        - Contact Email: {self.knowledge_base['business_info']['support_email']}
        - Phone: {self.knowledge_base['business_info']['support_phone']}
        
        Current Intent: {intent}
        Extracted Entities: {entities}
        
        Guidelines:
        - Keep responses concise but complete
        - Use a friendly, professional tone
        - If you cannot help, offer to escalate to a human agent
        - Always try to resolve the customer's issue
        """
        
        return base_prompt
    
    async def _handle_escalation(self, user_id: str, intent: str) -> str:
        """Handle escalation to human agent"""
        
        escalation_response = f"""
        I understand you need additional assistance, and I'd be happy to connect you with one of our human support specialists.
        
        Here are your options:
        
        📧 Email: {self.knowledge_base['business_info']['support_email']}
        📞 Phone: {self.knowledge_base['business_info']['support_phone']}
        🕒 Hours: {self.knowledge_base['business_info']['support_hours']}
        
        A human agent will be able to provide more personalized assistance with your {intent} inquiry.
        
        Is there anything else I can help you with in the meantime?
        """
        
        # Log escalation for analytics
        logger.info(f"Escalated conversation for user {user_id} with intent: {intent}")
        
        return escalation_response
    
    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """Get conversation history for a user"""
        return self.conversation_memory.get(user_id, [])
    
    def clear_conversation_history(self, user_id: str) -> bool:
        """Clear conversation history for a user"""
        if user_id in self.conversation_memory:
            del self.conversation_memory[user_id]
            return True
        return False
    
    def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of conversation"""
        history = self.conversation_memory.get(user_id, [])
        if not history:
            return {"message_count": 0, "duration": 0}
        
        first_message = history[0]
        last_message = history[-1]
        
        duration = 0
        if len(history) > 1:
            start_time = datetime.fromisoformat(first_message["timestamp"])
            end_time = datetime.fromisoformat(last_message["timestamp"])
            duration = (end_time - start_time).total_seconds()
        
        return {
            "message_count": len(history),
            "duration": duration,
            "start_time": first_message.get("timestamp"),
            "last_message_time": last_message.get("timestamp")
        }