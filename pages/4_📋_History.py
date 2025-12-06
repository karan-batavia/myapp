"""
History Page - Scan History and Audit Trail
DataGuardian Pro Multi-Page Architecture
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page_modules.auth_wrapper import require_authentication, show_license_check, track_page_view
from page_modules.history import render_history_page

def main():
    """Main entry point for history page"""
    if not require_authentication():
        return
    
    show_license_check()
    track_page_view('history')
    
    try:
        render_history_page()
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
