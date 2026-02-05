"""
Pricing Display Component for DataGuardian Pro
Clean, responsive pricing interface with competitive advantages
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List
from functools import lru_cache
from config.pricing_config import get_pricing_config, PricingTier, BillingCycle
from services.license_integration import LicenseIntegration
from services.auth_tracker import track_pricing_page_view

logger = logging.getLogger(__name__)


class CheckoutStateManager:
    """Centralized session state manager for checkout flow with atomic transitions"""
    
    CHECKOUT_KEYS = [
        'checkout_step',
        'checkout_tier',
        'checkout_billing',
        'checkout_price',
        'checkout_pricing_data',
        'stripe_session_id',
        'stripe_session_url',
    ]
    
    @staticmethod
    def get_step() -> str:
        """Get current checkout step: 'plans', 'confirmation', 'form', 'payment'"""
        return st.session_state.get('checkout_step', 'plans')
    
    @staticmethod
    def start_checkout(tier_value: str, billing_value: str, price: float, pricing_data: Dict[str, Any]):
        """Atomic transition: Start checkout flow with tier selection (stores only serializable primitives)"""
        st.session_state['checkout_step'] = 'confirmation'
        st.session_state['checkout_tier'] = tier_value
        st.session_state['checkout_billing'] = billing_value
        st.session_state['checkout_price'] = price
        st.session_state['checkout_pricing_data'] = pricing_data
    
    @staticmethod
    def proceed_to_form():
        """Atomic transition: Move from confirmation to checkout form"""
        st.session_state['checkout_step'] = 'form'
    
    @staticmethod
    def complete_stripe_session(session_id: str, session_url: str):
        """Store Stripe session for persistence across reruns"""
        st.session_state['checkout_step'] = 'payment'
        st.session_state['stripe_session_id'] = session_id
        st.session_state['stripe_session_url'] = session_url
    
    @staticmethod
    def reset_checkout():
        """Atomic transition: Reset all checkout state"""
        for key in CheckoutStateManager.CHECKOUT_KEYS:
            st.session_state.pop(key, None)
        st.session_state['checkout_step'] = 'plans'
    
    @staticmethod
    def get_checkout_data() -> Dict[str, Any]:
        """Get current checkout data as serializable dict"""
        return {
            'tier': st.session_state.get('checkout_tier'),
            'billing': st.session_state.get('checkout_billing'),
            'price': st.session_state.get('checkout_price'),
            'pricing_data': st.session_state.get('checkout_pricing_data'),
            'stripe_session_id': st.session_state.get('stripe_session_id'),
            'stripe_session_url': st.session_state.get('stripe_session_url'),
        }
    
    @staticmethod
    def has_valid_checkout() -> bool:
        """Check if checkout data is valid"""
        data = CheckoutStateManager.get_checkout_data()
        return bool(data['tier'] and data['billing'] and data['price'])
    
    @staticmethod
    def has_stripe_session() -> bool:
        """Check if a Stripe session exists"""
        return bool(st.session_state.get('stripe_session_url'))


@lru_cache(maxsize=1)
def get_cached_pricing_config():
    """Memoized pricing config to avoid repeated instantiation"""
    return get_pricing_config()


def show_pricing_page():
    """Display the main pricing page with proper routing"""
    from utils.i18n import _
    
    checkout_step = CheckoutStateManager.get_step()
    
    if checkout_step == 'payment' and CheckoutStateManager.has_stripe_session():
        show_payment_redirect()
        return
    
    if checkout_step == 'form' and CheckoutStateManager.has_valid_checkout():
        show_checkout_form_page()
        return
    
    if checkout_step == 'confirmation' and CheckoutStateManager.has_valid_checkout():
        show_checkout_confirmation()
        return
    
    st.title(_('pricing.title', 'DataGuardian Pro Pricing'))
    st.markdown(f"""
    **{_('pricing.subtitle', 'Enterprise-grade privacy compliance at breakthrough prices')}**  
    {_('pricing.description', 'Netherlands-specialized compliance with transparent, competitive pricing')}
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        billing_cycle = st.radio(
            _('pricing.select_billing', 'Select billing:'),
            [_('pricing.billing_monthly', 'Monthly'), _('pricing.billing_annual', 'Annual (Save 2 months)')],
            horizontal=True,
            key="billing_toggle"
        )
    
    billing = BillingCycle.ANNUAL if "Annual" in billing_cycle else BillingCycle.MONTHLY
    
    try:
        show_pricing_cards(billing)
    except Exception as e:
        st.error(f"Error in pricing cards: {e}")
        import traceback
        st.code(traceback.format_exc())
    
    try:
        show_scanner_availability()
    except Exception as e:
        st.error(f"Error in scanner availability: {e}")
        import traceback
        st.code(traceback.format_exc())
    
    try:
        show_competitive_comparison()
    except Exception as e:
        st.error(f"Error in competitive comparison: {e}")
    
    try:
        show_features_comparison()
    except Exception as e:
        st.error(f"Error in features comparison: {e}")
        import traceback
        st.code(traceback.format_exc())
    
    try:
        show_contact_section()
    except Exception as e:
        st.error(f"Error in contact section: {e}")


def render_breadcrumb(current_step: str):
    """Render checkout progress breadcrumb"""
    from utils.i18n import _
    
    steps = [
        ('plans', _('pricing.step_plans', 'Choose Plan')),
        ('confirmation', _('pricing.step_confirm', 'Confirm')),
        ('form', _('pricing.step_details', 'Details')),
        ('payment', _('pricing.step_payment', 'Payment')),
    ]
    
    step_order = ['plans', 'confirmation', 'form', 'payment']
    current_idx = step_order.index(current_step) if current_step in step_order else 0
    
    breadcrumb_html = '<div style="display: flex; gap: 10px; margin-bottom: 20px; font-size: 14px;">'
    for i, (step_key, step_label) in enumerate(steps):
        if i < current_idx:
            style = "color: #28a745; font-weight: bold;"
            prefix = "✓ "
        elif i == current_idx:
            style = "color: #007bff; font-weight: bold;"
            prefix = "● "
        else:
            style = "color: #6c757d;"
            prefix = "○ "
        
        breadcrumb_html += f'<span style="{style}">{prefix}{step_label}</span>'
        if i < len(steps) - 1:
            breadcrumb_html += '<span style="color: #6c757d;">→</span>'
    
    breadcrumb_html += '</div>'
    st.markdown(breadcrumb_html, unsafe_allow_html=True)


def show_checkout_confirmation():
    """Show the checkout confirmation page after tier selection"""
    from utils.i18n import _
    
    render_breadcrumb('confirmation')
    
    data = CheckoutStateManager.get_checkout_data()
    tier_value = data['tier']
    billing_value = data['billing']
    pricing_data = data['pricing_data']
    
    try:
        tier = PricingTier(tier_value)
        billing_cycle = BillingCycle(billing_value)
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Invalid checkout data: tier={tier_value}, billing={billing_value}, error={e}")
        st.error(_('pricing.error_invalid_selection', 'Invalid plan selection. Please try again.'))
        CheckoutStateManager.reset_checkout()
        return
    
    config = get_cached_pricing_config()
    tier_data = config.pricing_data["tiers"].get(tier.value, {})
    
    if st.button(_('pricing.back_to_plans', '← Back to Plans'), key="back_from_confirmation"):
        CheckoutStateManager.reset_checkout()
        st.rerun()
    
    plan_name = str(pricing_data.get('name', tier.value.title()))
    price = pricing_data.get('price', 0)
    
    st.success(_('pricing.selected_plan', 'Selected: {plan} - €{price:,} per {billing}').format(
        plan=plan_name, price=price, billing=billing_cycle.value
    ))
    
    st.markdown(f"### {_('pricing.order_summary', 'Order Summary')}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{_('pricing.plan', 'Plan')}:** {plan_name}")
        st.write(f"**{_('pricing.price', 'Price')}:** €{price:,} per {billing_cycle.value}")
        if billing_cycle == BillingCycle.ANNUAL and pricing_data.get('savings'):
            st.write(f"**{_('pricing.savings', 'Savings')}:** €{pricing_data['savings']:,} vs monthly")
    
    with col2:
        scans = tier_data.get('max_scans_monthly', 'Unlimited')
        sources = tier_data.get('max_data_sources', 'Unlimited')
        support = tier_data.get('support_level', 'Standard').replace('_', ' ').title()
        st.write(f"**{_('pricing.scans', 'Scans')}:** {scans}/month")
        st.write(f"**{_('pricing.data_sources', 'Data Sources')}:** {sources}")
        st.write(f"**{_('pricing.support', 'Support')}:** {support}")
    
    st.markdown("---")
    st.markdown(f"### {_('pricing.next_steps', 'Next Steps')}:")
    st.markdown(f"- **{_('pricing.setup', 'Setup')}**: {_('pricing.instant_activation', 'Instant activation')}")
    st.markdown(f"- **{_('pricing.support_included', 'Support')}**: {_('pricing.included_in_plan', 'Included in your plan')}")
    st.markdown(f"- **{_('pricing.billing_secure', 'Billing')}**: {_('pricing.stripe_secure', 'Secure payment processing via Stripe')}")
    st.markdown(f"- **{_('pricing.guarantee', 'Guarantee')}**: {_('pricing.money_back', '30-day money-back guarantee')}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(_('pricing.proceed_checkout', '💳 Proceed to Checkout'), type="primary", key="proceed_to_checkout_btn"):
            CheckoutStateManager.proceed_to_form()
            st.rerun()
    
    with col2:
        if st.button(_('pricing.view_details', '📋 View Plan Details'), key="view_plan_details_btn"):
            show_plan_details(tier, pricing_data)


def show_payment_redirect():
    """Show payment redirect page with persisted Stripe session"""
    from utils.i18n import _
    
    render_breadcrumb('payment')
    
    data = CheckoutStateManager.get_checkout_data()
    session_url = data.get('stripe_session_url')
    pricing_data = data.get('pricing_data', {})
    
    if st.button(_('pricing.back_to_plans', '← Back to Plans'), key="back_from_payment"):
        CheckoutStateManager.reset_checkout()
        st.rerun()
    
    st.success(_('pricing.checkout_ready', 'Checkout session ready!'))
    
    plan_name = str(pricing_data.get('name', 'Selected Plan'))
    price = pricing_data.get('price', 0)
    
    st.info(f"**{_('pricing.order', 'Order')}:** {plan_name} - €{price:,}")
    
    if session_url:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <a href="{session_url}" target="_self" 
               style="display: inline-block; padding: 15px 30px; 
                      background: #635bff; color: white; text-decoration: none; 
                      border-radius: 8px; font-weight: bold; font-size: 18px;">
                {_('pricing.complete_payment', 'Complete Payment Securely')}
            </a>
            <p style="font-size: 12px; color: #666; margin-top: 15px;">
                {_('pricing.secured_by_stripe', 'Secured by Stripe | SSL Encrypted | GDPR Compliant')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.link_button(_('pricing.click_if_not_redirected', 'Click here if not redirected'), session_url, type="primary")
    else:
        st.error(_('pricing.session_expired', 'Payment session expired. Please try again.'))
        if st.button(_('pricing.try_again', 'Try Again')):
            CheckoutStateManager.reset_checkout()
            st.rerun()

def show_pricing_cards(billing_cycle: BillingCycle):
    """Display pricing cards for all tiers"""
    config = get_cached_pricing_config()
    license_integration = LicenseIntegration()
    current_tier = license_integration.get_current_pricing_tier()
    
    st.markdown("## Choose Your Plan")
    
    # Standard tiers - 4 columns for 4 main tiers
    tiers = [PricingTier.STARTUP, PricingTier.PROFESSIONAL, PricingTier.GROWTH, PricingTier.SCALE]
    cols = st.columns(len(tiers))
    
    # Premium connector tiers (displayed separately for prominence)
    premium_tiers = [PricingTier.SALESFORCE_PREMIUM, PricingTier.SAP_ENTERPRISE, PricingTier.ENTERPRISE]
    
    for i, tier in enumerate(tiers):
        with cols[i]:
            pricing = config.get_tier_pricing(tier, billing_cycle)
            tier_data = config.pricing_data["tiers"][tier.value]
            
            # Card styling
            is_current = (current_tier == tier) if current_tier else False
            is_popular = tier_data.get("most_popular", False)
            
            if is_popular:
                st.markdown("🔥 **MOST POPULAR**")
            elif is_current:
                st.markdown("✅ **CURRENT PLAN**")
            
            # Pricing header
            st.markdown(f"### {pricing['name']}")
            
            if billing_cycle == BillingCycle.ANNUAL:
                st.markdown(f"**€{pricing['price']:,}/year**")
                st.markdown(f"*€{tier_data['monthly_price']}/month billed annually*")
                if 'savings' in pricing:
                    st.success(f"💰 Save €{pricing['savings']:,} vs monthly")
            else:
                st.markdown(f"**€{pricing['price']:,}/month**")
            
            # Target info
            st.markdown(f"**For {tier_data['target_employees']} employees**")
            st.markdown(f"*{tier_data['target_revenue']}*")
            
            # Key features (top 4)
            st.markdown("**Key Features:**")
            key_features = get_tier_key_features(tier)
            for feature in key_features[:4]:
                st.markdown(f"✅ {feature}")
            
            # Limits
            st.markdown(f"📊 {tier_data.get('max_scans_monthly', 'Unlimited')} scans/month")
            st.markdown(f"🔌 {tier_data.get('max_data_sources', 'Unlimited')} data sources")
            
            # CTA button
            button_text = "Current Plan" if is_current else f"Select {tier.value.title()}"
            button_disabled = is_current
            button_type = "secondary" if is_current else ("primary" if is_popular else "secondary")
            
            if st.button(button_text, key=f"select_{tier.value}", disabled=button_disabled, type=button_type):
                handle_tier_selection(tier, billing_cycle)
    
    # Premium Enterprise Connector Tiers
    st.markdown("---")
    st.markdown("## 🚀 Premium Enterprise Connectors")
    st.markdown("**For enterprises using Salesforce CRM or SAP ERP systems**")
    
    premium_cols = st.columns(3)
    for i, tier in enumerate(premium_tiers):
        with premium_cols[i]:
            pricing = config.get_tier_pricing(tier, billing_cycle)
            tier_data = config.pricing_data["tiers"][tier.value]
            
            # Premium tier styling
            is_current = (current_tier == tier) if current_tier else False
            
            if tier == PricingTier.ENTERPRISE:
                st.markdown("⭐ **ULTIMATE**")
            elif tier == PricingTier.SAP_ENTERPRISE:
                st.markdown("💼 **SAP PREMIUM**")
            elif tier == PricingTier.SALESFORCE_PREMIUM:
                st.markdown("🔥 **CRM PREMIUM**")
            
            # Pricing header
            st.markdown(f"### {pricing['name']}")
            
            if billing_cycle == BillingCycle.ANNUAL:
                st.markdown(f"**€{pricing['price']:,}/year**")
                st.markdown(f"*€{tier_data['monthly_price']}/month billed annually*")
                if 'savings' in pricing:
                    st.success(f"💰 Save €{pricing['savings']:,} vs monthly")
            else:
                st.markdown(f"**€{pricing['price']:,}/month**")
            
            # Target info
            st.markdown(f"**For {tier_data['target_employees']} employees**")
            st.markdown(f"*{tier_data['target_revenue']}*")
            
            # Premium features
            st.markdown("**Premium Features:**")
            premium_features = get_tier_premium_features(tier)
            for feature in premium_features[:4]:
                st.markdown(f"✅ {feature}")
            
            # CTA button
            button_text = "Current Plan" if is_current else f"Select {tier.value.replace('_', ' ').title()}"
            button_disabled = is_current
            button_type = "secondary" if is_current else "primary"
            
            if st.button(button_text, key=f"select_premium_{tier.value}", disabled=button_disabled, type=button_type):
                handle_tier_selection(tier, billing_cycle)
    
    # Government/Enterprise license
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏛️ Government & Enterprise License")
        st.markdown("**€15,000** one-time license")
        st.markdown("**€2,500/year** maintenance")
        st.markdown("**Features:**")
        st.markdown("✅ On-premises deployment")
        st.markdown("✅ Source code access")
        st.markdown("✅ Custom development")
        st.markdown("✅ Government compliance")
        st.markdown("✅ Unlimited everything")
    
    with col2:
        st.markdown("**Perfect for:**")
        st.markdown("• Government agencies")
        st.markdown("• Large enterprises (500+ employees)")
        st.markdown("• Organizations requiring on-premises")
        st.markdown("• Custom compliance requirements")
        
        # Check if user already has Government tier
        current_tier = st.session_state.get('pricing_tier', PricingTier.FREE)
        # Handle both string and enum values
        if isinstance(current_tier, str):
            is_current = current_tier.lower() == 'government'
        else:
            is_current = current_tier == PricingTier.GOVERNMENT
        
        if is_current:
            st.success("✅ Current Plan")
        else:
            if st.button("Select Government & Enterprise", key="select_government_enterprise", type="primary"):
                handle_tier_selection(PricingTier.GOVERNMENT, 'yearly')
        
        st.markdown("")
        if st.button("📞 Contact Sales", key="contact_government", type="secondary"):
            st.session_state['contact_sales'] = True
            st.rerun()

def get_tier_scanner_count(tier: PricingTier) -> tuple:
    """Get scanner count and list for a tier"""
    scanner_mapping = {
        PricingTier.STARTUP: (6, ["Code", "Document", "Database", "Image", "Website", "AI Model"]),
        PricingTier.PROFESSIONAL: (9, ["All Startup +", "DPIA", "SOC2/NIS2", "API Scanner"]),
        PricingTier.GROWTH: (12, ["All Professional +", "Enterprise Connectors", "Sustainability", "Repository"]),
        PricingTier.SCALE: (15, ["All 15 Scanners", "Audio/Video Deepfake", "Cookie Scanner", "Advanced AI"]),
        PricingTier.SALESFORCE_PREMIUM: (15, ["All 15 Scanners", "Salesforce CRM", "Advanced AI"]),
        PricingTier.SAP_ENTERPRISE: (15, ["All 15 Scanners", "SAP ERP", "Advanced AI"]),
        PricingTier.ENTERPRISE: (15, ["All 15 Scanners", "Data Sovereignty", "Salesforce + SAP", "Banking PSD2"]),
        PricingTier.GOVERNMENT: (15, ["All 15 Scanners", "Data Sovereignty", "On-Premises", "Custom Dev"]),
    }
    return scanner_mapping.get(tier, (6, ["Basic scanners"]))


def get_tier_key_features(tier: PricingTier) -> List[str]:
    """Get user-friendly key features for a tier"""
    feature_mapping = {
        PricingTier.STARTUP: [
            "6 Core Scanners included",
            "GDPR compliance reports", 
            "Netherlands BSN detection",
            "Email support",
            "200 scans/month",
            "20 data sources"
        ],
        PricingTier.PROFESSIONAL: [
            "9 Scanners (+DPIA, SOC2, API)",
            "350 scans/month",
            "Advanced scanning",
            "Compliance automation",
            "Priority email & phone support",
            "Compliance certificates"
        ],
        PricingTier.GROWTH: [
            "12 Scanners (+Enterprise, Repo)",
            "Enterprise data connectors",
            "Microsoft 365 integration",
            "Exact Online connector",
            "750 scans/month",
            "75 data sources"
        ],
        PricingTier.SCALE: [
            "All 15 Scanners",
            "Audio/Video Deepfake Detection",
            "Repository & Cookie Scanners",
            "EU AI Act compliance",
            "Unlimited scans",
            "Dedicated support 24/7"
        ],
        PricingTier.SALESFORCE_PREMIUM: [
            "Salesforce CRM connector",
            "Netherlands BSN/KvK detection in CRM",
            "Advanced CRM field mapping",
            "Dedicated compliance team",
            "Unlimited scans & sources",
            "Priority support"
        ],
        PricingTier.SAP_ENTERPRISE: [
            "SAP ERP connector (HR/Finance)",
            "BSN detection in SAP modules",
            "ERP data governance",
            "20 SAP consulting hours included",
            "Unlimited scans & sources",
            "Dedicated team 24/7"
        ],
        PricingTier.ENTERPRISE: [
            "All 15 Scanners + Premium",
            "Salesforce + SAP connectors",
            "Dutch Banking PSD2 integration",
            "White-label deployment",
            "24/7 executive partnership",
            "Unlimited everything"
        ],
        PricingTier.GOVERNMENT: [
            "On-premises deployment",
            "Source code access",
            "Custom development",
            "Government compliance",
            "Unlimited everything",
            "Enterprise support"
        ]
    }
    
    return feature_mapping.get(tier, [
        "Contact sales for details",
        "Full compliance features",
        "Priority support",
        "Custom configuration"
    ])

def get_tier_premium_features(tier: PricingTier) -> List[str]:
    """Get premium features for enterprise connector tiers"""
    premium_feature_mapping = {
        PricingTier.SALESFORCE_PREMIUM: [
            "Salesforce CRM connector",
            "Netherlands BSN/KvK detection in CRM", 
            "Advanced CRM field mapping",
            "Dedicated compliance team"
        ],
        PricingTier.SAP_ENTERPRISE: [
            "SAP ERP connector (HR/Finance)",
            "BSN detection in SAP modules",
            "ERP data governance", 
            "SAP consulting hours included"
        ],
        PricingTier.ENTERPRISE: [
            "Salesforce + SAP connectors",
            "Dutch Banking PSD2 integration",
            "Advanced BSN/KvK validation",
            "Executive partnership 24/7"
        ]
    }
    
    return premium_feature_mapping.get(tier, [])

def show_scanner_availability():
    """Show which scanners are available in each plan"""
    from utils.i18n import _
    
    st.markdown("## 🔍 Scanner Availability by Plan")
    st.markdown("**DataGuardian Pro includes 15 specialized compliance scanners**")
    
    # Scanner definitions with icons - Complete list of all 15 scanners + Data Sovereignty
    scanners = [
        ("Code Scanner", "Detects PII in source code & repositories"),
        ("Document Scanner", "PDF, Word, Excel file scanning"),
        ("Database Scanner", "PostgreSQL, MySQL, SQL Server"),
        ("Image Scanner (OCR)", "Extracts text from images/screenshots"),
        ("Website Scanner", "Crawls websites for privacy issues"),
        ("AI Model Scanner", "EU AI Act compliance checks"),
        ("DPIA Scanner", "Data Protection Impact Assessments"),
        ("SOC2/NIS2 Scanner", "Security compliance auditing"),
        ("Enterprise Connectors", "Microsoft 365, Exact Online, Google"),
        ("Sustainability Scanner", "Cloud resource efficiency analysis"),
        ("Audio/Video Deepfake", "AI-powered media authentication"),
        ("API Scanner", "REST API endpoint PII detection"),
        ("Repository Scanner", "Git repo scanning for PCI-DSS & GDPR"),
        ("Cookie Scanner", "Cookie & tracking compliance"),
        ("Advanced AI Analysis", "GPT-4 powered deep analysis"),
        ("Data Sovereignty Scanner", "Cross-border transfer & jurisdictional compliance"),
    ]
    
    # Tier availability - Updated counts (Data Sovereignty only for Enterprise/Government)
    tier_scanners = {
        "Startup": 6,
        "Professional": 9,
        "Growth": 12,
        "Scale": 15,
        "Enterprise": 16,  # Includes Data Sovereignty
    }
    
    with st.expander("📋 View Full Scanner Comparison", expanded=False):
        cols = st.columns([2, 1, 1, 1, 1, 1])
        cols[0].markdown("**Scanner**")
        cols[1].markdown("**Startup**")
        cols[2].markdown("**Professional**")
        cols[3].markdown("**Growth**")
        cols[4].markdown("**Scale**")
        cols[5].markdown("**Enterprise**")
        
        for idx, (scanner_name, scanner_desc) in enumerate(scanners):
            cols = st.columns([2, 1, 1, 1, 1, 1])
            cols[0].markdown(f"**{scanner_name}**")
            cols[0].caption(scanner_desc)
            
            # Data Sovereignty Scanner (index 15) only for Enterprise/Government
            if scanner_name == "Data Sovereignty Scanner":
                cols[1].markdown("❌")  # Startup: No
                cols[2].markdown("❌")  # Professional: No
                cols[3].markdown("❌")  # Growth: No
                cols[4].markdown("❌")  # Scale: No
                cols[5].markdown("✅")  # Enterprise/Government: Yes
            else:
                # Check availability per tier (updated for 15 scanners)
                cols[1].markdown("✅" if idx < 6 else "❌")   # Startup: 6
                cols[2].markdown("✅" if idx < 9 else "❌")   # Professional: 9
                cols[3].markdown("✅" if idx < 12 else "❌")  # Growth: 12
                cols[4].markdown("✅")  # Scale has all 15
                cols[5].markdown("✅")  # Enterprise has all 15
        
        st.markdown("---")
        st.markdown("**Total Scanners:**")
        cols = st.columns([2, 1, 1, 1, 1, 1])
        cols[0].markdown("")
        cols[1].markdown("**6**")
        cols[2].markdown("**9**")
        cols[3].markdown("**12**")
        cols[4].markdown("**15**")
        cols[5].markdown("**16**")  # Enterprise includes Data Sovereignty


def show_competitive_comparison():
    """Show DataGuardian Pro's unique competitive advantages"""
    from utils.i18n import _
    
    st.markdown("## 💡 Why DataGuardian Pro?")
    st.markdown("**Enterprise-grade features built for the Netherlands market**")
    
    # Unique advantages
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### 🇳🇱 {_('pricing.netherlands_specialization', 'Netherlands Specialization')}")
        st.markdown(f"• {_('pricing.bsn_detection', 'BSN (Dutch Social Security) detection')}")
        st.markdown(f"• {_('pricing.kvk_validation', 'KvK number validation')}")
        st.markdown(f"• {_('pricing.uavg_compliance', 'UAVG compliance rules')}")
        st.markdown(f"• {_('pricing.dutch_ap_integration', 'Dutch AP authority integration')}")
        st.markdown(f"• {_('pricing.dutch_language', 'Native Dutch language support')}")
    
    with col2:
        st.markdown("### 🚀 Unique Features")
        st.markdown("• Only solution with Exact Online connector")
        st.markdown("• 60% of Dutch SMEs use Exact Online")
        st.markdown("• EU AI Act 2025 compliance")
        st.markdown("• Real-time compliance monitoring")
        st.markdown("• Professional compliance certificates")

def show_features_comparison():
    """Show detailed features comparison table"""
    if st.checkbox("Show detailed features comparison"):
        config = get_pricing_config()
        
        # Create features matrix
        features_data = []
        all_features = set()
        
        # Collect all features
        for category, features in config.features_matrix.items():
            for feature in features.keys():
                all_features.add(feature)
        
        tiers = [PricingTier.STARTUP, PricingTier.PROFESSIONAL, PricingTier.GROWTH, PricingTier.SCALE, PricingTier.SALESFORCE_PREMIUM, PricingTier.SAP_ENTERPRISE, PricingTier.ENTERPRISE]
        
        # Build comparison matrix
        for feature in sorted(all_features):
            row = {"Feature": feature.replace("_", " ").title()}
            for tier in tiers:
                available_features = config.get_features_for_tier(tier)
                row[tier.value.title()] = "✅" if feature in available_features else "❌"
            features_data.append(row)
        
        st.table(features_data)

def show_contact_section():
    """Show contact and support section"""
    st.markdown("---")
    st.markdown("## 📞 Questions? We're Here to Help")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 💬 Sales Support")
        st.markdown("Need help choosing the right plan?")
        if st.button("Contact Sales Team", key="contact_sales_main"):
            st.session_state['contact_sales'] = True
            st.rerun()
    
    with col2:
        st.markdown("### 🔧 Technical Questions")
        st.markdown("Have technical implementation questions?")
        if st.button("Talk to Engineers", key="contact_tech"):
            st.session_state['contact_tech'] = True
            st.rerun()
    
    with col3:
        st.markdown("### 📊 Custom Requirements")
        st.markdown("Need custom features or enterprise deployment?")
        if st.button("Request Custom Quote", key="custom_quote"):
            st.session_state['custom_quote'] = True
            st.rerun()

def handle_tier_selection(tier: PricingTier, billing_cycle: BillingCycle):
    """Handle when user selects a pricing tier"""
    config = get_cached_pricing_config()
    pricing = config.get_tier_pricing(tier, billing_cycle)
    
    track_pricing_page_view(tier.value, page_path="/pricing")
    
    CheckoutStateManager.start_checkout(
        tier_value=tier.value,
        billing_value=billing_cycle.value,
        price=pricing['price'],
        pricing_data=pricing
    )
    
    st.rerun()


def show_checkout_form_page():
    """Show checkout form page with Stripe integration"""
    from utils.i18n import _
    import os
    import stripe
    
    render_breadcrumb('form')
    
    data = CheckoutStateManager.get_checkout_data()
    tier_value = data['tier']
    billing_value = data['billing']
    pricing_data = data['pricing_data']
    
    try:
        tier = PricingTier(tier_value)
        billing_cycle = BillingCycle(billing_value)
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Invalid checkout data in form: tier={tier_value}, billing={billing_value}, error={e}")
        st.error(_('pricing.error_invalid_selection', 'Invalid plan selection. Please try again.'))
        CheckoutStateManager.reset_checkout()
        return
    
    if st.button(_('pricing.back_to_plans', '← Back to Plans'), key="back_from_form"):
        CheckoutStateManager.reset_checkout()
        st.rerun()
    
    plan_name = str(pricing_data.get('name', tier.value.title()))
    price = pricing_data.get('price', 0)
    
    st.markdown(f"### {_('pricing.secure_checkout', 'Secure Checkout')}")
    
    st.info(f"""
    **{_('pricing.order_summary', 'Order Summary')}:**
    - **{_('pricing.plan', 'Plan')}**: {plan_name}
    - **{_('pricing.price', 'Price')}**: €{price:,} per {billing_cycle.value}
    - **{_('pricing.billing', 'Billing')}**: {_('pricing.annual_save', 'Annual (save 2 months)') if billing_cycle == BillingCycle.ANNUAL else _('pricing.monthly', 'Monthly')}
    """)
    
    st.success(_('pricing.money_back_note', '30-day money-back guarantee included with all plans'))
    
    with st.form("checkout_form"):
        st.markdown(f"**{_('pricing.contact_info', 'Contact Information')}**")
        
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input(_('pricing.company_name', 'Company Name*'), key="company_name")
            first_name = st.text_input(_('pricing.first_name', 'First Name*'), key="first_name")
            email = st.text_input(_('pricing.email', 'Email Address*'), key="email")
        
        with col2:
            country = st.selectbox(_('pricing.country', 'Country*'), ["Netherlands", "Belgium", "Germany", "Other EU"], key="country")
            last_name = st.text_input(_('pricing.last_name', 'Last Name*'), key="last_name")
            phone = st.text_input(_('pricing.phone', 'Phone Number'), key="phone")
        
        st.markdown(f"**{_('pricing.billing_address', 'Billing Address')}**")
        address = st.text_input(_('pricing.street_address', 'Street Address*'), key="address")
        col1, col2, col3 = st.columns(3)
        with col1:
            city = st.text_input(_('pricing.city', 'City*'), key="city")
        with col2:
            postal_code = st.text_input(_('pricing.postal_code', 'Postal Code*'), key="postal")
        with col3:
            vat_number = st.text_input(_('pricing.vat_number', 'VAT Number (optional)'), key="vat")
        
        st.markdown(f"**{_('pricing.payment_methods', 'Payment Methods Available')}:**")
        st.markdown(_('pricing.payment_options', 'Credit Card, iDEAL (Netherlands), SEPA Direct Debit'))
        
        terms_accepted = st.checkbox(_('pricing.accept_terms', 'I accept the Terms of Service and Privacy Policy*'))
        
        submitted = st.form_submit_button(_('pricing.continue_payment', 'Continue to Payment'), type="primary")
        
        if submitted:
            if not all([company_name, first_name, last_name, email, address, city, postal_code]) or not terms_accepted:
                st.error(_('pricing.fill_required', 'Please fill in all required fields and accept the terms.'))
            else:
                create_stripe_checkout(
                    tier=tier,
                    billing_cycle=billing_cycle,
                    pricing=pricing_data,
                    customer_data={
                        'company_name': company_name,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'phone': phone,
                        'country': country,
                        'address': address,
                        'city': city,
                        'postal_code': postal_code,
                        'vat_number': vat_number,
                    }
                )


def get_stripe_price_id(tier: PricingTier, billing_cycle: BillingCycle) -> Optional[str]:
    """Get Stripe Price ID from environment variables based on tier and billing cycle"""
    import os
    
    tier_map = {
        PricingTier.STARTUP: "STARTUP",
        PricingTier.PROFESSIONAL: "PROFESSIONAL",
        PricingTier.GROWTH: "GROWTH",
        PricingTier.SCALE: "SCALE",
        PricingTier.SALESFORCE_PREMIUM: "SALESFORCE",
        PricingTier.SAP_ENTERPRISE: "SAP",
        PricingTier.ENTERPRISE: "ENTERPRISE",
    }
    
    tier_key = tier_map.get(tier, tier.value.upper())
    billing_key = "ANNUAL" if billing_cycle == BillingCycle.ANNUAL else "MONTHLY"
    
    env_key = f"STRIPE_PRICE_{tier_key}_{billing_key}"
    price_id = os.getenv(env_key)
    
    if price_id and price_id.startswith('price_'):
        return price_id
    
    return None


def create_stripe_checkout(tier: PricingTier, billing_cycle: BillingCycle, pricing: Dict[str, Any], customer_data: Dict[str, str]):
    """Create Stripe checkout session with proper error handling"""
    from utils.i18n import _
    import os
    import stripe
    
    try:
        user_id = st.session_state.get('user_id') or st.session_state.get('user', {}).get('id')
        if not user_id:
            logger.warning("Checkout attempted without user login")
            st.error(_('pricing.login_required', 'Please log in before subscribing.'))
            return
        
        stripe_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe_key:
            logger.error("STRIPE_SECRET_KEY not configured")
            st.error(_('pricing.payment_not_configured', 'Payment system not configured. Please contact support.'))
            return
        
        stripe.api_key = stripe_key
        
        country_codes = {"Netherlands": "NL", "Belgium": "BE", "Germany": "DE", "Other EU": "NL"}
        country_code = country_codes.get(customer_data['country'], "NL")
        
        price_cents = int(pricing.get('price', 0) * 100)
        interval = "year" if billing_cycle == BillingCycle.ANNUAL else "month"
        
        base_url = os.getenv('BASE_URL')
        if not base_url:
            replit_domain = os.getenv('REPLIT_DEV_DOMAIN')
            if replit_domain:
                base_url = f"https://{replit_domain}"
            else:
                base_url = 'https://dataguardianpro.nl'
        
        payment_methods = ["card"]
        if country_code == "NL":
            payment_methods.extend(["ideal", "sepa_debit"])
        
        plan_name = str(pricing.get('name', tier.value.title()))
        
        stripe_price_id = get_stripe_price_id(tier, billing_cycle)
        
        if stripe_price_id:
            line_items = [{
                "price": stripe_price_id,
                "quantity": 1,
            }]
            logger.info(f"Using Stripe Price ID: {stripe_price_id} for {tier.value} {billing_cycle.value}")
        else:
            line_items = [{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"DataGuardian Pro - {plan_name}",
                        "description": f"{tier.value.title()} plan with full GDPR compliance features",
                    },
                    "unit_amount": price_cents,
                    "recurring": {
                        "interval": interval,
                        "interval_count": 1,
                    }
                },
                "quantity": 1,
            }]
            logger.info(f"Using inline price_data for {tier.value} {billing_cycle.value} (no Price ID configured)")
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=payment_methods,  # type: ignore
            line_items=line_items,
            mode="subscription",
            success_url=f"{base_url}?payment_success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}?payment_cancelled=true",
            customer_email=customer_data['email'],
            metadata={
                "tier": tier.value,
                "plan_tier": tier.value,
                "user_id": str(user_id),
                "billing_cycle": billing_cycle.value,
                "company_name": customer_data['company_name'][:500],
                "first_name": customer_data['first_name'][:100],
                "last_name": customer_data['last_name'][:100],
                "country": country_code,
                "vat_number": (customer_data.get('vat_number') or "")[:50],
            },
            subscription_data={
                "metadata": {
                    "tier": tier.value,
                    "plan_tier": tier.value,
                    "user_id": str(user_id),
                }
            },
            billing_address_collection="required",
            tax_id_collection={"enabled": True},
        )
        
        if checkout_session.id and checkout_session.url:
            CheckoutStateManager.complete_stripe_session(
                session_id=checkout_session.id,
                session_url=checkout_session.url
            )
            st.rerun()
        else:
            logger.error("Stripe session created without URL")
            st.error(_('pricing.session_error', 'Failed to create payment session. Please try again.'))
            
    except stripe.CardError as e:
        logger.error(f"Stripe CardError: {e.user_message}")
        st.error(_('pricing.card_error', 'Card error: {message}').format(message=e.user_message))
    except stripe.RateLimitError as e:
        logger.error(f"Stripe RateLimitError: {e}")
        st.error(_('pricing.rate_limit', 'Too many requests. Please wait a moment and try again.'))
    except stripe.InvalidRequestError as e:
        logger.error(f"Stripe InvalidRequestError: {e}")
        st.error(_('pricing.invalid_request', 'Invalid request. Please check your information and try again.'))
    except stripe.AuthenticationError as e:
        logger.error(f"Stripe AuthenticationError: {e}")
        st.error(_('pricing.payment_config_error', 'Payment configuration error. Please contact support.'))
    except stripe.APIConnectionError as e:
        logger.error(f"Stripe APIConnectionError: {e}")
        st.error(_('pricing.connection_error', 'Connection error. Please check your internet and try again.'))
    except stripe.StripeError as e:
        logger.error(f"Stripe generic error: {e}")
        st.error(_('pricing.payment_error', 'Payment service error. Please try again or contact support.'))
    except Exception as e:
        logger.error(f"Unexpected error in Stripe checkout: {type(e).__name__}: {e}")
        st.error(_('pricing.unexpected_error', 'An unexpected error occurred. Please try again or contact support.'))

def show_plan_details(tier: PricingTier, pricing: Dict[str, Any]):
    """Show detailed plan information"""
    config = get_pricing_config()
    features = config.get_features_for_tier(tier)
    tier_data = config.pricing_data["tiers"][tier.value]
    
    st.markdown(f"### {pricing['name']} - Detailed Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Plan Limits:**")
        st.markdown(f"• Max scans per month: {tier_data.get('max_scans_monthly', 'Unlimited')}")
        st.markdown(f"• Max data sources: {tier_data.get('max_data_sources', 'Unlimited')}")
        st.markdown(f"• Support level: {tier_data.get('support_level', 'Standard')}")
        st.markdown(f"• Response SLA: {tier_data.get('sla_hours', 48)} hours")
    
    with col2:
        st.markdown("**Included Features:**")
        for feature in features:
            st.markdown(f"✅ {feature.replace('_', ' ').title()}")

# Helper function for main app integration
def show_pricing_in_sidebar():
    """Show pricing info in sidebar - respects user's session tier"""
    # First check user's individual license tier from session
    user_license_tier = st.session_state.get('license_tier', None)
    
    if user_license_tier:
        # User has session-based tier - show that instead of global
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
        st.sidebar.markdown(f"**Current Plan**: {plan_name}")
        return
    
    # Fall back to global license tier
    license_integration = LicenseIntegration()
    current_tier = license_integration.get_current_pricing_tier()
    
    if current_tier:
        config = get_pricing_config()
        # Handle both string and enum values
        tier_key = current_tier.value if hasattr(current_tier, 'value') else str(current_tier)
        tier_data = config.pricing_data["tiers"].get(tier_key, {})
        plan_name = tier_data.get('name', tier_key.title() if tier_key else 'Unknown')
        st.sidebar.markdown(f"**Current Plan**: {plan_name}")
        
        # Check if enterprise tier
        is_enterprise = (current_tier == PricingTier.ENTERPRISE) if hasattr(current_tier, 'value') else (str(current_tier).lower() == 'enterprise')
        if not is_enterprise:
            # Enterprise license detected - no upgrade needed
            pass