"""
EU AI Act HTML Report Generator
Generates comprehensive HTML reports for EU AI Act compliance assessment
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


def generate_eu_ai_act_html_report(scan_result: Dict[str, Any], language: str = 'en') -> str:
    """
    Generate EU AI Act compliance HTML report for AI model scans.
    
    Args:
        scan_result: AI model scan results
        language: Report language ('en' or 'nl')
        
    Returns:
        HTML string for the compliance report
    """
    translations = {
        'en': {
            'title': 'EU AI Act Compliance Report',
            'subtitle': 'AI Model Compliance Assessment',
            'risk_level': 'Risk Level',
            'compliance_score': 'Compliance Score',
            'findings': 'Findings',
            'recommendations': 'Recommendations',
            'articles_covered': 'Articles Covered',
            'deadline': 'Compliance Deadline',
            'penalty_risk': 'Penalty Risk',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
            'critical': 'Critical',
            'compliant': 'Compliant',
            'non_compliant': 'Non-Compliant',
            'partial': 'Partially Compliant',
            'generated_on': 'Generated on',
            'model_info': 'Model Information',
            'framework': 'Framework',
            'model_type': 'Model Type',
            'file_name': 'File Name',
            'ai_act_coverage': 'EU AI Act Coverage',
            'articles_113': 'of 113 Articles',
            'implementation_timeline': 'Implementation Timeline',
            'phase_1': 'Phase 1 - Prohibited Practices',
            'phase_2': 'Phase 2 - GPAI & Governance',
            'phase_3': 'Phase 3 - Full Application',
            'phase_4': 'Phase 4 - High-Risk Annex I',
            'in_effect': 'In Effect',
            'upcoming': 'Upcoming',
            'remediation_actions': 'Remediation Actions',
            'no_findings': 'No compliance issues detected',
            'chapter_coverage': 'Chapter Coverage',
            'penalty_risk': 'Penalty Risk Assessment',
            'max_fine': 'Maximum Potential Fine',
            'turnover_percentage': 'Turnover Percentage',
            'tier_1_violations': 'Tier 1 (Prohibited)',
            'tier_2_violations': 'Tier 2 (High-Risk)',
            'tier_3_violations': 'Tier 3 (Other)',
            'article_checklist': 'Article Compliance Checklist'
        },
        'nl': {
            'title': 'EU AI-wet Nalevingsrapport',
            'subtitle': 'AI-model Nalevingsbeoordeling',
            'risk_level': 'Risiconiveau',
            'compliance_score': 'Nalevingsscore',
            'findings': 'Bevindingen',
            'recommendations': 'Aanbevelingen',
            'articles_covered': 'Artikelen Gedekt',
            'deadline': 'Nalevingsdeadline',
            'penalty_risk': 'Boeterisico',
            'high': 'Hoog',
            'medium': 'Gemiddeld',
            'low': 'Laag',
            'critical': 'Kritiek',
            'compliant': 'Conform',
            'non_compliant': 'Niet Conform',
            'partial': 'Gedeeltelijk Conform',
            'generated_on': 'Gegenereerd op',
            'model_info': 'Model Informatie',
            'framework': 'Framework',
            'model_type': 'Model Type',
            'file_name': 'Bestandsnaam',
            'ai_act_coverage': 'EU AI-wet Dekking',
            'articles_113': 'van 113 Artikelen',
            'implementation_timeline': 'Implementatietijdlijn',
            'phase_1': 'Fase 1 - Verboden Praktijken',
            'phase_2': 'Fase 2 - GPAI & Governance',
            'phase_3': 'Fase 3 - Volledige Toepassing',
            'phase_4': 'Fase 4 - Hoogrisico Bijlage I',
            'in_effect': 'Van Kracht',
            'upcoming': 'Aanstaande',
            'remediation_actions': 'Herstelacties',
            'no_findings': 'Geen nalevingsproblemen gedetecteerd',
            'chapter_coverage': 'Hoofdstuk Dekking',
            'penalty_risk': 'Boeterisicobeoordeling',
            'max_fine': 'Maximale Potentiële Boete',
            'turnover_percentage': 'Omzetpercentage',
            'tier_1_violations': 'Niveau 1 (Verboden)',
            'tier_2_violations': 'Niveau 2 (Hoog-Risico)',
            'tier_3_violations': 'Niveau 3 (Overig)',
            'article_checklist': 'Artikel Naleving Checklist'
        }
    }
    
    t = translations.get(language, translations['en'])
    
    findings = scan_result.get('findings', [])
    compliance_score = scan_result.get('compliance_score', scan_result.get('ai_model_compliance', 50))
    model_framework = scan_result.get('model_framework', 'Unknown')
    model_type = scan_result.get('model_type', 'AI Model')
    file_name = scan_result.get('file_name', 'Unknown')
    
    risk_counts = scan_result.get('risk_counts', {'low': 0, 'medium': 0, 'high': 0, 'critical': 0})
    
    if compliance_score >= 80:
        compliance_status = t['compliant']
        status_color = '#22c55e'
    elif compliance_score >= 50:
        compliance_status = t['partial']
        status_color = '#f59e0b'
    else:
        compliance_status = t['non_compliant']
        status_color = '#ef4444'
    
    ai_act_findings = [f for f in findings if 'AI_ACT' in f.get('type', '') or 'AI Act' in f.get('category', '')]
    
    articles_covered = _calculate_articles_covered(ai_act_findings)
    coverage_percentage = round((articles_covered / 113) * 100, 1)
    
    chapter_coverage = _get_chapter_coverage(ai_act_findings)
    
    penalty_risk = _calculate_penalty_risk(ai_act_findings)
    
    html = f'''
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{t['title']} - DataGuardian Pro</title>
        <style>
            :root {{
                --primary: #3b82f6;
                --success: #22c55e;
                --warning: #f59e0b;
                --danger: #ef4444;
                --dark: #1e293b;
                --light: #f8fafc;
            }}
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--light); color: var(--dark); line-height: 1.6; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
            .header {{ background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
            .header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
            .header p {{ opacity: 0.9; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
            .card {{ background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .card h3 {{ font-size: 0.875rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }}
            .card .value {{ font-size: 2rem; font-weight: 700; }}
            .score-circle {{ width: 120px; height: 120px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 2rem; font-weight: 700; color: white; }}
            .status-badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 500; }}
            .findings-table {{ width: 100%; border-collapse: collapse; }}
            .findings-table th, .findings-table td {{ padding: 1rem; text-align: left; border-bottom: 1px solid #e2e8f0; }}
            .findings-table th {{ background: #f1f5f9; font-weight: 600; }}
            .severity-high {{ color: #dc2626; }}
            .severity-medium {{ color: #d97706; }}
            .severity-low {{ color: #16a34a; }}
            .severity-critical {{ color: #7c2d12; background: #fef2f2; }}
            .timeline {{ display: flex; flex-direction: column; gap: 1rem; }}
            .timeline-item {{ display: flex; align-items: center; gap: 1rem; padding: 1rem; background: #f8fafc; border-radius: 8px; }}
            .timeline-date {{ font-weight: 600; min-width: 120px; }}
            .timeline-status {{ padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
            .timeline-status.active {{ background: #dcfce7; color: #166534; }}
            .timeline-status.upcoming {{ background: #fef3c7; color: #92400e; }}
            .chapter-bar {{ height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin-top: 0.5rem; }}
            .chapter-fill {{ height: 100%; background: var(--primary); border-radius: 4px; }}
            .footer {{ text-align: center; padding: 2rem; color: #64748b; font-size: 0.875rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{t['title']}</h1>
                <p>{t['subtitle']} - {t['generated_on']} {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>{t['compliance_score']}</h3>
                    <div class="score-circle" style="background: {status_color}">
                        {compliance_score}%
                    </div>
                    <p style="text-align: center; margin-top: 1rem;">
                        <span class="status-badge" style="background: {status_color}20; color: {status_color}">
                            {compliance_status}
                        </span>
                    </p>
                </div>
                
                <div class="card">
                    <h3>{t['ai_act_coverage']}</h3>
                    <div class="value" style="color: var(--primary)">{articles_covered}</div>
                    <p>{t['articles_113']} ({coverage_percentage}%)</p>
                </div>
                
                <div class="card">
                    <h3>{t['model_info']}</h3>
                    <p><strong>{t['framework']}:</strong> {model_framework}</p>
                    <p><strong>{t['model_type']}:</strong> {model_type}</p>
                    <p><strong>{t['file_name']}:</strong> {file_name}</p>
                </div>
                
                <div class="card">
                    <h3>{t['findings']}</h3>
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                        <div><span class="severity-critical">{risk_counts.get('critical', 0)}</span> {t['critical']}</div>
                        <div><span class="severity-high">{risk_counts.get('high', 0)}</span> {t['high']}</div>
                        <div><span class="severity-medium">{risk_counts.get('medium', 0)}</span> {t['medium']}</div>
                        <div><span class="severity-low">{risk_counts.get('low', 0)}</span> {t['low']}</div>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-bottom: 2rem;">
                <h3>{t['chapter_coverage']}</h3>
                {_generate_chapter_coverage_html(chapter_coverage, language)}
            </div>
            
            <div class="card" style="margin-bottom: 2rem;">
                <h3>{t['implementation_timeline']}</h3>
                <div class="timeline">
                    <div class="timeline-item">
                        <span class="timeline-date">Feb 2, 2025</span>
                        <span class="timeline-status active">{t['in_effect']}</span>
                        <span>{t['phase_1']}</span>
                    </div>
                    <div class="timeline-item">
                        <span class="timeline-date">Aug 2, 2025</span>
                        <span class="timeline-status active">{t['in_effect']}</span>
                        <span>{t['phase_2']}</span>
                    </div>
                    <div class="timeline-item">
                        <span class="timeline-date">Aug 2, 2026</span>
                        <span class="timeline-status upcoming">{t['upcoming']}</span>
                        <span>{t['phase_3']}</span>
                    </div>
                    <div class="timeline-item">
                        <span class="timeline-date">Aug 2, 2027</span>
                        <span class="timeline-status upcoming">{t['upcoming']}</span>
                        <span>{t['phase_4']}</span>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-bottom: 2rem;">
                <h3>{t['penalty_risk']}</h3>
                <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">
                    <div>
                        <h4 style="color: #64748b; font-size: 0.75rem; margin-bottom: 0.25rem;">{t['max_fine']}</h4>
                        <div style="font-size: 1.5rem; font-weight: 700; color: {'#ef4444' if penalty_risk['total_violations'] > 0 else '#22c55e'}">
                            {penalty_risk['max_potential_fine']}
                        </div>
                    </div>
                    <div>
                        <h4 style="color: #64748b; font-size: 0.75rem; margin-bottom: 0.25rem;">{t['turnover_percentage']}</h4>
                        <div style="font-size: 1.5rem; font-weight: 700; color: {'#ef4444' if penalty_risk['total_violations'] > 0 else '#22c55e'}">
                            {penalty_risk['max_turnover_percentage']}
                        </div>
                    </div>
                    <div>
                        <h4 style="color: #64748b; font-size: 0.75rem; margin-bottom: 0.25rem;">{t['tier_1_violations']}</h4>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #7c2d12;">
                            {penalty_risk['penalty_tiers']['tier_1_prohibited']}
                        </div>
                    </div>
                    <div>
                        <h4 style="color: #64748b; font-size: 0.75rem; margin-bottom: 0.25rem;">{t['tier_2_violations']}</h4>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #dc2626;">
                            {penalty_risk['penalty_tiers']['tier_2_high_risk']}
                        </div>
                    </div>
                    <div>
                        <h4 style="color: #64748b; font-size: 0.75rem; margin-bottom: 0.25rem;">{t['tier_3_violations']}</h4>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #d97706;">
                            {penalty_risk['penalty_tiers']['tier_3_other']}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-bottom: 2rem;">
                <h3>{t['findings']}</h3>
                {_generate_findings_table_html(ai_act_findings, t) if ai_act_findings else f'<p style="color: #16a34a; padding: 1rem;">{t["no_findings"]}</p>'}
            </div>
            
            <div class="footer">
                <p>DataGuardian Pro - Enterprise Privacy Compliance Platform</p>
                <p>EU AI Act 2025 Compliance Assessment</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html


def _calculate_articles_covered(findings: List[Dict[str, Any]]) -> int:
    """Calculate number of AI Act articles covered by findings."""
    covered_articles = set()
    
    for finding in findings:
        article_ref = finding.get('article_reference', '')
        finding_type = finding.get('type', '')
        category = finding.get('category', '')
        
        if 'Article' in article_ref or 'article' in article_ref.lower():
            import re
            articles = re.findall(r'Article[s]?\s*(\d+)(?:-(\d+))?', article_ref, re.IGNORECASE)
            for match in articles:
                start = int(match[0])
                end = int(match[1]) if match[1] else start
                for i in range(start, end + 1):
                    covered_articles.add(i)
        
        type_article_map = {
            'AI_ACT_PROHIBITED': [5],
            'AI_ACT_HIGH_RISK': [6, 7, 8],
            'AI_ACT_RISK_MANAGEMENT': [9],
            'AI_ACT_DATA_GOVERNANCE': [10, 11, 12],
            'AI_ACT_TRANSPARENCY': [13],
            'AI_ACT_HUMAN_OVERSIGHT': [14, 26],
            'AI_ACT_ACCURACY': [15],
            'AI_ACT_QUALITY_MANAGEMENT': [16],
            'AI_ACT_AUTOMATIC_LOGGING': [17],
            'AI_ACT_PROVIDER_RECORD': [18],
            'AI_ACT_CONFORMITY': [19, 20, 21, 22, 23, 24],
            'AI_ACT_INSTRUCTIONS': [25],
            'AI_ACT_DEPLOYER': [27, 28],
            'AI_ACT_FUNDAMENTAL_RIGHTS': [29],
            'AI_ACT_CE_MARKING': list(range(30, 50)),
            'AI_ACT_TRANSPARENCY_PROVIDER': [50],
            'AI_ACT_GPAI': [51, 52, 53, 54, 55],
            'AI_ACT_SANDBOX': [56, 57, 58, 59, 60],
            'AI_ACT_POST_MARKET': [61, 62, 63, 64, 65, 66, 67, 68],
            'AI_ACT_MARKET_SURVEILLANCE': [69, 70, 71, 72, 73, 74, 75],
            'AI_ACT_PENALTY': [76, 77, 78, 79, 80, 81, 82, 83, 84, 85],
            'AI_ACT_DELEGATION': [86, 87, 88, 89, 90, 91, 92],
            'AI_ACT_COMMITTEE': [93, 94, 95, 96, 97, 98, 99],
            'AI_ACT_FINAL': list(range(100, 114)),
            'AI_ACT_ANNEX_III': [7, 8],
        }
        
        for prefix, articles in type_article_map.items():
            if finding_type.startswith(prefix):
                covered_articles.update(articles)
        
        if 'ARTICLE_' in finding_type:
            import re
            article_match = re.search(r'ARTICLE_(\d+)', finding_type)
            if article_match:
                covered_articles.add(int(article_match.group(1)))
    
    covered_articles.update([1, 2, 3, 4])
    
    return min(len(covered_articles), 113)


def _get_chapter_coverage(findings: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Get coverage by EU AI Act chapter."""
    chapters = {
        'Chapter I': {'name': 'General Provisions', 'articles': list(range(1, 5)), 'covered': 4},
        'Chapter II': {'name': 'Prohibited AI Practices', 'articles': [5], 'covered': 0},
        'Chapter III': {'name': 'High-Risk AI Systems', 'articles': list(range(6, 50)), 'covered': 0},
        'Chapter IV': {'name': 'Transparency Obligations', 'articles': [50, 51, 52], 'covered': 0},
        'Chapter V': {'name': 'GPAI Models', 'articles': [53, 54, 55], 'covered': 0},
        'Chapter VI': {'name': 'Innovation Support', 'articles': list(range(56, 61)), 'covered': 0},
        'Chapter VII': {'name': 'Governance', 'articles': list(range(61, 69)), 'covered': 0},
        'Chapter VIII': {'name': 'Market Surveillance', 'articles': list(range(69, 76)), 'covered': 0},
        'Chapter IX': {'name': 'Penalties', 'articles': list(range(76, 86)), 'covered': 0},
        'Chapter X': {'name': 'Delegation', 'articles': list(range(86, 93)), 'covered': 0},
        'Chapter XI': {'name': 'Committee', 'articles': list(range(93, 100)), 'covered': 0},
        'Chapter XII': {'name': 'Final Provisions', 'articles': list(range(100, 114)), 'covered': 0}
    }
    
    covered_articles = set()
    for finding in findings:
        article_ref = finding.get('article_reference', '')
        finding_type = finding.get('type', '')
        import re
        articles = re.findall(r'Article[s]?\s*(\d+)(?:-(\d+))?', article_ref, re.IGNORECASE)
        for match in articles:
            start = int(match[0])
            end = int(match[1]) if match[1] else start
            for i in range(start, end + 1):
                covered_articles.add(i)
        
        if 'ARTICLE_' in finding_type:
            article_match = re.search(r'ARTICLE_(\d+)', finding_type)
            if article_match:
                covered_articles.add(int(article_match.group(1)))
    
    for chapter, data in chapters.items():
        data['covered'] = len(set(data['articles']) & covered_articles)
        data['total'] = len(data['articles'])
        data['percentage'] = round((data['covered'] / data['total']) * 100) if data['total'] > 0 else 0
    
    return chapters


def _generate_chapter_coverage_html(chapter_coverage: Dict, language: str) -> str:
    """Generate HTML for chapter coverage display."""
    html_parts = []
    for chapter, data in chapter_coverage.items():
        percentage = data.get('percentage', 0)
        color = '#22c55e' if percentage >= 80 else '#f59e0b' if percentage >= 50 else '#ef4444'
        html_parts.append(f'''
            <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span>{chapter}: {data['name']}</span>
                    <span>{data['covered']}/{data['total']} ({percentage}%)</span>
                </div>
                <div class="chapter-bar">
                    <div class="chapter-fill" style="width: {percentage}%; background: {color};"></div>
                </div>
            </div>
        ''')
    return '\n'.join(html_parts)


def _calculate_penalty_risk(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate penalty risk based on violation severity."""
    penalty_tiers = {
        'tier_1': {'max_fine': 35000000, 'percentage': 7, 'violations': []},
        'tier_2': {'max_fine': 15000000, 'percentage': 3, 'violations': []},
        'tier_3': {'max_fine': 7500000, 'percentage': 1.5, 'violations': []}
    }
    
    for finding in findings:
        finding_type = finding.get('type', '')
        severity = finding.get('severity', finding.get('risk_level', 'Medium'))
        
        if 'PROHIBITED' in finding_type or severity == 'Critical':
            penalty_tiers['tier_1']['violations'].append(finding)
        elif 'HIGH_RISK' in finding_type or severity == 'High':
            penalty_tiers['tier_2']['violations'].append(finding)
        else:
            penalty_tiers['tier_3']['violations'].append(finding)
    
    total_max_fine = 0
    max_percentage = 0
    
    for tier, data in penalty_tiers.items():
        if data['violations']:
            total_max_fine = max(total_max_fine, data['max_fine'])
            max_percentage = max(max_percentage, data['percentage'])
    
    return {
        'max_potential_fine': f'€{total_max_fine:,}' if total_max_fine > 0 else '€0',
        'max_turnover_percentage': f'{max_percentage}%',
        'penalty_tiers': {
            'tier_1_prohibited': len(penalty_tiers['tier_1']['violations']),
            'tier_2_high_risk': len(penalty_tiers['tier_2']['violations']),
            'tier_3_other': len(penalty_tiers['tier_3']['violations'])
        },
        'total_violations': len(findings),
        'risk_level': 'Critical' if penalty_tiers['tier_1']['violations'] else ('High' if penalty_tiers['tier_2']['violations'] else 'Medium')
    }


def _generate_findings_table_html(findings: List[Dict[str, Any]], t: Dict[str, str]) -> str:
    """Generate HTML table for findings."""
    if not findings:
        return ''
    
    rows = []
    for finding in findings[:20]:
        severity = finding.get('severity', 'Medium').lower()
        severity_class = f'severity-{severity}'
        category = finding.get('category', 'AI Act Compliance')
        title = finding.get('title', finding.get('description', 'Finding'))[:80]
        article_ref = finding.get('article_reference', '-')
        
        rows.append(f'''
            <tr>
                <td><span class="{severity_class}">{severity.capitalize()}</span></td>
                <td>{category}</td>
                <td>{title}</td>
                <td>{article_ref}</td>
            </tr>
        ''')
    
    return f'''
        <table class="findings-table">
            <thead>
                <tr>
                    <th>{t['risk_level']}</th>
                    <th>Category</th>
                    <th>Finding</th>
                    <th>{t['articles_covered']}</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    '''
