"""
Website Scanner module for comprehensive privacy compliance scanning of websites.

This module simulates a real visitor journey, analyzing pageviews and actions
to provide detailed reports on data collection, tracking pixels, cookies,
and consent choices across a website.
"""

import os
import re
import json
import time
import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("website_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
import requests
import fnmatch
import hashlib
import tldextract
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from trafilatura import fetch_url, extract
import whois
import dns.resolver

# Import PII detection for content scanning
try:
    from utils.pii_detection import identify_pii_in_text
    PII_DETECTION_AVAILABLE = True
except ImportError:
    PII_DETECTION_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class WebsiteScanner:
    """
    A comprehensive scanner that analyzes websites for privacy compliance issues,
    tracking technologies, cookies, and consent mechanisms.
    """
    
    def __init__(self, max_pages=100, max_depth=3, crawl_delay=1, 
                 save_screenshots=False, simulate_user=True, check_ssl=True,
                 check_dns=True, region="Netherlands"):
        """
        Initialize the website scanner.
        
        Args:
            max_pages: Maximum number of pages to scan (default: 100)
            max_depth: Maximum depth of crawling (default: 3)
            crawl_delay: Delay between requests in seconds (default: 1)
            save_screenshots: Whether to save screenshots of pages (default: False)
            simulate_user: Whether to simulate user interactions (default: True)
            check_ssl: Whether to check SSL/TLS configuration (default: True)
            check_dns: Whether to check DNS records (default: True)
            region: Region for applying GDPR rules (default: "Netherlands")
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.crawl_delay = crawl_delay
        self.save_screenshots = save_screenshots
        self.simulate_user = simulate_user
        self.check_ssl = check_ssl
        self.check_dns = check_dns
        self.region = region
        
        # Session with headers that mimic a real browser
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',  # Do Not Track header
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Initialize tracking databases
        self._load_tracking_databases()
        
        # Known consent management platforms
        self.consent_platforms = [
            {'name': 'OneTrust', 'patterns': ['otSDKStub', 'OneTrust', 'onetrust', 'optanon']},
            {'name': 'TrustArc', 'patterns': ['truste', 'TrustArc', 'trustarc.com']},
            {'name': 'Cookiebot', 'patterns': ['cookiebot', 'Cookiebot', 'CookieDeclaration']},
            {'name': 'CookiePro', 'patterns': ['cookiepro', 'CookiePro']},
            {'name': 'Osano', 'patterns': ['osano', 'Osano', 'osano.com']},
            {'name': 'Quantcast Choice', 'patterns': ['quantcast', 'Quantcast', 'quantcast.mgr.consensu.org']},
            {'name': 'CivicUK', 'patterns': ['civicuk', 'CivicUK', 'civic-cookie-control']},
            {'name': 'CookieYes', 'patterns': ['cookieyes', 'CookieYes']},
            {'name': 'GDPR Cookie Consent', 'patterns': ['gdpr-cookie-consent', 'gdpr_cookie_consent', 'GDPRCookieConsent']},
            {'name': 'Didomi', 'patterns': ['didomi', 'Didomi']},
            {'name': 'Termly', 'patterns': ['termly', 'Termly']},
            {'name': 'Usercentrics', 'patterns': ['usercentrics', 'Usercentrics']},
            {'name': 'iubenda', 'patterns': ['iubenda', 'Iubenda']},
            {'name': 'Complianz', 'patterns': ['complianz', 'Complianz']},
            {'name': 'CookieHub', 'patterns': ['cookiehub', 'CookieHub']},
            {'name': 'Consent Manager', 'patterns': ['consent-manager', 'ConsentManager']},
            {'name': 'Seers CMP', 'patterns': ['seers', 'Seers', 'seersco.io']},
            {'name': 'Onetrust Banner', 'patterns': ['onetrust-banner', 'OneTrustBanner']}
        ]
        
        # Known cookie categories
        self.cookie_categories = {
            'essential': ['session', 'csrf', 'security', 'auth', 'login', 'cookie_notice', 'gdpr'],
            'functional': ['preferences', 'settings', 'language', 'timezone', 'region', 'country', 'user_settings'],
            'analytics': ['ga', 'google', 'analytics', '_ga', '_gid', '_gat', 'utma', 'utmb', 'utmc', 'utmz', 'utmv', 'utmk'],
            'advertising': ['ad', 'ads', 'advert', 'doubleclick', 'google_ad', 'facebook', 'fb', 'twitter', 'linkedin'],
            'social': ['facebook', 'twitter', 'linkedin', 'pinterest', 'instagram', 'youtube', 'vimeo', 'tumblr']
        }
        
        # AI Act compliance patterns for website analysis
        self.ai_act_web_patterns = {
            'ai_chatbots': [
                r'(chatbot|chat.*bot|virtual.*assistant|ai.*assistant)',
                r'(openai|gpt|claude|bard|gemini|copilot)',
                r'(conversation.*ai|conversational.*ai|dialog.*system)',
                r'(nlp|natural.*language.*processing|speech.*recognition)'
            ],
            'recommendation_systems': [
                r'(recommendation|recommend|personalization|personalized)',
                r'(machine.*learning|ml.*algorithm|predictive.*analytics)',
                r'(user.*behavior|behavioral.*analytics|content.*filtering)',
                r'(collaborative.*filtering|content.*based.*filtering)'
            ],
            'automated_decision_making': [
                r'(automated.*decision|algorithmic.*decision|ai.*decision)',
                r'(scoring.*system|risk.*assessment|credit.*scoring)',
                r'(automated.*approval|automatic.*approval|ai.*approval)',
                r'(algorithmic.*trading|automated.*trading|robo.*advisor)'
            ],
            'biometric_ai': [
                r'(facial.*recognition|face.*recognition|biometric)',
                r'(fingerprint.*recognition|voice.*recognition|iris.*scan)',
                r'(emotion.*detection|sentiment.*analysis|mood.*detection)',
                r'(gait.*analysis|behavioral.*biometrics|keystroke.*dynamics)'
            ],
            'high_risk_web_ai': [
                r'(medical.*ai|healthcare.*ai|diagnostic.*ai)',
                r'(education.*ai|learning.*analytics|student.*assessment)',
                r'(recruitment.*ai|hiring.*algorithm|resume.*screening)',
                r'(financial.*ai|loan.*algorithm|credit.*ai)',
                r'(legal.*ai|court.*ai|judicial.*algorithm)'
            ],
            'ai_transparency_web': [
                r'(ai.*explanation|algorithm.*explanation|explainable.*ai)',
                r'(human.*review|manual.*oversight|human.*intervention)',
                r'(ai.*audit|algorithm.*audit|fairness.*testing)',
                r'(bias.*detection|discrimination.*testing|algorithmic.*accountability)'
            ]
        }
        
        # Progress tracking
        self.progress_callback = None
        self.is_running = False
    
    def _load_tracking_databases(self):
        """Load known tracking databases from JSON files"""
        
        # Define default trackers with comprehensive analysis data
        self.known_trackers = {
            'Google Analytics': {
                'domains': ['google-analytics.com', 'analytics.google.com'],
                'patterns': ['ga', 'gtag', 'gtm', 'analytics'],
                'purpose': 'Website analytics and user behavior tracking',
                'privacy_risk': 'Medium',
                'data_collected': 'User behavior, page views, demographics, device info',
                'gdpr_basis': 'Legitimate interest or consent required'
            },
            'Google Tag Manager': {
                'domains': ['googletagmanager.com', 'tagmanager.google.com'],
                'patterns': ['gtm', 'tagmanager'],
                'purpose': 'Tag management system for deploying tracking codes',
                'privacy_risk': 'Medium',
                'data_collected': 'Variable based on configured tags',
                'gdpr_basis': 'Depends on tags deployed'
            },
            'Facebook Pixel': {
                'domains': ['facebook.com', 'facebook.net', 'fbcdn.net'],
                'patterns': ['fbq', 'fbevents', 'facebook-jssdk'],
                'purpose': 'Social media advertising and conversion tracking',
                'privacy_risk': 'High',
                'data_collected': 'User behavior, conversions, demographics for ad targeting',
                'gdpr_basis': 'Consent required for non-essential tracking'
            },
            'LinkedIn Insight': {
                'domains': ['linkedin.com', 'licdn.com'],
                'patterns': ['_linkedin_partner_id', 'linkedin_data_partner'],
                'purpose': 'Professional network advertising and analytics',
                'privacy_risk': 'Medium',
                'data_collected': 'Professional demographics, page visits, conversions',
                'gdpr_basis': 'Consent required for marketing purposes'
            },
            'Twitter Pixel': {
                'domains': ['twitter.com', 'ads-twitter.com'],
                'patterns': ['twq', 'twitter_pixel'],
                'purpose': 'Social media advertising and conversion tracking',
                'privacy_risk': 'High',
                'data_collected': 'User behavior, interests, ad interactions',
                'gdpr_basis': 'Consent required for advertising tracking'
            },
            'HotJar': {
                'domains': ['hotjar.com', 'hotjar.io'],
                'patterns': ['hjLaunchSurvey', 'hjSiteSettings', 'hjUserAttributes'],
                'purpose': 'User experience analytics including heatmaps and recordings',
                'privacy_risk': 'High',
                'data_collected': 'Mouse movements, clicks, form interactions, session recordings',
                'gdpr_basis': 'Consent required for behavioral tracking'
            },
            'Mixpanel': {
                'domains': ['mixpanel.com'],
                'patterns': ['mixpanel'],
                'purpose': 'Advanced analytics and user behavior tracking',
                'privacy_risk': 'Medium',
                'data_collected': 'Event tracking, user properties, funnel analysis',
                'gdpr_basis': 'Legitimate interest or consent required'
            },
            'Hubspot': {
                'domains': ['hs-scripts.com', 'hubspot.com'],
                'patterns': ['hs-script', 'hubspot'],
                'purpose': 'Marketing automation and lead tracking',
                'privacy_risk': 'Medium',
                'data_collected': 'Contact information, website behavior, email interactions',
                'gdpr_basis': 'Consent required for marketing communications'
            },
            'Intercom': {
                'domains': ['intercom.io', 'intercom.com'],
                'patterns': ['intercom'],
                'purpose': 'Customer messaging and support chat',
                'privacy_risk': 'Medium',
                'data_collected': 'User interactions, support conversations, contact details',
                'gdpr_basis': 'Legitimate interest for support, consent for marketing'
            },
            'Segment': {
                'domains': ['segment.io', 'segment.com'],
                'patterns': ['segment']
            },
            'Amplitude': {
                'domains': ['amplitude.com'],
                'patterns': ['amplitude']
            },
            'Crazy Egg': {
                'domains': ['crazyegg.com'],
                'patterns': ['crazyegg', 'cetrk']
            },
            'FullStory': {
                'domains': ['fullstory.com'],
                'patterns': ['fullstory', 'FS']
            },
            'Lucky Orange': {
                'domains': ['luckyorange.com', 'luckyorange.net'],
                'patterns': ['LuckyOrange', 'LOTC']
            },
            'Mouseflow': {
                'domains': ['mouseflow.com'],
                'patterns': ['mouseflow', 'MF']
            },
            'Optimizely': {
                'domains': ['optimizely.com'],
                'patterns': ['optimizely']
            },
            'VWO': {
                'domains': ['visualwebsiteoptimizer.com', 'vwo.com'],
                'patterns': ['vwo', '_vis_opt']
            },
            'Matomo': {
                'domains': ['matomo.org', 'matomo.cloud'],
                'patterns': ['matomo', 'piwik']
            },
            'Adobe Analytics': {
                'domains': ['omtrdc.net', 'adobe.com'],
                'patterns': ['s_code', 's.trackingServer', 'sc.omtrdc']
            }
        }
        
        # Try to load trackers from a JSON file if it exists
        try:
            trackers_path = os.path.join('data', 'trackers_database.json')
            if os.path.exists(trackers_path):
                with open(trackers_path, 'r') as f:
                    self.known_trackers = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load trackers database: {str(e)}")
        
        # Define comprehensive cookie database with categorization
        self.cookie_database = {
            # Cloudflare cookies
            '__cf_bm': {
                'category': 'Security',
                'purpose': 'Bot detection and DDoS protection by Cloudflare',
                'persistent': False,
                'expiry': '30 minutes',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Legitimate interest for security'
            },
            '__cfruid': {
                'category': 'Security',
                'purpose': 'Cloudflare session identifier for security',
                'persistent': False,
                'expiry': 'Session',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Legitimate interest for security'
            },
            '_cf_chl_opt': {
                'category': 'Security',
                'purpose': 'Cloudflare challenge optimization',
                'persistent': False,
                'expiry': '24 hours',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Legitimate interest for security'
            },
            # Google Analytics cookies
            '_ga': {
                'category': 'Analytics',
                'purpose': 'Google Analytics - distinguishes unique users',
                'persistent': True,
                'expiry': '2 years',
                'privacy_risk': 'Medium',
                'gdpr_basis': 'Consent required'
            },
            '_ga_*': {
                'category': 'Analytics',
                'purpose': 'Google Analytics 4 - session and campaign data',
                'persistent': True,
                'expiry': '2 years',
                'privacy_risk': 'Medium',
                'gdpr_basis': 'Consent required'
            },
            '_gid': {
                'category': 'Analytics',
                'purpose': 'Google Analytics - distinguishes users',
                'persistent': True,
                'expiry': '24 hours',
                'privacy_risk': 'Medium',
                'gdpr_basis': 'Consent required'
            },
            '_gat': {
                'category': 'Analytics',
                'purpose': 'Google Analytics - throttle request rate',
                'persistent': False,
                'expiry': '1 minute',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Consent required'
            },
            # Session and functionality cookies
            'PHPSESSID': {
                'category': 'Essential',
                'purpose': 'PHP session identifier for website functionality',
                'persistent': False,
                'expiry': 'Session',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            'JSESSIONID': {
                'category': 'Essential',
                'purpose': 'Java session identifier for website functionality',
                'persistent': False,
                'expiry': 'Session',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            'ASP.NET_SessionId': {
                'category': 'Essential',
                'purpose': 'ASP.NET session identifier for website functionality',
                'persistent': False,
                'expiry': 'Session',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            # Consent management cookies
            'CookieConsent': {
                'category': 'Functional',
                'purpose': 'Stores user cookie consent preferences',
                'persistent': True,
                'expiry': '1 year',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            'cookieconsent_status': {
                'category': 'Functional',
                'purpose': 'Records cookie consent status',
                'persistent': True,
                'expiry': '1 year',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            # Facebook cookies
            '_fbp': {
                'category': 'Marketing',
                'purpose': 'Facebook Pixel - tracks conversions and user behavior',
                'persistent': True,
                'expiry': '3 months',
                'privacy_risk': 'High',
                'gdpr_basis': 'Consent required'
            },
            '_fbc': {
                'category': 'Marketing',
                'purpose': 'Facebook click identifier for conversion tracking',
                'persistent': True,
                'expiry': '3 months',
                'privacy_risk': 'High',
                'gdpr_basis': 'Consent required'
            },
            # YouTube/Google cookies
            'YSC': {
                'category': 'Marketing',
                'purpose': 'YouTube - registers unique ID for statistics',
                'persistent': False,
                'expiry': 'Session',
                'privacy_risk': 'Medium',
                'gdpr_basis': 'Consent required'
            },
            'VISITOR_INFO1_LIVE': {
                'category': 'Marketing',
                'purpose': 'YouTube - estimates bandwidth for video quality',
                'persistent': True,
                'expiry': '5 months',
                'privacy_risk': 'Medium',
                'gdpr_basis': 'Consent required'
            }
        }
    
    def _categorize_cookie(self, cookie_name: str, cookie_value: str = "") -> Dict[str, Any]:
        """
        Categorize a cookie based on its name and value using the comprehensive database.
        
        Args:
            cookie_name: The name of the cookie
            cookie_value: The value of the cookie (optional)
            
        Returns:
            Dictionary with category, purpose, persistent status, and expiry information
        """
        cookie_name_lower = cookie_name.lower()
        
        # Check exact matches first
        if cookie_name in self.cookie_database:
            return self.cookie_database[cookie_name]
        
        # Check pattern matches for Google Analytics cookies
        if cookie_name.startswith('_ga_'):
            return self.cookie_database['_ga_*']
        
        # Pattern-based matching for common cookie types
        patterns = {
            # Session cookies
            'session': {
                'category': 'Essential',
                'purpose': 'Session management for website functionality',
                'persistent': False,
                'expiry': 'Session',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            'sess': {
                'category': 'Essential',
                'purpose': 'Session identifier for website functionality',
                'persistent': False,
                'expiry': 'Session',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            # Security cookies
            'csrf': {
                'category': 'Security',
                'purpose': 'Cross-site request forgery protection',
                'persistent': False,
                'expiry': 'Session',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            'xsrf': {
                'category': 'Security',
                'purpose': 'Cross-site request forgery protection',
                'persistent': False,
                'expiry': 'Session',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            # Analytics patterns
            'analytics': {
                'category': 'Analytics',
                'purpose': 'Website analytics and user behavior tracking',
                'persistent': True,
                'expiry': 'Variable',
                'privacy_risk': 'Medium',
                'gdpr_basis': 'Consent required'
            },
            'utm': {
                'category': 'Analytics',
                'purpose': 'Campaign tracking and attribution',
                'persistent': True,
                'expiry': 'Variable',
                'privacy_risk': 'Medium',
                'gdpr_basis': 'Consent required'
            },
            # Marketing cookies
            'fb': {
                'category': 'Marketing',
                'purpose': 'Facebook advertising and tracking',
                'persistent': True,
                'expiry': 'Variable',
                'privacy_risk': 'High',
                'gdpr_basis': 'Consent required'
            },
            'google': {
                'category': 'Marketing',
                'purpose': 'Google advertising and tracking',
                'persistent': True,
                'expiry': 'Variable',
                'privacy_risk': 'Medium',
                'gdpr_basis': 'Consent required'
            },
            # Consent cookies
            'consent': {
                'category': 'Functional',
                'purpose': 'Cookie consent preferences storage',
                'persistent': True,
                'expiry': '1 year',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            },
            'cookie': {
                'category': 'Functional',
                'purpose': 'Cookie preferences and settings',
                'persistent': True,
                'expiry': '1 year',
                'privacy_risk': 'Low',
                'gdpr_basis': 'Strictly necessary'
            }
        }
        
        # Check for pattern matches
        for pattern, info in patterns.items():
            if pattern in cookie_name_lower:
                return info
        
        # Default categorization for unknown cookies
        return {
            'category': 'Functional',
            'purpose': f'Website functionality cookie ({cookie_name})',
            'persistent': True,
            'expiry': 'Unknown',
            'privacy_risk': 'Medium',
            'gdpr_basis': 'Review required - may need consent'
        }

    def set_progress_callback(self, callback_function):
        """
        Set a callback function for progress updates during website scanning.
        
        Args:
            callback_function: A function that takes current, total, and current URL
        """
        self.progress_callback = callback_function
    
    def scan_website(self, url: str, follow_links: bool = True) -> Dict[str, Any]:
        """
        Perform a comprehensive scan of a website.
        
        Args:
            url: The URL of the website to scan
            follow_links: Whether to follow links during crawling (default: True)
            
        Returns:
            Dictionary with comprehensive scan results
        """
        # Initialize scan data
        self.start_time = datetime.now()
        self.is_running = True
        
        # Generate a unique scan ID
        scan_id = hashlib.md5(f"{url}:{self.start_time.isoformat()}".encode()).hexdigest()[:10]
        
        # Parse and normalize the starting URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = f"https://{url}"
            parsed_url = urlparse(url)
        
        base_domain = parsed_url.netloc
        base_url = f"{parsed_url.scheme}://{base_domain}"
        
        # Initialize scan data structures
        visited_urls = set()
        pages_data = []
        findings = []
        cookies = {}
        trackers = {}
        all_links = set()
        same_domain_links = set()
        external_links = set()
        
        # Queue for BFS crawling
        queue = [(url, 0)]  # (url, depth)
        
        # Perform domain registration and DNS checks
        domain_info = self._check_domain_info(base_domain)
        
        # Scan the website by following links
        page_count = 0
        
        # Report initial progress
        if self.progress_callback:
            self.progress_callback(0, self.max_pages, url)
        
        while queue and page_count < self.max_pages and self.is_running:
            current_url, depth = queue.pop(0)
            
            # Skip if URL already visited or depth exceeded
            if current_url in visited_urls or depth > self.max_depth:
                continue
            
            visited_urls.add(current_url)
            
            # Scan the current page
            logger.info(f"Scanning page: {current_url}")
            
            try:
                # Respect crawl delay
                time.sleep(self.crawl_delay)
                
                # Fetch the page
                response = self.session.get(current_url, timeout=10)
                
                # Skip non-HTML responses
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    continue
                
                # Analyze the page
                page_data = self._analyze_page(current_url, response.text, depth)
                pages_data.append(page_data)
                
                # Extract and analyze cookies
                self._current_findings = []  # Temporary storage for cookie findings
                page_cookies = self._extract_cookies(response)
                for cookie_name, cookie_data in page_cookies.items():
                    cookies[cookie_name] = cookie_data
                
                # Add any cookie findings to the main findings list
                findings.extend(self._current_findings)
                delattr(self, '_current_findings')
                
                # Find trackers
                page_trackers = page_data.get('trackers', [])
                for tracker in page_trackers:
                    tracker_name = tracker.get('name')
                    if tracker_name:
                        trackers[tracker_name] = tracker
                
                # Add findings from the page
                page_findings = page_data.get('findings', [])
                findings.extend(page_findings)
                
                # Update links
                all_links.update(page_data.get('all_links', []))
                same_domain_links.update(page_data.get('same_domain_links', []))
                external_links.update(page_data.get('external_links', []))
                
                # Follow links if enabled
                if follow_links and depth < self.max_depth:
                    for link in page_data.get('same_domain_links', []):
                        if link not in visited_urls:
                            queue.append((link, 0))
                
                # Increment page count
                page_count += 1
                
                # Report progress
                if self.progress_callback:
                    self.progress_callback(page_count, self.max_pages, current_url)
                    
            except Exception as e:
                logger.error(f"Error scanning {current_url}: {str(e)}")
                findings.append({
                    'type': 'error',
                    'url': current_url,
                    'location': f"Page Access Error: {current_url}",
                    'element': 'page request',
                    'description': f"Failed to scan page: {str(e)}",
                    'severity': 'Medium'
                })
        
        # Check SSL/TLS configuration
        ssl_info = None
        if self.check_ssl:
            ssl_info = self._check_ssl(base_url)
        
        # Summarize findings
        self.is_running = False
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Generate statistics
        stats = {
            'pages_scanned': page_count,
            'total_cookies': len(cookies),
            'total_trackers': len(trackers),
            'total_findings': len(findings),
            'total_links': len(all_links),
            'internal_links': len(same_domain_links),
            'external_links': len(external_links),
            'scan_duration_seconds': duration
        }
        
        # Categorize cookies
        cookie_categories = self._categorize_cookies(cookies)
        
        # Generate the final scan results
        scan_results = {
            'scan_id': scan_id,
            'scan_time': self.start_time.isoformat(),
            'completion_time': end_time.isoformat(),
            'duration_seconds': duration,
            'url': url,
            'base_domain': base_domain,
            'pages_data': pages_data,
            'findings': findings,
            'cookies': cookies,
            'cookie_categories': cookie_categories,
            'trackers': list(trackers.values()),
            'links': {
                'all': list(all_links),
                'internal': list(same_domain_links),
                'external': list(external_links)
            },
            'domain_info': domain_info,
            'ssl_info': ssl_info,
            'stats': stats,
            'scan_type': 'website',
            'security_checks_summary': getattr(self, '_security_checks_summary', [])
        }
        
        # Integrate cost savings analysis
        try:
            from services.cost_savings_calculator import integrate_cost_savings_into_report
            scan_results = integrate_cost_savings_into_report(scan_results, 'website', 'Netherlands')
        except Exception as e:
            logger.warning(f"Cost savings integration failed: {e}")
        
        return scan_results
    
    def _analyze_page(self, url: str, html_content: str, depth: int) -> Dict[str, Any]:
        """
        Analyze a single webpage for privacy issues.
        
        Args:
            url: The URL of the page
            html_content: The HTML content of the page
            depth: The crawl depth
            
        Returns:
            Dictionary with page analysis results
        """
        # Parse the URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract page title and metadata
        title = soup.title.text.strip() if soup.title else "No title"
        
        meta_description = None
        meta_tags = []
        for meta in soup.find_all('meta'):
            meta_dict = {key: meta.get(key) for key in meta.attrs}
            meta_tags.append(meta_dict)
            if meta.get('name') == 'description':
                meta_description = meta.get('content', '')
        
        # Extract links
        all_links = set()
        same_domain_links = set()
        external_links = set()
        
        for link in soup.find_all('a', href=True):
            href = link.get('href').strip()
            
            # Skip empty links, anchors, javascript, and mailto
            if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            # Normalize the URL
            absolute_url = urljoin(url, href)
            parsed_link = urlparse(absolute_url)
            
            # Skip non-HTTP(S) links
            if parsed_link.scheme not in ('http', 'https'):
                continue
            
            clean_url = f"{parsed_link.scheme}://{parsed_link.netloc}{parsed_link.path}"
            if parsed_link.query:
                clean_url += f"?{parsed_link.query}"
                
            all_links.add(clean_url)
            
            # Classify as internal or external
            if parsed_link.netloc == domain:
                same_domain_links.add(clean_url)
            else:
                external_links.add(clean_url)
        
        # Detect trackers and cookies in the JavaScript
        scripts = soup.find_all('script')
        trackers = []
        findings = []
        
        # Check for inline scripts containing tracker patterns
        for script in scripts:
            # Check for src attribute
            src = script.get('src', '')
            if src:
                # Check external script sources against known trackers
                for tracker_name, tracker_info in self.known_trackers.items():
                    for domain_pattern in tracker_info['domains']:
                        if domain_pattern in src:
                            trackers.append({
                                'name': tracker_name,
                                'url': src,
                                'type': 'external',
                                'found_on': url,
                                'purpose': tracker_info.get('purpose', 'Analytics and tracking'),
                                'privacy_risk': tracker_info.get('privacy_risk', 'Medium'),
                                'data_collected': tracker_info.get('data_collected', 'User behavior data'),
                                'gdpr_basis': tracker_info.get('gdpr_basis', 'Consent or legitimate interest required')
                            })
                            # Map privacy_risk to severity level (appropriate for website scanning)
                            privacy_risk = tracker_info.get('privacy_risk', 'Medium')
                            severity_map = {'High': 'High', 'Medium': 'Medium', 'Low': 'Low'}
                            severity = severity_map.get(privacy_risk, 'Medium')
                            
                            findings.append({
                                'type': 'tracker',
                                'subtype': tracker_name,
                                'url': url,
                                'location': url,
                                'location_detail': f"External Script: {src}",
                                'element': 'script[src]',
                                'description': f"External tracker script from {tracker_name}",
                                'severity': severity,
                                'privacy_risk': privacy_risk,
                                'gdpr_article': 'Art. 6(1)(a), Art. 7'
                            })
                            break
            
            # Check inline script content for tracker patterns
            elif script.string:
                script_content = script.string
                for tracker_name, tracker_info in self.known_trackers.items():
                    for pattern in tracker_info['patterns']:
                        if pattern in script_content:
                            trackers.append({
                                'name': tracker_name,
                                'type': 'inline',
                                'found_on': url,
                                'purpose': tracker_info.get('purpose', 'Analytics and tracking'),
                                'privacy_risk': tracker_info.get('privacy_risk', 'Medium'),
                                'data_collected': tracker_info.get('data_collected', 'User behavior data'),
                                'gdpr_basis': tracker_info.get('gdpr_basis', 'Consent or legitimate interest required')
                            })
                            # Map privacy_risk to severity level (appropriate for website scanning)
                            privacy_risk = tracker_info.get('privacy_risk', 'Medium')
                            severity_map = {'High': 'High', 'Medium': 'Medium', 'Low': 'Low'}
                            severity = severity_map.get(privacy_risk, 'Medium')
                            
                            findings.append({
                                'type': 'tracker',
                                'subtype': tracker_name,
                                'url': url,
                                'location': url,
                                'location_detail': f"Inline Script Pattern: {pattern}",
                                'element': 'script[inline]',
                                'description': f"Inline tracker script for {tracker_name}",
                                'severity': severity,
                                'privacy_risk': privacy_risk,
                                'gdpr_article': 'Art. 6(1)(a), Art. 7'
                            })
                            break
        
        # Detect consent management platforms
        consent_management = []
        for platform in self.consent_platforms:
            for pattern in platform['patterns']:
                if pattern in html_content:
                    consent_management.append({
                        'name': platform['name'],
                        'found_on': url
                    })
                    findings.append({
                        'type': 'consent_management',
                        'subtype': platform['name'],
                        'url': url,
                        'location': url,
                        'location_detail': f"CMP Pattern: {pattern}",
                        'element': 'consent platform',
                        'description': f"Using {platform['name']} consent management platform",
                        'severity': 'Info',
                        'gdpr_article': 'Art. 7, Art. 13'
                    })
                    break
        
        # Check for tracking pixels
        img_tags = soup.find_all('img')
        tracking_pixels = []
        
        for img in img_tags:
            src = img.get('src', '')
            height = img.get('height', '')
            width = img.get('width', '')
            
            # Check for 1x1 pixel images or known tracking domains
            if (height == '1' and width == '1') or ('pixel' in src.lower()):
                tracking_pixels.append({
                    'url': src,
                    'found_on': url
                })
                findings.append({
                    'type': 'tracking_pixel',
                    'url': url,
                    'location': url,
                    'location_detail': f"Image Element: {src}",
                    'element': 'img[1x1]',
                    'description': f"Tracking pixel detected: {src}",
                    'severity': 'High',
                    'privacy_risk': 'High',
                    'gdpr_article': 'Art. 6(1)(a), Art. 7'
                })
        
        # Extract main text content
        try:
            main_content = extract(html_content) or "No content extracted"
        except:
            main_content = "Failed to extract content"
        
        # Check for privacy-related content
        privacy_terms = {
            'privacy_policy': ['privacy', 'privacy policy', 'privacy statement', 'data policy', 'data protection'],
            'cookie_policy': ['cookie', 'cookie policy', 'cookie statement', 'cookie notice', 'cookie preferences'],
            'terms_of_service': ['terms', 'terms of service', 'terms of use', 'terms and conditions', 'legal'],
            'gdpr': ['gdpr', 'general data protection regulation', 'data protection', 'eu regulation']
        }
        
        privacy_links = {}
        
        for link in soup.find_all('a', href=True):
            href = link.get('href').strip()
            text = link.get_text().lower()
            
            for policy_type, terms in privacy_terms.items():
                if any(term in text for term in terms):
                    absolute_url = urljoin(url, href)
                    privacy_links[policy_type] = absolute_url
                    break
        
        # Check for cookie banner
        cookie_banner = None
        cookie_banner_selectors = [
            '#cookie-banner', '.cookie-banner', '#cookieBanner', '.cookieBanner',
            '#cookie-notice', '.cookie-notice', '#cookieNotice', '.cookieNotice',
            '#gdpr-banner', '.gdpr-banner', '#gdprBanner', '.gdprBanner',
            '#cookie-consent', '.cookie-consent', '#cookieConsent', '.cookieConsent',
            '[class*="cookie"]', '[id*="cookie"]', '[class*="gdpr"]', '[id*="gdpr"]',
            '[class*="consent"]', '[id*="consent"]'
        ]
        
        for selector in cookie_banner_selectors:
            elements = soup.select(selector)
            if elements:
                cookie_banner = {
                    'found': True,
                    'selector': selector,
                    'count': len(elements),
                    'text': elements[0].get_text()[:200] + '...' if len(elements[0].get_text()) > 200 else elements[0].get_text()
                }
                break
        
        # Scan page content for PII (BSN, email, phone, etc.)
        pii_findings = self._scan_content_for_pii(main_content, url)
        findings.extend(pii_findings)
        
        # Scan for web vulnerabilities
        vulnerability_findings = self._scan_for_vulnerabilities(url, html_content, soup)
        findings.extend(vulnerability_findings)
        
        # Return the page analysis results
        return {
            'url': url,
            'depth': depth,
            'title': title,
            'meta_description': meta_description,
            'meta_tags': meta_tags,
            'all_links': all_links,
            'same_domain_links': same_domain_links,
            'external_links': external_links,
            'trackers': trackers,
            'consent_management': consent_management,
            'tracking_pixels': tracking_pixels,
            'privacy_links': privacy_links,
            'cookie_banner': cookie_banner,
            'main_content_sample': main_content[:1000] + '...' if len(main_content) > 1000 else main_content,
            'findings': findings
        }
    
    def _extract_cookies(self, response) -> Dict[str, Any]:
        """
        Extract cookies from a response.
        
        Args:
            response: The HTTP response object
            
        Returns:
            Dictionary of cookies with metadata
        """
        cookies = {}
        
        for cookie in response.cookies:
            # Skip if cookie already processed
            if cookie.name in cookies:
                continue
                
            # Analyze cookie properties
            secure = cookie.secure
            httponly = cookie.has_nonstandard_attr('httponly')
            samesite = cookie.get_nonstandard_attr('samesite', None)
            
            expiry = None
            if cookie.expires:
                try:
                    expiry = datetime.fromtimestamp(cookie.expires).isoformat()
                except:
                    expiry = str(cookie.expires)
            
            # Categorize the cookie using comprehensive database
            cookie_info = self._categorize_cookie(cookie.name, cookie.value)
            
            # Evaluate cookie compliance
            compliance_issues = []
            if not secure:
                compliance_issues.append("Cookie not marked as Secure")
            if not httponly and cookie_info['category'] == 'Essential':
                compliance_issues.append("Essential cookie not marked as HttpOnly")
            if not samesite and cookie_info['category'] != 'Essential':
                compliance_issues.append("Missing SameSite attribute")
            if cookie_info['category'] in ['Marketing', 'Analytics'] and not samesite == 'None':
                compliance_issues.append("Tracking cookie should use SameSite=None")
            
            # Add cookie data with comprehensive information
            cookies[cookie.name] = {
                'name': cookie.name,
                'domain': cookie.domain,
                'path': cookie.path,
                'value_length': len(cookie.value),
                'secure': secure,
                'httponly': httponly,
                'samesite': samesite,
                'expiry': expiry or cookie_info.get('expiry', 'Session'),
                'session': cookie.expires is None,
                'category': cookie_info.get('category', 'Functional'),
                'purpose': cookie_info.get('purpose', 'Website functionality'),
                'persistent': cookie_info.get('persistent', True),
                'privacy_risk': cookie_info.get('privacy_risk', 'Medium'),
                'gdpr_basis': cookie_info.get('gdpr_basis', 'Review required'),
                'compliance_issues': compliance_issues
            }
            
            # Add cookie findings based on privacy risk
            if cookie_info.get('privacy_risk') in ['High', 'Critical']:
                # High-risk cookies should generate findings (appropriate for website scanning)
                privacy_risk = cookie_info.get('privacy_risk', 'Medium')
                severity_map = {'High': 'High', 'Critical': 'High', 'Medium': 'Medium', 'Low': 'Low'}
                severity = severity_map.get(privacy_risk, 'Medium')
                
                # Create finding for high-risk cookie
                cookie_finding = {
                    'type': 'cookie',
                    'subtype': 'high_risk_cookie',
                    'url': response.url,
                    'location': response.url,
                    'location_detail': f"Cookie: {cookie.name}",
                    'element': 'http-cookie',
                    'description': f"High-risk cookie detected: {cookie.name} - {cookie_info.get('purpose', 'Tracking/analytics')}",
                    'severity': severity,
                    'privacy_risk': privacy_risk,
                    'gdpr_article': 'Art. 6(1)(a), Art. 7',
                    'recommendation': f"Ensure explicit consent before setting {cookie.name} cookie"
                }
                
                # Add to page findings if we have access to findings list
                # This will be captured by the calling function
                if hasattr(self, '_current_findings'):
                    self._current_findings.append(cookie_finding)
        
        return cookies
    

    
    def _categorize_cookies(self, cookies: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Categorize all cookies.
        
        Args:
            cookies: Dictionary of cookie data
            
        Returns:
            Dictionary with categories and cookie names
        """
        categories = {
            'essential': [],
            'functional': [],
            'analytics': [],
            'advertising': [],
            'social': [],
            'unknown': []
        }
        
        for cookie_name, cookie_data in cookies.items():
            category = cookie_data.get('category', 'unknown')
            categories.setdefault(category, []).append(cookie_name)
        
        return categories
    
    def generate_privacy_recommendations(self, scan_results: Dict[str, Any]) -> List[str]:
        """
        Generate comprehensive privacy compliance recommendations based on scan results.
        
        Args:
            scan_results: Complete scan results dictionary
            
        Returns:
            List of actionable privacy recommendations
        """
        recommendations = []
        
        # Cookie-related recommendations
        cookies = scan_results.get('cookies', {})
        if cookies:
            high_risk_cookies = [name for name, data in cookies.items() 
                               if data.get('privacy_risk', '').lower() == 'high']
            
            if high_risk_cookies:
                recommendations.append(
                    f"High-risk cookies detected ({len(high_risk_cookies)} found). "
                    "Ensure explicit consent is obtained before setting marketing/tracking cookies."
                )
            
            # Check for missing consent mechanisms
            consent_cookies = [name for name in cookies.keys() 
                             if 'consent' in name.lower() or 'cookie' in name.lower()]
            
            if not consent_cookies and len(cookies) > 2:
                recommendations.append(
                    "No cookie consent management detected. Implement a GDPR-compliant "
                    "cookie banner to obtain user consent for non-essential cookies."
                )
            
            # Security recommendations
            insecure_cookies = [name for name, data in cookies.items() 
                              if not data.get('secure', False)]
            
            if insecure_cookies:
                recommendations.append(
                    f"Security issue: {len(insecure_cookies)} cookies not marked as Secure. "
                    "Add Secure flag to prevent transmission over unencrypted connections."
                )
        
        # Tracker-related recommendations
        trackers = scan_results.get('trackers', {})
        if trackers:
            marketing_trackers = [name for name, data in trackers.items() 
                                if data.get('purpose', '').lower().find('marketing') != -1]
            
            if marketing_trackers:
                recommendations.append(
                    f"Marketing trackers detected ({len(marketing_trackers)} found). "
                    "Ensure these are only loaded after obtaining user consent."
                )
        
        # Privacy policy recommendations
        findings = scan_results.get('findings', [])
        privacy_policy_found = any(f.get('type') == 'privacy_policy' for f in findings)
        
        if not privacy_policy_found:
            recommendations.append(
                "No privacy policy detected. Create and prominently link a comprehensive "
                "privacy policy explaining data collection and processing activities."
            )
        
        # SSL/Security recommendations
        ssl_info = scan_results.get('ssl_info', {})
        if ssl_info and not ssl_info.get('valid', True):
            recommendations.append(
                "SSL/TLS configuration issues detected. Ensure valid SSL certificate "
                "and secure HTTPS implementation for all pages."
            )
        
        # General GDPR compliance recommendations
        if len(recommendations) == 0:
            recommendations.append(
                "Basic privacy compliance appears adequate. Consider regular privacy "
                "audits and staying updated on data protection regulations."
            )
        else:
            recommendations.append(
                "Review and update your privacy policy to reflect current data "
                "processing activities and ensure ongoing GDPR compliance."
            )
        
        return recommendations
    
    def _scan_for_vulnerabilities(self, url: str, html_content: str, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Scan page for common web vulnerabilities by analyzing HTML, forms, and scripts.
        
        Args:
            url: The page URL being analyzed
            html_content: Raw HTML content of the page
            soup: BeautifulSoup parsed HTML object
            
        Returns:
            List of vulnerability findings
        """
        findings = []
        parsed_url = urlparse(url)
        forms = soup.find_all('form')
        scripts = soup.find_all('script')
        links = soup.find_all('a', href=True)
        inputs = soup.find_all('input')

        check_counts_before = {}
        vuln_checks_order = [
            ('SQL Injection', 'CWE-89', 'A03:2021 - Injection'),
            ('XSS (Cross-Site Scripting)', 'CWE-79', 'A03:2021 - Injection'),
            ('Broken Authentication', 'CWE-287', 'A07:2021 - Identification and Authentication Failures'),
            ('Broken Session Management', 'CWE-384', 'A07:2021 - Identification and Authentication Failures'),
            ('Access Control Bypass', 'CWE-284', 'A01:2021 - Broken Access Control'),
            ('Open URL Redirect', 'CWE-601', 'A01:2021 - Broken Access Control'),
            ('Directory Traversal', 'CWE-22', 'A01:2021 - Broken Access Control'),
            ('SSRF (Server-Side Request Forgery)', 'CWE-918', 'A10:2021 - Server-Side Request Forgery'),
            ('RCE (Remote Command Execution)', 'CWE-78', 'A03:2021 - Injection'),
            ('Business Logic Error', 'CWE-840', 'A04:2021 - Insecure Design'),
        ]

        # 1. SQL Injection Detection
        for form in forms:
            action = form.get('action', '')
            method = (form.get('method', 'get')).lower()
            form_inputs = form.find_all('input')
            text_inputs = [i for i in form_inputs if i.get('type', 'text') in ('text', 'search', 'hidden', '')]
            form_classes = form.get('class', [])
            form_class_str = ' '.join(form_classes) if isinstance(form_classes, list) else str(form_classes or '')
            form_text = (action.lower() + ' ' + (form.get('id', '') or '').lower() + ' ' + form_class_str.lower())
            search_indicators = any(
                kw in form_text
                for kw in ['search', 'query', 'filter', 'lookup', 'find']
            ) if action else False
            
            if text_inputs and method == 'get' and search_indicators:
                for inp in text_inputs:
                    input_name = inp.get('name', '')
                    if input_name and any(kw in input_name.lower() for kw in ['q', 'query', 'search', 'keyword', 'filter', 'id', 'select']):
                        findings.append({
                            'type': 'vulnerability',
                            'subtype': 'sql_injection',
                            'url': url,
                            'location': url,
                            'location_detail': f"Form action: {action or '(self)'} with input '{input_name}'",
                            'element': 'form',
                            'description': f"Potential SQL injection risk: search/query form submits user input via GET parameter '{input_name}' without apparent sanitization",
                            'severity': 'Critical',
                            'privacy_risk': 'Critical',
                            'gdpr_article': 'Art. 32 - Security of processing',
                            'vulnerability_type': 'SQL Injection',
                            'owasp_category': 'A03:2021 - Injection',
                            'recommendation': 'Use parameterized queries/prepared statements. Validate and sanitize all user inputs server-side.',
                            'cwe_id': 'CWE-89'
                        })
                        break

        if parsed_url.query:
            sql_params = [p.split('=')[0] for p in parsed_url.query.split('&') if '=' in p]
            suspicious_params = [p for p in sql_params if any(kw in p.lower() for kw in ['id', 'select', 'where', 'order', 'sort', 'table', 'column', 'union'])]
            if suspicious_params:
                findings.append({
                    'type': 'vulnerability',
                    'subtype': 'sql_injection',
                    'url': url,
                    'location': url,
                    'location_detail': f"URL parameters: {', '.join(suspicious_params)}",
                    'element': 'url',
                    'description': f"URL contains parameters with SQL-related names ({', '.join(suspicious_params)}) that may be vulnerable to injection",
                    'severity': 'Critical',
                    'privacy_risk': 'Critical',
                    'gdpr_article': 'Art. 32 - Security of processing',
                    'vulnerability_type': 'SQL Injection',
                    'owasp_category': 'A03:2021 - Injection',
                    'recommendation': 'Use parameterized queries. Never construct SQL from URL parameters directly.',
                    'cwe_id': 'CWE-89'
                })

        # 2. XSS Detection
        event_handler_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur', 'onsubmit', 'onchange', 'onkeyup', 'onkeydown']
        inline_handlers = []
        for attr in event_handler_attrs:
            elements_with_handler = soup.find_all(attrs={attr: True})
            for el in elements_with_handler:
                handler_val = el.get(attr, '')
                if any(dangerous in handler_val.lower() for dangerous in ['eval(', 'document.cookie', 'document.write', 'innerhtml', 'location.href', 'window.location']):
                    inline_handlers.append((attr, el.name, handler_val[:100]))

        if inline_handlers:
            for attr, tag, val in inline_handlers[:3]:
                findings.append({
                    'type': 'vulnerability',
                    'subtype': 'xss',
                    'url': url,
                    'location': url,
                    'location_detail': f"Inline event handler: {attr} on <{tag}>",
                    'element': tag,
                    'description': f"Unsafe inline event handler '{attr}' on <{tag}> contains dangerous JavaScript operations",
                    'severity': 'High',
                    'privacy_risk': 'High',
                    'gdpr_article': 'Art. 32 - Security of processing',
                    'vulnerability_type': 'XSS (Cross-Site Scripting)',
                    'owasp_category': 'A03:2021 - Injection',
                    'recommendation': 'Remove inline event handlers. Use Content Security Policy (CSP) headers and sanitize all user inputs.',
                    'cwe_id': 'CWE-79'
                })

        for script in scripts:
            if script.string:
                script_text = script.string
                xss_patterns = [
                    (r'\.innerHTML\s*=\s*[^;]*(?:location|document\.URL|document\.referrer|window\.name)', 'innerHTML assignment from user-controlled source'),
                    (r'document\.write\s*\(\s*(?:location|document\.URL|unescape|decodeURI)', 'document.write with user-controlled input'),
                    (r'eval\s*\(\s*(?:location|document\.URL|window\.name|decodeURI)', 'eval() with user-controlled input'),
                ]
                for pattern, desc in xss_patterns:
                    if re.search(pattern, script_text, re.IGNORECASE):
                        findings.append({
                            'type': 'vulnerability',
                            'subtype': 'xss',
                            'url': url,
                            'location': url,
                            'location_detail': f"Script: {desc}",
                            'element': 'script',
                            'description': f"Potential DOM-based XSS: {desc}",
                            'severity': 'High',
                            'privacy_risk': 'High',
                            'gdpr_article': 'Art. 32 - Security of processing',
                            'vulnerability_type': 'XSS (Cross-Site Scripting)',
                            'owasp_category': 'A03:2021 - Injection',
                            'recommendation': 'Sanitize all user inputs before DOM insertion. Use textContent instead of innerHTML.',
                            'cwe_id': 'CWE-79'
                        })
                        break

        # 3. Broken Authentication
        login_forms = [f for f in forms if any(
            f.find('input', {'type': t}) for t in ['password']
        )]
        for form in login_forms:
            csrf_input = form.find('input', {'name': re.compile(r'csrf|token|_token|authenticity_token|__RequestVerificationToken', re.I)})
            if not csrf_input:
                findings.append({
                    'type': 'vulnerability',
                    'subtype': 'broken_authentication',
                    'url': url,
                    'location': url,
                    'location_detail': f"Login form action: {form.get('action', '(self)')}",
                    'element': 'form',
                    'description': 'Login form missing CSRF token protection, potentially vulnerable to cross-site request forgery attacks',
                    'severity': 'High',
                    'privacy_risk': 'High',
                    'gdpr_article': 'Art. 32 - Security of processing',
                    'vulnerability_type': 'Broken Authentication',
                    'owasp_category': 'A07:2021 - Identification and Authentication Failures',
                    'recommendation': 'Implement CSRF tokens in all authentication forms. Use anti-forgery tokens.',
                    'cwe_id': 'CWE-287'
                })

            password_fields = form.find_all('input', {'type': 'password'})
            for pwd_field in password_fields:
                if pwd_field.get('autocomplete', '').lower() not in ('off', 'new-password', 'current-password'):
                    findings.append({
                        'type': 'vulnerability',
                        'subtype': 'broken_authentication',
                        'url': url,
                        'location': url,
                        'location_detail': f"Password field: {pwd_field.get('name', 'unnamed')}",
                        'element': 'input[password]',
                        'description': 'Password field without proper autocomplete attribute may allow browser to cache credentials',
                        'severity': 'Medium',
                        'privacy_risk': 'Medium',
                        'gdpr_article': 'Art. 32 - Security of processing',
                        'vulnerability_type': 'Broken Authentication',
                        'owasp_category': 'A07:2021 - Identification and Authentication Failures',
                        'recommendation': 'Set autocomplete="off" or "current-password"/"new-password" on password fields.',
                        'cwe_id': 'CWE-287'
                    })
                    break

            if parsed_url.scheme == 'http':
                findings.append({
                    'type': 'vulnerability',
                    'subtype': 'broken_authentication',
                    'url': url,
                    'location': url,
                    'location_detail': 'Login page served over HTTP',
                    'element': 'page',
                    'description': 'Login page served over unencrypted HTTP connection, credentials can be intercepted',
                    'severity': 'Critical',
                    'privacy_risk': 'Critical',
                    'gdpr_article': 'Art. 32 - Security of processing',
                    'vulnerability_type': 'Broken Authentication',
                    'owasp_category': 'A07:2021 - Identification and Authentication Failures',
                    'recommendation': 'Serve all authentication pages over HTTPS. Implement HSTS headers.',
                    'cwe_id': 'CWE-287'
                })

        # 4. Broken Session Management
        if 'session' in parsed_url.query.lower() or 'sid=' in parsed_url.query.lower() or 'jsessionid' in parsed_url.query.lower() or 'phpsessid' in parsed_url.query.lower():
            findings.append({
                'type': 'vulnerability',
                'subtype': 'broken_session_management',
                'url': url,
                'location': url,
                'location_detail': f"Session token exposed in URL: {parsed_url.query[:100]}",
                'element': 'url',
                'description': 'Session identifier exposed in URL parameters, vulnerable to session fixation and leakage through referrer headers',
                'severity': 'High',
                'privacy_risk': 'High',
                'gdpr_article': 'Art. 32 - Security of processing',
                'vulnerability_type': 'Broken Session Management',
                'owasp_category': 'A07:2021 - Identification and Authentication Failures',
                'recommendation': 'Store session tokens in cookies with Secure and HttpOnly flags. Never pass session IDs in URLs.',
                'cwe_id': 'CWE-384'
            })

        for link in links:
            href = link.get('href', '')
            if any(token in href.lower() for token in ['sessionid=', 'sid=', 'jsessionid=', 'phpsessid=', 'token=']):
                findings.append({
                    'type': 'vulnerability',
                    'subtype': 'broken_session_management',
                    'url': url,
                    'location': url,
                    'location_detail': f"Link with session token: {href[:100]}",
                    'element': 'a',
                    'description': 'Internal link contains session token in URL, risking session leakage',
                    'severity': 'High',
                    'privacy_risk': 'High',
                    'gdpr_article': 'Art. 32 - Security of processing',
                    'vulnerability_type': 'Broken Session Management',
                    'owasp_category': 'A07:2021 - Identification and Authentication Failures',
                    'recommendation': 'Remove session tokens from URLs. Use cookie-based session management.',
                    'cwe_id': 'CWE-384'
                })
                break

        # 5. Access Control Bypass
        admin_patterns = ['/admin', '/administrator', '/wp-admin', '/cpanel', '/phpmyadmin', '/manager', '/console', '/dashboard/admin']
        for link in links:
            href = link.get('href', '')
            full_url = urljoin(url, href)
            path = urlparse(full_url).path.lower()
            if any(pattern in path for pattern in admin_patterns):
                findings.append({
                    'type': 'vulnerability',
                    'subtype': 'access_control_bypass',
                    'url': url,
                    'location': url,
                    'location_detail': f"Exposed admin link: {href}",
                    'element': 'a',
                    'description': f"Publicly accessible link to administrative panel found: {href}",
                    'severity': 'Medium',
                    'privacy_risk': 'Medium',
                    'gdpr_article': 'Art. 32 - Security of processing',
                    'vulnerability_type': 'Access Control Bypass',
                    'owasp_category': 'A01:2021 - Broken Access Control',
                    'recommendation': 'Restrict admin panel access by IP, require strong authentication, and remove public links to admin areas.',
                    'cwe_id': 'CWE-284'
                })
                break

        hidden_inputs = soup.find_all('input', {'type': 'hidden'})
        for hidden in hidden_inputs:
            name = (hidden.get('name', '') or '').lower()
            value = (hidden.get('value', '') or '').lower()
            if any(kw in name for kw in ['role', 'admin', 'is_admin', 'isadmin', 'privilege', 'permission', 'access_level', 'user_type']):
                findings.append({
                    'type': 'vulnerability',
                    'subtype': 'access_control_bypass',
                    'url': url,
                    'location': url,
                    'location_detail': f"Hidden field: {hidden.get('name')}={hidden.get('value', '')}",
                    'element': 'input[hidden]',
                    'description': f"Hidden form field '{hidden.get('name')}' with role/privilege value can be manipulated client-side",
                    'severity': 'High',
                    'privacy_risk': 'High',
                    'gdpr_article': 'Art. 32 - Security of processing',
                    'vulnerability_type': 'Access Control Bypass',
                    'owasp_category': 'A01:2021 - Broken Access Control',
                    'recommendation': 'Never use hidden fields for access control. Enforce authorization server-side.',
                    'cwe_id': 'CWE-284'
                })

        title_text = (soup.title.string if soup.title else '').lower()
        if 'index of' in title_text or 'directory listing' in title_text:
            findings.append({
                'type': 'vulnerability',
                'subtype': 'access_control_bypass',
                'url': url,
                'location': url,
                'location_detail': 'Directory listing enabled',
                'element': 'page',
                'description': 'Directory listing is enabled, exposing file structure and potentially sensitive files',
                'severity': 'Medium',
                'privacy_risk': 'Medium',
                'gdpr_article': 'Art. 32 - Security of processing',
                'vulnerability_type': 'Access Control Bypass',
                'owasp_category': 'A01:2021 - Broken Access Control',
                'recommendation': 'Disable directory listing in web server configuration.',
                'cwe_id': 'CWE-284'
            })

        # 6. Open URL Redirect
        redirect_params = ['url', 'redirect', 'next', 'returnurl', 'return_url', 'goto', 'dest', 'destination', 'redir', 'redirect_uri', 'continue', 'return_to']
        for link in links:
            href = link.get('href', '')
            try:
                link_parsed = urlparse(href)
                if link_parsed.query:
                    params = dict(p.split('=', 1) for p in link_parsed.query.split('&') if '=' in p)
                    for param_name in params:
                        if param_name.lower() in redirect_params:
                            param_val = params[param_name]
                            if param_val.startswith('http') or param_val.startswith('//') or param_val.startswith('%2f%2f'):
                                findings.append({
                                    'type': 'vulnerability',
                                    'subtype': 'open_redirect',
                                    'url': url,
                                    'location': url,
                                    'location_detail': f"Link with redirect param: {param_name}={param_val[:80]}",
                                    'element': 'a',
                                    'description': f"Open redirect vulnerability: parameter '{param_name}' accepts external URLs",
                                    'severity': 'Medium',
                                    'privacy_risk': 'Medium',
                                    'gdpr_article': 'Art. 32 - Security of processing',
                                    'vulnerability_type': 'Open URL Redirect',
                                    'owasp_category': 'A01:2021 - Broken Access Control',
                                    'recommendation': 'Validate redirect URLs against a whitelist. Only allow relative redirects or known trusted domains.',
                                    'cwe_id': 'CWE-601'
                                })
                                break
            except (ValueError, AttributeError):
                continue

        # 7. Directory Traversal
        for link in links:
            href = link.get('href', '')
            href_lower = href.lower()
            if any(kw in href_lower for kw in ['file=', 'path=', 'doc=', 'document=', 'folder=', 'root=', 'pg=', 'include=', 'page=', 'template=']):
                try:
                    link_parsed = urlparse(href)
                    if link_parsed.query:
                        params = dict(p.split('=', 1) for p in link_parsed.query.split('&') if '=' in p)
                        for param_name, param_val in params.items():
                            if param_name.lower() in ['file', 'path', 'doc', 'document', 'folder', 'root', 'include', 'template']:
                                if '..' in param_val or param_val.startswith('/') or '\\' in param_val:
                                    findings.append({
                                        'type': 'vulnerability',
                                        'subtype': 'directory_traversal',
                                        'url': url,
                                        'location': url,
                                        'location_detail': f"Path parameter: {param_name}={param_val[:80]}",
                                        'element': 'a',
                                        'description': f"Potential directory traversal: file path parameter '{param_name}' may allow access to arbitrary files",
                                        'severity': 'Medium',
                                        'privacy_risk': 'Medium',
                                        'gdpr_article': 'Art. 32 - Security of processing',
                                        'vulnerability_type': 'Directory Traversal',
                                        'owasp_category': 'A01:2021 - Broken Access Control',
                                        'recommendation': 'Validate file paths server-side. Use a whitelist of allowed files and reject path traversal sequences.',
                                        'cwe_id': 'CWE-22'
                                    })
                                    break
                except (ValueError, AttributeError):
                    continue

        for link in links:
            href = link.get('href', '').lower()
            if any(kw in href for kw in ['/download?', '/download/', '/getfile', '/readfile', '/fetch?', '/export?']):
                if 'file=' in href or 'path=' in href or 'name=' in href:
                    findings.append({
                        'type': 'vulnerability',
                        'subtype': 'directory_traversal',
                        'url': url,
                        'location': url,
                        'location_detail': f"File download endpoint: {href[:100]}",
                        'element': 'a',
                        'description': 'File download endpoint with filename parameter may be vulnerable to path traversal',
                        'severity': 'Medium',
                        'privacy_risk': 'Medium',
                        'gdpr_article': 'Art. 32 - Security of processing',
                        'vulnerability_type': 'Directory Traversal',
                        'owasp_category': 'A01:2021 - Broken Access Control',
                        'recommendation': 'Validate file download paths against a whitelist. Never serve files based on raw user input.',
                        'cwe_id': 'CWE-22'
                    })
                    break

        # 8. SSRF Detection
        for form in forms:
            form_inputs = form.find_all('input')
            for inp in form_inputs:
                inp_type = (inp.get('type', '') or '').lower()
                inp_name = (inp.get('name', '') or '').lower()
                inp_placeholder = (inp.get('placeholder', '') or '').lower()
                if inp_type == 'url' or any(kw in inp_name for kw in ['url', 'webhook', 'callback', 'endpoint', 'feed_url', 'import_url', 'fetch_url', 'proxy']):
                    findings.append({
                        'type': 'vulnerability',
                        'subtype': 'ssrf',
                        'url': url,
                        'location': url,
                        'location_detail': f"URL input field: {inp.get('name', 'unnamed')} in form action {form.get('action', '(self)')}",
                        'element': 'input',
                        'description': f"URL input field '{inp.get('name', '')}' may allow server-side request forgery if not properly validated",
                        'severity': 'High',
                        'privacy_risk': 'High',
                        'gdpr_article': 'Art. 32 - Security of processing',
                        'vulnerability_type': 'SSRF (Server-Side Request Forgery)',
                        'owasp_category': 'A10:2021 - Server-Side Request Forgery',
                        'recommendation': 'Validate and whitelist allowed URLs. Block requests to internal/private IP ranges. Use DNS resolution checks.',
                        'cwe_id': 'CWE-918'
                    })
                    break
                elif 'url' in inp_placeholder or 'webhook' in inp_placeholder:
                    findings.append({
                        'type': 'vulnerability',
                        'subtype': 'ssrf',
                        'url': url,
                        'location': url,
                        'location_detail': f"URL input field (by placeholder): {inp.get('name', 'unnamed')}",
                        'element': 'input',
                        'description': f"Input field accepting URLs (placeholder: '{inp_placeholder[:50]}') may allow SSRF attacks",
                        'severity': 'High',
                        'privacy_risk': 'High',
                        'gdpr_article': 'Art. 32 - Security of processing',
                        'vulnerability_type': 'SSRF (Server-Side Request Forgery)',
                        'owasp_category': 'A10:2021 - Server-Side Request Forgery',
                        'recommendation': 'Validate URLs against a whitelist. Block internal network access from user-supplied URLs.',
                        'cwe_id': 'CWE-918'
                    })
                    break

        # 9. RCE Detection
        for form in forms:
            action = (form.get('action', '') or '').lower()
            if any(kw in action for kw in ['exec', 'execute', 'run', 'cmd', 'command', 'shell', 'system', 'ping', 'eval']):
                findings.append({
                    'type': 'vulnerability',
                    'subtype': 'rce',
                    'url': url,
                    'location': url,
                    'location_detail': f"Form action with command execution pattern: {action}",
                    'element': 'form',
                    'description': f"Form action '{action}' suggests command execution functionality that may be vulnerable to RCE",
                    'severity': 'Critical',
                    'privacy_risk': 'Critical',
                    'gdpr_article': 'Art. 32 - Security of processing',
                    'vulnerability_type': 'RCE (Remote Command Execution)',
                    'owasp_category': 'A03:2021 - Injection',
                    'recommendation': 'Never pass user input to system commands. Use safe APIs instead of shell commands. Implement strict input validation.',
                    'cwe_id': 'CWE-78'
                })

        for script in scripts:
            if script.string:
                script_text = script.string
                rce_patterns = [
                    (r'eval\s*\(\s*(?:document\.|window\.|location\.|unescape|atob|String\.fromCharCode)', 'eval() with dynamic content'),
                    (r'new\s+Function\s*\(\s*(?:document\.|window\.|location\.)', 'new Function() with dynamic content'),
                    (r'setTimeout\s*\(\s*(?:document\.|location\.)', 'setTimeout with dynamic string execution'),
                ]
                for pattern, desc in rce_patterns:
                    if re.search(pattern, script_text, re.IGNORECASE):
                        findings.append({
                            'type': 'vulnerability',
                            'subtype': 'rce',
                            'url': url,
                            'location': url,
                            'location_detail': f"Script: {desc}",
                            'element': 'script',
                            'description': f"Potential code execution vulnerability: {desc}",
                            'severity': 'Critical',
                            'privacy_risk': 'Critical',
                            'gdpr_article': 'Art. 32 - Security of processing',
                            'vulnerability_type': 'RCE (Remote Command Execution)',
                            'owasp_category': 'A03:2021 - Injection',
                            'recommendation': 'Avoid eval(), new Function(), and setTimeout with string arguments. Use safe alternatives.',
                            'cwe_id': 'CWE-78'
                        })
                        break

        # 10. Business Logic Errors
        for form in forms:
            hidden_inputs_in_form = form.find_all('input', {'type': 'hidden'})
            for hidden in hidden_inputs_in_form:
                name = (hidden.get('name', '') or '').lower()
                if any(kw in name for kw in ['price', 'amount', 'total', 'cost', 'discount', 'rate', 'fee']):
                    findings.append({
                        'type': 'vulnerability',
                        'subtype': 'business_logic',
                        'url': url,
                        'location': url,
                        'location_detail': f"Hidden price field: {hidden.get('name')}={hidden.get('value', '')}",
                        'element': 'input[hidden]',
                        'description': f"Hidden field '{hidden.get('name')}' contains price/amount data that can be manipulated client-side",
                        'severity': 'Medium',
                        'privacy_risk': 'Medium',
                        'gdpr_article': 'Art. 32 - Security of processing',
                        'vulnerability_type': 'Business Logic Error',
                        'owasp_category': 'A04:2021 - Insecure Design',
                        'recommendation': 'Never trust client-side price values. Validate and calculate prices server-side from product database.',
                        'cwe_id': 'CWE-840'
                    })

            quantity_inputs = form.find_all('input', {'type': 'number'})
            for qty in quantity_inputs:
                name = (qty.get('name', '') or '').lower()
                min_val = qty.get('min')
                if any(kw in name for kw in ['quantity', 'qty', 'count', 'amount', 'num']) and min_val is None:
                    findings.append({
                        'type': 'vulnerability',
                        'subtype': 'business_logic',
                        'url': url,
                        'location': url,
                        'location_detail': f"Quantity input without min constraint: {qty.get('name')}",
                        'element': 'input[number]',
                        'description': f"Numeric input '{qty.get('name')}' lacks minimum value constraint, allowing negative quantities",
                        'severity': 'Medium',
                        'privacy_risk': 'Medium',
                        'gdpr_article': 'Art. 32 - Security of processing',
                        'vulnerability_type': 'Business Logic Error',
                        'owasp_category': 'A04:2021 - Insecure Design',
                        'recommendation': 'Set min="0" or min="1" on quantity fields. Validate quantities server-side.',
                        'cwe_id': 'CWE-840'
                    })

        security_checks_summary = []
        for vuln_name, cwe_id, owasp_cat in vuln_checks_order:
            found_count = sum(1 for f in findings if f.get('vulnerability_type') == vuln_name)
            security_checks_summary.append({
                'check': vuln_name,
                'cwe_id': cwe_id,
                'owasp_category': owasp_cat,
                'status': 'Issue Found' if found_count > 0 else 'Passed',
                'findings_count': found_count
            })

        if not hasattr(self, '_security_checks_summary'):
            self._security_checks_summary = security_checks_summary
        else:
            for new_check in security_checks_summary:
                for existing_check in self._security_checks_summary:
                    if existing_check['check'] == new_check['check']:
                        existing_check['findings_count'] += new_check['findings_count']
                        if new_check['status'] == 'Issue Found':
                            existing_check['status'] = 'Issue Found'
                        break

        return findings

    def _scan_content_for_pii(self, content: str, url: str) -> List[Dict[str, Any]]:
        """
        Scan page content for PII including Dutch BSN numbers with 11-proef validation.
        
        Args:
            content: The text content from the page
            url: The URL of the page
            
        Returns:
            List of PII findings
        """
        findings = []
        
        if not content or content == "No content extracted" or content == "Failed to extract content":
            return findings
        
        # Use centralized PII detection if available
        if PII_DETECTION_AVAILABLE:
            try:
                pii_items = identify_pii_in_text(content, self.region)
                for item in pii_items:
                    severity = 'Critical' if item.get('type') in ['BSN', 'Credit Card', 'SSN', 'Passport Number'] else 'High'
                    findings.append({
                        'type': 'pii_exposure',
                        'subtype': item.get('type', 'Unknown PII'),
                        'url': url,
                        'location': url,
                        'location_detail': 'Page Content',
                        'element': 'body',
                        'description': f"PII detected in page content: {item.get('type')}",
                        'severity': severity,
                        'privacy_risk': 'Critical' if item.get('type') == 'BSN' else 'High',
                        'gdpr_article': 'Art. 5(1)(f) - Integrity and confidentiality',
                        'uavg_article': 'Article 46' if item.get('type') == 'BSN' else None,
                        'recommendation': f"Remove or redact {item.get('type')} from public page content"
                    })
                return findings
            except Exception as e:
                logger.warning(f"PII detection module error: {e}")
        
        # Fallback: Direct BSN detection with 11-proef validation
        bsn_findings = self._detect_bsn_in_content(content, url)
        findings.extend(bsn_findings)
        
        # Detect other common PII patterns
        pii_patterns = {
            'EMAIL': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', 'Medium'),
            'PHONE_NL': (r'\b(?:\+31|0031|0)[\s-]?(?:[1-9]\d{1,2})[\s-]?\d{6,8}\b', 'Medium'),
            'IBAN': (r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b', 'High'),
            'CREDIT_CARD': (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'Critical')
        }
        
        for pii_type, (pattern, severity) in pii_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:5]:  # Limit to 5 matches per type
                findings.append({
                    'type': 'pii_exposure',
                    'subtype': pii_type,
                    'url': url,
                    'location': url,
                    'location_detail': 'Page Content',
                    'element': 'body',
                    'description': f"{pii_type} detected in publicly accessible page content",
                    'severity': severity,
                    'privacy_risk': severity,
                    'gdpr_article': 'Art. 5(1)(f) - Integrity and confidentiality',
                    'recommendation': f"Remove or redact {pii_type} from public page content"
                })
        
        return findings
    
    def _detect_bsn_in_content(self, content: str, url: str) -> List[Dict[str, Any]]:
        """
        Detect Dutch BSN numbers in page content with 11-proef validation.
        
        Args:
            content: The text content to scan
            url: The source URL
            
        Returns:
            List of BSN findings
        """
        findings = []
        
        # Pattern for explicit BSN mentions
        explicit_pattern = r'\b(?:BSN|Burgerservicenummer|burger\s*service\s*nummer)(?:[:\s-]+)?(\d{9})\b'
        for match in re.finditer(explicit_pattern, content, re.IGNORECASE):
            bsn = match.group(1) if match.lastindex else match.group(0)
            bsn = re.sub(r'\D', '', bsn)
            if len(bsn) == 9 and self._validate_bsn_11_proef(bsn):
                findings.append({
                    'type': 'pii_exposure',
                    'subtype': 'BSN',
                    'url': url,
                    'location': url,
                    'location_detail': 'Page Content',
                    'element': 'body',
                    'description': 'Dutch BSN (Burgerservicenummer) detected in publicly accessible page content',
                    'severity': 'Critical',
                    'privacy_risk': 'Critical',
                    'gdpr_article': 'Art. 87 - Processing of national identification number',
                    'uavg_article': 'Article 46 - Use of BSN',
                    'recommendation': 'Immediately remove BSN from public page content. BSN processing requires explicit legal basis under Dutch UAVG.',
                    'uavg_compliant': False
                })
        
        # Pattern for potential standalone 9-digit BSN numbers
        potential_pattern = r'\b(\d{9})\b'
        for match in re.finditer(potential_pattern, content):
            bsn = match.group(1)
            if self._validate_bsn_11_proef(bsn):
                # Avoid duplicates
                if not any(f.get('subtype') == 'BSN' for f in findings):
                    findings.append({
                        'type': 'pii_exposure',
                        'subtype': 'BSN',
                        'url': url,
                        'location': url,
                        'location_detail': 'Page Content',
                        'element': 'body',
                        'description': 'Potential Dutch BSN detected (passes 11-proef validation)',
                        'severity': 'Critical',
                        'privacy_risk': 'Critical',
                        'gdpr_article': 'Art. 87 - Processing of national identification number',
                        'uavg_article': 'Article 46 - Use of BSN',
                        'recommendation': 'Verify and remove if this is a BSN. BSN processing requires explicit legal basis under Dutch UAVG.',
                        'uavg_compliant': False
                    })
        
        return findings
    
    def _validate_bsn_11_proef(self, bsn: str) -> bool:
        """
        Validate Dutch BSN using the official 11-proef algorithm.
        
        The BSN must be exactly 9 digits.
        Checksum: (9*d1 + 8*d2 + 7*d3 + 6*d4 + 5*d5 + 4*d6 + 3*d7 + 2*d8 - 1*d9) mod 11 == 0
        
        Args:
            bsn: The BSN string to validate
            
        Returns:
            True if valid BSN, False otherwise
        """
        if not bsn.isdigit() or len(bsn) != 9:
            return False
        
        # Apply the official Dutch 11-proef
        total = 0
        for i in range(9):
            if i == 8:
                total -= int(bsn[i]) * 1
            else:
                total += int(bsn[i]) * (9 - i)
        
        return total % 11 == 0
    
    def _check_domain_info(self, domain: str) -> Dict[str, Any]:
        """
        Check domain registration information.
        
        Args:
            domain: The domain name to check
            
        Returns:
            Dictionary with domain registration information
        """
        # Extract the base domain without subdomains
        extracted = tldextract.extract(domain)
        base_domain = f"{extracted.domain}.{extracted.suffix}"
        
        domain_info = {
            'domain': base_domain,
            'registration': None,
            'registrar': None,
            'creation_date': None,
            'expiration_date': None,
            'dns_records': {}
        }
        
        # Get WHOIS information
        try:
            w = whois.whois(base_domain)
            domain_info['registration'] = {
                'registrar': w.registrar,
                'creation_date': w.creation_date.isoformat() if hasattr(w, 'creation_date') and w.creation_date else None,
                'expiration_date': w.expiration_date.isoformat() if hasattr(w, 'expiration_date') and w.expiration_date else None,
                'name_servers': w.name_servers if hasattr(w, 'name_servers') else None
            }
        except Exception as e:
            logger.warning(f"Failed to get WHOIS information for {base_domain}: {str(e)}")
            domain_info['registration'] = {'error': str(e)}
        
        # Get DNS records if enabled
        if self.check_dns:
            try:
                # Get A records
                try:
                    answers = dns.resolver.resolve(base_domain, 'A')
                    domain_info['dns_records']['A'] = [str(answer) for answer in answers]
                except Exception as e:
                    logger.warning(f"Failed to get A records for {base_domain}: {str(e)}")
                
                # Get MX records
                try:
                    answers = dns.resolver.resolve(base_domain, 'MX')
                    domain_info['dns_records']['MX'] = [str(answer) for answer in answers]
                except Exception as e:
                    logger.warning(f"Failed to get MX records for {base_domain}: {str(e)}")
                
                # Get TXT records
                try:
                    answers = dns.resolver.resolve(base_domain, 'TXT')
                    domain_info['dns_records']['TXT'] = [str(answer) for answer in answers]
                except Exception as e:
                    logger.warning(f"Failed to get TXT records for {base_domain}: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to get DNS records for {base_domain}: {str(e)}")
        
        return domain_info
    
    def _check_ssl(self, url: str) -> Dict[str, Any]:
        """
        Check SSL/TLS configuration.
        
        Args:
            url: The URL to check SSL for
            
        Returns:
            Dictionary with SSL/TLS information
        """
        ssl_info = {
            'enabled': False,
            'certificate': None,
            'expiry': None,
            'issuer': None,
            'protocols': [],
            'issues': []
        }
        
        try:
            response = requests.get(url, verify=True, timeout=10)
            
            # Check if HTTPS is enabled
            ssl_info['enabled'] = response.url.startswith('https://')
            
            if ssl_info['enabled']:
                # Unfortunately, requests doesn't provide detailed SSL/TLS info
                # Here we would need to use a library like pyOpenSSL or subprocess to openssl
                # For now, just mark that SSL is enabled
                ssl_info['certificate'] = "Valid (details not available)"
            else:
                ssl_info['issues'].append("HTTPS not enabled")
                
        except requests.exceptions.SSLError as e:
            ssl_info['issues'].append(f"SSL Error: {str(e)}")
        except Exception as e:
            ssl_info['issues'].append(f"Error checking SSL: {str(e)}")
        
        return ssl_info
    
    def cancel_scan(self):
        """Cancel the current scan if running"""
        self.is_running = False