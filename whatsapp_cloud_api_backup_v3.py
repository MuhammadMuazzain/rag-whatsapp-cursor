"""
WhatsApp Cloud API Integration for RAG Chatbot
FastAPI backend to handle WhatsApp messages and respond using a RAG chatbot
"""

import os
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
import httpx
from fastapi import FastAPI, Request, Query, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import json
import time
import asyncio
from collections import deque
from message_logger import get_logger

# Import your existing RAG and conversation components
from rag import RAGEngine, sanitize_response_text
from conversation_manager import ConversationManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="WhatsApp RAG Chatbot", version="1.0.0")

# Initialize message logger
msg_logger = get_logger()

# Duplicate message detection
# Store processed message IDs with timestamp for cleanup
processed_messages: Dict[str, datetime] = {}
message_processing_lock = asyncio.Lock()

# Cleanup old message IDs every hour to prevent memory growth
async def cleanup_old_messages():
    """Remove message IDs older than 1 hour from tracking"""
    while True:
        try:
            await asyncio.sleep(3600)  # Wait 1 hour
            current_time = datetime.now()
            expired_keys = [
                msg_id for msg_id, timestamp in processed_messages.items()
                if current_time - timestamp > timedelta(hours=1)
            ]
            for key in expired_keys:
                del processed_messages[key]
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} old message IDs")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")

# Configuration
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_secure_verify_token")
WHATSAPP_API_VERSION = "v18.0"
WHATSAPP_API_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{PHONE_NUMBER_ID}/messages"

# Validate required environment variables
if not WHATSAPP_ACCESS_TOKEN or not PHONE_NUMBER_ID:
    logger.error("Missing required environment variables: WHATSAPP_ACCESS_TOKEN or PHONE_NUMBER_ID")
    raise ValueError("Please set WHATSAPP_ACCESS_TOKEN and PHONE_NUMBER_ID in .env file")


# Initialize RAG engine and conversation manager
rag_engine = None
conversation_manager = None

try:
    # Initialize RAG engine
    rag_engine = RAGEngine()
    logger.info("RAG engine initialized successfully")
    
    # Initialize conversation manager
    conversation_manager = ConversationManager()
    logger.info("Conversation manager initialized successfully")
    
    # Warm up the engine
    rag_engine.warm_up()
    logger.info("RAG engine warmed up")
    
except Exception as e:
    logger.error(f"Failed to initialize RAG/ConversationManager: {e}")
    # Keep rag_engine and conversation_manager as None if initialization fails

def _finalize_before_link(text: str) -> str:
    """Simple cleanup before adding support link"""
    if not text:
        return text
    
    # Remove context disclaimers
    text = sanitize_response_text(text or "").strip()
    if not text:
        return text
    
    # Simple approach: just ensure it ends with punctuation
    if text and text[-1] not in '.!?':
        # Find the last sentence ending
        last_period = text.rfind('. ')
        last_exclaim = text.rfind('! ')
        last_question = text.rfind('? ')
        last_sentence_end = max([last_period, last_exclaim, last_question])
        
        if last_sentence_end > len(text) * 0.7:  # If we found a sentence ending in the last 30% 
            text = text[:last_sentence_end + 1].strip()
        else:
            # Just add a period
            text = text.rstrip(',;: ') + '.'
    
    return text

def generate_answer(query: str, session_id: str = None) -> str:
    """
    Generate answer using the actual RAG engine with conversation context
    """
    try:
        # If we don't have a session_id, create one for WhatsApp
        if not session_id:
            session_id = f"whatsapp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # If conversation manager is available, use it for context
        if conversation_manager:
            # Process message with conversation manager
            conv_result = conversation_manager.process_message(query, session_id)
            
            # Handle greetings and farewells
            if conv_result['intent'] == 'greeting' and conv_result['confidence'] > 0.7:
                return conv_result['quick_response'] or "Hello! How can I help you today?"
            elif conv_result['intent'] == 'farewell' and conv_result['confidence'] > 0.7:
                return conv_result['quick_response'] or "Goodbye! Take care!"
            
            # Get response style from conversation manager
            response_style = conv_result['response_style']
            
            # Check if we should show support link
            should_show_link = conversation_manager.should_show_support_link(query, conv_result['context'])
        else:
            response_style = "conversational"
            should_show_link = False
            conv_result = None
        
        # Use RAG engine if available
        if rag_engine:
            result = rag_engine.query(query, response_style=response_style)
            response = result.get("response", "I couldn't find an answer to your question.")
        else:
            # Fallback response if RAG is not available
            response = "I'm having trouble accessing my knowledge base right now. Please try again later."
        
        # Clean up response
        response = _finalize_before_link(response)
        
        # Add support link if appropriate
        if should_show_link and conversation_manager:
            link_text = "\n\nFor community support and to connect with others, visit: vitiligosupportgroup.com"
            
            # Ensure response + link fits WhatsApp limit (4000 chars)
            max_response_length = 4000 - len(link_text)
            if len(response) > max_response_length:
                # Truncate at sentence boundary
                truncated = response[:max_response_length]
                last_period = truncated.rfind('. ')
                last_exclaim = truncated.rfind('! ')
                last_question = truncated.rfind('? ')
                best_break = max([last_period, last_exclaim, last_question])
                
                if best_break > 100:
                    response = response[:best_break + 1].strip()
                else:
                    response = truncated.rsplit(' ', 1)[0].strip() + '.'
            
            response += link_text
            
            # Mark that we showed the link
            if conv_result and conv_result.get('context'):
                conv_result['context'].support_link_shown = True
        
        # Add to conversation history if available
        if conversation_manager and conv_result and conv_result.get('context'):
            conv_result['context'].add_message("assistant", response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."


class WhatsAppMessage:
    """Helper class to parse and handle WhatsApp messages"""
    
    @staticmethod
    def parse_message(webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract message details from webhook payload
        Returns: Dict with 'text', 'from', 'message_id' or None if not a text message
        """
        try:
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Check if there are messages
            messages = value.get("messages", [])
            if not messages:
                return None
            
            message = messages[0]
            
            # Only process text messages
            if message.get("type") != "text":
                logger.info(f"Skipping non-text message type: {message.get('type')}")
                return None
            
            return {
                "text": message.get("text", {}).get("body", ""),
                "from": message.get("from", ""),
                "message_id": message.get("id", ""),
                "timestamp": message.get("timestamp", ""),
                "contact_name": value.get("contacts", [{}])[0].get("profile", {}).get("name", "User")
            }
            
        except (IndexError, KeyError) as e:
            logger.error(f"Error parsing message: {e}")
            return None


class WhatsAppSender:
    """Helper class to send WhatsApp messages"""
    
    @staticmethod
    async def send_text_message(to: str, text: str, reply_to_message_id: Optional[str] = None) -> bool:
        """
        Send a text message via WhatsApp Cloud API
        
        Args:
            to: Recipient phone number (with country code, e.g., "1234567890")
            text: Message text to send
            reply_to_message_id: Optional message ID to reply to
            
        Returns:
            bool: True if successful, False otherwise
        """
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }
        
        # Add context if replying to a specific message
        if reply_to_message_id:
            payload["context"] = {"message_id": reply_to_message_id}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    WHATSAPP_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Message sent successfully to {to}")
                    logger.info(f"Response: {response.json()}")
                    return True
                else:
                    logger.error(f"❌ Failed to send message. Status: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False
                    
        except httpx.TimeoutException:
            logger.error("Timeout while sending message to WhatsApp API")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    @staticmethod
    async def mark_as_read(message_id: str) -> bool:
        """Mark a message as read"""
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    WHATSAPP_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "WhatsApp RAG Chatbot",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Webhook verification endpoint for Meta/WhatsApp
    Meta will call this to verify your webhook URL
    """
    logger.info(f"Webhook verification request received")
    logger.info(f"Mode: {hub_mode}, Token: {hub_verify_token}, Challenge: {hub_challenge}")
    
    # Verify the mode and token
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        return PlainTextResponse(content=hub_challenge)
    else:
        logger.error("❌ Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


async def process_message_async(message_data: Dict[str, Any], webhook_body: Dict[str, Any]):
    """
    Process WhatsApp message asynchronously in the background
    This function handles the actual RAG processing and response sending
    """
    try:
        # Log the incoming message to our logger
        msg_logger.log_incoming_message(webhook_body, message_data)
        
        # Log the incoming message
        logger.info(f"💬 Processing message from {message_data['contact_name']} ({message_data['from']}): {message_data['text']}")
        
        # Mark message as read
        await WhatsAppSender.mark_as_read(message_data['message_id'])
        
        # Track processing time
        start_time = time.time()
        
        # Generate response using RAG chatbot with session tracking
        try:
            logger.info(f"🤖 Generating RAG response...")
            # Use phone number as session ID for conversation continuity
            session_id = f"whatsapp_{message_data['from']}"
            chatbot_response = generate_answer(message_data['text'], session_id)
            logger.info(f"🤖 RAG response generated: {chatbot_response[:200]}...")  # Log first 200 chars
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            msg_logger.log_error("RAG_PROCESSING", str(e), related_message_id=message_data['message_id'])
            chatbot_response = "I apologize, but I'm having trouble processing your request right now. Please try again later."
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"⏱️ RAG processing took {processing_time_ms}ms")
        
        # Send the response back to the user
        api_start = time.time()
        success = await WhatsAppSender.send_text_message(
            to=message_data['from'],
            text=chatbot_response,
            reply_to_message_id=message_data['message_id']
        )
        api_time_ms = int((time.time() - api_start) * 1000)
        
        # Log the response
        api_response = {"success": success, "processing_time_ms": processing_time_ms}
        msg_logger.log_response(
            message_data['message_id'], 
            chatbot_response, 
            api_response, 
            success, 
            processing_time_ms
        )
        
        # Log API call
        msg_logger.log_api_call(
            f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages",
            "POST",
            200 if success else 500,
            api_time_ms,
            {"to": message_data['from'], "text": chatbot_response[:100]},
            api_response
        )
        
        if success:
            logger.info(f"✉️ Response sent to {message_data['from']}: {chatbot_response[:100]}...")
        else:
            logger.error(f"Failed to send response to {message_data['from']}")
            
    except Exception as e:
        logger.error(f"Error in async message processing: {e}")
        msg_logger.log_error("ASYNC_PROCESSING", str(e), related_message_id=message_data.get('message_id'))


@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Main webhook endpoint to handle incoming WhatsApp messages
    Now with immediate acknowledgment and duplicate detection
    """
    try:
        # Parse the request body
        body = await request.json()
        logger.info(f"📥 Webhook received: {json.dumps(body, indent=2)}")
        
        # Parse the message
        message_data = WhatsAppMessage.parse_message(body)
        
        if not message_data:
            logger.info("No processable message found in webhook")
            return {"status": "ok"}
        
        # Check for duplicate messages
        message_id = message_data['message_id']
        
        async with message_processing_lock:
            # Check if we've already processed this message
            if message_id in processed_messages:
                logger.info(f"🔁 Duplicate message detected: {message_id}. Ignoring.")
                return {"status": "ok"}  # Acknowledge but don't process
            
            # Mark this message as being processed
            processed_messages[message_id] = datetime.now()
            logger.info(f"📝 New message {message_id} added to processing queue")
        
        # Log that we're starting async processing
        logger.info(f"💬 Incoming message from {message_data['contact_name']} ({message_data['from']}): {message_data['text']}")
        logger.info(f"🚀 Starting background processing for message {message_id}")
        
        # Create background task for processing
        # This allows us to return immediately while processing continues
        asyncio.create_task(process_message_async(message_data, body))
        
        # Return immediately to acknowledge receipt (within 1-2 seconds)
        logger.info(f"✅ Webhook acknowledged for message {message_id}")
        return {"status": "ok"}
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Return 200 to prevent WhatsApp from retrying
        return {"status": "error", "message": str(e)}


@app.post("/test-send")
async def test_send_message(to: str, message: str):
    """
    Test endpoint to manually send a message
    Useful for debugging
    """
    success = await WhatsAppSender.send_text_message(to, message)
    return {"success": success, "to": to, "message": message}


@app.get("/logs/messages")
async def get_message_logs(phone_number: str = None, limit: int = 100):
    """
    Get message history
    
    Args:
        phone_number: Filter by phone number (optional)
        limit: Number of messages to return
    """
    messages = msg_logger.get_message_history(phone_number, limit)
    return {"messages": messages, "count": len(messages)}


@app.get("/logs/stats")
async def get_stats(date: str = None):
    """
    Get daily statistics
    
    Args:
        date: Date in YYYY-MM-DD format (today if not specified)
    """
    stats = msg_logger.get_daily_stats(date)
    return stats


@app.get("/logs/export")
async def export_logs(start_date: str = None, end_date: str = None):
    """
    Export logs to CSV
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    filename = msg_logger.export_to_csv(start_date=start_date, end_date=end_date)
    return {"status": "exported", "filename": filename}


@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    # Start the cleanup task for old message IDs
    asyncio.create_task(cleanup_old_messages())
    logger.info("🧹 Started message ID cleanup task")


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting WhatsApp RAG Chatbot server...")
    logger.info(f"📱 Phone Number ID: {PHONE_NUMBER_ID}")
    logger.info("🔗 Webhook URL: http://localhost:8000/webhook")
    logger.info("💡 Remember to expose this server using ngrok and configure the webhook in Meta Business Platform")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)