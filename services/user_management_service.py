#!/usr/bin/env python3
"""
User Management Service for DataGuardian Pro
Comprehensive user CRUD, role management, usage tracking, and billing verification
"""

import os
import hashlib
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles with access levels"""
    ADMIN = "admin"
    USER = "user"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SECURITY_OFFICER = "security_officer"
    DATA_PROTECTION_OFFICER = "data_protection_officer"
    DEVELOPER = "developer"
    MANAGER = "manager"

class LicenseTier(Enum):
    """License tiers aligned with pricing"""
    TRIAL = "trial"
    STARTUP = "startup"           # €59/month - 200 scans
    PROFESSIONAL = "professional" # €99/month - 350 scans
    GROWTH = "growth"             # €179/month - 750 scans
    SCALE = "scale"               # €499/month - unlimited
    ENTERPRISE = "enterprise"     # €1,199/month - unlimited

TIER_LIMITS = {
    "trial": {
        "price_monthly": 0,
        "scans_per_month": 10,
        "users": 1,
        "scanners": ["document", "website"],
        "features": ["basic_pii_detection"],
        "api_access": False,
        "enterprise_connectors": False,
        "priority_support": False
    },
    "startup": {
        "price_monthly": 59,
        "scans_per_month": 200,
        "users": 3,
        "scanners": ["document", "website", "code", "database"],
        "features": ["basic_pii_detection", "gdpr_compliance", "reports"],
        "api_access": False,
        "enterprise_connectors": False,
        "priority_support": False
    },
    "professional": {
        "price_monthly": 99,
        "scans_per_month": 350,
        "users": 5,
        "scanners": ["document", "website", "code", "database", "image", "api"],
        "features": ["basic_pii_detection", "gdpr_compliance", "reports", "ai_analysis"],
        "api_access": True,
        "enterprise_connectors": False,
        "priority_support": False
    },
    "growth": {
        "price_monthly": 179,
        "scans_per_month": 750,
        "users": 10,
        "scanners": ["document", "website", "code", "database", "image", "api", "ai_model"],
        "features": ["basic_pii_detection", "gdpr_compliance", "reports", "ai_analysis", "dpia", "soc2"],
        "api_access": True,
        "enterprise_connectors": True,
        "priority_support": False
    },
    "scale": {
        "price_monthly": 499,
        "scans_per_month": -1,  # Unlimited
        "users": 25,
        "scanners": ["all"],
        "features": ["all"],
        "api_access": True,
        "enterprise_connectors": True,
        "priority_support": True
    },
    "enterprise": {
        "price_monthly": 1199,
        "scans_per_month": -1,  # Unlimited
        "users": -1,  # Unlimited
        "scanners": ["all"],
        "features": ["all"],
        "api_access": True,
        "enterprise_connectors": True,
        "priority_support": True
    }
}

ROLE_DESCRIPTIONS = {
    "admin": "Full system access with all permissions",
    "user": "Standard user with basic scanning and viewing permissions",
    "analyst": "Can create and analyze scans, generate reports",
    "viewer": "Read-only access to scans and reports",
    "security_officer": "Focused on security compliance and auditing",
    "data_protection_officer": "Focused on data protection and compliance reporting",
    "developer": "Technical role for API integration and development",
    "manager": "Oversees operations with metric visibility"
}

@dataclass
class User:
    """User data model"""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    role: str = "user"
    company_name: str = ""
    license_tier: str = "trial"
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    login_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    metadata: Dict = None

@dataclass
class FeatureUsage:
    """Feature usage tracking"""
    user_id: int
    feature_name: str
    feature_category: str
    usage_count: int = 1
    usage_date: date = None

@dataclass
class BillingRecord:
    """Billing compliance record"""
    user_id: int
    billing_period_start: date
    billing_period_end: date
    license_tier: str
    expected_amount: float
    actual_usage: Dict
    is_compliant: bool = True
    compliance_notes: str = ""

class UserManagementService:
    """Comprehensive user management service"""
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            # Fallback for old SHA256 hashes
            return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    # ==================== USER CRUD OPERATIONS ====================
    
    def create_user(self, username: str, email: str, password: str, 
                   role: str = "user", company_name: str = "", 
                   license_tier: str = "trial", created_by: str = None) -> Tuple[bool, str, Optional[int]]:
        """Create a new user"""
        try:
            password_hash = self._hash_password(password)
            
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO platform_users 
                        (username, email, password_hash, role, company_name, license_tier, created_by, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (username, email, password_hash, role, company_name, license_tier, created_by, json.dumps({})))
                    
                    user_id = cur.fetchone()['id']
                    conn.commit()
                    
                    self._log_activity(user_id, "user_created", f"User created by {created_by or 'system'}")
                    
                    logger.info(f"User created: {username} (ID: {user_id})")
                    return True, "User created successfully", user_id
                    
        except psycopg2.errors.UniqueViolation as e:
            if 'username' in str(e):
                return False, "Username already exists", None
            elif 'email' in str(e):
                return False, "Email already exists", None
            return False, "User already exists", None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, f"Error creating user: {str(e)}", None
    
    def get_user(self, user_id: int = None, username: str = None, email: str = None) -> Optional[Dict]:
        """Get user by ID, username, or email"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    if user_id:
                        cur.execute("SELECT * FROM platform_users WHERE id = %s", (user_id,))
                    elif username:
                        cur.execute("SELECT * FROM platform_users WHERE username = %s", (username,))
                    elif email:
                        cur.execute("SELECT * FROM platform_users WHERE email = %s", (email,))
                    else:
                        return None
                    
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def update_user(self, user_id: int, updates: Dict[str, Any], updated_by: str = None) -> Tuple[bool, str]:
        """Update user information"""
        try:
            allowed_fields = ['email', 'role', 'company_name', 'license_tier', 'is_active', 'is_verified', 'metadata']
            
            # Filter to allowed fields only
            valid_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not valid_updates:
                return False, "No valid fields to update"
            
            # Handle password separately
            if 'password' in updates and updates['password']:
                valid_updates['password_hash'] = self._hash_password(updates['password'])
            
            # Build update query
            set_clauses = [f"{k} = %s" for k in valid_updates.keys()]
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            
            values = list(valid_updates.values())
            values.append(user_id)
            
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        UPDATE platform_users 
                        SET {', '.join(set_clauses)}
                        WHERE id = %s
                    """, values)
                    conn.commit()
                    
                    self._log_activity(user_id, "user_updated", f"Updated fields: {list(valid_updates.keys())} by {updated_by or 'system'}")
                    
                    return True, "User updated successfully"
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False, f"Error updating user: {str(e)}"
    
    def delete_user(self, user_id: int, deleted_by: str = None) -> Tuple[bool, str]:
        """Delete user (soft delete by deactivating)"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Get username for logging
                    cur.execute("SELECT username FROM platform_users WHERE id = %s", (user_id,))
                    result = cur.fetchone()
                    if not result:
                        return False, "User not found"
                    
                    username = result['username']
                    
                    # Soft delete
                    cur.execute("""
                        UPDATE platform_users 
                        SET is_active = false, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (user_id,))
                    conn.commit()
                    
                    self._log_activity(user_id, "user_deleted", f"User {username} deactivated by {deleted_by or 'system'}")
                    
                    return True, "User deactivated successfully"
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False, f"Error deleting user: {str(e)}"
    
    def list_users(self, include_inactive: bool = False, 
                  role_filter: str = None, tier_filter: str = None,
                  limit: int = 100, offset: int = 0) -> List[Dict]:
        """List all users with optional filters"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    query = "SELECT * FROM platform_users WHERE 1=1"
                    params = []
                    
                    if not include_inactive:
                        query += " AND is_active = true"
                    
                    if role_filter:
                        query += " AND role = %s"
                        params.append(role_filter)
                    
                    if tier_filter:
                        query += " AND license_tier = %s"
                        params.append(tier_filter)
                    
                    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                    params.extend([limit, offset])
                    
                    cur.execute(query, params)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    def get_user_count(self, include_inactive: bool = False) -> Dict[str, int]:
        """Get user counts by role and tier"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    active_filter = "" if include_inactive else "WHERE is_active = true"
                    
                    # Total count
                    cur.execute(f"SELECT COUNT(*) as count FROM platform_users {active_filter}")
                    total = cur.fetchone()['count']
                    
                    # By role
                    cur.execute(f"""
                        SELECT role, COUNT(*) as count 
                        FROM platform_users {active_filter}
                        GROUP BY role
                    """)
                    by_role = {row['role']: row['count'] for row in cur.fetchall()}
                    
                    # By tier
                    cur.execute(f"""
                        SELECT license_tier, COUNT(*) as count 
                        FROM platform_users {active_filter}
                        GROUP BY license_tier
                    """)
                    by_tier = {row['license_tier']: row['count'] for row in cur.fetchall()}
                    
                    return {
                        'total': total,
                        'by_role': by_role,
                        'by_tier': by_tier
                    }
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            return {'total': 0, 'by_role': {}, 'by_tier': {}}
    
    # ==================== USAGE TRACKING ====================
    
    def track_feature_usage(self, user_id: int, feature_name: str, 
                           feature_category: str, metadata: Dict = None) -> bool:
        """Track feature usage for a user"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Upsert usage record
                    cur.execute("""
                        INSERT INTO feature_usage (user_id, feature_name, feature_category, usage_count, metadata)
                        VALUES (%s, %s, %s, 1, %s)
                        ON CONFLICT (user_id, feature_name, usage_date)
                        DO UPDATE SET usage_count = feature_usage.usage_count + 1,
                                     metadata = COALESCE(feature_usage.metadata, '{}'::jsonb) || %s::jsonb
                    """, (user_id, feature_name, feature_category, 
                          json.dumps(metadata or {}), json.dumps(metadata or {})))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error tracking feature usage: {e}")
            return False
    
    def get_user_usage(self, user_id: int, start_date: date = None, 
                      end_date: date = None) -> List[Dict]:
        """Get feature usage for a user"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT feature_name, feature_category, 
                               SUM(usage_count) as total_usage,
                               MIN(usage_date) as first_used,
                               MAX(usage_date) as last_used
                        FROM feature_usage 
                        WHERE user_id = %s
                    """
                    params = [user_id]
                    
                    if start_date:
                        query += " AND usage_date >= %s"
                        params.append(start_date)
                    
                    if end_date:
                        query += " AND usage_date <= %s"
                        params.append(end_date)
                    
                    query += " GROUP BY feature_name, feature_category ORDER BY total_usage DESC"
                    
                    cur.execute(query, params)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user usage: {e}")
            return []
    
    def get_usage_summary(self, user_id: int, period: str = "month") -> Dict:
        """Get usage summary for billing verification"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Determine date range
                    if period == "month":
                        start_date = date.today().replace(day=1)
                    elif period == "week":
                        start_date = date.today() - timedelta(days=7)
                    else:
                        start_date = date.today() - timedelta(days=30)
                    
                    # Get total scans
                    cur.execute("""
                        SELECT SUM(usage_count) as total_scans
                        FROM feature_usage 
                        WHERE user_id = %s 
                        AND feature_category = 'scanner'
                        AND usage_date >= %s
                    """, (user_id, start_date))
                    result = cur.fetchone()
                    total_scans = result['total_scans'] or 0
                    
                    # Get scanner breakdown
                    cur.execute("""
                        SELECT feature_name, SUM(usage_count) as count
                        FROM feature_usage 
                        WHERE user_id = %s 
                        AND feature_category = 'scanner'
                        AND usage_date >= %s
                        GROUP BY feature_name
                    """, (user_id, start_date))
                    scanner_breakdown = {row['feature_name']: row['count'] for row in cur.fetchall()}
                    
                    # Get feature usage
                    cur.execute("""
                        SELECT feature_name, SUM(usage_count) as count
                        FROM feature_usage 
                        WHERE user_id = %s 
                        AND feature_category = 'feature'
                        AND usage_date >= %s
                        GROUP BY feature_name
                    """, (user_id, start_date))
                    feature_breakdown = {row['feature_name']: row['count'] for row in cur.fetchall()}
                    
                    return {
                        'period': period,
                        'start_date': start_date.isoformat(),
                        'total_scans': total_scans,
                        'scanner_breakdown': scanner_breakdown,
                        'feature_breakdown': feature_breakdown
                    }
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {'period': period, 'total_scans': 0, 'scanner_breakdown': {}, 'feature_breakdown': {}}
    
    # ==================== BILLING VERIFICATION ====================
    
    def verify_billing_compliance(self, user_id: int) -> Dict:
        """Verify if user's usage matches their billing tier"""
        try:
            user = self.get_user(user_id=user_id)
            if not user:
                return {'compliant': False, 'error': 'User not found'}
            
            tier = user['license_tier']
            tier_limits = TIER_LIMITS.get(tier, TIER_LIMITS['trial'])
            
            usage = self.get_usage_summary(user_id, "month")
            
            # Check scan limits
            scan_limit = tier_limits['scans_per_month']
            total_scans = usage.get('total_scans', 0)
            
            is_compliant = True
            issues = []
            
            if scan_limit != -1 and total_scans > scan_limit:
                is_compliant = False
                issues.append(f"Scan limit exceeded: {total_scans}/{scan_limit}")
            
            # Check scanner access
            allowed_scanners = tier_limits['scanners']
            if 'all' not in allowed_scanners:
                used_scanners = set(usage.get('scanner_breakdown', {}).keys())
                unauthorized = used_scanners - set(allowed_scanners)
                if unauthorized:
                    is_compliant = False
                    issues.append(f"Unauthorized scanners used: {unauthorized}")
            
            # Calculate usage percentage
            usage_percentage = (total_scans / scan_limit * 100) if scan_limit > 0 else 0
            
            return {
                'user_id': user_id,
                'username': user['username'],
                'tier': tier,
                'tier_price': tier_limits['price_monthly'],
                'compliant': is_compliant,
                'issues': issues,
                'scan_usage': {
                    'used': total_scans,
                    'limit': scan_limit if scan_limit != -1 else 'Unlimited',
                    'percentage': round(usage_percentage, 1) if scan_limit > 0 else 0
                },
                'recommended_tier': self._recommend_tier(total_scans, usage) if not is_compliant else tier
            }
        except Exception as e:
            logger.error(f"Error verifying billing compliance: {e}")
            return {'compliant': False, 'error': str(e)}
    
    def _recommend_tier(self, total_scans: int, usage: Dict) -> str:
        """Recommend appropriate tier based on usage"""
        for tier_name, limits in TIER_LIMITS.items():
            if limits['scans_per_month'] == -1:
                return tier_name
            if total_scans <= limits['scans_per_month']:
                return tier_name
        return 'enterprise'
    
    def generate_billing_report(self, start_date: date = None, end_date: date = None) -> List[Dict]:
        """Generate billing compliance report for all users"""
        try:
            users = self.list_users(include_inactive=False)
            report = []
            
            for user in users:
                compliance = self.verify_billing_compliance(user['id'])
                compliance['email'] = user['email']
                compliance['company'] = user.get('company_name', '')
                compliance['last_login'] = user.get('last_login')
                report.append(compliance)
            
            return report
        except Exception as e:
            logger.error(f"Error generating billing report: {e}")
            return []
    
    # ==================== ACTIVITY LOGGING ====================
    
    def _log_activity(self, user_id: int, action_type: str, 
                     action_details: str = None, ip_address: str = None):
        """Log user activity"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_activity_log 
                        (user_id, action_type, action_details, ip_address)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, action_type, action_details, ip_address))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def get_user_activity(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get recent activity for a user"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT action_type, action_details, ip_address, created_at
                        FROM user_activity_log
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return []
    
    def record_login(self, user_id: int, ip_address: str = None):
        """Record user login"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE platform_users 
                        SET last_login = CURRENT_TIMESTAMP, 
                            login_count = login_count + 1
                        WHERE id = %s
                    """, (user_id,))
                    conn.commit()
                    
                    self._log_activity(user_id, "login", "User logged in", ip_address)
        except Exception as e:
            logger.error(f"Error recording login: {e}")
    
    # ==================== TIER MANAGEMENT ====================
    
    def get_tier_info(self, tier: str) -> Dict:
        """Get information about a license tier"""
        return TIER_LIMITS.get(tier, TIER_LIMITS['trial'])
    
    def get_all_tiers(self) -> Dict:
        """Get all available tiers"""
        return TIER_LIMITS
    
    def get_all_roles(self) -> Dict:
        """Get all available roles with descriptions"""
        return ROLE_DESCRIPTIONS
    
    def can_access_feature(self, user_id: int, feature: str) -> bool:
        """Check if user can access a feature based on their tier"""
        user = self.get_user(user_id=user_id)
        if not user:
            return False
        
        tier = user['license_tier']
        tier_limits = TIER_LIMITS.get(tier, TIER_LIMITS['trial'])
        
        if 'all' in tier_limits.get('features', []):
            return True
        
        return feature in tier_limits.get('features', [])
    
    def can_use_scanner(self, user_id: int, scanner: str) -> bool:
        """Check if user can use a scanner based on their tier"""
        user = self.get_user(user_id=user_id)
        if not user:
            return False
        
        tier = user['license_tier']
        tier_limits = TIER_LIMITS.get(tier, TIER_LIMITS['trial'])
        
        if 'all' in tier_limits.get('scanners', []):
            return True
        
        return scanner in tier_limits.get('scanners', [])
    
    def get_remaining_scans(self, user_id: int) -> Dict:
        """Get remaining scans for the current billing period"""
        user = self.get_user(user_id=user_id)
        if not user:
            return {'remaining': 0, 'limit': 0, 'used': 0}
        
        tier = user['license_tier']
        tier_limits = TIER_LIMITS.get(tier, TIER_LIMITS['trial'])
        scan_limit = tier_limits['scans_per_month']
        
        usage = self.get_usage_summary(user_id, "month")
        used = usage.get('total_scans', 0)
        
        if scan_limit == -1:
            return {'remaining': 'Unlimited', 'limit': 'Unlimited', 'used': used}
        
        return {
            'remaining': max(0, scan_limit - used),
            'limit': scan_limit,
            'used': used
        }

    def export_users_csv(self) -> str:
        """Export all users to CSV format"""
        users = self.list_users(include_inactive=True)
        if not users:
            return ""
        
        headers = ['ID', 'Username', 'Email', 'Role', 'Company', 'License Tier', 
                  'Active', 'Last Login', 'Login Count', 'Created At']
        
        rows = [','.join(headers)]
        for user in users:
            row = [
                str(user['id']),
                user['username'],
                user['email'],
                user['role'],
                user.get('company_name', ''),
                user['license_tier'],
                str(user['is_active']),
                str(user.get('last_login', '')),
                str(user.get('login_count', 0)),
                str(user.get('created_at', ''))
            ]
            rows.append(','.join(f'"{v}"' for v in row))
        
        return '\n'.join(rows)


# Singleton instance
_user_management_service = None

def get_user_management_service() -> UserManagementService:
    """Get singleton instance of UserManagementService"""
    global _user_management_service
    if _user_management_service is None:
        _user_management_service = UserManagementService()
    return _user_management_service
