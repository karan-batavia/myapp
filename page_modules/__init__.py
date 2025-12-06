"""
DataGuardian Pro - Page Modules
Modular page components extracted from the main application

This module provides organized page rendering functions that can be imported
and used throughout the application.
"""

from .dashboard import render_dashboard
from .scanner import render_scanner_interface
from .results import render_results_page, render_detailed_scan_view
from .history import render_history_page, render_history_trends
from .settings import render_settings_page
from .admin import render_admin_page
from .pricing import render_pricing_page, render_upgrade_page
from .privacy_rights import render_privacy_rights_page

__all__ = [
    'render_dashboard',
    'render_scanner_interface',
    'render_results_page',
    'render_detailed_scan_view',
    'render_history_page',
    'render_history_trends',
    'render_settings_page',
    'render_admin_page',
    'render_pricing_page',
    'render_upgrade_page',
    'render_privacy_rights_page'
]
