"""
Webhook Server for DataGuardian Pro
Standalone webhook endpoint server to handle Stripe webhooks
"""

import os
import sys
import json
import logging

# Add parent directory to path for imports (when run as module or standalone)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from flask import Flask, request, jsonify

try:
    from services.webhook_handler import process_stripe_webhook
except ImportError:
    from webhook_handler import process_stripe_webhook

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

@app.route('/webhook/stripe', methods=['POST'])
@app.route('/stripe', methods=['POST'])
def stripe_webhook():
    """
    Stripe webhook endpoint
    Handles all Stripe webhook events with proper security
    """
    try:
        # Get request data
        payload = request.get_data()
        signature = request.headers.get('stripe-signature')
        
        if not signature:
            logger.error("Missing Stripe signature header")
            return jsonify({'error': 'Missing signature'}), 400
        
        # Process webhook
        result = process_stripe_webhook(payload, signature)
        
        # Return response based on processing result
        if result['status'] == 'success':
            return jsonify({'received': True, 'message': result['message']}), 200
        elif result['status'] == 'ignored':
            return jsonify({'received': True, 'message': result['message']}), 200
        else:
            logger.error(f"Webhook processing failed: {result['message']}")
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        logger.error(f"Webhook endpoint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/webhook/health', methods=['GET'])
def health_check():
    """Health check endpoint for webhook server"""
    return jsonify({
        'status': 'healthy',
        'service': 'DataGuardian Pro Webhook Server',
        'version': '1.0.0'
    }), 200

@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """Test endpoint for webhook functionality"""
    if not app.debug:
        return jsonify({'error': 'Test endpoint only available in debug mode'}), 404
    
    test_event = {
        'id': 'evt_test_webhook',
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': 'cs_test_123456',
                'customer_email': 'test@example.com',
                'amount_total': 2783,
                'currency': 'eur',
                'metadata': {
                    'scan_type': 'Code Scan',
                    'country_code': 'NL'
                }
            }
        }
    }
    
    from services.webhook_handler import webhook_handler
    result = webhook_handler.process_webhook_event(test_event)
    return jsonify(result), 200

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('WEBHOOK_HOST', '0.0.0.0')
    port = int(os.getenv('WEBHOOK_PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting DataGuardian Pro Webhook Server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)