"""
Intelligent Repository Scanner Wrapper

Provides intelligent scanning capabilities for code repositories.
Wraps the standard repo scanner with enhanced features.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class IntelligentRepoScanner:
    """Intelligent wrapper for repository scanning with enhanced capabilities."""
    
    def __init__(self, code_scanner):
        """
        Initialize intelligent repository scanner.
        
        Args:
            code_scanner: Base code scanner instance to use
        """
        self.code_scanner = code_scanner
        logger.info("Initialized IntelligentRepoScanner with code scanner integration")
    
    def scan(self, target, scan_mode="smart", max_files: Optional[int] = 200, **kwargs):
        """
        Scan a repository with intelligent processing.
        
        Args:
            target: Repository URL or path to scan
            scan_mode: Scanning strategy (smart, fast, deep)
            max_files: Maximum number of files to process
            **kwargs: Additional scanning parameters
            
        Returns:
            Dictionary with scan results
        """
        logger.info(f"Starting intelligent repository scan: {target} (mode: {scan_mode})")
        
        try:
            # Use the repo scanner for repository scanning (handles git clone + code scan)
            if hasattr(self.code_scanner, 'scan_repository'):
                branch = kwargs.get('branch')
                auth_token = kwargs.get('auth_token')
                progress_callback = kwargs.get('progress_callback')
                results = self.code_scanner.scan_repository(
                    target, 
                    branch=branch, 
                    auth_token=auth_token,
                    progress_callback=progress_callback
                )
            elif hasattr(self.code_scanner, 'scan_directory'):
                # Fallback to directory scan for local paths
                results = self.code_scanner.scan_directory(target, **kwargs)
            else:
                # Last resort fallback
                logger.warning(f"Scanner does not have scan_repository or scan_directory method")
                results = {
                    "findings": [],
                    "scan_mode": scan_mode,
                    "target": target,
                    "error": "No suitable scan method available"
                }
            
            logger.info(f"Repository scan completed with {len(results.get('findings', []))} findings")
            return results
            
        except Exception as e:
            logger.error(f"Repository scan failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "error": str(e),
                "findings": [],
                "scan_mode": scan_mode
            }
    
    def scan_repository_intelligent(self, repo_url, branch=None, scan_mode="smart", 
                                   max_files=None, progress_callback=None):
        """
        Intelligent repository scanning method called by IntelligentScannerManager.
        
        Args:
            repo_url: Repository URL to scan
            branch: Git branch to scan (optional)
            scan_mode: Scanning strategy (smart, fast, deep)
            max_files: Maximum files to process
            progress_callback: Progress reporting callback
            
        Returns:
            Dictionary with scan results
        """
        return self.scan(repo_url, scan_mode=scan_mode, max_files=max_files, 
                        branch=branch, progress_callback=progress_callback)
