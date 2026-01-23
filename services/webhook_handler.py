"""
Stripe Webhook Handler for DataGuardian Pro
Handles real-time payment confirmations and subscription events
"""

import os
import json
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import stripe

# Import new services - handle both standalone and integrated imports
try:
    from email_service import email_service
    from database_service import database_service
    from invoice_generator import invoice_generator
except ImportError:
    from services.email_service import email_service
    from services.database_service import database_service
    from services.invoice_generator import invoice_generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handle Stripe webhook events with security and reliability"""
    
    def __init__(self):
        self.stripe_api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if self.stripe_api_key:
            stripe.api_key = self.stripe_api_key
        
        if not self.webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not configured - webhook signature verification disabled")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Stripe webhook signature for security
        
        Args:
            payload: Raw request payload as bytes
            signature: Stripe signature header
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("Webhook signature verification skipped - no secret configured")
            return True
        
        try:
            stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return True
        except stripe.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return False
        except Exception as e:
            logger.error(f"Webhook verification error: {str(e)}")
            return False
    
    def process_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook event and return response
        
        Args:
            event: Stripe webhook event data
            
        Returns:
            Processing result dictionary
        """
        event_type = event.get('type', 'unknown')
        event_id = event.get('id', 'unknown')
        
        logger.info(f"Processing webhook event: {event_type} ({event_id})")
        
        try:
            # Route event to appropriate handler
            if event_type.startswith('checkout.session.'):
                return self._handle_checkout_event(event)
            elif event_type.startswith('payment_intent.'):
                return self._handle_payment_intent_event(event)
            elif event_type.startswith('invoice.'):
                return self._handle_invoice_event(event)
            elif event_type.startswith('customer.subscription.'):
                return self._handle_subscription_event(event)
            else:
                logger.info(f"Unhandled event type: {event_type}")
                return {'status': 'ignored', 'message': f'Event type {event_type} not handled'}
                
        except Exception as e:
            logger.error(f"Error processing webhook event {event_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_checkout_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle checkout session events"""
        event_type = event['type']
        session = event['data']['object']
        
        if event_type == 'checkout.session.completed':
            return self._handle_checkout_completed(session)
        elif event_type == 'checkout.session.expired':
            return self._handle_checkout_expired(session)
        
        return {'status': 'ignored', 'message': f'Checkout event {event_type} not handled'}
    
    def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful checkout completion"""
        session_id = session.get('id')
        customer_email = session.get('customer_email')
        amount_total = session.get('amount_total', 0)
        metadata = session.get('metadata', {})
        
        logger.info(f"Checkout completed: {session_id} for {customer_email}")
        logger.info(f"Checkout metadata: {metadata}")
        
        # Extract subscription plan details from metadata (for tier upgrades)
        user_id = metadata.get('user_id')
        plan_tier = metadata.get('plan_tier')
        
        # CRITICAL: Update user's license tier if this is a subscription checkout
        if plan_tier:
            logger.info(f"Subscription checkout detected - upgrading to tier: {plan_tier}")
            success = False
            
            # Try to update by user_id first
            if user_id:
                success = self._update_user_license_tier(user_id, plan_tier, session_id)
                if success:
                    logger.info(f"User {user_id} upgraded to {plan_tier} tier via checkout (by ID)")
                else:
                    logger.warning(f"Failed to upgrade user {user_id} by ID, trying by email...")
            
            # Fallback: try by email if user_id update failed or wasn't available
            if not success and customer_email:
                success = self._update_user_license_tier_by_email(customer_email, plan_tier, session_id)
                if success:
                    logger.info(f"User {customer_email} upgraded to {plan_tier} tier via checkout (by email)")
                else:
                    logger.error(f"Failed to upgrade user by email {customer_email} to {plan_tier}")
        
        # Extract scan details from metadata (for per-scan payments)
        scan_type = metadata.get('scan_type', 'Unknown')
        country_code = metadata.get('country_code', 'NL')
        
        # Log payment completion
        payment_record = {
            'session_id': session_id,
            'customer_email': customer_email,
            'amount': amount_total / 100,  # Convert from cents
            'currency': session.get('currency', 'eur'),
            'scan_type': scan_type,
            'country_code': country_code,
            'plan_tier': plan_tier,
            'user_id': user_id,
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat(),
            'payment_method': session.get('payment_method_types', ['unknown'])[0]
        }
        
        # Store payment record (in production, save to database)
        self._store_payment_record(payment_record)
        
        # Trigger scan processing (only if this is a scan payment, not subscription)
        if not plan_tier:
            self._trigger_scan_processing(payment_record)
        
        # Send confirmation email
        self._send_payment_confirmation(payment_record)
        
        return {
            'status': 'success',
            'message': f'Payment processed for {plan_tier or scan_type}',
            'payment_id': session_id
        }
    
    def _handle_checkout_expired(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle expired checkout sessions"""
        session_id = session.get('id')
        customer_email = session.get('customer_email')
        
        logger.info(f"Checkout expired: {session_id} for {customer_email}")
        
        # Log abandoned checkout for analytics
        abandoned_record = {
            'session_id': session_id,
            'customer_email': customer_email,
            'status': 'expired',
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': session.get('metadata', {})
        }
        
        self._store_abandoned_checkout(abandoned_record)
        
        return {
            'status': 'success',
            'message': 'Expired checkout logged',
            'session_id': session_id
        }
    
    def _handle_payment_intent_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment intent events"""
        event_type = event['type']
        payment_intent = event['data']['object']
        
        if event_type == 'payment_intent.succeeded':
            return self._handle_payment_succeeded(payment_intent)
        elif event_type == 'payment_intent.payment_failed':
            return self._handle_payment_failed(payment_intent)
        
        return {'status': 'ignored', 'message': f'Payment intent event {event_type} not handled'}
    
    def _handle_payment_succeeded(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment"""
        payment_id = payment_intent.get('id')
        amount = payment_intent.get('amount', 0)
        
        logger.info(f"Payment succeeded: {payment_id} for €{amount/100:.2f}")
        
        # Update payment status in database
        if payment_id:
            self._update_payment_status(payment_id, 'succeeded')
        
        return {
            'status': 'success',
            'message': 'Payment success recorded',
            'payment_id': payment_id
        }
    
    def _handle_payment_failed(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment"""
        payment_id = payment_intent.get('id')
        failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
        
        logger.warning(f"Payment failed: {payment_id} - {failure_reason}")
        
        # Update payment status and log failure
        if payment_id:
            self._update_payment_status(payment_id, 'failed', failure_reason)
        
        return {
            'status': 'success',
            'message': 'Payment failure recorded',
            'payment_id': payment_id
        }
    
    def _handle_invoice_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice events for subscriptions"""
        event_type = event['type']
        invoice = event['data']['object']
        
        if event_type == 'invoice.payment_succeeded':
            return self._handle_invoice_paid(invoice)
        elif event_type == 'invoice.payment_failed':
            return self._handle_invoice_failed(invoice)
        
        return {'status': 'ignored', 'message': f'Invoice event {event_type} not handled'}
    
    def _handle_invoice_paid(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful subscription payment"""
        invoice_id = invoice.get('id')
        customer_id = invoice.get('customer')
        amount_paid = invoice.get('amount_paid', 0)
        
        logger.info(f"Subscription payment succeeded: {invoice_id} for €{amount_paid/100:.2f}")
        
        # Update subscription status
        if customer_id:
            self._update_subscription_status(customer_id, 'active')
        
        return {
            'status': 'success',
            'message': 'Subscription payment recorded',
            'invoice_id': invoice_id
        }
    
    def _handle_invoice_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed subscription payment"""
        invoice_id = invoice.get('id')
        customer_id = invoice.get('customer')
        
        logger.warning(f"Subscription payment failed: {invoice_id}")
        
        # Handle failed payment (retry logic, notifications, etc.)
        if customer_id and invoice_id:
            self._handle_subscription_payment_failure(customer_id, invoice_id)
        
        return {
            'status': 'success',
            'message': 'Subscription payment failure handled',
            'invoice_id': invoice_id
        }
    
    def _handle_subscription_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription lifecycle events"""
        event_type = event['type']
        subscription = event['data']['object']
        
        if event_type == 'customer.subscription.created':
            return self._handle_subscription_created(subscription)
        elif event_type == 'customer.subscription.updated':
            return self._handle_subscription_updated(subscription)
        elif event_type == 'customer.subscription.deleted':
            return self._handle_subscription_cancelled(subscription)
        
        return {'status': 'ignored', 'message': f'Subscription event {event_type} not handled'}
    
    def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new subscription creation"""
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        metadata = subscription.get('metadata', {})
        
        logger.info(f"New subscription created: {subscription_id}")
        
        # Extract user_id and plan_tier from metadata
        user_id = metadata.get('user_id')
        plan_tier = metadata.get('plan_tier', 'professional')
        
        # Set up subscription in database
        self._create_subscription_record(subscription)
        
        # CRITICAL: Update the user's license_tier in platform_users
        success = False
        customer_email = subscription.get('customer_email')
        
        # Try to update by user_id first
        if user_id:
            success = self._update_user_license_tier(user_id, plan_tier, subscription_id)
            if success:
                logger.info(f"User {user_id} upgraded to {plan_tier} tier (by ID)")
            else:
                logger.warning(f"Failed to upgrade user {user_id} by ID, trying by email...")
        
        # Fallback: try by email if user_id update failed or wasn't available
        if not success and customer_email:
            success = self._update_user_license_tier_by_email(customer_email, plan_tier, subscription_id)
            if success:
                logger.info(f"User {customer_email} upgraded to {plan_tier} tier (by email)")
            else:
                logger.error(f"Failed to upgrade user by email {customer_email} to {plan_tier}")
        
        return {
            'status': 'success',
            'message': 'Subscription created and user upgraded',
            'subscription_id': subscription_id
        }
    
    def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates"""
        subscription_id = subscription.get('id')
        status = subscription.get('status')
        
        logger.info(f"Subscription updated: {subscription_id} status: {status}")
        
        # Update subscription in database
        self._update_subscription_record(subscription)
        
        return {
            'status': 'success',
            'message': 'Subscription updated',
            'subscription_id': subscription_id
        }
    
    def _handle_subscription_cancelled(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        metadata = subscription.get('metadata', {})
        
        logger.info(f"Subscription cancelled: {subscription_id}")
        
        # Update subscription status and handle cleanup
        if subscription_id:
            self._cancel_subscription_record(subscription_id)
        
        # Downgrade user to trial tier
        user_id = metadata.get('user_id')
        if user_id:
            self._update_user_license_tier(user_id, 'trial', None)
            logger.info(f"User {user_id} downgraded to trial tier after cancellation")
        
        return {
            'status': 'success',
            'message': 'Subscription cancelled',
            'subscription_id': subscription_id
        }
    
    def _update_user_license_tier(self, user_id: str, tier: str, subscription_id: Optional[str]) -> bool:
        """Update user's license tier in platform_users table"""
        try:
            return database_service.update_user_license_tier(user_id, tier, subscription_id)
        except Exception as e:
            logger.error(f"Error updating user license tier: {str(e)}")
            return False
    
    def _update_user_license_tier_by_email(self, email: str, tier: str, subscription_id: Optional[str]) -> bool:
        """Update user's license tier by email"""
        try:
            return database_service.update_user_license_tier_by_email(email, tier, subscription_id)
        except Exception as e:
            logger.error(f"Error updating user license tier by email: {str(e)}")
            return False
    
    # Helper methods for database operations (implement based on your database)
    def _store_payment_record(self, payment_record: Dict[str, Any]) -> None:
        """Store payment record in database"""
        success = database_service.store_payment_record(payment_record)
        if success:
            logger.info(f"Payment record stored successfully: {payment_record['session_id']}")
        else:
            logger.error(f"Failed to store payment record: {payment_record['session_id']}")
    
    def _store_abandoned_checkout(self, abandoned_record: Dict[str, Any]) -> None:
        """Store abandoned checkout for analytics"""
        success = database_service.track_analytics_event(
            event_type='checkout_abandoned',
            session_id=abandoned_record['session_id'],
            event_data=abandoned_record
        )
        if success:
            logger.info(f"Abandoned checkout tracked: {abandoned_record['session_id']}")
        else:
            logger.error(f"Failed to track abandoned checkout: {abandoned_record['session_id']}")
    
    def _trigger_scan_processing(self, payment_record: Dict[str, Any]) -> None:
        """Trigger automatic scan processing after payment"""
        # Track payment completion event
        database_service.track_analytics_event(
            event_type='payment_completed',
            session_id=payment_record['session_id'],
            event_data={
                'scan_type': payment_record['scan_type'],
                'amount': payment_record['amount'],
                'country_code': payment_record.get('country_code', 'NL'),
                'payment_method': payment_record.get('payment_method', 'unknown')
            }
        )
        
        # TODO: Implement actual scan queue processing
        logger.info(f"Scan processing triggered for: {payment_record['scan_type']}")
        logger.info(f"Customer: {payment_record['customer_email']}")
        logger.info(f"Amount: €{payment_record['amount']:.2f}")
    
    def _send_payment_confirmation(self, payment_record: Dict[str, Any]) -> None:
        """Send payment confirmation email with invoice"""
        try:
            # Generate invoice PDF
            invoice_pdf = invoice_generator.generate_payment_invoice(payment_record)
            
            # Store invoice record in database
            invoice_data = {
                'invoice_number': f"DGP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                'customer_email': payment_record['customer_email'],
                'amount_subtotal': payment_record['amount'] / 1.21,  # Assuming 21% VAT
                'amount_tax': payment_record['amount'] - (payment_record['amount'] / 1.21),
                'amount_total': payment_record['amount'],
                'currency': payment_record.get('currency', 'EUR'),
                'description': f"DataGuardian Pro - {payment_record['scan_type']}",
                'country_code': payment_record.get('country_code', 'NL'),
                'metadata': payment_record
            }
            database_service.store_invoice_record(invoice_data)
            
            # Send email with invoice
            success = email_service.send_payment_confirmation(payment_record, invoice_pdf)
            if success:
                logger.info(f"Payment confirmation sent to: {payment_record['customer_email']}")
            else:
                logger.error(f"Failed to send payment confirmation to: {payment_record['customer_email']}")
                
        except Exception as e:
            logger.error(f"Error sending payment confirmation: {str(e)}")
    
    def _update_payment_status(self, payment_id: str, status: str, error_message: Optional[str] = None) -> None:
        """Update payment status in database"""
        success = database_service.update_payment_status(payment_id, status, error_message)
        if success:
            logger.info(f"Payment {payment_id} status updated to: {status}")
        else:
            logger.error(f"Failed to update payment {payment_id} status")
    
    def _update_subscription_status(self, customer_id: str, status: str) -> None:
        """Update subscription status"""
        try:
            # Find subscription by customer ID
            subscription_data = database_service.get_subscription_by_customer_id(customer_id)
            if subscription_data:
                # Update the subscription status
                subscription_update = {
                    'status': status,
                    'updated_at': datetime.now(),
                    'metadata': subscription_data.get('metadata', {})
                }
                success = database_service.update_subscription_record(subscription_data['subscription_id'], subscription_update)
                if success:
                    logger.info(f"Subscription status updated for customer {customer_id}: {status}")
                else:
                    logger.error(f"Failed to update subscription status for customer {customer_id}")
            else:
                logger.warning(f"No subscription found for customer {customer_id}")
        except Exception as e:
            logger.error(f"Error updating subscription status for customer {customer_id}: {str(e)}")
    
    def _handle_subscription_payment_failure(self, customer_id: str, invoice_id: str) -> None:
        """Handle subscription payment failure"""
        try:
            # Track the payment failure event
            database_service.track_analytics_event(
                event_type='subscription_payment_failed',
                user_id=customer_id,
                event_data={
                    'invoice_id': invoice_id,
                    'failure_reason': 'payment_declined',
                    'retry_count': 1
                }
            )
            
            # Update subscription status to indicate payment issues
            self._update_subscription_status(customer_id, 'payment_failed')
            
            # Send notification email about payment failure
            subscription_data = database_service.get_subscription_by_customer_id(customer_id)
            if subscription_data:
                email_service.send_payment_failure_notification({
                    'customer_email': subscription_data['customer_email'],
                    'subscription_id': subscription_data['subscription_id'],
                    'invoice_id': invoice_id,
                    'plan_name': subscription_data['plan_name']
                })
            
            logger.warning(f"Subscription payment failure handled for customer {customer_id}, invoice {invoice_id}")
            
        except Exception as e:
            logger.error(f"Error handling subscription payment failure for customer {customer_id}: {str(e)}")
    
    def _create_subscription_record(self, subscription: Dict[str, Any]) -> None:
        """Create subscription record in database"""
        success = database_service.store_subscription_record(subscription)
        if success:
            logger.info(f"Subscription record created: {subscription.get('id')}")
            
            # Send subscription confirmation email
            try:
                subscription_data = {
                    'customer_email': subscription.get('customer_email', ''),
                    'plan_name': subscription.get('plan_name', ''),
                    'amount': subscription.get('amount', 0) / 100,
                    'subscription_id': subscription.get('id', ''),
                    'interval': subscription.get('interval', 'month')
                }
                email_service.send_subscription_confirmation(subscription_data)
            except Exception as e:
                logger.error(f"Failed to send subscription confirmation: {str(e)}")
        else:
            logger.error(f"Failed to create subscription record: {subscription.get('id')}")
    
    def _update_subscription_record(self, subscription: Dict[str, Any]) -> None:
        """Update subscription record in database"""
        success = database_service.store_subscription_record(subscription)  # Uses UPSERT
        if success:
            logger.info(f"Subscription record updated: {subscription.get('id')}")
        else:
            logger.error(f"Failed to update subscription record: {subscription.get('id')}")
    
    def _cancel_subscription_record(self, subscription_id: str) -> None:
        """Cancel subscription record"""
        try:
            # Update subscription status to cancelled
            subscription_update = {
                'status': 'cancelled',
                'updated_at': datetime.now(),
                'metadata': {'cancellation_date': datetime.now().isoformat()}
            }
            success = database_service.update_subscription_record(subscription_id, subscription_update)
            
            if success:
                logger.info(f"Subscription cancelled successfully: {subscription_id}")
                
                # Track cancellation event
                database_service.track_analytics_event(
                    event_type='subscription_cancelled',
                    session_id=subscription_id,
                    event_data={
                        'subscription_id': subscription_id,
                        'cancellation_reason': 'customer_request'
                    }
                )
            else:
                logger.error(f"Failed to cancel subscription: {subscription_id}")
                
        except Exception as e:
            logger.error(f"Error cancelling subscription {subscription_id}: {str(e)}")

# Global webhook handler instance
webhook_handler = WebhookHandler()

def process_stripe_webhook(payload: bytes, signature: str) -> Dict[str, Any]:
    """
    Process incoming Stripe webhook
    
    Args:
        payload: Raw request payload as bytes
        signature: Stripe signature header
        
    Returns:
        Processing result dictionary
    """
    # Verify signature
    if not webhook_handler.verify_webhook_signature(payload, signature):
        return {'status': 'error', 'message': 'Invalid signature'}
    
    try:
        # Parse event data
        event = json.loads(payload.decode('utf-8'))
        
        # Process event
        return webhook_handler.process_webhook_event(event)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return {'status': 'error', 'message': 'Invalid JSON payload'}
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return {'status': 'error', 'message': 'Internal processing error'}