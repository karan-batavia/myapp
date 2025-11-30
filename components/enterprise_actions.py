"""
Enterprise Actions Component

Provides contextual enterprise actions for scan results and compliance findings.
Generates downloadable DSAR requests, compliance reports, and evidence exports.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import base64
import io

try:
    from utils.event_bus import EventType, publish_event
    ENTERPRISE_EVENTS_AVAILABLE = True
except ImportError:
    ENTERPRISE_EVENTS_AVAILABLE = False

def show_enterprise_actions(scan_result: Dict[str, Any], scan_type: str = "code", 
                          username: str = "unknown"):
    """
    Display contextual enterprise actions based on scan results.
    
    Args:
        scan_result: The scan result data
        scan_type: Type of scan performed
        username: Current user
    """
    session_id = st.session_state.get('session_id', 'unknown')
    user_id = st.session_state.get('user_id', username)
    
    findings = scan_result.get('findings', [])
    high_risk_findings = [f for f in findings if f.get('risk_level') in ['Critical', 'High'] or f.get('severity') in ['Critical', 'High']]
    pii_findings = [f for f in findings if 'pii' in str(f).lower() or 'personal' in str(f).lower() or f.get('pii_found')]
    
    with st.expander("🔧 Enterprise Actions", expanded=False):
        st.markdown("**Compliance & Risk Management Actions**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Create DSAR", help="Create Data Subject Access Request document", 
                       key=f"dsar_action_{scan_result.get('scan_id', 'unknown')}"):
                _generate_dsar_document(scan_result, pii_findings, username)
        
        with col2:
            if st.button("📋 Generate Report", help="Generate compliance report",
                        key=f"report_action_{scan_result.get('scan_id', 'unknown')}"):
                _generate_compliance_report(scan_result, scan_type, username)
        
        with col3:
            if st.button("📊 Export Evidence", help="Export compliance evidence for audit purposes",
                        key=f"evidence_action_{scan_result.get('scan_id', 'unknown')}"):
                _generate_evidence_export(scan_result, scan_type, username)


def _generate_dsar_document(scan_result: Dict[str, Any], pii_findings: List[Dict], username: str):
    """Generate and download a DSAR document"""
    try:
        scan_id = scan_result.get('scan_id', f'SCAN-{datetime.now().strftime("%Y%m%d%H%M%S")}')
        timestamp = datetime.now()
        
        pii_types = set()
        for finding in pii_findings:
            if finding.get('pii_found'):
                for pii in finding.get('pii_found', []):
                    pii_types.add(pii.get('type', 'Personal Information'))
            if finding.get('pii_type'):
                pii_types.add(finding.get('pii_type'))
        
        pii_types = list(pii_types) if pii_types else ['Personal Information detected']
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DSAR Request - {scan_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; line-height: 1.6; color: #333; }}
        .header {{ background: linear-gradient(135deg, #1e3a5f, #2d5a87); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header .subtitle {{ opacity: 0.9; margin-top: 5px; }}
        .section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #1e3a5f; }}
        .section h2 {{ color: #1e3a5f; margin-top: 0; font-size: 18px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #1e3a5f; color: white; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
        .status-pending {{ background: #fff3cd; color: #856404; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #ddd; text-align: center; color: #666; }}
        .gdpr-badge {{ background: #28a745; color: white; padding: 8px 16px; border-radius: 5px; display: inline-block; }}
        ul {{ margin: 10px 0; padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 Data Subject Access Request (DSAR)</h1>
        <div class="subtitle">GDPR Article 15 - Right of Access Request</div>
    </div>
    
    <div class="section">
        <h2>Request Information</h2>
        <table>
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td>DSAR Reference</td><td><strong>DSAR-{timestamp.strftime('%Y%m%d')}-{scan_id[:8].upper()}</strong></td></tr>
            <tr><td>Request Date</td><td>{timestamp.strftime('%d %B %Y, %H:%M')}</td></tr>
            <tr><td>Generated By</td><td>{username}</td></tr>
            <tr><td>Source Scan ID</td><td>{scan_id}</td></tr>
            <tr><td>Status</td><td><span class="status status-pending">Pending Review</span></td></tr>
            <tr><td>Response Deadline</td><td>{(timestamp.replace(day=timestamp.day) + __import__('datetime').timedelta(days=30)).strftime('%d %B %Y')} (30 days per GDPR)</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Personal Data Categories Identified</h2>
        <p>The following categories of personal data were identified during the compliance scan:</p>
        <ul>
            {''.join(f'<li>{pii_type}</li>' for pii_type in pii_types)}
        </ul>
        <p><strong>Total PII Findings:</strong> {len(pii_findings)} instances detected</p>
    </div>
    
    <div class="section">
        <h2>GDPR Rights Applicable</h2>
        <table>
            <tr><th>Right</th><th>Article</th><th>Description</th></tr>
            <tr><td>Right of Access</td><td>Art. 15</td><td>Obtain confirmation of processing and access to data</td></tr>
            <tr><td>Right to Rectification</td><td>Art. 16</td><td>Request correction of inaccurate data</td></tr>
            <tr><td>Right to Erasure</td><td>Art. 17</td><td>Request deletion of personal data</td></tr>
            <tr><td>Right to Portability</td><td>Art. 20</td><td>Receive data in machine-readable format</td></tr>
            <tr><td>Right to Object</td><td>Art. 21</td><td>Object to processing of personal data</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Required Actions</h2>
        <ol>
            <li><strong>Verify Identity:</strong> Confirm the identity of the data subject before processing this request</li>
            <li><strong>Locate Data:</strong> Search all systems for data related to this subject based on scan findings</li>
            <li><strong>Compile Response:</strong> Prepare complete data export within 30 days</li>
            <li><strong>Document:</strong> Record all actions taken for compliance evidence</li>
            <li><strong>Respond:</strong> Provide data subject with requested information</li>
        </ol>
    </div>
    
    <div class="section">
        <h2>Netherlands UAVG Compliance</h2>
        <p>This DSAR request is subject to the Uitvoeringswet Algemene Verordening Gegevensbescherming (UAVG), the Dutch implementation of GDPR.</p>
        <p><strong>Special considerations for BSN (Burgerservicenummer):</strong> Processing of BSN is only permitted when required by law (Art. 46 UAVG).</p>
        <span class="gdpr-badge">🇳🇱 UAVG Compliant</span>
    </div>
    
    <div class="footer">
        <p><strong>DataGuardian Pro</strong> - Enterprise Privacy Compliance Platform</p>
        <p>Generated: {timestamp.strftime('%d %B %Y at %H:%M:%S')}</p>
        <p>This document should be retained for 7 years per GDPR Article 5(2) accountability requirements.</p>
    </div>
</body>
</html>"""
        
        b64 = base64.b64encode(html_content.encode()).decode()
        filename = f"DSAR_Request_{timestamp.strftime('%Y%m%d_%H%M%S')}.html"
        
        st.success("✅ DSAR document generated successfully!")
        st.markdown(
            f'<a href="data:text/html;base64,{b64}" download="{filename}" '
            f'style="display: inline-block; padding: 10px 20px; background: #1e3a5f; color: white; '
            f'text-decoration: none; border-radius: 5px; font-weight: bold;">📥 Download DSAR Document</a>',
            unsafe_allow_html=True
        )
        
        if ENTERPRISE_EVENTS_AVAILABLE:
            publish_event(
                event_type=EventType.DSAR_REQUEST_SUBMITTED,
                source="enterprise_actions",
                user_id=st.session_state.get('user_id', 'unknown'),
                session_id=st.session_state.get('session_id', 'unknown'),
                data={
                    'source_scan_id': scan_id,
                    'pii_findings_count': len(pii_findings),
                    'pii_types': list(pii_types),
                    'timestamp': timestamp.isoformat()
                }
            )
        
    except Exception as e:
        st.error(f"Failed to generate DSAR document: {str(e)}")


def _generate_compliance_report(scan_result: Dict[str, Any], scan_type: str, username: str):
    """Generate and download a compliance report"""
    try:
        scan_id = scan_result.get('scan_id', f'SCAN-{datetime.now().strftime("%Y%m%d%H%M%S")}')
        timestamp = datetime.now()
        
        total_findings = scan_result.get('total_findings', len(scan_result.get('findings', [])))
        high_risk = scan_result.get('high_risk_findings', 0)
        medium_risk = scan_result.get('medium_risk_findings', 0)
        low_risk = scan_result.get('low_risk_findings', total_findings - high_risk - medium_risk if total_findings > 0 else 0)
        compliance_score = scan_result.get('compliance_score', 85)
        
        findings_html = ""
        for i, finding in enumerate(scan_result.get('findings', [])[:20], 1):
            risk = finding.get('risk_level', finding.get('severity', 'Medium'))
            risk_color = '#dc3545' if risk in ['Critical', 'High'] else ('#ffc107' if risk == 'Medium' else '#28a745')
            source = finding.get('source', finding.get('location', 'Unknown'))
            
            pii_types = []
            if finding.get('pii_found'):
                pii_types = [p.get('type', 'PII') for p in finding.get('pii_found', [])]
            
            findings_html += f"""
            <tr>
                <td>{i}</td>
                <td>{source[:50]}...</td>
                <td>{'<br>'.join(pii_types[:3]) if pii_types else 'PII Detected'}</td>
                <td style="color: {risk_color}; font-weight: bold;">{risk}</td>
            </tr>"""
        
        score_color = '#28a745' if compliance_score >= 80 else ('#ffc107' if compliance_score >= 60 else '#dc3545')
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance Report - {scan_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; line-height: 1.6; color: #333; }}
        .header {{ background: linear-gradient(135deg, #1e3a5f, #2d5a87); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 32px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: #f8f9fa; padding: 25px; border-radius: 10px; text-align: center; border-top: 4px solid #1e3a5f; }}
        .metric-value {{ font-size: 36px; font-weight: bold; color: #1e3a5f; }}
        .metric-label {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .section {{ background: #fff; padding: 25px; border-radius: 10px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #1e3a5f; margin-top: 0; border-bottom: 2px solid #1e3a5f; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #1e3a5f; color: white; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        .score-badge {{ display: inline-block; padding: 15px 30px; border-radius: 10px; font-size: 24px; font-weight: bold; color: white; background: {score_color}; }}
        .risk-high {{ color: #dc3545; }}
        .risk-medium {{ color: #ffc107; }}
        .risk-low {{ color: #28a745; }}
        .footer {{ margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 10px; text-align: center; }}
        .recommendation {{ background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #0066cc; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 GDPR Compliance Report</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">Scan ID: {scan_id} | Generated: {timestamp.strftime('%d %B %Y, %H:%M')}</p>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <div class="metric-value" style="color: {score_color};">{compliance_score}%</div>
            <div class="metric-label">Compliance Score</div>
        </div>
        <div class="metric">
            <div class="metric-value">{total_findings}</div>
            <div class="metric-label">Total Findings</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color: #dc3545;">{high_risk}</div>
            <div class="metric-label">High Risk</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color: #ffc107;">{medium_risk}</div>
            <div class="metric-label">Medium Risk</div>
        </div>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <p>This compliance report summarizes the results of a <strong>{scan_type.upper()}</strong> scan performed on {timestamp.strftime('%d %B %Y')} by <strong>{username}</strong>.</p>
        <p>The scan identified <strong>{total_findings} data exposure findings</strong> requiring attention for GDPR compliance.</p>
        <div style="text-align: center; margin: 20px 0;">
            <span class="score-badge">Compliance Score: {compliance_score}%</span>
        </div>
    </div>
    
    <div class="section">
        <h2>Risk Distribution</h2>
        <table>
            <tr><th>Risk Level</th><th>Count</th><th>Percentage</th><th>Action Required</th></tr>
            <tr><td class="risk-high">🔴 High/Critical</td><td>{high_risk}</td><td>{(high_risk/max(total_findings,1)*100):.1f}%</td><td>Immediate remediation required</td></tr>
            <tr><td class="risk-medium">🟡 Medium</td><td>{medium_risk}</td><td>{(medium_risk/max(total_findings,1)*100):.1f}%</td><td>Review within 30 days</td></tr>
            <tr><td class="risk-low">🟢 Low</td><td>{low_risk}</td><td>{(low_risk/max(total_findings,1)*100):.1f}%</td><td>Monitor and document</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Detailed Findings</h2>
        <table>
            <tr><th>#</th><th>Location</th><th>Data Type</th><th>Risk Level</th></tr>
            {findings_html if findings_html else '<tr><td colspan="4">No detailed findings available</td></tr>'}
        </table>
        {f'<p style="color: #666; font-style: italic;">Showing first 20 of {total_findings} findings</p>' if total_findings > 20 else ''}
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        <div class="recommendation">
            <strong>🔴 Priority 1:</strong> Address all high-risk findings immediately to prevent potential data breaches
        </div>
        <div class="recommendation">
            <strong>🟡 Priority 2:</strong> Implement data minimization practices for medium-risk findings
        </div>
        <div class="recommendation">
            <strong>🟢 Priority 3:</strong> Document and monitor low-risk findings as part of ongoing compliance
        </div>
        <div class="recommendation">
            <strong>📋 Ongoing:</strong> Schedule regular scans to maintain GDPR compliance posture
        </div>
    </div>
    
    <div class="section">
        <h2>Netherlands UAVG Requirements</h2>
        <p>As a Dutch entity, the following UAVG-specific requirements apply:</p>
        <ul>
            <li><strong>BSN Processing (Art. 46):</strong> BSN may only be processed when specifically required by law</li>
            <li><strong>AP Notification:</strong> Data breaches must be reported to Autoriteit Persoonsgegevens within 72 hours</li>
            <li><strong>Record Keeping:</strong> Maintain processing records as per Art. 30 GDPR</li>
        </ul>
    </div>
    
    <div class="footer">
        <p><strong>DataGuardian Pro</strong> - Enterprise Privacy Compliance Platform</p>
        <p>Report generated: {timestamp.strftime('%d %B %Y at %H:%M:%S')}</p>
        <p style="color: #666;">This report should be retained as compliance evidence per GDPR Article 5(2)</p>
    </div>
</body>
</html>"""
        
        b64 = base64.b64encode(html_content.encode()).decode()
        filename = f"Compliance_Report_{timestamp.strftime('%Y%m%d_%H%M%S')}.html"
        
        st.success("✅ Compliance report generated successfully!")
        st.markdown(
            f'<a href="data:text/html;base64,{b64}" download="{filename}" '
            f'style="display: inline-block; padding: 10px 20px; background: #28a745; color: white; '
            f'text-decoration: none; border-radius: 5px; font-weight: bold;">📥 Download Compliance Report</a>',
            unsafe_allow_html=True
        )
        
        if ENTERPRISE_EVENTS_AVAILABLE:
            publish_event(
                event_type=EventType.COMPLIANCE_EVIDENCE_ADDED,
                source="enterprise_actions",
                user_id=st.session_state.get('user_id', 'unknown'),
                session_id=st.session_state.get('session_id', 'unknown'),
                data={
                    'report_type': 'compliance_summary',
                    'source_scan_id': scan_id,
                    'timestamp': timestamp.isoformat()
                }
            )
        
    except Exception as e:
        st.error(f"Failed to generate compliance report: {str(e)}")


def _generate_evidence_export(scan_result: Dict[str, Any], scan_type: str, username: str):
    """Generate and download compliance evidence package"""
    try:
        scan_id = scan_result.get('scan_id', f'SCAN-{datetime.now().strftime("%Y%m%d%H%M%S")}')
        timestamp = datetime.now()
        
        evidence_data = {
            'evidence_package': {
                'package_id': f'EVD-{timestamp.strftime("%Y%m%d")}-{scan_id[:8].upper()}',
                'generated_at': timestamp.isoformat(),
                'generated_by': username,
                'retention_period': '7 years (per GDPR Art. 5(2))',
                'classification': 'Internal - Compliance Evidence'
            },
            'scan_metadata': {
                'scan_id': scan_id,
                'scan_type': scan_type,
                'scan_date': scan_result.get('timestamp', timestamp.isoformat()),
                'region': scan_result.get('region', 'Netherlands'),
                'compliance_framework': 'GDPR / UAVG'
            },
            'compliance_metrics': {
                'total_items_scanned': scan_result.get('files_scanned', scan_result.get('total_items_scanned', 0)),
                'total_findings': scan_result.get('total_findings', len(scan_result.get('findings', []))),
                'high_risk_count': scan_result.get('high_risk_findings', 0),
                'medium_risk_count': scan_result.get('medium_risk_findings', 0),
                'low_risk_count': scan_result.get('low_risk_findings', 0),
                'compliance_score': scan_result.get('compliance_score', 0)
            },
            'netherlands_specific': {
                'bsn_instances': scan_result.get('bsn_fields_found', 0),
                'kvk_numbers': scan_result.get('kvk_fields_found', 0),
                'iban_fields': scan_result.get('iban_fields_found', 0),
                'uavg_applicable': True
            },
            'findings_summary': [],
            'audit_trail': {
                'action': 'evidence_export',
                'performed_by': username,
                'timestamp': timestamp.isoformat(),
                'ip_address': 'Logged separately for security',
                'session_id': st.session_state.get('session_id', 'unknown')
            }
        }
        
        for finding in scan_result.get('findings', [])[:50]:
            evidence_data['findings_summary'].append({
                'source': finding.get('source', finding.get('location', 'Unknown')),
                'risk_level': finding.get('risk_level', finding.get('severity', 'Medium')),
                'data_types': [p.get('type', 'PII') for p in finding.get('pii_found', [])] if finding.get('pii_found') else ['Personal Data'],
                'netherlands_specific': finding.get('netherlands_specific', False)
            })
        
        json_content = json.dumps(evidence_data, indent=2, default=str)
        b64 = base64.b64encode(json_content.encode()).decode()
        filename = f"Evidence_Package_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        st.success("✅ Evidence package generated successfully!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'<a href="data:application/json;base64,{b64}" download="{filename}" '
                f'style="display: inline-block; padding: 10px 20px; background: #6c757d; color: white; '
                f'text-decoration: none; border-radius: 5px; font-weight: bold;">📥 Download Evidence (JSON)</a>',
                unsafe_allow_html=True
            )
        
        with col2:
            st.info(f"📁 Package ID: {evidence_data['evidence_package']['package_id']}")
        
        with st.expander("Preview Evidence Data"):
            st.json(evidence_data)
        
        if ENTERPRISE_EVENTS_AVAILABLE:
            publish_event(
                event_type=EventType.COMPLIANCE_EVIDENCE_ADDED,
                source="enterprise_actions",
                user_id=st.session_state.get('user_id', 'unknown'),
                session_id=st.session_state.get('session_id', 'unknown'),
                data={
                    'evidence_type': 'scan_result',
                    'package_id': evidence_data['evidence_package']['package_id'],
                    'source_scan_id': scan_id,
                    'timestamp': timestamp.isoformat()
                }
            )
        
    except Exception as e:
        st.error(f"Failed to generate evidence package: {str(e)}")


def show_quick_enterprise_sidebar():
    """Show quick enterprise actions in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("**🏢 Enterprise Quick Actions**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 New DSAR", key="quick_dsar", help="Create new DSAR request"):
                st.session_state['show_quick_dsar'] = True
        
        with col2:
            if st.button("🎫 New Ticket", key="quick_ticket", help="Create new ticket"):
                st.session_state['show_quick_ticket'] = True
        
        if st.session_state.get('show_quick_dsar'):
            _show_quick_dsar_form()
        
        if st.session_state.get('show_quick_ticket'):
            _show_quick_ticket_form()


def _show_quick_dsar_form():
    """Show quick DSAR creation form"""
    with st.form("quick_dsar_form"):
        st.markdown("**Quick DSAR Request**")
        email = st.text_input("Requester Email")
        request_type = st.selectbox("Request Type", 
                                   ["access", "rectification", "erasure", "portability"])
        details = st.text_area("Request Details")
        
        if st.form_submit_button("Submit DSAR"):
            if email and details:
                st.success("DSAR request submitted successfully!")
                st.session_state['show_quick_dsar'] = False
                st.rerun()
            else:
                st.error("Please fill in all required fields")


def _show_quick_ticket_form():
    """Show quick ticket creation form"""
    with st.form("quick_ticket_form"):
        st.markdown("**Quick Ticket Creation**")
        title = st.text_input("Ticket Title")
        ticket_type = st.selectbox("Type", 
                                  ["compliance_issue", "security_finding", "privacy_violation"])
        priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])
        description = st.text_area("Description")
        
        if st.form_submit_button("Create Ticket"):
            if title and description:
                st.success("Ticket created successfully!")
                st.session_state['show_quick_ticket'] = False
                st.rerun()
            else:
                st.error("Please fill in all required fields")
