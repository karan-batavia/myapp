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
        if st.button("Next Step →", type="primary", use_container_width=True):
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
        if st.button("← Previous", use_container_width=True):
            st.session_state.dpia_step = 1
            st.rerun()
    with col2:
        if st.button("Next Step →", type="primary", use_container_width=True):
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
        if st.button("← Previous", use_container_width=True):
            st.session_state.dpia_step = 2
            st.rerun()
    with col2:
        if st.button("Next Step →", type="primary", use_container_width=True):
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
        if st.button("← Previous", use_container_width=True):
            st.session_state.dpia_step = 3
            st.rerun()
    with col2:
        if st.button("Next Step →", type="primary", use_container_width=True):
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
        if st.button("← Previous", use_container_width=True):
            st.session_state.dpia_step = 4
            st.rerun()
    with col2:
        if st.button("🚀 Generate DPIA Report", type="primary", use_container_width=True):
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
        st.metric("Risk Score", f"{scan_results['risk_score']}/10")
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
    
    # Generate enhanced HTML report
    html_report = generate_enhanced_dpia_report(scan_results)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download DPIA Report (HTML)",
            data=html_report,
            file_name=f"dpia-report-{scan_results['scan_id']}.html",
            mime="text/html",
            use_container_width=True
        )
    
    with col2:
        # JSON report for technical users
        json_report = json.dumps(scan_results, indent=2, default=str)
        st.download_button(
            label="📊 Download Assessment Data (JSON)",
            data=json_report,
            file_name=f"dpia-data-{scan_results['scan_id']}.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Success message
    st.success("✅ Enhanced DPIA assessment completed successfully!")

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
                <div class="value">{scan_results['risk_score']}/10</div>
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
        
        <h2>Detailed Findings</h2>
        {''.join(f'''
        <div class="finding">
            <h4>{finding['type']} - {finding['severity']} Severity</h4>
            <p><strong>Description:</strong> {finding['description']}</p>
            <p><strong>Recommendation:</strong> {finding['recommendation']}</p>
            <p><strong>Legal Reference:</strong> {finding['gdpr_article']}</p>
        </div>
        ''' for finding in scan_results['findings'])}
        
        <div class="next-steps">
            <h2>Next Steps</h2>
            <ol>
                <li>Review and address all high-priority recommendations</li>
                <li>Implement necessary safeguards and controls</li>
                <li>Document compliance measures</li>
                <li>Schedule regular review (recommended: 12 months)</li>
                <li>Monitor for changes in processing activities</li>
            </ol>
        </div>
        
        <div class="footer">
            <p><strong>Generated by DataGuardian Pro</strong></p>
            <p>Netherlands GDPR Compliance • Report ID: {scan_results['scan_id']}</p>
            <p>This report is generated based on the information provided and should be reviewed by qualified legal counsel.</p>
        </div>
    </body>
    </html>
    """
    
    return html_template



