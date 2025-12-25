"""
DataGuardian Pro API Middleware
Authentication, rate limiting, and request processing
Uses Redis-backed distributed rate limiting for multi-instance deployments.
"""

from flask import request, g, jsonify
from functools import wraps
import logging
import time
import os
from datetime import datetime

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 100

try:
    from utils.redis_rate_limiter import get_rate_limiter, get_tiered_rate_limiter
    REDIS_RATE_LIMITER_AVAILABLE = True
except ImportError:
    logger.warning("Redis rate limiter not available, using local fallback")
    REDIS_RATE_LIMITER_AVAILABLE = False
    from collections import defaultdict
    _local_rate_store = defaultdict(list)


def rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window=RATE_LIMIT_WINDOW):
    """Rate limiting decorator using Redis for distributed limiting."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            client_ip = request.remote_addr or 'unknown'
            
            if REDIS_RATE_LIMITER_AVAILABLE:
                limiter = get_rate_limiter(max_requests, window)
                allowed, info = limiter.is_allowed(client_ip)
                
                if not allowed:
                    logger.warning(f"Rate limit exceeded for {client_ip}")
                    response = jsonify({
                        'error': 'Rate limit exceeded. Try again later.',
                        'retry_after': info.get('reset', 60) - int(time.time())
                    })
                    response.status_code = 429
                    response.headers['X-RateLimit-Limit'] = str(info['limit'])
                    response.headers['X-RateLimit-Remaining'] = '0'
                    response.headers['X-RateLimit-Reset'] = str(info['reset'])
                    return response
                
                g.rate_limit_info = info
            else:
                current_time = time.time()
                _local_rate_store[client_ip] = [
                    t for t in _local_rate_store[client_ip] 
                    if current_time - t < window
                ]
                
                if len(_local_rate_store[client_ip]) >= max_requests:
                    logger.warning(f"Rate limit exceeded for {client_ip}")
                    return {'error': 'Rate limit exceeded. Try again later.'}, 429
                
                _local_rate_store[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def tiered_rate_limit(key_func=None):
    """Rate limiting based on user tier (uses Redis)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            client_ip = request.remote_addr or 'unknown'
            user_tier = getattr(g, 'user_tier', 'trial')
            
            if key_func:
                identifier = key_func(request)
            else:
                identifier = client_ip
            
            if REDIS_RATE_LIMITER_AVAILABLE:
                limiter = get_tiered_rate_limiter()
                allowed, info = limiter.is_allowed(identifier, user_tier)
                
                if not allowed:
                    logger.warning(f"Tiered rate limit exceeded for {identifier} (tier: {user_tier})")
                    response = jsonify({
                        'error': 'Rate limit exceeded. Upgrade your plan for higher limits.',
                        'retry_after': info.get('reset', 60) - int(time.time()),
                        'current_tier': user_tier
                    })
                    response.status_code = 429
                    return response
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def validate_api_key(api_key):
    """Validate API key against stored keys - requires explicit configuration"""
    try:
        api_keys_env = os.environ.get('API_KEYS', '')
        if not api_keys_env or api_keys_env.strip() == '':
            # SECURITY: Reject all API keys if none are configured
            logger.warning("API_KEYS not configured - rejecting API key authentication")
            return False
        valid_keys = [k.strip() for k in api_keys_env.split(',') if k.strip()]
        if not valid_keys:
            logger.warning("API_KEYS is empty - rejecting API key authentication")
            return False
        return api_key in valid_keys
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
                secret = os.environ.get('JWT_SECRET', '')
                # SECURITY: Require explicit JWT_SECRET configuration
                if not secret or secret.strip() == '' or secret == 'default-secret':
                    logger.error("JWT_SECRET not configured or using insecure default")
                    return {'error': 'Server configuration error'}, 500
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
