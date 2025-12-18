"""
Results Page - Scan Results Display
DataGuardian Pro Multi-Page Architecture
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page_modules.auth_wrapper import require_authentication, show_license_check, track_page_view
from page_modules.results import render_results_page

def main():
    """Main entry point for results page"""
    if not require_authentication():
        return
    
    show_license_check()
    track_page_view('results')
    
    try:
        render_results_page()
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

main()
