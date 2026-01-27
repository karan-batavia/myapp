"""
Results Page Module
Displays scan results with detailed findings
"""

import streamlit as st
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


def render_results_page():
    """Render results page with real scan data"""
    from utils.translations import _
    from services.results_aggregator import ResultsAggregator
    from config.pricing_config import is_free_user, can_view_scan_results, increment_free_user_scan_view, get_free_user_scan_count
    
    st.title(f"📊 {_('results.title', 'Scan Results')}")
    
    # Check if free user has exceeded view limit (track unique page visits, not reruns)
    if is_free_user():
        # Only count once per page visit, not on every Streamlit rerun
        if 'results_page_counted' not in st.session_state:
            st.session_state['results_page_counted'] = True
            increment_free_user_scan_view()
        
        views_used = get_free_user_scan_count()
        remaining = max(0, 3 - views_used)
        
        if views_used > 3:
            st.error("⚠️ **Free trial limit reached!** You've viewed 3 scan results.")
            st.info("🔓 Upgrade to a paid plan for unlimited scan result views and report downloads.")
            
            if st.button("🚀 View Pricing Plans", use_container_width=True):
                st.session_state['show_pricing'] = True
                st.rerun()
            return
        else:
            st.warning(f"📊 Free trial: {remaining} of 3 scan views remaining. Upgrade for unlimited access.")
    
    try:
        aggregator = ResultsAggregator()
        username = st.session_state.get('username', 'anonymous')
        
        recent_scans = aggregator.get_recent_scans(days=30, username=username)
        
        if not recent_scans:
            st.info(_('results.no_results', 'No scan results available. Please run a scan first.'))
            if st.button("🔍 Start New Scan"):
                st.session_state['start_new_scan'] = True
                st.rerun()
            return
            
        col1, col2, col3, col4 = st.columns(4)
        total_scans = len(recent_scans)
        total_pii = sum(scan.get('total_pii_found', 0) for scan in recent_scans)
        high_risk = sum(scan.get('high_risk_count', 0) for scan in recent_scans)
        avg_compliance = sum(scan.get('result', {}).get('compliance_score', 0) for scan in recent_scans) / max(total_scans, 1)
        
        with col1:
            st.metric("Total Scans", total_scans)
        with col2:
            st.metric("PII Items Found", total_pii)
        with col3:
            st.metric("High Risk Issues", high_risk)
        with col4:
            st.metric("Avg Compliance", f"{avg_compliance:.1f}%")
        
        st.markdown("---")
        
        st.subheader("Recent Scan Results")
        
        table_data = []
        for scan in recent_scans:
            result = scan.get('result', {})
            
            pii_count = scan.get('total_pii_found', 0)
            risk_high = scan.get('high_risk_count', 0)
            
            if pii_count == 0:
                pii_count = result.get('total_pii_found', 0)
            if risk_high == 0:
                risk_high = result.get('high_risk_count', 0)
            
            timestamp = scan.get('timestamp', 'N/A')
            if timestamp and hasattr(timestamp, 'strftime'):
                date_str = timestamp.strftime('%Y-%m-%d')
            elif timestamp:
                date_str = str(timestamp)[:10]
            else:
                date_str = 'N/A'
            
            compliance = result.get('compliance_score', 0)
            if compliance == 0:
                compliance = scan.get('compliance_score', 0)
            
            table_data.append({
                'Scan ID': scan.get('scan_id', 'N/A')[:12],
                'Date': date_str,
                'Type': scan.get('scan_type', 'N/A').replace('_', ' ').title(),
                'Files': scan.get('file_count', 0),
                'PII Found': pii_count,
                'High Risk': risk_high,
                'Compliance': f"{compliance:.1f}%"
            })
        
        if table_data:
            df = pd.DataFrame(table_data)
            
            selected_scan = st.selectbox(
                "Select scan for detailed view:",
                options=range(len(recent_scans)),
                format_func=lambda x: f"{recent_scans[x].get('scan_id', 'N/A')[:12]} - {recent_scans[x].get('scan_type', 'N/A').title()} ({recent_scans[x].get('timestamp', 'N/A')[:10] if recent_scans[x].get('timestamp') else 'N/A'})"
            )
            
            st.dataframe(df, use_container_width=True)
            
            if selected_scan is not None:
                st.markdown("---")
                render_detailed_scan_view(recent_scans[selected_scan])
                
    except Exception as e:
        logger.error(f"Error loading scan results: {e}")
        st.error(f"Error loading scan results: {str(e)}")
        st.info("Please try refreshing the page or contact support if the issue persists.")


def render_detailed_scan_view(scan_data):
    """Render detailed view of a specific scan"""
    try:
        st.subheader(f"📋 Scan Details: {scan_data.get('scan_id', 'N/A')[:12]}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Type:** {scan_data.get('scan_type', 'N/A').title()}")
            timestamp = scan_data.get('timestamp', 'N/A')
            if hasattr(timestamp, 'strftime'):
                st.write(f"**Date:** {timestamp.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.write(f"**Date:** {str(timestamp)[:19]}")
        with col2:
            st.write(f"**Region:** {scan_data.get('region', 'Netherlands')}")
            st.write(f"**Files Scanned:** {scan_data.get('file_count', 0)}")
        with col3:
            result = scan_data.get('result', {})
            st.write(f"**Compliance Score:** {result.get('compliance_score', 0):.1f}%")
            st.write(f"**High Risk Items:** {scan_data.get('high_risk_count', 0)}")
        
        findings = result.get('findings', [])
        if findings and len(findings) > 0:
            st.markdown("### 🔍 Detailed Findings")
            
            for i, finding in enumerate(findings[:20]):
                if isinstance(finding, dict):
                    with st.expander(f"Finding {i+1}: {finding.get('file_name', finding.get('pii_type', 'Unknown'))}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**File Path:** {finding.get('file_path', 'N/A')}")
                            st.write(f"**PII Type:** {finding.get('pii_type', 'N/A')}")
                            st.write(f"**Severity:** {finding.get('severity', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Line Number:** {finding.get('line_number', 'N/A')}")
                            st.write(f"**Context:** {finding.get('context', 'N/A')[:100]}...")
                            
                        if finding.get('remediation'):
                            st.info(f"**Remediation:** {finding.get('remediation')}")
            
            if len(findings) > 20:
                st.info(f"Showing first 20 of {len(findings)} findings. Download report for complete list.")
        
        st.markdown("---")
        _render_download_options(scan_data)
        
    except Exception as e:
        logger.error(f"Error rendering scan details: {e}")
        st.error(f"Error displaying scan details: {str(e)}")


def _render_download_options(scan_data):
    """Render report download options - restricted for free users"""
    from config.pricing_config import can_download_reports, is_free_user
    
    st.subheader("📥 Download Report")
    
    # Check if user can download (paid users only)
    if not can_download_reports():
        st.warning("⚠️ **Report downloads are available for paid subscribers only.**")
        st.info("🔓 Upgrade to any paid plan to download PDF, HTML, and JSON reports. You can still view scan results on screen.")
        
        # Show upgrade button
        if st.button("🚀 View Pricing Plans", use_container_width=True):
            st.session_state['show_pricing'] = True
            st.rerun()
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download PDF Report", use_container_width=True):
            try:
                from services.report_generator import ReportGenerator
                generator = ReportGenerator()
                pdf_data = generator.generate_pdf_report(scan_data)
                
                st.download_button(
                    label="📥 Save PDF",
                    data=pdf_data,
                    file_name=f"scan_report_{scan_data.get('scan_id', 'report')[:8]}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                logger.error(f"PDF generation error: {e}")
                st.error("PDF generation temporarily unavailable.")
    
    with col2:
        if st.button("📊 Download HTML Report", use_container_width=True):
            try:
                from services.unified_html_report_generator import generate_unified_html_report
                html_data = generate_unified_html_report(scan_data.get('result', scan_data))
                
                st.download_button(
                    label="📥 Save HTML",
                    data=html_data,
                    file_name=f"scan_report_{scan_data.get('scan_id', 'report')[:8]}.html",
                    mime="text/html"
                )
            except Exception as e:
                logger.error(f"HTML generation error: {e}")
                st.error("HTML generation temporarily unavailable.")
    
    with col3:
        if st.button("📋 Download JSON Data", use_container_width=True):
            import json
            json_data = json.dumps(scan_data, indent=2, default=str)
            
            st.download_button(
                label="📥 Save JSON",
                data=json_data,
                file_name=f"scan_data_{scan_data.get('scan_id', 'report')[:8]}.json",
                mime="application/json"
            )
