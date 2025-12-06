"""
Pricing Page Module
Displays pricing plans and upgrade options
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)


def render_pricing_page():
    """Render pricing page with all available plans"""
    st.title("💰 Pricing & Plans")
    
    st.markdown("""
    ### Choose the Right Plan for Your Organization
    All plans include GDPR compliance, Netherlands UAVG support, and EU AI Act 2025 readiness.
    """)
    
    plans = [
        {
            "name": "Trial",
            "price": "Free",
            "period": "14 days",
            "scans": "10 scans",
            "features": ["Basic PII detection", "Code & document scanning", "Standard reports", "Email support"],
            "highlight": False
        },
        {
            "name": "Startup",
            "price": "€59",
            "period": "/month",
            "scans": "200 scans/month",
            "features": ["All Trial features", "5 concurrent users", "API access", "Priority support"],
            "highlight": False
        },
        {
            "name": "Professional",
            "price": "€99",
            "period": "/month",
            "scans": "350 scans/month",
            "features": ["All Startup features", "AI-powered analysis", "Database scanning", "Custom reports", "Fraud detection"],
            "highlight": True
        },
        {
            "name": "Growth",
            "price": "€179",
            "period": "/month",
            "scans": "750 scans/month",
            "features": ["All Professional features", "Website scanning", "Enterprise connectors", "Dedicated support"],
            "highlight": False
        },
        {
            "name": "Scale",
            "price": "€499",
            "period": "/month",
            "scans": "Unlimited scans",
            "features": ["All Growth features", "White-label reports", "SLA guarantee", "Custom integrations"],
            "highlight": False
        },
        {
            "name": "Enterprise",
            "price": "€1,199",
            "period": "/month",
            "scans": "Unlimited + Priority",
            "features": ["All Scale features", "Dedicated instance", "Custom training", "24/7 support", "On-premise option"],
            "highlight": False
        }
    ]
    
    cols = st.columns(3)
    
    for i, plan in enumerate(plans):
        with cols[i % 3]:
            if plan["highlight"]:
                st.markdown(f"""
                <div style="border: 2px solid #2d5a4d; border-radius: 10px; padding: 20px; background: #f0fff4;">
                    <h3 style="color: #2d5a4d;">⭐ {plan['name']}</h3>
                    <h2>{plan['price']}<small>{plan['period']}</small></h2>
                    <p><strong>{plan['scans']}</strong></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
                    <h3>{plan['name']}</h3>
                    <h2>{plan['price']}<small>{plan['period']}</small></h2>
                    <p><strong>{plan['scans']}</strong></p>
                </div>
                """, unsafe_allow_html=True)
            
            for feature in plan["features"]:
                st.write(f"✓ {feature}")
            
            if st.button(f"Select {plan['name']}", key=f"select_{plan['name']}", use_container_width=True):
                st.session_state['selected_plan'] = plan['name']
                st.session_state['show_upgrade'] = True
                st.rerun()
            
            st.markdown("---")
    
    st.markdown("""
    ### Government Pricing
    **€15,000** one-time license for government organizations. Contact us for details.
    
    ### Need a Custom Solution?
    Contact our sales team for enterprise agreements, volume discounts, or custom requirements.
    
    📧 **sales@dataguardianpro.nl** | 📞 **+31 (0)20 123 4567**
    """)


def render_upgrade_page():
    """Render upgrade page for license upgrades"""
    st.title("🚀 Upgrade Your License")
    
    try:
        from components.license_upgrade import render_upgrade_interface
        render_upgrade_interface()
    except ImportError:
        _render_fallback_upgrade()


def _render_fallback_upgrade():
    """Fallback upgrade interface if component not available"""
    st.markdown("""
    ### Upgrade to Unlock More Features
    
    Choose your new plan below and complete the payment process.
    """)
    
    current_plan = st.session_state.get('license_type', 'Trial')
    st.info(f"**Current Plan:** {current_plan}")
    
    upgrade_options = ["Startup (€59/mo)", "Professional (€99/mo)", "Growth (€179/mo)", "Scale (€499/mo)", "Enterprise (€1,199/mo)"]
    
    selected_upgrade = st.selectbox("Select New Plan", upgrade_options)
    
    st.markdown("---")
    
    st.subheader("Payment Method")
    
    payment_method = st.radio("Choose payment method:", ["iDEAL (Netherlands)", "Credit Card", "SEPA Direct Debit"])
    
    if payment_method == "iDEAL (Netherlands)":
        bank = st.selectbox("Select your bank:", ["ING", "Rabobank", "ABN AMRO", "SNS Bank", "ASN Bank", "RegioBank", "Triodos Bank"])
        st.info(f"You will be redirected to {bank} to complete the payment.")
    
    elif payment_method == "Credit Card":
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Card Number", placeholder="1234 5678 9012 3456")
            st.text_input("Name on Card", placeholder="J. de Vries")
        with col2:
            st.text_input("Expiry Date", placeholder="MM/YY")
            st.text_input("CVV", placeholder="123", type="password")
    
    else:
        st.text_input("IBAN", placeholder="NL00 BANK 0123 4567 89")
        st.text_input("Account Holder Name", placeholder="J. de Vries")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        agree_terms = st.checkbox("I agree to the Terms of Service")
    with col2:
        agree_privacy = st.checkbox("I agree to the Privacy Policy")
    
    if st.button("🔐 Complete Upgrade", type="primary", use_container_width=True):
        if agree_terms and agree_privacy:
            with st.spinner("Processing payment..."):
                import time
                time.sleep(2)
            st.success("🎉 Upgrade successful! Your new plan is now active.")
            st.balloons()
        else:
            st.error("Please agree to the Terms of Service and Privacy Policy.")
    
    st.markdown("---")
    st.caption("🔒 Payments processed securely via Stripe. Your data is protected.")
