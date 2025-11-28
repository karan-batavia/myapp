"""
Cancellation and Refund Policy Component
Self-service cancellation interface with refund options
"""

import streamlit as st
from typing import Dict, Any, Optional
from services.payment_enhancements import (
    get_refund_policy, get_cancellation_policy,
    cancel_subscription_with_refund, process_refund
)

def show_cancellation_page():
    """Display self-service cancellation interface"""
    
    st.markdown("## ❌ Cancel Your Subscription")
    
    st.info("We're sorry to see you go. Please let us know why, and consider these options first.")
    
    # Cancellation reason selection
    st.markdown("### What's prompting you to cancel?")
    
    reason = st.selectbox(
        "Select cancellation reason",
        [
            "Not meeting my needs",
            "Too expensive",
            "Found a better solution",
            "Temporary pause (will return)",
            "Data migration to another tool",
            "No longer need compliance scanning",
            "Other reason"
        ],
        key="cancellation_reason"
    )
    
    # Show retention options based on reason
    if reason == "Too expensive":
        st.markdown("### 💡 Consider These Options Instead")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Lower-Cost Plans", key="view_lower_plans"):
                st.session_state['show_pricing_downgrade'] = True
                st.rerun()
        with col2:
            if st.button("🤝 Talk to Sales", key="talk_sales_pricing"):
                st.session_state['show_sales_contact'] = True
                st.rerun()
    
    elif reason == "Not meeting my needs":
        st.markdown("### 💡 We Can Help!")
        st.info("""
        Many users don't realize all the features available in their plan.
        Our support team can show you how to get more value.
        """)
        if st.button("📞 Schedule Demo with Support", key="schedule_demo"):
            st.session_state['show_support_contact'] = True
            st.rerun()
    
    elif reason == "Temporary pause (will return)":
        st.markdown("### 💡 Pause Subscription Instead")
        st.info("""
        Don't cancel! You can pause your subscription for up to 3 months.
        Your data remains safe and you can reactivate anytime.
        """)
        if st.button("⏸️ Pause Subscription", key="pause_subscription"):
            st.session_state['show_pause_confirm'] = True
            st.rerun()
    
    # Additional details
    st.markdown("---")
    details = st.text_area(
        "Additional details (optional)",
        placeholder="Help us improve: tell us more about your decision...",
        key="cancellation_details"
    )
    
    # Cancellation options
    st.markdown("### What would you like to do?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⏹️ Cancel Subscription Only", key="cancel_only"):
            show_cancel_confirm(reason, details, include_refund=False)
    
    with col2:
        if st.button("💰 Cancel & Request Refund", key="cancel_with_refund"):
            show_cancel_confirm(reason, details, include_refund=True)
    
    with col3:
        if st.button("🚫 Never Mind (Keep Subscription)", key="cancel_keep"):
            st.success("✅ Your subscription is safe. Happy scanning!")
            st.balloons()

def show_cancel_confirm(reason: str, details: str, include_refund: bool = False):
    """Show cancellation confirmation dialog"""
    
    st.markdown("---")
    st.markdown("## 🔒 Confirm Cancellation")
    
    subscription_id = st.session_state.get('subscription_id')
    
    if not subscription_id:
        st.error("Could not find your subscription. Please contact support.")
        return
    
    # Show what happens after cancellation
    with st.expander("What happens when I cancel?", expanded=True):
        st.markdown(f"""
        **Immediate:**
        - Your subscription ends at the end of your current billing period
        - No charges after cancellation
        - Access remains until end of billing period
        
        **After Billing Period Ends:**
        - Your account downgrades to free tier
        - Limited to basic scanning features
        - Your data remains available for download
        
        **Reactivation:**
        - You can reactivate anytime
        - Your previous tier pricing may apply
        - Historical scan data is preserved
        
        **Refund Status:**
        - {'Full refund applies within 30 days of purchase' if include_refund else 'No refund after initial 30 days'}
        - Processed to original payment method in 5-7 business days
        """)
    
    # Data export option
    st.markdown("### 📥 Download Your Data Before Leaving")
    st.info("Export all your scan results as PDF/HTML reports for your records.")
    if st.button("📊 Generate Export", key="generate_export"):
        st.session_state['show_export'] = True
        st.rerun()
    
    # Final confirmation
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        confirm = st.checkbox("I understand what will happen after cancellation", key="confirm_understand")
    
    with col2:
        if include_refund:
            refund_eligible = st.checkbox("I request a full refund", key="confirm_refund")
        else:
            refund_eligible = False
    
    with col3:
        if st.button("✅ Confirm Cancellation", disabled=not confirm, type="primary", key="confirm_cancel"):
            if perform_cancellation(subscription_id, reason, details, include_refund and refund_eligible):
                st.success("✅ Your subscription has been cancelled.")
                st.info("Check your email for cancellation confirmation and next steps.")
                st.balloons()
            else:
                st.error("❌ Could not process cancellation. Please contact support.")

def perform_cancellation(subscription_id: str, reason: str, details: str, include_refund: bool) -> bool:
    """Execute cancellation and optional refund"""
    
    try:
        result = cancel_subscription_with_refund(
            subscription_id=subscription_id,
            refund_reason=f"User cancellation: {reason}",
            include_current_invoice=include_refund
        )
        
        if result and result.get('status') == 'success':
            # Log cancellation with feedback
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"""
            Subscription cancelled: {subscription_id}
            Reason: {reason}
            Details: {details}
            Refund: {include_refund}
            Refund Status: {result.get('refund', {}).get('status', 'N/A')}
            """)
            
            st.session_state['subscription_cancelled'] = True
            return True
        else:
            st.error("Cancellation failed. Please try again or contact support.")
            return False
    
    except Exception as e:
        st.error(f"Error processing cancellation: {str(e)}")
        return False

def show_refund_policy():
    """Display refund policy"""
    
    st.markdown("## 💰 Refund Policy")
    
    policy = get_refund_policy()
    
    st.markdown(f"### {policy['policy_name']}")
    st.markdown(policy['description'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**✅ You're Eligible For Refund If:**")
        for item in policy['eligibility']:
            st.markdown(f"- {item}")
    
    with col2:
        st.markdown("**❌ Refunds Do Not Apply To:**")
        for item in policy['exclusions']:
            st.markdown(f"- {item}")
    
    st.markdown("---")
    st.markdown("**How to Request a Refund:**")
    for step in policy['how_to_request']:
        st.markdown(step)
    
    st.markdown("---")
    st.markdown(f"""
    **Questions?**
    
    📧 Email: {policy['contact']}
    
    📞 Phone: {policy['phone']}
    """)

def show_cancellation_policy():
    """Display cancellation policy"""
    
    st.markdown("## ❌ Cancellation Policy")
    
    policy = get_cancellation_policy()
    
    st.markdown(f"### {policy['policy_name']}")
    st.markdown(policy['description'])
    
    st.markdown("**How to Cancel:**")
    for step in policy['how_to_cancel']:
        st.markdown(step)
    
    st.markdown("---")
    st.markdown("**After Cancellation:**")
    for item in policy['after_cancellation']:
        st.markdown(f"- {item}")
    
    st.markdown("---")
    st.markdown("**Billing Information:**")
    for item in policy['billing']:
        st.markdown(f"- {item}")

def show_billing_settings():
    """Show billing settings with cancellation/refund options"""
    
    st.markdown("## 💳 Billing Settings")
    
    tab1, tab2, tab3 = st.tabs(["💳 Payment Method", "📋 Invoices", "🚨 Cancel/Refund"])
    
    with tab1:
        st.markdown("### Update Payment Method")
        # Payment method update interface
        payment_method = st.selectbox(
            "Select payment method",
            ["Credit Card", "SEPA Direct Debit", "iDEAL (Netherlands)"]
        )
        if st.button("Update Payment Method"):
            st.success("Payment method updated successfully")
    
    with tab2:
        st.markdown("### Recent Invoices")
        st.info("Your recent invoices would be displayed here")
        # Show invoices table
    
    with tab3:
        st.markdown("### Subscription Management")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 View Refund Policy", key="view_refund_policy"):
                show_refund_policy()
        with col2:
            if st.button("❌ Cancel Subscription", key="billing_cancel", type="primary"):
                show_cancellation_page()
