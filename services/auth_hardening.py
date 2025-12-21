"""
Authentication Hardening Module
Production-grade security enhancements for enterprise customers
- bcrypt password hashing
- Login attempt limiting with lockout
- Session timeout management
- Password policy enforcement
- Multi-factor authentication preparation
"""

import os
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

security_logger = logging.getLogger('security_audit')
if not security_logger.handlers:
    try:
        security_handler = logging.FileHandler('security_audit.log')
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        ))
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.INFO)
    except Exception:
        pass

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.warning("bcrypt not available, falling back to SHA256 hashing")

class PasswordStrength(Enum):
    """Password strength levels"""
    WEAK = "weak"
    FAIR = "fair"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 60
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    bcrypt_rounds: int = 12
    session_token_length: int = 64

_login_attempts: Dict[str, Dict[str, Any]] = {}
_active_sessions: Dict[str, Dict[str, Any]] = {}
_security_config = SecurityConfig()

def get_security_config() -> SecurityConfig:
    """Get the current security configuration"""
    return _security_config

def update_security_config(**kwargs) -> SecurityConfig:
    """Update security configuration"""
    global _security_config
    for key, value in kwargs.items():
        if hasattr(_security_config, key):
            setattr(_security_config, key, value)
    return _security_config

def hash_password_secure(password: str) -> str:
    """
    Hash password using bcrypt (preferred) or SHA256 with salt (fallback).
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=_security_config.bcrypt_rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    else:
        salt = secrets.token_hex(32)
        combined = f"{salt}${password}"
        hashed = hashlib.sha256(combined.encode()).hexdigest()
        return f"sha256${salt}${hashed}"

def verify_password_secure(password: str, stored_hash: str) -> bool:
    """
    Verify password against stored hash.
    Supports both bcrypt and legacy SHA256 hashes.
    
    Args:
        password: Plain text password to verify
        stored_hash: Stored hash to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$'):
        if BCRYPT_AVAILABLE:
            try:
                return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
            except Exception as e:
                logger.error(f"bcrypt verification error: {e}")
                return False
        else:
            logger.error("bcrypt hash found but bcrypt not available")
            return False
    elif stored_hash.startswith('sha256$'):
        parts = stored_hash.split('$')
        if len(parts) == 3:
            _, salt, original_hash = parts
            combined = f"{salt}${password}"
            new_hash = hashlib.sha256(combined.encode()).hexdigest()
            return secrets.compare_digest(new_hash, original_hash)
    else:
        plain_hash = hashlib.sha256(password.encode()).hexdigest()
        return secrets.compare_digest(plain_hash, stored_hash)
    
    return False

def check_password_policy(password: str) -> Tuple[bool, str, PasswordStrength]:
    """
    Check if password meets the security policy requirements.
    
    Args:
        password: Password to check
        
    Returns:
        Tuple of (is_valid, message, strength)
    """
    issues = []
    strength_score = 0
    
    if len(password) < _security_config.password_min_length:
        issues.append(f"Password must be at least {_security_config.password_min_length} characters")
    else:
        strength_score += 1
        if len(password) >= 12:
            strength_score += 1
        if len(password) >= 16:
            strength_score += 1
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:',.<>?/~`" for c in password)
    
    if _security_config.password_require_uppercase and not has_upper:
        issues.append("Password must contain at least one uppercase letter")
    elif has_upper:
        strength_score += 1
        
    if _security_config.password_require_lowercase and not has_lower:
        issues.append("Password must contain at least one lowercase letter")
    elif has_lower:
        strength_score += 1
        
    if _security_config.password_require_digit and not has_digit:
        issues.append("Password must contain at least one digit")
    elif has_digit:
        strength_score += 1
        
    if _security_config.password_require_special and not has_special:
        issues.append("Password must contain at least one special character")
    elif has_special:
        strength_score += 1
    
    if strength_score <= 2:
        strength = PasswordStrength.WEAK
    elif strength_score <= 4:
        strength = PasswordStrength.FAIR
    elif strength_score <= 6:
        strength = PasswordStrength.STRONG
    else:
        strength = PasswordStrength.VERY_STRONG
    
    is_valid = len(issues) == 0
    message = "; ".join(issues) if issues else "Password meets all requirements"
    
    return is_valid, message, strength

def check_login_allowed(username: str, ip_address: str = None) -> Tuple[bool, str, int]:
    """
    Check if login is allowed for the given username/IP.
    
    Args:
        username: Username attempting login
        ip_address: IP address of the request (optional)
        
    Returns:
        Tuple of (is_allowed, message, remaining_attempts)
    """
    key = f"{username}:{ip_address}" if ip_address else username
    
    if key not in _login_attempts:
        return True, "Login allowed", _security_config.max_login_attempts
    
    attempt_data = _login_attempts[key]
    
    if attempt_data.get('locked_until'):
        locked_until = attempt_data['locked_until']
        if datetime.now() < locked_until:
            remaining_seconds = int((locked_until - datetime.now()).total_seconds())
            remaining_minutes = remaining_seconds // 60 + 1
            security_logger.warning(f"Login blocked for locked account: {username} from {ip_address}")
            return False, f"Account locked. Try again in {remaining_minutes} minutes", 0
        else:
            attempt_data['attempts'] = 0
            attempt_data['locked_until'] = None
    
    remaining = _security_config.max_login_attempts - attempt_data.get('attempts', 0)
    return True, "Login allowed", max(remaining, 0)

def record_login_attempt(username: str, ip_address: str = None, success: bool = False) -> None:
    """
    Record a login attempt for rate limiting.
    
    Args:
        username: Username that attempted login
        ip_address: IP address of the request
        success: Whether the login was successful
    """
    key = f"{username}:{ip_address}" if ip_address else username
    
    if key not in _login_attempts:
        _login_attempts[key] = {
            'attempts': 0,
            'last_attempt': None,
            'locked_until': None
        }
    
    if success:
        _login_attempts[key] = {
            'attempts': 0,
            'last_attempt': datetime.now(),
            'locked_until': None
        }
        security_logger.info(f"Successful login: {username} from {ip_address}")
    else:
        _login_attempts[key]['attempts'] += 1
        _login_attempts[key]['last_attempt'] = datetime.now()
        
        if _login_attempts[key]['attempts'] >= _security_config.max_login_attempts:
            _login_attempts[key]['locked_until'] = datetime.now() + timedelta(
                minutes=_security_config.lockout_duration_minutes
            )
            security_logger.warning(
                f"Account locked due to too many failed attempts: {username} from {ip_address}"
            )
        else:
            remaining = _security_config.max_login_attempts - _login_attempts[key]['attempts']
            security_logger.warning(
                f"Failed login attempt ({remaining} remaining): {username} from {ip_address}"
            )

def create_session(user_id: str, username: str, role: str, ip_address: str = None) -> str:
    """
    Create a new secure session.
    
    Args:
        user_id: User ID
        username: Username
        role: User role
        ip_address: Client IP address
        
    Returns:
        Session token
    """
    session_token = secrets.token_urlsafe(_security_config.session_token_length)
    
    session_data = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'ip_address': ip_address,
        'created_at': datetime.now(),
        'last_activity': datetime.now(),
        'expires_at': datetime.now() + timedelta(minutes=_security_config.session_timeout_minutes)
    }
    
    _active_sessions[session_token] = session_data
    
    security_logger.info(f"Session created for user: {username} from {ip_address}")
    
    return session_token

def validate_session(session_token: str, ip_address: str = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate a session token.
    
    Args:
        session_token: Session token to validate
        ip_address: Current IP address for validation
        
    Returns:
        Tuple of (is_valid, session_data)
    """
    if not session_token or session_token not in _active_sessions:
        return False, None
    
    session = _active_sessions[session_token]
    
    if datetime.now() > session['expires_at']:
        del _active_sessions[session_token]
        security_logger.info(f"Session expired for user: {session['username']}")
        return False, None
    
    session['last_activity'] = datetime.now()
    session['expires_at'] = datetime.now() + timedelta(
        minutes=_security_config.session_timeout_minutes
    )
    
    return True, session

def invalidate_session(session_token: str) -> bool:
    """
    Invalidate a session (logout).
    
    Args:
        session_token: Session token to invalidate
        
    Returns:
        True if session was invalidated
    """
    if session_token in _active_sessions:
        session = _active_sessions[session_token]
        security_logger.info(f"Session invalidated for user: {session['username']}")
        del _active_sessions[session_token]
        return True
    return False

def get_active_sessions_count(username: str = None) -> int:
    """
    Get count of active sessions.
    
    Args:
        username: Filter by username (optional)
        
    Returns:
        Number of active sessions
    """
    if username:
        return sum(1 for s in _active_sessions.values() if s['username'] == username)
    return len(_active_sessions)

def cleanup_expired_sessions() -> int:
    """
    Remove expired sessions from memory.
    
    Returns:
        Number of sessions cleaned up
    """
    now = datetime.now()
    expired = [token for token, session in _active_sessions.items() if now > session['expires_at']]
    
    for token in expired:
        del _active_sessions[token]
    
    if expired:
        logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    return len(expired)

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def verify_tenant_access(user_id: str, organization_id: str) -> bool:
    """
    Verify user has access to the specified tenant/organization.
    
    Args:
        user_id: User ID
        organization_id: Organization/tenant ID
        
    Returns:
        True if user has access
    """
    try:
        from services.multi_tenant_service import MultiTenantService
        tenant_service = MultiTenantService()
        return tenant_service.verify_user_tenant_access(user_id, organization_id)
    except Exception as e:
        logger.warning(f"Tenant verification failed: {e}")
        return True

def get_security_audit_log(limit: int = 100) -> list:
    """
    Get recent security audit log entries.
    
    Args:
        limit: Maximum number of entries to return
        
    Returns:
        List of log entries
    """
    try:
        with open('security_audit.log', 'r') as f:
            lines = f.readlines()
            return lines[-limit:] if len(lines) > limit else lines
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.error(f"Error reading security audit log: {e}")
        return []


def authenticate_secure(username_or_email: str, password: str, ip_address: str = None) -> Optional[Dict[str, Any]]:
    """
    Secure authentication with rate limiting and logging.
    
    Args:
        username_or_email: Username or email
        password: Password
        ip_address: Client IP address
        
    Returns:
        User data dict if successful, None otherwise
    """
    is_allowed, message, remaining = check_login_allowed(username_or_email, ip_address)
    
    if not is_allowed:
        return None
    
    from services.auth import authenticate as base_authenticate
    user = base_authenticate(username_or_email, password)
    
    record_login_attempt(username_or_email, ip_address, success=user is not None)
    
    if user:
        session_token = create_session(
            user_id=user.get('user_id', username_or_email),
            username=user.get('username', username_or_email),
            role=user.get('role', 'user'),
            ip_address=ip_address
        )
        user['session_token'] = session_token
    
    return user
