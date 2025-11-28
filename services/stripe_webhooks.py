"""
Stripe Webhook Handler for DataGuardian Pro Subscription Billing
Handles automated billing events for SaaS model (70% of €25K MRR target)
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import Stripe with fallback
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logging.warning("Stripe library not available")

logger = logging.getLogger(__name__)

class StripeWebhookHandler:
    """
    Handle Stripe webhook events for subscription billing automation
    """
    
    def __init__(self):
        """Initialize Stripe webhook handler with API keys"""
        self.stripe_secret_key = os.environ.get('STRIPE_SECRET_KEY')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if STRIPE_AVAILABLE and self.stripe_secret_key:
            stripe.api_key = self.stripe_secret_key
        else:
            logger.warning("STRIPE_SECRET_KEY not found in environment or Stripe not available")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature for security
        
        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
            
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_secret or not STRIPE_AVAILABLE:
            logger.warning("STRIPE_WEBHOOK_SECRET not configured or Stripe not available")
            return False
            
        try:
            stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
        except ValueError:
            logger.error("Invalid payload in webhook")
            return False
        except Exception:  # Handle Stripe signature verification error
            logger.error("Invalid signature in webhook")
            return False
    
    def handle_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Stripe webhook event
        
        Args:
            event_data: Webhook event data from Stripe
            
        Returns:
            Dict with processing result
        """
        event_type = event_data.get('type')
        
        try:
            if event_type == 'customer.subscription.created':
                return self._handle_subscription_created(event_data)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_cancelled(event_data)
            elif event_type == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_payment_failed(event_data)
            elif event_type == 'customer.created':
                return self._handle_customer_created(event_data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {'status': 'ignored', 'event_type': event_type}
                
        except Exception as e:
            logger.error(f"Error processing webhook event {event_type}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_subscription_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new subscription creation"""
        subscription = event_data['data']['object']
        customer_id = subscription['customer']
        subscription_id = subscription['id']
        
        logger.info(f"New subscription created: {subscription_id} for customer: {customer_id}")
        
        # Update user permissions and license access
        try:
            # Use existing license manager or create fallback
            try:
                from services.license_manager import LicenseManager
                license_manager = LicenseManager()
                
                # Grant subscription access
                license_manager.activate_subscription(
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    plan_name=self._get_plan_name(subscription),
                    tier=self._get_subscription_tier(subscription)
                )
            except ImportError:
                # Fallback license management (to be implemented)
                logger.warning("License manager not available, using fallback")
                # Continue without license manager for now
                pass
            
            # Log activity
            self._log_subscription_activity(
                customer_id, 'subscription_created', {
                    'subscription_id': subscription_id,
                    'plan': self._get_plan_name(subscription)
                }
            )
            
            return {
                'status': 'success',
                'action': 'subscription_created',
                'subscription_id': subscription_id
            }
            
        except Exception as e:
            logger.error(f"Failed to activate subscription {subscription_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_subscription_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates (plan changes, etc.)"""
        subscription = event_data['data']['object']
        customer_id = subscription['customer']
        subscription_id = subscription['id']
        
        logger.info(f"Subscription updated: {subscription_id}")
        
        try:
            from services.license_manager import LicenseManager
            license_manager = LicenseManager()
            
            # Update subscription access
            license_manager.update_subscription(
                customer_id=customer_id,
                subscription_id=subscription_id,
                new_tier=self._get_subscription_tier(subscription),
                new_plan=self._get_plan_name(subscription)
            )
            
            self._log_subscription_activity(
                customer_id, 'subscription_updated', {
                    'subscription_id': subscription_id,
                    'new_plan': self._get_plan_name(subscription)
                }
            )
            
            return {
                'status': 'success',
                'action': 'subscription_updated',
                'subscription_id': subscription_id
            }
        except ImportError:
            logger.warning("License manager not available")
            self._log_subscription_activity(
                customer_id, 'subscription_updated', {
                    'subscription_id': subscription_id,
                    'new_plan': self._get_plan_name(subscription)
                }
            )
            return {
                'status': 'success',
                'action': 'subscription_updated',
                'subscription_id': subscription_id
            }
        except Exception as e:
            logger.error(f"Failed to update subscription {subscription_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_subscription_cancelled(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        subscription = event_data['data']['object']
        customer_id = subscription['customer']
        subscription_id = subscription['id']
        
        logger.info(f"Subscription cancelled: {subscription_id}")
        
        try:
            from services.license_manager import LicenseManager
            license_manager = LicenseManager()
            
            # Deactivate subscription access
            license_manager.deactivate_subscription(
                customer_id=customer_id,
                subscription_id=subscription_id
            )
            
            self._log_subscription_activity(
                customer_id, 'subscription_cancelled', {
                    'subscription_id': subscription_id
                }
            )
            
            return {
                'status': 'success',
                'action': 'subscription_cancelled',
                'subscription_id': subscription_id
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_payment_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment"""
        invoice = event_data['data']['object']
        customer_id = invoice['customer']
        subscription_id = invoice.get('subscription')
        
        logger.info(f"Payment succeeded for customer: {customer_id}")
        
        try:
            # Extend subscription period and reset usage limits
            from services.license_manager import LicenseManager
            license_manager = LicenseManager()
            
            if subscription_id:
                license_manager.reset_monthly_usage(subscription_id)
                
            self._log_subscription_activity(
                customer_id, 'payment_succeeded', {
                    'invoice_id': invoice['id'],
                    'amount': invoice['amount_paid'],
                    'subscription_id': subscription_id
                }
            )
            
            return {
                'status': 'success',
                'action': 'payment_succeeded',
                'customer_id': customer_id
            }
            
        except Exception as e:
            logger.error(f"Failed to process payment for customer {customer_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment"""
        invoice = event_data['data']['object']
        customer_id = invoice['customer']
        subscription_id = invoice.get('subscription')
        
        logger.warning(f"Payment failed for customer: {customer_id}")
        
        try:
            # Implement dunning management
            from services.license_manager import LicenseManager
            license_manager = LicenseManager()
            
            if subscription_id:
                # Mark subscription as past due
                license_manager.mark_subscription_past_due(subscription_id)
                
            self._log_subscription_activity(
                customer_id, 'payment_failed', {
                    'invoice_id': invoice['id'],
                    'subscription_id': subscription_id,
                    'attempt_count': invoice.get('attempt_count', 1)
                }
            )
            
            return {
                'status': 'success',
                'action': 'payment_failed',
                'customer_id': customer_id
            }
            
        except Exception as e:
            logger.error(f"Failed to handle payment failure for customer {customer_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_customer_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new customer creation"""
        customer = event_data['data']['object']
        customer_id = customer['id']
        
        logger.info(f"New customer created: {customer_id}")
        
        try:
            # Initialize customer in license system
            from services.license_manager import LicenseManager
            license_manager = LicenseManager()
            
            license_manager.create_customer_record(
                customer_id=customer_id,
                email=customer.get('email'),
                name=customer.get('name')
            )
            
            self._log_subscription_activity(
                customer_id, 'customer_created', {
                    'email': customer.get('email'),
                    'name': customer.get('name')
                }
            )
            
            return {
                'status': 'success',
                'action': 'customer_created',
                'customer_id': customer_id
            }
            
        except Exception as e:
            logger.error(f"Failed to create customer record {customer_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_plan_name(self, subscription: Dict[str, Any]) -> str:
        """Extract plan name from subscription"""
        try:
            if subscription.get('items', {}).get('data'):
                price_id = subscription['items']['data'][0]['price']['id']
                
                # Map price IDs to plan names (Netherlands market)
                plan_mapping = {
                    'price_starter_nl': 'Starter',
                    'price_professional_nl': 'Professional', 
                    'price_enterprise_nl': 'Enterprise',
                    'price_compliance_plus_nl': 'Compliance Plus'
                }
                
                return plan_mapping.get(price_id, 'Unknown')
            
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    def _get_subscription_tier(self, subscription: Dict[str, Any]) -> str:
        """Determine subscription tier for access control"""
        plan_name = self._get_plan_name(subscription)
        
        tier_mapping = {
            'Starter': 'basic',
            'Professional': 'professional',
            'Enterprise': 'enterprise',
            'Compliance Plus': 'premium'
        }
        
        return tier_mapping.get(plan_name, 'basic')
    
    def _log_subscription_activity(self, customer_id: str, action: str, details: Dict[str, Any]):
        """Log subscription activity for audit trail"""
        try:
            from utils.activity_tracker import ActivityTracker, ActivityType
            
            tracker = ActivityTracker()
            tracker.track_activity(
                session_id=f"webhook_{datetime.now().timestamp()}",
                user_id=customer_id,
                username=customer_id,
                activity_type=ActivityType.SETTINGS_CHANGED,  # Use closest available type
                details={
                    'webhook_action': action,
                    'timestamp': datetime.now().isoformat(),
                    **details
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to log subscription activity: {str(e)}")

# Webhook endpoint handler function for web frameworks
def handle_stripe_webhook(payload: bytes, signature: str) -> Dict[str, Any]:
    """
    Main webhook handler function for web framework integration
    
    Args:
        payload: Raw webhook payload from Stripe
        signature: Stripe signature header
        
    Returns:
        Dict with processing result
    """
    handler = StripeWebhookHandler()
    
    # Verify signature
    if not handler.verify_webhook_signature(payload, signature):
        return {'status': 'error', 'message': 'Invalid signature'}
    
    # Parse event data
    try:
        event_data = json.loads(payload.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {'status': 'error', 'message': f'Invalid payload: {str(e)}'}
    
    # Process webhook event
    return handler.handle_webhook_event(event_data)