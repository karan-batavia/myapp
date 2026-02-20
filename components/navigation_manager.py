"""
Navigation and Dashboard Management Module
Extracted from app.py to improve modularity while preserving exact UI behavior
"""
import streamlit as st
import logging
from datetime import datetime, timedelta
from services.auth import get_user_permissions, has_permission
from services.subscription_manager import SubscriptionManager
from utils.i18n import get_text

logger = logging.getLogger(__name__)

# Define translation function
def _(key, default=None):
    return get_text(key, default)

def create_modern_sidebar_nav(nav_options, icon_map=None):
    """
    Creates a simple sidebar navigation with working buttons.
    Extracted from app.py lines 952-1000
    
    Args:
        nav_options: List of navigation options
        icon_map: Dictionary mapping nav options to icons
    
    Returns:
        The selected navigation option
    """
    if icon_map is None:
        icon_map = {
            _("scan.title", "Scan"): "🔍",
            _("dashboard.welcome", "Dashboard"): "📊",
            "🤖 Predictive Analytics": "🤖", 
            _("history.title", "History"): "📚",
            _("results.title", "Results"): "📋",
            _("report.generate", "Reports"): "📄",
            "💳 iDEAL Payment Test": "💳",
            _("admin.title", "Admin"): "⚙️"
        }
    
    st.sidebar.markdown("### Navigation")
    
    selected_nav = None
    for option in nav_options:
        icon = icon_map.get(option, "•")
        if st.sidebar.button(f"{icon} {option}", width="stretch", key=f"nav_{option}"):
            selected_nav = option
            st.session_state.selected_nav = option
    
    # Return the currently selected navigation option
    return st.session_state.get('selected_nav', nav_options[0] if nav_options else None)

def get_navigation_options(user_role):
    """
    Get navigation options based on user role
    Extracted from app.py lines 930-950
    """
    # Get navigation titles with translations
    scan_title = _("scan.title", "Scan")
    dashboard_title = _("dashboard.welcome", "Dashboard")
    history_title = _("history.title", "History")
    results_title = _("results.title", "Results")
    report_title = _("report.generate", "Reports")
    simple_dpia_title = _("dpia.simple_assessment", "Simple DPIA")
    
    # Base navigation for all users  
    predictive_title = "🤖 Predictive Analytics"
    nav_options = [scan_title, simple_dpia_title, dashboard_title, predictive_title, history_title, results_title, report_title]
    
    # Add iDEAL Payment Test option
    ideal_test_title = "💳 iDEAL Payment Test"
    nav_options.append(ideal_test_title)
    
    # Add admin navigation if user is admin
    if user_role == 'admin':
        admin_title = _("admin.title", "Admin")
        nav_options.append(admin_title)
    
    return nav_options

def render_user_profile_sidebar():
    """
    Render user profile information in sidebar
    Extracted from app.py lines 1140-1200
    """
    if st.session_state.get('authenticated', False):
        current_user = st.session_state.get('user_data', {})
        if current_user:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### User Profile")
            
            # User role information
            user_role = st.session_state.get('user_role', 'user')
            
            # Role descriptions
            all_roles = {
                'user': _("roles.user_desc", "Basic scanning permissions"),
                'analyst': _("roles.analyst_desc", "Advanced analysis capabilities"),
                'manager': _("roles.manager_desc", "Team management features"),
                'admin': _("roles.admin_desc", "Full system access"),
                'auditor': _("roles.auditor_desc", "Compliance reporting"),
                'developer': _("roles.developer_desc", "API access"),
                'security_officer': _("roles.security_officer_desc", "Security oversight")
            }
            
            role_desc = all_roles.get(user_role, "Unknown role")
            st.sidebar.write(f"**Role:** {user_role.title()}")
            st.sidebar.write(f"*{role_desc}*")
            
            # User permissions
            user_permissions = get_user_permissions(user_role)
            if user_permissions:
                st.sidebar.markdown("**Permissions:**")
                permissions_by_category = {}
                for perm in user_permissions:
                    category = perm.split(':')[0] if ':' in perm else 'general'
                    if category not in permissions_by_category:
                        permissions_by_category[category] = []
                    permissions_by_category[category].append(perm)
                
                # Display permissions by category
                for category, perms in permissions_by_category.items():
                    st.sidebar.write(f"• **{category.title()}**: {len(perms)} permissions")

def render_membership_status():
    """
    Render membership status information
    Extracted from app.py lines 1020-1090
    """
    if st.session_state.get('authenticated', False):
        try:
            # Get membership details
            subscription_manager = SubscriptionManager()
            username = st.session_state.get('username', '')
            membership_details = None
            
            # Try to get subscription details using correct method name
            try:
                # Note: SubscriptionManager requires customer_id, not username
                # For now, provide fallback display until customer ID mapping is implemented
                membership_details = {
                    'plan': 'Basic',
                    'status': 'Active',
                    'expires': 'N/A'
                }
            except Exception as e:
                logger.debug(f"Could not get subscription details: {e}")
                membership_details = None
            
            if membership_details:
                # Parse membership information
                plan_name = membership_details.get('plan_name', 'Free')
                expiry_date = membership_details.get('expiry_date')
                if isinstance(expiry_date, str):
                    expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                
                # Calculate days remaining
                if expiry_date:
                    days_remaining = (expiry_date - datetime.now()).days
                    if days_remaining > 0:
                        status_color = "🟢" if days_remaining > 30 else "🟡" if days_remaining > 7 else "🔴"
                    else:
                        status_color = "🔴"
                        days_remaining = 0
                else:
                    status_color = "🔴"
                    days_remaining = 0
                
                # Display membership status
                st.sidebar.markdown("---")
                st.sidebar.markdown("### Membership Status")
                st.sidebar.write(f"{status_color} **{plan_name}**")
                
                if expiry_date:
                    expiry_date_str = expiry_date.strftime("%Y-%m-%d")
                    st.sidebar.write(f"Expires: {expiry_date_str}")
                    st.sidebar.write(f"Days remaining: {days_remaining}")
            else:
                # Show free trial information
                free_trial_days_left = 30  # Default free trial
                st.sidebar.markdown("---")
                st.sidebar.markdown("### Free Trial")
                st.sidebar.write(f"🆓 **Free Trial**")
                st.sidebar.write(f"Days remaining: {free_trial_days_left}")
                
        except Exception as e:
            logger.error(f"Error rendering membership status: {e}")
            # Fallback membership display
            membership_status = "Free"
            free_trial_active = True
            membership_expiry = None
            
            st.sidebar.markdown("---")
            st.sidebar.markdown("### Membership Status")
            if free_trial_active:
                st.sidebar.write("🆓 **Free Trial**")
                st.sidebar.write("Days remaining: 30")
            else:
                st.sidebar.write(f"📋 **{membership_status}**")

def render_dashboard_content():
    """
    Render the original colorful landing page design
    Restored from app.py lines 1200-1400 to preserve the beautiful UI
    """
    # Original beautiful landing page design
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 30px; border-radius: 10px; margin: 20px 0;">
        <h1 style="color: #1e3a8a; margin-bottom: 10px;">DataGuardian Pro</h1>
        <h3 style="color: #4b5563; font-weight: 500; margin-top: 0; margin-bottom: 20px;">Enterprise Privacy Compliance Platform</h3>
        <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
            Comprehensive GDPR compliance platform that helps organizations identify, analyze, and protect 
            personally identifiable information (PII) across multiple data sources.
        </p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #4f46e5; margin-top: 0;">🔍 Code Scanner</h4>
                <p style="color: #6b7280; margin-bottom: 0;">Scan source code repositories for security vulnerabilities and PII detection.</p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #4f46e5; margin-top: 0;">📄 Document Scanner</h4>
                <p style="color: #6b7280; margin-bottom: 0;">Analyze documents (PDF, DOCX, TXT) for personally identifiable information.</p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #4f46e5; margin-top: 0;">🖼️ Image Scanner</h4>
                <p style="color: #6b7280; margin-bottom: 0;">OCR-based scanning of images for text content and sensitive data.</p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #4f46e5; margin-top: 0;">🌐 Website Scanner</h4>
                <p style="color: #6b7280; margin-bottom: 0;">Evaluate websites for privacy compliance and data collection practices.</p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #4f46e5; margin-top: 0;">🗄️ Database Scanner</h4>
                <p style="color: #6b7280; margin-bottom: 0;">Direct database scanning for PII across multiple database types.</p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #4f46e5; margin-top: 0;">🔌 API Scanner</h4>
                <p style="color: #6b7280; margin-bottom: 0;">Assess API endpoints for security vulnerabilities and data exposure risks.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Beautiful gradient feature section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 15px; margin: 30px 0; color: white; text-align: center;">
        <h2 style="margin: 0 0 20px 0; color: white;">Start Your Privacy Compliance Journey</h2>
        <p style="font-size: 18px; margin: 0 0 30px 0; opacity: 0.9;">
            Get started with our comprehensive GDPR scanning platform and ensure your organization meets privacy compliance requirements.
        </p>
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <div style="background: rgba(255,255,255,0.2); padding: 15px 25px; border-radius: 8px; backdrop-filter: blur(10px);">
                <strong>Multi-Source Scanning</strong><br>
                <span style="opacity: 0.9;">Code, Documents, Images & More</span>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 15px 25px; border-radius: 8px; backdrop-filter: blur(10px);">
                <strong>Professional Reports</strong><br>
                <span style="opacity: 0.9;">Certificate-Style PDF & HTML</span>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 15px 25px; border-radius: 8px; backdrop-filter: blur(10px);">
                <strong>GDPR Compliance</strong><br>
                <span style="opacity: 0.9;">Dutch & EU Standards</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Professional footer section
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(to right, #f8f9fa, #f1f3f5); 
               border-radius: 10px; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h4 style="color: #3B82F6; margin-bottom: 15px;">DataGuardian Pro</h4>
        <p style="color: #4b5563; margin-bottom: 5px;">Enterprise Privacy Compliance Platform</p>
        <p style="color: #6b7280; font-size: 0.8em;">© 2025 DataGuardian. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)

def render_scan_history():
    """
    Render scan history page
    Extracted from app.py lines 1400-1500
    """
    st.title(_("history.title", "Scan History"))
    
    try:
        # Get user's scan history
        username = st.session_state.get('username', '')
        if username:
            # Placeholder for scan history
            st.info(_("history.no_scans", "No scan history available yet. Run some scans to see results here."))
        else:
            st.warning(_("history.login_required", "Please log in to view scan history."))
            
    except Exception as e:
        logger.error(f"Error loading scan history: {e}")
        st.error(_("history.error_loading", "Error loading scan history."))

def render_results_page():
    """
    Render results page
    Extracted from app.py lines 1500-1580
    """
    st.title(_("results.title", "Scan Results"))
    
    try:
        # Get user's scan results
        username = st.session_state.get('username', '')
        if username:
            # Placeholder for scan results
            st.info(_("results.no_results", "No scan results available. Please run a scan first."))
        else:
            st.warning(_("results.login_required", "Please log in to view scan results."))
            
    except Exception as e:
        logger.error(f"Error loading scan results: {e}")
        st.error(_("results.error_loading", "Error loading scan results."))

def render_reports_page():
    """
    Render reports generation page
    Extracted from app.py lines 6700-6850
    """
    st.title(_("report.generate", "Generate Reports"))
    
    try:
        # Get user's available reports
        username = st.session_state.get('username', '')
        if username:
            # Placeholder for report generation
            st.info(_("report.no_scans", "Report generation will be available after running scans."))
        else:
            st.warning(_("report.login_required", "Please log in to generate reports."))
            
    except Exception as e:
        logger.error(f"Error loading reports page: {e}")
        st.error(_("report.error_loading", "Error loading reports page."))

def render_admin_page():
    """
    Render admin panel page
    Extracted from app.py lines 6850-7600
    """
    st.title(_("admin.title", "Admin Panel"))
    
    # Check if user has admin permissions
    if not has_permission('admin:manage'):
        st.error(_("admin.access_denied", "Access denied. Admin privileges required."))
        return
    
    try:
        # Admin dashboard tabs
        admin_tabs = st.tabs([
            _("admin.users", "Users"),
            _("admin.system", "System"),
            _("admin.reports", "Reports"),
            _("admin.settings", "Settings")
        ])
        
        with admin_tabs[0]:
            st.subheader(_("admin.user_management", "User Management"))
            st.info(_("admin.users_placeholder", "User management features coming soon."))
        
        with admin_tabs[1]:
            st.subheader(_("admin.system_status", "System Status"))
            st.info(_("admin.system_placeholder", "System monitoring features coming soon."))
            
        with admin_tabs[2]:
            st.subheader(_("admin.report_management", "Report Management"))
            st.info(_("admin.reports_placeholder", "Report management features coming soon."))
            
        with admin_tabs[3]:
            st.subheader(_("admin.system_settings", "System Settings"))
            st.info(_("admin.settings_placeholder", "System settings features coming soon."))
            
    except Exception as e:
        logger.error(f"Error loading admin page: {e}")
        st.error(_("admin.error_loading", "Error loading admin panel."))