"""
History Page Module
Displays scan history with filtering and trends
"""

import streamlit as st
import logging
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def render_history_page():
    """Render scan history with real data and filtering"""
    from utils.translations import _
    from services.results_aggregator import ResultsAggregator
    
    st.title(f"📋 {_('history.title', 'Scan History')}")
    
    try:
        aggregator = ResultsAggregator()
        username = st.session_state.get('username', 'anonymous')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            days_filter = st.selectbox(
                "Time Period",
                [7, 30, 90, 365],
                index=1,
                format_func=lambda x: f"Last {x} days"
            )
        
        with col2:
            scan_types = st.multiselect(
                "Scan Types",
                ["code", "document", "image", "website", "database", "ai_model", "dpia"],
                default=[]
            )
        
        with col3:
            risk_filter = st.selectbox(
                "Risk Level",
                ["All", "High Risk Only", "Medium+", "Low Risk Only"],
                index=0
            )
        
        all_scans = aggregator.get_recent_scans(days=days_filter, username=username)
        
        filtered_scans = all_scans
        if scan_types:
            filtered_scans = [scan for scan in filtered_scans if scan.get('scan_type') in scan_types]
        
        if risk_filter != "All":
            if risk_filter == "High Risk Only":
                filtered_scans = [scan for scan in filtered_scans if scan.get('high_risk_count', 0) > 0]
            elif risk_filter == "Medium+":
                filtered_scans = [scan for scan in filtered_scans if scan.get('high_risk_count', 0) > 0 or 
                                scan.get('total_pii_found', 0) > 5]
            elif risk_filter == "Low Risk Only":
                filtered_scans = [scan for scan in filtered_scans if scan.get('high_risk_count', 0) == 0]
        
        if not filtered_scans:
            st.info("No scan history found matching the selected filters.")
            if st.button("🔍 Start New Scan"):
                st.session_state['start_new_scan'] = True
                st.rerun()
            return
        
        st.subheader(f"Found {len(filtered_scans)} scans")
        
        if len(filtered_scans) > 1:
            render_history_trends(filtered_scans)
        
        st.markdown("---")
        
        history_data = []
        for scan in filtered_scans:
            result = scan.get('result', {})
            
            total_pii = scan.get('total_pii_found', 0)
            high_risk = scan.get('high_risk_count', 0)
            
            if total_pii == 0:
                total_pii = result.get('total_pii_found', 0)
            if high_risk == 0:
                high_risk = result.get('high_risk_count', 0)
            
            timestamp = scan.get('timestamp', '')
            if timestamp:
                try:
                    if hasattr(timestamp, 'strftime'):
                        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
                    else:
                        dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = str(timestamp)[:16]
            else:
                formatted_time = 'Unknown'
            
            compliance = result.get('compliance_score', 0)
            if compliance == 0:
                compliance = scan.get('compliance_score', 0)
            
            history_data.append({
                'Timestamp': formatted_time,
                'Scan ID': scan.get('scan_id', 'N/A'),
                'Type': scan.get('scan_type', 'unknown').replace('_', ' ').title(),
                'Files Scanned': scan.get('file_count', 0),
                'PII Found': total_pii,
                'High Risk': high_risk,
                'Compliance Score': f"{compliance:.1f}%",
                'Region': scan.get('region', 'N/A')
            })
        
        if history_data:
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)
            
            st.subheader("Export Options")
            
            # Check if user can download (paid users only)
            from config.pricing_config import can_download_reports
            if not can_download_reports():
                st.info("🔒 **Report downloads available for paid subscribers only.** Upgrade to export your scan history.")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="📊 Download CSV",
                        data=csv_data,
                        file_name=f"scan_history_{username}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                        
                with col2:
                    if st.button("📋 Generate Compliance Report"):
                        st.info("Generating comprehensive compliance report...")
                        _generate_history_report(filtered_scans, username)
                    
    except Exception as e:
        logger.error(f"Error loading scan history: {e}")
        st.error(f"Error loading scan history: {str(e)}")
        st.info("Please try refreshing the page or contact support if the issue persists.")


def render_history_trends(scans_data):
    """Render historical trend charts"""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        
        dates = []
        pii_counts = []
        compliance_scores = []
        
        for scan in sorted(scans_data, key=lambda x: str(x.get('timestamp', ''))):
            timestamp = scan.get('timestamp', '')
            if timestamp:
                try:
                    if hasattr(timestamp, 'date'):
                        dates.append(timestamp.date())
                    else:
                        dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                        dates.append(dt.date())
                except:
                    continue
                
                pii_counts.append(scan.get('total_pii_found', 0))
                result = scan.get('result', {})
                compliance_scores.append(result.get('compliance_score', scan.get('compliance_score', 0)))
        
        if len(dates) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(x=dates, y=pii_counts, mode='lines+markers', name='PII Found'))
                fig1.update_layout(title='PII Detection Trend', xaxis_title='Date', yaxis_title='PII Count')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=dates, y=compliance_scores, mode='lines+markers', name='Compliance', line=dict(color='green')))
                fig2.update_layout(title='Compliance Score Trend', xaxis_title='Date', yaxis_title='Score (%)')
                st.plotly_chart(fig2, use_container_width=True)
        
    except ImportError:
        st.info("Install plotly for trend charts: pip install plotly")
    except Exception as e:
        logger.warning(f"Could not render trends: {e}")


def _generate_history_report(scans, username):
    """Generate a comprehensive history report"""
    try:
        total_scans = len(scans)
        total_pii = sum(s.get('total_pii_found', 0) for s in scans)
        total_high_risk = sum(s.get('high_risk_count', 0) for s in scans)
        
        compliance_scores = [s.get('result', {}).get('compliance_score', 0) for s in scans if s.get('result', {}).get('compliance_score', 0) > 0]
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Scan History Report - {username}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #2d5a4d; color: white; padding: 20px; border-radius: 8px; }}
                .metric {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background: #2d5a4d; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 Scan History Report</h1>
                <p>User: {username} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <h2>Summary Metrics</h2>
            <div class="metric"><strong>Total Scans:</strong> {total_scans}</div>
            <div class="metric"><strong>Total PII Found:</strong> {total_pii}</div>
            <div class="metric"><strong>High Risk Issues:</strong> {total_high_risk}</div>
            <div class="metric"><strong>Average Compliance:</strong> {avg_compliance:.1f}%</div>
            
            <h2>Scan Details</h2>
            <table>
                <tr><th>Date</th><th>Type</th><th>Files</th><th>PII</th><th>Risk</th><th>Compliance</th></tr>
        """
        
        for scan in scans[:50]:
            timestamp = scan.get('timestamp', 'N/A')
            if hasattr(timestamp, 'strftime'):
                date_str = timestamp.strftime('%Y-%m-%d')
            else:
                date_str = str(timestamp)[:10]
            
            report_html += f"""
                <tr>
                    <td>{date_str}</td>
                    <td>{scan.get('scan_type', 'N/A').title()}</td>
                    <td>{scan.get('file_count', 0)}</td>
                    <td>{scan.get('total_pii_found', 0)}</td>
                    <td>{scan.get('high_risk_count', 0)}</td>
                    <td>{scan.get('result', {}).get('compliance_score', 0):.1f}%</td>
                </tr>
            """
        
        report_html += """
            </table>
            <p><em>Generated by DataGuardian Pro - Enterprise Privacy Compliance Platform</em></p>
        </body>
        </html>
        """
        
        # Check if user can download (paid users only)
        from config.pricing_config import can_download_reports
        if not can_download_reports():
            st.info("🔒 Report downloads available for paid subscribers. Upgrade to download reports.")
        else:
            st.download_button(
                label="📥 Download Report",
                data=report_html,
                file_name=f"history_report_{username}_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html"
            )
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        st.error("Could not generate report. Please try again.")
