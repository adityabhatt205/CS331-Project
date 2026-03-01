"""
Database module for the Factory Floor System.
Provides SQLite database operations with proper connection management and migrations.
"""

import sqlite3
import os
import logging
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
from threading import Lock


class Database:
    """SQLite database manager with connection pooling and migration support."""
    
    def __init__(self, db_path: str = "factory_floor.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection_lock = Lock()
        self._logger = logging.getLogger(__name__)
        self.initialize_database()
    
    def initialize_database(self) -> None:
        """Initialize database with required tables."""
        try:
            with self.get_connection() as conn:
                self._create_tables(conn)
                self._logger.info("Database initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all required database tables."""
        
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP NULL
            )
        """)
        
        # Sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                login_time TIMESTAMP NOT NULL,
                last_activity TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Audit log table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 1
            )
        """)
        
        # System settings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                description TEXT,
                updated_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")  
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
        
        conn.commit()
    
    @contextmanager
    def get_connection(self):
        """
        Get database connection with proper cleanup.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            with self._connection_lock:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=30.0,
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                conn.execute("PRAGMA foreign_keys=ON")  # Enable foreign key constraints
                conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
                yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self._logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = (), fetch: bool = False) -> Optional[List[sqlite3.Row]]:
        """
        Execute a SQL query safely.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch and return results
            
        Returns:
            Query results if fetch=True, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch:
                    return cursor.fetchall()
                
                conn.commit()
                return None
                
        except Exception as e:
            self._logger.error(f"Query execution failed: {query}, Error: {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """
        Execute a SQL query with multiple parameter sets.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                
        except Exception as e:
            self._logger.error(f"Batch execution failed: {query}, Error: {e}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        query = "SELECT * FROM users WHERE username = ? AND is_active = 1"
        result = self.execute_query(query, (username,), fetch=True)
        return dict(result[0]) if result else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE user_id = ? AND is_active = 1"
        result = self.execute_query(query, (user_id,), fetch=True)
        return dict(result[0]) if result else None
    
    def create_user(self, user_data: Dict) -> bool:
        """Create a new user."""
        query = """
            INSERT INTO users (user_id, username, password_hash, salt, role, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        try:
            self.execute_query(query, (
                user_data['user_id'],
                user_data['username'], 
                user_data['password_hash'],
                user_data['salt'],
                user_data['role']
            ))
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_user_password(self, user_id: int, password_hash: str, salt: str) -> bool:
        """Update user password."""
        query = "UPDATE users SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
        try:
            self.execute_query(query, (password_hash, salt, user_id))
            return True
        except Exception:
            return False
    
    def update_user_login(self, user_id: int, success: bool = True) -> None:
        """Update user login information."""
        if success:
            query = """
                UPDATE users SET 
                    last_login = CURRENT_TIMESTAMP,
                    failed_login_attempts = 0,
                    locked_until = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """
        else:
            query = """
                UPDATE users SET 
                    failed_login_attempts = failed_login_attempts + 1,
                    locked_until = CASE 
                        WHEN failed_login_attempts >= 4 THEN datetime('now', '+30 minutes')
                        ELSE locked_until 
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """
        
        self.execute_query(query, (user_id,))
    
    def delete_user(self, user_id: int) -> bool:
        """Soft delete a user."""
        query = "UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
        try:
            self.execute_query(query, (user_id,))
            return True
        except Exception:
            return False
    
    def list_users(self) -> List[Dict]:
        """List all active users."""
        query = "SELECT user_id, username, role, created_at, last_login FROM users WHERE is_active = 1"
        results = self.execute_query(query, fetch=True)
        return [dict(row) for row in results] if results else []
    
    def create_session(self, session_data: Dict) -> bool:
        """Create a new session."""
        query = """
            INSERT INTO sessions (session_id, user_id, username, role, login_time, 
                                last_activity, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            self.execute_query(query, (
                session_data['session_id'],
                session_data['user_id'],
                session_data['username'],
                session_data['role'],
                session_data['login_time'],
                session_data['last_activity'],
                session_data['expires_at'],
                session_data.get('ip_address'),
                session_data.get('user_agent')
            ))
            return True
        except Exception:
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        query = "SELECT * FROM sessions WHERE session_id = ? AND is_active = 1"
        result = self.execute_query(query, (session_id,), fetch=True)
        return dict(result[0]) if result else None
    
    def update_session_activity(self, session_id: str) -> None:
        """Update session last activity."""
        query = "UPDATE sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_id = ?"
        self.execute_query(query, (session_id,))
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        query = "UPDATE sessions SET is_active = 0 WHERE session_id = ?"
        try:
            self.execute_query(query, (session_id,))
            return True
        except Exception:
            return False
    
    def invalidate_user_sessions(self, user_id: int) -> None:
        """Invalidate all sessions for a user."""
        query = "UPDATE sessions SET is_active = 0 WHERE user_id = ?"
        self.execute_query(query, (user_id,))
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        query = "UPDATE sessions SET is_active = 0 WHERE expires_at < CURRENT_TIMESTAMP"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    
    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions."""
        query = """
            SELECT session_id, user_id, username, role, login_time, last_activity, expires_at 
            FROM sessions 
            WHERE is_active = 1 AND expires_at > CURRENT_TIMESTAMP
        """
        results = self.execute_query(query, fetch=True)
        return [dict(row) for row in results] if results else []
    
    def log_audit_event(self, user_id: Optional[int], username: str, action: str, 
                       resource: Optional[str] = None, details: Optional[str] = None,
                       ip_address: Optional[str] = None, success: bool = True) -> None:
        """Log an audit event."""
        query = """
            INSERT INTO audit_log (user_id, username, action, resource, details, ip_address, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            self.execute_query(query, (user_id, username, action, resource, details, ip_address, success))
        except Exception as e:
            self._logger.error(f"Failed to log audit event: {e}")
    
    def get_audit_logs(self, user_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get audit logs."""
        if user_id:
            query = "SELECT * FROM audit_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?"
            params = (user_id, limit)
        else:
            query = "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)
        
        results = self.execute_query(query, params, fetch=True)
        return [dict(row) for row in results] if results else []
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup."""
        try:
            with self.get_connection() as source:
                backup = sqlite3.connect(backup_path)
                source.backup(backup)
                backup.close()
            return True
        except Exception as e:
            self._logger.error(f"Database backup failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        stats = {}
        
        try:
            # User stats
            result = self.execute_query("SELECT COUNT(*) as count FROM users WHERE is_active = 1", fetch=True)
            stats['total_users'] = result[0]['count'] if result else 0
            
            # Session stats
            result = self.execute_query("SELECT COUNT(*) as count FROM sessions WHERE is_active = 1", fetch=True)
            stats['active_sessions'] = result[0]['count'] if result else 0
            
            # Audit log stats
            result = self.execute_query("SELECT COUNT(*) as count FROM audit_log", fetch=True)
            stats['total_audit_logs'] = result[0]['count'] if result else 0
            
            # Database file size
            if os.path.exists(self.db_path):
                stats['database_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            
        except Exception as e:
            self._logger.error(f"Failed to get database stats: {e}")
        
        return stats


# Global database instance
db = Database()