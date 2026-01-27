"""
AI Act Calculator UI Component
Interactive Streamlit interface for EU AI Act 2025 compliance assessment
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any
from utils.ai_act_calculator import (
    AIActCalculator, AISystemProfile, AISystemRiskLevel,
    ComplianceAssessment, AIActArticle
)
from utils.translations import _ as translate

def render_ai_act_calculator():
    """Render the AI Act compliance calculator interface"""
    
    try:
        st.header("🤖 AI Act 2025 Compliance Calculator")
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 System Profile", 
            "🔍 Risk Assessment", 
            "📊 Compliance Analysis", 
            "📄 Generate Report"
        ])
        
        # Initialize calculator
        calculator = AIActCalculator(region="Netherlands")
        
        with tab1:
            render_system_profile_form()
        
        with tab2:
            render_risk_assessment()
        
        with tab3:
            render_compliance_analysis()
        
        with tab4:
            render_report_generation()
            
    except Exception as e:
        st.error("AI Act Calculator temporarily unavailable")
        st.error(f"Error: {str(e)}")
        with st.expander("View error details"):
            import traceback
            st.code(traceback.format_exc())

def render_system_profile_form():
    """Render the AI system profile form"""
    
    st.subheader("📋 AI System Profile")
    st.write("Provide details about your AI system for compliance assessment")
    
    with st.form("ai_act_system_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            system_name = st.text_input(
                "System Name *",
                placeholder="e.g., Customer Credit Scoring System",
                help="Enter the name of your AI system"
            )
            
            purpose = st.text_area(
                "System Purpose *",
                placeholder="e.g., Automated credit risk assessment for loan applications",
                help="Describe the main purpose of your AI system"
            )
            
            use_case = st.selectbox(
                "Primary Use Case *",
                [
                    "Biometric identification",
                    "Critical infrastructure management",
                    "Educational assessment",
                    "Employment and recruitment",
                    "Credit scoring and financial services",
                    "Healthcare diagnosis",
                    "Law enforcement",
                    "Migration and border control",
                    "Democratic processes",
                    "Content recommendation",
                    "Customer service automation",
                    "Fraud detection",
                    "Predictive maintenance",
                    "Supply chain optimization",
                    "Other"
                ],
                help="Select the primary use case category"
            )
            
            deployment_context = st.selectbox(
                "Deployment Context *",
                [
                    "Public sector",
                    "Private sector - B2B",
                    "Private sector - B2C",
                    "Healthcare",
                    "Financial services",
                    "Education",
                    "Law enforcement",
                    "Critical infrastructure",
                    "Other"
                ],
                help="Select the deployment context"
            )
            
            decision_impact = st.selectbox(
                "Decision Impact Level *",
                [
                    "No impact - Information only",
                    "Low - Minor convenience",
                    "Medium - Moderate impact on user",
                    "High - Significant impact on user",
                    "Critical - Life-changing decisions"
                ],
                help="Select the level of impact of system decisions"
            )
            
            automation_level = st.selectbox(
                "Automation Level *",
                [
                    "Human-in-the-loop - All decisions reviewed",
                    "Human-on-the-loop - Human oversight available",
                    "Mostly automated - Minimal human involvement",
                    "Fully automated - No human intervention"
                ],
                help="Select the level of automation"
            )
        
        with col2:
            data_types = st.multiselect(
                "Data Types Processed *",
                [
                    "Personal data",
                    "Special category data (health, biometric)",
                    "Financial data",
                    "Behavioral data",
                    "Location data",
                    "Biometric data",
                    "Health data",
                    "Criminal records",
                    "Children's data",
                    "Public data only",
                    "Synthetic data only"
                ],
                help="Select all types of data processed by your system"
            )
            
            user_groups = st.multiselect(
                "User Groups Affected *",
                [
                    "General public",
                    "Employees",
                    "Customers",
                    "Patients",
                    "Students",
                    "Children (under 18)",
                    "Vulnerable groups",
                    "Law enforcement officers",
                    "Government officials",
                    "Other professionals"
                ],
                help="Select all user groups affected by your system"
            )
            
            geographic_deployment = st.multiselect(
                "Geographic Deployment *",
                [
                    "Netherlands",
                    "Germany",
                    "France",
                    "Belgium",
                    "European Union",
                    "Global"
                ],
                help="Select regions where your system is deployed"
            )
            
            data_processing_scope = st.selectbox(
                "Data Processing Scope *",
                [
                    "Small scale - <1000 individuals",
                    "Medium scale - 1K-10K individuals",
                    "Large scale - 10K-100K individuals",
                    "Very large scale - >100K individuals"
                ],
                help="Select the scale of data processing"
            )
            
            human_oversight = st.checkbox(
                "Human Oversight Available",
                help="Check if human oversight is available for system decisions"
            )
            
            regulatory_context = st.selectbox(
                "Regulatory Context",
                [
                    "GDPR only",
                    "GDPR + AI Act",
                    "GDPR + AI Act + Sector-specific",
                    "Other regulatory framework"
                ],
                help="Select applicable regulatory context"
            )
        
        # Form submission
        submitted = st.form_submit_button("📊 Analyze AI System", type="primary")
        
        if submitted:
            # Validate required fields
            if not all([system_name, purpose, use_case, deployment_context, decision_impact, automation_level]):
                st.error("Please fill in all required fields marked with *")
                return
            
            if not data_types or not user_groups or not geographic_deployment:
                st.error("Please select at least one option for data types, user groups, and geographic deployment")
                return
            
            # Create system profile with proper error handling
            try:
                system_profile = AISystemProfile(
                    system_name=system_name,
                    purpose=purpose,
                    use_case=use_case,
                    deployment_context=deployment_context,
                    data_types=data_types,
                    user_groups=user_groups,
                    decision_impact=decision_impact,
                    automation_level=automation_level,
                    human_oversight=human_oversight,
                    data_processing_scope=data_processing_scope,
                    geographic_deployment=geographic_deployment,
                    regulatory_context=regulatory_context
                )
                
                # Store in session state with unique key
                st.session_state.ai_act_system_profile = system_profile
                st.session_state.ai_act_calculator_step = 2
                
                st.success("✅ System profile created successfully! Move to Risk Assessment tab.")
                
            except Exception as e:
                st.error(f"Error creating system profile: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

def render_risk_assessment():
    """Render the risk assessment section"""
    
    st.subheader("🔍 AI Act Risk Assessment")
    
    if 'ai_act_system_profile' not in st.session_state:
        st.info("Please complete the System Profile first")
        return
    
    system_profile = st.session_state.ai_act_system_profile
    calculator = AIActCalculator(region="Netherlands")
    
    # Perform risk classification
    risk_level = calculator.classify_ai_system(system_profile)
    
    # Display risk level
    st.markdown("### 📊 Risk Classification Result")
    
    if risk_level == AISystemRiskLevel.UNACCEPTABLE:
        st.error("🚨 **UNACCEPTABLE RISK** - System involves prohibited practices")
        st.markdown("""
        **Immediate Actions Required:**
        - Discontinue system use immediately
        - Consult legal counsel
        - Review system design for prohibited practices
        """)
    elif risk_level == AISystemRiskLevel.HIGH_RISK:
        st.error("🔴 **HIGH RISK** - Comprehensive compliance requirements")
        st.markdown("""
        **Compliance Requirements:**
        - Full AI Act compliance documentation
        - Risk management systems
        - Human oversight protocols
        - Continuous monitoring
        """)
    elif risk_level == AISystemRiskLevel.LIMITED_RISK:
        st.warning("🟡 **LIMITED RISK** - Transparency requirements")
        st.markdown("""
        **Compliance Requirements:**
        - Transparency and information to users
        - Human oversight capabilities
        - Basic documentation
        """)
    else:
        st.success("🟢 **MINIMAL RISK** - Basic transparency requirements")
        st.markdown("""
        **Compliance Requirements:**
        - Basic user information
        - Simple transparency measures
        """)
    
    # Display system characteristics analysis
    st.markdown("### 🔍 System Characteristics Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**System Details:**")
        st.write(f"• **Use Case:** {system_profile.use_case}")
        st.write(f"• **Deployment:** {system_profile.deployment_context}")
        st.write(f"• **Decision Impact:** {system_profile.decision_impact}")
        st.write(f"• **Automation Level:** {system_profile.automation_level}")
    
    with col2:
        st.markdown("**Risk Factors:**")
        st.write(f"• **Data Types:** {len(system_profile.data_types)} types")
        st.write(f"• **User Groups:** {len(system_profile.user_groups)} groups")
        st.write(f"• **Processing Scope:** {system_profile.data_processing_scope}")
        st.write(f"• **Human Oversight:** {'Yes' if system_profile.human_oversight else 'No'}")
    
    # Risk assessment details
    st.markdown("### 📋 Risk Assessment Details")
    
    with st.expander("🔍 View Detailed Risk Analysis"):
        st.write("**High-Risk Indicators:**")
        high_risk_indicators = [
            "Biometric identification systems",
            "Critical infrastructure management",
            "Educational assessment systems",
            "Employment and recruitment tools",
            "Credit scoring systems",
            "Healthcare diagnosis systems",
            "Law enforcement applications",
            "Migration and border control"
        ]
        
        for indicator in high_risk_indicators:
            if any(keyword in system_profile.use_case.lower() for keyword in indicator.lower().split()):
                st.write(f"• ✅ {indicator}")
            else:
                st.write(f"• ❌ {indicator}")
    
    # Store risk assessment
    st.session_state.ai_risk_level = risk_level
    st.session_state.ai_calculator_step = 3
    
    st.success("✅ Risk assessment completed! Move to Compliance Analysis tab.")

def render_compliance_analysis():
    """Render the compliance analysis section"""
    
    st.subheader("📊 AI Act Compliance Analysis")
    
    if 'ai_act_system_profile' not in st.session_state or 'ai_risk_level' not in st.session_state:
        st.info("Please complete the System Profile and Risk Assessment first")
        return
    
    system_profile = st.session_state.ai_act_system_profile
    risk_level = st.session_state.ai_risk_level
    calculator = AIActCalculator(region="Netherlands")
    
    # Current compliance status form
    st.markdown("### 📋 Current Compliance Status")
    st.write("Please indicate your current implementation status for each requirement:")
    
    with st.form("ai_act_compliance_status_form"):
        current_compliance = {}
        
        # Get applicable articles
        applicable_articles = calculator._get_applicable_articles(risk_level)
        
        if applicable_articles:
            for article in applicable_articles:
                article_info = calculator.compliance_articles[article]
                
                st.markdown(f"**{article_info['title']}** (Deadline: {article_info['deadline']})")
                
                implemented = st.checkbox(
                    f"✅ {article_info['title']} implemented",
                    key=f"compliance_{article.value}",
                    help=f"Implementation effort: {article_info['implementation_effort']}"
                )
                
                current_compliance[article.value] = implemented
                
                # Show requirements
                with st.expander(f"View {article_info['title']} Requirements"):
                    for req in article_info['requirements']:
                        st.write(f"• {req}")
        else:
            st.info("Minimal compliance requirements for this risk level")
            current_compliance = {"basic_transparency": True}
        
        # Additional information
        st.markdown("### 💰 Business Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            annual_turnover = st.number_input(
                "Annual Turnover (€)",
                min_value=0,
                value=1000000,
                step=100000,
                help="Used for fine risk calculation"
            )
        
        with col2:
            company_size = st.selectbox(
                "Company Size",
                ["Startup (<10 employees)", "Small (10-50)", "Medium (50-250)", "Large (250+)"],
                help="Company size affects implementation complexity"
            )
        
        # Submit compliance analysis
        analyze_compliance = st.form_submit_button("📊 Analyze Compliance", type="primary")
        
        if analyze_compliance:
            # Perform complete assessment with error handling
            try:
                with st.spinner("Analyzing compliance requirements..."):
                    assessment = calculator.perform_complete_assessment(
                        system_profile=system_profile,
                        current_compliance=current_compliance,
                        annual_turnover=annual_turnover
                    )
                
                # Store assessment
                st.session_state.ai_compliance_assessment = assessment
                st.session_state.ai_calculator_step = 4
                
                # Display results
                display_compliance_results(assessment)
                
            except Exception as e:
                st.error(f"Error analyzing compliance: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

def display_compliance_results(assessment: ComplianceAssessment):
    """Display comprehensive compliance results"""
    
    st.markdown("### 📊 Compliance Analysis Results")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Compliance Score",
            f"{assessment.compliance_score:.1f}/100",
            help="Overall compliance percentage"
        )
    
    with col2:
        risk_level_display = assessment.risk_level.value.replace("_", " ").title()
        if assessment.compliance_score >= 85 and assessment.risk_level == AISystemRiskLevel.HIGH_RISK:
            risk_level_display += " (Well Managed)"
        
        st.metric(
            "Risk Level",
            risk_level_display,
            help="AI Act risk classification based on use case"
        )
    
    with col3:
        fine_display = f"€{assessment.fine_risk:,.0f}"
        if assessment.fine_risk < 1000 and assessment.compliance_score >= 85:
            fine_display = "Very Low Risk"
        
        st.metric(
            "Fine Risk",
            fine_display,
            help="Current fine risk based on compliance level"
        )
    
    with col4:
        st.metric(
            "Implementation Cost",
            f"€{assessment.cost_estimate.get('total_estimated_cost', 0):,.0f}",
            help="Estimated implementation cost"
        )
    
    # Compliance score visualization
    st.markdown("### 📈 Compliance Score Breakdown")
    
    if assessment.compliance_score >= 90:
        st.success(f"✅ Excellent compliance score ({assessment.compliance_score:.1f}/100)")
        if assessment.risk_level == AISystemRiskLevel.HIGH_RISK:
            st.info("🛡️ High-risk system with excellent compliance - fine risk significantly reduced")
    elif assessment.compliance_score >= 70:
        st.warning(f"⚠️ Good compliance score ({assessment.compliance_score:.1f}/100)")
        if assessment.risk_level == AISystemRiskLevel.HIGH_RISK:
            st.warning("⚠️ High-risk system with good compliance - moderate fine risk reduction")
    elif assessment.compliance_score >= 50:
        st.warning(f"🟡 Moderate compliance score ({assessment.compliance_score:.1f}/100)")
        if assessment.risk_level == AISystemRiskLevel.HIGH_RISK:
            st.error("🚨 High-risk system with insufficient compliance - significant fine risk")
    else:
        st.error(f"🚨 Low compliance score ({assessment.compliance_score:.1f}/100)")
        if assessment.risk_level == AISystemRiskLevel.HIGH_RISK:
            st.error("🚨 High-risk system with poor compliance - maximum fine risk")
    
    # Progress bar
    st.progress(assessment.compliance_score / 100)
    
    # Risk classification explanation
    if assessment.risk_level == AISystemRiskLevel.HIGH_RISK and assessment.compliance_score >= 85:
        st.markdown("### ℹ️ Risk Classification Explanation")
        st.info("""
        **Why is this still classified as "High Risk"?**
        
        • **Risk Level** is determined by your AI system's use case and characteristics (e.g., employment screening, credit scoring)
        • **Compliance Score** shows how well you've implemented the required safeguards
        • **Fine Risk** is significantly reduced because of your excellent compliance implementation
        
        Your system remains "High Risk" by definition, but with excellent compliance, the actual regulatory risk is very low.
        """)
    
    # Compliance gaps
    if assessment.gaps:
        st.markdown("### ❌ Compliance Gaps Identified")
        for gap in assessment.gaps:
            st.write(f"• {gap}")
    
    # Recommendations
    st.markdown("### 💡 Recommendations")
    for rec in assessment.recommendations:
        st.write(f"• {rec}")
    
    # Implementation timeline
    st.markdown("### 📅 Implementation Timeline")
    
    for phase, activity in assessment.implementation_timeline.items():
        st.write(f"**{phase}:** {activity}")
    
    # Cost breakdown
    st.markdown("### 💰 Cost Breakdown")
    
    cost_data = []
    for item, cost in assessment.cost_estimate.items():
        if item != "total_estimated_cost":
            cost_data.append({"Component": item.replace("_", " ").title(), "Cost (€)": f"{cost:,.0f}"})
    
    if cost_data:
        st.table(cost_data)

def render_report_generation():
    """Render the report generation section"""
    
    st.subheader("📄 AI Act Compliance Report")
    
    if 'ai_compliance_assessment' not in st.session_state:
        st.info("Please complete the compliance analysis first")
        return
    
    assessment = st.session_state.ai_compliance_assessment
    calculator = AIActCalculator(region="Netherlands")
    
    # Report summary
    st.markdown("### 📋 Report Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**System:** {assessment.system_profile.system_name}")
        st.write(f"**Risk Level:** {assessment.risk_level.value.replace('_', ' ').title()}")
        st.write(f"**Compliance Score:** {assessment.compliance_score:.1f}/100")
    
    with col2:
        st.write(f"**Fine Risk:** €{assessment.fine_risk:,.0f}")
        st.write(f"**Implementation Cost:** €{assessment.cost_estimate.get('total_estimated_cost', 0):,.0f}")
        st.write(f"**Assessment Date:** {datetime.now().strftime('%Y-%m-%d')}")
    
    # Generate reports
    st.markdown("### 📥 Download Reports")
    
    # Check if user can download (paid users only)
    from config.pricing_config import can_download_reports
    if not can_download_reports():
        st.info("🔒 Report downloads available for paid subscribers. Upgrade to download reports.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generate Executive Summary", type="primary"):
                executive_summary = generate_executive_summary(assessment)
                st.download_button(
                    label="📥 Download Executive Summary",
                    data=executive_summary,
                    file_name=f"ai_act_executive_summary_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html"
                )
        
        with col2:
            if st.button("📋 Generate Technical Report", type="secondary"):
                technical_report = generate_technical_report(assessment)
                st.download_button(
                    label="📥 Download Technical Report",
                    data=technical_report,
                    file_name=f"ai_act_technical_report_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html"
                )
        
        # Export assessment data
        st.markdown("### 💾 Export Assessment Data")
        
        if st.button("📄 Export JSON Data"):
            report_data = calculator.export_assessment_report(assessment)
            st.download_button(
                label="📥 Download Assessment Data",
                data=json.dumps(report_data, indent=2),
                file_name=f"ai_act_assessment_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

def generate_executive_summary(assessment: ComplianceAssessment) -> str:
    """Generate executive summary HTML report"""
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Act Compliance Executive Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f2f6; padding: 20px; border-radius: 5px; }}
            .risk-high {{ color: #ff4444; }}
            .risk-medium {{ color: #ff8c00; }}
            .risk-low {{ color: #28a745; }}
            .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 5px; }}
            .recommendations {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI Act 2025 Compliance Assessment</h1>
            <h2>Executive Summary</h2>
            <p><strong>System:</strong> {assessment.system_profile.system_name}</p>
            <p><strong>Assessment Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
        
        <h3>📊 Key Metrics</h3>
        <div class="metric">
            <strong>Risk Level:</strong> {assessment.risk_level.value.replace('_', ' ').title()}
        </div>
        <div class="metric">
            <strong>Compliance Score:</strong> {assessment.compliance_score:.1f}/100
        </div>
        <div class="metric">
            <strong>Fine Risk:</strong> €{assessment.fine_risk:,.0f}
        </div>
        <div class="metric">
            <strong>Implementation Cost:</strong> €{assessment.cost_estimate.get('total_estimated_cost', 0):,.0f}
        </div>
        
        <h3>🎯 Risk Assessment</h3>
        <p><strong>Use Case:</strong> {assessment.system_profile.use_case}</p>
        <p><strong>Deployment Context:</strong> {assessment.system_profile.deployment_context}</p>
        <p><strong>Decision Impact:</strong> {assessment.system_profile.decision_impact}</p>
        
        <h3>💡 Key Recommendations</h3>
        <div class="recommendations">
            <ul>
                {''.join(f'<li>{rec}</li>' for rec in assessment.recommendations)}
            </ul>
        </div>
        
        <h3>📅 Implementation Timeline</h3>
        <ul>
            {''.join(f'<li><strong>{phase}:</strong> {activity}</li>' for phase, activity in assessment.implementation_timeline.items())}
        </ul>
        
        <hr>
        <p><small>Generated by DataGuardian Pro - AI Act Compliance Platform</small></p>
    </body>
    </html>
    """
    
    return html_template

def generate_technical_report(assessment: ComplianceAssessment) -> str:
    """Generate technical implementation report"""
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Act Technical Implementation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f2f6; padding: 20px; border-radius: 5px; }}
            .requirement {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }}
            .cost-item {{ display: flex; justify-content: space-between; padding: 5px 0; }}
            .total {{ font-weight: bold; border-top: 2px solid #000; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔧 AI Act Technical Implementation Report</h1>
            <p><strong>System:</strong> {assessment.system_profile.system_name}</p>
            <p><strong>Assessment Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
        
        <h3>📋 System Profile</h3>
        <p><strong>Purpose:</strong> {assessment.system_profile.purpose}</p>
        <p><strong>Use Case:</strong> {assessment.system_profile.use_case}</p>
        <p><strong>Data Types:</strong> {', '.join(assessment.system_profile.data_types)}</p>
        <p><strong>User Groups:</strong> {', '.join(assessment.system_profile.user_groups)}</p>
        <p><strong>Geographic Deployment:</strong> {', '.join(assessment.system_profile.geographic_deployment)}</p>
        
        <h3>📊 Compliance Requirements</h3>
        {''.join(f'<div class="requirement"><strong>{req.article.value}:</strong> {req.description}<br><small>Effort: {req.implementation_effort} | Deadline: {req.deadline}</small></div>' for req in assessment.requirements)}
        
        <h3>❌ Compliance Gaps</h3>
        <ul>
            {''.join(f'<li>{gap}</li>' for gap in assessment.gaps)}
        </ul>
        
        <h3>💰 Implementation Cost Breakdown</h3>
        {''.join(f'<div class="cost-item"><span>{item.replace("_", " ").title()}</span><span>€{cost:,.0f}</span></div>' for item, cost in assessment.cost_estimate.items() if item != "total_estimated_cost")}
        <div class="cost-item total">
            <span>Total Estimated Cost</span>
            <span>€{assessment.cost_estimate.get('total_estimated_cost', 0):,.0f}</span>
        </div>
        
        <h3>🇳🇱 Netherlands-Specific Considerations</h3>
        <ul>
            <li><strong>UAVG Compliance:</strong> Required for Dutch deployment</li>
            <li><strong>BSN Handling:</strong> {'Required' if 'person_data' in assessment.system_profile.data_types else 'Not required'}</li>
            <li><strong>Dutch DPA Registration:</strong> {'Required' if assessment.risk_level == AISystemRiskLevel.HIGH_RISK else 'Not required'}</li>
        </ul>
        
        <hr>
        <p><small>Generated by DataGuardian Pro - AI Act Compliance Platform</small></p>
    </body>
    </html>
    """
    
    return html_template