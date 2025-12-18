"""
Exact Online Repository Scanner for DataGuardian Pro
Comprehensive scanner for Exact Online integrations with GDPR, UAVG, and Netherlands-specific compliance.

Scans for:
1. Exact Online integration patterns (code, URLs, SDKs, env vars, pipelines, docs)
2. Privacy risks (BSN, KvK, IBAN, personal data) - GDPR/UAVG
3. Credential and secret leakage (OAuth, tokens, .env files)
4. Data flow inference (API → App → DB → Logs)
5. NL-specific compliance (AVG Art. 5 retention, special category data)
"""

import os
import re
import json
import logging
import tempfile
import shutil
import subprocess
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("exact_online_scanner")
except ImportError:
    logger = logging.getLogger(__name__)

from services.repo_scanner import RepoScanner


class ExactOnlineScanner:
    """
    Scanner for repositories with Exact Online integration.
    Detects PII handling, credential exposure, and GDPR/UAVG compliance issues.
    """
    
    def __init__(self, region: str = "Netherlands"):
        """Initialize Exact Online Scanner with Netherlands-focused compliance patterns."""
        self.region = region
        self.scan_id = str(uuid.uuid4())[:8]
        self.start_time = None
        
        self.file_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.cs', '.java', '.php',
            '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.vue', '.svelte',
            '.json', '.yaml', '.yml', '.xml', '.env', '.config', '.conf',
            '.properties', '.ini', '.toml', '.md', '.txt', '.html', '.css',
            '.sh', '.bash', '.ps1', '.bat', '.cmd', '.dockerfile', '.tf',
            '.bicep', '.arm', '.cfn', '.csproj', '.sln', '.gradle', '.pom'
        ]
        
        self.excluded_files = [
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'Gemfile.lock',
            'composer.lock', 'poetry.lock', 'Cargo.lock', 'go.sum',
            'node_modules', '__pycache__', '.git', '.svn', '.hg',
            'dist', 'build', 'out', 'target', 'bin', 'obj',
            '.next', '.nuxt', '.cache', 'coverage', '.pytest_cache'
        ]
        
        self.exact_online_patterns = {
            'exact_sdk_import': {
                'pattern': r'(?i)(exactonline|exact[-_]?online[-_]?client|ExactOnline\.Client|exactonline[-_]sdk)',
                'description': 'Exact Online SDK/Library Import',
                'category': 'integration',
                'severity': 'Info',
                'recommendation': 'Ensure SDK is up-to-date and OAuth tokens are securely managed'
            },
            'exact_api_url': {
                'pattern': r'(?i)(start\.exactonline\.nl|api\.exactonline\.nl|exactonline\.nl/api)',
                'description': 'Exact Online API URL',
                'category': 'integration',
                'severity': 'Info',
                'recommendation': 'Verify API endpoints use HTTPS and proper authentication'
            },
            'exact_oauth_endpoint': {
                'pattern': r'(?i)/oauth2/token|/api/oauth2|exactonline.*oauth|oauth.*exactonline',
                'description': 'Exact Online OAuth Endpoint',
                'category': 'integration',
                'severity': 'Medium',
                'recommendation': 'Ensure OAuth flow follows security best practices'
            },
            'exact_api_path': {
                'pattern': r'(?i)/api/v1/|/api/v2/|/sync/|/bulk/|/current/',
                'description': 'Exact Online API Path',
                'category': 'integration',
                'severity': 'Info',
                'recommendation': 'Document all API endpoints for data flow mapping'
            },
            'exact_php_client': {
                'pattern': r'(?i)picqer/exact[-_]?php[-_]?client|ExactOnlineClient|Picqer\\Exactonline',
                'description': 'Picqer Exact Online PHP Client',
                'category': 'integration',
                'severity': 'Info',
                'recommendation': 'Keep PHP client updated and review token storage'
            },
            'exact_dotnet_client': {
                'pattern': r'(?i)ExactOnline\.Client\.Sdk|using\s+ExactOnline|ExactOnlineClient',
                'description': 'Exact Online .NET Client',
                'category': 'integration',
                'severity': 'Info',
                'recommendation': 'Ensure .NET client uses secure credential storage'
            },
            'exact_integration_doc': {
                'pattern': r'(?i)exact\s*online\s*integration|integrat(e|ion)\s*with\s*exact|exact\s*api\s*connection',
                'description': 'Exact Online Integration Documentation',
                'category': 'documentation',
                'severity': 'Info',
                'recommendation': 'Review integration documentation for data handling policies'
            }
        }
        
        self.exact_env_patterns = {
            'exact_client_id': {
                'pattern': r'(?i)(EXACT[-_]?CLIENT[-_]?ID|EXACT[-_]?ONLINE[-_]?CLIENT[-_]?ID)\s*[=:]\s*["\']?([A-Za-z0-9-]+)["\']?',
                'description': 'Exact Online Client ID',
                'category': 'credential',
                'severity': 'Medium',
                'recommendation': 'Use secrets manager (Azure Key Vault, HashiCorp Vault) - not plaintext in code or env files'
            },
            'exact_client_secret': {
                'pattern': r'(?i)(EXACT[-_]?CLIENT[-_]?SECRET|EXACT[-_]?SECRET|EXACT[-_]?ONLINE[-_]?SECRET)\s*[=:]\s*["\']?([A-Za-z0-9+/=_-]{16,})["\']?',
                'description': 'Exact Online Client Secret - CRITICAL',
                'category': 'credential',
                'severity': 'Critical',
                'recommendation': 'IMMEDIATELY rotate secret. Use Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault for production storage'
            },
            'exact_access_token': {
                'pattern': r'(?i)(EXACT[-_]?ACCESS[-_]?TOKEN|EXACT[-_]?BEARER[-_]?TOKEN)\s*[=:]\s*["\']?([A-Za-z0-9._-]{20,})["\']?',
                'description': 'Exact Online Access Token Exposed',
                'category': 'credential',
                'severity': 'Critical',
                'recommendation': 'Revoke token immediately. Use secrets management solution with automatic token rotation'
            },
            'exact_refresh_token': {
                'pattern': r'(?i)(EXACT[-_]?REFRESH[-_]?TOKEN)\s*[=:]\s*["\']?([A-Za-z0-9._-]{20,})["\']?',
                'description': 'Exact Online Refresh Token Exposed',
                'category': 'credential',
                'severity': 'Critical',
                'recommendation': 'Revoke and regenerate. Store in secrets vault with automated rotation'
            },
            'exact_division': {
                'pattern': r'(?i)(EXACT[-_]?DIVISION|EXACT[-_]?DIVISION[-_]?ID)\s*[=:]\s*["\']?(\d+)["\']?',
                'description': 'Exact Online Division ID',
                'category': 'configuration',
                'severity': 'Low',
                'recommendation': 'Document division access for audit purposes'
            }
        }
        
        self.nl_pii_patterns = {
            'bsn_number': {
                'pattern': r'(?i)(?:bsn|burgerservicenummer|sofi|citizen[-_\s]?service[-_\s]?number|social[-_\s]?security)\s*[=:]*\s*["\']?(\d{9})["\']?',
                'description': 'Netherlands BSN (Burgerservicenummer) - Special Category Data',
                'category': 'pii_critical',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 9', 'Art. 87'],
                'uavg_articles': ['Art. 46'],
                'recommendation': 'BSN requires explicit legal basis. Review processing legitimacy.'
            },
            'bsn_field': {
                'pattern': r'(?i)\b(bsn|burgerservicenummer|bsn[-_]?number|citizen[-_]?service)\b',
                'description': 'BSN Field Reference - Code Processing BSN Data',
                'category': 'pii_critical',
                'severity': 'High',
                'gdpr_articles': ['Art. 9'],
                'uavg_articles': ['Art. 46'],
                'recommendation': 'Document legal basis for BSN processing per UAVG Art. 46'
            },
            'kvk_number': {
                'pattern': r'(?i)(?:kvk|kamer[-_\s]?van[-_\s]?koophandel|chamber[-_\s]?of[-_\s]?commerce|coc[-_\s]?number|company[-_\s]?registration)\s*[=:]*\s*["\']?(\d{8})["\']?',
                'description': 'Netherlands KvK (Chamber of Commerce) Number',
                'category': 'pii',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': ['Art. 3'],
                'recommendation': 'KvK is business data but may link to natural persons'
            },
            'kvk_field': {
                'pattern': r'(?i)\b(kvk[-_]?number|chamber[-_]?of[-_]?commerce[-_]?number|cocNumber)\b',
                'description': 'KvK Field Reference',
                'category': 'pii',
                'severity': 'Low',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': [],
                'recommendation': 'Document if KvK links to personal data'
            },
            'iban_nl': {
                'pattern': r'\b(NL\d{2}[A-Z]{4}\d{10})\b',
                'description': 'Netherlands IBAN Bank Account',
                'category': 'pii',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 32'],
                'uavg_articles': ['Art. 3'],
                'recommendation': 'Financial data requires encryption at rest and in transit'
            },
            'iban_eu': {
                'pattern': r'\b(DE\d{2}[A-Z0-9]{4}\d{14}|BE\d{14}|FR\d{2}[A-Z0-9]{11}\d{11})\b',
                'description': 'EU IBAN Bank Account (DE/BE/FR)',
                'category': 'pii',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 32'],
                'uavg_articles': [],
                'recommendation': 'Cross-border financial data may require additional safeguards'
            },
            'personal_name_fields': {
                'pattern': r'(?i)\b(first[-_]?name|last[-_]?name|voornaam|achternaam|full[-_]?name|volledige[-_]?naam|contactpersoon)\b',
                'description': 'Personal Name Field',
                'category': 'pii',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': [],
                'recommendation': 'Personal names are PII - ensure lawful processing basis'
            },
            'email_pattern': {
                'pattern': r'(?i)(email|e[-_]?mail|mail[-_]?address|emailadres)\s*[=:]\s*["\']([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})["\']',
                'description': 'Email Address in Code',
                'category': 'pii',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': [],
                'recommendation': 'Review email usage for marketing consent requirements'
            },
            'phone_nl': {
                'pattern': r'(?i)(?:phone|telefoon|tel|mobile|mobiel)[-_\s]*[=:]*\s*["\']?(\+31|0031|06)[0-9\s-]{8,12}["\']?',
                'description': 'Netherlands Phone Number',
                'category': 'pii',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': [],
                'recommendation': 'Phone numbers are PII - ensure consent for marketing use'
            },
            'date_of_birth': {
                'pattern': r'(?i)(?:geboortedatum|birth[-_\s]?date|dob|birthday|date[-_\s]?of[-_\s]?birth)\s*[=:]*',
                'description': 'Date of Birth Field',
                'category': 'pii',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 9'],
                'uavg_articles': [],
                'recommendation': 'Age data can reveal special categories - apply data minimization'
            }
        }
        
        self.exact_financial_patterns = {
            'sales_invoice': {
                'pattern': r'(?i)(sales[-_\s]?invoice|verkoop[-_\s]?factuur|SalesInvoice|factuur[-_\s]?verkoop)',
                'description': 'Sales Invoice Processing',
                'category': 'financial',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'recommendation': 'Sales invoices contain customer PII - apply retention limits'
            },
            'purchase_invoice': {
                'pattern': r'(?i)(purchase[-_\s]?invoice|inkoop[-_\s]?factuur|PurchaseInvoice|factuur[-_\s]?inkoop)',
                'description': 'Purchase Invoice Processing',
                'category': 'financial',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'recommendation': 'Purchase invoices may contain supplier contact PII'
            },
            'payment_data': {
                'pattern': r'(?i)(payment|betaling|transaction|transactie|bank[-_\s]?mutation|bankmutatie)',
                'description': 'Payment/Transaction Data',
                'category': 'financial',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 32'],
                'recommendation': 'Financial transactions require audit logging and encryption'
            },
            'debtor_creditor': {
                'pattern': r'(?i)(debtor|debiteur|creditor|crediteur|customer[-_\s]?account|relatie)',
                'description': 'Debtor/Creditor Account Data',
                'category': 'financial',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'recommendation': 'Account data links to individuals - ensure data subject rights'
            }
        }
        
        self.credential_leak_patterns = {
            'hardcoded_password': {
                'pattern': r'(?i)(password|passwd|pwd|wachtwoord|secret)\s*[=:]\s*["\'][^"\']{6,}["\']',
                'description': 'Hardcoded Password/Secret',
                'category': 'security',
                'severity': 'Critical',
                'recommendation': 'Remove immediately. Use secrets manager.'
            },
            'api_key_generic': {
                'pattern': r'(?i)(api[-_\s]?key|apikey|api[-_\s]?secret)\s*[=:]\s*["\']([A-Za-z0-9+/=_-]{16,})["\']',
                'description': 'API Key/Secret Exposed',
                'category': 'security',
                'severity': 'Critical',
                'recommendation': 'Rotate key and use environment variables'
            },
            'bearer_token': {
                'pattern': r'(?i)(bearer|authorization)\s*[=:]\s*["\']([A-Za-z0-9._-]{20,})["\']',
                'description': 'Bearer/Authorization Token Exposed',
                'category': 'security',
                'severity': 'Critical',
                'recommendation': 'Token should never be hardcoded. Use secure vault.'
            },
            'oauth_secret': {
                'pattern': r'(?i)(client[-_\s]?secret|consumer[-_\s]?secret|oauth[-_\s]?secret)\s*[=:]\s*["\']([A-Za-z0-9+/=_-]{16,})["\']',
                'description': 'OAuth Client Secret Exposed',
                'category': 'security',
                'severity': 'Critical',
                'recommendation': 'Revoke and regenerate OAuth credentials immediately'
            },
            'private_key': {
                'pattern': r'(?i)-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
                'description': 'Private Key Exposed in Code',
                'category': 'security',
                'severity': 'Critical',
                'recommendation': 'Remove private key from repository. Use secrets manager.'
            },
            'env_file_committed': {
                'pattern': r'(?i)^\s*[A-Z_]+\s*=\s*["\']?[^"\'\n]+["\']?\s*$',
                'description': 'Environment Variable Definition (potential .env commit)',
                'category': 'security',
                'severity': 'High',
                'recommendation': 'Ensure .env files are in .gitignore'
            },
            'connection_string': {
                'pattern': r'(?i)(connection[-_\s]?string|database[-_\s]?url|db[-_\s]?url)\s*[=:]\s*["\'][^"\']+["\']',
                'description': 'Database Connection String Exposed',
                'category': 'security',
                'severity': 'Critical',
                'recommendation': 'Use environment variables for database connections'
            }
        }
        
        self.data_flow_patterns = {
            'api_fetch': {
                'pattern': r'(?i)(fetch|axios|request|http\.get|http\.post|client\.get|api\.get|\.fetch\()',
                'description': 'Data Fetch from API',
                'category': 'data_flow',
                'flow_type': 'source',
                'recommendation': 'Document data sources for GDPR Art. 13/14 transparency'
            },
            'database_write': {
                'pattern': r'(?i)(\.save\(|\.insert\(|\.create\(|\.update\(|INSERT\s+INTO|UPDATE\s+\w+\s+SET)',
                'description': 'Database Write Operation',
                'category': 'data_flow',
                'flow_type': 'storage',
                'recommendation': 'Ensure data retention policies are implemented'
            },
            'database_read': {
                'pattern': r'(?i)(\.find\(|\.select\(|\.query\(|SELECT\s+.+\s+FROM|\.get\()',
                'description': 'Database Read Operation',
                'category': 'data_flow',
                'flow_type': 'access',
                'recommendation': 'Implement access logging for GDPR accountability'
            },
            'cache_storage': {
                'pattern': r'(?i)(redis|memcache|cache\.set|\.setex\(|cache\.put)',
                'description': 'Cache Storage',
                'category': 'data_flow',
                'flow_type': 'storage',
                'recommendation': 'Set appropriate TTL for cached PII data'
            },
            'log_output': {
                'pattern': r'(?i)(console\.log|logger\.|logging\.|print\(|\.info\(|\.debug\(|\.error\()',
                'description': 'Logging Statement',
                'category': 'data_flow',
                'flow_type': 'exposure',
                'recommendation': 'Ensure PII is not logged. Implement log redaction.'
            },
            'file_write': {
                'pattern': r'(?i)(writeFile|write\(|fopen\(|file_put_contents|to_csv|to_json)',
                'description': 'File Write Operation',
                'category': 'data_flow',
                'flow_type': 'storage',
                'recommendation': 'File storage must be encrypted and access-controlled'
            },
            'api_transmit': {
                'pattern': r'(?i)(\.post\(|\.put\(|\.patch\(|sendEmail|send_mail|webhook|notify)',
                'description': 'External Data Transmission',
                'category': 'data_flow',
                'flow_type': 'transmission',
                'recommendation': 'Document data recipients for GDPR Art. 13/14'
            }
        }
        
        self.nl_compliance_checks = {
            'retention_config': {
                'pattern': r'(?i)(retention|bewaartermijn|expir|ttl|delete[-_\s]?after|purge[-_\s]?after)',
                'description': 'Data Retention Configuration',
                'category': 'compliance',
                'status': 'positive',
                'recommendation': 'Good: Retention policy detected. Verify alignment with AVG Art. 5'
            },
            'encryption_config': {
                'pattern': r'(?i)(encrypt|decrypt|aes|cipher|crypto|hash|bcrypt|argon)',
                'description': 'Encryption Implementation',
                'category': 'compliance',
                'status': 'positive',
                'recommendation': 'Good: Encryption detected. Ensure key management is secure.'
            },
            'consent_handling': {
                'pattern': r'(?i)(consent|toestemming|gdpr[-_\s]?consent|privacy[-_\s]?consent|opt[-_\s]?in)',
                'description': 'Consent Management',
                'category': 'compliance',
                'status': 'positive',
                'recommendation': 'Good: Consent handling detected. Verify granular consent per purpose.'
            },
            'access_control': {
                'pattern': r'(?i)(authorize|permission|role[-_\s]?check|is[-_\s]?admin|has[-_\s]?permission|rbac)',
                'description': 'Access Control Implementation',
                'category': 'compliance',
                'status': 'positive',
                'recommendation': 'Good: Access control detected. Ensure principle of least privilege.'
            },
            'audit_logging': {
                'pattern': r'(?i)(audit[-_\s]?log|audit[-_\s]?trail|activity[-_\s]?log|access[-_\s]?log)',
                'description': 'Audit Logging',
                'category': 'compliance',
                'status': 'positive',
                'recommendation': 'Good: Audit logging detected. Required for GDPR accountability.'
            },
            'data_anonymization': {
                'pattern': r'(?i)(anonymize|pseudonymize|mask|redact|hash[-_\s]?pii)',
                'description': 'Data Anonymization/Pseudonymization',
                'category': 'compliance',
                'status': 'positive',
                'recommendation': 'Good: Data protection technique detected.'
            }
        }
        
        self.pipeline_patterns = {
            'github_actions': {
                'pattern': r'(?i)(\.github/workflows|github[-_\s]?action|uses:\s*actions/)',
                'description': 'GitHub Actions CI/CD',
                'category': 'pipeline',
                'severity': 'Info',
                'recommendation': 'Review secrets management in GitHub Actions'
            },
            'azure_devops': {
                'pattern': r'(?i)(azure[-_\s]?pipelines|azure[-_\s]?devops|\$\(Pipeline\.)',
                'description': 'Azure DevOps Pipeline',
                'category': 'pipeline',
                'severity': 'Info',
                'recommendation': 'Use Azure Key Vault for secrets in pipelines'
            },
            'jenkins': {
                'pattern': r'(?i)(Jenkinsfile|jenkins\.io|withCredentials)',
                'description': 'Jenkins Pipeline',
                'category': 'pipeline',
                'severity': 'Info',
                'recommendation': 'Use Jenkins credentials store for secrets'
            },
            'secrets_injection': {
                'pattern': r'(?i)(secrets\.|env\.|environment:|variables:|parameters:)',
                'description': 'Pipeline Variables/Secrets Injection',
                'category': 'pipeline',
                'severity': 'Medium',
                'recommendation': 'Verify secrets are not exposed in pipeline logs'
            },
            'docker_secrets': {
                'pattern': r'(?i)(docker[-_\s]?secret|--secret|ARG\s+\w+_SECRET)',
                'description': 'Docker Secrets Usage',
                'category': 'pipeline',
                'severity': 'Medium',
                'recommendation': 'Use Docker secrets or external vault for sensitive data'
            }
        }
    
    def scan(
        self,
        repo_url: Optional[str] = None,
        directory_path: Optional[str] = None,
        files_content: Optional[Dict[str, str]] = None,
        max_files: int = 500,
        status_callback=None
    ) -> Dict[str, Any]:
        """
        Main scan entry point for Exact Online repository scanning.
        
        Args:
            repo_url: Git repository URL to clone and scan
            directory_path: Local directory path to scan
            files_content: Dict of filename -> content for direct scanning
            max_files: Maximum number of files to scan
            status_callback: Optional callback for progress updates
            
        Returns:
            Comprehensive scan results with findings and compliance assessment
        """
        self.start_time = time.time()
        
        results = {
            'scan_id': self.scan_id,
            'scan_type': 'exact_online',
            'scanner': 'ExactOnlineScanner',
            'region': self.region,
            'started_at': datetime.utcnow().isoformat(),
            'source': repo_url or directory_path or 'direct_content',
            'exact_integration_detected': False,
            'findings': [],
            'integration_findings': [],
            'pii_findings': [],
            'credential_findings': [],
            'data_flow_findings': [],
            'compliance_findings': [],
            'pipeline_findings': [],
            'risk_summary': {},
            'gdpr_compliance': {},
            'uavg_compliance': {},
            'recommendations': [],
            'data_flow_map': [],
            'files_scanned': 0,
            'errors': []
        }
        
        try:
            if status_callback:
                status_callback("Initializing Exact Online scan...")
            
            files_to_scan = {}
            temp_dir = None
            
            if files_content:
                files_to_scan = files_content
            elif repo_url:
                if status_callback:
                    status_callback("Cloning repository...")
                temp_dir, files_to_scan = self._clone_and_read_repo(repo_url, max_files)
            elif directory_path:
                if status_callback:
                    status_callback("Reading directory...")
                files_to_scan = self._read_directory(directory_path, max_files)
            
            results['files_scanned'] = len(files_to_scan)
            
            if status_callback:
                status_callback(f"Scanning {len(files_to_scan)} files for Exact Online patterns...")
            
            for filename, content in files_to_scan.items():
                file_findings = self._scan_file(filename, content)
                
                for finding in file_findings:
                    finding['file'] = filename
                    results['findings'].append(finding)
                    
                    if finding['category'] == 'integration':
                        results['integration_findings'].append(finding)
                        results['exact_integration_detected'] = True
                    elif finding['category'] in ['pii', 'pii_critical']:
                        results['pii_findings'].append(finding)
                    elif finding['category'] in ['credential', 'security']:
                        results['credential_findings'].append(finding)
                    elif finding['category'] == 'data_flow':
                        results['data_flow_findings'].append(finding)
                    elif finding['category'] == 'compliance':
                        results['compliance_findings'].append(finding)
                    elif finding['category'] == 'pipeline':
                        results['pipeline_findings'].append(finding)
            
            if status_callback:
                status_callback("Analyzing data flows...")
            results['data_flow_map'] = self._analyze_data_flows(results['data_flow_findings'])
            
            if status_callback:
                status_callback("Calculating risk assessment...")
            results['risk_summary'] = self._calculate_risk_summary(results)
            results['gdpr_compliance'] = self._assess_gdpr_compliance(results)
            results['uavg_compliance'] = self._assess_uavg_compliance(results)
            results['recommendations'] = self._generate_recommendations(results)
            
            results['compliance_score'] = self._calculate_compliance_score(results)
            
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
        except Exception as e:
            logger.error(f"Scan error: {str(e)}")
            results['errors'].append(str(e))
        
        results['duration_seconds'] = time.time() - self.start_time
        results['completed_at'] = datetime.utcnow().isoformat()
        
        return results
    
    def _clone_and_read_repo(self, repo_url: str, max_files: int) -> Tuple[str, Dict[str, str]]:
        """Clone repository with optimized settings."""
        temp_dir = tempfile.mkdtemp(prefix='exact_scan_')
        
        try:
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'
            env['GIT_ASKPASS'] = ''
            env['SSH_ASKPASS'] = ''
            env['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes -o StrictHostKeyChecking=no'
            if 'REPLIT_ASKPASS_PID2_SESSION' in env:
                del env['REPLIT_ASKPASS_PID2_SESSION']
            
            clone_cmd = [
                'git', 'clone',
                '--depth', '1',
                '--single-branch',
                '--no-tags',
                repo_url,
                temp_dir
            ]
            
            logger.info(f"Cloning repository: {repo_url}")
            
            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            if result.returncode != 0:
                stderr = result.stderr or ""
                if "terminal prompts disabled" in stderr or "could not read Username" in stderr:
                    logger.error(f"Repository not found or requires authentication: {repo_url}")
                    raise RuntimeError("Repository not found or is private. Please verify the URL is correct and publicly accessible.")
                error_msg = stderr[:200] if stderr else "Unknown error"
                logger.error(f"Git clone failed: {error_msg}")
                raise RuntimeError(f"Git clone failed: {error_msg}")
            
            if not os.path.exists(os.path.join(temp_dir, '.git')):
                raise RuntimeError("Repository clone produced no files")
            
            files_content = self._read_directory(temp_dir, max_files)
            logger.info(f"Successfully read {len(files_content)} files from repository")
            
            return temp_dir, files_content
            
        except subprocess.TimeoutExpired:
            logger.error("Git clone timed out after 120 seconds")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError("Repository clone timed out. Try uploading files directly.")
        except Exception as e:
            logger.error(f"Clone error: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    def _read_directory(self, directory: str, max_files: int) -> Dict[str, str]:
        """Read files from directory, prioritizing code files."""
        files_content = {}
        file_count = 0
        
        priority_ext = {'.cs', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.env', '.config'}
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in self.excluded_files and not d.startswith('.')]
            
            sorted_files = sorted(files, key=lambda f: (0 if any(f.endswith(e) for e in priority_ext) else 1, f))
            
            for file in sorted_files:
                if file_count >= max_files:
                    return files_content
                
                if file in self.excluded_files:
                    continue
                    
                if not any(file.endswith(ext) for ext in self.file_extensions):
                    continue
                
                file_path = os.path.join(root, file)
                
                try:
                    if os.path.getsize(file_path) > 150000:
                        continue
                        
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(50000)
                        rel_path = os.path.relpath(file_path, directory)
                        files_content[rel_path] = content
                        file_count += 1
                except Exception:
                    pass
        
        return files_content
    
    def _scan_file(self, filename: str, content: str) -> List[Dict[str, Any]]:
        """Scan a single file for all patterns."""
        findings = []
        lines = content.split('\n')
        
        all_patterns = [
            (self.exact_online_patterns, 'exact_integration'),
            (self.exact_env_patterns, 'exact_credentials'),
            (self.nl_pii_patterns, 'pii'),
            (self.exact_financial_patterns, 'financial'),
            (self.credential_leak_patterns, 'credentials'),
            (self.data_flow_patterns, 'data_flow'),
            (self.nl_compliance_checks, 'compliance'),
            (self.pipeline_patterns, 'pipeline')
        ]
        
        for patterns_dict, pattern_type in all_patterns:
            for pattern_name, pattern_info in patterns_dict.items():
                try:
                    pattern = pattern_info['pattern']
                    matches = list(re.finditer(pattern, content, re.MULTILINE))
                    
                    for match in matches[:5]:
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ''
                        
                        finding = {
                            'pattern_name': pattern_name,
                            'pattern_type': pattern_type,
                            'category': pattern_info.get('category', pattern_type),
                            'description': pattern_info['description'],
                            'severity': pattern_info.get('severity', 'Medium'),
                            'line_number': line_num,
                            'line_content': line_content[:200],
                            'match': match.group(0)[:100],
                            'recommendation': pattern_info.get('recommendation', ''),
                            'gdpr_articles': pattern_info.get('gdpr_articles', []),
                            'uavg_articles': pattern_info.get('uavg_articles', []),
                            'flow_type': pattern_info.get('flow_type')
                        }
                        findings.append(finding)
                        
                except Exception as e:
                    logger.debug(f"Pattern error {pattern_name}: {e}")
        
        return findings
    
    def _analyze_data_flows(self, data_flow_findings: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze and map data flows from findings."""
        flow_map = {
            'sources': [],
            'storage': [],
            'access': [],
            'transmission': [],
            'exposure': []
        }
        
        for finding in data_flow_findings:
            flow_type = finding.get('flow_type')
            if flow_type and flow_type in flow_map:
                flow_map[flow_type].append({
                    'file': finding.get('file', ''),
                    'line': finding.get('line_number'),
                    'description': finding.get('description')
                })
        
        flows = []
        if flow_map['sources'] and flow_map['storage']:
            flows.append({
                'flow': 'API → Storage',
                'description': 'Data fetched from Exact Online API and stored locally',
                'gdpr_concern': 'Data minimization (Art. 5)',
                'sources': len(flow_map['sources']),
                'destinations': len(flow_map['storage'])
            })
        
        if flow_map['storage'] and flow_map['exposure']:
            flows.append({
                'flow': 'Storage → Logs',
                'description': 'Stored data potentially exposed in logs',
                'gdpr_concern': 'Logging exposure - verify PII redaction',
                'sources': len(flow_map['storage']),
                'destinations': len(flow_map['exposure'])
            })
        
        if flow_map['sources'] and flow_map['transmission']:
            flows.append({
                'flow': 'API → External',
                'description': 'Data transmitted to external systems',
                'gdpr_concern': 'Third-party sharing (Art. 28)',
                'sources': len(flow_map['sources']),
                'destinations': len(flow_map['transmission'])
            })
        
        return flows
    
    def _calculate_risk_summary(self, results: Dict) -> Dict[str, Any]:
        """Calculate overall risk summary."""
        critical = sum(1 for f in results['findings'] if f.get('severity') == 'Critical')
        high = sum(1 for f in results['findings'] if f.get('severity') == 'High')
        medium = sum(1 for f in results['findings'] if f.get('severity') == 'Medium')
        low = sum(1 for f in results['findings'] if f.get('severity') == 'Low')
        
        if critical > 0:
            risk_level = 'Critical'
            risk_score = 15
        elif high > 2:
            risk_level = 'High'
            risk_score = 35
        elif high > 0 or medium > 5:
            risk_level = 'Medium'
            risk_score = 60
        else:
            risk_level = 'Low'
            risk_score = 85
        
        return {
            'overall_risk': risk_level,
            'risk_score': risk_score,
            'critical_count': critical,
            'high_count': high,
            'medium_count': medium,
            'low_count': low,
            'total_findings': len(results['findings']),
            'exact_integration': results['exact_integration_detected'],
            'bsn_processing': any('bsn' in f.get('pattern_name', '').lower() for f in results['pii_findings']),
            'credential_exposure': len(results['credential_findings']) > 0
        }
    
    def _assess_gdpr_compliance(self, results: Dict) -> Dict[str, Any]:
        """Assess GDPR compliance based on findings."""
        articles_triggered = set()
        for finding in results['findings']:
            articles_triggered.update(finding.get('gdpr_articles', []))
        
        compliance_positive = [f for f in results['compliance_findings'] if f.get('status') == 'positive']
        
        return {
            'articles_triggered': list(articles_triggered),
            'positive_controls': len(compliance_positive),
            'has_retention_policy': any('retention' in f.get('pattern_name', '') for f in compliance_positive),
            'has_encryption': any('encrypt' in f.get('pattern_name', '') for f in compliance_positive),
            'has_consent_management': any('consent' in f.get('pattern_name', '') for f in compliance_positive),
            'has_access_control': any('access' in f.get('pattern_name', '') for f in compliance_positive),
            'has_audit_logging': any('audit' in f.get('pattern_name', '') for f in compliance_positive)
        }
    
    def _assess_uavg_compliance(self, results: Dict) -> Dict[str, Any]:
        """Assess Netherlands UAVG-specific compliance."""
        uavg_articles = set()
        for finding in results['findings']:
            uavg_articles.update(finding.get('uavg_articles', []))
        
        bsn_findings = [f for f in results['pii_findings'] if 'bsn' in f.get('pattern_name', '').lower()]
        
        return {
            'uavg_articles_triggered': list(uavg_articles),
            'bsn_processing_detected': len(bsn_findings) > 0,
            'bsn_legal_basis_required': len(bsn_findings) > 0,
            'kvk_processing_detected': any('kvk' in f.get('pattern_name', '').lower() for f in results['pii_findings']),
            'special_category_data': len(bsn_findings) > 0,
            'recommendation': 'Document legal basis per UAVG Art. 46 for BSN processing' if bsn_findings else 'No special category data detected'
        }
    
    def _calculate_compliance_score(self, results: Dict) -> float:
        """Calculate overall compliance score (0-100).
        
        Uses a normalized scoring model that accounts for repository size
        and distinguishes between actual credential leaks vs. code patterns.
        """
        score = 100.0
        files_scanned = max(1, results.get('files_scanned', 1))
        
        critical = results['risk_summary'].get('critical_count', 0)
        high = results['risk_summary'].get('high_count', 0)
        medium = results['risk_summary'].get('medium_count', 0)
        low = results['risk_summary'].get('low_count', 0)
        
        real_credential_leaks = sum(
            1 for f in results.get('credential_findings', [])
            if f.get('severity') == 'Critical' and 
            not any(x in f.get('matched_text', '').lower() for x in ['example', 'sample', 'test', 'placeholder', 'xxx', '***'])
        )
        
        score -= min(50, real_credential_leaks * 25)
        
        normalized_critical = min(10, critical) / files_scanned * 100
        normalized_high = min(50, high) / files_scanned * 100
        normalized_medium = min(100, medium) / files_scanned * 100
        
        score -= min(15, normalized_critical * 0.5)
        score -= min(20, normalized_high * 0.3)
        score -= min(10, normalized_medium * 0.1)
        
        gdpr = results['gdpr_compliance']
        if gdpr.get('has_encryption'):
            score += 5
        if gdpr.get('has_consent_management'):
            score += 5
        if gdpr.get('has_access_control'):
            score += 5
        if gdpr.get('has_audit_logging'):
            score += 5
        if gdpr.get('has_retention_policy'):
            score += 5
        
        if results.get('exact_integration_detected'):
            score += 10
        
        return max(15, min(100, score))
    
    def _generate_recommendations(self, results: Dict) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        if results['credential_findings']:
            recommendations.append({
                'priority': 'Critical',
                'category': 'Security',
                'title': 'Credential Exposure Detected',
                'description': f"Found {len(results['credential_findings'])} exposed credentials. Immediate action required.",
                'actions': [
                    'Revoke and rotate all exposed credentials immediately',
                    'Implement secrets management (Azure Key Vault, AWS Secrets Manager)',
                    'Add pre-commit hooks to prevent future credential commits',
                    'Review git history for previously committed secrets'
                ]
            })
        
        if results['uavg_compliance'].get('bsn_processing_detected'):
            recommendations.append({
                'priority': 'High',
                'category': 'Compliance',
                'title': 'BSN Processing Requires Legal Basis',
                'description': 'BSN (Burgerservicenummer) processing detected. UAVG Art. 46 compliance required.',
                'actions': [
                    'Document legal basis for BSN processing',
                    'Implement additional security measures for BSN data',
                    'Conduct Data Protection Impact Assessment (DPIA)',
                    'Notify DPO about BSN processing activities'
                ]
            })
        
        if not results['gdpr_compliance'].get('has_retention_policy'):
            recommendations.append({
                'priority': 'High',
                'category': 'Compliance',
                'title': 'Implement Data Retention Policy',
                'description': 'No data retention configuration detected. Required for AVG Art. 5.',
                'actions': [
                    'Define retention periods for each data category',
                    'Implement automated data purging',
                    'Document retention policy in privacy documentation'
                ]
            })
        
        if results['exact_integration_detected'] and not results['gdpr_compliance'].get('has_encryption'):
            recommendations.append({
                'priority': 'High',
                'category': 'Security',
                'title': 'Implement Encryption for Exact Online Data',
                'description': 'Exact Online integration detected but no encryption implementation found.',
                'actions': [
                    'Encrypt OAuth tokens at rest',
                    'Use TLS for all API communications',
                    'Implement encryption for cached/stored data'
                ]
            })
        
        if results['data_flow_map']:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Documentation',
                'title': 'Document Data Flows for GDPR Transparency',
                'description': f"Detected {len(results['data_flow_map'])} data flow patterns. Documentation required.",
                'actions': [
                    'Create data flow diagrams',
                    'Document all data recipients',
                    'Update privacy policy with data processing details',
                    'Maintain Records of Processing Activities (RoPA)'
                ]
            })
        
        return recommendations


def scan_exact_online_repo(
    repo_url: Optional[str] = None,
    directory_path: Optional[str] = None,
    files_content: Optional[Dict[str, str]] = None,
    region: str = "Netherlands",
    max_files: int = 500,
    status_callback=None
) -> Dict[str, Any]:
    """Convenience function to scan for Exact Online integration."""
    scanner = ExactOnlineScanner(region=region)
    return scanner.scan(
        repo_url=repo_url,
        directory_path=directory_path,
        files_content=files_content,
        max_files=max_files,
        status_callback=status_callback
    )
