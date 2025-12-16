"""
SAP Code Repository Scanner for DataGuardian Pro
Scans SAP ABAP, Fiori, BTP code repositories for compliance with GDPR, UAVG, NIS2, SOC2 standards.
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
    logger = get_scanner_logger("sap_repo_scanner")
except ImportError:
    logger = logging.getLogger(__name__)

from services.code_scanner import CodeScanner
from services.repo_scanner import RepoScanner


class SAPRepoScanner:
    """
    Scanner for SAP code repositories (ABAP, Fiori, BTP, CAP) to detect 
    PII exposure, security vulnerabilities, and compliance issues.
    """
    
    def __init__(self, region: str = "Netherlands"):
        """Initialize SAP Repository Scanner with compliance-focused patterns."""
        self.region = region
        self.scan_id = str(uuid.uuid4())[:8]
        self.start_time = None
        
        self.sap_file_extensions = [
            '.abap', '.prog', '.clas', '.fugr', '.tabl', '.doma', '.dtel',
            '.js', '.jsx', '.ts', '.tsx', '.json', '.xml', '.yaml', '.yml',
            '.html', '.css', '.scss', '.less', '.cds', '.hdbtable', '.hdbview',
            '.hdbprocedure', '.hdbfunction', '.hdbrole', '.hdbgrants',
            '.properties', '.env', '.config', '.txt', '.md'
        ]
        
        self.excluded_files = [
            'CHANGELOG', 'changelog', 'HISTORY', 'history', 'NEWS', 'RELEASES',
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'Gemfile.lock',
            'composer.lock', 'poetry.lock', 'Cargo.lock', 'go.sum'
        ]
        
        self.sap_pii_patterns = {
            'bsn_number': {
                'pattern': r'(?i)(?:bsn|burgerservicenummer|sofi|citizen.?service)\s*[=:]\s*["\']?([0-9]{9})["\']?',
                'description': 'Netherlands BSN (Social Security Number)',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 9', 'Art. 87'],
                'uavg_articles': ['Art. 46'],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            },
            'kvk_number': {
                'pattern': r'(?i)(?:kvk|kamer.?van.?koophandel|chamber.?of.?commerce|coc)\s*[=:]\s*["\']?([0-9]{8})["\']?',
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
                'pattern': r'(?i)(?:email|e-mail|mail)\s*[=:]\s*["\']([A-Za-z0-9._%+-]+@(?!example\.com|test\.com|localhost)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})["\']',
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
                'pattern': r'(?i)(?:passport|paspoort|reisdocument)\s*[=:]\s*["\']?([A-Z]{2}[A-Z0-9]{6}[0-9])["\']?',
                'description': 'Netherlands Passport Number',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 9', 'Art. 87'],
                'uavg_articles': ['Art. 46'],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            },
            'credit_card': {
                'pattern': r'(?i)(?:card|credit|cc|creditcard)\s*[=:]\s*["\']?(4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})["\']?',
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
            }
        }
        
        self.sap_security_patterns = {
            'hardcoded_password': {
                'pattern': r'(?i)(password|passwd|pwd|wachtwoord)\s*[=:]\s*["\'][^"\']{4,}["\']',
                'description': 'Hardcoded Password',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            },
            'sap_client_secret': {
                'pattern': r'(?i)(client_?secret|clientsecret)\s*[=:]\s*["\'][A-Za-z0-9+/=]{20,}["\']',
                'description': 'SAP Client Secret Exposed',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            },
            'api_key_exposed': {
                'pattern': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][A-Za-z0-9_-]{20,}["\']',
                'description': 'API Key Exposed in Code',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            },
            'sql_injection_risk': {
                'pattern': r'(?i)(SELECT|INSERT|UPDATE|DELETE|DROP).*\+\s*["\']?\w+["\']?\s*\+',
                'description': 'Potential SQL Injection Vulnerability',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC7.1']
            },
            'abap_authority_bypass': {
                'pattern': r'(?i)AUTHORITY-CHECK\s+OBJECT\s+["\'][^"\']+["\']\s+ID\s+["\']ACTVT["\']\s+FIELD\s+["\'](\*|X)',
                'description': 'ABAP Authority Check Bypass Pattern',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.3']
            },
            'missing_auth_check': {
                'pattern': r'(?i)(?:FUNCTION|METHOD)\s+\w+\.\s*(?:(?!AUTHORITY-CHECK).)*?(?:SELECT|UPDATE|DELETE)',
                'description': 'Missing Authorization Check in ABAP',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.3']
            },
            'btp_binding_exposed': {
                'pattern': r'(?i)(VCAP_SERVICES|xsuaa|hana|destination)\s*[=:]\s*["\'][^"\']{50,}',
                'description': 'SAP BTP Service Binding Exposed',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            },
            'fiori_xss_risk': {
                'pattern': r'(?i)(innerHTML|outerHTML|document\.write)\s*=',
                'description': 'Potential XSS Vulnerability in Fiori/UI5',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC7.1']
            },
            'unencrypted_storage': {
                'pattern': r'(?i)(localStorage|sessionStorage)\s*\.\s*(setItem|getItem)\s*\([^)]*(?:password|token|secret|key)',
                'description': 'Sensitive Data in Browser Storage',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            },
            'hana_db_credentials': {
                'pattern': r'(?i)(hana|hdb)\s*(host|user|password)\s*[=:]\s*["\'][^"\']+["\']',
                'description': 'SAP HANA Database Credentials',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            }
        }
        
        self.sap_abap_patterns = {
            'pa0002_access': {
                'pattern': r'(?i)(?:SELECT|UPDATE|DELETE|INSERT)\s+(?:\*|SINGLE)?\s*FROM\s+PA0002',
                'description': 'Direct access to SAP HR Personal Data Table PA0002',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 6', 'Art. 9', 'Art. 32'],
                'uavg_articles': ['Art. 46'],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.7']
            },
            'kna1_access': {
                'pattern': r'(?i)(?:SELECT|UPDATE|DELETE|INSERT)\s+(?:\*|SINGLE)?\s*FROM\s+KNA1',
                'description': 'Direct access to SAP Customer Master Table KNA1',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 32'],
                'uavg_articles': [],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            },
            'lfa1_access': {
                'pattern': r'(?i)(?:SELECT|UPDATE|DELETE|INSERT)\s+(?:\*|SINGLE)?\s*FROM\s+LFA1',
                'description': 'Direct access to SAP Vendor Master Table LFA1',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 32'],
                'uavg_articles': [],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            },
            'but000_access': {
                'pattern': r'(?i)(?:SELECT|UPDATE|DELETE|INSERT)\s+(?:\*|SINGLE)?\s*FROM\s+BUT000',
                'description': 'Direct access to SAP Business Partner Table BUT000',
                'severity': 'High',
                'gdpr_articles': ['Art. 6', 'Art. 32'],
                'uavg_articles': [],
                'nis2_articles': [],
                'soc2_controls': ['CC6.1']
            },
            'bseg_access': {
                'pattern': r'(?i)(?:SELECT|UPDATE|DELETE|INSERT)\s+(?:\*|SINGLE)?\s*FROM\s+BSEG',
                'description': 'Direct access to SAP Financial Document Segment Table',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 6'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1']
            },
            'usr02_access': {
                'pattern': r'(?i)(?:SELECT|UPDATE|DELETE|INSERT)\s+(?:\*|SINGLE)?\s*FROM\s+USR02',
                'description': 'Direct access to SAP User Logon Data Table',
                'severity': 'Critical',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.6']
            },
            'debug_statement': {
                'pattern': r'(?i)\bBREAK-POINT\b|\bDEBUGGING\b',
                'description': 'ABAP Debug Statement in Production Code',
                'severity': 'Medium',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': [],
                'soc2_controls': ['CC7.1']
            },
            'native_sql': {
                'pattern': r'(?i)EXEC\s+SQL|NATIVE\s+SQL',
                'description': 'Native SQL Usage (Bypass of Authority Checks)',
                'severity': 'High',
                'gdpr_articles': ['Art. 32'],
                'uavg_articles': [],
                'nis2_articles': ['Art. 21'],
                'soc2_controls': ['CC6.1', 'CC6.3']
            }
        }
        
        self.compliance_frameworks = {
            'gdpr': {
                'name': 'GDPR',
                'full_name': 'General Data Protection Regulation',
                'key_articles': ['Art. 6', 'Art. 9', 'Art. 17', 'Art. 32', 'Art. 87']
            },
            'uavg': {
                'name': 'UAVG',
                'full_name': 'Uitvoeringswet Algemene Verordening Gegevensbescherming',
                'key_articles': ['Art. 3', 'Art. 46']
            },
            'nis2': {
                'name': 'NIS2',
                'full_name': 'Network and Information Security Directive 2',
                'key_articles': ['Art. 21', 'Art. 23']
            },
            'soc2': {
                'name': 'SOC2 Type II',
                'full_name': 'Service Organization Control 2',
                'key_controls': ['CC6.1', 'CC6.3', 'CC6.6', 'CC6.7', 'CC7.1', 'CC7.2']
            }
        }
    
    def scan_repository(self, repo_url: Optional[str] = None, directory_path: Optional[str] = None,
                        branch: Optional[str] = None, auth_token: Optional[str] = None,
                        scan_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Scan SAP code repository for compliance issues.
        
        Args:
            repo_url: GitHub/Bitbucket/GitLab repository URL
            directory_path: Local directory path (alternative to repo_url)
            branch: Branch to scan
            auth_token: Authentication token for private repos
            scan_config: Additional scan configuration
            
        Returns:
            Comprehensive scan results with compliance findings
        """
        self.start_time = time.time()
        scan_config = scan_config or {}
        
        code_scanner = CodeScanner(
            extensions=self.sap_file_extensions,
            region=self.region,
            include_article_refs=True
        )
        
        findings = []
        files_scanned = 0
        scan_path = None
        temp_dir = None
        
        try:
            if repo_url:
                repo_scanner = RepoScanner(code_scanner)
                clone_result = repo_scanner.clone_repository(
                    repo_url=repo_url,
                    branch=branch,
                    auth_token=auth_token
                )
                
                if clone_result.get('status') == 'error':
                    return self._build_error_result(clone_result.get('message', 'Clone failed'))
                
                scan_path = clone_result.get('repo_path')
                temp_dir = scan_path
                
            elif directory_path:
                if os.path.exists(directory_path):
                    scan_path = directory_path
                else:
                    return self._build_error_result(f"Directory not found: {directory_path}")
            else:
                return self._build_error_result("No repository URL or directory provided")
            
            for root, dirs, files in os.walk(scan_path):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.idea', 'dist', 'build']]
                
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in self.sap_file_extensions or file in ['.env', 'manifest.json', 'package.json', 'xs-app.json']:
                        file_path = os.path.join(root, file)
                        try:
                            file_findings = self._scan_file(file_path, scan_path)
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
            logger.error(f"SAP repository scan failed: {str(e)}")
            return self._build_error_result(str(e))
    
    def _scan_file(self, file_path: str, base_path: str) -> List[Dict[str, Any]]:
        """Scan a single file for SAP-specific compliance issues."""
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
        
        for pattern_name, pattern_info in self.sap_pii_patterns.items():
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
        
        for pattern_name, pattern_info in self.sap_security_patterns.items():
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
        
        for pattern_name, pattern_info in self.sap_abap_patterns.items():
            try:
                regex = re.compile(pattern_info['pattern'], re.IGNORECASE | re.MULTILINE)
                for match in regex.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append(self._create_finding(
                        category='sap_specific',
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
                                   'sap_specific': 'System Configuration'}
        category_impact = {'pii_exposure': 'Potential GDPR violation and data breach risk',
                          'security_vulnerability': 'Security vulnerability requiring immediate attention',
                          'sap_specific': 'Potential security or compliance impact requiring investigation'}
        
        return {
            'id': f"SAP-{self.scan_id}-{uuid.uuid4().hex[:6]}",
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
            'bsn_number': 'Remove or encrypt BSN numbers. Use SAP Data Masking or tokenization.',
            'kvk_number': 'Review if KvK number storage is necessary. Apply data minimization.',
            'hardcoded_password': 'Move credentials to SAP Secure Store or environment variables.',
            'sap_client_secret': 'Use SAP BTP Destination Service or credential store.',
            'api_key_exposed': 'Store API keys in SAP Credential Store or BTP Secrets.',
            'sql_injection_risk': 'Use parameterized queries or prepared statements.',
            'abap_authority_bypass': 'Review and restrict authorization object assignments.',
            'pa0002_access': 'Implement proper authorization checks (AUTHORITY-CHECK OBJECT).',
            'kna1_access': 'Add authorization checks for customer master data access.',
            'hana_db_credentials': 'Use HDI container binding or secure store for credentials.',
            'fiori_xss_risk': 'Use UI5 formatter functions instead of direct DOM manipulation.',
        }
        return remediations.get(pattern_name, f'Review and remediate {category} issue.')
    
    def _assess_compliance(self, findings: List[Dict]) -> Dict[str, Any]:
        """Assess compliance status across all frameworks."""
        gdpr_findings = [f for f in findings if f.get('gdpr_articles')]
        uavg_findings = [f for f in findings if f.get('uavg_articles')]
        nis2_findings = [f for f in findings if f.get('nis2_articles')]
        soc2_findings = [f for f in findings if f.get('soc2_controls')]
        
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
            'scan_type': 'SAP Code Repository',
            'scanner_type': 'sap_repo',
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
                'sap_specific_issues': len([f for f in findings if f['category'] == 'sap_specific']),
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
        return affected
    
    def _build_error_result(self, error_message: str) -> Dict[str, Any]:
        """Build error result."""
        return {
            'success': False,
            'scan_id': self.scan_id,
            'scan_type': 'SAP Code Repository',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat(),
            'duration_seconds': time.time() - (self.start_time or time.time()),
            'files_scanned': 0,
            'total_findings': 0,
            'findings': [],
            'compliance_score': 0,
            'severity': 'error'
        }
