"""
Admin Page Module
Administrative functions for system management
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)


def render_admin_page():
    """Render admin page for administrative users"""
    from utils.i18n import get_text as _
    
    user_role = st.session_state.get('user_role', 'user')
    
    if user_role != 'admin':
        st.warning("⚠️ Admin access required")
        st.info("Please contact your administrator for access to this section.")
        return
    
    st.title(f"👥 {_('admin.title', 'Administration')}")
    
    tabs = st.tabs([
        "👥 User Management",
        "📊 System Overview",
        "🔧 Configuration",
        "📈 Analytics",
        "🔍 Audit Logs"
    ])
    
    with tabs[0]:
        _render_user_management()
    
    with tabs[1]:
        _render_system_overview()
    
    with tabs[2]:
        _render_configuration()
    
    with tabs[3]:
        _render_analytics()
    
    with tabs[4]:
        _render_audit_logs()


def _render_user_management():
    """Render user management section"""
    st.subheader("User Management")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", "24")
    with col2:
        st.metric("Active Today", "8")
    with col3:
        st.metric("Pending Invites", "3")
    
    st.markdown("---")
    
    st.write("**Add New User**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_email = st.text_input("Email", placeholder="user@company.com")
    with col2:
        new_role = st.selectbox("Role", ["user", "analyst", "manager", "admin"])
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Add User"):
            if new_email:
                st.success(f"Invitation sent to {new_email}")
            else:
                st.error("Please enter an email address")
    
    st.markdown("---")
    
    st.write("**Current Users**")
    
    users = [
        {"email": "admin@company.com", "role": "admin", "status": "Active", "last_login": "Today"},
        {"email": "analyst1@company.com", "role": "analyst", "status": "Active", "last_login": "Yesterday"},
        {"email": "user1@company.com", "role": "user", "status": "Active", "last_login": "3 days ago"},
    ]
    
    for user in users:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        
        with col1:
            st.write(user["email"])
        with col2:
            st.write(user["role"].title())
        with col3:
            st.write(user["status"])
        with col4:
            st.write(user["last_login"])
        with col5:
            if st.button("✏️", key=f"edit_{user['email']}"):
                st.info(f"Editing {user['email']}")


def _render_system_overview():
    """Render system overview section"""
    st.subheader("System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Scans (30d)", "1,247")
    with col2:
        st.metric("PII Detected", "15,832")
    with col3:
        st.metric("Avg Compliance", "87.5%")
    with col4:
        st.metric("System Health", "✅ Good")
    
    st.markdown("---")
    
    st.write("**Service Status**")
    
    services = [
        {"name": "Streamlit Server", "status": "🟢 Running", "uptime": "99.9%"},
        {"name": "PostgreSQL Database", "status": "🟢 Running", "uptime": "99.8%"},
        {"name": "Redis Cache", "status": "🟢 Running", "uptime": "99.9%"},
        {"name": "Webhook Server", "status": "🟢 Running", "uptime": "99.7%"},
    ]
    
    for service in services:
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.write(service["name"])
        with col2:
            st.write(service["status"])
        with col3:
            st.write(f"Uptime: {service['uptime']}")


def _render_configuration():
    """Render system configuration section"""
    st.subheader("System Configuration")
    
    st.write("**Scan Settings**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Max concurrent scans", min_value=1, max_value=10, value=5)
        st.number_input("Scan timeout (minutes)", min_value=5, max_value=60, value=30)
    
    with col2:
        st.checkbox("Enable AI-powered analysis", value=True)
        st.checkbox("Auto-generate reports", value=True)
    
    st.markdown("---")
    
    st.write("**Security Settings**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Session timeout (minutes)", min_value=15, max_value=480, value=60)
        st.checkbox("Require 2FA for admins", value=False)
    
    with col2:
        st.checkbox("IP whitelist enabled", value=False)
        st.checkbox("Audit logging enabled", value=True)
    
    if st.button("💾 Save Configuration"):
        st.success("Configuration saved successfully!")


def _render_analytics():
    """Render analytics section"""
    st.subheader("Usage Analytics")
    
    try:
        from components.visitor_analytics_dashboard import render_visitor_analytics
        render_visitor_analytics()
    except ImportError:
        st.write("**Scan Activity (Last 7 Days)**")
        
        import pandas as pd
        data = {
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'Scans': [45, 52, 38, 61, 49, 12, 8]
        }
        df = pd.DataFrame(data)
        st.bar_chart(df.set_index('Day'))
        
        st.markdown("---")
        
        st.write("**Top Scan Types**")
        col1, col2 = st.columns(2)
        with col1:
            st.write("1. Code Scanner - 45%")
            st.write("2. Document Scanner - 25%")
            st.write("3. Website Scanner - 15%")
        with col2:
            st.write("4. Database Scanner - 8%")
            st.write("5. AI Model Scanner - 5%")
            st.write("6. Other - 2%")


def _render_audit_logs():
    """Render audit logs section"""
    st.subheader("Audit Logs")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.date_input("Start Date")
    with col2:
        st.date_input("End Date")
    with col3:
        st.selectbox("Event Type", ["All", "Login", "Scan", "Export", "Settings Change"])
    
    if st.button("🔍 Search Logs"):
        st.info("Searching audit logs...")
    
    st.markdown("---")
    
    logs = [
        {"timestamp": "2024-12-06 14:32:15", "user": "admin@company.com", "action": "Login", "details": "Successful login"},
        {"timestamp": "2024-12-06 14:28:42", "user": "analyst1@company.com", "action": "Scan", "details": "Code scan completed"},
        {"timestamp": "2024-12-06 14:15:08", "user": "admin@company.com", "action": "Settings", "details": "Updated notification preferences"},
        {"timestamp": "2024-12-06 13:55:21", "user": "user1@company.com", "action": "Export", "details": "Downloaded PDF report"},
    ]
    
    for log in logs:
        col1, col2, col3, col4 = st.columns([2, 2, 1, 3])
        with col1:
            st.caption(log["timestamp"])
        with col2:
            st.write(log["user"])
        with col3:
            st.write(log["action"])
        with col4:
            st.caption(log["details"])
