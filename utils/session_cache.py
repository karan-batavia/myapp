"""
Session State Cache Utilities for DataGuardian Pro
Provides cached access to frequently accessed user data to avoid repeated lookups
"""

import streamlit as st
import logging
import time
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300


def get_cached_user_license(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get user license info with session state caching.
    Caches for 5 minutes to avoid repeated database/service calls.
    
    Returns:
        dict with license info: tier, is_active, usage_limits, expiry, etc.
    """
    cache_key = '_cached_license_info'
    cache_time_key = '_cached_license_time'
    
    current_time = time.time()
    cached_time = st.session_state.get(cache_time_key, 0)
    
    if not force_refresh and cache_key in st.session_state:
        if current_time - cached_time < CACHE_TTL_SECONDS:
            return st.session_state[cache_key]
    
    try:
        from services.license_integration import LicenseIntegration
        
        username = st.session_state.get('username', 'anonymous')
        org_id = st.session_state.get('organization_id', 'default')
        
        license_service = LicenseIntegration()
        license_info = license_service.get_user_license_info(username, org_id)
        
        result = {
            'tier': license_info.get('tier', 'trial'),
            'tier_display': license_info.get('tier_display', 'Trial'),
            'is_active': license_info.get('is_active', True),
            'scans_remaining': license_info.get('scans_remaining', 10),
            'scans_limit': license_info.get('scans_limit', 10),
            'users_limit': license_info.get('users_limit', 1),
            'expiry_date': license_info.get('expiry_date'),
            'features': license_info.get('features', []),
            'scanner_count': license_info.get('scanner_count', 3),
        }
        
        st.session_state[cache_key] = result
        st.session_state[cache_time_key] = current_time
        logger.debug(f"License info cached for user {username}")
        
        return result
        
    except Exception as e:
        logger.warning(f"Failed to get license info, using defaults: {e}")
        return {
            'tier': 'trial',
            'tier_display': 'Trial',
            'is_active': True,
            'scans_remaining': 10,
            'scans_limit': 10,
            'users_limit': 1,
            'expiry_date': None,
            'features': [],
            'scanner_count': 3,
        }


def get_cached_user_tier() -> str:
    """Get user's current tier with caching."""
    return get_cached_user_license().get('tier', 'trial')


def get_cached_scanner_count() -> int:
    """Get user's available scanner count with caching."""
    return get_cached_user_license().get('scanner_count', 3)


def invalidate_license_cache():
    """Invalidate the license cache to force refresh on next access."""
    st.session_state.pop('_cached_license_info', None)
    st.session_state.pop('_cached_license_time', None)
    logger.debug("License cache invalidated")


def get_cached_compliance_status(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get compliance status with session state caching.
    Caches for 5 minutes to avoid repeated calculations.
    """
    cache_key = '_cached_compliance_status'
    cache_time_key = '_cached_compliance_time'
    
    current_time = time.time()
    cached_time = st.session_state.get(cache_time_key, 0)
    
    if not force_refresh and cache_key in st.session_state:
        if current_time - cached_time < CACHE_TTL_SECONDS:
            return st.session_state[cache_key]
    
    try:
        from services.results_aggregator import ResultsAggregator
        
        username = st.session_state.get('username', 'anonymous')
        
        aggregator = ResultsAggregator()
        recent_scans = aggregator.get_recent_scans(days=30, username=username)
        
        total_scans = len(recent_scans)
        total_pii = sum(s.get('total_pii_found', 0) for s in recent_scans)
        high_risk = sum(s.get('high_risk_count', 0) for s in recent_scans)
        
        compliance_scores = []
        for scan in recent_scans:
            result = scan.get('result', {})
            if isinstance(result, dict):
                score = result.get('compliance_score', 0)
                if score > 0:
                    compliance_scores.append(score)
        
        avg_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        result = {
            'total_scans_30d': total_scans,
            'total_pii_found': total_pii,
            'high_risk_count': high_risk,
            'avg_compliance_score': round(avg_score, 1),
            'gdpr_status': 'compliant' if avg_score >= 80 else 'needs_attention',
        }
        
        st.session_state[cache_key] = result
        st.session_state[cache_time_key] = current_time
        
        return result
        
    except Exception as e:
        logger.warning(f"Failed to get compliance status: {e}")
        return {
            'total_scans_30d': 0,
            'total_pii_found': 0,
            'high_risk_count': 0,
            'avg_compliance_score': 0,
            'gdpr_status': 'unknown',
        }


def invalidate_compliance_cache():
    """Invalidate compliance cache to force refresh on next access."""
    st.session_state.pop('_cached_compliance_status', None)
    st.session_state.pop('_cached_compliance_time', None)
    logger.debug("Compliance cache invalidated")


def invalidate_all_caches():
    """Invalidate all session caches."""
    invalidate_license_cache()
    invalidate_compliance_cache()
    logger.info("All session caches invalidated")
