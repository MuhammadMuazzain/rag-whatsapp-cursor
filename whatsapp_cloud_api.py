"""
WhatsApp Cloud API Integration for RAG Chatbot
FastAPI backend to handle WhatsApp messages and respond using a RAG chatbot
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import json

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


# Import your existing RAG function
try:
    from rag import RAGEngine
    rag_engine = RAGEngine()
    logger.info("RAG engine imported and initialized successfully")
    
    def generate_answer(query: str) -> str:
        """Use your existing RAG engine to generate answers"""
        try:
            result = rag_engine.query(query)
            return result.get("response", "I couldn't find an answer to your question.")
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return "I'm having trouble processing your question right now. Please try again."
except ImportError as e:
    logger.warning(f"RAG engine not found: {e}. Using placeholder function.")
    # Placeholder if your RAG is not available
    def generate_answer(query: str) -> str:
        """
        Your existing RAG chatbot function.
        Replace this with your actual implementation.
        """
        # Provide some basic responses for testing
        responses = {
            "vitiligo": "Vitiligo is a skin condition where patches of skin lose their pigment. It occurs when melanocytes (pigment-producing cells) die or stop functioning.",
            "hello": "Hello! I'm your WhatsApp assistant. How can I help you today?",
            "hi": "Hi there! How can I assist you?",
        }
        
        # Check for keywords
        query_lower = query.lower()
        for keyword, response in responses.items():
            if keyword in query_lower:
                return response
        
        return "I'm here to help! Please ask me about vitiligo or any health-related questions."


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


@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Main webhook endpoint to handle incoming WhatsApp messages
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
        
        # Log the incoming message
        logger.info(f"💬 Incoming message from {message_data['contact_name']} ({message_data['from']}): {message_data['text']}")
        
        # Mark message as read
        await WhatsAppSender.mark_as_read(message_data['message_id'])
        
        # Generate response using RAG chatbot
        try:
            logger.info(f"🤖 Generating RAG response...")
            chatbot_response = generate_answer(message_data['text'])
            logger.info(f"🤖 RAG response: {chatbot_response}")
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            chatbot_response = "I apologize, but I'm having trouble processing your request right now. Please try again later."
        
        # Send the response back to the user
        success = await WhatsAppSender.send_text_message(
            to=message_data['from'],
            text=chatbot_response,
            reply_to_message_id=message_data['message_id']
        )
        
        if success:
            logger.info(f"✉️ Response sent to {message_data['from']}: {chatbot_response[:100]}...")
        else:
            logger.error(f"Failed to send response to {message_data['from']}")
        
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


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting WhatsApp RAG Chatbot server...")
    logger.info(f"📱 Phone Number ID: {PHONE_NUMBER_ID}")
    logger.info("🔗 Webhook URL: http://localhost:8000/webhook")
    logger.info("💡 Remember to expose this server using ngrok and configure the webhook in Meta Business Platform")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)