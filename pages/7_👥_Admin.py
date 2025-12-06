"""
Admin Page - Administration and User Management
DataGuardian Pro Multi-Page Architecture
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page_modules.auth_wrapper import require_role, show_license_check, track_page_view
from page_modules.admin import render_admin_page

def main():
    """Main entry point for admin page"""
    if not require_role('admin'):
        return
    
    show_license_check()
    track_page_view('admin')
    
    try:
        render_admin_page()
    except Exception as e:
        st.error(f"Error loading admin panel: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
