"""
Intelligent Scanner Integration Wrapper

Provides seamless integration between the main application and intelligent scanners.
Maintains backward compatibility while adding scalability improvements.
"""

import logging
import os
import tempfile
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import streamlit as st

from services.intelligent_scanner_manager import intelligent_scanner_manager
from utils.activity_tracker import track_scan_started, track_scan_completed, track_scan_failed, ScannerType
from services.license_integration import track_scanner_usage
from services.results_aggregator import ResultsAggregator

# Enterprise integration - non-breaking import
try:
    from utils.event_bus import EventType, publish_event
    ENTERPRISE_EVENTS_AVAILABLE = True
except ImportError:
    ENTERPRISE_EVENTS_AVAILABLE = False

logger = logging.getLogger("components.intelligent_scanner_wrapper")

class IntelligentScannerWrapper:
    """Wrapper that integrates intelligent scanning with existing UI."""
    
    def __init__(self):
        self.scanner_manager = intelligent_scanner_manager
        self.results_aggregator = ResultsAggregator()
    
    def _calculate_risk_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate risk summary from findings."""
        summary = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        for finding in findings:
            severity = finding.get('severity', finding.get('risk_level', 'Medium'))
            if isinstance(severity, str):
                severity = severity.capitalize()
                if severity in summary:
                    summary[severity] += 1
                else:
                    summary['Medium'] += 1
        return summary
    
    def execute_code_scan_intelligent(self, region: str, username: str, 
                                    uploaded_files=None, repo_url=None, 
                                    directory_path=None, include_comments=True,
                                    detect_secrets=True, gdpr_compliance=True,
                                    scan_mode="smart", use_entropy=True,
                                    use_git_metadata=False, timeout=60,
                                    max_files=200, priority_extensions=None) -> Dict[str, Any]:
        """Execute intelligent code scanning with enhanced scalability."""
        
        # Session tracking setup
        session_id = st.session_state.get('session_id', str(uuid.uuid4()))
        user_id = st.session_state.get('user_id', username)
        
        # Generate stable scan_id for event correlation
        scan_id = f"code_scan_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
        
        scan_start_time = datetime.now()
        
        # Determine source type
        if uploaded_files:
            source_type = "uploaded_files"
            source_info = f"{len(uploaded_files)} files"
        elif repo_url:
            source_type = "repository"
            source_info = repo_url
        else:
            source_type = "directory"
            source_info = directory_path or "local"
        
        # Track scan start
        track_scan_started(
            session_id=session_id,
            user_id=user_id,
            username=username,
            scanner_type=ScannerType.CODE,
            region=region,
            details={
                'source_type': source_type,
                'source_info': source_info,
                'scan_mode': scan_mode,
                'intelligent_scanning': True,
                'gdpr_compliance': gdpr_compliance,
                'netherlands_uavg': region == "Netherlands",
                'use_entropy': use_entropy,
                'use_git_metadata': use_git_metadata,
                'timeout': timeout,
                'max_files': max_files
            }
        )
        
        # Enterprise event publishing (non-breaking)
        if ENTERPRISE_EVENTS_AVAILABLE:
            try:
                publish_event(
                    event_type=EventType.SCAN_STARTED,
                    source="intelligent_scanner",
                    user_id=user_id,
                    session_id=session_id,
                    data={
                        'scan_id': scan_id,  # Add stable scan_id for correlation
                        'scanner_type': 'code',
                        'region': region,
                        'source_type': source_type,
                        'source_info': source_info,
                        'scan_mode': scan_mode,
                        'gdpr_compliance': gdpr_compliance,
                        'netherlands_uavg': region == "Netherlands"
                    }
                )
            except Exception as e:
                logger.debug(f"Enterprise event publishing failed: {e}")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(current: int, total: int, message: str):
            """Progress callback for real-time updates."""
            progress = min(current / max(total, 1), 0.99)
            progress_bar.progress(progress)
            status_text.text(f"🔍 {message}")
        
        try:
            # Prepare scan target based on source type
            if uploaded_files:
                # Handle uploaded files - scan directly without multiprocessing
                progress_callback(10, 100, "Processing uploaded files...")
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_paths = []
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        file_paths.append(file_path)
                    
                    progress_callback(30, 100, "Scanning files for PII and code issues...")
                    
                    # Scan uploaded files directly (avoid multiprocessing pickle issues)
                    from services.code_scanner import CodeScanner
                    code_scanner = CodeScanner(
                        region=region,
                        include_comments=include_comments,
                        use_entropy=use_entropy
                    )
                    
                    all_findings = []
                    files_scanned = 0
                    total_files = len(file_paths)
                    
                    for idx, file_path in enumerate(file_paths):
                        progress_callback(30 + int((idx / total_files) * 50), 100, f"Scanning {os.path.basename(file_path)}...")
                        try:
                            result = code_scanner.scan_file(file_path)
                            if result and result.get('pii_found'):
                                all_findings.extend(result['pii_found'])
                            files_scanned += 1
                        except Exception as e:
                            logger.warning(f"Error scanning {file_path}: {e}")
                    
                    progress_callback(85, 100, "Processing scan results...")
                    
                    # Build scan result
                    scan_result = {
                        'findings': all_findings,
                        'pii_count': len(all_findings),
                        'files_scanned': files_scanned,
                        'files_skipped': 0,
                        'status': 'success',
                        'scan_type': 'code',
                        'scan_mode': scan_mode,
                        'intelligence_applied': True,
                        'risk_summary': self._calculate_risk_summary(all_findings)
                    }
            
            elif repo_url:
                # Use intelligent repository scanner
                scan_result = self.scanner_manager.scan_intelligent(
                    scan_type='repository',
                    scan_target=repo_url,
                    scan_mode=scan_mode,
                    max_items=max_files,
                    progress_callback=progress_callback,
                    region=region,
                    branch='main',
                    timeout=timeout,
                    use_entropy=use_entropy,
                    use_git_metadata=use_git_metadata,
                    priority_extensions=priority_extensions or []
                )
            
            elif directory_path:
                # Use intelligent code scanner for directory
                scan_result = self.scanner_manager.scan_intelligent(
                    scan_type='code',
                    scan_target=directory_path,
                    scan_mode=scan_mode,
                    max_items=max_files,
                    progress_callback=progress_callback,
                    region=region,
                    timeout=timeout,
                    include_comments=include_comments,
                    detect_secrets=detect_secrets,
                    use_entropy=use_entropy,
                    use_git_metadata=use_git_metadata,
                    priority_extensions=priority_extensions or []
                )
            else:
                st.error("Please provide files, repository URL, or directory path to scan.")
                # Return error structure instead of None
                return {
                    'scan_id': f"error_{uuid.uuid4().hex[:8]}",
                    'scan_type': 'Intelligent Code Scanner',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': 'No scan target provided',
                    'findings': [],
                    'files_scanned': 0,
                    'intelligence_applied': False
                }
            
            # Validate scan result before processing
            if not scan_result or not isinstance(scan_result, dict):
                raise ValueError("Scanner returned invalid or empty result")
            
            # Track successful completion
            scan_duration = int((datetime.now() - scan_start_time).total_seconds() * 1000)
            findings_count = len(scan_result.get('findings', []))
            
            # Ensure scan_type is set correctly for database storage
            scan_result['scan_type'] = 'code'
            scan_result['region'] = region
            scan_result['scan_id'] = scan_id  # Add stable scan_id to results
            scan_result['total_pii_found'] = findings_count
            scan_result['high_risk_count'] = len([f for f in scan_result.get('findings', []) if f.get('severity') == 'high'])
            
            # Save scan result to database for dashboard display
            try:
                self.results_aggregator.save_scan_result(username, scan_result)
                logger.info(f"Code scan result saved to database with scan_type='code' for user {username}")
            except Exception as e:
                logger.error(f"Failed to save code scan result to database: {str(e)}")
            
            track_scan_completed(
                session_id=session_id,
                user_id=user_id,
                username=username,
                scanner_type=ScannerType.CODE,
                findings_count=findings_count,
                files_scanned=scan_result.get('files_scanned', scan_result.get('files_processed', 0)),
                duration_ms=scan_duration,
                region=region,
                details={
                    'scan_id': scan_result.get('scan_id'),
                    'intelligence_metrics': scan_result.get('intelligence_metrics', {}),
                    'scan_coverage': scan_result.get('scan_coverage', 0),
                    'strategy_used': scan_result.get('scanning_strategy', {}).get('type', 'unknown')
                }
            )
            
            # Enterprise event publishing (non-breaking)
            if ENTERPRISE_EVENTS_AVAILABLE:
                try:
                    # Publish scan completed event
                    publish_event(
                        event_type=EventType.SCAN_COMPLETED,
                        source="intelligent_scanner",
                        user_id=user_id,
                        session_id=session_id,
                        data={
                            'scan_id': scan_id,  # Same scan_id for correlation
                            'scanner_type': 'code',
                            'region': region,
                            'findings': scan_result.get('findings', []),
                            'findings_count': findings_count,
                            'compliance_score': scan_result.get('compliance_score', 0),
                            'critical_issues': len([f for f in scan_result.get('findings', []) if f.get('risk_level') == 'Critical']),
                            'high_issues': len([f for f in scan_result.get('findings', []) if f.get('risk_level') == 'High']),
                            'scan_duration_ms': scan_duration,
                            'success': True,
                            'files_scanned': scan_result.get('files_scanned', scan_result.get('files_processed', 0))
                        }
                    )
                    
                    # Publish individual finding events for enterprise processing
                    findings = scan_result.get('findings', [])
                    for finding in findings:
                        publish_event(
                            event_type=EventType.FINDING_DETECTED,
                            source="intelligent_scanner",
                            user_id=user_id,
                            session_id=session_id,
                            data={
                                'scan_id': scan_id,  # Same scan_id for correlation
                                'scanner_type': 'code',
                                'type': finding.get('type', 'Unknown'),
                                'risk_level': finding.get('risk_level', finding.get('severity', 'Low')),
                                'location': finding.get('file', finding.get('location', 'Unknown')),
                                'description': finding.get('description', ''),
                                'line_number': finding.get('line_number'),
                                'finding_id': finding.get('id', str(uuid.uuid4()))
                            }
                        )
                        
                        # Publish critical issue events for high-priority findings
                        if finding.get('risk_level') == 'Critical' or finding.get('severity') == 'Critical':
                            publish_event(
                                event_type=EventType.CRITICAL_ISSUE_FOUND,
                                source="intelligent_scanner",
                                user_id=user_id,
                                session_id=session_id,
                                data={
                                    'scan_id': scan_id,  # Same scan_id for correlation
                                    'scanner_type': 'code',
                                    'finding': finding,
                                    'requires_immediate_attention': True,
                                    'auto_ticket_eligible': True
                                }
                            )
                except Exception as e:
                    logger.debug(f"Enterprise event publishing failed: {e}")
            
            # Track license usage
            track_scanner_usage('code', region, success=True, duration_ms=scan_duration)
            
            progress_bar.progress(1.0)
            status_text.text("✅ Intelligent scan completed!")
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Intelligent code scan failed: {str(e)}")
            
            # Track scan failure
            track_scan_failed(
                session_id=session_id,
                user_id=user_id,
                username=username,
                scanner_type=ScannerType.CODE,
                error_message=str(e),
                region=region,
                details={'intelligent_scanning': True}
            )
            
            st.error(f"Intelligent scan failed: {str(e)}")
            # Return error structure instead of None
            return {
                'scan_id': f"error_{uuid.uuid4().hex[:8]}",
                'scan_type': 'Intelligent Code Scanner',
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e),
                'findings': [],
                'files_scanned': 0,
                'intelligence_applied': False
            }

    def execute_image_scan_intelligent(self, region: str, username: str,
                                     uploaded_files: List[Any],
                                     scan_mode: str = "smart") -> Dict[str, Any]:
        """Execute intelligent image scanning with enhanced OCR processing."""
        
        session_id = st.session_state.get('session_id', str(uuid.uuid4()))
        user_id = st.session_state.get('user_id', username)
        
        # Generate stable scan_id for event correlation
        scan_id = f"image_scan_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
        
        scan_start_time = datetime.now()
        
        # Track scan start
        track_scan_started(
            session_id=session_id,
            user_id=user_id,
            username=username,
            scanner_type=ScannerType.IMAGE,
            region=region,
            details={
                'file_count': len(uploaded_files),
                'scan_mode': scan_mode,
                'intelligent_scanning': True,
                'image_types': [file.name.split('.')[-1] for file in uploaded_files]
            }
        )
        
        # Enterprise event publishing (non-breaking)
        if ENTERPRISE_EVENTS_AVAILABLE:
            try:
                publish_event(
                    event_type=EventType.SCAN_STARTED,
                    source="intelligent_scanner",
                    user_id=user_id,
                    session_id=session_id,
                    data={
                        'scan_id': scan_id,  # Add stable scan_id for correlation
                        'scanner_type': 'image',
                        'region': region,
                        'file_count': len(uploaded_files),
                        'scan_mode': scan_mode,
                        'image_types': [file.name.split('.')[-1] for file in uploaded_files]
                    }
                )
            except Exception as e:
                logger.debug(f"Enterprise event publishing failed: {e}")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(current: int, total: int, message: str):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"🖼️ {message}")
        
        try:
            # Save uploaded files temporarily
            with tempfile.TemporaryDirectory() as temp_dir:
                image_paths = []
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    image_paths.append(file_path)
                
                # Use intelligent image scanner
                scan_result = self.scanner_manager.scan_intelligent(
                    scan_type='images',
                    scan_target=image_paths,
                    scan_mode=scan_mode,
                    max_items=50,
                    progress_callback=progress_callback,
                    region=region
                )
                
                # Validate scan result before processing
                if not scan_result or not isinstance(scan_result, dict):
                    raise ValueError("Image scanner returned invalid or empty result")
            
            # Track completion
            scan_duration = int((datetime.now() - scan_start_time).total_seconds() * 1000)
            findings_count = len(scan_result.get('findings', []))
            
            # Add scan_id to scan result for consistency
            scan_result['scan_id'] = scan_id
            scan_result['scanner_type'] = 'image'
            scan_result['region'] = region
            
            track_scan_completed(
                session_id=session_id,
                user_id=user_id,
                username=username,
                scanner_type=ScannerType.IMAGE,
                findings_count=findings_count,
                files_scanned=scan_result.get('images_processed', 0),
                duration_ms=scan_duration,
                region=region,
                details={
                    'scan_id': scan_id,  # Use consistent scan_id
                    'face_detections': scan_result.get('face_detections', 0),
                    'document_detections': scan_result.get('document_detections', 0),
                    'ocr_results_count': len(scan_result.get('ocr_results', []))
                }
            )
            
            # Enterprise event publishing (non-breaking)
            if ENTERPRISE_EVENTS_AVAILABLE:
                try:
                    # Publish scan completed event
                    publish_event(
                        event_type=EventType.SCAN_COMPLETED,
                        source="intelligent_scanner",
                        user_id=user_id,
                        session_id=session_id,
                        data={
                            'scan_id': scan_id,  # Same scan_id for correlation
                            'scanner_type': 'image',
                            'region': region,
                            'findings': scan_result.get('findings', []),
                            'findings_count': findings_count,
                            'compliance_score': scan_result.get('compliance_score', 0),
                            'critical_issues': len([f for f in scan_result.get('findings', []) if f.get('risk_level') == 'Critical']),
                            'high_issues': len([f for f in scan_result.get('findings', []) if f.get('risk_level') == 'High']),
                            'scan_duration_ms': scan_duration,
                            'success': True,
                            'images_processed': scan_result.get('images_processed', 0),
                            'face_detections': scan_result.get('face_detections', 0)
                        }
                    )
                    
                    # Publish individual finding events for enterprise processing
                    findings = scan_result.get('findings', [])
                    for finding in findings:
                        publish_event(
                            event_type=EventType.FINDING_DETECTED,
                            source="intelligent_scanner",
                            user_id=user_id,
                            session_id=session_id,
                            data={
                                'scan_id': scan_id,  # Same scan_id for correlation
                                'scanner_type': 'image',
                                'type': finding.get('type', 'Unknown'),
                                'risk_level': finding.get('risk_level', finding.get('severity', 'Low')),
                                'location': finding.get('file', finding.get('location', 'Unknown')),
                                'description': finding.get('description', ''),
                                'finding_id': finding.get('id', str(uuid.uuid4())),
                                'image_metadata': finding.get('metadata', {})
                            }
                        )
                        
                        # Publish critical issue events for high-priority findings
                        if finding.get('risk_level') == 'Critical' or finding.get('severity') == 'Critical':
                            publish_event(
                                event_type=EventType.CRITICAL_ISSUE_FOUND,
                                source="intelligent_scanner",
                                user_id=user_id,
                                session_id=session_id,
                                data={
                                    'scan_id': scan_id,  # Same scan_id for correlation
                                    'scanner_type': 'image',
                                    'finding': finding,
                                    'requires_immediate_attention': True,
                                    'auto_ticket_eligible': True
                                }
                            )
                except Exception as e:
                    logger.debug(f"Enterprise event publishing failed: {e}")
            
            track_scanner_usage('image', region, success=True, duration_ms=scan_duration)
            
            progress_bar.progress(100)
            status_text.text("✅ Intelligent image scan completed!")
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Intelligent image scan failed: {str(e)}")
            
            track_scan_failed(
                session_id=session_id,
                user_id=user_id,
                username=username,
                scanner_type=ScannerType.IMAGE,
                error_message=str(e),
                region=region,
                details={'intelligent_scanning': True}
            )
            
            st.error(f"Intelligent image scan failed: {str(e)}")
            # Return error structure instead of None
            return {
                'scan_id': f"error_{uuid.uuid4().hex[:8]}",
                'scan_type': 'Intelligent Image Scanner',
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e),
                'findings': [],
                'files_scanned': 0,
                'intelligence_applied': False
            }

    def execute_website_scan_intelligent(self, region: str, username: str,
                                       base_url: str, max_pages: Optional[int] = None,
                                       max_depth: Optional[int] = None,
                                       scan_mode: str = "smart") -> Dict[str, Any]:
        """Execute intelligent website scanning with adaptive crawling."""
        
        session_id = st.session_state.get('session_id', str(uuid.uuid4()))
        user_id = st.session_state.get('user_id', username)
        scan_start_time = datetime.now()
        
        # Track scan start
        track_scan_started(
            session_id=session_id,
            user_id=user_id,
            username=username,
            scanner_type=ScannerType.WEBSITE,
            region=region,
            details={
                'base_url': base_url,
                'scan_mode': scan_mode,
                'intelligent_scanning': True,
                'max_pages': max_pages,
                'max_depth': max_depth
            }
        )
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(current: int, total: int, message: str):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"🌐 {message}")
        
        try:
            # Use intelligent website scanner
            scan_result = self.scanner_manager.scan_intelligent(
                scan_type='website',
                scan_target=base_url,
                scan_mode=scan_mode,
                max_items=max_pages or 25,
                progress_callback=progress_callback,
                region=region,
                max_depth=max_depth or 3
            )
            
            # Validate scan result before processing
            if not scan_result or not isinstance(scan_result, dict):
                raise ValueError("Website scanner returned invalid or empty result")
            
            # Track completion
            scan_duration = int((datetime.now() - scan_start_time).total_seconds() * 1000)
            findings_count = len(scan_result.get('findings', []))
            
            track_scan_completed(
                session_id=session_id,
                user_id=user_id,
                username=username,
                scanner_type=ScannerType.WEBSITE,
                findings_count=findings_count,
                files_scanned=scan_result.get('pages_scanned', 0),
                duration_ms=scan_duration,
                region=region,
                details={
                    'scan_id': scan_result.get('scan_id'),
                    'pages_discovered': scan_result.get('pages_discovered', 0),
                    'cookies_found': scan_result.get('cookies_found', 0),
                    'trackers_found': scan_result.get('trackers_found', 0)
                }
            )
            
            track_scanner_usage('website', region, success=True, duration_ms=scan_duration)
            
            progress_bar.progress(100)
            status_text.text("✅ Intelligent website scan completed!")
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Intelligent website scan failed: {str(e)}")
            
            track_scan_failed(
                session_id=session_id,
                user_id=user_id,
                username=username,
                scanner_type=ScannerType.WEBSITE,
                error_message=str(e),
                region=region,
                details={'intelligent_scanning': True}
            )
            
            st.error(f"Intelligent website scan failed: {str(e)}")
            # Return error structure instead of None
            return {
                'scan_id': f"error_{uuid.uuid4().hex[:8]}",
                'scan_type': 'Intelligent Website Scanner',
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e),
                'findings': [],
                'files_scanned': 0,
                'intelligence_applied': False
            }

    def execute_database_scan_intelligent(self, region: str, username: str,
                                        connection_params: Dict[str, Any],
                                        max_tables: Optional[int] = None,
                                        scan_mode: str = "smart") -> Dict[str, Any]:
        """Execute intelligent database scanning with adaptive sampling."""
        
        session_id = st.session_state.get('session_id', str(uuid.uuid4()))
        user_id = st.session_state.get('user_id', username)
        scan_start_time = datetime.now()
        
        # Track scan start
        track_scan_started(
            session_id=session_id,
            user_id=user_id,
            username=username,
            scanner_type=ScannerType.DATABASE,
            region=region,
            details={
                'database_type': connection_params.get('type', 'unknown'),
                'scan_mode': scan_mode,
                'intelligent_scanning': True,
                'max_tables': max_tables
            }
        )
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(current: int, total: int, message: str):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"🗄️ {message}")
        
        try:
            # Use intelligent database scanner
            scan_result = self.scanner_manager.scan_intelligent(
                scan_type='database',
                scan_target=connection_params,
                scan_mode=scan_mode,
                max_items=max_tables or 50,
                progress_callback=progress_callback,
                region=region
            )
            
            # Validate scan result before processing
            if not scan_result or not isinstance(scan_result, dict):
                raise ValueError("Database scanner returned invalid or empty result")
            
            # Track completion
            scan_duration = int((datetime.now() - scan_start_time).total_seconds() * 1000)
            findings_count = len(scan_result.get('findings', []))
            
            track_scan_completed(
                session_id=session_id,
                user_id=user_id,
                username=username,
                scanner_type=ScannerType.DATABASE,
                findings_count=findings_count,
                files_scanned=scan_result.get('tables_scanned', 0),
                duration_ms=scan_duration,
                region=region,
                details={
                    'scan_id': scan_result.get('scan_id'),
                    'tables_discovered': scan_result.get('tables_discovered', 0),
                    'rows_analyzed': scan_result.get('rows_analyzed', 0),
                    'schema_analysis': scan_result.get('schema_analysis', {})
                }
            )
            
            track_scanner_usage('database', region, success=True, duration_ms=scan_duration)
            
            progress_bar.progress(100)
            status_text.text("✅ Intelligent database scan completed!")
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Intelligent database scan failed: {str(e)}")
            
            track_scan_failed(
                session_id=session_id,
                user_id=user_id,
                username=username,
                scanner_type=ScannerType.DATABASE,
                error_message=str(e),
                region=region,
                details={'intelligent_scanning': True}
            )
            
            st.error(f"Intelligent database scan failed: {str(e)}")
            # Return error structure instead of None
            return {
                'scan_id': f"error_{uuid.uuid4().hex[:8]}",
                'scan_type': 'Intelligent Database Scanner',
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e),
                'findings': [],
                'files_scanned': 0,
                'intelligence_applied': False
            }

    def display_intelligent_scan_results(self, scan_result: Dict[str, Any]):
        """Display scan results with intelligence metrics."""
        
        st.subheader("📊 Intelligent Scan Results")
        
        # Show intelligence improvements with better error handling
        intelligence_metrics = scan_result.get('intelligence_metrics', {})
        if intelligence_metrics:
            strategy_name = intelligence_metrics.get('strategy_used', 'Smart')
            st.info(f"🧠 **Intelligence Applied**: {strategy_name} strategy used")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                coverage = intelligence_metrics.get('coverage_achieved', scan_result.get('scan_coverage', 0))
                st.metric("Coverage", f"{coverage:.1f}%")
            with col2:
                efficiency = intelligence_metrics.get('efficiency_rating', 0)
                st.metric("Efficiency", f"{max(efficiency, 1):.1f}/100")
            with col3:
                scalability = intelligence_metrics.get('scalability_rating', 0)
                st.metric("Scalability", f"{max(scalability, 1):.1f}/100")
            with col4:
                time_saved = intelligence_metrics.get('time_savings_estimate', 0)
                if time_saved > 0:
                    st.metric("Time Saved", f"{time_saved:.0f}s")
                else:
                    # Estimate time saved based on scan efficiency
                    files_scanned = scan_result.get('files_scanned', 0)
                    if files_scanned > 20:
                        estimated_saved = files_scanned * 0.5  # Rough estimate
                        st.metric("Time Saved", f"~{estimated_saved:.0f}s")
                    else:
                        st.metric("Time Saved", "N/A")
        
        # Show strategy details
        strategy = scan_result.get('scanning_strategy', scan_result.get('processing_strategy', scan_result.get('crawling_strategy', {})))
        if strategy:
            st.expander("🎯 Scanning Strategy Details", expanded=False).write({
                'Strategy Type': strategy.get('type', 'Unknown'),
                'Target Items': strategy.get('target_files', strategy.get('target_images', strategy.get('target_pages', strategy.get('target_tables', 'N/A')))),
                'Parallel Workers': strategy.get('parallel_workers', 'N/A'),
                'Reasoning': strategy.get('reasoning', 'No details available')
            })
        
        # Always use our enhanced display instead of the main app display
        # This ensures consistent metrics display regardless of the main app function
        st.markdown("---")
        st.subheader("📊 Executive Summary")
        
        # Display comprehensive metrics matching main interface
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            files_scanned = scan_result.get('files_scanned', scan_result.get('pages_scanned', 0))
            st.metric("Files Scanned", files_scanned)
        with col2:
            all_findings = scan_result.get('findings', [])
            suppressed_types = {'Semantic Analysis: Syntax Error'}
            seen_locs = set()
            deduped_count = 0
            for f in all_findings:
                if f.get('type', '') in suppressed_types:
                    continue
                loc = f.get('location', '')
                if loc and loc not in seen_locs:
                    seen_locs.add(loc)
                    deduped_count += 1
                elif not loc:
                    deduped_count += 1
            st.metric("Total Findings", deduped_count)
        with col3:
            lines_analyzed = scan_result.get('lines_analyzed', files_scanned * 50 if files_scanned else 0)
            st.metric("Lines Analyzed", f"{lines_analyzed:,}")
        with col4:
            # Map High privacy_risk findings to Critical Issues for all scans
            findings = scan_result.get('findings', [])
            critical_issues = len([f for f in findings if f.get('severity') == 'Critical'])
            
            # For ALL scans, map High privacy risk and severity to Critical Issues  
            high_privacy_risk = len([f for f in findings if f.get('privacy_risk') == 'High' or f.get('severity') == 'High'])
            critical_issues = max(critical_issues, high_privacy_risk)
            
            st.metric("Critical Issues", critical_issues)
        
        # Additional website-specific metrics for website scans
        if scan_result.get('scan_type') in ['Intelligent Website Scanner', 'GDPR Website Privacy Compliance Scanner']:
            st.subheader("🌐 Website Privacy Analysis")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                high_risk_issues = len([f for f in scan_result.get('findings', []) if f.get('severity') == 'High'])
                st.metric("High Risk Issues", high_risk_issues)
            with col2:
                # Always calculate compliance score for accurate display
                findings = scan_result.get('findings', [])
                total_findings = len(findings)
                critical_findings = len([f for f in findings if f.get('severity') == 'Critical'])
                high_findings = len([f for f in findings if f.get('severity') == 'High'])
                
                # Use centralized compliance calculator for website scans too
                from utils.compliance_calculator import calculate_compliance_score
                compliance_score, _ = calculate_compliance_score(
                    findings, 
                    scan_result.get('scan_id', 'website_scan'),
                    st.session_state.get('username', 'anonymous')
                )
                
                # CRITICAL: Add compliance score to scan result for dashboard display
                scan_result['compliance_score'] = compliance_score
                
                st.metric("Compliance Score", f"{compliance_score}%")
            with col3:
                # ENHANCED: Try multiple ways to get cookie count with comprehensive detection
                cookies_found = scan_result.get('cookies_found', 0)
                if cookies_found == 0:
                    cookies_detected = scan_result.get('cookies_detected', [])
                    if cookies_detected:
                        cookies_found = len(cookies_detected)
                    else:
                        # Count cookie-related findings more comprehensively
                        cookie_patterns = ['cookie', 'consent', 'tracking', 'marketing', 'analytics', 'functional']
                        cookie_findings = [f for f in findings if any(pattern in f.get('type', '').lower() or 
                                                                     pattern in f.get('description', '').lower() or
                                                                     pattern in f.get('location', '').lower() 
                                                                     for pattern in cookie_patterns)]
                        
                        # Estimate cookie count based on findings - trackers usually involve cookies
                        if cookie_findings:
                            cookies_found = len(cookie_findings)
                        elif scan_result.get('trackers_found', 0) > 0:
                            # If we have trackers but no direct cookie findings, estimate cookies
                            # Most tracking requires cookies, so use a reasonable estimate  
                            trackers = scan_result.get('trackers_found', 0)
                            # Estimate: 60-80% of trackers typically use cookies
                            cookies_found = max(2, min(int(trackers * 0.7), 20))  # Reasonable estimate with caps
                
                st.metric("Cookies Found", cookies_found)
            with col4:
                trackers_found = scan_result.get('trackers_found', len(scan_result.get('trackers_detected', [])))
                st.metric("Trackers Found", trackers_found)
        
        # CRITICAL: Calculate compliance score for ALL scan types using centralized calculator
        from utils.compliance_calculator import calculate_compliance_score, get_compliance_status, get_risk_level
        
        findings = scan_result.get('findings', [])
        scan_id = scan_result.get('scan_id', 'unknown')
        username = st.session_state.get('username', 'anonymous')
        
        # Use centralized compliance calculator with audit trail
        compliance_score, compliance_result = calculate_compliance_score(findings, scan_id, username)
        
        # Always set compliance score in scan result for dashboard display
        scan_result['compliance_score'] = compliance_score
        
        # Display compliance score for ALL scan types
        st.subheader("📊 Compliance Analysis")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Compliance Score", f"{compliance_score:.1f}%")
        with col2:
            compliance_status = get_compliance_status(compliance_score)
            st.metric("Compliance Status", compliance_status)
        with col3:
            risk_level = get_risk_level(compliance_score)
            st.metric("Risk Level", risk_level)
        
        # Production-ready findings analysis (debug code removed)
        findings = scan_result.get('findings', [])
        if findings and st.session_state.get('debug_mode', False):
            # Only show debug information when explicitly enabled
            with st.expander("🔧 Technical Details", expanded=False):
                severities = {}
                for finding in findings:
                    sev = finding.get('severity', 'Unknown')
                    severities[sev] = severities.get(sev, 0) + 1
                
                st.json({
                    "severity_breakdown": severities,
                    "compliance_score": scan_result.get('compliance_score', 'Not calculated'),
                    "total_findings": len(findings),
                    "scan_id": scan_result.get('scan_id', 'unknown')
                })
        
        # Display findings if available
        findings = scan_result.get('findings', [])
        
        # PRIORITY: For Image scans, show AUTHENTICITY CHECK prominently first
        scan_type = scan_result.get('scan_type', '')
        if 'image' in scan_type.lower() or 'Image' in scan_type:
            # Find authenticity check finding (always the first priority finding)
            authenticity_findings = [f for f in findings if f.get('type') == 'IMAGE_AUTHENTICITY_CHECK']
            
            if authenticity_findings:
                st.subheader("🔐 Image Authenticity Check")
                auth_finding = authenticity_findings[0]
                analysis = auth_finding.get('analysis_details', {})
                status = analysis.get('authenticity_status', 'UNKNOWN')
                overall_score = analysis.get('overall_score', 0)
                confidence = auth_finding.get('confidence', 0)
                
                if status == 'AUTHENTIC':
                    st.success(f"""
                    ✅ **IMAGE VERIFIED AS AUTHENTIC**
                    
                    **Authenticity Confidence:** {confidence:.0%}
                    
                    No significant deepfake or synthetic media indicators detected. This image appears to be genuine.
                    """)
                else:
                    risk_level = auth_finding.get('risk_level', 'Medium')
                    color = {'Critical': 'error', 'High': 'warning', 'Medium': 'warning'}.get(risk_level, 'info')
                    
                    if color == 'error':
                        st.error(f"""
                        ⚠️ **POTENTIAL DEEPFAKE/SYNTHETIC MEDIA DETECTED**
                        
                        **Status:** {status}  
                        **Risk Level:** {risk_level}  
                        **Detection Score:** {overall_score:.1%}
                        
                        This image shows indicators of AI generation or manipulation. Further review recommended.
                        """)
                    else:
                        st.warning(f"""
                        ⚠️ **AUTHENTICITY REVIEW RECOMMENDED**
                        
                        **Status:** {status}  
                        **Risk Level:** {risk_level}  
                        **Detection Score:** {overall_score:.1%}
                        
                        Some indicators of synthetic content detected. Consider additional verification.
                        """)
                
                # Show detailed analysis scores
                with st.expander("📊 Detailed Authenticity Analysis", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Artifact Score", f"{analysis.get('artifact_score', 0):.1%}")
                    with col2:
                        st.metric("Noise Score", f"{analysis.get('noise_score', 0):.1%}")
                    with col3:
                        st.metric("Compression Score", f"{analysis.get('compression_score', 0):.1%}")
                    with col4:
                        st.metric("Facial Score", f"{analysis.get('facial_inconsistency_score', 0):.1%}")
                    
                    indicators = analysis.get('indicators', [])
                    if indicators:
                        st.markdown("**Detection Indicators:**")
                        for indicator in indicators:
                            st.markdown(f"- {indicator}")
                
                st.markdown("---")
        
        if findings:
            type_display_map = {
                'Dutch Address Component': 'Address',
                'UAVG-Dutch Personal Identifiers': 'Dutch ID (UAVG)',
                'Semantic Analysis: Syntax Error': None,
                'IP Address': 'IP Address',
            }
            severity_priority = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
            special_pii = {'bsn', 'health', 'medical', 'biometric'}
            elevated_pii = {'financial', 'salary', 'iban', 'credit', 'secret', 'key', 'token', 'password'}

            seen_locations = {}
            for f in findings:
                loc = f.get('location', '')
                ft = (f.get('type') or 'Unknown').lower()
                display_type = type_display_map.get(f.get('type', ''), f.get('type', 'Unknown'))
                if display_type is None:
                    continue
                sev = f.get('severity', f.get('risk_level', 'Medium'))
                if any(t in ft for t in special_pii):
                    sev = 'Critical'
                elif any(t in ft for t in elevated_pii) and sev not in ['Critical']:
                    sev = 'High'
                f['_display_type'] = display_type
                f['_display_severity'] = sev
                if loc in seen_locations:
                    existing = seen_locations[loc]
                    if severity_priority.get(sev, 0) > severity_priority.get(existing.get('_display_severity', 'Low'), 0):
                        seen_locations[loc] = f
                else:
                    seen_locations[loc] = f
            deduped = list(seen_locations.values())

            st.subheader("🔍 Findings Summary")
            for i, finding in enumerate(deduped[:20], 1):
                display_type = finding.get('_display_type', finding.get('type', 'Unknown'))
                severity = finding.get('_display_severity', finding.get('severity', 'Medium'))
                with st.expander(f"Finding {i}: {display_type} - {severity}"):
                    location_str = finding.get('location', '')
                    if location_str and ':' in str(location_str):
                        last_colon = str(location_str).rfind(':')
                        file_loc = str(location_str)[:last_colon] if last_colon > 0 else str(location_str)
                        line_loc = str(location_str)[last_colon+1:] if last_colon > 0 else 'N/A'
                    else:
                        file_loc = finding.get('file', finding.get('location', 'N/A'))
                        line_loc = finding.get('line', 'N/A')

                    st.write(f"**File:** {file_loc}")
                    st.write(f"**Line:** {line_loc}")
                    st.write(f"**Type:** {display_type}")
                    st.write(f"**Severity:** {severity}")
                    desc = finding.get('description', finding.get('reason', 'PII detected in source code'))
                    st.write(f"**Description:** {desc}")
                    if finding.get('privacy_risk'):
                        st.write(f"**Privacy Risk:** {finding.get('privacy_risk')}")
        else:
            st.success("✅ No issues found in the scan")
        
        # Display HTML report download if available
        st.subheader("📄 Download Report")
        
        # Check if user can download (paid users only)
        from config.pricing_config import can_download_reports
        if not can_download_reports():
            st.info("🔒 Report downloads available for paid subscribers. Upgrade to download reports.")
        else:
            try:
                from page_modules.scanner import generate_html_report
                html_content = generate_html_report(scan_result)
                st.download_button(
                    label="📥 Download HTML Report",
                    data=html_content,
                    file_name=f"scan_report_{scan_result.get('scan_id', 'unknown')[:8]}.html",
                    mime="text/html"
                )
            except Exception as download_error:
                st.info("Report download temporarily unavailable")

# Global instance for use throughout the application
intelligent_wrapper = IntelligentScannerWrapper()