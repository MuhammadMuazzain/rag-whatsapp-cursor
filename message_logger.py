"""
WhatsApp Message Logger
Logs all incoming messages, responses, and API interactions to files and database
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MessageLogger:
    """Comprehensive message logging system for WhatsApp interactions"""
    
    def __init__(self, log_dir: str = "whatsapp_logs", db_path: str = "whatsapp_messages.db"):
        """
        Initialize the message logger
        
        Args:
            log_dir: Directory to store log files
            db_path: Path to SQLite database
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different log types
        (self.log_dir / "daily").mkdir(exist_ok=True)
        (self.log_dir / "errors").mkdir(exist_ok=True)
        (self.log_dir / "webhooks").mkdir(exist_ok=True)
        
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for message logging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                from_number TEXT,
                from_name TEXT,
                message_text TEXT,
                response_text TEXT,
                response_status TEXT,
                response_id TEXT,
                processing_time_ms INTEGER,
                error_message TEXT,
                raw_webhook TEXT,
                api_response TEXT
            )
        """)
        
        # Create API calls table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                method TEXT,
                status_code INTEGER,
                response_time_ms INTEGER,
                request_body TEXT,
                response_body TEXT,
                error_message TEXT
            )
        """)
        
        # Create errors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_type TEXT,
                error_code TEXT,
                error_message TEXT,
                related_message_id TEXT,
                full_traceback TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def log_incoming_message(self, webhook_data: Dict[str, Any], parsed_message: Optional[Dict[str, Any]]) -> str:
        """
        Log an incoming WhatsApp message
        
        Args:
            webhook_data: Raw webhook payload
            parsed_message: Parsed message data
            
        Returns:
            Log entry ID
        """
        timestamp = datetime.now()
        
        # Extract message details
        if parsed_message:
            message_id = parsed_message.get("message_id", "unknown")
            from_number = parsed_message.get("from", "unknown")
            from_name = parsed_message.get("contact_name", "unknown")
            message_text = parsed_message.get("text", "")
        else:
            message_id = "unknown"
            from_number = "unknown"
            from_name = "unknown"
            message_text = ""
        
        # Log to daily file
        daily_file = self.log_dir / "daily" / f"{timestamp.strftime('%Y-%m-%d')}.json"
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "type": "incoming_message",
            "message_id": message_id,
            "from_number": from_number,
            "from_name": from_name,
            "message_text": message_text,
            "raw_webhook": webhook_data
        }
        
        self._append_to_json_file(daily_file, log_entry)
        
        # Log to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO messages 
            (message_id, timestamp, from_number, from_name, message_text, raw_webhook)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (message_id, timestamp, from_number, from_name, message_text, json.dumps(webhook_data)))
        conn.commit()
        conn.close()
        
        # Log webhook raw data
        webhook_file = self.log_dir / "webhooks" / f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_{message_id}.json"
        with open(webhook_file, 'w') as f:
            json.dump(webhook_data, f, indent=2)
        
        logger.info(f"Logged incoming message: {message_id} from {from_number}")
        return message_id
    
    def log_response(self, message_id: str, response_text: str, api_response: Dict[str, Any], 
                    success: bool, processing_time_ms: int = 0):
        """
        Log the response sent to a message
        
        Args:
            message_id: Original message ID
            response_text: Text sent as response
            api_response: WhatsApp API response
            success: Whether the send was successful
            processing_time_ms: Time taken to process
        """
        timestamp = datetime.now()
        
        # Update daily log
        daily_file = self.log_dir / "daily" / f"{timestamp.strftime('%Y-%m-%d')}.json"
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "type": "response_sent",
            "message_id": message_id,
            "response_text": response_text,
            "success": success,
            "processing_time_ms": processing_time_ms,
            "api_response": api_response
        }
        
        self._append_to_json_file(daily_file, log_entry)
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        response_id = api_response.get("messages", [{}])[0].get("id", "") if success else ""
        response_status = "sent" if success else "failed"
        
        cursor.execute("""
            UPDATE messages 
            SET response_text = ?, response_status = ?, response_id = ?, 
                processing_time_ms = ?, api_response = ?
            WHERE message_id = ?
        """, (response_text, response_status, response_id, processing_time_ms, 
              json.dumps(api_response), message_id))
        conn.commit()
        conn.close()
        
        logger.info(f"Logged response for message: {message_id}, success: {success}")
    
    def log_error(self, error_type: str, error_message: str, error_code: str = None, 
                  related_message_id: str = None, full_traceback: str = None):
        """
        Log an error
        
        Args:
            error_type: Type of error (API, Processing, etc.)
            error_message: Error message
            error_code: Error code if available
            related_message_id: Related message ID if applicable
            full_traceback: Full error traceback
        """
        timestamp = datetime.now()
        
        # Log to error file
        error_file = self.log_dir / "errors" / f"{timestamp.strftime('%Y-%m-%d')}_errors.json"
        error_entry = {
            "timestamp": timestamp.isoformat(),
            "error_type": error_type,
            "error_code": error_code,
            "error_message": error_message,
            "related_message_id": related_message_id,
            "full_traceback": full_traceback
        }
        
        self._append_to_json_file(error_file, error_entry)
        
        # Log to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO errors 
            (timestamp, error_type, error_code, error_message, related_message_id, full_traceback)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, error_type, error_code, error_message, related_message_id, full_traceback))
        conn.commit()
        conn.close()
        
        logger.error(f"Logged error: {error_type} - {error_message}")
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, 
                    response_time_ms: int, request_body: Dict[str, Any] = None, 
                    response_body: Dict[str, Any] = None, error_message: str = None):
        """
        Log an API call to WhatsApp
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            request_body: Request payload
            response_body: Response payload
            error_message: Error message if any
        """
        timestamp = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_calls 
            (timestamp, endpoint, method, status_code, response_time_ms, 
             request_body, response_body, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, endpoint, method, status_code, response_time_ms,
              json.dumps(request_body) if request_body else None,
              json.dumps(response_body) if response_body else None,
              error_message))
        conn.commit()
        conn.close()
        
        logger.info(f"Logged API call: {method} {endpoint} - Status: {status_code}")
    
    def _append_to_json_file(self, filepath: Path, data: Dict[str, Any]):
        """Append data to a JSON file (as JSON lines format)"""
        with open(filepath, 'a', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')
    
    def get_message_history(self, phone_number: str = None, limit: int = 100) -> list:
        """
        Get message history from database
        
        Args:
            phone_number: Filter by phone number (optional)
            limit: Maximum number of messages to return
            
        Returns:
            List of message records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if phone_number:
            cursor.execute("""
                SELECT * FROM messages 
                WHERE from_number = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (phone_number, limit))
        else:
            cursor.execute("""
                SELECT * FROM messages 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        columns = [description[0] for description in cursor.description]
        messages = []
        for row in cursor.fetchall():
            messages.append(dict(zip(columns, row)))
        
        conn.close()
        return messages
    
    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """
        Get statistics for a specific day
        
        Args:
            date: Date in YYYY-MM-DD format (today if None)
            
        Returns:
            Dictionary with daily statistics
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get message counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total_messages,
                COUNT(DISTINCT from_number) as unique_users,
                COUNT(response_text) as responses_sent,
                SUM(CASE WHEN response_status = 'sent' THEN 1 ELSE 0 END) as successful_responses,
                AVG(processing_time_ms) as avg_processing_time
            FROM messages 
            WHERE DATE(timestamp) = ?
        """, (date,))
        
        stats = cursor.fetchone()
        
        # Get error counts
        cursor.execute("""
            SELECT COUNT(*) as error_count
            FROM errors 
            WHERE DATE(timestamp) = ?
        """, (date,))
        
        errors = cursor.fetchone()
        
        conn.close()
        
        return {
            "date": date,
            "total_messages": stats[0] or 0,
            "unique_users": stats[1] or 0,
            "responses_sent": stats[2] or 0,
            "successful_responses": stats[3] or 0,
            "avg_processing_time_ms": round(stats[4] or 0, 2),
            "error_count": errors[0] or 0
        }
    
    def export_to_csv(self, output_file: str = None, start_date: str = None, end_date: str = None):
        """
        Export message logs to CSV
        
        Args:
            output_file: Output CSV filename
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
        """
        import csv
        
        if not output_file:
            output_file = f"whatsapp_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM messages"
        params = []
        
        if start_date and end_date:
            query += " WHERE DATE(timestamp) BETWEEN ? AND ?"
            params = [start_date, end_date]
        elif start_date:
            query += " WHERE DATE(timestamp) >= ?"
            params = [start_date]
        elif end_date:
            query += " WHERE DATE(timestamp) <= ?"
            params = [end_date]
        
        query += " ORDER BY timestamp"
        
        cursor.execute(query, params)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write headers
            headers = [description[0] for description in cursor.description]
            csv_writer.writerow(headers)
            
            # Write data
            csv_writer.writerows(cursor.fetchall())
        
        conn.close()
        logger.info(f"Exported logs to {output_file}")
        return output_file


# Singleton instance
_logger_instance = None

def get_logger() -> MessageLogger:
    """Get or create the singleton logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = MessageLogger()
    return _logger_instance


if __name__ == "__main__":
    # Test the logger
    logger = get_logger()
    
    # Test logging a message
    test_webhook = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456",
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "1234567890",
                        "id": "test_msg_001",
                        "text": {"body": "Test message"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    
    parsed_msg = {
        "message_id": "test_msg_001",
        "from": "1234567890",
        "contact_name": "Test User",
        "text": "Test message"
    }
    
    # Log incoming message
    msg_id = logger.log_incoming_message(test_webhook, parsed_msg)
    print(f"Logged message: {msg_id}")
    
    # Log response
    logger.log_response(
        msg_id, 
        "Test response", 
        {"messages": [{"id": "resp_001"}]}, 
        True, 
        150
    )
    
    # Get stats
    stats = logger.get_daily_stats()
    print(f"Today's stats: {stats}")
    
    # Get history
    history = logger.get_message_history(limit=5)
    print(f"Recent messages: {len(history)} found")