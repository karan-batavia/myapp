"""
License Expiry Manager Component
Handles license expiry reminders and renewal prompts for DataGuardian Pro
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from services.payment_enhancements import check_license_expiry_and_remind, SubscriptionStatus

def show_license_expiry_banner():
    """
    Display license expiry banner if needed
    Shows 14-day warning before expiry
    """
    try:
        # Get subscription ID from license or session
        subscription_id = st.session_state.get('subscription_id', None)
        if not subscription_id:
            return
        
        # Check expiry status
        expiry_info = check_license_expiry_and_remind(subscription_id, days_before_expiry=14)
        
        if expiry_info.get('status') == 'error':
            return
        
        days_remaining = expiry_info.get('days_remaining', -1)
        
        # Show appropriate banner based on days remaining
        if days_remaining <= 0:
            st.error(f"⚠️ **Your license has expired!** Please renew to continue using DataGuardian Pro.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Renew Now", type="primary", key="renew_expired"):
                    st.session_state['show_renewal_page'] = True
                    st.rerun()
            with col2:
                if st.button("📥 Download Data", key="download_expired"):
                    st.session_state['show_export_data'] = True
                    st.rerun()
        
        elif 1 <= days_remaining <= 7:
            st.error(f"🔴 **Your license expires in {days_remaining} day{'s' if days_remaining != 1 else ''}!** Renew now to avoid interruption.")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Renew License", type="primary", key="renew_critical"):
                    st.session_state['show_renewal_page'] = True
                    st.rerun()
            with col2:
                if st.button("📞 Contact Sales", key="contact_sales_critical"):
                    st.session_state['show_contact_form'] = True
                    st.rerun()
        
        elif 7 < days_remaining <= 14:
            st.warning(f"🟡 **Your license expires in {days_remaining} days.** Consider renewing soon to maintain uninterrupted service.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Renew License", key="renew_soon"):
                    st.session_state['show_renewal_page'] = True
                    st.rerun()
            with col2:
                if st.button("ℹ️ Learn About Renewal", key="learn_renewal"):
                    st.session_state['show_renewal_info'] = True
                    st.rerun()
    
    except Exception as e:
        # Silently fail - don't disrupt user experience
        pass

def show_renewal_options():
    """Display renewal options for expiring license"""
    
    st.markdown("## 🔄 Renew Your License")
    
    st.markdown("""
    Keep your DataGuardian Pro subscription active and uninterrupted.
    """)
    
    # Renewal options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 Renew Current Plan")
        st.markdown("""
        Continue with your current tier at the current price.
        
        **Benefits:**
        - Seamless continuation
        - No service interruption
        - All data preserved
        - Same tier and features
        """)
        
        if st.button("Continue with Current Plan", type="primary", key="renew_current"):
            st.session_state['show_payment'] = True
            st.rerun()
    
    with col2:
        st.markdown("### ⬆️ Upgrade Plan")
        st.markdown("""
        Upgrade to a higher tier for more features.
        
        **Benefits:**
        - More scans/month
        - Additional scanners
        - Priority support
        - Advanced features
        """)
        
        if st.button("Explore Upgrade Options", key="upgrade_plan"):
            st.session_state['show_pricing'] = True
            st.rerun()

def show_license_status_dashboard():
    """Show current license status with renewal information"""
    
    try:
        subscription_id = st.session_state.get('subscription_id', None)
        if not subscription_id:
            return
        
        expiry_info = check_license_expiry_and_remind(subscription_id)
        
        if expiry_info.get('status') == 'error':
            st.warning("Could not load license status")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            days_remaining = expiry_info.get('days_remaining', 0)
            if days_remaining > 0:
                st.metric("Days Remaining", days_remaining, delta="Active")
            elif days_remaining == 0:
                st.metric("Days Remaining", "Today", delta="Expires today!", delta_color="inverse")
            else:
                st.metric("Days Remaining", "Expired", delta="Action needed", delta_color="inverse")
        
        with col2:
            expiry_date = expiry_info.get('expiry_date', 'Unknown')
            st.metric("Expires", expiry_date.split('T')[0] if isinstance(expiry_date, str) else expiry_date)
        
        with col3:
            status = expiry_info.get('status_enum', SubscriptionStatus.ACTIVE)
            status_color = "🟢" if status == SubscriptionStatus.ACTIVE else "🟡" if status == SubscriptionStatus.EXPIRING else "🔴"
            st.metric("Status", f"{status_color} {status.value.title()}")
    
    except Exception as e:
        # Silently fail
        pass

def show_auto_renewal_info():
    """Show information about auto-renewal"""
    
    with st.expander("ℹ️ About Auto-Renewal", expanded=False):
        st.markdown("""
        ### Auto-Renewal Information
        
        **How it works:**
        - Your subscription automatically renews on the renewal date
        - We charge your saved payment method on file
        - You'll receive an invoice via email 3 days before renewal
        - Access continues uninterrupted after renewal
        
        **Payment methods:**
        - Credit card (Visa, Mastercard, American Express)
        - SEPA Direct Debit (European customers)
        - iDEAL (Netherlands customers)
        
        **Managing your subscription:**
        - Change billing frequency anytime in Settings
        - Update payment method in Billing settings
        - View upcoming invoice before renewal
        - Cancel anytime - even after renewal
        
        **30-Day Money-Back Guarantee:**
        - New customers: Full refund within 30 days
        - No questions asked
        - Request in Settings → Billing → Request Refund
        """)

def send_expiry_reminder_email(customer_email: str, days_remaining: int, 
                               customer_name: str = "Valued Customer") -> bool:
    """
    Send license expiry reminder email (placeholder for email service)
    
    Args:
        customer_email: Customer email address
        days_remaining: Days until license expires
        customer_name: Customer name for personalization
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # This is a placeholder - integrate with your email service (SendGrid, Mailgun, etc.)
        # For now, log the action
        import logging
        email_logger = logging.getLogger(__name__)
        email_logger.info(f"Expiry reminder email triggered for {customer_email} - {days_remaining} days remaining")
        
        # In production, call your email service:
        # from services.email_service import send_email
        # send_email(
        #     to=customer_email,
        #     subject=f"Your DataGuardian Pro license expires in {days_remaining} days",
        #     template="license_expiry_reminder",
        #     data={
        #         "customer_name": customer_name,
        #         "days_remaining": days_remaining,
        #         "renewal_url": "https://dataguardianpro.nl/renew"
        #     }
        # )
        
        return True
    
    except Exception as e:
        email_logger = logging.getLogger(__name__)
        email_logger.error(f"Error sending expiry reminder email: {str(e)}")
        return False
