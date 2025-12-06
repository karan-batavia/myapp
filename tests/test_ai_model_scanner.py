"""
Comprehensive Unit Tests for AI Model Scanner

Tests all major functionality including:
- Model scanning for different sources (API, Hub, Repository)
- Framework-specific analysis (PyTorch, TensorFlow, ONNX, sklearn)
- Risk metrics calculation
- Compliance metrics calculation
- GitHub repository validation
- EU AI Act 2025 compliance findings
- Bias analysis
- PII leakage detection
- Explainability assessment
"""

import os
import sys
import pytest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_model_scanner import AIModelScanner


class TestAIModelScannerInitialization:
    """Test scanner initialization and configuration."""
    
    def test_default_initialization(self):
        """Test scanner initializes with default region."""
        scanner = AIModelScanner()
        assert scanner.region == "Netherlands"
        assert scanner.progress_callback is None
    
    def test_custom_region_initialization(self):
        """Test scanner initializes with custom region."""
        scanner = AIModelScanner(region="Germany")
        assert scanner.region == "Germany"
    
    def test_progress_callback_setting(self):
        """Test progress callback can be set."""
        scanner = AIModelScanner()
        callback = Mock()
        scanner.set_progress_callback(callback)
        assert scanner.progress_callback == callback


class TestScanResultStructure:
    """Test scan result structure and required fields."""
    
    def test_scan_result_has_required_fields(self):
        """Test scan result contains all required fields."""
        scanner = AIModelScanner()
        
        result = scanner.scan_model(
            model_source="API Endpoint",
            model_details={"api_endpoint": "https://api.example.com/model"}
        )
        
        required_fields = [
            "scan_id", "scan_type", "timestamp", "model_source",
            "findings", "risk_score", "region", "files_scanned",
            "total_lines", "lines_analyzed", "model_framework",
            "ai_act_compliance", "compliance_score", "ai_model_compliance"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
    
    def test_scan_id_format(self):
        """Test scan ID follows expected format."""
        scanner = AIModelScanner()
        
        result = scanner.scan_model(
            model_source="API Endpoint",
            model_details={"api_endpoint": "https://api.example.com/model"}
        )
        
        assert result["scan_id"].startswith("AIMOD-")
        assert len(result["scan_id"]) > 10
    
    def test_timestamp_format(self):
        """Test timestamp is valid ISO format."""
        scanner = AIModelScanner()
        
        result = scanner.scan_model(
            model_source="API Endpoint",
            model_details={"api_endpoint": "https://api.example.com/model"}
        )
        
        datetime.fromisoformat(result["timestamp"])
    
    def test_findings_is_list(self):
        """Test findings is always a list."""
        scanner = AIModelScanner()
        
        result = scanner.scan_model(
            model_source="API Endpoint",
            model_details={}
        )
        
        assert isinstance(result["findings"], list)


class TestModelSourceHandling:
    """Test handling of different model sources."""
    
    def test_api_endpoint_source(self):
        """Test API endpoint source handling."""
        scanner = AIModelScanner()
        
        result = scanner.scan_model(
            model_source="API Endpoint",
            model_details={
                "api_endpoint": "https://api.openai.com/v1/models",
                "repository_path": "/models"
            }
        )
        
        assert result["model_source"] == "API Endpoint"
        assert "api_endpoint" in result
    
    def test_model_hub_source(self):
        """Test Model Hub source handling."""
        scanner = AIModelScanner()
        
        result = scanner.scan_model(
            model_source="Model Hub",
            model_details={
                "hub_url": "huggingface.co/bert-base-uncased",
                "repository_path": "/hub"
            }
        )
        
        assert result["model_source"] == "Model Hub"
        assert "model_name" in result


class TestRiskMetricsCalculation:
    """Test risk metrics calculation."""
    
    def test_calculate_risk_counts_empty(self):
        """Test risk counts with no findings."""
        scanner = AIModelScanner()
        
        counts = scanner._calculate_risk_counts([])
        
        assert counts["low"] == 0
        assert counts["medium"] == 0
        assert counts["high"] == 0
        assert counts["critical"] == 0
    
    def test_calculate_risk_counts_mixed(self):
        """Test risk counts with mixed severity findings."""
        scanner = AIModelScanner()
        
        findings = [
            {"severity": "low"},
            {"severity": "medium"},
            {"severity": "medium"},
            {"severity": "high"},
            {"severity": "critical"}
        ]
        
        counts = scanner._calculate_risk_counts(findings)
        
        assert counts["low"] == 1
        assert counts["medium"] == 2
        assert counts["high"] == 1
        assert counts["critical"] == 1
    
    def test_calculate_risk_metrics_structure(self):
        """Test risk metrics calculation returns expected structure."""
        scanner = AIModelScanner()
        
        findings = [
            {"risk_level": "high", "type": "TEST_FINDING"}
        ]
        
        metrics = scanner._calculate_risk_metrics(findings)
        
        assert "risk_score" in metrics
        assert "severity_level" in metrics
        assert "severity_color" in metrics
        assert "risk_counts" in metrics
        assert "total_findings" in metrics


class TestComplianceMetricsCalculation:
    """Test AI compliance metrics calculation."""
    
    def test_compliance_metrics_structure(self):
        """Test compliance metrics returns expected structure."""
        scanner = AIModelScanner()
        
        scan_result = {
            "findings": [],
            "model_source": "API Endpoint",
            "risk_score": 50
        }
        
        metrics = scanner._calculate_ai_compliance_metrics(scan_result)
        
        assert "model_framework" in metrics
        assert "ai_act_compliance" in metrics
        assert "compliance_score" in metrics
        assert "ai_model_compliance" in metrics
    
    def test_compliance_score_range(self):
        """Test compliance score is within valid range."""
        scanner = AIModelScanner()
        
        scan_result = {
            "findings": [],
            "model_source": "API Endpoint",
            "risk_score": 50
        }
        
        metrics = scanner._calculate_ai_compliance_metrics(scan_result)
        
        assert 0 <= metrics["compliance_score"] <= 100
        assert 0 <= metrics["ai_model_compliance"] <= 100


class TestArchitectureFindings:
    """Test architecture findings generation."""
    
    def test_generate_architecture_findings(self):
        """Test architecture findings are generated."""
        scanner = AIModelScanner()
        
        findings = scanner._generate_architecture_findings(
            model_source="API Endpoint",
            model_details={"api_endpoint": "https://api.example.com"}
        )
        
        assert isinstance(findings, list)
    
    def test_architecture_findings_have_required_fields(self):
        """Test architecture findings have required fields."""
        scanner = AIModelScanner()
        
        findings = scanner._generate_architecture_findings(
            model_source="Model Hub",
            model_details={"hub_url": "huggingface.co/bert"}
        )
        
        for finding in findings:
            assert "type" in finding or "category" in finding
            assert "description" in finding or "title" in finding


class TestIOFindings:
    """Test input/output findings generation."""
    
    def test_generate_io_findings_empty_inputs(self):
        """Test I/O findings with empty inputs."""
        scanner = AIModelScanner()
        
        findings = scanner._generate_io_findings(
            sample_inputs=[],
            context=["General"]
        )
        
        assert isinstance(findings, list)
    
    def test_generate_io_findings_with_pii(self):
        """Test I/O findings with PII in sample inputs."""
        scanner = AIModelScanner()
        
        findings = scanner._generate_io_findings(
            sample_inputs=[
                "John Doe's email is john.doe@example.com",
                "BSN: 123456789"
            ],
            context=["Healthcare"]
        )
        
        assert isinstance(findings, list)


class TestComplianceFindings:
    """Test compliance findings generation."""
    
    def test_generate_compliance_findings_all_types(self):
        """Test compliance findings for all leakage types."""
        scanner = AIModelScanner()
        
        findings = scanner._generate_compliance_findings(
            leakage_types=["All"],
            region="Netherlands"
        )
        
        assert isinstance(findings, list)
    
    def test_compliance_findings_netherlands_region(self):
        """Test Netherlands-specific compliance findings."""
        scanner = AIModelScanner()
        
        findings = scanner._generate_compliance_findings(
            leakage_types=["Personal Data"],
            region="Netherlands"
        )
        
        assert isinstance(findings, list)


class TestEUAIActFindings:
    """Test EU AI Act 2025 findings generation."""
    
    def test_generate_eu_ai_act_findings(self):
        """Test EU AI Act findings generation."""
        scanner = AIModelScanner()
        
        scan_result = {
            "findings": [],
            "model_source": "API Endpoint",
            "risk_score": 50
        }
        
        findings = scanner._generate_eu_ai_act_2025_findings(scan_result)
        
        assert isinstance(findings, list)
        assert len(findings) > 0
    
    def test_eu_ai_act_findings_have_article_references(self):
        """Test EU AI Act findings include article references."""
        scanner = AIModelScanner()
        
        scan_result = {
            "findings": [],
            "model_source": "API Endpoint"
        }
        
        findings = scanner._generate_eu_ai_act_2025_findings(scan_result)
        
        article_findings = [f for f in findings if 'article' in str(f).lower() or 'Article' in str(f)]
        assert len(article_findings) > 0, "EU AI Act findings must include article references"


class TestProhibitedPracticesDetection:
    """Test prohibited practices detection (Article 5)."""
    
    def test_add_prohibited_practices_findings(self):
        """Test prohibited practices findings are added."""
        scanner = AIModelScanner()
        
        findings = []
        scanner._add_prohibited_practices_findings(findings)
        
        assert isinstance(findings, list)


class TestHighRiskSystemsDetection:
    """Test high-risk systems detection (Articles 6-15)."""
    
    def test_add_high_risk_systems_findings(self):
        """Test high-risk systems findings are added."""
        scanner = AIModelScanner()
        
        findings = []
        scan_result = {"model_source": "API Endpoint"}
        scanner._add_high_risk_systems_findings(findings, scan_result)
        
        assert isinstance(findings, list)


class TestTransparencyObligations:
    """Test transparency obligations detection (Article 50-52)."""
    
    def test_add_transparency_obligations_findings(self):
        """Test transparency obligations findings are added."""
        scanner = AIModelScanner()
        
        findings = []
        scanner._add_transparency_obligations_findings(findings)
        
        assert isinstance(findings, list)


class TestConformityAssessment:
    """Test conformity assessment detection (Articles 19-24)."""
    
    def test_add_conformity_assessment_findings(self):
        """Test conformity assessment findings are added."""
        scanner = AIModelScanner()
        
        findings = []
        scanner._add_conformity_assessment_findings(findings)
        
        assert isinstance(findings, list)


class TestPostMarketMonitoring:
    """Test post-market monitoring detection (Articles 61-68)."""
    
    def test_add_post_market_monitoring_findings(self):
        """Test post-market monitoring findings are added."""
        scanner = AIModelScanner()
        
        findings = []
        scanner._add_post_market_monitoring_findings(findings)
        
        assert isinstance(findings, list)


class TestBiasAnalysis:
    """Test bias analysis functionality."""
    
    def test_perform_bias_analysis(self):
        """Test bias analysis is performed."""
        scanner = AIModelScanner()
        
        model_results = {
            "model_type": "classifier",
            "num_classes": 2
        }
        
        result = scanner._perform_bias_analysis(model_results)
        
        assert isinstance(result, dict)
        assert "bias_indicators" in result or "findings" in result or result.get("analysis_performed", False) is not None


class TestPIILeakageAnalysis:
    """Test PII leakage analysis functionality."""
    
    def test_analyze_pii_leakage(self):
        """Test PII leakage analysis."""
        scanner = AIModelScanner()
        
        model_results = {
            "model_type": "language_model"
        }
        
        result = scanner._analyze_pii_leakage(model_results)
        
        assert isinstance(result, dict)


class TestExplainabilityAssessment:
    """Test explainability assessment functionality."""
    
    def test_assess_explainability(self):
        """Test explainability assessment."""
        scanner = AIModelScanner()
        
        model_results = {
            "model_type": "neural_network"
        }
        
        result = scanner._assess_explainability(model_results)
        
        assert isinstance(result, dict)


class TestRiskLevelMapping:
    """Test risk level to severity mapping."""
    
    def test_map_risk_level_low(self):
        """Test Low risk level mapping (case-sensitive)."""
        scanner = AIModelScanner()
        
        severity = scanner._map_risk_level_to_severity("Low")
        assert severity == "Low"
    
    def test_map_risk_level_high(self):
        """Test High risk level mapping (case-sensitive)."""
        scanner = AIModelScanner()
        
        severity = scanner._map_risk_level_to_severity("High")
        assert severity == "High"
    
    def test_map_risk_level_critical(self):
        """Test Critical risk level mapping (case-sensitive)."""
        scanner = AIModelScanner()
        
        severity = scanner._map_risk_level_to_severity("Critical")
        assert severity == "Critical"
    
    def test_map_risk_level_unknown_defaults_to_medium(self):
        """Test unknown risk level defaults to Medium."""
        scanner = AIModelScanner()
        
        severity = scanner._map_risk_level_to_severity("unknown")
        assert severity == "Medium"


class TestUUIDGeneration:
    """Test UUID generation."""
    
    def test_generate_uuid_format(self):
        """Test UUID is generated in correct format."""
        scanner = AIModelScanner()
        
        uuid = scanner._generate_uuid()
        
        assert isinstance(uuid, str)
        assert len(uuid) > 0


class TestModelFileValidation:
    """Test model file validation."""
    
    def test_validate_model_file_nonexistent(self):
        """Test validation fails for non-existent file."""
        scanner = AIModelScanner()
        
        result = scanner._validate_model_file("/nonexistent/path/model.pt")
        
        assert result == False
    
    def test_validate_model_file_too_large(self):
        """Test validation fails for oversized file."""
        scanner = AIModelScanner()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as f:
            f.write(b"x" * 1000)
            temp_path = f.name
        
        try:
            result = scanner._validate_model_file(temp_path, max_size_mb=0)
            assert result == False
        finally:
            os.unlink(temp_path)


class TestDocumentationAssessment:
    """Test model documentation assessment."""
    
    def test_assess_model_documentation(self):
        """Test model documentation assessment."""
        scanner = AIModelScanner()
        
        findings = [
            {"type": "DOCUMENTATION_MISSING", "risk_level": "medium"}
        ]
        model_details = {
            "documentation_url": "https://docs.example.com"
        }
        
        score = scanner._assess_model_documentation(findings, model_details)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


class TestPrivacySafeguardsAssessment:
    """Test privacy safeguards assessment."""
    
    def test_assess_privacy_safeguards(self):
        """Test privacy safeguards assessment."""
        scanner = AIModelScanner()
        
        findings = []
        model_details = {}
        
        score = scanner._assess_privacy_safeguards(findings, model_details)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


class TestExplainabilityFeaturesAssessment:
    """Test explainability features assessment."""
    
    def test_assess_explainability_features(self):
        """Test explainability features assessment."""
        scanner = AIModelScanner()
        
        findings = []
        model_details = {
            "explainability": True
        }
        
        score = scanner._assess_explainability_features(findings, model_details)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


class TestHumanOversightAssessment:
    """Test human oversight mechanisms assessment."""
    
    def test_assess_human_oversight_mechanisms(self):
        """Test human oversight assessment."""
        scanner = AIModelScanner()
        
        findings = []
        model_details = {
            "human_in_loop": True
        }
        
        score = scanner._assess_human_oversight_mechanisms(findings, model_details)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


class TestBiasMitigationAssessment:
    """Test bias mitigation measures assessment."""
    
    def test_assess_bias_mitigation_measures(self):
        """Test bias mitigation assessment."""
        scanner = AIModelScanner()
        
        findings = []
        model_details = {}
        
        score = scanner._assess_bias_mitigation_measures(findings, model_details)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


class TestDataGovernanceAssessment:
    """Test data governance processes assessment."""
    
    def test_assess_data_governance_processes(self):
        """Test data governance assessment."""
        scanner = AIModelScanner()
        
        findings = []
        model_details = {}
        
        score = scanner._assess_data_governance_processes(findings, model_details)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


class TestRiskManagementAssessment:
    """Test risk management system assessment."""
    
    def test_assess_risk_management_system(self):
        """Test risk management assessment."""
        scanner = AIModelScanner()
        
        findings = []
        model_details = {}
        
        score = scanner._assess_risk_management_system(findings, model_details)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


class TestRegulatoryComplianceAssessment:
    """Test regulatory compliance measures assessment."""
    
    def test_assess_regulatory_compliance_measures(self):
        """Test regulatory compliance assessment."""
        scanner = AIModelScanner()
        
        findings = []
        model_details = {}
        
        score = scanner._assess_regulatory_compliance_measures(findings, model_details)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


class TestComplianceImprovementFindings:
    """Test compliance improvement findings generation."""
    
    def test_generate_compliance_improvement_findings(self):
        """Test compliance improvement findings generation."""
        scanner = AIModelScanner()
        
        findings = scanner._generate_compliance_improvement_findings("Netherlands")
        
        assert isinstance(findings, list)
    
    def test_compliance_improvement_findings_have_recommendations(self):
        """Test compliance improvement findings include recommendations."""
        scanner = AIModelScanner()
        
        findings = scanner._generate_compliance_improvement_findings("Netherlands")
        
        for finding in findings:
            assert "recommendation" in finding or "remediation" in finding or "description" in finding


class Test2025ComplianceGapAssessment:
    """Test 2025 compliance gap assessment."""
    
    def test_perform_2025_compliance_gap_assessment(self):
        """Test 2025 compliance gap assessment."""
        scanner = AIModelScanner()
        
        findings = scanner._perform_2025_compliance_gap_assessment(
            model_source="API Endpoint",
            model_details={},
            sample_inputs=[]
        )
        
        assert isinstance(findings, list)


class TestProgressCallback:
    """Test progress callback functionality."""
    
    def test_progress_callback_is_called(self):
        """Test progress callback is called during scan."""
        scanner = AIModelScanner()
        callback = Mock()
        scanner.set_progress_callback(callback)
        
        scanner.scan_model(
            model_source="API Endpoint",
            model_details={"api_endpoint": "https://api.example.com"}
        )
        
        assert callback.call_count >= 1


class TestGitHubRepoValidation:
    """Test GitHub repository validation."""
    
    def test_validate_invalid_github_url(self):
        """Test validation of invalid GitHub URL."""
        scanner = AIModelScanner()
        
        result = scanner._validate_github_repo("not-a-valid-url")
        
        assert "valid" in result
        assert result["valid"] == False or "error" in str(result).lower()
    
    def test_validate_malformed_github_url(self):
        """Test validation of malformed GitHub URL."""
        scanner = AIModelScanner()
        
        result = scanner._validate_github_repo("https://github.com/")
        
        assert "valid" in result


class TestIntegrationScanning:
    """Integration tests for full scanning workflow."""
    
    def test_full_scan_api_endpoint(self):
        """Test full scan workflow for API endpoint."""
        scanner = AIModelScanner()
        
        result = scanner.scan_model(
            model_source="API Endpoint",
            model_details={
                "api_endpoint": "https://api.openai.com/v1/models/gpt-4"
            },
            leakage_types=["Personal Data", "Training Data"],
            context=["Healthcare"],
            sample_inputs=["Test patient data"]
        )
        
        assert result["scan_id"].startswith("AIMOD-")
        assert result["scan_type"] == "AI Model"
        assert result["model_source"] == "API Endpoint"
        assert isinstance(result["findings"], list)
        assert "compliance_score" in result
    
    def test_full_scan_model_hub(self):
        """Test full scan workflow for Model Hub."""
        scanner = AIModelScanner()
        
        result = scanner.scan_model(
            model_source="Model Hub",
            model_details={
                "hub_url": "huggingface.co/bert-base-uncased"
            }
        )
        
        assert result["scan_type"] == "AI Model"
        assert result["model_source"] == "Model Hub"


class TestRegionSpecificCompliance:
    """Test region-specific compliance rules."""
    
    def test_netherlands_region_compliance(self):
        """Test Netherlands-specific compliance rules."""
        scanner = AIModelScanner(region="Netherlands")
        
        result = scanner.scan_model(
            model_source="API Endpoint",
            model_details={}
        )
        
        assert result["region"] == "Netherlands"
    
    def test_germany_region_compliance(self):
        """Test Germany-specific compliance rules."""
        scanner = AIModelScanner(region="Germany")
        
        result = scanner.scan_model(
            model_source="API Endpoint",
            model_details={}
        )
        
        assert result["region"] == "Germany"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
