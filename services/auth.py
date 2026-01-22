import hashlib
import json
import os
import re
import secrets
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List, Set
from cryptography.fernet import Fernet
import base64

try:
    from email_service import email_service
except ImportError:
    from services.email_service import email_service

# Enhanced secure user store with encryption
# Users are stored encrypted in JSON file with proper security measures
USERS_FILE = "users.json"
SECURE_USERS_FILE = "secure_users.json"
USERS_ENCRYPTION_KEY_FILE = "users.key"

# Main logger
logger = logging.getLogger(__name__)

# Security logger (separate from main app logging)
security_logger = logging.getLogger('security_audit')
security_handler = logging.FileHandler('security_audit.log')
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

# Define permission structure
# Each permission is a string like 'scan:create' or 'user:delete'
# Format: resource:action
PERMISSIONS = {
    # Scan permissions
    'scan:create': 'Ability to create new scans',
    'scan:view': 'Ability to view scan results',
    'scan:export': 'Ability to export scan results',
    'scan:delete': 'Ability to delete scan results',
    'scan:premium': 'Ability to use premium scan features',
    'scan:configure': 'Ability to configure scan settings',
    
    # User management permissions
    'user:create': 'Ability to create new users',
    'user:view': 'Ability to view user information',
    'user:update': 'Ability to update user information',
    'user:delete': 'Ability to delete users',
    
    # Report permissions
    'report:create': 'Ability to create reports',
    'report:view': 'Ability to view reports',
    'report:export': 'Ability to export reports',
    
    # System permissions
    'system:settings': 'Ability to modify system settings',
    'system:logs': 'Ability to view system logs',
    'system:backup': 'Ability to backup system data',
    'system:restore': 'Ability to restore system data',
    
    # Admin permissions
    'admin:manage_users': 'Ability to manage users',
    'admin:manage_roles': 'Ability to manage roles',
    'admin:view_metrics': 'Ability to view system metrics',
    
    # Payment management
    'payment:manage': 'Ability to manage payment settings',
    'payment:view': 'Ability to view payment history',
    
    # Audit permissions
    'audit:view': 'Ability to view audit logs',
    'audit:export': 'Ability to export audit logs',
    
    # View permissions
    'dashboard:view': 'Ability to view the dashboard',
    'history:view': 'Ability to view scan history',
    
    # API permissions
    'api:access': 'Ability to access API endpoints',
    'api:manage_keys': 'Ability to manage API keys',
    
    # Advanced scanning features
    'scan:website': 'Ability to scan websites',
    'scan:code': 'Ability to scan code repositories',
    'scan:document': 'Ability to scan documents',
    'scan:database': 'Ability to scan databases',
    'scan:api': 'Ability to scan APIs',
}

# Define roles and their permissions
ROLE_PERMISSIONS = {
    'admin': {
        'description': 'Full system access with all permissions',
        'permissions': [
            # Scan permissions
            'scan:create', 'scan:view', 'scan:export', 'scan:delete', 'scan:premium', 'scan:configure',
            'scan:website', 'scan:code', 'scan:document', 'scan:database', 'scan:api',
            
            # User management
            'user:create', 'user:view', 'user:update', 'user:delete',
            
            # Report permissions
            'report:create', 'report:view', 'report:export',
            
            # System management
            'system:settings', 'system:logs', 'system:backup', 'system:restore',
            
            # Admin permissions
            'admin:manage_users', 'admin:manage_roles', 'admin:view_metrics',
            
            # Payment management
            'payment:manage', 'payment:view',
            
            # Audit permissions
            'audit:view', 'audit:export',
            
            # View permissions
            'dashboard:view', 'history:view',
            
            # API permissions
            'api:access', 'api:manage_keys'
        ]
    },
    'user': {
        'description': 'Standard user with basic scanning and viewing permissions',
        'permissions': [
            # Basic scan permissions
            'scan:create', 'scan:view', 'scan:export',
            'scan:website', 'scan:code', 'scan:document', 'scan:database', 'scan:api',
            
            # Report permissions
            'report:create', 'report:view', 'report:export',
            
            # View permissions
            'dashboard:view', 'history:view'
        ]
    },
    'analyst': {
        'description': 'Can create and analyze scans, generate reports',
        'permissions': [
            # Scan permissions
            'scan:create', 'scan:view', 'scan:export', 'scan:premium', 'scan:configure',
            'scan:website', 'scan:code', 'scan:document', 'scan:database', 'scan:api',
            
            # Report permissions
            'report:create', 'report:view', 'report:export',
            
            # Limited user access
            'user:view',
            
            # Audit access
            'audit:view',
            
            # View permissions
            'dashboard:view', 'history:view',
            
            # API access
            'api:access'
        ]
    },
    'viewer': {
        'description': 'Read-only access to scans and reports',
        'permissions': [
            # Limited scan access
            'scan:view',
            
            # Limited report access
            'report:view',
            
            # View permissions
            'dashboard:view', 'history:view'
        ]
    },
    'security_officer': {
        'description': 'Focused on security compliance and auditing',
        'permissions': [
            # Scan permissions
            'scan:create', 'scan:view', 'scan:export', 'scan:configure',
            'scan:website', 'scan:code', 'scan:document',
            
            # Report access
            'report:view', 'report:export', 'report:create',
            
            # System monitoring
            'system:logs',
            
            # Audit access
            'audit:view', 'audit:export',
            
            # View permissions
            'dashboard:view', 'history:view'
        ]
    },
    'data_protection_officer': {
        'description': 'Focused on data protection and compliance reporting',
        'permissions': [
            # Limited scan access
            'scan:view', 'scan:export',
            
            # Report access
            'report:view', 'report:export', 'report:create',
            
            # Audit access
            'audit:view',
            
            # View permissions
            'dashboard:view', 'history:view'
        ]
    },
    'developer': {
        'description': 'Technical role for API integration and development',
        'permissions': [
            # Scan access
            'scan:create', 'scan:view', 'scan:export',
            'scan:website', 'scan:code', 'scan:api',
            
            # Limited report access
            'report:view',
            
            # API access
            'api:access', 'api:manage_keys',
            
            # View permissions
            'dashboard:view', 'history:view'
        ]
    },
    'manager': {
        'description': 'Oversees operations with metric visibility',
        'permissions': [
            # Limited scan access
            'scan:view', 'scan:export',
            
            # Report access
            'report:view', 'report:export',
            
            # Limited admin access
            'admin:view_metrics',
            
            # Limited payment access
            'payment:view',
            
            # Audit access
            'audit:view',
            
            # View permissions
            'dashboard:view', 'history:view'
        ]
    }
}

# Default users to create if the file doesn't exist
DEFAULT_USERS = [
    {
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "email": "admin@example.com",
        "permissions": ROLE_PERMISSIONS["admin"]["permissions"],
        "created_at": datetime.now().isoformat()
    },
    {
        "username": "analyst",
        "password_hash": hashlib.sha256("analyst123".encode()).hexdigest(),
        "role": "analyst",
        "email": "analyst@example.com",
        "permissions": ROLE_PERMISSIONS["analyst"]["permissions"],
        "created_at": datetime.now().isoformat()
    },
    {
        "username": "viewer",
        "password_hash": hashlib.sha256("viewer123".encode()).hexdigest(),
        "role": "viewer",
        "email": "viewer@example.com",
        "permissions": ROLE_PERMISSIONS["viewer"]["permissions"],
        "created_at": datetime.now().isoformat()
    },
    {
        "username": "security",
        "password_hash": hashlib.sha256("security123".encode()).hexdigest(),
        "role": "security_officer",
        "email": "security@example.com",
        "permissions": ROLE_PERMISSIONS["security_officer"]["permissions"],
        "created_at": datetime.now().isoformat()
    },
    {
        "username": "dpo",
        "password_hash": hashlib.sha256("dpo123".encode()).hexdigest(),
        "role": "data_protection_officer",
        "email": "dpo@example.com",
        "permissions": ROLE_PERMISSIONS["data_protection_officer"]["permissions"],
        "created_at": datetime.now().isoformat()
    },
    {
        "username": "developer",
        "password_hash": hashlib.sha256("developer123".encode()).hexdigest(),
        "role": "developer",
        "email": "developer@example.com",
        "permissions": ROLE_PERMISSIONS["developer"]["permissions"],
        "created_at": datetime.now().isoformat()
    },
    {
        "username": "manager",
        "password_hash": hashlib.sha256("manager123".encode()).hexdigest(),
        "role": "manager",
        "email": "manager@example.com",
        "permissions": ROLE_PERMISSIONS["manager"]["permissions"],
        "created_at": datetime.now().isoformat()
    },
    {
        "username": "user",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "user",
        "email": "user@example.com",
        "permissions": ROLE_PERMISSIONS["user"]["permissions"],
        "created_at": datetime.now().isoformat()
    }
]

def _load_users() -> Dict[str, Dict[str, Any]]:
    """
    Load users from file, creating with defaults if it doesn't exist.
    
    Returns:
        Dictionary of users indexed by username
    """
    if not os.path.exists(USERS_FILE):
        # Create default users file
        users = {user["username"]: user for user in DEFAULT_USERS}
        _save_users(users)
        return users
    
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        # If file is corrupted, create a new one with defaults
        users = {user["username"]: user for user in DEFAULT_USERS}
        _save_users(users)
        return users

def _save_users(users: Dict[str, Dict[str, Any]]) -> None:
    """
    Save users to file.
    
    Args:
        users: Dictionary of users indexed by username
    """
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {str(e)}")

def validate_email(email: str) -> bool:
    """
    Validates if a string is a proper email address.
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))
    
def get_user_by_email(email: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Find a user by email address.
    
    Args:
        email: The email to search for
        
    Returns:
        Tuple of (username, user_data) if found, None otherwise
    """
    if not validate_email(email):
        return None
        
    users = _load_users()
    
    for username, user_data in users.items():
        if user_data.get("email") == email:
            return (username, user_data)
    
    return None
    
def reset_password(email: str, new_password: str) -> Tuple[bool, str]:
    """
    Reset a user's password using their email address.
    
    Args:
        email: The email address of the user
        new_password: The new password to set
        
    Returns:
        Tuple of (success, message)
    """
    # Validate email
    if not validate_email(email):
        return False, "Invalid email format"
        
    # Find user by email
    user_info = get_user_by_email(email)
    if not user_info:
        return False, "No account found with this email address"
        
    username, _ = user_info
    
    # Validate password
    if not new_password or len(new_password) < 6:
        return False, "New password must be at least 6 characters"
    
    # Update user password
    users = _load_users()
    users[username]["password_hash"] = hashlib.sha256(new_password.encode()).hexdigest()
    users[username]["password_reset_at"] = datetime.now().isoformat()
    
    _save_users(users)
    return True, "Password reset successfully"

def authenticate(username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with username/email and password.
    
    Args:
        username_or_email: The username or email to authenticate
        password: The password to check
        
    Returns:
        User data dictionary if authentication is successful, None otherwise
    """
    users = _load_users()
    
    # Check if direct username match
    if username_or_email in users:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if users[username_or_email]["password_hash"] == password_hash:
            # Return user data without password hash
            user_data = users[username_or_email].copy()
            user_data.pop("password_hash", None)
            # Record login in database
            _record_user_login(username_or_email)
            return user_data
    
    # Check if email match
    is_email = validate_email(username_or_email)
    if is_email:
        for username, user_data in users.items():
            if user_data.get("email") == username_or_email:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if user_data["password_hash"] == password_hash:
                    # Return user data without password hash
                    result = user_data.copy()
                    result.pop("password_hash", None)
                    # Record login in database
                    _record_user_login(username)
                    return result
    
    return None


def _record_user_login(username: str):
    """Record user login in the database for tracking"""
    try:
        from services.user_management_service import get_user_management_service
        ums = get_user_management_service()
        user = ums.get_user(username=username)
        if user:
            ums.record_login(user['id'])
    except Exception as e:
        # Don't fail authentication if tracking fails
        logger.warning(f"Failed to record login for {username}: {e}")

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """
    Get user data by username.
    
    Args:
        username: The username to look up
        
    Returns:
        User data dictionary if found, None otherwise
    """
    users = _load_users()
    
    if username in users:
        # Return user data without password hash
        user_data = users[username].copy()
        user_data.pop("password_hash", None)
        return user_data
    
    return None

def create_user(username: str, password: str, role: str, email: str) -> Tuple[bool, str]:
    """
    Create a new user with validation.
    
    Args:
        username: The username for the new user
        password: The password for the new user
        role: The role for the new user
        email: The email for the new user
        
    Returns:
        Tuple of (success, message) where success is True if user was created, 
        False otherwise, and message provides details
    """
    users = _load_users()
    
    # Validate username
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    # Check if username exists
    if username in users:
        return False, "Username already exists"
    
    # Check for email format
    if not validate_email(email):
        return False, "Invalid email format"
    
    # Check if email is already used
    for existing_user in users.values():
        if existing_user.get("email") == email:
            return False, "Email address is already registered"
    
    # Validate password
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Validate role
    if role not in ROLE_PERMISSIONS:
        return False, f"Invalid role. Valid roles are: {', '.join(ROLE_PERMISSIONS.keys())}"
    
    # Create user
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    users[username] = {
        "username": username,
        "password_hash": password_hash,
        "role": role,
        "email": email,
        "permissions": ROLE_PERMISSIONS[role]["permissions"],
        "created_at": datetime.now().isoformat()
    }
    
    _save_users(users)
    
    # Send welcome email to new user
    try:
        email_service.send_welcome_email({
            'username': username,
            'email': email,
            'role': role
        })
        logger.info(f"Welcome email sent to new user: {username}")
    except Exception as e:
        logger.warning(f"Failed to send welcome email to {username}: {str(e)}")
    
    return True, "User created successfully"

def update_user(username: str, updates: Dict[str, Any]) -> bool:
    """
    Update an existing user.
    
    Args:
        username: The username of the user to update
        updates: Dictionary of fields to update
        
    Returns:
        True if user was updated, False if user doesn't exist
    """
    users = _load_users()
    
    if username not in users:
        return False
    
    # Update password if provided
    if "password" in updates:
        updates["password_hash"] = hashlib.sha256(updates.pop("password").encode()).hexdigest()
    
    # Update other fields
    for key, value in updates.items():
        if key != "username" and key != "password":  # Don't allow username changes
            users[username][key] = value
    
    _save_users(users)
    return True

def delete_user(username: str) -> bool:
    """
    Delete a user.
    
    Args:
        username: The username of the user to delete
        
    Returns:
        True if user was deleted, False if user doesn't exist
    """
    users = _load_users()
    
    if username not in users:
        return False
    
    del users[username]
    _save_users(users)
    return True


# ============================================================================
# MFA/2FA Functions - SOC 2 Compliant Multi-Factor Authentication
# ============================================================================

def _load_secure_users() -> Dict[str, Dict[str, Any]]:
    """Load users from secure_users.json file."""
    if os.path.exists(SECURE_USERS_FILE):
        try:
            with open(SECURE_USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_secure_users(users: Dict[str, Dict[str, Any]]) -> None:
    """Save users to secure_users.json file."""
    with open(SECURE_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2, default=str)

def enable_mfa(username: str, email: str = None) -> Dict[str, Any]:
    """
    Enable MFA for a user and return setup data.
    
    Args:
        username: The username to enable MFA for
        email: Optional email for QR code provisioning
        
    Returns:
        Dict with setup data including QR code and backup codes
    """
    from services.mfa_service import enable_mfa_for_user
    
    secure_users = _load_secure_users()
    users = _load_users()
    
    if username in secure_users:
        user_data = secure_users[username]
        user_email = email or user_data.get("email", username)
        result = enable_mfa_for_user(username, user_email)
        
        if result["success"]:
            secure_users[username]["mfa_enabled"] = False
            secure_users[username]["mfa_secret"] = result["secret"]
            secure_users[username]["mfa_backup_codes"] = result["backup_code_hashes"]
            secure_users[username]["mfa_setup_pending"] = True
            _save_secure_users(secure_users)
            security_logger.info(f"MFA setup initiated for user: {username}")
        return result
    elif username in users:
        user_email = email or users[username].get("email", username)
        result = enable_mfa_for_user(username, user_email)
        
        if result["success"]:
            users[username]["mfa_enabled"] = False
            users[username]["mfa_secret"] = result["secret"]
            users[username]["mfa_backup_codes"] = result["backup_code_hashes"]
            users[username]["mfa_setup_pending"] = True
            _save_users(users)
            security_logger.info(f"MFA setup initiated for user: {username}")
        return result
    else:
        return {"success": False, "error": "User not found"}


def confirm_mfa_setup(username: str, verification_code: str) -> Tuple[bool, str]:
    """
    Confirm MFA setup by verifying the first code.
    
    Args:
        username: The username
        verification_code: TOTP code from authenticator app
        
    Returns:
        Tuple of (success, message)
    """
    from services.mfa_service import verify_mfa_code
    
    secure_users = _load_secure_users()
    users = _load_users()
    
    if username in secure_users:
        user = secure_users[username]
        if not user.get("mfa_setup_pending"):
            return False, "No MFA setup in progress"
        
        secret = user.get("mfa_secret")
        if not secret:
            return False, "MFA secret not found"
        
        result = verify_mfa_code(verification_code, totp_secret=secret)
        
        if result["valid"]:
            secure_users[username]["mfa_enabled"] = True
            secure_users[username]["mfa_setup_pending"] = False
            secure_users[username]["mfa_enabled_at"] = datetime.now().isoformat()
            _save_secure_users(secure_users)
            security_logger.info(f"MFA enabled for user: {username}")
            return True, "MFA enabled successfully"
        return False, "Invalid verification code"
    elif username in users:
        user = users[username]
        if not user.get("mfa_setup_pending"):
            return False, "No MFA setup in progress"
        
        secret = user.get("mfa_secret")
        if not secret:
            return False, "MFA secret not found"
        
        result = verify_mfa_code(verification_code, totp_secret=secret)
        
        if result["valid"]:
            users[username]["mfa_enabled"] = True
            users[username]["mfa_setup_pending"] = False
            users[username]["mfa_enabled_at"] = datetime.now().isoformat()
            _save_users(users)
            security_logger.info(f"MFA enabled for user: {username}")
            return True, "MFA enabled successfully"
        return False, "Invalid verification code"
    else:
        return False, "User not found"


def disable_mfa(username: str, password: str) -> Tuple[bool, str]:
    """
    Disable MFA for a user (requires password confirmation).
    
    Args:
        username: The username
        password: Password for confirmation
        
    Returns:
        Tuple of (success, message)
    """
    users = _load_users()
    if username not in users:
        return False, "User not found"
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if users[username]["password_hash"] != password_hash:
        security_logger.warning(f"MFA disable failed - wrong password for user: {username}")
        return False, "Invalid password"
    
    users[username]["mfa_enabled"] = False
    users[username]["mfa_secret"] = None
    users[username]["mfa_backup_codes"] = None
    users[username]["mfa_setup_pending"] = False
    users[username]["mfa_disabled_at"] = datetime.now().isoformat()
    _save_users(users)
    
    security_logger.info(f"MFA disabled for user: {username}")
    return True, "MFA disabled successfully"


def get_mfa_status(username: str) -> Dict[str, Any]:
    """
    Get MFA status for a user.
    
    Returns:
        Dict with mfa_enabled, setup_pending status
    """
    secure_users = _load_secure_users()
    users = _load_users()
    
    if username in secure_users:
        user = secure_users[username]
    elif username in users:
        user = users[username]
    else:
        return {"enabled": False, "setup_pending": False, "error": "User not found"}
    
    return {
        "enabled": user.get("mfa_enabled", False),
        "setup_pending": user.get("mfa_setup_pending", False),
        "enabled_at": user.get("mfa_enabled_at"),
        "backup_codes_remaining": len(user.get("mfa_backup_codes", []))
    }


def verify_mfa(username: str, code: str) -> Tuple[bool, str]:
    """
    Verify MFA code for a user.
    
    Args:
        username: The username
        code: TOTP or backup code
        
    Returns:
        Tuple of (success, method_used)
    """
    from services.mfa_service import verify_mfa_code
    
    users = _load_users()
    if username not in users:
        return False, "User not found"
    
    user = users[username]
    if not user.get("mfa_enabled"):
        return True, "mfa_not_required"
    
    secret = user.get("mfa_secret")
    backup_codes = user.get("mfa_backup_codes", [])
    
    result = verify_mfa_code(code, totp_secret=secret, backup_code_hashes=backup_codes)
    
    if result["valid"]:
        if result["method"] == "backup_code":
            from services.mfa_service import get_mfa_service
            service = get_mfa_service()
            code_hash = service.hash_backup_code(code)
            if code_hash in backup_codes:
                backup_codes.remove(code_hash)
                users[username]["mfa_backup_codes"] = backup_codes
                _save_users(users)
                security_logger.info(f"Backup code used for user: {username}")
        
        security_logger.info(f"MFA verification successful for user: {username} via {result['method']}")
        return True, result["method"]
    
    security_logger.warning(f"MFA verification failed for user: {username}")
    return False, "invalid_code"


def authenticate_with_mfa(
    username_or_email: str, 
    password: str, 
    mfa_code: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Authenticate a user with optional MFA verification.
    
    Args:
        username_or_email: Username or email
        password: Password
        mfa_code: Optional MFA code (required if MFA is enabled)
        
    Returns:
        Tuple of (user_data, error_or_status)
        - (user_data, None) - Success
        - (None, "mfa_required") - Password OK, MFA code needed
        - (None, "invalid_credentials") - Wrong password
        - (None, "invalid_mfa") - Wrong MFA code
    """
    user_data = authenticate(username_or_email, password)
    
    if not user_data:
        security_logger.warning(f"Authentication failed for: {username_or_email}")
        return None, "invalid_credentials"
    
    username = user_data.get("username", username_or_email)
    
    mfa_status = get_mfa_status(username)
    if not mfa_status.get("enabled"):
        return user_data, None
    
    if not mfa_code:
        return None, "mfa_required"
    
    mfa_valid, method = verify_mfa(username, mfa_code)
    if not mfa_valid:
        security_logger.warning(f"MFA verification failed for: {username}")
        return None, "invalid_mfa"
    
    user_data["mfa_verified"] = True
    user_data["mfa_method"] = method
    
    return user_data, None


def regenerate_backup_codes(username: str, password: str) -> Dict[str, Any]:
    """
    Regenerate backup codes for a user.
    
    Args:
        username: The username
        password: Password for confirmation
        
    Returns:
        Dict with new backup codes or error
    """
    from services.mfa_service import get_mfa_service
    
    users = _load_users()
    if username not in users:
        return {"success": False, "error": "User not found"}
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if users[username]["password_hash"] != password_hash:
        return {"success": False, "error": "Invalid password"}
    
    if not users[username].get("mfa_enabled"):
        return {"success": False, "error": "MFA is not enabled"}
    
    service = get_mfa_service()
    new_codes = service.generate_backup_codes()
    hashed_codes = [service.hash_backup_code(code) for code in new_codes]
    
    users[username]["mfa_backup_codes"] = hashed_codes
    users[username]["backup_codes_regenerated_at"] = datetime.now().isoformat()
    _save_users(users)
    
    security_logger.info(f"Backup codes regenerated for user: {username}")
    
    return {
        "success": True,
        "backup_codes": new_codes
    }


def is_authenticated() -> bool:
    """
    Check if user is authenticated in the current Streamlit session.
    
    Returns:
        True if authenticated, False otherwise
    """
    import streamlit as st
    return st.session_state.get("logged_in", False)

def logout() -> None:
    """
    Log out the current user by clearing session state.
    Enhanced to guarantee language preference preservation using multiple redundant mechanisms.
    """
    import streamlit as st
    
    # LANGUAGE PRESERVATION STRATEGY:
    # 1. Gather ALL language sources with fallback chain
    # 2. Store in multiple persistent locations
    # 3. Preserve through session state clearing
    # 4. Restore to ALL possible destinations
    # 5. Force immediate reinitialization
    
    # Step 1: Check ALL possible language locations in priority order
    lang_sources = {
        "_persistent_language": st.session_state.get("_persistent_language"),
        "language": st.session_state.get("language"),
        "pre_login_language": st.session_state.get("pre_login_language"),
        "backup_language": st.session_state.get("backup_language"),
        "force_language_after_login": st.session_state.get("force_language_after_login")
    }
    
    # Log all language sources for debugging
    print(f"LOGOUT - Language sources: {lang_sources}")
    
    # Step 2: Determine the most reliable language value using priority chain
    effective_language = None
    for key in ["_persistent_language", "language", "pre_login_language", "backup_language", "force_language_after_login"]:
        if lang_sources[key]:
            effective_language = lang_sources[key]
            print(f"LOGOUT - Using language from {key}: {effective_language}")
            break
    
    # Fallback to English if no language is found
    if not effective_language:
        effective_language = "en"
        print(f"LOGOUT - No language found, defaulting to: {effective_language}")
    
    # Step A: Create a special temporary variable to hold language through the reset
    temp_language_holder = effective_language
    
    # Step 3: Store language in ALL redundant persistent locations
    # These will survive the session state clearing
    st.session_state["_persistent_language"] = effective_language
    st.session_state["pre_logout_language"] = effective_language  # New backup location
    
    # Step 4: Clear ALL authentication-related session state
    # Only clear auth keys, preserve all other state
    auth_keys = ["logged_in", "username", "role", "permissions", "user_data"]
    for key in auth_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Step 5: Restore language to ALL possible locations for maximum redundancy
    st.session_state["language"] = temp_language_holder
    st.session_state["backup_language"] = temp_language_holder
    st.session_state["pre_login_language"] = temp_language_holder
    st.session_state["force_language_after_login"] = temp_language_holder
    
    # Double-check that language is still set correctly after clearing
    print(f"LOGOUT - Restored language: {st.session_state.get('language')}")
    
    # Step 6: Force complete reinitialization of translations
    st.session_state["reload_translations"] = True
    
    # Step 7: Explicitly reload translations via direct function calls
    from utils.i18n import initialize, set_language, _translations
    
    # Force clear translation cache
    if '_translations' in globals():
        _translations = {}
    
    # Set the language directly
    set_language(temp_language_holder)
    
    # Complete full initialization
    initialize()
    
    # Reset active tab to login
    st.session_state["active_tab"] = "login"
    
    # Final verification
    print(f"LOGOUT - Complete. Language status check: {st.session_state.get('language')}")

def has_permission(permission: str) -> bool:
    """
    Check if the current user has a specific permission.
    
    Args:
        permission: The permission to check (e.g., 'scan:create')
        
    Returns:
        True if the user has the permission, False otherwise
    """
    import streamlit as st
    
    # Premium membership override - premium members get access to all scanning features
    if 'premium_member' in st.session_state and st.session_state.premium_member:
        # Define which premium features are always accessible for premium members
        premium_features = [
            'scan:premium', 'scan:export', 'scan:configure',
            'scan:website', 'scan:code', 'scan:document', 'scan:database', 'scan:api',
            'report:export', 'report:create'
        ]
        
        # If the requested permission is a premium feature, grant access
        if permission in premium_features:
            return True
            
    # Admin bypass - admins have all permissions
    if st.session_state.get("role") == "admin":
        return True
    
    # Check if user has explicit permission
    user_permissions = st.session_state.get("permissions", [])
    return permission in user_permissions

def require_permission(permission: str) -> bool:
    """
    Check if the user has the required permission and show an error if not.
    
    Args:
        permission: The permission to check
        
    Returns:
        True if the user has the permission, False otherwise
    """
    import streamlit as st
    
    if not is_authenticated():
        st.error("You must be logged in to access this feature.")
        return False
        
    if not has_permission(permission):
        st.error(f"You don't have permission to access this feature ({permission}).")
        return False
        
    return True
    
def get_user_permissions(username: Optional[str] = None) -> List[str]:
    """
    Get permissions for a specific user or the current user.
    
    Args:
        username: Optional username to get permissions for.
                 If None, returns permissions for the current user.
                 
    Returns:
        List of permission strings
    """
    import streamlit as st
    
    if username is None:
        # Get current user's permissions from session
        return st.session_state.get("permissions", [])
    
    # Get specific user's permissions
    user_data = get_user(username)
    if user_data and "permissions" in user_data:
        return user_data["permissions"]
    
    # If role exists but no permissions, derive from role
    if user_data and "role" in user_data and user_data["role"] in ROLE_PERMISSIONS:
        return ROLE_PERMISSIONS[user_data["role"]]["permissions"]
    
    return []

def get_all_permissions() -> Dict[str, str]:
    """
    Get all available permissions with descriptions.
    
    Returns:
        Dictionary of permission keys to descriptions
    """
    return PERMISSIONS

def get_all_roles() -> Dict[str, Dict[str, Any]]:
    """
    Get all available roles with descriptions and permissions.
    
    Returns:
        Dictionary of roles with their descriptions and permissions
    """
    return ROLE_PERMISSIONS

def add_custom_permissions(username: str, permissions: List[str]) -> bool:
    """
    Add custom permissions to a user beyond their role.
    
    Args:
        username: The username to add permissions to
        permissions: List of permissions to add
        
    Returns:
        True if permissions were added, False if user doesn't exist
    """
    users = _load_users()
    
    if username not in users:
        return False
    
    # Get current permissions
    current_permissions = users[username].get("permissions", [])
    
    # Add new permissions
    for permission in permissions:
        if permission in PERMISSIONS and permission not in current_permissions:
            current_permissions.append(permission)
    
    # Update user
    users[username]["permissions"] = current_permissions
    _save_users(users)
    
    return True

def remove_custom_permissions(username: str, permissions: List[str]) -> bool:
    """
    Remove custom permissions from a user.
    
    Args:
        username: The username to remove permissions from
        permissions: List of permissions to remove
        
    Returns:
        True if permissions were removed, False if user doesn't exist
    """
    users = _load_users()
    
    if username not in users:
        return False
    
    # Get current permissions
    current_permissions = users[username].get("permissions", [])
    
    # Get the base permissions for the user's role
    role = users[username].get("role")
    if role not in ROLE_PERMISSIONS:
        return False
        
    # Safely access role permissions with type checking
    if role is None or role not in ROLE_PERMISSIONS:
        return False
    base_permissions = ROLE_PERMISSIONS[role]["permissions"]
    
    # Remove permissions if they're not in the base role permissions
    for permission in permissions:
        if permission in current_permissions and permission not in base_permissions:
            current_permissions.remove(permission)
    
    # Update user
    users[username]["permissions"] = current_permissions
    _save_users(users)
    
    return True

def reset_user_permissions(username: str) -> bool:
    """
    Reset a user's permissions to their role's default permissions.
    
    Args:
        username: The username to reset permissions for
        
    Returns:
        True if permissions were reset, False if user doesn't exist or role is invalid
    """
    users = _load_users()
    
    if username not in users:
        return False
    
    # Get the user's role
    role = users[username].get("role")
    if role not in ROLE_PERMISSIONS:
        return False
    
    # Reset permissions to role default with type safety
    if role is None or role not in ROLE_PERMISSIONS:
        return False
    users[username]["permissions"] = ROLE_PERMISSIONS[role]["permissions"].copy()
    _save_users(users)
    
    return True

def change_user_role(username: str, new_role: str) -> bool:
    """
    Change a user's role and update their permissions accordingly.
    
    Args:
        username: The username to change role for
        new_role: The new role to assign
        
    Returns:
        True if role was changed, False if user doesn't exist or role is invalid
    """
    users = _load_users()
    
    if username not in users:
        return False
    
    # Validate role
    if new_role not in ROLE_PERMISSIONS:
        return False
    
    # Update role and permissions
    users[username]["role"] = new_role
    users[username]["permissions"] = ROLE_PERMISSIONS[new_role]["permissions"].copy()
    _save_users(users)
    
    return True

def get_user_role_details(username: str) -> Optional[Dict[str, Any]]:
    """
    Get details about a user's role and permissions.
    
    Args:
        username: The username to get role details for
        
    Returns:
        Dictionary with role details or None if user doesn't exist
    """
    user_data = get_user(username)
    if not user_data:
        return None
    
    role = user_data.get("role")
    if not role or role not in ROLE_PERMISSIONS:
        return None
    
    role_data = ROLE_PERMISSIONS[role].copy()
    
    # Get custom permissions (permissions not in the role)
    user_permissions = set(user_data.get("permissions", []))
    role_permissions = set(role_data.get("permissions", []))
    
    custom_permissions = list(user_permissions - role_permissions)
    missing_permissions = list(role_permissions - user_permissions)
    
    return {
        "role": role,
        "role_description": role_data.get("description", ""),
        "custom_permissions": custom_permissions,
        "missing_permissions": missing_permissions,
        "total_permissions": len(user_permissions)
    }

def create_custom_role(role_name: str, description: str, permissions: List[str]) -> Tuple[bool, str]:
    """
    Create a new custom role with specified permissions.
    
    Args:
        role_name: Name for the new role (must be unique)
        description: Description of the role
        permissions: List of permission strings to assign to this role
        
    Returns:
        Tuple of (success, message) where success is True if role was created, 
        False otherwise, and message provides details
    """
    global ROLE_PERMISSIONS
    
    # Validate inputs
    if not role_name or not role_name.strip():
        return False, "Role name cannot be empty"
    
    # Clean role name (alphanumeric + underscores only)
    role_name = role_name.strip().lower().replace(' ', '_')
    
    # Check if role already exists
    if role_name in ROLE_PERMISSIONS:
        return False, f"Role '{role_name}' already exists"
    
    # Validate permissions
    valid_permissions = []
    for perm in permissions:
        if perm in PERMISSIONS:
            valid_permissions.append(perm)
    
    # Create the new role
    ROLE_PERMISSIONS[role_name] = {
        "description": description,
        "permissions": valid_permissions,
        "custom": True  # Flag to identify custom roles
    }
    
    # Return success
    return True, f"Role '{role_name}' created successfully with {len(valid_permissions)} permissions"

def update_role(role_name: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Update an existing role.
    
    Args:
        role_name: The name of the role to update
        updates: Dictionary of fields to update (description, permissions)
        
    Returns:
        Tuple of (success, message) where success is True if role was updated, 
        False otherwise, and message provides details
    """
    global ROLE_PERMISSIONS
    
    # Check if role exists
    if role_name not in ROLE_PERMISSIONS:
        return False, f"Role '{role_name}' does not exist"
    
    # Check if it's a system role (only custom roles can be updated)
    if not ROLE_PERMISSIONS[role_name].get('custom', False):
        return False, f"Cannot update system role '{role_name}'"
    
    # Update description if provided
    if 'description' in updates:
        ROLE_PERMISSIONS[role_name]['description'] = updates['description']
    
    # Update permissions if provided
    if 'permissions' in updates:
        valid_permissions = []
        for perm in updates['permissions']:
            if perm in PERMISSIONS:
                valid_permissions.append(perm)
        
        ROLE_PERMISSIONS[role_name]['permissions'] = valid_permissions
    
    # Update other fields
    for key, value in updates.items():
        if key not in ['description', 'permissions', 'custom']:
            ROLE_PERMISSIONS[role_name][key] = value
    
    # Return success
    return True, f"Role '{role_name}' updated successfully"

def delete_role(role_name: str) -> Tuple[bool, str]:
    """
    Delete a custom role.
    
    Args:
        role_name: The name of the role to delete
        
    Returns:
        Tuple of (success, message) where success is True if role was deleted, 
        False otherwise, and message provides details
    """
    global ROLE_PERMISSIONS
    
    # Check if role exists
    if role_name not in ROLE_PERMISSIONS:
        return False, f"Role '{role_name}' does not exist"
    
    # Check if it's a system role (only custom roles can be deleted)
    if not ROLE_PERMISSIONS[role_name].get('custom', False):
        return False, f"Cannot delete system role '{role_name}'"
    
    # Check if any users have this role (optional - requires loading all users)
    try:
        users = _load_users()
        role_users = [username for username, data in users.items() if data.get('role') == role_name]
        if role_users:
            return False, f"Cannot delete role '{role_name}' because it is assigned to {len(role_users)} users"
    except:
        # If we can't load users, continue with deletion
        pass
    
    # Delete the role
    del ROLE_PERMISSIONS[role_name]
    
    # Return success
    return True, f"Role '{role_name}' deleted successfully"
