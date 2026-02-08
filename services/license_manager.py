#!/usr/bin/env python3
"""
Copyright (c) 2025 DataGuardian Pro B.V.
All rights reserved.

CONFIDENTIAL AND PROPRIETARY - DataGuardian Pro™ License Manager
This software contains trade secrets and proprietary algorithms for license 
validation and intellectual property protection.

Patent Pending: Netherlands Patent Application #NL2025002 (License Security System)
Trademark: DataGuardian Pro™ is a trademark of DataGuardian Pro B.V.

UNAUTHORIZED ACCESS PROHIBITED
Any attempt to reverse engineer, decompile, or circumvent the license protection
mechanisms is strictly prohibited and may result in legal prosecution under
Netherlands copyright law.

Licensed under DataGuardian Pro Commercial License Agreement.
For licensing inquiries: legal@dataguardianpro.nl
"""

"""
License Manager for DataGuardian Pro
Comprehensive licensing and usage control system
"""

import os
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

class LicenseType(Enum):
    """License types aligned with pricing tiers"""
    TRIAL = "trial"
    STARTUP = "startup"           # €59/month - 200 scans
    PROFESSIONAL = "professional" # €99/month - 350 scans (new tier)
    GROWTH = "growth"             # €179/month - 750 scans
    SCALE = "scale"               # €499/month - unlimited
    ENTERPRISE = "enterprise"     # €1,199/month - unlimited
    GOVERNMENT = "government"     # €15,000 one-time
    # Legacy types for backward compatibility
    BASIC = "basic"              # Maps to startup
    ENTERPRISE_PLUS = "enterprise_plus"  # Maps to government
    CONSULTANCY = "consultancy"
    AI_COMPLIANCE = "ai_compliance"
    STANDALONE = "standalone"
    SAAS = "saas"
    CUSTOM = "custom"

class UsageLimitType(Enum):
    """Types of usage limits"""
    SCANS_PER_MONTH = "scans_per_month"
    SCANS_PER_DAY = "scans_per_day"
    CONCURRENT_USERS = "concurrent_users"
    API_CALLS = "api_calls"
    STORAGE_MB = "storage_mb"
    EXPORT_REPORTS = "export_reports"
    SCANNER_TYPES = "scanner_types"
    REGIONS = "regions"

@dataclass
class UsageLimit:
    """Usage limit configuration"""
    limit_type: UsageLimitType
    limit_value: int
    current_usage: int = 0
    reset_period: str = "monthly"  # daily, weekly, monthly, yearly
    last_reset: Optional[datetime] = None

@dataclass
class LicenseConfig:
    """License configuration"""
    license_id: str
    license_type: LicenseType
    customer_id: str
    customer_name: str
    company_name: str
    email: str
    issued_date: datetime
    expiry_date: datetime
    usage_limits: List[UsageLimit]
    allowed_features: List[str]
    allowed_scanners: List[str]
    allowed_regions: List[str]
    max_concurrent_users: int
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None

class LicenseManager:
    """Comprehensive license management system"""
    
    def __init__(self, license_file: str = "license.json", encrypt_license: bool = False):
        self.license_file = license_file
        self.encrypt_license = encrypt_license
        self.current_license: Optional[LicenseConfig] = None
        self.usage_tracker: Dict[str, Any] = {}
        self.session_tracker: Dict[str, datetime] = {}
        
        # Generate or load encryption key only if encryption is enabled
        if self.encrypt_license:
            self.encryption_key = self._get_encryption_key()
        
        # Load existing license
        self.load_license()
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate hardware-based encryption key with tamper protection"""
        key_file = ".license_key"
        hardware_id = self._get_hardware_fingerprint()
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                stored_key = f.read()
            
            # Verify key integrity with hardware fingerprint
            if not self._verify_key_integrity(stored_key, hardware_id):
                logger.warning("License key integrity violation detected")
                raise Exception("License tamper detected - contact legal@dataguardianpro.nl")
            
            return stored_key
        else:
            # Generate hardware-bound encryption key
            key = self._generate_hardware_bound_key(hardware_id)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _get_hardware_fingerprint(self) -> str:
        """Generate unique hardware fingerprint for license binding"""
        import platform
        import psutil
        
        # Collect hardware identifiers
        system_info = [
            platform.machine(),
            platform.processor(),
            str(psutil.virtual_memory().total),
            platform.system(),
            platform.release()
        ]
        
        # Create stable fingerprint
        fingerprint_data = '|'.join(system_info)
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
    
    def _generate_hardware_bound_key(self, hardware_id: str) -> bytes:
        """Generate encryption key bound to hardware"""
        base_key = Fernet.generate_key()
        hw_salt = hashlib.sha256(hardware_id.encode()).digest()[:16]
        
        # Combine base key with hardware salt
        combined = base_key + hw_salt
        return combined
    
    def _verify_key_integrity(self, key: bytes, hardware_id: str) -> bool:
        """Verify key was generated for this hardware"""
        if len(key) < 48:  # 32 (Fernet key) + 16 (hw salt)
            return False
        
        hw_salt = key[32:48]
        expected_salt = hashlib.sha256(hardware_id.encode()).digest()[:16]
        
        return hw_salt == expected_salt
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt license data"""
        if not self.encrypt_license:
            return data
        
        f = Fernet(self.encryption_key)
        encrypted = f.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt license data"""
        if not self.encrypt_license:
            return encrypted_data
        
        try:
            f = Fernet(self.encryption_key)
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = f.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt license data: {e}")
            return ""
    
    def generate_license(self, 
                        license_type: LicenseType,
                        customer_id: str,
                        customer_name: str,
                        company_name: str,
                        email: str,
                        validity_days: int = 365,
                        custom_limits: Optional[Dict[str, int]] = None) -> LicenseConfig:
        """Generate a new license"""
        
        # Usage limits aligned with optimized pricing tiers
        default_limits = {
            LicenseType.TRIAL: {
                UsageLimitType.SCANS_PER_MONTH: 10,
                UsageLimitType.CONCURRENT_USERS: 1,
                UsageLimitType.EXPORT_REPORTS: 5,
                UsageLimitType.SCANNER_TYPES: 3
            },
            LicenseType.STARTUP: {  # €59/month tier
                UsageLimitType.SCANS_PER_MONTH: 200,
                UsageLimitType.CONCURRENT_USERS: 5,
                UsageLimitType.EXPORT_REPORTS: 50,
                UsageLimitType.SCANNER_TYPES: 6  # code, document, database, image, website, ai_model
            },
            LicenseType.PROFESSIONAL: {  # €99/month tier
                UsageLimitType.SCANS_PER_MONTH: 350,
                UsageLimitType.CONCURRENT_USERS: 10,
                UsageLimitType.EXPORT_REPORTS: 100,
                UsageLimitType.SCANNER_TYPES: 8  # +dpia, soc2
            },
            LicenseType.GROWTH: {  # €179/month tier
                UsageLimitType.SCANS_PER_MONTH: 750,
                UsageLimitType.CONCURRENT_USERS: 25,
                UsageLimitType.EXPORT_REPORTS: 250,
                UsageLimitType.SCANNER_TYPES: 10  # +enterprise, sustainability
            },
            LicenseType.SCALE: {  # €499/month tier
                UsageLimitType.SCANS_PER_MONTH: 999999,  # Unlimited
                UsageLimitType.CONCURRENT_USERS: 100,
                UsageLimitType.EXPORT_REPORTS: 999999,  # Unlimited
                UsageLimitType.SCANNER_TYPES: 12  # All scanners: +audio_video, advanced_ai
            },
            LicenseType.ENTERPRISE: {  # €1,399/month tier
                UsageLimitType.SCANS_PER_MONTH: 999999,  # Unlimited
                UsageLimitType.CONCURRENT_USERS: 999999,  # Unlimited
                UsageLimitType.EXPORT_REPORTS: 999999,  # Unlimited
                UsageLimitType.SCANNER_TYPES: 12  # All 12 scanners
            },
            LicenseType.GOVERNMENT: {  # €15,000 one-time
                UsageLimitType.SCANS_PER_MONTH: 999999,  # Unlimited
                UsageLimitType.CONCURRENT_USERS: 999999,  # Unlimited
                UsageLimitType.EXPORT_REPORTS: 999999,  # Unlimited
                UsageLimitType.SCANNER_TYPES: 12  # All 12 scanners
            },
            # Backward compatibility mappings
            LicenseType.BASIC: {  # Maps to startup
                UsageLimitType.SCANS_PER_MONTH: 200,
                UsageLimitType.CONCURRENT_USERS: 5,
                UsageLimitType.EXPORT_REPORTS: 50,
                UsageLimitType.SCANNER_TYPES: 8
            },
            LicenseType.ENTERPRISE_PLUS: {  # Maps to government
                UsageLimitType.SCANS_PER_MONTH: 999999,
                UsageLimitType.CONCURRENT_USERS: 999999,
                UsageLimitType.EXPORT_REPORTS: 999999,
                UsageLimitType.SCANNER_TYPES: 10
            },
            LicenseType.CONSULTANCY: {
                UsageLimitType.SCANS_PER_MONTH: 500,
                UsageLimitType.CONCURRENT_USERS: 25,
                UsageLimitType.EXPORT_REPORTS: 999999,
                UsageLimitType.SCANNER_TYPES: 10
            },
            LicenseType.AI_COMPLIANCE: {
                UsageLimitType.SCANS_PER_MONTH: 999999,
                UsageLimitType.CONCURRENT_USERS: 20,
                UsageLimitType.EXPORT_REPORTS: 999999,
                UsageLimitType.SCANNER_TYPES: 10
            },
            LicenseType.STANDALONE: {
                UsageLimitType.SCANS_PER_MONTH: 999999,
                UsageLimitType.CONCURRENT_USERS: 999999,
                UsageLimitType.EXPORT_REPORTS: 999999,
                UsageLimitType.SCANNER_TYPES: 10
            }
        }
        
        # Create usage limits
        limits = default_limits.get(license_type, default_limits[LicenseType.TRIAL]).copy()
        if custom_limits:
            for limit_type, limit_value in custom_limits.items():
                if isinstance(limit_type, str):
                    # Convert string to UsageLimitType enum
                    limit_type = UsageLimitType(limit_type)
                limits[limit_type] = limit_value
        
        usage_limits = []
        for limit_type, limit_value in limits.items():
            usage_limits.append(UsageLimit(
                limit_type=limit_type,
                limit_value=limit_value,
                current_usage=0,
                reset_period="monthly",
                last_reset=datetime.now()
            ))
        
        # Define features and scanners based on license type
        all_features = [
            "code_scanner", "document_scanner", "image_scanner", "database_scanner",
            "api_scanner", "ai_model_scanner", "website_scanner", "soc2_scanner",
            "dpia_scanner", "sustainability_scanner", "reporting", "audit_trail",
            "compliance_dashboard", "multi_region", "api_access", "white_label"
        ]
        
        # 12 Scanners ordered by tier availability
        # Core (all tiers): code, document, database, image, website, ai_model
        # Professional+: dpia, soc2
        # Growth+: enterprise, sustainability
        # Scale+: audio_video, advanced_ai
        all_scanners = [
            "code", "document", "database", "image", "website", "ai_model",
            "dpia", "soc2", "enterprise", "sustainability", "audio_video",
            "data_sovereignty", "api", "advanced_ai"
        ]
        
        all_regions = ["Netherlands", "Germany", "France", "Belgium", "EU", "Global"]
        
        # Configure features aligned with pricing tiers (12 scanners total)
        if license_type == LicenseType.TRIAL:
            allowed_features = all_features[:6]  # Limited trial features
            allowed_scanners = all_scanners[:3]  # 3 scanners: code, document, database
            allowed_regions = ["Netherlands"]
            max_concurrent = 1
        elif license_type == LicenseType.STARTUP:
            allowed_features = all_features[:10]  # Enhanced startup features with AI Act
            allowed_scanners = all_scanners[:6]  # 6 scanners: +image, website, ai_model
            allowed_regions = ["Netherlands", "Belgium"]
            max_concurrent = 5
        elif license_type == LicenseType.PROFESSIONAL:
            allowed_features = all_features[:12]  # Professional Plus features
            allowed_scanners = all_scanners[:8]  # 8 scanners: +dpia, soc2
            allowed_regions = ["Netherlands", "Germany", "Belgium", "France"]
            max_concurrent = 10
        elif license_type == LicenseType.GROWTH:
            allowed_features = all_features[:14]  # Growth Professional features
            allowed_scanners = all_scanners[:10]  # 10 scanners: +enterprise, sustainability
            allowed_regions = ["Netherlands", "Germany", "Belgium", "France", "EU"]
            max_concurrent = 25
        elif license_type == LicenseType.SCALE:
            allowed_features = all_features[:15]  # Scale Enterprise with API access
            allowed_scanners = all_scanners  # All 12 scanners: +audio_video, advanced_ai
            allowed_regions = all_regions  # Global access
            max_concurrent = 100
        elif license_type == LicenseType.ENTERPRISE:
            allowed_features = all_features  # All features including white-label
            allowed_scanners = all_scanners  # All 12 scanners
            allowed_regions = all_regions  # Global access
            max_concurrent = 999999  # Unlimited
        elif license_type == LicenseType.GOVERNMENT:
            allowed_features = all_features  # All features + source code access
            allowed_scanners = all_scanners  # All scanners
            allowed_regions = all_regions  # Global access
            max_concurrent = 999999  # Unlimited
        # Backward compatibility
        elif license_type == LicenseType.BASIC:
            allowed_features = all_features[:10]  # Maps to startup
            allowed_scanners = all_scanners[:6]
            allowed_regions = ["Netherlands", "Belgium"]
            max_concurrent = 5
        elif license_type == LicenseType.ENTERPRISE_PLUS:
            allowed_features = all_features  # Maps to government
            allowed_scanners = all_scanners
            allowed_regions = all_regions
            max_concurrent = 999999
        elif license_type == LicenseType.CONSULTANCY:
            allowed_features = all_features  # All features for client work
            allowed_scanners = all_scanners  # All scanners
            allowed_regions = all_regions  # Global access for clients
            max_concurrent = 25
        elif license_type == LicenseType.AI_COMPLIANCE:
            allowed_features = all_features  # All features with AI focus
            allowed_scanners = all_scanners  # All scanners especially AI
            allowed_regions = all_regions  # Global AI compliance
            max_concurrent = 20
        else:  # STANDALONE
            allowed_features = all_features
            allowed_scanners = all_scanners
            allowed_regions = all_regions
            max_concurrent = 999999
        
        # Generate license
        license_config = LicenseConfig(
            license_id=str(uuid.uuid4()),
            license_type=license_type,
            customer_id=customer_id,
            customer_name=customer_name,
            company_name=company_name,
            email=email,
            issued_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=validity_days),
            usage_limits=usage_limits,
            allowed_features=allowed_features,
            allowed_scanners=allowed_scanners,
            allowed_regions=allowed_regions,
            max_concurrent_users=max_concurrent,
            is_active=True,
            metadata={
                "generated_by": "DataGuardian Pro License Manager",
                "version": "1.0",
                "hardware_id": self._get_hardware_id(),
                "creation_timestamp": datetime.now().isoformat()
            }
        )
        
        return license_config
    
    def _get_hardware_id(self) -> str:
        """Generate hardware-specific ID for license binding"""
        import platform
        import subprocess
        
        # Get system information
        system_info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "node": platform.node()
        }
        
        # Try to get MAC address
        try:
            import uuid
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                                  for i in range(0, 8*6, 8)][::-1])
            system_info["mac"] = mac_address
        except:
            pass
        
        # Create hash of system info
        info_string = json.dumps(system_info, sort_keys=True)
        return hashlib.sha256(info_string.encode()).hexdigest()[:16]
    
    def save_license(self, license_config: LicenseConfig) -> bool:
        """Save license to file"""
        try:
            # Convert to dictionary
            license_dict = {
                "license_id": license_config.license_id,
                "license_type": license_config.license_type.value,
                "customer_id": license_config.customer_id,
                "customer_name": license_config.customer_name,
                "company_name": license_config.company_name,
                "email": license_config.email,
                "issued_date": license_config.issued_date.isoformat(),
                "expiry_date": license_config.expiry_date.isoformat(),
                "usage_limits": [
                    {
                        "limit_type": limit.limit_type.value,
                        "limit_value": limit.limit_value,
                        "current_usage": limit.current_usage,
                        "reset_period": limit.reset_period,
                        "last_reset": limit.last_reset.isoformat() if limit.last_reset else None
                    }
                    for limit in license_config.usage_limits
                ],
                "allowed_features": license_config.allowed_features,
                "allowed_scanners": license_config.allowed_scanners,
                "allowed_regions": license_config.allowed_regions,
                "max_concurrent_users": license_config.max_concurrent_users,
                "is_active": license_config.is_active,
                "metadata": license_config.metadata or {}
            }
            
            # Convert to JSON
            json_data = json.dumps(license_dict, indent=2)
            
            # Encrypt if needed
            if self.encrypt_license:
                json_data = self._encrypt_data(json_data)
            
            # Save to file
            with open(self.license_file, 'w') as f:
                f.write(json_data)
            
            self.current_license = license_config
            logger.info(f"License saved: {license_config.license_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save license: {e}")
            return False
    
    def load_license(self) -> Optional[LicenseConfig]:
        """Load license from file"""
        try:
            if not os.path.exists(self.license_file):
                return None
            
            with open(self.license_file, 'r') as f:
                json_data = f.read()
            
            # Decrypt if needed
            if self.encrypt_license:
                json_data = self._decrypt_data(json_data)
                if not json_data:
                    return None
            
            # Parse JSON
            license_dict = json.loads(json_data)
            
            # Convert usage limits
            usage_limits = []
            for limit_dict in license_dict.get("usage_limits", []):
                usage_limits.append(UsageLimit(
                    limit_type=UsageLimitType(limit_dict["limit_type"]),
                    limit_value=limit_dict["limit_value"],
                    current_usage=limit_dict["current_usage"],
                    reset_period=limit_dict["reset_period"],
                    last_reset=datetime.fromisoformat(limit_dict["last_reset"]) if limit_dict["last_reset"] else None
                ))
            
            # Create license config
            license_config = LicenseConfig(
                license_id=license_dict["license_id"],
                license_type=LicenseType(license_dict["license_type"]),
                customer_id=license_dict["customer_id"],
                customer_name=license_dict["customer_name"],
                company_name=license_dict["company_name"],
                email=license_dict["email"],
                issued_date=datetime.fromisoformat(license_dict["issued_date"]),
                expiry_date=datetime.fromisoformat(license_dict["expiry_date"]),
                usage_limits=usage_limits,
                allowed_features=license_dict["allowed_features"],
                allowed_scanners=license_dict["allowed_scanners"],
                allowed_regions=license_dict["allowed_regions"],
                max_concurrent_users=license_dict["max_concurrent_users"],
                is_active=license_dict["is_active"],
                metadata=license_dict.get("metadata", {})
            )
            
            self.current_license = license_config
            logger.info(f"License loaded: {license_config.license_id}")
            return license_config
            
        except Exception as e:
            logger.error(f"Failed to load license: {e}")
            return None
    
    def validate_license(self) -> Tuple[bool, str]:
        """Validate current license"""
        if not self.current_license:
            return False, "No license found"
        
        # Check if license is active
        if not self.current_license.is_active:
            return False, "License is deactivated"
        
        # Check expiry date
        if datetime.now() > self.current_license.expiry_date:
            return False, "License has expired"
        
        # Check hardware binding (for standalone licenses)
        if self.current_license.license_type == LicenseType.STANDALONE:
            current_hardware_id = self._get_hardware_id()
            stored_hardware_id = (self.current_license.metadata or {}).get("hardware_id")
            if stored_hardware_id and current_hardware_id != stored_hardware_id:
                return False, "License is bound to different hardware"
        
        return True, "License is valid"
    
    def check_feature_access(self, feature: str) -> bool:
        """Check if feature is allowed"""
        if not self.current_license:
            return False
        
        is_valid, _ = self.validate_license()
        if not is_valid:
            return False
        
        return feature in (self.current_license.allowed_features or [])
    
    def check_scanner_access(self, scanner_type: str) -> bool:
        """Check if scanner is allowed"""
        if not self.current_license:
            return False
        
        is_valid, _ = self.validate_license()
        if not is_valid:
            return False
        
        # All 13 scanners available for valid active licenses
        all_scanners = [
            "code", "document", "database", "image", "website", "ai_model",
            "dpia", "soc2", "enterprise", "sustainability", "audio_video", 
            "data_sovereignty", "api", "advanced_ai"
        ]
        return scanner_type in all_scanners
    
    def check_region_access(self, region: str) -> bool:
        """Check if region is allowed"""
        if not self.current_license:
            return False
        
        is_valid, _ = self.validate_license()
        if not is_valid:
            return False
        
        return region in self.current_license.allowed_regions
    
    def check_usage_limit(self, limit_type: UsageLimitType) -> Tuple[bool, int, int]:
        """Check usage limit - returns (allowed, current, limit)"""
        if not self.current_license:
            return False, 0, 0
        
        is_valid, _ = self.validate_license()
        if not is_valid:
            return False, 0, 0
        
        # Find the limit
        for limit in self.current_license.usage_limits:
            if limit.limit_type == limit_type:
                # Check if reset is needed
                self._check_reset_usage(limit)
                return limit.current_usage < limit.limit_value, limit.current_usage, limit.limit_value
        
        return True, 0, 999999  # No limit set
    
    def _check_reset_usage(self, limit: UsageLimit):
        """Check if usage should be reset based on period"""
        if not limit.last_reset:
            limit.last_reset = datetime.now()
            return
        
        now = datetime.now()
        should_reset = False
        
        if limit.reset_period == "daily":
            should_reset = now.date() > limit.last_reset.date()
        elif limit.reset_period == "weekly":
            should_reset = now.isocalendar()[1] > limit.last_reset.isocalendar()[1]
        elif limit.reset_period == "monthly":
            should_reset = now.month > limit.last_reset.month or now.year > limit.last_reset.year
        elif limit.reset_period == "yearly":
            should_reset = now.year > limit.last_reset.year
        
        if should_reset:
            limit.current_usage = 0
            limit.last_reset = now
            if self.current_license:
                self.save_license(self.current_license)
    
    def increment_usage(self, limit_type: UsageLimitType, amount: int = 1) -> bool:
        """Increment usage counter"""
        if not self.current_license:
            return False
        
        for limit in self.current_license.usage_limits:
            if limit.limit_type == limit_type:
                limit.current_usage += amount
                if self.current_license:
                    self.save_license(self.current_license)
                return True
        
        return True  # No limit set
    
    def get_license_info(self) -> Dict[str, Any]:
        """Get license information"""
        if not self.current_license:
            return {"status": "No license"}
        
        is_valid, message = self.validate_license()
        
        usage_info = {}
        for limit in self.current_license.usage_limits:
            self._check_reset_usage(limit)
            usage_info[limit.limit_type.value] = {
                "current": limit.current_usage,
                "limit": limit.limit_value,
                "percentage": (limit.current_usage / limit.limit_value) * 100 if limit.limit_value > 0 else 0
            }
        
        return {
            "status": "Valid" if is_valid else "Invalid",
            "message": message,
            "license_id": self.current_license.license_id,
            "license_type": self.current_license.license_type.value,
            "customer_name": self.current_license.customer_name,
            "company_name": self.current_license.company_name,
            "expiry_date": self.current_license.expiry_date.isoformat(),
            "days_remaining": (self.current_license.expiry_date - datetime.now()).days,
            "allowed_features": self.current_license.allowed_features,
            "allowed_scanners": self.current_license.allowed_scanners,
            "allowed_regions": self.current_license.allowed_regions,
            "max_concurrent_users": self.current_license.max_concurrent_users,
            "usage": usage_info
        }
    
    def track_session(self, user_id: str) -> bool:
        """Track user session for concurrent user limits"""
        current_sessions = len([
            session_id for session_id, last_activity in self.session_tracker.items()
            if datetime.now() - last_activity < timedelta(hours=1)  # 1 hour timeout
        ])
        
        if self.current_license and current_sessions >= self.current_license.max_concurrent_users:
            return False
        
        self.session_tracker[user_id] = datetime.now()
        return True
    
    def cleanup_sessions(self):
        """Clean up expired sessions"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        expired_sessions = [
            session_id for session_id, last_activity in self.session_tracker.items()
            if last_activity < cutoff_time
        ]
        
        for session_id in expired_sessions:
            del self.session_tracker[session_id]

# Global license manager instance
license_manager = LicenseManager()

# Convenience functions
def check_license() -> Tuple[bool, str]:
    """Check if license is valid"""
    return license_manager.validate_license()

def check_feature(feature: str) -> bool:
    """Check if feature is allowed"""
    return license_manager.check_feature_access(feature)

def check_scanner(scanner_type: str) -> bool:
    """Check if scanner is allowed"""
    return license_manager.check_scanner_access(scanner_type)

def check_region(region: str) -> bool:
    """Check if region is allowed"""
    return license_manager.check_region_access(region)

def check_usage(limit_type: UsageLimitType) -> Tuple[bool, int, int]:
    """Check usage limit"""
    return license_manager.check_usage_limit(limit_type)

def increment_usage(limit_type: UsageLimitType, amount: int = 1) -> bool:
    """Increment usage counter"""
    return license_manager.increment_usage(limit_type, amount)

def get_license_info() -> Dict[str, Any]:
    """Get license information"""
    return license_manager.get_license_info()

def track_user_session(user_id: str) -> bool:
    """Track user session"""
    return license_manager.track_session(user_id)

# Webhook integration methods for Stripe subscription management
def activate_subscription(customer_id: str, subscription_id: str, plan_name: str, tier: str) -> bool:
    """
    Activate subscription access after successful payment
    Called by webhook when subscription is created
    """
    logger.info(f"Activating subscription {subscription_id} for customer {customer_id}")
    
    # Map tier to license type
    tier_mapping = {
        'basic': LicenseType.BASIC,
        'professional': LicenseType.PROFESSIONAL,
        'enterprise': LicenseType.ENTERPRISE,
        'premium': LicenseType.ENTERPRISE_PLUS
    }
    
    license_type = tier_mapping.get(tier.lower(), LicenseType.BASIC)
    
    try:
        # Generate new license for subscription
        license_config = license_manager.generate_license(
            license_type=license_type,
            customer_id=customer_id,
            customer_name=customer_id,  # Use customer_id as name initially
            company_name="Subscription Customer",
            email=f"{customer_id}@customer.email",
            validity_days=365  # Annual subscription
        )
        
        # Add subscription metadata
        license_config.metadata = license_config.metadata or {}
        license_config.metadata.update({
            'stripe_subscription_id': subscription_id,
            'stripe_customer_id': customer_id,
            'subscription_plan': plan_name,
            'subscription_tier': tier,
            'activation_date': datetime.now().isoformat(),
            'payment_method': 'stripe_subscription'
        })
        
        # Save the license
        success = license_manager.save_license(license_config)
        logger.info(f"Subscription activation {'successful' if success else 'failed'}")
        return success
        
    except Exception as e:
        logger.error(f"Failed to activate subscription {subscription_id}: {e}")
        return False

def update_subscription(customer_id: str, subscription_id: str, new_tier: str, new_plan: str) -> bool:
    """
    Update existing subscription with new tier/plan
    Called by webhook when subscription is modified
    """
    logger.info(f"Updating subscription {subscription_id} to tier {new_tier}")
    
    try:
        # Load current license
        current_license = license_manager.load_license()
        if not current_license or not current_license.metadata or current_license.metadata.get('stripe_subscription_id') != subscription_id:
            logger.warning(f"No matching license found for subscription {subscription_id}")
            return False
        
        # Map new tier to license type
        tier_mapping = {
            'basic': LicenseType.BASIC,
            'professional': LicenseType.PROFESSIONAL,
            'enterprise': LicenseType.ENTERPRISE,
            'premium': LicenseType.ENTERPRISE_PLUS
        }
        
        new_license_type = tier_mapping.get(new_tier.lower(), LicenseType.BASIC)
        
        # Generate updated license
        updated_license = license_manager.generate_license(
            license_type=new_license_type,
            customer_id=current_license.customer_id,
            customer_name=current_license.customer_name,
            company_name=current_license.company_name,
            email=current_license.email,
            validity_days=(current_license.expiry_date - datetime.now()).days
        )
        
        # Preserve subscription metadata
        updated_license.metadata = (current_license.metadata or {}).copy()
        updated_license.metadata.update({
            'subscription_plan': new_plan,
            'subscription_tier': new_tier,
            'last_updated': datetime.now().isoformat()
        })
        
        # Save updated license
        success = license_manager.save_license(updated_license)
        logger.info(f"Subscription update {'successful' if success else 'failed'}")
        return success
        
    except Exception as e:
        logger.error(f"Failed to update subscription {subscription_id}: {e}")
        return False

def deactivate_subscription(customer_id: str, subscription_id: str) -> bool:
    """
    Deactivate subscription access after cancellation
    Called by webhook when subscription is cancelled
    """
    logger.info(f"Deactivating subscription {subscription_id}")
    
    try:
        # Load current license
        current_license = license_manager.load_license()
        if not current_license or not current_license.metadata or current_license.metadata.get('stripe_subscription_id') != subscription_id:
            logger.warning(f"No matching license found for subscription {subscription_id}")
            return False
        
        # Deactivate the license
        current_license.is_active = False
        if not current_license.metadata:
            current_license.metadata = {}
        current_license.metadata['deactivation_date'] = datetime.now().isoformat()
        current_license.metadata['deactivation_reason'] = 'subscription_cancelled'
        
        # Save deactivated license
        success = license_manager.save_license(current_license)
        logger.info(f"Subscription deactivation {'successful' if success else 'failed'}")
        return success
        
    except Exception as e:
        logger.error(f"Failed to deactivate subscription {subscription_id}: {e}")
        return False

def reset_monthly_usage(subscription_id: str) -> bool:
    """
    Reset monthly usage limits after successful payment
    Called by webhook on successful subscription renewal
    """
    logger.info(f"Resetting monthly usage for subscription {subscription_id}")
    
    try:
        current_license = license_manager.load_license()
        if not current_license or not current_license.metadata or current_license.metadata.get('stripe_subscription_id') != subscription_id:
            logger.warning(f"No matching license found for subscription {subscription_id}")
            return False
        
        # Reset monthly usage counters
        for limit in current_license.usage_limits:
            if limit.reset_period == "monthly":
                limit.current_usage = 0
                limit.last_reset = datetime.now()
        
        # Save updated license
        success = license_manager.save_license(current_license)
        logger.info(f"Usage reset {'successful' if success else 'failed'}")
        return success
        
    except Exception as e:
        logger.error(f"Failed to reset usage for subscription {subscription_id}: {e}")
        return False

def mark_subscription_past_due(subscription_id: str) -> bool:
    """
    Mark subscription as past due for failed payments
    Called by webhook when payment fails
    """
    logger.info(f"Marking subscription {subscription_id} as past due")
    
    try:
        current_license = license_manager.load_license()
        if not current_license or not current_license.metadata or current_license.metadata.get('stripe_subscription_id') != subscription_id:
            return False
        
        # Mark as past due but keep active for grace period
        if not current_license.metadata:
            current_license.metadata = {}
        current_license.metadata['payment_status'] = 'past_due'
        current_license.metadata['past_due_date'] = datetime.now().isoformat()
        
        # Save updated license
        success = license_manager.save_license(current_license)
        logger.info(f"Past due marking {'successful' if success else 'failed'}")
        return success
        
    except Exception as e:
        logger.error(f"Failed to mark subscription past due {subscription_id}: {e}")
        return False

def create_customer_record(customer_id: str, email: Optional[str] = None, name: Optional[str] = None) -> bool:
    """
    Create customer record for new Stripe customer
    Called by webhook when customer is created
    """
    logger.info(f"Creating customer record for {customer_id}")
    
    try:
        # For now, just log the customer creation
        # In production, this would create a customer database record
        logger.info(f"Customer record created: {customer_id} ({email or 'no-email'})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create customer record {customer_id}: {e}")
        return False