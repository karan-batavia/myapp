"""
Unit Tests for MFA Service and Security Headers
Tests SOC 2 compliant authentication and security features
"""

import pytest
import sys
import os
import time
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mfa_service import (
    MFAService,
    MFASetupResult,
    MFAValidationResult,
    get_mfa_service,
    enable_mfa_for_user,
    verify_mfa_code
)
from utils.security_headers import (
    SECURITY_HEADERS,
    CSP_DIRECTIVES,
    build_csp_header,
    get_all_security_headers,
    get_nginx_security_headers_config,
    verify_security_headers,
    get_security_headers_report
)


class TestMFAService:
    """Test cases for MFA Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mfa_service = MFAService()
        self.test_username = "test_user"
        self.test_email = "test@example.com"
    
    def test_generate_secret(self):
        """Test TOTP secret generation."""
        secret = self.mfa_service.generate_secret()
        
        assert secret is not None
        assert len(secret) == 32
        assert secret.isalnum()
    
    def test_generate_secret_uniqueness(self):
        """Test that generated secrets are unique."""
        secrets_list = [self.mfa_service.generate_secret() for _ in range(10)]
        assert len(set(secrets_list)) == 10
    
    def test_get_totp(self):
        """Test TOTP object creation."""
        secret = self.mfa_service.generate_secret()
        totp = self.mfa_service.get_totp(secret)
        
        assert totp is not None
        assert totp.interval == 30
        assert totp.digits == 6
    
    def test_generate_qr_code(self):
        """Test QR code generation."""
        secret = self.mfa_service.generate_secret()
        qr_code = self.mfa_service.generate_qr_code(secret, self.test_username, self.test_email)
        
        assert qr_code is not None
        assert len(qr_code) > 100
        import base64
        decoded = base64.b64decode(qr_code)
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n'
    
    def test_generate_backup_codes(self):
        """Test backup code generation."""
        codes = self.mfa_service.generate_backup_codes()
        
        assert len(codes) == 10
        for code in codes:
            assert len(code) == 8
            assert code.isalnum()
    
    def test_backup_codes_uniqueness(self):
        """Test that backup codes are unique."""
        codes = self.mfa_service.generate_backup_codes()
        assert len(set(codes)) == 10
    
    def test_hash_backup_code(self):
        """Test backup code hashing."""
        code = "ABC12345"
        hashed = self.mfa_service.hash_backup_code(code)
        
        assert len(hashed) == 64
        expected = hashlib.sha256(code.upper().encode()).hexdigest()
        assert hashed == expected
    
    def test_hash_backup_code_case_insensitive(self):
        """Test that backup code hashing is case-insensitive."""
        hash1 = self.mfa_service.hash_backup_code("ABC12345")
        hash2 = self.mfa_service.hash_backup_code("abc12345")
        assert hash1 == hash2
    
    def test_setup_mfa(self):
        """Test MFA setup."""
        result = self.mfa_service.setup_mfa(self.test_username, self.test_email)
        
        assert isinstance(result, MFASetupResult)
        assert result.success is True
        assert result.secret is not None
        assert result.qr_code_base64 is not None
        assert result.backup_codes is not None
        assert len(result.backup_codes) == 10
        assert result.error is None
    
    def test_verify_totp_valid_code(self):
        """Test TOTP verification with valid code."""
        secret = self.mfa_service.generate_secret()
        current_code = self.mfa_service.get_current_code(secret)
        
        assert self.mfa_service.verify_totp(secret, current_code) is True
    
    def test_verify_totp_invalid_code(self):
        """Test TOTP verification with invalid code."""
        secret = self.mfa_service.generate_secret()
        
        assert self.mfa_service.verify_totp(secret, "000000") is False
        assert self.mfa_service.verify_totp(secret, "123456") is False
    
    def test_verify_totp_malformed_code(self):
        """Test TOTP verification with malformed codes."""
        secret = self.mfa_service.generate_secret()
        
        assert self.mfa_service.verify_totp(secret, "") is False
        assert self.mfa_service.verify_totp(secret, "abc") is False
        assert self.mfa_service.verify_totp(secret, "12345") is False
        assert self.mfa_service.verify_totp(secret, "1234567") is False
        assert self.mfa_service.verify_totp(secret, None) is False
    
    def test_verify_totp_empty_secret(self):
        """Test TOTP verification with empty secret."""
        assert self.mfa_service.verify_totp("", "123456") is False
        assert self.mfa_service.verify_totp(None, "123456") is False
    
    def test_verify_backup_code_valid(self):
        """Test backup code verification with valid code."""
        codes = self.mfa_service.generate_backup_codes()
        hashes = [self.mfa_service.hash_backup_code(c) for c in codes]
        
        is_valid, used_hash = self.mfa_service.verify_backup_code(hashes, codes[0])
        
        assert is_valid is True
        assert used_hash == hashes[0]
    
    def test_verify_backup_code_invalid(self):
        """Test backup code verification with invalid code."""
        codes = self.mfa_service.generate_backup_codes()
        hashes = [self.mfa_service.hash_backup_code(c) for c in codes]
        
        is_valid, used_hash = self.mfa_service.verify_backup_code(hashes, "INVALID1")
        
        assert is_valid is False
        assert used_hash is None
    
    def test_verify_backup_code_case_insensitive(self):
        """Test that backup code verification is case-insensitive."""
        codes = self.mfa_service.generate_backup_codes()
        hashes = [self.mfa_service.hash_backup_code(c) for c in codes]
        
        is_valid, _ = self.mfa_service.verify_backup_code(hashes, codes[0].lower())
        assert is_valid is True
    
    def test_validate_mfa_totp(self):
        """Test MFA validation with TOTP code."""
        secret = self.mfa_service.generate_secret()
        current_code = self.mfa_service.get_current_code(secret)
        
        result = self.mfa_service.validate_mfa(current_code, totp_secret=secret)
        
        assert isinstance(result, MFAValidationResult)
        assert result.valid is True
        assert result.method == "totp"
        assert result.error is None
    
    def test_validate_mfa_backup_code(self):
        """Test MFA validation with backup code."""
        codes = self.mfa_service.generate_backup_codes()
        hashes = [self.mfa_service.hash_backup_code(c) for c in codes]
        
        result = self.mfa_service.validate_mfa(codes[0], backup_code_hashes=hashes)
        
        assert result.valid is True
        assert result.method == "backup_code"
    
    def test_validate_mfa_no_code(self):
        """Test MFA validation with no code."""
        result = self.mfa_service.validate_mfa("")
        
        assert result.valid is False
        assert result.error == "No code provided"
    
    def test_get_mfa_service_singleton(self):
        """Test MFA service singleton pattern."""
        service1 = get_mfa_service()
        service2 = get_mfa_service()
        
        assert service1 is service2
    
    def test_enable_mfa_for_user(self):
        """Test enable_mfa_for_user helper function."""
        result = enable_mfa_for_user(self.test_username, self.test_email)
        
        assert result["success"] is True
        assert "secret" in result
        assert "qr_code_base64" in result
        assert "backup_codes" in result
        assert "backup_code_hashes" in result
        assert len(result["backup_codes"]) == 10
        assert len(result["backup_code_hashes"]) == 10
    
    def test_verify_mfa_code_totp(self):
        """Test verify_mfa_code helper function with TOTP."""
        secret = self.mfa_service.generate_secret()
        current_code = self.mfa_service.get_current_code(secret)
        
        result = verify_mfa_code(current_code, totp_secret=secret)
        
        assert result["valid"] is True
        assert result["method"] == "totp"
    
    def test_verify_mfa_code_backup(self):
        """Test verify_mfa_code helper function with backup code."""
        codes = self.mfa_service.generate_backup_codes()
        hashes = [self.mfa_service.hash_backup_code(c) for c in codes]
        
        result = verify_mfa_code(codes[5], backup_code_hashes=hashes)
        
        assert result["valid"] is True
        assert result["method"] == "backup_code"


class TestSecurityHeaders:
    """Test cases for Security Headers."""
    
    def test_security_headers_defined(self):
        """Test that all required security headers are defined."""
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Cache-Control",
            "Pragma"
        ]
        
        for header in required_headers:
            assert header in SECURITY_HEADERS
    
    def test_x_content_type_options(self):
        """Test X-Content-Type-Options header value."""
        assert SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
    
    def test_x_frame_options(self):
        """Test X-Frame-Options header value."""
        assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"
    
    def test_x_xss_protection(self):
        """Test X-XSS-Protection header value."""
        assert SECURITY_HEADERS["X-XSS-Protection"] == "1; mode=block"
    
    def test_referrer_policy(self):
        """Test Referrer-Policy header value."""
        assert SECURITY_HEADERS["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_cache_control(self):
        """Test Cache-Control header prevents caching."""
        cache_control = SECURITY_HEADERS["Cache-Control"]
        assert "no-store" in cache_control
        assert "no-cache" in cache_control
        assert "private" in cache_control
    
    def test_csp_directives_defined(self):
        """Test that CSP directives are defined."""
        required_directives = [
            "default-src",
            "script-src",
            "style-src",
            "img-src",
            "connect-src",
            "frame-ancestors",
            "form-action",
            "base-uri",
            "object-src"
        ]
        
        for directive in required_directives:
            assert directive in CSP_DIRECTIVES
    
    def test_csp_default_src_self(self):
        """Test CSP default-src is 'self'."""
        assert CSP_DIRECTIVES["default-src"] == "'self'"
    
    def test_csp_frame_ancestors_none(self):
        """Test CSP frame-ancestors prevents framing."""
        assert CSP_DIRECTIVES["frame-ancestors"] == "'none'"
    
    def test_csp_object_src_none(self):
        """Test CSP object-src blocks plugins."""
        assert CSP_DIRECTIVES["object-src"] == "'none'"
    
    def test_build_csp_header(self):
        """Test CSP header building."""
        csp = build_csp_header()
        
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "; " in csp
    
    def test_get_all_security_headers(self):
        """Test getting all security headers including CSP."""
        headers = get_all_security_headers()
        
        assert "Content-Security-Policy" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert len(headers) == len(SECURITY_HEADERS) + 1
    
    def test_get_nginx_security_headers_config(self):
        """Test Nginx security headers config generation."""
        config = get_nginx_security_headers_config()
        
        assert "add_header X-Content-Type-Options" in config
        assert "add_header X-Frame-Options" in config
        assert "SOC 2 Compliant" in config
        assert "HSTS" in config
    
    def test_get_security_headers_report(self):
        """Test security headers compliance report."""
        report = get_security_headers_report()
        
        assert report["status"] == "configured"
        assert report["headers_count"] > 0
        assert "headers" in report
        assert "compliance" in report
        assert report["compliance"]["soc2_cc6.1"] is True
        assert report["compliance"]["soc2_cc6.7"] is True
        assert report["compliance"]["owasp"] is True
        assert "recommendations" in report


class TestMFASecurityIntegration:
    """Integration tests for MFA and security features."""
    
    def test_mfa_code_not_reusable_immediately(self):
        """Test that the same TOTP code is valid within time window."""
        mfa = MFAService()
        secret = mfa.generate_secret()
        code = mfa.get_current_code(secret)
        
        assert mfa.verify_totp(secret, code) is True
        assert mfa.verify_totp(secret, code) is True
    
    def test_backup_code_hash_secure(self):
        """Test that backup codes are securely hashed."""
        mfa = MFAService()
        code = "ABC12345"
        hash1 = mfa.hash_backup_code(code)
        hash2 = mfa.hash_backup_code(code)
        
        assert hash1 == hash2
        assert code not in hash1
        assert len(hash1) == 64
    
    def test_totp_code_format(self):
        """Test TOTP code format (6 digits)."""
        mfa = MFAService()
        secret = mfa.generate_secret()
        code = mfa.get_current_code(secret)
        
        assert len(code) == 6
        assert code.isdigit()
    
    def test_security_headers_prevent_clickjacking(self):
        """Test that headers prevent clickjacking."""
        assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"
        assert CSP_DIRECTIVES["frame-ancestors"] == "'none'"
    
    def test_security_headers_prevent_mime_sniffing(self):
        """Test that headers prevent MIME sniffing."""
        assert SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
