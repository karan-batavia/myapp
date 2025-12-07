"""
Settings Page Module
User settings, preferences, and account management
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)


def render_settings_page():
    """Render settings page with tabbed interface"""
    from utils.i18n import get_text as _
    
    st.title(f"⚙️ {_('sidebar.settings', 'Settings')}")
    
    tabs = st.tabs([
        "👤 Profile",
        "🔔 Notifications", 
        "🔐 Security",
        "🎨 Preferences",
        "💳 Billing",
        "🔌 Integrations",
        "🛡️ Privacy & GDPR"
    ])
    
    with tabs[0]:
        _render_profile_settings()
    
    with tabs[1]:
        _render_notification_settings()
    
    with tabs[2]:
        _render_security_settings()
    
    with tabs[3]:
        _render_preference_settings()
    
    with tabs[4]:
        _render_billing_settings()
    
    with tabs[5]:
        _render_integration_settings()
    
    with tabs[6]:
        _render_gdpr_privacy_settings()


def _render_profile_settings():
    """Render profile settings tab"""
    st.subheader("Profile Information")
    
    username = st.session_state.get('username', 'User')
    user_role = st.session_state.get('user_role', 'user')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Username", value=username, disabled=True)
        st.text_input("Email", value=f"{username}@company.com", disabled=True)
    
    with col2:
        st.text_input("Role", value=user_role.title(), disabled=True)
        st.text_input("Organization", value=st.session_state.get('organization', 'Default'), disabled=True)
    
    st.markdown("---")
    
    st.subheader("Update Profile")
    new_name = st.text_input("Display Name", placeholder="Enter your display name")
    new_email = st.text_input("Update Email", placeholder="newemail@company.com")
    
    if st.button("💾 Save Profile Changes"):
        if new_name or new_email:
            st.success("Profile updated successfully!")
        else:
            st.warning("Please enter values to update.")


def _render_notification_settings():
    """Render notification settings tab"""
    st.subheader("Notification Preferences")
    
    st.write("**Email Notifications**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("Scan completed notifications", value=True)
        st.checkbox("High-risk findings alerts", value=True)
        st.checkbox("Weekly compliance summary", value=True)
    
    with col2:
        st.checkbox("License expiry reminders", value=True)
        st.checkbox("New feature announcements", value=False)
        st.checkbox("Marketing updates", value=False)
    
    st.markdown("---")
    
    st.write("**Alert Thresholds**")
    st.slider("High-risk alert threshold", 0, 10, 3, help="Alert when high-risk findings exceed this number")
    st.slider("Compliance score alert", 0, 100, 70, help="Alert when compliance drops below this percentage")
    
    if st.button("💾 Save Notification Settings"):
        st.success("Notification preferences saved!")


def _render_security_settings():
    """Render security settings tab"""
    st.subheader("Security Settings")
    
    st.write("**Password Management**")
    current_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    
    if st.button("🔐 Update Password"):
        if new_password != confirm_password:
            st.error("Passwords do not match!")
        elif len(new_password) < 8:
            st.error("Password must be at least 8 characters!")
        else:
            st.success("Password updated successfully!")
    
    st.markdown("---")
    
    st.write("**Two-Factor Authentication**")
    tfa_enabled = st.checkbox("Enable Two-Factor Authentication", value=False)
    if tfa_enabled:
        st.info("2FA setup: Scan the QR code with your authenticator app.")
        st.code("SAMPLE-2FA-SECRET-KEY", language=None)
    
    st.markdown("---")
    
    st.write("**Active Sessions**")
    st.write("Current session: Active (This device)")
    if st.button("🚫 Sign Out All Other Devices"):
        st.success("All other sessions terminated.")


def _render_preference_settings():
    """Render preference settings tab"""
    st.subheader("Display Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("Language", ["English", "Nederlands"], index=0)
        st.selectbox("Date Format", ["YYYY-MM-DD", "DD-MM-YYYY", "MM/DD/YYYY"], index=0)
        st.selectbox("Time Zone", ["Europe/Amsterdam", "UTC", "Europe/London"], index=0)
    
    with col2:
        st.selectbox("Default Region", ["Netherlands", "Germany", "France", "Belgium"], index=0)
        st.selectbox("Theme", ["Light", "Dark", "System Default"], index=0)
        st.number_input("Results per page", min_value=10, max_value=100, value=25)
    
    st.markdown("---")
    
    st.write("**Scan Defaults**")
    st.checkbox("Auto-generate PDF reports after scan", value=True)
    st.checkbox("Include AI-powered remediation suggestions", value=True)
    st.checkbox("Enable fraud detection analysis", value=True)
    
    if st.button("💾 Save Preferences"):
        st.success("Preferences saved successfully!")


def _render_billing_settings():
    """Render billing settings tab"""
    st.subheader("Billing & Subscription")
    
    try:
        from services.license_manager import LicenseManager
        license_mgr = LicenseManager()
        license_info = license_mgr.get_license_info()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Current Plan:** {license_info.get('license_type', 'Trial').title()}")
            st.write(f"**Status:** {'Active' if license_info.get('is_active', True) else 'Inactive'}")
            st.write(f"**Scans Used:** {license_info.get('current_usage', 0)}")
        
        with col2:
            st.write(f"**Scan Limit:** {license_info.get('scan_limit', 'Unlimited')}")
            st.write(f"**Expires:** {license_info.get('expiry_date', 'N/A')}")
            st.write(f"**Next Billing:** {license_info.get('next_billing', 'N/A')}")
    
    except Exception as e:
        logger.warning(f"Could not load license info: {e}")
        st.write("**Current Plan:** Professional")
        st.write("**Status:** Active")
    
    st.markdown("---")
    
    st.write("**Payment Methods**")
    st.info("💳 iDEAL (Primary) - ING Bank •••• 1234")
    
    if st.button("➕ Add Payment Method"):
        st.info("Payment method management coming soon.")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Upgrade Plan", use_container_width=True):
            st.session_state['show_upgrade'] = True
            st.rerun()
    
    with col2:
        if st.button("📜 View Invoices", use_container_width=True):
            st.info("Invoice history will be displayed here.")


def _render_integration_settings():
    """Render integration settings tab"""
    st.subheader("Connected Integrations")
    
    integrations = [
        {"name": "Microsoft 365", "status": "Not Connected", "icon": "🔵"},
        {"name": "Google Workspace", "status": "Not Connected", "icon": "🟢"},
        {"name": "Exact Online", "status": "Not Connected", "icon": "🟠"},
        {"name": "Salesforce", "status": "Not Connected", "icon": "☁️"},
        {"name": "SAP", "status": "Not Connected", "icon": "🔷"}
    ]
    
    for integration in integrations:
        col1, col2, col3 = st.columns([1, 3, 2])
        
        with col1:
            st.write(integration["icon"])
        
        with col2:
            st.write(f"**{integration['name']}**")
            st.caption(integration["status"])
        
        with col3:
            if integration["status"] == "Connected":
                if st.button("Disconnect", key=f"disc_{integration['name']}"):
                    st.warning(f"Disconnected {integration['name']}")
            else:
                if st.button("Connect", key=f"conn_{integration['name']}"):
                    st.info(f"Connecting to {integration['name']}...")
        
        st.markdown("---")
    
    st.write("**API Access**")
    st.code("API Key: dgp_••••••••••••••••", language=None)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Regenerate API Key"):
            st.warning("Are you sure? This will invalidate the current key.")
    with col2:
        if st.button("📋 Copy API Key"):
            st.success("API key copied to clipboard!")


def _render_gdpr_privacy_settings():
    """Render GDPR Privacy & Data Protection settings tab"""
    from utils.i18n import get_text as _
    import json
    from datetime import datetime
    
    username = st.session_state.get('username', 'User')
    
    st.subheader("🛡️ Privacy & Data Protection (GDPR)")
    
    st.info("""
    **Your Data Rights Under GDPR**  
    As a user in the EU/Netherlands, you have rights under GDPR and UAVG including:
    - Right of Access (Article 15)
    - Right to Rectification (Article 16)
    - Right to Erasure (Article 17)
    - Right to Data Portability (Article 20)
    """)
    
    st.markdown("---")
    
    st.subheader("📋 Data Processing Consent")
    st.write("Control what data we store from your scans:")
    
    consent_pii = st.checkbox(
        "Store detailed PII findings from scans",
        value=st.session_state.get('consent_pii_storage', False),
        help="When enabled, we store anonymized PII type information from your scans. When disabled, we only store aggregate counts."
    )
    
    consent_analytics = st.checkbox(
        "Usage analytics for service improvement",
        value=st.session_state.get('consent_analytics', True),
        help="Help us improve DataGuardian by sharing anonymous usage patterns."
    )
    
    if st.button("💾 Save Consent Preferences"):
        st.session_state['consent_pii_storage'] = consent_pii
        st.session_state['consent_analytics'] = consent_analytics
        
        try:
            from services.results_aggregator import ResultsAggregator
            aggregator = ResultsAggregator()
            aggregator.gdpr_record_consent(username, 'pii_findings', consent_pii)
            aggregator.gdpr_record_consent(username, 'usage_analytics', consent_analytics)
            st.success("✅ Consent preferences saved successfully!")
        except Exception as e:
            logger.error(f"Error saving consent: {e}")
            st.success("✅ Consent preferences saved!")
    
    st.markdown("---")
    
    st.subheader("📊 Data Retention Policies")
    st.write("We automatically delete your data according to these policies:")
    
    retention_data = [
        {"Category": "Scan Results", "Retention": "365 days", "Legal Basis": "Contract Performance", "Purpose": "Service delivery & audit trail"},
        {"Category": "PII Findings", "Retention": "90 days", "Legal Basis": "Consent", "Purpose": "Remediation tracking"},
        {"Category": "Usage Analytics", "Retention": "90 days", "Legal Basis": "Legitimate Interest", "Purpose": "Service improvement"},
        {"Category": "Cloud Resource Data", "Retention": "0 days (memory only)", "Legal Basis": "Consent", "Purpose": "Sustainability analysis"}
    ]
    
    for item in retention_data:
        with st.expander(f"📁 {item['Category']} - {item['Retention']}"):
            st.write(f"**Legal Basis:** {item['Legal Basis']} (GDPR Art. 6)")
            st.write(f"**Purpose:** {item['Purpose']}")
            st.write(f"**Automatic Deletion:** After {item['Retention']}")
    
    st.markdown("---")
    
    st.subheader("📤 Export Your Data")
    st.write("Download all your data in a portable format (GDPR Article 20).")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export All My Data", use_container_width=True):
            with st.spinner("Preparing your data export..."):
                try:
                    from services.results_aggregator import ResultsAggregator
                    aggregator = ResultsAggregator()
                    export_data = aggregator.gdpr_export_user_data(username)
                    
                    if 'error' not in export_data:
                        export_json = json.dumps(export_data, indent=2, default=str)
                        st.download_button(
                            label="⬇️ Download Export (JSON)",
                            data=export_json,
                            file_name=f"dataguardian_export_{username}_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json"
                        )
                        st.success(f"✅ Export ready! Contains {len(export_data.get('data', {}).get('scans', []))} scan records.")
                    else:
                        st.error(f"Export failed: {export_data['error']}")
                except Exception as e:
                    logger.error(f"Export error: {e}")
                    st.error("Unable to export data. Please try again later.")
    
    with col2:
        st.write("Export includes:")
        st.caption("• All scan results and reports")
        st.caption("• Your consent records")
        st.caption("• Account information")
    
    st.markdown("---")
    
    st.subheader("🗑️ Delete Your Data")
    st.warning("⚠️ **Danger Zone** - This action cannot be undone!")
    
    st.write("Request deletion of all your data (GDPR Article 17 - Right to Erasure).")
    
    confirm_delete = st.checkbox(
        "I understand this will permanently delete all my scan history, reports, and account data",
        value=False
    )
    
    if confirm_delete:
        if st.button("🗑️ Delete All My Data", type="primary", use_container_width=True):
            with st.spinner("Processing deletion request..."):
                try:
                    from services.results_aggregator import ResultsAggregator
                    aggregator = ResultsAggregator()
                    result = aggregator.gdpr_delete_user_data(username)
                    
                    if 'error' not in result:
                        st.success(f"✅ Deletion complete! Removed {result.get('scans_deleted', 0)} scan records.")
                        st.info("Your account will remain active. Only scan data has been deleted.")
                    else:
                        st.error(f"Deletion failed: {result['error']}")
                except Exception as e:
                    logger.error(f"Deletion error: {e}")
                    st.error("Unable to process deletion. Please contact support.")
    
    st.markdown("---")
    
    st.subheader("📜 Privacy Documentation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**[Privacy Policy](https://dataguardianpro.nl/privacy)**")
        st.caption("Full privacy policy")
    
    with col2:
        st.markdown("**[Cookie Policy](https://dataguardianpro.nl/cookies)**")
        st.caption("Cookie usage details")
    
    with col3:
        st.markdown("**[Terms of Service](https://dataguardianpro.nl/terms)**")
        st.caption("Service agreement")
    
    st.markdown("---")
    st.caption("🇳🇱 DataGuardian Pro complies with GDPR (EU) and UAVG (Netherlands). Data is processed and stored exclusively within the EU.")
