#!/usr/bin/env python3
"""
User Management UI Component for DataGuardian Pro Admin Panel
Provides comprehensive user management, role assignment, usage tracking, and billing verification
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def render_user_management_panel():
    """Render the complete user management panel"""
    try:
        from services.user_management_service import get_user_management_service, TIER_LIMITS, ROLE_DESCRIPTIONS
        
        ums = get_user_management_service()
        
        st.markdown("### 👥 User Management")
        
        # Sub-tabs for different functions
        subtab1, subtab2, subtab3, subtab4 = st.tabs([
            "📋 User List", 
            "➕ Create User", 
            "📊 Usage & Billing", 
            "📈 Statistics"
        ])
        
        with subtab1:
            render_user_list(ums)
        
        with subtab2:
            render_create_user_form(ums)
        
        with subtab3:
            render_usage_billing(ums)
        
        with subtab4:
            render_user_statistics(ums)
            
    except Exception as e:
        logger.error(f"Error rendering user management panel: {e}")
        st.error(f"Error loading user management: {e}")
        st.info("Please ensure the database is properly configured.")


def render_user_list(ums):
    """Render user list with filters and actions"""
    from services.user_management_service import TIER_LIMITS, ROLE_DESCRIPTIONS
    
    st.markdown("#### Active Users")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        role_filter = st.selectbox(
            "Filter by Role",
            ["All Roles"] + list(ROLE_DESCRIPTIONS.keys()),
            key="user_role_filter"
        )
    
    with col2:
        tier_filter = st.selectbox(
            "Filter by Tier",
            ["All Tiers"] + list(TIER_LIMITS.keys()),
            key="user_tier_filter"
        )
    
    with col3:
        include_inactive = st.checkbox("Include Inactive", key="include_inactive_users")
    
    with col4:
        if st.button("🔄 Refresh", key="refresh_users"):
            st.rerun()
    
    # Get users with filters
    users = ums.list_users(
        include_inactive=include_inactive,
        role_filter=role_filter if role_filter != "All Roles" else None,
        tier_filter=tier_filter if tier_filter != "All Tiers" else None
    )
    
    if not users:
        st.info("No users found. Create your first user in the 'Create User' tab.")
        return
    
    # Display users in a table
    user_data = []
    for user in users:
        user_data.append({
            "ID": user['id'],
            "Username": user['username'],
            "Email": user['email'],
            "Role": user['role'].replace('_', ' ').title(),
            "Tier": user['license_tier'].title(),
            "Company": user.get('company_name', '-'),
            "Status": "✅ Active" if user['is_active'] else "❌ Inactive",
            "Last Login": user.get('last_login', 'Never')[:10] if user.get('last_login') else 'Never',
            "Logins": user.get('login_count', 0)
        })
    
    df = pd.DataFrame(user_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # User actions
    st.markdown("---")
    st.markdown("#### User Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_user_id = st.selectbox(
            "Select User to Manage",
            options=[u['id'] for u in users],
            format_func=lambda x: next((u['username'] for u in users if u['id'] == x), str(x)),
            key="selected_user_manage"
        )
    
    if selected_user_id:
        selected_user = next((u for u in users if u['id'] == selected_user_id), None)
        
        if selected_user:
            with col2:
                action = st.selectbox(
                    "Action",
                    ["View Details", "Edit User", "View Usage", "Check Billing", "Deactivate"],
                    key="user_action"
                )
            
            if action == "View Details":
                render_user_details(selected_user, ums)
            elif action == "Edit User":
                render_edit_user_form(selected_user, ums)
            elif action == "View Usage":
                render_user_usage(selected_user, ums)
            elif action == "Check Billing":
                render_user_billing(selected_user, ums)
            elif action == "Deactivate":
                render_deactivate_user(selected_user, ums)
    
    # Export functionality
    st.markdown("---")
    if st.button("📥 Export Users to CSV", key="export_users"):
        csv_data = ums.export_users_csv()
        if csv_data:
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"users_export_{date.today().isoformat()}.csv",
                mime="text/csv",
                key="download_users_csv"
            )


def render_user_details(user: Dict, ums):
    """Render detailed user information"""
    st.markdown(f"##### 👤 User Details: {user['username']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Username:** {user['username']}  
        **Email:** {user['email']}  
        **Role:** {user['role'].replace('_', ' ').title()}  
        **Company:** {user.get('company_name', '-')}
        """)
    
    with col2:
        st.markdown(f"""
        **License Tier:** {user['license_tier'].title()}  
        **Status:** {'Active' if user['is_active'] else 'Inactive'}  
        **Last Login:** {str(user.get('last_login', 'Never'))[:19]}  
        **Total Logins:** {user.get('login_count', 0)}
        """)
    
    # Recent activity
    st.markdown("**Recent Activity:**")
    activity = ums.get_user_activity(user['id'], limit=5)
    if activity:
        for act in activity:
            st.text(f"• {act['action_type']}: {act.get('action_details', '')} ({str(act['created_at'])[:16]})")
    else:
        st.text("No recent activity")


def render_edit_user_form(user: Dict, ums):
    """Render edit user form"""
    from services.user_management_service import TIER_LIMITS, ROLE_DESCRIPTIONS
    
    st.markdown(f"##### ✏️ Edit User: {user['username']}")
    
    with st.form(f"edit_user_{user['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input("Email", value=user['email'])
            new_role = st.selectbox(
                "Role",
                options=list(ROLE_DESCRIPTIONS.keys()),
                index=list(ROLE_DESCRIPTIONS.keys()).index(user['role']) if user['role'] in ROLE_DESCRIPTIONS else 0
            )
            new_company = st.text_input("Company Name", value=user.get('company_name', ''))
        
        with col2:
            new_tier = st.selectbox(
                "License Tier",
                options=list(TIER_LIMITS.keys()),
                index=list(TIER_LIMITS.keys()).index(user['license_tier']) if user['license_tier'] in TIER_LIMITS else 0
            )
            new_password = st.text_input("New Password (leave blank to keep current)", type="password")
            is_active = st.checkbox("Active", value=user['is_active'])
        
        submitted = st.form_submit_button("💾 Save Changes")
        
        if submitted:
            updates = {
                'email': new_email,
                'role': new_role,
                'company_name': new_company,
                'license_tier': new_tier,
                'is_active': is_active
            }
            
            if new_password:
                updates['password'] = new_password
            
            current_user = st.session_state.get('username', 'admin')
            success, message = ums.update_user(user['id'], updates, updated_by=current_user)
            
            if success:
                st.success(f"✅ {message}")
                st.rerun()
            else:
                st.error(f"❌ {message}")


def render_user_usage(user: Dict, ums):
    """Render user usage statistics"""
    st.markdown(f"##### 📊 Usage Statistics: {user['username']}")
    
    # Get remaining scans
    remaining = ums.get_remaining_scans(user['id'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Scans Used", remaining['used'])
    
    with col2:
        st.metric("Scan Limit", remaining['limit'])
    
    with col3:
        if remaining['limit'] != 'Unlimited':
            percentage = (remaining['used'] / remaining['limit'] * 100) if remaining['limit'] > 0 else 0
            st.metric("Usage %", f"{percentage:.1f}%")
        else:
            st.metric("Status", "Unlimited")
    
    # Usage breakdown
    st.markdown("**Scanner Usage This Month:**")
    usage = ums.get_usage_summary(user['id'], "month")
    
    scanner_data = usage.get('scanner_breakdown', {})
    if scanner_data:
        df = pd.DataFrame([
            {"Scanner": k.replace('_', ' ').title(), "Count": v}
            for k, v in scanner_data.items()
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No scanner usage this month")
    
    # Feature usage
    feature_data = usage.get('feature_breakdown', {})
    if feature_data:
        st.markdown("**Feature Usage:**")
        df = pd.DataFrame([
            {"Feature": k.replace('_', ' ').title(), "Count": v}
            for k, v in feature_data.items()
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_user_billing(user: Dict, ums):
    """Render user billing compliance check"""
    from services.user_management_service import TIER_LIMITS
    
    st.markdown(f"##### 💰 Billing Check: {user['username']}")
    
    compliance = ums.verify_billing_compliance(user['id'])
    
    tier_info = TIER_LIMITS.get(user['license_tier'], {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Current Tier:** {user['license_tier'].title()}  
        **Monthly Price:** €{tier_info.get('price_monthly', 0)}  
        **Scan Limit:** {tier_info.get('scans_per_month', 0) if tier_info.get('scans_per_month', 0) != -1 else 'Unlimited'}  
        **User Limit:** {tier_info.get('users', 0) if tier_info.get('users', 0) != -1 else 'Unlimited'}
        """)
    
    with col2:
        scan_usage = compliance.get('scan_usage', {})
        st.markdown(f"""
        **Scans Used:** {scan_usage.get('used', 0)}  
        **Scan Limit:** {scan_usage.get('limit', 0)}  
        **Usage %:** {scan_usage.get('percentage', 0)}%
        """)
    
    # Compliance status
    if compliance.get('compliant', True):
        st.success("✅ User is within billing limits - correctly billed")
    else:
        st.error("⚠️ Usage exceeds tier limits")
        for issue in compliance.get('issues', []):
            st.warning(f"• {issue}")
        
        if compliance.get('recommended_tier'):
            st.info(f"💡 Recommended tier: **{compliance['recommended_tier'].title()}**")


def render_deactivate_user(user: Dict, ums):
    """Render user deactivation confirmation"""
    st.markdown(f"##### ⚠️ Deactivate User: {user['username']}")
    
    st.warning("This will deactivate the user account. The user will no longer be able to log in.")
    
    if st.button("🗑️ Confirm Deactivation", key=f"confirm_deactivate_{user['id']}"):
        current_user = st.session_state.get('username', 'admin')
        success, message = ums.delete_user(user['id'], deleted_by=current_user)
        
        if success:
            st.success(f"✅ {message}")
            st.rerun()
        else:
            st.error(f"❌ {message}")


def render_create_user_form(ums):
    """Render create new user form"""
    from services.user_management_service import TIER_LIMITS, ROLE_DESCRIPTIONS
    
    st.markdown("#### ➕ Create New User")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username *", placeholder="john.doe")
            email = st.text_input("Email *", placeholder="john.doe@company.com")
            password = st.text_input("Password *", type="password")
            confirm_password = st.text_input("Confirm Password *", type="password")
        
        with col2:
            role = st.selectbox(
                "Role *",
                options=list(ROLE_DESCRIPTIONS.keys()),
                format_func=lambda x: f"{x.replace('_', ' ').title()} - {ROLE_DESCRIPTIONS[x][:50]}..."
            )
            license_tier = st.selectbox(
                "License Tier *",
                options=list(TIER_LIMITS.keys()),
                format_func=lambda x: f"{x.title()} (€{TIER_LIMITS[x]['price_monthly']}/mo)"
            )
            company_name = st.text_input("Company Name", placeholder="Company Ltd.")
        
        submitted = st.form_submit_button("✅ Create User")
        
        if submitted:
            # Validation
            errors = []
            
            if not username or len(username) < 3:
                errors.append("Username must be at least 3 characters")
            
            if not email or '@' not in email:
                errors.append("Valid email is required")
            
            if not password or len(password) < 6:
                errors.append("Password must be at least 6 characters")
            
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                current_user = st.session_state.get('username', 'admin')
                success, message, user_id = ums.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role,
                    company_name=company_name,
                    license_tier=license_tier,
                    created_by=current_user
                )
                
                if success:
                    st.success(f"✅ {message} (ID: {user_id})")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")


def render_usage_billing(ums):
    """Render usage and billing overview"""
    from services.user_management_service import TIER_LIMITS
    
    st.markdown("#### 📊 Usage & Billing Overview")
    
    # Generate billing report
    if st.button("🔄 Generate Billing Report", key="gen_billing_report"):
        with st.spinner("Generating billing report..."):
            report = ums.generate_billing_report()
            
            if report:
                st.session_state['billing_report'] = report
    
    # Display report if available
    report = st.session_state.get('billing_report', [])
    
    if report:
        # Summary metrics
        total_users = len(report)
        compliant_users = sum(1 for r in report if r.get('compliant', True))
        non_compliant = total_users - compliant_users
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", total_users)
        with col2:
            st.metric("Compliant", compliant_users, delta_color="normal")
        with col3:
            st.metric("Over Limit", non_compliant, delta_color="inverse" if non_compliant > 0 else "normal")
        with col4:
            total_revenue = sum(TIER_LIMITS.get(r.get('tier', 'trial'), {}).get('price_monthly', 0) for r in report)
            st.metric("Monthly Revenue", f"€{total_revenue:,.0f}")
        
        st.markdown("---")
        
        # Non-compliant users
        if non_compliant > 0:
            st.markdown("##### ⚠️ Users Exceeding Limits")
            
            non_compliant_users = [r for r in report if not r.get('compliant', True)]
            for user in non_compliant_users:
                with st.expander(f"🔴 {user.get('username', 'Unknown')} - {user.get('tier', 'Unknown').title()}"):
                    st.markdown(f"**Email:** {user.get('email', '-')}")
                    st.markdown(f"**Company:** {user.get('company', '-')}")
                    st.markdown(f"**Issues:**")
                    for issue in user.get('issues', []):
                        st.warning(f"• {issue}")
                    st.markdown(f"**Recommended Tier:** {user.get('recommended_tier', '-').title()}")
        
        # All users table
        st.markdown("##### 📋 All Users Billing Status")
        
        billing_data = []
        for r in report:
            scan_usage = r.get('scan_usage', {})
            billing_data.append({
                "Username": r.get('username', '-'),
                "Tier": r.get('tier', '-').title(),
                "Price": f"€{r.get('tier_price', 0)}",
                "Scans Used": scan_usage.get('used', 0),
                "Scan Limit": scan_usage.get('limit', 'Unlimited'),
                "Usage %": f"{scan_usage.get('percentage', 0)}%",
                "Status": "✅ OK" if r.get('compliant', True) else "⚠️ Over Limit"
            })
        
        df = pd.DataFrame(billing_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Click 'Generate Billing Report' to see usage and billing data for all users.")


def render_user_statistics(ums):
    """Render user statistics dashboard"""
    from services.user_management_service import TIER_LIMITS, ROLE_DESCRIPTIONS
    
    st.markdown("#### 📈 User Statistics")
    
    # Get user counts
    counts = ums.get_user_count()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Active Users", counts.get('total', 0))
    
    with col2:
        admin_count = counts.get('by_role', {}).get('admin', 0)
        st.metric("Administrators", admin_count)
    
    with col3:
        enterprise_count = counts.get('by_tier', {}).get('enterprise', 0) + counts.get('by_tier', {}).get('scale', 0)
        st.metric("Enterprise Users", enterprise_count)
    
    st.markdown("---")
    
    # Users by Role
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Users by Role")
        role_data = counts.get('by_role', {})
        if role_data:
            df = pd.DataFrame([
                {"Role": k.replace('_', ' ').title(), "Count": v}
                for k, v in role_data.items()
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No users found")
    
    with col2:
        st.markdown("##### Users by Tier")
        tier_data = counts.get('by_tier', {})
        if tier_data:
            df = pd.DataFrame([
                {"Tier": k.title(), "Count": v, "Price": f"€{TIER_LIMITS.get(k, {}).get('price_monthly', 0)}/mo"}
                for k, v in tier_data.items()
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No users found")
    
    # Revenue calculation
    st.markdown("---")
    st.markdown("##### 💰 Revenue Summary")
    
    tier_counts = counts.get('by_tier', {})
    total_mrr = 0
    revenue_breakdown = []
    
    for tier, count in tier_counts.items():
        price = TIER_LIMITS.get(tier, {}).get('price_monthly', 0)
        tier_revenue = price * count
        total_mrr += tier_revenue
        revenue_breakdown.append({
            "Tier": tier.title(),
            "Users": count,
            "Price/User": f"€{price}",
            "Tier Revenue": f"€{tier_revenue:,.0f}"
        })
    
    if revenue_breakdown:
        df = pd.DataFrame(revenue_breakdown)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monthly Recurring Revenue", f"€{total_mrr:,.0f}")
        with col2:
            st.metric("Annual Recurring Revenue", f"€{total_mrr * 12:,.0f}")
        with col3:
            avg_revenue = total_mrr / counts.get('total', 1) if counts.get('total', 0) > 0 else 0
            st.metric("Avg Revenue/User", f"€{avg_revenue:.0f}")


def render_system_settings_panel():
    """Render system settings panel"""
    st.markdown("### ⚙️ System Settings")
    
    st.markdown("#### Application Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**General Settings**")
        st.text_input("Application Name", value="DataGuardian Pro", disabled=True)
        st.text_input("Support Email", value="support@dataguardianpro.nl")
        st.selectbox("Default Language", ["English", "Dutch"])
    
    with col2:
        st.markdown("**Security Settings**")
        st.number_input("Session Timeout (minutes)", value=30, min_value=5, max_value=480)
        st.number_input("Max Login Attempts", value=5, min_value=3, max_value=10)
        st.checkbox("Require 2FA for Admins", value=False)
    
    st.markdown("---")
    
    st.markdown("#### Database Status")
    
    try:
        from services.user_management_service import get_user_management_service
        ums = get_user_management_service()
        counts = ums.get_user_count()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Database Users", counts.get('total', 0))
        with col2:
            st.success("✅ Database Connected")
        with col3:
            st.info("PostgreSQL")
    except Exception as e:
        st.error(f"Database connection issue: {e}")
    
    st.markdown("---")
    
    if st.button("💾 Save Settings", disabled=True):
        st.info("Settings saved!")
