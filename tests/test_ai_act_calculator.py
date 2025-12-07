"""
Unit Tests for AI Act 2025 Compliance Calculator
Comprehensive test suite for risk classification, compliance scoring, and assessment logic
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ai_act_calculator import (
    AIActCalculator,
    AISystemProfile,
    AISystemRiskLevel,
    AIActArticle,
    ComplianceAssessment,
    ComplianceRequirement
)


class TestAISystemProfile:
    """Test AISystemProfile dataclass"""
    
    def test_create_basic_profile(self):
        """Test creating a basic system profile"""
        profile = AISystemProfile(
            system_name="Test System",
            purpose="Test purpose",
            use_case="Customer service automation",
            deployment_context="Private sector - B2B",
            data_types=["Personal data"],
            user_groups=["Customers"],
            decision_impact="Low - Minor convenience",
            automation_level="Human-in-the-loop - All decisions reviewed",
            human_oversight=True,
            data_processing_scope="Small scale - <1000 individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
        
        assert profile.system_name == "Test System"
        assert profile.human_oversight is True
        assert "Netherlands" in profile.geographic_deployment
    
    def test_high_risk_profile(self):
        """Test creating a high-risk system profile"""
        profile = AISystemProfile(
            system_name="Credit Scoring AI",
            purpose="Automated credit risk assessment for loan applications",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Personal data", "Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=False,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands", "European Union"],
            regulatory_context="GDPR + AI Act"
        )
        
        assert profile.use_case == "Credit scoring and financial services"
        assert profile.human_oversight is False


class TestAIActCalculator:
    """Test AIActCalculator class"""
    
    @pytest.fixture
    def calculator(self):
        """Create a calculator instance"""
        return AIActCalculator(region="Netherlands")
    
    @pytest.fixture
    def minimal_risk_profile(self):
        """Create a minimal risk profile"""
        return AISystemProfile(
            system_name="Simple Chatbot",
            purpose="Answer FAQs about products",
            use_case="Other",
            deployment_context="Private sector - B2C",
            data_types=["Public data only"],
            user_groups=["Customers"],
            decision_impact="No impact - Information only",
            automation_level="Human-in-the-loop - All decisions reviewed",
            human_oversight=True,
            data_processing_scope="Small scale - <1000 individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
    
    @pytest.fixture
    def limited_risk_profile(self):
        """Create a limited risk profile"""
        return AISystemProfile(
            system_name="Content Recommender",
            purpose="Recommend products based on browsing history",
            use_case="Content recommendation",
            deployment_context="Private sector - B2C",
            data_types=["Behavioral data"],
            user_groups=["Customers"],
            decision_impact="Low - Minor convenience",
            automation_level="Human-on-the-loop - Human oversight available",
            human_oversight=True,
            data_processing_scope="Medium scale - 1K-10K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
    
    @pytest.fixture
    def high_risk_profile(self):
        """Create a high-risk profile"""
        return AISystemProfile(
            system_name="Credit Scoring System",
            purpose="Automated credit risk assessment for loan applications",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Personal data", "Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=False,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands", "European Union"],
            regulatory_context="GDPR + AI Act"
        )
    
    @pytest.fixture
    def employment_risk_profile(self):
        """Create an employment high-risk profile"""
        return AISystemProfile(
            system_name="HR Screening AI",
            purpose="Automated CV screening and candidate ranking",
            use_case="Employment and recruitment",
            deployment_context="Private sector - B2B",
            data_types=["Personal data"],
            user_groups=["Employees"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=True,
            data_processing_scope="Medium scale - 1K-10K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )


class TestRiskClassification:
    """Test risk classification logic"""
    
    @pytest.fixture
    def calculator(self):
        return AIActCalculator(region="Netherlands")
    
    def test_minimal_risk_classification(self, calculator):
        """Test minimal risk system classification"""
        profile = AISystemProfile(
            system_name="FAQ Bot",
            purpose="Answer simple questions",
            use_case="Other",
            deployment_context="Private sector - B2C",
            data_types=["Public data only"],
            user_groups=["General public"],
            decision_impact="No impact - Information only",
            automation_level="Human-in-the-loop - All decisions reviewed",
            human_oversight=True,
            data_processing_scope="Small scale - <1000 individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
        
        risk_level = calculator.classify_ai_system(profile)
        assert risk_level == AISystemRiskLevel.MINIMAL_RISK
    
    def test_limited_risk_chatbot(self, calculator):
        """Test limited risk chatbot classification"""
        profile = AISystemProfile(
            system_name="Customer Chatbot",
            purpose="Interact with customers via chatbot interface",
            use_case="Customer service automation",
            deployment_context="Private sector - B2C",
            data_types=["Personal data"],
            user_groups=["Customers"],
            decision_impact="Low - Minor convenience",
            automation_level="Human-on-the-loop - Human oversight available",
            human_oversight=True,
            data_processing_scope="Medium scale - 1K-10K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
        
        risk_level = calculator.classify_ai_system(profile)
        assert risk_level == AISystemRiskLevel.LIMITED_RISK
    
    def test_high_risk_credit_scoring(self, calculator):
        """Test high-risk credit scoring classification"""
        profile = AISystemProfile(
            system_name="Credit Score AI",
            purpose="Assess creditworthiness of loan applicants",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Personal data", "Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=False,
            data_processing_scope="Very large scale - >100K individuals",
            geographic_deployment=["Netherlands", "European Union"],
            regulatory_context="GDPR + AI Act"
        )
        
        risk_level = calculator.classify_ai_system(profile)
        assert risk_level == AISystemRiskLevel.HIGH_RISK
    
    def test_high_risk_biometric(self, calculator):
        """Test high-risk biometric identification classification"""
        profile = AISystemProfile(
            system_name="Facial Recognition System",
            purpose="Identify individuals using facial recognition",
            use_case="Biometric identification",
            deployment_context="Public sector",
            data_types=["Biometric data"],
            user_groups=["General public"],
            decision_impact="Critical - Life-changing decisions",
            automation_level="Fully automated - No human intervention",
            human_oversight=False,
            data_processing_scope="Very large scale - >100K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        risk_level = calculator.classify_ai_system(profile)
        assert risk_level == AISystemRiskLevel.HIGH_RISK
    
    def test_high_risk_employment(self, calculator):
        """Test high-risk employment screening classification"""
        profile = AISystemProfile(
            system_name="CV Screening AI",
            purpose="Screen job applicants automatically",
            use_case="Employment and recruitment",
            deployment_context="Private sector - B2B",
            data_types=["Personal data"],
            user_groups=["Employees"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=True,
            data_processing_scope="Medium scale - 1K-10K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        risk_level = calculator.classify_ai_system(profile)
        assert risk_level == AISystemRiskLevel.HIGH_RISK
    
    def test_high_risk_decision_impact(self, calculator):
        """Test that high decision impact triggers high-risk classification"""
        profile = AISystemProfile(
            system_name="Decision System",
            purpose="Make automated decisions",
            use_case="Other",
            deployment_context="Private sector - B2B",
            data_types=["Personal data"],
            user_groups=["Customers"],
            decision_impact="Critical - Life-changing decisions",
            automation_level="Fully automated - No human intervention",
            human_oversight=False,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        risk_level = calculator.classify_ai_system(profile)
        assert risk_level == AISystemRiskLevel.HIGH_RISK


class TestComplianceScoring:
    """Test compliance score calculation"""
    
    @pytest.fixture
    def calculator(self):
        return AIActCalculator(region="Netherlands")
    
    def test_minimal_risk_default_score(self, calculator):
        """Test minimal risk systems get high default score"""
        profile = AISystemProfile(
            system_name="Simple Bot",
            purpose="Basic information",
            use_case="Other",
            deployment_context="Private sector - B2C",
            data_types=["Public data only"],
            user_groups=["General public"],
            decision_impact="No impact - Information only",
            automation_level="Human-in-the-loop - All decisions reviewed",
            human_oversight=True,
            data_processing_scope="Small scale - <1000 individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
        
        score = calculator.calculate_compliance_score(profile, {})
        assert score >= 90.0
    
    def test_high_risk_full_compliance(self, calculator):
        """Test high-risk system with full compliance"""
        profile = AISystemProfile(
            system_name="Credit AI",
            purpose="Credit scoring",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=True,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        full_compliance = {
            "article_8": True,
            "article_9": True,
            "article_10": True,
            "article_11": True,
            "article_12": True,
            "article_13": True,
            "article_14": True,
            "article_15": True,
            "article_16": True,
            "article_17": True,
            "article_26": True,
            "article_27": True,
            "article_29": True
        }
        
        score = calculator.calculate_compliance_score(profile, full_compliance)
        assert score >= 80.0
    
    def test_high_risk_no_compliance(self, calculator):
        """Test high-risk system with no compliance"""
        profile = AISystemProfile(
            system_name="Credit AI",
            purpose="Credit scoring",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=False,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        score = calculator.calculate_compliance_score(profile, {})
        assert score < 20.0


class TestFineRiskCalculation:
    """Test fine risk calculation"""
    
    @pytest.fixture
    def calculator(self):
        return AIActCalculator(region="Netherlands")
    
    def test_minimal_risk_no_fine(self, calculator):
        """Test minimal risk systems have no fine risk"""
        profile = AISystemProfile(
            system_name="Simple Bot",
            purpose="Basic information",
            use_case="Other",
            deployment_context="Private sector - B2C",
            data_types=["Public data only"],
            user_groups=["General public"],
            decision_impact="No impact - Information only",
            automation_level="Human-in-the-loop - All decisions reviewed",
            human_oversight=True,
            data_processing_scope="Small scale - <1000 individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
        
        fine_risk = calculator.calculate_fine_risk(profile, 95.0, 1000000)
        assert fine_risk == 0.0
    
    def test_high_risk_high_compliance_low_fine(self, calculator):
        """Test high-risk with high compliance has reduced fine risk"""
        profile = AISystemProfile(
            system_name="Credit AI",
            purpose="Credit scoring",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=True,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        fine_risk_high_compliance = calculator.calculate_fine_risk(profile, 90.0, 1000000)
        fine_risk_low_compliance = calculator.calculate_fine_risk(profile, 40.0, 1000000)
        
        assert fine_risk_high_compliance < fine_risk_low_compliance
        assert fine_risk_high_compliance < 10000
    
    def test_fine_cap_at_turnover_percentage(self, calculator):
        """Test fine is capped at 7% of annual turnover"""
        profile = AISystemProfile(
            system_name="Credit AI",
            purpose="Credit scoring",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Fully automated - No human intervention",
            human_oversight=False,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        annual_turnover = 100000000
        fine_risk = calculator.calculate_fine_risk(profile, 0.0, annual_turnover)
        
        max_fine = annual_turnover * 0.07
        assert fine_risk <= max_fine


class TestApplicableArticles:
    """Test applicable articles logic"""
    
    @pytest.fixture
    def calculator(self):
        return AIActCalculator(region="Netherlands")
    
    def test_minimal_risk_articles(self, calculator):
        """Test minimal risk gets only basic transparency article"""
        articles = calculator._get_applicable_articles(AISystemRiskLevel.MINIMAL_RISK)
        assert len(articles) == 1
        assert AIActArticle.ARTICLE_13 in articles
    
    def test_limited_risk_articles(self, calculator):
        """Test limited risk gets transparency and oversight articles"""
        articles = calculator._get_applicable_articles(AISystemRiskLevel.LIMITED_RISK)
        assert len(articles) == 2
        assert AIActArticle.ARTICLE_13 in articles
        assert AIActArticle.ARTICLE_14 in articles
    
    def test_high_risk_articles(self, calculator):
        """Test high-risk gets comprehensive articles"""
        articles = calculator._get_applicable_articles(AISystemRiskLevel.HIGH_RISK)
        
        assert len(articles) >= 10
        assert AIActArticle.ARTICLE_9 in articles
        assert AIActArticle.ARTICLE_10 in articles
        assert AIActArticle.ARTICLE_14 in articles
        assert AIActArticle.ARTICLE_15 in articles
        assert AIActArticle.ARTICLE_16 in articles
        assert AIActArticle.ARTICLE_29 in articles


class TestImplementationTimeline:
    """Test implementation timeline generation"""
    
    @pytest.fixture
    def calculator(self):
        return AIActCalculator(region="Netherlands")
    
    def test_minimal_risk_timeline(self, calculator):
        """Test minimal risk gets short timeline"""
        profile = AISystemProfile(
            system_name="Simple Bot",
            purpose="Basic info",
            use_case="Other",
            deployment_context="Private sector - B2C",
            data_types=["Public data only"],
            user_groups=["General public"],
            decision_impact="No impact - Information only",
            automation_level="Human-in-the-loop - All decisions reviewed",
            human_oversight=True,
            data_processing_scope="Small scale - <1000 individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
        
        timeline = calculator.generate_implementation_timeline(profile)
        assert "Week 1" in timeline or "Week 4" in timeline
    
    def test_high_risk_timeline(self, calculator):
        """Test high-risk gets longer timeline"""
        profile = AISystemProfile(
            system_name="Credit AI",
            purpose="Credit scoring",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=True,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        timeline = calculator.generate_implementation_timeline(profile)
        assert "Month 1" in timeline or "Month 6" in timeline


class TestCostEstimation:
    """Test cost estimation logic"""
    
    @pytest.fixture
    def calculator(self):
        return AIActCalculator(region="Netherlands")
    
    def test_minimal_risk_low_cost(self, calculator):
        """Test minimal risk has lower cost"""
        profile = AISystemProfile(
            system_name="Simple Bot",
            purpose="Basic info",
            use_case="Other",
            deployment_context="Private sector - B2C",
            data_types=["Public data only"],
            user_groups=["General public"],
            decision_impact="No impact - Information only",
            automation_level="Human-in-the-loop - All decisions reviewed",
            human_oversight=True,
            data_processing_scope="Small scale - <1000 individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
        
        costs = calculator.estimate_implementation_cost(profile)
        assert "total_estimated_cost" in costs
        assert costs["total_estimated_cost"] < 100000
    
    def test_high_risk_higher_cost(self, calculator):
        """Test high-risk has higher cost"""
        profile = AISystemProfile(
            system_name="Credit AI",
            purpose="Credit scoring",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=True,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        costs = calculator.estimate_implementation_cost(profile)
        assert "total_estimated_cost" in costs
        assert costs["total_estimated_cost"] > 100000
        assert "project_management" in costs
        assert "legal_consultation" in costs


class TestCompleteAssessment:
    """Test complete assessment workflow"""
    
    @pytest.fixture
    def calculator(self):
        return AIActCalculator(region="Netherlands")
    
    def test_complete_assessment_high_risk(self, calculator):
        """Test complete assessment for high-risk system"""
        profile = AISystemProfile(
            system_name="HR Screening AI",
            purpose="Automated candidate screening",
            use_case="Employment and recruitment",
            deployment_context="Private sector - B2B",
            data_types=["Personal data"],
            user_groups=["Employees"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=True,
            data_processing_scope="Medium scale - 1K-10K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        current_compliance = {
            "article_9": True,
            "article_10": True,
            "article_13": True,
            "article_14": True
        }
        
        assessment = calculator.perform_complete_assessment(
            profile, current_compliance, 5000000
        )
        
        assert isinstance(assessment, ComplianceAssessment)
        assert assessment.risk_level == AISystemRiskLevel.HIGH_RISK
        assert 0 <= assessment.compliance_score <= 100
        assert len(assessment.requirements) > 0
        assert len(assessment.recommendations) > 0
        assert "total_estimated_cost" in assessment.cost_estimate
    
    def test_netherlands_specific_recommendations(self, calculator):
        """Test Netherlands-specific recommendations are included"""
        profile = AISystemProfile(
            system_name="Dutch AI System",
            purpose="Process Dutch citizen data",
            use_case="Credit scoring and financial services",
            deployment_context="Financial services",
            data_types=["Personal data", "Financial data"],
            user_groups=["Customers"],
            decision_impact="High - Significant impact on user",
            automation_level="Mostly automated - Minimal human involvement",
            human_oversight=True,
            data_processing_scope="Large scale - 10K-100K individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR + AI Act"
        )
        
        assessment = calculator.perform_complete_assessment(
            profile, {}, 1000000
        )
        
        nl_recommendations = [r for r in assessment.recommendations if "Netherlands" in r or "Dutch" in r or "🇳🇱" in r]
        assert len(nl_recommendations) > 0


class TestReportExport:
    """Test report export functionality"""
    
    @pytest.fixture
    def calculator(self):
        return AIActCalculator(region="Netherlands")
    
    def test_export_assessment_report(self, calculator):
        """Test exporting assessment as JSON report"""
        profile = AISystemProfile(
            system_name="Test System",
            purpose="Testing",
            use_case="Other",
            deployment_context="Private sector - B2C",
            data_types=["Public data only"],
            user_groups=["General public"],
            decision_impact="No impact - Information only",
            automation_level="Human-in-the-loop - All decisions reviewed",
            human_oversight=True,
            data_processing_scope="Small scale - <1000 individuals",
            geographic_deployment=["Netherlands"],
            regulatory_context="GDPR only"
        )
        
        assessment = calculator.perform_complete_assessment(profile, {}, 100000)
        report = calculator.export_assessment_report(assessment)
        
        assert "assessment_id" in report
        assert "timestamp" in report
        assert "region" in report
        assert report["region"] == "Netherlands"
        assert "system_profile" in report
        assert "risk_assessment" in report
        assert "risk_level" in report["risk_assessment"]
        assert "compliance_score" in report["risk_assessment"]
        assert "netherlands_specific" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
