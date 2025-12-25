"""
Comprehensive Unit Tests for Pricing and Scanner Flow

Tests the complete pricing and scanner integration:
- Scanner availability per license tier
- Scanner limits in license manager
- Pricing configuration consistency
- Scanner page filtering logic
- Premium scanner upgrade flow
"""

import os
import sys
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.license_manager import (
    LicenseManager, LicenseType, UsageLimitType
)


class TestScannerTierAvailability:
    """Test scanner availability per license tier."""
    
    def test_scanner_page_tier_limits(self):
        """Test get_available_scanners_for_tier returns correct counts."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        test_cases = [
            ('trial', 3),
            ('free', 3),
            ('startup', 6),
            ('professional', 8),
            ('growth', 10),
            ('scale', 12),
            ('enterprise', 12),
            ('unlimited', 12),
            ('government', 12),
        ]
        
        for tier, expected_count in test_cases:
            available, locked = get_available_scanners_for_tier(tier)
            assert len(available) == expected_count, f"Tier {tier}: expected {expected_count} scanners, got {len(available)}"
            assert len(available) + len(locked) == 12, f"Tier {tier}: total scanners should be 12"
    
    def test_scanner_page_tier_limits_case_insensitive(self):
        """Test tier matching is case-insensitive."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        test_cases = [
            ('TRIAL', 3),
            ('Startup', 6),
            ('PROFESSIONAL', 8),
            ('Enterprise', 12),
        ]
        
        for tier, expected_count in test_cases:
            available, locked = get_available_scanners_for_tier(tier)
            assert len(available) == expected_count, f"Tier {tier} (case test): expected {expected_count}"
    
    def test_scanner_page_unknown_tier_defaults(self):
        """Test unknown tier defaults to 6 scanners."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        available, locked = get_available_scanners_for_tier('unknown_tier')
        assert len(available) == 6, "Unknown tier should default to 6 scanners"
    
    def test_scanner_order_matches_tier_slicing(self):
        """Test scanner order enables proper tier-based slicing."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        trial_scanners, _ = get_available_scanners_for_tier('trial')
        startup_scanners, _ = get_available_scanners_for_tier('startup')
        
        trial_ids = [s[0] for s in trial_scanners]
        startup_ids = [s[0] for s in startup_scanners]
        
        assert trial_ids == ['code', 'document', 'database'], "Trial should have core 3 scanners"
        assert startup_ids[:3] == trial_ids, "Startup should include all trial scanners"
        assert 'image' in startup_ids, "Startup should include image scanner"
        assert 'website' in startup_ids, "Startup should include website scanner"
        assert 'ai_model' in startup_ids, "Startup should include ai_model scanner"


class TestLicenseManagerScannerLimits:
    """Test scanner limits in license manager."""
    
    def test_usage_limits_scanner_types(self):
        """Test SCANNER_TYPES limits per tier via license generation."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            expected_limits = {
                LicenseType.TRIAL: 3,
                LicenseType.STARTUP: 6,
                LicenseType.PROFESSIONAL: 8,
                LicenseType.GROWTH: 10,
                LicenseType.SCALE: 12,
                LicenseType.ENTERPRISE: 12,
                LicenseType.GOVERNMENT: 12,
            }
            
            for license_type, expected_scanner_count in expected_limits.items():
                license_config = manager.generate_license(
                    license_type=license_type,
                    customer_id=f"TEST-{license_type.value}",
                    customer_name="Test User",
                    company_name="Test Company",
                    email="test@example.com",
                    validity_days=30
                )
                scanner_count = len(license_config.allowed_scanners)
                assert scanner_count == expected_scanner_count, \
                    f"{license_type.value}: expected {expected_scanner_count} scanners, got {scanner_count}"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_allowed_scanners_generation(self):
        """Test allowed_scanners list matches tier limits."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            test_cases = [
                (LicenseType.TRIAL, 3),
                (LicenseType.STARTUP, 6),
                (LicenseType.PROFESSIONAL, 8),
                (LicenseType.GROWTH, 10),
                (LicenseType.SCALE, 12),
                (LicenseType.ENTERPRISE, 12),
            ]
            
            for license_type, expected_count in test_cases:
                license_config = manager.generate_license(
                    license_type=license_type,
                    customer_id=f"TEST-{license_type.value}",
                    customer_name="Test User",
                    company_name="Test Company",
                    email="test@example.com",
                    validity_days=30
                )
                
                allowed_scanners = license_config.allowed_scanners
                assert len(allowed_scanners) == expected_count, \
                    f"{license_type.value}: expected {expected_count} allowed_scanners, got {len(allowed_scanners)}"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_scanner_order_consistency(self):
        """Test scanner order is consistent between page and license manager."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            manager = LicenseManager(license_file=temp_file, encrypt_license=False)
            
            enterprise_license = manager.generate_license(
                license_type=LicenseType.ENTERPRISE,
                customer_id="TEST-ENTERPRISE",
                customer_name="Test User",
                company_name="Test Company",
                email="test@example.com",
                validity_days=30
            )
            
            page_scanners, _ = get_available_scanners_for_tier('enterprise')
            page_scanner_ids = [s[0] for s in page_scanners]
            license_scanner_ids = enterprise_license.allowed_scanners
            
            assert page_scanner_ids == license_scanner_ids, \
                f"Scanner order mismatch: page={page_scanner_ids}, license={license_scanner_ids}"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestPricingConfigConsistency:
    """Test pricing configuration consistency."""
    
    def test_pricing_tiers_exist(self):
        """Test all pricing tiers are defined."""
        from config.pricing_config import PricingTier
        
        expected_tiers = [
            'STARTUP', 'PROFESSIONAL', 'GROWTH', 'SCALE',
            'ENTERPRISE', 'GOVERNMENT'
        ]
        
        for tier in expected_tiers:
            assert hasattr(PricingTier, tier), f"Missing pricing tier: {tier}"
    
    def test_pricing_values_defined(self):
        """Test pricing values are properly set."""
        from config.pricing_config import get_pricing_config, PricingTier
        
        config = get_pricing_config()
        
        test_tiers = [
            'startup', 'professional', 'growth', 'scale', 'enterprise'
        ]
        
        for tier_name in test_tiers:
            tier_config = config.pricing_data['tiers'].get(tier_name)
            assert tier_config is not None, f"No config for tier: {tier_name}"
            assert tier_config.get('monthly_price', 0) > 0, f"No price for tier: {tier_name}"
    
    def test_enterprise_pricing_consistent(self):
        """Test Enterprise tier pricing is consistent between pricing_config and license_manager."""
        from config.pricing_config import get_pricing_config
        
        config = get_pricing_config()
        enterprise_tier = config.pricing_data['tiers'].get('enterprise')
        
        assert enterprise_tier is not None, "Enterprise tier should exist"
        
        monthly_price = enterprise_tier.get('monthly_price')
        assert monthly_price is not None, "Enterprise should have monthly_price defined"
        assert monthly_price > 0, "Enterprise monthly_price should be positive"
        assert monthly_price >= 1000, "Enterprise should be premium tier (>= €1000)"
        
        scale_tier = config.pricing_data['tiers'].get('scale')
        if scale_tier and scale_tier.get('monthly_price'):
            assert monthly_price > scale_tier.get('monthly_price'), \
                "Enterprise should cost more than Scale tier"


class TestScannerAllocation:
    """Test 12-scanner allocation across tiers."""
    
    def test_all_12_scanners_defined(self):
        """Test all 12 scanners are defined."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        all_available, all_locked = get_available_scanners_for_tier('enterprise')
        total_scanners = len(all_available) + len(all_locked)
        
        assert total_scanners == 12, f"Expected 12 total scanners, got {total_scanners}"
    
    def test_scanner_ids_are_valid(self):
        """Test scanner IDs are valid identifiers."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        expected_ids = [
            'code', 'document', 'database', 'image', 'website', 'ai_model',
            'dpia', 'soc2', 'enterprise', 'sustainability', 'audio_video', 'advanced_ai'
        ]
        
        all_scanners, _ = get_available_scanners_for_tier('enterprise')
        actual_ids = [s[0] for s in all_scanners]
        
        assert actual_ids == expected_ids, \
            f"Scanner IDs mismatch: expected {expected_ids}, got {actual_ids}"
    
    def test_core_scanners_available_to_all_tiers(self):
        """Test core scanners (code, document, database) are in all tiers."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        core_scanners = ['code', 'document', 'database']
        
        for tier in ['trial', 'startup', 'professional', 'growth', 'scale', 'enterprise']:
            available, _ = get_available_scanners_for_tier(tier)
            available_ids = [s[0] for s in available]
            
            for scanner in core_scanners:
                assert scanner in available_ids, \
                    f"Core scanner '{scanner}' missing from tier '{tier}'"
    
    def test_premium_scanners_only_in_higher_tiers(self):
        """Test audio_video and advanced_ai are only in Scale/Enterprise."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        premium_scanners = ['audio_video', 'advanced_ai']
        
        for tier in ['trial', 'startup', 'professional', 'growth']:
            available, locked = get_available_scanners_for_tier(tier)
            available_ids = [s[0] for s in available]
            locked_ids = [s[0] for s in locked]
            
            for scanner in premium_scanners:
                assert scanner not in available_ids, \
                    f"Premium scanner '{scanner}' should not be in tier '{tier}'"
                assert scanner in locked_ids, \
                    f"Premium scanner '{scanner}' should be locked in tier '{tier}'"
        
        for tier in ['scale', 'enterprise']:
            available, _ = get_available_scanners_for_tier(tier)
            available_ids = [s[0] for s in available]
            
            for scanner in premium_scanners:
                assert scanner in available_ids, \
                    f"Premium scanner '{scanner}' should be available in tier '{tier}'"


class TestLockedScannerDisplay:
    """Test locked scanner upgrade flow."""
    
    def test_locked_scanners_returned_for_lower_tiers(self):
        """Test locked scanners are properly returned for lower tiers."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        test_cases = [
            ('trial', 9),
            ('startup', 6),
            ('professional', 4),
            ('growth', 2),
            ('scale', 0),
            ('enterprise', 0),
        ]
        
        for tier, expected_locked in test_cases:
            _, locked = get_available_scanners_for_tier(tier)
            assert len(locked) == expected_locked, \
                f"Tier {tier}: expected {expected_locked} locked scanners, got {len(locked)}"
    
    def test_locked_scanners_have_descriptions(self):
        """Test locked scanners include descriptions for upgrade display."""
        from page_modules.scanner import get_available_scanners_for_tier
        
        _, locked = get_available_scanners_for_tier('trial')
        
        for scanner_id, scanner_desc in locked:
            assert scanner_id, "Scanner ID should not be empty"
            assert scanner_desc, f"Scanner {scanner_id} should have a description"
            assert len(scanner_desc) > 10, f"Scanner {scanner_id} description too short"


class TestPricingDisplayScannerInfo:
    """Test pricing display shows scanner information."""
    
    def test_tier_scanner_count_function(self):
        """Test get_tier_scanner_count returns correct values."""
        from components.pricing_display import get_tier_scanner_count, PricingTier
        
        test_cases = [
            (PricingTier.STARTUP, 6),
            (PricingTier.PROFESSIONAL, 8),
            (PricingTier.GROWTH, 10),
            (PricingTier.SCALE, 12),
            (PricingTier.ENTERPRISE, 12),
        ]
        
        for tier, expected_count in test_cases:
            count, scanner_list = get_tier_scanner_count(tier)
            assert count == expected_count, \
                f"Tier {tier}: expected scanner count {expected_count}, got {count}"
            assert len(scanner_list) > 0, \
                f"Tier {tier}: scanner list should not be empty"
    
    def test_key_features_include_scanner_info(self):
        """Test key features mention scanner counts."""
        from components.pricing_display import get_tier_key_features, PricingTier
        
        test_tiers = [
            PricingTier.STARTUP,
            PricingTier.PROFESSIONAL,
            PricingTier.GROWTH,
            PricingTier.SCALE,
        ]
        
        for tier in test_tiers:
            features = get_tier_key_features(tier)
            has_scanner_mention = any('scanner' in f.lower() for f in features)
            assert has_scanner_mention, \
                f"Tier {tier}: features should mention scanners"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
