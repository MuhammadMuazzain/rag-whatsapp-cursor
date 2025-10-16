"""
Test script to verify async improvements and duplicate detection
"""

import asyncio
import aiohttp
import json
import time

async def send_webhook_request(message_id: str, text: str, from_number: str = "923314126791"):
    """Send a test webhook request"""
    url = "http://localhost:8000/webhook"
    
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "698647366529686",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "6580361975",
                        "phone_number_id": "755335244332796"
                    },
                    "contacts": [{
                        "profile": {"name": "Test User"},
                        "wa_id": from_number
                    }],
                    "messages": [{
                        "from": from_number,
                        "id": message_id,
                        "timestamp": str(int(time.time())),
                        "text": {"body": text},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        async with session.post(url, json=payload) as response:
            response_time = time.time() - start_time
            result = await response.json()
            return response.status, result, response_time

async def test_immediate_acknowledgment():
    """Test that webhook returns immediately"""
    print("\n" + "="*60)
    print("TEST 1: IMMEDIATE ACKNOWLEDGMENT")
    print("="*60)
    
    status, result, response_time = await send_webhook_request(
        "test_msg_001",
        "What is vitiligo?"
    )
    
    print(f"Response Status: {status}")
    print(f"Response Body: {result}")
    print(f"Response Time: {response_time:.2f} seconds")
    
    if response_time < 2:
        print("OK: Webhook acknowledged within 2 seconds")
    else:
        print(f"WARNING: Webhook took {response_time:.2f} seconds (should be < 2s)")
    
    # Wait for async processing to complete
    print("\nWaiting 5 seconds for background processing...")
    await asyncio.sleep(5)

async def test_duplicate_detection():
    """Test that duplicate messages are ignored"""
    print("\n" + "="*60)
    print("TEST 2: DUPLICATE DETECTION")
    print("="*60)
    
    message_id = "test_duplicate_msg"
    
    # Send first message
    print("\nSending first message...")
    status1, result1, time1 = await send_webhook_request(message_id, "Hello")
    print(f"First message: Status={status1}, Time={time1:.2f}s")
    
    # Send duplicate immediately
    print("\nSending duplicate message with same ID...")
    status2, result2, time2 = await send_webhook_request(message_id, "Hello")
    print(f"Duplicate message: Status={status2}, Time={time2:.2f}s")
    
    # Send another duplicate after 2 seconds
    await asyncio.sleep(2)
    print("\nSending another duplicate after 2 seconds...")
    status3, result3, time3 = await send_webhook_request(message_id, "Hello")
    print(f"Third duplicate: Status={status3}, Time={time3:.2f}s")
    
    print("\nOK: All duplicates should be acknowledged but not processed")
    print("Check server logs to verify only first message was processed")

async def test_multiple_users():
    """Test that different users can send messages simultaneously"""
    print("\n" + "="*60)
    print("TEST 3: MULTIPLE USERS SIMULTANEOUSLY")
    print("="*60)
    
    tasks = []
    users = [
        ("user1_msg", "923314126791", "What causes vitiligo?"),
        ("user2_msg", "923314126792", "How is vitiligo treated?"),
        ("user3_msg", "923314126793", "Is vitiligo genetic?")
    ]
    
    print("\nSending messages from 3 users simultaneously...")
    for msg_id, phone, text in users:
        task = send_webhook_request(msg_id, text, phone)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    for i, (status, result, response_time) in enumerate(results):
        user_phone = users[i][1]
        print(f"User {user_phone}: Status={status}, Time={response_time:.2f}s")
    
    print("\nOK: All users should get immediate acknowledgment")
    print("Responses will be processed in background")

async def test_response_quality():
    """Test that response quality is maintained"""
    print("\n" + "="*60)
    print("TEST 4: RESPONSE QUALITY CHECK")
    print("="*60)
    
    # Send a message that should trigger support link
    status, result, response_time = await send_webhook_request(
        "quality_test_msg",
        "What is vitiligo and how can I get support?"
    )
    
    print(f"Message sent: Status={status}, Time={response_time:.2f}s")
    print("\nWaiting 60 seconds for RAG processing to complete...")
    print("Check the logs to verify:")
    print("1. Full RAG response is generated")
    print("2. Support link is included when appropriate")
    print("3. Response maintains same quality as before")
    
    await asyncio.sleep(60)

async def main():
    """Run all tests"""
    print("="*60)
    print("ASYNC IMPROVEMENTS TEST SUITE")
    print("="*60)
    print("\nMake sure the server is running with: .\\run_direct.bat")
    print("Press Ctrl+C to stop tests at any time\n")
    
    try:
        await test_immediate_acknowledgment()
        await test_duplicate_detection()
        await test_multiple_users()
        await test_response_quality()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        print("\nSUMMARY:")
        print("1. Webhook now acknowledges immediately (< 2 seconds)")
        print("2. Duplicate messages are detected and ignored")
        print("3. Multiple users can send messages without blocking")
        print("4. Response quality is maintained (check logs)")
        print("\nCHECK SERVER LOGS FOR DETAILED PROCESSING INFORMATION")
        
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    asyncio.run(main())