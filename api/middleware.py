"""
DataGuardian Pro API Middleware
Authentication, rate limiting, and request processing
"""

from flask import request, g
from functools import wraps
import logging
import time
import os
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 100


def rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window=RATE_LIMIT_WINDOW):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            rate_limit_store[client_ip] = [
                t for t in rate_limit_store[client_ip] 
                if current_time - t < window
            ]
            
            if len(rate_limit_store[client_ip]) >= max_requests:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return {'error': 'Rate limit exceeded. Try again later.'}, 429
            
            rate_limit_store[client_ip].append(current_time)
            return f(*args, **kwargs)
        return decorated
    return decorator


def validate_api_key(api_key):
    """Validate API key against stored keys"""
    try:
        valid_keys = os.environ.get('API_KEYS', '').split(',')
        return api_key in valid_keys if valid_keys else True
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return False


def require_auth(f):
    """Authentication middleware decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        api_key = request.headers.get('X-API-Key')
        
        if api_key:
            if not validate_api_key(api_key):
                return {'error': 'Invalid API key'}, 401
            g.auth_method = 'api_key'
            
        elif auth_header:
            if not auth_header.startswith('Bearer '):
                return {'error': 'Invalid authorization header'}, 401
            
            token = auth_header.split(' ')[1]
            try:
                import jwt as pyjwt
                secret = os.environ.get('JWT_SECRET', 'default-secret')
                payload = pyjwt.decode(token, secret, algorithms=['HS256'])
                g.user_id = payload.get('user_id')
                g.auth_method = 'jwt'
            except Exception as e:
                error_msg = str(e).lower()
                if 'expired' in error_msg:
                    return {'error': 'Token expired'}, 401
                return {'error': 'Invalid token'}, 401
        else:
            return {'error': 'Authentication required'}, 401
        
        return f(*args, **kwargs)
    return decorated


def log_request(f):
    """Request logging middleware"""
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        
        logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
        
        response = f(*args, **kwargs)
        
        duration = time.time() - start_time
        logger.info(f"Response: {request.path} completed in {duration:.3f}s")
        
        return response
    return decorated


def cors_headers(response):
    """Add CORS headers to response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
    return response


class APIError(Exception):
    """Custom API error class"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['timestamp'] = datetime.utcnow().isoformat()
        return rv


def init_middleware(app):
    """Initialize middleware on Flask app"""
    @app.before_request
    def before_request():
        g.request_start_time = time.time()
    
    @app.after_request
    def after_request(response):
        duration = time.time() - g.get('request_start_time', time.time())
        response.headers['X-Request-Duration'] = str(duration)
        return cors_headers(response)
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        return error.to_dict(), error.status_code
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500
