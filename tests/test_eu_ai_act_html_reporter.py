"""
Unit Tests for EU AI Act HTML Report Generator
Tests report generation accuracy and formatting
"""

import pytest
import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.eu_ai_act_html_reporter import (
    generate_eu_ai_act_html_report,
    _calculate_articles_covered,
    _get_chapter_coverage,
    _generate_chapter_coverage_html,
    _generate_findings_table_html,
)


class TestHTMLReportGeneration:
    """Test HTML report generation functionality."""
    
    def test_generate_report_english(self):
        """Test HTML report generation in English."""
        scan_result = {
            'findings': [
                {
                    'type': 'AI_ACT_HIGH_RISK',
                    'category': 'Article 6 - High-Risk Classification',
                    'severity': 'High',
                    'title': 'High-Risk AI System Detected',
                    'description': 'AI system classified as high-risk',
                    'article_reference': 'EU AI Act Article 6'
                }
            ],
            'compliance_score': 75,
            'model_framework': 'PyTorch',
            'model_type': 'Classification Model',
            'file_name': 'test_model.pt',
            'risk_counts': {'low': 1, 'medium': 2, 'high': 1, 'critical': 0}
        }
        
        html = generate_eu_ai_act_html_report(scan_result, language='en')
        
        assert isinstance(html, str)
        assert len(html) > 0
        assert '<!DOCTYPE html>' in html
        assert 'EU AI Act Compliance Report' in html
        assert 'PyTorch' in html
        assert 'Classification Model' in html
    
    def test_generate_report_dutch(self):
        """Test HTML report generation in Dutch."""
        scan_result = {
            'findings': [],
            'compliance_score': 85,
            'model_framework': 'TensorFlow',
            'model_type': 'Regression Model',
            'file_name': 'test_model.h5',
            'risk_counts': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        }
        
        html = generate_eu_ai_act_html_report(scan_result, language='nl')
        
        assert isinstance(html, str)
        assert 'EU AI-wet Nalevingsrapport' in html
        assert 'Nalevingsscore' in html
    
    def test_report_contains_timeline(self):
        """Test that report contains implementation timeline."""
        scan_result = {
            'findings': [],
            'compliance_score': 90,
            'risk_counts': {}
        }
        
        html = generate_eu_ai_act_html_report(scan_result)
        
        assert 'Feb 2, 2025' in html or 'February' in html
        assert 'Aug 2, 2025' in html or 'August' in html
        assert 'Aug 2, 2026' in html
        assert 'Aug 2, 2027' in html
    
    def test_report_contains_chapter_coverage(self):
        """Test that report contains chapter coverage section."""
        scan_result = {
            'findings': [
                {
                    'type': 'AI_ACT_PROHIBITED',
                    'category': 'Article 5 - Prohibited Practices',
                    'article_reference': 'EU AI Act Article 5'
                }
            ],
            'compliance_score': 60,
            'risk_counts': {}
        }
        
        html = generate_eu_ai_act_html_report(scan_result)
        
        assert 'Chapter' in html
        assert 'General Provisions' in html or 'Prohibited' in html
    
    def test_report_compliance_status_colors(self):
        """Test that compliance status uses correct colors."""
        high_compliance = {
            'findings': [],
            'compliance_score': 85,
            'risk_counts': {}
        }
        
        low_compliance = {
            'findings': [],
            'compliance_score': 35,
            'risk_counts': {}
        }
        
        high_html = generate_eu_ai_act_html_report(high_compliance)
        low_html = generate_eu_ai_act_html_report(low_compliance)
        
        assert '#22c55e' in high_html  # Green for compliant
        assert '#ef4444' in low_html   # Red for non-compliant
    
    def test_report_with_empty_findings(self):
        """Test report generation with no findings."""
        scan_result = {
            'findings': [],
            'compliance_score': 100,
            'risk_counts': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        }
        
        html = generate_eu_ai_act_html_report(scan_result)
        
        assert 'No compliance issues detected' in html or 'geen nalevingsproblemen' in html.lower()
    
    def test_report_html_structure(self):
        """Test that report has proper HTML structure."""
        scan_result = {
            'findings': [],
            'compliance_score': 75,
            'risk_counts': {}
        }
        
        html = generate_eu_ai_act_html_report(scan_result)
        
        assert '<html' in html
        assert '</html>' in html
        assert '<head>' in html
        assert '</head>' in html
        assert '<body>' in html
        assert '</body>' in html
        assert '<style>' in html
        assert '</style>' in html


class TestArticleCoverageCalculation:
    """Test article coverage calculation functions."""
    
    def test_calculate_articles_from_findings(self):
        """Test article count calculation from findings."""
        findings = [
            {'type': 'AI_ACT_PROHIBITED', 'article_reference': 'EU AI Act Article 5'},
            {'type': 'AI_ACT_HIGH_RISK', 'article_reference': 'EU AI Act Articles 6-8'},
            {'type': 'AI_ACT_GPAI', 'article_reference': 'EU AI Act Article 51'}
        ]
        
        count = _calculate_articles_covered(findings)
        
        assert count > 0
        assert count <= 113
    
    def test_calculate_articles_with_range(self):
        """Test article count with article ranges."""
        findings = [
            {'type': 'AI_ACT_CE_MARKING', 'article_reference': 'EU AI Act Articles 30-49'}
        ]
        
        count = _calculate_articles_covered(findings)
        
        assert count >= 4  # At least base articles + range
    
    def test_calculate_articles_empty(self):
        """Test article count with no findings."""
        findings = []
        
        count = _calculate_articles_covered(findings)
        
        assert count >= 4  # Base articles 1-4 always included


class TestChapterCoverage:
    """Test chapter coverage calculation."""
    
    def test_get_chapter_coverage(self):
        """Test chapter coverage calculation."""
        findings = [
            {'article_reference': 'EU AI Act Article 5'},
            {'article_reference': 'EU AI Act Articles 9-15'},
            {'article_reference': 'EU AI Act Article 51'}
        ]
        
        coverage = _get_chapter_coverage(findings)
        
        assert isinstance(coverage, dict)
        assert 'Chapter I' in coverage
        assert 'Chapter II' in coverage
        assert 'Chapter III' in coverage
        
        for chapter, data in coverage.items():
            assert 'name' in data
            assert 'articles' in data
            assert 'covered' in data
            assert 'total' in data
            assert 'percentage' in data
    
    def test_chapter_coverage_percentages(self):
        """Test chapter coverage percentage calculations."""
        findings = [
            {'article_reference': 'EU AI Act Article 5'}  # Chapter II has only 1 article
        ]
        
        coverage = _get_chapter_coverage(findings)
        
        for chapter, data in coverage.items():
            assert 0 <= data['percentage'] <= 100
            assert data['covered'] <= data['total']


class TestFindingsTableGeneration:
    """Test findings table HTML generation."""
    
    def test_generate_findings_table(self):
        """Test findings table generation."""
        findings = [
            {
                'severity': 'High',
                'category': 'Article 6 - High-Risk',
                'title': 'High-Risk System Detected',
                'article_reference': 'EU AI Act Article 6'
            },
            {
                'severity': 'Medium',
                'category': 'Article 13 - Transparency',
                'description': 'Transparency requirements not met',
                'article_reference': 'EU AI Act Article 13'
            }
        ]
        
        translations = {
            'risk_level': 'Risk Level',
            'articles_covered': 'Articles'
        }
        
        html = _generate_findings_table_html(findings, translations)
        
        assert '<table' in html
        assert '</table>' in html
        assert 'High' in html
        assert 'Medium' in html
    
    def test_generate_empty_findings_table(self):
        """Test findings table with no findings."""
        findings = []
        translations = {'risk_level': 'Risk', 'articles_covered': 'Articles'}
        
        html = _generate_findings_table_html(findings, translations)
        
        assert html == ''
    
    def test_findings_table_truncation(self):
        """Test that findings table truncates long lists."""
        findings = [
            {
                'severity': 'Low',
                'category': f'Category {i}',
                'title': f'Finding {i}',
                'article_reference': f'Article {i}'
            }
            for i in range(30)  # More than 20 findings
        ]
        
        translations = {'risk_level': 'Risk', 'articles_covered': 'Articles'}
        
        html = _generate_findings_table_html(findings, translations)
        
        row_count = html.count('<tr>')
        assert row_count <= 22  # Header row + max 20 findings + 1


class TestChapterCoverageHTML:
    """Test chapter coverage HTML generation."""
    
    def test_generate_chapter_coverage_html(self):
        """Test chapter coverage HTML generation."""
        chapter_coverage = {
            'Chapter I': {'name': 'General Provisions', 'covered': 4, 'total': 4, 'percentage': 100},
            'Chapter II': {'name': 'Prohibited Practices', 'covered': 1, 'total': 1, 'percentage': 100},
            'Chapter III': {'name': 'High-Risk AI', 'covered': 20, 'total': 44, 'percentage': 45}
        }
        
        html = _generate_chapter_coverage_html(chapter_coverage, 'en')
        
        assert 'Chapter I' in html
        assert 'General Provisions' in html
        assert '100%' in html or '100' in html
        assert '45%' in html or '45' in html
    
    def test_chapter_coverage_colors(self):
        """Test that chapter coverage uses correct colors based on percentage."""
        chapter_coverage = {
            'High': {'name': 'High Coverage', 'covered': 9, 'total': 10, 'percentage': 90},
            'Medium': {'name': 'Medium Coverage', 'covered': 6, 'total': 10, 'percentage': 60},
            'Low': {'name': 'Low Coverage', 'covered': 2, 'total': 10, 'percentage': 20}
        }
        
        html = _generate_chapter_coverage_html(chapter_coverage, 'en')
        
        assert '#22c55e' in html  # Green for high
        assert '#f59e0b' in html  # Yellow for medium  
        assert '#ef4444' in html  # Red for low


class TestReportDataHandling:
    """Test report data handling edge cases."""
    
    def test_missing_fields(self):
        """Test report handles missing fields gracefully."""
        scan_result = {}  # Empty scan result
        
        html = generate_eu_ai_act_html_report(scan_result)
        
        assert isinstance(html, str)
        assert len(html) > 0
    
    def test_malformed_findings(self):
        """Test report handles malformed findings."""
        scan_result = {
            'findings': [
                {},  # Empty finding
                {'type': 'TEST'},  # Minimal finding
                None  # Should be handled gracefully if present
            ],
            'compliance_score': 50
        }
        
        try:
            html = generate_eu_ai_act_html_report(scan_result)
            assert isinstance(html, str)
        except Exception as e:
            pytest.fail(f"Should handle malformed findings gracefully: {e}")
    
    def test_extreme_compliance_scores(self):
        """Test report handles extreme compliance scores."""
        for score in [0, 100, -10, 150]:
            scan_result = {
                'findings': [],
                'compliance_score': score
            }
            
            html = generate_eu_ai_act_html_report(scan_result)
            assert isinstance(html, str)
    
    def test_special_characters_in_content(self):
        """Test report handles special characters."""
        scan_result = {
            'findings': [
                {
                    'type': 'TEST',
                    'title': 'Test with <script> & "quotes"',
                    'description': "Special chars: < > & ' \" €",
                    'article_reference': 'Article 1'
                }
            ],
            'compliance_score': 75,
            'model_framework': 'Test <Framework>',
            'file_name': 'test&file.py'
        }
        
        html = generate_eu_ai_act_html_report(scan_result)
        
        assert isinstance(html, str)


class TestReportAccessibility:
    """Test report accessibility features."""
    
    def test_report_has_lang_attribute(self):
        """Test that HTML has language attribute."""
        html_en = generate_eu_ai_act_html_report({'findings': []}, language='en')
        html_nl = generate_eu_ai_act_html_report({'findings': []}, language='nl')
        
        assert 'lang="en"' in html_en
        assert 'lang="nl"' in html_nl
    
    def test_report_has_meta_charset(self):
        """Test that report has charset meta tag."""
        html = generate_eu_ai_act_html_report({'findings': []})
        
        assert 'charset="UTF-8"' in html or 'charset=UTF-8' in html
    
    def test_report_has_viewport_meta(self):
        """Test that report has viewport meta tag."""
        html = generate_eu_ai_act_html_report({'findings': []})
        
        assert 'viewport' in html


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
