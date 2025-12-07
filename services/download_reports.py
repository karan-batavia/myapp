"""
Report Generation Service - Unified Template

Generates PDF and HTML reports for all scanners with consistent professional styling.
Includes fraud detection analysis for document scanners.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime


def generate_pdf_report(scan_results: Dict[str, Any], filename: str = "scan_report.pdf") -> Optional[bytes]:
    """
    Generate PDF report from scan results.
    
    Args:
        scan_results: Complete scan results with findings
        filename: Output filename
    
    Returns:
        PDF bytes or None if generation fails
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title with proper styling
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=26,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("📄 DataGuardian Pro - Scan Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata box with professional styling
        scan_type = scan_results.get('scan_type', 'Unknown')
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        files_scanned = scan_results.get('files_scanned', scan_results.get('endpoints_scanned', 0))
        total_findings = len(scan_results.get('findings', []))
        
        metadata_data = [
            ["Report Generated", report_date],
            ["Scan Type", scan_type],
            ["Items Scanned", str(files_scanned)],
            ["Total Findings", str(total_findings)],
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2.5*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Findings section
        story.append(Paragraph("🔍 Findings Summary", styles['Heading2']))
        findings = scan_results.get('findings', [])
        
        if findings:
            findings_data = [["Type", "Severity", "Description", "Location"]]
            for finding in findings[:20]:  # Limit to first 20 for PDF
                findings_data.append([
                    str(finding.get('type', 'Unknown'))[:25],
                    str(finding.get('severity', finding.get('risk_level', 'Medium')))[:12],
                    str(finding.get('description', 'No description'))[:35],
                    str(finding.get('location', finding.get('file', 'N/A')))[:20]
                ])
            
            findings_table = Table(findings_data, colWidths=[1.3*inch, 1*inch, 1.7*inch, 1.5*inch])
            findings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
            ]))
            story.append(findings_table)
        else:
            story.append(Paragraph("✅ No findings detected.", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Fraud detection section (if available)
        fraud_findings = [f for f in findings if f.get('fraud_analysis')]
        if fraud_findings:
            story.append(Paragraph("🚨 AI Fraud Detection Analysis", styles['Heading2']))
            
            fraud_data = [["Document", "Risk Level", "AI Score", "Model"]]
            for finding in fraud_findings:
                fraud_analysis = finding.get('fraud_analysis', {})
                fraud_data.append([
                    str(finding.get('file_name', 'Unknown'))[:25],
                    str(fraud_analysis.get('risk_level', 'N/A'))[:12],
                    f"{fraud_analysis.get('ai_generated_risk', 0):.0%}",
                    str(fraud_analysis.get('ai_model', 'Unknown'))[:20]
                ])
            
            fraud_table = Table(fraud_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.8*inch])
            fraud_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fecaca')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fee2e2')])
            ]))
            story.append(fraud_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Footer
        story.append(Spacer(1, 0.2*inch))
        footer_text = "Generated by DataGuardian Pro - Enterprise Privacy Compliance Platform"
        story.append(Paragraph(f"<i>{footer_text}</i>", ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#9ca3af'),
            alignment=1
        )))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None


def generate_html_report(scan_results: Dict[str, Any], filename: str = "scan_report.html") -> Optional[str]:
    """
    Generate professional HTML report from scan results - Uses unified template for all scanners.
    
    Args:
        scan_results: Complete scan results with findings
        filename: Output filename
    
    Returns:
        HTML string or None if generation fails
    """
    try:
        # Use the unified HTML report generator for consistent professional reports
        from services.unified_html_report_generator import generate_unified_html_report
        return generate_unified_html_report(scan_results)
    except ImportError:
        # Fallback to legacy generator if unified not available
        pass
    except Exception as e:
        # Log error but continue with fallback
        import logging
        logging.warning(f"Unified report generator failed, using fallback: {e}")
    
    # Legacy fallback generator
    try:
        findings = scan_results.get('findings', [])
        scan_type = scan_results.get('scan_type', 'Security Scan')
        files_scanned = scan_results.get('files_scanned', scan_results.get('endpoints_scanned', 0))
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build findings table
        findings_rows = ""
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        
        for finding in findings:
            severity = finding.get('severity', finding.get('risk_level', 'Medium'))
            severity_lower = severity.lower()
            
            if severity_lower == 'critical':
                critical_count += 1
                badge = '<span style="background: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">CRITICAL</span>'
            elif severity_lower == 'high':
                high_count += 1
                badge = '<span style="background: #ea580c; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">HIGH</span>'
            elif severity_lower == 'medium':
                medium_count += 1
                badge = '<span style="background: #f59e0b; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">MEDIUM</span>'
            else:
                low_count += 1
                badge = '<span style="background: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">LOW</span>'
            
            findings_rows += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{finding.get('type', 'Unknown')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center;">{badge}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{finding.get('description', 'No description')}</td>
            </tr>
            """
        
        # Build fraud detection section if available
        fraud_findings = [f for f in findings if f.get('fraud_analysis')]
        fraud_section = ""
        if fraud_findings:
            fraud_rows = ""
            for finding in fraud_findings:
                fraud_analysis = finding.get('fraud_analysis', {})
                risk_level = fraud_analysis.get('risk_level', 'Low')
                if risk_level == 'Critical':
                    risk_badge = '<span style="background: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🔴 CRITICAL</span>'
                elif risk_level == 'High':
                    risk_badge = '<span style="background: #ea580c; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟠 HIGH</span>'
                elif risk_level == 'Medium':
                    risk_badge = '<span style="background: #f59e0b; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟡 MEDIUM</span>'
                else:
                    risk_badge = '<span style="background: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟢 LOW</span>'
                
                fraud_rows += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #fee2e2;">{finding.get('file_name', 'Unknown')}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #fee2e2;">{risk_badge}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #fee2e2;">{fraud_analysis.get('ai_generated_risk', 0):.0%}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #fee2e2;">{fraud_analysis.get('confidence', 0):.1f}%</td>
                    <td style="padding: 12px; border-bottom: 1px solid #fee2e2;">{fraud_analysis.get('ai_model', 'Unknown')}</td>
                </tr>
                """
            
            fraud_section = f"""
            <div style="margin-top: 40px; padding: 30px; background: #fef2f2; border-radius: 10px; border-left: 4px solid #dc2626;">
                <h2 style="color: #dc2626; margin-top: 0;">🚨 AI Fraud Detection Analysis</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #dc2626; color: white;">
                            <th style="padding: 12px; text-align: left; font-weight: bold;">Document</th>
                            <th style="padding: 12px; text-align: left; font-weight: bold;">Risk Level</th>
                            <th style="padding: 12px; text-align: left; font-weight: bold;">AI Score</th>
                            <th style="padding: 12px; text-align: left; font-weight: bold;">Confidence</th>
                            <th style="padding: 12px; text-align: left; font-weight: bold;">Model</th>
                        </tr>
                    </thead>
                    <tbody>
                        {fraud_rows}
                    </tbody>
                </table>
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>DataGuardian Pro - Scan Report</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #1f2937;
                    background: #f9fafb;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                }}
                .header {{
                    background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
                    color: white;
                    padding: 40px;
                    border-radius: 10px;
                    margin-bottom: 40px;
                    text-align: center;
                }}
                .header h1 {{
                    font-size: 32px;
                    margin-bottom: 10px;
                }}
                .header p {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .metadata {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 40px;
                    padding: 20px;
                    background: #f3f4f6;
                    border-left: 4px solid #1e40af;
                    border-radius: 8px;
                }}
                .metadata-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .metadata-item:last-child {{
                    border-bottom: none;
                }}
                .metadata-label {{
                    font-weight: 600;
                    color: #374151;
                }}
                .metadata-value {{
                    color: #1e40af;
                    font-weight: 500;
                }}
                h2 {{
                    color: #1e40af;
                    font-size: 22px;
                    margin: 30px 0 20px 0;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #e5e7eb;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background: #1e40af;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                td {{
                    padding: 12px;
                    border-bottom: 1px solid #e5e7eb;
                }}
                tr:nth-child(even) {{
                    background: #f9fafb;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-box {{
                    background: #f3f4f6;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    border-left: 4px solid #1e40af;
                }}
                .stat-box.critical {{
                    border-left-color: #dc2626;
                }}
                .stat-box.high {{
                    border-left-color: #ea580c;
                }}
                .stat-box.medium {{
                    border-left-color: #f59e0b;
                }}
                .stat-box.low {{
                    border-left-color: #10b981;
                }}
                .stat-number {{
                    font-size: 24px;
                    font-weight: 700;
                    margin: 10px 0;
                }}
                .stat-label {{
                    font-size: 12px;
                    color: #6b7280;
                    font-weight: 600;
                    text-transform: uppercase;
                }}
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 2px solid #e5e7eb;
                    text-align: center;
                    font-size: 12px;
                    color: #9ca3af;
                }}
                .no-findings {{
                    padding: 30px;
                    background: #ecfdf5;
                    border-left: 4px solid #10b981;
                    border-radius: 8px;
                    text-align: center;
                    color: #047857;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📄 DataGuardian Pro - Scan Report</h1>
                    <p>Enterprise Privacy Compliance Analysis</p>
                </div>
                
                <div class="metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Report Generated</span>
                        <span class="metadata-value">{report_date}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Scan Type</span>
                        <span class="metadata-value">{scan_type}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Items Scanned</span>
                        <span class="metadata-value">{files_scanned}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Total Findings</span>
                        <span class="metadata-value">{len(findings)}</span>
                    </div>
                </div>
                
                <h2>📊 Risk Summary</h2>
                <div class="stats">
                    <div class="stat-box critical">
                        <div class="stat-label">🔴 Critical</div>
                        <div class="stat-number">{critical_count}</div>
                    </div>
                    <div class="stat-box high">
                        <div class="stat-label">🟠 High</div>
                        <div class="stat-number">{high_count}</div>
                    </div>
                    <div class="stat-box medium">
                        <div class="stat-label">🟡 Medium</div>
                        <div class="stat-number">{medium_count}</div>
                    </div>
                    <div class="stat-box low">
                        <div class="stat-label">🟢 Low</div>
                        <div class="stat-number">{low_count}</div>
                    </div>
                </div>
                
                <h2>🔍 Detailed Findings</h2>
                {f'''
                <table>
                    <thead>
                        <tr>
                            <th>Finding Type</th>
                            <th>Severity</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {findings_rows if findings_rows else '<tr><td colspan="3" style="text-align: center; padding: 30px;">✅ No findings detected</td></tr>'}
                    </tbody>
                </table>
                ''' if findings else '<div class="no-findings">✅ No findings detected - Your system passed compliance checks!</div>'}
                
                {fraud_section}
                
                <div class="footer">
                    <p>Generated by DataGuardian Pro - Enterprise Privacy Compliance Platform</p>
                    <p>Netherlands Hosted | GDPR Compliant | UAVG Compliant</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        st.error(f"HTML generation failed: {str(e)}")
        return None
