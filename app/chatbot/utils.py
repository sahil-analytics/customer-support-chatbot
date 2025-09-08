"""
Utility functions for chatbot operations
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def classify_intent(message: str, knowledge_base: Dict[str, Any]) -> str:
    """
    Classify the intent of a customer message
    
    Args:
        message: Customer's message
        knowledge_base: Knowledge base with intent mappings
        
    Returns:
        Classified intent as string
    """
    
    message_lower = message.lower()
    
    # Define intent patterns
    intent_patterns = {
        "greeting": [r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b"],
        "order_status": [r"\b(track|tracking|order|delivery|shipped|shipping)\b"],
        "billing": [r"\b(bill|charge|payment|invoice|refund|money|cost|price)\b"],
        "returns": [r"\b(return|exchange|defective|damaged|broken|wrong item)\b"],
        "account": [r"\b(password|login|account|profile|settings|username)\b"],
        "product_info": [r"\b(product|item|specification|details|features|size)\b"],
        "complaint": [r"\b(complaint|dissatisfied|problem|issue|frustrated|angry|terrible)\b"],
        "compliment": [r"\b(great|excellent|amazing|satisfied|happy|love|perfect)\b"],
        "technical_support": [r"\b(error|bug|not working|broken|crash|technical)\b"],
        "cancellation": [r"\b(cancel|cancellation|stop|remove)\b"]
    }
    
    # Score each intent
    intent_scores = {}
    
    for intent, patterns in intent_patterns.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, message_lower))
            score += matches
        intent_scores[intent] = score
    
    # Return the highest scoring intent, or 'general' if no matches
    best_intent = max(intent_scores, key=intent_scores.get)
    
    if intent_scores[best_intent] > 0:
        return best_intent
    else:
        return "general"

def extract_entities(message: str) -> Dict[str, Any]:
    """
    Extract entities from customer message
    
    Args:
        message: Customer's message
        
    Returns:
        Dictionary of extracted entities
    """
    
    entities = {}
    
    # Extract order numbers (pattern: letters/numbers, 6-20 characters)
    order_pattern = r'\b([A-Z0-9]{6,20})\b'
    order_matches = re.findall(order_pattern, message.upper())
    if order_matches:
        entities['order_numbers'] = order_matches
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, message)
    if email_matches:
        entities['emails'] = email_matches
    
    # Extract phone numbers (basic pattern)
    phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    phone_matches = re.findall(phone_pattern, message)
    if phone_matches:
        entities['phone_numbers'] = phone_matches
    
    # Extract dollar amounts
    money_pattern = r'\$\d+(?:\.\d{2})?'
    money_matches = re.findall(money_pattern, message)
    if money_matches:
        entities['amounts'] = money_matches
    
    # Extract dates (simple patterns)
    date_patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
        r'\b\d{4}-\d{2}-\d{2}\b',      # YYYY-MM-DD
        r'\b\d{1,2}-\d{1,2}-\d{4}\b'   # MM-DD-YYYY
    ]
    
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, message))
    
    if dates:
        entities['dates'] = dates
    
    # Extract product mentions (common product keywords)
    product_keywords = ['laptop', 'phone', 'tablet', 'headphones', 'keyboard', 'mouse', 'monitor', 'watch']
    found_products = [keyword for keyword in product_keywords if keyword.lower() in message.lower()]
    if found_products:
        entities['products'] = found_products
    
    return entities

def should_escalate(message: str, conversation_history: List[Dict], knowledge_base: Dict[str, Any]) -> bool:
    """
    Determine if conversation should be escalated to human agent
    
    Args:
        message: Current customer message
        conversation_history: Previous conversation messages
        knowledge_base: Knowledge base with escalation keywords
        
    Returns:
        Boolean indicating whether to escalate
    """
    
    message_lower = message.lower()
    
    # Check for explicit escalation keywords
    escalation_keywords = knowledge_base.get('escalation_keywords', [])
    for keyword in escalation_keywords:
        if keyword.lower() in message_lower:
            return True
    
    # Check for patterns indicating frustration
    frustration_patterns = [
        r'\b(frustrated|angry|mad|upset|annoyed)\b',
        r'\b(terrible|awful|horrible|worst)\b',
        r'\b(unacceptable|ridiculous|stupid)\b',
        r'\b(cancel|refund|money back)\b.*\b(now|immediately)\b'
    ]
    
    for pattern in frustration_patterns:
        if re.search(pattern, message_lower):
            return True
    
    # Check conversation length - escalate after many back-and-forth messages
    if len(conversation_history) > 10:
        return True
    
    # Check for repeated issues (same intent multiple times)
    if len(conversation_history) >= 6:
        recent_messages = conversation_history[-6:]
        user_messages = [msg for msg in recent_messages if msg['role'] == 'user']
        
        if len(user_messages) >= 3:
            # Simple check for repeated similar content
            intents = [classify_intent(msg['content'], knowledge_base) for msg in user_messages]
            if len(set(intents)) == 1 and intents[0] in ['complaint', 'billing', 'returns']:
                return True
    
    return False

def sanitize_message(message: str) -> str:
    """
    Sanitize user message for security and processing
    
    Args:
        message: Raw user message
        
    Returns:
        Sanitized message
    """
    
    # Remove excessive whitespace
    message = re.sub(r'\s+', ' ', message.strip())
    
    # Remove potentially harmful characters but keep basic punctuation
    message = re.sub(r'[<>{}[\]\\]', '', message)
    
    # Limit message length
    if len(message) > 1000:
        message = message[:1000] + "..."
    
    return message

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate basic similarity between two texts
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Similarity score between 0 and 1
    """
    
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if len(union) == 0:
        return 0.0
    
    return len(intersection) / len(union)

def format_response(response: str, user_name: Optional[str] = None) -> str:
    """
    Format bot response with personalization
    
    Args:
        response: Raw response text
        user_name: Optional user name for personalization
        
    Returns:
        Formatted response
    """
    
    # Add personalization if user name is available
    if user_name:
        response = response.replace("[USER]", user_name)
    else:
        response = response.replace("[USER]", "")
    
    # Ensure proper punctuation
    if response and not response[-1] in '.!?':
        response += '.'
    
    # Remove extra spaces
    response = re.sub(r'\s+', ' ', response.strip())
    
    return response

def extract_phone_number(message: str) -> Optional[str]:
    """
    Extract and validate phone number from message
    
    Args:
        message: Message containing potential phone number
        
    Returns:
        Formatted phone number or None
    """
    
    # Common phone number patterns
    patterns = [
        r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',  # US format
        r'(\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'  # US with country code
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            # Clean and format the phone number
            phone = re.sub(r'[^\d]', '', match.group(1))
            if len(phone) == 10:
                return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
            elif len(phone) == 11 and phone[0] == '1':
                return f"({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
    
    return None

def is_business_hours() -> bool:
    """
    Check if current time is within business hours
    
    Returns:
        Boolean indicating if it's business hours
    """
    
    from app.config.settings import BUSINESS_HOURS_CONFIG
    
    now = datetime.now()
    current_day = now.strftime("%A").lower()
    current_time = now.strftime("%H:%M")
    
    day_config = BUSINESS_HOURS_CONFIG["days"].get(current_day, {})
    
    if day_config.get("closed", False):
        return False
    
    start_time = day_config.get("start")
    end_time = day_config.get("end")
    
    if start_time and end_time:
        return start_time <= current_time <= end_time
    
    return True  # Default to open if no config

def generate_conversation_id(user_id: str) -> str:
    """
    Generate unique conversation ID
    
    Args:
        user_id: User identifier
        
    Returns:
        Unique conversation ID
    """
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{user_id}_{timestamp}"

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        Boolean indicating if email is valid
    """
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def mask_sensitive_data(message: str) -> str:
    """
    Mask sensitive information in message for logging
    
    Args:
        message: Message that may contain sensitive data
        
    Returns:
        Message with sensitive data masked
    """
    
    # Mask email addresses
    message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     '[EMAIL_MASKED]', message)
    
    # Mask phone numbers
    message = re.sub(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', 
                     '[PHONE_MASKED]', message)
    
    # Mask credit card numbers (basic pattern)
    message = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 
                     '[CARD_MASKED]', message)
    
    # Mask SSN (basic pattern)
    message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_MASKED]', message)
    
    return message