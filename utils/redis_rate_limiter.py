"""
DataGuardian Pro Distributed Rate Limiter
Redis-backed rate limiting for multi-instance deployments.
Uses sliding window algorithm for accurate rate limiting.
"""

import logging
import os
import time
from typing import Tuple, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    """
    Distributed rate limiter using Redis.
    Uses sliding window log algorithm for accurate limiting across instances.
    """
    
    RATE_LIMIT_PREFIX = "dataguardian:ratelimit"
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        redis_client=None
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis_client = redis_client
        self._local_store = {}
        self._connect_redis()
    
    def _connect_redis(self):
        """Connect to Redis if not provided."""
        if self.redis_client:
            return
            
        try:
            import redis
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            self.redis_client.ping()
            logger.info("Rate limiter connected to Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable for rate limiter, using local fallback: {e}")
            self.redis_client = None
    
    def is_allowed(self, identifier: str) -> Tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (IP, user_id, API key, etc.)
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        if self.redis_client:
            return self._redis_check(identifier)
        else:
            return self._local_check(identifier)
    
    def _redis_check(self, identifier: str) -> Tuple[bool, dict]:
        """Check rate limit using Redis sliding window."""
        key = f"{self.RATE_LIMIT_PREFIX}:{identifier}"
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        try:
            pipe = self.redis_client.pipeline()
            
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds + 1)
            
            results = pipe.execute()
            request_count = results[2]
            
            remaining = max(0, self.max_requests - request_count)
            reset_at = int(current_time) + self.window_seconds
            
            info = {
                'limit': self.max_requests,
                'remaining': remaining,
                'reset': reset_at,
                'window': self.window_seconds
            }
            
            if request_count > self.max_requests:
                self.redis_client.zrem(key, str(current_time))
                return False, info
            
            return True, info
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return self._local_check(identifier)
    
    def _local_check(self, identifier: str) -> Tuple[bool, dict]:
        """Fallback local rate limit check."""
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        if identifier not in self._local_store:
            self._local_store[identifier] = []
        
        self._local_store[identifier] = [
            t for t in self._local_store[identifier]
            if t > window_start
        ]
        
        request_count = len(self._local_store[identifier])
        remaining = max(0, self.max_requests - request_count - 1)
        reset_at = int(current_time) + self.window_seconds
        
        info = {
            'limit': self.max_requests,
            'remaining': remaining,
            'reset': reset_at,
            'window': self.window_seconds,
            'mode': 'local_fallback'
        }
        
        if request_count >= self.max_requests:
            return False, info
        
        self._local_store[identifier].append(current_time)
        return True, info
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        _, info = self.is_allowed(identifier)
        return info.get('remaining', 0)
    
    def reset(self, identifier: str):
        """Reset rate limit for identifier."""
        key = f"{self.RATE_LIMIT_PREFIX}:{identifier}"
        
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis reset failed: {e}")
        
        if identifier in self._local_store:
            del self._local_store[identifier]
    
    def cleanup(self):
        """Clean up expired local entries."""
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        for identifier in list(self._local_store.keys()):
            self._local_store[identifier] = [
                t for t in self._local_store[identifier]
                if t > window_start
            ]
            if not self._local_store[identifier]:
                del self._local_store[identifier]


_default_limiter = None

def get_rate_limiter(max_requests: int = 100, window_seconds: int = 60) -> RedisRateLimiter:
    """Get rate limiter instance."""
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RedisRateLimiter(max_requests, window_seconds)
    return _default_limiter


def rate_limit(max_requests: int = 100, window_seconds: int = 60, key_func=None):
    """
    Rate limiting decorator for Flask/API routes.
    
    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
        key_func: Function to extract identifier from request (default: IP)
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import request, jsonify
            
            if key_func:
                identifier = key_func(request)
            else:
                identifier = request.remote_addr or 'unknown'
            
            limiter = get_rate_limiter(max_requests, window_seconds)
            allowed, info = limiter.is_allowed(identifier)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {identifier}")
                response = jsonify({
                    'error': 'Rate limit exceeded. Try again later.',
                    'retry_after': info.get('reset', 60) - int(time.time())
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
                return response
            
            response = f(*args, **kwargs)
            
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
            
            return response
        return decorated
    return decorator


class TieredRateLimiter:
    """
    Rate limiter with different limits based on user tier.
    """
    
    TIER_LIMITS = {
        'trial': (20, 60),
        'startup': (50, 60),
        'professional': (100, 60),
        'growth': (200, 60),
        'scale': (500, 60),
        'enterprise': (1000, 60),
    }
    
    def __init__(self):
        self._limiters = {}
    
    def get_limiter_for_tier(self, tier: str) -> RedisRateLimiter:
        """Get rate limiter configured for specific tier."""
        tier_lower = tier.lower()
        if tier_lower not in self._limiters:
            max_req, window = self.TIER_LIMITS.get(tier_lower, (50, 60))
            self._limiters[tier_lower] = RedisRateLimiter(max_req, window)
        return self._limiters[tier_lower]
    
    def is_allowed(self, identifier: str, tier: str = 'trial') -> Tuple[bool, dict]:
        """Check if request is allowed for given tier."""
        limiter = self.get_limiter_for_tier(tier)
        return limiter.is_allowed(identifier)


_tiered_limiter = None

def get_tiered_rate_limiter() -> TieredRateLimiter:
    """Get singleton tiered rate limiter."""
    global _tiered_limiter
    if _tiered_limiter is None:
        _tiered_limiter = TieredRateLimiter()
    return _tiered_limiter
