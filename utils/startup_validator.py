"""
DataGuardian Pro Startup Validator
Hard-fails on missing critical dependencies to prevent security bypasses.
This ensures production deployments have all required modules.
"""

import logging
import sys
import os
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class StartupValidationError(Exception):
    """Raised when critical startup validation fails."""
    pass

class StartupValidator:
    """
    Validates all critical dependencies at application startup.
    Hard-fails if any required module is missing to prevent security bypasses.
    """
    
    CRITICAL_MODULES = [
        ('services.license_integration', 'License enforcement'),
        ('services.license_manager', 'License management'),
    ]
    
    REQUIRED_MODULES = [
        ('utils.redis_cache', 'Redis caching layer'),
        ('utils.database_optimizer', 'Database optimization'),
        ('config.pricing_config', 'Pricing configuration'),
    ]
    
    OPTIONAL_MODULES = [
        ('utils.session_optimizer', 'Session optimization'),
        ('utils.code_profiler', 'Code profiling'),
        ('services.enterprise_auth_service', 'Enterprise authentication'),
    ]
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, fail on any critical module missing.
                        If False (dev only), log warnings but continue.
        """
        self.strict_mode = strict_mode
        self.validation_results = {
            'critical': [],
            'required': [],
            'optional': [],
            'redis_status': None,
            'database_status': None
        }
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (success, list of error messages)
        """
        errors = []
        
        critical_ok, critical_errors = self._validate_critical_modules()
        if not critical_ok:
            errors.extend(critical_errors)
        
        required_ok, required_errors = self._validate_required_modules()
        if not required_ok:
            errors.extend(required_errors)
        
        redis_ok, redis_error = self._validate_redis_connection()
        if not redis_ok and self.strict_mode:
            errors.append(redis_error)
        
        db_ok, db_error = self._validate_database_connection()
        if not db_ok and self.strict_mode:
            errors.append(db_error)
        
        self._validate_optional_modules()
        
        success = len(errors) == 0
        return success, errors
    
    def _validate_critical_modules(self) -> Tuple[bool, List[str]]:
        """Validate critical security modules - hard fail if missing."""
        errors = []
        
        for module_path, description in self.CRITICAL_MODULES:
            try:
                __import__(module_path)
                self.validation_results['critical'].append({
                    'module': module_path,
                    'status': 'ok',
                    'description': description
                })
                logger.info(f"Critical module loaded: {description}")
            except ImportError as e:
                error_msg = f"CRITICAL: {description} ({module_path}) failed to load: {e}"
                errors.append(error_msg)
                self.validation_results['critical'].append({
                    'module': module_path,
                    'status': 'failed',
                    'description': description,
                    'error': str(e)
                })
                logger.error(error_msg)
        
        return len(errors) == 0, errors
    
    def _validate_required_modules(self) -> Tuple[bool, List[str]]:
        """Validate required modules - warn or fail based on strict mode."""
        errors = []
        
        for module_path, description in self.REQUIRED_MODULES:
            try:
                __import__(module_path)
                self.validation_results['required'].append({
                    'module': module_path,
                    'status': 'ok',
                    'description': description
                })
                logger.info(f"Required module loaded: {description}")
            except ImportError as e:
                if self.strict_mode:
                    error_msg = f"REQUIRED: {description} ({module_path}) failed to load: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                else:
                    logger.warning(f"Required module unavailable (non-strict): {description}")
                
                self.validation_results['required'].append({
                    'module': module_path,
                    'status': 'failed',
                    'description': description,
                    'error': str(e)
                })
        
        return len(errors) == 0, errors
    
    def _validate_optional_modules(self) -> None:
        """Validate optional modules - log status but don't fail."""
        for module_path, description in self.OPTIONAL_MODULES:
            try:
                __import__(module_path)
                self.validation_results['optional'].append({
                    'module': module_path,
                    'status': 'ok',
                    'description': description
                })
                logger.debug(f"Optional module loaded: {description}")
            except ImportError as e:
                self.validation_results['optional'].append({
                    'module': module_path,
                    'status': 'unavailable',
                    'description': description,
                    'error': str(e)
                })
                logger.debug(f"Optional module unavailable: {description}")
    
    def _validate_redis_connection(self) -> Tuple[bool, Optional[str]]:
        """Validate Redis is available and connected, with retry for container cold-start."""
        import time
        max_retries = 5
        retry_delay = 2

        for attempt in range(1, max_retries + 1):
            try:
                from utils.redis_cache import get_cache
                cache = get_cache()

                if cache and cache.redis_client:
                    cache.redis_client.ping()
                    self.validation_results['redis_status'] = 'connected'
                    logger.info("Redis connection validated")
                    return True, None
                else:
                    if attempt < max_retries:
                        logger.warning(f"Redis not ready (attempt {attempt}/{max_retries}), retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 10)
                        continue
                    self.validation_results['redis_status'] = 'fallback_mode'
                    error_msg = "Redis not connected - running in fallback mode (not suitable for production scale)"
                    logger.warning(error_msg)
                    return False, error_msg

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Redis connection attempt {attempt}/{max_retries} failed, retrying in {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 10)
                else:
                    self.validation_results['redis_status'] = 'error'
                    error_msg = f"Redis validation failed after {max_retries} attempts: {e}"
                    logger.error(error_msg)
                    return False, error_msg

        self.validation_results['redis_status'] = 'error'
        return False, "Redis validation failed after all retries"
    
    def _validate_database_connection(self) -> Tuple[bool, Optional[str]]:
        """Validate database connection is available with retry for cold-start endpoints."""
        import time
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            self.validation_results['database_status'] = 'not_configured'
            error_msg = "DATABASE_URL not configured"
            logger.warning(error_msg)
            return False, error_msg

        max_retries = 5
        retry_delay = 2
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                import psycopg2
                conn = psycopg2.connect(database_url, connect_timeout=10)
                conn.close()

                self.validation_results['database_status'] = 'connected'
                logger.info("Database connection validated")
                return True, None

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(f"Database connection attempt {attempt}/{max_retries} failed, retrying in {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2

        self.validation_results['database_status'] = 'error'
        error_msg = f"Database validation failed after {max_retries} attempts: {last_error}"
        logger.error(error_msg)
        return False, error_msg
    
    def get_status_report(self) -> dict:
        """Get detailed validation status report."""
        return {
            'validation_results': self.validation_results,
            'strict_mode': self.strict_mode,
            'ready_for_production': self._is_production_ready()
        }
    
    def _is_production_ready(self) -> bool:
        """Check if all production requirements are met."""
        critical_ok = all(
            r['status'] == 'ok' 
            for r in self.validation_results['critical']
        )
        required_ok = all(
            r['status'] == 'ok' 
            for r in self.validation_results['required']
        )
        redis_ok = self.validation_results['redis_status'] == 'connected'
        db_ok = self.validation_results['database_status'] == 'connected'
        
        return critical_ok and required_ok and redis_ok and db_ok


def validate_startup(strict_mode: bool = None) -> bool:
    """
    Main entry point for startup validation.
    
    Args:
        strict_mode: If None, auto-detect based on environment.
                    Production = strict, Development = lenient.
    
    Returns:
        True if validation passed, raises StartupValidationError otherwise.
    """
    if strict_mode is None:
        env = os.environ.get('ENVIRONMENT', 'development').lower()
        strict_mode = env in ('production', 'prod', 'staging')
    
    validator = StartupValidator(strict_mode=strict_mode)
    success, errors = validator.validate_all()
    
    if not success:
        if strict_mode:
            error_report = "\n".join(errors)
            raise StartupValidationError(
                f"Startup validation failed. Cannot proceed.\n{error_report}"
            )
        else:
            logger.warning(f"Startup validation warnings (non-strict mode): {errors}")
    
    report = validator.get_status_report()
    if report['ready_for_production']:
        logger.info("All startup validations passed - production ready")
    else:
        logger.warning("Some validations failed - not recommended for production")
    
    return success


_cached_validator = None

def get_startup_validator() -> StartupValidator:
    """Get cached startup validator instance."""
    global _cached_validator
    if _cached_validator is None:
        _cached_validator = StartupValidator(strict_mode=False)
        _cached_validator.validate_all()
    return _cached_validator
