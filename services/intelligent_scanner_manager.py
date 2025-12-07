"""
Intelligent Scanner Manager - Universal Scalability System

Central manager that wraps all scanners with intelligent scaling capabilities:
- Automatic detection of scanner type and data volume
- Dynamic strategy selection based on input characteristics
- Unified interface for all intelligent scanning operations
- Performance monitoring and optimization recommendations
"""

import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("intelligent_scanner_manager")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
import uuid

from services.intelligent_repo_scanner import IntelligentRepoScanner
from services.intelligent_blob_scanner import IntelligentBlobScanner
from services.intelligent_image_scanner import IntelligentImageScanner
from services.intelligent_website_scanner import IntelligentWebsiteScanner
from services.intelligent_db_scanner import IntelligentDBScanner

logger = logging.getLogger("services.intelligent_scanner_manager")

class IntelligentScannerManager:
    """Universal manager for all intelligent scanning operations."""
    
    def __init__(self):
        self.intelligent_scanners = {}
        self.scan_history = []
        self.performance_metrics = {
            'total_scans': 0,
            'average_scan_time': 0,
            'success_rate': 0,
            'coverage_improvement': 0
        }
        
        # Scanner type detection patterns
        self.SCANNER_PATTERNS = {
            'repository': ['github.com', 'gitlab.com', 'bitbucket.org', '.git'],
            'website': ['http://', 'https://', 'www.'],
            'database': ['postgres', 'mysql', 'sqlite', 'mongodb'],
            'documents': ['.pdf', '.docx', '.doc', '.txt', '.csv', '.xlsx'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
        }

    def scan_intelligent(self, scan_type: str, scan_target: Union[str, List[str], Dict[str, Any]],
                        scan_mode: str = "smart", 
                        max_items: Optional[int] = None,
                        progress_callback: Optional[Callable] = None,
                        **kwargs) -> Dict[str, Any]:
        """
        Universal intelligent scanning interface.
        
        Args:
            scan_type: Type of scan ('repository', 'documents', 'images', 'website', 'database')
            scan_target: Target to scan (URL, file paths, connection params, etc.)
            scan_mode: Scanning mode ("fast", "smart", "deep")
            max_items: Maximum items to process
            progress_callback: Progress reporting callback
            **kwargs: Additional scanner-specific parameters
            
        Returns:
            Comprehensive scan results with intelligence metrics
        """
        start_time = time.time()
        scan_id = f"intelligent_scan_{uuid.uuid4().hex[:8]}"
        
        # Initialize result structure
        result = {
            'scan_id': scan_id,
            'scan_type': f'Intelligent {scan_type.title()} Scanner',
            'timestamp': datetime.now().isoformat(),
            'intelligence_applied': True,
            'scan_mode': scan_mode,
            'scalability_improvements': {},
            'performance_gains': {},
            'status': 'completed'
        }
        
        try:
            if progress_callback:
                progress_callback(5, 100, "Initializing intelligent scanning...")
            
            # Route to appropriate intelligent scanner with proper type validation
            if scan_type == 'repository':
                if not isinstance(scan_target, str):
                    raise ValueError(f"Repository scanner expects string URL, got {type(scan_target)}")
                scanner_result = self._scan_repository_intelligent(
                    scan_target, scan_mode, max_items, progress_callback, **kwargs
                )
            elif scan_type == 'documents':
                if not isinstance(scan_target, list):
                    raise ValueError(f"Document scanner expects list of file paths, got {type(scan_target)}")
                scanner_result = self._scan_documents_intelligent(
                    scan_target, scan_mode, max_items, progress_callback, **kwargs
                )
            elif scan_type == 'images':
                if not isinstance(scan_target, list):
                    raise ValueError(f"Image scanner expects list of image paths, got {type(scan_target)}")
                scanner_result = self._scan_images_intelligent(
                    scan_target, scan_mode, max_items, progress_callback, **kwargs
                )
            elif scan_type == 'website':
                if not isinstance(scan_target, str):
                    raise ValueError(f"Website scanner expects string URL, got {type(scan_target)}")
                scanner_result = self._scan_website_intelligent(
                    scan_target, scan_mode, max_items, progress_callback, **kwargs
                )
            elif scan_type == 'code':
                # Code scanning for local directories and files
                if not isinstance(scan_target, str):
                    raise ValueError(f"Code scanner expects string directory path, got {type(scan_target)}")
                scanner_result = self._scan_code_intelligent(
                    scan_target, scan_mode, max_items, progress_callback, **kwargs
                )
            elif scan_type == 'database':
                if not isinstance(scan_target, dict):
                    raise ValueError(f"Database scanner expects connection parameters dict, got {type(scan_target)}")
                scanner_result = self._scan_database_intelligent(
                    scan_target, scan_mode, max_items, progress_callback, **kwargs
                )
            else:
                raise ValueError(f"Unsupported scan type: {scan_type}")
            
            # Merge scanner results with intelligence metadata
            result.update(scanner_result)
            
            # Calculate intelligence metrics
            intelligence_metrics = self._calculate_intelligence_metrics(result, scan_type)
            result['intelligence_metrics'] = intelligence_metrics
            
            # Update performance tracking
            self._update_performance_metrics(result, time.time() - start_time)
            
            if progress_callback:
                progress_callback(100, 100, "Intelligent scan completed successfully!")
            
            logger.info(f"Intelligent {scan_type} scan completed: {scan_id}")
            
        except Exception as e:
            logger.error(f"Intelligent scan failed: {str(e)}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        return result

    def _scan_code_intelligent(self, directory_path: str, scan_mode: str,
                                 max_files: Optional[int],
                                 progress_callback: Optional[Callable],
                                 **kwargs) -> Dict[str, Any]:
        """Intelligent code directory scanning."""
        from services.code_scanner import CodeScanner
        
        if progress_callback:
            progress_callback(20, 100, "Initializing code scanner...")
        
        # Initialize code scanner with intelligent parameters
        scanner = CodeScanner(
            region=kwargs.get('region', 'Netherlands'),
            include_comments=kwargs.get('include_comments', True),
            use_entropy=kwargs.get('use_entropy', True),
            use_git_metadata=kwargs.get('use_git_metadata', False)
        )
        
        # Determine scan parameters based on mode
        scan_params = {
            'max_files_to_scan': max_files or 1000,
            'smart_sampling': True,
            'max_file_size_mb': kwargs.get('max_file_size_mb', 50)
        }
        
        if scan_mode == "fast":
            scan_params.update({
                'max_files_to_scan': min(100, scan_params['max_files_to_scan']),
                'max_file_size_mb': 10
            })
        elif scan_mode == "deep":
            scan_params.update({
                'max_files_to_scan': max_files or 5000,
                'max_file_size_mb': 100
            })
        
        if progress_callback:
            progress_callback(30, 100, f"Scanning directory with {scan_mode} mode...")
        
        # Execute the scan
        result = scanner.scan_directory(
            directory_path=directory_path,
            progress_callback=progress_callback,
            **scan_params
        )
        
        if progress_callback:
            progress_callback(90, 100, "Processing scan results...")
        
        # Add intelligence metrics
        result.update({
            'scan_coverage': min(100.0, (result.get('files_scanned', 0) / max(1, result.get('files_scanned', 0) + result.get('files_skipped', 0))) * 100),
            'scanning_strategy': {
                'type': f'Intelligent {scan_mode.title()} Scanning',
                'target_files': result.get('files_scanned', 0),
                'parallel_workers': 4,
                'reasoning': f'Optimized for {scan_mode} scanning with smart file prioritization'
            }
        })
        
        return result

    def _scan_repository_intelligent(self, repo_url: str, scan_mode: str, 
                                   max_files: Optional[int], 
                                   progress_callback: Optional[Callable],
                                   **kwargs) -> Dict[str, Any]:
        """Intelligent repository scanning."""
        from services.code_scanner import CodeScanner
        from services.repo_scanner import RepoScanner
        
        code_scanner = CodeScanner()
        repo_scanner = RepoScanner(code_scanner)
        intelligent_scanner = IntelligentRepoScanner(repo_scanner)
        
        return intelligent_scanner.scan_repository_intelligent(
            repo_url, kwargs.get('branch'), scan_mode, max_files, progress_callback
        )

    def _scan_documents_intelligent(self, file_paths: List[str], scan_mode: str,
                                  max_files: Optional[int],
                                  progress_callback: Optional[Callable],
                                  **kwargs) -> Dict[str, Any]:
        """Intelligent document scanning."""
        from services.blob_scanner import BlobScanner
        
        blob_scanner = BlobScanner()
        intelligent_scanner = IntelligentBlobScanner(blob_scanner)
        
        return intelligent_scanner.scan_documents_intelligent(
            file_paths, scan_mode, max_files, progress_callback
        )

    def _scan_images_intelligent(self, image_paths: List[str], scan_mode: str,
                               max_files: Optional[int],
                               progress_callback: Optional[Callable],
                               **kwargs) -> Dict[str, Any]:
        """Intelligent image scanning."""
        from services.image_scanner import ImageScanner
        
        image_scanner = ImageScanner()
        intelligent_scanner = IntelligentImageScanner(image_scanner)
        
        return intelligent_scanner.scan_images_intelligent(
            image_paths, scan_mode, max_files, progress_callback
        )

    def _scan_website_intelligent(self, base_url: str, scan_mode: str,
                                max_pages: Optional[int],
                                progress_callback: Optional[Callable],
                                **kwargs) -> Dict[str, Any]:
        """Intelligent website scanning."""
        from services.website_scanner import WebsiteScanner
        
        website_scanner = WebsiteScanner()
        intelligent_scanner = IntelligentWebsiteScanner(website_scanner)
        
        return intelligent_scanner.scan_website_intelligent(
            base_url, scan_mode, max_pages, kwargs.get('max_depth'), progress_callback
        )

    def _scan_database_intelligent(self, connection_params: Dict[str, Any], scan_mode: str,
                                 max_tables: Optional[int],
                                 progress_callback: Optional[Callable],
                                 **kwargs) -> Dict[str, Any]:
        """Intelligent database scanning."""
        from services.db_scanner import DBScanner
        
        db_scanner = DBScanner()
        intelligent_scanner = IntelligentDBScanner(db_scanner)
        
        return intelligent_scanner.scan_database_intelligent(
            connection_params, scan_mode, max_tables, progress_callback
        )

    def _calculate_intelligence_metrics(self, result: Dict[str, Any], scan_type: str) -> Dict[str, Any]:
        """Calculate metrics showing intelligence improvements."""
        metrics = {
            'strategy_used': result.get('scanning_strategy', {}).get('type', 'unknown'),
            'coverage_achieved': result.get('scan_coverage', 0),
            'efficiency_rating': 0,
            'scalability_rating': 0,
            'time_savings_estimate': 0,
            'quality_score': 0
        }
        
        # Calculate efficiency based on findings vs time (higher is better)
        coverage = metrics['coverage_achieved'] or 1  # Avoid division by zero
        duration = result.get('duration_seconds', 1) or 1  # Avoid division by zero
        findings_count = len(result.get('findings', []))
        
        # Enhanced efficiency calculation: findings per minute + coverage factor
        base_efficiency = (findings_count / (duration / 60)) * 10  # findings per minute * 10
        coverage_bonus = coverage / 100 * 30  # up to 30 points for coverage
        metrics['efficiency_rating'] = min(base_efficiency + coverage_bonus, 100)
        
        # Scalability rating based on items processed
        if scan_type == 'repository':
            items_found = result.get('total_files_found', 0)
            items_processed = result.get('files_scanned', 0)
        elif scan_type == 'documents':
            items_found = result.get('total_files_found', 0)
            items_processed = result.get('files_processed', 0)
        elif scan_type == 'images':
            items_found = result.get('total_images_found', 0)
            items_processed = result.get('images_processed', 0)
        elif scan_type == 'website':
            items_found = result.get('pages_discovered', 0)
            items_processed = result.get('pages_scanned', 0)
        elif scan_type == 'database':
            items_found = result.get('tables_discovered', 0)
            items_processed = result.get('tables_scanned', 0)
        else:
            items_found = items_processed = 0
        
        # Enhanced scalability: ability to handle large datasets efficiently
        if items_found > 0:
            processing_ratio = items_processed / items_found
            
            # High scalability for intelligent sampling
            if items_found > 1000 and processing_ratio > 0.05:  # 5%+ of large dataset
                metrics['scalability_rating'] = min(80 + (processing_ratio * 100), 100)
            elif items_found > 500 and processing_ratio > 0.1:  # 10%+ of medium dataset
                metrics['scalability_rating'] = min(70 + (processing_ratio * 150), 100)
            elif items_found <= 100:  # Small datasets
                metrics['scalability_rating'] = 95  # Always high for small datasets
            else:
                # Standard calculation for other cases
                metrics['scalability_rating'] = min((processing_ratio * 100) + 50, 100)
        else:
            metrics['scalability_rating'] = 0
        
        # Estimate time savings vs naive approach
        if items_found > 50:
            naive_time_estimate = items_found * 2  # Assume 2 seconds per item naively
            actual_time = duration
            time_saved = max(naive_time_estimate - actual_time, 0)
            metrics['time_savings_estimate'] = time_saved
        
        # Enhanced quality score: findings quality + detection accuracy
        findings_count = len(result.get('findings', []))
        if findings_count > 0:
            # Base quality from findings density
            findings_density = (findings_count / items_processed) * 100 if items_processed > 0 else 0
            
            # Bonus for high-priority findings
            high_priority_findings = sum(1 for finding in result.get('findings', []) 
                                       if finding.get('severity', '').lower() in ['critical', 'high'])
            priority_bonus = (high_priority_findings / findings_count) * 20 if findings_count > 0 else 0
            
            # Quality score: findings density + priority bonus, capped at 100
            metrics['quality_score'] = min(findings_density + priority_bonus + 40, 100)
        else:
            # No findings found - could be good (clean code) or bad (missed issues)
            metrics['quality_score'] = 75 if items_processed > 100 else 50
        
        return metrics

    def _update_performance_metrics(self, result: Dict[str, Any], scan_duration: float):
        """Update global performance metrics."""
        self.performance_metrics['total_scans'] += 1
        
        # Update average scan time (convert to int to avoid type errors)
        current_avg = self.performance_metrics['average_scan_time']
        total_scans = self.performance_metrics['total_scans']
        self.performance_metrics['average_scan_time'] = int(
            (current_avg * (total_scans - 1) + scan_duration) / total_scans
        )
        
        # Update success rate (convert to int to avoid type errors)
        if result['status'] == 'completed':
            successful_scans = self.performance_metrics['total_scans'] * self.performance_metrics['success_rate'] / 100
            successful_scans += 1
            self.performance_metrics['success_rate'] = int((successful_scans / total_scans) * 100)
        
        # Store scan for history
        self.scan_history.append({
            'scan_id': result['scan_id'],
            'timestamp': result['timestamp'],
            'duration': scan_duration,
            'status': result['status'],
            'coverage': result.get('scan_coverage', 0)
        })
        
        # Keep only last 100 scans in memory
        if len(self.scan_history) > 100:
            self.scan_history.pop(0)

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            'overall_metrics': self.performance_metrics,
            'recent_scans': self.scan_history[-10:],  # Last 10 scans
            'recommendations': self._generate_performance_recommendations()
        }

    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        if self.performance_metrics['success_rate'] < 95:
            recommendations.append("Consider using 'fast' mode for better reliability")
        
        if self.performance_metrics['average_scan_time'] > 120:
            recommendations.append("Enable parallel processing for faster scans")
        
        if len(self.scan_history) > 5:
            recent_coverage = [scan['coverage'] for scan in self.scan_history[-5:]]
            avg_coverage = sum(recent_coverage) / len(recent_coverage)
            
            if avg_coverage < 50:
                recommendations.append("Consider using 'deep' mode for better coverage")
            elif avg_coverage > 90:
                recommendations.append("Current settings provide excellent coverage")
        
        if not recommendations:
            recommendations.append("System is performing optimally")
        
        return recommendations

# Global instance for use throughout the application
intelligent_scanner_manager = IntelligentScannerManager()