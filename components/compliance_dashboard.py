"""
Compliance Dashboard Component

This module provides the real-time compliance score visualization and tracking
for the DataGuardian Pro dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from services.compliance_score import ComplianceScoreManager
from services.compliance_coverage_analyzer import coverage_analyzer
from utils.i18n import get_text

# Enterprise integration - non-breaking import
try:
    from utils.event_bus import EventType, publish_event
    ENTERPRISE_EVENTS_AVAILABLE = True
except ImportError:
    ENTERPRISE_EVENTS_AVAILABLE = False
    # Define dummy functions to prevent unbound variable errors
    EventType = None
    publish_event = None

def render_compliance_dashboard(current_username: Optional[str] = None):
    """
    Render the compliance score dashboard with interactive visualizations.
    
    Args:
        current_username: Optional username to filter results by
    """
    # Initialize compliance score manager
    manager = ComplianceScoreManager()
    
    # Update score with latest data
    current_score = manager.update_score()
    
    # Get trend information
    trend = manager.get_score_trend(days=30)
    
    # Get badge data
    badge = manager.get_score_badge(current_score["overall_score"])
    
    # Create dashboard layout
    st.subheader("Compliance Score Dashboard")
    
    # Publish compliance dashboard viewed event
    if ENTERPRISE_EVENTS_AVAILABLE and publish_event and EventType:
        try:
            publish_event(
                event_type=EventType.CONNECTOR_EVENT,
                source="compliance_dashboard",
                user_id=current_username or "unknown",
                session_id=st.session_state.get('session_id', 'unknown'),
                data={
                    'event': 'dashboard_viewed',
                    'compliance_score': current_score["overall_score"],
                    'timestamp': datetime.now().isoformat()
                }
            )
        except Exception:
            pass  # Silently continue if event publishing fails
    
    # Main score display with badge
    st.markdown(f"""
    <div style="background-color: white; border-radius: 10px; padding: 20px; margin-bottom: 20px;
               box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: relative;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; color: #333;">Current Compliance Score</h3>
                <div style="display: flex; align-items: baseline; margin-top: 5px;">
                    <span style="font-size: 42px; font-weight: bold; color: {badge['color']};">
                        {current_score["overall_score"]}
                    </span>
                    <span style="font-size: 16px; color: #666; margin-left: 5px;">/100</span>
                </div>
                <div style="margin-top: 10px;">
                    <span style="font-weight: 500; color: {badge['color']};">{badge['level']}</span>
                    <span style="color: #666; font-size: 14px; display: block; margin-top: 3px;">
                        {badge['description']}
                    </span>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 16px; font-weight: 500; margin-bottom: 5px;">30-Day Trend</div>
                <div style="display: flex; align-items: center; justify-content: flex-end;">
                    <span style="font-size: 24px; color: {
                        '#4CAF50' if trend['direction'] == 'improving' else 
                        '#F44336' if trend['direction'] == 'declining' else 
                        '#9E9E9E'
                    };">
                        {
                            '↑' if trend['direction'] == 'improving' else 
                            '↓' if trend['direction'] == 'declining' else 
                            '→'
                        }
                    </span>
                    <span style="margin-left: 5px; font-weight: 500; color: {
                        '#4CAF50' if trend['direction'] == 'improving' else 
                        '#F44336' if trend['direction'] == 'declining' else 
                        '#9E9E9E'
                    };">
                        {f"{abs(trend['percentage_change'])}%" if trend['direction'] != 'stable' else 'Stable'}
                    </span>
                </div>
                <div style="color: #666; font-size: 14px; margin-top: 3px;">
                    {f"{'Increased' if trend['score_change'] > 0 else 'Decreased'} by {abs(trend['score_change'])} points" 
                     if trend['direction'] != 'stable' else 'No significant change'}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced dashboard with regulatory coverage
    st.markdown("---")
    
    # Regulatory Coverage Overview 
    _render_regulatory_coverage_overview()
    
    # Create two-column layout for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Timeline chart
        st.write("#### Compliance Score Timeline")
        timeline_chart = manager.create_score_timeline_chart(days=90)
        st.plotly_chart(timeline_chart, width="stretch")
    
    with col2:
        # Component radar chart
        st.write("#### Component Analysis")
        radar_chart = manager.create_component_radar_chart()
        st.plotly_chart(radar_chart, width="stretch")
    
    # Enhanced regulatory compliance section
    _render_enhanced_regulatory_section()
    
    # Add compliance recommendations based on component scores
    _render_compliance_recommendations(current_score)

def _render_compliance_recommendations(score_data: Dict[str, Any]):
    """
    Render actionable compliance recommendations based on the current score.
    
    Args:
        score_data: Current compliance score data
    """
    # Get component scores
    components = score_data.get("components", {})
    
    # Filter components that need improvement (score < 80)
    needs_improvement = {k: v for k, v in components.items() if v is not None and v < 80}
    
    if not needs_improvement:
        st.success("🎉 Great job! Your compliance practices meet or exceed all standards. Continue monitoring to maintain this level.")
        return
    
    # Recommendations by component
    recommendations = {
        "code": [
            "Implement automated PII detection in your CI/CD pipeline",
            "Add code review steps specifically for privacy compliance",
            "Update PII handling patterns in your codebase"
        ],
        "blob": [
            "Review document retention policies",
            "Implement document classification for sensitive information",
            "Add metadata scanning for sensitive documents"
        ],
        "dpia": [
            "Schedule regular DPIA reviews for all data processing activities",
            "Document all high-risk processing activities",
            "Consult with your DPO on DPIA findings"
        ],
        "image": [
            "Implement image redaction for sensitive content",
            "Add face detection and blurring capabilities",
            "Document image processing practices"
        ],
        "website": [
            "Update cookie consent mechanisms",
            "Review third-party tracking scripts",
            "Implement privacy by design in web forms"
        ],
        "database": [
            "Implement column-level encryption for sensitive data",
            "Review database access controls",
            "Add audit logging for sensitive data access"
        ]
    }
    
    # Display recommendations
    st.write("### Compliance Recommendations")
    
    for component, score in sorted(needs_improvement.items(), key=lambda x: x[1]):
        if component in recommendations:
            # Determine severity based on score
            if score < 60:
                severity = "High Priority"
                color = "#F44336"  # Red
            elif score < 70:
                severity = "Medium Priority"
                color = "#FF9800"  # Orange
            else:
                severity = "Low Priority" 
                color = "#FFC107"  # Amber
            
            # Get component display name
            display_name = {
                "code": "Code Repositories",
                "blob": "Documents & Files",
                "dpia": "Data Protection Impact Assessment",
                "image": "Image Processing",
                "website": "Website & Cookies",
                "database": "Database Management"
            }.get(component, component.title())
            
            # Display component recommendations
            st.markdown(f"""
            <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px;
                       box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span style="font-weight: 500;">{display_name}</span>
                    <span style="color: {color}; font-weight: 500;">{severity}</span>
                </div>
                <div style="margin-left: 15px;">
                    {"<br>".join(f"• {rec}" for rec in recommendations[component][:2])}
                </div>
            </div>
            """, unsafe_allow_html=True)

def _render_regulatory_coverage_overview():
    """
    Render data-driven regulatory coverage overview with real compliance data and audit trails.
    """
    st.subheader(f"🏆 {get_text('compliance_dashboard.regulatory_coverage_title', '🏆 Regulatory Coverage Overview')}")
    
    # Get real coverage data
    coverage_report = coverage_analyzer.get_comprehensive_coverage_report()
    
    # Extract coverage statistics with audit trails
    gdpr_data = coverage_report["regulations"]["gdpr"]
    ai_act_data = coverage_report["regulations"]["eu_ai_act_2025"]
    uavg_data = coverage_report["regulations"]["netherlands_uavg"]
    soc2_data = coverage_report["regulations"]["soc2_security"]
    
    coverage_stats = {
        "GDPR": {
            "implemented": gdpr_data["implemented_articles"],
            "total": gdpr_data["total_articles"],
            "percentage": gdpr_data["coverage_percentage"],
            "evidence": gdpr_data["evidence_count"],
            "last_updated": gdpr_data["last_assessment"],
            "color": "#28a745" if gdpr_data["coverage_percentage"] >= 95 else "#fd7e14"
        },
        "EU AI Act 2025": {
            "implemented": ai_act_data["implemented_categories"],
            "total": ai_act_data["total_categories"],
            "percentage": ai_act_data["coverage_percentage"],
            "evidence": ai_act_data["evidence_count"],
            "last_updated": ai_act_data["last_assessment"],
            "color": "#28a745" if ai_act_data["coverage_percentage"] >= 95 else "#fd7e14"
        },
        "Netherlands UAVG": {
            "implemented": uavg_data["implemented_areas"],
            "total": uavg_data["total_areas"],
            "percentage": uavg_data["coverage_percentage"],
            "evidence": uavg_data["total_evidence"],
            "last_updated": uavg_data["last_assessment"],
            "color": "#28a745" if uavg_data["coverage_percentage"] >= 95 else "#fd7e14"
        },
        "SOC2 Security": {
            "implemented": 67,
            "total": 67,
            "percentage": soc2_data["coverage_percentage"],
            "evidence": soc2_data["evidence_count"],
            "last_updated": soc2_data["last_assessment"],
            "color": "#28a745"
        }
    }
    
    # Display coverage cards with audit trails
    cols = st.columns(4)
    for i, (regulation, stats) in enumerate(coverage_stats.items()):
        with cols[i]:
            # Parse timestamp for display
            try:
                from datetime import datetime
                timestamp = datetime.fromisoformat(stats['last_updated'].replace('Z', '+00:00'))
                time_display = timestamp.strftime('%H:%M')
                date_display = timestamp.strftime('%Y-%m-%d')
            except:
                time_display = "N/A"
                date_display = "N/A"
            
            st.markdown(f"""
            <div style="background-color: white; border-radius: 10px; padding: 15px; margin-bottom: 10px;
                       box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;
                       border-top: 4px solid {stats['color']};">
                <h4 style="margin: 0; color: #333; font-size: 14px;">{regulation}</h4>
                <div style="font-size: 24px; font-weight: bold; color: {stats['color']}; margin: 5px 0;">
                    {stats['percentage']:.1f}%
                </div>
                <div style="color: #666; font-size: 12px; margin-bottom: 5px;">
                    {stats['implemented']}/{stats['total']} Complete
                </div>
                <div style="color: #888; font-size: 10px; display: flex; justify-content: space-between;">
                    <span>Evidence: {stats['evidence']}</span>
                    <span>{time_display}</span>
                </div>
                <div style="color: #888; font-size: 10px; margin-top: 2px;">
                    {date_display}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Add audit trail summary
    audit_trail = coverage_report["audit_trail"]
    data_provenance = coverage_report["data_provenance"]
    
    st.markdown(f"""
    <div style="background-color: #f8f9fa; border-radius: 8px; padding: 12px; margin-top: 15px;
               border-left: 4px solid #17a2b8; font-size: 12px;">
        <strong>📋 {get_text('compliance_dashboard.audit_trail', 'Audit Trail')}:</strong> {audit_trail["assessor"]} v{audit_trail["version"]} | 
        <strong>{get_text('compliance_dashboard.confidence', 'Confidence')}:</strong> {audit_trail["confidence_level"]} | 
        <strong>{get_text('compliance_dashboard.data_source', 'Data Source')}:</strong> {data_provenance["source"]} | 
        <strong>{get_text('compliance_dashboard.methodology', 'Methodology')}:</strong> {data_provenance["methodology"]}
    </div>
    """, unsafe_allow_html=True)

def _render_enhanced_regulatory_section():
    """
    Render enhanced regulatory compliance section with detailed breakdowns.
    """
    st.markdown("---")
    st.subheader(f"📊 {get_text('compliance_dashboard.detailed_compliance_title', 'Detailed Regulatory Compliance')}")
    
    # Create tabs for different regulations with translations
    tab1, tab2, tab3, tab4 = st.tabs([
        get_text('compliance_dashboard.gdpr_tab', 'GDPR Coverage'),
        get_text('compliance_dashboard.ai_act_tab', 'AI Act 2025'),
        get_text('compliance_dashboard.uavg_tab', 'Netherlands UAVG'),
        get_text('compliance_dashboard.competitive_tab', 'Competitive Analysis')
    ])
    
    with tab1:
        _render_gdpr_coverage_details()
    
    with tab2:
        _render_ai_act_coverage_details()
    
    with tab3:
        _render_uavg_coverage_details()
    
    with tab4:
        _render_competitive_analysis()

def _render_gdpr_coverage_details():
    """Render data-driven GDPR coverage analysis with real chapter breakdowns."""
    st.write(f"#### {get_text('compliance_dashboard.gdpr_coverage_title', 'Complete GDPR Coverage - Data-Driven Analysis')}")
    
    # Get real GDPR coverage data
    gdpr_data = coverage_analyzer.get_gdpr_coverage_real()
    chapter_breakdown = gdpr_data["chapter_breakdown"]
    
    # Display overall GDPR metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            get_text('compliance_dashboard.total_articles', 'Total Articles'), 
            f"{gdpr_data['implemented_articles']}/{gdpr_data['total_articles']}"
        )
    with col2:
        st.metric(
            get_text('compliance_dashboard.coverage', 'Coverage'), 
            f"{gdpr_data['coverage_percentage']:.1f}%"
        )
    with col3:
        st.metric(
            get_text('compliance_dashboard.evidence_count', 'Evidence Count'), 
            gdpr_data['evidence_count']
        )
    
    # Display chapter breakdown with real data
    for chapter_name, chapter_data in chapter_breakdown.items():
        # Determine color based on actual percentage
        percentage = chapter_data['percentage']
        if percentage >= 95:
            color = "#28a745"  # Green
            status_icon = "✓"
            status_text = get_text('compliance_dashboard.complete', 'Complete')
        elif percentage >= 80:
            color = "#ffc107"  # Yellow
            status_icon = "⚠"
            status_text = get_text('compliance_dashboard.mostly_complete', 'Mostly Complete')
        else:
            color = "#dc3545"  # Red
            status_icon = "⚠"
            status_text = get_text('compliance_dashboard.in_progress', 'In Progress')
        
        # Parse timestamp for display
        try:
            timestamp = datetime.fromisoformat(chapter_data['last_validated'].replace('Z', '+00:00'))
            time_display = timestamp.strftime('%H:%M %d/%m')
        except:
            time_display = "N/A"
        
        st.markdown(f"""
        <div style="background-color: white; border-radius: 8px; padding: 12px; margin-bottom: 8px;
                   box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 500; color: #333;">{chapter_name}</span>
                <div style="display: flex; align-items: center;">
                    <span style="color: #666; font-size: 12px; margin-right: 10px;">
                        {chapter_data['implemented']}/{chapter_data['total']} articles | 
                        Evidence: {chapter_data['evidence_count']} | 
                        {time_display}
                    </span>
                    <span style="color: {color}; font-weight: 500;">{status_icon} {status_text}</span>
                </div>
            </div>
            <div style="margin-top: 5px;">
                <div style="background-color: #f0f0f0; border-radius: 10px; height: 4px; overflow: hidden;">
                    <div style="background-color: {color}; height: 100%; width: {percentage}%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add data source information with internationalization
    st.markdown(f"""
    <div style="background-color: #e9ecef; border-radius: 6px; padding: 10px; margin-top: 15px; font-size: 12px;">
        <strong>{get_text('compliance_dashboard.data_source', 'Data Source')}:</strong> {gdpr_data['data_source']} | 
        <strong>{get_text('compliance_dashboard.region', 'Region')}:</strong> {gdpr_data['region']} | 
        <strong>{get_text('compliance_dashboard.last_assessment', 'Last Assessment')}:</strong> {gdpr_data['last_assessment'][:19]} | 
        <strong>{get_text('compliance_dashboard.scan_evidence', 'Scan Evidence')}:</strong> {gdpr_data['scan_count']} recent scans analyzed
    </div>
    """, unsafe_allow_html=True)

def _render_ai_act_coverage_details():
    """Render detailed AI Act 2025 coverage analysis."""
    st.write("#### EU AI Act 2025 - Complete Implementation")
    
    ai_act_sections = {
        "Prohibited AI Practices": {"articles": "Article 5", "status": "Complete", "color": "#dc3545"},
        "High-Risk AI Systems": {"articles": "Articles 6-15", "status": "Complete", "color": "#fd7e14"},
        "Limited Risk Systems": {"articles": "Articles 50-51", "status": "Complete", "color": "#ffc107"},
        "General Purpose AI Models": {"articles": "Articles 51-55", "status": "Complete", "color": "#17a2b8"},
        "Governance & Compliance": {"articles": "Articles 56-85", "status": "Complete", "color": "#28a745"}
    }
    
    for section, details in ai_act_sections.items():
        st.markdown(f"""
        <div style="background-color: white; border-radius: 8px; padding: 12px; margin-bottom: 8px;
                   box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid {details['color']};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 500; color: #333;">{section}</span>
                <div style="display: flex; align-items: center;">
                    <span style="color: #666; font-size: 14px; margin-right: 10px;">{details['articles']}</span>
                    <span style="color: {details['color']}; font-weight: 500;">✓ {details['status']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def _render_uavg_coverage_details():
    """Render detailed Netherlands UAVG coverage analysis."""
    st.write("#### Netherlands UAVG - Complete Specialization")
    
    uavg_areas = {
        "AP Guidelines 2024-2025": {"coverage": "100%", "status": "Complete", "color": "#28a745"},
        "BSN Processing (11-test validation)": {"coverage": "Advanced", "status": "Complete", "color": "#28a745"},
        "Cookie Consent (AP Rules)": {"coverage": "Real-time", "status": "Complete", "color": "#28a745"},
        "Breach Notification (72h)": {"coverage": "Automated", "status": "Complete", "color": "#28a745"},
        "Dutch Language Support": {"coverage": "Native", "status": "Complete", "color": "#28a745"},
        "Data Residency (NL/EU)": {"coverage": "Enforced", "status": "Complete", "color": "#28a745"}
    }
    
    for area, details in uavg_areas.items():
        st.markdown(f"""
        <div style="background-color: white; border-radius: 8px; padding: 12px; margin-bottom: 8px;
                   box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid {details['color']};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 500; color: #333;">{area}</span>
                <div style="display: flex; align-items: center;">
                    <span style="color: #666; font-size: 14px; margin-right: 10px;">{details['coverage']}</span>
                    <span style="color: {details['color']}; font-weight: 500;">✓ {details['status']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def _render_competitive_analysis():
    """Render competitive analysis showing market advantages."""
    st.write("#### Market Position vs Competitors")
    
    # Competitive comparison data
    comparison_data = {
        "DataGuardian Pro": {
            "gdpr_coverage": 100,
            "ai_act_coverage": 100,
            "netherlands_specialization": 100,
            "cost_savings": 82,
            "color": "#28a745"
        },
        "OneTrust": {
            "gdpr_coverage": 86,
            "ai_act_coverage": 30,
            "netherlands_specialization": 20,
            "cost_savings": 0,
            "color": "#dc3545"
        },
        "TrustArc": {
            "gdpr_coverage": 78,
            "ai_act_coverage": 25,
            "netherlands_specialization": 15,
            "cost_savings": 0,
            "color": "#fd7e14"
        }
    }
    
    # Create comparison chart
    import plotly.graph_objects as go
    
    categories = ['GDPR Coverage', 'AI Act 2025', 'Netherlands UAVG', 'Cost Savings']
    
    fig = go.Figure()
    
    for platform, data in comparison_data.items():
        values = [
            data['gdpr_coverage'],
            data['ai_act_coverage'], 
            data['netherlands_specialization'],
            data['cost_savings']
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=platform,
            line_color=data['color']
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Competitive Comparison (%)",
        height=400
    )
    
    st.plotly_chart(fig, width="stretch")
    
    # Market advantages
    st.markdown("""
    **Key Competitive Advantages:**
    - 🏆 **Comprehensive GDPR compliance coverage across all chapters**
    - 🚀 **Broad EU AI Act 2025 implementation (ahead of market)**
    - 🇳🇱 **Native Netherlands UAVG specialization (BSN validation, AP compliance)**
    - 💰 **76-84% cost savings vs OneTrust/TrustArc**
    - ⚡ **Advanced features competitors lack (real-time monitoring, predictive compliance)**
    """)

def generate_mock_compliance_data():
    """
    Generate mock compliance data for testing.
    This should only be called if no real scan data is available to generate compliance scores.
    """
    # Call the mock data generator from the compliance score module
    from services.compliance_score import generate_mock_history
    generate_mock_history(days=90)
    st.success("Generated mock compliance history for demonstration purposes.")

if __name__ == "__main__":
    # Note: set_page_config is already called in main app.py
    # Remove duplicate call to prevent Streamlit error
    render_compliance_dashboard()