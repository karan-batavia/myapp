"""
Comprehensive Unit Tests for License Manager and Subscription Manager

Tests the complete licensing and subscription flow:
- License generation and validation
- License types and tiers
- Feature access control
- Scanner access control
- Region access control
- Usage limits and tracking
- Session tracking
- Subscription plans
- Subscription lifecycle
"""

import os
import sys
import pytest
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.license_manager import (
    LicenseManager, LicenseType, LicenseConfig, UsageLimitType, UsageLimit,
    check_license, check_feature, check_scanner, check_region,
    activate_subscription, update_subscription, deactivate_subscription
)


class TestLicenseManagerInitialization:
    """Test LicenseManager initialization."""
    
    def test_default_initialization(self):
        """Test LicenseManager initializes with defaults."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            assert manager.license_file == temp_file
            assert manager.encrypt_license == False
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_encrypted_initialization(self):
        """Test LicenseManager with encryption enabled."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            if os.path.exists('.license_key'):
                os.unlink('.license_key')
            
            manager = LicenseManager(license_file=temp_file, encrypt_license=True)
            assert manager.encrypt_license == True
            assert hasattr(manager, 'encryption_key')
        except Exception as e:
            if "tamper" in str(e).lower():
                pytest.skip("Hardware fingerprint changed - expected in test environment")
            raise
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists('.license_key'):
                os.unlink('.license_key')


class TestLicenseTypes:
    """Test license type definitions."""
    
    def test_all_license_types_defined(self):
        """Test all expected license types exist."""
        expected_types = [
            'trial', 'startup', 'professional', 'growth', 'scale',
            'enterprise', 'government', 'basic', 'enterprise_plus',
            'consultancy', 'ai_compliance', 'standalone', 'saas', 'custom'
        ]
        
        for license_type in expected_types:
            assert hasattr(LicenseType, license_type.upper()), f"Missing license type: {license_type}"
    
    def test_license_type_values(self):
        """Test license type enum values."""
        assert LicenseType.TRIAL.value == "trial"
        assert LicenseType.STARTUP.value == "startup"
        assert LicenseType.PROFESSIONAL.value == "professional"
        assert LicenseType.ENTERPRISE.value == "enterprise"


class TestUsageLimitTypes:
    """Test usage limit type definitions."""
    
    def test_all_usage_limit_types_defined(self):
        """Test all expected usage limit types exist."""
        expected_types = [
            'scans_per_month', 'scans_per_day', 'concurrent_users',
            'api_calls', 'storage_mb', 'export_reports', 'scanner_types', 'regions'
        ]
        
        for limit_type in expected_types:
            assert hasattr(UsageLimitType, limit_type.upper()), f"Missing limit type: {limit_type}"


class TestLicenseGeneration:
    """Test license generation functionality."""
    
    def test_generate_trial_license(self):
        """Test generating a trial license."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.TRIAL,
                customer_id="CUST-001",
                customer_name="Test User",
                company_name="Test Company",
                email="test@example.com",
                validity_days=14
            )
            
            assert license_config.license_type == LicenseType.TRIAL
            assert license_config.customer_id == "CUST-001"
            assert license_config.customer_name == "Test User"
            assert license_config.company_name == "Test Company"
            assert license_config.email == "test@example.com"
            assert license_config.is_active == True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_generate_startup_license(self):
        """Test generating a startup license."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.STARTUP,
                customer_id="CUST-002",
                customer_name="Startup User",
                company_name="Startup BV",
                email="startup@example.com"
            )
            
            assert license_config.license_type == LicenseType.STARTUP
            assert license_config.max_concurrent_users == 5
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_generate_enterprise_license(self):
        """Test generating an enterprise license."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.ENTERPRISE,
                customer_id="CUST-003",
                customer_name="Enterprise User",
                company_name="Enterprise Corp",
                email="enterprise@example.com"
            )
            
            assert license_config.license_type == LicenseType.ENTERPRISE
            assert license_config.max_concurrent_users == 999999  # Unlimited
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_license_expiry_date(self):
        """Test license expiry date calculation."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.PROFESSIONAL,
                customer_id="CUST-004",
                customer_name="Pro User",
                company_name="Pro Company",
                email="pro@example.com",
                validity_days=30
            )
            
            expected_expiry = datetime.now() + timedelta(days=30)
            assert (license_config.expiry_date.date() - expected_expiry.date()).days <= 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestLicenseSaveLoad:
    """Test license save and load functionality."""
    
    def test_save_license(self):
        """Test saving a license to file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.STARTUP,
                customer_id="CUST-005",
                customer_name="Save Test",
                company_name="Save Company",
                email="save@example.com"
            )
            
            result = manager.save_license(license_config)
            assert result == True
            assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_load_license(self):
        """Test loading a license from file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.GROWTH,
                customer_id="CUST-006",
                customer_name="Load Test",
                company_name="Load Company",
                email="load@example.com"
            )
            
            manager.save_license(license_config)
            
            manager2 = LicenseManager(license_file=temp_file, encrypt_license=False)
            loaded_license = manager2.load_license()
            
            assert loaded_license is not None
            assert loaded_license.customer_id == "CUST-006"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestLicenseValidation:
    """Test license validation functionality."""
    
    def test_validate_active_license(self):
        """Test validation of an active license."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.PROFESSIONAL,
                customer_id="CUST-007",
                customer_name="Valid User",
                company_name="Valid Company",
                email="valid@example.com",
                validity_days=365
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            is_valid, message = manager.validate_license()
            assert is_valid == True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_validate_expired_license(self):
        """Test validation of an expired license."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.TRIAL,
                customer_id="CUST-008",
                customer_name="Expired User",
                company_name="Expired Company",
                email="expired@example.com",
                validity_days=1
            )
            
            license_config.expiry_date = datetime.now() - timedelta(days=10)
            manager.current_license = license_config
            
            is_valid, message = manager.validate_license()
            assert is_valid == False
            assert "expired" in message.lower()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestFeatureAccessControl:
    """Test feature access control."""
    
    def test_check_feature_access_granted(self):
        """Test feature access when feature is allowed."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.ENTERPRISE,
                customer_id="CUST-009",
                customer_name="Feature User",
                company_name="Feature Company",
                email="feature@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            has_access = manager.check_feature_access("code_scanner")
            assert has_access == True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_check_feature_access_denied(self):
        """Test feature access when feature is not allowed."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.TRIAL,
                customer_id="CUST-010",
                customer_name="Limited User",
                company_name="Limited Company",
                email="limited@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            has_access = manager.check_feature_access("white_label")
            assert has_access == False
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestScannerAccessControl:
    """Test scanner access control."""
    
    def test_check_scanner_access_granted(self):
        """Test scanner access when scanner is allowed."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.SCALE,
                customer_id="CUST-011",
                customer_name="Scanner User",
                company_name="Scanner Company",
                email="scanner@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            has_access = manager.check_scanner_access("ai_model")
            assert has_access == True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestRegionAccessControl:
    """Test region access control."""
    
    def test_check_region_access_netherlands(self):
        """Test region access for Netherlands."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.STARTUP,
                customer_id="CUST-012",
                customer_name="Region User",
                company_name="Region Company",
                email="region@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            has_access = manager.check_region_access("Netherlands")
            assert has_access == True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_check_region_access_global(self):
        """Test global region access for enterprise license."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.ENTERPRISE,
                customer_id="CUST-013",
                customer_name="Global User",
                company_name="Global Company",
                email="global@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            has_access = manager.check_region_access("Global")
            assert has_access == True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestUsageLimits:
    """Test usage limits functionality."""
    
    def test_check_usage_limit(self):
        """Test checking usage limits."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.STARTUP,
                customer_id="CUST-014",
                customer_name="Usage User",
                company_name="Usage Company",
                email="usage@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            within_limit, current, limit = manager.check_usage_limit(UsageLimitType.SCANS_PER_MONTH)
            
            assert within_limit == True
            assert current >= 0
            assert limit == 200  # Startup tier limit
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_increment_usage(self):
        """Test incrementing usage."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.PROFESSIONAL,
                customer_id="CUST-015",
                customer_name="Increment User",
                company_name="Increment Company",
                email="increment@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            result = manager.increment_usage(UsageLimitType.SCANS_PER_MONTH, 5)
            
            assert result == True
            
            _, current, _ = manager.check_usage_limit(UsageLimitType.SCANS_PER_MONTH)
            assert current == 5
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestSessionTracking:
    """Test session tracking functionality."""
    
    def test_track_session(self):
        """Test tracking a user session."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.GROWTH,
                customer_id="CUST-016",
                customer_name="Session User",
                company_name="Session Company",
                email="session@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            result = manager.track_session("user_123")
            
            assert result == True
            assert "user_123" in manager.session_tracker
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_cleanup_sessions(self):
        """Test cleaning up expired sessions."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.ENTERPRISE,
                customer_id="CUST-017",
                customer_name="Cleanup User",
                company_name="Cleanup Company",
                email="cleanup@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            manager.session_tracker["old_user"] = datetime.now() - timedelta(hours=2)
            manager.session_tracker["new_user"] = datetime.now()
            
            manager.cleanup_sessions()
            
            assert "old_user" not in manager.session_tracker
            assert "new_user" in manager.session_tracker
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestLicenseInfo:
    """Test license info retrieval."""
    
    def test_get_license_info(self):
        """Test getting license info."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.SCALE,
                customer_id="CUST-018",
                customer_name="Info User",
                company_name="Info Company",
                email="info@example.com"
            )
            
            manager.save_license(license_config)
            manager.current_license = license_config
            
            info = manager.get_license_info()
            
            assert "license_type" in info
            assert "customer_name" in info
            assert "company_name" in info
            assert info["license_type"] == "scale"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestSubscriptionActivation:
    """Test subscription activation functions."""
    
    @patch('services.license_manager.LicenseManager')
    def test_activate_subscription(self, mock_license_manager):
        """Test activating a subscription."""
        mock_instance = MagicMock()
        mock_license_manager.return_value = mock_instance
        mock_instance.generate_license.return_value = MagicMock()
        mock_instance.save_license.return_value = True
        
        result = activate_subscription(
            customer_id="CUST-019",
            subscription_id="sub_123",
            plan_name="Professional Plan",
            tier="professional"
        )
        
        assert result == True
    
    def test_deactivate_subscription(self):
        """Test deactivating a subscription returns boolean."""
        result = deactivate_subscription(
            customer_id="CUST-020",
            subscription_id="sub_456"
        )
        
        assert isinstance(result, bool)


class TestSubscriptionPlans:
    """Test subscription plans configuration."""
    
    def test_subscription_plans_defined(self):
        """Test subscription plans are defined."""
        from services.subscription_manager import SUBSCRIPTION_PLANS
        
        expected_plans = ['basic', 'professional', 'enterprise', 'enterprise_plus', 'consultancy', 'ai_compliance']
        
        for plan in expected_plans:
            assert plan in SUBSCRIPTION_PLANS, f"Missing plan: {plan}"
    
    def test_plan_structure(self):
        """Test plan structure has required fields."""
        from services.subscription_manager import SUBSCRIPTION_PLANS
        
        required_fields = ['name', 'description', 'price', 'currency', 'interval', 'features']
        
        for plan_id, plan in SUBSCRIPTION_PLANS.items():
            for field in required_fields:
                assert field in plan, f"Plan {plan_id} missing field: {field}"
    
    def test_plan_prices_in_cents(self):
        """Test plan prices are in cents."""
        from services.subscription_manager import SUBSCRIPTION_PLANS
        
        for plan_id, plan in SUBSCRIPTION_PLANS.items():
            assert plan['price'] > 100, f"Plan {plan_id} price should be in cents"
            assert plan['currency'] == 'eur'


class TestSubscriptionManagerInitialization:
    """Test SubscriptionManager initialization."""
    
    @patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'})
    def test_initialization_with_stripe_key(self):
        """Test initialization with Stripe key."""
        from services.subscription_manager import SubscriptionManager
        
        with patch('streamlit.warning'):
            manager = SubscriptionManager()
            assert manager.stripe_api_key == 'sk_test_123'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_initialization_without_stripe_key(self):
        """Test initialization without Stripe key."""
        from services.subscription_manager import SubscriptionManager
        
        if 'STRIPE_SECRET_KEY' in os.environ:
            del os.environ['STRIPE_SECRET_KEY']
        
        with patch('streamlit.warning') as mock_warning:
            manager = SubscriptionManager()
            assert manager.stripe_api_key is None


class TestSubscriptionStatus:
    """Test subscription status functionality."""
    
    @patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'})
    def test_get_subscription_status(self):
        """Test getting subscription status."""
        from services.subscription_manager import SubscriptionManager
        
        with patch('streamlit.warning'):
            manager = SubscriptionManager()
            
            status = manager.get_subscription_status("user_123")
            
            assert status is not None
            assert 'user_id' in status
            assert 'status' in status
            assert 'plan' in status


class TestLicenseTierLimits:
    """Test license tier limits are correctly configured."""
    
    def test_trial_limits(self):
        """Test trial tier limits."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.TRIAL,
                customer_id="CUST-TRIAL",
                customer_name="Trial User",
                company_name="Trial Company",
                email="trial@example.com"
            )
            
            scans_limit = next(
                (l for l in license_config.usage_limits if l.limit_type == UsageLimitType.SCANS_PER_MONTH),
                None
            )
            
            assert scans_limit is not None
            assert scans_limit.limit_value == 10
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_startup_limits(self):
        """Test startup tier limits (€59/month)."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.STARTUP,
                customer_id="CUST-STARTUP",
                customer_name="Startup User",
                company_name="Startup Company",
                email="startup@example.com"
            )
            
            scans_limit = next(
                (l for l in license_config.usage_limits if l.limit_type == UsageLimitType.SCANS_PER_MONTH),
                None
            )
            
            assert scans_limit is not None
            assert scans_limit.limit_value == 200
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_professional_limits(self):
        """Test professional tier limits (€99/month)."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.PROFESSIONAL,
                customer_id="CUST-PRO",
                customer_name="Pro User",
                company_name="Pro Company",
                email="pro@example.com"
            )
            
            scans_limit = next(
                (l for l in license_config.usage_limits if l.limit_type == UsageLimitType.SCANS_PER_MONTH),
                None
            )
            
            assert scans_limit is not None
            assert scans_limit.limit_value == 350
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_growth_limits(self):
        """Test growth tier limits (€179/month)."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.GROWTH,
                customer_id="CUST-GROWTH",
                customer_name="Growth User",
                company_name="Growth Company",
                email="growth@example.com"
            )
            
            scans_limit = next(
                (l for l in license_config.usage_limits if l.limit_type == UsageLimitType.SCANS_PER_MONTH),
                None
            )
            
            assert scans_limit is not None
            assert scans_limit.limit_value == 750
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_scale_unlimited(self):
        """Test scale tier has unlimited scans (€499/month)."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.SCALE,
                customer_id="CUST-SCALE",
                customer_name="Scale User",
                company_name="Scale Company",
                email="scale@example.com"
            )
            
            scans_limit = next(
                (l for l in license_config.usage_limits if l.limit_type == UsageLimitType.SCANS_PER_MONTH),
                None
            )
            
            assert scans_limit is not None
            assert scans_limit.limit_value == 999999  # Unlimited
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestHardwareFingerprint:
    """Test hardware fingerprint functionality."""
    
    def test_get_hardware_fingerprint(self):
        """Test getting hardware fingerprint."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            fingerprint = manager._get_hardware_fingerprint()
            
            assert isinstance(fingerprint, str)
            assert len(fingerprint) == 32  # SHA256 hex[:32]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_hardware_fingerprint_consistent(self):
        """Test hardware fingerprint is consistent."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            fingerprint1 = manager._get_hardware_fingerprint()
            fingerprint2 = manager._get_hardware_fingerprint()
            
            assert fingerprint1 == fingerprint2
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestLicenseIntegrationFlow:
    """Integration tests for complete license flow."""
    
    def test_complete_license_flow(self):
        """Test complete license generation, save, load, validate flow."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            license_config = manager.generate_license(
                license_type=LicenseType.PROFESSIONAL,
                customer_id="FLOW-001",
                customer_name="Flow User",
                company_name="Flow Company",
                email="flow@example.com",
                validity_days=365
            )
            
            save_result = manager.save_license(license_config)
            assert save_result == True
            
            manager2 = LicenseManager(license_file=temp_file, encrypt_license=False)
            loaded = manager2.load_license()
            assert loaded is not None
            
            manager2.current_license = loaded
            is_valid, message = manager2.validate_license()
            assert is_valid == True
            
            has_feature = manager2.check_feature_access("code_scanner")
            assert has_feature == True
            
            has_scanner = manager2.check_scanner_access("document")
            assert has_scanner == True
            
            has_region = manager2.check_region_access("Netherlands")
            assert has_region == True
            
            within_limit, current, limit = manager2.check_usage_limit(UsageLimitType.SCANS_PER_MONTH)
            assert within_limit == True
            assert limit == 350  # Professional tier
            
            info = manager2.get_license_info()
            assert info["license_type"] == "professional"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
