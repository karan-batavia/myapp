"""
Unit tests for free user restrictions feature
Tests the pricing config utility functions and access controls
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPricingTierEnum:
    """Test PricingTier enum includes FREE tier"""
    
    def test_free_tier_exists(self):
        """Verify FREE tier is defined in PricingTier enum"""
        from config.pricing_config import PricingTier
        assert hasattr(PricingTier, 'FREE')
        assert PricingTier.FREE.value == 'free'
    
    def test_all_tiers_exist(self):
        """Verify all expected tiers exist"""
        from config.pricing_config import PricingTier
        expected_tiers = ['FREE', 'STARTUP', 'PROFESSIONAL', 'GROWTH', 'SCALE', 
                         'SALESFORCE_PREMIUM', 'SAP_ENTERPRISE', 'ENTERPRISE', 'GOVERNMENT']
        for tier in expected_tiers:
            assert hasattr(PricingTier, tier), f"Missing tier: {tier}"


class TestIsFreeUser:
    """Test is_free_user() function"""
    
    @patch('streamlit.session_state', {'user_tier': 'free', 'subscription_id': None})
    def test_free_user_no_subscription(self):
        """User with no subscription is free"""
        from config.pricing_config import is_free_user
        assert is_free_user() == True
    
    @patch('streamlit.session_state', {'user_tier': '', 'subscription_id': ''})
    def test_free_user_empty_tier(self):
        """User with empty tier is free"""
        from config.pricing_config import is_free_user
        assert is_free_user() == True
    
    @patch('streamlit.session_state', {'user_tier': 'professional', 'subscription_id': 'sub_123abc'})
    def test_paid_user_with_subscription(self):
        """User with subscription_id is paid"""
        from config.pricing_config import is_free_user
        assert is_free_user() == False
    
    @patch('streamlit.session_state', {'user_tier': 'startup', 'subscription_id': 'sub_xyz789'})
    def test_startup_tier_with_subscription(self):
        """Startup tier with subscription is paid"""
        from config.pricing_config import is_free_user
        assert is_free_user() == False


class TestCanDownloadReports:
    """Test can_download_reports() function"""
    
    @patch('config.pricing_config.is_free_user')
    def test_free_user_cannot_download(self, mock_is_free):
        """Free users cannot download reports"""
        mock_is_free.return_value = True
        
        from config.pricing_config import can_download_reports
        assert can_download_reports() == False
    
    @patch('config.pricing_config.is_free_user')
    def test_paid_user_can_download(self, mock_is_free):
        """Paid users can download reports"""
        mock_is_free.return_value = False
        
        from config.pricing_config import can_download_reports
        assert can_download_reports() == True


class TestFreeUserScanCount:
    """Test scan view counting for free users"""
    
    @patch('streamlit.session_state', {'free_user_scan_views': 0})
    def test_initial_scan_count_zero(self):
        """Initial scan count should be zero"""
        from config.pricing_config import get_free_user_scan_count
        assert get_free_user_scan_count() == 0
    
    def test_increment_scan_view(self):
        """Incrementing scan view should increase count"""
        mock_session = {'free_user_scan_views': 0}
        
        with patch('streamlit.session_state', mock_session):
            from config.pricing_config import increment_free_user_scan_view
            increment_free_user_scan_view()
            assert mock_session['free_user_scan_views'] == 1
    
    def test_scan_count_increments_multiple(self):
        """Scan count should increment correctly multiple times"""
        mock_session = {'free_user_scan_views': 2}
        
        with patch('streamlit.session_state', mock_session):
            from config.pricing_config import increment_free_user_scan_view
            increment_free_user_scan_view()
            assert mock_session['free_user_scan_views'] == 3


class TestCanViewScanResults:
    """Test can_view_scan_results() function"""
    
    @patch('config.pricing_config.is_free_user')
    @patch('config.pricing_config.get_free_user_scan_count')
    def test_paid_user_unlimited_views(self, mock_count, mock_is_free):
        """Paid users have unlimited views"""
        mock_is_free.return_value = False
        mock_count.return_value = 100
        
        from config.pricing_config import can_view_scan_results
        assert can_view_scan_results() == True
    
    @patch('config.pricing_config.is_free_user')
    @patch('config.pricing_config.get_free_user_scan_count')
    def test_free_user_under_limit(self, mock_count, mock_is_free):
        """Free user under 3 views can view"""
        mock_is_free.return_value = True
        mock_count.return_value = 2
        
        from config.pricing_config import can_view_scan_results
        assert can_view_scan_results() == True
    
    @patch('config.pricing_config.is_free_user')
    @patch('config.pricing_config.get_free_user_scan_count')
    def test_free_user_at_limit(self, mock_count, mock_is_free):
        """Free user at 3 views cannot view more"""
        mock_is_free.return_value = True
        mock_count.return_value = 3
        
        from config.pricing_config import can_view_scan_results
        assert can_view_scan_results() == False
    
    @patch('config.pricing_config.is_free_user')
    @patch('config.pricing_config.get_free_user_scan_count')
    def test_free_user_over_limit(self, mock_count, mock_is_free):
        """Free user over 3 views cannot view"""
        mock_is_free.return_value = True
        mock_count.return_value = 5
        
        from config.pricing_config import can_view_scan_results
        assert can_view_scan_results() == False
    
    @patch('config.pricing_config.is_free_user')
    @patch('config.pricing_config.get_free_user_scan_count')
    def test_free_user_zero_views(self, mock_count, mock_is_free):
        """Free user with zero views can view"""
        mock_is_free.return_value = True
        mock_count.return_value = 0
        
        from config.pricing_config import can_view_scan_results
        assert can_view_scan_results() == True


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @patch('streamlit.session_state', {'user_tier': None, 'subscription_id': None})
    def test_none_tier_is_free(self):
        """None tier should be treated as free"""
        from config.pricing_config import is_free_user
        assert is_free_user() == True
    
    @patch('streamlit.session_state', {'user_tier': 'Free', 'subscription_id': None})
    def test_case_insensitive_free(self):
        """Free tier check should handle 'Free' case"""
        from config.pricing_config import is_free_user
        assert is_free_user() == True
    
    @patch('streamlit.session_state', {'user_tier': 'free', 'subscription_id': 'sub_active123'})
    def test_subscription_overrides_free_tier(self):
        """Having subscription_id makes user paid even with free tier"""
        from config.pricing_config import is_free_user
        assert is_free_user() == False
    
    @patch('streamlit.session_state', {})
    def test_missing_session_keys(self):
        """Missing session keys should default to free"""
        from config.pricing_config import is_free_user
        assert is_free_user() == True


class TestIntegration:
    """Integration tests for the complete flow"""
    
    @patch('streamlit.session_state', {'user_tier': 'free', 'subscription_id': None, 'free_user_scan_views': 0})
    def test_free_user_first_view(self):
        """Free user's first view should be allowed"""
        from config.pricing_config import is_free_user, can_view_scan_results, can_download_reports
        
        assert is_free_user() == True
        assert can_view_scan_results() == True
        assert can_download_reports() == False
    
    @patch('streamlit.session_state', {'user_tier': 'professional', 'subscription_id': 'sub_123', 'free_user_scan_views': 10})
    def test_paid_user_full_access(self):
        """Paid user should have full access regardless of view count"""
        from config.pricing_config import is_free_user, can_view_scan_results, can_download_reports
        
        assert is_free_user() == False
        assert can_view_scan_results() == True
        assert can_download_reports() == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
