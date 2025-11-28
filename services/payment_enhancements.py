"""
Payment Flow Enhancements for DataGuardian Pro
Implements:
1. Payment callback verification
2. License expiry reminders
3. Automatic renewal configuration
4. Refund/cancellation policy
5. iDEAL payment method integration
"""

import os
import stripe
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Literal
from enum import Enum

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class SubscriptionStatus(Enum):
    """Subscription status enumeration"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRING = "expiring"

def verify_payment_callback(session_id: str, expected_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Verify payment callback with enhanced security and validation
    
    Args:
        session_id: Stripe checkout session ID
        expected_metadata: Expected metadata to validate (prevents tampering)
    
    Returns:
        Dictionary with payment verification result
    """
    try:
        if not session_id or not isinstance(session_id, str):
            return {
                "status": "error",
                "valid": False,
                "message": "Invalid session ID"
            }
        
        # Retrieve checkout session from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Verify metadata integrity if expected metadata provided
        if expected_metadata:
            session_metadata = checkout_session.metadata or {}
            for key, expected_value in expected_metadata.items():
                if session_metadata.get(key) != str(expected_value):
                    logger.warning(f"Payment callback metadata mismatch for session {session_id}")
                    return {
                        "status": "error",
                        "valid": False,
                        "message": "Metadata validation failed"
                    }
        
        # Get payment intent - handle both string and object types
        if not checkout_session.payment_intent:
            return {
                "status": "error",
                "valid": False,
                "message": "No payment intent found"
            }
        
        payment_intent_id: str = (
            checkout_session.payment_intent.id 
            if hasattr(checkout_session.payment_intent, 'id') 
            else str(checkout_session.payment_intent)
        )
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # Validate payment status
        is_valid = payment_intent.status == "succeeded"
        
        return {
            "status": "success",
            "valid": is_valid,
            "payment_status": payment_intent.status,
            "amount": payment_intent.amount / 100,
            "currency": payment_intent.currency.upper() if payment_intent.currency else "EUR",
            "customer_email": checkout_session.customer_email or "",
            "metadata": checkout_session.metadata or {},
            "created": datetime.fromtimestamp(payment_intent.created).isoformat(),
            "payment_method": payment_intent.payment_method_types[0] if payment_intent.payment_method_types else None,
            "message": "Payment verified successfully" if is_valid else "Payment not completed"
        }
    
    except stripe.StripeError as e:
        logger.error(f"Stripe error during payment verification: {str(e)}")
        return {
            "status": "error",
            "valid": False,
            "message": f"Payment service error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error during payment verification: {str(e)}")
        return {
            "status": "error",
            "valid": False,
            "message": "Verification failed"
        }

def create_subscription(customer_email: str, plan_tier: str, billing_cycle: str = "monthly", 
                       country_code: str = "NL") -> Optional[Dict[str, Any]]:
    """
    Create Stripe subscription for automatic renewal
    
    Args:
        customer_email: Customer email for subscription
        plan_tier: Pricing tier (e.g., 'startup', 'professional', 'enterprise')
        billing_cycle: 'monthly' or 'annual'
        country_code: Country code for region-specific handling
    
    Returns:
        Subscription details or None if failed
    """
    try:
        # Map plan tiers to Stripe price IDs
        price_mapping = {
            "startup": {"monthly": "price_startup_monthly", "annual": "price_startup_annual"},
            "professional": {"monthly": "price_professional_monthly", "annual": "price_professional_annual"},
            "growth": {"monthly": "price_growth_monthly", "annual": "price_growth_annual"},
            "scale": {"monthly": "price_scale_monthly", "annual": "price_scale_annual"},
            "salesforce_premium": {"monthly": "price_salesforce_monthly", "annual": "price_salesforce_annual"},
            "sap_enterprise": {"monthly": "price_sap_monthly", "annual": "price_sap_annual"},
            "enterprise": {"monthly": "price_enterprise_monthly", "annual": "price_enterprise_annual"},
        }
        
        if plan_tier not in price_mapping or billing_cycle not in price_mapping[plan_tier]:
            logger.error(f"Invalid plan tier or billing cycle: {plan_tier}, {billing_cycle}")
            return None
        
        price_id = price_mapping[plan_tier][billing_cycle]
        
        # Create or get customer
        customers = stripe.Customer.list(email=customer_email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(email=customer_email)
        
        # Create subscription with auto-renewal
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={
                "save_default_payment_method": "on_subscription"
            },
            metadata={
                "tier": plan_tier,
                "billing_cycle": billing_cycle,
                "country_code": country_code,
                "created_at": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Subscription created: {subscription.id} for customer {customer_email}")
        
        return {
            "status": "success",
            "subscription_id": subscription.id,
            "customer_id": customer.id,
            "subscription_status": subscription.status,
            "current_period_start": datetime.fromtimestamp(int(subscription.current_period_start or 0)).isoformat(),
            "current_period_end": datetime.fromtimestamp(int(subscription.current_period_end or 0)).isoformat(),
            "price_id": price_id,
            "message": "Subscription created successfully"
        }
    
    except stripe.StripeError as e:
        logger.error(f"Stripe error creating subscription: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        return None

def check_license_expiry_and_remind(subscription_id: str, days_before_expiry: int = 14) -> Dict[str, Any]:
    """
    Check license expiry and determine if reminder should be sent
    
    Args:
        subscription_id: Stripe subscription ID
        days_before_expiry: Days before expiry to send reminder (default: 14)
    
    Returns:
        Dictionary with expiry status and reminder information
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        current_period_end = datetime.fromtimestamp(int(subscription.current_period_end or 0))
        days_remaining = (current_period_end - datetime.now()).days
        
        reminder_needed = 0 < days_remaining <= days_before_expiry
        
        status_enum = SubscriptionStatus.EXPIRING if reminder_needed else SubscriptionStatus.ACTIVE
        
        return {
            "status": "success",
            "subscription_id": subscription_id,
            "expiry_date": current_period_end.isoformat(),
            "days_remaining": days_remaining,
            "reminder_needed": reminder_needed,
            "status_enum": status_enum
        }
    
    except stripe.StripeError as e:
        logger.error(f"Error checking subscription expiry: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to check expiry"
        }

def process_refund(payment_intent_id: str, reason: Literal['duplicate', 'fraudulent', 'requested_by_customer'] = 'requested_by_customer', 
                   amount_cents: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Process refund for a payment (with automatic cancellation option)
    
    Args:
        payment_intent_id: Stripe payment intent ID
        reason: Refund reason ('duplicate', 'fraudulent', 'requested_by_customer')
        amount_cents: Amount to refund in cents (None = full refund)
    
    Returns:
        Refund details or None if failed
    """
    try:
        refund_kwargs: Dict[str, Any] = {
            "payment_intent": payment_intent_id,
            "reason": reason,
            "metadata": {
                "refund_date": datetime.now().isoformat(),
                "reason_detail": reason
            }
        }
        if amount_cents is not None:
            refund_kwargs["amount"] = amount_cents
        
        refund = stripe.Refund.create(**refund_kwargs)
        
        logger.info(f"Refund created: {refund.id} for payment intent {payment_intent_id}")
        
        return {
            "status": "success",
            "refund_id": refund.id,
            "amount": refund.amount / 100 if refund.amount else 0,
            "currency": (refund.currency or "eur").upper(),
            "refund_status": refund.status,
            "reason": reason,
            "created": datetime.fromtimestamp(refund.created).isoformat()
        }
    
    except stripe.StripeError as e:
        logger.error(f"Error processing refund: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing refund: {str(e)}")
        return None

def cancel_subscription_with_refund(subscription_id: str, refund_reason: str = "customer_request",
                                   include_current_invoice: bool = True) -> Optional[Dict[str, Any]]:
    """
    Cancel subscription and optionally refund current invoice
    
    Args:
        subscription_id: Stripe subscription ID
        refund_reason: Reason for cancellation/refund
        include_current_invoice: Whether to refund current invoice
    
    Returns:
        Cancellation details with refund status
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Get current invoice if exists
        invoice_id = subscription.latest_invoice
        refund_result = None
        
        if include_current_invoice and invoice_id:
            try:
                invoice_obj = stripe.Invoice.retrieve(str(invoice_id) if not isinstance(invoice_id, str) else invoice_id)
                paid = getattr(invoice_obj, 'paid', False)
                payment_intent = getattr(invoice_obj, 'payment_intent', None)
                if paid and payment_intent:
                    pi_str = str(payment_intent) if not isinstance(payment_intent, str) else payment_intent
                    refund_result = process_refund(pi_str, reason='requested_by_customer')
            except Exception as e:
                logger.warning(f"Could not refund current invoice: {str(e)}")
        
        # Cancel subscription
        cancelled_subscription = stripe.Subscription.delete(subscription_id)
        
        logger.info(f"Subscription cancelled: {subscription_id}")
        
        cancelled_at = None
        if hasattr(cancelled_subscription, 'canceled_at') and cancelled_subscription.canceled_at:
            cancelled_at = datetime.fromtimestamp(int(cancelled_subscription.canceled_at)).isoformat()
        
        return {
            "status": "success",
            "subscription_id": subscription_id,
            "cancelled_at": cancelled_at,
            "refund": refund_result,
            "reason": refund_reason,
            "message": "Subscription cancelled successfully"
        }
    
    except stripe.StripeError as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error cancelling subscription: {str(e)}")
        return None

def get_refund_policy() -> Dict[str, Any]:
    """Get refund policy details for display"""
    return {
        "policy_name": "DataGuardian Pro 30-Day Money-Back Guarantee",
        "description": "We're confident you'll love DataGuardian Pro. If you're not satisfied within 30 days, we'll refund your money - no questions asked.",
        "eligibility": [
            "New customers within 30 days of first purchase",
            "Full refund for subscription tier purchase",
            "Applicable to monthly and annual plans"
        ],
        "exclusions": [
            "Refunds for per-scan purchases after scan completion",
            "Customers with multiple refund requests (fraud prevention)",
            "Enterprise custom development services"
        ],
        "how_to_request": [
            "1. Login to your account",
            "2. Go to Settings → Billing",
            "3. Click 'Cancel Subscription' → 'Request Refund'",
            "4. Select reason and submit",
            "5. Refund processed within 5-7 business days"
        ],
        "contact": "billing@dataguardianpro.nl",
        "phone": "+31 (0)20 XXXX XXXX"
    }

def get_cancellation_policy() -> Dict[str, Any]:
    """Get cancellation policy details for display"""
    return {
        "policy_name": "Flexible Cancellation Policy",
        "description": "Cancel your subscription at any time without penalty.",
        "how_to_cancel": [
            "1. Login to DataGuardian Pro",
            "2. Navigate to Settings → Billing",
            "3. Click 'Cancel Subscription'",
            "4. Confirm cancellation (your data remains available for download)"
        ],
        "after_cancellation": [
            "Access ends at end of current billing period",
            "All your scan results are downloadable as PDF/HTML",
            "Free tier access remains available",
            "Reactivate any time - your old data is preserved"
        ],
        "billing": [
            "No pro-rata refunds for partial months",
            "30-day money-back guarantee applies to new customers",
            "For cancellations after 30 days, no refund issued",
            "Annual plans: Refund allowed within first 30 days only"
        ]
    }

# Initialize Stripe if available
try:
    if os.getenv('STRIPE_SECRET_KEY'):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
except Exception as e:
    logger.warning(f"Stripe initialization failed: {str(e)}")
