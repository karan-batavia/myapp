"""
Authentication Tracking Wrapper
Clean integration layer for visitor tracking without modifying core auth.py

This module wraps existing authentication functions to add GDPR-compliant tracking
"""

import logging
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from services.visitor_tracker import get_visitor_tracker, VisitorEventType
from services.auth import authenticate as _auth_authenticate, create_user as _auth_create_user

logger = logging.getLogger(__name__)

def get_client_ip_from_streamlit() -> str:
    """
    Get client IP address from Streamlit context
    Falls back to 'unknown' if not available
    
    Returns:
        str: Client IP address (will be anonymized by VisitorTracker)
    """
    try:
        import streamlit as st
        
        # Try to get from X-Forwarded-For header (if behind proxy)
        if hasattr(st, 'context') and hasattr(st.context, 'headers'):
            forwarded_for = st.context.headers.get('X-Forwarded-For')
            if forwarded_for:
                # Get first IP in chain
                return forwarded_for.split(',')[0].strip()
            
            # Try to get from X-Real-IP header
            real_ip = st.context.headers.get('X-Real-IP')
            if real_ip:
                return real_ip
            
            # Fallback to remote address
            remote_addr = st.context.headers.get('Remote-Addr')
            if remote_addr:
                return remote_addr
        
        return 'unknown'
        
    except Exception as e:
        logger.debug(f"Could not get client IP: {e}")
        return 'unknown'

def get_session_id() -> str:
    """
    Get or create session ID for visitor tracking
    
    Returns:
        str: Session ID
    """
    try:
        import streamlit as st
        
        if 'visitor_session_id' not in st.session_state:
            st.session_state.visitor_session_id = str(uuid.uuid4())
        
        return st.session_state.visitor_session_id
    except Exception:
        return str(uuid.uuid4())

def get_country_from_ip(ip_address: str) -> Optional[str]:
    """
    Get country code from IP address using free geolocation API
    GDPR-compliant: Only stores 2-letter country code, not the IP
    
    Returns:
        2-letter country code (e.g., 'NL', 'DE', 'US') or None
    """
    try:
        import streamlit as st
        
        # Check cache first (stored in session)
        cache_key = 'visitor_country'
        if cache_key in st.session_state:
            return st.session_state[cache_key]
        
        if not ip_address or ip_address == 'unknown':
            return None
        
        import requests
        
        # Use ipapi.co free tier (1000 requests/day)
        response = requests.get(f'https://ipapi.co/{ip_address}/country/', timeout=2)
        
        if response.status_code == 200:
            country_code = response.text.strip()[:2].upper()
            if len(country_code) == 2 and country_code.isalpha():
                st.session_state[cache_key] = country_code
                return country_code
        
        return None
        
    except Exception as e:
        logger.debug(f"Country detection failed: {e}")
        return None

def authenticate_with_tracking(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user and track the attempt (success or failure)
    
    This is a wrapper around services.auth.authenticate() that adds tracking
    
    Args:
        username: Username or email
        password: Password
        
    Returns:
        User dict if successful, None if failed
    """
    tracker = get_visitor_tracker()
    session_id = get_session_id()
    ip_address = get_client_ip_from_streamlit()
    
    try:
        # Attempt authentication using original function
        user = _auth_authenticate(username, password)
        
        if user:
            # Track successful login - NO PII in details (GDPR-compliant)
            tracker.track_event(
                session_id=session_id,
                event_type=VisitorEventType.LOGIN_SUCCESS,
                page_path="/login",
                ip_address=ip_address,
                user_id=hashlib.sha256(str(user.get('user_id', '')).encode()).hexdigest()[:16],  # Anonymized user_id
                username=None,  # Don't store username in events table
                details={
                    'method': 'password',
                    'role': user.get('role', 'unknown'),
                    'timestamp': datetime.now().isoformat()
                },
                success=True
            )
            logger.info(f"✅ Login successful: {username}")
            return user
        else:
            # Track failed login - NO PII (GDPR-compliant)
            tracker.track_event(
                session_id=session_id,
                event_type=VisitorEventType.LOGIN_FAILURE,
                page_path="/login",
                ip_address=ip_address,
                details={
                    'method': 'password',
                    'attempt_time': datetime.now().isoformat()
                },
                success=False,
                error_message="Invalid credentials"
            )
            logger.warning(f"❌ Login failed: {username}")
            return None
            
    except Exception as e:
        # Track failed login due to error - NO PII (GDPR-compliant)
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.LOGIN_FAILURE,
            page_path="/login",
            ip_address=ip_address,
            details={
                'method': 'password',
                'error_type': type(e).__name__
            },
            success=False,
            error_message="Authentication error"
        )
        logger.error(f"❌ Login error for {username}: {e}")
        return None

def create_user_with_tracking(username: str, password: str, role: str, 
                             email: str) -> tuple:
    """
    Create user and track the attempt (success or failure)
    
    This is a wrapper around services.auth.create_user() that adds tracking
    Maintains the original signature: (username, password, role, email) -> Tuple[bool, str]
    
    Args:
        username: Username
        password: Password
        role: User role
        email: Email address
        
    Returns:
        Tuple of (success, message)
    """
    tracker = get_visitor_tracker()
    session_id = get_session_id()
    ip_address = get_client_ip_from_streamlit()
    
    try:
        # Track registration started - NO PII in details (GDPR-compliant)
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.REGISTRATION_STARTED,
            page_path="/register",
            ip_address=ip_address,
            details={
                'role': role,
                'method': 'signup_form',
                'timestamp': datetime.now().isoformat()
            },
            success=True
        )
        
        # Attempt user creation using original function
        success, message = _auth_create_user(username, password, role, email)
        
        if success:
            # Track successful registration - NO PII (GDPR-compliant)
            tracker.track_event(
                session_id=session_id,
                event_type=VisitorEventType.REGISTRATION_SUCCESS,
                page_path="/register",
                ip_address=ip_address,
                user_id=None,  # Don't store user_id for registration events
                username=None,  # Don't store username
                details={
                    'role': role,
                    'method': 'signup_form',
                    'timestamp': datetime.now().isoformat()
                },
                success=True
            )
            logger.info(f"✅ User registered successfully: {username}")
            return (True, message)
        else:
            # Track failed registration - NO PII (GDPR-compliant)
            tracker.track_event(
                session_id=session_id,
                event_type=VisitorEventType.REGISTRATION_FAILURE,
                page_path="/register",
                ip_address=ip_address,
                details={
                    'role': role,
                    'method': 'signup_form',
                    'failure_reason': 'validation_error'
                },
                success=False,
                error_message="Registration validation failed"
            )
            logger.warning(f"❌ User registration failed: {username}")
            return (False, message)
            
    except Exception as e:
        # Track failed registration due to error - NO PII (GDPR-compliant)
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.REGISTRATION_FAILURE,
            page_path="/register",
            ip_address=ip_address,
            details={
                'role': role,
                'error_type': type(e).__name__
            },
            success=False,
            error_message="Registration system error"
        )
        logger.error(f"❌ User registration error for {username}: {e}")
        return (False, str(e))

def track_page_view(page_path: str = "/", referrer: Optional[str] = None):
    """
    Track anonymous page view (GDPR-compliant)
    
    Args:
        page_path: URL path being viewed
        referrer: HTTP referrer (optional)
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        country = get_country_from_ip(ip_address)
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.PAGE_VIEW,
            page_path=page_path,
            ip_address=ip_address,
            referrer=referrer,
            country=country,
            success=True
        )
        
    except Exception as e:
        logger.debug(f"Failed to track page view: {e}")

def track_login_success(user_id: str = None, role: str = None):
    """
    Track successful login (GDPR-compliant, no PII stored)
    
    Args:
        user_id: User ID (will be hashed)
        role: User role
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        country = get_country_from_ip(ip_address)
        
        hashed_user_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:16] if user_id else None
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.LOGIN_SUCCESS,
            page_path="/login",
            ip_address=ip_address,
            country=country,
            user_id=hashed_user_id,
            details={'role': role, 'method': 'password'},
            success=True
        )
        logger.info("✅ Login success tracked")
        
    except Exception as e:
        logger.debug(f"Failed to track login success: {e}")

def track_login_failure(reason: str = None):
    """
    Track failed login attempt (GDPR-compliant, no PII stored)
    
    Args:
        reason: Failure reason (generic, no usernames)
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.LOGIN_FAILURE,
            page_path="/login",
            ip_address=ip_address,
            details={'method': 'password'},
            success=False,
            error_message=reason or "Invalid credentials"
        )
        logger.info("❌ Login failure tracked")
        
    except Exception as e:
        logger.debug(f"Failed to track login failure: {e}")

def track_registration_success(role: str = None):
    """
    Track successful registration (GDPR-compliant)
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        country = get_country_from_ip(ip_address)
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.REGISTRATION_SUCCESS,
            page_path="/register",
            ip_address=ip_address,
            country=country,
            details={'role': role or 'user', 'method': 'signup_form'},
            success=True
        )
        logger.info("✅ Registration success tracked")
        
    except Exception as e:
        logger.debug(f"Failed to track registration success: {e}")

def track_registration_failure(reason: str = None):
    """
    Track failed registration (GDPR-compliant)
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        country = get_country_from_ip(ip_address)
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.REGISTRATION_FAILURE,
            page_path="/register",
            ip_address=ip_address,
            country=country,
            details={'method': 'signup_form'},
            success=False,
            error_message=reason or "Registration failed"
        )
        logger.info("❌ Registration failure tracked")
        
    except Exception as e:
        logger.debug(f"Failed to track registration failure: {e}")

def track_logout(user_id: str, username: str):
    """
    Track user logout event (GDPR-compliant, no PII stored)
    
    Args:
        user_id: User ID (will be hashed before storage)
        username: Username (used for logging only, NOT stored)
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        
        # Hash user_id for anonymization (GDPR compliance)
        hashed_user_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.LOGOUT,
            page_path="/logout",
            ip_address=ip_address,
            user_id=hashed_user_id,  # Hashed, not raw user_id
            username=None,  # Never store username (GDPR)
            details={
                'method': 'manual_logout',
                'timestamp': datetime.now().isoformat()
            },
            success=True
        )
        
        logger.info(f"👋 User logged out: {username}")
        
    except Exception as e:
        logger.debug(f"Failed to track logout: {e}")

def track_session_start():
    """Track session start event"""
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.SESSION_START,
            page_path="/",
            ip_address=ip_address,
            success=True
        )
        
    except Exception as e:
        logger.debug(f"Failed to track session start: {e}")


# ============================================================================
# Revenue Tracking Functions (GDPR-Compliant)
# ============================================================================

def track_pricing_page_view(tier_viewed: str, page_path: str = "/pricing"):
    """
    Track pricing page view with tier interest (GDPR-compliant)
    
    Args:
        tier_viewed: Pricing tier name (e.g., "Startup", "Enterprise")
        page_path: URL path (default: /pricing)
    
    Example:
        track_pricing_page_view("Professional", "/pricing")
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.PRICING_PAGE_VIEW,
            page_path=page_path,
            ip_address=ip_address,
            details={
                'tier_viewed': tier_viewed,
                'timestamp': datetime.now().isoformat()
            },
            success=True
        )
        
        logger.debug(f"📊 Pricing page viewed: {tier_viewed}")
        
    except Exception as e:
        logger.debug(f"Failed to track pricing page view: {e}")


def track_trial_started(tier: str, duration_days: int = 14, user_id: Optional[str] = None):
    """
    Track trial signup (GDPR-compliant, no PII)
    
    Args:
        tier: Pricing tier for trial (e.g., "Professional")
        duration_days: Trial duration in days (default: 14)
        user_id: Optional anonymized user ID (will be hashed)
    
    Example:
        track_trial_started("Professional", 14, user_id)
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        
        # Hash user_id if provided (GDPR compliance)
        hashed_user_id = None
        if user_id:
            hashed_user_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.TRIAL_STARTED,
            page_path="/trial/signup",
            ip_address=ip_address,
            user_id=hashed_user_id,
            username=None,  # Never store username (GDPR)
            details={
                'tier': tier,
                'duration_days': duration_days,
                'trial_start': datetime.now().isoformat()
            },
            success=True
        )
        
        logger.info(f"🎯 Trial started: {tier} ({duration_days} days)")
        
    except Exception as e:
        logger.debug(f"Failed to track trial start: {e}")


def track_trial_converted(tier: str, mrr: float, user_id: Optional[str] = None):
    """
    Track trial-to-paid conversion (GDPR-compliant, no PII)
    
    Args:
        tier: Pricing tier converted to (e.g., "Professional")
        mrr: Monthly recurring revenue in EUR (e.g., 99.0)
        user_id: Optional anonymized user ID (will be hashed)
    
    Example:
        track_trial_converted("Professional", 99.0, user_id)
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        
        # Hash user_id if provided (GDPR compliance)
        hashed_user_id = None
        if user_id:
            hashed_user_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.TRIAL_CONVERTED,
            page_path="/subscription/activated",
            ip_address=ip_address,
            user_id=hashed_user_id,
            username=None,  # Never store username (GDPR)
            details={
                'tier': tier,
                'mrr': mrr,
                'conversion_date': datetime.now().isoformat()
            },
            success=True
        )
        
        logger.info(f"💰 Trial converted: {tier} (€{mrr}/month)")
        
    except Exception as e:
        logger.debug(f"Failed to track trial conversion: {e}")


def track_scanner_executed(scanner_type: str, success: bool = True, 
                           findings_count: int = 0, user_id: Optional[str] = None):
    """
    Track scanner execution for feature usage analytics (GDPR-compliant)
    
    Args:
        scanner_type: Type of scanner (e.g., "database", "code", "ai_model")
        success: Whether scan succeeded
        findings_count: Number of findings (optional)
        user_id: Optional anonymized user ID (will be hashed)
    
    Example:
        track_scanner_executed("database", True, 42, user_id)
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        
        # Hash user_id if provided (GDPR compliance)
        hashed_user_id = None
        if user_id:
            hashed_user_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
        
        tracker.track_event(
            session_id=session_id,
            event_type=VisitorEventType.SCANNER_EXECUTED,
            page_path=f"/scanner/{scanner_type}",
            ip_address=ip_address,
            user_id=hashed_user_id,
            username=None,  # Never store username (GDPR)
            details={
                'scanner_type': scanner_type,
                'findings_count': findings_count,
                'execution_time': datetime.now().isoformat()
            },
            success=success
        )
        
        logger.debug(f"🔍 Scanner executed: {scanner_type} (success={success}, findings={findings_count})")
        
    except Exception as e:
        logger.debug(f"Failed to track scanner execution: {e}")


def track_subscription_change(action: str, from_tier: str, to_tier: str, 
                              mrr_change: float, user_id: Optional[str] = None):
    """
    Track subscription upgrades, downgrades, or cancellations (GDPR-compliant)
    
    Args:
        action: Action type ("upgraded", "downgraded", "cancelled")
        from_tier: Previous tier (e.g., "Startup")
        to_tier: New tier (e.g., "Professional")
        mrr_change: MRR change in EUR (positive for upgrade, negative for downgrade)
        user_id: Optional anonymized user ID (will be hashed)
    
    Example:
        track_subscription_change("upgraded", "Startup", "Professional", 40.0, user_id)
    """
    try:
        tracker = get_visitor_tracker()
        session_id = get_session_id()
        ip_address = get_client_ip_from_streamlit()
        
        # Hash user_id if provided (GDPR compliance)
        hashed_user_id = None
        if user_id:
            hashed_user_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
        
        # Determine event type
        event_type_map = {
            "upgraded": VisitorEventType.SUBSCRIPTION_UPGRADED,
            "downgraded": VisitorEventType.SUBSCRIPTION_DOWNGRADED,
            "cancelled": VisitorEventType.SUBSCRIPTION_CANCELLED
        }
        event_type = event_type_map.get(action, VisitorEventType.SUBSCRIPTION_UPGRADED)
        
        tracker.track_event(
            session_id=session_id,
            event_type=event_type,
            page_path="/subscription/change",
            ip_address=ip_address,
            user_id=hashed_user_id,
            username=None,  # Never store username (GDPR)
            details={
                'action': action,
                'from_tier': from_tier,
                'to_tier': to_tier,
                'mrr_change': mrr_change,
                'change_date': datetime.now().isoformat()
            },
            success=True
        )
        
        logger.info(f"📈 Subscription {action}: {from_tier} → {to_tier} (€{mrr_change:+.2f})")
        
    except Exception as e:
        logger.debug(f"Failed to track subscription change: {e}")
