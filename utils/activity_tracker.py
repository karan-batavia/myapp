"""
Centralized Activity Tracking System for DataGuardian Pro
Unified activity logging across all scanner types with real-time dashboard integration
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ActivityType(Enum):
    """Activity types for consistent tracking"""
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    DASHBOARD_ACCESS = "dashboard_access"
    LOGIN = "login"
    LOGOUT = "logout"
    SETTINGS_CHANGED = "settings_changed"
    REPORT_GENERATED = "report_generated"
    REPORT_DOWNLOADED = "report_downloaded"

class ScannerType(Enum):
    """Scanner types for consistent tracking - All scanner types"""
    CODE = "code"                           # 1. Code Scanner
    DOCUMENT = "document"                   # 2. Document/Blob Scanner  
    IMAGE = "image"                         # 3. Image Scanner (OCR-based)
    DATABASE = "database"                   # 4. Database Scanner
    API = "api"                            # 5. API Scanner
    ENTERPRISE = "enterprise"               # 6. Enterprise Connector Scanner
    AI_MODEL = "ai_model"                  # 7. AI Model Scanner
    WEBSITE = "website"                    # 8. Website Scanner  
    SOC2 = "soc2"                         # 9. SOC2 Scanner
    DPIA = "dpia"                         # 10. DPIA Scanner
    SUSTAINABILITY = "sustainability"      # 11. Sustainability Scanner (bonus)
    REPOSITORY = "repository"              # Git Repository Scanner
    BLOB = "blob"                         # Blob storage scanner
    COOKIE = "cookie"                     # Cookie compliance scanner
    CONNECTORS_E2E = "connectors_e2e"     # Connectors E2E Testing
    AUDIO_VIDEO = "audio_video"           # Audio/Video Deepfake Scanner

@dataclass
class ActivityEntry:
    """Structured activity entry"""
    activity_id: str
    session_id: str
    user_id: str
    username: str
    activity_type: ActivityType
    scanner_type: Optional[ScannerType]
    timestamp: datetime
    details: Dict[str, Any]
    region: Optional[str] = None
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None

class ActivityTracker:
    """Centralized activity tracking system"""
    
    def __init__(self):
        self.activities: Dict[str, List[ActivityEntry]] = {}  # user_id -> activities
        self.lock = threading.Lock()
        self.session_activities: Dict[str, List[ActivityEntry]] = {}  # session_id -> activities
        
    def track_activity(self, 
                      session_id: str,
                      user_id: str,
                      username: str,
                      activity_type: ActivityType,
                      scanner_type: Optional[ScannerType] = None,
                      details: Optional[Dict[str, Any]] = None,
                      region: Optional[str] = None,
                      duration_ms: Optional[int] = None,
                      success: bool = True,
                      error_message: Optional[str] = None) -> str:
        """Track a user activity with comprehensive details"""
        
        activity_id = str(uuid.uuid4())
        activity_entry = ActivityEntry(
            activity_id=activity_id,
            session_id=session_id,
            user_id=user_id,
            username=username,
            activity_type=activity_type,
            scanner_type=scanner_type,
            timestamp=datetime.now(),
            details=details or {},
            region=region,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        
        with self.lock:
            # Add to user activities
            if user_id not in self.activities:
                self.activities[user_id] = []
            self.activities[user_id].append(activity_entry)
            
            # Add to session activities
            if session_id not in self.session_activities:
                self.session_activities[session_id] = []
            self.session_activities[session_id].append(activity_entry)
            
            # Keep only last 1000 activities per user
            if len(self.activities[user_id]) > 1000:
                self.activities[user_id] = self.activities[user_id][-1000:]
            
            # Keep only last 500 activities per session
            if len(self.session_activities[session_id]) > 500:
                self.session_activities[session_id] = self.session_activities[session_id][-500:]
        
        logger.info(f"Activity tracked: {activity_type.value} for user {username}")
        return activity_id
    
    def get_user_activities(self, user_id: str, limit: int = 100) -> List[ActivityEntry]:
        """Get user activities with optional limit"""
        with self.lock:
            activities = self.activities.get(user_id, [])
            return activities[-limit:] if limit else activities
    
    def get_session_activities(self, session_id: str, limit: int = 100) -> List[ActivityEntry]:
        """Get session activities with optional limit"""
        with self.lock:
            activities = self.session_activities.get(session_id, [])
            return activities[-limit:] if limit else activities
    
    def get_scanner_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive scanner usage statistics for a user"""
        activities = self.get_user_activities(user_id, limit=10000)  # Large limit for all activities
        scan_activities = [a for a in activities if a.activity_type in [
            ActivityType.SCAN_STARTED, ActivityType.SCAN_COMPLETED, ActivityType.SCAN_FAILED
        ]]
        
        scanner_stats = {}
        for scanner_type in ScannerType:
            scanner_activities = [a for a in scan_activities if a.scanner_type == scanner_type]
            
            completed_scans = [a for a in scanner_activities if a.activity_type == ActivityType.SCAN_COMPLETED]
            failed_scans = [a for a in scanner_activities if a.activity_type == ActivityType.SCAN_FAILED]
            
            total_findings = sum(a.details.get('findings_count', 0) for a in completed_scans)
            total_files = sum(a.details.get('files_scanned', 0) for a in completed_scans)
            
            scanner_stats[scanner_type.value] = {
                'total_scans': len(completed_scans),
                'failed_scans': len(failed_scans),
                'success_rate': len(completed_scans) / max(len(scanner_activities), 1),
                'total_findings': total_findings,
                'total_files': total_files,
                'avg_duration_ms': sum(a.duration_ms for a in completed_scans if a.duration_ms) / max(len(completed_scans), 1) if completed_scans else 0
            }
        
        return scanner_stats
    
    def get_dashboard_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get real-time dashboard metrics for a user"""
        activities = self.get_user_activities(user_id, limit=10000)  # Large limit for all activities
        
        # Calculate scan metrics
        scan_activities = [a for a in activities if a.activity_type in [
            ActivityType.SCAN_STARTED, ActivityType.SCAN_COMPLETED, ActivityType.SCAN_FAILED
        ]]
        
        completed_scans = [a for a in scan_activities if a.activity_type == ActivityType.SCAN_COMPLETED]
        failed_scans = [a for a in scan_activities if a.activity_type == ActivityType.SCAN_FAILED]
        
        total_scans = len(completed_scans)
        total_pii_found = sum(a.details.get('findings_count', 0) for a in completed_scans)
        high_risk_findings = sum(a.details.get('high_risk_count', 0) for a in completed_scans)
        
        # Calculate compliance score (weighted average)
        compliance_scores = [a.details.get('compliance_score', 0) for a in completed_scans if a.details.get('compliance_score')]
        avg_compliance_score = sum(compliance_scores) / max(len(compliance_scores), 1) if compliance_scores else 0
        
        # Recent activity (last 10)
        recent_activities = activities[-10:] if activities else []
        
        return {
            'total_scans': total_scans,
            'total_pii_found': total_pii_found,
            'high_risk_findings': high_risk_findings,
            'average_compliance_score': avg_compliance_score,
            'success_rate': len(completed_scans) / max(len(scan_activities), 1) if scan_activities else 0,
            'failed_scans': len(failed_scans),
            'recent_activities': [
                {
                    'timestamp': a.timestamp.isoformat(),
                    'activity_type': a.activity_type.value,
                    'scanner_type': a.scanner_type.value if a.scanner_type else None,
                    'success': a.success,
                    'details': a.details
                }
                for a in recent_activities
            ]
        }
    
    def get_activity_timeline(self, user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get activity timeline for the last N hours"""
        activities = self.get_user_activities(user_id, limit=10000)  # Large limit for all activities
        
        # Filter activities from last N hours
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_activities = [a for a in activities if a.timestamp >= cutoff_time]
        
        # Group by hour
        timeline = {}
        for activity in recent_activities:
            hour_key = activity.timestamp.strftime('%Y-%m-%d %H:00')
            if hour_key not in timeline:
                timeline[hour_key] = {
                    'hour': hour_key,
                    'total_activities': 0,
                    'scans_completed': 0,
                    'scans_failed': 0,
                    'findings_found': 0
                }
            
            timeline[hour_key]['total_activities'] += 1
            if activity.activity_type == ActivityType.SCAN_COMPLETED:
                timeline[hour_key]['scans_completed'] += 1
                timeline[hour_key]['findings_found'] += activity.details.get('findings_count', 0)
            elif activity.activity_type == ActivityType.SCAN_FAILED:
                timeline[hour_key]['scans_failed'] += 1
        
        return sorted(timeline.values(), key=lambda x: x['hour'])

# Global activity tracker instance
_activity_tracker = None
_tracker_lock = threading.Lock()

def get_activity_tracker() -> ActivityTracker:
    """Get the global activity tracker instance"""
    global _activity_tracker
    if _activity_tracker is None:
        with _tracker_lock:
            if _activity_tracker is None:
                _activity_tracker = ActivityTracker()
    return _activity_tracker

# Convenience functions for common operations
def track_scan_started(session_id: str, user_id: str, username: str, scanner_type: ScannerType, 
                      region: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> str:
    """Track scan start activity"""
    tracker = get_activity_tracker()
    return tracker.track_activity(
        session_id=session_id,
        user_id=user_id,
        username=username,
        activity_type=ActivityType.SCAN_STARTED,
        scanner_type=scanner_type,
        region=region,
        details=details
    )

def track_scan_completed(session_id: str, user_id: str, username: str, scanner_type: ScannerType,
                        findings_count: int, files_scanned: int = 0, compliance_score: float = 0,
                        duration_ms: Optional[int] = None, region: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> str:
    """Track scan completion activity"""
    tracker = get_activity_tracker()
    scan_details = {
        'findings_count': findings_count,
        'files_scanned': files_scanned,
        'compliance_score': compliance_score,
        **(details or {})
    }
    return tracker.track_activity(
        session_id=session_id,
        user_id=user_id,
        username=username,
        activity_type=ActivityType.SCAN_COMPLETED,
        scanner_type=scanner_type,
        region=region,
        duration_ms=duration_ms,
        details=scan_details
    )

def track_scan_failed(session_id: str, user_id: str, username: str, scanner_type: ScannerType,
                     error_message: str, region: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> str:
    """Track scan failure activity"""
    tracker = get_activity_tracker()
    return tracker.track_activity(
        session_id=session_id,
        user_id=user_id,
        username=username,
        activity_type=ActivityType.SCAN_FAILED,
        scanner_type=scanner_type,
        region=region,
        success=False,
        error_message=error_message,
        details=details
    )

def get_dashboard_metrics(user_id: str) -> Dict[str, Any]:
    """Get dashboard metrics for a user from actual scan results"""
    try:
        # Get real scan data from database
        from services.results_aggregator import ResultsAggregator
        from services.compliance_score import ComplianceScoreManager
        
        agg = ResultsAggregator()
        recent_scans = agg.get_recent_scans(days=30)
        
        # Filter scans for this user - try multiple matching patterns
        user_scans = []
        
        # Try exact username match first
        user_scans = [scan for scan in recent_scans if scan.get('username') == user_id]
        
        # Try partial match (remove prefixes like 'user')
        if not user_scans:
            clean_user_id = user_id.replace('user', '').replace('_', '')
            user_scans = [scan for scan in recent_scans 
                         if scan.get('username', '').replace('user', '').replace('_', '') == clean_user_id]
        
        # Try any scan with similar username
        if not user_scans:
            user_scans = [scan for scan in recent_scans if user_id in scan.get('username', '') or scan.get('username', '') in user_id]
        
        # Calculate actual metrics from scan results
        total_scans = len(user_scans)
        total_pii_found = 0
        high_risk_findings = 0
        
        for scan in user_scans:
            result = scan.get('result', {})
            if isinstance(result, dict):
                findings = result.get('findings', [])
                
                # Count total findings as PII found
                if isinstance(findings, list):
                    total_pii_found += len(findings)
                    
                    # Count high-risk findings
                    for finding in findings:
                        if isinstance(finding, dict):
                            severity = finding.get('severity', '').lower()
                            if severity in ['high', 'critical']:
                                high_risk_findings += 1
                            
                            # Also try to get specific PII counts
                            pii_count = finding.get('pii_count', 0)
                            if pii_count > 0:
                                total_pii_found += pii_count
                
                # Also check for direct PII count in results
                total_pii_found += result.get('total_pii_found', 0)
                high_risk_findings += result.get('high_risk_count', 0)
        
        # Calculate compliance score
        compliance_manager = ComplianceScoreManager()
        compliance_data = compliance_manager.calculate_current_score()
        avg_compliance_score = compliance_data.get('overall_score', 0)
        
        # Get activity data for recent activities display
        tracker = get_activity_tracker()
        activities = tracker.get_user_activities(user_id, limit=10)
        
        return {
            'total_scans': total_scans,
            'total_pii_found': total_pii_found,
            'high_risk_findings': high_risk_findings,
            'average_compliance_score': avg_compliance_score,
            'success_rate': 1.0 if total_scans > 0 else 0,
            'failed_scans': 0,
            'recent_activities': [
                {
                    'timestamp': a.timestamp.isoformat(),
                    'activity_type': a.activity_type.value,
                    'scanner_type': a.scanner_type.value if a.scanner_type else None,
                    'success': a.success,
                    'details': a.details
                }
                for a in activities
            ] if activities else []
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        # Fallback to activity tracker
        tracker = get_activity_tracker()
        return tracker.get_dashboard_metrics(user_id)

def get_scanner_statistics(user_id: str) -> Dict[str, Any]:
    """Get scanner statistics for a user"""
    tracker = get_activity_tracker()
    return tracker.get_scanner_statistics(user_id)