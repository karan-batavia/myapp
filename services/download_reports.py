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
    Generate modern, best-in-class PDF report from scan results.
    Matches the HTML report design with professional styling.
    
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
        from reportlab.graphics.shapes import Drawing, Rect, Line
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Extract data
        scan_type = scan_results.get('scan_type', 'Document Scanner')
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scan_id = scan_results.get('scan_id', 'N/A')[:20]
        region = scan_results.get('region', 'Netherlands')
        files_scanned = scan_results.get('files_scanned', scan_results.get('endpoints_scanned', 1)) or 1
        findings = scan_results.get('findings', [])
        total_findings = len(findings)
        
        # Count severity levels
        critical_count = sum(1 for f in findings if f.get('severity', f.get('risk_level', '')).lower() == 'critical')
        high_count = sum(1 for f in findings if f.get('severity', f.get('risk_level', '')).lower() == 'high')
        medium_count = sum(1 for f in findings if f.get('severity', f.get('risk_level', '')).lower() == 'medium')
        low_count = total_findings - critical_count - high_count - medium_count
        compliance_score = scan_results.get('compliance_score', 75.0)
        
        # === MODERN HEADER WITH GRADIENT ===
        header_drawing = Drawing(540, 70)
        header_drawing.add(Rect(0, 0, 540, 70, fillColor=colors.HexColor('#0f172a'), strokeColor=None))
        header_drawing.add(Rect(0, 0, 540, 4, fillColor=colors.HexColor('#3b82f6'), strokeColor=None))
        header_drawing.add(Rect(0, 66, 540, 4, fillColor=colors.HexColor('#8b5cf6'), strokeColor=None))
        story.append(header_drawing)
        
        # Title
        title_style = ParagraphStyle('ModernTitle', parent=styles['Title'], fontSize=24, textColor=colors.HexColor('#1e3a5f'), spaceAfter=5, alignment=1, fontName='Helvetica-Bold')
        story.append(Paragraph("DataGuardian Pro Report", title_style))
        
        # Scan type subtitle
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#3b82f6'), alignment=1, spaceAfter=8)
        story.append(Paragraph(f"Scan Type: {scan_type}", subtitle_style))
        
        # Metadata line
        meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'), alignment=1, spaceAfter=15)
        story.append(Paragraph(f"Scan ID: {scan_id} | Generated: {report_date} | Region: {region}", meta_style))
        
        # === EXECUTIVE SUMMARY SECTION ===
        section_header = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#1e3a5f'), spaceBefore=20, spaceAfter=15, fontName='Helvetica-Bold')
        story.append(Paragraph("Executive Summary", section_header))
        
        # Create styled paragraphs for metric values
        def styled_value(val, color):
            return Paragraph(f'<font size="26" color="{color}"><b>{val}</b></font>', styles['Normal'])
        
        def styled_label(text):
            return Paragraph(f'<font size="8" color="#6b7280">{text}</font>', styles['Normal'])
        
        # Build metric cards as a 2-row table (values row + labels row)
        values_row = [
            styled_value(files_scanned, '#2563eb'),
            styled_value(total_findings, '#d97706'),
            styled_value(critical_count, '#dc2626'),
            styled_value(high_count, '#ea580c')
        ]
        labels_row = [
            styled_label('Files Scanned'),
            styled_label('Total Findings'),
            styled_label('Critical Issues'),
            styled_label('High Risk')
        ]
        
        metrics_table = Table([values_row, labels_row], colWidths=[1.35*inch, 1.35*inch, 1.35*inch, 1.35*inch])
        metrics_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eff6ff')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#fffbeb')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#fef2f2')),
            ('BACKGROUND', (3, 0), (3, -1), colors.HexColor('#fff7ed')),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 1), (-1, 1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LINEBEFORE', (1, 0), (1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LINEBEFORE', (2, 0), (2, -1), 1, colors.HexColor('#e2e8f0')),
            ('LINEBEFORE', (3, 0), (3, -1), 1, colors.HexColor('#e2e8f0')),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 15))
        
        # Compliance Score with visual indicator
        score_color = '#166534' if compliance_score >= 80 else '#d97706' if compliance_score >= 60 else '#dc2626'
        score_bg = '#dcfce7' if compliance_score >= 80 else '#fef3c7' if compliance_score >= 60 else '#fee2e2'
        score_status = 'Excellent' if compliance_score >= 80 else 'Needs Attention' if compliance_score >= 60 else 'Critical'
        
        score_text = Paragraph(f'<font size="11" color="{score_color}"><b>Compliance Score: {compliance_score:.1f}%</b></font>', styles['Normal'])
        status_text = Paragraph(f'<font size="11" color="{score_color}"><b>{score_status}</b></font>', styles['Normal'])
        
        score_table = Table([[score_text, status_text]], colWidths=[3.5*inch, 1.9*inch])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(score_bg)),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor(score_color)),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 20))
        
        # === DETAILED FINDINGS SECTION ===
        if findings:
            story.append(Paragraph("Detailed Findings", section_header))
            
            for idx, finding in enumerate(findings[:15], 1):  # Limit to 15 for readability
                finding_type = finding.get('type', 'Security Finding')
                severity = finding.get('severity', finding.get('risk_level', 'Medium'))
                severity_lower = severity.lower()
                
                # Severity colors
                if severity_lower == 'critical':
                    sev_color = '#dc2626'
                    sev_bg = '#fef2f2'
                elif severity_lower == 'high':
                    sev_color = '#ea580c'
                    sev_bg = '#fff7ed'
                elif severity_lower == 'medium':
                    sev_color = '#d97706'
                    sev_bg = '#fefce8'
                else:
                    sev_color = '#16a34a'
                    sev_bg = '#f0fdf4'
                
                # Finding card header with severity badge
                finding_title = ParagraphStyle('FindingTitle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#1f2937'), fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=4)
                story.append(Paragraph(f"Finding #{idx}: {finding_type} <font color='{sev_color}'>[{severity.upper()}]</font>", finding_title))
                
                # Source file
                source_file = finding.get('file', finding.get('file_name', finding.get('location', '')))
                if source_file and source_file != 'N/A':
                    file_style = ParagraphStyle('FileInfo', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#3b82f6'), spaceAfter=3)
                    story.append(Paragraph(f"Source: {source_file}", file_style))
                
                # Description
                description = finding.get('description', finding.get('context', ''))
                if description:
                    desc_style = ParagraphStyle('Desc', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#374151'), spaceAfter=4, leftIndent=10)
                    story.append(Paragraph(f"{description[:250]}{'...' if len(description) > 250 else ''}", desc_style))
                
                # Business Impact
                impact = finding.get('business_impact', '')
                if impact:
                    impact_style = ParagraphStyle('Impact', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#7c3aed'), leftIndent=10)
                    story.append(Paragraph(f"Business Impact: {impact[:150]}", impact_style))
                
                # Priority
                priority = finding.get('priority', '')
                if priority:
                    pri_color = '#dc2626' if 'Critical' in priority else '#ea580c' if 'High' in priority else '#6b7280'
                    pri_style = ParagraphStyle('Priority', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor(pri_color), leftIndent=10)
                    story.append(Paragraph(f"Priority: {priority}", pri_style))
                
                # Compliance Requirements
                comp_reqs = finding.get('compliance_requirements', finding.get('gdpr_article', ''))
                if comp_reqs:
                    comp_header = ParagraphStyle('CompHeader', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#1e3a5f'), fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=2, leftIndent=10)
                    story.append(Paragraph("Compliance Requirements:", comp_header))
                    comp_style = ParagraphStyle('CompReq', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#374151'), leftIndent=20)
                    if isinstance(comp_reqs, list):
                        for req in comp_reqs[:3]:
                            story.append(Paragraph(f"• {req}", comp_style))
                    else:
                        story.append(Paragraph(f"• {comp_reqs}", comp_style))
                
                # Recommendations
                recommendations = finding.get('recommendations', finding.get('actionable_recommendations', []))
                if recommendations:
                    rec_header = ParagraphStyle('RecHeader', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#166534'), fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=2, leftIndent=10)
                    story.append(Paragraph("Actionable Recommendations:", rec_header))
                    rec_style = ParagraphStyle('Rec', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#374151'), leftIndent=20)
                    if isinstance(recommendations, list):
                        for rec in recommendations[:3]:
                            if isinstance(rec, dict):
                                story.append(Paragraph(f"• {rec.get('description', rec.get('title', str(rec)))}", rec_style))
                            else:
                                story.append(Paragraph(f"• {rec}", rec_style))
                    else:
                        story.append(Paragraph(f"• {recommendations}", rec_style))
                
                # Separator
                story.append(Spacer(1, 6))
                sep = Drawing(500, 1)
                sep.add(Line(0, 0, 500, 0, strokeColor=colors.HexColor('#e5e7eb'), strokeWidth=0.5))
                story.append(sep)
            
            # Show truncation if needed
            if len(findings) > 15:
                trunc_style = ParagraphStyle('Trunc', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'), alignment=1, spaceBefore=10)
                story.append(Paragraph(f"Showing 15 of {len(findings)} total findings", trunc_style))
        else:
            success_style = ParagraphStyle('Success', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#166534'), alignment=1)
            story.append(Paragraph("No privacy or security issues detected.", success_style))
        
        # === FRAUD DETECTION SECTION ===
        fraud_findings = [f for f in findings if f.get('fraud_analysis')]
        if fraud_findings:
            story.append(PageBreak())
            story.append(Paragraph("AI Fraud Detection Analysis", section_header))
            
            fraud_data = [["Document", "Risk Level", "AI Score", "Detection Model"]]
            for finding in fraud_findings[:10]:
                fraud = finding.get('fraud_analysis', {})
                fraud_data.append([
                    str(finding.get('file_name', 'Unknown'))[:30],
                    str(fraud.get('risk_level', 'N/A')),
                    f"{fraud.get('ai_generated_risk', 0):.0%}",
                    str(fraud.get('ai_model', 'GPT-4'))[:20]
                ])
            
            fraud_table = Table(fraud_data, colWidths=[2.2*inch, 1.2*inch, 1*inch, 1.8*inch])
            fraud_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ddd6fe')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f3ff')])
            ]))
            story.append(fraud_table)
        
        # === PROFESSIONAL FOOTER ===
        story.append(Spacer(1, 30))
        footer_line = Drawing(540, 2)
        footer_line.add(Line(0, 1, 540, 1, strokeColor=colors.HexColor('#1e3a5f'), strokeWidth=1))
        story.append(footer_line)
        story.append(Spacer(1, 8))
        
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'), alignment=1)
        story.append(Paragraph("Generated by DataGuardian Pro - Enterprise Privacy &amp; Sustainability Compliance Platform", footer_style))
        story.append(Paragraph(f"Report ID: {scan_id} | Generated: {report_date}", footer_style))
        story.append(Paragraph("GDPR | UAVG | EU AI Act 2025 | SOC2 Type II Compliant", footer_style))
        
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
