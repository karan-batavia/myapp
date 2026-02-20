"""
SOC2 UI Components Module

This module contains reusable UI components for the SOC2 scanner interface
to eliminate code duplication and improve maintainability.
"""

import streamlit as st
from typing import Dict, Any
from utils.i18n import _

def render_soc2_categories(key_prefix: str = "") -> Dict[str, bool]:
    """
    Render SOC2 categories checkboxes with consistent styling.
    
    Args:
        key_prefix: Prefix for checkbox keys to avoid conflicts
        
    Returns:
        Dictionary of category selections
    """
    st.subheader(_("scan.soc2_categories", "SOC2 Categories to Scan"))
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    categories = {}
    
    with col1:
        categories['security'] = st.checkbox(
            "Security", 
            value=True, 
            key=f"{key_prefix}_soc2_category_security",
            help="Focuses on system protection against unauthorized access"
        )
    
    with col2:
        categories['availability'] = st.checkbox(
            "Availability", 
            value=True, 
            key=f"{key_prefix}_soc2_category_availability",
            help="Examines system availability for operation and use"
        )
    
    with col3:
        categories['processing'] = st.checkbox(
            "Processing Integrity", 
            value=True, 
            key=f"{key_prefix}_soc2_category_processing",
            help="Checks if system processing is complete, accurate, and timely"
        )
    
    with col4:
        categories['confidentiality'] = st.checkbox(
            "Confidentiality", 
            value=True, 
            key=f"{key_prefix}_soc2_category_confidentiality",
            help="Ensures information designated as confidential is protected"
        )
    
    with col5:
        categories['privacy'] = st.checkbox(
            "Privacy", 
            value=True, 
            key=f"{key_prefix}_soc2_category_privacy",
            help="Verifies personal information is collected and used appropriately"
        )
    
    return categories

def render_soc2_advanced_config(key_prefix: str = "") -> Dict[str, Any]:
    """
    Render SOC2 advanced configuration options.
    
    Args:
        key_prefix: Prefix for input keys to avoid conflicts
        
    Returns:
        Dictionary of configuration values
    """
    config = {}
    
    # Target check options
    st.subheader("Target Checks")
    config['target_checks'] = st.radio(
        "Select scan scope",
        ["All", "Security Only", "Custom"],
        horizontal=True,
        key=f"{key_prefix}_soc2_target_checks"
    )
    
    # Path to config file
    config['access_control_path'] = st.text_input(
        "Access Control Config File Path",
        placeholder="/path/to/iam/config.yaml",
        value="/path/to/iam/config.yaml",
        key=f"{key_prefix}_soc2_config_path"
    )
    
    # Scan timeframe
    config['scan_timeframe'] = st.selectbox(
        _("scan.soc2_timeframe", "Scan Timeframe"),
        ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
        index=0,
        key=f"{key_prefix}_soc2_timeframe"
    )
    
    # Custom ruleset
    st.subheader(_("scan.soc2_custom_rules", "Custom SOC2 Ruleset"))
    config['custom_rules'] = st.text_area(
        "Custom SOC2 rules (JSON format)",
        value='{\n  "rules": [\n    {\n      "id": "session-timeout",\n      "requirement": "CC6.1",\n      "check": "session_timeout < 15"\n    }\n  ]\n}',
        height=200,
        key=f"{key_prefix}_soc2_custom_rules"
    )
    
    return config

def render_soc2_info_section():
    """Render SOC2 information and description section."""
    # Display enhanced description
    st.write(_(
        "scan.soc2_description", 
        "Scan Infrastructure as Code (IaC) repositories for SOC2 compliance issues. "
        "This scanner identifies security, availability, processing integrity, "
        "confidentiality, and privacy issues in your infrastructure code."
    ))
    
    # Add detailed info
    st.info(_(
        "scan.soc2_info",
        "SOC2 scanning analyzes your infrastructure code against Trust Services Criteria (TSC) "
        "to identify potential compliance issues. The scanner maps findings to specific TSC controls "
        "and provides recommendations for remediation."
    ))

def render_soc2_output_info():
    """Render SOC2 expected output information."""
    st.info(_("scan.soc2_no_uploads", "SOC2 scanning does not require file uploads. Configure the repository details in the Advanced Configuration section and click the scan button below."))
    
    # Add expected output information
    st.markdown(f"""
    <div style="padding: 10px; border-radius: 5px; background-color: #f0f8ff; margin: 10px 0;">
        <span style="font-weight: bold;">Output:</span> {_("scan.soc2_output", "SOC2 checklist + mapped violations aligned with Trust Services Criteria")}
    </div>
    """, unsafe_allow_html=True)

def render_soc2_scan_button(key_prefix: str = "") -> bool:
    """
    Render SOC2 scan button with consistent styling.
    
    Args:
        key_prefix: Prefix for button key to avoid conflicts
        
    Returns:
        True if button was clicked, False otherwise
    """
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    scan_col1, scan_col2, scan_col3 = st.columns([1, 2, 1])
    
    with scan_col2:
        return st.button(
            f"🛡️ {_('scan.soc2_scan_button', 'Start SOC2 Compliance Scan')}",
            type="primary",
            width="stretch",
            key=f"{key_prefix}_soc2_scan_button",
            help="Start comprehensive SOC2 compliance scanning for your repository"
        )

def render_soc2_action_buttons(scan_results: Dict[str, Any], key_prefix: str = ""):
    """
    Render SOC2 action buttons for PDF generation, new scan, and dashboard view.
    
    Args:
        scan_results: Scan results dictionary
        key_prefix: Prefix for button keys to avoid conflicts
    """
    st.markdown("### Actions")
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button(f"📄 {_('scan.soc2_pdf_report', 'Generate PDF Report')}", 
                     type="primary", 
                     key=f"{key_prefix}_soc2_pdf_button", 
                     width="stretch"):
            # Check if user can download (paid users only)
            from config.pricing_config import can_download_reports
            if not can_download_reports():
                st.info("🔒 Report downloads available for paid subscribers. Upgrade to download reports.")
            else:
                with st.spinner("Generating comprehensive SOC2 compliance report..."):
                    try:
                        from services.soc2_display import generate_soc2_pdf_report
                        from datetime import datetime
                        
                        pdf_bytes = generate_soc2_pdf_report(scan_results)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        pdf_filename = f"soc2_compliance_report_{timestamp}.pdf"
                        
                        st.download_button(
                            label="📥 Download SOC2 Report",
                            data=pdf_bytes,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            key=f"{key_prefix}_soc2_download_btn"
                        )
                        st.success("SOC2 compliance report generated successfully!")
                    except Exception as e:
                        st.error(f"Failed to generate PDF report: {str(e)}")
    
    with action_col2:
        if st.button(f"🔄 {_('scan.soc2_new_scan', 'New SOC2 Scan')}", 
                     key=f"{key_prefix}_soc2_new_scan", 
                     width="stretch"):
            # Clear session state for new scan
            for key in list(st.session_state.keys()):
                if 'soc2' in key.lower():
                    del st.session_state[key]
            # Note: st.rerun() removed from button click to avoid no-op warning
            # The app will automatically rerun due to session state changes
    
    with action_col3:
        if st.button(f"📊 {_('scan.soc2_view_dashboard', 'View in Dashboard')}", 
                     key=f"{key_prefix}_soc2_view_dashboard", 
                     width="stretch"):
            # Store results in history and redirect to dashboard
            if 'scan_history' not in st.session_state:
                st.session_state.scan_history = []
            
            from datetime import datetime
            
            compliance_score = scan_results.get("compliance_score", 0)
            high_risk = scan_results.get("high_risk_count", 0)
            medium_risk = scan_results.get("medium_risk_count", 0)
            low_risk = scan_results.get("low_risk_count", 0)
            total_findings = high_risk + medium_risk + low_risk
            
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'scan_type': 'SOC2 Compliance',
                'repository': scan_results.get('repo_url', 'Unknown'),
                'branch': scan_results.get('branch', 'main'),
                'compliance_score': compliance_score,
                'total_findings': total_findings,
                'high_risk': high_risk,
                'medium_risk': medium_risk,
                'low_risk': low_risk,
                'results': scan_results
            }
            st.session_state.scan_history.append(history_entry)
            st.session_state.selected_nav = "Dashboard"
            # Note: st.rerun() removed from button click to avoid no-op warning
            # The app will automatically rerun due to session state changes