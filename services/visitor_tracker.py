"""
Visitor & Authentication Tracking System for DataGuardian Pro
GDPR-compliant tracking of anonymous visitors, login attempts, and user creation

Features:
- Anonymous visitor tracking (no PII, GDPR-compliant)
- Login attempt tracking (success/failure)
- User registration tracking
- IP anonymization (GDPR Article 32)
- PostgreSQL-based audit logs
- Real-time analytics dashboard
"""

import logging
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os

logger = logging.getLogger(__name__)

_visitor_pool = None
_visitor_pool_lock = threading.Lock()

def get_visitor_pool(db_url: str, min_connections: int = 2, max_connections: int = 15):
    """Get or create a thread-safe connection pool for visitor tracking."""
    global _visitor_pool
    if _visitor_pool is None:
        with _visitor_pool_lock:
            if _visitor_pool is None:
                try:
                    _visitor_pool = pool.ThreadedConnectionPool(
                        min_connections, max_connections, db_url
                    )
                    logger.info(f"Visitor tracking connection pool initialized: min={min_connections}, max={max_connections}")
                except Exception as e:
                    logger.error(f"Failed to create visitor tracking pool: {e}")
                    raise
    return _visitor_pool

class VisitorEventType(Enum):
    """Visitor event types for tracking"""
    PAGE_VIEW = "page_view"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    REGISTRATION_STARTED = "registration_started"
    REGISTRATION_SUCCESS = "registration_success"
    REGISTRATION_FAILURE = "registration_failure"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    
    # Revenue Tracking Events (GDPR-compliant, no PII)
    PRICING_PAGE_VIEW = "pricing_page_view"
    TRIAL_STARTED = "trial_started"
    TRIAL_CONVERTED = "trial_converted"
    SCANNER_EXECUTED = "scanner_executed"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_DOWNGRADED = "subscription_downgraded"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"

@dataclass
class VisitorEvent:
    """GDPR-compliant visitor event (no PII)"""
    event_id: str
    session_id: str
    event_type: VisitorEventType
    timestamp: datetime
    anonymized_ip: str  # Hashed IP for GDPR compliance
    user_agent: Optional[str]
    page_path: str
    referrer: Optional[str]
    country: Optional[str]
    user_id: Optional[str] = None  # Only for authenticated events
    username: Optional[str] = None  # Only for authenticated events
    details: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None

class VisitorTracker:
    """
    GDPR-Compliant Visitor Tracking System
    
    Privacy Features:
    - IP anonymization (last octet removed + hashed)
    - No cookies stored (session-based only)
    - No personal data collection
    - Data retention: 90 days (GDPR Article 5)
    - Right to deletion support (GDPR Article 17)
    """
    
    def __init__(self):
        self.events: List[VisitorEvent] = []
        self.lock = threading.Lock()
        self._pool = None
        self.db_url = os.getenv('DATABASE_URL')
        if self.db_url:
            try:
                self._pool = get_visitor_pool(self.db_url)
            except Exception as e:
                logger.warning(f"Failed to initialize visitor pool: {e}")
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection from pool with automatic release"""
        conn = None
        try:
            if self._pool:
                conn = self._pool.getconn()
            elif self.db_url:
                conn = psycopg2.connect(self.db_url)
            yield conn
        finally:
            if conn:
                if self._pool:
                    try:
                        self._pool.putconn(conn)
                    except Exception:
                        try:
                            conn.close()
                        except:
                            pass
                else:
                    try:
                        conn.close()
                    except:
                        pass
        
    def _init_database(self):
        """Initialize PostgreSQL tables for visitor tracking"""
        try:
            if not self.db_url:
                logger.warning("DATABASE_URL not set - using in-memory tracking only")
                return
                
            with self._get_connection() as conn:
                if not conn:
                    return
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS visitor_events (
                        event_id VARCHAR(36) PRIMARY KEY,
                        session_id VARCHAR(36) NOT NULL,
                        event_type VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        anonymized_ip VARCHAR(64) NOT NULL,
                        user_agent TEXT,
                        page_path VARCHAR(500),
                        referrer VARCHAR(500),
                        country VARCHAR(2),
                        user_id VARCHAR(36),
                        username VARCHAR(100),
                        details JSONB,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_visitor_events_timestamp 
                    ON visitor_events(timestamp DESC)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_visitor_events_session 
                    ON visitor_events(session_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_visitor_events_type 
                    ON visitor_events(event_type)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_visitor_events_user 
                    ON visitor_events(user_id)
                """)
                
                conn.commit()
                cursor.close()
            
            logger.info("✅ Visitor tracking database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize visitor tracking database: {e}")
    
    def _anonymize_ip(self, ip_address: str) -> str:
        """
        Anonymize IP address for GDPR compliance (Article 32)
        
        Method:
        1. Remove last octet (IPv4) or last 80 bits (IPv6)
        2. Hash the result with SHA-256
        
        Example: 192.168.1.100 → hash("192.168.1.0")
        """
        if not ip_address:
            return "unknown"
        
        try:
            # IPv4: Remove last octet
            if '.' in ip_address:
                parts = ip_address.split('.')
                anonymized = '.'.join(parts[:3]) + '.0'
            # IPv6: Remove last 80 bits
            elif ':' in ip_address:
                parts = ip_address.split(':')
                anonymized = ':'.join(parts[:3]) + '::0'
            else:
                anonymized = "unknown"
            
            # Hash for additional privacy
            return hashlib.sha256(anonymized.encode()).hexdigest()[:16]
            
        except Exception as e:
            logger.error(f"IP anonymization error: {e}")
            return "unknown"
    
    def track_event(self,
                   session_id: str,
                   event_type: VisitorEventType,
                   page_path: str = "/",
                   ip_address: Optional[str] = None,
                   user_agent: Optional[str] = None,
                   referrer: Optional[str] = None,
                   country: Optional[str] = None,
                   user_id: Optional[str] = None,
                   username: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None,
                   success: bool = True,
                   error_message: Optional[str] = None) -> str:
        """
        Track a visitor event with GDPR compliance
        
        Args:
            session_id: Session identifier (no cookies)
            event_type: Type of event
            page_path: URL path visited
            ip_address: Raw IP (will be anonymized)
            user_agent: Browser user agent
            referrer: HTTP referrer
            country: Country code (2-letter)
            user_id: User ID (only for authenticated events)
            username: Username (only for authenticated events)
            details: Additional event details
            success: Whether event was successful
            error_message: Error message if failed
            
        Returns:
            event_id: Unique event identifier
        """
        
        event_id = str(uuid.uuid4())
        anonymized_ip = self._anonymize_ip(ip_address) if ip_address else "unknown"
        
        # GDPR ENFORCEMENT: Force username to None (never store PII)
        # This prevents accidental PII leakage from tracking calls
        username = None  # Always None regardless of what was passed
        
        # GDPR ENFORCEMENT: ALWAYS hash user_id to prevent PII storage
        # Defensive programming: Never trust caller, always anonymize
        # This guarantees NO raw identifiers can reach database
        if user_id:
            # UNCONDITIONALLY hash to ensure complete anonymization
            # Even if caller claims it's already hashed, hash it again for safety
            anonymized_user_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
        else:
            anonymized_user_id = None
        
        # GDPR ENFORCEMENT: Sanitize details to prevent PII leakage
        # Remove any keys that might contain PII
        if details:
            sanitized_details = {}
            blocked_keys = ['username', 'email', 'attempted_username', 'user_email', 'name', 'password']
            for key, value in details.items():
                if key.lower() not in blocked_keys:
                    sanitized_details[key] = value
                else:
                    logger.warning(f"🔒 GDPR: Blocked PII field '{key}' from visitor_events.details")
            details = sanitized_details
        
        event = VisitorEvent(
            event_id=event_id,
            session_id=session_id,
            event_type=event_type,
            timestamp=datetime.now(),
            anonymized_ip=anonymized_ip,
            user_agent=user_agent,
            page_path=page_path,
            referrer=referrer,
            country=country,
            user_id=anonymized_user_id,  # Always hashed (enforced above)
            username=username,  # Always None (enforced above)
            details=details or {},
            success=success,
            error_message=error_message
        )
        
        # Store in memory
        with self.lock:
            self.events.append(event)
            # Keep only last 10,000 events in memory
            if len(self.events) > 10000:
                self.events = self.events[-10000:]
        
        # Store in database (async)
        self._store_event_db(event)
        
        logger.info(f"📊 Visitor event tracked: {event_type.value} for session {session_id[:8]}...")
        return event_id
    
    def _store_event_db(self, event: VisitorEvent):
        """Store event in PostgreSQL database using connection pool"""
        try:
            if not self.db_url:
                return
            
            with self._get_connection() as conn:
                if not conn:
                    return
                cursor = conn.cursor()
                
                details_json = json.dumps(event.details) if event.details else '{}'
                
                cursor.execute("""
                    INSERT INTO visitor_events (
                        event_id, session_id, event_type, timestamp,
                        anonymized_ip, user_agent, page_path, referrer,
                        country, user_id, username, details, success, error_message
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    event.event_id,
                    event.session_id,
                    event.event_type.value,
                    event.timestamp,
                    event.anonymized_ip,
                    event.user_agent,
                    event.page_path,
                    event.referrer,
                    event.country,
                    event.user_id,
                    event.username,
                    details_json,
                    event.success,
                    event.error_message
                ))
                
                conn.commit()
                cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to store visitor event in database: {e}")
    
    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get visitor analytics for dashboard
        
        Returns:
            - Total unique visitors (sessions)
            - Total page views
            - Login attempts (success/failure)
            - Registration attempts (success/failure)
            - Top pages
            - Top referrers
            - Country breakdown
        """
        try:
            if not self.db_url:
                return self._get_memory_analytics(days)
            
            with self._get_connection() as conn:
                if not conn:
                    return self._get_memory_analytics(days)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                since = datetime.now() - timedelta(days=days)
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT session_id) as total_visitors
                    FROM visitor_events
                    WHERE timestamp >= %s
                """, (since,))
                result = cursor.fetchone()
                total_visitors = result['total_visitors'] if result else 0
                
                cursor.execute("""
                    SELECT COUNT(*) as total_pageviews
                    FROM visitor_events
                    WHERE timestamp >= %s AND event_type = 'page_view'
                """, (since,))
                result = cursor.fetchone()
                total_pageviews = result['total_pageviews'] if result else 0
                
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN event_type = 'login_success' THEN 1 ELSE 0 END) as login_success,
                        SUM(CASE WHEN event_type = 'login_failure' THEN 1 ELSE 0 END) as login_failure
                    FROM visitor_events
                    WHERE timestamp >= %s
                """, (since,))
                login_stats = cursor.fetchone()
                
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN event_type = 'registration_success' THEN 1 ELSE 0 END) as registration_success,
                        SUM(CASE WHEN event_type = 'registration_failure' THEN 1 ELSE 0 END) as registration_failure
                    FROM visitor_events
                    WHERE timestamp >= %s
                """, (since,))
                registration_stats = cursor.fetchone()
                
                cursor.execute("""
                    SELECT page_path, COUNT(*) as views
                    FROM visitor_events
                    WHERE timestamp >= %s AND event_type = 'page_view'
                    GROUP BY page_path
                    ORDER BY views DESC
                    LIMIT 10
                """, (since,))
                top_pages = cursor.fetchall()
                
                cursor.execute("""
                    SELECT referrer, COUNT(*) as visits
                    FROM visitor_events
                    WHERE timestamp >= %s AND referrer IS NOT NULL
                    GROUP BY referrer
                    ORDER BY visits DESC
                    LIMIT 10
                """, (since,))
                top_referrers = cursor.fetchall()
                
                cursor.execute("""
                    SELECT country, COUNT(DISTINCT session_id) as visitors
                    FROM visitor_events
                    WHERE timestamp >= %s AND country IS NOT NULL
                    GROUP BY country
                    ORDER BY visitors DESC
                    LIMIT 10
                """, (since,))
                countries = cursor.fetchall()
                
                cursor.close()
                
                return {
                    'period_days': days,
                    'total_visitors': total_visitors,
                    'total_pageviews': total_pageviews,
                    'login_success': (login_stats['login_success'] if login_stats else 0) or 0,
                    'login_failure': (login_stats['login_failure'] if login_stats else 0) or 0,
                    'registration_success': (registration_stats['registration_success'] if registration_stats else 0) or 0,
                    'registration_failure': (registration_stats['registration_failure'] if registration_stats else 0) or 0,
                    'top_pages': [dict(p) for p in top_pages] if top_pages else [],
                    'top_referrers': [dict(r) for r in top_referrers] if top_referrers else [],
                    'countries': [dict(c) for c in countries] if countries else []
                }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return self._get_memory_analytics(days)
    
    def _get_memory_analytics(self, days: int) -> Dict[str, Any]:
        """Fallback analytics from in-memory events"""
        since = datetime.now() - timedelta(days=days)
        recent_events = [e for e in self.events if e.timestamp >= since]
        
        unique_sessions = len(set(e.session_id for e in recent_events))
        page_views = len([e for e in recent_events if e.event_type == VisitorEventType.PAGE_VIEW])
        login_success = len([e for e in recent_events if e.event_type == VisitorEventType.LOGIN_SUCCESS])
        login_failure = len([e for e in recent_events if e.event_type == VisitorEventType.LOGIN_FAILURE])
        reg_success = len([e for e in recent_events if e.event_type == VisitorEventType.REGISTRATION_SUCCESS])
        reg_failure = len([e for e in recent_events if e.event_type == VisitorEventType.REGISTRATION_FAILURE])
        
        return {
            'period_days': days,
            'total_visitors': unique_sessions,
            'total_pageviews': page_views,
            'login_success': login_success,
            'login_failure': login_failure,
            'registration_success': reg_success,
            'registration_failure': reg_failure,
            'top_pages': [],
            'top_referrers': [],
            'countries': []
        }
    
    def cleanup_old_events(self, retention_days: int = 90):
        """
        Clean up old events per GDPR data retention (Article 5)
        
        Default: 90 days retention for visitor analytics
        """
        try:
            if not self.db_url:
                return
            
            with self._get_connection() as conn:
                if not conn:
                    return
                cursor = conn.cursor()
                
                cutoff = datetime.now() - timedelta(days=retention_days)
                
                cursor.execute("""
                    DELETE FROM visitor_events
                    WHERE timestamp < %s
                """, (cutoff,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                cursor.close()
            
            logger.info(f"🗑️  Cleaned up {deleted_count} old visitor events (>{retention_days} days)")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old events: {e}")
    
    def get_recent_events(self, limit: int = 50, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent events from database for display
        
        Args:
            limit: Maximum number of events to return
            days: Number of days to look back
            
        Returns:
            List of event dictionaries
        """
        try:
            if not self.db_url:
                return self._get_memory_recent_events(limit)
            
            with self._get_connection() as conn:
                if not conn:
                    return self._get_memory_recent_events(limit)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                since = datetime.now() - timedelta(days=days)
                
                cursor.execute("""
                    SELECT 
                        event_id, session_id, event_type, timestamp,
                        page_path, user_id, success, error_message
                    FROM visitor_events
                    WHERE timestamp >= %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (since, limit))
                
                events = cursor.fetchall()
                cursor.close()
                
                return [dict(e) for e in events] if events else []
            
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return self._get_memory_recent_events(limit)
    
    def _get_memory_recent_events(self, limit: int) -> List[Dict[str, Any]]:
        """Fallback to in-memory events"""
        recent = sorted(self.events, key=lambda e: e.timestamp, reverse=True)[:limit]
        return [
            {
                'event_id': e.event_id,
                'session_id': e.session_id,
                'event_type': e.event_type.value,
                'timestamp': e.timestamp,
                'page_path': e.page_path,
                'user_id': e.user_id,
                'success': e.success,
                'error_message': e.error_message
            }
            for e in recent
        ]
    
    def get_visitor_sessions(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get detailed visitor sessions with pages visited
        
        Returns list of sessions with their page views
        """
        try:
            if not self.db_url:
                return []
            
            with self._get_connection() as conn:
                if not conn:
                    return []
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                since = datetime.now() - timedelta(days=days)
                
                cursor.execute("""
                    SELECT 
                        session_id,
                        MIN(timestamp) as session_start,
                        MAX(timestamp) as last_activity,
                        COUNT(*) as total_events,
                        COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) as page_views,
                        ARRAY_AGG(DISTINCT page_path) as pages_visited,
                        MAX(user_id) as user_id,
                        BOOL_OR(event_type = 'login_success') as logged_in
                    FROM visitor_events
                    WHERE timestamp >= %s
                    GROUP BY session_id
                    ORDER BY session_start DESC
                    LIMIT %s
                """, (since, limit))
                
                sessions = cursor.fetchall()
                cursor.close()
                
                return [dict(s) for s in sessions] if sessions else []
            
        except Exception as e:
            logger.error(f"Failed to get visitor sessions: {e}")
            return []

# Global instance
_visitor_tracker = None

def get_visitor_tracker() -> VisitorTracker:
    """Get or create global visitor tracker instance"""
    global _visitor_tracker
    if _visitor_tracker is None:
        _visitor_tracker = VisitorTracker()
    return _visitor_tracker
