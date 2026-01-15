"""
Authentication Wrapper for Multi-Page Architecture
Provides shared authentication, session initialization, and license enforcement for all pages.
Mirrors the initialization flow from app.py main() to ensure consistent behavior.
"""

import streamlit as st
import logging
import uuid

logger = logging.getLogger(__name__)


def initialize_session():
    """Initialize session state with defaults - mirrors app.py initialization"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    if 'page_configured' not in st.session_state:
        st.session_state.page_configured = False
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())


def init_i18n():
    """Initialize internationalization"""
    try:
        from utils.i18n import initialize, detect_browser_language
        
        if 'language' not in st.session_state:
            detected_lang = detect_browser_language()
            st.session_state.language = detected_lang
        
        initialize()
    except ImportError as e:
        logger.warning(f"i18n initialization failed: {e}")


def init_session_optimizer():
    """Initialize session optimization for authenticated users - mirrors app.py"""
    try:
        from utils.session_optimizer import get_streamlit_session
        streamlit_session = get_streamlit_session()
        
        if streamlit_session and st.session_state.get('authenticated'):
            user_data = {
                'username': st.session_state.get('username', 'unknown'),
                'user_role': st.session_state.get('user_role', 'user'),
                'language': st.session_state.get('language', 'en')
            }
            streamlit_session.init_session(st.session_state.get('username', 'unknown'), user_data)
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Session optimizer initialization failed: {e}")


def check_authentication():
    """Check if user is authenticated, return True/False"""
    try:
        if not st.session_state.get('authenticated', False):
            return False
        
        auth_token = st.session_state.get('auth_token')
        if not auth_token:
            return False
        
        try:
            import jwt
            import os
            secret = os.environ.get('JWT_SECRET')
            if not secret:
                logger.error("JWT_SECRET environment variable is not set - authentication disabled")
                st.session_state['authenticated'] = False
                return False
            jwt.decode(auth_token, secret, algorithms=['HS256'])
            return True
        except Exception:
            st.session_state['authenticated'] = False
            return False
            
    except Exception as e:
        logger.error(f"Authentication check failed: {e}")
        return False


def require_license_check():
    """Enforce license requirements - mirrors app.py"""
    try:
        from services.license_integration import require_license_check as license_check
        return license_check()
    except ImportError:
        return True
    except Exception as e:
        logger.warning(f"License check failed: {e}")
        return True


def show_license_expiry_banner():
    """Show license expiry banner if needed - mirrors app.py"""
    try:
        from components.license_expiry_manager import show_license_expiry_banner
        show_license_expiry_banner()
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"License expiry banner unavailable: {e}")


def hide_sidebar_navigation():
    """Hide the default Streamlit page navigation in sidebar"""
    hide_nav_css = """
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0 !important;
        }
    </style>
    """
    st.markdown(hide_nav_css, unsafe_allow_html=True)


def require_authentication():
    """
    Require authentication for a page.
    Returns True if authenticated, otherwise shows login redirect.
    Mirrors the full authentication flow from app.py main().
    """
    initialize_session()
    init_i18n()
    
    if not check_authentication():
        hide_sidebar_navigation()
        st.warning("Please log in to access this page.")
        st.info("Use the main application at the home page to authenticate.")
        
        if st.button("Go to Login"):
            st.switch_page("app.py")
        
        return False
    
    if not require_license_check():
        return False
    
    show_license_expiry_banner()
    
    init_session_optimizer()
    
    return True


def require_role(required_roles):
    """
    Require specific role(s) for access.
    required_roles: string or list of strings
    """
    if not require_authentication():
        return False
    
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    user_role = st.session_state.get('user_role', 'user')
    
    if user_role not in required_roles:
        st.error(f"Access denied. Required role: {', '.join(required_roles)}")
        return False
    
    return True


def get_current_user():
    """Get current user information"""
    return {
        'username': st.session_state.get('username', 'anonymous'),
        'user_id': st.session_state.get('user_id', 'anonymous'),
        'role': st.session_state.get('user_role', 'user'),
        'organization_id': st.session_state.get('organization_id', 'default')
    }


def show_license_check():
    """Show license status in sidebar"""
    try:
        from services.license_integration import show_license_sidebar
        show_license_sidebar()
    except ImportError:
        pass


def track_page_view(page_name):
    """Track page view activity"""
    try:
        from utils.session_optimizer import get_streamlit_session
        streamlit_session = get_streamlit_session()
        if streamlit_session and 'session_id' in st.session_state:
            streamlit_session.track_scan_activity('page_view', {'page': page_name})
    except Exception:
        pass
