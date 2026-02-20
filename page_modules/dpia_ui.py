import streamlit as st
import uuid
import logging
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def track_scanner_usage(scanner_type: str, region: str, success: bool = True, duration_ms: int = 0):
    """Track scanner usage for license management"""
    try:
        from services.license_integration import LicenseIntegration
        license_manager = LicenseIntegration()
        license_manager.track_scan_usage(scanner_type)
    except Exception as e:
        logger.debug(f"License tracking not available: {e}")

def track_scan_failed_wrapper(scanner_type, user_id, session_id, error_message, region, details=None):
    """Wrapper for tracking failed scans"""
    try:
        from utils.activity_tracker import track_scan_failed
        track_scan_failed(
            session_id=session_id,
            user_id=user_id,
            username=user_id,
            scanner_type=scanner_type,
            error_message=error_message,
            region=region,
            details=details
        )
    except Exception as e:
        logger.warning(f"Failed to track scan failure: {e}")

def display_scan_results(scan_results: Dict[str, Any]):
    """Display scan results in expandable sections"""
    findings = scan_results.get('findings', [])
    if findings:
        with st.expander(f"📋 Detailed Findings ({len(findings)})", expanded=False):
            for finding in findings:
                severity = finding.get('severity', 'Medium')
                icon = "🔴" if severity == 'Critical' else "🟠" if severity == 'High' else "🟡" if severity == 'Medium' else "🟢"
                st.markdown(f"{icon} **{finding.get('type', 'Finding')}**: {finding.get('description', '')}")
                if finding.get('recommendation'):
                    st.caption(f"💡 {finding.get('recommendation')}")


def render_dpia_scanner_interface(region: str, username: str):
    """Enhanced DPIA scanner interface with step-by-step wizard"""
    # Import required modules to avoid unbound variables
    from utils.activity_tracker import ScannerType
    
    # Initialize variables at function start to avoid scope issues
    session_id = st.session_state.get('session_id', str(uuid.uuid4()))
    user_id = st.session_state.get('user_id', username)
    
    st.title("📋 DPIA Assessment - Step by Step")
    
    # Initialize session state for DPIA wizard
    if 'dpia_step' not in st.session_state:
        st.session_state.dpia_step = 1
    if 'dpia_responses' not in st.session_state:
        st.session_state.dpia_responses = {}
    if 'dpia_completed' not in st.session_state:
        st.session_state.dpia_completed = False
    
    # Progress tracking
    progress = st.progress(st.session_state.dpia_step / 5)
    st.write(f"**Step {st.session_state.dpia_step} of 5**")
    
    # Step-by-step interface
    if st.session_state.dpia_step == 1:
        show_project_info_step(region, username)
    elif st.session_state.dpia_step == 2:
        show_data_types_step(region, username)
    elif st.session_state.dpia_step == 3:
        show_risk_factors_step(region, username)
    elif st.session_state.dpia_step == 4:
        show_safeguards_step(region, username)
    elif st.session_state.dpia_step == 5:
        show_review_submit_step(region, username)

def show_project_info_step(region: str, username: str):
    """Step 1: Project Information"""
    st.subheader("📝 Step 1: Project Information")
    
    with st.expander("ℹ️ What information do I need?", expanded=False):
        st.write("""
        **Project Name**: A clear name for your data processing project
        **Data Controller**: The organization responsible for determining how personal data is processed
        **Processing Purpose**: The specific reason why you're collecting and processing personal data
        """)
    
    project_name = st.text_input(
        "Project Name *",
        value=st.session_state.dpia_responses.get('project_name', ''),
        placeholder="e.g., Employee Performance Management System"
    )
    
    data_controller = st.text_input(
        "Data Controller *",
        value=st.session_state.dpia_responses.get('data_controller', ''),
        placeholder="e.g., ABC Company B.V."
    )
    
    processing_purpose = st.text_area(
        "Processing Purpose *",
        value=st.session_state.dpia_responses.get('processing_purpose', ''),
        placeholder="Describe the purpose of data processing (e.g., Performance evaluation, recruitment, customer service)",
        height=100
    )
    
    # Validation and navigation
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Next Step →", type="primary", width="stretch"):
            if project_name and data_controller and processing_purpose:
                st.session_state.dpia_responses.update({
                    'project_name': project_name,
                    'data_controller': data_controller,
                    'processing_purpose': processing_purpose
                })
                st.session_state.dpia_step = 2
                st.rerun()
            else:
                st.error("Please fill in all required fields marked with *")

def show_data_types_step(region: str, username: str):
    """Step 2: Data Types"""
    st.subheader("📊 Step 2: Data Types Being Processed")
    
    with st.expander("ℹ️ Understanding data categories", expanded=False):
        st.write("""
        **Personal Data**: Any information about an identified or identifiable person
        **Sensitive Data**: Special categories like health, biometric, racial origin, political opinions
        **Biometric Data**: Fingerprints, facial recognition, iris scans
        **Health Data**: Medical records, fitness tracking, mental health information
        """)
    
    col1, col2 = st.columns(2)
    with col1:
        personal_data = st.checkbox(
            "Personal Data",
            value=st.session_state.dpia_responses.get('personal_data', True),
            help="Names, email addresses, phone numbers, etc."
        )
        sensitive_data = st.checkbox(
            "Sensitive Data",
            value=st.session_state.dpia_responses.get('sensitive_data', False),
            help="Special categories under GDPR Article 9"
        )
    with col2:
        biometric_data = st.checkbox(
            "Biometric Data",
            value=st.session_state.dpia_responses.get('biometric_data', False),
            help="Fingerprints, facial recognition, etc."
        )
        health_data = st.checkbox(
            "Health Data",
            value=st.session_state.dpia_responses.get('health_data', False),
            help="Medical records, health monitoring"
        )
    
    # Netherlands-specific checks
    if region == 'Netherlands':
        st.write("**Netherlands-Specific Data Types:**")
        bsn_data = st.checkbox(
            "BSN (Dutch Social Security Number)",
            value=st.session_state.dpia_responses.get('bsn_data', False),
            help="Special protection required under Dutch law"
        )
        government_data = st.checkbox(
            "Government Data",
            value=st.session_state.dpia_responses.get('government_data', False),
            help="Data processed for government purposes"
        )
    else:
        bsn_data = False
        government_data = False
    
    # Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Previous", width="stretch"):
            st.session_state.dpia_step = 1
            st.rerun()
    with col2:
        if st.button("Next Step →", type="primary", width="stretch"):
            st.session_state.dpia_responses.update({
                'personal_data': personal_data,
                'sensitive_data': sensitive_data,
                'biometric_data': biometric_data,
                'health_data': health_data,
                'bsn_data': bsn_data,
                'government_data': government_data
            })
            st.session_state.dpia_step = 3
            st.rerun()

def show_risk_factors_step(region: str, username: str):
    """Step 3: Risk Factors"""
    st.subheader("⚠️ Step 3: Risk Factors Assessment")
    
    with st.expander("ℹ️ GDPR Article 35 Risk Factors", expanded=False):
        st.write("""
        According to GDPR Article 35, a DPIA is required when processing is likely to result in high risk.
        These factors help determine the risk level of your processing activities.
        """)
    
    large_scale = st.checkbox(
        "Large-scale processing",
        value=st.session_state.dpia_responses.get('large_scale', False),
        help="Processing affecting many individuals (typically 1000+)"
    )
    
    automated_decisions = st.checkbox(
        "Automated decision-making",
        value=st.session_state.dpia_responses.get('automated_decisions', False),
        help="Automated systems making decisions that affect individuals"
    )
    
    vulnerable_subjects = st.checkbox(
        "Vulnerable data subjects",
        value=st.session_state.dpia_responses.get('vulnerable_subjects', False),
        help="Children, elderly, patients, employees in vulnerable positions"
    )
    
    new_technology = st.checkbox(
        "New or innovative technology",
        value=st.session_state.dpia_responses.get('new_technology', False),
        help="AI, machine learning, biometric systems, IoT devices"
    )
    
    systematic_monitoring = st.checkbox(
        "Systematic monitoring",
        value=st.session_state.dpia_responses.get('systematic_monitoring', False),
        help="CCTV, location tracking, behavioral monitoring"
    )
    
    cross_border_transfer = st.checkbox(
        "Cross-border data transfers",
        value=st.session_state.dpia_responses.get('cross_border_transfer', False),
        help="Transferring data outside the EU/EEA"
    )
    
    # Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Previous", width="stretch"):
            st.session_state.dpia_step = 2
            st.rerun()
    with col2:
        if st.button("Next Step →", type="primary", width="stretch"):
            st.session_state.dpia_responses.update({
                'large_scale': large_scale,
                'automated_decisions': automated_decisions,
                'vulnerable_subjects': vulnerable_subjects,
                'new_technology': new_technology,
                'systematic_monitoring': systematic_monitoring,
                'cross_border_transfer': cross_border_transfer
            })
            st.session_state.dpia_step = 4
            st.rerun()

def show_safeguards_step(region: str, username: str):
    """Step 4: Safeguards"""
    st.subheader("🛡️ Step 4: Security Safeguards")
    
    with st.expander("ℹ️ Security and Privacy Measures", expanded=False):
        st.write("""
        Document the security measures and safeguards you have in place to protect personal data.
        These measures help mitigate risks identified in the previous steps.
        """)
    
    encryption = st.checkbox(
        "Data encryption (at rest and in transit)",
        value=st.session_state.dpia_responses.get('encryption', False),
        help="Encryption protects data from unauthorized access"
    )
    
    access_controls = st.checkbox(
        "Access controls and authentication",
        value=st.session_state.dpia_responses.get('access_controls', False),
        help="Restricting access to authorized personnel only"
    )
    
    data_minimization = st.checkbox(
        "Data minimization practices",
        value=st.session_state.dpia_responses.get('data_minimization', False),
        help="Collecting only necessary data for the specified purpose"
    )
    
    retention_policy = st.checkbox(
        "Data retention policy",
        value=st.session_state.dpia_responses.get('retention_policy', False),
        help="Clear policies on how long data is kept"
    )
    
    consent_mechanisms = st.checkbox(
        "Consent mechanisms",
        value=st.session_state.dpia_responses.get('consent_mechanisms', False),
        help="Proper consent collection and management"
    )
    
    breach_procedures = st.checkbox(
        "Data breach procedures",
        value=st.session_state.dpia_responses.get('breach_procedures', False),
        help="Procedures for handling data breaches"
    )
    
    # Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Previous", width="stretch"):
            st.session_state.dpia_step = 3
            st.rerun()
    with col2:
        if st.button("Next Step →", type="primary", width="stretch"):
            st.session_state.dpia_responses.update({
                'encryption': encryption,
                'access_controls': access_controls,
                'data_minimization': data_minimization,
                'retention_policy': retention_policy,
                'consent_mechanisms': consent_mechanisms,
                'breach_procedures': breach_procedures
            })
            st.session_state.dpia_step = 5
            st.rerun()

def show_review_submit_step(region: str, username: str):
    """Step 5: Review and Submit"""
    st.subheader("📋 Step 5: Review and Generate Report")
    
    # Calculate risk score
    risk_assessment = calculate_dpia_risk(st.session_state.dpia_responses)
    
    # Display risk level
    risk_color = {"High": "red", "Medium": "orange", "Low": "green"}[risk_assessment['level'].split(' - ')[0]]
    st.markdown(f"**Risk Level:** <span style='color: {risk_color}; font-weight: bold;'>{risk_assessment['level']}</span>", unsafe_allow_html=True)
    
    # Show summary
    st.write("**Assessment Summary:**")
    st.write(f"• **Project:** {st.session_state.dpia_responses.get('project_name', 'N/A')}")
    st.write(f"• **Controller:** {st.session_state.dpia_responses.get('data_controller', 'N/A')}")
    st.write(f"• **Risk Score:** {risk_assessment['score']}/10")
    st.write(f"• **Risk Factors:** {len(risk_assessment['factors'])} identified")
    
    # Risk factors found
    if risk_assessment['factors']:
        st.write("**Risk Factors Identified:**")
        for factor in risk_assessment['factors']:
            st.write(f"• {factor}")
    
    # Navigation and submission
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Previous", width="stretch"):
            st.session_state.dpia_step = 4
            st.rerun()
    with col2:
        if st.button("🚀 Generate DPIA Report", type="primary", width="stretch"):
            execute_enhanced_dpia_scan(region, username, st.session_state.dpia_responses)

def calculate_dpia_risk(responses):
    """Calculate real DPIA risk based on GDPR Article 35 criteria"""
    risk_score = 0
    risk_factors = []
    
    # High-risk indicators from GDPR Article 35
    if responses.get('sensitive_data', False):
        risk_score += 3
        risk_factors.append("Special category data processing")
    
    if responses.get('large_scale', False):
        risk_score += 2
        risk_factors.append("Large-scale data processing")
    
    if responses.get('automated_decisions', False):
        risk_score += 3
        risk_factors.append("Automated decision-making")
    
    if responses.get('vulnerable_subjects', False):
        risk_score += 2
        risk_factors.append("Vulnerable data subjects")
    
    if responses.get('new_technology', False):
        risk_score += 2
        risk_factors.append("Innovative technology use")
    
    if responses.get('systematic_monitoring', False):
        risk_score += 2
        risk_factors.append("Systematic monitoring")
    
    if responses.get('cross_border_transfer', False):
        risk_score += 1
        risk_factors.append("Cross-border data transfers")
    
    # Netherlands-specific risk factors
    if responses.get('bsn_data', False):
        risk_score += 2
        risk_factors.append("BSN processing (Dutch law)")
    
    if responses.get('government_data', False):
        risk_score += 1
        risk_factors.append("Government data processing")
    
    # Calculate risk level
    if risk_score >= 7:
        risk_level = "High - DPIA Required"
    elif risk_score >= 4:
        risk_level = "Medium - DPIA Recommended"
    else:
        risk_level = "Low - Standard measures sufficient"
    
    return {
        'score': risk_score,
        'level': risk_level,
        'factors': risk_factors,
        'recommendations': generate_dpia_recommendations(risk_score, risk_factors, responses)
    }

def generate_dpia_recommendations(risk_score, risk_factors, responses):
    """Generate specific recommendations based on risk assessment"""
    recommendations = []
    
    if risk_score >= 7:
        recommendations.append({
            'title': 'Formal DPIA Required',
            'description': 'Conduct a formal DPIA as required by GDPR Article 35',
            'priority': 'Critical',
            'timeline': '1-2 weeks'
        })
    
    if 'Special category data processing' in risk_factors:
        recommendations.append({
            'title': 'Enhanced Data Protection',
            'description': 'Implement additional safeguards for special category data',
            'priority': 'High',
            'timeline': '2-4 weeks'
        })
    
    if 'Automated decision-making' in risk_factors:
        recommendations.append({
            'title': 'Human Oversight Implementation',
            'description': 'Ensure human review and intervention in automated decisions',
            'priority': 'High',
            'timeline': '2-3 weeks'
        })
    
    if not responses.get('encryption', False):
        recommendations.append({
            'title': 'Data Encryption',
            'description': 'Implement encryption for data at rest and in transit',
            'priority': 'Medium',
            'timeline': '1-2 weeks'
        })
    
    if not responses.get('retention_policy', False):
        recommendations.append({
            'title': 'Data Retention Policy',
            'description': 'Establish clear data retention and deletion policies',
            'priority': 'Medium',
            'timeline': '1 week'
        })
    
    if 'BSN processing (Dutch law)' in risk_factors:
        recommendations.append({
            'title': 'BSN Processing Authorization',
            'description': 'Verify authorization for BSN processing under Dutch law',
            'priority': 'High',
            'timeline': '1 week'
        })
    
    return recommendations

def execute_enhanced_dpia_scan(region, username, responses):
    """Execute enhanced DPIA assessment with real calculation"""
    try:
        from services.dpia_scanner import DPIAScanner
        from utils.activity_tracker import track_scan_started, track_scan_completed, track_scan_failed, ScannerType
        
        # Get session information
        session_id = st.session_state.get('session_id', str(uuid.uuid4()))
        user_id = st.session_state.get('user_id', username)
        
        # Track scan start
        scan_start_time = datetime.now()
        track_scan_started(
            session_id=session_id,
            user_id=user_id,
            username=username,
            scanner_type=ScannerType.DPIA,
            region=region,
            details={
                'project_name': responses.get('project_name', 'Unknown'),
                'data_controller': responses.get('data_controller', 'Unknown'),
                'legal_basis': responses.get('legal_basis', 'Unknown'),
                'sensitive_data': responses.get('sensitive_data', False),
                'large_scale': responses.get('large_scale', False),
                'automated_decisions': responses.get('automated_decisions', False)
            }
        )
        
        # Track license usage
        track_scanner_usage('dpia', region, success=True, duration_ms=0)
        
        # Convert region to language code
        language = 'nl' if region == 'Netherlands' else 'en'
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Phase 1: Risk Assessment
        status_text.text("📊 Phase 1: Calculating risk assessment...")
        progress_bar.progress(25)
        
        risk_assessment = calculate_dpia_risk(responses)
        
        # Phase 2: Generating findings
        status_text.text("🔍 Phase 2: Generating compliance findings...")
        progress_bar.progress(50)
        
        findings = generate_dpia_findings(risk_assessment, responses, region)
        
        # Phase 3: Creating report
        status_text.text("📄 Phase 3: Creating professional report...")
        progress_bar.progress(75)
        
        scan_results = {
            "scan_id": str(uuid.uuid4()),
            "scan_type": "Enhanced DPIA Scanner",
            "timestamp": datetime.now().isoformat(),
            "project_name": responses.get('project_name', ''),
            "data_controller": responses.get('data_controller', ''),
            "processing_purpose": responses.get('processing_purpose', ''),
            "risk_score": risk_assessment['score'],
            "risk_level": risk_assessment['level'],
            "risk_factors": risk_assessment['factors'],
            "recommendations": risk_assessment['recommendations'],
            "findings": findings,
            "responses": responses,
            "region": region,
            "compliance_status": "Compliant" if risk_assessment['score'] < 7 else "Requires Action",
            "netherlands_specific": region == 'Netherlands'
        }
        
        # Phase 4: Complete
        status_text.text("✅ Phase 4: DPIA assessment completed!")
        progress_bar.progress(100)
        
        # Display results
        display_enhanced_dpia_results(scan_results)
        
        # Calculate scan metrics and track completion
        scan_duration = int((datetime.now() - scan_start_time).total_seconds() * 1000)
        findings_count = len(scan_results["findings"])
        high_risk_count = sum(1 for f in scan_results["findings"] if f.get('severity') in ['Critical', 'High'])
        
        # Track successful completion
        track_scan_completed(
            session_id=session_id,
            user_id=user_id,
            username=username,
            scanner_type=ScannerType.DPIA,
            findings_count=findings_count,
            files_scanned=1,  # DPIA is a single assessment
            compliance_score=min(100, max(0, 100 - (scan_results["risk_score"] * 10))),
            duration_ms=scan_duration,
            region=region,
            details={
                'scan_id': scan_results["scan_id"],
                'high_risk_count': high_risk_count,
                'project_name': responses.get('project_name', 'Unknown'),
                'risk_score': scan_results["risk_score"],
                'risk_level': scan_results["risk_level"],
                'compliance_status': scan_results["compliance_status"],
                'netherlands_specific': scan_results["netherlands_specific"]
            }
        )
        
        # CRITICAL: Save scan results to database for Results/History pages
        try:
            from services.results_aggregator import ResultsAggregator
            aggregator = ResultsAggregator()
            
            scan_results['scan_type'] = 'DPIA Scanner'
            scan_results['file_count'] = 1
            scan_results['total_pii_found'] = findings_count
            scan_results['high_risk_count'] = high_risk_count
            scan_results['compliance_score'] = min(100, max(0, 100 - (scan_results["risk_score"] * 10)))
            
            stored_scan_id = aggregator.save_scan_result(username=username, result=scan_results)
            if stored_scan_id:
                logger.info(f"DPIA scan saved to database: {stored_scan_id}")
                st.session_state['last_scan_id'] = stored_scan_id
        except Exception as save_error:
            logger.error(f"Failed to save DPIA scan: {save_error}")
        
        # Reset wizard for new assessment
        st.session_state.dpia_step = 1
        st.session_state.dpia_responses = {}
        st.session_state.dpia_completed = True
        
    except Exception as e:
        # Track scan failure with safe error handling
        try:
            from utils.activity_tracker import ScannerType as LocalScannerType
            scanner_type_ref = LocalScannerType.DPIA
            
            local_session_id = st.session_state.get('session_id', str(uuid.uuid4()))
            local_user_id = st.session_state.get('user_id', username)
            
            track_scan_failed_wrapper(
                scanner_type=scanner_type_ref,
                user_id=local_user_id,
                session_id=local_session_id,
                error_message=str(e),
                region=region,
                details={
                    'project_name': responses.get('project_name', 'Unknown'),
                    'data_controller': responses.get('data_controller', 'Unknown')
                }
            )
        except Exception as track_error:
            logger.warning(f"DPIA scan tracking failed: {track_error}")
        st.error(f"DPIA assessment failed: {str(e)}")

def generate_dpia_findings(risk_assessment, responses, region):
    """Generate specific findings based on responses"""
    findings = []
    
    # Legal basis finding
    findings.append({
        'type': 'LEGAL_BASIS',
        'severity': 'High' if risk_assessment['score'] >= 7 else 'Medium',
        'description': 'Legal basis for processing must be clearly established',
        'recommendation': 'Document legal basis under GDPR Article 6',
        'gdpr_article': 'Article 6 - Lawfulness of processing'
    })
    
    # Data minimization
    if not responses.get('data_minimization', False):
        findings.append({
            'type': 'DATA_MINIMIZATION',
            'severity': 'Medium',
            'description': 'Data minimization practices not implemented',
            'recommendation': 'Implement data minimization to collect only necessary data',
            'gdpr_article': 'Article 5(1)(c) - Data minimization'
        })
    
    # Retention period
    if not responses.get('retention_policy', False):
        findings.append({
            'type': 'RETENTION_PERIOD',
            'severity': 'Medium',
            'description': 'Data retention periods not defined',
            'recommendation': 'Establish clear data retention and deletion policies',
            'gdpr_article': 'Article 5(1)(e) - Storage limitation'
        })
    
    # Security measures
    if not responses.get('encryption', False):
        findings.append({
            'type': 'SECURITY_MEASURES',
            'severity': 'High',
            'description': 'Data encryption not implemented',
            'recommendation': 'Implement encryption for data at rest and in transit',
            'gdpr_article': 'Article 32 - Security of processing'
        })
    
    # Netherlands-specific findings
    if region == 'Netherlands':
        if responses.get('bsn_data', False):
            findings.append({
                'type': 'BSN_PROCESSING',
                'severity': 'High',
                'description': 'BSN processing requires special authorization',
                'recommendation': 'Verify BSN processing authorization under Dutch law',
                'gdpr_article': 'Netherlands UAVG compliance'
            })
        
        if responses.get('government_data', False):
            findings.append({
                'type': 'GOVERNMENT_DATA',
                'severity': 'Medium',
                'description': 'Government data processing requires additional safeguards',
                'recommendation': 'Ensure compliance with Dutch Government Data Protection Act',
                'gdpr_article': 'Netherlands Police Act compliance'
            })
    
    return findings

def display_enhanced_dpia_results(scan_results):
    """Display enhanced DPIA results with professional formatting"""
    st.markdown("---")
    st.subheader("📋 DPIA Assessment Results")
    
    # Risk level display
    risk_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[scan_results['risk_level'].split(' - ')[0]]
    st.markdown(f"### {risk_color} Risk Level: {scan_results['risk_level']}")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Risk Score", f"{min(10, scan_results['risk_score'])}/10")
    with col2:
        st.metric("Risk Factors", len(scan_results['risk_factors']))
    with col3:
        st.metric("Recommendations", len(scan_results['recommendations']))
    with col4:
        st.metric("Compliance Status", scan_results['compliance_status'])
    
    # Risk factors
    if scan_results['risk_factors']:
        st.write("**Risk Factors Identified:**")
        for factor in scan_results['risk_factors']:
            st.write(f"• {factor}")
    
    # Recommendations
    st.write("**Key Recommendations:**")
    for rec in scan_results['recommendations']:
        priority_color = {"Critical": "🔴", "High": "🟡", "Medium": "🟢"}[rec['priority']]
        st.write(f"{priority_color} **{rec['title']}** ({rec['timeline']})")
        st.write(f"   {rec['description']}")
    
    # Detailed findings
    display_scan_results(scan_results)
    
    # Professional report download
    st.markdown("---")
    st.subheader("📄 Professional Reports")
    
    # Check if user can download (paid users only)
    from config.pricing_config import can_download_reports
    if not can_download_reports():
        st.info("🔒 **Report downloads available for paid subscribers only.** Upgrade to download DPIA reports.")
    else:
        # Generate enhanced HTML report
        html_report = generate_enhanced_dpia_report(scan_results)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download DPIA Report (HTML)",
                data=html_report,
                file_name=f"dpia-report-{scan_results['scan_id']}.html",
                mime="text/html",
                width="stretch"
            )
        
        with col2:
            # JSON report for technical users
            json_report = json.dumps(scan_results, indent=2, default=str)
            st.download_button(
                label="📊 Download Assessment Data (JSON)",
                data=json_report,
                file_name=f"dpia-data-{scan_results['scan_id']}.json",
                mime="application/json",
                width="stretch"
            )
    
    # Success message
    st.success("✅ Enhanced DPIA assessment completed successfully!")


def _generate_dpo_signoff_section(scan_results):
    """Generate DPO Sign-off Section for DPIA report"""
    return """
        <div style="background: #e3f2fd; padding: 25px; border-radius: 8px; margin: 25px 0; border: 2px solid #1976d2;">
            <h2 style="color: #1565c0; margin-top: 0;">🔏 DPO Sign-off Section</h2>
            <p style="color: #555; margin-bottom: 20px;">
                As required by GDPR Article 35(2), the Data Protection Officer must be consulted on this DPIA.
            </p>
            
            <table style="width: 100%; border-collapse: collapse; background: white;">
                <tr>
                    <td style="padding: 15px; border: 1px solid #ddd; width: 30%;"><strong>DPO Name:</strong></td>
                    <td style="padding: 15px; border: 1px solid #ddd; border-bottom: 2px dotted #999;">_______________________________</td>
                </tr>
                <tr>
                    <td style="padding: 15px; border: 1px solid #ddd;"><strong>Review Date:</strong></td>
                    <td style="padding: 15px; border: 1px solid #ddd; border-bottom: 2px dotted #999;">_______________________________</td>
                </tr>
                <tr>
                    <td style="padding: 15px; border: 1px solid #ddd;"><strong>DPO Recommendation:</strong></td>
                    <td style="padding: 15px; border: 1px solid #ddd;">
                        <label style="margin-right: 20px;">☐ Proceed with processing</label>
                        <label style="margin-right: 20px;">☐ Proceed with conditions</label>
                        <label>☐ Further review needed</label>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 15px; border: 1px solid #ddd;"><strong>DPO Comments:</strong></td>
                    <td style="padding: 15px; border: 1px solid #ddd; height: 60px; border-bottom: 2px dotted #999;"></td>
                </tr>
                <tr>
                    <td style="padding: 15px; border: 1px solid #ddd;"><strong>DPO Signature:</strong></td>
                    <td style="padding: 15px; border: 1px solid #ddd; border-bottom: 2px dotted #999;">_______________________________</td>
                </tr>
            </table>
            
            <p style="font-size: 11px; color: #666; margin-top: 15px;">
                <em>Legal Reference: GDPR Article 35(2), Article 39(1)(c) - DPO tasks include providing advice on DPIA</em>
            </p>
        </div>
    """


def _generate_ap_consultation_section(scan_results):
    """Generate Autoriteit Persoonsgegevens (Dutch DPA) Consultation Trigger Section"""
    risk_level = scan_results.get('risk_level', '').lower()
    risk_score = scan_results.get('risk_score', 0)
    
    # Determine if AP consultation is required (high residual risk)
    ap_required = 'high' in risk_level or risk_score >= 7
    
    if ap_required:
        status_color = "#dc3545"
        status_bg = "#f8d7da"
        status_icon = "⚠️"
        status_text = "REQUIRED"
        message = """
            <p><strong>Residual risk remains HIGH after mitigation measures.</strong></p>
            <p>→ Autoriteit Persoonsgegevens (AP) consultation is <strong>REQUIRED</strong></p>
            <p>→ <strong>Deadline:</strong> Before processing starts</p>
            <p>→ <strong>Contact:</strong> <a href="https://autoriteitpersoonsgegevens.nl">autoriteitpersoonsgegevens.nl</a></p>
        """
    else:
        status_color = "#28a745"
        status_bg = "#d4edda"
        status_icon = "✅"
        status_text = "NOT REQUIRED"
        message = """
            <p>Residual risk is acceptable after mitigation measures.</p>
            <p>→ AP consultation is <strong>NOT REQUIRED</strong> at this time</p>
            <p>→ Re-assess if processing activities change significantly</p>
        """
    
    return f"""
        <div style="background: {status_bg}; padding: 25px; border-radius: 8px; margin: 25px 0; border-left: 5px solid {status_color};">
            <h2 style="color: {status_color}; margin-top: 0;">{status_icon} AP Consultation Trigger</h2>
            <div style="background: white; padding: 15px; border-radius: 6px; margin: 15px 0;">
                <p style="font-size: 18px; font-weight: bold; color: {status_color};">
                    Status: {status_text}
                </p>
                {message}
            </div>
            <p style="font-size: 11px; color: #666;">
                <em>Legal Reference: GDPR Article 36 - Prior consultation with supervisory authority when residual risk is high</em>
            </p>
        </div>
    """


def _generate_netherlands_specific_section(scan_results):
    """Generate Netherlands-specific compliance section (UAVG, AP Guidelines, BSN)"""
    region = scan_results.get('region', 'Netherlands')
    
    # Detect if BSN processing is involved
    has_bsn = any('bsn' in str(f).lower() or 'burgerservicenummer' in str(f).lower() 
                  for f in scan_results.get('findings', []))
    
    bsn_section = ""
    if has_bsn:
        bsn_section = """
            <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin: 15px 0; border-left: 4px solid #ffc107;">
                <h4 style="margin: 0 0 10px 0; color: #856404;">🆔 BSN Processing Detected</h4>
                <p>Burgerservicenummer (BSN) processing requires additional safeguards under UAVG.</p>
                <ul style="margin: 10px 0;">
                    <li>UAVG Article 46: BSN may only be used when legally required</li>
                    <li>Ensure legal basis is documented</li>
                    <li>Implement additional security measures</li>
                    <li>Limit access to authorized personnel only</li>
                </ul>
            </div>
        """
    
    return f"""
        <div style="background: #fff8e1; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #ffb300;">
            <h2 style="color: #ff6f00; margin-top: 0;">🇳🇱 Netherlands-Specific Compliance</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div style="background: white; padding: 15px; border-radius: 6px;">
                    <h4 style="margin: 0 0 10px 0; color: #e65100;">📜 UAVG References</h4>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px;">
                        <li>UAVG Art. 1-10: General provisions</li>
                        <li>UAVG Art. 22-31: Special categories</li>
                        <li>UAVG Art. 41-51: Enforcement & AP powers</li>
                        <li>UAVG Art. 46: BSN processing rules</li>
                    </ul>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 6px;">
                    <h4 style="margin: 0 0 10px 0; color: #e65100;">📋 AP Guidelines 2024-2025</h4>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px;">
                        <li>DPIA threshold criteria for NL</li>
                        <li>Healthcare data processing guidance</li>
                        <li>Employee monitoring requirements</li>
                        <li>Camera surveillance rules</li>
                    </ul>
                </div>
            </div>
            
            {bsn_section}
            
            <div style="background: white; padding: 15px; border-radius: 6px; margin-top: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #e65100;">🏛️ Sector-Specific Requirements</h4>
                <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Sector</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Additional Requirements</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">Healthcare</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Wbp, NEN 7510, Medical confidentiality</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">Financial</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Wwft, DNB guidelines, PSD2</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">Government</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">BIO, Baseline Informatiebeveiliging</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">Telecom</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Telecommunicatiewet, ACM rules</td>
                    </tr>
                </table>
            </div>
            
            <p style="font-size: 11px; color: #666; margin-top: 15px;">
                <em>References: Uitvoeringswet AVG (UAVG), Autoriteit Persoonsgegevens Guidelines 2024-2025</em>
            </p>
        </div>
    """


def _generate_implementation_timeline(scan_results):
    """Generate visual implementation timeline (Gantt-style) for recommendations"""
    recommendations = scan_results.get('recommendations', [])
    
    if not recommendations:
        return ""
    
    # Generate timeline bars
    timeline_items = []
    colors = {
        'Critical': '#dc3545',
        'High': '#fd7e14', 
        'Medium': '#ffc107',
        'Low': '#28a745'
    }
    
    for i, rec in enumerate(recommendations):
        priority = rec.get('priority', 'Medium')
        color = colors.get(priority, '#6c757d')
        title = rec.get('title', f'Recommendation {i+1}')[:40]
        timeline = rec.get('timeline', '1-2 weeks')
        
        # Calculate bar width based on timeline
        if 'day' in timeline.lower():
            width = 15
        elif '1' in timeline and 'week' in timeline.lower():
            width = 25
        elif '2' in timeline and 'week' in timeline.lower():
            width = 40
        elif '3' in timeline and 'week' in timeline.lower():
            width = 55
        elif '4' in timeline and 'week' in timeline.lower():
            width = 70
        elif 'month' in timeline.lower():
            width = 85
        else:
            width = 30
        
        timeline_items.append(f"""
            <div style="display: flex; align-items: center; margin: 8px 0;">
                <div style="width: 200px; font-size: 12px; padding-right: 10px; text-align: right;">{title}</div>
                <div style="flex: 1; background: #e9ecef; border-radius: 4px; height: 24px; position: relative;">
                    <div style="width: {width}%; background: {color}; height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 8px;">
                        <span style="color: white; font-size: 11px; font-weight: bold;">{timeline}</span>
                    </div>
                </div>
                <div style="width: 80px; padding-left: 10px;">
                    <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px;">{priority}</span>
                </div>
            </div>
        """)
    
    return f"""
        <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #dee2e6;">
            <h2 style="color: #495057; margin-top: 0;">📅 Implementation Timeline</h2>
            <p style="color: #666; margin-bottom: 20px;">Visual timeline for implementing recommendations by priority</p>
            
            <div style="background: white; padding: 20px; border-radius: 6px;">
                <div style="display: flex; margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 10px;">
                    <div style="width: 200px; font-weight: bold; text-align: right; padding-right: 10px;">Task</div>
                    <div style="flex: 1; display: flex; justify-content: space-between; font-size: 11px; color: #666;">
                        <span>Week 1</span>
                        <span>Week 2</span>
                        <span>Week 3</span>
                        <span>Week 4</span>
                        <span>Month 2+</span>
                    </div>
                    <div style="width: 80px; text-align: center; font-weight: bold;">Priority</div>
                </div>
                {''.join(timeline_items)}
            </div>
            
            <div style="display: flex; gap: 15px; margin-top: 15px; font-size: 11px;">
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #dc3545; border-radius: 2px;"></span> Critical</span>
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #fd7e14; border-radius: 2px;"></span> High</span>
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #ffc107; border-radius: 2px;"></span> Medium</span>
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #28a745; border-radius: 2px;"></span> Low</span>
            </div>
        </div>
    """


def _generate_stakeholder_signoff_section(scan_results):
    """Generate Stakeholder Sign-off Table for DPIA report"""
    return """
        <div style="background: #e8f5e9; padding: 25px; border-radius: 8px; margin: 25px 0; border: 2px solid #4caf50;">
            <h2 style="color: #2e7d32; margin-top: 0;">✍️ Stakeholder Sign-off</h2>
            <p style="color: #555; margin-bottom: 20px;">
                All relevant stakeholders must review and approve this DPIA before processing begins.
            </p>
            
            <table style="width: 100%; border-collapse: collapse; background: white;">
                <thead>
                    <tr style="background: #4caf50; color: white;">
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Role</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Name</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Date</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Signature</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Data Controller</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Data Protection Officer (DPO)</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>IT Security Officer</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Legal / Compliance</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Business Owner</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                        <td style="padding: 12px; border: 1px solid #ddd; border-bottom: 2px dotted #999;"></td>
                    </tr>
                </tbody>
            </table>
            
            <p style="font-size: 11px; color: #666; margin-top: 15px;">
                <em>All parties confirm they have reviewed the DPIA and approve the processing activities described herein.</em>
            </p>
        </div>
    """


def _generate_data_flow_diagram(scan_results):
    """Generate visual Data Flow Diagram section"""
    project_name = scan_results.get('project_name', 'Data Processing System')
    data_controller = scan_results.get('data_controller', 'Organization')
    
    # Determine data types being processed
    data_types = []
    if scan_results.get('personal_data', True):
        data_types.append('Personal Data')
    if scan_results.get('sensitive_data'):
        data_types.append('Sensitive Data')
    if scan_results.get('biometric_data'):
        data_types.append('Biometric Data')
    if scan_results.get('health_data'):
        data_types.append('Health Data')
    if scan_results.get('bsn_data'):
        data_types.append('BSN Data')
    
    data_types_html = ''.join(f'<li>{dt}</li>' for dt in data_types) if data_types else '<li>Personal Data</li>'
    
    return f"""
        <div style="background: #e8eaf6; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #5c6bc0;">
            <h2 style="color: #3949ab; margin-top: 0;">🔄 Data Flow Diagram</h2>
            <p style="color: #555; margin-bottom: 20px;">Visual representation of data flow through the processing system</p>
            
            <div style="background: white; padding: 25px; border-radius: 8px; text-align: center;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <!-- Data Subjects -->
                    <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; min-width: 140px; border: 2px solid #1976d2;">
                        <div style="font-size: 32px;">👥</div>
                        <div style="font-weight: bold; color: #1565c0;">Data Subjects</div>
                        <div style="font-size: 11px; color: #666;">Individuals</div>
                    </div>
                    
                    <!-- Arrow 1 -->
                    <div style="font-size: 24px; color: #5c6bc0;">→</div>
                    
                    <!-- Collection Point -->
                    <div style="background: #fff3e0; padding: 20px; border-radius: 8px; min-width: 140px; border: 2px solid #ff9800;">
                        <div style="font-size: 32px;">📥</div>
                        <div style="font-weight: bold; color: #e65100;">Collection</div>
                        <div style="font-size: 11px; color: #666;">Forms/APIs</div>
                    </div>
                    
                    <!-- Arrow 2 -->
                    <div style="font-size: 24px; color: #5c6bc0;">→</div>
                    
                    <!-- Processing -->
                    <div style="background: #f3e5f5; padding: 20px; border-radius: 8px; min-width: 140px; border: 2px solid #9c27b0;">
                        <div style="font-size: 32px;">⚙️</div>
                        <div style="font-weight: bold; color: #7b1fa2;">Processing</div>
                        <div style="font-size: 11px; color: #666;">{project_name[:15]}...</div>
                    </div>
                    
                    <!-- Arrow 3 -->
                    <div style="font-size: 24px; color: #5c6bc0;">→</div>
                    
                    <!-- Storage -->
                    <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; min-width: 140px; border: 2px solid #4caf50;">
                        <div style="font-size: 32px;">💾</div>
                        <div style="font-weight: bold; color: #2e7d32;">Storage</div>
                        <div style="font-size: 11px; color: #666;">EU Servers</div>
                    </div>
                </div>
                
                <!-- Data Controller -->
                <div style="margin-top: 30px; padding: 15px; background: #fafafa; border-radius: 6px; border: 1px dashed #999;">
                    <strong>Data Controller:</strong> {data_controller}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                <div style="background: white; padding: 15px; border-radius: 6px;">
                    <h4 style="margin: 0 0 10px 0; color: #3949ab;">📊 Data Types Processed</h4>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px;">
                        {data_types_html}
                    </ul>
                </div>
                <div style="background: white; padding: 15px; border-radius: 6px;">
                    <h4 style="margin: 0 0 10px 0; color: #3949ab;">🔐 Data Recipients</h4>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px;">
                        <li>Internal staff (authorized)</li>
                        <li>IT administrators</li>
                        <li>Third-party processors (if any)</li>
                        <li>Regulatory authorities (if required)</li>
                    </ul>
                </div>
            </div>
        </div>
    """


def _generate_processing_description(scan_results):
    """Generate detailed Processing Description section (what/why/how)"""
    purpose = scan_results.get('processing_purpose', 'Data processing for business operations')
    project_name = scan_results.get('project_name', 'Data Processing Project')
    
    return f"""
        <div style="background: #fce4ec; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #ec407a;">
            <h2 style="color: #c2185b; margin-top: 0;">📝 Processing Description</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #e91e63;">
                    <h4 style="margin: 0 0 15px 0; color: #880e4f;">WHAT</h4>
                    <p style="font-size: 13px; margin: 0;">
                        <strong>Nature of Processing:</strong><br/>
                        {purpose[:200]}{'...' if len(purpose) > 200 else ''}
                    </p>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #9c27b0;">
                    <h4 style="margin: 0 0 15px 0; color: #4a148c;">WHY</h4>
                    <p style="font-size: 13px; margin: 0;">
                        <strong>Purpose & Necessity:</strong><br/>
                        Processing is necessary to achieve the stated business objectives and fulfill legal obligations.
                    </p>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #673ab7;">
                    <h4 style="margin: 0 0 15px 0; color: #311b92;">HOW</h4>
                    <p style="font-size: 13px; margin: 0;">
                        <strong>Processing Methods:</strong><br/>
                        Collection, storage, analysis, and secure retention following GDPR principles.
                    </p>
                </div>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 8px; margin-top: 15px;">
                <h4 style="margin: 0 0 15px 0; color: #c2185b;">📋 Scope and Context</h4>
                <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; width: 30%; background: #fafafa;"><strong>Project/System</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{project_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background: #fafafa;"><strong>Data Subjects</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Employees, customers, or as specified in the assessment</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background: #fafafa;"><strong>Geographic Scope</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Netherlands / EU (GDPR jurisdiction)</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background: #fafafa;"><strong>Duration</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Ongoing processing with defined retention periods</td>
                    </tr>
                </table>
            </div>
        </div>
    """


def _generate_legal_basis_section(scan_results):
    """Generate Legal Basis mapping to GDPR Article 6"""
    purpose = scan_results.get('processing_purpose', '').lower()
    
    # Determine likely legal basis based on purpose
    legal_bases = [
        {
            'article': '6(1)(a) - Consent',
            'description': 'Data subject has given consent for one or more specific purposes',
            'applicable': 'consent' in purpose or 'marketing' in purpose,
            'requirements': 'Freely given, specific, informed, unambiguous; easily withdrawable'
        },
        {
            'article': '6(1)(b) - Contract',
            'description': 'Processing necessary for performance of a contract',
            'applicable': 'contract' in purpose or 'service' in purpose or 'order' in purpose,
            'requirements': 'Contract must exist or be about to be entered into'
        },
        {
            'article': '6(1)(c) - Legal Obligation',
            'description': 'Processing necessary for compliance with legal obligation',
            'applicable': 'legal' in purpose or 'tax' in purpose or 'compliance' in purpose,
            'requirements': 'Must identify specific legal obligation under EU or Member State law'
        },
        {
            'article': '6(1)(d) - Vital Interests',
            'description': 'Processing necessary to protect vital interests',
            'applicable': 'emergency' in purpose or 'health' in purpose or 'safety' in purpose,
            'requirements': 'Life-threatening situation; no other legal basis available'
        },
        {
            'article': '6(1)(e) - Public Task',
            'description': 'Processing necessary for public interest or official authority',
            'applicable': 'public' in purpose or 'government' in purpose,
            'requirements': 'Task carried out in public interest or exercise of official authority'
        },
        {
            'article': '6(1)(f) - Legitimate Interests',
            'description': 'Processing necessary for legitimate interests of controller',
            'applicable': True,  # Default fallback
            'requirements': 'Balance test required; not applicable for public authorities'
        }
    ]
    
    basis_rows = []
    for basis in legal_bases:
        status = '✅' if basis['applicable'] else '⬜'
        bg_color = '#d4edda' if basis['applicable'] else 'white'
        basis_rows.append(f"""
            <tr style="background: {bg_color};">
                <td style="padding: 12px; border: 1px solid #ddd;">{status}</td>
                <td style="padding: 12px; border: 1px solid #ddd;"><strong>{basis['article']}</strong></td>
                <td style="padding: 12px; border: 1px solid #ddd;">{basis['description']}</td>
                <td style="padding: 12px; border: 1px solid #ddd; font-size: 12px;">{basis['requirements']}</td>
            </tr>
        """)
    
    return f"""
        <div style="background: #e0f2f1; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #26a69a;">
            <h2 style="color: #00796b; margin-top: 0;">⚖️ Legal Basis (GDPR Article 6)</h2>
            <p style="color: #555; margin-bottom: 20px;">
                Every processing activity must have a valid legal basis under GDPR Article 6.
                Select and document the applicable basis below.
            </p>
            
            <table style="width: 100%; border-collapse: collapse; background: white; font-size: 13px;">
                <thead>
                    <tr style="background: #00897b; color: white;">
                        <th style="padding: 12px; text-align: center; width: 40px;">Select</th>
                        <th style="padding: 12px; text-align: left;">Legal Basis</th>
                        <th style="padding: 12px; text-align: left;">Description</th>
                        <th style="padding: 12px; text-align: left;">Requirements</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(basis_rows)}
                </tbody>
            </table>
            
            <div style="background: #fff8e1; padding: 15px; border-radius: 6px; margin-top: 20px; border-left: 4px solid #ffc107;">
                <strong>⚠️ Special Categories (Article 9):</strong> If processing sensitive data, an additional legal basis 
                from Article 9(2) is required in addition to Article 6.
            </div>
            
            <p style="font-size: 11px; color: #666; margin-top: 15px;">
                <em>Legal Reference: GDPR Article 6 - Lawfulness of processing</em>
            </p>
        </div>
    """


def _generate_residual_risk_section(scan_results):
    """Generate Residual Risk section showing risk AFTER mitigation"""
    risk_score = min(10, scan_results.get('risk_score', 5))
    
    # Calculate residual risk based on safeguards
    safeguards_count = sum([
        scan_results.get('encryption', False),
        scan_results.get('access_controls', False),
        scan_results.get('data_minimization', False),
        scan_results.get('retention_policy', False),
        scan_results.get('consent_mechanisms', False),
        scan_results.get('breach_procedures', False)
    ])
    
    # Residual risk = original risk - mitigation effect
    mitigation_effect = min(safeguards_count * 0.8, risk_score * 0.6)  # Max 60% reduction
    residual_score = max(1, round(risk_score - mitigation_effect, 1))
    
    # Determine residual risk level
    if residual_score >= 7:
        residual_level = 'High'
        residual_color = '#dc3545'
        residual_bg = '#f8d7da'
        action_required = 'AP consultation may be required before processing'
    elif residual_score >= 4:
        residual_level = 'Medium'
        residual_color = '#fd7e14'
        residual_bg = '#fff3cd'
        action_required = 'Proceed with additional monitoring and review'
    else:
        residual_level = 'Low'
        residual_color = '#28a745'
        residual_bg = '#d4edda'
        action_required = 'Proceed with standard controls'
    
    reduction_pct = round(((risk_score - residual_score) / risk_score) * 100) if risk_score > 0 else 0
    
    return f"""
        <div style="background: {residual_bg}; padding: 25px; border-radius: 8px; margin: 25px 0; border: 2px solid {residual_color};">
            <h2 style="color: {residual_color}; margin-top: 0;">📉 Residual Risk Assessment</h2>
            <p style="color: #555; margin-bottom: 20px;">
                Risk level AFTER applying mitigation measures and safeguards
            </p>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">INITIAL RISK</div>
                    <div style="font-size: 36px; font-weight: bold; color: #dc3545;">{risk_score}/10</div>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">RISK REDUCTION</div>
                    <div style="font-size: 36px; font-weight: bold; color: #28a745;">-{reduction_pct}%</div>
                    <div style="font-size: 11px; color: #666;">{safeguards_count} safeguards applied</div>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; border: 3px solid {residual_color};">
                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">RESIDUAL RISK</div>
                    <div style="font-size: 36px; font-weight: bold; color: {residual_color};">{residual_score}/10</div>
                    <div style="font-size: 14px; font-weight: bold; color: {residual_color};">{residual_level}</div>
                </div>
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 6px; margin-top: 15px;">
                <strong>Required Action:</strong> {action_required}
            </div>
            
            <p style="font-size: 11px; color: #666; margin-top: 15px;">
                <em>Residual risk is calculated after applying documented safeguards. If residual risk remains high, 
                consult Autoriteit Persoonsgegevens (GDPR Article 36).</em>
            </p>
        </div>
    """


def _generate_data_subject_rights_section(scan_results):
    """Generate Data Subject Rights section - how rights will be honored"""
    return """
        <div style="background: #e1f5fe; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #03a9f4;">
            <h2 style="color: #0277bd; margin-top: 0;">👤 Data Subject Rights</h2>
            <p style="color: #555; margin-bottom: 20px;">
                How data subject rights under GDPR Chapter III will be honored
            </p>
            
            <table style="width: 100%; border-collapse: collapse; background: white; font-size: 13px;">
                <thead>
                    <tr style="background: #0288d1; color: white;">
                        <th style="padding: 12px; text-align: left;">Right</th>
                        <th style="padding: 12px; text-align: left;">GDPR Article</th>
                        <th style="padding: 12px; text-align: left;">How Fulfilled</th>
                        <th style="padding: 12px; text-align: center;">Response Time</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Right of Access</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Article 15</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Data export functionality / manual request process</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">30 days</td>
                    </tr>
                    <tr style="background: #fafafa;">
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Right to Rectification</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Article 16</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">User profile editing / support request</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">30 days</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Right to Erasure</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Article 17</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Account deletion / data removal process</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">30 days</td>
                    </tr>
                    <tr style="background: #fafafa;">
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Right to Restrict Processing</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Article 18</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Processing suspension mechanism</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">30 days</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Right to Data Portability</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Article 20</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Machine-readable export (JSON/CSV)</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">30 days</td>
                    </tr>
                    <tr style="background: #fafafa;">
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Right to Object</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Article 21</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Opt-out mechanisms / objection handling</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">Immediately</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Automated Decision-Making</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Article 22</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">Human review option / explanation provided</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">30 days</td>
                    </tr>
                </tbody>
            </table>
            
            <div style="background: white; padding: 15px; border-radius: 6px; margin-top: 20px;">
                <h4 style="margin: 0 0 10px 0; color: #0277bd;">📧 Contact for Rights Requests</h4>
                <p style="margin: 0; font-size: 13px;">
                    Data subjects can exercise their rights by contacting: <br/>
                    <strong>Email:</strong> privacy@[organization].nl | 
                    <strong>Response deadline:</strong> Within 30 days (extendable by 60 days for complex requests)
                </p>
            </div>
            
            <p style="font-size: 11px; color: #666; margin-top: 15px;">
                <em>Legal Reference: GDPR Chapter III - Rights of the Data Subject (Articles 12-23)</em>
            </p>
        </div>
    """


def _generate_review_schedule_section(scan_results):
    """Generate Review Schedule section with specific dates"""
    from datetime import timedelta
    
    today = datetime.now()
    review_dates = {
        'initial': today.strftime('%B %d, %Y'),
        'quarterly_1': (today + timedelta(days=90)).strftime('%B %d, %Y'),
        'quarterly_2': (today + timedelta(days=180)).strftime('%B %d, %Y'),
        'quarterly_3': (today + timedelta(days=270)).strftime('%B %d, %Y'),
        'annual': (today + timedelta(days=365)).strftime('%B %d, %Y'),
    }
    
    risk_level = scan_results.get('risk_level', 'Medium').split(' - ')[0].lower()
    review_frequency = 'Quarterly' if 'high' in risk_level else 'Bi-annually' if 'medium' in risk_level else 'Annually'
    
    return f"""
        <div style="background: #fff3e0; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #ff9800;">
            <h2 style="color: #e65100; margin-top: 0;">📆 Review Schedule</h2>
            <p style="color: #555; margin-bottom: 20px;">
                DPIA must be reviewed regularly and when significant changes occur (GDPR Article 35(11))
            </p>
            
            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div>
                        <strong style="color: #e65100;">Recommended Review Frequency:</strong>
                        <span style="background: #ff9800; color: white; padding: 4px 12px; border-radius: 15px; margin-left: 10px;">{review_frequency}</span>
                    </div>
                    <div style="font-size: 12px; color: #666;">Based on risk level: {risk_level.title()}</div>
                </div>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; background: white; font-size: 13px;">
                <thead>
                    <tr style="background: #f57c00; color: white;">
                        <th style="padding: 12px; text-align: left;">Review Type</th>
                        <th style="padding: 12px; text-align: left;">Scheduled Date</th>
                        <th style="padding: 12px; text-align: center;">Status</th>
                        <th style="padding: 12px; text-align: left;">Reviewer</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="background: #d4edda;">
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Initial Assessment</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{review_dates['initial']}</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">✅ Complete</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">_________________</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Q1 Review</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{review_dates['quarterly_1']}</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">⬜ Pending</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">_________________</td>
                    </tr>
                    <tr style="background: #fafafa;">
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Q2 Review</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{review_dates['quarterly_2']}</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">⬜ Pending</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">_________________</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Q3 Review</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{review_dates['quarterly_3']}</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">⬜ Pending</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">_________________</td>
                    </tr>
                    <tr style="background: #fff3cd;">
                        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Annual Review</strong></td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{review_dates['annual']}</td>
                        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">⬜ Pending</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">_________________</td>
                    </tr>
                </tbody>
            </table>
            
            <div style="background: white; padding: 15px; border-radius: 6px; margin-top: 20px;">
                <h4 style="margin: 0 0 10px 0; color: #e65100;">⚠️ Trigger Events Requiring Immediate Review</h4>
                <ul style="margin: 0; padding-left: 20px; font-size: 13px;">
                    <li>Significant changes to processing operations</li>
                    <li>New data types or categories collected</li>
                    <li>Changes in technology or systems</li>
                    <li>Data breach or security incident</li>
                    <li>Regulatory guidance updates</li>
                    <li>Complaints from data subjects</li>
                </ul>
            </div>
            
            <p style="font-size: 11px; color: #666; margin-top: 15px;">
                <em>Legal Reference: GDPR Article 35(11) - Review obligation when risks change</em>
            </p>
        </div>
    """


def generate_enhanced_dpia_report(scan_results):
    """Generate professional HTML report for DPIA assessment"""
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DPIA Assessment Report - {scan_results['project_name']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .header {{ background: #f8f9fa; padding: 30px; border-radius: 12px; margin-bottom: 30px; }}
            .header h1 {{ color: #2c3e50; margin: 0; }}
            .risk-high {{ color: #dc3545; font-weight: bold; }}
            .risk-medium {{ color: #fd7e14; font-weight: bold; }}
            .risk-low {{ color: #28a745; font-weight: bold; }}
            .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
            .metric {{ background: #e9ecef; padding: 20px; border-radius: 8px; text-align: center; }}
            .metric h3 {{ margin: 0; color: #495057; }}
            .metric .value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .recommendation {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-left: 4px solid #007bff; border-radius: 8px; }}
            .recommendation h4 {{ margin: 0 0 10px 0; color: #2c3e50; }}
            .finding {{ margin: 15px 0; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 8px; }}
            .footer {{ margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px; font-size: 12px; color: #6c757d; }}
            .next-steps {{ background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .compliance-status {{ padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; }}
            .compliant {{ background: #d4edda; color: #155724; }}
            .requires-action {{ background: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Data Protection Impact Assessment Report</h1>
            <p><strong>Project:</strong> {scan_results['project_name']}</p>
            <p><strong>Data Controller:</strong> {scan_results['data_controller']}</p>
            <p><strong>Assessment Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            <p><strong>Region:</strong> {scan_results['region']}</p>
        </div>
        
        <div class="compliance-status {'compliant' if scan_results['compliance_status'] == 'Compliant' else 'requires-action'}">
            Compliance Status: {scan_results['compliance_status']}
        </div>
        
        <div class="metrics">
            <div class="metric">
                <h3>Risk Score</h3>
                <div class="value">{min(10, scan_results['risk_score'])}/10</div>
            </div>
            <div class="metric">
                <h3>Risk Level</h3>
                <div class="value risk-{scan_results['risk_level'].split(' - ')[0].lower()}">{scan_results['risk_level'].split(' - ')[0]}</div>
            </div>
            <div class="metric">
                <h3>Risk Factors</h3>
                <div class="value">{len(scan_results['risk_factors'])}</div>
            </div>
            <div class="metric">
                <h3>Recommendations</h3>
                <div class="value">{len(scan_results['recommendations'])}</div>
            </div>
        </div>
        
        <h2>Risk Assessment Summary</h2>
        <p class="risk-{scan_results['risk_level'].split(' - ')[0].lower()}">
            <strong>Risk Level:</strong> {scan_results['risk_level']}
        </p>
        
        <h3>Risk Factors Identified:</h3>
        <ul>
            {''.join(f'<li>{factor}</li>' for factor in scan_results['risk_factors'])}
        </ul>
        
        <h2>Key Recommendations</h2>
        {''.join(f'''
        <div class="recommendation">
            <h4>{rec['title']} ({rec['priority']} Priority)</h4>
            <p>{rec['description']}</p>
            <p><strong>Timeline:</strong> {rec['timeline']}</p>
        </div>
        ''' for rec in scan_results['recommendations'])}
        
        {_generate_data_flow_diagram(scan_results)}
        
        {_generate_processing_description(scan_results)}
        
        {_generate_legal_basis_section(scan_results)}
        
        <h2>Detailed Findings</h2>
        {''.join(f'''
        <div class="finding">
            <h4>{finding['type']} - {finding['severity']} Severity</h4>
            <p><strong>Description:</strong> {finding['description']}</p>
            <p><strong>Recommendation:</strong> {finding['recommendation']}</p>
            <p><strong>Legal Reference:</strong> {finding['gdpr_article']}</p>
        </div>
        ''' for finding in scan_results['findings'])}
        
        {_generate_residual_risk_section(scan_results)}
        
        {_generate_data_subject_rights_section(scan_results)}
        
        {_generate_ap_consultation_section(scan_results)}
        
        {_generate_netherlands_specific_section(scan_results)}
        
        {_generate_implementation_timeline(scan_results)}
        
        {_generate_stakeholder_signoff_section(scan_results)}
        
        {_generate_dpo_signoff_section(scan_results)}
        
        {_generate_review_schedule_section(scan_results)}
        
        <div class="next-steps">
            <h2>Next Steps</h2>
            <ol>
                <li>Review and address all high-priority recommendations</li>
                <li>Implement necessary safeguards and controls</li>
                <li>Document compliance measures</li>
                <li>Obtain required stakeholder sign-offs</li>
                <li>Consult Autoriteit Persoonsgegevens if residual risk remains high</li>
                <li>Schedule regular review (recommended: 12 months)</li>
                <li>Monitor for changes in processing activities</li>
            </ol>
        </div>
        
        <div class="footer">
            <p><strong>Generated by DataGuardian Pro</strong></p>
            <p>Netherlands GDPR & UAVG Compliance • Report ID: {scan_results['scan_id']}</p>
            <p>This report is generated based on the information provided and should be reviewed by qualified legal counsel.</p>
            <p><em>References: GDPR Art. 35, UAVG Art. 1-51, AP Guidelines 2024-2025</em></p>
        </div>
    </body>
    </html>
    """
    
    return html_template



