# WhatsApp Cloud API Setup Instructions

## Prerequisites

1. **Meta Business Account**: Create one at https://business.facebook.com
2. **WhatsApp Business App**: Set up in Meta Business Platform
3. **Python 3.8+** installed
4. **Ngrok** installed for local testing: https://ngrok.com/download

## Installation

### 1. Install Dependencies

```bash
pip install fastapi uvicorn httpx python-dotenv
```

### 2. Configure Environment Variables

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
   - `WHATSAPP_ACCESS_TOKEN`: Get from Meta Business Settings > System Users
   - `PHONE_NUMBER_ID`: Get from WhatsApp > API Setup in Meta Business Platform
   - `VERIFY_TOKEN`: Choose a secure string (you'll use this in webhook config)

## Running the Server

### 1. Start the FastAPI Server

```bash
python whatsapp_cloud_api.py
```

The server will start on `http://localhost:8000`

### 2. Expose with Ngrok

In a new terminal, run:
```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

## Meta Webhook Configuration

### 1. Configure Webhook in Meta Business Platform

1. Go to **Meta Business Platform** > **WhatsApp** > **Configuration**
2. Click **Edit** next to Webhook
3. Enter:
   - **Callback URL**: `https://your-ngrok-url.ngrok.io/webhook`
   - **Verify Token**: The same value from your `.env` file
4. Click **Verify and Save**

### 2. Subscribe to Webhook Fields

After verification, subscribe to:
- `messages` (required)
- `message_status` (optional, for delivery receipts)

## Testing

### Method 1: WhatsApp Test Number

1. In Meta Business Platform, go to **WhatsApp** > **API Setup**
2. Add your phone number to **Test numbers**
3. Send a message to the WhatsApp Business number
4. Check server logs for incoming/outgoing messages

### Method 2: Manual Test Endpoint

Send a test message using the API:

```bash
curl -X POST http://localhost:8000/test-send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "1234567890",
    "message": "Hello from the API!"
  }'
```

### Method 3: WhatsApp Sandbox (Development)

1. Go to **WhatsApp** > **Getting Started** in Meta Business Platform
2. Follow sandbox setup instructions
3. Send the join code to the sandbox number
4. Test messages with the sandbox

## Production Deployment

### 1. Deploy to Cloud Provider

Options:
- **AWS EC2/Lambda**: Use Application Load Balancer for HTTPS
- **Google Cloud Run**: Automatic HTTPS with Cloud Run URL
- **Heroku**: One-click deploy with HTTPS included
- **DigitalOcean App Platform**: Easy deployment with HTTPS

### 2. Update Webhook URL

Replace ngrok URL with your production URL:
- Go to Meta Business Platform > WhatsApp > Configuration
- Update webhook URL to `https://your-domain.com/webhook`

### 3. SSL Certificate

Ensure your production server has a valid SSL certificate (Let's Encrypt is free)

## Monitoring & Debugging

### Check Logs

The server logs every:
- Incoming webhook request
- Message parsing
- RAG processing
- Outgoing API calls
- Success/failure status

### Common Issues

1. **Webhook Verification Fails**
   - Check `VERIFY_TOKEN` matches in both `.env` and Meta config
   - Ensure ngrok is running and URL is correct

2. **Messages Not Received**
   - Verify webhook is subscribed to `messages` field
   - Check phone number is added to test numbers
   - Ensure ngrok tunnel is active

3. **Messages Not Sending**
   - Verify `WHATSAPP_ACCESS_TOKEN` is valid
   - Check `PHONE_NUMBER_ID` is correct
   - Ensure recipient number includes country code

4. **RAG Integration Issues**
   - Ensure your `generate_answer()` function is imported correctly
   - Check RAG dependencies are installed
   - Verify RAG model/data is loaded

## API Endpoints

- `GET /`: Health check
- `GET /webhook`: Webhook verification (Meta calls this)
- `POST /webhook`: Receive WhatsApp messages
- `POST /test-send`: Manual message sending for testing

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use environment variables** in production
3. **Implement rate limiting** for production
4. **Add request validation** for webhook payloads
5. **Use webhook signature verification** (optional but recommended)
6. **Rotate access tokens** regularly

## Support

For WhatsApp Cloud API issues:
- [WhatsApp Business Platform Documentation](https://developers.facebook.com/docs/whatsapp)
- [Meta Business Help Center](https://www.facebook.com/business/help)

For FastAPI issues:
- [FastAPI Documentation](https://fastapi.tiangolo.com)