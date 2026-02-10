"""
API Scanner module for comprehensive privacy compliance and security scanning of REST APIs.

This module analyzes API endpoints for PII exposure, authentication vulnerabilities,
data leakage, GDPR compliance issues, and provides detailed security recommendations.
"""

import os
import re
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, local

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("api_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
import requests
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin, parse_qs
import yaml
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class APIScanner:
    """
    A comprehensive scanner that analyzes REST APIs for privacy compliance issues,
    security vulnerabilities, PII exposure, and GDPR compliance requirements.
    """
    
    def __init__(self, max_endpoints=50, request_timeout=10, rate_limit_delay=0.1, 
                 follow_redirects=True, verify_ssl=True, region="Netherlands", 
                 batch_size=5, max_workers=3):
        """
        Initialize the API scanner.
        
        Args:
            max_endpoints: Maximum number of endpoints to scan (default: 50)
            request_timeout: Timeout for API requests in seconds (default: 10)
            rate_limit_delay: Delay between requests to respect rate limits (default: 0.1)
            follow_redirects: Whether to follow HTTP redirects (default: True)
            verify_ssl: Whether to verify SSL certificates (default: True)
            region: Region for applying GDPR rules (default: "Netherlands")
        """
        self.max_endpoints = max_endpoints
        self.request_timeout = request_timeout
        self.rate_limit_delay = rate_limit_delay
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl
        self.region = region
        self.progress_callback = None
        self.is_running = False
        self.start_time = None
        self._rate_limit_detected = False
        self._rate_limit_retries = 0
        self.batch_size = batch_size
        self.max_workers = max_workers
        self._stats_lock = Lock()  # Thread-safe statistics
        self._shared_data_lock = Lock()  # Lock for all shared data structures
        self._checkpoint_enabled = True
        self._checkpoint_interval = 5  # Save checkpoint every 5 scanned endpoints
        
        # Initialize thread-local storage for sessions
        self._local = local()
        self._session_headers = {
            'User-Agent': 'DataGuardian-API-Scanner/1.0 (Privacy Compliance Scanner)',
            'Accept': 'application/json, application/xml, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        # Load PII detection patterns
        self._load_pii_patterns()
        
        # Load common API vulnerabilities database
        self._load_vulnerability_patterns()
        
        # Load authentication methods database
        self._load_auth_methods()
        
        # Load AI Act 2025 compliance patterns
        self._load_ai_act_patterns()
        
        # Load Netherlands UAVG specific rules
        self._load_netherlands_compliance_rules()
    
    def _get_session(self):
        """Get or create a thread-local requests session for thread safety."""
        if not hasattr(self._local, 'session'):
            self._local.session = requests.Session()
            self._local.session.headers.update(self._session_headers)
            
            # Apply global session configuration - timeout is handled per-request
            # Note: Session object doesn't have timeout attribute, use it in request calls
            if hasattr(self, 'verify_ssl'):
                self._local.session.verify = self.verify_ssl
        
        return self._local.session
    
    def _get_user_scope(self):
        """Get user scope for checkpoint keys - ensures user isolation"""
        try:
            import streamlit as st
            # Try to get session ID or user ID from Streamlit
            if hasattr(st, 'session_state'):
                # Create a consistent user scope from session
                session_info = getattr(st.session_state, '_session_info', None)
                if session_info:
                    return f"user_{hash(str(session_info)) % 1000000}"
                # Fallback: create scope from session state hash
                session_hash = hash(str(id(st.session_state))) % 1000000
                return f"session_{session_hash}"
        except (ImportError, AttributeError):
            pass
        
        # Fallback to thread ID for isolation
        import threading
        thread_id = threading.current_thread().ident
        # Ensure thread_id is not None before using modulo
        if thread_id is not None:
            return f"thread_{thread_id % 1000000}"
        else:
            # Ultimate fallback if thread ID is None
            import os
            return f"process_{os.getpid() % 1000000}"
    
    def _load_pii_patterns(self):
        """Load PII detection patterns for API response analysis."""
        self.pii_patterns = {
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'description': 'Email addresses detected in API response',
                'severity': 'High',
                'gdpr_category': 'Personal Data'
            },
            'phone': {
                'pattern': r'(\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                'description': 'Phone numbers detected in API response',
                'severity': 'High',
                'gdpr_category': 'Personal Data'
            },
            'ssn': {
                'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
                'description': 'US Social Security Numbers detected',
                'severity': 'Critical',
                'gdpr_category': 'Special Category Data'
            },
            'credit_card': {
                'pattern': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                'description': 'Credit card numbers detected',
                'severity': 'Critical',
                'gdpr_category': 'Financial Data'
            },
            'ip_address': {
                'pattern': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                'description': 'IP addresses detected',
                'severity': 'Medium',
                'gdpr_category': 'Technical Data'
            },
            'api_key': {
                'pattern': r'[Aa][Pp][Ii][-_]?[Kk][Ee][Yy]\s*[:=]\s*["\']?([A-Za-z0-9\-_]{20,})["\']?',
                'description': 'API keys exposed in response',
                'severity': 'Critical',
                'gdpr_category': 'Security Credentials'
            },
            'password': {
                'pattern': r'[Pp]assword\s*[:=]\s*["\']?([^"\'\s]{6,})["\']?',
                'description': 'Passwords exposed in response',
                'severity': 'Critical',
                'gdpr_category': 'Authentication Data'
            },
            'bsn': {
                'pattern': r'\b\d{9}\b|\b\d{3}[-.\s]\d{2}[-.\s]\d{3}\b',
                'description': 'Dutch BSN (Burgerservicenummer) detected',
                'severity': 'Critical',
                'gdpr_category': 'Netherlands UAVG Special Category',
                'netherlands_specific': True,
                'notification_required': True,
                'validation_required': True  # Needs 11-proef validation
            },
            'dutch_postal_code': {
                'pattern': r'\b\d{4}\s?[A-Z]{2}\b',
                'description': 'Dutch postal codes detected',
                'severity': 'Medium',
                'gdpr_category': 'Location Data',
                'netherlands_specific': True
            },
            'iban': {
                'pattern': r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b',
                'description': 'IBAN bank account numbers detected',
                'severity': 'High',
                'gdpr_category': 'Financial Data'
            }
        }
    
    def _load_vulnerability_patterns(self):
        """Load common API vulnerability patterns."""
        self.vulnerability_patterns = {
            'sql_injection': {
                'payloads': ["' OR '1'='1", "'; DROP TABLE users; --", "' UNION SELECT * FROM users --"],
                'indicators': ['mysql', 'postgresql', 'sql syntax', 'ora-', 'sqlite'],
                'description': 'SQL injection vulnerability detected',
                'severity': 'Critical'
            },
            'xss': {
                'payloads': ['<script>alert("xss")</script>', '"><script>alert(1)</script>', "javascript:alert('xss')"],
                'indicators': ['<script>', 'javascript:', 'onerror=', 'onload='],
                'description': 'Cross-site scripting vulnerability detected',
                'severity': 'High'
            },
            'path_traversal': {
                'payloads': ['../../../etc/passwd', '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts'],
                'indicators': ['/etc/passwd', 'root:x:', 'windows\\system32'],
                'description': 'Path traversal vulnerability detected',
                'severity': 'High'
            },
            'command_injection': {
                'payloads': ['; ls -la', '| whoami', '& dir'],
                'indicators': ['bin/', 'total ', 'drwx', 'administrator', 'system32'],
                'description': 'Command injection vulnerability detected',
                'severity': 'Critical'
            }
        }
    
    def _load_auth_methods(self):
        """Load authentication method analysis patterns."""
        self.auth_methods = {
            'bearer_token': {
                'header': 'Authorization',
                'pattern': r'Bearer\s+([A-Za-z0-9\-_\.]+)',
                'description': 'Bearer token authentication',
                'security_level': 'Medium'
            },
            'basic_auth': {
                'header': 'Authorization',
                'pattern': r'Basic\s+([A-Za-z0-9+/=]+)',
                'description': 'HTTP Basic authentication',
                'security_level': 'Low'
            },
            'api_key_header': {
                'header': 'X-API-Key',
                'pattern': r'([A-Za-z0-9\-_]{20,})',
                'description': 'API key in header',
                'security_level': 'Medium'
            },
            'jwt_token': {
                'header': 'Authorization',
                'pattern': r'Bearer\s+([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)',
                'description': 'JWT token authentication',
                'security_level': 'High'
            }
        }
    
    def _load_ai_act_patterns(self):
        """Load EU AI Act 2025 compliance patterns for API analysis."""
        self.ai_act_patterns = {
            'ai_endpoints': {
                'patterns': [
                    r'/ai/', r'/artificial[-_]intelligence/', r'/machine[-_]learning/',
                    r'/ml/', r'/neural/', r'/prediction/', r'/classification/',
                    r'/recommendation/', r'/sentiment/', r'/nlp/', r'/cv/',
                    r'/facial[-_]recognition/', r'/biometric/', r'/automated[-_]decision/'
                ],
                'description': 'AI system endpoints detected',
                'severity': 'High',
                'ai_act_category': 'AI System',
                'compliance_required': True
            },
            'high_risk_ai': {
                'patterns': [
                    r'/credit[-_]scoring/', r'/loan[-_]approval/', r'/hiring/',
                    r'/recruitment/', r'/facial[-_]recognition/', r'/emotion[-_]detection/',
                    r'/biometric/', r'/surveillance/', r'/law[-_]enforcement/'
                ],
                'description': 'High-risk AI system detected',
                'severity': 'Critical',
                'ai_act_category': 'High-Risk AI System',
                'transparency_required': True,
                'human_oversight_required': True
            },
            'prohibited_ai': {
                'patterns': [
                    r'/social[-_]scoring/', r'/subliminal/', r'/manipulation/',
                    r'/exploit[-_]vulnerabilities/', r'/mass[-_]surveillance/'
                ],
                'description': 'Potentially prohibited AI practice detected',
                'severity': 'Critical',
                'ai_act_category': 'Prohibited AI Practice',
                'immediate_review_required': True
            }
        }
    
    def _load_netherlands_compliance_rules(self):
        """Load Netherlands UAVG specific compliance rules."""
        self.netherlands_rules = {
            'ap_notification_triggers': {
                'bsn_detection': {
                    'threshold': 1,  # Any BSN detection triggers notification
                    'description': 'BSN detection requires AP notification',
                    'authority': 'Autoriteit Persoonsgegevens (AP)',
                    'notification_period': '72 hours',
                    'severity': 'Critical'
                },
                'data_breach_indicators': {
                    'patterns': [
                        r'unauthorized_access', r'data_leak', r'security_breach',
                        r'privacy_violation', r'gdpr_breach'
                    ],
                    'description': 'Potential data breach indicators',
                    'notification_required': True
                }
            },
            'dutch_specific_pii': {
                'description': 'Netherlands-specific PII categories requiring special protection',
                'categories': [
                    'BSN (Burgerservicenummer)',
                    'Dutch postal codes with house numbers',
                    'Dutch bank account numbers (IBAN)',
                    'Dutch passport/ID numbers'
                ]
            },
            'uavg_rights': {
                'data_subject_rights': [
                    'right_to_access', 'right_to_rectification', 
                    'right_to_erasure', 'right_to_portability',
                    'right_to_object', 'right_to_restrict_processing'
                ],
                'description': 'UAVG data subject rights implementation required'
            }
        }
    
    def set_progress_callback(self, callback_function):
        """
        Set a callback function for progress updates during API scanning.
        
        Args:
            callback_function: A function that takes current, total, and current endpoint
        """
        self.progress_callback = callback_function
    
    def scan_api(self, base_url: str, auth_token: Optional[str] = None, openapi_spec: Optional[str] = None, 
                 endpoints: Optional[List[str]] = None, resume_scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform a comprehensive scan of an API.
        
        Args:
            base_url: The base URL of the API to scan
            auth_token: Authentication token (optional)
            openapi_spec: OpenAPI/Swagger specification URL or content (optional)
            endpoints: List of specific endpoints to scan (optional)
            
        Returns:
            Dictionary with comprehensive scan results
        """
        self.start_time = datetime.now()
        self.is_running = True
        
        # Generate or use existing scan ID for resume functionality
        if resume_scan_id:
            scan_id = resume_scan_id
            logger.info(f"Resuming scan with ID: {scan_id}")
        else:
            scan_id = hashlib.md5(f"{base_url}:{self.start_time.isoformat()}".encode()).hexdigest()[:10]
            logger.info(f"Starting new scan with ID: {scan_id}")
        
        # Parse and normalize the base URL
        parsed_url = urlparse(base_url)
        if not parsed_url.scheme:
            base_url = f"https://{base_url}"
            parsed_url = urlparse(base_url)
        
        base_domain = parsed_url.netloc
        
        # Initialize or resume scan data structures
        checkpoint_data = self._load_checkpoint(scan_id) if resume_scan_id else None
        
        if checkpoint_data:
            # Resume from checkpoint
            scanned_endpoints = checkpoint_data.get('scanned_endpoints', [])
            findings = checkpoint_data.get('findings', [])
            vulnerabilities = checkpoint_data.get('vulnerabilities', [])
            pii_exposures = checkpoint_data.get('pii_exposures', [])
            auth_issues = checkpoint_data.get('auth_issues', [])
            completed_endpoints = set(checkpoint_data.get('completed_endpoints', []))
            logger.info(f"Resumed from checkpoint: {len(scanned_endpoints)} endpoints already completed")
        else:
            # Initialize fresh scan data structures
            scanned_endpoints = []
            findings = []
            vulnerabilities = []
            pii_exposures = []
            auth_issues = []
            completed_endpoints = set()
        
        # Set up authentication if provided (stored for thread-local sessions)
        if auth_token:
            if auth_token.startswith('Bearer '):
                self._session_headers['Authorization'] = auth_token
            else:
                self._session_headers['Authorization'] = f'Bearer {auth_token}'
        
        # Discover endpoints
        if openapi_spec:
            discovered_endpoints = self._parse_openapi_spec(openapi_spec, base_url)
        elif endpoints:
            discovered_endpoints = [urljoin(base_url, ep) for ep in endpoints]
        else:
            discovered_endpoints = self._discover_endpoints(base_url)
        
        # Limit the number of endpoints to scan
        discovered_endpoints = discovered_endpoints[:self.max_endpoints]
        
        # Report initial progress
        if self.progress_callback:
            self.progress_callback(0, len(discovered_endpoints), f"Starting API scan of {base_domain}")
        
        # Filter out already completed endpoints for resume functionality
        if resume_scan_id and completed_endpoints:
            remaining_endpoints = [ep for ep in discovered_endpoints if ep not in completed_endpoints]
            logger.info(f"Resume: Skipping {len(completed_endpoints)} already completed endpoints, "
                       f"scanning {len(remaining_endpoints)} remaining")
            discovered_endpoints = remaining_endpoints

        # Scan endpoints with batch processing
        self._batch_scan_endpoints(discovered_endpoints, base_url, scanned_endpoints, 
                                 findings, vulnerabilities, pii_exposures, auth_issues, 
                                 scan_id, completed_endpoints)
        
        # Perform additional security checks
        ssl_info = self._check_ssl_security(base_url)
        cors_analysis = self._analyze_cors_policy(base_url)
        rate_limiting = self._check_rate_limiting(base_url)
        
        # Calculate completion time
        completion_time = datetime.now()
        duration_seconds = (completion_time - self.start_time).total_seconds()
        
        # Generate comprehensive scan results
        scan_results = {
            'scan_id': scan_id,
            'scan_type': 'api',  # Set proper scanner type for dashboard display
            'scan_time': self.start_time.isoformat(),
            'completion_time': completion_time.isoformat(),
            'duration_seconds': duration_seconds,
            'base_url': base_url,
            'base_domain': base_domain,
            'endpoints_scanned': len(scanned_endpoints),
            'endpoints_data': scanned_endpoints,
            'findings': findings,
            'vulnerabilities': vulnerabilities,
            'pii_exposures': pii_exposures,
            'auth_issues': auth_issues,
            'ssl_info': ssl_info,
            'cors_analysis': cors_analysis,
            'rate_limiting': rate_limiting,
            'stats': {
                'total_endpoints': len(discovered_endpoints),
                'successful_scans': len(scanned_endpoints),
                'total_findings': len(findings),
                'critical_findings': len([f for f in findings if f.get('severity') == 'Critical']),
                'high_findings': len([f for f in findings if f.get('severity') == 'High']),
                'medium_findings': len([f for f in findings if f.get('severity') == 'Medium']),
                'low_findings': len([f for f in findings if f.get('severity') == 'Low'])
            },
            'scan_type': 'api'
        }
        
        # Aggregate compliance findings into scan-level summaries
        self._aggregate_compliance_findings(scan_results)
        
        self.is_running = False
        return scan_results
    
    def _batch_scan_endpoints(self, discovered_endpoints, base_url, scanned_endpoints, 
                            findings, vulnerabilities, pii_exposures, auth_issues,
                            scan_id, completed_endpoints):
        """Scan endpoints using batch processing with concurrent execution and checkpoint support"""
        total_endpoints = len(discovered_endpoints)
        completed = 0
        
        # Process endpoints in batches
        for batch_start in range(0, total_endpoints, self.batch_size):
            if not self.is_running:
                break
                
            batch_end = min(batch_start + self.batch_size, total_endpoints)
            batch_endpoints = discovered_endpoints[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//self.batch_size + 1}: "
                       f"endpoints {batch_start + 1}-{batch_end} of {total_endpoints}")
            
            # Use ThreadPoolExecutor for concurrent scanning
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all endpoints in the batch
                future_to_endpoint = {
                    executor.submit(self._scan_endpoint_with_retry, endpoint_url, base_url): endpoint_url
                    for endpoint_url in batch_endpoints
                }
                
                # Process completed scans
                for future in as_completed(future_to_endpoint):
                    if not self.is_running:
                        break
                        
                    endpoint_url = future_to_endpoint[future]
                    completed += 1
                    
                    try:
                        endpoint_data = future.result()
                        
                        # Thread-safe operations - protect ALL shared data access
                        with self._shared_data_lock:
                            scanned_endpoints.append(endpoint_data)
                            
                            # Extract findings
                            endpoint_findings = endpoint_data.get('findings', [])
                            findings.extend(endpoint_findings)
                            
                            # Categorize findings
                            for finding in endpoint_findings:
                                if finding.get('type') == 'vulnerability':
                                    vulnerabilities.append(finding)
                                elif finding.get('type') == 'pii_exposure':
                                    pii_exposures.append(finding)
                                elif finding.get('type') == 'auth_issue':
                                    auth_issues.append(finding)
                            
                            # Mark endpoint as completed for resume functionality
                            completed_endpoints.add(endpoint_url)
                        
                        # Report progress (outside lock to avoid blocking)
                        if self.progress_callback:
                            self.progress_callback(completed, total_endpoints, 
                                                 f"Completed {endpoint_url}")
                        logger.debug(f"Successfully scanned {endpoint_url}")
                        
                        # Save checkpoint periodically
                        if self._checkpoint_enabled and completed % self._checkpoint_interval == 0:
                            self._save_checkpoint(scan_id, scanned_endpoints, findings, 
                                                vulnerabilities, pii_exposures, auth_issues, 
                                                completed_endpoints)
                        
                    except Exception as e:
                        logger.warning(f"Error scanning endpoint {endpoint_url}: {str(e)}")
                        continue
            
            # Small delay between batches to prevent overwhelming the server
            if batch_end < total_endpoints and self.is_running:
                time.sleep(0.5)
        
        # Save final checkpoint
        if self._checkpoint_enabled:
            self._save_checkpoint(scan_id, scanned_endpoints, findings, 
                                vulnerabilities, pii_exposures, auth_issues, 
                                completed_endpoints)
    
    def _scan_endpoint_with_retry(self, endpoint_url, base_url):
        """Scan individual endpoint with retry logic - thread-safe wrapper"""
        try:
            # Adaptive rate limiting per thread
            if self._rate_limit_detected:
                import random
                base_delay = self.rate_limit_delay
                exponential_delay = min(10.0, base_delay * (2 ** self._rate_limit_retries))
                jitter = random.uniform(0, 0.1 * exponential_delay)
                total_delay = exponential_delay + jitter
                time.sleep(total_delay)
            else:
                time.sleep(self.rate_limit_delay)  # Minimal delay (0.1s default)
            
            # Scan the endpoint
            endpoint_data = self._scan_endpoint(endpoint_url, base_url)
            
            # Check for rate limit response and adjust strategy
            if endpoint_data.get('status_code') == 429:
                if not self._rate_limit_detected:
                    self._rate_limit_detected = True
                    self._rate_limit_retries = 1
                else:
                    self._rate_limit_retries = min(5, self._rate_limit_retries + 1)
                logger.warning(f"Rate limiting detected on {endpoint_url}, retry #{self._rate_limit_retries}")
            elif endpoint_data.get('status_code') in [200, 201, 202]:
                # Reset rate limiting state on success
                self._rate_limit_detected = False
                self._rate_limit_retries = 0
            
            return endpoint_data
            
        except Exception as e:
            logger.error(f"Error in _scan_endpoint_with_retry for {endpoint_url}: {str(e)}")
            # Return a minimal error response
            return {
                'url': endpoint_url,
                'status_code': 0,
                'error': str(e) if e is not None else "Unknown error",
                'findings': []
            }
    
    def _save_checkpoint(self, scan_id: str, scanned_endpoints: list, findings: list,
                        vulnerabilities: list, pii_exposures: list, auth_issues: list,
                        completed_endpoints: set, user_id: str = None):
        """Save scan checkpoint for resume functionality with user scoping"""
        try:
            checkpoint_data = {
                'scan_id': scan_id,
                'timestamp': datetime.now().isoformat(),
                'scanned_endpoints': scanned_endpoints,
                'findings': findings,
                'vulnerabilities': vulnerabilities,
                'pii_exposures': pii_exposures,
                'auth_issues': auth_issues,
                'completed_endpoints': list(completed_endpoints),
                'total_completed': len(completed_endpoints)
            }
            
            # Create user-scoped checkpoint key to prevent unauthorized access
            user_scope = user_id or self._get_user_scope()
            checkpoint_key = f"api_scan_checkpoint_{user_scope}_{scan_id}"
            
            # Try to use Redis cache first, fallback to session state
            try:
                from utils.redis_cache import get_cache
                cache = get_cache()
                cache.set(checkpoint_key, checkpoint_data, ttl=86400)  # 24 hours
                logger.debug(f"Checkpoint saved to cache for scan {scan_id} (user: {user_scope})")
            except Exception as e:
                # Fallback to session state if available
                try:
                    import streamlit as st
                    if hasattr(st, 'session_state'):
                        st.session_state[f'checkpoint_{user_scope}_{scan_id}'] = checkpoint_data
                        logger.debug(f"Checkpoint saved to session for scan {scan_id} (user: {user_scope})")
                except:
                    logger.warning(f"Failed to save checkpoint for scan {scan_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error saving checkpoint for scan {scan_id}: {e}")
    
    def _load_checkpoint(self, scan_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Load scan checkpoint for resume functionality with user scoping"""
        try:
            # Create user-scoped checkpoint key to prevent unauthorized access
            user_scope = user_id or self._get_user_scope()
            checkpoint_key = f"api_scan_checkpoint_{user_scope}_{scan_id}"
            
            # Try Redis cache first
            try:
                from utils.redis_cache import get_cache
                cache = get_cache()
                checkpoint_data = cache.get(checkpoint_key)
                if checkpoint_data:
                    logger.info(f"Checkpoint loaded from cache for scan {scan_id} (user: {user_scope})")
                    return checkpoint_data
            except Exception as e:
                logger.debug(f"Cache checkpoint load failed: {e}")
            
            # Fallback to session state
            try:
                import streamlit as st
                if hasattr(st, 'session_state'):
                    checkpoint_data = st.session_state.get(f'checkpoint_{user_scope}_{scan_id}')
                    if checkpoint_data:
                        logger.info(f"Checkpoint loaded from session for scan {scan_id} (user: {user_scope})")
                        return checkpoint_data
            except:
                pass
            
            logger.info(f"No checkpoint found for scan {scan_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading checkpoint for scan {scan_id}: {e}")
            return None
    
    def get_available_checkpoints(self) -> List[Dict[str, str]]:
        """Get list of available scan checkpoints for resume"""
        checkpoints = []
        try:
            # Try Redis cache first
            try:
                from utils.redis_cache import get_cache
                cache = get_cache()
                # Note: This is a simplified approach - in production you'd want to 
                # maintain a separate index of checkpoints
                logger.debug("Checkpoint listing from cache not implemented (requires key scanning)")
            except Exception as e:
                logger.debug(f"Cache checkpoint listing failed: {e}")
            
            # Fallback to session state
            try:
                import streamlit as st
                if hasattr(st, 'session_state'):
                    for key, value in st.session_state.items():
                        # Ensure key is string before calling string methods
                        key_str = str(key) if key is not None else ""
                        if key_str.startswith('checkpoint_') and isinstance(value, dict):
                            checkpoints.append({
                                'scan_id': value.get('scan_id', key_str.replace('checkpoint_', '')),
                                'timestamp': value.get('timestamp', 'Unknown'),
                                'completed_endpoints': value.get('total_completed', 0)
                            })
            except:
                pass
            
        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}")
        
        return checkpoints
    
    def _discover_endpoints(self, base_url: str) -> List[str]:
        """
        Discover API endpoints through various methods.
        
        Args:
            base_url: The base URL to discover endpoints from
            
        Returns:
            List of discovered endpoint URLs
        """
        endpoints = set()
        
        # Common API endpoint patterns
        common_endpoints = [
            '/api/v1/users', '/api/v1/user', '/api/users', '/users',
            '/api/v1/auth', '/api/auth', '/auth', '/login',
            '/api/v1/data', '/api/data', '/data',
            '/api/v1/profile', '/api/profile', '/profile',
            '/api/v1/admin', '/api/admin', '/admin',
            '/api/v1/config', '/api/config', '/config',
            '/api/v1/health', '/api/health', '/health',
            '/api/v1/status', '/api/status', '/status',
            '/api/docs', '/docs', '/swagger', '/openapi.json'
        ]
        
        # Try common endpoints
        for endpoint in common_endpoints:
            full_url = urljoin(base_url, endpoint)
            endpoints.add(full_url)
        
        # Try to find OpenAPI/Swagger documentation
        doc_endpoints = ['/swagger.json', '/openapi.json', '/api-docs', '/docs']
        for doc_endpoint in doc_endpoints:
            try:
                response = self._get_session().get(urljoin(base_url, doc_endpoint), 
                                          timeout=self.request_timeout)
                if response.status_code == 200:
                    spec_endpoints = self._parse_openapi_spec(response.text, base_url)
                    endpoints.update(spec_endpoints)
                    break
            except:
                continue
        
        return list(endpoints)
    
    def _parse_openapi_spec(self, spec_content: str, base_url: str) -> List[str]:
        """
        Parse OpenAPI/Swagger specification to extract endpoints.
        
        Args:
            spec_content: OpenAPI specification content (JSON or YAML)
            base_url: Base URL for the API
            
        Returns:
            List of endpoint URLs
        """
        endpoints = []
        
        try:
            # Try to parse as JSON first
            try:
                spec = json.loads(spec_content)
            except json.JSONDecodeError:
                # Try to parse as YAML
                spec = yaml.safe_load(spec_content)
            
            # Extract paths from OpenAPI spec
            paths = spec.get('paths', {})
            for path, methods in paths.items():
                if isinstance(methods, dict):
                    for method in methods.keys():
                        if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                            endpoint_url = urljoin(base_url, path)
                            endpoints.append(endpoint_url)
        
        except Exception as e:
            logger.warning(f"Failed to parse OpenAPI spec: {str(e)}")
        
        return endpoints
    
    def _scan_endpoint(self, endpoint_url: str, base_url: str) -> Dict[str, Any]:
        """
        Scan a single API endpoint for security issues and PII exposure using thread-local session for thread safety.
        
        Args:
            endpoint_url: The endpoint URL to scan
            base_url: The base URL of the API
            
        Returns:
            Dictionary with endpoint scan results
        """
        endpoint_data = {
            'url': endpoint_url,
            'methods_tested': [],
            'responses': {},
            'findings': [],
            'pii_detected': [],
            'vulnerabilities': [],
            'auth_required': False,
            'response_time_ms': 0
        }
        
        # Test different HTTP methods
        methods_to_test = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
        
        for method in methods_to_test:
            try:
                start_time = time.time()
                
                # Prepare request data for POST/PUT/PATCH
                request_data = None
                if method in ['POST', 'PUT', 'PATCH']:
                    request_data = {'test': 'data', 'id': 1}
                
                # Make the request using thread-local session
                response = self._get_session().request(
                    method=method,
                    url=endpoint_url,
                    json=request_data,
                    timeout=self.request_timeout,
                    verify=self.verify_ssl,
                    allow_redirects=self.follow_redirects
                )
                
                response_time = (time.time() - start_time) * 1000
                endpoint_data['response_time_ms'] = max(endpoint_data['response_time_ms'], response_time)
                
                # Store response information
                endpoint_data['methods_tested'].append(method)
                endpoint_data['responses'][method] = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.content),
                    'response_time_ms': response_time
                }
                
                # Analyze response for security issues
                self._analyze_response_security(response, method, endpoint_data)
                
                # Check for PII in response
                self._check_pii_exposure(response, method, endpoint_data)
                
                # Check for AI Act 2025 compliance
                self._check_ai_act_compliance(endpoint_url, response, method, endpoint_data)
                
                # Check Netherlands UAVG specific compliance
                if self.region.lower() == "netherlands":
                    self._check_netherlands_compliance(response, method, endpoint_data)
                
                # Test for vulnerabilities if method allows input
                if method in ['GET', 'POST', 'PUT', 'PATCH'] and response.status_code not in [404, 405]:
                    self._test_vulnerabilities(endpoint_url, method, endpoint_data)
                
            except requests.exceptions.Timeout:
                endpoint_data['findings'].append({
                    'type': 'performance',
                    'severity': 'Medium',
                    'description': f'{method} request timed out after {self.request_timeout} seconds',
                    'method': method,
                    'url': endpoint_url
                })
            except requests.exceptions.SSLError:
                endpoint_data['findings'].append({
                    'type': 'ssl_error',
                    'severity': 'High',
                    'description': f'SSL certificate error for {method} request',
                    'method': method,
                    'url': endpoint_url
                })
            except Exception as e:
                logger.debug(f"Error testing {method} on {endpoint_url}: {str(e)}")
                continue
        
        return endpoint_data
    
    def _analyze_response_security(self, response: requests.Response, method: str, endpoint_data: Dict[str, Any]):
        """Analyze HTTP response for security issues."""
        headers = response.headers
        
        # Check for missing security headers
        security_headers = {
            'X-Frame-Options': 'Missing X-Frame-Options header (clickjacking protection)',
            'X-Content-Type-Options': 'Missing X-Content-Type-Options header (MIME sniffing protection)',
            'X-XSS-Protection': 'Missing X-XSS-Protection header (XSS protection)',
            'Strict-Transport-Security': 'Missing HSTS header (HTTPS enforcement)',
            'Content-Security-Policy': 'Missing Content-Security-Policy header (XSS/injection protection)'
        }
        
        present_sec_headers = [h for h in security_headers if h in headers]
        for header, description in security_headers.items():
            if header not in headers:
                endpoint_data['findings'].append({
                    'type': 'security_header',
                    'severity': 'Medium',
                    'description': description,
                    'method': method,
                    'url': response.url,
                    'recommendation': f'Add {header} header to improve security',
                    'evidence': f'Header "{header}" not found in server response. Present security headers: {", ".join(present_sec_headers) if present_sec_headers else "None"}'
                })
        
        # Check for information disclosure in headers
        sensitive_headers = ['Server', 'X-Powered-By', 'X-AspNet-Version']
        for header in sensitive_headers:
            if header in headers:
                endpoint_data['findings'].append({
                    'type': 'information_disclosure',
                    'severity': 'Low',
                    'description': f'Server information disclosed in {header} header: {headers[header]}',
                    'method': method,
                    'url': response.url,
                    'recommendation': f'Remove or obfuscate {header} header'
                })
        
        # Check for authentication requirements
        if response.status_code == 401:
            endpoint_data['auth_required'] = True
            endpoint_data['findings'].append({
                'type': 'auth_issue',
                'severity': 'Info',
                'description': 'Endpoint requires authentication',
                'method': method,
                'url': response.url
            })
        elif response.status_code == 403:
            endpoint_data['findings'].append({
                'type': 'auth_issue',
                'severity': 'Medium',
                'description': 'Access forbidden - insufficient permissions',
                'method': method,
                'url': response.url
            })
    
    def _check_pii_exposure(self, response: requests.Response, method: str, endpoint_data: Dict[str, Any]):
        """Check API response for PII exposure."""
        try:
            response_text = response.text
            
            for pii_type, pattern_info in self.pii_patterns.items():
                matches = re.findall(pattern_info['pattern'], response_text, re.IGNORECASE)
                if matches:
                    endpoint_data['pii_detected'].append({
                        'type': pii_type,
                        'count': len(matches),
                        'severity': pattern_info['severity'],
                        'description': pattern_info['description'],
                        'gdpr_category': pattern_info['gdpr_category'],
                        'method': method
                    })
                    
                    endpoint_data['findings'].append({
                        'type': 'pii_exposure',
                        'severity': pattern_info['severity'],
                        'description': f"{pattern_info['description']} ({len(matches)} instances)",
                        'pii_type': pii_type,
                        'method': method,
                        'url': response.url,
                        'gdpr_category': pattern_info['gdpr_category'],
                        'recommendation': f'Implement data masking or removal for {pii_type} in API responses'
                    })
        
        except Exception as e:
            logger.debug(f"Error checking PII exposure: {str(e)}")
    
    def _check_ai_act_compliance(self, endpoint_url: str, response: requests.Response, method: str, endpoint_data: Dict[str, Any]):
        """Check API endpoint for EU AI Act 2025 compliance requirements."""
        try:
            # Check endpoint URL for AI-related patterns
            for category_name, category_info in self.ai_act_patterns.items():
                for pattern in category_info['patterns']:
                    if re.search(pattern, endpoint_url, re.IGNORECASE):
                        finding = {
                            'type': 'ai_act_compliance',
                            'severity': category_info['severity'],
                            'description': f"{category_info['description']} - {endpoint_url}",
                            'ai_act_category': category_info['ai_act_category'],
                            'method': method,
                            'url': response.url,
                            'endpoint_pattern': pattern
                        }
                        
                        # Add specific requirements based on AI category
                        if category_info.get('transparency_required'):
                            finding['transparency_required'] = True
                            finding['recommendation'] = 'Implement transparency measures: clear AI disclosure, decision explanation capabilities'
                        
                        if category_info.get('human_oversight_required'):
                            finding['human_oversight_required'] = True
                            finding['recommendation'] = 'Implement human oversight: meaningful human review of AI decisions'
                        
                        if category_info.get('immediate_review_required'):
                            finding['immediate_review_required'] = True
                            finding['recommendation'] = 'CRITICAL: Review for potential EU AI Act prohibition - may require immediate system changes'
                        
                        endpoint_data['findings'].append(finding)
                        
                        # Also check response content for AI-related data
                        self._check_ai_response_content(response, method, endpoint_data, category_info)
                        
                        break  # Only match first pattern per category
        
        except Exception as e:
            logger.debug(f"Error checking AI Act compliance: {str(e)}")
    
    def _check_ai_response_content(self, response: requests.Response, method: str, endpoint_data: Dict[str, Any], ai_category: Dict[str, Any]):
        """Check API response content for AI Act compliance indicators."""
        try:
            response_text = response.text.lower()
            
            # AI Act specific content patterns
            ai_content_patterns = {
                'decision_explanation': r'(explanation|reasoning|why|because|decision_factors)',
                'confidence_score': r'(confidence|probability|score|certainty)',
                'human_review': r'(human_review|manual_check|human_oversight)',
                'bias_indicators': r'(bias|fairness|discrimination|unfair)',
                'automated_decision': r'(automated|algorithm|ml_decision|ai_result)'
            }
            
            for pattern_name, pattern in ai_content_patterns.items():
                if re.search(pattern, response_text):
                    endpoint_data['findings'].append({
                        'type': 'ai_transparency',
                        'severity': 'Medium',
                        'description': f'AI transparency indicator detected: {pattern_name}',
                        'ai_pattern': pattern_name,
                        'method': method,
                        'url': response.url,
                        'recommendation': f'Ensure {pattern_name} meets EU AI Act transparency requirements'
                    })
        
        except Exception as e:
            logger.debug(f"Error checking AI response content: {str(e)}")
    
    def _check_netherlands_compliance(self, response: requests.Response, method: str, endpoint_data: Dict[str, Any]):
        """Check API response for Netherlands UAVG specific compliance requirements."""
        try:
            response_text = response.text
            
            # Check for BSN with enhanced Netherlands-specific handling and validation
            if 'bsn' in self.pii_patterns:
                bsn_pattern = self.pii_patterns['bsn']['pattern']
                bsn_candidates = re.findall(bsn_pattern, response_text)
                
                # Validate each BSN candidate using 11-proef algorithm
                valid_bsns = [bsn for bsn in bsn_candidates if self._validate_bsn(bsn)]
                
                if valid_bsns:
                    # BSN detection triggers critical Netherlands compliance requirements
                    endpoint_data['findings'].append({
                        'type': 'netherlands_uavg_critical',
                        'severity': 'Critical',
                        'description': f'BSN detected in API response - UAVG compliance required',
                        'netherlands_specific': True,
                        'ap_notification_required': True,
                        'notification_period': '72 hours',
                        'authority': 'Autoriteit Persoonsgegevens (AP)',
                        'method': method,
                        'url': response.url,
                        'bsn_count': len(valid_bsns),
                        'recommendation': 'IMMEDIATE ACTION: Implement BSN masking, notify AP within 72 hours if data breach'
                    })
            
            # Check for other Netherlands-specific patterns
            nl_patterns = {
                'dutch_address': r'\b\d{4}\s?[A-Z]{2}\s+\d+[A-Z]?\b',  # Postal code + house number
                'dutch_kvk': r'\b\d{8}\b',  # KvK number
                'dutch_phone': r'\b(\+31|0031|0)\s?[1-9]\s?\d{1,2}\s?\d{6,7}\b'
            }
            
            for pattern_name, pattern in nl_patterns.items():
                matches = re.findall(pattern, response_text, re.IGNORECASE)
                if matches:
                    endpoint_data['findings'].append({
                        'type': 'netherlands_pii',
                        'severity': 'High',
                        'description': f'Netherlands-specific PII detected: {pattern_name}',
                        'netherlands_specific': True,
                        'pattern_type': pattern_name,
                        'method': method,
                        'url': response.url,
                        'count': len(matches),
                        'recommendation': f'Implement UAVG-compliant handling for {pattern_name}'
                    })
            
            # Check for UAVG data subject rights implementation indicators
            uavg_rights_indicators = [
                'data_access', 'data_deletion', 'data_portability', 
                'data_rectification', 'consent_withdrawal'
            ]
            
            for indicator in uavg_rights_indicators:
                if indicator in response_text.lower():
                    endpoint_data['findings'].append({
                        'type': 'uavg_rights_implementation',
                        'severity': 'Low',
                        'description': f'UAVG data subject rights implementation detected: {indicator}',
                        'netherlands_specific': True,
                        'rights_indicator': indicator,
                        'method': method,
                        'url': response.url,
                        'recommendation': 'Verify UAVG data subject rights implementation is complete and compliant'
                    })
        
        except Exception as e:
            logger.debug(f"Error checking Netherlands compliance: {str(e)}")
    
    def _validate_bsn(self, bsn_candidate: str) -> bool:
        """Validate Dutch BSN using 11-proef checksum algorithm."""
        try:
            # Remove any separators and get just digits
            digits = re.sub(r'[-.\s]', '', bsn_candidate)
            
            # BSN must be exactly 9 digits
            if len(digits) != 9 or not digits.isdigit():
                return False
            
            # Apply 11-proef validation
            total = 0
            for i, digit in enumerate(digits[:8]):  # First 8 digits
                total += int(digit) * (9 - i)
            
            # Add last digit multiplied by -1
            total += int(digits[8]) * -1
            
            # Valid if total is divisible by 11
            return total % 11 == 0
            
        except Exception:
            return False
    
    def _aggregate_compliance_findings(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate compliance findings into scan-level summaries."""
        try:
            compliance_summary = {
                'ai_act_findings': [],
                'regulatory_notifications': [],
                'netherlands_uavg_status': 'compliant',
                'ai_act_status': 'no_ai_detected'
            }
            
            # Aggregate findings from all endpoints
            all_findings = []
            for endpoint_data in scan_results.get('endpoints_data', []):
                all_findings.extend(endpoint_data.get('findings', []))
            
            # Process AI Act findings
            ai_findings = [f for f in all_findings if f.get('type') in ['ai_act_compliance', 'ai_transparency']]
            if ai_findings:
                compliance_summary['ai_act_findings'] = ai_findings
                
                # Determine overall AI Act status
                if any(f.get('immediate_review_required') for f in ai_findings):
                    compliance_summary['ai_act_status'] = 'prohibited_practices_detected'
                elif any(f.get('ai_act_category') == 'High-Risk AI System' for f in ai_findings):
                    compliance_summary['ai_act_status'] = 'high_risk_ai_detected'
                else:
                    compliance_summary['ai_act_status'] = 'ai_system_detected'
            
            # Process Netherlands UAVG findings
            nl_findings = [f for f in all_findings if f.get('netherlands_specific')]
            bsn_findings = [f for f in nl_findings if f.get('type') == 'netherlands_uavg_critical']
            
            if bsn_findings:
                compliance_summary['netherlands_uavg_status'] = 'critical_violation'
                compliance_summary['regulatory_notifications'].append({
                    'authority': 'Autoriteit Persoonsgegevens (AP)',
                    'trigger': 'BSN detection in API response',
                    'notification_period': '72 hours',
                    'severity': 'Critical',
                    'bsn_instances': sum(f.get('bsn_count', 0) for f in bsn_findings),
                    'affected_endpoints': len(set(f.get('url') for f in bsn_findings))
                })
            elif nl_findings:
                compliance_summary['netherlands_uavg_status'] = 'requires_attention'
            
            scan_results.update(compliance_summary)
            return compliance_summary
            
        except Exception as e:
            logger.debug(f"Error aggregating compliance findings: {str(e)}")
            return {}
    
    def _test_vulnerabilities(self, endpoint_url: str, method: str, endpoint_data: Dict[str, Any]):
        """Test endpoint for common vulnerabilities."""
        for vuln_type, vuln_info in self.vulnerability_patterns.items():
            for payload in vuln_info['payloads']:
                try:
                    # Test vulnerability with payload
                    test_url = endpoint_url
                    request_data = None
                    
                    if method == 'GET':
                        # Add payload to URL parameters
                        test_url = f"{endpoint_url}?test={payload}"
                    elif method in ['POST', 'PUT', 'PATCH']:
                        # Add payload to request body
                        request_data = {'test': payload, 'id': payload}
                    
                    response = self._get_session().request(
                        method=method,
                        url=test_url,
                        json=request_data,
                        timeout=self.request_timeout,
                        verify=self.verify_ssl
                    )
                    
                    # Check response for vulnerability indicators
                    response_text = response.text.lower()
                    for indicator in vuln_info['indicators']:
                        if indicator in response_text:
                            endpoint_data['vulnerabilities'].append({
                                'type': vuln_type,
                                'severity': vuln_info['severity'],
                                'description': vuln_info['description'],
                                'payload': payload,
                                'indicator': indicator,
                                'method': method
                            })
                            
                            endpoint_data['findings'].append({
                                'type': 'vulnerability',
                                'severity': vuln_info['severity'],
                                'description': f"{vuln_info['description']} with payload: {payload}",
                                'vulnerability_type': vuln_type,
                                'method': method,
                                'url': endpoint_url,
                                'recommendation': f'Implement input validation and sanitization to prevent {vuln_type}'
                            })
                            break
                
                except Exception as e:
                    logger.debug(f"Error testing {vuln_type} vulnerability: {str(e)}")
                    continue
    
    def _check_ssl_security(self, base_url: str) -> Dict[str, Any]:
        """Check SSL/TLS security configuration."""
        ssl_info = {
            'enabled': False,
            'valid_certificate': False,
            'protocol_version': None,
            'cipher_suite': None,
            'issues': []
        }
        
        try:
            parsed_url = urlparse(base_url)
            if parsed_url.scheme == 'https':
                ssl_info['enabled'] = True
                
                # Test SSL connection
                response = self._get_session().get(base_url, timeout=self.request_timeout, verify=True)
                ssl_info['valid_certificate'] = True
                
            else:
                ssl_info['issues'].append('API does not use HTTPS encryption')
        
        except requests.exceptions.SSLError as e:
            ssl_info['issues'].append(f'SSL certificate error: {str(e)}')
        except Exception as e:
            ssl_info['issues'].append(f'SSL check failed: {str(e)}')
        
        return ssl_info
    
    def _analyze_cors_policy(self, base_url: str) -> Dict[str, Any]:
        """Analyze CORS policy configuration."""
        cors_info = {
            'enabled': False,
            'allow_origins': [],
            'allow_methods': [],
            'allow_headers': [],
            'issues': []
        }
        
        try:
            # Send OPTIONS request to check CORS headers
            response = self._get_session().options(base_url, timeout=self.request_timeout)
            
            cors_headers = {
                'Access-Control-Allow-Origin': 'allow_origins',
                'Access-Control-Allow-Methods': 'allow_methods',
                'Access-Control-Allow-Headers': 'allow_headers'
            }
            
            for header, key in cors_headers.items():
                if header in response.headers:
                    cors_info['enabled'] = True
                    cors_info[key] = response.headers[header].split(',')
            
            # Check for overly permissive CORS
            if cors_info.get('allow_origins') and '*' in cors_info['allow_origins']:
                cors_info['issues'].append('Overly permissive CORS policy allows all origins')
        
        except Exception as e:
            cors_info['issues'].append(f'CORS analysis failed: {str(e)}')
        
        return cors_info
    
    def _check_rate_limiting(self, base_url: str) -> Dict[str, Any]:
        """Check if rate limiting is implemented."""
        rate_limit_info = {
            'enabled': False,
            'limit_headers': [],
            'issues': []
        }
        
        try:
            # Make multiple rapid requests to test rate limiting
            responses = []
            for i in range(5):
                response = self._get_session().get(base_url, timeout=self.request_timeout)
                responses.append(response)
                
                # Check for rate limit headers
                rate_headers = ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'Retry-After']
                for header in rate_headers:
                    if header in response.headers:
                        rate_limit_info['enabled'] = True
                        if header not in rate_limit_info['limit_headers']:
                            rate_limit_info['limit_headers'].append(header)
                
                # Check if we hit rate limit
                if response.status_code == 429:
                    rate_limit_info['enabled'] = True
                    break
            
            if not rate_limit_info['enabled']:
                rate_limit_info['issues'].append('No rate limiting detected - API may be vulnerable to abuse')
        
        except Exception as e:
            rate_limit_info['issues'].append(f'Rate limiting check failed: {str(e)}')
        
        return rate_limit_info
    
    def generate_privacy_recommendations(self, scan_results: Dict[str, Any]) -> List[str]:
        """
        Generate comprehensive privacy compliance recommendations based on scan results.
        
        Args:
            scan_results: Complete API scan results dictionary
            
        Returns:
            List of actionable privacy recommendations
        """
        recommendations = []
        
        # PII exposure recommendations
        pii_exposures = scan_results.get('pii_exposures', [])
        if pii_exposures:
            critical_pii = [p for p in pii_exposures if p.get('severity') == 'Critical']
            if critical_pii:
                recommendations.append(
                    f"Critical: {len(critical_pii)} endpoints expose sensitive PII (SSN, credit cards, passwords). "
                    "Implement immediate data masking and access controls."
                )
            
            high_pii = [p for p in pii_exposures if p.get('severity') == 'High']
            if high_pii:
                recommendations.append(
                    f"High Priority: {len(high_pii)} endpoints expose personal data (emails, phones). "
                    "Review data minimization practices and implement field-level encryption."
                )
        
        # Authentication and authorization recommendations
        auth_issues = scan_results.get('auth_issues', [])
        if auth_issues:
            recommendations.append(
                f"Security Gap: {len(auth_issues)} authentication issues detected. "
                "Implement proper OAuth 2.0 or JWT-based authentication for all sensitive endpoints."
            )
        
        # SSL/TLS recommendations
        ssl_info = scan_results.get('ssl_info', {})
        if not ssl_info.get('enabled'):
            recommendations.append(
                "Critical Security Issue: API does not use HTTPS encryption. "
                "Implement SSL/TLS encryption immediately to protect data in transit."
            )
        elif ssl_info.get('issues'):
            recommendations.append(
                "SSL Configuration Issues: Invalid or misconfigured SSL certificate detected. "
                "Update SSL certificate and verify proper HTTPS implementation."
            )
        
        # Rate limiting recommendations
        rate_limiting = scan_results.get('rate_limiting', {})
        if not rate_limiting.get('enabled'):
            recommendations.append(
                "API Security: No rate limiting detected. Implement rate limiting to prevent "
                "API abuse and ensure service availability."
            )
        
        # CORS policy recommendations
        cors_analysis = scan_results.get('cors_analysis', {})
        if cors_analysis.get('issues'):
            recommendations.append(
                "CORS Security: Overly permissive CORS policy detected. "
                "Restrict allowed origins to only trusted domains."
            )
        
        # Vulnerability recommendations
        vulnerabilities = scan_results.get('vulnerabilities', [])
        if vulnerabilities:
            critical_vulns = [v for v in vulnerabilities if v.get('severity') == 'Critical']
            if critical_vulns:
                recommendations.append(
                    f"Critical Vulnerabilities: {len(critical_vulns)} critical security vulnerabilities found. "
                    "Implement input validation, parameterized queries, and security testing."
                )
        
        # General API security recommendations
        findings = scan_results.get('findings', [])
        security_headers = [f for f in findings if f.get('type') == 'security_header']
        if security_headers:
            recommendations.append(
                f"Security Headers: {len(security_headers)} missing security headers detected. "
                "Implement HSTS, CSP, X-Frame-Options, and other security headers."
            )
        
        # GDPR compliance recommendations
        if pii_exposures or auth_issues:
            recommendations.append(
                "GDPR Compliance: Implement data protection measures including encryption, "
                "access logging, data retention policies, and user consent management."
            )
        
        # API documentation and monitoring
        recommendations.append(
            "Best Practices: Implement API documentation, request/response logging, "
            "monitoring, and regular security assessments to maintain compliance."
        )
        
        if len(recommendations) == 1:  # Only the best practices recommendation
            recommendations.insert(0, 
                "Good Security Posture: Basic API security appears adequate. "
                "Continue regular security assessments and monitoring."
            )
        
        return recommendations
    
    def cancel_scan(self):
        """Cancel the current scan if running."""
        self.is_running = False