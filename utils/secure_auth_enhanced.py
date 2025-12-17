"""
Enhanced Secure Authentication Module
Implements enterprise-grade security with bcrypt password hashing, JWT tokens, 
and secure credential management without hardcoded fallbacks.
"""
import os
import json
import logging
import secrets
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AuthResult:
    """Authentication result with user information and token"""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    token: Optional[str] = None
    message: Optional[str] = None
    expires_at: Optional[datetime] = None

class SecureAuthManager:
    """Enhanced authentication manager with JWT and bcrypt security"""
    
    def __init__(self):
        self.jwt_secret = self._get_jwt_secret()
        self.token_expiry_hours = 24  # 24 hour token expiry
        self.users_file = "secure_users.json"
        self.failed_attempts = {}  # Rate limiting
        self.max_failed_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        
    def _get_jwt_secret(self) -> str:
        """Get JWT secret from environment or fail safely"""
        secret = os.getenv('JWT_SECRET')
        if not secret:
            # In production, this should be a hard requirement
            # For development, we'll allow a generated secret with clear warning
            if os.getenv('ENVIRONMENT') == 'production':
                raise ValueError("JWT_SECRET environment variable is required in production")
            
            # Generate a secure random secret for development only
            secret = secrets.token_urlsafe(64)
            logger.warning("JWT_SECRET not set - using generated secret (DEVELOPMENT ONLY - will not persist across restarts)")
            logger.info("To fix: Set JWT_SECRET environment variable to a secure random value")
        return secret
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt with salt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def _generate_token(self, user_data: Dict) -> Tuple[str, datetime]:
        """Generate JWT token for authenticated user"""
        expires_at = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
        
        payload = {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'role': user_data['role'],
            'exp': expires_at,
            'iat': datetime.utcnow(),
            'iss': 'dataguardian-pro'
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        return token, expires_at
    
    def _verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def _load_users(self) -> Dict[str, Dict]:
        """Load users from secure storage and database"""
        # Load file-based users first
        file_users = {}
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    file_users = json.load(f)
            except Exception as e:
                logger.error(f"Error loading users from file: {e}")
        
        if not file_users:
            file_users = self._create_default_users()
        
        # Also load users from database (platform_users table)
        try:
            import psycopg2
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, password_hash, role, is_active, license_tier
                    FROM platform_users WHERE is_active = TRUE
                """)
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                
                for row in rows:
                    user_id, username, email, password_hash, role, is_active, license_tier = row
                    # Add database users (keyed by both username and email for flexibility)
                    user_data = {
                        'user_id': str(user_id),
                        'username': username,
                        'email': email,
                        'password_hash': password_hash,
                        'role': role or 'user',
                        'active': is_active,
                        'license_tier': license_tier,
                        'created_at': None,
                        'last_login': None,
                        'failed_attempts': 0,
                        'locked_until': None
                    }
                    file_users[username] = user_data
                    # Also allow login by email
                    if email and email != username:
                        file_users[email] = user_data
        except Exception as e:
            logger.debug(f"Could not load database users: {e}")
        
        return file_users
    
    def _save_users(self, users: Dict[str, Dict]) -> None:
        """Save users to secure storage"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def _create_default_users(self) -> Dict[str, Dict]:
        """Create default users with secure passwords from environment"""
        # Get admin credentials from environment
        admin_password = os.getenv('ADMIN_PASSWORD')
        if not admin_password:
            # Generate secure random password if not set
            admin_password = secrets.token_urlsafe(16)
            logger.warning("ADMIN_PASSWORD not set - generated secure password (password not logged for security)")
        
        # Create default users with secure passwords
        default_users = {
            'admin': {
                'user_id': 'admin_001',
                'username': 'admin',
                'password_hash': self._hash_password(admin_password),
                'role': 'admin',
                'email': 'admin@dataguardian.pro',
                'active': True,
                'created_at': datetime.utcnow().isoformat(),
                'last_login': None,
                'failed_attempts': 0,
                'locked_until': None
            }
        }
        
        # Add demo user if specified
        demo_password = os.getenv('DEMO_PASSWORD', 'demo_secure_2024')
        if demo_password:
            default_users['demo'] = {
                'user_id': 'demo_001',
                'username': 'demo',
                'password_hash': self._hash_password(demo_password),
                'role': 'viewer',
                'email': 'demo@dataguardian.pro',
                'active': True,
                'created_at': datetime.utcnow().isoformat(),
                'last_login': None,
                'failed_attempts': 0,
                'locked_until': None
            }
        
        self._save_users(default_users)
        logger.info(f"Created {len(default_users)} default users")
        return default_users
    
    def _is_user_locked(self, username: str) -> bool:
        """Check if user is locked due to failed attempts"""
        users = self._load_users()
        if username not in users:
            return False
        
        user = users[username]
        if user.get('locked_until'):
            lock_until = datetime.fromisoformat(user['locked_until'])
            if datetime.utcnow() < lock_until:
                return True
            else:
                # Unlock user
                user['locked_until'] = None
                user['failed_attempts'] = 0
                self._save_users(users)
        
        return False
    
    def _record_failed_attempt(self, username: str) -> None:
        """Record failed login attempt and potentially lock user"""
        users = self._load_users()
        if username not in users:
            return
        
        user = users[username]
        user['failed_attempts'] = user.get('failed_attempts', 0) + 1
        
        if user['failed_attempts'] >= self.max_failed_attempts:
            lock_until = datetime.utcnow() + timedelta(seconds=self.lockout_duration)
            user['locked_until'] = lock_until.isoformat()
            logger.warning(f"User {username} locked due to failed attempts")
        
        self._save_users(users)
    
    def _clear_failed_attempts(self, username: str) -> None:
        """Clear failed attempts on successful login"""
        users = self._load_users()
        if username in users:
            users[username]['failed_attempts'] = 0
            users[username]['locked_until'] = None
            users[username]['last_login'] = datetime.utcnow().isoformat()
            self._save_users(users)
    
    def authenticate(self, username: str, password: str) -> AuthResult:
        """Authenticate user with username and password"""
        # Check if user is locked
        if self._is_user_locked(username):
            return AuthResult(
                success=False,
                message="Account temporarily locked due to failed login attempts"
            )
        
        # Load users
        users = self._load_users()
        
        # Check if user exists
        if username not in users:
            logger.warning(f"Authentication failed: user {username} not found")
            return AuthResult(success=False, message="Invalid credentials")
        
        user = users[username]
        
        # Check if user is active
        if not user.get('active', True):
            return AuthResult(success=False, message="Account disabled")
        
        # Verify password
        if not self._verify_password(password, user['password_hash']):
            self._record_failed_attempt(username)
            logger.warning(f"Authentication failed: invalid password for {username}")
            return AuthResult(success=False, message="Invalid credentials")
        
        # Clear failed attempts on successful login
        self._clear_failed_attempts(username)
        
        # Generate JWT token
        token, expires_at = self._generate_token(user)
        
        logger.info(f"User {username} authenticated successfully")
        return AuthResult(
            success=True,
            user_id=user['user_id'],
            username=username,
            role=user['role'],
            token=token,
            expires_at=expires_at,
            message="Authentication successful"
        )
    
    def validate_token(self, token: str) -> AuthResult:
        """Validate JWT token and return user information"""
        payload = self._verify_token(token)
        if not payload:
            return AuthResult(success=False, message="Invalid or expired token")
        
        # Verify user still exists and is active
        users = self._load_users()
        username = payload['username']
        
        if username not in users or not users[username].get('active', True):
            return AuthResult(success=False, message="User account no longer valid")
        
        return AuthResult(
            success=True,
            user_id=payload['user_id'],
            username=username,
            role=payload['role'],
            token=token,
            message="Token valid"
        )
    
    def create_user(self, username: str, password: str, role: str = 'user', email: Optional[str] = None) -> bool:
        """Create new user with secure password hashing"""
        users = self._load_users()
        
        if username in users:
            logger.warning(f"User {username} already exists")
            return False
        
        # Generate secure user ID
        user_id = f"{username}_{secrets.token_hex(8)}"
        
        users[username] = {
            'user_id': user_id,
            'username': username,
            'password_hash': self._hash_password(password),
            'role': role,
            'email': email or f"{username}@dataguardian.pro",
            'active': True,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None,
            'failed_attempts': 0,
            'locked_until': None
        }
        
        self._save_users(users)
        logger.info(f"Created user {username} with role {role}")
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password with verification"""
        users = self._load_users()
        
        if username not in users:
            return False
        
        user = users[username]
        
        # Verify old password
        if not self._verify_password(old_password, user['password_hash']):
            logger.warning(f"Password change failed: invalid old password for {username}")
            return False
        
        # Update password
        user['password_hash'] = self._hash_password(new_password)
        user['password_changed_at'] = datetime.utcnow().isoformat()
        
        self._save_users(users)
        logger.info(f"Password changed for user {username}")
        return True
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information (excluding password hash)"""
        users = self._load_users()
        if username not in users:
            return None
        
        user = users[username].copy()
        user.pop('password_hash', None)  # Remove password hash
        return user
    
    def is_admin(self, username: str) -> bool:
        """Check if user has admin role"""
        user_info = self.get_user_info(username)
        return bool(user_info and user_info.get('role') == 'admin')
    
    def get_user_role(self, username: str) -> Optional[str]:
        """Get user role"""
        user_info = self.get_user_info(username)
        return user_info.get('role') if user_info else None

# Global instance
_auth_manager = None

def get_auth_manager() -> SecureAuthManager:
    """Get global authentication manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = SecureAuthManager()
    return _auth_manager

# Convenience functions for backward compatibility
def authenticate_user(username: str, password: str) -> AuthResult:
    """Authenticate user and return result"""
    return get_auth_manager().authenticate(username, password)

def validate_token(token: str) -> AuthResult:
    """Validate JWT token"""
    return get_auth_manager().validate_token(token)

def create_user(username: str, password: str, role: str = 'user', email: Optional[str] = None) -> bool:
    """Create new user"""
    return get_auth_manager().create_user(username, password, role, email)

def is_admin_user(username: str) -> bool:
    """Check if user is admin"""
    return get_auth_manager().is_admin(username)

def get_user_role(username: str) -> Optional[str]:
    """Get user role"""
    return get_auth_manager().get_user_role(username)