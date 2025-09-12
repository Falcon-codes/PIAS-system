"""
Production database configuration for PIAS
SQLite database for user sessions and data persistence
"""

import sqlite3
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class PIASDatabase:
    """Simple SQLite database for PIAS production deployment"""
    
    def __init__(self, db_path: str = "pias.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    filename TEXT,
                    total_products INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    company TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    session_id TEXT,
                    user_email TEXT,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def store_session(self, session_id: str, data: Dict[str, Any], 
                     filename: str = None, expires_hours: int = 24) -> bool:
        """Store session data"""
        try:
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            total_products = 0
            
            # Extract product count if available
            if 'kpis' in data and 'totalProducts' in data['kpis']:
                total_products = data['kpis']['totalProducts']
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (session_id, data, expires_at, filename, total_products)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, json.dumps(data), expires_at, filename, total_products))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Database error storing session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT data FROM sessions 
                    WHERE session_id = ? AND expires_at > CURRENT_TIMESTAMP
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
            
            return None
        except Exception as e:
            print(f"Database error retrieving session: {e}")
            return None
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM sessions WHERE expires_at <= CURRENT_TIMESTAMP
                """)
                deleted = cursor.rowcount
                conn.commit()
                
                if deleted > 0:
                    print(f"Cleaned up {deleted} expired sessions")
                    
        except Exception as e:
            print(f"Database error during cleanup: {e}")
    
    def store_user(self, email: str, name: str, company: str = None) -> bool:
        """Store user information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO users (email, name, company, last_login)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (email, name, company))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Database error storing user: {e}")
            return False
    
    def log_analytics(self, event_type: str, session_id: str = None, 
                     user_email: str = None, data: Dict[str, Any] = None):
        """Log analytics events"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO analytics (event_type, session_id, user_email, data)
                    VALUES (?, ?, ?, ?)
                """, (event_type, session_id, user_email, 
                     json.dumps(data) if data else None))
                conn.commit()
        except Exception as e:
            print(f"Analytics logging error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Session stats
                cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > CURRENT_TIMESTAMP")
                active_sessions = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT SUM(total_products) FROM sessions WHERE expires_at > CURRENT_TIMESTAMP")
                result = cursor.fetchone()[0]
                total_products = result if result else 0
                
                return {
                    'active_sessions': active_sessions,
                    'total_users': total_users,
                    'total_products_analyzed': total_products,
                    'database_path': self.db_path
                }
        except Exception as e:
            print(f"Stats error: {e}")
            return {}

# Global database instance
db = PIASDatabase()

# Helper functions for backward compatibility
def get_session_data(session_id: str) -> Dict[str, Any]:
    """Get session data - backward compatible"""
    result = db.get_session(session_id)
    return result if result else {}

def set_session_data(session_id: str, data: Dict[str, Any], filename: str = None):
    """Set session data - backward compatible"""
    db.store_session(session_id, data, filename)
