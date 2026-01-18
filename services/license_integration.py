#!/usr/bin/env python3
"""
Copyright (c) 2025 DataGuardian Pro B.V.
All rights reserved.

PROPRIETARY LICENSE INTEGRATION SYSTEM - DataGuardian Pro™
This software contains confidential integration mechanisms and usage tracking
algorithms protected by copyright and trade secret law.

Patent Pending: Netherlands Patent Application #NL2025004 (License Integration System)
Trademark: DataGuardian Pro™ is a trademark of DataGuardian Pro B.V.

Licensed under DataGuardian Pro Commercial License Agreement.
For licensing inquiries: legal@dataguardianpro.nl
"""

"""
License Integration with DataGuardian Pro
Seamless integration of licensing controls with the main application
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import logging
from services.license_manager import (
    LicenseManager, LicenseType, UsageLimitType, 
    check_license, check_feature, check_scanner, check_region, 
    check_usage, increment_usage, get_license_info, track_user_session
)
from config.pricing_config import get_pricing_config, PricingTier, BillingCycle
from services.usage_analytics import (
    UsageAnalytics, UsageEventType, track_usage_event, 
    get_usage_stats, get_compliance_report
)
from utils.activity_tracker import ScannerType

logger = logging.getLogger(__name__)

class LicenseIntegration:
    """Integration layer for license management in DataGuardian Pro"""
    
    def __init__(self):
        self.license_manager = LicenseManager()
        self.usage_analytics = UsageAnalytics()
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary for the Downloads section"""
        try:
            usage_stats = get_usage_stats()
            # Handle both dict and object types for usage_stats
            if isinstance(usage_stats, dict):
                return {
                    'total_downloads': usage_stats.get('total_scans', 0),
                    'reports_generated': usage_stats.get('reports_generated', 0),
                    'scans_completed': usage_stats.get('scans_completed', 0),
                    'compliance_score': usage_stats.get('compliance_score', 0)
                }
            else:
                # Handle object type
                return {
                    'total_downloads': getattr(usage_stats, 'total_scans', 0),
                    'reports_generated': getattr(usage_stats, 'reports_generated', 0),
                    'scans_completed': getattr(usage_stats, 'scans_completed', 0),
                    'compliance_score': getattr(usage_stats, 'compliance_score', 0)
                }
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {
                'total_downloads': 0,
                'reports_generated': 0,
                'scans_completed': 0,
                'compliance_score': 0
            }
    
    def initialize_license_check(self) -> bool:
        """Initialize license check for the application"""
        try:
            is_valid, message = check_license()
            
            if not is_valid:
                st.error(f"License Error: {message}")
                self.show_license_upgrade_prompt()
                return False
            
            # Track application start
            if 'user_id' in st.session_state:
                track_usage_event(
                    event_type=UsageEventType.USER_LOGIN,
                    user_id=st.session_state['user_id'],
                    session_id=st.session_state.get('session_id', 'unknown'),
                    feature='application_start'
                )
            
            return True
            
        except Exception as e:
            logger.error(f"License initialization failed: {e}")
            st.error("License system error. Please contact support.")
            return False
    
    def check_scanner_permission(self, scanner_type: str, region: str) -> Tuple[bool, str]:
        """Check if user can access a scanner type in a region"""
        
        # Check license validity
        is_valid, message = check_license()
        if not is_valid:
            return False, f"License invalid: {message}"
        
        # Check scanner access
        if not check_scanner(scanner_type):
            return False, f"Scanner '{scanner_type}' not available in your license"
        
        # Check region access
        if not check_region(region):
            return False, f"Region '{region}' not available in your license"
        
        # Check usage limits
        allowed, current, limit = check_usage(UsageLimitType.SCANS_PER_MONTH)
        if not allowed:
            return False, f"Monthly scan limit reached ({current}/{limit})"
        
        # Check concurrent users
        if 'user_id' in st.session_state:
            if not track_user_session(st.session_state['user_id']):
                return False, "Maximum concurrent users reached"
        
        return True, "Access granted"
    
    def track_scan_usage(self, scanner_type: str, region: str, success: bool = True, 
                        duration_ms: Optional[int] = None, error_message: Optional[str] = None):
        """Track scanner usage for licensing and analytics"""
        
        if 'user_id' not in st.session_state:
            return
        
        user_id = st.session_state['user_id']
        session_id = st.session_state.get('session_id', 'unknown')
        
        # Increment usage counters
        if success:
            increment_usage(UsageLimitType.SCANS_PER_MONTH, 1)
            increment_usage(UsageLimitType.SCANS_PER_DAY, 1)
        
        # Track in analytics
        event_type = UsageEventType.SCAN_COMPLETED if success else UsageEventType.SCAN_FAILED
        track_usage_event(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            scanner_type=scanner_type,
            region=region,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
    
    def check_report_generation(self) -> Tuple[bool, str]:
        """Check if user can generate reports"""
        
        # Check license validity
        is_valid, message = check_license()
        if not is_valid:
            return False, f"License invalid: {message}"
        
        # Check reporting feature
        if not check_feature("reporting"):
            return False, "Report generation not available in your license"
        
        # Check export limits
        allowed, current, limit = check_usage(UsageLimitType.EXPORT_REPORTS)
        if not allowed:
            return False, f"Report export limit reached ({current}/{limit})"
        
        return True, "Report generation allowed"
    
    def track_report_generation(self, report_type: str, success: bool = True):
        """Track report generation for licensing"""
        
        if 'user_id' not in st.session_state:
            return
        
        user_id = st.session_state['user_id']
        session_id = st.session_state.get('session_id', 'unknown')
        
        # Increment usage if successful
        if success:
            increment_usage(UsageLimitType.EXPORT_REPORTS, 1)
        
        # Track in analytics
        track_usage_event(
            event_type=UsageEventType.REPORT_GENERATED,
            user_id=user_id,
            session_id=session_id,
            feature=f"report_{report_type}",
            success=success
        )
    
    def track_report_download(self, report_type: str):
        """Track report download"""
        
        if 'user_id' not in st.session_state:
            return
        
        user_id = st.session_state['user_id']
        session_id = st.session_state.get('session_id', 'unknown')
        
        track_usage_event(
            event_type=UsageEventType.REPORT_DOWNLOADED,
            user_id=user_id,
            session_id=session_id,
            feature=f"download_{report_type}"
        )
    
    def check_api_access(self) -> Tuple[bool, str]:
        """Check API access permissions"""
        
        # Check license validity
        is_valid, message = check_license()
        if not is_valid:
            return False, f"License invalid: {message}"
        
        # Check API feature
        if not check_feature("api_access"):
            return False, "API access not available in your license"
        
        # Check API call limits
        allowed, current, limit = check_usage(UsageLimitType.API_CALLS)
        if not allowed:
            return False, f"API call limit reached ({current}/{limit})"
        
        return True, "API access granted"
    
    def show_license_status(self):
        """Show license status in sidebar"""
        import logging
        
        # First check user's individual license tier from session
        user_license_tier = st.session_state.get('license_tier', None)
        username = st.session_state.get('username', 'User')
        authenticated = st.session_state.get('authenticated', False)
        
        logging.info(f"show_license_status: authenticated={authenticated}, license_tier={user_license_tier}, username={username}")
        
        if user_license_tier:
            # Show user's individual license tier
            st.sidebar.success("✅ License Active")
            
            tier_names = {
                'trial': 'Free Trial',
                'startup': 'Startup',
                'professional': 'Professional',
                'growth': 'Growth',
                'scale': 'Scale',
                'enterprise': 'Enterprise',
                'free': 'Free'
            }
            plan_name = tier_names.get(user_license_tier, user_license_tier.title())
            
            with st.sidebar.expander("📋 License Details", expanded=True):
                st.write(f"**Plan:** {plan_name}")
                st.write(f"**Account:** {username}")
                
                # Show free scans remaining for trial users
                if user_license_tier == 'trial':
                    free_scans = st.session_state.get('free_scans_remaining', 3)
                    st.write(f"**Free Scans:** {free_scans} remaining")
                    if free_scans <= 1:
                        st.warning("⚠️ Running low on scans!")
                    if st.button("Upgrade Now", key="upgrade_sidebar"):
                        st.session_state['show_pricing'] = True
                        st.switch_page("pages/6_Pricing.py")
            return
        
        # Fall back to global license info
        license_info = get_license_info()
        
        if license_info.get("status") == "Valid":
            # Get current tier for detailed information
            current_tier = self.get_current_pricing_tier()
            tier_limits = self.get_tier_limits(current_tier) if current_tier else {}
            
            st.sidebar.success("✅ License Active")
            
            # Show license details with meaningful information
            with st.sidebar.expander("📋 License Details", expanded=True):
                # Plan information
                plan_name = license_info['license_type'].replace('_', ' ').title()
                if current_tier:
                    plan_name = f"{plan_name} ({current_tier.value.title()})"
                st.write(f"**Plan:** {plan_name}")
                st.write(f"**Company:** {license_info['company_name']}")
                
                # Usage limits and remaining resources
                st.write("---")
                st.write("**📊 Usage This Month:**")
                
                # Get actual usage from license info or calculate defaults
                monthly_scans = license_info.get("usage", {}).get("monthly_scans", {"current": 23, "limit": "unlimited"})
                data_sources = license_info.get("usage", {}).get("data_sources", {"current": 4, "limit": "unlimited"})
                
                if isinstance(monthly_scans["limit"], str) and monthly_scans["limit"] == "unlimited":
                    st.write(f"**Scans:** {monthly_scans['current']} used (Unlimited)")
                    st.success("✨ Unlimited scans available")
                else:
                    scans_remaining = monthly_scans['limit'] - monthly_scans['current']
                    st.write(f"**Scans:** {monthly_scans['current']}/{monthly_scans['limit']} ({scans_remaining} left)")
                    progress = monthly_scans['current'] / monthly_scans['limit']
                    st.progress(progress)
                
                if isinstance(data_sources["limit"], str) and data_sources["limit"] == "unlimited":
                    st.write(f"**Data Sources:** {data_sources['current']} connected (Unlimited)")
                else:
                    st.write(f"**Data Sources:** {data_sources['current']}/{data_sources['limit']}")
                
                # Subscription status
                st.write("---")
                st.write("**🗓️ Subscription:**")
                expiry_date = license_info['expiry_date'][:10] if license_info.get('expiry_date') else 'Unknown'
                days_remaining = license_info.get('days_remaining', 'Unknown')
                
                if isinstance(days_remaining, int):
                    if days_remaining > 30:
                        st.write(f"**Expires:** {expiry_date} ({days_remaining} days)")
                        st.success("🟢 Active subscription")
                    elif days_remaining > 7:
                        st.write(f"**Expires:** {expiry_date} ({days_remaining} days)")
                        st.warning("🟡 Renewal due soon")
                    else:
                        st.write(f"**Expires:** {expiry_date} ({days_remaining} days)")
                        st.error("🔴 Expires soon - Renew now!")
                else:
                    st.write(f"**Expires:** {expiry_date}")
                
                # Support level
                support_level = tier_limits.get('support_level', 'email').replace('_', ' ').title()
                sla_hours = tier_limits.get('sla_hours', 48)
                st.write(f"**Support:** {support_level} ({sla_hours}h SLA)")
                
            # Enterprise license active - no upgrade needed
        else:
            st.sidebar.error("❌ License Invalid")
            st.sidebar.write(license_info.get("message", "Unknown error"))
            
            if st.sidebar.button("Upgrade License"):
                self.show_license_upgrade_prompt()
    
    def get_current_pricing_tier(self) -> Optional[PricingTier]:
        """Determine current user's pricing tier based on license"""
        try:
            license_info = get_license_info()
            license_type = license_info.get('license_type', 'trial')
            
            # Map license types to pricing tiers
            tier_mapping = {
                'trial': PricingTier.STARTUP,
                'basic': PricingTier.STARTUP,
                'startup': PricingTier.STARTUP,
                'professional': PricingTier.PROFESSIONAL,
                'growth': PricingTier.GROWTH,
                'scale': PricingTier.SCALE,
                'salesforce_premium': PricingTier.SALESFORCE_PREMIUM,
                'sap_enterprise': PricingTier.SAP_ENTERPRISE,
                'enterprise': PricingTier.ENTERPRISE,
                'ultimate': PricingTier.ENTERPRISE,
                'government': PricingTier.GOVERNMENT
            }
            
            return tier_mapping.get(license_type.lower(), PricingTier.STARTUP)
            
        except Exception as e:
            logger.error(f"Error determining pricing tier: {e}")
            return PricingTier.STARTUP
    
    def get_tier_limits(self, tier: PricingTier) -> Dict[str, Any]:
        """Get usage limits and features for a pricing tier"""
        config = get_pricing_config()
        tier_data = config.pricing_data["tiers"].get(tier.value, {})
        
        return {
            "max_scans_monthly": tier_data.get("max_scans_monthly", 10),
            "max_data_sources": tier_data.get("max_data_sources", 1),
            "support_level": tier_data.get("support_level", "email"),
            "sla_hours": tier_data.get("sla_hours", 48),
            "features": config.get_features_for_tier(tier)
        }
    
    def check_feature_access(self, feature_name: str) -> bool:
        """Check if current tier has access to specific feature"""
        current_tier = self.get_current_pricing_tier()
        if not current_tier:
            return False
        
        config = get_pricing_config()
        available_features = config.get_features_for_tier(current_tier)
        return feature_name in available_features
    
    def show_upgrade_prompt(self, required_tier: PricingTier, feature_name: str):
        """Show upgrade prompt for accessing premium features"""
        current_tier = self.get_current_pricing_tier()
        config = get_pricing_config()
        
        # Get pricing for required tier
        required_pricing = config.get_tier_pricing(required_tier, BillingCycle.ANNUAL)
        current_pricing = config.get_tier_pricing(current_tier, BillingCycle.ANNUAL) if current_tier else None
        
        st.warning(f"**Feature Upgrade Required**")
        st.info(f"""
        The **{feature_name}** feature requires **{required_pricing['name']}** tier or higher.
        
        **Current Plan**: {current_pricing['name'] if current_pricing else 'No active plan'}
        **Required Plan**: {required_pricing['name']} - €{required_pricing['price']}/year
        
        **Upgrade Benefits:**
        • Access to {feature_name}
        • {required_tier.value.title()} tier features
        • Priority support
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Upgrade Now", type="primary"):
                self.redirect_to_pricing(required_tier)
        with col2:
            if st.button("📋 View All Plans"):
                self.show_pricing_comparison()
    
    def redirect_to_pricing(self, suggested_tier: Optional[PricingTier] = None):
        """Redirect to pricing page with suggested tier"""
        st.session_state['show_pricing'] = True
        if suggested_tier:
            st.session_state['suggested_tier'] = suggested_tier.value
        st.rerun()
    
    def show_pricing_comparison(self):
        """Display comprehensive pricing comparison"""
        config = get_pricing_config()
        
        st.header("💰 DataGuardian Pro Pricing")
        st.markdown("Choose the perfect plan for your compliance needs")
        
        # Create pricing cards
        cols = st.columns(4)
        tiers = [PricingTier.STARTUP, PricingTier.GROWTH, PricingTier.SCALE, PricingTier.ENTERPRISE]
        
        for i, tier in enumerate(tiers):
            with cols[i]:
                pricing = config.get_tier_pricing(tier, BillingCycle.ANNUAL)
                tier_data = config.pricing_data["tiers"][tier.value]
                
                # Highlight most popular
                if tier_data.get("most_popular"):
                    st.markdown("🔥 **MOST POPULAR**")
                
                st.markdown(f"### {pricing['name']}")
                st.markdown(f"**€{pricing['price']}/year**")
                st.markdown(f"*€{tier_data['monthly_price']}/month*")
                
                if 'savings' in pricing:
                    st.success(f"Save €{pricing['savings']} vs monthly")
                
                st.markdown(f"**{tier_data['target_employees']} employees**")
                
                # Features
                st.markdown("**Features:**")
                features = config.get_features_for_tier(tier)[:5]  # Show top 5
                for feature in features:
                    st.markdown(f"✅ {feature.replace('_', ' ').title()}")
                
                if len(features) > 5:
                    st.markdown(f"+ {len(features) - 5} more features")
                
                if st.button(f"Select {tier.value.title()}", key=f"select_{tier.value}"):
                    self.handle_plan_selection(tier)
        
        # Government/Enterprise license
        st.markdown("---")
        st.markdown("### 🏛️ Government & Enterprise License")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**On-premises deployment**")
            st.markdown("€15,000 one-time + €2,500/year maintenance")
            st.markdown("• Full source code access")
            st.markdown("• Custom development")
            st.markdown("• Government compliance")
        with col2:
            if st.button("Contact Sales", key="contact_gov"):
                st.session_state['contact_sales'] = True
    
    def handle_plan_selection(self, tier: PricingTier):
        """Handle pricing plan selection"""
        st.session_state['selected_tier'] = tier.value
        st.session_state['show_checkout'] = True
        st.success(f"Selected {tier.value.title()} plan!")
        st.rerun()
    
    def show_license_upgrade_prompt(self):
        """Show license upgrade options"""
        
        st.error("🔐 License Upgrade Required")
        
        st.markdown("""
        Your current license has limitations. Upgrade to unlock full features:
        """)
        
        # License comparison table
        license_options = {
            "Trial": {
                "price": "Free",
                "scans": "50/month",
                "users": "2",
                "features": "Basic scanners",
                "regions": "Netherlands"
            },
            "Basic": {
                "price": "€49.99/month",
                "scans": "500/month",
                "users": "5",
                "features": "All scanners",
                "regions": "Netherlands, Germany"
            },
            "Professional": {
                "price": "€149.99/month",
                "scans": "2,000/month",
                "users": "15",
                "features": "All scanners + API",
                "regions": "All EU regions"
            },
            "Enterprise": {
                "price": "€399.99/month",
                "scans": "10,000/month",
                "users": "50",
                "features": "All features + White-label",
                "regions": "Netherlands"
            }
        }
        
        cols = st.columns(len(license_options))
        for i, (name, details) in enumerate(license_options.items()):
            with cols[i]:
                st.markdown(f"### {name}")
                st.write(f"**Price:** {details['price']}")
                st.write(f"**Scans:** {details['scans']}")
                st.write(f"**Users:** {details['users']}")
                st.write(f"**Features:** {details['features']}")
                st.write(f"**Regions:** {details['regions']}")
                
                if st.button(f"Select {name}", key=f"select_{name}"):
                    st.info(f"Redirecting to upgrade to {name} plan...")
                    # Here you would redirect to payment or contact form
    
    def show_usage_dashboard(self):
        """Show usage analytics dashboard"""
        
        if not check_feature("compliance_dashboard"):
            st.error("Usage dashboard not available in your license")
            return
        
        st.header("📊 Usage Analytics Dashboard")
        
        # Add auto-refresh for real-time updates
        if st.button("🔄 Refresh Dashboard", help="Refresh dashboard metrics to show latest scan results"):
            st.rerun()
        
        # Get real-time usage statistics from activity tracker
        user_id = st.session_state.get('user_id', 'default_user')
        username = st.session_state.get('username', 'default_user')
        
        # Debug info for troubleshooting
        st.caption(f"Tracking data for user: {user_id}")
        
        # Initialize default values to prevent unbound variables
        total_scans = 0
        total_pii_found = 0
        high_risk_findings = 0
        avg_compliance_score = 0.0
        user_activities = []
        metrics = {}
        
        try:
            # Get live dashboard metrics from activity tracker (includes real scan data)
            from utils.activity_tracker import get_dashboard_metrics, get_activity_tracker
            
            # Force a fresh calculation of metrics
            tracker = get_activity_tracker()
            user_activities = tracker.get_user_activities(user_id, limit=100)  # Use reasonable default instead of None
            
            # Calculate live metrics directly from activity data
            scan_activities = [a for a in user_activities if a.activity_type.value in ['scan_started', 'scan_completed', 'scan_failed']]
            completed_scans = [a for a in scan_activities if a.activity_type.value == 'scan_completed']
            failed_scans = [a for a in scan_activities if a.activity_type.value == 'scan_failed']
            
            # Calculate cumulative totals from all completed scans
            total_scans = len(completed_scans)
            total_pii_found = 0
            high_risk_findings = 0
            compliance_scores = []
            
            for scan in completed_scans:
                scan_details = scan.details
                total_pii_found += scan_details.get('findings_count', 0)
                high_risk_findings += scan_details.get('high_risk_count', 0)
                
                # Collect compliance scores for averaging
                comp_score = scan_details.get('compliance_score', 0)
                if comp_score > 0:
                    compliance_scores.append(comp_score)
            
            # Calculate average compliance score
            avg_compliance_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0.0
            
            # Calculate success rate
            success_rate = len(completed_scans) / max(len(scan_activities), 1) if scan_activities else 0
            
            # Also get metrics from database for additional data
            metrics = get_dashboard_metrics(user_id) or {}  # Ensure metrics is not None
            
            # Use database data if activity tracker has no data (fallback)
            if total_scans == 0:
                total_scans = metrics.get('total_scans', 0)
                total_pii_found = metrics.get('total_pii_found', 0)
                high_risk_findings = metrics.get('high_risk_findings', 0)
                avg_compliance_score = metrics.get('average_compliance_score', 0.0)
            
            # Debug information
            st.caption(f"Dashboard data: Scans: {total_scans}, PII: {total_pii_found}, High Risk: {high_risk_findings}, Completed Scans in Tracker: {len(completed_scans)}")
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            # Fallback to basic stats if available
            stats = get_usage_stats()
            total_scans = getattr(stats, 'total_scans', 0)
            success_rate = max(0, 1 - getattr(stats, 'error_rate', 0))
            total_pii_found = 0
            high_risk_findings = 0
            avg_compliance_score = 0.0
            user_activities = []
            metrics = {}
        
        license_info = get_license_info()
        
        # Overview metrics with real scan data and delta calculations
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            # Show current total scans
            st.metric("Total Scans", total_scans)
        with col2:
            # Show compliance score as percentage
            st.metric("Compliance Score", f"{avg_compliance_score:.1f}%")
        with col3:
            # Show total PII found across all scans
            st.metric("Total PII Found", total_pii_found)
        with col4:
            # Show active high-risk issues
            st.metric("Active Issues", high_risk_findings)
        
        # License compliance
        st.subheader("License Compliance")
        compliance = get_compliance_report(license_info)
        
        if compliance.get("warnings"):
            st.warning("⚠️ License Usage Warnings:")
            for warning in compliance["warnings"]:
                st.write(f"- {warning}")
        else:
            st.success("✅ All usage within license limits")
        
        # Scanner usage from activity tracker
        st.subheader("Scanner Usage")
        try:
            scanner_stats = {}
            for activity in user_activities:
                if activity.activity_type.value == 'scan_completed' and activity.scanner_type:
                    scanner_name = activity.scanner_type.value
                    scanner_stats[scanner_name] = scanner_stats.get(scanner_name, 0) + 1
            
            if scanner_stats:
                st.bar_chart(scanner_stats)
            else:
                st.info("No scanner usage data available yet")
        except:
            st.info("Scanner usage data will appear after running scans")
        
        # Recent activity from activity tracker
        st.subheader("Recent Activity")
        try:
            recent_activities = metrics.get('recent_activities', [])
            
            if recent_activities:
                for activity in recent_activities[-10:]:  # Show last 10 activities
                    icon = "✅" if activity.get('success', True) else "❌"
                    activity_type = activity.get('activity_type', 'unknown')
                    scanner_type = activity.get('scanner_type', '')
                    timestamp = activity.get('timestamp', '')
                    
                    try:
                        # Format timestamp
                        if timestamp:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            timestamp_str = "unknown"
                    except:
                        timestamp_str = str(timestamp)
                    
                    # Format activity description
                    if scanner_type:
                        activity_desc = f"{activity_type} ({scanner_type})"
                    else:
                        activity_desc = activity_type
                        
                    st.write(f"{icon} {activity_desc} - {timestamp_str}")
            else:
                st.info("No recent activity found. Start by running a scan.")
        except Exception as e:
            logger.error(f"Error displaying recent activities: {e}")
            st.info("Recent activity will appear after using the scanners.")
    
    def create_license_decorator(self):
        """Create decorator for license-protected functions"""
        
        def license_required(scanner_type: Optional[str] = None, feature: Optional[str] = None, region: Optional[str] = None):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    # Check license
                    is_valid, message = check_license()
                    if not is_valid:
                        st.error(f"License Error: {message}")
                        return None
                    
                    # Check specific permissions
                    if scanner_type and not check_scanner(scanner_type):
                        st.error(f"Scanner '{scanner_type}' not available in your license")
                        return None
                    
                    if feature and not check_feature(feature):
                        st.error(f"Feature '{feature}' not available in your license")
                        return None
                    
                    if region and not check_region(region):
                        st.error(f"Region '{region}' not available in your license")
                        return None
                    
                    # Check usage limits
                    if scanner_type:
                        allowed, current, limit = check_usage(UsageLimitType.SCANS_PER_MONTH)
                        if not allowed:
                            st.error(f"Monthly scan limit reached ({current}/{limit})")
                            return None
                    
                    # Execute function
                    return func(*args, **kwargs)
                
                return wrapper
            return decorator
        
        return license_required

# Global license integration instance
license_integration = LicenseIntegration()

# Convenience functions
def require_license_check() -> bool:
    """Check if license is valid for application use"""
    return license_integration.initialize_license_check()

def require_scanner_access(scanner_type: str, region: str) -> bool:
    """Check scanner access permissions"""
    allowed, message = license_integration.check_scanner_permission(scanner_type, region)
    if not allowed:
        st.error(f"Access denied: {message}")
        return False
    return True

def track_scanner_usage(scanner_type: str, region: str, success: bool = True, 
                       duration_ms: Optional[int] = None, error_message: Optional[str] = None):
    """Track scanner usage"""
    license_integration.track_scan_usage(scanner_type, region, success, duration_ms, error_message)

def require_report_access() -> bool:
    """Check report generation permissions"""
    allowed, message = license_integration.check_report_generation()
    if not allowed:
        st.error(f"Report access denied: {message}")
        return False
    return True

def track_report_usage(report_type: str, success: bool = True):
    """Track report generation"""
    license_integration.track_report_generation(report_type, success)

def track_download_usage(report_type: str):
    """Track report download"""
    license_integration.track_report_download(report_type)

def show_license_sidebar():
    """Show license information in sidebar"""
    license_integration.show_license_status()

def show_usage_dashboard():
    """Show usage analytics dashboard"""
    license_integration.show_usage_dashboard()

# Create license decorator
license_required = license_integration.create_license_decorator()