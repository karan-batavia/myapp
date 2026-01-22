"""
Dashboard Page Module
Displays real-time scan metrics and activity overview
"""

import streamlit as st
import logging
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from utils.redis_cache import RedisCache
    _redis_cache = RedisCache(strict_mode=False)
except Exception:
    _redis_cache = None

def get_organization_id():
    """Get organization ID for multi-tenant support"""
    return st.session_state.get('organization_id', 'default')


@st.cache_data(ttl=60, show_spinner=False)
def _get_cached_dashboard_metrics(username: str, org_id: str) -> dict:
    """
    Cache dashboard metrics for 60 seconds to avoid repeated database queries.
    Uses Redis for distributed caching + Streamlit cache for session-level.
    """
    cache_key = f"dashboard_metrics:{username}:{org_id}"
    
    if _redis_cache:
        cached = _redis_cache.get(cache_key)
        if cached:
            logger.debug(f"Dashboard metrics loaded from Redis cache for {username}")
            return cached
    
    from services.results_aggregator import ResultsAggregator
    
    aggregator = ResultsAggregator()
    aggregator.use_file_storage = False
    
    recent_scans = aggregator.get_recent_scans(days=365, username=username)
    
    if len(recent_scans) == 0:
        recent_scans = aggregator.get_recent_scans(days=30)
    
    total_scans = len(recent_scans)
    total_pii = 0
    high_risk_issues = 0
    compliance_scores = []
    
    for scan in recent_scans:
        result = scan.get('result', {})
        if isinstance(result, dict):
            scan_pii = scan.get('total_pii_found', 0)
            scan_high_risk = scan.get('high_risk_count', 0)
            
            if scan_pii == 0:
                findings = result.get('findings', [])
                if isinstance(findings, list):
                    scan_pii = len(findings)
                    for finding in findings:
                        if isinstance(finding, dict) and finding.get('severity', '').lower() in ['high', 'critical']:
                            scan_high_risk += 1
            
            if scan_pii == 0:
                scan_pii = result.get('total_pii_found', 0)
            if scan_high_risk == 0:
                scan_high_risk = result.get('high_risk_count', 0)
            
            total_pii += scan_pii
            high_risk_issues += scan_high_risk
            
            comp_score = result.get('compliance_score', 0)
            if comp_score > 0:
                compliance_scores.append(comp_score)
    
    avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
    
    result = {
        'total_scans': total_scans,
        'total_pii': total_pii,
        'high_risk_issues': high_risk_issues,
        'avg_compliance': avg_compliance,
        'recent_scans': recent_scans
    }
    
    if _redis_cache:
        _redis_cache.set(cache_key, result, ttl=120)
        logger.debug(f"Dashboard metrics cached in Redis for {username}")
    
    return result


def render_dashboard():
    """Render the main dashboard with real-time data from scan results and activity tracker"""
    from services.results_aggregator import ResultsAggregator
    from utils.activity_tracker import get_dashboard_metrics, get_activity_tracker
    
    if st.session_state.get('_trigger_rerun', False):
        st.session_state['_trigger_rerun'] = False
        st.rerun()
    
    from utils.i18n import get_text as _
    
    st.title(f"📊 {_('dashboard.title', 'Dashboard')}")
    
    col_refresh, col_spacer = st.columns([2, 8])
    with col_refresh:
        if st.button("🔄 Refresh Dashboard", help="Update dashboard with latest scan results"):
            st.rerun()
    
    current_scan_count = 0
    
    try:
        username = st.session_state.get('username', 'anonymous')
        user_id = st.session_state.get('user_id', username)
        org_id = get_organization_id()
        
        metrics = _get_cached_dashboard_metrics(username, org_id)
        total_scans = metrics['total_scans']
        total_pii = metrics['total_pii']
        high_risk_issues = metrics['high_risk_issues']
        recent_scans = metrics['recent_scans']
        compliance_scores = [metrics['avg_compliance']] if metrics['avg_compliance'] > 0 else []
        
        logger.info(f"Dashboard: Retrieved {total_scans} total scans for user {username} (cached)")
        
        user_scan_key = f'last_known_scan_count_{username}'
        last_known_count = st.session_state.get(user_scan_key, 0)
        current_scan_count = total_scans
        if current_scan_count > last_known_count and last_known_count > 0:
            _get_cached_dashboard_metrics.clear()
            st.info(f"✨ Dashboard updated with {current_scan_count - last_known_count} new scan(s)!")
        st.session_state[user_scan_key] = current_scan_count
        
        tracker = get_activity_tracker()
        user_activities = tracker.get_user_activities(user_id, limit=10000)
        
        scan_activities = [a for a in user_activities if hasattr(a, 'activity_type') and a.activity_type.value in ['scan_started', 'scan_completed', 'scan_failed']]
        completed_activities = [a for a in scan_activities if a.activity_type.value == 'scan_completed']
        
        today = datetime.now().date()
        today_activities = [a for a in completed_activities if a.timestamp.date() == today]
        
        for activity in today_activities:
            scan_details = activity.details
            activity_pii = scan_details.get('findings_count', 0)
            activity_high_risk = scan_details.get('high_risk_count', 0)
            activity_compliance = scan_details.get('compliance_score', 0)
            
            if activity_pii > 0:
                total_pii += activity_pii
            if activity_high_risk > 0:
                high_risk_issues += activity_high_risk
            if activity_compliance > 0:
                compliance_scores.append(activity_compliance)
        
        total_scans = total_scans + len(today_activities)
        
        if compliance_scores:
            avg_compliance = sum(compliance_scores) / len(compliance_scores)
        else:
            if total_scans > 0 and high_risk_issues > 0:
                avg_compliance = max(25, 100 - (high_risk_issues * 8))
            else:
                avg_compliance = 94.5
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(_('dashboard.metric.total_scans', 'Total Scans'), total_scans)
            
        with col2:
            st.metric(_('dashboard.metric.total_pii', 'Total PII Found'), total_pii)
            
        with col3:
            st.metric(_('dashboard.metric.compliance_score', 'Compliance Score'), f"{avg_compliance:.1f}%")
            
        with col4:
            st.metric(_('dashboard.metric.active_issues', 'Active Issues'), high_risk_issues)
        
        st.markdown("---")
        
        _render_recent_activity(recent_scans, username)
        _render_quick_actions()
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        st.error("Dashboard temporarily unavailable. Please try refreshing.")
        if st.button("🔄 Refresh Dashboard"):
            st.rerun()


def _render_recent_activity(recent_scans, username):
    """Render recent scan activity section"""
    from utils.i18n import get_text as _
    
    st.subheader(_('dashboard.recent_activity', 'Recent Scan Activity'))
    
    if not recent_scans:
        st.info("No recent scan activity. Start a new scan to see results here.")
        return
    
    activity_data = []
    for scan in recent_scans[:10]:
        result = scan.get('result', {})
        
        timestamp = scan.get('timestamp', '')
        if timestamp:
            try:
                if hasattr(timestamp, 'strftime'):
                    formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
                else:
                    dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_time = str(timestamp)[:16]
        else:
            formatted_time = 'Unknown'
        
        scan_type = scan.get('scan_type', 'unknown').replace('_', ' ').title()
        pii_count = scan.get('total_pii_found', result.get('total_pii_found', 0))
        
        activity_data.append({
            'Time': formatted_time,
            'Type': scan_type,
            'Files': scan.get('file_count', 0),
            'PII Found': pii_count,
            'Status': '✅ Complete'
        })
    
    if activity_data:
        df = pd.DataFrame(activity_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def _render_quick_actions():
    """Render quick action buttons"""
    from utils.i18n import get_text as _
    
    st.subheader(_('dashboard.quick_actions', 'Quick Actions'))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 New Scan", use_container_width=True):
            st.session_state['start_new_scan'] = True
            st.rerun()
    
    with col2:
        if st.button("📊 View Results", use_container_width=True):
            st.session_state['view_detailed_results'] = True
            st.rerun()
    
    with col3:
        if st.button("📋 Scan History", use_container_width=True):
            st.session_state['view_history'] = True
            st.rerun()
    
    with col4:
        if st.button("📈 Reports", use_container_width=True):
            st.info("Generate comprehensive compliance reports from the Results page.")
