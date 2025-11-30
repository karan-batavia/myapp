"""
Unified HTML Report Generator for DataGuardian Pro
Consolidates all HTML report generation into a single, standardized system.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Safe imports with fallbacks
try:
    import streamlit as st
except ImportError:
    # Fallback for non-Streamlit environments
    class StreamlitMock:
        session_state = {"language": "en"}
    st = StreamlitMock()

# Safe translation imports with fallbacks
try:
    from utils.unified_translation import t_report, t_technical, t_ui
except ImportError:
    # Fallback translation functions
    def t_report(key, default=None):
        return default or key.replace('_', ' ').title()
    
    def t_technical(key, default=None):
        return default or key.replace('_', ' ').title()
        
    def t_ui(key, default=None):
        return default or key.replace('_', ' ').title()

# Safe enhanced findings import with fallback
try:
    from services.enhanced_finding_generator import enhance_findings_for_report
except ImportError:
    # Fallback that returns original findings unchanged
    def enhance_findings_for_report(scanner_type, findings, region):
        return findings

logger = logging.getLogger(__name__)

class UnifiedHTMLReportGenerator:
    """Consolidated HTML report generator with unified translation support."""
    
    def __init__(self):
        self.current_language = 'en'
        self._update_language()
    
    def _update_language(self):
        """Update current language from session state."""
        self.current_language = st.session_state.get('language', 'en')
    
    def generate_html_report(self, scan_result: Dict[str, Any]) -> str:
        """
        Generate a unified HTML report for any scanner type.
        
        Args:
            scan_result: Scan result data
            
        Returns:
            Complete HTML report as string
        """
        self._update_language()
        
        # Extract basic scan information
        scan_type = scan_result.get('scan_type', 'Unknown')
        scan_id = scan_result.get('scan_id', 'Unknown')
        timestamp = scan_result.get('timestamp', datetime.now().isoformat())
        region = scan_result.get('region', 'Netherlands')
        
        # Format timestamp based on language
        formatted_timestamp = self._format_timestamp(timestamp)
        
        # Extract metrics
        metrics = self._extract_metrics(scan_result)
        
        # Enhance findings with specific context and actionable recommendations
        original_findings = scan_result.get('findings', [])
        enhanced_findings = enhance_findings_for_report(
            scanner_type=scan_type.lower().replace(' ', '_'),
            findings=original_findings,
            region=region
        )
        
        # Generate findings HTML with enhanced findings
        findings_html = self._generate_findings_html(enhanced_findings)
        
        # Generate scanner-specific content
        scanner_content = self._generate_scanner_specific_content(scan_result)
        
        # Generate compliance forecast chart
        compliance_forecast_html = self._generate_compliance_forecast_section(scan_result)
        
        # Build complete HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="{self.current_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t_report('dataGuardian_pro', 'DataGuardian Pro')} - {scan_type} {t_report('comprehensive_report', 'Report')}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    {self._get_unified_css()}
</head>
<body>
    <div class="container">
        {self._generate_header(scan_type, scan_id, formatted_timestamp, region)}
        {self._generate_executive_summary(metrics)}
        {compliance_forecast_html}
        {scanner_content}
        {self._generate_findings_section(findings_html)}
        {self._generate_footer(scan_id, formatted_timestamp)}
    </div>
</body>
</html>
        """
        
        return html_content.strip()
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp based on current language."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if self.current_language == 'nl':
                return dt.strftime('%d-%m-%Y %H:%M:%S')
            else:
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return str(timestamp)
    
    def _extract_metrics(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and standardize metrics from scan result."""
        # Handle different metric naming conventions
        summary = scan_result.get('summary', {})
        
        metrics = {
            'files_scanned': (
                summary.get('scanned_files') or 
                scan_result.get('files_scanned') or 
                scan_result.get('pages_scanned') or 
                scan_result.get('images_processed') or 0
            ),
            'lines_analyzed': (
                summary.get('lines_analyzed') or 
                scan_result.get('lines_analyzed') or 
                scan_result.get('content_analysis') or 
                scan_result.get('text_extracted') or 0
            ),
            'total_findings': len(scan_result.get('findings', [])),
            'critical_count': len([f for f in scan_result.get('findings', []) if f.get('severity') == 'Critical']),
            'high_risk_count': (
                summary.get('high_risk_count') or 
                scan_result.get('high_risk_count') or
                len([f for f in scan_result.get('findings', []) if f.get('severity') == 'High'])
            ),
            'medium_risk_count': (
                summary.get('medium_risk_count') or 
                scan_result.get('medium_risk_count') or
                len([f for f in scan_result.get('findings', []) if f.get('severity') == 'Medium'])
            ),
            'low_risk_count': (
                summary.get('low_risk_count') or 
                scan_result.get('low_risk_count') or
                len([f for f in scan_result.get('findings', []) if f.get('severity') == 'Low'])
            ),
            'compliance_score': (
                summary.get('overall_compliance_score') or 
                scan_result.get('compliance_score') or 
                self._calculate_compliance_score(scan_result)
            )
        }
        
        return metrics
    
    def _calculate_compliance_score(self, scan_result: Dict[str, Any]) -> int:
        """Calculate compliance score based on findings."""
        findings = scan_result.get('findings', [])
        if not findings:
            return 100
        
        # Count severity levels
        critical = len([f for f in findings if f.get('severity') == 'Critical'])
        high = len([f for f in findings if f.get('severity') == 'High'])
        medium = len([f for f in findings if f.get('severity') == 'Medium'])
        low = len([f for f in findings if f.get('severity') == 'Low'])
        
        # Calculate penalty
        penalty = (critical * 25) + (high * 15) + (medium * 10) + (low * 5)
        score = max(0, 100 - penalty)
        
        return score
    
    def _get_unified_css(self) -> str:
        """Get unified CSS styles for all report types."""
        return """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1f77b4, #2196F3);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            margin-bottom: 0;
        }
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 2.2em;
            font-weight: 300;
        }
        .header p {
            margin: 5px 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .summary {
            margin: 30px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #28a745;
        }
        .summary h2 {
            margin-top: 0;
            color: #2c5282;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #1f77b4;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 14px;
            color: #6b7280;
        }
        .findings {
            margin: 30px;
        }
        .findings h2 {
            color: #2c5282;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }
        .finding {
            margin: 15px 0;
            padding: 20px;
            border-left: 4px solid #dc3545;
            background: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .finding.critical {
            border-left-color: #dc3545;
            background: #fef2f2;
        }
        .finding.high {
            border-left-color: #fd7e14;
            background: #fef3e8;
        }
        .finding.medium {
            border-left-color: #ffc107;
            background: #fffbeb;
        }
        .finding.low {
            border-left-color: #28a745;
            background: #f0fdf4;
        }
        .finding-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .finding-type {
            font-weight: 600;
            color: #374151;
        }
        .finding-severity {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .severity-critical {
            background: #dc3545;
            color: white;
        }
        .severity-high {
            background: #fd7e14;
            color: white;
        }
        .severity-medium {
            background: #ffc107;
            color: #000;
        }
        .severity-low {
            background: #28a745;
            color: white;
        }
        .finding-description {
            color: #4b5563;
            line-height: 1.6;
        }
        .finding-location {
            font-family: 'Courier New', monospace;
            background: #f3f4f6;
            padding: 8px;
            border-radius: 4px;
            font-size: 13px;
            margin: 10px 0;
        }
        .scanner-specific {
            margin: 30px;
            padding: 25px;
            background: #e8f5e8;
            border-radius: 10px;
        }
        .footer {
            margin-top: 0;
            padding: 20px 30px;
            background: #6c757d;
            color: white;
            text-align: center;
        }
        .footer p {
            margin: 5px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 15px;
            border: 1px solid #dee2e6;
            text-align: left;
        }
        th {
            background: #6c757d;
            color: white;
            font-weight: 600;
        }
        .compliance-score {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            padding: 20px;
        }
        .score-excellent { color: #28a745; }
        .score-good { color: #17a2b8; }
        .score-warning { color: #ffc107; }
        .score-danger { color: #dc3545; }
        
        /* Enhanced findings styles */
        .enhanced-finding {
            margin: 20px 0;
            border-radius: 8px;
        }
        .finding-content {
            margin-top: 15px;
        }
        .finding-content > div {
            margin: 10px 0;
            padding: 8px 0;
        }
        .finding-context, .business-impact {
            background: rgba(0,0,0,0.02);
            border-radius: 4px;
            padding: 12px;
            margin: 10px 0;
        }
        .compliance-section {
            background: #e3f2fd;
            border-radius: 6px;
            padding: 15px;
            margin: 15px 0;
        }
        .compliance-section h4 {
            margin: 0 0 10px 0;
            color: #1565c0;
        }
        .compliance-list {
            list-style: none;
            padding: 0;
        }
        .compliance-list li {
            padding: 4px 0;
            padding-left: 20px;
            position: relative;
        }
        .compliance-list li::before {
            content: "⚖️";
            position: absolute;
            left: 0;
        }
        .recommendations-section {
            background: #f3e5f5;
            border-radius: 6px;
            padding: 15px;
            margin: 15px 0;
        }
        .recommendations-section h4 {
            margin: 0 0 15px 0;
            color: #7b1fa2;
        }
        .recommendation {
            background: white;
            border-radius: 4px;
            padding: 12px;
            margin: 10px 0;
            border-left: 4px solid #9c27b0;
        }
        .recommendation-header {
            font-weight: bold;
            color: #4a148c;
            margin-bottom: 8px;
        }
        .recommendation-details {
            font-size: 0.9em;
            color: #666;
            margin: 6px 0;
        }
        .recommendation-priority {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .priority-critical {
            background: #ffebee;
            color: #c62828;
        }
        .priority-high {
            background: #fff3e0;
            color: #ef6c00;
        }
        .priority-medium {
            background: #fffde7;
            color: #f57f17;
        }
        .priority-low {
            background: #e8f5e8;
            color: #2e7d32;
        }
        
        /* Compliance Forecast Section Styles */
        .compliance-forecast-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid #dee2e6;
        }
        .compliance-forecast-section h2 {
            color: #1565c0;
            margin-bottom: 20px;
            font-size: 1.4em;
        }
        .forecast-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .forecast-metric {
            background: white;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
            border: 1px solid #e0e0e0;
        }
        .forecast-metric .metric-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #1976d2;
            margin-bottom: 5px;
            display: block;
        }
        .forecast-metric .metric-label {
            font-size: 0.9em;
            color: #666;
        }
        .trend-improving {
            color: #2e7d32 !important;
        }
        .trend-declining {
            color: #d32f2f !important;
        }
        .trend-stable {
            color: #1976d2 !important;
        }
        #compliance-forecast-chart {
            background: white;
            border-radius: 6px;
            padding: 10px;
            margin: 20px 0;
            border: 1px solid #e0e0e0;
        }
        .forecast-explanation {
            background: white;
            border-radius: 6px;
            padding: 15px;
            margin-top: 20px;
            border: 1px solid #e0e0e0;
        }
        .forecast-explanation h4 {
            color: #1565c0;
            margin-bottom: 15px;
        }
        .explanation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }
        .explanation-item {
            padding: 8px 0;
            font-size: 0.9em;
        }
        .risk-zone-guide {
            background: #f5f5f5;
            border-radius: 4px;
            padding: 10px;
            margin-top: 15px;
        }
        .risk-zone-guide h5 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .risk-zone-guide ul {
            margin: 0;
            padding-left: 20px;
        }
        .risk-zone-guide li {
            margin: 5px 0;
            font-size: 0.9em;
        }
    </style>
        """
    
    def _generate_header(self, scan_type: str, scan_id: str, timestamp: str, region: str) -> str:
        """Generate report header."""
        return f"""
        <div class="header">
            <h1>🛡️ {t_report('dataGuardian_pro', 'DataGuardian Pro')} {t_report('comprehensive_report', 'Comprehensive Report')}</h1>
            <p><strong>{t_report('scan_type', 'Scan Type')}:</strong> {scan_type}</p>
            <p><strong>{t_report('scan_id', 'Scan ID')}:</strong> {scan_id[:8]}...</p>
            <p><strong>{t_report('generated_on', 'Generated')}:</strong> {timestamp}</p>
            <p><strong>{t_report('region', 'Region')}:</strong> {region}</p>
        </div>
        """
    
    def _generate_executive_summary(self, metrics: Dict[str, Any]) -> str:
        """Generate executive summary section."""
        score = metrics.get('compliance_score', 0)
        score_class = self._get_score_class(score)
        
        return f"""
        <div class="summary">
            <h2>📊 {t_report('executive_summary', 'Executive Summary')}</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('files_scanned', 0):,}</div>
                    <div class="metric-label">{t_report('files_scanned', 'Files Scanned')}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('total_findings', 0):,}</div>
                    <div class="metric-label">{t_report('total_findings', 'Total Findings')}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('critical_count', 0):,}</div>
                    <div class="metric-label">{t_report('critical_issues', 'Critical Issues')}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('high_risk_count', 0):,}</div>
                    <div class="metric-label">{t_technical('high_risk', 'High Risk Issues')}</div>
                </div>
            </div>
            <div class="compliance-score {score_class}">
                {t_technical('compliance_score', 'Compliance Score')}: {score}%
            </div>
        </div>
        """
    
    def _get_score_class(self, score: int) -> str:
        """Get CSS class for compliance score."""
        if score >= 90:
            return 'score-excellent'
        elif score >= 75:
            return 'score-good'
        elif score >= 50:
            return 'score-warning'
        else:
            return 'score-danger'
    
    def _generate_findings_section(self, findings_html: str) -> str:
        """Generate findings section."""
        return f"""
        <div class="findings">
            <h2>🔍 {t_report('detailed_findings', 'Detailed Findings')}</h2>
            {findings_html}
        </div>
        """
    
    def _generate_findings_html(self, findings: List[Dict[str, Any]]) -> str:
        """Generate HTML for enhanced findings list with actionable recommendations."""
        if not findings:
            return f"<p>✅ {t_report('no_issues_found', 'No issues found in the analysis.')}</p>"
        
        # Separate deepfake findings from other findings
        deepfake_findings = [f for f in findings if f.get('type') == 'DEEPFAKE_SYNTHETIC_MEDIA']
        other_findings = [f for f in findings if f.get('type') != 'DEEPFAKE_SYNTHETIC_MEDIA']
        
        findings_html = ""
        
        # Add deepfake findings section if present
        if deepfake_findings:
            findings_html += self._generate_deepfake_findings_section(deepfake_findings)
        
        # Add other findings
        for finding in other_findings:
            # Handle both enhanced and original findings
            severity = finding.get('severity', finding.get('risk_level', 'Low')).lower()
            finding_type = finding.get('title', finding.get('type', finding.get('category', 'Unknown')))
            description = finding.get('description', finding.get('message', 'No description available'))
            location = finding.get('location', 'Unknown')
            
            # Enhanced finding fields
            context = finding.get('context', '')
            business_impact = finding.get('business_impact', '')
            gdpr_articles = finding.get('gdpr_articles', [])
            compliance_requirements = finding.get('compliance_requirements', [])
            recommendations = finding.get('recommendations', [])
            remediation_priority = finding.get('remediation_priority', '')
            estimated_effort = finding.get('estimated_effort', '')
            data_classification = finding.get('data_classification', '')
            
            # Build enhanced finding HTML
            findings_html += f"""
            <div class="finding enhanced-finding {severity}">
                <div class="finding-header">
                    <span class="finding-type">{finding_type}</span>
                    <span class="finding-severity severity-{severity}">{finding.get('severity', finding.get('risk_level', 'Low'))}</span>
                </div>
                
                <div class="finding-content">
                    <div class="finding-description">
                        <strong>Description:</strong> {description}
                    </div>
                    
                    {f'<div class="finding-context"><strong>Context:</strong> {context}</div>' if context else ''}
                    
                    <div class="finding-location">
                        <strong>{t_report('location_details', 'Location')}:</strong> {location}
                    </div>
                    
                    {f'<div class="finding-classification"><strong>Data Classification:</strong> {data_classification}</div>' if data_classification else ''}
                    
                    {f'<div class="business-impact"><strong>Business Impact:</strong> {business_impact}</div>' if business_impact else ''}
                    
                    {f'<div class="remediation-priority"><strong>Priority:</strong> {remediation_priority}</div>' if remediation_priority else ''}
                    
                    {f'<div class="estimated-effort"><strong>Estimated Effort:</strong> {estimated_effort}</div>' if estimated_effort else ''}
                    
                    {self._generate_compliance_section(gdpr_articles, compliance_requirements)}
                    
                    {self._generate_recommendations_section(recommendations)}
                </div>
            </div>
            """
        
        return findings_html
    
    def _generate_deepfake_findings_section(self, deepfake_findings: List[Dict[str, Any]]) -> str:
        """Generate special section for deepfake/synthetic media findings with EU AI Act compliance."""
        if not deepfake_findings:
            return ""
        
        section_html = f"""
        <div class="deepfake-section" style="background: #fff3cd; border-left: 5px solid #ff6b6b; padding: 20px; margin: 20px 0; border-radius: 8px;">
            <h3 style="color: #c92a2a; margin-top: 0;">
                🤖 {t_report('deepfake_detection', 'Deepfake/Synthetic Media Detection')} 
                <span style="font-size: 0.8em; color: #e67700;">(EU AI Act Article 50(2))</span>
            </h3>
            <p style="margin: 10px 0; font-size: 0.95em; color: #555;">
                {t_report('deepfake_intro', 'Automated detection of potentially synthetic or AI-generated media requiring transparency labeling under EU AI Act 2025.')}
            </p>
        """
        
        for finding in deepfake_findings:
            severity = finding.get('risk_level', 'Medium')
            confidence = finding.get('confidence', 0)
            context = finding.get('context', '')
            source = finding.get('source', 'Unknown')
            reason = finding.get('reason', '')
            
            # Extract analysis details
            analysis_details = finding.get('analysis_details', {})
            overall_score = analysis_details.get('overall_score', 0)
            artifact_score = analysis_details.get('artifact_score', 0)
            noise_score = analysis_details.get('noise_score', 0)
            compression_score = analysis_details.get('compression_score', 0)
            facial_score = analysis_details.get('facial_inconsistency_score', 0)
            indicators = analysis_details.get('indicators', [])
            
            # Extract EU AI Act compliance details
            eu_compliance = finding.get('eu_ai_act_compliance', {})
            article = eu_compliance.get('article', 'Article 50(2)')
            article_title = eu_compliance.get('title', 'Transparency Obligations')
            requirements = eu_compliance.get('requirements', [])
            recommendation = eu_compliance.get('compliance_recommendation', '')
            
            # Severity color
            severity_colors = {
                'Critical': '#c92a2a',
                'High': '#e67700',
                'Medium': '#f59f00',
                'Low': '#37b24d'
            }
            severity_color = severity_colors.get(severity, '#868e96')
            
            section_html += f"""
            <div class="deepfake-finding" style="background: white; border: 2px solid {severity_color}; padding: 20px; margin: 15px 0; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: {severity_color};">
                        🎭 Synthetic Media Detected
                    </h4>
                    <span style="background: {severity_color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 0.9em;">
                        {severity} Risk
                    </span>
                </div>
                
                <div style="margin: 15px 0;">
                    <strong>{t_report('source_file', 'Source File')}:</strong> 
                    <code style="background: #f8f9fa; padding: 2px 8px; border-radius: 4px;">{source}</code>
                </div>
                
                <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                    <strong style="color: #495057;">📊 {t_report('detection_analysis', 'Detection Analysis')}:</strong>
                    <p style="margin: 10px 0 5px 0;">{context}</p>
                    <div style="margin-top: 10px;">
                        <div style="margin: 5px 0;">
                            <strong>{t_report('overall_likelihood', 'Overall Likelihood')}:</strong> 
                            <span style="color: {severity_color}; font-weight: bold;">{overall_score:.1%}</span>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                            <div>• Artifact Score: <strong>{artifact_score:.2f}</strong></div>
                            <div>• Noise Patterns: <strong>{noise_score:.2f}</strong></div>
                            <div>• Compression Anomalies: <strong>{compression_score:.2f}</strong></div>
                            <div>• Facial Inconsistencies: <strong>{facial_score:.2f}</strong></div>
                        </div>
                    </div>
                </div>
                
                {self._generate_deepfake_indicators_html(indicators)}
                
                <div style="margin: 20px 0; padding: 15px; background: #e7f5ff; border-left: 4px solid #1c7ed6; border-radius: 6px;">
                    <h5 style="margin: 0 0 10px 0; color: #1864ab;">
                        ⚖️ {article}: {article_title}
                    </h5>
                    <p style="margin: 10px 0; font-size: 0.9em; color: #495057;">{reason}</p>
                    
                    {self._generate_compliance_requirements_html(requirements)}
                    
                    <div style="margin: 15px 0; padding: 12px; background: #fff3bf; border-left: 4px solid #fab005; border-radius: 4px;">
                        <strong style="color: #862e9c;">📋 {t_report('recommended_actions', 'Recommended Actions')}:</strong>
                        <p style="margin: 8px 0 0 0; font-size: 0.9em;">{recommendation}</p>
                    </div>
                </div>
            </div>
            """
        
        section_html += "</div>"
        return section_html
    
    def _generate_deepfake_indicators_html(self, indicators: List[str]) -> str:
        """Generate HTML for deepfake detection indicators."""
        if not indicators:
            return ""
        
        indicators_html = """
        <div style="margin: 15px 0;">
            <strong>🔍 Detection Indicators:</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
        """
        
        for indicator in indicators:
            indicators_html += f"<li style='margin: 5px 0;'>{indicator}</li>"
        
        indicators_html += "</ul></div>"
        return indicators_html
    
    def _generate_compliance_requirements_html(self, requirements: List[Dict[str, Any]]) -> str:
        """Generate HTML for EU AI Act compliance requirements."""
        if not requirements:
            return ""
        
        req_html = """
        <div style="margin: 15px 0;">
            <strong>📜 Compliance Requirements:</strong>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background: #f1f3f5;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">Requirement</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">Status</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">Penalty if Non-Compliant</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for req in requirements:
            requirement_text = req.get('requirement', '')
            status = req.get('status', 'Unknown')
            penalty = req.get('penalty_if_non_compliant', 'N/A')
            
            status_color = '#37b24d' if 'implemented' in status.lower() else '#f59f00'
            
            req_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{requirement_text}</td>
                    <td style="padding: 8px; border: 1px solid #dee2e6; color: {status_color}; font-weight: bold;">{status}</td>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{penalty}</td>
                </tr>
            """
        
        req_html += """
                </tbody>
            </table>
        </div>
        """
        return req_html
    
    def _generate_scanner_specific_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate scanner-specific content sections."""
        scan_type = scan_result.get('scan_type', '').lower()
        
        if 'sustainability' in scan_type:
            return self._generate_sustainability_content(scan_result)
        elif 'website' in scan_type:
            return self._generate_website_content(scan_result)
        elif 'ai' in scan_type or 'model' in scan_type:
            return self._generate_ai_model_content(scan_result)
        elif 'dpia' in scan_type:
            return self._generate_dpia_content(scan_result)
        elif 'enterprise' in scan_type or 'connector' in scan_type:
            return self._generate_enterprise_connector_content(scan_result)
        else:
            return ""
    
    def _generate_enterprise_connector_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate enterprise connector-specific metrics and Netherlands compliance."""
        connector_name = scan_result.get('connector_name', 'Unknown')
        connector_metrics = scan_result.get('connector_metrics', {})
        netherlands_findings = scan_result.get('netherlands_findings', {})
        uavg_compliance = scan_result.get('uavg_compliance', {})
        
        # Build connector metrics section
        metrics_html = ""
        if connector_metrics:
            metrics_html = f"""
            <div class="scanner-specific">
                <h3>📊 {connector_name} Scan Metrics</h3>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{connector_metrics.get('accounts_scanned', 0):,}</div>
                        <div class="metric-label">Accounts Scanned</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{connector_metrics.get('contacts_scanned', 0):,}</div>
                        <div class="metric-label">Contacts Scanned</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{connector_metrics.get('leads_scanned', 0):,}</div>
                        <div class="metric-label">Leads Scanned</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{connector_metrics.get('custom_objects_scanned', 0):,}</div>
                        <div class="metric-label">Custom Objects</div>
                    </div>
                </div>
            </div>
            """
        
        # Build Netherlands-specific findings section
        netherlands_html = ""
        if netherlands_findings and any(netherlands_findings.values()):
            netherlands_html = f"""
            <div class="scanner-specific" style="background: linear-gradient(135deg, #fff7e6 0%, #ffe4b5 100%); border-left: 4px solid #ff9800;">
                <h3>🇳🇱 Netherlands-Specific PII Findings</h3>
                <div class="metrics-grid">
                    <div class="metric-card" style="background: {'#ffebee' if netherlands_findings.get('bsn_fields_found', 0) > 0 else '#e8f5e9'};">
                        <div class="metric-value" style="color: {'#c62828' if netherlands_findings.get('bsn_fields_found', 0) > 0 else '#2e7d32'};">{netherlands_findings.get('bsn_fields_found', 0)}</div>
                        <div class="metric-label">BSN Instances</div>
                        <div class="metric-subtitle">Social Security Numbers</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{netherlands_findings.get('kvk_fields_found', 0)}</div>
                        <div class="metric-label">KvK Numbers</div>
                        <div class="metric-subtitle">Business Registry</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{netherlands_findings.get('iban_fields_found', 0)}</div>
                        <div class="metric-label">IBAN Accounts</div>
                        <div class="metric-subtitle">Banking Information</div>
                    </div>
                    <div class="metric-card" style="background: {'#ffebee' if netherlands_findings.get('uavg_violations', 0) > 0 else '#e8f5e9'};">
                        <div class="metric-value" style="color: {'#c62828' if netherlands_findings.get('uavg_violations', 0) > 0 else '#2e7d32'};">{netherlands_findings.get('uavg_violations', 0)}</div>
                        <div class="metric-label">UAVG Violations</div>
                        <div class="metric-subtitle">Dutch Privacy Law</div>
                    </div>
                </div>
            </div>
            """
        
        # Build UAVG compliance section
        uavg_html = ""
        if uavg_compliance.get('applicable'):
            data_min_status = uavg_compliance.get('data_minimization', 'Not assessed')
            data_min_color = '#2e7d32' if data_min_status == 'Adequate' else '#ff9800'
            
            uavg_html = f"""
            <div class="scanner-specific" style="border-left: 4px solid #1976d2;">
                <h3>⚖️ UAVG/GDPR Compliance Assessment</h3>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Requirement</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Status</th>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Data Minimization (Art. 5)</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: {data_min_color}; font-weight: bold;">{data_min_status}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Lawful Basis (Art. 6)</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: #ff9800;">{uavg_compliance.get('lawful_basis', 'Not assessed')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Retention Policy (Art. 5(e))</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{uavg_compliance.get('retention_policy', 'Not assessed')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Data Subject Rights (Art. 15-22)</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: #2e7d32;">{uavg_compliance.get('data_subject_rights', 'Not assessed')}</td>
                    </tr>
                </table>
                <p style="margin-top: 15px; font-size: 0.9em; color: #666;">
                    <strong>Note:</strong> UAVG is the Dutch implementation of GDPR with additional requirements for BSN processing.
                    BSN may only be processed when specifically required by law (Art. 46 UAVG).
                </p>
            </div>
            """
        
        return metrics_html + netherlands_html + uavg_html
    
    def _generate_sustainability_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate sustainability-specific metrics."""
        co2_emissions = scan_result.get('co2_emissions', 'N/A')
        energy_consumption = scan_result.get('energy_consumption', 'N/A')
        cost_savings = scan_result.get('cost_savings_potential', 'N/A')
        
        return f"""
        <div class="scanner-specific">
            <h2>🌱 {t_report('sustainability_report', 'Sustainability Metrics')}</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{co2_emissions}</div>
                    <div class="metric-label">CO₂ Emissions/Month</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{energy_consumption}</div>
                    <div class="metric-label">Energy Consumption</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cost_savings}</div>
                    <div class="metric-label">Potential Cost Savings</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_website_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate website-specific compliance content."""
        cookies_found = scan_result.get('cookies_found', 0)
        trackers_detected = scan_result.get('trackers_detected', 0)
        
        return f"""
        <div class="scanner-specific">
            <h2>🌐 {t_report('website_privacy_report', 'Website Privacy Analysis')}</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{cookies_found}</div>
                    <div class="metric-label">Cookies Found</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{trackers_detected}</div>
                    <div class="metric-label">Trackers Detected</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_compliance_section(self, gdpr_articles: List[str], compliance_requirements: List[str]) -> str:
        """Generate compliance requirements section."""
        if not gdpr_articles and not compliance_requirements:
            return ""
        
        articles_html = ""
        if gdpr_articles:
            articles_html = "<ul class='compliance-list'>"
            for article in gdpr_articles[:3]:  # Limit to first 3 for readability
                articles_html += f"<li>{article}</li>"
            articles_html += "</ul>"
        
        requirements_html = ""
        if compliance_requirements:
            requirements_html = "<ul class='compliance-list'>"
            for requirement in compliance_requirements[:3]:  # Limit to first 3
                requirements_html += f"<li>{requirement}</li>"
            requirements_html += "</ul>"
        
        return f"""
        <div class="compliance-section">
            <h4>⚖️ Compliance Requirements</h4>
            {articles_html}
            {requirements_html}
        </div>
        """
    
    def _generate_recommendations_section(self, recommendations: List[Dict[str, Any]]) -> str:
        """Generate actionable recommendations section."""
        if not recommendations:
            return ""
        
        recommendations_html = ""
        for rec in recommendations[:3]:  # Limit to first 3 for readability
            priority = rec.get('priority', 'Medium').lower()
            priority_class = f"priority-{priority}"
            
            recommendations_html += f"""
            <div class="recommendation">
                <div class="recommendation-header">
                    {rec.get('action', 'Action Required')}
                    <span class="recommendation-priority {priority_class}">{rec.get('priority', 'Medium')}</span>
                </div>
                <div class="recommendation-details">
                    <strong>Description:</strong> {rec.get('description', 'No description available')}
                </div>
                <div class="recommendation-details">
                    <strong>Implementation:</strong> {rec.get('implementation', 'Implementation details not specified')}
                </div>
                <div class="recommendation-details">
                    <strong>Effort:</strong> {rec.get('effort_estimate', 'Not estimated')} | 
                    <strong>Verification:</strong> {rec.get('verification', 'Verification method not specified')}
                </div>
            </div>
            """
        
        return f"""
        <div class="recommendations-section">
            <h4>💡 Actionable Recommendations</h4>
            {recommendations_html}
        </div>
        """
    
    def _generate_compliance_forecast_section(self, scan_result: Dict[str, Any]) -> str:
        """Generate compliance forecast chart section for HTML report."""
        try:
            # Get current user from scan result
            username = scan_result.get('username', 'unknown')
            current_score = scan_result.get('compliance_score', 70)
            scan_timestamp = scan_result.get('timestamp', datetime.now().isoformat())
            
            # Safe import of predictive engine with dependencies
            try:
                from services.predictive_compliance_engine import PredictiveComplianceEngine
                from services.results_aggregator import ResultsAggregator
                engine = PredictiveComplianceEngine(region="Netherlands")
                aggregator = ResultsAggregator()
            except ImportError as e:
                logger.warning(f"Predictive compliance engine not available: {e}")
                return self._generate_fallback_forecast_section(current_score)
            
            import json
            from datetime import timedelta
            
            # Get real user scan history instead of fake data
            try:
                historical_data = aggregator.get_all_scans(username, limit=50)
                if not historical_data or len(historical_data) < 3:
                    logger.warning(f"Insufficient historical data for user {username}, using fallback")
                    return self._generate_fallback_forecast_section(current_score)
                
                # Process data through enhanced predictive engine with smoothing
                try:
                    time_series = engine._prepare_time_series_data(historical_data)
                    has_time_series = not time_series.empty
                except:
                    has_time_series = False
                    time_series = None
                    
            except Exception as e:
                logger.warning(f"Error loading user scan history: {e}, using fallback")
                return self._generate_fallback_forecast_section(current_score)
            
            # Get prediction using real smoothed data
            prediction = engine.predict_compliance_trajectory(historical_data, forecast_days=30)
            
            # Prepare data for the chart using time series data
            if has_time_series and time_series is not None:
                dates = time_series['date'].dt.strftime('%Y-%m-%d').tolist()
                raw_scores = time_series['raw_compliance_score'].tolist() if 'raw_compliance_score' in time_series.columns else []
                smoothed_scores = time_series['smoothed_compliance_score'].tolist() if 'smoothed_compliance_score' in time_series.columns else time_series['compliance_score'].tolist()
            else:
                # Fallback to basic data processing
                dates = [datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00').replace('+00:00', '')).strftime('%Y-%m-%d') for item in historical_data]
                raw_scores = [item['compliance_score'] for item in historical_data]
                smoothed_scores = raw_scores.copy()
            
            # Add prediction point
            base_date = datetime.fromisoformat(scan_timestamp.replace('Z', '+00:00').replace('+00:00', ''))
            future_date = (base_date + timedelta(days=30)).strftime('%Y-%m-%d')
            dates.append(future_date)
            if raw_scores and isinstance(raw_scores, list):
                raw_scores.append(prediction.future_score)
            if isinstance(smoothed_scores, list):
                smoothed_scores.append(prediction.future_score)
            
            # Enhanced compliance visualization: Combined bar + line + forecast with interactivity
            
            # Weekly aggregation using built-in Python (no pandas dependency)
            from collections import defaultdict
            
            weekly_data = defaultdict(list)
            scores_by_date = list(zip(dates[:-1], smoothed_scores[:-1]))
            
            # Group data points by week
            for date_str, score in scores_by_date:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    # Get Monday of the week
                    monday = date_obj - timedelta(days=date_obj.weekday())
                    week_key = monday.strftime('%Y-%m-%d')
                    weekly_data[week_key].append(score)
                except:
                    continue
            
            # Calculate weekly averages
            weekly_dates = sorted(weekly_data.keys())
            weekly_smoothed = []
            for week in weekly_dates:
                scores = weekly_data[week]
                avg_score = sum(scores) / len(scores) if scores else 0
                weekly_smoothed.append(avg_score)
            
            chart_data_series = []
            
            # 1. Weekly compliance bars (primary visualization)
            chart_data_series.append({
                'x': weekly_dates,
                'y': weekly_smoothed,
                'type': 'bar',
                'name': '📊 Weekly Compliance',
                'marker': {
                    'color': weekly_smoothed,
                    'colorscale': [
                        [0, '#F44336'],     # 0-25%: Red
                        [0.25, '#FF9800'],  # 25-50%: Orange  
                        [0.5, '#FFC107'],   # 50-75%: Amber
                        [0.75, '#8BC34A'],  # 75-90%: Light Green
                        [1, '#4CAF50']      # 90-100%: Green
                    ],
                    'cmin': 0,
                    'cmax': 100,
                    'line': {'color': 'white', 'width': 1}
                },
                'hovertemplate': '<b>Week of %{x}</b><br>Compliance: <b>%{y:.1f}%</b><br><extra></extra>',
                'opacity': 0.8
            })
            
            # 2. Trend line removed per user request
            
            # 3. Forecast center line
            chart_data_series.append({
                'x': [dates[-2], dates[-1]],
                'y': [smoothed_scores[-2], smoothed_scores[-1]],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': '🔮 AI Forecast',
                'line': {'color': '#FF6B35', 'dash': 'dash', 'width': 3},
                'marker': {'size': 12, 'color': '#FF6B35', 'line': {'width': 2, 'color': 'white'}},
                'hovertemplate': '<b>%{x}</b><br>Forecast: <b>%{y:.1f}%</b><extra></extra>'
            })
            
            # 4. Forecast confidence band (upper bound)
            chart_data_series.append({
                'x': [dates[-2], dates[-1]],
                'y': [smoothed_scores[-2], prediction.confidence_interval[1]],
                'type': 'scatter',
                'mode': 'lines',
                'name': 'Upper Confidence',
                'line': {'color': 'rgba(255, 107, 53, 0.3)', 'width': 0},
                'showlegend': False,
                'hoverinfo': 'skip'
            })
            
            # 5. Forecast confidence band (lower bound with fill)
            chart_data_series.append({
                'x': [dates[-2], dates[-1]],
                'y': [smoothed_scores[-2], prediction.confidence_interval[0]],
                'type': 'scatter',
                'mode': 'lines',
                'name': 'Confidence Band',
                'line': {'color': 'rgba(255, 107, 53, 0.3)', 'width': 0},
                'fill': 'tonexty',
                'fillcolor': 'rgba(255, 107, 53, 0.2)',
                'hovertemplate': '<b>Confidence Range</b><br>%{x}: %{y:.1f}%<extra></extra>'
            })
            
            chart_data = {
                'data': chart_data_series,
                'layout': {
                    'title': {
                        'text': '📊 Interactive Compliance Forecast & Trends',
                        'font': {'size': 20, 'color': '#333', 'family': 'Arial, sans-serif'},
                        'x': 0.5
                    },
                    'xaxis': {
                        'title': 'Timeline',
                        'showgrid': True,
                        'gridwidth': 0.5,
                        'gridcolor': 'rgba(0,0,0,0.1)',
                        'showline': True,
                        'linecolor': 'rgba(0,0,0,0.2)',
                        'rangeslider': {'visible': True, 'thickness': 0.05},
                        'rangeselector': {
                            'buttons': [
                                {'count': 30, 'label': '30D', 'step': 'day', 'stepmode': 'backward'},
                                {'count': 90, 'label': '90D', 'step': 'day', 'stepmode': 'backward'},
                                {'step': 'all', 'label': 'All'}
                            ],
                            'y': 1.1
                        }
                    },
                    'yaxis': {
                        'title': 'Compliance Score (%)',
                        'range': [0, 100],
                        'showgrid': True,
                        'gridwidth': 0.5,
                        'gridcolor': 'rgba(0,0,0,0.1)',
                        'ticksuffix': '%',
                        'showline': True,
                        'linecolor': 'rgba(0,0,0,0.2)',
                        'fixedrange': False
                    },
                    'plot_bgcolor': 'white',
                    'paper_bgcolor': 'white',
                    'shapes': [
                        # Risk zone background shading (professional colors)
                        {'type': 'rect', 'x0': weekly_dates[0] if weekly_dates else dates[0], 'x1': dates[-1], 'y0': 90, 'y1': 100, 
                         'fillcolor': 'rgba(76, 175, 80, 0.1)', 'line': {'width': 0}, 'layer': 'below'},
                        {'type': 'rect', 'x0': weekly_dates[0] if weekly_dates else dates[0], 'x1': dates[-1], 'y0': 75, 'y1': 90, 
                         'fillcolor': 'rgba(139, 195, 74, 0.08)', 'line': {'width': 0}, 'layer': 'below'},
                        {'type': 'rect', 'x0': weekly_dates[0] if weekly_dates else dates[0], 'x1': dates[-1], 'y0': 50, 'y1': 75, 
                         'fillcolor': 'rgba(255, 193, 7, 0.08)', 'line': {'width': 0}, 'layer': 'below'},
                        {'type': 'rect', 'x0': weekly_dates[0] if weekly_dates else dates[0], 'x1': dates[-1], 'y0': 0, 'y1': 50, 
                         'fillcolor': 'rgba(244, 67, 54, 0.08)', 'line': {'width': 0}, 'layer': 'below'},
                        # Reference lines (industry benchmarks)
                        {'type': 'line', 'x0': weekly_dates[0] if weekly_dates else dates[0], 'x1': dates[-1], 'y0': 90, 'y1': 90, 
                         'line': {'dash': 'dash', 'color': 'rgba(76, 175, 80, 0.7)', 'width': 2}},
                        {'type': 'line', 'x0': weekly_dates[0] if weekly_dates else dates[0], 'x1': dates[-1], 'y0': 75, 'y1': 75, 
                         'line': {'dash': 'dash', 'color': 'rgba(255, 193, 7, 0.7)', 'width': 2}},
                        {'type': 'line', 'x0': weekly_dates[0] if weekly_dates else dates[0], 'x1': dates[-1], 'y0': 50, 'y1': 50, 
                         'line': {'dash': 'dash', 'color': 'rgba(244, 67, 54, 0.7)', 'width': 2}}
                    ],
                    'annotations': [
                        {'x': dates[-1], 'y': 95, 'text': 'Excellent (90%+)', 'showarrow': False, 'xanchor': 'left',
                         'font': {'size': 11, 'color': '#4CAF50', 'family': 'Arial'}, 'bgcolor': 'rgba(255,255,255,0.9)'},
                        {'x': dates[-1], 'y': 82, 'text': 'Good (75-90%)', 'showarrow': False, 'xanchor': 'left',
                         'font': {'size': 11, 'color': '#8BC34A', 'family': 'Arial'}, 'bgcolor': 'rgba(255,255,255,0.9)'},
                        {'x': dates[-1], 'y': 62, 'text': 'Attention Needed (50-75%)', 'showarrow': False, 'xanchor': 'left',
                         'font': {'size': 11, 'color': '#FF9800', 'family': 'Arial'}, 'bgcolor': 'rgba(255,255,255,0.9)'},
                        {'x': dates[-1], 'y': 25, 'text': 'Critical (<50%)', 'showarrow': False, 'xanchor': 'left',
                         'font': {'size': 11, 'color': '#F44336', 'family': 'Arial'}, 'bgcolor': 'rgba(255,255,255,0.9)'}
                    ],
                    'updatemenus': [{
                        'type': 'buttons',
                        'direction': 'left',
                        'buttons': [
                            {'label': 'Bar + Trend', 'method': 'restyle', 'args': [{'visible': [True, True, True, True, True]}]},
                            {'label': 'Trend Only', 'method': 'restyle', 'args': [{'visible': [False, True, True, True, True]}]},
                            {'label': 'Bars Only', 'method': 'restyle', 'args': [{'visible': [True, False, True, True, True]}]}
                        ],
                        'x': 0,
                        'y': 1.15,
                        'xanchor': 'left',
                        'yanchor': 'top'
                    }],
                    'legend': {
                        'orientation': 'h',
                        'yanchor': 'bottom',
                        'y': 1.02,
                        'xanchor': 'center',
                        'x': 0.5,
                        'font': {'size': 12, 'family': 'Arial'},
                        'bgcolor': 'rgba(255,255,255,0.8)'
                    },
                    'height': 500,
                    'margin': {'t': 120, 'b': 80, 'l': 80, 'r': 80},
                    'hovermode': 'x unified'
                },
                'config': {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToAdd': ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
                    'modeBarButtonsToRemove': ['resetScale2d'],
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': 'compliance_forecast',
                        'height': 500,
                        'width': 1000,
                        'scale': 2
                    }
                }
            }
            
            # Convert to JSON for embedding
            chart_json = json.dumps(chart_data)
            
            # Determine trend based on smoothed data (more reliable than raw)
            if len(smoothed_scores) >= 2:
                trend_direction = "↗️" if smoothed_scores[-1] > smoothed_scores[-2] else "↘️" if smoothed_scores[-1] < smoothed_scores[-2] else "→"
                trend_text = "Improving" if smoothed_scores[-1] > smoothed_scores[-2] else "Declining" if smoothed_scores[-1] < smoothed_scores[-2] else "Stable"
                trend_class = "trend-improving" if smoothed_scores[-1] > smoothed_scores[-2] else "trend-declining" if smoothed_scores[-1] < smoothed_scores[-2] else "trend-stable"
            else:
                trend_direction = "→"
                trend_text = "Stable"
                trend_class = "trend-stable"
            
            return f"""
            <div class="compliance-forecast-section">
                <h2>📈 Compliance Score Forecast</h2>
                <div class="forecast-summary">
                    <div class="forecast-metric">
                        <span class="metric-value">{prediction.future_score:.1f}%</span>
                        <span class="metric-label">🔮 AI Predicted Score (30 days)</span>
                    </div>
                    <div class="forecast-metric">
                        <span class="metric-value {trend_class}">{trend_direction} {trend_text}</span>
                        <span class="metric-label">📈 Trend Analysis</span>
                    </div>
                    <div class="forecast-metric">
                        <span class="metric-value">{prediction.confidence_interval[0]:.1f}% - {prediction.confidence_interval[1]:.1f}%</span>
                        <span class="metric-label">📊 Confidence Range</span>
                    </div>
                </div>
                <div id="compliance-forecast-chart"></div>
                <script>
                    var chartData = {chart_json};
                    var config = {{
                        responsive: true,
                        displayModeBar: false,
                        displaylogo: false
                    }};
                    Plotly.newPlot('compliance-forecast-chart', chartData.data, chartData.layout, config);
                </script>
                
                <div class="forecast-explanation">
                    <h4>📊 Understanding Your Interactive Compliance Dashboard</h4>
                    <div class="explanation-grid">
                        <div class="explanation-item">
                            <strong>📊 Weekly Compliance Bars:</strong> Color-coded weekly averages showing your compliance levels<br>
                            <strong>📈 Trend Line:</strong> Smoothed trend analysis overlaid for pattern recognition (blue line)
                        </div>
                        <div class="explanation-item">
                            <strong>🔮 AI Forecast:</strong> Machine learning forecast with confidence bands (orange dashed line)<br>
                            <strong>🎛️ Interactive Controls:</strong> Use buttons to switch views, drag timeline, hover for details
                        </div>
                        <div class="explanation-item">
                            <strong>🏢 Industry Benchmarks:</strong> Dotted lines showing average scores for Financial Services and Technology sectors
                        </div>
                        <div class="explanation-item">
                            <strong>🚨 Risk Zones:</strong> Color-coded background areas indicating compliance health levels
                        </div>
                    </div>
                    
                    <div class="risk-zone-guide">
                        <h5>Risk Zone Guide:</h5>
                        <ul>
                            <li><span style="color: green;">🟢 Excellent (90%+):</span> Outstanding compliance posture</li>
                            <li><span style="color: orange;">🟡 Good (80-89%):</span> Solid compliance with minor improvements needed</li>
                            <li><span style="color: red;">🟠 Needs Attention (70-79%):</span> Moderate risk requiring focused action</li>
                            <li><span style="color: darkred;">🔴 Critical (&lt;60%):</span> High risk requiring immediate intervention</li>
                        </ul>
                    </div>
                </div>
            </div>
            """
            
        except Exception as e:
            logger.error(f"Error generating compliance forecast section: {str(e)}")
            return self._generate_fallback_forecast_section(scan_result.get('compliance_score', 70))
    
    def _generate_fallback_forecast_section(self, current_score: float) -> str:
        """Generate a fallback forecast section when full prediction is unavailable."""
        return f"""
        <div class="compliance-forecast-section">
            <h2>🎯 Compliance Score Analysis</h2>
            <div class="forecast-summary">
                <div class="forecast-metric">
                    <span class="metric-value">{current_score:.1f}%</span>
                    <span class="metric-label">📊 Current Compliance Score</span>
                </div>
                <div class="forecast-metric">
                    <span class="metric-value">{'🟢 Excellent' if current_score >= 90 else '🟡 Good' if current_score >= 80 else '🟠 Attention' if current_score >= 70 else '🔴 Critical'}</span>
                    <span class="metric-label">🚨 Risk Level</span>
                </div>
                <div class="forecast-metric">
                    <span class="metric-value">{'Financial Services: 78.5%' if current_score < 78.5 else 'Technology: 81.2%'}</span>
                    <span class="metric-label">🏢 Industry Benchmark</span>
                </div>
            </div>
            
            <div class="forecast-explanation">
                <h4>📊 Compliance Score Analysis</h4>
                <div class="explanation-grid">
                    <div class="explanation-item">
                        <strong>📊 Current Status:</strong> Your compliance score of {current_score:.1f}% indicates {'excellent' if current_score >= 90 else 'good' if current_score >= 80 else 'moderate' if current_score >= 70 else 'critical'} compliance posture.
                    </div>
                    <div class="explanation-item">
                        <strong>🏢 Industry Comparison:</strong> {'Above average' if current_score > 80 else 'Below average' if current_score < 75 else 'Average'} compared to industry benchmarks.
                    </div>
                    <div class="explanation-item">
                        <strong>📈 Recommendations:</strong> {'Continue current practices' if current_score >= 85 else 'Focus on addressing critical findings' if current_score < 70 else 'Implement systematic improvements'}.
                    </div>
                </div>
            </div>
            
            <p style="text-align: center; color: #666; font-style: italic; margin-top: 20px;">
                💡 <strong>Pro Tip:</strong> Advanced AI-powered compliance forecasting is available with full system dependencies installed.
            </p>
        </div>
        """

    def _generate_ai_model_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate AI model-specific compliance content with comprehensive EU AI Act coverage."""
        model_framework = scan_result.get('model_framework', 'Unknown')
        ai_act_compliance = scan_result.get('ai_act_compliance', 'Not assessed')
        coverage_version = scan_result.get('coverage_version', '')
        compliance_score = scan_result.get('compliance_score', scan_result.get('ai_model_compliance', 0))
        
        # Extract articles_covered properly - it's a dictionary with stats
        articles_covered_dict = scan_result.get('articles_covered', {})
        if isinstance(articles_covered_dict, dict):
            articles_covered = articles_covered_dict.get('articles_checked', [])
            article_count = articles_covered_dict.get('article_count', len(articles_covered))
            coverage_pct = articles_covered_dict.get('coverage_percentage', 0)
        else:
            articles_covered = []
            article_count = 0
            coverage_pct = 0
        
        # Build comprehensive coverage section if available
        comprehensive_html = ""
        if coverage_version and '2.0' in str(coverage_version):
            # Get Phase 2-10 data
            annex_iii = scan_result.get('annex_iii_classification', {})
            transparency = scan_result.get('transparency_compliance', {})
            provider_deployer = scan_result.get('provider_deployer_obligations', {})
            conformity = scan_result.get('conformity_assessment', {})
            gpai = scan_result.get('gpai_compliance', {})
            post_market = scan_result.get('post_market_monitoring', {})
            ai_literacy = scan_result.get('ai_literacy', {})
            enforcement = scan_result.get('enforcement_rights', {})
            governance = scan_result.get('governance_structures', {})
            
            phase_cards = ""
            phases = [
                ("Annex III Classification", annex_iii),
                ("Transparency (Art. 50)", transparency),
                ("Provider/Deployer Obligations", provider_deployer),
                ("Conformity Assessment", conformity),
                ("GPAI Compliance (Art. 52-56)", gpai),
                ("Post-Market Monitoring", post_market),
                ("AI Literacy (Art. 4)", ai_literacy),
                ("Enforcement & Rights", enforcement),
                ("Governance Structures", governance)
            ]
            
            for title, phase_data in phases:
                if phase_data:
                    # Determine status and display text
                    is_compliant = phase_data.get('compliant', phase_data.get('is_compliant', False))
                    is_applicable = phase_data.get('applicable', phase_data.get('is_applicable', True))
                    compliance_pct = phase_data.get('compliance_percentage', 0)
                    
                    # Choose icon and display based on data available
                    if compliance_pct > 0:
                        if compliance_pct >= 80:
                            icon, color, display = '✅', '#10b981', f'{compliance_pct}% Compliant'
                        elif compliance_pct >= 50:
                            icon, color, display = '⚠️', '#f59e0b', f'{compliance_pct}% Partial'
                        else:
                            icon, color, display = '🔍', '#ef4444', f'{compliance_pct}% Coverage'
                    elif is_compliant:
                        icon, color, display = '✅', '#10b981', 'Assessed'
                    elif not is_applicable:
                        icon, color, display = '➖', '#9ca3af', 'Not Applicable'
                    else:
                        icon, color, display = '🔍', '#6366f1', 'Analyzed'
                    
                    phase_cards += f"""
                    <div class="metric-card" style="border-left: 4px solid {color};">
                        <div class="metric-value" style="font-size: 14px;">{icon} {display}</div>
                        <div class="metric-label" style="font-size: 11px;">{title}</div>
                    </div>
                    """
            
            # Format articles display safely
            if articles_covered:
                articles_preview = ', '.join(map(str, articles_covered[:15]))
                articles_suffix = "..." if len(articles_covered) > 15 else ""
                articles_display = f"{article_count} articles ({coverage_pct}% coverage): {articles_preview}{articles_suffix}"
            else:
                articles_display = "Multiple EU AI Act articles analyzed"
            
            comprehensive_html = f"""
            <div class="info-box success" style="margin-top: 20px; background: #f0fdf4; border: 2px solid #10b981; padding: 20px; border-radius: 8px;">
                <h3 style="color: #065f46; margin-bottom: 15px;">🎯 Comprehensive EU AI Act 2025 Coverage ({coverage_version})</h3>
                <p style="margin-bottom: 15px;"><strong>Articles Analyzed:</strong> {articles_display}</p>
                <div class="metrics-grid">
                    {phase_cards}
                </div>
            </div>
            """
        
        return f"""
        <div class="scanner-specific">
            <h2>🤖 {t_report('ai_model_compliance', 'AI Model Compliance')}</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{model_framework}</div>
                    <div class="metric-label">Model Framework</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{ai_act_compliance}</div>
                    <div class="metric-label">AI Act 2025 Status</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{compliance_score}%</div>
                    <div class="metric-label">Compliance Score</div>
                </div>
            </div>
            {comprehensive_html}
        </div>
        """
    
    def _generate_dpia_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate DPIA-specific content."""
        risk_score = scan_result.get('risk_score', 'Unknown')
        overall_risk_level = scan_result.get('overall_risk_level', 'Unknown')
        
        return f"""
        <div class="scanner-specific">
            <h2>⚖️ {t_report('dpia_assessment', 'DPIA Assessment')}</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{risk_score}</div>
                    <div class="metric-label">Risk Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{overall_risk_level}</div>
                    <div class="metric-label">Risk Level</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_footer(self, scan_id: str, timestamp: str) -> str:
        """Generate report footer."""
        return f"""
        <div class="footer">
            <p>{t_report('generated_by', 'Generated by')} {t_report('dataGuardian_pro', 'DataGuardian Pro')} - {t_report('privacy_compliance_platform', 'Enterprise Privacy & Sustainability Compliance Platform')}</p>
            <p>Report ID: {scan_id} | {t_report('generated_on', 'Generated')}: {timestamp}</p>
        </div>
        """

# Global instance for unified report generation
_unified_generator = None

def get_unified_generator() -> UnifiedHTMLReportGenerator:
    """Get the global unified HTML report generator."""
    global _unified_generator
    if _unified_generator is None:
        _unified_generator = UnifiedHTMLReportGenerator()
    return _unified_generator

def generate_unified_html_report(scan_result: Dict[str, Any]) -> str:
    """
    Generate a unified HTML report using the global generator.
    
    Args:
        scan_result: Scan result data
        
    Returns:
        Complete HTML report as string
    """
    generator = get_unified_generator()
    return generator.generate_html_report(scan_result)

def generate_unified_html_report(scan_result: Dict[str, Any]) -> str:
    """
    Generate a unified HTML report using the global generator.
    
    Args:
        scan_result: Scan result data
        
    Returns:
        Complete HTML report as string
    """
    generator = get_unified_generator()
    return generator.generate_html_report(scan_result)

def generate_comprehensive_report(scan_result: Dict[str, Any]) -> str:
    """
    Generate a comprehensive HTML report (alias for backward compatibility).
    
    Args:
        scan_result: Scan result data
        
    Returns:
        Complete HTML report as string
    """
    return generate_unified_html_report(scan_result)