"""
Pricing Display Component for DataGuardian Pro
Clean, responsive pricing interface with competitive advantages
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from config.pricing_config import get_pricing_config, PricingTier, BillingCycle
from services.license_integration import LicenseIntegration
from services.auth_tracker import track_pricing_page_view

def show_pricing_page():
    """Display the main pricing page"""
    # Import i18n for translations
    from utils.i18n import _
    
    # Check if user is in checkout flow
    if st.session_state.get('show_checkout_form', False):
        tier = st.session_state.get('checkout_tier')
        billing = st.session_state.get('checkout_billing')
        pricing = st.session_state.get('checkout_pricing')
        
        if tier and billing and pricing:
            # Show back button
            if st.button("Back to Plans", key="back_to_plans"):
                st.session_state['show_checkout_form'] = False
                st.session_state.pop('checkout_tier', None)
                st.session_state.pop('checkout_billing', None)
                st.session_state.pop('checkout_pricing', None)
                st.session_state.pop('selected_tier', None)
                st.session_state.pop('show_checkout', None)
                st.rerun()
            
            # Show checkout form
            show_checkout_form(tier, billing, pricing)
            return
    
    # Check if a tier has been selected (show the checkout confirmation)
    if st.session_state.get('show_checkout', False) and st.session_state.get('selected_tier'):
        show_checkout_confirmation()
        return
    
    # Header section
    st.title(f"{_('pricing.title', 'DataGuardian Pro Pricing')}")
    st.markdown(f"""
    **{_('pricing.subtitle', 'Enterprise-grade privacy compliance at breakthrough prices')}**  
    {_('pricing.description', 'Netherlands-specialized compliance with transparent, competitive pricing')}
    """)
    
    # Billing toggle with translations
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        billing_cycle = st.radio(
            "Select billing:",
            [_('pricing.billing_monthly', 'Monthly'), _('pricing.billing_annual', 'Annual (Save 2 months)')],
            horizontal=True,
            key="billing_toggle"
        )
    
    billing = BillingCycle.ANNUAL if "Annual" in billing_cycle else BillingCycle.MONTHLY
    
    # Main pricing cards
    show_pricing_cards(billing)
    
    # Competitive comparison
    show_competitive_comparison()
    
    # Features comparison table
    show_features_comparison()
    
    # Contact section
    show_contact_section()


def show_checkout_confirmation():
    """Show the checkout confirmation page after tier selection"""
    from utils.i18n import _
    
    tier_value = st.session_state.get('selected_tier')
    billing_value = st.session_state.get('selected_billing')
    price = st.session_state.get('selected_price')
    
    # Convert tier value to PricingTier enum
    try:
        tier = PricingTier(tier_value)
        billing_cycle = BillingCycle(billing_value)
    except (ValueError, KeyError):
        st.error("Invalid plan selection. Please try again.")
        st.session_state.pop('selected_tier', None)
        st.session_state.pop('show_checkout', None)
        return
    
    config = get_pricing_config()
    pricing = config.get_tier_pricing(tier, billing_cycle)
    tier_data = config.pricing_data["tiers"][tier.value]
    
    # Back button
    if st.button("Back to Plans", key="back_from_confirmation"):
        st.session_state.pop('selected_tier', None)
        st.session_state.pop('selected_billing', None)
        st.session_state.pop('selected_price', None)
        st.session_state.pop('show_checkout', None)
        st.rerun()
    
    st.success(f"Selected {pricing['name']} - €{pricing['price']:,} per {billing_cycle.value}")
    
    # Show order summary
    st.markdown("### Order Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Plan:** {pricing['name']}")
        st.markdown(f"**Price:** €{pricing['price']:,} per {billing_cycle.value}")
        if billing_cycle == BillingCycle.ANNUAL and 'savings' in pricing:
            st.markdown(f"**Savings:** €{pricing['savings']:,} vs monthly")
    
    with col2:
        st.markdown(f"**Scans:** {tier_data.get('max_scans_monthly', 'Unlimited')}/month")
        st.markdown(f"**Data Sources:** {tier_data.get('max_data_sources', 'Unlimited')}")
        st.markdown(f"**Support:** {tier_data.get('support_level', 'Standard').replace('_', ' ').title()}")
    
    st.markdown("---")
    st.markdown("### Next Steps:")
    st.markdown("- **Setup**: Instant activation")
    st.markdown("- **Support**: Included in your plan")
    st.markdown("- **Billing**: Secure payment processing via Stripe")
    st.markdown("- **Guarantee**: 30-day money-back guarantee")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Proceed to Checkout", type="primary", key="proceed_to_checkout_btn"):
            st.session_state['checkout_tier'] = tier
            st.session_state['checkout_billing'] = billing_cycle
            st.session_state['checkout_pricing'] = pricing
            st.session_state['show_checkout_form'] = True
            st.rerun()
    
    with col2:
        if st.button("View Plan Details", key="view_plan_details_btn"):
            show_plan_details(tier, pricing)

def show_pricing_cards(billing_cycle: BillingCycle):
    """Display pricing cards for all tiers"""
    config = get_pricing_config()
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
        
        if st.button("📞 Contact Sales", key="contact_government", type="primary"):
            st.session_state['contact_sales'] = True
            st.rerun()

def get_tier_key_features(tier: PricingTier) -> List[str]:
    """Get user-friendly key features for a tier"""
    feature_mapping = {
        PricingTier.STARTUP: [
            "Basic PII scanning",
            "GDPR compliance reports", 
            "Netherlands BSN detection",
            "Email support",
            "200 scans/month",
            "20 data sources"
        ],
        PricingTier.PROFESSIONAL: [
            "350 scans/month",
            "35 data sources",
            "Advanced scanning",
            "Compliance automation",
            "Priority email & phone support",
            "Compliance certificates"
        ],
        PricingTier.GROWTH: [
            "Enterprise data connectors",
            "Microsoft 365 integration",
            "Exact Online connector",
            "Compliance certificates",
            "750 scans/month",
            "75 data sources"
        ],
        PricingTier.SCALE: [
            "Unlimited scans & data sources",
            "Advanced AI scanning",
            "EU AI Act compliance",
            "Custom integrations",
            "DPIA automation",
            "Dedicated support team 24/7"
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
            "Salesforce + SAP connectors",
            "Dutch Banking PSD2 integration",
            "White-label deployment",
            "API access & Custom development",
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
    config = get_pricing_config()
    pricing = config.get_tier_pricing(tier, billing_cycle)
    
    # Track pricing page view (revenue tracking)
    track_pricing_page_view(tier.value, page_path="/pricing")
    
    # Store selection in session state
    st.session_state['selected_tier'] = tier.value
    st.session_state['selected_billing'] = billing_cycle.value
    st.session_state['selected_price'] = pricing['price']
    st.session_state['show_checkout'] = True
    
    # Trigger rerun to show checkout confirmation page
    st.rerun()

def show_checkout_form(tier: PricingTier, billing_cycle: BillingCycle, pricing: Dict[str, Any]):
    """Show checkout form for selected plan with Stripe integration"""
    import os
    import stripe
    
    st.markdown("### Secure Checkout")
    
    # Display order summary
    st.markdown(f"""
    **Order Summary:**
    - **Plan**: {pricing['name']}
    - **Price**: €{pricing['price']:,} per {billing_cycle.value}
    - **Billing**: {'Annual (save 2 months)' if billing_cycle == BillingCycle.ANNUAL else 'Monthly'}
    """)
    
    # Add 30-day money-back guarantee note
    st.info("30-day money-back guarantee included with all plans")
    
    with st.form("checkout_form"):
        st.markdown("**Contact Information**")
        
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name*", key="company_name")
            first_name = st.text_input("First Name*", key="first_name")
            email = st.text_input("Email Address*", key="email")
        
        with col2:
            country = st.selectbox("Country*", ["Netherlands", "Belgium", "Germany", "Other EU"], key="country")
            last_name = st.text_input("Last Name*", key="last_name")
            phone = st.text_input("Phone Number", key="phone")
        
        # Billing address
        st.markdown("**Billing Address**")
        address = st.text_input("Street Address*", key="address")
        col1, col2, col3 = st.columns(3)
        with col1:
            city = st.text_input("City*", key="city")
        with col2:
            postal_code = st.text_input("Postal Code*", key="postal")
        with col3:
            vat_number = st.text_input("VAT Number (optional)", key="vat")
        
        # Payment method info
        st.markdown("**Payment Methods Available:**")
        st.markdown("Credit Card, iDEAL (Netherlands), SEPA Direct Debit")
        
        # Terms
        terms_accepted = st.checkbox("I accept the Terms of Service and Privacy Policy*")
        
        submitted = st.form_submit_button("Continue to Payment", type="primary")
        
        if submitted:
            if not all([company_name, first_name, last_name, email, address, city, postal_code]) or not terms_accepted:
                st.error("Please fill in all required fields and accept the terms.")
            else:
                # Create Stripe checkout session
                try:
                    stripe_key = os.getenv('STRIPE_SECRET_KEY')
                    if not stripe_key:
                        st.error("Payment system not configured. Please contact support.")
                        return
                    
                    stripe.api_key = stripe_key
                    
                    # Get country code for VAT
                    country_codes = {"Netherlands": "NL", "Belgium": "BE", "Germany": "DE", "Other EU": "NL"}
                    country_code = country_codes.get(country, "NL")
                    
                    # Calculate price in cents
                    price_cents = int(pricing['price'] * 100)
                    
                    # Determine billing interval
                    if billing_cycle == BillingCycle.ANNUAL:
                        interval = "year"
                        interval_count = 1
                    else:
                        interval = "month"
                        interval_count = 1
                    
                    # Get base URL for redirects
                    base_url = os.getenv('REPLIT_DEV_DOMAIN')
                    if base_url:
                        base_url = f"https://{base_url}"
                    else:
                        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
                    
                    # Payment methods - include iDEAL for Netherlands
                    from typing import cast, List, Any
                    payment_methods: Any = ["card"]
                    if country_code == "NL":
                        payment_methods.extend(["ideal", "sepa_debit"])
                    
                    # Create checkout session for subscription
                    checkout_session = stripe.checkout.Session.create(
                        payment_method_types=payment_methods,
                        line_items=[{
                            "price_data": {
                                "currency": "eur",
                                "product_data": {
                                    "name": f"DataGuardian Pro - {pricing['name']}",
                                    "description": f"{tier.value.title()} plan with full GDPR compliance features",
                                },
                                "unit_amount": price_cents,
                                "recurring": {
                                    "interval": interval,
                                    "interval_count": interval_count,
                                }
                            },
                            "quantity": 1,
                        }],
                        mode="subscription",
                        success_url=f"{base_url}?payment_success=true&session_id={{CHECKOUT_SESSION_ID}}",
                        cancel_url=f"{base_url}?payment_cancelled=true",
                        customer_email=email,
                        metadata={
                            "tier": tier.value,
                            "billing_cycle": billing_cycle.value,
                            "company_name": company_name,
                            "first_name": first_name,
                            "last_name": last_name,
                            "country": country_code,
                            "vat_number": vat_number or "",
                        },
                        billing_address_collection="required",
                        tax_id_collection={"enabled": True},
                    )
                    
                    # Store session ID
                    st.session_state['stripe_session_id'] = checkout_session.id
                    
                    # Show redirect link
                    st.success("Checkout session created successfully!")
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px;">
                        <a href="{checkout_session.url}" target="_self" 
                           style="display: inline-block; padding: 15px 30px; 
                                  background: #635bff; color: white; text-decoration: none; 
                                  border-radius: 8px; font-weight: bold; font-size: 18px;">
                            Complete Payment Securely
                        </a>
                        <p style="font-size: 12px; color: #666; margin-top: 15px;">
                            Secured by Stripe | SSL Encrypted | GDPR Compliant
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Also use Streamlit's link button as backup
                    if checkout_session.url:
                        st.link_button("Click here if not redirected", checkout_session.url, type="primary")
                    
                except stripe.StripeError as e:
                    st.error(f"Payment service error. Please try again or contact support.")
                except Exception as e:
                    st.error(f"An error occurred. Please try again or contact support.")

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
    """Show pricing info in sidebar"""
    license_integration = LicenseIntegration()
    current_tier = license_integration.get_current_pricing_tier()
    
    if current_tier:
        config = get_pricing_config()
        tier_data = config.pricing_data["tiers"][current_tier.value]
        st.sidebar.markdown(f"**Current Plan**: {tier_data['name']}")
        
        if current_tier != PricingTier.ENTERPRISE:
            # Enterprise license detected - no upgrade needed
            pass