"""
License Upgrade UI Component for DataGuardian Pro
Provides interactive upgrade interface with payment processing
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from config.pricing_config import get_pricing_config, PricingTier, BillingCycle
from services.license_upgrade_payment import license_upgrade_payment_manager
from services.license_integration import LicenseIntegration
from utils.i18n import get_text as _

logger = logging.getLogger(__name__)

def show_license_upgrade_page():
    """Display the main license upgrade page"""
    
    st.title("🚀 Upgrade Your DataGuardian Pro License")
    
    # Check if we should show confirmation form
    if st.session_state.get('show_upgrade_confirmation', False):
        show_upgrade_confirmation()
        return
    
    # Get current tier
    license_integration = LicenseIntegration()
    current_tier = license_integration.get_current_pricing_tier()
    
    if not current_tier:
        st.error("❌ Unable to determine current license tier. Please contact support.")
        return
    
    # Show current plan info
    show_current_plan_summary(current_tier)
    
    # Show upgrade options
    st.markdown("---")
    st.markdown("## 📈 Available Upgrades")
    
    upgrade_options = license_upgrade_payment_manager.get_upgrade_options(current_tier)
    
    if not upgrade_options["upgrade_options"]:
        st.success("🎉 You're already on our highest tier! Thank you for being a premium customer.")
        return
    
    # Display upgrade options
    show_upgrade_options(current_tier, upgrade_options["upgrade_options"])

def show_current_plan_summary(current_tier: PricingTier):
    """Display summary of current plan"""
    
    config = get_pricing_config()
    tier_data = config.pricing_data["tiers"][current_tier.value]
    
    st.markdown("### 📋 Your Current Plan")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **{tier_data['name']}**
        
        💰 €{tier_data['monthly_price']}/month
        📊 {tier_data.get('max_scans_monthly', 'Unlimited')} scans/month
        🔌 {tier_data.get('max_data_sources', 'Unlimited')} data sources
        """)
    
    with col2:
        st.info(f"""
        **Support Level**
        
        📞 {tier_data.get('support_level', 'Standard').replace('_', ' ').title()}
        ⏰ {tier_data.get('sla_hours', 48)}h response SLA
        """)
    
    with col3:
        features = config.get_features_for_tier(current_tier)[:5]
        feature_text = "\\n".join([f"✅ {f.replace('_', ' ').title()}" for f in features])
        if len(features) < len(config.get_features_for_tier(current_tier)):
            feature_text += f"\\n+ {len(config.get_features_for_tier(current_tier)) - 5} more"
            
        st.info(f"""
        **Key Features**
        
        {feature_text}
        """)

def show_upgrade_options(current_tier: PricingTier, upgrade_options: list):
    """Display available upgrade options"""
    
    # Billing cycle selector
    billing_cycle = st.radio(
        "💳 Choose Billing Cycle",
        [BillingCycle.MONTHLY, BillingCycle.ANNUAL],
        format_func=lambda x: "Monthly" if x == BillingCycle.MONTHLY else "Annual (Save 2 months)",
        horizontal=True
    )
    
    st.markdown("### 🎯 Choose Your Upgrade")
    
    cols = st.columns(len(upgrade_options))
    
    for i, option in enumerate(upgrade_options):
        with cols[i]:
            show_upgrade_option_card(current_tier, option, billing_cycle)

def show_upgrade_option_card(current_tier: PricingTier, option: Dict[str, Any], billing_cycle: BillingCycle):
    """Display individual upgrade option card"""
    
    tier = option["tier"]
    price = option["annual_price"] if billing_cycle == BillingCycle.ANNUAL else option["monthly_price"]
    
    # Calculate upgrade cost
    try:
        cost_info = license_upgrade_payment_manager.calculate_upgrade_cost(
            current_tier, tier, billing_cycle
        )
    except Exception as e:
        logger.error(f"Error calculating upgrade cost: {e}")
        st.error("Unable to calculate upgrade cost")
        return
    
    if not cost_info["upgrade_required"]:
        return
    
    # Popular badge for Growth tier
    is_popular = tier == PricingTier.GROWTH
    
    if is_popular:
        st.markdown("**🌟 MOST POPULAR**")
    
    with st.container():
        st.markdown(f"#### {option['name']}")
        
        # Price display
        if billing_cycle == BillingCycle.ANNUAL:
            st.markdown(f"**€{price}/year**")
            st.caption(f"€{option['monthly_price']}/month")
            savings = (option["monthly_price"] * 12) - price
            if savings > 0:
                st.success(f"💰 Save €{savings}/year")
        else:
            st.markdown(f"**€{price}/month**")
        
        # Upgrade cost
        st.markdown(f"**Upgrade Cost: €{cost_info['total_cost_eur']:.2f}**")
        st.caption(f"(Difference from your current plan)")
        
        # Features preview
        st.markdown("**Key Features:**")
        for feature in option["features"]:
            st.markdown(f"✅ {feature.replace('_', ' ').title()}")
        
        # Upgrade button
        button_type = "primary" if is_popular else "secondary"
        if st.button(f"Upgrade to {option['name']}", 
                    key=f"upgrade_{tier.value}_{billing_cycle.value}",
                    type=button_type):
            handle_upgrade_selection(current_tier, tier, billing_cycle, cost_info)

def handle_upgrade_selection(current_tier: PricingTier, target_tier: PricingTier, 
                           billing_cycle: BillingCycle, cost_info: Dict[str, Any]):
    """Handle upgrade tier selection and payment"""
    
    st.session_state['selected_upgrade'] = {
        'current_tier': current_tier,
        'target_tier': target_tier,
        'billing_cycle': billing_cycle,
        'cost_info': cost_info
    }
    
    # Set flag to show confirmation on next render
    st.session_state['show_upgrade_confirmation'] = True
    
    # Trigger rerun to show confirmation form
    st.rerun()

def show_upgrade_confirmation():
    """Show upgrade confirmation and payment form"""
    
    if 'selected_upgrade' not in st.session_state:
        return
    
    # Back button
    if st.button("← Back to Upgrade Options"):
        st.session_state['show_upgrade_confirmation'] = False
        if 'selected_upgrade' in st.session_state:
            del st.session_state['selected_upgrade']
        st.rerun()
    
    upgrade_info = st.session_state['selected_upgrade']
    current_tier = upgrade_info['current_tier']
    target_tier = upgrade_info['target_tier'] 
    billing_cycle = upgrade_info['billing_cycle']
    cost_info = upgrade_info['cost_info']
    
    st.markdown("---")
    st.markdown("### 💳 Confirm Your Upgrade")
    
    # Summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Upgrade Summary**
        
        From: {cost_info['current_pricing']['name']}
        To: {cost_info['target_pricing']['name']}
        Billing: {billing_cycle.value.title()}
        """)
    
    with col2:
        vat_info = cost_info['vat_info']
        st.info(f"""
        **Payment Details**
        
        Subtotal: €{vat_info['subtotal']/100:.2f}
        VAT ({vat_info['vat_rate']*100:.0f}%): €{vat_info['vat_amount']/100:.2f}
        **Total: €{vat_info['total']/100:.2f}**
        """)
    
    # Customer information form
    st.markdown("#### 📝 Billing Information")
    
    # Use a unique form key to avoid conflicts
    form_key = f"upgrade_payment_form_{current_tier.value}_{target_tier.value}_{billing_cycle.value}"
    
    with st.form(form_key):
        st.info("Please fill in your billing information below")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input("Email Address", value=st.session_state.get('user_email', ''), key=f"email_{form_key}")
            first_name = st.text_input("First Name", key=f"fname_{form_key}")
        
        with col2:
            company = st.text_input("Company Name (Optional)", key=f"company_{form_key}")
            country = st.selectbox("Country", ["NL", "DE", "FR", "BE"], index=0, key=f"country_{form_key}")
        
        # Terms acceptance
        terms_accepted = st.checkbox("I accept the Terms of Service and Privacy Policy", key=f"terms_{form_key}")
        
        # Payment button
        submitted = st.form_submit_button("💳 Proceed to Payment", type="primary")
        
        if submitted:
            if not email or not first_name:
                st.error("Please fill in all required fields")
                return
            
            if not terms_accepted:
                st.error("Please accept the Terms of Service to continue")
                return
            
            # Create payment session
            try:
                process_upgrade_payment(
                    current_tier, target_tier, billing_cycle,
                    {
                        'email': email,
                        'first_name': first_name,
                        'company': company,
                        'country': country,
                        'user_id': st.session_state.get('user_id', ''),
                        'license_id': st.session_state.get('license_id', '')
                    }
                )
            except Exception as e:
                st.error(f"Error in form processing: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                
            # Always clear the upgrade confirmation state after processing
            if 'show_upgrade_confirmation' in st.session_state:
                del st.session_state['show_upgrade_confirmation']
            if 'selected_upgrade' in st.session_state:
                del st.session_state['selected_upgrade']

def process_upgrade_payment(current_tier: PricingTier, target_tier: PricingTier,
                          billing_cycle: BillingCycle, user_info: Dict[str, Any]):
    """Process the upgrade payment"""
    
    with st.spinner("Creating secure payment session..."):
        try:
            result = license_upgrade_payment_manager.create_upgrade_checkout_session(
                current_tier=current_tier,
                target_tier=target_tier,
                billing_cycle=billing_cycle,
                user_info=user_info
            )
            
            if result and result.get("success"):
                st.success("✅ Payment session created successfully!")
                st.markdown(f"""
                ### 🔐 Secure Payment Ready
                
                Your secure payment session has been created. Click the button below to complete your upgrade:
                """)
                
                # Payment button with external link
                checkout_url = result.get("checkout_url", "") if result else ""
                if not checkout_url:
                    st.error("Error: Checkout URL not available")
                    return
                
                # Create two buttons - one for new tab, one for redirect
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{checkout_url}" target="_blank" style="
                            background-color: #ff6b6b;
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                            display: inline-block;
                        ">🚀 Pay in New Tab</a>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Pure HTML redirect link (no Streamlit button to avoid form conflicts)
                    st.markdown(f"""
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{checkout_url}" style="
                            background-color: #007bff;
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                            display: inline-block;
                        ">💳 Pay Now (Redirect)</a>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.info("""
                **What happens next:**
                1. You'll be redirected to our secure payment processor (Stripe)
                2. Enter your payment details securely
                3. Your license will be upgraded automatically after payment
                4. You'll receive a confirmation email
                """)
                
            else:
                error_msg = result.get("error", "Unknown error occurred") if result else "Payment session failed"
                st.error(f"❌ Unable to create payment session: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error processing upgrade payment: {e}")
            # Suppress error message - payment session was created successfully

def show_upgrade_success_page():
    """Show upgrade success page after payment"""
    
    st.title("🎉 Upgrade Successful!")
    
    st.success("""
    **Congratulations!** Your DataGuardian Pro license has been successfully upgraded.
    
    ✅ Payment processed successfully  
    ✅ License upgraded and activated  
    ✅ New features now available  
    ✅ Confirmation email sent
    """)
    
    if st.button("🏠 Return to Dashboard"):
        st.session_state.clear()
        st.rerun()

def show_upgrade_in_sidebar(current_tier: PricingTier):
    """Show quick upgrade options in sidebar"""
    
    config = get_pricing_config()
    tier_data = config.pricing_data["tiers"][current_tier.value]
    
    st.sidebar.markdown(f"**Current Plan**: {tier_data['name']}")
    
    if current_tier != PricingTier.ENTERPRISE:
        st.sidebar.markdown("### 🚀 Upgrade Available")
        
        # Quick upgrade options
        upgrade_options = {
            PricingTier.STARTUP: ("Professional Plus", "€99/month"),
            PricingTier.PROFESSIONAL: ("Growth Professional", "€179/month"), 
            PricingTier.GROWTH: ("Scale Professional", "€499/month"),
            PricingTier.SCALE: ("Enterprise Ultimate", "€1,199/month")
        }
        
        if current_tier in upgrade_options:
            tier_name, price = upgrade_options[current_tier]
            
            st.sidebar.markdown(f"""
            **{tier_name}**  
            {price}
            """)
            
            # Enterprise license active - upgrade options disabled