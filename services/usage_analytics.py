"""
Usage Analytics and Monitoring System
Real-time usage tracking and analytics for license management
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import threading
import uuid

logger = logging.getLogger(__name__)

class UsageEventType(Enum):
    """Types of usage events"""
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    REPORT_GENERATED = "report_generated"
    REPORT_DOWNLOADED = "report_downloaded"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    FEATURE_ACCESSED = "feature_accessed"
    API_CALL = "api_call"
    CONCURRENT_USER = "concurrent_user"
    STORAGE_USED = "storage_used"
    EXPORT_LIMIT_HIT = "export_limit_hit"
    USAGE_LIMIT_WARNING = "usage_limit_warning"
    USAGE_LIMIT_EXCEEDED = "usage_limit_exceeded"

@dataclass
class UsageEvent:
    """Individual usage event"""
    event_id: str
    event_type: UsageEventType
    timestamp: datetime
    user_id: str
    session_id: str
    scanner_type: Optional[str] = None
    region: Optional[str] = None
    feature: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class UsageStatistics:
    """Usage statistics summary"""
    total_scans: int
    successful_scans: int
    failed_scans: int
    average_duration_ms: float
    peak_concurrent_users: int
    total_reports_generated: int
    total_reports_downloaded: int
    features_used: List[str]
    scanners_used: List[str]
    regions_used: List[str]
    usage_by_hour: Dict[int, int]
    usage_by_day: Dict[str, int]
    error_rate: float

class UsageAnalytics:
    """Usage analytics and monitoring system"""
    
    def __init__(self, db_file: str = "usage_analytics.db"):
        self.db_file = db_file
        self.lock = threading.Lock()
        self.init_database()
        self.current_users: Dict[str, datetime] = {}
    
    def track_event(self, event_type: UsageEventType, user_id: str, session_id: str, 
                   scanner_type: Optional[str] = None, region: Optional[str] = None,
                   feature: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
                   duration_ms: Optional[int] = None, success: bool = True,
                   error_message: Optional[str] = None) -> bool:
        """Track a usage event"""
        try:
            event = UsageEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                scanner_type=scanner_type,
                region=region,
                feature=feature,
                details=details,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message
            )
            
            event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            event_type_log = event_type.value if hasattr(event_type, 'value') else str(event_type)
            
            with self.lock:
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO usage_events 
                    (event_id, event_type, timestamp, user_id, session_id, scanner_type, 
                     region, feature, details, duration_ms, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id, event_type_str, event.timestamp.isoformat(),
                    event.user_id, event.session_id, event.scanner_type, event.region,
                    event.feature, json.dumps(event.details) if event.details else None,
                    event.duration_ms, event.success, event.error_message
                ))
                
                conn.commit()
                conn.close()
                
                logger.info(f"Usage event tracked: {event_type_log} for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to track usage event: {e}")
            return False
        
    def init_database(self):
        """Initialize SQLite database for usage tracking"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create usage events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                scanner_type TEXT,
                region TEXT,
                feature TEXT,
                details TEXT,
                duration_ms INTEGER,
                success BOOLEAN,
                error_message TEXT
            )
        """)
        
        # Create usage summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_summary (
                date TEXT PRIMARY KEY,
                total_scans INTEGER,
                successful_scans INTEGER,
                failed_scans INTEGER,
                unique_users INTEGER,
                peak_concurrent_users INTEGER,
                total_reports INTEGER,
                features_used TEXT,
                scanners_used TEXT,
                regions_used TEXT
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON usage_events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON usage_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scanner_type ON usage_events(scanner_type)")
        
        conn.commit()
        conn.close()
    
    def track_event_object(self, event: UsageEvent):
        """Track a usage event object (legacy method)"""
        return self.track_event(
            event_type=event.event_type,
            user_id=event.user_id,
            session_id=event.session_id,
            scanner_type=event.scanner_type,
            region=event.region,
            feature=event.feature,
            details=event.details,
            duration_ms=event.duration_ms,
            success=event.success,
            error_message=event.error_message
        )
    
    def get_usage_statistics(self, 
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           user_id: Optional[str] = None) -> UsageStatistics:
        """Get usage statistics for a period"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Base query with optional filters
        where_clause = "WHERE timestamp BETWEEN ? AND ?"
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if user_id:
            where_clause += " AND user_id = ?"
            params.append(user_id)
        
        # Get scan statistics
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_scans,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_scans,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_scans,
                AVG(duration_ms) as avg_duration
            FROM usage_events 
            {where_clause}
            AND event_type IN ('scan_started', 'scan_completed', 'scan_failed')
        """, params)
        
        scan_stats = cursor.fetchone()
        total_scans = scan_stats[0] or 0
        successful_scans = scan_stats[1] or 0
        failed_scans = scan_stats[2] or 0
        avg_duration = scan_stats[3] or 0
        
        # Get report statistics
        cursor.execute(f"""
            SELECT 
                SUM(CASE WHEN event_type = 'report_generated' THEN 1 ELSE 0 END) as reports_generated,
                SUM(CASE WHEN event_type = 'report_downloaded' THEN 1 ELSE 0 END) as reports_downloaded
            FROM usage_events 
            {where_clause}
        """, params)
        
        report_stats = cursor.fetchone()
        reports_generated = report_stats[0] or 0
        reports_downloaded = report_stats[1] or 0
        
        # Get unique features used
        cursor.execute(f"""
            SELECT DISTINCT feature 
            FROM usage_events 
            {where_clause}
            AND feature IS NOT NULL
        """, params)
        
        features_used = [row[0] for row in cursor.fetchall()]
        
        # Get unique scanners used
        cursor.execute(f"""
            SELECT DISTINCT scanner_type 
            FROM usage_events 
            {where_clause}
            AND scanner_type IS NOT NULL
        """, params)
        
        scanners_used = [row[0] for row in cursor.fetchall()]
        
        # Get unique regions used
        cursor.execute(f"""
            SELECT DISTINCT region 
            FROM usage_events 
            {where_clause}
            AND region IS NOT NULL
        """, params)
        
        regions_used = [row[0] for row in cursor.fetchall()]
        
        # Get usage by hour
        cursor.execute(f"""
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as count
            FROM usage_events 
            {where_clause}
            GROUP BY hour
            ORDER BY hour
        """, params)
        
        usage_by_hour = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get usage by day
        cursor.execute(f"""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as count
            FROM usage_events 
            {where_clause}
            GROUP BY date
            ORDER BY date
        """, params)
        
        usage_by_day = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Calculate peak concurrent users (approximate)
        peak_concurrent = len(self.current_users)
        
        # Calculate error rate
        error_rate = (failed_scans / max(total_scans, 1)) * 100
        
        conn.close()
        
        return UsageStatistics(
            total_scans=total_scans,
            successful_scans=successful_scans,
            failed_scans=failed_scans,
            average_duration_ms=avg_duration,
            peak_concurrent_users=peak_concurrent,
            total_reports_generated=reports_generated,
            total_reports_downloaded=reports_downloaded,
            features_used=features_used,
            scanners_used=scanners_used,
            regions_used=regions_used,
            usage_by_hour=usage_by_hour,
            usage_by_day=usage_by_day,
            error_rate=error_rate
        )
    
    def get_user_activity(self, user_id: str, limit: int = 100) -> List[UsageEvent]:
        """Get recent activity for a user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM usage_events 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (user_id, limit))
        
        events = []
        for row in cursor.fetchall():
            events.append(UsageEvent(
                event_id=row[0],
                event_type=UsageEventType(row[1]),
                timestamp=datetime.fromisoformat(row[2]),
                user_id=row[3],
                session_id=row[4],
                scanner_type=row[5],
                region=row[6],
                feature=row[7],
                details=json.loads(row[8]) if row[8] else None,
                duration_ms=row[9],
                success=bool(row[10]),
                error_message=row[11]
            ))
        
        conn.close()
        return events
    
    def get_scanner_usage(self, scanner_type: str, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get usage statistics for a specific scanner"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_uses,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_uses,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_uses,
                AVG(duration_ms) as avg_duration,
                MIN(duration_ms) as min_duration,
                MAX(duration_ms) as max_duration,
                COUNT(DISTINCT user_id) as unique_users
            FROM usage_events 
            WHERE scanner_type = ? 
            AND timestamp BETWEEN ? AND ?
        """, (scanner_type, start_date.isoformat(), end_date.isoformat()))
        
        stats = cursor.fetchone()
        
        # Get usage by day
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as count
            FROM usage_events 
            WHERE scanner_type = ? 
            AND timestamp BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (scanner_type, start_date.isoformat(), end_date.isoformat()))
        
        usage_by_day = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "scanner_type": scanner_type,
            "total_uses": stats[0] or 0,
            "successful_uses": stats[1] or 0,
            "failed_uses": stats[2] or 0,
            "success_rate": (stats[1] / max(stats[0], 1)) * 100,
            "average_duration_ms": stats[3] or 0,
            "min_duration_ms": stats[4] or 0,
            "max_duration_ms": stats[5] or 0,
            "unique_users": stats[6] or 0,
            "usage_by_day": usage_by_day
        }
    
    def get_license_compliance_report(self, license_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate license compliance report"""
        stats = self.get_usage_statistics()
        
        # Check against license limits
        compliance_status = {}
        warnings = []
        
        usage_info = license_info.get("usage", {})
        
        for limit_type, limit_data in usage_info.items():
            current = limit_data["current"]
            limit = limit_data["limit"]
            percentage = limit_data["percentage"]
            
            if percentage > 90:
                compliance_status[limit_type] = "CRITICAL"
                warnings.append(f"{limit_type}: {percentage:.1f}% of limit used")
            elif percentage > 75:
                compliance_status[limit_type] = "WARNING"
                warnings.append(f"{limit_type}: {percentage:.1f}% of limit used")
            else:
                compliance_status[limit_type] = "OK"
        
        # Check concurrent users
        current_concurrent = len(self.current_users)
        max_concurrent = license_info.get("max_concurrent_users", 1)
        
        if current_concurrent >= max_concurrent:
            compliance_status["concurrent_users"] = "CRITICAL"
            warnings.append(f"Concurrent users: {current_concurrent}/{max_concurrent}")
        elif current_concurrent > max_concurrent * 0.8:
            compliance_status["concurrent_users"] = "WARNING"
        else:
            compliance_status["concurrent_users"] = "OK"
        
        return {
            "license_type": license_info.get("license_type"),
            "compliance_status": compliance_status,
            "warnings": warnings,
            "usage_statistics": asdict(stats),
            "current_concurrent_users": current_concurrent,
            "max_concurrent_users": max_concurrent,
            "license_expires": license_info.get("expiry_date"),
            "days_remaining": license_info.get("days_remaining")
        }
    
    def cleanup_old_events(self, days_to_keep: int = 90):
        """Clean up old usage events"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM usage_events 
            WHERE timestamp < ?
        """, (cutoff_date.isoformat(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} old usage events")
        return deleted_count
    
    def export_usage_data(self, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         format: str = "json") -> str:
        """Export usage data for analysis"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM usage_events 
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """, (start_date.isoformat(), end_date.isoformat()))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                "event_id": row[0],
                "event_type": row[1],
                "timestamp": row[2],
                "user_id": row[3],
                "session_id": row[4],
                "scanner_type": row[5],
                "region": row[6],
                "feature": row[7],
                "details": json.loads(row[8]) if row[8] else None,
                "duration_ms": row[9],
                "success": bool(row[10]),
                "error_message": row[11]
            })
        
        conn.close()
        
        if format == "json":
            return json.dumps(events, indent=2)
        elif format == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if events:
                writer = csv.DictWriter(output, fieldnames=events[0].keys())
                writer.writeheader()
                writer.writerows(events)
            
            return output.getvalue()
        else:
            return json.dumps(events, indent=2)

# Global analytics instance
usage_analytics = UsageAnalytics()

# Convenience functions
def track_usage_event(event_type: UsageEventType, 
                     user_id: str, 
                     session_id: str,
                     scanner_type: Optional[str] = None,
                     region: Optional[str] = None,
                     feature: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None,
                     duration_ms: Optional[int] = None,
                     success: bool = True,
                     error_message: Optional[str] = None):
    """Track a usage event"""
    event = UsageEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(),
        user_id=user_id,
        session_id=session_id,
        scanner_type=scanner_type,
        region=region,
        feature=feature,
        details=details,
        duration_ms=duration_ms,
        success=success,
        error_message=error_message
    )
    usage_analytics.track_event_object(event)

def get_usage_stats(start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   user_id: Optional[str] = None) -> UsageStatistics:
    """Get usage statistics"""
    return usage_analytics.get_usage_statistics(start_date, end_date, user_id)

def get_compliance_report(license_info: Dict[str, Any]) -> Dict[str, Any]:
    """Get license compliance report"""
    return usage_analytics.get_license_compliance_report(license_info)