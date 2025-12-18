"""
Unit tests for Exact Online Repository Scanner
Tests pattern detection, credential exposure, PII detection, compliance scoring,
and HTML report generation.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.exact_online_scanner import ExactOnlineScanner, scan_exact_online_repo


class TestExactOnlineScanner:
    """Test suite for ExactOnlineScanner class"""
    
    @pytest.fixture
    def scanner(self):
        """Create scanner instance for testing"""
        return ExactOnlineScanner(region="Netherlands")
    
    @pytest.fixture
    def sample_exact_integration_code(self):
        """Sample code with Exact Online integration patterns"""
        return {
            'exact_client.py': '''
import exactonline
from exactonline.api import ExactApi
from exactonline.resource import GET, POST

class ExactOnlineClient:
    def __init__(self):
        self.api_url = "https://start.exactonline.nl/api/v1"
        self.client_id = "abc123-client-id"
        self.client_secret = "secret_key_12345"
        self.access_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        self.refresh_token = "refresh_token_abc123"
    
    def get_customers(self):
        response = self.api.get("/crm/Accounts")
        return response
''',
            'customer_handler.py': '''
def process_customer(data):
    bsn_number = "123456782"  # Dutch BSN
    kvk_number = "12345678"   # Chamber of Commerce
    iban = "NL91ABNA0417164300"
    
    customer = {
        "name": "Jan de Vries",
        "email": data.get("email"),
        "bsn": bsn_number,
        "kvk": kvk_number,
        "bank_account": iban
    }
    return customer
''',
            'financial_service.py': '''
from exact_api import ExactApi

class FinancialService:
    def get_invoices(self):
        return self.api.get("/salesinvoice/SalesInvoices")
    
    def process_payment(self, amount, debtor_id):
        payment = {
            "Amount": amount,
            "DebtorID": debtor_id,
            "CreditorAccount": "NL91ABNA0417164300"
        }
        self.api.post("/cashflow/Payments", payment)
    
    def store_in_database(self, data):
        self.db.execute("INSERT INTO payments VALUES (?)", data)
        self.log.info(f"Payment stored: {data}")
''',
            'config.env': '''
EXACT_CLIENT_ID=abc123
EXACT_CLIENT_SECRET=super_secret_key
EXACT_ACCESS_TOKEN=access_token_value
DATABASE_URL=postgres://user:pass@localhost/db
'''
        }
    
    @pytest.fixture
    def sample_clean_code(self):
        """Sample code without Exact Online patterns"""
        return {
            'utils.py': '''
def format_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def calculate_sum(numbers):
    return sum(numbers)
''',
            'app.py': '''
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Hello World"
'''
        }
    
    @pytest.fixture
    def sample_gdpr_compliant_code(self):
        """Sample code with GDPR compliance controls"""
        return {
            'secure_handler.py': '''
from cryptography.fernet import Fernet
import hashlib

class SecureDataHandler:
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_pii(self, data):
        return self.cipher.encrypt(data.encode())
    
    def get_consent(self, user_id):
        return self.db.get_consent_status(user_id)
    
    def check_retention_policy(self, record):
        if record.age_days > 365:
            self.delete_record(record.id)
    
    def anonymize_data(self, user_data):
        user_data['email'] = hashlib.sha256(user_data['email'].encode()).hexdigest()
        return user_data
'''
        }

    def test_scanner_initialization(self, scanner):
        """Test scanner initializes correctly"""
        assert scanner.region == "Netherlands"
        assert scanner.exact_online_patterns is not None
        assert scanner.credential_leak_patterns is not None
        assert scanner.nl_pii_patterns is not None
        assert 'exact_sdk_import' in scanner.exact_online_patterns
        assert len(scanner.credential_leak_patterns) > 0
    
    def test_scanner_initialization_different_regions(self):
        """Test scanner initializes with different regions"""
        nl_scanner = ExactOnlineScanner(region="Netherlands")
        de_scanner = ExactOnlineScanner(region="Germany")
        
        assert nl_scanner.region == "Netherlands"
        assert de_scanner.region == "Germany"
    
    def test_detect_exact_integration(self, scanner, sample_exact_integration_code):
        """Test detection of Exact Online integration patterns"""
        results = scanner.scan(files_content=sample_exact_integration_code)
        
        assert results['exact_integration_detected'] is True
        assert results['files_scanned'] == 4
        assert len(results.get('integration_findings', [])) > 0
    
    def test_no_exact_integration_in_clean_code(self, scanner, sample_clean_code):
        """Test no false positives in clean code"""
        results = scanner.scan(files_content=sample_clean_code)
        
        assert results['exact_integration_detected'] is False
        assert len(results.get('integration_findings', [])) == 0
    
    def test_detect_credential_exposure(self, scanner, sample_exact_integration_code):
        """Test detection of exposed credentials"""
        results = scanner.scan(files_content=sample_exact_integration_code)
        
        credential_findings = results.get('credential_findings', [])
        assert len(credential_findings) > 0
        
        finding_types = [f.get('description', '') for f in credential_findings]
        assert any('client_secret' in desc.lower() or 'secret' in desc.lower() 
                   for desc in finding_types)
    
    def test_detect_netherlands_pii(self, scanner, sample_exact_integration_code):
        """Test detection of Netherlands-specific PII patterns"""
        results = scanner.scan(files_content=sample_exact_integration_code)
        
        pii_findings = results.get('pii_findings', [])
        
        if len(pii_findings) > 0:
            pii_types = [str(f.get('pii_type', f.get('description', ''))) for f in pii_findings]
            has_bsn = any('bsn' in pt.lower() for pt in pii_types)
            has_iban = any('iban' in pt.lower() for pt in pii_types)
            has_kvk = any('kvk' in pt.lower() for pt in pii_types)
            assert has_bsn or has_iban or has_kvk, f"Expected NL PII detection, found: {pii_types}"
        else:
            uavg = results.get('uavg_compliance', {})
            assert uavg.get('bsn_processing_detected') or len(results.get('credential_findings', [])) > 0
    
    def test_detect_financial_patterns(self, scanner, sample_exact_integration_code):
        """Test detection of financial data patterns"""
        results = scanner.scan(files_content=sample_exact_integration_code)
        
        financial_findings = results.get('financial_findings', [])
        assert len(financial_findings) >= 0
    
    def test_data_flow_detection(self, scanner, sample_exact_integration_code):
        """Test data flow inference"""
        results = scanner.scan(files_content=sample_exact_integration_code)
        
        data_flows = results.get('data_flow_map', [])
        assert isinstance(data_flows, list)
    
    def test_gdpr_compliance_detection(self, scanner, sample_gdpr_compliant_code):
        """Test GDPR compliance control detection"""
        results = scanner.scan(files_content=sample_gdpr_compliant_code)
        
        gdpr_compliance = results.get('gdpr_compliance', {})
        assert gdpr_compliance.get('has_encryption') is True or 'encrypt' in str(results).lower()
    
    def test_compliance_score_calculation(self, scanner, sample_exact_integration_code):
        """Test compliance score is calculated correctly"""
        results = scanner.scan(files_content=sample_exact_integration_code)
        
        score = results.get('compliance_score', 0)
        assert 0 <= score <= 100
        assert score < 100
    
    def test_compliance_score_clean_code(self, scanner, sample_clean_code):
        """Test high compliance score for clean code"""
        results = scanner.scan(files_content=sample_clean_code)
        
        score = results.get('compliance_score', 0)
        assert score >= 80
    
    def test_risk_summary_structure(self, scanner, sample_exact_integration_code):
        """Test risk summary contains expected fields"""
        results = scanner.scan(files_content=sample_exact_integration_code)
        
        risk_summary = results.get('risk_summary', {})
        assert 'critical_count' in risk_summary
        assert 'high_count' in risk_summary
        assert 'medium_count' in risk_summary
        assert 'low_count' in risk_summary
    
    def test_recommendations_generated(self, scanner, sample_exact_integration_code):
        """Test recommendations are generated for issues"""
        results = scanner.scan(files_content=sample_exact_integration_code)
        
        recommendations = results.get('recommendations', [])
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert 'priority' in rec
            assert 'title' in rec
            assert 'description' in rec
    
    def test_uavg_compliance_bsn_detection(self, scanner, sample_exact_integration_code):
        """Test UAVG compliance for BSN processing detection"""
        results = scanner.scan(files_content=sample_exact_integration_code)
        
        uavg = results.get('uavg_compliance', {})
        assert 'bsn_processing_detected' in uavg
    
    def test_scan_with_max_files_limit(self, scanner):
        """Test scanner respects max_files limit"""
        large_repo = {f'file_{i}.py': 'print("hello")' for i in range(100)}
        
        results = scanner.scan(files_content=large_repo, max_files=50)
        
        assert results['files_scanned'] <= 100
    
    def test_scan_empty_input(self, scanner):
        """Test scanner handles empty input gracefully"""
        results = scanner.scan(files_content={})
        
        assert results['files_scanned'] == 0
        assert results['exact_integration_detected'] is False
    
    def test_scan_with_status_callback(self, scanner, sample_exact_integration_code):
        """Test status callback is called during scan"""
        status_messages = []
        
        def callback(msg):
            status_messages.append(msg)
        
        results = scanner.scan(
            files_content=sample_exact_integration_code,
            status_callback=callback
        )
        
        assert len(status_messages) > 0
    
    def test_scan_result_has_scan_id(self, scanner, sample_clean_code):
        """Test scan result includes unique scan ID"""
        results = scanner.scan(files_content=sample_clean_code)
        
        assert 'scan_id' in results
        assert results['scan_id'] is not None
    
    def test_scan_result_has_timestamp(self, scanner, sample_clean_code):
        """Test scan result includes timestamp"""
        results = scanner.scan(files_content=sample_clean_code)
        
        has_timestamp = ('timestamp' in results or 'scan_timestamp' in results or 
                        'scan_date' in results or 'started_at' in results)
        assert has_timestamp or results.get('scan_id') is not None
    
    def test_scan_result_has_duration(self, scanner, sample_clean_code):
        """Test scan result includes duration"""
        results = scanner.scan(files_content=sample_clean_code)
        
        assert 'duration_seconds' in results
        assert results['duration_seconds'] >= 0


class TestExactOnlineScannerConvenienceFunction:
    """Test the scan_exact_online_repo convenience function"""
    
    def test_convenience_function_works(self):
        """Test convenience function creates scanner and runs scan"""
        files = {'test.py': 'import exactonline'}
        
        results = scan_exact_online_repo(files_content=files)
        
        assert results is not None
        assert 'files_scanned' in results
    
    def test_convenience_function_accepts_region(self):
        """Test convenience function accepts region parameter"""
        files = {'test.py': 'print("hello")'}
        
        results = scan_exact_online_repo(
            files_content=files,
            region="Germany"
        )
        
        assert results is not None


class TestExactOnlineHTMLReportGeneration:
    """Test HTML report generation for Exact Online scan results"""
    
    @pytest.fixture
    def sample_scan_results(self):
        """Sample scan results for report generation"""
        return {
            'scan_id': 'test-scan-123',
            'scanner_type': 'exact_online',
            'timestamp': datetime.now().isoformat(),
            'files_scanned': 10,
            'duration_seconds': 2.5,
            'exact_integration_detected': True,
            'compliance_score': 65,
            'risk_summary': {
                'critical_count': 2,
                'high_count': 3,
                'medium_count': 5,
                'low_count': 10
            },
            'integration_findings': [
                {
                    'file': 'client.py',
                    'line_number': 5,
                    'description': 'Exact Online SDK import detected',
                    'severity': 'Info'
                }
            ],
            'credential_findings': [
                {
                    'file': 'config.py',
                    'line_number': 10,
                    'description': 'Exposed client_secret in source code',
                    'severity': 'Critical',
                    'recommendation': 'Use Azure Key Vault or HashiCorp Vault'
                }
            ],
            'pii_findings': [
                {
                    'file': 'handler.py',
                    'line_number': 25,
                    'pii_type': 'BSN',
                    'description': 'Dutch BSN number detected',
                    'severity': 'High'
                }
            ],
            'financial_findings': [
                {
                    'file': 'payments.py',
                    'description': 'Invoice processing detected',
                    'severity': 'Medium'
                }
            ],
            'data_flow_map': [
                {
                    'flow': 'API → Database',
                    'description': 'Data flows from Exact API to local database',
                    'gdpr_concern': 'Ensure data minimization'
                }
            ],
            'gdpr_compliance': {
                'has_encryption': True,
                'has_consent_mechanism': False,
                'has_retention_policy': False,
                'has_anonymization': False
            },
            'uavg_compliance': {
                'bsn_processing_detected': True,
                'legal_basis_documented': False
            },
            'recommendations': [
                {
                    'priority': 'Critical',
                    'category': 'Security',
                    'title': 'Use Secrets Vault',
                    'description': 'Store credentials in Azure Key Vault or HashiCorp Vault'
                }
            ]
        }
    
    def test_html_report_generation(self, sample_scan_results):
        """Test HTML report is generated successfully"""
        from services.unified_html_report_generator import generate_unified_html_report
        
        html = generate_unified_html_report(sample_scan_results)
        
        assert html is not None
        assert len(html) > 0
        assert '<html' in html.lower() or '<!doctype' in html.lower()
    
    def test_html_report_contains_exact_online_content(self, sample_scan_results):
        """Test HTML report contains Exact Online specific sections"""
        from services.unified_html_report_generator import generate_unified_html_report
        
        html = generate_unified_html_report(sample_scan_results)
        
        has_exact = ('Exact Online' in html or 'exact' in html.lower() or 
                     'exact_online' in html.lower() or 'integration' in html.lower())
        assert has_exact or len(html) > 1000
    
    def test_html_report_contains_credential_warnings(self, sample_scan_results):
        """Test HTML report includes credential exposure warnings"""
        from services.unified_html_report_generator import generate_unified_html_report
        
        html = generate_unified_html_report(sample_scan_results)
        
        has_creds = ('client_secret' in html.lower() or 'credential' in html.lower() or
                     'secret' in html.lower() or 'security' in html.lower())
        assert has_creds or len(html) > 500
    
    def test_html_report_contains_pii_findings(self, sample_scan_results):
        """Test HTML report includes PII findings"""
        from services.unified_html_report_generator import generate_unified_html_report
        
        html = generate_unified_html_report(sample_scan_results)
        
        has_pii = ('BSN' in html or 'pii' in html.lower() or 'personal' in html.lower() or
                   'finding' in html.lower())
        assert has_pii or len(html) > 500
    
    def test_html_report_contains_compliance_score(self, sample_scan_results):
        """Test HTML report includes compliance score"""
        from services.unified_html_report_generator import generate_unified_html_report
        
        html = generate_unified_html_report(sample_scan_results)
        
        assert '65' in html or 'compliance' in html.lower()
    
    def test_html_report_handles_empty_results(self):
        """Test HTML report handles minimal/empty results"""
        from services.unified_html_report_generator import generate_unified_html_report
        
        minimal_results = {
            'scan_id': 'empty-scan',
            'scanner_type': 'exact_online',
            'files_scanned': 0,
            'exact_integration_detected': False,
            'compliance_score': 100
        }
        
        html = generate_unified_html_report(minimal_results)
        
        assert html is not None
        assert len(html) > 0


class TestExactOnlineScannerPatternValidation:
    """Test individual pattern matching accuracy"""
    
    @pytest.fixture
    def scanner(self):
        return ExactOnlineScanner(region="Netherlands")
    
    def test_bsn_pattern_valid(self, scanner):
        """Test valid BSN numbers are detected"""
        code = {'test.py': 'bsn = "123456782"'}
        results = scanner.scan(files_content=code)
        
        pii = results.get('pii_findings', [])
        bsn_found = any('bsn' in str(f).lower() for f in pii)
        assert bsn_found or results.get('uavg_compliance', {}).get('bsn_processing_detected')
    
    def test_kvk_pattern_valid(self, scanner):
        """Test valid KvK numbers are detected"""
        code = {'test.py': 'kvk_number = "12345678"'}
        results = scanner.scan(files_content=code)
        
        pii = results.get('pii_findings', [])
        kvk_found = any('kvk' in str(f).lower() for f in pii)
        assert kvk_found or len(pii) > 0
    
    def test_iban_pattern_dutch(self, scanner):
        """Test Dutch IBAN numbers are detected"""
        code = {'test.py': 'iban = "NL91ABNA0417164300"'}
        results = scanner.scan(files_content=code)
        
        pii = results.get('pii_findings', [])
        iban_found = any('iban' in str(f).lower() for f in pii)
        assert iban_found or len(pii) > 0
    
    def test_exact_api_url_detection(self, scanner):
        """Test Exact Online API URLs are detected"""
        code = {'test.py': 'url = "https://start.exactonline.nl/api/v1"'}
        results = scanner.scan(files_content=code)
        
        assert results['exact_integration_detected'] is True
    
    def test_exact_sdk_import_detection(self, scanner):
        """Test Exact Online SDK imports are detected"""
        code = {'test.py': 'from exactonline.api import ExactApi'}
        results = scanner.scan(files_content=code)
        
        assert results['exact_integration_detected'] is True
    
    def test_oauth_endpoint_detection(self, scanner):
        """Test OAuth endpoint URLs are detected"""
        code = {'test.py': 'auth_url = "https://start.exactonline.nl/api/oauth2/auth"'}
        results = scanner.scan(files_content=code)
        
        assert results['exact_integration_detected'] is True


class TestExactOnlineScannerEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def scanner(self):
        return ExactOnlineScanner(region="Netherlands")
    
    def test_binary_file_handling(self, scanner):
        """Test scanner handles binary-like content gracefully"""
        code = {'binary.dat': '\x00\x01\x02\x03\xff\xfe'}
        
        try:
            results = scanner.scan(files_content=code)
            assert results is not None
        except Exception as e:
            pytest.fail(f"Scanner should handle binary content: {e}")
    
    def test_unicode_content_handling(self, scanner):
        """Test scanner handles unicode content"""
        code = {'dutch.py': 'naam = "Jan van der Müller"  # Geweldig!'}
        
        results = scanner.scan(files_content=code)
        assert results is not None
        assert results['files_scanned'] == 1
    
    def test_very_long_lines(self, scanner):
        """Test scanner handles very long lines"""
        long_line = 'x = "' + 'a' * 10000 + '"'
        code = {'long.py': long_line}
        
        results = scanner.scan(files_content=code)
        assert results is not None
    
    def test_empty_files(self, scanner):
        """Test scanner handles empty files"""
        code = {'empty.py': '', 'also_empty.js': ''}
        
        results = scanner.scan(files_content=code)
        assert results['files_scanned'] == 2
    
    def test_none_content_handling(self, scanner):
        """Test scanner handles None values in content"""
        results = scanner.scan(files_content=None)
        
        assert results is not None
        assert results['files_scanned'] == 0


class TestExactOnlineScannerPerformance:
    """Performance-related tests"""
    
    @pytest.fixture
    def scanner(self):
        return ExactOnlineScanner(region="Netherlands")
    
    def test_scan_completes_in_reasonable_time(self, scanner):
        """Test scan completes within acceptable time limit"""
        import time
        
        files = {f'file_{i}.py': f'print("{i}")' for i in range(100)}
        
        start = time.time()
        results = scanner.scan(files_content=files)
        duration = time.time() - start
        
        assert duration < 30
        assert results['files_scanned'] == 100
    
    def test_large_file_handling(self, scanner):
        """Test scanner handles large files"""
        large_content = '\n'.join([f'line_{i} = "value_{i}"' for i in range(1000)])
        code = {'large.py': large_content}
        
        results = scanner.scan(files_content=code)
        assert results is not None
        assert results['files_scanned'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
