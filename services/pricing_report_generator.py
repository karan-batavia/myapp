"""
Pricing Report Generator
Generates beautiful HTML reports with complete pricing and scanner details
"""

from datetime import datetime
from typing import Dict, List, Any
import base64


def generate_pricing_html_report() -> str:
    """Generate a comprehensive HTML pricing report with all scanner and plan details"""
    
    from config.pricing_config import get_pricing_config, PricingTier
    
    config = get_pricing_config()
    
    scanners = [
        {"id": "code", "name": "Code Scanner", "description": "Detects PII in source code repositories, configuration files, and version control systems", "tier": 1},
        {"id": "document", "name": "Document Scanner", "description": "Analyzes PDF, Word, Excel, and text files for personal data patterns", "tier": 1},
        {"id": "database", "name": "Database Scanner", "description": "Connects to PostgreSQL, MySQL, SQL Server to scan table structures and content", "tier": 1},
        {"id": "image", "name": "Image Scanner (OCR)", "description": "Extracts text from images and screenshots using advanced OCR technology", "tier": 2},
        {"id": "website", "name": "Website Scanner", "description": "Comprehensive privacy and cookie compliance analysis with GDPR checks", "tier": 2},
        {"id": "ai_model", "name": "AI Model Scanner", "description": "EU AI Act 2025 compliance verification and bias detection for ML models", "tier": 2},
        {"id": "dpia", "name": "DPIA Scanner", "description": "Automated Data Protection Impact Assessment wizard per GDPR Article 35", "tier": 3},
        {"id": "soc2", "name": "SOC2/NIS2 Scanner", "description": "Security compliance auditing for SOC2 Type II and NIS2 directive", "tier": 3},
        {"id": "enterprise", "name": "Enterprise Connectors", "description": "Microsoft 365, Google Workspace, Exact Online integration for automated scanning", "tier": 4},
        {"id": "sustainability", "name": "Sustainability Scanner", "description": "Cloud resource efficiency analysis and carbon footprint estimation", "tier": 4},
        {"id": "audio_video", "name": "Audio/Video Deepfake", "description": "AI-powered media authentication and deepfake detection with EU AI Act flagging", "tier": 5},
        {"id": "advanced_ai", "name": "Advanced AI Analysis", "description": "GPT-4 powered deep analysis for complex compliance scenarios", "tier": 5},
    ]
    
    tier_scanner_limits = {
        "trial": 3,
        "startup": 6,
        "professional": 8,
        "growth": 10,
        "scale": 12,
        "enterprise": 12,
    }
    
    plans = []
    for tier_name in ["startup", "professional", "growth", "scale", "enterprise"]:
        tier_data = config.pricing_data['tiers'].get(tier_name, {})
        plans.append({
            "id": tier_name,
            "name": tier_data.get('name', tier_name.title()),
            "description": tier_data.get('description', ''),
            "monthly_price": tier_data.get('monthly_price', 0),
            "annual_price": tier_data.get('annual_price', 0),
            "max_scans": tier_data.get('max_scans_monthly', 'N/A'),
            "max_sources": tier_data.get('max_data_sources', 'N/A'),
            "support": tier_data.get('support_level', 'email'),
            "sla_hours": tier_data.get('sla_hours', 24),
            "scanner_count": tier_scanner_limits.get(tier_name, 6),
            "target_employees": tier_data.get('target_employees', ''),
            "target_revenue": tier_data.get('target_revenue', ''),
            "most_popular": tier_data.get('most_popular', False),
        })
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataGuardian Pro - Complete Pricing & Scanner Guide</title>
    <style>
        :root {{
            --primary: #1e40af;
            --primary-light: #3b82f6;
            --secondary: #059669;
            --accent: #f59e0b;
            --dark: #1f2937;
            --light: #f3f4f6;
            --white: #ffffff;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--dark);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        .report-header {{
            background: var(--white);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        
        .logo {{
            font-size: 2.5em;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        
        .tagline {{
            color: #6b7280;
            font-size: 1.1em;
            margin-bottom: 20px;
        }}
        
        .report-meta {{
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            color: #9ca3af;
            font-size: 0.9em;
        }}
        
        .section {{
            background: var(--white);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--primary-light);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .pricing-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
        }}
        
        .plan-card {{
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .plan-card:hover {{
            border-color: var(--primary-light);
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.15);
        }}
        
        .plan-card.popular {{
            border-color: var(--secondary);
            background: linear-gradient(180deg, #ecfdf5 0%, var(--white) 100%);
        }}
        
        .popular-badge {{
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--secondary);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
        }}
        
        .plan-name {{
            font-size: 1.3em;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 5px;
        }}
        
        .plan-price {{
            font-size: 2.5em;
            font-weight: 800;
            color: var(--primary);
            margin: 15px 0;
        }}
        
        .plan-price span {{
            font-size: 0.4em;
            font-weight: 400;
            color: #6b7280;
        }}
        
        .plan-features {{
            text-align: left;
            margin-top: 20px;
            font-size: 0.9em;
        }}
        
        .plan-features li {{
            list-style: none;
            padding: 8px 0;
            border-bottom: 1px solid #f3f4f6;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .check {{
            color: var(--secondary);
            font-weight: bold;
        }}
        
        .scanner-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .scanner-table th {{
            background: var(--primary);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .scanner-table td {{
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .scanner-table tr:hover {{
            background: #f9fafb;
        }}
        
        .scanner-name {{
            font-weight: 600;
            color: var(--primary);
        }}
        
        .tier-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        
        .tier-1 {{ background: #dbeafe; color: #1e40af; }}
        .tier-2 {{ background: #d1fae5; color: #059669; }}
        .tier-3 {{ background: #fef3c7; color: #d97706; }}
        .tier-4 {{ background: #ede9fe; color: #7c3aed; }}
        .tier-5 {{ background: #fce7f3; color: #db2777; }}
        
        .availability-grid {{
            display: grid;
            grid-template-columns: 2fr repeat(5, 1fr);
            gap: 2px;
            margin-top: 20px;
            font-size: 0.9em;
        }}
        
        .availability-header {{
            background: var(--primary);
            color: white;
            padding: 12px;
            font-weight: 600;
            text-align: center;
        }}
        
        .availability-header:first-child {{
            text-align: left;
        }}
        
        .availability-cell {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
            text-align: center;
        }}
        
        .availability-cell:first-child {{
            text-align: left;
            font-weight: 500;
        }}
        
        .available {{ color: var(--secondary); font-size: 1.3em; }}
        .unavailable {{ color: #d1d5db; font-size: 1.3em; }}
        
        .highlight-box {{
            background: linear-gradient(135deg, #dbeafe 0%, #ede9fe 100%);
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
        }}
        
        .highlight-title {{
            font-size: 1.2em;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 10px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            background: var(--white);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: 800;
            color: var(--primary);
        }}
        
        .stat-label {{
            color: #6b7280;
            font-size: 0.9em;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: white;
            font-size: 0.9em;
        }}
        
        .footer a {{
            color: #fcd34d;
            text-decoration: none;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .section {{
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #e5e7eb;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <div class="logo">🛡️ DataGuardian Pro</div>
            <div class="tagline">Enterprise Privacy Compliance Platform for the Netherlands & Europe</div>
            <div class="report-meta">
                <span>📅 Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}</span>
                <span>🌍 Region: Netherlands (GDPR/UAVG)</span>
                <span>💶 Currency: EUR</span>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📊 Platform Overview</div>
            <div class="highlight-box">
                <div class="highlight-title">Why DataGuardian Pro?</div>
                <p>The only comprehensive privacy compliance platform built specifically for the Netherlands market. 
                Full GDPR, UAVG, and EU AI Act 2025 compliance with native Dutch integrations including Exact Online, 
                BSN validation, and DigiD compatibility.</p>
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">12</div>
                    <div class="stat-label">Specialized Scanners</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">100%</div>
                    <div class="stat-label">GDPR Coverage</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">90%</div>
                    <div class="stat-label">Cost Savings vs Competitors</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">24/7</div>
                    <div class="stat-label">Enterprise Support</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">💰 Pricing Plans</div>
            <div class="pricing-grid">
"""
    
    for plan in plans:
        popular_class = "popular" if plan.get('most_popular') else ""
        popular_badge = '<span class="popular-badge">Most Popular</span>' if plan.get('most_popular') else ""
        
        html += f"""
                <div class="plan-card {popular_class}">
                    {popular_badge}
                    <div class="plan-name">{plan['name']}</div>
                    <div style="color: #6b7280; font-size: 0.85em;">{plan['target_employees']} employees</div>
                    <div class="plan-price">€{plan['monthly_price']}<span>/month</span></div>
                    <div style="color: #059669; font-size: 0.9em;">€{plan['annual_price']}/year (save 2 months)</div>
                    <ul class="plan-features">
                        <li><span class="check">✓</span> {plan['scanner_count']} scanners included</li>
                        <li><span class="check">✓</span> {plan['max_scans']} scans/month</li>
                        <li><span class="check">✓</span> {plan['max_sources']} data sources</li>
                        <li><span class="check">✓</span> {plan['sla_hours']}h SLA response</li>
                    </ul>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🔍 Scanner Details</div>
            <table class="scanner-table">
                <thead>
                    <tr>
                        <th style="width: 20%;">Scanner</th>
                        <th style="width: 50%;">Description</th>
                        <th style="width: 15%;">Availability</th>
                        <th style="width: 15%;">Use Cases</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    tier_names = {1: "Core", 2: "Startup+", 3: "Professional+", 4: "Growth+", 5: "Scale+"}
    for scanner in scanners:
        tier_class = f"tier-{scanner['tier']}"
        tier_label = tier_names.get(scanner['tier'], "Core")
        
        html += f"""
                    <tr>
                        <td><span class="scanner-name">{scanner['name']}</span></td>
                        <td>{scanner['description']}</td>
                        <td><span class="tier-badge {tier_class}">{tier_label}</span></td>
                        <td>GDPR, UAVG</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <div class="section-title">📋 Scanner Availability by Plan</div>
            <div class="availability-grid">
                <div class="availability-header">Scanner</div>
                <div class="availability-header">Startup<br>€59/mo</div>
                <div class="availability-header">Professional<br>€99/mo</div>
                <div class="availability-header">Growth<br>€179/mo</div>
                <div class="availability-header">Scale<br>€499/mo</div>
                <div class="availability-header">Enterprise<br>€1,399/mo</div>
"""
    
    plan_limits = [6, 8, 10, 12, 12]
    for idx, scanner in enumerate(scanners):
        html += f"""
                <div class="availability-cell">{scanner['name']}</div>
"""
        for limit in plan_limits:
            if idx < limit:
                html += '                <div class="availability-cell"><span class="available">✓</span></div>\n'
            else:
                html += '                <div class="availability-cell"><span class="unavailable">—</span></div>\n'
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🇳🇱 Netherlands Specialization</div>
            <div class="highlight-box">
                <div class="highlight-title">Built for Dutch Compliance</div>
                <ul style="margin-top: 10px; margin-left: 20px;">
                    <li><strong>BSN (Burgerservicenummer)</strong> - Automatic detection and validation of Dutch citizen service numbers</li>
                    <li><strong>UAVG Compliance</strong> - Full Uitvoeringswet AVG implementation including specific Dutch requirements</li>
                    <li><strong>Exact Online Integration</strong> - Native connector for the leading Dutch accounting software</li>
                    <li><strong>Dutch Language Support</strong> - Complete interface and reports in Dutch</li>
                    <li><strong>Netherlands Data Residency</strong> - All data processed and stored within EU/NL jurisdiction</li>
                    <li><strong>DigiD Compatible</strong> - Ready for Dutch government authentication standards</li>
                </ul>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🤖 EU AI Act 2025 Compliance</div>
            <p style="margin-bottom: 15px;">DataGuardian Pro provides comprehensive EU AI Act compliance across all 113 articles with phased implementation tracking:</p>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" style="font-size: 1.5em;">Feb 2025</div>
                    <div class="stat-label">Prohibited AI Practices</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="font-size: 1.5em;">Aug 2025</div>
                    <div class="stat-label">GPAI Requirements</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="font-size: 1.5em;">Aug 2026</div>
                    <div class="stat-label">High-Risk AI Systems</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="font-size: 1.5em;">Aug 2027</div>
                    <div class="stat-label">Full Enforcement</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📞 Contact & Support</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                <div>
                    <h4 style="color: var(--primary); margin-bottom: 10px;">Sales Inquiries</h4>
                    <p>📧 sales@dataguardianpro.nl</p>
                    <p>📞 +31 (0)20 123 4567</p>
                </div>
                <div>
                    <h4 style="color: var(--primary); margin-bottom: 10px;">Technical Support</h4>
                    <p>📧 support@dataguardianpro.nl</p>
                    <p>🌐 help.dataguardianpro.nl</p>
                </div>
                <div>
                    <h4 style="color: var(--primary); margin-bottom: 10px;">Enterprise Partnerships</h4>
                    <p>📧 partners@dataguardianpro.nl</p>
                    <p>🏢 Amsterdam, Netherlands</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>© {datetime.now().year} DataGuardian Pro - Enterprise Privacy Compliance Platform</p>
        <p>Built with ❤️ for the Netherlands & European Market</p>
        <p><a href="https://dataguardianpro.nl">dataguardianpro.nl</a></p>
    </div>
</body>
</html>
"""
    
    return html


def get_pricing_report_download_link() -> tuple:
    """Generate download link for pricing report"""
    html_content = generate_pricing_html_report()
    b64 = base64.b64encode(html_content.encode()).decode()
    filename = f"DataGuardian_Pro_Pricing_Report_{datetime.now().strftime('%Y%m%d')}.html"
    return b64, filename, html_content
