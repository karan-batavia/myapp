"""
Intelligent Website Scanner - Scalable Web Crawling and Analysis

Implements smart page selection and parallel crawling:
- Priority-based page selection (privacy policies, forms, auth pages first)
- Parallel crawling with intelligent depth control
- Adaptive sampling for large websites
- Smart cookie and tracking analysis
"""

import os
import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("intelligent_website_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
import concurrent.futures
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Set
from urllib.parse import urlparse, urljoin
import uuid
import requests
from collections import deque

logger = logging.getLogger("services.intelligent_website_scanner")

class IntelligentWebsiteScanner:
    """Smart website scanner with scalability optimizations."""
    
    def __init__(self, website_scanner):
        self.website_scanner = website_scanner
        self.MAX_SCAN_TIME = 300  # 5 minutes max
        self.MAX_PAGES_DEFAULT = 25
        self.MAX_DEPTH_DEFAULT = 3
        self.PARALLEL_WORKERS = 4
        self.REQUEST_TIMEOUT = 10
        
        # Page priority scoring
        self.PAGE_PRIORITIES = {
            # High priority - likely to contain privacy/compliance info
            'privacy': 3.0,
            'policy': 3.0,
            'cookie': 3.0,
            'gdpr': 3.0,
            'terms': 2.8,
            'legal': 2.5,
            'consent': 3.0,
            'contact': 2.5,
            'about': 2.0,
            'login': 2.5,
            'register': 2.5,
            'signup': 2.5,
            'profile': 2.0,
            'account': 2.0,
            'settings': 2.0,
            'form': 2.0,
            'checkout': 2.5,
            'payment': 2.5,
            'billing': 2.5,
            'personal': 2.5,
            'data': 2.2,
            'security': 2.2,
            'help': 1.5,
            'support': 1.5,
            'faq': 1.2,
            'blog': 1.0,
            'news': 1.0,
            'search': 0.8,
            'sitemap': 0.5,
        }
        
        # URL pattern priorities
        self.URL_PATTERNS = {
            '/privacy': 3.0,
            '/cookie': 3.0,
            '/gdpr': 3.0,
            '/terms': 2.8,
            '/legal': 2.5,
            '/contact': 2.0,
            '/login': 2.5,
            '/register': 2.5,
            '/account': 2.0,
            '/profile': 2.0,
            '/checkout': 2.5,
            '/api/': 1.8,
            '/admin': 1.5,
            '/dashboard': 1.8,
        }

    def scan_website_intelligent(self, base_url: str,
                               scan_mode: str = "smart",
                               max_pages: Optional[int] = None,
                               max_depth: Optional[int] = None,
                               progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Intelligent website scanning with adaptive crawling strategies.
        
        Args:
            base_url: Base URL to start scanning from
            scan_mode: "fast", "smart", "deep"
            max_pages: Maximum pages to scan
            max_depth: Maximum crawling depth
            progress_callback: Progress reporting callback
            
        Returns:
            Comprehensive scan results
        """
        start_time = time.time()
        scan_id = f"web_scan_{uuid.uuid4().hex[:8]}"
        
        scan_results = {
            'scan_id': scan_id,
            'scan_type': 'Intelligent Website Scanner',
            'timestamp': datetime.now().isoformat(),
            'region': self.website_scanner.region,
            'base_url': base_url,
            'scan_mode': scan_mode,
            'pages_discovered': 0,
            'pages_scanned': 0,
            'files_scanned': 0,  # For UI compatibility
            'pages_skipped': 0,
            'findings': [],
            'crawling_strategy': {},
            'cookies_found': 0,
            'trackers_found': 0,
            'trackers_detected': [],
            'cookies_detected': [],
            'forms_analyzed': 0,
            'status': 'completed'
        }
        
        try:
            # Step 1: Initial site analysis
            site_analysis = self._analyze_website_structure(base_url)
            
            # Step 2: Select crawling strategy
            strategy = self._select_crawling_strategy(site_analysis, scan_mode, max_pages, max_depth)
            scan_results['crawling_strategy'] = strategy
            
            if progress_callback:
                progress_callback(10, 100, "Website analyzed, starting intelligent crawl...")
            
            # Step 3: Discover and prioritize pages
            pages_to_scan = self._discover_pages_intelligent(base_url, strategy)
            scan_results['pages_discovered'] = len(pages_to_scan)
            
            # Step 4: Scan pages in parallel
            findings, metrics, all_cookies, all_trackers = self._scan_pages_parallel(
                pages_to_scan, scan_results, progress_callback
            )
            
            # Step 5: Deduplicate findings (same tracker/cookie on multiple pages)
            findings = self._deduplicate_findings(findings)
            
            scan_results['findings'] = findings
            scan_results['cookies_found'] = len(all_cookies)
            scan_results['trackers_found'] = len(all_trackers)
            scan_results['forms_analyzed'] = metrics.get('forms', 0)
            scan_results['duration_seconds'] = time.time() - start_time
            
            # Store actual cookies and trackers data
            scan_results['cookies_detected'] = list(all_cookies.values())
            scan_results['trackers_detected'] = all_trackers
            
            # Calculate meaningful metrics for display
            scan_results['total_findings'] = len(findings)
            scan_results['critical_findings'] = len([f for f in findings if f.get('severity') == 'Critical'])
            scan_results['high_risk_findings'] = len([f for f in findings if f.get('severity') == 'High'])
            
            # Set database-compatible field names for dashboard display
            scan_results['total_pii_found'] = len(findings)  # Database expects this field name
            scan_results['high_risk_count'] = len([f for f in findings if f.get('severity') == 'High'])  # Database expects this field name
            scan_results['files_scanned'] = scan_results['pages_scanned']  # Database expects files_scanned
            scan_results['lines_analyzed'] = scan_results['pages_scanned'] * 50  # Estimate 50 lines per page
            
            # Calculate coverage metrics
            scan_results['scan_coverage'] = (
                scan_results['pages_scanned'] / max(scan_results['pages_discovered'], 1) * 100
            )
            
            # Calculate compliance score based on findings (same logic as regular website scanner)
            total_findings = len(findings)
            critical_findings = len([f for f in findings if f.get('severity') == 'Critical'])
            high_findings = len([f for f in findings if f.get('severity') == 'High'])
            
            if total_findings == 0:
                compliance_score = 100
                risk_level = "Low"
            else:
                # Penalty-based scoring system (same as code scanner)
                penalty = (critical_findings * 25) + (high_findings * 15) + ((total_findings - critical_findings - high_findings) * 5)
                compliance_score = max(0, 100 - penalty)
                
                # Determine risk level based on findings
                if critical_findings > 0:
                    risk_level = "Critical"
                elif high_findings > 2:
                    risk_level = "High"
                elif total_findings > 10:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
            
            scan_results['compliance_score'] = compliance_score
            scan_results['risk_level'] = risk_level
            
            logger.info(f"Intelligent website scan completed: {len(findings)} findings in {scan_results['duration_seconds']:.1f}s")
            logger.info(f"Scanned {scan_results['pages_scanned']}/{scan_results['pages_discovered']} pages ({scan_results['scan_coverage']:.1f}% coverage)")
            
        except Exception as e:
            logger.error(f"Intelligent website scan failed: {str(e)}")
            scan_results['status'] = 'failed'
            scan_results['error'] = str(e)
        
        return scan_results

    def _analyze_website_structure(self, base_url: str) -> Dict[str, Any]:
        """Analyze website structure to determine optimal crawling strategy."""
        analysis = {
            'base_domain': urlparse(base_url).netloc,
            'has_sitemap': False,
            'has_robots_txt': False,
            'estimated_pages': 0,
            'response_time': 0,
            'https_enabled': base_url.startswith('https'),
            'accessible': True
        }
        
        try:
            # Test basic connectivity and response time
            start_time = time.time()
            response = requests.get(base_url, timeout=self.REQUEST_TIMEOUT)
            analysis['response_time'] = time.time() - start_time
            analysis['accessible'] = response.status_code == 200
            
            if analysis['accessible']:
                # Check for sitemap
                sitemap_urls = [
                    urljoin(base_url, '/sitemap.xml'),
                    urljoin(base_url, '/sitemap_index.xml'),
                    urljoin(base_url, '/sitemaps.xml')
                ]
                
                for sitemap_url in sitemap_urls:
                    try:
                        sitemap_response = requests.get(sitemap_url, timeout=5)
                        if sitemap_response.status_code == 200:
                            analysis['has_sitemap'] = True
                            # Rough estimate of pages from sitemap
                            analysis['estimated_pages'] = sitemap_response.text.count('<url>')
                            break
                    except:
                        continue
                
                # Check robots.txt
                try:
                    robots_response = requests.get(urljoin(base_url, '/robots.txt'), timeout=5)
                    analysis['has_robots_txt'] = robots_response.status_code == 200
                except:
                    pass
                
                # If no sitemap, estimate based on main page links
                if not analysis['has_sitemap']:
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.content, 'html.parser')
                        links = soup.find_all('a', href=True)
                        internal_links = [
                            link for link in links 
                            if self._is_internal_link(str(link['href']), analysis['base_domain'])
                        ]
                        analysis['estimated_pages'] = min(len(internal_links) * 2, 500)  # Rough estimate
                    except:
                        analysis['estimated_pages'] = 10  # Conservative fallback
                        
        except Exception as e:
            logger.warning(f"Error analyzing website structure: {str(e)}")
            analysis['accessible'] = False
        
        return analysis

    def _select_crawling_strategy(self, site_analysis: Dict[str, Any],
                                scan_mode: str, max_pages: Optional[int], 
                                max_depth: Optional[int]) -> Dict[str, Any]:
        """Select optimal crawling strategy based on site analysis."""
        
        estimated_pages = site_analysis['estimated_pages']
        response_time = site_analysis['response_time']
        has_sitemap = site_analysis['has_sitemap']
        
        # Determine strategy based on analysis
        if scan_mode == "fast" or estimated_pages <= 10:
            strategy_type = "comprehensive"
            target_pages = min(estimated_pages, 15)
            target_depth = 2
            workers = 2
            
        elif scan_mode == "deep" or estimated_pages < 50:
            strategy_type = "priority_deep"
            target_pages = min(max_pages or 50, estimated_pages)
            target_depth = max_depth or 4
            workers = 3
            
        elif estimated_pages > 200 or response_time > 3:
            strategy_type = "sampling"
            target_pages = min(max_pages or 25, estimated_pages)
            target_depth = max_depth or 2
            workers = 4
            
        else:  # smart mode
            strategy_type = "priority"
            target_pages = min(max_pages or self.MAX_PAGES_DEFAULT, estimated_pages)
            target_depth = max_depth or self.MAX_DEPTH_DEFAULT
            workers = 3
        
        return {
            'type': strategy_type,
            'target_pages': target_pages,
            'max_depth': target_depth,
            'parallel_workers': workers,
            'use_sitemap': has_sitemap,
            'max_scan_time': self.MAX_SCAN_TIME,
            'reasoning': f"Selected {strategy_type} for ~{estimated_pages} pages with {response_time:.1f}s response time"
        }

    def _discover_pages_intelligent(self, base_url: str, strategy: Dict[str, Any]) -> List[str]:
        """Discover and prioritize pages for scanning."""
        
        discovered_pages = set()
        prioritized_pages = []
        
        # Start with base URL
        discovered_pages.add(base_url)
        
        # Use sitemap if available and strategy allows
        if strategy['use_sitemap']:
            sitemap_pages = self._extract_sitemap_urls(base_url)
            discovered_pages.update(sitemap_pages)
        
        # Crawl from base page to discover more
        additional_pages = self._crawl_for_links(
            base_url, strategy['max_depth'], strategy['target_pages'] * 2
        )
        discovered_pages.update(additional_pages)
        
        # Prioritize discovered pages
        for page_url in discovered_pages:
            priority = self._calculate_page_priority(page_url)
            prioritized_pages.append((page_url, priority))
        
        # Sort by priority and select top pages
        prioritized_pages.sort(key=lambda x: x[1], reverse=True)
        
        # Apply strategy-specific selection
        target_pages = strategy['target_pages']
        
        if strategy['type'] == 'sampling':
            # Take top 80% by priority, random sample the rest
            high_priority_count = min(target_pages * 80 // 100, len(prioritized_pages) // 2)
            selected = prioritized_pages[:high_priority_count]
            
            # Random sample from remaining
            remaining = prioritized_pages[high_priority_count:]
            if remaining and len(selected) < target_pages:
                import random
                sample_size = min(target_pages - len(selected), len(remaining))
                selected.extend(random.sample(remaining, sample_size))
        else:
            # Take top priority pages
            selected = prioritized_pages[:target_pages]
        
        selected_urls = [page[0] for page in selected]
        
        logger.info(f"Discovered {len(discovered_pages)} pages, selected {len(selected_urls)} for scanning")
        return selected_urls

    def _calculate_page_priority(self, page_url: str) -> float:
        """Calculate priority score for a page URL."""
        url_lower = page_url.lower()
        path = urlparse(page_url).path.lower()
        
        priority = 1.0  # Base priority
        
        # URL pattern priority
        for pattern, weight in self.URL_PATTERNS.items():
            if pattern in path:
                priority += weight
        
        # Page keyword priority
        for keyword, weight in self.PAGE_PRIORITIES.items():
            if keyword in url_lower:
                priority += weight
        
        # Special high-priority patterns
        high_priority_patterns = [
            'privacy', 'policy', 'cookie', 'gdpr', 'consent', 
            'terms', 'legal', 'data-protection', 'compliance'
        ]
        
        for pattern in high_priority_patterns:
            if pattern in url_lower:
                priority += 3.0
        
        # Penalize very deep URLs or URLs with many parameters
        path_depth = path.count('/')
        if path_depth > 4:
            priority -= 0.5 * (path_depth - 4)
        
        query_params = urlparse(page_url).query
        if len(query_params) > 100:
            priority -= 1.0
        
        return max(priority, 0.1)  # Minimum priority

    def _crawl_for_links(self, base_url: str, max_depth: int, max_links: int) -> Set[str]:
        """Crawl website to discover additional links."""
        from collections import deque
        from typing import Tuple
        
        discovered = set()
        to_crawl: deque[Tuple[str, int]] = deque()
        to_crawl.append((base_url, 0))  # (url, depth)
        crawled = set()
        base_domain = urlparse(base_url).netloc
        
        while to_crawl and len(discovered) < max_links:
            current_url, depth = to_crawl.popleft()
            
            if current_url in crawled or depth >= max_depth:
                continue
            
            crawled.add(current_url)
            
            try:
                response = requests.get(current_url, timeout=self.REQUEST_TIMEOUT)
                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract all links
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = str(link['href'])
                        absolute_url = urljoin(current_url, href)
                        
                        if (self._is_internal_link(absolute_url, base_domain) and 
                            absolute_url not in discovered and 
                            len(discovered) < max_links):
                            
                            discovered.add(absolute_url)
                            if depth + 1 < max_depth:
                                to_crawl.append((absolute_url, depth + 1))
                        
            except Exception as e:
                logger.warning(f"Error crawling {current_url}: {str(e)}")
                continue
        
        return discovered

    def _is_internal_link(self, url: str, base_domain: str) -> bool:
        """Check if URL is internal to the base domain."""
        try:
            parsed = urlparse(url)
            return (not parsed.netloc or parsed.netloc == base_domain) and \
                   not url.startswith('mailto:') and \
                   not url.startswith('tel:') and \
                   not url.startswith('javascript:')
        except:
            return False

    def _extract_sitemap_urls(self, base_url: str) -> Set[str]:
        """Extract URLs from sitemap."""
        urls = set()
        sitemap_urls = [
            urljoin(base_url, '/sitemap.xml'),
            urljoin(base_url, '/sitemap_index.xml')
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                response = requests.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    # Simple XML parsing for URLs
                    import re
                    url_pattern = r'<loc>(.*?)</loc>'
                    found_urls = re.findall(url_pattern, response.text)
                    urls.update(found_urls[:100])  # Limit to first 100 URLs
                    break
            except Exception as e:
                logger.warning(f"Error fetching sitemap {sitemap_url}: {str(e)}")
        
        return urls

    def _scan_pages_parallel(self, pages_to_scan: List[str],
                           scan_results: Dict[str, Any],
                           progress_callback: Optional[Callable]) -> tuple:
        """Scan pages in parallel with progress tracking."""
        
        all_findings = []
        all_cookies = {}
        all_trackers = []
        metrics = {'cookies': 0, 'trackers': 0, 'forms': 0}
        
        workers = scan_results['crawling_strategy']['parallel_workers']
        max_time = scan_results['crawling_strategy']['max_scan_time']
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all page scanning tasks
            future_to_page = {
                executor.submit(self._scan_single_page, page_url): page_url
                for page_url in pages_to_scan
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_page, timeout=max_time):
                try:
                    # Check timeout
                    if time.time() - start_time > max_time:
                        logger.warning("Website scanning timeout reached")
                        break
                    
                    page_url = future_to_page[future]
                    result = future.result(timeout=30)  # 30 second per page timeout
                    
                    if result:
                        findings, page_metrics, page_cookies, page_trackers = result
                        all_findings.extend(findings)
                        
                        # Accumulate cookies and trackers
                        for cookie_name, cookie_data in page_cookies.items():
                            all_cookies[cookie_name] = cookie_data
                        all_trackers.extend(page_trackers)
                        
                        metrics['cookies'] += len(page_cookies)
                        metrics['trackers'] += len(page_trackers)
                        metrics['forms'] += page_metrics.get('forms', 0)
                    
                    completed += 1
                    scan_results['pages_scanned'] = completed
                    scan_results['files_scanned'] = completed  # For UI compatibility
                    
                    # Progress callback
                    if progress_callback:
                        progress = 20 + int(70 * completed / len(pages_to_scan))
                        page_name = urlparse(page_url).path or '/'
                        progress_callback(progress, 100, f"Scanned {page_name}")
                
                except concurrent.futures.TimeoutError:
                    scan_results['pages_skipped'] += 1
                    logger.warning(f"Page scan timeout: {future_to_page[future]}")
                except Exception as e:
                    scan_results['pages_skipped'] += 1
                    logger.warning(f"Page scan error: {str(e)}")
        
        return all_findings, metrics, all_cookies, all_trackers

    def _deduplicate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate findings that appear across multiple pages.
        
        Groups identical trackers/cookies and consolidates them with page counts.
        """
        if not findings:
            return []
        
        unique_findings = {}
        
        for finding in findings:
            finding_type = finding.get('type', '')
            description = finding.get('description', '')
            location = finding.get('location', '')
            
            pattern_match = ''
            if 'Pattern:' in location:
                pattern_match = location.split('Pattern:')[-1].strip()
            
            key = f"{finding_type}|{pattern_match or description[:50]}"
            
            if key not in unique_findings:
                consolidated = finding.copy()
                consolidated['pages_affected'] = []
                consolidated['occurrence_count'] = 0
                unique_findings[key] = consolidated
            
            found_on = finding.get('found_on', finding.get('location', ''))
            if found_on and found_on not in unique_findings[key]['pages_affected']:
                unique_findings[key]['pages_affected'].append(found_on)
            unique_findings[key]['occurrence_count'] += 1
        
        result = []
        for key, finding in unique_findings.items():
            count = finding['occurrence_count']
            pages = finding['pages_affected']
            
            if count > 1:
                finding['context'] = f"Found on {count} pages across the website"
                if len(pages) > 0:
                    finding['location'] = f"{finding.get('location', '')} (affects {len(pages)} pages)"
            else:
                tracker_name = finding.get('description', '').replace('Inline tracker script for ', '')
                if 'tracker' in finding.get('type', '').lower():
                    finding['context'] = f"Third-party tracking script detected: {tracker_name}"
                elif 'consent' in finding.get('type', '').lower():
                    finding['context'] = f"Consent management platform: {tracker_name}"
                else:
                    finding['context'] = finding.get('description', 'Privacy-related finding requiring review')
            
            del finding['occurrence_count']
            result.append(finding)
        
        logger.info(f"Deduplicated {len(findings)} findings to {len(result)} unique findings")
        return result

    def _scan_single_page(self, page_url: str) -> Optional[tuple]:
        """Scan a single page for privacy compliance issues."""
        try:
            # Import WebsiteScanner and create a temporary scanner for single page analysis
            from services.website_scanner import WebsiteScanner
            temp_scanner = WebsiteScanner(region=self.website_scanner.region)
            temp_scanner.max_pages = 1
            temp_scanner.max_depth = 1
            
            # Use the existing website scanner's scan_website method for single page
            result = temp_scanner.scan_website(page_url, follow_links=False)
            
            # Extract findings, cookies, and trackers from result
            findings = []
            metrics = {'cookies': 0, 'trackers': 0, 'forms': 0}
            cookies = {}
            trackers = []
            
            if isinstance(result, dict):
                findings = result.get('findings', [])
                
                # Extract cookies from multiple possible locations
                cookies = result.get('cookies', {})
                if not cookies:
                    # Try to extract from page results or other sources
                    page_results = result.get('page_results', [])
                    for page_result in page_results:
                        page_cookies = page_result.get('cookies', [])
                        for cookie in page_cookies:
                            if isinstance(cookie, dict):
                                cookie_name = cookie.get('name', f'cookie_{len(cookies)}')
                                cookies[cookie_name] = cookie
                            elif isinstance(cookie, str):
                                cookies[cookie] = {'name': cookie, 'source': page_url}
                
                # Extract trackers from multiple possible locations  
                trackers = result.get('trackers', [])
                if not trackers:
                    page_results = result.get('page_results', [])
                    for page_result in page_results:
                        page_trackers = page_result.get('trackers', [])
                        trackers.extend(page_trackers)
                
                # CRITICAL: Extract cookies and trackers from findings - this is the main source
                # Most privacy findings represent cookies/trackers but aren't in dedicated fields
                cookie_related_patterns = ['cookie', 'consent', 'marketing', 'analytics', 'functional', 'advertising']
                tracker_related_patterns = ['tracker', 'tracking', 'google', 'analytics', 'facebook', 'pixel', 'tag', 'script']
                
                for finding in findings:
                    finding_type = finding.get('type', '').lower()
                    finding_desc = finding.get('description', '').lower()
                    finding_location = finding.get('location', '').lower()
                    
                    # Enhanced cookie detection - look in multiple fields
                    if any(pattern in finding_type or pattern in finding_desc or pattern in finding_location 
                           for pattern in cookie_related_patterns):
                        cookie_name = (finding.get('location', '').replace('Cookie: ', '') or 
                                     finding.get('type', '') or 
                                     f'privacy_cookie_{len(cookies)}')
                        if cookie_name and cookie_name not in cookies:
                            cookies[cookie_name] = {
                                'name': cookie_name,
                                'source': page_url,
                                'privacy_risk': finding.get('privacy_risk', 'Medium'),
                                'from_finding': True,
                                'type': finding.get('type', ''),
                                'description': finding.get('description', '')
                            }
                    
                    # Enhanced tracker detection - look in multiple fields
                    if any(pattern in finding_type or pattern in finding_desc or pattern in finding_location 
                           for pattern in tracker_related_patterns):
                        tracker_name = (finding.get('location', '') or 
                                      finding.get('type', '') or 
                                      finding.get('description', '')[:50] or 
                                      'privacy_tracker')
                        tracker_data = {
                            'name': tracker_name,
                            'source': page_url,
                            'privacy_risk': finding.get('privacy_risk', 'Medium'),
                            'from_finding': True,
                            'type': finding.get('type', ''),
                            'description': finding.get('description', '')
                        }
                        # Avoid duplicates
                        if not any(t.get('name') == tracker_name for t in trackers):
                            trackers.append(tracker_data)
                
                # Calculate metrics
                metrics['cookies'] = len(cookies)
                metrics['trackers'] = len(trackers)
                metrics['forms'] = len(result.get('forms', []))
                    
            elif isinstance(result, list):
                findings = result
            
            return findings, metrics, cookies, trackers
                
        except Exception as e:
            logger.warning(f"Error scanning page {page_url}: {str(e)}")
            return None