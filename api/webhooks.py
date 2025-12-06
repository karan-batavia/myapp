"""
DataGuardian Pro Webhook Handlers
Handles incoming webhooks from external services (Stripe, enterprise connectors)
"""

from flask import Blueprint, jsonify, request
import logging
import hmac
import hashlib
import os
from datetime import datetime

logger = logging.getLogger(__name__)

webhook_blueprint = Blueprint('webhooks', __name__, url_prefix='/webhooks')


def verify_stripe_signature(payload, sig_header):
    """Verify Stripe webhook signature"""
    try:
        import stripe
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        if not endpoint_secret:
            logger.warning("Stripe webhook secret not configured")
            return True
        
        stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        return True
    except Exception as e:
        logger.error(f"Stripe signature verification failed: {e}")
        return False


@webhook_blueprint.route('/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe payment webhooks"""
    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature', '')
        
        if not verify_stripe_signature(payload, sig_header):
            return jsonify({'error': 'Invalid signature'}), 400
        
        event = request.get_json()
        event_type = event.get('type', '')
        
        logger.info(f"Stripe webhook received: {event_type}")
        
        if event_type == 'checkout.session.completed':
            _handle_checkout_completed(event)
        elif event_type == 'customer.subscription.updated':
            _handle_subscription_updated(event)
        elif event_type == 'customer.subscription.deleted':
            _handle_subscription_cancelled(event)
        elif event_type == 'invoice.payment_failed':
            _handle_payment_failed(event)
        elif event_type == 'invoice.paid':
            _handle_invoice_paid(event)
        
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}")
        return jsonify({'error': str(e)}), 500


def _handle_checkout_completed(event):
    """Handle successful checkout"""
    try:
        session = event.get('data', {}).get('object', {})
        customer_email = session.get('customer_email')
        subscription_id = session.get('subscription')
        
        logger.info(f"Checkout completed for {customer_email}, subscription: {subscription_id}")
        
    except Exception as e:
        logger.error(f"Error handling checkout: {e}")


def _handle_subscription_updated(event):
    """Handle subscription update"""
    try:
        subscription = event.get('data', {}).get('object', {})
        sub_id = subscription.get('id')
        status = subscription.get('status')
        
        logger.info(f"Subscription {sub_id} updated to status: {status}")
        
    except Exception as e:
        logger.error(f"Error handling subscription update: {e}")


def _handle_subscription_cancelled(event):
    """Handle subscription cancellation"""
    try:
        subscription = event.get('data', {}).get('object', {})
        sub_id = subscription.get('id')
        
        logger.info(f"Subscription {sub_id} cancelled")
        
    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {e}")


def _handle_payment_failed(event):
    """Handle failed payment"""
    try:
        invoice = event.get('data', {}).get('object', {})
        customer_email = invoice.get('customer_email')
        
        logger.warning(f"Payment failed for customer: {customer_email}")
        
    except Exception as e:
        logger.error(f"Error handling payment failure: {e}")


def _handle_invoice_paid(event):
    """Handle successful invoice payment"""
    try:
        invoice = event.get('data', {}).get('object', {})
        customer_email = invoice.get('customer_email')
        amount = invoice.get('amount_paid', 0)
        
        logger.info(f"Invoice paid by {customer_email}: {amount/100} EUR")
        
    except Exception as e:
        logger.error(f"Error handling invoice paid: {e}")


@webhook_blueprint.route('/microsoft365', methods=['POST'])
def microsoft365_webhook():
    """Handle Microsoft 365 webhooks for change notifications"""
    try:
        validation_token = request.args.get('validationToken')
        if validation_token:
            return validation_token, 200
        
        notifications = request.get_json()
        
        for notification in notifications.get('value', []):
            resource = notification.get('resource')
            change_type = notification.get('changeType')
            
            logger.info(f"Microsoft 365 notification: {change_type} on {resource}")
        
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        logger.error(f"Error processing Microsoft 365 webhook: {e}")
        return jsonify({'error': str(e)}), 500


@webhook_blueprint.route('/google', methods=['POST'])
def google_webhook():
    """Handle Google Workspace webhooks"""
    try:
        data = request.get_json()
        
        resource_state = request.headers.get('X-Goog-Resource-State')
        resource_id = request.headers.get('X-Goog-Resource-ID')
        
        logger.info(f"Google notification: state={resource_state}, resource={resource_id}")
        
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        logger.error(f"Error processing Google webhook: {e}")
        return jsonify({'error': str(e)}), 500


@webhook_blueprint.route('/exact', methods=['POST'])
def exact_online_webhook():
    """Handle Exact Online webhooks"""
    try:
        data = request.get_json()
        
        topic = data.get('Topic')
        action = data.get('Action')
        
        logger.info(f"Exact Online notification: {action} on {topic}")
        
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        logger.error(f"Error processing Exact Online webhook: {e}")
        return jsonify({'error': str(e)}), 500


@webhook_blueprint.route('/health', methods=['GET'])
def webhook_health():
    """Webhook endpoint health check"""
    return jsonify({
        'status': 'healthy',
        'endpoints': ['stripe', 'microsoft365', 'google', 'exact'],
        'timestamp': datetime.utcnow().isoformat()
    })
