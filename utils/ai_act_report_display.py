"""
AI Act Report Display Utilities

This module provides utilities for displaying EU AI Act 2025 HTML reports
in the Streamlit interface with proper formatting and download capabilities.
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
from typing import Dict, Any

def display_ai_act_html_report(scan_result: Dict[str, Any]) -> None:
    """
    Display EU AI Act 2025 HTML report in Streamlit interface
    
    Args:
        scan_result: Dictionary containing AI model scan results with HTML report
    """
    
    html_report = scan_result.get('ai_act_html_report', '')
    
    if html_report:
        # Display the HTML report
        components.html(html_report, height=800, scrolling=True)
        
        # Add download button for the HTML report
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📄 Download EU AI Act 2025 Compliance Report")
            st.markdown("Complete regulatory assessment ready for compliance documentation")
        
        with col2:
            # Create download button
            b64_html = base64.b64encode(html_report.encode()).decode()
            
            ai_system_name = scan_result.get('ai_model_info', {}).get('name', 'AI_System')
            filename = f"EU_AI_Act_2025_Compliance_Report_{ai_system_name}_{scan_result.get('scan_id', 'report')}.html"
            
            href = f'<a href="data:text/html;base64,{b64_html}" download="{filename}">📋 Download HTML Report</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.warning("EU AI Act 2025 HTML report not available. Please run an AI model scan to generate the report.")

def create_ai_act_summary_metrics(scan_result: Dict[str, Any]) -> None:
    """
    Create summary metrics display for AI Act compliance
    
    Args:
        scan_result: Dictionary containing AI model scan results
    """
    
    compliance_metrics = scan_result.get('compliance_metrics', {})
    findings = scan_result.get('findings', [])
    ai_act_findings = [f for f in findings if 'AI_ACT' in f.get('type', '')]
    
    # Create metrics columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🇪🇺 EU AI Act Status",
            compliance_metrics.get('ai_act_compliance', 'Not Assessed'),
            help="Overall compliance status under EU AI Act (Regulation 2024/1689)"
        )
    
    with col2:
        compliance_score = compliance_metrics.get('compliance_score', 0)
        st.metric(
            "📊 Compliance Score",
            f"{compliance_score}%",
            help="AI Act compliance percentage based on assessment findings"
        )
    
    with col3:
        st.metric(
            "⚖️ Risk Level",
            compliance_metrics.get('ai_act_risk_level', 'Assessment Required'),
            help="AI Act risk classification: Minimal, Limited, High, or Unacceptable Risk"
        )
    
    with col4:
        st.metric(
            "🔍 AI Act Findings",
            len(ai_act_findings),
            help="Number of specific EU AI Act compliance issues detected"
        )
    
    # Display key findings summary
    if ai_act_findings:
        st.markdown("### 🚨 Key EU AI Act 2025 Compliance Issues")
        
        # Group findings by type
        prohibited_practices = len([f for f in ai_act_findings if f.get('type') == 'AI_ACT_PROHIBITED'])
        high_risk_violations = len([f for f in ai_act_findings if f.get('type') == 'AI_ACT_HIGH_RISK'])
        transparency_violations = len([f for f in ai_act_findings if f.get('type') == 'AI_ACT_TRANSPARENCY'])
        fundamental_rights = len([f for f in ai_act_findings if f.get('type') == 'AI_ACT_FUNDAMENTAL_RIGHTS'])
        accountability_issues = len([f for f in ai_act_findings if f.get('type') == 'AI_ACT_ACCOUNTABILITY'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if prohibited_practices > 0:
                st.error(f"🚫 {prohibited_practices} Prohibited Practice(s) - Article 5")
            if high_risk_violations > 0:
                st.warning(f"⚠️ {high_risk_violations} High-Risk System Issue(s) - Annex III")
        
        with col2:
            if transparency_violations > 0:
                st.warning(f"👁️ {transparency_violations} Transparency Violation(s) - Article 13")
            if fundamental_rights > 0:
                st.error(f"⚖️ {fundamental_rights} Fundamental Rights Impact(s) - Article 29")
        
        with col3:
            if accountability_issues > 0:
                st.info(f"📊 {accountability_issues} Accountability Issue(s) - Articles 14-15")
    
    else:
        st.success("✅ No specific EU AI Act compliance violations detected")

def show_ai_act_enforcement_info() -> None:
    """
    Display EU AI Act enforcement information
    """
    
    st.markdown("### ⚖️ EU AI Act 2025 Enforcement Information")
    
    with st.expander("📅 Regulatory Timeline & Enforcement"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **EU AI Act Timeline:**
            - ✅ **August 1, 2024**: Act entered into force
            - ⚡ **February 2, 2025**: Full enforcement begins
            - 🏛️ **Enforcement**: National supervisory authorities
            - 🇪🇺 **Scope**: All EU Member States
            """)
        
        with col2:
            st.markdown("""
            **Administrative Fines:**
            - 🚫 **€35M or 7% turnover**: Prohibited AI practices
            - ⚠️ **€15M or 3% turnover**: High-risk system violations  
            - 📋 **€7.5M or 1% turnover**: Incorrect information to authorities
            - ⚖️ **Authority**: National supervisory authorities
            """)
    
    with st.expander("🛡️ Compliance Requirements Summary"):
        st.markdown("""
        **Key Compliance Obligations:**
        
        1. **🚫 Article 5 - Prohibited Practices**
           - No subliminal techniques or social scoring
           - No mass biometric surveillance systems
           - No emotion recognition in workplace/education
        
        2. **⚠️ High-Risk AI Systems (Annex III)**
           - Risk management systems required
           - Conformity assessments before market placement
           - Post-market monitoring and reporting
           - Human oversight and transparency
        
        3. **👁️ Article 13 - Transparency Obligations**
           - Clear disclosure when humans interact with AI
           - Information about AI system capabilities and limitations
           - Instructions for use and human oversight
        
        4. **⚖️ Article 29 - Fundamental Rights Impact**
           - Assessment of fundamental rights impact
           - Safeguards and mitigation measures
           - Regular monitoring and evaluation
        
        5. **📊 Articles 14-15 - Algorithmic Accountability**
           - Governance frameworks for AI systems
           - Audit trails for algorithmic decisions
           - Explainability mechanisms where required
        """)