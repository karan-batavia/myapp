"""
Database Caching Layer for DataGuardian Pro
Combines Streamlit cache_data with Redis for optimal performance
"""

import streamlit as st
import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from utils.redis_cache import RedisCache
    redis_cache = RedisCache(strict_mode=False)
except Exception as e:
    logger.warning(f"Redis cache unavailable: {e}")
    redis_cache = None

def _get_db_connection():
    """Get database connection with error handling"""
    import psycopg2
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        return None
    try:
        return psycopg2.connect(db_url)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

@st.cache_data(ttl=60, show_spinner=False)
def get_user_license_tier_cached(username: str) -> str:
    """Get user's license tier with 60s cache"""
    cache_key = f"license_tier:{username}"
    
    if redis_cache:
        cached = redis_cache.get(cache_key)
        if cached:
            return cached
    
    try:
        conn = _get_db_connection()
        if not conn:
            return "trial"
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT license_tier FROM platform_users WHERE username = %s OR email = %s",
            (username, username)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        tier = row[0] if row else "trial"
        
        if redis_cache:
            redis_cache.set(cache_key, tier, ttl=300)
        
        return tier
    except Exception as e:
        logger.error(f"Error getting license tier: {e}")
        return "trial"

@st.cache_data(ttl=60, show_spinner=False)
def get_user_metadata_cached(username: str) -> Dict[str, Any]:
    """Get user metadata with 60s cache"""
    cache_key = f"user_metadata:{username}"
    
    if redis_cache:
        cached = redis_cache.get(cache_key)
        if cached:
            return cached
    
    try:
        conn = _get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT metadata FROM platform_users WHERE username = %s OR email = %s",
            (username, username)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row and row[0]:
            metadata = row[0] if isinstance(row[0], dict) else json.loads(str(row[0]))
        else:
            metadata = {}
        
        if redis_cache:
            redis_cache.set(cache_key, metadata, ttl=300)
        
        return metadata
    except Exception as e:
        logger.error(f"Error getting user metadata: {e}")
        return {}

@st.cache_data(ttl=120, show_spinner=False)
def get_user_scan_count_cached(username: str) -> int:
    """Get user's total scan count with 2min cache"""
    cache_key = f"scan_count:{username}"
    
    if redis_cache:
        cached = redis_cache.get(cache_key)
        if cached is not None:
            return int(cached)
    
    try:
        conn = _get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM scans WHERE username = %s",
            (username,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        count = row[0] if row else 0
        
        if redis_cache:
            redis_cache.set(cache_key, count, ttl=300)
        
        return count
    except Exception as e:
        logger.error(f"Error getting scan count: {e}")
        return 0

@st.cache_data(ttl=300, show_spinner=False)
def get_recent_scans_cached(username: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent scans with 5min cache"""
    cache_key = f"recent_scans:{username}:{limit}"
    
    if redis_cache:
        cached = redis_cache.get(cache_key)
        if cached:
            return cached
    
    try:
        conn = _get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT scan_id, scan_type, status, created_at, completed_at
            FROM scans 
            WHERE username = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (username, limit))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        scans = []
        for row in rows:
            scans.append({
                'scan_id': row[0],
                'scan_type': row[1],
                'status': row[2],
                'created_at': row[3].isoformat() if row[3] else None,
                'completed_at': row[4].isoformat() if row[4] else None
            })
        
        if redis_cache:
            redis_cache.set(cache_key, scans, ttl=600)
        
        return scans
    except Exception as e:
        logger.error(f"Error getting recent scans: {e}")
        return []

@st.cache_data(ttl=60, show_spinner=False)
def get_dashboard_metrics_cached(username: str) -> Dict[str, Any]:
    """Get dashboard metrics with 60s cache"""
    cache_key = f"dashboard_metrics:{username}"
    
    if redis_cache:
        cached = redis_cache.get(cache_key)
        if cached:
            return cached
    
    try:
        conn = _get_db_connection()
        if not conn:
            return {'total_scans': 0, 'completed_scans': 0, 'pending_scans': 0}
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM scans 
            WHERE username = %s
        """, (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        metrics = {
            'total_scans': row[0] or 0 if row else 0,
            'completed_scans': row[1] or 0 if row else 0,
            'pending_scans': row[2] or 0 if row else 0
        }
        
        if redis_cache:
            redis_cache.set(cache_key, metrics, ttl=120)
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return {'total_scans': 0, 'completed_scans': 0, 'pending_scans': 0}

def invalidate_user_cache(username: str):
    """Invalidate all caches for a user after data changes"""
    cache_keys = [
        f"license_tier:{username}",
        f"user_metadata:{username}",
        f"scan_count:{username}",
        f"recent_scans:{username}:10",
        f"dashboard_metrics:{username}"
    ]
    
    if redis_cache:
        for key in cache_keys:
            redis_cache.delete(key)
    
    get_user_license_tier_cached.clear()
    get_user_metadata_cached.clear()
    get_user_scan_count_cached.clear()
    get_recent_scans_cached.clear()
    get_dashboard_metrics_cached.clear()
    
    logger.info(f"Cache invalidated for user: {username}")

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    if redis_cache:
        return redis_cache.stats
    return {'status': 'redis_unavailable', 'using_streamlit_cache': True}
