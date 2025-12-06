"""
Dashboard Page - Overview and Analytics
DataGuardian Pro Multi-Page Architecture
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page_modules.auth_wrapper import require_authentication, show_license_check, track_page_view
from page_modules.dashboard import render_dashboard

def main():
    """Main entry point for dashboard page"""
    if not require_authentication():
        return
    
    show_license_check()
    track_page_view('dashboard')
    
    try:
        render_dashboard()
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
