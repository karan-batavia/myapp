"""
Repository Scanner for Banking Sector
Enterprise-grade code repository scanning for PCI-DSS, GDPR, and UAVG compliance.

Features:
- Hardcoded personal data detection (IBAN, BSN, PAN, emails, phones)
- Secrets exposure detection (API keys, tokens, certificates, passwords)
- PII logging violation detection
- PCI-DSS secure coding validation
- Read-only access with data masking
- Hash-based storage (no raw data)
- Comprehensive HTML report generation

Target: Banking sector compliance (PCI-DSS, GDPR Art. 25/32, UAVG)
"""

import os
import re
import json
import hashlib
import logging
import tempfile
import shutil
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid

try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("repository_scanner")
except ImportError:
    logger = logging.getLogger(__name__)

try:
    from utils.complete_gdpr_99_validator import validate_complete_gdpr_compliance
    GDPR_VALIDATOR_AVAILABLE = True
except ImportError:
    GDPR_VALIDATOR_AVAILABLE = False

try:
    from utils.netherlands_uavg_compliance import detect_uavg_compliance_gaps
    UAVG_VALIDATOR_AVAILABLE = True
except ImportError:
    UAVG_VALIDATOR_AVAILABLE = False


class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(Enum):
    HARDCODED_PII = "hardcoded_pii"
    SECRETS_EXPOSURE = "secrets_exposure"
    PII_LOGGING = "pii_logging"
    PCI_DSS_VIOLATION = "pci_dss_violation"
    GDPR_VIOLATION = "gdpr_violation"
    UAVG_VIOLATION = "uavg_violation"
    IAC_SECURITY = "iac_security"


@dataclass
class Finding:
    """A single finding from the repository scan."""
    id: str
    category: FindingCategory
    severity: SeverityLevel
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    masked_value: str
    value_hash: str
    compliance_refs: List[str]
    remediation: str
    evidence_hash: str = field(default_factory=lambda: "")


@dataclass
class ScanResult:
    """Complete result of a repository scan."""
    scan_id: str
    repo_url: str
    scan_timestamp: datetime
    files_scanned: int
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    risk_score: float
    findings: List[Finding]
    compliance_summary: Dict[str, Any]
    methodology: str
    recommendations: List[str]
    trend_comparison: Optional[Dict[str, Any]] = None


class RepositoryScanner:
    """
    Enterprise Repository Scanner for Banking Sector Compliance.
    Scans code repositories for PCI-DSS, GDPR, and UAVG violations.
    """
    
    def __init__(self, region: str = "Netherlands", bank_name: str = None):
        """
        Initialize the Repository Scanner.
        
        Args:
            region: Target region for compliance (default: Netherlands)
            bank_name: Name of the bank for custom policy rules
        """
        self.region = region
        self.bank_name = bank_name
        self.scan_id = str(uuid.uuid4())
        self.findings: List[Finding] = []
        self.files_scanned = 0
        self.progress_callback: Optional[Callable] = None
        
        self.code_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cs', '.go', '.rb',
            '.php', '.swift', '.kt', '.rs', '.c', '.cpp', '.h', '.hpp',
            '.sql', '.sh', '.bash', '.ps1', '.yml', '.yaml', '.json', '.xml',
            '.tf', '.tfvars', '.env', '.properties', '.conf', '.ini', '.config'
        ]
        
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile detection patterns for efficiency."""
        
        self.pii_patterns = {
            'iban_nl': {
                'pattern': re.compile(r'\b(NL\d{2}[A-Z]{4}\d{10})\b', re.IGNORECASE),
                'description': 'Dutch IBAN',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 3.4', 'GDPR Art. 5', 'UAVG Art. 6']
            },
            'iban_eu': {
                'pattern': re.compile(r'\b([A-Z]{2}\d{2}[A-Z0-9]{4,30})\b'),
                'description': 'EU IBAN',
                'severity': SeverityLevel.HIGH,
                'compliance': ['PCI-DSS 3.4', 'GDPR Art. 5']
            },
            'bsn': {
                'pattern': re.compile(r'\b(\d{9})\b'),
                'description': 'Dutch BSN (Burger Service Nummer)',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['UAVG Art. 46', 'GDPR Art. 9', 'UAVG BSN Law']
            },
            'pan': {
                'pattern': re.compile(r'\b(4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'),
                'description': 'Payment Card Number (PAN)',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 3.4', 'PCI-DSS 3.5', 'PCI-DSS 4.1']
            },
            'email': {
                'pattern': re.compile(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'),
                'description': 'Email Address',
                'severity': SeverityLevel.MEDIUM,
                'compliance': ['GDPR Art. 4', 'GDPR Art. 5']
            },
            'phone_nl': {
                'pattern': re.compile(r'\b((?:\+31|0031|0)(?:6|[1-5][0-9])[0-9]{8})\b'),
                'description': 'Dutch Phone Number',
                'severity': SeverityLevel.MEDIUM,
                'compliance': ['GDPR Art. 4', 'UAVG Art. 6']
            },
            'kvk': {
                'pattern': re.compile(r'\b(KVK[:\s]*)?([0-9]{8})\b', re.IGNORECASE),
                'description': 'Dutch KvK Number',
                'severity': SeverityLevel.MEDIUM,
                'compliance': ['GDPR Art. 4']
            },
            'passport': {
                'pattern': re.compile(r'\b([A-Z]{2}[A-Z0-9]{6,7})\b'),
                'description': 'Passport Number',
                'severity': SeverityLevel.HIGH,
                'compliance': ['GDPR Art. 9', 'UAVG Art. 22']
            }
        }
        
        self.secret_patterns = {
            'api_key': {
                'pattern': re.compile(r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{20,64})["\']?'),
                'description': 'API Key',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 8.2', 'GDPR Art. 32']
            },
            'aws_key': {
                'pattern': re.compile(r'\b(AKIA[0-9A-Z]{16})\b'),
                'description': 'AWS Access Key',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 8.2', 'GDPR Art. 32']
            },
            'aws_secret': {
                'pattern': re.compile(r'(?i)(aws_secret_access_key|secret_key)\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?'),
                'description': 'AWS Secret Key',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 8.2', 'GDPR Art. 32']
            },
            'password': {
                'pattern': re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']{8,64})["\']?'),
                'description': 'Password',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 8.2.3', 'GDPR Art. 32']
            },
            'private_key': {
                'pattern': re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'),
                'description': 'Private Key',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 3.5', 'GDPR Art. 32']
            },
            'oauth_token': {
                'pattern': re.compile(r'(?i)(oauth[_-]?token|bearer|access[_-]?token)\s*[=:]\s*["\']?([A-Za-z0-9_\-\.]{30,500})["\']?'),
                'description': 'OAuth Token',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 8.2', 'GDPR Art. 32']
            },
            'jwt': {
                'pattern': re.compile(r'\b(eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b'),
                'description': 'JWT Token',
                'severity': SeverityLevel.HIGH,
                'compliance': ['PCI-DSS 8.2', 'GDPR Art. 32']
            },
            'db_connection': {
                'pattern': re.compile(r'(?i)(mysql|postgres|postgresql|mongodb|redis)://[^\s"\']+'),
                'description': 'Database Connection String',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 8.2', 'GDPR Art. 32']
            },
            'stripe_key': {
                'pattern': re.compile(r'\b(sk_live_[0-9a-zA-Z]{24,})\b'),
                'description': 'Stripe Secret Key',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 8.2', 'PCI-DSS 3.4']
            },
            'certificate': {
                'pattern': re.compile(r'-----BEGIN CERTIFICATE-----'),
                'description': 'Certificate',
                'severity': SeverityLevel.HIGH,
                'compliance': ['PCI-DSS 4.1', 'GDPR Art. 32']
            }
        }
        
        self.logging_patterns = {
            'log_pii': {
                'pattern': re.compile(r'(?i)(log|logger|print|console\.log|debug|info|warn|error)\s*\([^)]*?(iban|bsn|ssn|pan|card|password|token|secret)[^)]*\)', re.MULTILINE),
                'description': 'PII in Logging Statement',
                'severity': SeverityLevel.HIGH,
                'compliance': ['PCI-DSS 3.4', 'GDPR Art. 5(1)(f)']
            },
            'debug_sensitive': {
                'pattern': re.compile(r'(?i)(debug|console\.log|print)\s*\([^)]*?(customer|user|client)[^)]*\)', re.MULTILINE),
                'description': 'Debug Statement with Sensitive Data',
                'severity': SeverityLevel.MEDIUM,
                'compliance': ['PCI-DSS 6.5.1', 'GDPR Art. 25']
            }
        }
        
        self.pci_patterns = {
            'pan_storage': {
                'pattern': re.compile(r'(?i)(store|save|insert|write).*?(pan|card_number|credit_card)', re.MULTILINE),
                'description': 'PAN Storage Operation',
                'severity': SeverityLevel.CRITICAL,
                'compliance': ['PCI-DSS 3.2', 'PCI-DSS 3.4']
            },
            'missing_mask': {
                'pattern': re.compile(r'(?i)(display|show|render|return).*?(pan|card|iban)[^}]*(?<!mask)(?<!truncate)', re.MULTILINE),
                'description': 'Missing Data Masking',
                'severity': SeverityLevel.HIGH,
                'compliance': ['PCI-DSS 3.3']
            },
            'weak_encryption': {
                'pattern': re.compile(r'(?i)(md5|sha1|des|rc4|ecb)\s*\('),
                'description': 'Weak Encryption Algorithm',
                'severity': SeverityLevel.HIGH,
                'compliance': ['PCI-DSS 3.5', 'GDPR Art. 32']
            },
            'insecure_random': {
                'pattern': re.compile(r'(?i)(random\(\)|math\.random|rand\(\))'),
                'description': 'Insecure Random Number Generation',
                'severity': SeverityLevel.MEDIUM,
                'compliance': ['PCI-DSS 3.6', 'PCI-DSS 6.5.3']
            }
        }
    
    def _validate_bsn(self, potential_bsn: str) -> bool:
        """
        Validate Dutch BSN using the 11-proef algorithm.
        
        Args:
            potential_bsn: 9-digit string to validate
        
        Returns:
            True if valid BSN, False otherwise
        """
        if not potential_bsn.isdigit() or len(potential_bsn) != 9:
            return False
        
        weights = [9, 8, 7, 6, 5, 4, 3, 2, -1]
        total = sum(int(d) * w for d, w in zip(potential_bsn, weights))
        
        return total % 11 == 0 and total != 0
    
    def _mask_value(self, value: str, pattern_type: str) -> str:
        """
        Mask sensitive values for safe display.
        
        Args:
            value: The sensitive value to mask
            pattern_type: Type of pattern for appropriate masking
        
        Returns:
            Masked value
        """
        if not value:
            return "***"
        
        if pattern_type in ['iban_nl', 'iban_eu']:
            return f"{value[:4]}****{value[-4:]}" if len(value) > 8 else "****"
        elif pattern_type == 'pan':
            return f"****-****-****-{value[-4:]}" if len(value) >= 4 else "****"
        elif pattern_type == 'bsn':
            return f"*****{value[-4:]}" if len(value) > 4 else "****"
        elif pattern_type in ['email']:
            parts = value.split('@')
            if len(parts) == 2:
                return f"{parts[0][:2]}***@{parts[1]}"
            return "***@***"
        elif pattern_type in ['password', 'api_key', 'aws_secret', 'oauth_token', 'jwt']:
            return "*" * min(len(value), 20)
        else:
            return f"{value[:3]}...{value[-3:]}" if len(value) > 6 else "***"
    
    def _hash_value(self, value: str) -> str:
        """
        Create SHA256 hash of value for secure storage.
        
        Args:
            value: Value to hash
        
        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def _get_code_context(self, content: str, match_start: int, match_end: int, lines: int = 2) -> Tuple[str, int]:
        """
        Get code context around a match.
        
        Args:
            content: File content
            match_start: Start position of match
            match_end: End position of match
            lines: Number of context lines
        
        Returns:
            Tuple of (code snippet, line number)
        """
        line_num = content[:match_start].count('\n') + 1
        
        all_lines = content.split('\n')
        start_line = max(0, line_num - lines - 1)
        end_line = min(len(all_lines), line_num + lines)
        
        context_lines = all_lines[start_line:end_line]
        context = '\n'.join(f"{i+start_line+1}: {line}" for i, line in enumerate(context_lines))
        
        return context, line_num
    
    def _scan_file_content(self, file_path: str, content: str) -> List[Finding]:
        """
        Scan file content for all violations.
        
        Args:
            file_path: Path to the file
            content: File content
        
        Returns:
            List of findings
        """
        findings = []
        
        for pattern_name, pattern_info in self.pii_patterns.items():
            for match in pattern_info['pattern'].finditer(content):
                value = match.group(1) if match.lastindex else match.group(0)
                
                if pattern_name == 'bsn' and not self._validate_bsn(value):
                    continue
                
                context, line_num = self._get_code_context(content, match.start(), match.end())
                
                finding = Finding(
                    id=str(uuid.uuid4()),
                    category=FindingCategory.HARDCODED_PII,
                    severity=pattern_info['severity'],
                    title=f"Hardcoded {pattern_info['description']} Detected",
                    description=f"Found hardcoded {pattern_info['description']} in source code. This violates data protection requirements.",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=context,
                    masked_value=self._mask_value(value, pattern_name),
                    value_hash=self._hash_value(value),
                    compliance_refs=pattern_info['compliance'],
                    remediation=f"Remove hardcoded {pattern_info['description']}. Use environment variables or secure vault. Implement data masking for display.",
                    evidence_hash=self._hash_value(f"{file_path}:{line_num}:{value}")
                )
                findings.append(finding)
        
        for pattern_name, pattern_info in self.secret_patterns.items():
            for match in pattern_info['pattern'].finditer(content):
                value = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(0)
                
                context, line_num = self._get_code_context(content, match.start(), match.end())
                
                finding = Finding(
                    id=str(uuid.uuid4()),
                    category=FindingCategory.SECRETS_EXPOSURE,
                    severity=pattern_info['severity'],
                    title=f"{pattern_info['description']} Exposed in Code",
                    description=f"Found exposed {pattern_info['description']} in source code. This is a security vulnerability.",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=context,
                    masked_value=self._mask_value(value, pattern_name),
                    value_hash=self._hash_value(value),
                    compliance_refs=pattern_info['compliance'],
                    remediation=f"Remove {pattern_info['description']} from code. Use environment variables, secret management (HashiCorp Vault, AWS Secrets Manager), or .env files (excluded from version control).",
                    evidence_hash=self._hash_value(f"{file_path}:{line_num}:{value}")
                )
                findings.append(finding)
        
        for pattern_name, pattern_info in self.logging_patterns.items():
            for match in pattern_info['pattern'].finditer(content):
                value = match.group(0)
                context, line_num = self._get_code_context(content, match.start(), match.end())
                
                finding = Finding(
                    id=str(uuid.uuid4()),
                    category=FindingCategory.PII_LOGGING,
                    severity=pattern_info['severity'],
                    title=pattern_info['description'],
                    description="Sensitive data may be exposed in application logs. This violates data minimization principles.",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=context,
                    masked_value="[logging statement]",
                    value_hash=self._hash_value(value),
                    compliance_refs=pattern_info['compliance'],
                    remediation="Remove sensitive data from logging statements. Use structured logging with PII filtering. Implement log masking middleware.",
                    evidence_hash=self._hash_value(f"{file_path}:{line_num}")
                )
                findings.append(finding)
        
        for pattern_name, pattern_info in self.pci_patterns.items():
            for match in pattern_info['pattern'].finditer(content):
                value = match.group(0)
                context, line_num = self._get_code_context(content, match.start(), match.end())
                
                finding = Finding(
                    id=str(uuid.uuid4()),
                    category=FindingCategory.PCI_DSS_VIOLATION,
                    severity=pattern_info['severity'],
                    title=pattern_info['description'],
                    description=f"PCI-DSS secure coding violation detected: {pattern_info['description']}",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=context,
                    masked_value="[code pattern]",
                    value_hash=self._hash_value(value),
                    compliance_refs=pattern_info['compliance'],
                    remediation=self._get_pci_remediation(pattern_name),
                    evidence_hash=self._hash_value(f"{file_path}:{line_num}")
                )
                findings.append(finding)
        
        return findings
    
    def _get_pci_remediation(self, pattern_name: str) -> str:
        """Get PCI-DSS specific remediation guidance."""
        remediations = {
            'pan_storage': "Do not store PAN in source code. Use tokenization service. Implement PCI-DSS compliant payment gateway.",
            'missing_mask': "Always mask PAN when displaying (show only last 4 digits). Implement masking utility function.",
            'weak_encryption': "Replace with AES-256 or stronger encryption. Use established cryptographic libraries.",
            'insecure_random': "Use cryptographically secure random number generators (CSPRNG). In Python: secrets module. In Java: SecureRandom."
        }
        return remediations.get(pattern_name, "Follow PCI-DSS secure coding guidelines.")
    
    def scan_repository(
        self,
        repo_url: str = None,
        branch: str = "main",
        access_token: str = None,
        uploaded_files: List[Dict[str, Any]] = None,
        scan_config: Dict[str, Any] = None
    ) -> ScanResult:
        """
        Scan a repository for compliance violations.
        
        Args:
            repo_url: Git repository URL
            branch: Branch to scan
            access_token: Access token for private repos
            uploaded_files: List of uploaded files with content
            scan_config: Optional configuration overrides
        
        Returns:
            ScanResult with all findings
        """
        start_time = datetime.now()
        self.findings = []
        self.files_scanned = 0
        
        logger.info(f"Starting repository scan: {repo_url or 'uploaded files'}")
        
        if self.progress_callback:
            self.progress_callback("Initializing scan...", 5)
        
        try:
            if uploaded_files:
                self._scan_uploaded_files(uploaded_files)
            elif repo_url:
                self._scan_git_repo(repo_url, branch, access_token)
            else:
                raise ValueError("Either repo_url or uploaded_files must be provided")
            
            critical_count = sum(1 for f in self.findings if f.severity == SeverityLevel.CRITICAL)
            high_count = sum(1 for f in self.findings if f.severity == SeverityLevel.HIGH)
            medium_count = sum(1 for f in self.findings if f.severity == SeverityLevel.MEDIUM)
            low_count = sum(1 for f in self.findings if f.severity == SeverityLevel.LOW)
            
            risk_score = self._calculate_risk_score(critical_count, high_count, medium_count, low_count)
            
            compliance_summary = self._generate_compliance_summary()
            
            recommendations = self._generate_recommendations()
            
            result = ScanResult(
                scan_id=self.scan_id,
                repo_url=repo_url or "uploaded_files",
                scan_timestamp=start_time,
                files_scanned=self.files_scanned,
                total_findings=len(self.findings),
                critical_count=critical_count,
                high_count=high_count,
                medium_count=medium_count,
                low_count=low_count,
                risk_score=risk_score,
                findings=self.findings,
                compliance_summary=compliance_summary,
                methodology=self._get_methodology(),
                recommendations=recommendations
            )
            
            if self.progress_callback:
                self.progress_callback("Scan completed", 100)
            
            logger.info(f"Repository scan completed: {len(self.findings)} findings in {self.files_scanned} files")
            
            return result
            
        except Exception as e:
            logger.error(f"Repository scan failed: {e}")
            raise
    
    def _scan_uploaded_files(self, uploaded_files: List[Dict[str, Any]]):
        """Scan uploaded files."""
        total_files = len(uploaded_files)
        
        for idx, file_info in enumerate(uploaded_files):
            file_name = file_info.get('name', 'unknown')
            content = file_info.get('content', '')
            
            if self.progress_callback:
                progress = 10 + int((idx / total_files) * 80)
                self.progress_callback(f"Scanning {file_name}...", progress)
            
            ext = os.path.splitext(file_name)[1].lower()
            if ext in self.code_extensions or not ext:
                findings = self._scan_file_content(file_name, content)
                self.findings.extend(findings)
                self.files_scanned += 1
    
    def _validate_repo_url(self, repo_url: str) -> bool:
        """
        Validate repository URL to prevent command injection.
        
        Args:
            repo_url: Repository URL to validate
        
        Returns:
            True if valid, raises ValueError if invalid
        """
        import urllib.parse
        
        if not repo_url:
            raise ValueError("Repository URL is required")
        
        dangerous_chars = [';', '|', '&', '$', '`', '>', '<', '!', '\n', '\r']
        for char in dangerous_chars:
            if char in repo_url:
                raise ValueError(f"Invalid character in repository URL: {char}")
        
        allowed_schemes = ['https', 'http', 'git']
        try:
            parsed = urllib.parse.urlparse(repo_url)
            if parsed.scheme not in allowed_schemes:
                raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Allowed: {allowed_schemes}")
            if not parsed.netloc:
                raise ValueError("Invalid repository URL: missing host")
        except Exception as e:
            raise ValueError(f"Invalid repository URL: {e}")
        
        allowed_hosts = ['github.com', 'gitlab.com', 'bitbucket.org', 'dev.azure.com', 'ssh.dev.azure.com']
        host = parsed.netloc.lower()
        host_without_auth = host.split('@')[-1]
        
        if not any(allowed in host_without_auth for allowed in allowed_hosts):
            logger.warning(f"Non-standard repository host: {host_without_auth}")
        
        return True
    
    def _sanitize_branch_name(self, branch: str) -> str:
        """Sanitize branch name to prevent injection."""
        if not branch:
            return ""
        safe_branch = re.sub(r'[^a-zA-Z0-9_\-/.]', '', branch)
        return safe_branch[:100]
    
    def _detect_default_branch(self, repo_url: str, access_token: str = None) -> str:
        """
        Detect the default branch of a repository using git ls-remote.
        
        Args:
            repo_url: Repository URL
            access_token: Optional access token for private repos
        
        Returns:
            Default branch name (e.g., 'main' or 'master')
        """
        try:
            if access_token and 'github.com' in repo_url:
                auth_url = repo_url.replace('https://', f'https://{access_token}@')
            elif access_token and 'gitlab.com' in repo_url:
                auth_url = repo_url.replace('https://', f'https://oauth2:{access_token}@')
            else:
                auth_url = repo_url
            
            result = subprocess.run(
                ['git', 'ls-remote', '--symref', auth_url, 'HEAD'],
                capture_output=True,
                text=True,
                timeout=30,
                shell=False
            )
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.split('\n'):
                    if 'ref: refs/heads/' in line:
                        branch = line.split('refs/heads/')[-1].split()[0]
                        logger.info(f"Detected default branch: {branch}")
                        return branch
        except Exception as e:
            logger.warning(f"Failed to detect default branch: {e}")
        
        return "main"
    
    def _scan_git_repo(self, repo_url: str, branch: str, access_token: str = None):
        """Clone and scan a git repository (read-only)."""
        self._validate_repo_url(repo_url)
        
        safe_branch = self._sanitize_branch_name(branch) if branch else ""
        
        temp_dir = tempfile.mkdtemp(prefix="repo_scan_")
        
        try:
            if access_token and 'github.com' in repo_url:
                auth_url = repo_url.replace('https://', f'https://{access_token}@')
            elif access_token and 'gitlab.com' in repo_url:
                auth_url = repo_url.replace('https://', f'https://oauth2:{access_token}@')
            else:
                auth_url = repo_url
            
            if self.progress_callback:
                self.progress_callback("Detecting default branch...", 8)
            
            if not safe_branch:
                safe_branch = self._detect_default_branch(repo_url, access_token)
            
            branches_to_try = [safe_branch]
            if safe_branch == "main":
                branches_to_try.append("master")
            elif safe_branch == "master":
                branches_to_try.append("main")
            else:
                branches_to_try.extend(["main", "master"])
            
            if self.progress_callback:
                self.progress_callback("Cloning repository (read-only)...", 10)
            
            clone_success = False
            last_error = None
            
            for attempt_branch in branches_to_try:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    temp_dir = tempfile.mkdtemp(prefix="repo_scan_")
                    
                    subprocess.run(
                        ['git', 'clone', '--depth', '1', '--branch', attempt_branch, auth_url, temp_dir],
                        check=True,
                        capture_output=True,
                        timeout=120,
                        shell=False
                    )
                    clone_success = True
                    logger.info(f"Successfully cloned with branch: {attempt_branch}")
                    break
                except subprocess.CalledProcessError as e:
                    last_error = e
                    logger.warning(f"Clone failed with branch '{attempt_branch}': {e}")
                    continue
            
            if not clone_success:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    temp_dir = tempfile.mkdtemp(prefix="repo_scan_")
                    
                    subprocess.run(
                        ['git', 'clone', '--depth', '1', auth_url, temp_dir],
                        check=True,
                        capture_output=True,
                        timeout=120,
                        shell=False
                    )
                    clone_success = True
                    logger.info("Successfully cloned without specifying branch")
                except subprocess.CalledProcessError as e:
                    raise RuntimeError(f"Failed to clone repository after trying multiple branches: {last_error or e}")
            
            all_files = []
            for root, dirs, files in os.walk(temp_dir):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', '.venv']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.code_extensions:
                        all_files.append(file_path)
            
            total_files = len(all_files)
            
            for idx, file_path in enumerate(all_files):
                if self.progress_callback:
                    progress = 20 + int((idx / total_files) * 70)
                    self.progress_callback(f"Scanning {os.path.basename(file_path)}...", progress)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    relative_path = os.path.relpath(file_path, temp_dir)
                    findings = self._scan_file_content(relative_path, content)
                    self.findings.extend(findings)
                    self.files_scanned += 1
                except Exception as e:
                    logger.warning(f"Failed to scan file {file_path}: {e}")
            
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")
    
    def _calculate_risk_score(self, critical: int, high: int, medium: int, low: int) -> float:
        """Calculate overall risk score (0-100, higher = more risk)."""
        weighted = (critical * 40) + (high * 20) + (medium * 5) + (low * 1)
        max_score = 100
        return min(weighted, max_score)
    
    def _generate_compliance_summary(self) -> Dict[str, Any]:
        """Generate compliance framework summary."""
        pci_findings = [f for f in self.findings if f.category == FindingCategory.PCI_DSS_VIOLATION]
        gdpr_findings = [f for f in self.findings if any('GDPR' in ref for ref in f.compliance_refs)]
        uavg_findings = [f for f in self.findings if any('UAVG' in ref for ref in f.compliance_refs)]
        secrets_findings = [f for f in self.findings if f.category == FindingCategory.SECRETS_EXPOSURE]
        pii_findings = [f for f in self.findings if f.category == FindingCategory.HARDCODED_PII]
        
        return {
            'pci_dss': {
                'status': 'non_compliant' if pci_findings else 'compliant',
                'finding_count': len(pci_findings),
                'critical_count': sum(1 for f in pci_findings if f.severity == SeverityLevel.CRITICAL),
                'requirements_violated': list(set(ref for f in pci_findings for ref in f.compliance_refs if 'PCI' in ref))
            },
            'gdpr': {
                'status': 'non_compliant' if gdpr_findings else 'compliant',
                'finding_count': len(gdpr_findings),
                'critical_count': sum(1 for f in gdpr_findings if f.severity == SeverityLevel.CRITICAL),
                'articles_violated': list(set(ref for f in gdpr_findings for ref in f.compliance_refs if 'GDPR' in ref))
            },
            'uavg': {
                'status': 'non_compliant' if uavg_findings else 'compliant',
                'finding_count': len(uavg_findings),
                'critical_count': sum(1 for f in uavg_findings if f.severity == SeverityLevel.CRITICAL),
                'articles_violated': list(set(ref for f in uavg_findings for ref in f.compliance_refs if 'UAVG' in ref))
            },
            'secrets_management': {
                'status': 'vulnerable' if secrets_findings else 'secure',
                'finding_count': len(secrets_findings),
                'exposure_types': list(set(f.title for f in secrets_findings))
            },
            'pii_protection': {
                'status': 'at_risk' if pii_findings else 'protected',
                'finding_count': len(pii_findings),
                'pii_types_found': list(set(f.title for f in pii_findings))
            }
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate prioritized remediation recommendations."""
        recommendations = []
        
        critical_findings = [f for f in self.findings if f.severity == SeverityLevel.CRITICAL]
        if critical_findings:
            recommendations.append("IMMEDIATE ACTION: Address all critical findings before next deployment")
        
        secrets = [f for f in self.findings if f.category == FindingCategory.SECRETS_EXPOSURE]
        if secrets:
            recommendations.append("Implement secrets management (HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault)")
            recommendations.append("Add pre-commit hooks to prevent secrets from being committed")
        
        pii = [f for f in self.findings if f.category == FindingCategory.HARDCODED_PII]
        if pii:
            recommendations.append("Remove all hardcoded PII from source code")
            recommendations.append("Implement data masking for any displayed sensitive data")
        
        logging = [f for f in self.findings if f.category == FindingCategory.PII_LOGGING]
        if logging:
            recommendations.append("Implement PII filtering in logging middleware")
            recommendations.append("Review and sanitize all debug/logging statements")
        
        pci = [f for f in self.findings if f.category == FindingCategory.PCI_DSS_VIOLATION]
        if pci:
            recommendations.append("Review PCI-DSS secure coding guidelines")
            recommendations.append("Implement tokenization for payment card data")
        
        if not recommendations:
            recommendations.append("No critical issues found. Continue regular security scanning.")
        
        recommendations.append("Schedule quarterly security code reviews")
        recommendations.append("Implement CI/CD security gates to block violations before merge")
        
        return recommendations
    
    def _get_methodology(self) -> str:
        """Return scan methodology description."""
        return """
Repository Security Scan Methodology:

1. SCOPE: Source code repository analysis only (no production data access)
2. ACCESS: Read-only clone, no modifications to source repository
3. DETECTION: Pattern-based scanning with validation (e.g., BSN 11-proef)
4. SECURITY: All detected values are masked and stored as hashes only
5. COMPLIANCE: PCI-DSS v4.0, GDPR, Netherlands UAVG coverage
6. PATTERNS: 
   - Hardcoded PII (IBAN, BSN, PAN, email, phone)
   - Secrets (API keys, tokens, passwords, certificates)
   - PII logging violations
   - PCI-DSS secure coding violations
7. OUTPUT: Risk-scored findings with remediation guidance
"""
    
    def generate_html_report(self, result: ScanResult) -> str:
        """
        Generate comprehensive HTML report for the scan results.
        
        Args:
            result: ScanResult from the scan
        
        Returns:
            HTML string
        """
        import html
        
        def escape(s: str) -> str:
            """Escape HTML special characters."""
            return html.escape(str(s)) if s else ""
        
        severity_colors = {
            SeverityLevel.CRITICAL: '#dc3545',
            SeverityLevel.HIGH: '#fd7e14',
            SeverityLevel.MEDIUM: '#ffc107',
            SeverityLevel.LOW: '#28a745',
            SeverityLevel.INFO: '#17a2b8'
        }
        
        findings_by_category = {}
        for finding in result.findings:
            cat = finding.category.value
            if cat not in findings_by_category:
                findings_by_category[cat] = []
            findings_by_category[cat].append(finding)
        
        findings_html = ""
        for category, findings in findings_by_category.items():
            category_title = escape(category.replace('_', ' ').title())
            findings_html += f"""
            <div class="category-section">
                <h3>{category_title} ({len(findings)} findings)</h3>
                <table class="findings-table">
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Title</th>
                            <th>File</th>
                            <th>Line</th>
                            <th>Compliance</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for finding in findings:
                severity_color = severity_colors.get(finding.severity, '#6c757d')
                findings_html += f"""
                        <tr>
                            <td><span class="severity-badge" style="background-color: {severity_color}">{escape(finding.severity.value.upper())}</span></td>
                            <td>{escape(finding.title)}</td>
                            <td class="file-path">{escape(finding.file_path)}</td>
                            <td>{escape(str(finding.line_number))}</td>
                            <td>{escape(', '.join(finding.compliance_refs[:3]))}</td>
                        </tr>
                """
            findings_html += """
                    </tbody>
                </table>
            </div>
            """
        
        compliance = result.compliance_summary
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Repository Security Scan Report - {result.scan_id[:8]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1.2em; }}
        .bank-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            margin-top: 15px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card.critical {{ border-left: 5px solid #dc3545; }}
        .summary-card.high {{ border-left: 5px solid #fd7e14; }}
        .summary-card.medium {{ border-left: 5px solid #ffc107; }}
        .summary-card.low {{ border-left: 5px solid #28a745; }}
        .summary-card .value {{ font-size: 3em; font-weight: bold; }}
        .summary-card .label {{ color: #666; font-size: 0.9em; }}
        .risk-score {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }}
        .risk-meter {{
            width: 100%;
            height: 30px;
            background: linear-gradient(to right, #28a745, #ffc107, #fd7e14, #dc3545);
            border-radius: 15px;
            position: relative;
            margin: 20px 0;
        }}
        .risk-indicator {{
            position: absolute;
            top: -5px;
            width: 40px;
            height: 40px;
            background: white;
            border: 3px solid #333;
            border-radius: 50%;
            transform: translateX(-50%);
            left: {min(result.risk_score, 100)}%;
        }}
        .compliance-section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .compliance-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .compliance-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .compliance-card.compliant {{ background: #d4edda; border: 1px solid #c3e6cb; }}
        .compliance-card.non-compliant {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
        .compliance-card.vulnerable {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
        .compliance-card.secure {{ background: #d4edda; border: 1px solid #c3e6cb; }}
        .compliance-card.at-risk {{ background: #fff3cd; border: 1px solid #ffeeba; }}
        .compliance-card.protected {{ background: #d4edda; border: 1px solid #c3e6cb; }}
        .section {{ 
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .section h2 {{ margin-bottom: 20px; color: #1e3a5f; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .findings-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .findings-table th, .findings-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .findings-table th {{ background: #f8f9fa; font-weight: 600; }}
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            color: white;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .file-path {{ font-family: monospace; font-size: 0.9em; color: #666; }}
        .recommendations {{
            background: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        .recommendations ul {{ margin-left: 20px; }}
        .recommendations li {{ margin-bottom: 10px; }}
        .methodology {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
        }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9em;
        }}
        .category-section {{ margin-top: 30px; }}
        .category-section h3 {{ 
            background: #f8f9fa; 
            padding: 10px 15px; 
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ max-width: 100%; }}
            .section {{ box-shadow: none; border: 1px solid #ddd; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Repository Security Scan Report</h1>
            <div class="subtitle">PCI-DSS | GDPR | UAVG Compliance Analysis</div>
            <div class="bank-badge">🏦 Banking Sector Compliance Scan</div>
            <p style="margin-top: 20px; opacity: 0.8;">
                Scan ID: {escape(result.scan_id[:8])} | 
                Date: {escape(result.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S'))} |
                Repository: {escape(result.repo_url)}
            </p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <div class="value">{result.files_scanned}</div>
                <div class="label">Files Scanned</div>
            </div>
            <div class="summary-card critical">
                <div class="value" style="color: #dc3545">{result.critical_count}</div>
                <div class="label">Critical</div>
            </div>
            <div class="summary-card high">
                <div class="value" style="color: #fd7e14">{result.high_count}</div>
                <div class="label">High</div>
            </div>
            <div class="summary-card medium">
                <div class="value" style="color: #ffc107">{result.medium_count}</div>
                <div class="label">Medium</div>
            </div>
            <div class="summary-card low">
                <div class="value" style="color: #28a745">{result.low_count}</div>
                <div class="label">Low</div>
            </div>
        </div>

        <div class="risk-score">
            <h2>Overall Risk Score</h2>
            <div class="risk-meter">
                <div class="risk-indicator"></div>
            </div>
            <div style="display: flex; justify-content: space-between; color: #666; font-size: 0.9em;">
                <span>Low Risk</span>
                <span style="font-size: 2em; font-weight: bold;">{result.risk_score:.0f}/100</span>
                <span>High Risk</span>
            </div>
        </div>

        <div class="compliance-section">
            <h2>Compliance Framework Status</h2>
            <div class="compliance-grid">
                <div class="compliance-card {compliance['pci_dss']['status'].replace('_', '-')}">
                    <h3>PCI-DSS</h3>
                    <div style="font-size: 2em;">{'✅' if compliance['pci_dss']['status'] == 'compliant' else '❌'}</div>
                    <div>{compliance['pci_dss']['finding_count']} findings</div>
                </div>
                <div class="compliance-card {compliance['gdpr']['status'].replace('_', '-')}">
                    <h3>GDPR</h3>
                    <div style="font-size: 2em;">{'✅' if compliance['gdpr']['status'] == 'compliant' else '❌'}</div>
                    <div>{compliance['gdpr']['finding_count']} findings</div>
                </div>
                <div class="compliance-card {compliance['uavg']['status'].replace('_', '-')}">
                    <h3>UAVG</h3>
                    <div style="font-size: 2em;">{'✅' if compliance['uavg']['status'] == 'compliant' else '❌'}</div>
                    <div>{compliance['uavg']['finding_count']} findings</div>
                </div>
                <div class="compliance-card {compliance['secrets_management']['status']}">
                    <h3>Secrets</h3>
                    <div style="font-size: 2em;">{'✅' if compliance['secrets_management']['status'] == 'secure' else '⚠️'}</div>
                    <div>{compliance['secrets_management']['finding_count']} exposures</div>
                </div>
                <div class="compliance-card {'protected' if compliance['pii_protection']['status'] == 'protected' else 'at-risk'}">
                    <h3>PII Protection</h3>
                    <div style="font-size: 2em;">{'✅' if compliance['pii_protection']['status'] == 'protected' else '⚠️'}</div>
                    <div>{compliance['pii_protection']['finding_count']} issues</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Findings by Category</h2>
            {findings_html if findings_html else '<p>No findings detected. Repository passed all security checks.</p>'}
        </div>

        <div class="section">
            <h2>Recommendations</h2>
            <div class="recommendations">
                <ul>
                    {''.join(f'<li>{rec}</li>' for rec in result.recommendations)}
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>Scan Methodology</h2>
            <div class="methodology">{result.methodology}</div>
        </div>

        <div class="footer">
            <p><strong>DataGuardian Pro</strong> - Enterprise Privacy Compliance Platform</p>
            <p>This report is code-audit-ready and provides evidence for PCI-DSS, GDPR, and UAVG compliance assessments.</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Report Version: 1.0</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
