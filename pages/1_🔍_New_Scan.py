"""
New Scan Page - Scanner Selection and Execution
DataGuardian Pro Multi-Page Architecture
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page_modules.auth_wrapper import require_authentication, show_license_check, track_page_view
from page_modules.scanner import render_scanner_interface

def main():
    """Main entry point for scanner page"""
    if not require_authentication():
        return
    
    show_license_check()
    track_page_view('new_scan')
    
    try:
        render_scanner_interface()
    except Exception as e:
        st.error(f"Error loading scanner page: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

main()
