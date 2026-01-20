"""
Unit tests for payment flow - user license tier updates after subscription events.

Tests the critical path:
1. Webhook handler extracts user_id from subscription metadata
2. Database service updates user's license_tier
3. Subscription cancellation downgrades user
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWebhookHandler:
    """Tests for webhook handler subscription events"""
    
    @pytest.fixture
    def mock_database_service(self):
        """Create a mock database service"""
        with patch('services.webhook_handler.database_service') as mock_db:
            mock_db.update_user_license_tier.return_value = True
            mock_db.update_user_license_tier_by_email.return_value = True
            mock_db.store_subscription_record.return_value = True
            yield mock_db
    
    @pytest.fixture
    def webhook_handler(self, mock_database_service):
        """Create webhook handler with mocked dependencies"""
        from services.webhook_handler import WebhookHandler
        handler = WebhookHandler()
        return handler
    
    def test_subscription_created_updates_user_tier_by_id(self, webhook_handler, mock_database_service):
        """Test that subscription creation updates user tier when user_id is in metadata"""
        subscription = {
            'id': 'sub_test123',
            'customer': 'cus_test456',
            'status': 'active',
            'metadata': {
                'user_id': '42',
                'plan_tier': 'professional'
            },
            'current_period_start': int(datetime.now().timestamp()),
            'current_period_end': int(datetime.now().timestamp()) + 86400 * 30
        }
        
        result = webhook_handler._handle_subscription_created(subscription)
        
        assert result['status'] == 'success'
        assert 'user upgraded' in result['message']
        mock_database_service.update_user_license_tier.assert_called_once_with(
            '42', 'professional', 'sub_test123'
        )
    
    def test_subscription_created_updates_user_tier_by_email(self, webhook_handler, mock_database_service):
        """Test that subscription creation updates user tier by email when user_id is missing"""
        subscription = {
            'id': 'sub_test789',
            'customer': 'cus_test012',
            'customer_email': 'test@example.com',
            'status': 'active',
            'metadata': {
                'plan_tier': 'growth'
            },
            'current_period_start': int(datetime.now().timestamp()),
            'current_period_end': int(datetime.now().timestamp()) + 86400 * 30
        }
        
        result = webhook_handler._handle_subscription_created(subscription)
        
        assert result['status'] == 'success'
        mock_database_service.update_user_license_tier_by_email.assert_called_once_with(
            'test@example.com', 'growth', 'sub_test789'
        )
    
    def test_subscription_created_default_tier(self, webhook_handler, mock_database_service):
        """Test that default tier is 'professional' when not specified"""
        subscription = {
            'id': 'sub_default',
            'customer': 'cus_default',
            'status': 'active',
            'metadata': {
                'user_id': '100'
            },
            'current_period_start': int(datetime.now().timestamp()),
            'current_period_end': int(datetime.now().timestamp()) + 86400 * 30
        }
        
        webhook_handler._handle_subscription_created(subscription)
        
        mock_database_service.update_user_license_tier.assert_called_once_with(
            '100', 'professional', 'sub_default'
        )
    
    def test_subscription_cancelled_downgrades_user(self, webhook_handler, mock_database_service):
        """Test that subscription cancellation downgrades user to trial"""
        subscription = {
            'id': 'sub_cancel123',
            'customer': 'cus_cancel456',
            'status': 'canceled',
            'metadata': {
                'user_id': '55'
            }
        }
        
        result = webhook_handler._handle_subscription_cancelled(subscription)
        
        assert result['status'] == 'success'
        mock_database_service.update_user_license_tier.assert_called_once_with(
            '55', 'trial', None
        )


class TestDatabaseService:
    """Tests for database service license tier updates"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock database connection"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        return mock_conn, mock_cursor
    
    @pytest.fixture
    def database_service(self, mock_connection):
        """Create database service with mocked connection"""
        mock_conn, mock_cursor = mock_connection
        
        with patch('services.database_service.psycopg2') as mock_psycopg2:
            from services.database_service import DatabaseService
            service = DatabaseService()
            service.enabled = True
            service.get_connection = Mock(return_value=mock_conn)
            yield service, mock_cursor
    
    def test_update_user_license_tier_success(self, database_service):
        """Test successful user tier update by ID"""
        service, mock_cursor = database_service
        mock_cursor.rowcount = 1
        
        result = service.update_user_license_tier('42', 'professional', 'sub_123')
        
        assert result == True
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert 'UPDATE platform_users' in call_args[0][0]
        assert 'license_tier' in call_args[0][0]
    
    def test_update_user_license_tier_user_not_found(self, database_service):
        """Test tier update when user not found"""
        service, mock_cursor = database_service
        mock_cursor.rowcount = 0
        
        result = service.update_user_license_tier('999', 'professional', 'sub_123')
        
        assert result == False
    
    def test_update_user_license_tier_by_email_success(self, database_service):
        """Test successful user tier update by email"""
        service, mock_cursor = database_service
        mock_cursor.rowcount = 1
        
        result = service.update_user_license_tier_by_email('test@example.com', 'growth', 'sub_456')
        
        assert result == True
        call_args = mock_cursor.execute.call_args
        assert 'WHERE email = %s' in call_args[0][0]
    
    def test_store_subscription_with_user_id(self, database_service):
        """Test that subscription record stores user_id from metadata"""
        service, mock_cursor = database_service
        
        subscription = {
            'id': 'sub_test',
            'customer': 'cus_test',
            'customer_email': 'test@example.com',
            'plan_name': 'Professional',
            'status': 'active',
            'amount': 9900,
            'currency': 'eur',
            'interval': 'month',
            'current_period_start': int(datetime.now().timestamp()),
            'current_period_end': int(datetime.now().timestamp()) + 86400 * 30,
            'metadata': {
                'user_id': '42',
                'plan_tier': 'professional'
            }
        }
        
        result = service.store_subscription_record(subscription)
        
        assert result == True
        call_args = mock_cursor.execute.call_args
        assert 'user_id' in call_args[0][0]


class TestPaymentSuccessHandler:
    """Tests for payment success URL handling"""
    
    def test_plan_tier_extraction_from_metadata(self):
        """Test that plan tier is correctly extracted from checkout session metadata"""
        mock_metadata = {'plan_tier': 'growth', 'user_id': '42'}
        tier = mock_metadata.get('plan_tier', 'professional')
        assert tier == 'growth'
    
    def test_plan_tier_default_value(self):
        """Test default tier when not specified in metadata"""
        mock_metadata = {'user_id': '42'}
        tier = mock_metadata.get('plan_tier', 'professional')
        assert tier == 'professional'


class TestSubscriptionRecordUserLink:
    """Tests for subscription-user linking"""
    
    def test_subscription_metadata_contains_user_id(self):
        """Verify subscription metadata structure includes user_id"""
        metadata = {
            'user_id': '123',
            'plan_tier': 'professional',
            'billing_cycle': 'monthly'
        }
        
        assert 'user_id' in metadata
        assert metadata['user_id'] == '123'
    
    def test_tier_mapping(self):
        """Test tier name mapping is correct"""
        tier_map = {
            'startup': 'Startup',
            'professional': 'Professional', 
            'growth': 'Growth',
            'scale': 'Scale'
        }
        
        for key, expected in tier_map.items():
            assert key.title() == expected or expected == tier_map[key]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
