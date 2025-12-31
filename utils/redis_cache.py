"""
Redis Caching Layer for DataGuardian Pro
Provides high-performance caching for scan results and user sessions
"""

import redis
import json
import logging
import time
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import os
import base64
from decimal import Decimal

logger = logging.getLogger(__name__)

class RedisCacheError(Exception):
    """Raised when Redis is required but unavailable."""
    pass


class RedisCache:
    """High-performance Redis cache manager with optional strict mode."""
    
    def __init__(self, strict_mode: bool = None):
        """
        Initialize Redis cache.
        
        Args:
            strict_mode: If True, raise error if Redis unavailable.
                        If None, auto-detect from environment.
        """
        self.redis_client = None
        self._fallback_cache = {}
        self._fallback_expiry = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        self.ttl_config = {
            'scan_results': 7200,
            'compliance_scores': 3600,
            'user_sessions': 1800,
            'dashboard_data': 300,
            'large_datasets': 14400,
            'default': 3600
        }
        self.default_ttl = self.ttl_config['default']
        
        if strict_mode is None:
            env = os.getenv('ENVIRONMENT', 'development').lower()
            self.strict_mode = env in ('production', 'prod', 'staging')
        else:
            self.strict_mode = strict_mode
        
        self.connect()
    
    def connect(self):
        """Connect to Redis server with retry logic and graceful fallback"""
        redis_urls = [
            os.getenv('REDIS_URL', ''),
            'redis://localhost:6379/0',
            'redis://127.0.0.1:6379/0',
            'redis://redis:6379/0'  # Docker container name
        ]
        
        # Filter out empty URLs
        redis_urls = [url for url in redis_urls if url]
        
        for attempt in range(3):  # 3 retry attempts
            for redis_url in redis_urls:
                try:
                    logger.info(f"Attempting Redis connection to {redis_url} (attempt {attempt + 1}/3)")
                    
                    # Enhanced Redis connection with performance settings
                    self.redis_client = redis.from_url(
                        redis_url, 
                        decode_responses=False,
                        socket_connect_timeout=2,  # Faster timeout for retries
                        socket_timeout=2,
                        retry_on_timeout=True,
                        health_check_interval=30,
                        max_connections=20  # Connection pooling
                    )
                    
                    # Test connection
                    self.redis_client.ping()
                    logger.info(f"Redis cache connected successfully to {redis_url}")
                    return  # Success, exit function
                    
                except Exception as e:
                    logger.debug(f"Redis connection failed for {redis_url}: {e}")
                    self.redis_client = None
                    continue
            
            # Wait before next attempt (exponential backoff)
            if attempt < 2:
                wait_time = 2 ** attempt
                logger.debug(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        if self.strict_mode:
            error_msg = "All Redis connection attempts failed. Strict mode requires Redis."
            logger.error(error_msg)
            raise RedisCacheError(error_msg)
        else:
            logger.warning("All Redis connection attempts failed. Using in-memory fallback.")
            self._init_fallback_cache()
    
    def _init_fallback_cache(self):
        """Initialize in-memory fallback cache"""
        self._fallback_cache = {}
        self._fallback_expiry = {}
        logger.info("In-memory fallback cache initialized")
    
    def _cleanup_expired_fallback_entries(self):
        """Clean up expired entries from fallback cache"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self._fallback_expiry.items() 
            if current_time > expiry
        ]
        
        for key in expired_keys:
            self._fallback_cache.pop(key, None)
            self._fallback_expiry.pop(key, None)
    
    def _get_key(self, key: str, namespace: str = "dg") -> str:
        """Get namespaced cache key"""
        return f"{namespace}:{key}"
    
    def get(self, key: str, namespace: str = "dg") -> Any:
        """Get value from cache with fallback support"""
        cache_key = self._get_key(key, namespace)
        
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(cache_key)
                
                if value is not None:
                    self.stats['hits'] += 1
                    # Use only JSON deserialization for security
                    try:
                        decoded_value = value.decode('utf-8') if isinstance(value, bytes) else str(value)
                        return self._safe_json_loads(decoded_value)
                    except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as e:
                        logger.warning(f"Failed to deserialize cached value for key {key}: {e}")
                        # Return None instead of attempting unsafe pickle deserialization
                        return None
                        
            except Exception as e:
                logger.debug(f"Redis get error for key {key}: {e}")
                self.stats['errors'] += 1
        
        # Fallback to in-memory cache
        self._cleanup_expired_fallback_entries()
        if cache_key in self._fallback_cache:
            self.stats['hits'] += 1
            return self._fallback_cache[cache_key]
        
        self.stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = "dg") -> bool:
        """Set value in cache with fallback support"""
        cache_key = self._get_key(key, namespace)
        expiry = ttl or self.default_ttl
        success = False
        
        # Try Redis first
        if self.redis_client:
            try:
                # Use only JSON serialization for security
                serialized_value = self._safe_json_dumps(value)
                
                result = self.redis_client.setex(cache_key, expiry, serialized_value)
                
                if result:
                    self.stats['sets'] += 1
                    success = True
                else:
                    self.stats['errors'] += 1
                    
            except Exception as e:
                logger.debug(f"Redis set error for key {key}: {e}")
                self.stats['errors'] += 1
        
        # Always store in fallback cache as backup (with TTL)
        self._cleanup_expired_fallback_entries()
        self._fallback_cache[cache_key] = value
        self._fallback_expiry[cache_key] = time.time() + expiry
        
        if not success:
            self.stats['sets'] += 1  # Count fallback as successful set
        
        return True  # Always return True since we have fallback
    
    def _safe_json_dumps(self, value: Any) -> str:
        """Safely serialize value to JSON, handling complex types"""
        def json_serializer(obj):
            """Custom JSON serializer for complex types"""
            if isinstance(obj, datetime):
                return {'__datetime__': obj.isoformat()}
            elif isinstance(obj, timedelta):
                return {'__timedelta__': obj.total_seconds()}
            elif isinstance(obj, Decimal):
                return {'__decimal__': str(obj)}
            elif isinstance(obj, set):
                return {'__set__': list(obj)}
            elif isinstance(obj, bytes):
                return {'__bytes__': base64.b64encode(obj).decode('utf-8')}
            elif hasattr(obj, '__dict__'):
                return {'__object__': obj.__dict__, '__class__': obj.__class__.__name__}
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        
        return json.dumps(value, default=json_serializer, ensure_ascii=False)
    
    def _safe_json_loads(self, value: str) -> Any:
        """Safely deserialize JSON value, handling complex types"""
        def json_deserializer(dct):
            """Custom JSON deserializer for complex types"""
            if '__datetime__' in dct:
                return datetime.fromisoformat(dct['__datetime__'])
            elif '__timedelta__' in dct:
                return timedelta(seconds=dct['__timedelta__'])
            elif '__decimal__' in dct:
                return Decimal(dct['__decimal__'])
            elif '__set__' in dct:
                return set(dct['__set__'])
            elif '__bytes__' in dct:
                return base64.b64decode(dct['__bytes__'])
            elif '__object__' in dct:
                # For security, don't reconstruct arbitrary objects
                # Return the dict instead
                return dct['__object__']
            return dct
        
        return json.loads(value, object_hook=json_deserializer)
    
    def delete(self, key: str, namespace: str = "dg") -> bool:
        """Delete value from cache"""
        if not self.redis_client:
            return False
            
        try:
            cache_key = self._get_key(key, namespace)
            result = self.redis_client.delete(cache_key)
            
            if result:
                self.stats['deletes'] += 1
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    def exists(self, key: str, namespace: str = "dg") -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
            
        try:
            cache_key = self._get_key(key, namespace)
            return bool(self.redis_client.exists(cache_key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def get_or_set(self, key: str, generator_func, ttl: Optional[int] = None, namespace: str = "dg") -> Any:
        """Get value from cache or generate and set it"""
        value = self.get(key, namespace)
        
        if value is None:
            value = generator_func()
            self.set(key, value, ttl, namespace)
        
        return value
    
    def increment(self, key: str, amount: int = 1, namespace: str = "dg") -> Optional[int]:
        """Increment counter in cache"""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._get_key(key, namespace)
            result = self.redis_client.incr(cache_key, amount)
            return int(result) if isinstance(result, (int, str)) else None
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {**self.stats, 'connected': False}
            
        try:
            info = self.redis_client.info()
            db_info = info.get('db0', {}) if isinstance(info, dict) else {}
            return {
                **self.stats,
                'connected': True,
                'memory_used': info.get('used_memory_human', 'N/A') if isinstance(info, dict) else 'N/A',
                'total_keys': db_info.get('keys', 0) if isinstance(db_info, dict) else 0,
                'hit_rate': self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {**self.stats, 'connected': False}
    
    def clear_namespace(self, namespace: str = "dg") -> int:
        """Clear all keys in namespace"""
        if not self.redis_client:
            return 0
            
        try:
            pattern = f"{namespace}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                # Convert keys to list if needed for proper unpacking
                key_list = list(keys) if keys else []
                deleted = self.redis_client.delete(*key_list)
                deleted_count = int(deleted) if deleted is not None else 0
                logger.info(f"Cleared {deleted_count} keys from namespace {namespace}")
                return deleted_count
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error clearing namespace {namespace}: {e}")
            return 0

# Specialized cache managers for DataGuardian Pro

class ScanResultsCache:
    """Cache manager for scan results"""
    
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache
        self.namespace = "scan_results"
        self.ttl = 7200  # 2 hours
    
    def get_scan_result(self, scan_id: str) -> Optional[Dict]:
        """Get scan result from cache"""
        return self.cache.get(f"result:{scan_id}", self.namespace)
    
    def set_scan_result(self, scan_id: str, result: Dict) -> bool:
        """Cache scan result"""
        return self.cache.set(f"result:{scan_id}", result, self.ttl, self.namespace)
    
    def get_user_scans(self, user_id: str) -> Optional[List]:
        """Get user's scan history from cache"""
        return self.cache.get(f"user_scans:{user_id}", self.namespace)
    
    def set_user_scans(self, user_id: str, scans: List) -> bool:
        """Cache user's scan history"""
        return self.cache.set(f"user_scans:{user_id}", scans, self.ttl, self.namespace)
    
    def invalidate_user_scans(self, user_id: str) -> bool:
        """Invalidate user's cached scans"""
        return self.cache.delete(f"user_scans:{user_id}", self.namespace)

class SessionCache:
    """Cache manager for user sessions"""
    
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache
        self.namespace = "sessions"
        self.ttl = 3600  # 1 hour
    
    def get(self, key: str) -> Any:
        """Get value from session cache"""
        return self.cache.get(key, self.namespace)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in session cache"""
        return self.cache.set(key, value, ttl or self.ttl, self.namespace)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data from cache"""
        return self.cache.get(f"session:{session_id}", self.namespace)
    
    def set_session(self, session_id: str, session_data: Dict) -> bool:
        """Cache session data"""
        return self.cache.set(f"session:{session_id}", session_data, self.ttl, self.namespace)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from cache"""
        return self.cache.delete(f"session:{session_id}", self.namespace)
    
    def get_user_sessions(self, user_id: str) -> Optional[List]:
        """Get all sessions for a user"""
        return self.cache.get(f"user_sessions:{user_id}", self.namespace)
    
    def track_user_activity(self, user_id: str, activity: str) -> bool:
        """Track user activity"""
        key = f"activity:{user_id}"
        activities = self.cache.get(key, self.namespace) or []
        
        activities.append({
            'activity': activity,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 activities
        if len(activities) > 100:
            activities = activities[-100:]
        
        return self.cache.set(key, activities, self.ttl * 24, self.namespace)  # 24 hours

class PerformanceCache:
    """Cache manager for performance metrics"""
    
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache
        self.namespace = "performance"
        self.ttl = 300  # 5 minutes
    
    def get_system_metrics(self) -> Optional[Dict]:
        """Get cached system metrics"""
        return self.cache.get("system_metrics", self.namespace)
    
    def set_system_metrics(self, metrics: Dict) -> bool:
        """Cache system metrics"""
        return self.cache.set("system_metrics", metrics, self.ttl, self.namespace)
    
    def get_scanner_stats(self, scanner_type: str) -> Optional[Dict]:
        """Get scanner performance stats"""
        return self.cache.get(f"scanner_stats:{scanner_type}", self.namespace)
    
    def set_scanner_stats(self, scanner_type: str, stats: Dict) -> bool:
        """Cache scanner performance stats"""
        return self.cache.set(f"scanner_stats:{scanner_type}", stats, self.ttl, self.namespace)
    
    def increment_scan_counter(self, scanner_type: str) -> Optional[int]:
        """Increment scan counter for analytics"""
        return self.cache.increment(f"scan_count:{scanner_type}", 1, self.namespace)

# Global cache instances
redis_cache = RedisCache()
scan_cache = ScanResultsCache(redis_cache)
session_cache = SessionCache(redis_cache)
performance_cache = PerformanceCache(redis_cache)

def get_cache():
    """Get the main Redis cache instance"""
    return redis_cache

def get_scan_cache():
    """Get the scan results cache"""
    return scan_cache

def get_session_cache():
    """Get the session cache"""
    return session_cache

def get_performance_cache():
    """Get the performance cache"""
    return performance_cache