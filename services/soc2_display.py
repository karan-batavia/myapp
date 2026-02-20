"""
SOC2 Display Utilities

This module provides specialized display functions for SOC2 scan results.
"""

import streamlit as st
# Disable pandas to resolve numpy conflicts
# import pandas as pd
pd = None

def display_soc2_findings(scan_results):
    """
    Display SOC2 findings with TSC criteria mapping.
    
    Args:
        scan_results: Dictionary containing SOC2 scan results
    """
    # Display findings table with enhanced TSC mapping
    st.subheader("Compliance Findings")
    if 'findings' in scan_results and scan_results['findings']:
        # Filter out invalid findings and ensure proper data structure
        valid_findings = []
        for f in scan_results['findings'][:10]:
            # Only process dictionary-based findings (authentic scan results)
            if isinstance(f, dict):
                valid_findings.append({
                    "Risk": f.get("risk_level", "Unknown").upper(),
                    "Category": f.get("category", "Unknown").capitalize(),
                    "Description": f.get("description", "No description"),
                    "File": f.get("file", "Unknown"),
                    "Line": f.get("line", "N/A"),
                    "SOC2 TSC": ", ".join(f.get("soc2_tsc_criteria", [])),
                    "Technology": f.get("technology", "Unknown"),
                    "Recommendation": f.get("recommendation", "No recommendation")[:100] + "..." if len(f.get("recommendation", "")) > 100 else f.get("recommendation", "No recommendation")
                })
        
        if valid_findings:
            findings_df = pd.DataFrame(valid_findings)
            
            # Apply styling to highlight risk levels
            def highlight_risk_in_table(val):
                if val == 'HIGH':
                    return 'background-color: #fee2e2; color: #dc2626; font-weight: bold'
                elif val == 'MEDIUM':
                    return 'background-color: #fef3c7; color: #d97706; font-weight: bold'
                elif val == 'LOW':
                    return 'background-color: #dcfce7; color: #16a34a; font-weight: bold'
                return ''
            
            styled_df = findings_df.style.map(highlight_risk_in_table, subset=['Risk'])
            st.dataframe(styled_df, width="stretch")
            
            # Show detailed violation breakdown by category
            st.markdown("### Detailed Violation Analysis")
            
            categories = {}
            for f in scan_results['findings']:
                if isinstance(f, dict):
                    category = f.get('category', 'unknown')
                    if category not in categories:
                        categories[category] = {'high': 0, 'medium': 0, 'low': 0, 'items': []}
                    
                    risk_level = f.get('risk_level', 'medium')
                    categories[category][risk_level] += 1
                    categories[category]['items'].append(f)
            
            # Display category breakdown without nested expanders
            for category, data in categories.items():
                st.markdown(f"#### 📊 {category.replace('_', ' ').title()} Issues ({data['high']} High, {data['medium']} Medium, {data['low']} Low)")
                
                for item in data['items']:
                    risk_color = "#dc2626" if item.get('risk_level') == 'high' else "#d97706" if item.get('risk_level') == 'medium' else "#16a34a"
                    st.markdown(f"""
                    <div style="border-left: 4px solid {risk_color}; padding: 10px; margin: 5px 0; background: #f8f9fa;">
                        <strong>{item.get('risk_level', 'medium').upper()}</strong>: {item.get('description', 'No description')}
                        <br><small>📁 {item.get('file', 'Unknown')} (Line {item.get('line', 'N/A')})</small>
                        <br><small>🔧 Technology: {item.get('technology', 'Unknown')}</small>
                        <br><small>📋 SOC2 TSC: {', '.join(item.get('soc2_tsc_criteria', []))}</small>
                        <br><em>💡 {item.get('recommendation', 'No recommendation')}</em>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
            
            if len(scan_results['findings']) > 10:
                st.info(f"Showing 10 of {len(scan_results['findings'])} findings. Download the PDF report for complete results.")
        else:
            st.info("No compliance findings detected in this scan.")
    else:
        st.info("No compliance findings detected in this scan.")
            
        # Add detailed TSC mapping explanation
        st.markdown("### SOC2 Trust Services Criteria Details")
        st.markdown("""
        #### SOC2 Trust Services Criteria Explained
        
        Each finding is mapped to specific SOC2 Trust Services Criteria to help you understand 
        how it impacts your compliance posture:
        
        - **CC**: Common Criteria (Security)
        - **A**: Availability
        - **PI**: Processing Integrity
        - **C**: Confidentiality
        - **P**: Privacy
        
        For example, a finding mapped to **CC6.1** means it impacts the "Logical and Physical Access Controls"
        criteria under the Security category.
        
        #### Remediation Prioritization
        
        When addressing findings, prioritize based on these criteria:
        
        1. **CC (Security)** - Critical foundation for all other controls
        2. **C (Confidentiality)** - Protects sensitive data from unauthorized disclosure
        3. **A (Availability)** - Ensures systems are operational when needed
        4. **PI (Processing Integrity)** - Ensures data processing is complete and accurate
        5. **P (Privacy)** - Addresses personal data protection requirements
        """)
            
    # Display SOC2 TSC Checklist
    if 'soc2_tsc_checklist' in scan_results:
        st.subheader("SOC2 Trust Services Criteria Checklist")
        
        # Create tabs for each SOC2 category
        checklist = scan_results['soc2_tsc_checklist']
        categories = ["security", "availability", "processing_integrity", "confidentiality", "privacy"]
        
        soc2_tabs = st.tabs([c.capitalize() for c in categories])
        
        for i, category in enumerate(categories):
            with soc2_tabs[i]:
                # Filter criteria for this category
                category_criteria = {k: v for k, v in checklist.items() if v.get("category") == category}
                if not category_criteria:
                    st.info(f"No {category.capitalize()} criteria assessed.")
                    continue
                    
                # Create dataframe for this category
                criteria_data = []
                for criterion, details in category_criteria.items():
                    criteria_data.append({
                        "Criterion": criterion,
                        "Description": details.get("description", ""),
                        "Status": details.get("status", "not_assessed").upper(),
                        "Violations": len(details.get("violations", []))
                    })
                
                # Sort by criterion
                criteria_data.sort(key=lambda x: x["Criterion"])
                
                # Create dataframe
                df = pd.DataFrame(criteria_data)
                st.dataframe(df, width="stretch")
                
                # Summary for this category
                statuses = [details.get("status", "not_assessed") for details in category_criteria.values()]
                passed = statuses.count("passed")
                failed = statuses.count("failed")
                warning = statuses.count("warning")
                info = statuses.count("info")
                
                st.write(f"**Summary**: {passed} Passed, {failed} Failed, {warning} Warning, {info} Info")
                
                # Show violations if any criteria failed
                if failed > 0 or warning > 0:
                    st.markdown("#### Violations")
                    
                    for criterion, details in category_criteria.items():
                        violations = details.get("violations", [])
                        if violations:
                            st.markdown(f"**{criterion}**: {details.get('description', '')}")
                            for v in violations:
                                st.markdown(f"- **{v.get('risk_level', '').upper()}**: {v.get('description', '')} in `{v.get('file', '')}:{v.get('line', '')}`")
                            st.markdown("---")

def run_soc2_display_standalone():
    """
    Run a standalone SOC2 display page.
    This can be imported and called directly from app.py
    """
    st.title("SOC2 Compliance Results")
    
    if 'soc2_scan_results' not in st.session_state:
        st.warning("No SOC2 scan results found. Please run a SOC2 scan first.")
        return
        
    scan_results = st.session_state.soc2_scan_results
    
    # Show repository info
    st.write(f"**Repository:** {scan_results.get('repo_url')}")
    if 'project' in scan_results:
        st.write(f"**Project:** {scan_results.get('project')}")
    st.write(f"**Branch:** {scan_results.get('branch', 'main')}")
    
    # Extract metrics
    compliance_score = scan_results.get("compliance_score", 0)
    high_risk = scan_results.get("high_risk_count", 0)
    medium_risk = scan_results.get("medium_risk_count", 0)
    low_risk = scan_results.get("low_risk_count", 0)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Color coding based on compliance score
    if compliance_score >= 80:
        compliance_color = "green"
        compliance_status = "✓ Good"
    elif compliance_score >= 60:
        compliance_color = "orange"
        compliance_status = "⚠️ Needs Review"
    else:
        compliance_color = "red"
        compliance_status = "✗ Critical"
    
    with col1:
        st.metric("Compliance Score", f"{compliance_score}/100")
        st.markdown(f"<div style='text-align: center; color: {compliance_color};'>{compliance_status}</div>", unsafe_allow_html=True)
    
    with col2:
        st.metric("High Risk Issues", high_risk)
    
    with col3:
        st.metric("Medium Risk Issues", medium_risk)
    
    with col4:
        st.metric("Low Risk Issues", low_risk)
    
    # Display findings
    display_soc2_findings(scan_results)
    
    # Report generation
    st.markdown("---")
    st.markdown("### Download Reports")
    
    # Check if user can download (paid users only)
    from config.pricing_config import can_download_reports
    if not can_download_reports():
        st.info("🔒 Report downloads available for paid subscribers. Upgrade to download reports.")
    else:
        report_tabs = st.tabs(["Download", "Preview"])
        
        with report_tabs[0]:
            col1, col2 = st.columns(2)
            
            with col1:
                # PDF Download button
                if st.button("Generate PDF Report", type="primary"):
                    from services.report_generator import generate_report
                    import base64
                    from datetime import datetime
                    
                    with st.spinner("Generating PDF report..."):
                        # Generate PDF report
                        pdf_bytes = generate_report(scan_results)
                        
                        # Provide download link
                        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                        pdf_filename = f"soc2_compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_filename}">Download SOC2 Compliance Report PDF</a>'
                        st.markdown(href, unsafe_allow_html=True)
        
        with col2:
            # HTML Download button
            if st.button("Generate HTML Report", type="primary"):
                from services.html_report_generator import get_html_report_as_base64
                import base64
                from datetime import datetime
                
                with st.spinner("Generating HTML report..."):
                    # Generate HTML report
                    # First adapt scan_results to the HTML report format
                    html_compatible_results = {
                        'scan_id': scan_results.get('scan_id', f"soc2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                        'scan_type': 'SOC2',
                        'timestamp': datetime.now().isoformat(),
                        'region': scan_results.get('region', 'Netherlands'),
                        'url': scan_results.get('repo_url', 'Not available'),
                        'findings': scan_results.get('findings', []),
                        'total_pii_found': len(scan_results.get('findings', [])),
                        'high_risk_count': scan_results.get('high_risk_count', 0),
                        'medium_risk_count': scan_results.get('medium_risk_count', 0),
                        'low_risk_count': scan_results.get('low_risk_count', 0),
                        'pii_types': {'SOC2 Findings': len(scan_results.get('findings', []))},
                        'recommendations': [
                            {
                                'title': 'Address High Risk SOC2 Findings',
                                'priority': 'High',
                                'description': 'Focus on high-risk SOC2 issues to improve your compliance posture.',
                                'steps': ['Review all high-risk findings', 'Prioritize based on TSC criteria impact', 'Develop remediation plans']
                            },
                            {
                                'title': 'Improve SOC2 Documentation',
                                'priority': 'Medium',
                                'description': 'Ensure all SOC2 control procedures are properly documented.',
                                'steps': ['Update control documentation', 'Cross-reference with TSC criteria', 'Review with compliance team']
                            }
                        ]
                    }
                    
                    # Get base64 encoded HTML
                    html_base64 = get_html_report_as_base64(html_compatible_results)
                    
                    # Provide download link
                    html_filename = f"soc2_compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    href = f'<a href="data:text/html;base64,{html_base64}" download="{html_filename}">Download SOC2 Compliance Report HTML</a>'
                    st.markdown(href, unsafe_allow_html=True)
    
    with report_tabs[1]:
        # Full Report viewing option
        if st.button("Show Detailed Report"):
            with st.spinner("Generating detailed report view..."):
                st.markdown("## Detailed SOC2 Compliance Report")

def generate_soc2_pdf_report(scan_results: dict) -> bytes:
    """
    Generate a comprehensive SOC2 compliance PDF report.
    
    Args:
        scan_results: Dictionary containing SOC2 scan results
        
    Returns:
        PDF report as bytes
    """
    try:
        from services.report_generator import generate_report
        
        # Ensure scan_results has the correct structure for SOC2 reports
        if not scan_results:
            raise ValueError("No scan results provided")
            
        # Add SOC2-specific metadata to scan results
        enhanced_results = scan_results.copy()
        enhanced_results['scan_type'] = 'SOC2'
        enhanced_results['report_title'] = 'SOC2 Compliance Report'
        
        # Ensure we have required fields
        if 'findings' not in enhanced_results:
            enhanced_results['findings'] = []
            
        if 'compliance_score' not in enhanced_results:
            # Calculate a basic compliance score based on findings
            total_findings = len(enhanced_results['findings'])
            high_risk = enhanced_results.get('high_risk_count', 0)
            medium_risk = enhanced_results.get('medium_risk_count', 0)
            
            if total_findings == 0:
                enhanced_results['compliance_score'] = 95
            else:
                # Simple scoring: start at 100, deduct for findings
                score = 100 - (high_risk * 15) - (medium_risk * 8) - ((total_findings - high_risk - medium_risk) * 3)
                enhanced_results['compliance_score'] = max(0, min(100, score))
        
        # Generate the PDF using the SOC2 format
        pdf_bytes = generate_report(
            scan_data=enhanced_results,
            include_details=True,
            include_charts=True,
            include_metadata=True,
            include_recommendations=True,
            report_format="soc2"
        )
        
        return pdf_bytes
        
    except Exception as e:
        # Create a basic error PDF if report generation fails
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        from datetime import datetime
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add error message to PDF
        p.drawString(100, 750, "SOC2 Compliance Report")
        p.drawString(100, 720, f"Error generating report: {str(e)}")
        p.drawString(100, 690, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add basic scan info if available
        if scan_results:
            p.drawString(100, 650, f"Repository: {scan_results.get('repo_url', 'N/A')}")
            p.drawString(100, 620, f"Findings: {len(scan_results.get('findings', []))}")
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()