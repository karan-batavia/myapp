"""
Pricing Page - Subscription Plans and Payment
DataGuardian Pro Multi-Page Architecture
Note: Pricing page is publicly accessible (no auth required)
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page_modules.auth_wrapper import initialize_session, init_i18n
from page_modules.pricing import render_pricing_page

def main():
    """Main entry point for pricing page"""
    initialize_session()
    init_i18n()
    
    try:
        render_pricing_page()
    except Exception as e:
        st.error(f"Error loading pricing: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

main()
