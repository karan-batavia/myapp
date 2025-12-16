"""
Salesforce Code Repository Scanner for DataGuardian Pro
Scans Salesforce Apex, Lightning, Visualforce code repositories for compliance with GDPR, UAVG, NIS2, SOC2 standards.
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
from typing import Dict, List, Any, Optional

try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("salesforce_repo_scanner")
except ImportError:
    logger = logging.getLogger(__name__)

from services.repo_scanner import RepoScanner


class SalesforceRepoScanner:
    """
    Scanner for Salesforce code repositories (Apex, Lightning, Visualforce, LWC) to detect 
    PII exposure, security vulnerabilities, fraud patterns, and compliance issues.
    """
    
    def __init__(self, region: str = "Netherlands"):
        """Initialize Salesforce Repository Scanner with compliance-focused patterns."""
        self.region = region
        self.scan_id = str(uuid.uuid4())[:8]
        self.start_time = None
        
        self.salesforce_file_extensions = [
            '.cls', '.trigger', '.apex', '.page', '.component', '.app',
            '.js', '.html', '.css', '.xml', '.json', '.yaml', '.yml',
            '.cmp', '.evt', '.intf', '.design', '.auradoc', '.tokens',
            '.flexipage', '.object', '.field', '.tab', '.layout',
            '.permissionset', '.profile', '.workflow', '.flow',
            '.report', '.dashboard', '.email', '.label', '.translation',
            '.resource', '.staticresource', '.remoteSite', '.namedCredential',
            '.connectedApp', '.externalDataSource', '.customMetadata',
            '.lwc', '.ts', '.tsx', '.md', '.txt', '.properties', '.env'
        ]
        
        self.excluded_files = [
            'CHANGELOG', 'changelog', 'HISTORY', 'history', 'NEWS', 'RELEASES',
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'Gemfile.lock',
            'composer.lock', 'poetry.lock', 'Cargo.lock', 'go.sum',
            'sfdx-project.json', 'package.xml'
        ]
        
        self.salesforce_pii_patterns = {
            'bsn_number': {
                'pattern': r'(?i)(?:bsn|burgerservicenummer|sofi|citizen.?service|social.?security)\s*[=:]\s*["\']?([0-9]{9})["\']?',
                'description': 'Netherlands BSN (Social Security Number)',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 9', 'Art. 87'],
                'uavg_articles': ['Art. 46'],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            },
            'kvk_number': {
                'pattern': r'(?i)(?:kvk|kamer.?van.?koophandel|chamber.?of.?commerce|coc|company.?registration)\s*[=:]\s*["\']?([0-9]{8})["\']?',
                'description': 'Netherlands KvK (Chamber of Commerce) Number',
                'severity': 'High',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': ['Art. 3'],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            },
            'iban_number': {
                'pattern': r'\b(NL[0-9]{2}[A-Z]{4}[0-9]{10}|DE[0-9]{2}[A-Z0-9]{4}[0-9]{14}|BE[0-9]{14}|FR[0-9]{2}[A-Z0-9]{11}[0-9]{11})\b',
                'description': 'IBAN Bank Account Number',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 32'],
                'uavg_articles': ['Art. 3'],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            },
            'email_personal': {
                'pattern': r'(?i)(?:personal.?email|private.?email|home.?email)\s*[=:]\s*["\']([A-Za-z0-9._%+-]+@(?!example\.com|test\.com|localhost)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})["\']',
                'description': 'Personal Email Address in Code',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': [],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            },
            'phone_nl': {
                'pattern': r'(?i)(?:phone|telefoon|tel|mobile|mobiel)\s*[=:]\s*["\']?(\+31|0031)[0-9]{9}["\']?',
                'description': 'Netherlands Phone Number',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': [],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            },
            'passport_nl': {
                'pattern': r'(?i)(?:passport|paspoort|reisdocument|travel.?document)\s*[=:]\s*["\']?([A-Z]{2}[A-Z0-9]{6}[0-9])["\']?',
                'description': 'Netherlands Passport Number',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 9', 'Art. 87'],
                'uavg_articles': ['Art. 46'],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            },
            'credit_card': {
                'pattern': r'(?i)(?:card|credit|cc|creditcard|card.?number)\s*[=:]\s*["\']?(4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})["\']?',
                'description': 'Credit Card Number',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7', 'CC7.2']
            },
            'date_of_birth': {
                'pattern': r'(?i)(?:geboortedatum|birth_?date|dob|birthday|date.?of.?birth)\s*[=:]\s*["\']?\d{1,4}[-/]\d{1,2}[-/]\d{1,4}["\']?',
                'description': 'Date of Birth Field',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 9'],
                'uavg_articles': [],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            },
            'national_id': {
                'pattern': r'(?i)(?:national.?id|id.?number|identity.?number|rijbewijs|driver.?license)\s*[=:]\s*["\']?[A-Z0-9]{6,12}["\']?',
                'description': 'National ID or Driver License Number',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 9', 'Art. 87'],
                'uavg_articles': ['Art. 46'],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            }
        }
        
        self.salesforce_security_patterns = {
            'hardcoded_password': {
                'pattern': r'(?i)(password|passwd|pwd|wachtwoord|secret)\s*[=:]\s*["\'][^"\']{4,}["\']',
                'description': 'Hardcoded Password or Secret',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            },
            'salesforce_session_id': {
                'pattern': r'(?i)(session[_\s]?id|sid)\s*[=:]\s*["\'][A-Za-z0-9!]{15,}["\']',
                'description': 'Salesforce Session ID Exposed',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            },
            'consumer_secret': {
                'pattern': r'(?i)(consumer[_\s]?secret|client[_\s]?secret)\s*[=:]\s*["\'][A-Za-z0-9+/=]{20,}["\']',
                'description': 'OAuth Consumer/Client Secret Exposed',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            },
            'api_key_exposed': {
                'pattern': r'(?i)(api[_\-]?key|apikey|access[_\-]?token)\s*[=:]\s*["\'][A-Za-z0-9_-]{20,}["\']',
                'description': 'API Key or Access Token Exposed',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            },
            'soql_injection': {
                'pattern': r'(?i)Database\.(query|getQueryLocator)\s*\([^)]*\+[^)]*\)|String\.escapeSingleQuotes\s*\([^)]*\)',
                'description': 'Potential SOQL Injection Risk',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC7.1']
            },
            'xss_vulnerability': {
                'pattern': r'(?i)(innerHTML|outerHTML|document\.write|eval\s*\(|\.html\s*\()',
                'description': 'Potential XSS Vulnerability',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC7.1']
            },
            'debug_statement': {
                'pattern': r'(?i)(System\.debug|console\.log|System\.assert)\s*\([^)]*(?:password|secret|token|key|credential)[^)]*\)',
                'description': 'Debug Statement with Sensitive Data',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC7.2']
            },
            'without_sharing': {
                'pattern': r'(?i)class\s+\w+\s+(?:without\s+sharing)',
                'description': 'Apex Class Without Sharing (Security Risk)',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.3']
            },
            'crud_fls_bypass': {
                'pattern': r'(?i)(?:insert|update|delete|upsert)\s+\w+\s*;(?!.*(?:isCreateable|isUpdateable|isDeletable|isAccessible))',
                'description': 'DML Without CRUD/FLS Check',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.3']
            }
        }
        
        self.salesforce_specific_patterns = {
            'contact_pii_query': {
                'pattern': r'(?i)SELECT\s+[^;]*(?:Email|Phone|MobilePhone|HomePhone|Birthdate|MailingAddress|OtherAddress)[^;]*FROM\s+(?:Contact|Lead|Account)',
                'description': 'Query Accessing Contact PII Fields',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6', 'Art. 13'],
                'uavg_articles': ['Art. 3'],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            },
            'health_data_query': {
                'pattern': r'(?i)SELECT\s+[^;]*(?:Health|Medical|Diagnosis|Treatment|Insurance)[^;]*FROM',
                'description': 'Query Accessing Health/Medical Data',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 9'],
                'uavg_articles': ['Art. 22'],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            },
            'financial_data_query': {
                'pattern': r'(?i)SELECT\s+[^;]*(?:CreditScore|Income|Salary|BankAccount|PaymentMethod)[^;]*FROM',
                'description': 'Query Accessing Financial Data',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 32'],
                'uavg_articles': ['Art. 3'],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            },
            'bulk_data_export': {
                'pattern': r'(?i)(?:QueryLocator|Database\.getQueryLocator|Batchable|FOR\s+UPDATE)',
                'description': 'Bulk Data Export/Processing Pattern',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6', 'Art. 44'],
                'uavg_articles': [],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            },
            'external_callout': {
                'pattern': r'(?i)(?:Http\.send|HttpRequest|ExternalService|NamedCredential)',
                'description': 'External HTTP Callout (Data Transfer Risk)',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 44', 'Art. 46'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.6', 'CC6.7']
            },
            'platform_event': {
                'pattern': r'(?i)(?:EventBus\.publish|Platform\s*Event|__e\b)',
                'description': 'Platform Event Publishing (Data Flow)',
                'severity': 'Low',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': [],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            }
        }
        
        self.fraud_detection_patterns = {
            'price_manipulation': {
                'pattern': r'(?i)(?:UnitPrice|TotalPrice|Amount|Discount)\s*=\s*(?:0|null|-)',
                'description': 'Potential Price Manipulation Pattern',
                'severity': 'Critical',
                'gdpr_articles': [],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC7.2', 'CC7.4']
            },
            'approval_bypass': {
                'pattern': r'(?i)(?:IsApproved|ApprovalStatus|Approval__c)\s*=\s*(?:true|["\']Approved["\'])',
                'description': 'Hardcoded Approval Status (Bypass Risk)',
                'severity': 'High',
                'gdpr_articles': [],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC5.2', 'CC7.2']
            },
            'record_ownership_change': {
                'pattern': r'(?i)(?:OwnerId|CreatedById|LastModifiedById)\s*=\s*["\'][0-9a-zA-Z]{15,18}["\']',
                'description': 'Hardcoded Record Ownership Change',
                'severity': 'High',
                'gdpr_articles': [],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC5.2', 'CC6.3']
            },
            'audit_field_manipulation': {
                'pattern': r'(?i)(?:CreatedDate|LastModifiedDate|SystemModstamp)\s*=',
                'description': 'Audit Field Manipulation Attempt',
                'severity': 'Critical',
                'gdpr_articles': [],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC7.2', 'CC7.4']
            },
            'sharing_bypass': {
                'pattern': r'(?i)(?:SharingModel|OrgWideDefaults|SharingRules)\s*=\s*["\'](?:None|Private|Read)["\']',
                'description': 'Sharing Model Bypass Configuration',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.3']
            },
            'system_admin_check': {
                'pattern': r'(?i)Profile\.Name\s*(?:==|!=)\s*["\']System\s*Administrator["\']',
                'description': 'System Administrator Profile Check (Privilege Escalation Risk)',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.3']
            }
        }
    
    def scan(self, repo_url: Optional[str] = None, 
             directory_path: Optional[str] = None,
             access_token: Optional[str] = None,
             branch: str = "main",
             scan_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Scan a Salesforce code repository for compliance issues.
        
        Args:
            repo_url: Git repository URL (GitHub, Bitbucket, GitLab, Azure DevOps)
            directory_path: Local directory path (alternative to repo_url)
            access_token: Access token for private repositories
            branch: Git branch to scan (default: main)
            scan_config: Configuration for scan options
            
        Returns:
            Comprehensive scan results with findings and compliance assessment
        """
        self.start_time = time.time()
        
        scan_config = scan_config or {
            'scan_pii': True,
            'scan_security': True,
            'scan_salesforce_specific': True,
            'scan_fraud': True,
            'frameworks': ['gdpr', 'uavg', 'nis2', 'soc2']
        }
        
        try:
            scan_path = None
            temp_dir = None
            
            if repo_url:
                logger.info(f"Cloning Salesforce repository: {repo_url}")
                temp_dir = tempfile.mkdtemp(prefix="salesforce_scan_")
                
                clone_cmd = ['git', 'clone', '--depth', '1', '--branch', branch]
                
                if access_token:
                    if 'github.com' in repo_url:
                        auth_url = repo_url.replace('https://', f'https://{access_token}@')
                    elif 'bitbucket.org' in repo_url:
                        auth_url = repo_url.replace('https://', f'https://x-token-auth:{access_token}@')
                    elif 'gitlab.com' in repo_url:
                        auth_url = repo_url.replace('https://', f'https://oauth2:{access_token}@')
                    elif 'dev.azure.com' in repo_url:
                        auth_url = repo_url.replace('https://', f'https://{access_token}@')
                    else:
                        auth_url = repo_url
                else:
                    auth_url = repo_url
                
                clone_cmd.extend([auth_url, temp_dir])
                
                result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    error_msg = result.stderr if result.stderr else "Unknown clone error"
                    if access_token and access_token in error_msg:
                        error_msg = error_msg.replace(access_token, '***')
                    return self._build_error_result(f"Failed to clone repository: {error_msg}")
                
                scan_path = temp_dir
                
            elif directory_path:
                if not os.path.exists(directory_path):
                    return self._build_error_result(f"Directory not found: {directory_path}")
                scan_path = directory_path
            else:
                return self._build_error_result("Either repo_url or directory_path must be provided")
            
            findings = []
            files_scanned = 0
            
            for root, dirs, files in os.walk(scan_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'dist', 'build']]
                
                for file in files:
                    if any(file.endswith(ext) for ext in self.salesforce_file_extensions):
                        file_path = os.path.join(root, file)
                        try:
                            file_findings = self._scan_file(file_path, scan_path, scan_config)
                            findings.extend(file_findings)
                            files_scanned += 1
                        except Exception as e:
                            logger.warning(f"Error scanning file {file_path}: {str(e)}")
            
            compliance_assessment = self._assess_compliance(findings)
            
            result = self._build_result(
                findings=findings,
                files_scanned=files_scanned,
                repo_url=repo_url,
                directory_path=directory_path,
                compliance_assessment=compliance_assessment,
                scan_config=scan_config
            )
            
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Salesforce repository scan failed: {str(e)}")
            return self._build_error_result(str(e))
    
    def _scan_file(self, file_path: str, base_path: str, scan_config: Dict) -> List[Dict[str, Any]]:
        """Scan a single file for Salesforce-specific compliance issues."""
        findings = []
        relative_path = os.path.relpath(file_path, base_path)
        filename = os.path.basename(file_path)
        
        if any(excluded in filename for excluded in self.excluded_files):
            logger.debug(f"Skipping excluded file: {filename}")
            return findings
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return findings
        
        if scan_config.get('scan_pii', True):
            for pattern_name, pattern_info in self.salesforce_pii_patterns.items():
                try:
                    regex = re.compile(pattern_info['pattern'], re.IGNORECASE | re.MULTILINE)
                    for match in regex.finditer(content):
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(self._create_finding(
                            category='pii_exposure',
                            pattern_name=pattern_name,
                            pattern_info=pattern_info,
                            file_path=relative_path,
                            line_number=line_num,
                            matched_text=match.group()[:50],
                            context=self._get_context(lines, line_num)
                        ))
                except re.error as e:
                    logger.warning(f"Regex error for pattern {pattern_name}: {e}")
        
        if scan_config.get('scan_security', True):
            for pattern_name, pattern_info in self.salesforce_security_patterns.items():
                try:
                    regex = re.compile(pattern_info['pattern'], re.IGNORECASE | re.MULTILINE)
                    for match in regex.finditer(content):
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(self._create_finding(
                            category='security_vulnerability',
                            pattern_name=pattern_name,
                            pattern_info=pattern_info,
                            file_path=relative_path,
                            line_number=line_num,
                            matched_text=match.group()[:50],
                            context=self._get_context(lines, line_num)
                        ))
                except re.error as e:
                    logger.warning(f"Regex error for pattern {pattern_name}: {e}")
        
        if scan_config.get('scan_salesforce_specific', True):
            for pattern_name, pattern_info in self.salesforce_specific_patterns.items():
                try:
                    regex = re.compile(pattern_info['pattern'], re.IGNORECASE | re.MULTILINE)
                    for match in regex.finditer(content):
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(self._create_finding(
                            category='salesforce_specific',
                            pattern_name=pattern_name,
                            pattern_info=pattern_info,
                            file_path=relative_path,
                            line_number=line_num,
                            matched_text=match.group()[:50],
                            context=self._get_context(lines, line_num)
                        ))
                except re.error as e:
                    logger.warning(f"Regex error for pattern {pattern_name}: {e}")
        
        if scan_config.get('scan_fraud', True):
            for pattern_name, pattern_info in self.fraud_detection_patterns.items():
                try:
                    regex = re.compile(pattern_info['pattern'], re.IGNORECASE | re.MULTILINE)
                    for match in regex.finditer(content):
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(self._create_finding(
                            category='fraud_detection',
                            pattern_name=pattern_name,
                            pattern_info=pattern_info,
                            file_path=relative_path,
                            line_number=line_num,
                            matched_text=match.group()[:50],
                            context=self._get_context(lines, line_num)
                        ))
                except re.error as e:
                    logger.warning(f"Regex error for pattern {pattern_name}: {e}")
        
        return findings
    
    def _create_finding(self, category: str, pattern_name: str, pattern_info: Dict,
                       file_path: str, line_number: int, matched_text: str,
                       context: str) -> Dict[str, Any]:
        """Create a standardized finding entry."""
        severity = pattern_info['severity']
        gdpr_articles = pattern_info.get('gdpr_articles', [])
        
        severity_priority = {'Critical': 'Critical - Immediate action required', 
                            'High': 'High - Address within 24-48 hours',
                            'Medium': 'Medium - Review within 7 days', 
                            'Low': 'Low - Address in next sprint'}
        severity_effort = {'Critical': '4-8 hours - Urgent remediation',
                          'High': '2-4 hours - Priority fix',
                          'Medium': '1-4 hours - Investigation and remediation',
                          'Low': '1-2 hours - Minor adjustment'}
        category_classification = {'pii_exposure': 'Personal Data (PII)',
                                   'security_vulnerability': 'System Configuration',
                                   'salesforce_specific': 'Salesforce Platform',
                                   'fraud_detection': 'Fraud/Compliance Risk'}
        category_impact = {'pii_exposure': 'Potential GDPR violation and data breach risk',
                          'security_vulnerability': 'Security vulnerability requiring immediate attention',
                          'salesforce_specific': 'Salesforce-specific compliance concern',
                          'fraud_detection': 'Potential fraud or unauthorized activity pattern'}
        
        return {
            'id': f"SF-{self.scan_id}-{uuid.uuid4().hex[:6]}",
            'category': category,
            'type': pattern_name,
            'title': f"{category.replace('_', ' ').title()}: {pattern_name.replace('_', ' ').title()}",
            'description': pattern_info['description'],
            'severity': severity,
            'file_path': file_path,
            'line_number': line_number,
            'location': f"{file_path}:{line_number}" if file_path and line_number else file_path or 'Unknown',
            'source': file_path,
            'source_file': file_path,
            'matched_text': matched_text,
            'context': context,
            'gdpr_articles': gdpr_articles,
            'uavg_articles': pattern_info.get('uavg_articles', []),
            'nis2_articles': pattern_info.get('nis2_articles', []),
            'soc2_controls': pattern_info.get('soc2_controls', []),
            'remediation': self._get_remediation(pattern_name, category),
            'data_classification': category_classification.get(category, 'Unknown'),
            'business_impact': category_impact.get(category, 'Requires review'),
            'remediation_priority': severity_priority.get(severity, 'Review required'),
            'estimated_effort': severity_effort.get(severity, '1-2 hours'),
            'compliance_requirements': gdpr_articles,
            'recommendations': [{
                'title': f'Review and Remediate {severity}',
                'description': f'Address: {pattern_info["description"]}',
                'implementation': 'Investigate the finding and implement appropriate remediation',
                'effort': severity_effort.get(severity, '1-2 hours').split(' - ')[0],
                'verification': 'Confirm remediation complete'
            }],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_context(self, lines: List[str], line_num: int, context_lines: int = 2) -> str:
        """Get surrounding context for a finding."""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        return '\n'.join(lines[start:end])
    
    def _get_remediation(self, pattern_name: str, category: str) -> str:
        """Get remediation advice for a finding type."""
        remediations = {
            'bsn_number': 'Remove or encrypt BSN numbers. Use Salesforce Shield for encryption.',
            'kvk_number': 'Review if KvK number storage is necessary. Apply data minimization.',
            'hardcoded_password': 'Move credentials to Named Credentials or Custom Metadata.',
            'salesforce_session_id': 'Never store session IDs. Use Named Credentials for auth.',
            'consumer_secret': 'Store OAuth secrets in Named Credentials or Protected Custom Settings.',
            'api_key_exposed': 'Use Named Credentials or encrypted Custom Settings for API keys.',
            'soql_injection': 'Use bind variables or String.escapeSingleQuotes() for dynamic SOQL.',
            'xss_vulnerability': 'Use JSENCODE, HTMLENCODE, or Lightning Data Service.',
            'without_sharing': 'Review sharing requirements. Use "with sharing" when possible.',
            'crud_fls_bypass': 'Add Schema.sObjectType checks before DML operations.',
            'price_manipulation': 'Add validation rules and approval processes for price changes.',
            'approval_bypass': 'Remove hardcoded approval logic. Use Salesforce Approval Processes.',
            'audit_field_manipulation': 'Audit fields are system-managed. Remove modification attempts.',
        }
        return remediations.get(pattern_name, f'Review and remediate {category} issue.')
    
    def _assess_compliance(self, findings: List[Dict]) -> Dict[str, Any]:
        """Assess compliance status across all frameworks."""
        gdpr_findings = [f for f in findings if f.get('gdpr_articles')]
        uavg_findings = [f for f in findings if f.get('uavg_articles')]
        nis2_findings = [f for f in findings if f.get('nis2_articles')]
        soc2_findings = [f for f in findings if f.get('soc2_controls')]
        fraud_findings = [f for f in findings if f.get('category') == 'fraud_detection']
        
        critical_count = len([f for f in findings if f['severity'] == 'Critical'])
        high_count = len([f for f in findings if f['severity'] == 'High'])
        medium_count = len([f for f in findings if f['severity'] == 'Medium'])
        
        base_score = 100
        base_score -= critical_count * 15
        base_score -= high_count * 8
        base_score -= medium_count * 3
        compliance_score = max(0, min(100, base_score))
        
        return {
            'overall_score': compliance_score,
            'gdpr': {
                'finding_count': len(gdpr_findings),
                'affected_articles': list(set(a for f in gdpr_findings for a in f.get('gdpr_articles', []))),
                'status': 'compliant' if len(gdpr_findings) == 0 else 'non-compliant'
            },
            'uavg': {
                'finding_count': len(uavg_findings),
                'affected_articles': list(set(a for f in uavg_findings for a in f.get('uavg_articles', []))),
                'status': 'compliant' if len(uavg_findings) == 0 else 'non-compliant'
            },
            'nis2': {
                'finding_count': len(nis2_findings),
                'affected_articles': list(set(a for f in nis2_findings for a in f.get('nis2_articles', []))),
                'status': 'compliant' if len(nis2_findings) == 0 else 'non-compliant'
            },
            'soc2': {
                'finding_count': len(soc2_findings),
                'affected_controls': list(set(c for f in soc2_findings for c in f.get('soc2_controls', []))),
                'status': 'compliant' if len(soc2_findings) == 0 else 'non-compliant'
            },
            'fraud': {
                'finding_count': len(fraud_findings),
                'status': 'clean' if len(fraud_findings) == 0 else 'risks_detected'
            },
            'severity_breakdown': {
                'critical': critical_count,
                'high': high_count,
                'medium': medium_count,
                'low': len([f for f in findings if f['severity'] == 'Low'])
            }
        }
    
    def _build_result(self, findings: List[Dict], files_scanned: int,
                      repo_url: Optional[str], directory_path: Optional[str],
                      compliance_assessment: Dict, scan_config: Dict) -> Dict[str, Any]:
        """Build comprehensive scan result."""
        scan_duration = time.time() - (self.start_time or time.time())
        
        return {
            'success': True,
            'scan_id': self.scan_id,
            'scan_type': 'Salesforce Code Repository',
            'scanner_type': 'salesforce_repo',
            'timestamp': datetime.utcnow().isoformat(),
            'duration_seconds': round(scan_duration, 2),
            'source': {
                'type': 'repository' if repo_url else 'directory',
                'url': repo_url,
                'path': directory_path
            },
            'files_scanned': files_scanned,
            'total_findings': len(findings),
            'findings': findings,
            'compliance': compliance_assessment,
            'compliance_score': compliance_assessment['overall_score'],
            'severity': self._get_overall_severity(findings),
            'summary': {
                'pii_exposures': len([f for f in findings if f['category'] == 'pii_exposure']),
                'security_issues': len([f for f in findings if f['category'] == 'security_vulnerability']),
                'salesforce_issues': len([f for f in findings if f['category'] == 'salesforce_specific']),
                'fraud_patterns': len([f for f in findings if f['category'] == 'fraud_detection']),
                'critical_findings': len([f for f in findings if f['severity'] == 'Critical']),
                'high_findings': len([f for f in findings if f['severity'] == 'High']),
                'frameworks_affected': self._get_affected_frameworks(compliance_assessment)
            },
            'region': self.region,
            'scan_config': scan_config
        }
    
    def _get_overall_severity(self, findings: List[Dict]) -> str:
        """Determine overall severity based on findings."""
        if any(f['severity'] == 'Critical' for f in findings):
            return 'critical'
        elif any(f['severity'] == 'High' for f in findings):
            return 'high'
        elif any(f['severity'] == 'Medium' for f in findings):
            return 'medium'
        elif findings:
            return 'low'
        return 'none'
    
    def _get_affected_frameworks(self, compliance: Dict) -> List[str]:
        """Get list of affected compliance frameworks."""
        affected = []
        if compliance['gdpr']['finding_count'] > 0:
            affected.append('GDPR')
        if compliance['uavg']['finding_count'] > 0:
            affected.append('UAVG')
        if compliance['nis2']['finding_count'] > 0:
            affected.append('NIS2')
        if compliance['soc2']['finding_count'] > 0:
            affected.append('SOC2')
        if compliance['fraud']['finding_count'] > 0:
            affected.append('Fraud')
        return affected
    
    def _build_error_result(self, error_message: str) -> Dict[str, Any]:
        """Build error result."""
        return {
            'success': False,
            'scan_id': self.scan_id,
            'scan_type': 'Salesforce Code Repository',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat(),
            'duration_seconds': time.time() - (self.start_time or time.time()),
            'files_scanned': 0,
            'total_findings': 0,
            'findings': [],
            'compliance_score': 0,
            'severity': 'error'
        }
