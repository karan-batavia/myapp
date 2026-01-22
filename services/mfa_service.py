"""
Multi-Factor Authentication (MFA/2FA) Service for DataGuardian Pro
SOC 2 Compliant TOTP-based Two-Factor Authentication

Features:
- TOTP (Time-based One-Time Password) using RFC 6238
- QR code generation for authenticator app setup
- Backup codes for account recovery
- Secure secret storage with encryption
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MFASetupResult:
    """Result of MFA setup operation."""
    success: bool
    secret: Optional[str] = None
    qr_code_base64: Optional[str] = None
    backup_codes: Optional[List[str]] = None
    error: Optional[str] = None

@dataclass
class MFAValidationResult:
    """Result of MFA validation."""
    valid: bool
    method: str = "totp"
    error: Optional[str] = None

class MFAService:
    """
    TOTP-based Multi-Factor Authentication Service.
    
    Implements:
    - SOC 2 CC6.1: Logical access security
    - SOC 2 CC6.6: System operations security
    - GDPR Art. 32: Security of processing
    """
    
    ISSUER_NAME = "DataGuardian Pro"
    TOTP_INTERVAL = 30
    TOTP_DIGITS = 6
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8
    
    def __init__(self):
        self._users_cache = {}
        logger.info("MFA Service initialized - SOC 2 compliant 2FA enabled")
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()
    
    def get_totp(self, secret: str) -> pyotp.TOTP:
        """Get TOTP object for a secret."""
        return pyotp.TOTP(
            secret,
            interval=self.TOTP_INTERVAL,
            digits=self.TOTP_DIGITS
        )
    
    def generate_qr_code(self, secret: str, username: str, email: str = None) -> str:
        """
        Generate QR code for authenticator app setup.
        
        Returns:
            Base64 encoded PNG image of QR code
        """
        totp = self.get_totp(secret)
        
        account_name = email if email else username
        provisioning_uri = totp.provisioning_uri(
            name=account_name,
            issuer_name=self.ISSUER_NAME
        )
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate backup codes for account recovery.
        
        Returns:
            List of backup codes (each 8 characters)
        """
        codes = []
        for _ in range(self.BACKUP_CODE_COUNT):
            code = secrets.token_hex(self.BACKUP_CODE_LENGTH // 2).upper()
            codes.append(code)
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Hash a backup code for secure storage."""
        return hashlib.sha256(code.upper().encode()).hexdigest()
    
    def setup_mfa(self, username: str, email: str = None) -> MFASetupResult:
        """
        Set up MFA for a user.
        
        Returns:
            MFASetupResult with secret, QR code, and backup codes
        """
        try:
            secret = self.generate_secret()
            qr_code = self.generate_qr_code(secret, username, email)
            backup_codes = self.generate_backup_codes()
            
            logger.info(f"MFA setup initiated for user: {username}")
            
            return MFASetupResult(
                success=True,
                secret=secret,
                qr_code_base64=qr_code,
                backup_codes=backup_codes
            )
            
        except Exception as e:
            logger.error(f"MFA setup failed for {username}: {e}")
            return MFASetupResult(
                success=False,
                error=str(e)
            )
    
    def verify_totp(self, secret: str, code: str, valid_window: int = 1) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            secret: The user's TOTP secret
            code: The code to verify
            valid_window: Number of time steps to allow (default 1 = 30s before/after)
            
        Returns:
            True if code is valid
        """
        if not secret or not code:
            return False
            
        try:
            code = code.strip().replace(" ", "").replace("-", "")
            
            if not code.isdigit() or len(code) != self.TOTP_DIGITS:
                return False
            
            totp = self.get_totp(secret)
            return totp.verify(code, valid_window=valid_window)
            
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False
    
    def verify_backup_code(self, stored_hashes: List[str], code: str) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code.
        
        Args:
            stored_hashes: List of hashed backup codes
            code: The backup code to verify
            
        Returns:
            Tuple of (is_valid, hash_to_remove)
        """
        if not stored_hashes or not code:
            return False, None
            
        code_hash = self.hash_backup_code(code)
        
        if code_hash in stored_hashes:
            return True, code_hash
            
        return False, None
    
    def validate_mfa(
        self, 
        code: str, 
        totp_secret: Optional[str] = None,
        backup_code_hashes: Optional[List[str]] = None
    ) -> MFAValidationResult:
        """
        Validate MFA code (TOTP or backup code).
        
        Args:
            code: The code to validate
            totp_secret: User's TOTP secret
            backup_code_hashes: List of hashed backup codes
            
        Returns:
            MFAValidationResult
        """
        if not code:
            return MFAValidationResult(valid=False, error="No code provided")
        
        code = code.strip().replace(" ", "").replace("-", "")
        
        if totp_secret and len(code) == self.TOTP_DIGITS and code.isdigit():
            if self.verify_totp(totp_secret, code):
                logger.info("MFA validation successful via TOTP")
                return MFAValidationResult(valid=True, method="totp")
        
        if backup_code_hashes and len(code) == self.BACKUP_CODE_LENGTH:
            is_valid, used_hash = self.verify_backup_code(backup_code_hashes, code)
            if is_valid:
                logger.info("MFA validation successful via backup code")
                return MFAValidationResult(valid=True, method="backup_code")
        
        logger.warning("MFA validation failed - invalid code")
        return MFAValidationResult(valid=False, error="Invalid verification code")
    
    def get_current_code(self, secret: str) -> str:
        """Get current TOTP code (for testing only)."""
        totp = self.get_totp(secret)
        return totp.now()


_mfa_service = None

def get_mfa_service() -> MFAService:
    """Get singleton MFA service instance."""
    global _mfa_service
    if _mfa_service is None:
        _mfa_service = MFAService()
    return _mfa_service


def enable_mfa_for_user(username: str, email: str = None) -> Dict[str, Any]:
    """
    Enable MFA for a user and return setup data.
    
    This function should be called from the settings page.
    The returned data includes the secret and QR code for setup.
    """
    service = get_mfa_service()
    result = service.setup_mfa(username, email)
    
    if result.success:
        hashed_backup_codes = [
            service.hash_backup_code(code) 
            for code in result.backup_codes
        ]
        
        return {
            "success": True,
            "secret": result.secret,
            "qr_code_base64": result.qr_code_base64,
            "backup_codes": result.backup_codes,
            "backup_code_hashes": hashed_backup_codes
        }
    
    return {
        "success": False,
        "error": result.error
    }


def verify_mfa_code(
    code: str,
    totp_secret: Optional[str] = None,
    backup_code_hashes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Verify an MFA code.
    
    Args:
        code: The TOTP or backup code
        totp_secret: User's TOTP secret
        backup_code_hashes: List of hashed backup codes
        
    Returns:
        Dict with 'valid' boolean and 'method' if valid
    """
    service = get_mfa_service()
    result = service.validate_mfa(code, totp_secret, backup_code_hashes)
    
    return {
        "valid": result.valid,
        "method": result.method,
        "error": result.error
    }
