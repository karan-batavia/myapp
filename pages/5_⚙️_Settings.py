"""
Settings Page - User Preferences and Configuration
DataGuardian Pro Multi-Page Architecture
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page_modules.auth_wrapper import require_authentication, show_license_check, track_page_view
from page_modules.settings import render_settings_page

def main():
    """Main entry point for settings page"""
    if not require_authentication():
        return
    
    show_license_check()
    track_page_view('settings')
    
    try:
        render_settings_page()
    except Exception as e:
        st.error(f"Error loading settings: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

main()
