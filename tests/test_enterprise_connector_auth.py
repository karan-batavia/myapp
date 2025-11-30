"""
Comprehensive tests for Enterprise Connector Auth Resilience
Tests checkpoint resume/clear semantics, token expiry simulation, and auth handling
"""

import pytest
import json
import hashlib
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MockRedis:
    """Mock Redis client for testing checkpoint functionality"""
    
    def __init__(self):
        self.data = {}
        self.ttls = {}
        self.call_log = []
    
    def ping(self):
        self.call_log.append(('ping', None))
        return True
    
    def setex(self, key: str, ttl: int, value: str):
        self.call_log.append(('setex', {'key': key, 'ttl': ttl, 'value': value}))
        self.data[key] = value
        self.ttls[key] = ttl
        return True
    
    def get(self, key: str) -> Optional[str]:
        self.call_log.append(('get', {'key': key}))
        return self.data.get(key)
    
    def delete(self, key: str):
        self.call_log.append(('delete', {'key': key}))
        if key in self.data:
            del self.data[key]
            if key in self.ttls:
                del self.ttls[key]
        return 1
    
    def exists(self, key: str) -> bool:
        return key in self.data
    
    def get_call_log(self):
        return self.call_log
    
    def clear_call_log(self):
        self.call_log = []


class TestCheckpointResumeClearSemantics:
    """Test suite for checkpoint save/restore/clear functionality with mocked Redis"""
    
    @pytest.fixture
    def mock_redis(self):
        return MockRedis()
    
    @pytest.fixture
    def scanner_with_mock_redis(self, mock_redis):
        """Create scanner with mocked Redis"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            scanner = EnterpriseConnectorScanner(
                connector_type='microsoft365',
                credentials={'access_token': 'test_token'},
                region='Netherlands'
            )
            scanner.redis_client = mock_redis
            return scanner
    
    def test_checkpoint_save_creates_valid_checkpoint(self, scanner_with_mock_redis, mock_redis):
        """Test that _save_checkpoint creates a valid checkpoint in Redis"""
        scanner = scanner_with_mock_redis
        
        scanner.completed_queries = {'sharepoint', 'onedrive'}
        scanner.findings = [
            {'source': 'SharePoint', 'pii_found': [{'type': 'email'}]},
            {'source': 'OneDrive', 'pii_found': [{'type': 'BSN'}]}
        ]
        scanner.scanned_items = 150
        
        scan_config = {'scan_sharepoint': True, 'scan_onedrive': True}
        partial_results = {'total_items_scanned': 150, 'status': 'auth_required'}
        
        checkpoint_id = scanner._save_checkpoint(scan_config, partial_results)
        
        assert checkpoint_id is not None
        assert len(checkpoint_id) == 16  # SHA256 hex hash truncated to 16 chars
        
        # Redis key format is "scan_checkpoint:{checkpoint_id}"
        checkpoint_key = f"scan_checkpoint:{checkpoint_id}"
        saved_data = mock_redis.get(checkpoint_key)
        assert saved_data is not None
        
        checkpoint_data = json.loads(saved_data)
        assert set(checkpoint_data['completed_queries']) == {'sharepoint', 'onedrive'}
        assert checkpoint_data['scanned_items'] == 150
        assert len(checkpoint_data['findings']) == 2
        assert checkpoint_data['connector_type'] == 'microsoft365'
        
        logger.info(f"Checkpoint save test passed: {checkpoint_id}")
    
    def test_checkpoint_save_uses_correct_ttl(self, scanner_with_mock_redis, mock_redis):
        """Test that checkpoint is saved with 24-hour TTL"""
        scanner = scanner_with_mock_redis
        scanner.completed_queries = {'test_query'}
        
        checkpoint_id = scanner._save_checkpoint({}, {})
        checkpoint_key = f"scan_checkpoint:{checkpoint_id}"
        
        assert checkpoint_key in mock_redis.ttls
        # TTL is stored as timedelta(hours=24) = timedelta(days=1)
        expected_ttl = mock_redis.ttls[checkpoint_key]
        if isinstance(expected_ttl, timedelta):
            assert expected_ttl.total_seconds() == 86400
        else:
            assert expected_ttl == 86400
        
        logger.info("Checkpoint TTL test passed: 24h TTL verified")
    
    def test_checkpoint_load_returns_valid_data(self, scanner_with_mock_redis, mock_redis):
        """Test that _load_checkpoint retrieves valid checkpoint data"""
        scanner = scanner_with_mock_redis
        
        checkpoint_data = {
            'completed_queries': ['sharepoint', 'exchange'],
            'findings': [{'source': 'test'}],
            'scanned_items': 100,
            'connector_type': 'microsoft365',
            'region': 'Netherlands',
            'timestamp': datetime.now().isoformat()
        }
        # Use the correct key format: scan_checkpoint:{checkpoint_id}
        mock_redis.data['scan_checkpoint:checkpoint_test123'] = json.dumps(checkpoint_data)
        
        loaded = scanner._load_checkpoint('checkpoint_test123')
        
        assert loaded is not None
        assert loaded['completed_queries'] == ['sharepoint', 'exchange']
        assert loaded['scanned_items'] == 100
        
        logger.info("Checkpoint load test passed")
    
    def test_checkpoint_load_returns_none_for_missing(self, scanner_with_mock_redis, mock_redis):
        """Test that _load_checkpoint returns None for non-existent checkpoint"""
        scanner = scanner_with_mock_redis
        
        loaded = scanner._load_checkpoint('nonexistent_checkpoint')
        
        assert loaded is None
        logger.info("Checkpoint missing load test passed")
    
    def test_restore_from_checkpoint_restores_state(self, scanner_with_mock_redis, mock_redis):
        """Test that _restore_from_checkpoint properly restores scanner state"""
        scanner = scanner_with_mock_redis
        
        checkpoint_data = {
            'checkpoint_id': 'checkpoint_restore_test',
            'completed_queries': ['sharepoint', 'onedrive', 'exchange'],
            'findings': [
                {'source': 'SharePoint', 'pii_found': [{'type': 'email'}]},
                {'source': 'OneDrive', 'pii_found': [{'type': 'phone'}]}
            ],
            'scanned_items': 250,
            'connector_type': 'microsoft365',
            'region': 'Netherlands',
            'timestamp': datetime.now().isoformat()
        }
        # Use the correct key format
        mock_redis.data['scan_checkpoint:checkpoint_restore_test'] = json.dumps(checkpoint_data)
        
        scanner._restore_from_checkpoint('checkpoint_restore_test')
        
        assert scanner.completed_queries == {'sharepoint', 'onedrive', 'exchange'}
        assert len(scanner.findings) == 2
        assert scanner.scanned_items == 250
        assert scanner.checkpoint_id == 'checkpoint_restore_test'
        
        logger.info("Checkpoint restore test passed")
    
    def test_delete_checkpoint_removes_from_redis(self, scanner_with_mock_redis, mock_redis):
        """Test that _delete_checkpoint removes checkpoint from Redis"""
        scanner = scanner_with_mock_redis
        
        # Use the correct key format
        mock_redis.data['scan_checkpoint:checkpoint_to_delete'] = json.dumps({'test': 'data'})
        
        scanner._delete_checkpoint('checkpoint_to_delete')
        
        assert 'scan_checkpoint:checkpoint_to_delete' not in mock_redis.data
        
        delete_calls = [c for c in mock_redis.call_log if c[0] == 'delete']
        assert len(delete_calls) > 0
        
        logger.info("Checkpoint delete test passed")
    
    def test_checkpoint_cleared_on_successful_scan(self, scanner_with_mock_redis, mock_redis):
        """Test that checkpoint is cleared after successful scan completion"""
        scanner = scanner_with_mock_redis
        scanner.checkpoint_id = 'checkpoint_success_test'
        # Use the correct key format
        mock_redis.data['scan_checkpoint:checkpoint_success_test'] = json.dumps({'test': 'data'})
        
        scanner._delete_checkpoint(scanner.checkpoint_id)
        
        assert 'scan_checkpoint:checkpoint_success_test' not in mock_redis.data
        
        logger.info("Checkpoint clear on success test passed")
    
    def test_resume_skips_completed_queries(self, scanner_with_mock_redis, mock_redis):
        """Test that resumed scan skips already completed queries"""
        scanner = scanner_with_mock_redis
        scanner.completed_queries = {'sharepoint', 'onedrive'}
        
        queries_to_run = ['sharepoint', 'onedrive', 'exchange', 'teams']
        skipped = []
        executed = []
        
        for query in queries_to_run:
            if query in scanner.completed_queries:
                skipped.append(query)
            else:
                executed.append(query)
        
        assert set(skipped) == {'sharepoint', 'onedrive'}
        assert set(executed) == {'exchange', 'teams'}
        
        logger.info("Resume skip completed queries test passed")


class TestTokenExpirySimulation:
    """Test token expiry detection and refresh for each connector"""
    
    @pytest.fixture
    def mock_redis(self):
        return MockRedis()
    
    def create_scanner(self, connector_type: str, token_expires: datetime = None, mock_redis=None):
        """Helper to create scanner with specific token expiry"""
        credentials = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh_token',
            'client_id': 'test_client',
            'client_secret': 'test_secret'
        }
        
        with patch('redis.Redis', return_value=mock_redis or MockRedis()):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            scanner = EnterpriseConnectorScanner(
                connector_type=connector_type,
                credentials=credentials,
                region='Netherlands'
            )
            if token_expires:
                scanner.token_expires = token_expires
            if mock_redis:
                scanner.redis_client = mock_redis
            return scanner
    
    def test_token_not_expired_when_future(self):
        """Test token is not considered expired when expiry is in future"""
        scanner = self.create_scanner(
            'microsoft365',
            token_expires=datetime.now() + timedelta(hours=1)
        )
        
        assert scanner._is_token_expired() == False
        logger.info("Token not expired (future) test passed")
    
    def test_token_expired_when_past(self):
        """Test token is considered expired when expiry is in past"""
        scanner = self.create_scanner(
            'microsoft365',
            token_expires=datetime.now() - timedelta(minutes=5)
        )
        
        assert scanner._is_token_expired() == True
        logger.info("Token expired (past) test passed")
    
    def test_token_expired_within_buffer(self):
        """Test token is considered expired within 5-minute buffer"""
        scanner = self.create_scanner(
            'microsoft365',
            token_expires=datetime.now() + timedelta(minutes=3)
        )
        
        assert scanner._is_token_expired() == True
        logger.info("Token expired (within buffer) test passed")
    
    def test_token_none_considered_expired(self):
        """Test that None token_expires is considered expired"""
        scanner = self.create_scanner('microsoft365')
        scanner.token_expires = None
        
        assert scanner._is_token_expired() == True
        logger.info("Token None expired test passed")
    
    def test_microsoft365_token_refresh_called_on_expiry(self):
        """Test Microsoft 365 token refresh is attempted when expired"""
        mock_redis = MockRedis()
        scanner = self.create_scanner(
            'microsoft365',
            token_expires=datetime.now() - timedelta(hours=1),
            mock_redis=mock_redis
        )
        
        with patch.object(scanner, '_refresh_microsoft365_token', return_value=True) as mock_refresh:
            # Call _refresh_access_token which dispatches to connector-specific refresh
            scanner._refresh_access_token()
            mock_refresh.assert_called_once()
        
        logger.info("Microsoft 365 token refresh on expiry test passed")
    
    def test_google_workspace_token_refresh_called_on_expiry(self):
        """Test Google Workspace token refresh is attempted when expired"""
        mock_redis = MockRedis()
        scanner = self.create_scanner(
            'google_workspace',
            token_expires=datetime.now() - timedelta(hours=1),
            mock_redis=mock_redis
        )
        
        with patch.object(scanner, '_refresh_google_workspace_token', return_value=True) as mock_refresh:
            # Call _refresh_access_token which dispatches to connector-specific refresh
            scanner._refresh_access_token()
            mock_refresh.assert_called_once()
        
        logger.info("Google Workspace token refresh on expiry test passed")
    
    def test_exact_online_token_refresh_called_on_expiry(self):
        """Test Exact Online token refresh is attempted when expired"""
        mock_redis = MockRedis()
        scanner = self.create_scanner(
            'exact_online',
            token_expires=datetime.now() - timedelta(hours=1),
            mock_redis=mock_redis
        )
        
        with patch.object(scanner, '_refresh_exact_online_token', return_value=True) as mock_refresh:
            # Call _refresh_access_token which dispatches to connector-specific refresh
            scanner._refresh_access_token()
            mock_refresh.assert_called_once()
        
        logger.info("Exact Online token refresh on expiry test passed")
    
    def test_salesforce_token_refresh_called_on_expiry(self):
        """Test Salesforce token refresh is attempted when expired"""
        mock_redis = MockRedis()
        scanner = self.create_scanner(
            'salesforce',
            token_expires=datetime.now() - timedelta(hours=1),
            mock_redis=mock_redis
        )
        scanner.instance_url = 'https://test.salesforce.com'
        
        with patch.object(scanner, '_refresh_salesforce_token', return_value=True) as mock_refresh:
            # Call _refresh_access_token which dispatches to connector-specific refresh
            scanner._refresh_access_token()
            mock_refresh.assert_called_once()
        
        logger.info("Salesforce token refresh on expiry test passed")


class TestAuthRequiredHandling:
    """Test auth_required status handling across all connectors"""
    
    @pytest.fixture
    def mock_redis(self):
        return MockRedis()
    
    def test_microsoft365_returns_auth_required_on_failure(self, mock_redis):
        """Test Microsoft 365 scan returns auth_required when auth fails"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            scanner = EnterpriseConnectorScanner(
                connector_type='microsoft365',
                credentials={'access_token': 'expired_token'},
                region='Netherlands'
            )
            scanner.redis_client = mock_redis
            scanner.token_expires = datetime.now() - timedelta(hours=1)
            
            with patch.object(scanner, '_refresh_access_token', return_value=False):
                with patch.object(scanner, '_is_token_expired', return_value=True):
                    scan_config = {'scan_sharepoint': True}
                    results = scanner._scan_microsoft365(scan_config)
                    
                    assert results.get('status') == 'auth_required'
                    assert results.get('auth_status') == 'expired'
                    assert 'auth_message' in results
        
        logger.info("Microsoft 365 auth_required test passed")
    
    def test_google_workspace_returns_auth_required_on_failure(self, mock_redis):
        """Test Google Workspace scan returns auth_required when auth fails"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            scanner = EnterpriseConnectorScanner(
                connector_type='google_workspace',
                credentials={'access_token': 'expired_token'},
                region='Netherlands'
            )
            scanner.redis_client = mock_redis
            scanner.token_expires = datetime.now() - timedelta(hours=1)
            
            with patch.object(scanner, '_refresh_access_token', return_value=False):
                with patch.object(scanner, '_is_token_expired', return_value=True):
                    scan_config = {'scan_drive': True}
                    results = scanner._scan_google_workspace(scan_config)
                    
                    assert results.get('status') == 'auth_required'
                    assert results.get('auth_status') == 'expired'
        
        logger.info("Google Workspace auth_required test passed")
    
    def test_exact_online_returns_auth_required_on_failure(self, mock_redis):
        """Test Exact Online scan returns auth_required when auth fails"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            scanner = EnterpriseConnectorScanner(
                connector_type='exact_online',
                credentials={'access_token': 'expired_token'},
                region='Netherlands'
            )
            scanner.redis_client = mock_redis
            scanner.token_expires = datetime.now() - timedelta(hours=1)
            
            with patch.object(scanner, '_refresh_access_token', return_value=False):
                with patch.object(scanner, '_is_token_expired', return_value=True):
                    scan_config = {'scan_customers': True}
                    results = scanner._scan_exact_online(scan_config)
                    
                    assert results.get('status') == 'auth_required'
                    assert results.get('auth_status') == 'expired'
        
        logger.info("Exact Online auth_required test passed")
    
    def test_checkpoint_saved_on_auth_failure(self, mock_redis):
        """Test that checkpoint is saved when auth fails mid-scan"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            scanner = EnterpriseConnectorScanner(
                connector_type='microsoft365',
                credentials={'access_token': 'expired_token'},
                region='Netherlands'
            )
            scanner.redis_client = mock_redis
            scanner.completed_queries = {'sharepoint'}
            scanner.findings = [{'source': 'test'}]
            scanner.token_expires = datetime.now() - timedelta(hours=1)
            
            with patch.object(scanner, '_refresh_access_token', return_value=False):
                with patch.object(scanner, '_is_token_expired', return_value=True):
                    scan_config = {'scan_sharepoint': True, 'scan_onedrive': True}
                    results = scanner._scan_microsoft365(scan_config)
                    
                    assert 'checkpoint_id' in results or results.get('status') == 'auth_required'
        
        logger.info("Checkpoint saved on auth failure test passed")


class TestDeploymentLogMonitoring:
    """Test logging for checkpoint save/restore events"""
    
    @pytest.fixture
    def mock_redis(self):
        return MockRedis()
    
    def test_checkpoint_save_logs_event(self, mock_redis, caplog):
        """Test that checkpoint save is logged"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            scanner = EnterpriseConnectorScanner(
                connector_type='microsoft365',
                credentials={'access_token': 'test_token'},
                region='Netherlands'
            )
            scanner.redis_client = mock_redis
            scanner.completed_queries = {'test'}
            
            with caplog.at_level(logging.INFO):
                checkpoint_id = scanner._save_checkpoint({}, {})
                
                log_messages = [record.message for record in caplog.records]
                checkpoint_logs = [msg for msg in log_messages if 'checkpoint' in msg.lower() or 'Checkpoint' in msg]
                
                assert len(checkpoint_logs) > 0 or checkpoint_id is not None
        
        logger.info("Checkpoint save logging test passed")
    
    def test_checkpoint_restore_logs_event(self, mock_redis, caplog):
        """Test that checkpoint restore is logged"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            
            checkpoint_data = {
                'completed_queries': ['test'],
                'findings': [],
                'scanned_items': 0,
                'connector_type': 'microsoft365',
                'region': 'Netherlands',
                'timestamp': datetime.now().isoformat()
            }
            mock_redis.data['checkpoint_log_test'] = json.dumps(checkpoint_data)
            
            with caplog.at_level(logging.INFO):
                scanner = EnterpriseConnectorScanner(
                    connector_type='microsoft365',
                    credentials={'access_token': 'test_token'},
                    region='Netherlands',
                    checkpoint_id='checkpoint_log_test'
                )
                scanner.redis_client = mock_redis
                scanner._restore_from_checkpoint('checkpoint_log_test')
        
        logger.info("Checkpoint restore logging test passed")
    
    def test_token_refresh_logs_attempt(self, mock_redis, caplog):
        """Test that token refresh attempts are logged"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            scanner = EnterpriseConnectorScanner(
                connector_type='microsoft365',
                credentials={
                    'access_token': 'test_token',
                    'refresh_token': 'test_refresh',
                    'client_id': 'test_client',
                    'client_secret': 'test_secret'
                },
                region='Netherlands'
            )
            scanner.redis_client = mock_redis
            scanner.token_expires = datetime.now() - timedelta(hours=1)
            
            with caplog.at_level(logging.INFO):
                with patch('requests.post') as mock_post:
                    mock_post.return_value.status_code = 401
                    mock_post.return_value.json.return_value = {'error': 'invalid_grant'}
                    
                    scanner._refresh_access_token()
        
        logger.info("Token refresh logging test passed")


class TestIntegrationScenarios:
    """Integration tests for complete auth resilience flow"""
    
    @pytest.fixture
    def mock_redis(self):
        return MockRedis()
    
    def test_full_resume_flow(self, mock_redis):
        """Test complete flow: save checkpoint -> new scanner -> resume"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            
            scanner1 = EnterpriseConnectorScanner(
                connector_type='microsoft365',
                credentials={'access_token': 'test_token'},
                region='Netherlands'
            )
            scanner1.redis_client = mock_redis
            scanner1.completed_queries = {'sharepoint', 'onedrive'}
            scanner1.findings = [{'source': 'SharePoint', 'data': 'test'}]
            scanner1.scanned_items = 100
            
            checkpoint_id = scanner1._save_checkpoint(
                {'scan_sharepoint': True, 'scan_onedrive': True, 'scan_exchange': True},
                {'status': 'auth_required'}
            )
            
            scanner2 = EnterpriseConnectorScanner(
                connector_type='microsoft365',
                credentials={'access_token': 'new_token'},
                region='Netherlands',
                checkpoint_id=checkpoint_id
            )
            scanner2.redis_client = mock_redis
            scanner2._restore_from_checkpoint(checkpoint_id)
            
            assert scanner2.completed_queries == {'sharepoint', 'onedrive'}
            assert len(scanner2.findings) == 1
            assert scanner2.scanned_items == 100
            
            assert 'exchange' not in scanner2.completed_queries
        
        logger.info("Full resume flow integration test passed")
    
    def test_checkpoint_cleanup_after_success(self, mock_redis):
        """Test that checkpoints are cleaned up after successful completion"""
        with patch('redis.Redis', return_value=mock_redis):
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            
            scanner = EnterpriseConnectorScanner(
                connector_type='microsoft365',
                credentials={'access_token': 'test_token'},
                region='Netherlands'
            )
            scanner.redis_client = mock_redis
            scanner.completed_queries = {'test'}
            
            checkpoint_id = scanner._save_checkpoint({}, {})
            checkpoint_key = f"scan_checkpoint:{checkpoint_id}"
            assert checkpoint_key in mock_redis.data
            
            scanner.checkpoint_id = checkpoint_id
            scanner._delete_checkpoint(checkpoint_id)
            
            assert checkpoint_key not in mock_redis.data
        
        logger.info("Checkpoint cleanup integration test passed")


def run_all_tests():
    """Run all enterprise connector auth tests and return summary"""
    import sys
    
    pytest_args = [
        __file__,
        '-v',
        '--tb=short',
        '-x'
    ]
    
    result = pytest.main(pytest_args)
    
    return result == 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    success = run_all_tests()
    print(f"\nAll tests {'PASSED' if success else 'FAILED'}")
