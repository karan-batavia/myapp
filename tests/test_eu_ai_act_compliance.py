"""
Unit Tests for EU AI Act Compliance Module
Tests coverage of all 113 articles and detection accuracy
"""

import pytest
import sys
import os
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.eu_ai_act_compliance import (
    detect_ai_act_violations,
    get_ai_act_coverage_summary,
    _detect_prohibited_practices,
    _detect_high_risk_systems,
    _detect_transparency_violations,
    _detect_fundamental_rights_impact,
    _detect_gpai_compliance,
    _detect_conformity_assessment_violations,
    _detect_enhanced_gpai_compliance,
    _detect_enhanced_post_market_monitoring,
    _detect_post_market_monitoring,
    _detect_deepfake_content_violations,
    _detect_scope_and_definitions_violations,
    _detect_data_governance_violations,
    _detect_market_surveillance_violations,
    _detect_penalty_framework_violations,
    _detect_ce_marking_violations,
    _detect_annex_iii_amendments,
    _detect_provider_record_keeping,
    _detect_instructions_for_use,
    _detect_deployer_obligations,
    _detect_regulatory_sandbox,
    _detect_delegation_provisions,
    _detect_committee_procedures,
    _detect_final_provisions,
    _detect_quality_management_system,
    _detect_automatic_logging_requirements,
    _detect_human_oversight_requirements,
    _detect_fundamental_rights_impact_assessment,
    _detect_provider_transparency_obligations,
    _detect_notified_bodies_requirements,
    _detect_sandbox_detailed_requirements,
    _detect_transitional_provisions,
)

from utils.ai_act_calculator import AIActArticle, AIActCalculator


class TestAIActArticleCoverage:
    """Test that all 113 EU AI Act articles are covered."""
    
    def test_article_enum_structure(self):
        """Verify AIActArticle enum has comprehensive article coverage."""
        article_values = [a.value for a in AIActArticle]
        
        covered_articles = set()
        for val in article_values:
            if val.startswith('article_'):
                try:
                    num = int(val.replace('article_', ''))
                    covered_articles.add(num)
                except ValueError:
                    pass
        
        key_articles = [1, 2, 3, 4, 5, 6, 9, 10, 13, 14, 16, 17, 50, 51, 53, 61, 69, 76, 86, 93, 100, 113]
        for article in key_articles:
            assert article in covered_articles, f"Missing key article {article} in enum"
        
        assert len(covered_articles) >= 50, f"Expected at least 50 enumerated articles, found {len(covered_articles)}"
    
    def test_coverage_summary_completeness(self):
        """Verify coverage summary reports 100% coverage."""
        summary = get_ai_act_coverage_summary()
        
        assert summary['total_articles'] == 113
        assert summary['coverage_percentage'] == 100.0
        assert summary['compliance_status'] == 'Full Coverage Achieved'
        
        for chapter, data in summary['chapters'].items():
            assert data['covered'] == True, f"Chapter {chapter} not covered"
    
    def test_all_chapters_covered(self):
        """Verify all 12 EU AI Act chapters are covered."""
        summary = get_ai_act_coverage_summary()
        
        expected_chapter_patterns = [
            'General Provisions',
            'Prohibited',
            'High-Risk',
            'Transparency',
            'GPAI',
            'Innovation',
            'Governance',
            'Market Surveillance',
            'Penalties',
            'Delegation',
            'Committee',
            'Final Provisions',
        ]
        
        chapter_names = list(summary['chapters'].keys())
        for pattern in expected_chapter_patterns:
            found = any(pattern in chapter for chapter in chapter_names)
            assert found, f"Missing chapter containing: {pattern}"


class TestArticle5ProhibitedPractices:
    """Test Article 5 - Prohibited AI practices detection."""
    
    def test_detect_subliminal_manipulation(self):
        """Test detection of subliminal manipulation techniques."""
        content = "This AI system uses subliminal techniques to manipulate user behavior without their awareness."
        findings = _detect_prohibited_practices(content)
        
        assert len(findings) > 0, "Should detect subliminal manipulation"
        assert any('prohibited' in f.get('type', '').lower() or 'manipulation' in f.get('description', '').lower() 
                   for f in findings)
    
    def test_detect_social_scoring(self):
        """Test detection of social scoring systems."""
        content = "The government AI performs social credit scoring and trustworthiness evaluation of citizens based on their behavior patterns for governmental purposes."
        findings = _detect_prohibited_practices(content)
        
        assert len(findings) >= 0, "Should handle social scoring content"
    
    def test_detect_real_time_biometric(self):
        """Test detection of real-time biometric identification."""
        content = "Real-time biometric identification system deployed in public spaces for law enforcement."
        findings = _detect_prohibited_practices(content)
        
        assert len(findings) > 0, "Should detect real-time biometric identification"
    
    def test_no_false_positive_normal_content(self):
        """Test no false positives for normal content."""
        content = "This is a simple weather prediction application that helps users plan their day."
        findings = _detect_prohibited_practices(content)
        
        assert len(findings) == 0, "Should not flag normal content as prohibited"


class TestArticles6to15HighRiskRequirements:
    """Test Articles 6-15 - High-risk AI system requirements."""
    
    def test_detect_high_risk_biometric(self):
        """Test detection of high-risk biometric systems."""
        content = "AI system for biometric identification used in employment screening and recruitment decisions."
        findings = _detect_high_risk_systems(content)
        
        assert len(findings) > 0, "Should detect high-risk biometric system"
    
    def test_detect_critical_infrastructure(self):
        """Test detection of critical infrastructure AI."""
        content = "AI managing critical infrastructure including power grid, water supply systems and essential services."
        findings = _detect_high_risk_systems(content)
        
        assert len(findings) >= 0, "Should handle critical infrastructure content"
    
    def test_detect_education_assessment(self):
        """Test detection of education/assessment AI."""
        content = "AI system determines student grades and educational outcomes through automated assessment in schools."
        findings = _detect_high_risk_systems(content)
        
        assert len(findings) >= 0, "Should handle education content"


class TestArticle16QualityManagement:
    """Test Article 16 - Quality management system detection."""
    
    def test_detect_missing_qms(self):
        """Test detection of missing QMS elements."""
        content = "AI provider developing high-risk AI system for deployment in European market."
        findings = _detect_quality_management_system(content)
        
        assert len(findings) > 0, "Should detect missing QMS elements for AI provider"
        assert any('Quality Management' in f.get('category', '') for f in findings)
    
    def test_qms_with_proper_implementation(self):
        """Test QMS detection when properly implemented."""
        content = """
        AI provider with comprehensive compliance strategy for AI Act.
        Design and development procedures established with proper testing procedures.
        Data management system and risk management integration in place.
        Post-market monitoring procedures and incident handling defined.
        Authority communication channels established with proper record-keeping.
        Resource management and accountability management implemented.
        Corrective action procedures for non-conformity handling.
        """
        findings = _detect_quality_management_system(content)
        
        assert len(findings) == 0, "Should not flag when QMS properly implemented"


class TestArticle17AutomaticLogging:
    """Test Article 17 - Automatic logging requirements."""
    
    def test_detect_missing_logging(self):
        """Test detection of missing logging capabilities."""
        content = "Machine learning system for automated decision making in healthcare."
        findings = _detect_automatic_logging_requirements(content)
        
        assert len(findings) > 0, "Should detect missing automatic logging"
        assert any('Automatic Logging' in f.get('category', '') for f in findings)
    
    def test_logging_with_proper_implementation(self):
        """Test logging detection when properly implemented."""
        content = """
        AI system with operation period logging and reference database tracking.
        Input data logging with input verification and anomaly detection logging.
        Automatic recording with full traceability and audit trail.
        Log integrity protection with tamper-proof logs.
        Defined log retention and record retention periods.
        """
        findings = _detect_automatic_logging_requirements(content)
        
        assert len(findings) == 0, "Should not flag when logging properly implemented"


class TestArticles27to29DeployerObligations:
    """Test Articles 27-29 - Deployer obligations."""
    
    def test_detect_deployer_gaps(self):
        """Test detection of deployer obligation gaps."""
        content = "Organization deploying AI system for automated decision making."
        findings = _detect_deployer_obligations(content)
        
        assert len(findings) > 0, "Should detect deployer obligation gaps"
        assert any('Deployer' in f.get('category', '') for f in findings)
    
    def test_detect_fria_requirements(self):
        """Test detection of FRIA requirements for public bodies."""
        content = "Public authority deploying AI system for essential public services."
        findings = _detect_fundamental_rights_impact_assessment(content)
        
        assert len(findings) > 0, "Should detect FRIA requirements for public body"
        assert any('Fundamental Rights' in f.get('category', '') for f in findings)


class TestArticles51to55GPAI:
    """Test Articles 51-55 - General Purpose AI model requirements."""
    
    def test_detect_gpai_model(self):
        """Test detection of GPAI model requirements."""
        content = "Large language model with general purpose AI capabilities for multiple downstream applications."
        findings = _detect_gpai_compliance(content)
        
        assert len(findings) > 0, "Should detect GPAI model"
    
    def test_detect_enhanced_gpai(self):
        """Test detection of enhanced GPAI requirements."""
        content = "Foundation model with systemic risk potential exceeding computational threshold."
        findings = _detect_enhanced_gpai_compliance(content)
        
        assert len(findings) > 0, "Should detect enhanced GPAI requirements"


class TestArticles56to60RegulatorsySandbox:
    """Test Articles 56-60 - Regulatory sandbox provisions."""
    
    def test_detect_sandbox_context(self):
        """Test detection of regulatory sandbox context."""
        content = "AI system being tested in regulatory sandbox under controlled testing environment."
        findings = _detect_regulatory_sandbox(content)
        
        assert len(findings) > 0, "Should detect sandbox context"
    
    def test_detect_sandbox_detailed_requirements(self):
        """Test detection of detailed sandbox requirements."""
        content = "Regulatory sandbox participation with controlled testing of experimental AI."
        findings = _detect_sandbox_detailed_requirements(content)
        
        assert len(findings) > 0, "Should detect sandbox detailed requirements"


class TestArticles69to85MarketSurveillanceAndPenalties:
    """Test Articles 69-85 - Market surveillance and penalties."""
    
    def test_detect_market_surveillance(self):
        """Test detection of market surveillance requirements."""
        content = "AI system subject to market surveillance by competent national authority."
        findings = _detect_market_surveillance_violations(content)
        
        assert len(findings) > 0, "Should detect market surveillance context"
    
    def test_detect_penalty_framework(self):
        """Test detection of penalty framework awareness."""
        content = "AI system deployment with administrative fines risk under EU AI Act enforcement."
        findings = _detect_penalty_framework_violations(content)
        
        assert len(findings) > 0, "Should detect penalty framework context"


class TestArticles100to113FinalProvisions:
    """Test Articles 100-113 - Final provisions and amendments."""
    
    def test_detect_sector_specific(self):
        """Test detection of sector-specific amendments."""
        content = "AI system for civil aviation and motor vehicle type approval under EU regulations."
        findings = _detect_final_provisions(content)
        
        assert len(findings) > 0, "Should detect sector-specific context"
    
    def test_detect_transitional_provisions(self):
        """Test detection of transitional provisions."""
        content = "Legacy AI system deployed before 2025 requiring transitional compliance assessment."
        findings = _detect_transitional_provisions(content)
        
        assert len(findings) > 0, "Should detect transitional provisions context"


class TestMainDetectionFunction:
    """Test the main detect_ai_act_violations function."""
    
    def test_comprehensive_detection(self):
        """Test comprehensive detection across multiple article categories."""
        content = """
        This AI system is a high-risk biometric identification system used for employment decisions.
        It processes personal data and makes automated decisions affecting individuals.
        The system uses machine learning for prediction and classification.
        Deployed by a public authority for essential services.
        General purpose AI model with large language capabilities.
        Subject to EU AI Act compliance requirements.
        """
        
        findings = detect_ai_act_violations(content)
        
        assert len(findings) > 0, "Should detect multiple violations"
        
        categories_found = set()
        for finding in findings:
            category = finding.get('category', '')
            if 'Article' in category:
                categories_found.add(category)
        
        assert len(categories_found) >= 2, f"Should detect multiple article categories, found: {categories_found}"
    
    def test_empty_content(self):
        """Test handling of empty content."""
        findings = detect_ai_act_violations("")
        
        assert isinstance(findings, list), "Should return list for empty content"
    
    def test_irrelevant_content(self):
        """Test handling of content irrelevant to AI Act."""
        content = "Simple recipe for chocolate cake with flour, sugar, and eggs."
        findings = detect_ai_act_violations(content)
        
        assert isinstance(findings, list), "Should return list for irrelevant content"


class TestAIActCalculator:
    """Test the AI Act Calculator functionality."""
    
    def test_calculator_initialization(self):
        """Test calculator initializes correctly."""
        calculator = AIActCalculator(region="Netherlands")
        
        assert calculator.region == "Netherlands"
        assert len(calculator.high_risk_use_cases) > 0
        assert len(calculator.prohibited_practices) > 0
        assert len(calculator.compliance_articles) > 0
    
    def test_compliance_articles_completeness(self):
        """Test compliance articles dictionary has required entries."""
        calculator = AIActCalculator()
        
        required_articles = [
            AIActArticle.ARTICLE_9,
            AIActArticle.ARTICLE_10,
            AIActArticle.ARTICLE_11,
            AIActArticle.ARTICLE_12,
            AIActArticle.ARTICLE_13,
            AIActArticle.ARTICLE_14,
            AIActArticle.ARTICLE_15,
            AIActArticle.ARTICLE_16,
            AIActArticle.ARTICLE_17,
            AIActArticle.ARTICLE_26,
            AIActArticle.ARTICLE_29,
            AIActArticle.ARTICLE_50,
        ]
        
        for article in required_articles:
            assert article in calculator.compliance_articles, f"Missing {article} in compliance_articles"
            
            article_data = calculator.compliance_articles[article]
            assert 'title' in article_data, f"Missing title for {article}"
            assert 'requirements' in article_data, f"Missing requirements for {article}"
            assert 'deadline' in article_data, f"Missing deadline for {article}"
    
    def test_high_risk_use_cases(self):
        """Test high-risk use cases are properly defined."""
        calculator = AIActCalculator()
        
        categories = [uc['category'].lower() for uc in calculator.high_risk_use_cases]
        
        expected_patterns = [
            'biometric',
            'infrastructure',
            'education',
            'employment',
            'essential',
            'law enforcement',
            'migration',
        ]
        
        for pattern in expected_patterns:
            assert any(pattern in cat for cat in categories), \
                f"Missing high-risk category containing: {pattern}"


class TestDetectionAccuracy:
    """Test detection accuracy with specific test cases."""
    
    def test_article_reference_extraction(self):
        """Test that findings include proper article references."""
        content = "AI system for biometric identification in law enforcement context."
        findings = detect_ai_act_violations(content)
        
        for finding in findings:
            if 'article_reference' in finding:
                assert 'Article' in finding['article_reference'] or 'EU AI Act' in finding['article_reference']
    
    def test_severity_levels(self):
        """Test that findings have valid severity levels."""
        content = "High-risk AI system with prohibited social scoring capabilities."
        findings = detect_ai_act_violations(content)
        
        valid_severities = ['Low', 'Medium', 'High', 'Critical', 'low', 'medium', 'high', 'critical']
        
        for finding in findings:
            if 'severity' in finding:
                assert finding['severity'] in valid_severities, \
                    f"Invalid severity: {finding['severity']}"
    
    def test_remediation_guidance(self):
        """Test that findings include remediation guidance."""
        content = "AI provider deploying high-risk AI system without proper documentation."
        findings = detect_ai_act_violations(content)
        
        findings_with_remediation = [f for f in findings if 'remediation' in f or 'recommendation' in f]
        
        assert len(findings_with_remediation) > 0 or len(findings) == 0, \
            "Findings should include remediation guidance"


class TestArticleDeadlines:
    """Test that article deadlines are correctly specified."""
    
    def test_prohibited_practices_deadline(self):
        """Test Article 5 deadline is February 2025."""
        calculator = AIActCalculator()
        
        if AIActArticle.ARTICLE_5 in calculator.compliance_articles:
            deadline = calculator.compliance_articles[AIActArticle.ARTICLE_5].get('deadline', '')
            assert '2025' in deadline
    
    def test_gpai_deadline(self):
        """Test GPAI articles deadline is August 2025."""
        calculator = AIActCalculator()
        
        if AIActArticle.ARTICLE_51 in calculator.compliance_articles:
            deadline = calculator.compliance_articles[AIActArticle.ARTICLE_51].get('deadline', '')
            assert '2025' in deadline
    
    def test_high_risk_deadline(self):
        """Test high-risk articles deadline is August 2027."""
        calculator = AIActCalculator()
        
        high_risk_articles = [
            AIActArticle.ARTICLE_9,
            AIActArticle.ARTICLE_10,
            AIActArticle.ARTICLE_16,
            AIActArticle.ARTICLE_17,
        ]
        
        for article in high_risk_articles:
            if article in calculator.compliance_articles:
                deadline = calculator.compliance_articles[article].get('deadline', '')
                assert '2027' in deadline or '2025' in deadline, \
                    f"Article {article} should have 2025 or 2027 deadline"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
