"""
Repository Scanner module for cloning and scanning Git repositories.

This module provides functionality to clone Git repositories from URLs (GitHub, GitLab, Bitbucket)
and scan the codebase for PII and sensitive information using the CodeScanner.
"""

import os
import re
import shutil
import tempfile
import subprocess
import logging
import fnmatch

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("repo_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import uuid

from services.code_scanner import CodeScanner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class RepoScanner:
    """
    A scanner that clones and analyzes Git repositories for PII and sensitive information.
    """
    
    def __init__(self, code_scanner: CodeScanner):
        """
        Initialize the repository scanner.
        
        Args:
            code_scanner: An instance of CodeScanner to use for scanning files
        """
        self.code_scanner = code_scanner
        # Enable fast_mode for repo scanning (skip advanced analyzers)
        self.code_scanner.fast_mode = True
        # Expanded list to include more GitHub domains and variations
        self.supported_platforms = [
            'github.com', 
            'gitlab.com', 
            'bitbucket.org', 
            'dev.azure.com',
            'github.io',
            'githubusercontent.com',
            'raw.githubusercontent.com'
        ]
        self.temp_dirs = []
        
    def __del__(self):
        """
        Cleanup temporary directories on object destruction.
        """
        self._cleanup_temp_dirs()
        
    def _cleanup_temp_dirs(self):
        """
        Clean up all temporary directories created during scanning.
        """
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory {temp_dir}: {str(e)}")
    
    def normalize_repo_url(self, repo_url: str) -> str:
        """
        Normalize a repository URL to a valid Git clone URL.
        Converts GitHub/GitLab tree/blob URLs to proper clone URLs.
        
        Args:
            repo_url: Raw repository URL (may include /tree/, /blob/, etc.)
            
        Returns:
            Normalized URL suitable for git clone
        """
        if not repo_url:
            return repo_url
            
        # Strip whitespace
        repo_url = repo_url.strip()
        
        # Remove trailing slashes
        repo_url = repo_url.rstrip('/')
        
        # Handle GitHub/GitLab/Bitbucket tree and blob URLs
        # Pattern: https://github.com/owner/repo/tree/branch/path
        #       -> https://github.com/owner/repo
        tree_blob_pattern = r'^(https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org)/[^/]+/[^/]+)/(?:tree|blob|raw)/.*$'
        match = re.match(tree_blob_pattern, repo_url)
        if match:
            normalized = match.group(1)
            logger.info(f"Normalized repo URL: {repo_url} -> {normalized}")
            return normalized
        
        # Handle URLs that already end with .git
        if repo_url.endswith('.git'):
            return repo_url
        
        return repo_url
    
    def is_valid_repo_url(self, repo_url: str) -> bool:
        """
        Check if a repository URL is valid.
        
        Args:
            repo_url: URL of the Git repository
            
        Returns:
            True if the URL seems to be a valid Git repository URL, False otherwise
        """
        # Handle empty URL
        if not repo_url or repo_url.strip() == "":
            return False
            
        # Normalize the URL first
        repo_url = self.normalize_repo_url(repo_url)
            
        # Basic URL validation - allow URLs with repository paths (like /tree/master/.github)
        # More permissive pattern - just ensure it's an http(s) URL with at least org/repo pattern
        url_pattern = r'^https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/[^/]+/[^/]+'
        match = re.match(url_pattern, repo_url)
        
        if not match:
            logger.warning(f"URL pattern validation failed for: {repo_url}")
            return False
        
        # Check if the domain is a supported Git platform
        domain = match.group(1)
        valid_domain = any(platform in domain for platform in self.supported_platforms)
        
        if not valid_domain:
            logger.warning(f"Domain validation failed for: {domain} in URL: {repo_url}")
            
        return valid_domain
    
    def _prepare_auth_for_clone(self, repo_url: str, auth_token: Optional[str] = None) -> str:
        """
        Prepare repository URL with authentication if needed.
        
        Args:
            repo_url: Original repository URL
            auth_token: Authentication token for private repositories
            
        Returns:
            Repository URL with authentication included if needed
        """
        if not auth_token:
            return repo_url
            
        # Add auth token to URL based on platform
        if 'github.com' in repo_url:
            # For GitHub
            parts = repo_url.split('https://')
            return f'https://{auth_token}:x-oauth-basic@{parts[1]}'
        elif 'gitlab.com' in repo_url:
            # For GitLab
            parts = repo_url.split('https://')
            return f'https://oauth2:{auth_token}@{parts[1]}'
        elif 'bitbucket.org' in repo_url:
            # For Bitbucket
            parts = repo_url.split('https://')
            return f'https://x-token-auth:{auth_token}@{parts[1]}'
        elif 'dev.azure.com' in repo_url:
            # For Azure DevOps
            parts = repo_url.split('https://')
            return f'https://{auth_token}@{parts[1]}'
        
        return repo_url
    
    def clone_repository(self, repo_url: str, branch: Optional[str] = None, 
                         auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Clone a Git repository to a temporary directory.
        
        Args:
            repo_url: URL of the Git repository
            branch: Branch to clone (default: repository default branch)
            auth_token: Authentication token for private repositories
            
        Returns:
            Dictionary with cloning results and local path
        """
        start_time = time.time()
        
        # Normalize the URL first (convert tree/blob URLs to proper clone URLs)
        repo_url = self.normalize_repo_url(repo_url)
        
        if not self.is_valid_repo_url(repo_url):
            return {
                'status': 'error',
                'message': 'Invalid repository URL format',
                'repo_path': None,
                'time_ms': int((time.time() - start_time) * 1000)
            }
        
        # Create a unique temporary directory
        temp_dir = os.path.join(tempfile.gettempdir(), f"repo_scan_{uuid.uuid4().hex}")
        self.temp_dirs.append(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Prepare authentication if needed
        clone_url = self._prepare_auth_for_clone(repo_url, auth_token)
        
        # Optimize the clone operation
        success = False
        error_msg = ""
        
        # Even more aggressive optimization for very large repositories
        clone_cmd = ['git', 'clone', '--depth', '1', '--filter=blob:none', '--single-branch', '--no-tags']
        
        # Add branch specification if provided
        if branch:
            clone_cmd.extend(['--branch', branch])
            
        # Add the repository URL and target directory
        clone_cmd.extend([clone_url, temp_dir])
        
        try:
            # Execute optimized git clone command with shorter timeout
            logger.info(f"Fast cloning repository from {repo_url}" + (f" (branch: {branch})" if branch else " (default branch)"))
            
            # Set environment to disable credential prompts (prevents hanging on auth)
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'
            env['GIT_ASKPASS'] = 'echo'
            
            # Reduce timeout for faster feedback
            result = subprocess.run(
                clone_cmd, 
                capture_output=True, 
                text=True,
                timeout=300,  # 5 min timeout (reduced from 10)
                env=env
            )
            
            if result.returncode == 0:
                success = True
            else:
                error_msg = result.stderr
                
                # If branch-specific clone failed, try default branch
                if branch:
                    logger.warning(f"Failed to clone branch '{branch}', will try default branch instead.")
                    
                    # Clean up for next attempt
                    shutil.rmtree(temp_dir)
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Try without branch specification
                    default_cmd = ['git', 'clone', '--depth', '1', '--filter=blob:none', clone_url, temp_dir]
                    
                    try:
                        logger.info(f"Fast cloning repository from {repo_url} (default branch)")
                        result = subprocess.run(
                            default_cmd, 
                            capture_output=True, 
                            text=True,
                            timeout=300,  # 5 min timeout
                            env=env  # Use same env to disable credential prompts
                        )
                        
                        if result.returncode == 0:
                            success = True
                        else:
                            error_msg = result.stderr
                    except Exception as e:
                        error_msg = str(e)
                
                if not success:
                    # Remove auth token from error message if present
                    if auth_token:
                        error_msg = error_msg.replace(auth_token, '********')
                        
                    logger.error(f"Git clone failed: {error_msg}")
                    return {
                        'status': 'error',
                        'message': f'Failed to clone repository: {error_msg}',
                        'repo_path': None,
                        'time_ms': int((time.time() - start_time) * 1000)
                    }
                
        except subprocess.TimeoutExpired:
            logger.error("Git clone operation timed out")
            return {
                'status': 'error',
                'message': 'Git clone operation timed out after 5 minutes',
                'repo_path': None,
                'time_ms': int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error cloning repository: {str(e)}',
                'repo_path': None,
                'time_ms': int((time.time() - start_time) * 1000)
            }
        
        # Verify the clone was successful
        if not os.listdir(temp_dir) or not os.path.exists(os.path.join(temp_dir, '.git')):
            logger.error("Git clone completed but repository appears empty")
            return {
                'status': 'error',
                'message': 'Repository appears to be empty or not a Git repository',
                'repo_path': None,
                'time_ms': int((time.time() - start_time) * 1000)
            }
            
        # Check repository size and limit scanning for very large repositories
        repo_size_bytes = self._get_repo_size(temp_dir)
        repo_size_mb = repo_size_bytes / (1024 * 1024)
        
        # Flag very large repositories (over 500MB)
        is_large_repo = repo_size_mb > 500
        
        if is_large_repo:
            logger.warning(f"Very large repository detected: {repo_size_mb:.2f} MB. Enabling optimized scanning.")
            
            # For very large repos, we'll limit scanning to specific directories
            # Create a .scanignore file to help the scanner skip irrelevant paths
            try:
                with open(os.path.join(temp_dir, '.scanignore'), 'w') as f:
                    # Common directories to ignore in large repos
                    f.write("\n".join([
                        "node_modules/",
                        ".git/",
                        "dist/",
                        "build/",
                        "out/",
                        "vendor/",
                        "*.min.js",
                        "*.min.css",
                        "*.svg",
                        "*.png",
                        "*.jpg",
                        "*.jpeg",
                        "*.gif",
                        "*.ico",
                        "*.woff",
                        "*.ttf",
                        "*.eot",
                        "*.mp3",
                        "*.mp4",
                        "*.avi",
                        "*.pdf",
                        "*.zip",
                        "*.tar",
                        "*.gz",
                        "*.jar",
                        "*.war",
                        "*.class",
                        "*.o",
                        "*.so",
                        "*.dll",
                        "*.exe",
                        "*.bin",
                        "__pycache__/",
                        ".vscode/",
                        ".idea/",
                        # Large repos specific patterns
                        "tests/fixtures/",
                        "test/fixtures/",
                        "spec/fixtures/",
                        "fixtures/",
                        "examples/",
                        "samples/",
                        "docs/",
                        "documentation/",
                        "locales/",
                        "i18n/",
                        "translations/"
                    ]))
            except Exception as e:
                logger.warning(f"Failed to create .scanignore file: {str(e)}")
                
        return {
            'status': 'success',
            'message': 'Repository cloned successfully',
            'repo_path': temp_dir,
            'time_ms': int((time.time() - start_time) * 1000),
            'is_large_repo': is_large_repo,
            'repo_size_mb': repo_size_mb
        }
    
    def _get_repo_size(self, repo_path: str) -> int:
        """
        Get the size of a repository directory in bytes.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        try:
            # We'll use du command for efficiency on large repos
            try:
                result = subprocess.run(
                    ['du', '-sb', repo_path], 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Parse the output - first part is the size in bytes
                    parts = result.stdout.strip().split()
                    if parts and parts[0].isdigit():
                        return int(parts[0])
            except:
                # Fall back to manual calculation if du command fails
                pass
                
            # Manual calculation (slower but more portable)
            for dirpath, dirnames, filenames in os.walk(repo_path):
                # Skip .git directory to speed up calculation
                if '.git' in dirnames:
                    dirnames.remove('.git')
                    
                # Add the size of all files in this directory
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        # Skip files that can't be accessed
                        pass
        except Exception as e:
            logger.warning(f"Error calculating repository size: {str(e)}")
            # Return a default size (100MB) if calculation fails
            return 100 * 1024 * 1024
            
        return total_size
            
    # Get repository metadata
    def _get_repo_metadata(self, repo_path: str) -> Dict[str, Any]:
        
        # Get the actual branch name that was cloned
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=temp_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                actual_branch = result.stdout.strip()
                repo_info['active_branch'] = actual_branch
        except Exception:
            # If we can't get the branch name, that's okay
            pass
            
        logger.info(f"Repository cloned successfully to {temp_dir}")
        return {
            'status': 'success',
            'message': 'Repository cloned successfully',
            'repo_path': temp_dir,
            'metadata': repo_info,
            'time_ms': int((time.time() - start_time) * 1000)
        }
    
    def _get_repo_metadata(self, repo_path: str) -> Dict[str, Any]:
        """
        Get Git repository metadata.
        
        Args:
            repo_path: Path to the cloned repository
            
        Returns:
            Dictionary with repository metadata
        """
        metadata = {
            'commit_count': 0,
            'latest_commit': '',
            'latest_commit_date': '',
            'branches': [],
            'authors': [],
            'file_count': 0,
            'repo_size_bytes': 0
        }
        
        try:
            # Get latest commit info
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%H|%an|%ae|%ad|%s'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                parts = result.stdout.split('|')
                if len(parts) >= 5:
                    metadata['latest_commit'] = parts[0]
                    metadata['latest_commit_author'] = parts[1]
                    metadata['latest_commit_email'] = parts[2]
                    metadata['latest_commit_date'] = parts[3]
                    metadata['latest_commit_message'] = parts[4]
            
            # Count total files (excluding .git directory)
            file_count = 0
            repo_size = 0
            
            for root, _, files in os.walk(repo_path):
                if '.git' in root:
                    continue
                for file in files:
                    file_count += 1
                    try:
                        file_path = os.path.join(root, file)
                        repo_size += os.path.getsize(file_path)
                    except:
                        pass
                        
            metadata['file_count'] = file_count
            metadata['repo_size_bytes'] = repo_size
            
            # Get other metadata as needed
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting repository metadata: {str(e)}")
            return metadata
    
    def scan_repository(self, repo_url: str, branch: Optional[str] = None, 
                        auth_token: Optional[str] = None,
                        progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Clone a repository and scan it for PII and sensitive information.
        
        Args:
            repo_url: URL of the Git repository
            branch: Branch to clone (default: repository default branch)
            auth_token: Authentication token for private repositories
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with scan results
        """
        start_time = time.time()
        
        # First, clone the repository
        clone_result = self.clone_repository(repo_url, branch, auth_token)
        
        if clone_result['status'] != 'success':
            return {
                'scan_type': 'repository',
                'status': 'error',
                'message': clone_result['message'],
                'repo_url': repo_url,
                'branch': branch or 'default',
                'scan_time': datetime.now().isoformat(),
                'process_time_seconds': time.time() - start_time,
                'findings': []
            }
        
        repo_path = clone_result['repo_path']
        
        # Now scan the repository using a more robust method that avoids pickling errors
        try:
            # Configure ignore patterns specific to repositories
            ignore_patterns = [
                "**/.git/**",        # Git internals
                "**/node_modules/**", # Node.js dependencies
                "**/__pycache__/**",  # Python cache
                "**/venv/**",         # Python virtual environment
                "**/env/**",          # Python virtual environment
                "**/build/**",        # Build artifacts
                "**/dist/**",         # Distribution artifacts
                "**/*.min.js",        # Minified JavaScript
                "**/*.pyc",           # Python compiled files
                "**/*.pyo",           # Python optimized files
                "**/*.class",         # Java compiled files
                "**/.DS_Store",       # macOS metadata
                "**/Thumbs.db",       # Windows metadata
                "**/*.jpg",           # Images
                "**/*.jpeg",          # Images
                "**/*.png",           # Images
                "**/*.gif",           # Images
                "**/*.ico",           # Icons
                "**/*.svg",           # SVGs
                "**/*.eot",           # Fonts
                "**/*.ttf",           # Fonts
                "**/*.woff",          # Fonts
                "**/*.woff2",         # Fonts
                "**/*.lock",          # Lock files
                "**/*.gz",            # Compressed files
                "**/*.zip",           # Compressed files
                "**/*.map"            # Source map files
            ]
            
            # Use a simpler approach to scan the repository by directly processing files
            # Initialize scan results
            scan_results = {
                'scan_type': 'repository',
                'status': 'completed',
                'findings': [],
                'total_files': 0,
                'processed_files': 0,
                'skipped_files': 0,
                'critical_count': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0
            }
            
            # Collect files to be scanned
            all_files = []
            for root, dirs, files in os.walk(repo_path):
                # Skip directories matching ignore patterns
                dirs_to_remove = []
                for i, dir_name in enumerate(dirs):
                    full_dir_path = os.path.join(root, dir_name)
                    rel_dir_path = os.path.relpath(full_dir_path, repo_path)
                    
                    # Check if directory should be ignored
                    for pattern in ignore_patterns:
                        if fnmatch.fnmatch(rel_dir_path, pattern.replace("**/", "")):
                            dirs_to_remove.append(i)
                            break
                
                # Remove directories from bottom to top to preserve indices
                for i in sorted(dirs_to_remove, reverse=True):
                    dirs.pop(i)
                
                # Add files that don't match ignore patterns
                for file_name in files:
                    full_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(full_path, repo_path)
                    
                    # Skip files matching ignore patterns
                    should_skip = False
                    for pattern in ignore_patterns:
                        if fnmatch.fnmatch(rel_path, pattern.replace("**/", "")):
                            should_skip = True
                            break
                    
                    if should_skip:
                        scan_results['skipped_files'] += 1
                        continue
                    
                    # Skip files larger than 50MB
                    try:
                        if os.path.getsize(full_path) > 50 * 1024 * 1024:
                            scan_results['skipped_files'] += 1
                            continue
                    except:
                        scan_results['skipped_files'] += 1
                        continue
                    
                    all_files.append(full_path)
            
            # Update total files count
            scan_results['total_files'] = len(all_files)
            
            # Limit files to scan for large repositories (prevent timeout)
            MAX_FILES_TO_SCAN = 200
            if len(all_files) > MAX_FILES_TO_SCAN:
                logger.info(f"Large repository detected: {len(all_files)} files. Limiting to {MAX_FILES_TO_SCAN} files.")
                # Prioritize important files: sort by extension priority
                priority_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', 
                                      '.php', '.cs', '.env', '.yml', '.yaml', '.json', '.sql', '.sh']
                
                def get_priority(f):
                    ext = os.path.splitext(f)[1].lower()
                    try:
                        return priority_extensions.index(ext)
                    except ValueError:
                        return len(priority_extensions)
                
                all_files.sort(key=get_priority)
                all_files = all_files[:MAX_FILES_TO_SCAN]
                scan_results['limited_scan'] = True
                scan_results['original_file_count'] = scan_results['total_files']
                scan_results['total_files'] = len(all_files)
            
            # Process files sequentially to avoid multiprocessing issues
            for i, file_path in enumerate(all_files):
                # Update progress if callback is provided
                if progress_callback:
                    rel_path = os.path.relpath(file_path, repo_path)
                    progress_callback(i + 1, len(all_files), rel_path)
                
                try:
                    # Process each file individually using the code scanner's scan_file method
                    file_result = self.code_scanner.scan_file(file_path)
                    
                    # Get relative path for the file
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    # Check for skipped or error files
                    if file_result.get('status') in ['skipped', 'error']:
                        scan_results['processed_files'] += 1
                        continue
                    
                    # Get findings - scan_file uses 'pii_found' key
                    pii_findings = file_result.get('pii_found', [])
                    
                    # Skip if no findings
                    if not pii_findings:
                        scan_results['processed_files'] += 1
                        continue
                    
                    # Convert pii_found to findings format and add to results
                    for finding in pii_findings:
                        # Add file path to finding
                        finding['file_path'] = rel_path
                        finding['source_file'] = rel_path
                        
                        # Normalize risk level/severity - ensure both fields are set
                        risk_level = finding.get('risk_level', finding.get('severity', 'Medium'))
                        if isinstance(risk_level, str):
                            risk_level = risk_level.capitalize()
                        
                        # Ensure both severity and risk_level are set for report compatibility
                        finding['severity'] = risk_level
                        finding['risk_level'] = risk_level
                        
                        # Count risk levels
                        if risk_level.lower() == 'critical':
                            scan_results['critical_count'] += 1
                        elif risk_level.lower() == 'high':
                            scan_results['high_risk_count'] += 1
                        elif risk_level.lower() == 'medium':
                            scan_results['medium_risk_count'] += 1
                        elif risk_level.lower() == 'low':
                            scan_results['low_risk_count'] += 1
                        
                        # Add individual finding to results
                        scan_results['findings'].append(finding)
                    
                    # Increment processed files count
                    scan_results['processed_files'] += 1
                    
                except Exception as e:
                    logger.warning(f"Error scanning file {file_path}: {str(e)}")
                    scan_results['skipped_files'] += 1
            
            # Add repository metadata
            scan_results['repo_url'] = repo_url
            scan_results['branch'] = branch or 'default'
            scan_results['repository_metadata'] = clone_result.get('metadata', {})
            scan_results['scan_time'] = datetime.now().isoformat()
            scan_results['process_time_seconds'] = time.time() - start_time
            
            # Add files_scanned for report compatibility
            scan_results['files_scanned'] = scan_results['processed_files']
            
            # Calculate compliance score based on findings
            total_findings = len(scan_results['findings'])
            if total_findings == 0:
                scan_results['compliance_score'] = 100
            else:
                critical = scan_results.get('critical_count', 0)
                high = scan_results.get('high_risk_count', 0)
                medium = scan_results.get('medium_risk_count', 0)
                low = scan_results.get('low_risk_count', 0)
                
                # Weight: Critical=25, High=10, Medium=3, Low=1
                penalty = (critical * 25) + (high * 10) + (medium * 3) + (low * 1)
                score = max(0, 100 - min(penalty, 100))
                scan_results['compliance_score'] = score
            
            return scan_results
            
        except Exception as e:
            logger.error(f"Error scanning repository: {str(e)}")
            return {
                'scan_type': 'repository',
                'status': 'error',
                'message': f'Error scanning repository: {str(e)}',
                'repo_url': repo_url,
                'branch': branch or 'default',
                'scan_time': datetime.now().isoformat(),
                'process_time_seconds': time.time() - start_time,
                'findings': []
            }
        finally:
            # Clean up temporary directory
            self._cleanup_temp_dirs()