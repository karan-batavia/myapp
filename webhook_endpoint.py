"""
Standalone Webhook Endpoint for Stripe
Runs on port 5002 and handles Stripe webhooks for iDEAL and other async payments
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/webhook/stripe', methods=['POST'])
@app.route('/stripe', methods=['POST'])
@app.route('/', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        from services.webhook_handler import process_stripe_webhook
        
        payload = request.get_data()
        signature = request.headers.get('stripe-signature', '')
        
        logger.info(f"Received webhook, signature present: {bool(signature)}")
        
        if not signature:
            logger.warning("No Stripe signature - processing anyway for testing")
        
        result = process_stripe_webhook(payload, signature)
        
        logger.info(f"Webhook result: {result}")
        
        if result.get('status') == 'success':
            return jsonify({'received': True, 'message': result.get('message', 'OK')}), 200
        elif result.get('status') == 'ignored':
            return jsonify({'received': True, 'message': result.get('message', 'Ignored')}), 200
        else:
            return jsonify({'error': result.get('message', 'Failed')}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
@app.route('/', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'DataGuardian Pro Stripe Webhook',
        'endpoints': ['/webhook/stripe', '/stripe', '/']
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 5002))
    logger.info(f"Starting Stripe Webhook Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
