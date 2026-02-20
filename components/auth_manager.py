"""
Authentication and Language Management Module
Extracted from app.py to improve modularity while preserving exact UI behavior
"""
import streamlit as st
import logging
from services.auth import is_authenticated, logout, validate_email
from services.auth import create_user as _create_user_original, authenticate as _authenticate_original
from services.auth_tracker import authenticate_with_tracking, create_user_with_tracking, track_logout
from services.stripe_payment import display_payment_button, handle_payment_callback, SCAN_PRICES, verify_payment
from services.subscription_manager import display_subscription_plans, SubscriptionManager
from utils.i18n import initialize, language_selector, get_text, set_language, LANGUAGES, _translations

logger = logging.getLogger(__name__)

# Use tracking wrappers by default
authenticate = authenticate_with_tracking
create_user = create_user_with_tracking

# Define translation function
def _(key, default=None):
    return get_text(key, default)

def initialize_language_system():
    """
    Initialize language system - extracted from app.py lines 65-120
    This critical section ensures language preservation across app state changes
    """
    # Check multiple storage locations for language settings
    
    # First, initialize basic session state if needed
    if 'language' not in st.session_state:
        # Check if we have a persistent language setting
        if '_persistent_language' in st.session_state:
            # Use persistent language across app reloads
            current_language = st.session_state['_persistent_language']
        elif 'pre_login_language' in st.session_state:
            # Use pre-login language setting
            current_language = st.session_state['pre_login_language']
        elif 'backup_language' in st.session_state:
            # Use backup language setting
            current_language = st.session_state['backup_language']
        else:
            # Default to English if no language specified
            current_language = 'en'
        
        # Set the language in the primary location
        st.session_state['language'] = current_language
        
        # Force translations to be reloaded
        st.session_state['reload_translations'] = True

    # Ensure translations are properly initialized 
    # Sometimes the initialize function needs to be called multiple times
    # to properly load all translations
    global _translations
    _translations = {}  # Reset translations for fresh load
    initialize()  # Initialize translations

def handle_forced_language_after_login():
    """Handle forced language setting after login - extracted from app.py lines 101-120"""
    if 'force_language_after_login' in st.session_state and st.session_state['force_language_after_login']:
        forced_language = st.session_state['force_language_after_login']
        
        # Set language immediately
        st.session_state['language'] = forced_language
        st.session_state['_persistent_language'] = forced_language
        
        # Clear the force flag
        st.session_state['force_language_after_login'] = None
        
        # Reinitialize translations with forced language
        set_language(forced_language)
        initialize()

def preserve_language_during_operations():
    """Preserve language settings during various operations - extracted from app.py lines 475-520"""
    # Multi-layer language preservation system
    if 'language' in st.session_state:
        # Get language from session state sources
        lang_sources = []
        if 'language' in st.session_state and st.session_state['language']:
            lang_sources.append(st.session_state['language'])
        if '_persistent_language' in st.session_state and st.session_state['_persistent_language']:
            lang_sources.append(st.session_state['_persistent_language'])
        
        # Find the most reliable language
        key = f"language_preservation_{st.session_state.get('language', 'en')}"
        current_language = st.session_state.get('language', 'en')
        
        # Only update if we have a solid language reference
        if current_language in LANGUAGES:
            current_language = current_language
        elif len(lang_sources) > 0:
            current_language = lang_sources[0]
        
        # Preserve language with recursive fallback
        preserved_language = current_language
        
        # Store in multiple locations for redundancy
        if preserved_language and preserved_language in LANGUAGES:
            st.session_state['_persistent_language'] = preserved_language
            st.session_state['pre_login_language'] = preserved_language
            st.session_state['backup_language'] = preserved_language
            st.session_state['language'] = preserved_language
            
            # Ensure the translation system is using this language
            if get_text('app.title', 'DataGuardian Pro') == 'DataGuardian Pro':
                set_language(preserved_language)
                
        return preserved_language
    return 'en'

def debug_translations():
    """Debug information about critical translation keys - for development only"""
    try:
        # Set the current language properly
        current_language = st.session_state.get('language', 'en')
        if current_language in LANGUAGES:
            set_language(current_language)
            initialize()
    except Exception as e:
        logger.error(f"DEBUG_TRANSLATIONS - Error: {e}")

def render_login_interface():
    """Render the complete login interface - preserving original design from app.py"""
    
    # Load custom CSS to hide unwanted navigation buttons
    try:
        with open("static/custom.css") as st_css:
            st.markdown(f'<style>{st_css.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # File doesn't exist, skip custom CSS
        pass

    # Create top-right language switcher in a container with minimal style
    lang_col1, lang_col2, lang_col3 = st.columns([6, 3, 1])
    with lang_col3:
        # Create a clean language selector in the top-right
        st.markdown("""
        <div style="float: right; margin-right: 10px; margin-top: 5px;">
            <span style="font-size: 1em; margin-right: 5px;">🌐</span>
        </div>
        """, unsafe_allow_html=True)
        # Add a simple language dropdown
        current_language = st.session_state.get('language', 'en')
        language_options = {"en": "🇬🇧 English", "nl": "🇳🇱 Nederlands"}
        selected_language = st.selectbox(
            "",
            options=list(language_options.keys()),
            format_func=lambda x: language_options[x],
            index=0 if current_language == "en" else 1,
            key="lang_selector_top",
            label_visibility="collapsed"
        )
        if selected_language != current_language:
            st.session_state['language'] = selected_language
            st.session_state['_persistent_language'] = selected_language
            from utils.i18n import set_language, initialize
            set_language(selected_language)
            initialize()
            # Set flag to trigger rerun on next app cycle (avoids no-op warning)
            st.session_state['_trigger_rerun'] = True

    # Authentication sidebar with professional colorful design
    with st.sidebar:
        # Ensure translations are initialized with the current language
        current_language = st.session_state.get('language', 'en')
        from utils.i18n import set_language
        set_language(current_language)
        
        # Header with gradient background and professional name
        # Get translations or use defaults if translations aren't loaded yet
        title = _("app.title", "DataGuardian Pro")
        subtitle = _("app.subtitle", "Enterprise Privacy Compliance Platform")
        
        st.markdown(f"""
        <div style="background-image: linear-gradient(120deg, #6200EA, #3700B3); 
                   padding: 20px; border-radius: 15px; margin-bottom: 20px; text-align: center;
                   box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h2 style="color: white; margin: 0; font-weight: bold;">{title}</h2>
            <p style="color: #E9DAFF; margin: 5px 0 0 0; font-size: 0.9em;">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Meaningful GDPR theme with privacy-focused visual
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 25px; padding: 0 10px;">
            <div style="background-image: linear-gradient(120deg, #F5F0FF, #E9DAFF); 
                       border-radius: 12px; padding: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                    <div style="background-image: linear-gradient(120deg, #6200EA, #3700B3); 
                               width: 40px; height: 40px; border-radius: 8px; display: flex; 
                               justify-content: center; align-items: center; margin-right: 10px;">
                        <span style="color: white; font-size: 20px;">🔒</span>
                    </div>
                    <div style="background-image: linear-gradient(120deg, #00BFA5, #00897B); 
                               width: 40px; height: 40px; border-radius: 8px; display: flex; 
                               justify-content: center; align-items: center; margin-right: 10px;">
                        <span style="color: white; font-size: 20px;">📊</span>
                    </div>
                    <div style="background-image: linear-gradient(120deg, #FF6D00, #E65100); 
                               width: 40px; height: 40px; border-radius: 8px; display: flex; 
                               justify-content: center; align-items: center;">
                        <span style="color: white; font-size: 20px;">📋</span>
                    </div>
                </div>
                <p style="color: #4527A0; font-size: 0.9em; margin: 0; text-align: center;">
                    {_("app.tagline")}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Original tab-based login interface
        render_original_login_tabs()


def render_original_login_tabs():
    """Render the original tab-based login interface from app.py"""
    # Tab UI for login/register with colorful styling
    st.markdown("""
    <style>
    .tab-selected {
        background-color: #6200EA !important;
        color: white !important;
        font-weight: bold;
        border-radius: 5px;
        padding: 10px 0;
    }
    .tab-not-selected {
        background-color: #F5F0FF;
        color: #4527A0;
        border-radius: 5px;
        padding: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.columns(2)
    
    with tab1:
        if st.button(_("sidebar.sign_in"), key="tab_login", width="stretch"):
            st.session_state.active_tab = "login"
    
    with tab2:
        if st.button(_("sidebar.create_account"), key="tab_register", width="stretch"):
            st.session_state.active_tab = "register"
    
    # Default to login tab if not set
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "login"
        
    # Apply custom styling to selected tab
    if st.session_state.active_tab == "login":
        st.markdown("""
        <style>
        [data-testid="stButton"] button:nth-child(1) {
            background-color: #6200EA;
            color: white;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:nth-child(2) {
            background-color: #6200EA;
            color: white;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Render the appropriate tab content
    if st.session_state.active_tab == "login":
        render_signin_tab()
    else:
        render_signup_tab()

def render_signin_tab():
    """Render sign-in tab content - sidebar-compatible version"""
    st.subheader(_("login.signin", "Sign In"))
    
    # Main login form
    with st.form("login_form"):
        username_or_email = st.text_input(_("login.username_email", "Username or Email"))
        password = st.text_input(_("login.password", "Password"), type="password")
        login_button = st.form_submit_button(_("login.signin", "Sign In"))
    
    if login_button:
        user_data = authenticate(username_or_email, password)
        if user_data:
            st.session_state.authenticated = True
            st.session_state.logged_in = True
            st.session_state.user_data = user_data
            st.session_state.username = user_data['username']
            st.session_state.user_role = user_data['role']
            st.session_state.role = user_data['role']  # Also set 'role' key for permission checks
            st.session_state.user_email = user_data['email']
            st.session_state.permissions = user_data.get('permissions', [])  # Critical: Set user permissions
            
            # Initialize session manager (static class - no instantiation needed)
            from utils.session_manager import SessionManager
            # SessionManager uses static methods, no instantiation required
            user_id = SessionManager.get_user_id()
            
            # Handle language forcing after login
            if 'force_language_after_login' in st.session_state:
                handle_forced_language_after_login()
            
            st.success(_("login.success", "Login successful!"))
            # Note: st.rerun() removed from form submission to avoid no-op warning
            # The app will automatically rerun due to session state changes
        else:
            st.error(_("login.invalid", "Invalid username/email or password"))
    
    # Password Reset Section
    with st.expander(_("login.forgot_password", "Forgot Password?")):
        st.subheader(_("login.reset_password", "Reset Password"))
        reset_email = st.text_input(_("login.email", "Email"), key="reset_email")
        new_password = st.text_input(_("login.new_password", "New Password"), type="password", key="reset_new_password")
        confirm_password = st.text_input(_("login.confirm_password", "Confirm Password"), type="password", key="reset_confirm_password")
        
        if st.button(_("login.reset_submit", "Reset Password"), key="reset_submit"):
            if new_password != confirm_password:
                st.error(_("login.password_mismatch", "Passwords don't match"))
            elif len(new_password) < 6:
                st.error(_("login.password_too_short", "Password must be at least 6 characters"))
            else:
                # Implement password reset logic
                if reset_email and new_password:
                    from services.auth import reset_password
                    success, message = reset_password(reset_email, new_password)
                    if success:
                        st.success(_("login.password_reset_success", "Password reset successful! Please sign in."))
                    else:
                        st.error(f"{_('login.reset_failed', 'Reset failed')}: {message}")
        
        st.info(_("login.reset_instructions", "Enter your email and new password to reset your account."))

def render_signup_tab():
    """Render sign-up tab content - sidebar-compatible version"""
    st.subheader(_("register.signup", "Sign Up"))
    
    # Role selection
    role_options = {
        'user': _("roles.user", "User - Basic scanning permissions"),
        'analyst': _("roles.analyst", "Analyst - Advanced analysis capabilities"),
        'manager': _("roles.manager", "Manager - Team management features"),
        'admin': _("roles.admin", "Admin - Full system access"),
        'viewer': _("roles.viewer", "Viewer - Read-only access"),
        'developer': _("roles.developer", "Developer - API access"),
        'security_officer': _("roles.security_officer", "Security Officer - Security oversight"),
        'data_protection_officer': _("roles.dpo", "Data Protection Officer - Privacy compliance")
    }
    
    with st.form("register_form"):
        new_username = st.text_input(_("register.username", "Username"))
        new_email = st.text_input(_("register.email", "Email"))
        new_password = st.text_input(_("register.password", "Password"), type="password")
        new_role = st.selectbox(_("register.role", "Role"), options=list(role_options.keys()), format_func=lambda x: role_options[x])
        confirm_password = st.text_input(_("register.confirm_password", "Confirm Password"), type="password")
        terms = st.checkbox(_("register.terms", "I agree to the Terms of Service and Privacy Policy"))
        register_button = st.form_submit_button(_("register.signup", "Sign Up"))
    
    if register_button:
        success, message = create_user(new_username, new_password, new_role, new_email)
        if success:
            st.success(_("register.success", "Account created successfully! Please sign in."))
        else:
            st.error(f"{_('register.failed', 'Registration failed')}: {message}")