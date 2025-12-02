#!/usr/bin/env python3
"""
Comprehensive Unit Tests for User Management System
Tests: CRUD operations, role assignment, tier management, usage tracking, billing verification
"""

import pytest
import os
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.user_management_service import (
    UserManagementService, 
    get_user_management_service,
    TIER_LIMITS,
    ROLE_DESCRIPTIONS,
    UserRole,
    LicenseTier
)


class TestUserManagementService:
    """Test suite for UserManagementService"""
    
    @pytest.fixture
    def ums(self):
        """Get UserManagementService instance"""
        return get_user_management_service()
    
    @pytest.fixture
    def test_user_data(self):
        """Test user data fixture"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        return {
            'username': f'test_user_{unique_id}',
            'email': f'test_{unique_id}@example.com',
            'password': 'TestPassword123!',
            'role': 'user',
            'company_name': 'Test Company',
            'license_tier': 'startup'
        }
    
    # ==================== USER CRUD TESTS ====================
    
    class TestUserCreation:
        """Tests for user creation"""
        
        def test_create_user_success(self, ums, test_user_data):
            """Test successful user creation"""
            success, message, user_id = ums.create_user(**test_user_data)
            
            assert success is True
            assert "successfully" in message.lower()
            assert user_id is not None
            assert isinstance(user_id, int)
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_create_user_duplicate_username(self, ums, test_user_data):
            """Test duplicate username rejection"""
            # Create first user
            success1, _, user_id = ums.create_user(**test_user_data)
            assert success1 is True
            
            # Try to create duplicate
            success2, message, _ = ums.create_user(**test_user_data)
            assert success2 is False
            assert "already exists" in message.lower()
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_create_user_duplicate_email(self, ums, test_user_data):
            """Test duplicate email rejection"""
            # Create first user
            success1, _, user_id = ums.create_user(**test_user_data)
            assert success1 is True
            
            # Try with same email but different username
            test_user_data['username'] = test_user_data['username'] + '_v2'
            success2, message, _ = ums.create_user(**test_user_data)
            assert success2 is False
            assert "already exists" in message.lower()
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_create_user_with_all_roles(self, ums):
            """Test user creation with all valid roles"""
            import uuid
            created_ids = []
            
            for role in ROLE_DESCRIPTIONS.keys():
                unique_id = str(uuid.uuid4())[:8]
                success, _, user_id = ums.create_user(
                    username=f'role_test_{role}_{unique_id}',
                    email=f'{role}_{unique_id}@test.com',
                    password='TestPass123!',
                    role=role,
                    license_tier='startup'
                )
                assert success is True, f"Failed to create user with role: {role}"
                created_ids.append(user_id)
            
            # Cleanup
            for uid in created_ids:
                ums.delete_user(uid)
        
        def test_create_user_with_all_tiers(self, ums):
            """Test user creation with all license tiers"""
            import uuid
            created_ids = []
            
            for tier in TIER_LIMITS.keys():
                unique_id = str(uuid.uuid4())[:8]
                success, _, user_id = ums.create_user(
                    username=f'tier_test_{tier}_{unique_id}',
                    email=f'{tier}_{unique_id}@test.com',
                    password='TestPass123!',
                    role='user',
                    license_tier=tier
                )
                assert success is True, f"Failed to create user with tier: {tier}"
                created_ids.append(user_id)
            
            # Cleanup
            for uid in created_ids:
                ums.delete_user(uid)
    
    class TestUserRetrieval:
        """Tests for user retrieval"""
        
        def test_get_user_by_id(self, ums, test_user_data):
            """Test retrieving user by ID"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            user = ums.get_user(user_id=user_id)
            assert user is not None
            assert user['username'] == test_user_data['username']
            assert user['email'] == test_user_data['email']
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_get_user_by_username(self, ums, test_user_data):
            """Test retrieving user by username"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            user = ums.get_user(username=test_user_data['username'])
            assert user is not None
            assert user['id'] == user_id
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_get_user_by_email(self, ums, test_user_data):
            """Test retrieving user by email"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            user = ums.get_user(email=test_user_data['email'])
            assert user is not None
            assert user['id'] == user_id
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_get_nonexistent_user(self, ums):
            """Test retrieving non-existent user returns None"""
            user = ums.get_user(user_id=999999)
            assert user is None
            
            user = ums.get_user(username='nonexistent_user_xyz')
            assert user is None
    
    class TestUserUpdate:
        """Tests for user updates"""
        
        def test_update_user_email(self, ums, test_user_data):
            """Test updating user email"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            new_email = 'updated_' + test_user_data['email']
            update_success, message = ums.update_user(
                user_id, 
                {'email': new_email},
                updated_by='test'
            )
            
            assert update_success is True
            
            user = ums.get_user(user_id=user_id)
            assert user['email'] == new_email
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_update_user_role(self, ums, test_user_data):
            """Test updating user role"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            update_success, _ = ums.update_user(
                user_id,
                {'role': 'analyst'},
                updated_by='test'
            )
            
            assert update_success is True
            
            user = ums.get_user(user_id=user_id)
            assert user['role'] == 'analyst'
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_update_user_tier(self, ums, test_user_data):
            """Test updating user license tier"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            update_success, _ = ums.update_user(
                user_id,
                {'license_tier': 'enterprise'},
                updated_by='test'
            )
            
            assert update_success is True
            
            user = ums.get_user(user_id=user_id)
            assert user['license_tier'] == 'enterprise'
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_update_user_invalid_field(self, ums, test_user_data):
            """Test that invalid fields are ignored"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            update_success, message = ums.update_user(
                user_id,
                {'invalid_field': 'value'},
                updated_by='test'
            )
            
            assert update_success is False
            assert "no valid fields" in message.lower()
            
            # Cleanup
            ums.delete_user(user_id)
    
    class TestUserDeletion:
        """Tests for user deletion (soft delete)"""
        
        def test_delete_user(self, ums, test_user_data):
            """Test soft delete user"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            delete_success, message = ums.delete_user(user_id, deleted_by='test')
            assert delete_success is True
            assert "deactivated" in message.lower()
            
            # User should still exist but be inactive
            user = ums.get_user(user_id=user_id)
            assert user is not None
            assert user['is_active'] is False
        
        def test_delete_nonexistent_user(self, ums):
            """Test deleting non-existent user"""
            delete_success, message = ums.delete_user(999999, deleted_by='test')
            assert delete_success is False
            assert "not found" in message.lower()
    
    class TestUserListing:
        """Tests for listing users"""
        
        def test_list_users(self, ums):
            """Test listing all active users"""
            users = ums.list_users()
            assert isinstance(users, list)
        
        def test_list_users_with_role_filter(self, ums, test_user_data):
            """Test listing users filtered by role"""
            test_user_data['role'] = 'analyst'
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            users = ums.list_users(role_filter='analyst')
            assert all(u['role'] == 'analyst' for u in users)
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_list_users_with_tier_filter(self, ums, test_user_data):
            """Test listing users filtered by tier"""
            test_user_data['license_tier'] = 'growth'
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            users = ums.list_users(tier_filter='growth')
            assert all(u['license_tier'] == 'growth' for u in users)
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_list_users_include_inactive(self, ums, test_user_data):
            """Test listing including inactive users"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            ums.delete_user(user_id)  # Soft delete
            
            # Should not appear in active list
            active_users = ums.list_users(include_inactive=False)
            active_ids = [u['id'] for u in active_users]
            assert user_id not in active_ids
            
            # Should appear in list including inactive
            all_users = ums.list_users(include_inactive=True)
            all_ids = [u['id'] for u in all_users]
            assert user_id in all_ids
        
        def test_get_user_count(self, ums):
            """Test getting user counts"""
            counts = ums.get_user_count()
            
            assert 'total' in counts
            assert 'by_role' in counts
            assert 'by_tier' in counts
            assert isinstance(counts['total'], int)
            assert isinstance(counts['by_role'], dict)
            assert isinstance(counts['by_tier'], dict)
    
    # ==================== USAGE TRACKING TESTS ====================
    
    class TestUsageTracking:
        """Tests for feature usage tracking"""
        
        def test_track_feature_usage(self, ums, test_user_data):
            """Test tracking feature usage"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Track usage
            track_result = ums.track_feature_usage(
                user_id, 
                'document_scanner', 
                'scanner',
                {'file_type': 'pdf'}
            )
            assert track_result is True
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_track_multiple_usages(self, ums, test_user_data):
            """Test tracking multiple usages"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Track multiple usages
            for i in range(5):
                ums.track_feature_usage(user_id, 'website_scanner', 'scanner')
            
            usage = ums.get_usage_summary(user_id, 'month')
            assert usage['total_scans'] >= 5
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_get_usage_summary(self, ums, test_user_data):
            """Test getting usage summary"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            ums.track_feature_usage(user_id, 'document_scanner', 'scanner')
            ums.track_feature_usage(user_id, 'gdpr_check', 'feature')
            
            usage = ums.get_usage_summary(user_id, 'month')
            
            assert 'period' in usage
            assert 'total_scans' in usage
            assert 'scanner_breakdown' in usage
            assert 'feature_breakdown' in usage
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_get_remaining_scans(self, ums, test_user_data):
            """Test getting remaining scans"""
            test_user_data['license_tier'] = 'startup'  # 200 scans/month
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Track some usage
            for i in range(10):
                ums.track_feature_usage(user_id, 'document_scanner', 'scanner')
            
            remaining = ums.get_remaining_scans(user_id)
            
            assert 'remaining' in remaining
            assert 'limit' in remaining
            assert 'used' in remaining
            assert remaining['limit'] == 200
            assert remaining['used'] >= 10
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_unlimited_tier_remaining_scans(self, ums, test_user_data):
            """Test remaining scans for unlimited tier"""
            test_user_data['license_tier'] = 'enterprise'  # Unlimited
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            remaining = ums.get_remaining_scans(user_id)
            assert remaining['remaining'] == 'Unlimited'
            assert remaining['limit'] == 'Unlimited'
            
            # Cleanup
            ums.delete_user(user_id)
    
    # ==================== BILLING VERIFICATION TESTS ====================
    
    class TestBillingVerification:
        """Tests for billing compliance verification"""
        
        def test_billing_compliance_within_limits(self, ums, test_user_data):
            """Test user within billing limits is compliant"""
            test_user_data['license_tier'] = 'professional'  # 350 scans
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Track a few scans (well within limit)
            for i in range(5):
                ums.track_feature_usage(user_id, 'document_scanner', 'scanner')
            
            compliance = ums.verify_billing_compliance(user_id)
            
            assert compliance['compliant'] is True
            assert compliance['tier'] == 'professional'
            assert len(compliance.get('issues', [])) == 0
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_billing_compliance_unlimited_tier(self, ums, test_user_data):
            """Test unlimited tier is always compliant"""
            test_user_data['license_tier'] = 'enterprise'
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Track many scans
            for i in range(100):
                ums.track_feature_usage(user_id, 'document_scanner', 'scanner')
            
            compliance = ums.verify_billing_compliance(user_id)
            
            assert compliance['compliant'] is True
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_billing_compliance_response_structure(self, ums, test_user_data):
            """Test billing compliance response has all required fields"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            compliance = ums.verify_billing_compliance(user_id)
            
            assert 'user_id' in compliance
            assert 'username' in compliance
            assert 'tier' in compliance
            assert 'tier_price' in compliance
            assert 'compliant' in compliance
            assert 'scan_usage' in compliance
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_generate_billing_report(self, ums):
            """Test generating billing report for all users"""
            report = ums.generate_billing_report()
            
            assert isinstance(report, list)
            
            if report:
                for entry in report:
                    assert 'username' in entry
                    assert 'tier' in entry
                    assert 'compliant' in entry
    
    # ==================== TIER AND ROLE TESTS ====================
    
    class TestTierManagement:
        """Tests for tier information and access control"""
        
        def test_get_tier_info(self, ums):
            """Test getting tier information"""
            for tier_name in TIER_LIMITS.keys():
                tier_info = ums.get_tier_info(tier_name)
                
                assert 'price_monthly' in tier_info
                assert 'scans_per_month' in tier_info
                assert 'users' in tier_info
                assert 'scanners' in tier_info
                assert 'features' in tier_info
        
        def test_get_all_tiers(self, ums):
            """Test getting all tiers"""
            tiers = ums.get_all_tiers()
            
            assert 'trial' in tiers
            assert 'startup' in tiers
            assert 'professional' in tiers
            assert 'growth' in tiers
            assert 'scale' in tiers
            assert 'enterprise' in tiers
        
        def test_get_all_roles(self, ums):
            """Test getting all roles"""
            roles = ums.get_all_roles()
            
            assert 'admin' in roles
            assert 'user' in roles
            assert 'analyst' in roles
            assert 'viewer' in roles
        
        def test_can_access_feature(self, ums, test_user_data):
            """Test feature access checking"""
            test_user_data['license_tier'] = 'professional'
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Professional tier should have gdpr_compliance
            can_access = ums.can_access_feature(user_id, 'gdpr_compliance')
            assert can_access is True
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_can_use_scanner(self, ums, test_user_data):
            """Test scanner access checking"""
            test_user_data['license_tier'] = 'startup'
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Startup tier should have document scanner
            can_use = ums.can_use_scanner(user_id, 'document')
            assert can_use is True
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_enterprise_has_all_access(self, ums, test_user_data):
            """Test enterprise tier has access to everything"""
            test_user_data['license_tier'] = 'enterprise'
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Should have access to all features and scanners
            assert ums.can_access_feature(user_id, 'any_feature') is True
            assert ums.can_use_scanner(user_id, 'any_scanner') is True
            
            # Cleanup
            ums.delete_user(user_id)
    
    # ==================== ACTIVITY LOGGING TESTS ====================
    
    class TestActivityLogging:
        """Tests for user activity logging"""
        
        def test_record_login(self, ums, test_user_data):
            """Test recording user login"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Record login
            ums.record_login(user_id, ip_address='192.168.1.1')
            
            # Check login count increased
            user = ums.get_user(user_id=user_id)
            assert user['login_count'] >= 1
            assert user['last_login'] is not None
            
            # Cleanup
            ums.delete_user(user_id)
        
        def test_get_user_activity(self, ums, test_user_data):
            """Test getting user activity log"""
            success, _, user_id = ums.create_user(**test_user_data)
            assert success is True
            
            # Activity should include creation
            activity = ums.get_user_activity(user_id, limit=10)
            
            assert isinstance(activity, list)
            
            # Cleanup
            ums.delete_user(user_id)
    
    # ==================== EXPORT TESTS ====================
    
    class TestExport:
        """Tests for data export functionality"""
        
        def test_export_users_csv(self, ums):
            """Test exporting users to CSV"""
            csv_data = ums.export_users_csv()
            
            assert isinstance(csv_data, str)
            
            if csv_data:
                lines = csv_data.split('\n')
                # Should have header
                assert len(lines) >= 1
                
                # Check header contains expected columns
                header = lines[0]
                assert 'Username' in header
                assert 'Email' in header
                assert 'Role' in header
    
    # ==================== TIER LIMITS VALIDATION ====================
    
    class TestTierLimitsConfiguration:
        """Tests for tier limits configuration"""
        
        def test_tier_prices(self):
            """Test tier prices are correctly defined"""
            assert TIER_LIMITS['trial']['price_monthly'] == 0
            assert TIER_LIMITS['startup']['price_monthly'] == 59
            assert TIER_LIMITS['professional']['price_monthly'] == 99
            assert TIER_LIMITS['growth']['price_monthly'] == 179
            assert TIER_LIMITS['scale']['price_monthly'] == 499
            assert TIER_LIMITS['enterprise']['price_monthly'] == 1199
        
        def test_tier_scan_limits(self):
            """Test tier scan limits are correctly defined"""
            assert TIER_LIMITS['trial']['scans_per_month'] == 10
            assert TIER_LIMITS['startup']['scans_per_month'] == 200
            assert TIER_LIMITS['professional']['scans_per_month'] == 350
            assert TIER_LIMITS['growth']['scans_per_month'] == 750
            assert TIER_LIMITS['scale']['scans_per_month'] == -1  # Unlimited
            assert TIER_LIMITS['enterprise']['scans_per_month'] == -1  # Unlimited
        
        def test_tier_user_limits(self):
            """Test tier user limits"""
            assert TIER_LIMITS['trial']['users'] == 1
            assert TIER_LIMITS['startup']['users'] == 3
            assert TIER_LIMITS['professional']['users'] == 5
            assert TIER_LIMITS['growth']['users'] == 10
            assert TIER_LIMITS['scale']['users'] == 25
            assert TIER_LIMITS['enterprise']['users'] == -1  # Unlimited


# ==================== PASSWORD VERIFICATION TESTS ====================

class TestPasswordVerification:
    """Tests for password hashing and verification"""
    
    @pytest.fixture
    def ums(self):
        return get_user_management_service()
    
    def test_password_hash_is_not_plaintext(self, ums):
        """Test that password is hashed, not stored as plaintext"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        password = 'MySecretPassword123!'
        
        success, _, user_id = ums.create_user(
            username=f'pw_test_{unique_id}',
            email=f'pw_{unique_id}@test.com',
            password=password,
            role='user',
            license_tier='trial'
        )
        assert success is True
        
        user = ums.get_user(user_id=user_id)
        
        # Password hash should not be the plaintext password
        assert user['password_hash'] != password
        # Password hash should be significantly longer (bcrypt hash)
        assert len(user['password_hash']) > 50
        
        # Cleanup
        ums.delete_user(user_id)
    
    def test_password_verification(self, ums):
        """Test password verification works correctly"""
        password = 'TestPassword123!'
        
        # Test internal verification method
        hashed = ums._hash_password(password)
        
        assert ums._verify_password(password, hashed) is True
        assert ums._verify_password('WrongPassword', hashed) is False


# ==================== INTEGRATION TESTS ====================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def ums(self):
        return get_user_management_service()
    
    def test_full_user_lifecycle(self, ums):
        """Test complete user lifecycle: create -> update -> track -> verify -> delete"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # 1. Create user
        success, _, user_id = ums.create_user(
            username=f'lifecycle_{unique_id}',
            email=f'lifecycle_{unique_id}@test.com',
            password='Test123!',
            role='user',
            company_name='Lifecycle Corp',
            license_tier='professional'
        )
        assert success is True
        
        # 2. Update user
        update_success, _ = ums.update_user(
            user_id,
            {'role': 'analyst', 'company_name': 'Updated Corp'}
        )
        assert update_success is True
        
        # 3. Track usage
        for _ in range(3):
            ums.track_feature_usage(user_id, 'document_scanner', 'scanner')
        
        # 4. Record login
        ums.record_login(user_id, ip_address='10.0.0.1')
        
        # 5. Verify usage
        usage = ums.get_usage_summary(user_id, 'month')
        assert usage['total_scans'] >= 3
        
        # 6. Check billing compliance
        compliance = ums.verify_billing_compliance(user_id)
        assert compliance['compliant'] is True
        
        # 7. Get remaining scans
        remaining = ums.get_remaining_scans(user_id)
        assert remaining['limit'] == 350  # Professional tier
        
        # 8. Check activity log
        activity = ums.get_user_activity(user_id)
        assert len(activity) > 0
        
        # 9. Delete (soft delete)
        delete_success, _ = ums.delete_user(user_id)
        assert delete_success is True
        
        # 10. Verify deactivated
        user = ums.get_user(user_id=user_id)
        assert user['is_active'] is False
    
    def test_admin_can_see_all_users(self, ums):
        """Test that admin user can see all users"""
        # Get all users
        users = ums.list_users(include_inactive=True)
        
        # Verify vishaal314 exists as admin
        vishaal = ums.get_user(username='vishaal314')
        assert vishaal is not None
        assert vishaal['role'] == 'admin'
        
        # Admin should be able to see all users (implicit in list_users)
        assert len(users) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
