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
        """Update current language from user's session state selection."""
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
        
        # Deduplicate findings first (prevents duplicate violations in reports)
        original_findings = scan_result.get('findings', [])
        seen_findings = set()
        deduplicated_findings = []
        for finding in original_findings:
            # Create unique key from location and description
            location = finding.get('location', finding.get('file', ''))
            if not location and finding.get('file'):
                line = finding.get('line', 0)
                location = f"{finding.get('file')}:{line}" if line else finding.get('file')
            description = finding.get('description', '')
            key = (location, description)
            if key not in seen_findings:
                seen_findings.add(key)
                deduplicated_findings.append(finding)
        
        # Create copy of scan_result with deduplicated findings for metrics
        scan_result_deduped = scan_result.copy()
        scan_result_deduped['findings'] = deduplicated_findings
        
        # Extract metrics using deduplicated findings
        metrics = self._extract_metrics(scan_result_deduped)
        
        # Enhance findings with specific context and actionable recommendations
        enhanced_findings = enhance_findings_for_report(
            scanner_type=scan_type.lower().replace(' ', '_'),
            findings=deduplicated_findings,
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
        
        findings = scan_result.get('findings', [])
        
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
            'total_findings': len(findings),
            'critical_count': len([f for f in findings if str(f.get('severity', '')).lower() == 'critical' or str(f.get('risk_level', '')).lower() == 'critical']),
            'high_risk_count': (
                summary.get('high_risk_count') or 
                scan_result.get('high_risk_count') or
                len([f for f in findings if str(f.get('severity', '')).lower() == 'high' or str(f.get('risk_level', '')).lower() == 'high'])
            ),
            'medium_risk_count': (
                summary.get('medium_risk_count') or 
                scan_result.get('medium_risk_count') or
                len([f for f in findings if str(f.get('severity', '')).lower() == 'medium' or str(f.get('risk_level', '')).lower() == 'medium'])
            ),
            'low_risk_count': (
                summary.get('low_risk_count') or 
                scan_result.get('low_risk_count') or
                len([f for f in findings if str(f.get('severity', '')).lower() == 'low' or str(f.get('risk_level', '')).lower() == 'low'])
            ),
            'compliance_score': self._get_compliance_score(scan_result, summary, findings)
        }
        
        return metrics
    
    def _get_compliance_score(self, scan_result: Dict[str, Any], summary: Dict[str, Any], findings: list) -> int:
        """Get compliance score from scan result, or calculate if not provided.
        
        The scanner is the authoritative source for compliance scores. 
        Only calculate here if no score was provided by the scanner.
        Minimum score is 10% to remain actionable (never show 0%).
        If scanner reports 100% but there are high/critical findings, recalculate.
        """
        # Get existing score from scanner (authoritative source)
        existing_score = summary.get('overall_compliance_score')
        if existing_score is None:
            existing_score = scan_result.get('compliance_score')
        
        # Check if there are high-risk or critical findings
        high_risk_findings = [f for f in findings if str(f.get('severity', f.get('risk_level', ''))).lower() in ('critical', 'high')]
        
        # If scanner reports 100% but there are high/critical findings, recalculate
        # This catches cases where scanners don't properly penalize for findings
        if existing_score is not None and existing_score >= 100 and len(high_risk_findings) > 0:
            return self._calculate_compliance_score(scan_result)
        
        # If scanner provided a score, use it (but enforce minimum 10%)
        if existing_score is not None:
            score = int(round(existing_score))
            return max(10, score) if score < 10 and len(findings) > 0 else max(0, min(100, score))
        
        # Only calculate if no score was provided
        return self._calculate_compliance_score(scan_result)
    
    def _calculate_compliance_score(self, scan_result: Dict[str, Any]) -> int:
        """Calculate compliance score based on findings using hybrid approach.
        
        For compliance scans (SOC2, NIS2, GDPR), individual high-risk findings 
        significantly impact compliance posture regardless of file count.
        
        Scoring approach:
        - Base score: 100
        - Critical findings: -15 points each (max -60)
        - High findings: -10 points each (max -40)
        - Medium findings: -5 points each (max -25)
        - Low findings: -2 points each (max -10)
        - Minimum score: 10% (never 0%) to remain actionable
        """
        findings = scan_result.get('findings', [])
        
        if not findings:
            return 100
        
        # Count severity levels (check both severity and risk_level)
        critical = 0
        high = 0
        medium = 0
        low = 0
        
        for f in findings:
            severity = str(f.get('severity', f.get('risk_level', 'medium'))).lower()
            if severity == 'critical':
                critical += 1
            elif severity == 'high':
                high += 1
            elif severity == 'medium':
                medium += 1
            else:
                low += 1
        
        # Direct penalty approach - compliance findings are significant
        score = 100.0
        
        # Apply capped penalties per severity level
        critical_penalty = min(60, critical * 15)
        high_penalty = min(40, high * 10)
        medium_penalty = min(25, medium * 5)
        low_penalty = min(10, low * 2)
        
        score -= (critical_penalty + high_penalty + medium_penalty + low_penalty)
        
        # Minimum score is 10% (never 0%) to remain actionable
        score = max(10, min(100, score))
        
        return int(score)
    
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
    
    def _deduplicate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate findings based on article reference and description."""
        seen = set()
        deduplicated = []
        
        for finding in findings:
            article_ref = finding.get('article_reference', finding.get('location', ''))
            description = finding.get('description', finding.get('title', ''))
            finding_type = finding.get('type', '')
            
            key = f"{article_ref}|{description[:100]}|{finding_type}"
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(finding)
        
        return deduplicated
    
    def _generate_findings_html(self, findings: List[Dict[str, Any]]) -> str:
        """Generate HTML for enhanced findings list with actionable recommendations."""
        if not findings:
            return f"<p>✅ {t_report('no_issues_found', 'No issues found in the analysis.')}</p>"
        
        findings = self._deduplicate_findings(findings)
        
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
            
            # Get source file information
            import os
            source_path = finding.get('source', finding.get('source_file', ''))
            source_file = os.path.basename(source_path) if source_path else ''
            
            # Enhanced finding fields
            context = finding.get('context', '')
            business_impact = finding.get('business_impact', '')
            gdpr_articles = finding.get('gdpr_articles', [])
            compliance_requirements = finding.get('compliance_requirements', [])
            recommendations = finding.get('recommendations', [])
            remediation_priority = finding.get('remediation_priority', '')
            estimated_effort = finding.get('estimated_effort', '')
            data_classification = finding.get('data_classification', '')
            
            # SOC2/NIS2 specific fields (check both field names for compatibility)
            tsc_criteria = finding.get('tsc_criteria', finding.get('soc2_tsc_criteria', []))
            nis2_articles = finding.get('nis2_articles', [])
            
            # Build enhanced finding HTML
            findings_html += f"""
            <div class="finding enhanced-finding {severity}">
                <div class="finding-header">
                    <span class="finding-type">{finding_type}</span>
                    <span class="finding-severity severity-{severity}">{finding.get('severity', finding.get('risk_level', 'Low'))}</span>
                </div>
                
                <div class="finding-content">
                    {f'<div class="finding-source" style="margin-bottom: 10px;"><strong>📄 Source File:</strong> <code style="background: #f8f9fa; padding: 2px 8px; border-radius: 4px;">{source_file}</code></div>' if source_file else ''}
                    
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
                    
                    {self._generate_penalty_info(finding)}
                    
                    {self._generate_compliance_section(gdpr_articles, compliance_requirements, tsc_criteria, nis2_articles)}
                    
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
            
            # Extract filename from source path
            import os
            source_path = finding.get('source', '')
            source = os.path.basename(source_path) if source_path else 'Unknown'
            if not source or source == '':
                source = 'Uploaded Image'
            
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
            
            # Determine detection status based on score
            if overall_score >= 0.6:
                detection_title = "🎭 Synthetic Media Detected - High Confidence"
                detection_context = context if context else f"High likelihood ({overall_score:.1%}) of AI-generated or manipulated content detected through multi-factor analysis."
            elif overall_score >= 0.4:
                detection_title = "🎭 Potential Synthetic Media"
                detection_context = context if context else f"Moderate indicators ({overall_score:.1%}) suggest possible AI-generated content. Further verification recommended."
            elif overall_score >= 0.2:
                detection_title = "🎭 Synthetic Media Indicators"
                detection_context = context if context else f"Some indicators ({overall_score:.1%}) of potential synthetic content. Review recommended."
            else:
                detection_title = "🎭 Low Synthetic Indicators"
                detection_context = context if context else "Minimal indicators detected. Image appears authentic but was flagged for review."
            
            # Generate default recommendation if missing
            if not recommendation:
                recommendation = "(1) Verify content authenticity with source, (2) Add AI disclosure labels if confirmed synthetic, (3) Document verification in compliance records"
            
            section_html += f"""
            <div class="deepfake-finding" style="background: white; border: 2px solid {severity_color}; padding: 20px; margin: 15px 0; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: {severity_color};">
                        {detection_title}
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
                    <p style="margin: 10px 0 5px 0;">{detection_context}</p>
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
                    <p style="margin: 10px 0; font-size: 0.9em; color: #495057;">{reason if reason else 'EU AI Act Article 50(2) requires transparency labeling for AI-generated content to prevent misinformation and protect user rights.'}</p>
                    
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
    
    def _generate_penalty_info(self, finding: Dict[str, Any]) -> str:
        """Generate HTML for EU AI Act penalty information based on finding severity and type."""
        finding_type = finding.get('type', '').lower()
        severity = finding.get('severity', 'Medium').lower()
        article_ref = finding.get('article_reference', finding.get('location', '')).lower()
        
        penalty_html = ""
        
        if 'prohibited' in finding_type or 'article 5' in article_ref or severity == 'critical':
            penalty_html = """
            <div class="penalty-info" style="background: #fee2e2; border-left: 4px solid #dc2626; padding: 12px; margin: 10px 0; border-radius: 4px;">
                <strong style="color: #991b1b;">⚠️ Penalty Risk - Tier 1 (Prohibited Practices):</strong>
                <span style="color: #b91c1c; font-weight: 600;">Up to €35 million or 7% of global annual turnover</span>
            </div>
            """
        elif 'high_risk' in finding_type or 'gpai' in finding_type or severity == 'high' or any(x in article_ref for x in ['article 6', 'article 9', 'article 10', 'article 51', 'article 52']):
            penalty_html = """
            <div class="penalty-info" style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 10px 0; border-radius: 4px;">
                <strong style="color: #92400e;">⚠️ Penalty Risk - Tier 2 (High-Risk/GPAI Requirements):</strong>
                <span style="color: #b45309; font-weight: 600;">Up to €15 million or 3% of global annual turnover</span>
            </div>
            """
        elif 'ai_act' in finding_type or 'eu ai' in article_ref.lower():
            penalty_html = """
            <div class="penalty-info" style="background: #dbeafe; border-left: 4px solid #3b82f6; padding: 12px; margin: 10px 0; border-radius: 4px;">
                <strong style="color: #1e40af;">ℹ️ Penalty Risk - Tier 3 (Other Violations):</strong>
                <span style="color: #1d4ed8; font-weight: 600;">Up to €7.5 million or 1.5% of global annual turnover</span>
            </div>
            """
        
        return penalty_html
    
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
        elif 'document' in scan_type:
            return self._generate_document_scanner_content(scan_result)
        elif 'image' in scan_type:
            return self._generate_image_scanner_content(scan_result)
        elif 'exact' in scan_type:
            return self._generate_exact_online_content(scan_result)
        else:
            return ""
    
    def _generate_document_scanner_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate document scanner specific content with fraud detection analysis."""
        content_html = ""
        
        document_results = scan_result.get('document_results', [])
        
        fraud_detected_count = 0
        high_risk_fraud_count = 0
        fraud_docs = []
        
        for doc in document_results:
            fraud_analysis = doc.get('fraud_analysis', {})
            if fraud_analysis and fraud_analysis.get('ai_generated_risk', 0) > 0:
                fraud_detected_count += 1
                if fraud_analysis.get('risk_level') in ['High', 'Critical']:
                    high_risk_fraud_count += 1
                fraud_docs.append({
                    'file_name': doc.get('file_name', 'Unknown'),
                    'fraud_analysis': fraud_analysis
                })
        
        if fraud_docs:
            content_html += f"""
            <div class="fraud-section" style="background: #fff3cd; border-left: 5px solid #dc3545; padding: 20px; margin: 20px 0; border-radius: 8px;">
                <h3 style="color: #c92a2a; margin-top: 0;">
                    🚨 {t_report('ai_fraud_detection', 'AI Document Fraud Detection')}
                    <span style="font-size: 0.8em; color: #e67700;">(EU AI Act Article 50)</span>
                </h3>
                <p style="margin: 10px 0; font-size: 0.95em; color: #555;">
                    {t_report('fraud_intro', 'Automated detection of AI-generated or tampered documents requiring verification under EU AI Act 2025 transparency obligations.')}
                </p>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0;">
                    <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2em; color: #495057;">{len(document_results)}</div>
                        <div style="color: #6c757d;">Documents Scanned</div>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2em; color: #e67700;">{fraud_detected_count}</div>
                        <div style="color: #6c757d;">AI Indicators Found</div>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2em; color: #c92a2a;">{high_risk_fraud_count}</div>
                        <div style="color: #6c757d;">High Risk Documents</div>
                    </div>
                </div>
            """
            
            for doc in fraud_docs:
                fraud = doc['fraud_analysis']
                risk_level = fraud.get('risk_level', 'Medium')
                ai_risk = fraud.get('ai_generated_risk', 0)
                confidence = fraud.get('confidence', 0)
                ai_model = fraud.get('ai_model', 'Unknown')
                indicators = fraud.get('fraud_indicators', [])
                recommendations = fraud.get('recommendations', [])
                
                risk_colors = {
                    'Critical': '#c92a2a',
                    'High': '#e67700',
                    'Medium': '#f59f00',
                    'Low': '#37b24d'
                }
                risk_color = risk_colors.get(risk_level, '#868e96')
                
                content_html += f"""
                <div class="fraud-finding" style="background: white; border: 2px solid {risk_color}; padding: 20px; margin: 15px 0; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <h4 style="margin: 0; color: #495057;">
                            📄 {doc['file_name']}
                        </h4>
                        <span style="background: {risk_color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">
                            {risk_level} Risk
                        </span>
                    </div>
                    
                    <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                            <div>
                                <strong>AI Generated Risk:</strong>
                                <div style="color: {risk_color}; font-size: 1.5em; font-weight: bold;">{ai_risk:.0%}</div>
                            </div>
                            <div>
                                <strong>Detection Confidence:</strong>
                                <div style="color: #495057; font-size: 1.5em; font-weight: bold;">{confidence:.1f}%</div>
                            </div>
                            <div>
                                <strong>Suspected Model:</strong>
                                <div style="color: #495057; font-size: 1.2em; font-weight: bold;">{ai_model}</div>
                            </div>
                        </div>
                    </div>
                """
                
                if indicators:
                    content_html += """
                    <div style="margin: 15px 0;">
                        <strong>🔍 Detection Indicators:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                    """
                    for ind in indicators:
                        if ind.get('score', 0) > 0:
                            ind_type = ind.get('type', '').replace('_', ' ').title()
                            ind_score = ind.get('score', 0)
                            ind_details = ind.get('details', '')
                            content_html += f"""
                            <li style="margin: 5px 0;">
                                <strong>{ind_type}:</strong> {ind_score:.0%} - {ind_details}
                            </li>
                            """
                    content_html += "</ul></div>"
                
                if recommendations:
                    content_html += """
                    <div style="margin: 15px 0; padding: 12px; background: #e7f5ff; border-left: 4px solid #1c7ed6; border-radius: 4px;">
                        <strong style="color: #1864ab;">📋 Recommended Actions:</strong>
                        <ul style="margin: 8px 0; padding-left: 20px;">
                    """
                    for rec in recommendations[:3]:
                        content_html += f"<li style='margin: 5px 0;'>{rec}</li>"
                    content_html += "</ul></div>"
                
                content_html += "</div>"
            
            content_html += "</div>"
        
        return content_html
    
    def _generate_image_scanner_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate image scanner specific content."""
        return ""
    
    def _generate_enterprise_connector_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate enterprise connector-specific metrics and Netherlands compliance."""
        connector_name = scan_result.get('connector_name', 'Unknown')
        connector_metrics = scan_result.get('connector_metrics', {})
        netherlands_findings = scan_result.get('netherlands_findings', {})
        uavg_compliance = scan_result.get('uavg_compliance', {})
        
        # Metric labels for display
        metric_labels = {
            'sharepoint_sites': 'SharePoint Sites',
            'onedrive_files': 'OneDrive Files',
            'exchange_emails': 'Exchange Emails',
            'teams_messages': 'Teams Messages',
            'office_documents': 'Office Documents',
            'drive_files': 'Drive Files',
            'gmail_messages': 'Gmail Messages',
            'docs_sheets': 'Docs/Sheets',
            'calendar_events': 'Calendar Events',
            'customers': 'Customers',
            'employees': 'Employees',
            'financial_records': 'Financial Records',
            'invoices': 'Invoices',
            'projects': 'Projects',
            'hr_records_scanned': 'HR Records',
            'customer_records_scanned': 'Customer Records',
            'vendor_records_scanned': 'Vendor Records',
            'bsn_instances_found': 'BSN Instances',
            'financial_data_found': 'Financial Data',
            'accounts_scanned': 'Accounts',
            'contacts_scanned': 'Contacts',
            'leads_scanned': 'Leads',
            'custom_objects_scanned': 'Custom Objects',
            'items_processed': 'Items Processed',
        }
        
        # Build connector metrics section dynamically
        metrics_html = ""
        if connector_metrics:
            # Filter non-zero numeric metrics only (skip lists/dicts)
            non_zero_metrics = {k: v for k, v in connector_metrics.items() if isinstance(v, (int, float)) and v > 0}
            
            if non_zero_metrics:
                metric_cards = ""
                for key, value in non_zero_metrics.items():
                    label = metric_labels.get(key, key.replace('_', ' ').title())
                    metric_cards += f"""
                    <div class="metric-card">
                        <div class="metric-value">{value:,}</div>
                        <div class="metric-label">{label}</div>
                    </div>
                    """
                
                metrics_html = f"""
                <div class="scanner-specific">
                    <h3>📊 {connector_name} Scan Metrics</h3>
                    <div class="metrics-grid">
                        {metric_cards}
                    </div>
                </div>
                """
        
        # Build Netherlands-specific findings section
        netherlands_html = ""
        # Helper function to safely get numeric value (handles lists)
        def safe_numeric(value, default=0):
            if isinstance(value, list):
                return len(value)
            if isinstance(value, (int, float)):
                return value
            return default
        
        # Extract values safely
        bsn_count = safe_numeric(netherlands_findings.get('bsn_fields_found', 0)) if netherlands_findings else 0
        kvk_count = safe_numeric(netherlands_findings.get('kvk_fields_found', 0)) if netherlands_findings else 0
        iban_count = safe_numeric(netherlands_findings.get('iban_fields_found', 0)) if netherlands_findings else 0
        uavg_count = safe_numeric(netherlands_findings.get('uavg_violations', 0)) if netherlands_findings else 0
        
        if netherlands_findings and any(isinstance(v, (int, float)) and v > 0 or isinstance(v, list) and len(v) > 0 for v in netherlands_findings.values()):
            netherlands_html = f"""
            <div class="scanner-specific" style="background: linear-gradient(135deg, #fff7e6 0%, #ffe4b5 100%); border-left: 4px solid #ff9800;">
                <h3>🇳🇱 Netherlands-Specific PII Findings</h3>
                <div class="metrics-grid">
                    <div class="metric-card" style="background: {'#ffebee' if bsn_count > 0 else '#e8f5e9'};">
                        <div class="metric-value" style="color: {'#c62828' if bsn_count > 0 else '#2e7d32'};">{bsn_count}</div>
                        <div class="metric-label">BSN Instances</div>
                        <div class="metric-subtitle">Social Security Numbers</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{kvk_count}</div>
                        <div class="metric-label">KvK Numbers</div>
                        <div class="metric-subtitle">Business Registry</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{iban_count}</div>
                        <div class="metric-label">IBAN Accounts</div>
                        <div class="metric-subtitle">Banking Information</div>
                    </div>
                    <div class="metric-card" style="background: {'#ffebee' if uavg_count > 0 else '#e8f5e9'};">
                        <div class="metric-value" style="color: {'#c62828' if uavg_count > 0 else '#2e7d32'};">{uavg_count}</div>
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
        # Get emissions data from the nested 'emissions' dictionary
        emissions_data = scan_result.get('emissions', {})
        metrics_data = scan_result.get('metrics', {})
        resources_data = scan_result.get('resources', {})
        
        # Extract values from the correct locations
        co2_emissions = emissions_data.get('total_co2_kg_month', 0)
        energy_consumption = emissions_data.get('total_energy_kwh_month', 0)
        cost_savings = resources_data.get('total_waste_cost', 0) + metrics_data.get('total_cost_savings_potential', 0)
        co2_reduction = metrics_data.get('total_co2_reduction_potential', 0)
        sustainability_score = metrics_data.get('sustainability_score', 0)
        
        # Format values for display
        co2_display = f"{co2_emissions:.1f} kg" if co2_emissions else 'N/A'
        energy_display = f"{energy_consumption:.1f} kWh" if energy_consumption else 'N/A'
        cost_display = f"€{cost_savings:.2f}" if cost_savings else 'N/A'
        
        # Build additional metrics section
        additional_metrics = ""
        if co2_reduction or sustainability_score:
            additional_metrics = f"""
            <div class="metrics-grid" style="margin-top: 20px;">
                <div class="metric-card">
                    <div class="metric-value">{co2_reduction:.1f} kg</div>
                    <div class="metric-label">CO₂ Reduction Potential</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{sustainability_score}/100</div>
                    <div class="metric-label">Sustainability Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{resources_data.get('unused_resources', 0)}</div>
                    <div class="metric-label">Unused Resources</div>
                </div>
            </div>
            """
        
        # Calculate itemized savings from findings
        findings = scan_result.get('findings', [])
        savings_items = []
        total_monthly_cost = 0
        total_monthly_co2 = 0
        
        for finding in findings:
            desc = finding.get('description', '') or finding.get('context', '')
            # Extract cost from description (e.g., "Cost: €145.99/month")
            import re
            cost_match = re.search(r'Cost:\s*€?([\d,.]+)/month', desc)
            co2_match = re.search(r'CO₂:\s*([\d.]+)\s*kg', desc)
            
            if cost_match:
                try:
                    cost = float(cost_match.group(1).replace(',', '.'))
                    co2 = float(co2_match.group(1)) if co2_match else 0
                    total_monthly_cost += cost
                    total_monthly_co2 += co2
                    savings_items.append({
                        'type': finding.get('type', 'Issue'),
                        'cost': cost,
                        'co2': co2,
                        'severity': finding.get('severity', 'medium')
                    })
                except (ValueError, AttributeError):
                    pass
        
        # Build savings summary section
        annual_savings = total_monthly_cost * 12
        savings_summary = ""
        if savings_items or cost_savings > 0:
            final_monthly = total_monthly_cost if total_monthly_cost > 0 else cost_savings
            final_annual = final_monthly * 12
            
            savings_summary = f"""
            <div class="savings-summary" style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-radius: 12px; padding: 25px; margin: 20px 0; border-left: 5px solid #2e7d32;">
                <h3 style="color: #1b5e20; margin-top: 0;">💰 Your Potential Savings</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 15px;">
                    <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <div style="font-size: 2em; font-weight: bold; color: #d32f2f;">€{final_monthly:.2f}</div>
                        <div style="color: #666; font-size: 0.9em;">Monthly Waste</div>
                        <div style="color: #888; font-size: 0.8em; margin-top: 5px;">Currently being spent</div>
                    </div>
                    <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <div style="font-size: 2em; font-weight: bold; color: #2e7d32;">€{final_annual:.2f}</div>
                        <div style="color: #666; font-size: 0.9em;">Annual Savings</div>
                        <div style="color: #888; font-size: 0.8em; margin-top: 5px;">If all issues are fixed</div>
                    </div>
                    <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <div style="font-size: 2em; font-weight: bold; color: #1565c0;">{total_monthly_co2 if total_monthly_co2 > 0 else co2_reduction:.1f} kg</div>
                        <div style="color: #666; font-size: 0.9em;">CO₂ Reduction</div>
                        <div style="color: #888; font-size: 0.8em; margin-top: 5px;">Monthly environmental impact</div>
                    </div>
                </div>
            """
            
            # Add itemized breakdown if we have specific items
            if savings_items:
                savings_summary += """
                <div style="margin-top: 20px;">
                    <h4 style="color: #1b5e20; margin-bottom: 10px;">📋 Itemized Savings Breakdown</h4>
                    <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
                        <thead>
                            <tr style="background: #f5f5f5;">
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Issue</th>
                                <th style="padding: 12px; text-align: right; border-bottom: 2px solid #ddd;">Monthly Cost</th>
                                <th style="padding: 12px; text-align: right; border-bottom: 2px solid #ddd;">Annual Cost</th>
                                <th style="padding: 12px; text-align: right; border-bottom: 2px solid #ddd;">CO₂/Month</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for item in savings_items:
                    severity_color = '#d32f2f' if item['severity'].lower() == 'critical' else '#f57c00' if item['severity'].lower() == 'high' else '#1976d2'
                    savings_summary += f"""
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                                    <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: {severity_color}; margin-right: 8px;"></span>
                                    {item['type'].replace('_', ' ').title()}
                                </td>
                                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #eee; color: #d32f2f; font-weight: bold;">€{item['cost']:.2f}</td>
                                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #eee; color: #d32f2f;">€{item['cost'] * 12:.2f}</td>
                                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #eee;">{item['co2']:.1f} kg</td>
                            </tr>
                    """
                savings_summary += f"""
                        </tbody>
                        <tfoot>
                            <tr style="background: #e8f5e9; font-weight: bold;">
                                <td style="padding: 12px;">Total Potential Savings</td>
                                <td style="padding: 12px; text-align: right; color: #2e7d32;">€{total_monthly_cost:.2f}</td>
                                <td style="padding: 12px; text-align: right; color: #2e7d32;">€{total_monthly_cost * 12:.2f}</td>
                                <td style="padding: 12px; text-align: right; color: #1565c0;">{total_monthly_co2:.1f} kg</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                """
            
            savings_summary += """
                <p style="margin-top: 15px; padding: 10px; background: #fff3e0; border-radius: 6px; color: #e65100; font-size: 0.9em;">
                    💡 <strong>Quick Win:</strong> Addressing the critical and high-priority issues first can achieve up to 80% of these savings with minimal effort.
                </p>
            </div>
            """
        
        return f"""
        <div class="scanner-specific">
            <h2>🌱 {t_report('sustainability_report', 'Sustainability Metrics')}</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{co2_display}</div>
                    <div class="metric-label">CO₂ Emissions/Month</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{energy_display}</div>
                    <div class="metric-label">Energy Consumption</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cost_display}</div>
                    <div class="metric-label">Potential Cost Savings</div>
                </div>
            </div>
            {additional_metrics}
            {savings_summary}
        </div>
        """
    
    def _generate_website_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate website-specific compliance content."""
        cookies_raw = scan_result.get('cookies_found', 0)
        trackers_raw = scan_result.get('trackers_detected', 0)
        
        # Handle both list and integer values
        cookies_count = len(cookies_raw) if isinstance(cookies_raw, list) else cookies_raw
        trackers_count = len(trackers_raw) if isinstance(trackers_raw, list) else trackers_raw
        
        # Build detailed cookie and tracker lists if available
        cookies_details = ""
        if isinstance(cookies_raw, list) and cookies_raw:
            cookies_details = "<div class='details-section'><h3>🍪 Cookie Details</h3><table class='findings-table'><tr><th>Name</th><th>Type</th><th>Purpose</th><th>Privacy Risk</th></tr>"
            for cookie in cookies_raw[:10]:  # Limit to first 10
                name = cookie.get('name', 'Unknown')
                cookie_type = cookie.get('type', 'Unknown')
                purpose = cookie.get('purpose', 'Unknown')
                risk = cookie.get('privacy_risk', 'Unknown')
                risk_class = 'high' if risk.lower() == 'high' else 'medium' if risk.lower() == 'medium' else 'low'
                cookies_details += f"<tr><td>{name}</td><td>{cookie_type}</td><td>{purpose}</td><td class='{risk_class}'>{risk}</td></tr>"
            cookies_details += "</table></div>"
        
        trackers_details = ""
        if isinstance(trackers_raw, list) and trackers_raw:
            trackers_details = "<div class='details-section'><h3>📡 Tracker Details</h3><table class='findings-table'><tr><th>Name</th><th>Type</th><th>Purpose</th><th>Privacy Risk</th></tr>"
            for tracker in trackers_raw[:10]:  # Limit to first 10
                name = tracker.get('name', 'Unknown')
                tracker_type = tracker.get('type', 'Unknown')
                purpose = tracker.get('purpose', 'Unknown')
                risk = tracker.get('privacy_risk', 'Unknown')
                risk_class = 'high' if risk.lower() == 'high' else 'medium' if risk.lower() == 'medium' else 'low'
                trackers_details += f"<tr><td>{name}</td><td>{tracker_type}</td><td>{purpose}</td><td class='{risk_class}'>{risk}</td></tr>"
            trackers_details += "</table></div>"
        
        return f"""
        <div class="scanner-specific">
            <h2>🌐 {t_report('website_privacy_report', 'Website Privacy Analysis')}</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{cookies_count}</div>
                    <div class="metric-label">Cookies Found</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{trackers_count}</div>
                    <div class="metric-label">Trackers Detected</div>
                </div>
            </div>
            {cookies_details}
            {trackers_details}
        </div>
        """
    
    def _generate_compliance_section(self, gdpr_articles: List[str], compliance_requirements: List[str], 
                                       tsc_criteria: List[str] = None, nis2_articles: List[str] = None) -> str:
        """Generate compliance requirements section with support for SOC2/NIS2 frameworks."""
        tsc_criteria = tsc_criteria or []
        nis2_articles = nis2_articles or []
        
        # Check if this is a SOC2/NIS2 finding (has TSC criteria or NIS2 articles)
        is_soc2_nis2 = bool(tsc_criteria or nis2_articles)
        
        if is_soc2_nis2:
            # Generate SOC2 TSC and NIS2 compliance section
            tsc_html = ""
            if tsc_criteria:
                tsc_html = "<div style='margin-bottom: 10px;'><strong>🔒 SOC2 TSC Criteria:</strong><ul class='compliance-list'>"
                for criterion in tsc_criteria[:5]:  # Limit to first 5 for readability
                    tsc_html += f"<li>{criterion}</li>"
                tsc_html += "</ul></div>"
            
            nis2_html = ""
            if nis2_articles:
                nis2_html = "<div><strong>🇪🇺 NIS2 Articles:</strong><ul class='compliance-list'>"
                for article in nis2_articles[:5]:  # Limit to first 5
                    nis2_html += f"<li>{article}</li>"
                nis2_html += "</ul></div>"
            
            return f"""
            <div class="compliance-section">
                <h4>⚖️ Compliance Requirements (SOC2 & NIS2)</h4>
                {tsc_html}
                {nis2_html}
            </div>
            """
        
        # Standard GDPR compliance section
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
        
        # Use language-aware title
        recommendations_title = "Praktische Aanbevelingen" if self.current_language == 'nl' else "Practical Recommendations"
        
        return f"""
        <div class="recommendations-section">
            <h4>💡 {recommendations_title}</h4>
            {recommendations_html}
        </div>
        """
    
    def _generate_compliance_forecast_section(self, scan_result: Dict[str, Any]) -> str:
        """Generate compliance forecast chart section for HTML report."""
        try:
            # Get current user from scan result
            username = scan_result.get('username', 'unknown')
            current_score = scan_result.get('compliance_score', 70)
            findings = scan_result.get('findings', [])
            
            # Check for high-risk/critical findings
            high_risk_findings = [f for f in findings if str(f.get('severity', f.get('risk_level', ''))).lower() in ('critical', 'high')]
            
            # If score is 100 but there are high/critical findings, recalculate
            if current_score >= 100 and len(high_risk_findings) > 0:
                current_score = self._calculate_compliance_score(scan_result)
            # Enforce minimum 10% for actionability (consistent with executive summary)
            elif current_score < 10 and len(findings) > 0:
                current_score = 10
                
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
            
            # Translate trend text
            trend_text_translated = t_report('trend_improving', 'Improving') if trend_text == "Improving" else t_report('trend_declining', 'Declining') if trend_text == "Declining" else t_report('trend_stable', 'Stable')
            
            return f"""
            <div class="compliance-forecast-section">
                <h2>📈 {t_report('compliance_score_forecast', 'Compliance Score Forecast')}</h2>
                <div class="forecast-summary">
                    <div class="forecast-metric">
                        <span class="metric-value">{prediction.future_score:.1f}%</span>
                        <span class="metric-label">🔮 {t_report('ai_predicted_score', 'AI Predicted Score (30 days)')}</span>
                    </div>
                    <div class="forecast-metric">
                        <span class="metric-value {trend_class}">{trend_direction} {trend_text_translated}</span>
                        <span class="metric-label">📈 {t_report('trend_analysis', 'Trend Analysis')}</span>
                    </div>
                    <div class="forecast-metric">
                        <span class="metric-value">{prediction.confidence_interval[0]:.1f}% - {prediction.confidence_interval[1]:.1f}%</span>
                        <span class="metric-label">📊 {t_report('confidence_range', 'Confidence Range')}</span>
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
                    <h4>📊 {t_report('understanding_dashboard', 'Understanding Your Interactive Compliance Dashboard')}</h4>
                    <div class="explanation-grid">
                        <div class="explanation-item">
                            <strong>📊 {t_report('weekly_bars', 'Weekly Compliance Bars')}:</strong> {t_report('weekly_bars_desc', 'Color-coded weekly averages showing your compliance levels')}<br>
                            <strong>📈 {t_report('trend_line', 'Trend Line')}:</strong> {t_report('trend_line_desc', 'Smoothed trend analysis overlaid for pattern recognition (blue line)')}
                        </div>
                        <div class="explanation-item">
                            <strong>🔮 {t_report('ai_forecast', 'AI Forecast')}:</strong> {t_report('ai_forecast_desc', 'Machine learning forecast with confidence bands (orange dashed line)')}<br>
                            <strong>🎛️ {t_report('interactive_controls', 'Interactive Controls')}:</strong> {t_report('interactive_controls_desc', 'Use buttons to switch views, drag timeline, hover for details')}
                        </div>
                        <div class="explanation-item">
                            <strong>🏢 {t_report('industry_benchmarks', 'Industry Benchmarks')}:</strong> {t_report('industry_benchmarks_desc', 'Dotted lines showing average scores for Financial Services and Technology sectors')}
                        </div>
                        <div class="explanation-item">
                            <strong>🚨 {t_report('risk_zones', 'Risk Zones')}:</strong> {t_report('risk_zones_desc', 'Color-coded background areas indicating compliance health levels')}
                        </div>
                    </div>
                    
                    <div class="risk-zone-guide">
                        <h5>{t_report('risk_zone_guide', 'Risk Zone Guide')}:</h5>
                        <ul>
                            <li><span style="color: green;">🟢 {t_report('excellent_90', 'Excellent (90%+)')}:</span> {t_report('outstanding_posture', 'Outstanding compliance posture')}</li>
                            <li><span style="color: orange;">🟡 {t_report('good_80_89', 'Good (80-89%)')}:</span> {t_report('solid_compliance', 'Solid compliance with minor improvements needed')}</li>
                            <li><span style="color: red;">🟠 {t_report('needs_attention_70_79', 'Needs Attention (70-79%)')}:</span> {t_report('moderate_risk', 'Moderate risk requiring focused action')}</li>
                            <li><span style="color: darkred;">🔴 {t_report('critical_60', 'Critical (<60%)')}:</span> {t_report('high_risk', 'High risk requiring immediate intervention')}</li>
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
        # Use translation function for consistent language
        risk_level = t_report('risk_excellent', 'Excellent') if current_score >= 90 else t_report('risk_good', 'Good') if current_score >= 80 else t_report('risk_attention', 'Attention Needed') if current_score >= 70 else t_report('risk_critical', 'Critical')
        risk_icon = '🟢' if current_score >= 90 else '🟡' if current_score >= 80 else '🟠' if current_score >= 70 else '🔴'
        benchmark = f"{t_report('financial_services', 'Financial Services')}: 78.5%" if current_score < 78.5 else f"{t_report('technology', 'Technology')}: 81.2%"
        status_text = t_report('excellent_position', 'excellent compliance position') if current_score >= 90 else t_report('good_position', 'good compliance position') if current_score >= 80 else t_report('moderate_position', 'moderate compliance position') if current_score >= 70 else t_report('critical_position', 'critical compliance position')
        comparison = t_report('above_average', 'Above average') if current_score > 80 else t_report('below_average', 'Below average') if current_score < 75 else t_report('average', 'Average')
        recommendation = t_report('continue_practices', 'Continue current practices') if current_score >= 85 else t_report('focus_critical', 'Focus on addressing critical findings') if current_score < 70 else t_report('implement_improvements', 'Implement systematic improvements')
        
        return f"""
        <div class="compliance-forecast-section">
            <h2>🎯 {t_report('compliance_score_analysis', 'Compliance Score Analysis')}</h2>
            <div class="forecast-summary">
                <div class="forecast-metric">
                    <span class="metric-value">{current_score:.1f}%</span>
                    <span class="metric-label">📊 {t_report('current_compliance_score', 'Current Compliance Score')}</span>
                </div>
                <div class="forecast-metric">
                    <span class="metric-value">{risk_icon} {risk_level}</span>
                    <span class="metric-label">🚨 {t_report('risk_level', 'Risk Level')}</span>
                </div>
                <div class="forecast-metric">
                    <span class="metric-value">{benchmark}</span>
                    <span class="metric-label">🏢 {t_report('sector_benchmark', 'Sector Benchmark')}</span>
                </div>
            </div>
            
            <div class="forecast-explanation">
                <h4>📊 {t_report('compliance_score_analysis', 'Compliance Score Analysis')}</h4>
                <div class="explanation-grid">
                    <div class="explanation-item">
                        <strong>📊 {t_report('current_status', 'Current Status')}:</strong> {t_report('your_score_indicates', 'Your compliance score of')} {current_score:.1f}% {t_report('indicates_a', 'indicates a')} {status_text}.
                    </div>
                    <div class="explanation-item">
                        <strong>🏢 {t_report('sector_comparison', 'Sector Comparison')}:</strong> {comparison} {t_report('compared_to_benchmarks', 'compared to sector benchmarks')}.
                    </div>
                    <div class="explanation-item">
                        <strong>📈 {t_report('recommendations', 'Recommendations')}:</strong> {recommendation}.
                    </div>
                </div>
            </div>
            
            <p style="text-align: center; color: #666; font-style: italic; margin-top: 20px;">
                💡 <strong>{t_report('tip', 'Tip')}:</strong> {t_report('advanced_ai_forecast', 'Advanced AI-powered compliance forecasting is available with full system dependencies')}.
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
        if coverage_version and ('2.0' in str(coverage_version) or '3.0' in str(coverage_version)):
            # Get Phase 2-10 data - use correct keys from advanced_ai_scanner
            annex_iii = scan_result.get('annex_iii_classification', {})
            transparency = scan_result.get('transparency_compliance_article_50', scan_result.get('transparency_compliance', {}))
            provider_deployer = scan_result.get('provider_deployer_obligations_articles_16_27', scan_result.get('provider_deployer_obligations', {}))
            conformity = scan_result.get('conformity_assessment_articles_38_46', scan_result.get('conformity_assessment', {}))
            gpai = scan_result.get('complete_gpai_compliance_articles_52_56', scan_result.get('gpai_compliance', {}))
            post_market = scan_result.get('post_market_monitoring_articles_85_87', scan_result.get('post_market_monitoring', {}))
            ai_literacy = scan_result.get('ai_literacy_article_4', scan_result.get('ai_literacy', {}))
            enforcement = scan_result.get('enforcement_rights_articles_88_94', scan_result.get('enforcement_rights', {}))
            governance = scan_result.get('governance_structures_articles_60_75', scan_result.get('governance_structures', {}))
            
            phase_cards = ""
            phases = [
                ("Annex III Classification", annex_iii),
                ("Transparency (Art. 50)", transparency),
                ("Provider/Deployer Obligations", provider_deployer),
                ("Conformity Assessment", conformity),
                ("GPAI Compliance (Art. 51-55)", gpai),
                ("Post-Market Monitoring", post_market),
                ("AI Literacy (Art. 4)", ai_literacy),
                ("Enforcement & Rights", enforcement),
                ("Governance Structures", governance)
            ]
            
            for title, phase_data in phases:
                if phase_data:
                    # Extract compliance percentage from various data structures
                    compliance_pct = 0
                    is_compliant = False
                    is_applicable = True
                    
                    # Handle different data formats from advanced_ai_scanner
                    if isinstance(phase_data, dict):
                        # Direct compliance_percentage
                        compliance_pct = phase_data.get('compliance_percentage', 0)
                        
                        # Conformity assessment uses different key
                        if compliance_pct == 0:
                            compliance_pct = phase_data.get('conformity_progress_percentage', 0)
                        
                        # Provider/deployer has nested structure
                        if compliance_pct == 0 and 'provider' in phase_data:
                            provider_pct = phase_data.get('provider', {}).get('compliance_percentage', 0)
                            deployer_pct = phase_data.get('deployer', {}).get('compliance_percentage', 0)
                            if provider_pct > 0 or deployer_pct > 0:
                                compliance_pct = (provider_pct + deployer_pct) / 2 if deployer_pct > 0 else provider_pct
                        
                        # GPAI may have compliance score
                        if compliance_pct == 0:
                            compliance_pct = phase_data.get('compliance_score', 0)
                        
                        # Check for compliance boolean flags
                        is_compliant = phase_data.get('overall_compliant', 
                                        phase_data.get('compliant', 
                                        phase_data.get('is_compliant', 
                                        phase_data.get('market_ready', False))))
                        
                        is_applicable = phase_data.get('applicable', 
                                        phase_data.get('is_applicable', 
                                        phase_data.get('article_50_applicable', True)))
                        
                        # Annex III: check if high risk
                        if 'is_high_risk' in phase_data:
                            is_applicable = phase_data.get('is_high_risk', False)
                            compliance_pct = 100 if phase_data.get('is_high_risk') else 0
                    
                    # Choose icon and display based on data available
                    if compliance_pct > 0:
                        compliance_pct = round(compliance_pct, 0)
                        if compliance_pct >= 80:
                            icon, color, display = '✅', '#10b981', f'{int(compliance_pct)}% Compliant'
                        elif compliance_pct >= 50:
                            icon, color, display = '⚠️', '#f59e0b', f'{int(compliance_pct)}% Partial'
                        else:
                            icon, color, display = '🔍', '#ef4444', f'{int(compliance_pct)}% Coverage'
                    elif is_compliant:
                        icon, color, display = '✅', '#10b981', 'Compliant'
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
        
        # Generate enhanced sections (traceability, remediation, conformity)
        enhanced_sections = self._generate_enhanced_ai_act_sections(scan_result, compliance_score)
        
        return f"""
        <div class="scanner-specific">
            <h2>🤖 {t_report('ai_model_compliance', 'AI Model Naleving')}</h2>
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
                    <div class="metric-label">Nalevingsscore</div>
                </div>
            </div>
            {comprehensive_html}
            {enhanced_sections}
        </div>
        """
    
    def _generate_enhanced_ai_act_sections(self, scan_result: Dict[str, Any], compliance_score: float) -> str:
        """Generate enhanced AI Act sections: traceability matrix, remediation plan, conformity scorecard."""
        try:
            from services.advanced_ai_scanner import generate_enhanced_compliance_report
            
            # Language-aware translations
            is_dutch = self.current_language == 'nl'
            t = {
                'traceability_title': 'EU AI Act Artikel Traceerbaarheidsmatrix (Alle 113 Artikelen)' if is_dutch else 'EU AI Act Article Traceability Matrix (All 113 Articles)',
                'total_compliance': 'Totale Naleving' if is_dutch else 'Total Compliance',
                'articles_assessed': 'Artikelen Beoordeeld' if is_dutch else 'Articles Assessed',
                'fully_compliant': 'Volledig Conform' if is_dutch else 'Fully Compliant',
                'partially_compliant': 'Gedeeltelijk Conform' if is_dutch else 'Partially Compliant',
                'non_compliant': 'Niet Conform' if is_dutch else 'Non-Compliant',
                'compliance_by_chapter': 'Naleving per Hoofdstuk' if is_dutch else 'Compliance by Chapter',
                'chapter': 'Hoofdstuk' if is_dutch else 'Chapter',
                'articles': 'Artikelen' if is_dutch else 'Articles',
                'compliant': 'Conform' if is_dutch else 'Compliant',
                'partial': 'Gedeeltelijk' if is_dutch else 'Partial',
                'score': 'Score' if is_dutch else 'Score',
                'status': 'Status' if is_dutch else 'Status',
                'remediation_plan': 'Geprioriteerd Herstelplan' if is_dutch else 'Prioritized Remediation Plan',
                'article': 'Artikel' if is_dutch else 'Article',
                'priority': 'Prioriteit' if is_dutch else 'Priority',
                'deadline': 'Deadline' if is_dutch else 'Deadline',
                'effort': 'Inspanning' if is_dutch else 'Effort',
                'conformity_scorecard': 'Conformiteitsbeoordeling Gereedheidsscorekaart' if is_dutch else 'Conformity Assessment Readiness Scorecard',
                'documentation': 'Documentatie' if is_dutch else 'Documentation',
                'technical_measures': 'Technische Maatregelen' if is_dutch else 'Technical Measures',
                'governance': 'Governance' if is_dutch else 'Governance',
                'risk_management': 'Risicobeheer' if is_dutch else 'Risk Management',
                'time_to_ready': 'Geschatte Tijd tot Gereedheid' if is_dutch else 'Estimated Time to Ready',
                'key_recommendations': 'Belangrijke Aanbevelingen' if is_dutch else 'Key Recommendations',
                'executive_summary': 'Toezichthouder-Klaar Managementsamenvatting' if is_dutch else 'Regulator-Ready Executive Summary',
                'compliance_overview': 'Nalevingsoverzicht' if is_dutch else 'Compliance Overview',
                'total_score': 'Totale Score' if is_dutch else 'Total Score',
                'rating': 'Beoordeling' if is_dutch else 'Rating',
                'regulatory_deadlines': 'Regelgevende Deadlines' if is_dutch else 'Regulatory Deadlines',
            }
            
            system_name = scan_result.get('model_name', scan_result.get('repository_url', 'AI System'))
            enhanced = generate_enhanced_compliance_report(
                scan_result, 
                system_name=str(system_name)[:50] if system_name else "AI System",
                organization="Organization",
                region=scan_result.get('region', 'Netherlands')
            )
            
            if 'error' in enhanced:
                return ""
            
            # Build traceability summary section
            traceability = enhanced.get('traceability_matrix', {})
            overall = traceability.get('overall_metrics', {})
            chapter_summary = traceability.get('chapter_summary', {})
            
            # Article status summary
            traceability_html = f"""
            <div style="margin-top: 30px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px;">
                <h3 style="color: #1e293b; margin-bottom: 20px; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">
                    📋 {t['traceability_title']}
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size: 28px; font-weight: bold; color: #10b981;">{overall.get('overall_compliance_score', 0):.1f}%</div>
                        <div style="font-size: 12px; color: #64748b;">{t['total_compliance']}</div>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size: 28px; font-weight: bold; color: #3b82f6;">{overall.get('total_articles', 0)}</div>
                        <div style="font-size: 12px; color: #64748b;">{t['articles_assessed']}</div>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #22c55e; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size: 28px; font-weight: bold; color: #22c55e;">{overall.get('compliant', 0)}</div>
                        <div style="font-size: 12px; color: #64748b;">{t['fully_compliant']}</div>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size: 28px; font-weight: bold; color: #f59e0b;">{overall.get('partially_compliant', 0)}</div>
                        <div style="font-size: 12px; color: #64748b;">{t['partially_compliant']}</div>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #ef4444; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size: 28px; font-weight: bold; color: #ef4444;">{overall.get('non_compliant', 0)}</div>
                        <div style="font-size: 12px; color: #64748b;">{t['non_compliant']}</div>
                    </div>
                </div>
            """
            
            # Chapter breakdown table
            if chapter_summary:
                traceability_html += f"""
                <h4 style="color: #475569; margin: 20px 0 15px 0;">{t['compliance_by_chapter']}</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <thead>
                        <tr style="background: #1e293b; color: white;">
                            <th style="padding: 10px; text-align: left; border-radius: 4px 0 0 0;">{t['chapter']}</th>
                            <th style="padding: 10px; text-align: center;">{t['articles']}</th>
                            <th style="padding: 10px; text-align: center;">{t['compliant']}</th>
                            <th style="padding: 10px; text-align: center;">{t['partial']}</th>
                            <th style="padding: 10px; text-align: center;">{t['score']}</th>
                            <th style="padding: 10px; text-align: center; border-radius: 0 4px 0 0;">{t['status']}</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for chapter, data in list(chapter_summary.items())[:12]:
                    avg_score = data.get('average_score', 0)
                    status_icon = "✅" if avg_score >= 80 else "⚠️" if avg_score >= 50 else "❌"
                    status_color = "#10b981" if avg_score >= 80 else "#f59e0b" if avg_score >= 50 else "#ef4444"
                    
                    traceability_html += f"""
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 10px;">{chapter[:40]}{'...' if len(chapter) > 40 else ''}</td>
                            <td style="padding: 10px; text-align: center;">{len(data.get('articles', []))}</td>
                            <td style="padding: 10px; text-align: center; color: #22c55e;">{data.get('compliant', 0)}</td>
                            <td style="padding: 10px; text-align: center; color: #f59e0b;">{data.get('partial', 0)}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold;">{avg_score:.0f}%</td>
                            <td style="padding: 10px; text-align: center; color: {status_color};">{status_icon}</td>
                        </tr>
                    """
                
                traceability_html += "</tbody></table>"
            
            traceability_html += "</div>"
            
            # Remediation Priority Plan
            remediation = enhanced.get('remediation_plan', {})
            prioritized = remediation.get('prioritized_items', [])[:8]
            
            remediation_html = ""
            if prioritized:
                remediation_html = f"""
                <div style="margin-top: 30px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #f59e0b; border-radius: 12px; padding: 25px;">
                    <h3 style="color: #92400e; margin-bottom: 20px; border-bottom: 2px solid #f59e0b; padding-bottom: 10px;">
                        🎯 {t['remediation_plan']}
                    </h3>
                    <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
                        <thead>
                            <tr style="background: #92400e; color: white;">
                                <th style="padding: 12px; text-align: left;">ID</th>
                                <th style="padding: 12px; text-align: left;">Artikel</th>
                                <th style="padding: 12px; text-align: left;">Bevinding</th>
                                <th style="padding: 12px; text-align: center;">Prioriteit</th>
                                <th style="padding: 12px; text-align: center;">Impact</th>
                                <th style="padding: 12px; text-align: center;">Inspanning</th>
                                <th style="padding: 12px; text-align: center;">Deadline</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                
                for item in prioritized:
                    priority = item.get('priority', 'medium')
                    priority_color = "#ef4444" if priority == "critical" else "#f59e0b" if priority == "high" else "#3b82f6"
                    priority_icon = "🔴" if priority == "critical" else "🟠" if priority == "high" else "🟡"
                    
                    finding_text = item.get('finding', '')[:60]
                    if len(item.get('finding', '')) > 60:
                        finding_text += '...'
                    
                    remediation_html += f"""
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 10px; font-family: monospace; font-size: 11px;">{item.get('id', '')}</td>
                            <td style="padding: 10px; font-weight: 600;">{item.get('article', '')}</td>
                            <td style="padding: 10px; font-size: 12px;">{finding_text}</td>
                            <td style="padding: 10px; text-align: center;"><span style="background: {priority_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{priority_icon} {priority.upper()}</span></td>
                            <td style="padding: 10px; text-align: center; font-weight: bold;">{item.get('impact_score', 0):.0f}</td>
                            <td style="padding: 10px; text-align: center;">{item.get('effort_hours', 0):.0f}h</td>
                            <td style="padding: 10px; text-align: center; font-size: 11px;">{item.get('deadline', '')}</td>
                        </tr>
                    """
                
                remediation_html += """
                        </tbody>
                    </table>
                    <p style="margin-top: 15px; font-size: 12px; color: #92400e; font-style: italic;">
                        💡 Items gesorteerd op zakelijke impactscore. Focus eerst op kritieke en hoge prioriteit items.
                    </p>
                </div>
                """
            
            # Conformity Assessment Readiness Scorecard
            conformity = enhanced.get('conformity_scorecard', {})
            readiness = conformity.get('readiness_scores', {})
            
            conformity_html = f"""
            <div style="margin-top: 30px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border: 1px solid #3b82f6; border-radius: 12px; padding: 25px;">
                <h3 style="color: #1e40af; margin-bottom: 20px; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">
                    📊 {t['conformity_scorecard']}
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
            """
            
            # Language-aware readiness labels
            overall_label = "Algehele Gereedheid" if is_dutch else "Overall Readiness"
            doc_label = "Documentatie" if is_dutch else "Documentation"
            tech_label = "Technisch" if is_dutch else "Technical"
            gov_label = "Bestuur" if is_dutch else "Governance"
            oversight_label = "Menselijk Toezicht" if is_dutch else "Human Oversight"
            risk_label = "Risicobeheer" if is_dutch else "Risk Management"
            
            readiness_items = [
                (overall_label, readiness.get('overall', 0), "#3b82f6"),
                (doc_label, readiness.get('documentation', 0), "#8b5cf6"),
                (tech_label, readiness.get('technical', 0), "#06b6d4"),
                (gov_label, readiness.get('governance', 0), "#10b981"),
                (oversight_label, readiness.get('human_oversight', 0), "#f59e0b"),
                (risk_label, readiness.get('risk_management', 0), "#ef4444"),
            ]
            
            for label, score, color in readiness_items:
                status_icon = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
                conformity_html += f"""
                    <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size: 24px; font-weight: bold; color: {color};">{score:.0f}%</div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 5px;">{label}</div>
                        <div style="font-size: 16px; margin-top: 5px;">{status_icon}</div>
                    </div>
                """
            
            conformity_html += "</div>"
            
            # Time to ready estimate
            time_to_ready = conformity.get('estimated_time_to_ready', 'Unknown')
            recommendations = conformity.get('recommendations', [])[:4]
            
            conformity_html += f"""
                <div style="background: white; padding: 20px; border-radius: 8px; margin-top: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <span style="font-weight: bold; color: #1e40af;">⏱️ {t['time_to_ready']}:</span>
                        <span style="background: #1e40af; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">{time_to_ready}</span>
                    </div>
                    <div style="border-top: 1px solid #e2e8f0; padding-top: 15px;">
                        <strong style="color: #1e40af;">{t['key_recommendations']}:</strong>
                        <ul style="margin-top: 10px; padding-left: 20px;">
            """
            
            for rec in recommendations:
                conformity_html += f'<li style="margin-bottom: 5px; color: #475569; font-size: 13px;">{rec}</li>'
            
            conformity_html += """
                        </ul>
                    </div>
                </div>
            </div>
            """
            
            # Executive Summary for Regulators
            exec_summary = enhanced.get('executive_summary', {})
            compliance_overview = exec_summary.get('compliance_overview', {})
            
            executive_html = f"""
            <div style="margin-top: 30px; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 2px solid #16a34a; border-radius: 12px; padding: 25px;">
                <h3 style="color: #166534; margin-bottom: 20px; border-bottom: 2px solid #16a34a; padding-bottom: 10px;">
                    📄 {t['executive_summary']}
                </h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h4 style="color: #166534; margin-bottom: 10px;">{t['compliance_overview']}</h4>
                        <table style="width: 100%; font-size: 13px;">
                            <tr><td style="padding: 5px; color: #64748b;">{t['total_score']}:</td><td style="padding: 5px; font-weight: bold;">{compliance_overview.get('overall_score', 'N/A')}</td></tr>
                            <tr><td style="padding: 5px; color: #64748b;">{t['rating']}:</td><td style="padding: 5px; font-weight: bold;">{compliance_overview.get('rating', 'N/A')}</td></tr>
                            <tr><td style="padding: 5px; color: #64748b;">{t['articles_assessed']}:</td><td style="padding: 5px; font-weight: bold;">{compliance_overview.get('articles_assessed', 0)}</td></tr>
                        </table>
                    </div>
                    <div>
                        <h4 style="color: #166534; margin-bottom: 10px;">{t['regulatory_deadlines']}</h4>
                        <table style="width: 100%; font-size: 13px;">
                            <tr><td style="padding: 5px; color: #64748b;">{"Verboden Praktijken" if is_dutch else "Prohibited Practices"}:</td><td style="padding: 5px; font-weight: bold;">{"2 feb 2025" if is_dutch else "Feb 2, 2025"}</td></tr>
                            <tr><td style="padding: 5px; color: #64748b;">{"GPAI Modellen" if is_dutch else "GPAI Models"}:</td><td style="padding: 5px; font-weight: bold;">{"2 aug 2025" if is_dutch else "Aug 2, 2025"}</td></tr>
                            <tr><td style="padding: 5px; color: #64748b;">{"Hoog-Risico Systemen" if is_dutch else "High-Risk Systems"}:</td><td style="padding: 5px; font-weight: bold;">{"2 aug 2026" if is_dutch else "Aug 2, 2026"}</td></tr>
                        </table>
                    </div>
                </div>
                <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 8px;">
                    <strong style="color: #166534;">🇳🇱 {"Nederland Specifiek" if is_dutch else "Netherlands Specific"}:</strong>
                    <p style="margin-top: 10px; font-size: 13px; color: #475569;">
                        {"Autoriteit: Autoriteit Persoonsgegevens (AP) | UAVG naleving gewaarborgd | BSN verwerkingsprocedures geïmplementeerd waar van toepassing" if is_dutch else "Authority: Dutch Data Protection Authority (AP) | UAVG compliance ensured | BSN processing procedures implemented where applicable"}
                    </p>
                </div>
                <p style="margin-top: 15px; text-align: center; font-size: 11px; color: #64748b;">
                    {"Beoordelingsdatum" if is_dutch else "Assessment Date"}: {datetime.now().strftime('%d-%m-%Y' if is_dutch else '%Y-%m-%d')} | {"Beoordelaar" if is_dutch else "Assessor"}: DataGuardian Pro AI Compliance Platform | {"Geldig tot materiële wijzigingen" if is_dutch else "Valid until material changes"}
                </p>
            </div>
            """
            
            return traceability_html + remediation_html + conformity_html + executive_html
            
        except Exception as e:
            logger.warning(f"Could not generate enhanced AI Act sections: {e}")
            return ""
    
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
                    <div class="metric-label">Risicoscore</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{overall_risk_level}</div>
                    <div class="metric-label">Risiconiveau</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_exact_online_content(self, scan_result: Dict[str, Any]) -> str:
        """Generate Exact Online scanner specific content with GDPR/UAVG compliance details."""
        content_html = ""
        
        exact_detected = scan_result.get('exact_integration_detected', False)
        integration_findings = scan_result.get('integration_findings', [])
        pii_findings = scan_result.get('pii_findings', [])
        credential_findings = scan_result.get('credential_findings', [])
        data_flow_map = scan_result.get('data_flow_map', [])
        risk_summary = scan_result.get('risk_summary', {})
        gdpr_compliance = scan_result.get('gdpr_compliance', {})
        uavg_compliance = scan_result.get('uavg_compliance', {})
        recommendations = scan_result.get('recommendations', [])
        
        integration_status = "Detected" if exact_detected else "Not Found"
        integration_color = "#37b24d" if exact_detected else "#868e96"
        
        content_html += f"""
        <div class="exact-online-section" style="margin: 20px 0;">
            <h2 style="color: #1e3a5f; border-bottom: 3px solid #3b82f6; padding-bottom: 10px;">
                🔗 Exact Online Integration Analysis
            </h2>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0;">
                <div style="background: #f0f9ff; padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid {integration_color};">
                    <div style="font-size: 1.8em; color: {integration_color}; font-weight: bold;">{integration_status}</div>
                    <div style="color: #64748b; margin-top: 5px;">Exact Online</div>
                </div>
                <div style="background: #fef2f2; padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #dc2626;">
                    <div style="font-size: 1.8em; color: #dc2626; font-weight: bold;">{len(credential_findings)}</div>
                    <div style="color: #64748b; margin-top: 5px;">Credential Issues</div>
                </div>
                <div style="background: #fff7ed; padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #ea580c;">
                    <div style="font-size: 1.8em; color: #ea580c; font-weight: bold;">{len(pii_findings)}</div>
                    <div style="color: #64748b; margin-top: 5px;">PII Patterns</div>
                </div>
                <div style="background: #f0fdf4; padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #16a34a;">
                    <div style="font-size: 1.8em; color: #16a34a; font-weight: bold;">{len(data_flow_map)}</div>
                    <div style="color: #64748b; margin-top: 5px;">Data Flows</div>
                </div>
            </div>
        """
        
        if credential_findings:
            content_html += """
            <div style="background: #fef2f2; border: 2px solid #dc2626; padding: 20px; margin: 20px 0; border-radius: 10px;">
                <h3 style="color: #dc2626; margin-top: 0;">🚨 Critical: Credential Exposure Detected</h3>
                <p style="color: #7f1d1d; margin-bottom: 15px;">The following credentials or secrets were found in the codebase. Immediate action required.</p>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #fee2e2;">
                            <th style="padding: 10px; text-align: left; border: 1px solid #fecaca;">File</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #fecaca;">Type</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #fecaca;">Line</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #fecaca;">Action Required</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for finding in credential_findings[:10]:
                content_html += f"""
                        <tr>
                            <td style="padding: 8px; border: 1px solid #fecaca;">{finding.get('file', 'N/A')}</td>
                            <td style="padding: 8px; border: 1px solid #fecaca; color: #dc2626; font-weight: bold;">{finding.get('description', finding.get('pattern_name', 'Unknown'))}</td>
                            <td style="padding: 8px; border: 1px solid #fecaca;">{finding.get('line_number', 'N/A')}</td>
                            <td style="padding: 8px; border: 1px solid #fecaca; font-size: 0.9em;">{finding.get('recommendation', 'Rotate immediately')}</td>
                        </tr>
                """
            content_html += """
                    </tbody>
                </table>
            </div>
            """
        
        bsn_detected = uavg_compliance.get('bsn_processing_detected', False)
        if bsn_detected or pii_findings:
            content_html += """
            <div style="background: #fffbeb; border: 2px solid #d97706; padding: 20px; margin: 20px 0; border-radius: 10px;">
                <h3 style="color: #92400e; margin-top: 0;">🇳🇱 Netherlands Privacy Data (UAVG Compliance)</h3>
            """
            
            if bsn_detected:
                content_html += """
                <div style="background: #fef2f2; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #dc2626;">
                    <strong style="color: #dc2626;">⚠️ BSN Processing Detected</strong>
                    <p style="margin: 10px 0; color: #7f1d1d;">
                        Burgerservicenummer (BSN) handling detected. Under UAVG Article 46, BSN processing requires explicit legal basis.
                    </p>
                    <ul style="margin: 10px 0; padding-left: 20px; color: #7f1d1d;">
                        <li>Document legal basis for BSN processing</li>
                        <li>Conduct Data Protection Impact Assessment (DPIA)</li>
                        <li>Notify Data Protection Officer (DPO)</li>
                        <li>Implement additional security measures</li>
                    </ul>
                </div>
                """
            
            content_html += """
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #fef3c7;">
                            <th style="padding: 10px; text-align: left; border: 1px solid #fcd34d;">Data Type</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #fcd34d;">File</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #fcd34d;">GDPR Articles</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #fcd34d;">Severity</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for finding in pii_findings[:15]:
                gdpr_arts = ', '.join(finding.get('gdpr_articles', []))
                severity = finding.get('severity', 'Medium')
                sev_color = '#dc2626' if severity == 'Critical' else '#ea580c' if severity == 'High' else '#d97706'
                content_html += f"""
                        <tr>
                            <td style="padding: 8px; border: 1px solid #fcd34d;">{finding.get('description', finding.get('pattern_name', 'Unknown'))}</td>
                            <td style="padding: 8px; border: 1px solid #fcd34d; font-size: 0.85em;">{finding.get('file', 'N/A')}</td>
                            <td style="padding: 8px; border: 1px solid #fcd34d;">{gdpr_arts or 'N/A'}</td>
                            <td style="padding: 8px; border: 1px solid #fcd34d; color: {sev_color}; font-weight: bold;">{severity}</td>
                        </tr>
                """
            content_html += """
                    </tbody>
                </table>
            </div>
            """
        
        if data_flow_map:
            content_html += """
            <div style="background: #f0f9ff; border: 2px solid #3b82f6; padding: 20px; margin: 20px 0; border-radius: 10px;">
                <h3 style="color: #1e40af; margin-top: 0;">📊 Data Flow Analysis</h3>
                <p style="color: #1e3a5f; margin-bottom: 15px;">Inferred data flows from code structure. Review for GDPR compliance.</p>
            """
            for flow in data_flow_map:
                content_html += f"""
                <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #3b82f6;">
                    <strong style="color: #1e40af;">{flow.get('flow', 'Unknown Flow')}</strong>
                    <p style="margin: 5px 0; color: #475569;">{flow.get('description', '')}</p>
                    <p style="margin: 5px 0; color: #dc2626; font-size: 0.9em;">
                        ⚠️ GDPR Concern: {flow.get('gdpr_concern', 'Review required')}
                    </p>
                </div>
                """
            content_html += "</div>"
        
        if gdpr_compliance:
            controls_html = ""
            controls = [
                ('has_encryption', '🔐 Encryption', 'Art. 32'),
                ('has_consent_management', '✅ Consent', 'Art. 6/7'),
                ('has_access_control', '🔒 Access Control', 'Art. 25'),
                ('has_audit_logging', '📋 Audit', 'Art. 30'),
                ('has_retention_policy', '📅 Retention', 'Art. 5')
            ]
            for key, label, article in controls:
                status = gdpr_compliance.get(key, False)
                status_icon = "✓" if status else "✗"
                status_color = "#16a34a" if status else "#dc2626"
                controls_html += f"""
                <div style="padding: 10px; text-align: center; background: {'#f0fdf4' if status else '#fef2f2'}; border-radius: 8px;">
                    <div style="font-size: 1.5em; color: {status_color};">{status_icon}</div>
                    <div style="font-weight: bold; color: #475569;">{label}</div>
                    <div style="font-size: 0.8em; color: #64748b;">{article}</div>
                </div>
                """
            
            content_html += f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; margin: 20px 0; border-radius: 10px;">
                <h3 style="color: #1e3a5f; margin-top: 0;">📋 GDPR Compliance Controls</h3>
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 15px;">
                    {controls_html}
                </div>
            </div>
            """
        
        if recommendations:
            content_html += """
            <div style="background: #f0fdf4; border: 2px solid #16a34a; padding: 20px; margin: 20px 0; border-radius: 10px;">
                <h3 style="color: #166534; margin-top: 0;">📝 Prioritized Recommendations</h3>
            """
            for rec in recommendations:
                priority = rec.get('priority', 'Medium')
                priority_color = '#dc2626' if priority == 'Critical' else '#ea580c' if priority == 'High' else '#d97706'
                actions = rec.get('actions', [])
                actions_html = ''.join([f'<li>{action}</li>' for action in actions])
                
                content_html += f"""
                <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid {priority_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: #1e3a5f;">{rec.get('title', 'Recommendation')}</strong>
                        <span style="background: {priority_color}; color: white; padding: 3px 10px; border-radius: 15px; font-size: 0.8em;">{priority}</span>
                    </div>
                    <p style="margin: 10px 0; color: #475569;">{rec.get('description', '')}</p>
                    <ul style="margin: 10px 0; padding-left: 20px; color: #1e3a5f; font-size: 0.9em;">
                        {actions_html}
                    </ul>
                </div>
                """
            content_html += "</div>"
        
        content_html += "</div>"
        return content_html
    
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

def generate_comprehensive_report(scan_result: Dict[str, Any]) -> str:
    """
    Generate a comprehensive HTML report (alias for backward compatibility).
    
    Args:
        scan_result: Scan result data
        
    Returns:
        Complete HTML report as string
    """
    return generate_unified_html_report(scan_result)