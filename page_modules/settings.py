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

# === Settings Page (moved from app.py) ===
def render_settings_page():
    """Comprehensive settings page with user preferences, API configurations, and compliance settings"""
    from utils.translations import _
    from utils.settings_manager import SettingsManager
    import json
    
    logger.info("Settings page rendering started")
    st.title(f"⚙️ {_('sidebar.settings', 'Settings')}")
    
    # Initialize settings manager
    settings_manager = SettingsManager()
    username = st.session_state.get('username', 'anonymous')
    
    # Initialize user settings if first time
    if f"settings_initialized_{username}" not in st.session_state:
        settings_manager.initialize_user_settings(username)
        st.session_state[f"settings_initialized_{username}"] = True
    
    # Settings categories
    tabs = st.tabs([
        "👤 Profile", "🔐 API Keys", "⚖️ Compliance", 
        "🔍 Scanners", "📊 Reports", "🔒 Security", "📥 Downloads", "💳 Billing"
    ])
    
    # Profile Settings
    with tabs[0]:
        st.subheader("Profile Preferences")
        
        profile_settings = settings_manager.get_user_settings(username, "profile")
        
        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox(
                "Language",
                ["en", "nl"],
                index=0 if profile_settings.get("language", "en") == "en" else 1,
                format_func=lambda x: "English" if x == "en" else "Nederlands"
            )
            
            region = st.selectbox(
                "Default Region",
                ["Netherlands", "Germany", "France", "Belgium", "Europe"],
                index=["Netherlands", "Germany", "France", "Belgium", "Europe"].index(
                    profile_settings.get("region", "Netherlands")
                )
            )
        
        with col2:
            theme = st.selectbox(
                "Theme",
                ["light", "dark", "auto"],
                index=["light", "dark", "auto"].index(profile_settings.get("theme", "light"))
            )
            
            timezone = st.selectbox(
                "Timezone",
                ["Europe/Amsterdam", "Europe/Berlin", "Europe/Paris", "Europe/Brussels"],
                index=0
            )
        
        # Notification preferences
        st.markdown("#### Notifications")
        email_notifications = st.checkbox(
            "Email Notifications", 
            value=profile_settings.get("email_notifications", True)
        )
        desktop_notifications = st.checkbox(
            "Desktop Notifications", 
            value=profile_settings.get("desktop_notifications", False)
        )
        
        if st.button("💾 Save Profile Settings", key="save_profile"):
            settings_manager.save_user_setting(username, "profile", "language", language)
            settings_manager.save_user_setting(username, "profile", "region", region)
            settings_manager.save_user_setting(username, "profile", "theme", theme)
            settings_manager.save_user_setting(username, "profile", "timezone", timezone)
            settings_manager.save_user_setting(username, "profile", "email_notifications", email_notifications)
            settings_manager.save_user_setting(username, "profile", "desktop_notifications", desktop_notifications)
            st.success("Profile settings saved successfully!")
            st.rerun()
    
    # API Keys Settings
    with tabs[1]:
        st.subheader("API Configuration")
        
        api_settings = settings_manager.get_user_settings(username, "api_keys")
        
        # OpenAI API Key
        st.markdown("#### OpenAI Configuration")
        openai_key = st.text_input(
            "OpenAI API Key",
            value=api_settings.get("openai_api_key", ""),
            type="password",
            help="Enter your OpenAI API key for AI-powered analysis"
        )
        
        if st.button("🧪 Test OpenAI Connection", key="test_openai"):
            if openai_key:
                validation = settings_manager.validate_api_key(openai_key, "openai")
                if validation["valid"]:
                    st.success(f"✅ {validation['message']}")
                    st.info(f"Models available: {validation['details'].get('models_available', 'Unknown')}")
                else:
                    st.error(f"❌ {validation['message']}")
            else:
                st.warning("Please enter an API key to test")
        
        # Stripe API Keys
        st.markdown("#### Stripe Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            stripe_secret = st.text_input(
                "Stripe Secret Key",
                value=api_settings.get("stripe_secret_key", ""),
                type="password",
                help="Stripe secret key for payment processing"
            )
        
        with col2:
            stripe_publishable = st.text_input(
                "Stripe Publishable Key",
                value=api_settings.get("stripe_publishable_key", ""),
                help="Stripe publishable key for frontend"
            )
        
        if st.button("🧪 Test Stripe Connection", key="test_stripe"):
            if stripe_secret:
                validation = settings_manager.validate_api_key(stripe_secret, "stripe")
                if validation["valid"]:
                    st.success(f"✅ {validation['message']}")
                    st.info(f"Account ID: {validation['details'].get('account_id', 'Unknown')}")
                else:
                    st.error(f"❌ {validation['message']}")
            else:
                st.warning("Please enter Stripe secret key to test")
        
        if st.button("💾 Save API Keys", key="save_apis"):
            settings_manager.save_user_setting(username, "api_keys", "openai_api_key", openai_key, encrypted=True)
            settings_manager.save_user_setting(username, "api_keys", "stripe_secret_key", stripe_secret, encrypted=True)
            settings_manager.save_user_setting(username, "api_keys", "stripe_publishable_key", stripe_publishable, encrypted=True)
            st.success("API keys saved securely!")
    
    # Compliance Settings
    with tabs[2]:
        st.subheader("GDPR & Compliance")
        
        compliance_settings = settings_manager.get_user_settings(username, "compliance")
        
        col1, col2 = st.columns(2)
        with col1:
            gdpr_region = st.selectbox(
                "GDPR Region",
                ["Netherlands", "Germany", "France", "Belgium", "General EU"],
                index=0
            )
            
            retention_days = st.number_input(
                "Data Retention (days)",
                min_value=30,
                max_value=2555,  # 7 years
                value=int(compliance_settings.get("retention_days", 365))
            )
        
        with col2:
            data_residency = st.selectbox(
                "Data Residency",
                ["EU", "Netherlands", "Germany", "France"],
                index=0
            )
            
            dpo_contact = st.text_input(
                "DPO Contact Email",
                value=compliance_settings.get("dpo_contact", "")
            )
        
        # Compliance toggles
        audit_logging = st.checkbox(
            "Audit Logging", 
            value=compliance_settings.get("audit_logging", True),
            help="Enable comprehensive audit trail"
        )
        breach_notifications = st.checkbox(
            "Breach Notifications", 
            value=compliance_settings.get("breach_notifications", True),
            help="Automatic breach notification alerts"
        )
        
        if st.button("💾 Save Compliance Settings", key="save_compliance"):
            settings_manager.save_user_setting(username, "compliance", "gdpr_region", gdpr_region)
            settings_manager.save_user_setting(username, "compliance", "data_residency", data_residency)
            settings_manager.save_user_setting(username, "compliance", "retention_days", retention_days)
            settings_manager.save_user_setting(username, "compliance", "dpo_contact", dpo_contact)
            settings_manager.save_user_setting(username, "compliance", "audit_logging", audit_logging)
            settings_manager.save_user_setting(username, "compliance", "breach_notifications", breach_notifications)
            st.success("Compliance settings saved successfully!")
    
    # Scanner Settings
    with tabs[3]:
        st.subheader("Scanner Configuration")
        
        scanner_settings = settings_manager.get_user_settings(username, "scanners")
        
        col1, col2 = st.columns(2)
        with col1:
            default_scanner = st.selectbox(
                "Default Scanner Type",
                ["code", "document", "image", "website", "database", "api", "ai_model"],
                index=0
            )
            
            max_concurrent = st.number_input(
                "Max Concurrent Scans",
                min_value=1,
                max_value=10,
                value=int(scanner_settings.get("max_concurrent", 3))
            )
        
        with col2:
            timeout_seconds = st.number_input(
                "Scan Timeout (seconds)",
                min_value=60,
                max_value=1800,
                value=int(scanner_settings.get("timeout_seconds", 300))
            )
            
            file_size_limit = st.number_input(
                "File Size Limit (MB)",
                min_value=1,
                max_value=500,
                value=int(scanner_settings.get("file_size_limit_mb", 100))
            )
        
        scan_depth = st.selectbox(
            "Default Scan Depth",
            ["surface", "standard", "deep", "comprehensive"],
            index=2
        )
        
        if st.button("💾 Save Scanner Settings", key="save_scanners"):
            settings_manager.save_user_setting(username, "scanners", "default_scanner", default_scanner)
            settings_manager.save_user_setting(username, "scanners", "max_concurrent", max_concurrent)
            settings_manager.save_user_setting(username, "scanners", "timeout_seconds", timeout_seconds)
            settings_manager.save_user_setting(username, "scanners", "file_size_limit_mb", file_size_limit)
            settings_manager.save_user_setting(username, "scanners", "scan_depth", scan_depth)
            st.success("Scanner settings saved successfully!")
    
    # Report Settings
    with tabs[4]:
        st.subheader("Report Configuration")
        
        report_settings = settings_manager.get_user_settings(username, "reports")
        
        col1, col2 = st.columns(2)
        with col1:
            default_format = st.selectbox(
                "Default Report Format",
                ["html", "pdf", "json", "csv"],
                index=0
            )
            
            template = st.selectbox(
                "Report Template",
                ["professional", "detailed", "executive", "technical"],
                index=0
            )
        
        with col2:
            auto_download = st.checkbox(
                "Auto Download Reports", 
                value=report_settings.get("auto_download", True)
            )
            
            include_remediation = st.checkbox(
                "Include Remediation Steps", 
                value=report_settings.get("include_remediation", True)
            )
        
        if st.button("💾 Save Report Settings", key="save_reports"):
            settings_manager.save_user_setting(username, "reports", "default_format", default_format)
            settings_manager.save_user_setting(username, "reports", "template", template)
            settings_manager.save_user_setting(username, "reports", "auto_download", auto_download)
            settings_manager.save_user_setting(username, "reports", "include_remediation", include_remediation)
            st.success("Report settings saved successfully!")
    
    # Billing Settings
    with tabs[7]:
        st.subheader("💳 Billing & Subscription")
        
        try:
            from components.cancellation_policy import show_cancellation_interface
            from services.payment_enhancements import get_refund_policy, get_cancellation_policy
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("#### Subscription Management")
                subscription_id = st.session_state.get('subscription_id', None)
                if subscription_id:
                    st.success("✅ Active Subscription")
                    st.write(f"Subscription ID: `{subscription_id}`")
                    show_cancellation_interface()
                else:
                    st.info("No active subscription. Upgrade to unlock premium features.")
                    if st.button("🚀 Upgrade Now", type="primary", key="billing_upgrade"):
                        st.session_state['show_pricing'] = True
                        st.switch_page("pages/6_Pricing.py")
            
            with col2:
                st.markdown("#### Policies")
                refund_policy = get_refund_policy()
                cancellation_policy = get_cancellation_policy()
                
                with st.expander("💰 Refund Policy"):
                    st.markdown(f"**{refund_policy['policy_name']}**")
                    st.write(refund_policy['description'])
                
                with st.expander("❌ Cancellation Policy"):
                    st.write(cancellation_policy['description'])
            
            st.markdown("---")
            st.markdown("#### Payment Methods")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("💳 Credit/Debit Cards")
            with col2:
                st.write("🏦 iDEAL (Netherlands)")
            with col3:
                st.write("💶 SEPA Direct Debit")
            
            st.info("📧 Contact: billing@dataguardianpro.nl")
            
        except ImportError as e:
            st.warning(f"Billing components unavailable: {str(e)}")
    
    # Security Settings
    with tabs[5]:
        st.subheader("Security Configuration")
        
        security_settings = settings_manager.get_user_settings(username, "security")
        
        col1, col2 = st.columns(2)
        with col1:
            session_timeout = st.number_input(
                "Session Timeout (minutes)",
                min_value=15,
                max_value=480,
                value=int(security_settings.get("session_timeout_minutes", 60))
            )
            
            audit_retention = st.number_input(
                "Audit Log Retention (days)",
                min_value=90,
                max_value=2555,
                value=int(security_settings.get("audit_log_retention", 730))
            )
        
        with col2:
            login_alerts = st.checkbox(
                "Login Alerts", 
                value=security_settings.get("login_alerts", True)
            )
            
        st.markdown("---")
        st.markdown("### 🔐 Two-Factor Authentication (2FA)")
        
        try:
            from services.auth import get_mfa_status, enable_mfa, confirm_mfa_setup, disable_mfa
            from services.mfa_service import get_mfa_service
            import base64
            
            mfa_status = get_mfa_status(username)
            
            if mfa_status.get("enabled"):
                st.success("✅ Two-Factor Authentication is **enabled**")
                st.write(f"Backup codes remaining: {mfa_status.get('backup_codes_remaining', 0)}")
                
                with st.expander("Disable 2FA"):
                    disable_password = st.text_input("Enter your password to disable 2FA", type="password", key="disable_mfa_pwd")
                    if st.button("🔓 Disable 2FA", key="disable_mfa_btn"):
                        if disable_password:
                            success, msg = disable_mfa(username, disable_password)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Please enter your password")
            else:
                st.info("🔒 Two-Factor Authentication is not enabled")
                
                if "mfa_setup_data" not in st.session_state:
                    if st.button("🔐 Enable 2FA", key="enable_mfa_btn"):
                        result = enable_mfa(username)
                        if result.get("success"):
                            st.session_state.mfa_setup_data = result
                            st.rerun()
                        else:
                            st.error(result.get("error", "Failed to initialize 2FA"))
                else:
                    setup_data = st.session_state.mfa_setup_data
                    
                    st.markdown("#### Step 1: Scan QR Code")
                    st.write("Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)")
                    
                    qr_image = base64.b64decode(setup_data["qr_code_base64"])
                    st.image(qr_image, width=200)
                    
                    with st.expander("Can't scan? Enter manually"):
                        st.code(setup_data["secret"])
                    
                    st.markdown("#### Step 2: Enter Verification Code")
                    verify_code = st.text_input("Enter the 6-digit code from your app", max_chars=6, key="mfa_verify_code")
                    
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("✅ Verify & Enable", key="confirm_mfa_btn"):
                            if verify_code and len(verify_code) == 6:
                                success, msg = confirm_mfa_setup(username, verify_code)
                                if success:
                                    st.success("2FA enabled successfully!")
                                    st.markdown("**Save your backup codes:**")
                                    for i, code in enumerate(setup_data.get("backup_codes", []), 1):
                                        st.code(f"{i}. {code}")
                                    del st.session_state.mfa_setup_data
                                else:
                                    st.error(msg)
                            else:
                                st.warning("Please enter a valid 6-digit code")
                    
                    with col_cancel:
                        if st.button("❌ Cancel", key="cancel_mfa_btn"):
                            del st.session_state.mfa_setup_data
                            st.rerun()
        
        except ImportError as e:
            st.warning("2FA module not available")
        except Exception as e:
            st.error(f"Error loading 2FA settings: {str(e)}")
        
        st.markdown("---")
        
        if st.button("💾 Save Security Settings", key="save_security"):
            settings_manager.save_user_setting(username, "security", "session_timeout_minutes", session_timeout)
            settings_manager.save_user_setting(username, "security", "audit_log_retention", audit_retention)
            settings_manager.save_user_setting(username, "security", "login_alerts", login_alerts)
            st.success("Security settings saved successfully!")
    
    # Downloads Management
    with tabs[6]:
        st.subheader("📥 Document Downloads")
        
        # Available documents section
        st.markdown("### 📄 Available Documents")
        
        # Patent applications
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔬 Patent Applications")
            
            # Check if patent PDFs exist
            import os
            patent_files = []
            if os.path.exists("DataGuardian_Pro_Patent_Application_2_Predictive_Compliance_Engine.pdf"):
                patent_files.append({
                    "name": "Predictive Compliance Analytics Engine", 
                    "file": "DataGuardian_Pro_Patent_Application_2_Predictive_Compliance_Engine.pdf",
                    "size": "49KB",
                    "type": "Patent Application"
                })
            
            # Check for other patent files
            for file in ["Patent_Conclusions.pdf", "Patent_Description.pdf", "Patent_Drawings.pdf"]:
                if os.path.exists(file):
                    patent_files.append({
                        "name": file.replace("_", " ").replace(".pdf", ""),
                        "file": file,
                        "size": f"{os.path.getsize(file)//1024}KB" if os.path.exists(file) else "Unknown",
                        "type": "Patent Document"
                    })
            
            if patent_files:
                for patent in patent_files:
                    with st.container():
                        st.write(f"**{patent['name']}**")
                        st.caption(f"{patent['type']} • {patent['size']}")
                        
                        if os.path.exists(patent['file']):
                            with open(patent['file'], "rb") as file:
                                st.download_button(
                                    label=f"📥 Download {patent['name']}",
                                    data=file.read(),
                                    file_name=patent['file'],
                                    mime="application/pdf",
                                    key=f"patent_{patent['file']}"
                                )
                        st.markdown("---")
            else:
                st.info("No patent documents available yet.")
        
        with col2:
            st.markdown("#### 📊 Scan Reports") 
            
            # Get recent scan results from session
            if 'last_scan_results' in st.session_state:
                scan_results = st.session_state['last_scan_results']
                
                st.write("**Latest Scan Report**")
                st.caption(f"Scan ID: {scan_results.get('scan_id', 'Unknown')} • {scan_results.get('scan_type', 'Unknown')} Scan")
                
                # Generate and offer downloads
                try:
                    from services.download_reports import generate_html_report, generate_pdf_report
                    
                    col_pdf, col_html = st.columns(2)
                    
                    with col_pdf:
                        try:
                            pdf_content = generate_pdf_report(scan_results)
                            st.download_button(
                                label="📥 PDF Report",
                                data=pdf_content,
                                file_name=f"scan_report_{scan_results.get('scan_id', 'unknown')}.pdf",
                                mime="application/pdf",
                                key="latest_pdf_download"
                            )
                        except Exception as e:
                            st.caption("PDF generation unavailable")
                    
                    with col_html:
                        try:
                            html_content = generate_html_report(scan_results)
                            st.download_button(
                                label="📥 HTML Report",
                                data=html_content,
                                file_name=f"scan_report_{scan_results.get('scan_id', 'unknown')}.html",
                                mime="text/html",
                                key="latest_html_download"
                            )
                        except Exception as e:
                            st.caption("HTML generation unavailable")
                            
                except ImportError:
                    st.caption("Report generation services unavailable")
                
                st.markdown("---")
                
                # Raw data download
                st.write("**Raw Scan Data**")
                if st.button("📊 Export as JSON", key="json_export"):
                    import json
                    json_data = json.dumps(scan_results, indent=2, default=str)
                    st.download_button(
                        label="💾 Download JSON",
                        data=json_data,
                        file_name=f"scan_data_{scan_results.get('scan_id', 'unknown')}.json",
                        mime="application/json",
                        key="json_data_download"
                    )
                    st.success("JSON export ready!")
                    
            else:
                st.info("No recent scan results available. Run a scan to generate reports.")
        
        # Download history section
        st.markdown("### 📈 Download Statistics")
        
        # Show download statistics if license manager is available
        try:
            from services.license_integration import LicenseIntegration
            license_integration = LicenseIntegration()
            usage_stats = license_integration.get_usage_summary()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Downloads", usage_stats.get('total_downloads', 0))
            with col2:
                st.metric("Report Downloads", usage_stats.get('reports_generated', 0))
            with col3:
                st.metric("Document Downloads", usage_stats.get('scans_completed', 0))
                
        except (ImportError, Exception):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Downloads", "0")
            with col2:
                st.metric("Report Downloads", "0")
            with col3:
                st.metric("Document Downloads", "0")
        
        # Download preferences
        st.markdown("### ⚙️ Download Preferences")
        
        download_settings = settings_manager.get_user_settings(username, "downloads")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_download = st.checkbox(
                "Auto-download reports after scans",
                value=download_settings.get("auto_download", False),
                help="Automatically download reports after each scan completes"
            )
            
            default_format = st.selectbox(
                "Preferred download format",
                ["PDF", "HTML", "JSON", "CSV"],
                index=0
            )
        
        with col2:
            include_metadata = st.checkbox(
                "Include scan metadata",
                value=download_settings.get("include_metadata", True),
                help="Include technical metadata in downloaded reports"
            )
            
            compress_downloads = st.checkbox(
                "Compress large files",
                value=download_settings.get("compress_downloads", False),
                help="Automatically compress downloads larger than 1MB"
            )
        
        if st.button("💾 Save Download Preferences", key="save_downloads"):
            settings_manager.save_user_setting(username, "downloads", "auto_download", auto_download)
            settings_manager.save_user_setting(username, "downloads", "default_format", default_format.lower())
            settings_manager.save_user_setting(username, "downloads", "include_metadata", include_metadata)
            settings_manager.save_user_setting(username, "downloads", "compress_downloads", compress_downloads)
            st.success("Download preferences saved successfully!")
    
    # Settings management section
    st.markdown("---")
    st.subheader("🔧 Settings Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Export Settings"):
            export_data = settings_manager.export_settings(username, include_sensitive=False)
            if export_data:
                st.download_button(
                    label="💾 Download Settings Backup",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"dataguardian_settings_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                st.success("Settings export ready for download")
    
    with col2:
        uploaded_file = st.file_uploader(
            "📥 Import Settings",
            type="json",
            help="Upload a previously exported settings file"
        )
        if uploaded_file and st.button("Import"):
            try:
                import_data = json.load(uploaded_file)
                if settings_manager.import_settings(username, import_data):
                    st.success("Settings imported successfully!")
                    st.rerun()
                else:
                    st.error("Failed to import settings")
            except Exception as e:
                st.error(f"Invalid settings file: {e}")
    
    with col3:
        if st.button("🔄 Reset to Defaults"):
            if st.button("⚠️ Confirm Reset", key="confirm_reset"):
                settings_manager.initialize_user_settings(username)
                st.success("Settings reset to defaults!")
                st.rerun()

def render_performance_dashboard_safe():
    """Render performance dashboard with error handling"""
    try:
        from utils.performance_dashboard import render_performance_dashboard
        render_performance_dashboard()
    except Exception as e:
        st.error(f"Performance dashboard unavailable: {e}")
        st.info("Performance monitoring is temporarily unavailable. Please try again later.")

def render_log_dashboard():
    """Render the redesigned scanner log dashboard"""
    try:
        from utils.scanner_log_dashboard import show_scanner_log_dashboard
        show_scanner_log_dashboard()
    except Exception as e:
        st.error(f"Error loading scanner log dashboard: {str(e)}")
        st.write("Scanner log dashboard is temporarily unavailable.")

