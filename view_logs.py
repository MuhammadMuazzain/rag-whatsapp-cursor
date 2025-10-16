"""
Simple script to view WhatsApp message logs
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from message_logger import get_logger

def view_recent_messages(limit=10):
    """View recent messages"""
    logger = get_logger()
    messages = logger.get_message_history(limit=limit)
    
    print("\n" + "="*80)
    print(f"RECENT {limit} MESSAGES")
    print("="*80)
    
    for msg in messages:
        print(f"\n📅 {msg['timestamp']}")
        print(f"👤 From: {msg['from_name']} ({msg['from_number']})")
        print(f"💬 Message: {msg['message_text']}")
        print(f"🤖 Response: {msg['response_text']}")
        print(f"✅ Status: {msg['response_status']}")
        if msg['error_message']:
            print(f"❌ Error: {msg['error_message']}")
        print("-"*40)

def view_today_stats():
    """View today's statistics"""
    logger = get_logger()
    stats = logger.get_daily_stats()
    
    print("\n" + "="*80)
    print(f"TODAY'S STATISTICS ({stats['date']})")
    print("="*80)
    print(f"📊 Total Messages: {stats['total_messages']}")
    print(f"👥 Unique Users: {stats['unique_users']}")
    print(f"✉️ Responses Sent: {stats['responses_sent']}")
    print(f"✅ Successful: {stats['successful_responses']}")
    print(f"⏱️ Avg Processing Time: {stats['avg_processing_time_ms']}ms")
    print(f"❌ Errors: {stats['error_count']}")

def view_user_history(phone_number):
    """View history for a specific user"""
    logger = get_logger()
    messages = logger.get_message_history(phone_number=phone_number, limit=50)
    
    print("\n" + "="*80)
    print(f"MESSAGE HISTORY FOR: {phone_number}")
    print("="*80)
    
    for msg in messages:
        print(f"\n📅 {msg['timestamp']}")
        print(f"💬 User: {msg['message_text']}")
        print(f"🤖 Bot: {msg['response_text']}")
        print("-"*40)

def view_errors():
    """View recent errors"""
    conn = sqlite3.connect("whatsapp_messages.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM errors 
        ORDER BY timestamp DESC 
        LIMIT 20
    """)
    
    errors = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*80)
    print("RECENT ERRORS")
    print("="*80)
    
    for error in errors:
        print(f"\n📅 {error[1]}")  # timestamp
        print(f"❌ Type: {error[2]}")  # error_type
        print(f"📝 Message: {error[4]}")  # error_message
        print(f"🔗 Related Message: {error[5]}")  # related_message_id
        print("-"*40)

def export_today_logs():
    """Export today's logs to CSV"""
    logger = get_logger()
    today = datetime.now().strftime('%Y-%m-%d')
    filename = logger.export_to_csv(start_date=today, end_date=today)
    print(f"\n✅ Exported today's logs to: {filename}")

def main():
    """Main menu"""
    while True:
        print("\n" + "="*80)
        print("WHATSAPP MESSAGE LOGGER VIEWER")
        print("="*80)
        print("1. View Recent Messages")
        print("2. View Today's Statistics")
        print("3. View User History")
        print("4. View Recent Errors")
        print("5. Export Today's Logs to CSV")
        print("6. Exit")
        print("-"*80)
        
        choice = input("Select option (1-6): ")
        
        if choice == "1":
            limit = input("How many messages? (default 10): ") or "10"
            view_recent_messages(int(limit))
        elif choice == "2":
            view_today_stats()
        elif choice == "3":
            phone = input("Enter phone number (with country code): ")
            view_user_history(phone)
        elif choice == "4":
            view_errors()
        elif choice == "5":
            export_today_logs()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()