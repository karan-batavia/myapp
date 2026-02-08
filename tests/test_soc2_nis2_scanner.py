"""
Unit Tests for SOC2 & NIS2 Compliance Scanner

Tests cover:
1. SOC2 Trust Services Criteria (TSC) mapping
2. NIS2 EU Directive 2022/2555 article mapping
3. IaC file scanning for compliance issues
4. Finding generation with dual-framework references
5. Risk pattern detection across technologies
"""

import pytest
import os
import tempfile
import json
from datetime import datetime

from services.soc2_scanner import (
    SOC2_CATEGORIES,
    SOC2_TSC_MAPPING,
    NIS2_CATEGORIES,
    NIS2_ARTICLE_MAPPING,
    FINDING_TO_TSC_MAP,
    FINDING_TO_NIS2_MAP,
    NIS2_CATEGORY_TO_ARTICLES,
    CATEGORY_TO_TSC_MAP,
    scan_iac_file,
    identify_iac_technology,
    TERRAFORM_RISK_PATTERNS,
    CLOUDFORMATION_RISK_PATTERNS,
    KUBERNETES_RISK_PATTERNS,
    DOCKER_RISK_PATTERNS,
    JAVASCRIPT_RISK_PATTERNS
)


class TestSOC2Categories:
    """Test SOC2 Trust Services Categories"""
    
    def test_soc2_categories_complete(self):
        """Verify all 5 SOC2 TSC categories are defined"""
        expected_categories = ["security", "availability", "processing_integrity", 
                               "confidentiality", "privacy"]
        for category in expected_categories:
            assert category in SOC2_CATEGORIES
            assert isinstance(SOC2_CATEGORIES[category], str)
    
    def test_soc2_tsc_mapping_complete(self):
        """Verify SOC2 TSC criteria are properly mapped"""
        assert len(SOC2_TSC_MAPPING) > 30
        
        cc_criteria = [k for k in SOC2_TSC_MAPPING.keys() if k.startswith("CC")]
        assert len(cc_criteria) >= 30
        
        availability_criteria = [k for k in SOC2_TSC_MAPPING.keys() if k.startswith("A")]
        assert len(availability_criteria) >= 3
        
        privacy_criteria = [k for k in SOC2_TSC_MAPPING.keys() if k.startswith("P")]
        assert len(privacy_criteria) >= 8
    
    def test_category_to_tsc_mapping(self):
        """Verify category to TSC criteria mapping"""
        assert "security" in CATEGORY_TO_TSC_MAP
        assert "availability" in CATEGORY_TO_TSC_MAP
        assert "privacy" in CATEGORY_TO_TSC_MAP
        
        assert "CC6.1" in CATEGORY_TO_TSC_MAP["security"]
        assert "A1.1" in CATEGORY_TO_TSC_MAP["availability"]


class TestNIS2Categories:
    """Test NIS2 EU Directive Categories and Articles"""
    
    def test_nis2_categories_complete(self):
        """Verify NIS2 10 mandatory security measure categories"""
        expected_categories = [
            "risk_management", "incident_handling", "business_continuity",
            "supply_chain", "network_security", "access_control",
            "cryptography", "asset_management", "cybersecurity_training",
            "vulnerability_management"
        ]
        for category in expected_categories:
            assert category in NIS2_CATEGORIES, f"Missing NIS2 category: {category}"
    
    def test_nis2_article_mapping_comprehensive(self):
        """Verify NIS2 article mapping covers key directive sections"""
        assert len(NIS2_ARTICLE_MAPPING) >= 40
        
        chapter_1_articles = [k for k in NIS2_ARTICLE_MAPPING.keys() 
                            if k.startswith("NIS2-1") or k.startswith("NIS2-2") or k.startswith("NIS2-6")]
        assert len(chapter_1_articles) >= 3
        
        article_20_keys = [k for k in NIS2_ARTICLE_MAPPING.keys() if k.startswith("NIS2-20")]
        assert len(article_20_keys) >= 4
        
        article_21_keys = [k for k in NIS2_ARTICLE_MAPPING.keys() if k.startswith("NIS2-21")]
        assert len(article_21_keys) >= 11
        
        article_22_keys = [k for k in NIS2_ARTICLE_MAPPING.keys() if k.startswith("NIS2-22")]
        assert len(article_22_keys) >= 3
        
        article_23_keys = [k for k in NIS2_ARTICLE_MAPPING.keys() if k.startswith("NIS2-23")]
        assert len(article_23_keys) >= 4
        
        article_34_keys = [k for k in NIS2_ARTICLE_MAPPING.keys() if k.startswith("NIS2-34")]
        assert len(article_34_keys) >= 3
    
    def test_nis2_key_requirements_present(self):
        """Verify key NIS2 requirements are documented"""
        assert "NIS2-21.2a" in NIS2_ARTICLE_MAPPING
        assert "incident" in NIS2_ARTICLE_MAPPING["NIS2-21.2a"].lower()
        
        assert "NIS2-21.2b" in NIS2_ARTICLE_MAPPING
        assert "business continuity" in NIS2_ARTICLE_MAPPING["NIS2-21.2b"].lower()
        
        assert "NIS2-21.2g" in NIS2_ARTICLE_MAPPING
        assert "cryptography" in NIS2_ARTICLE_MAPPING["NIS2-21.2g"].lower()
        
        assert "NIS2-21.2i" in NIS2_ARTICLE_MAPPING
        assert "multi-factor" in NIS2_ARTICLE_MAPPING["NIS2-21.2i"].lower() or "mfa" in NIS2_ARTICLE_MAPPING["NIS2-21.2i"].lower()
        
        assert "NIS2-23.1" in NIS2_ARTICLE_MAPPING
        assert "24-hour" in NIS2_ARTICLE_MAPPING["NIS2-23.1"].lower() or "24 hour" in NIS2_ARTICLE_MAPPING["NIS2-23.1"].lower()
    
    def test_nis2_penalties_documented(self):
        """Verify NIS2 penalty structure is documented per Article 34"""
        essential_penalty = NIS2_ARTICLE_MAPPING.get("NIS2-34.4", "")
        assert "10" in essential_penalty or "essential" in essential_penalty.lower()
        
        important_penalty = NIS2_ARTICLE_MAPPING.get("NIS2-34.5", "")
        assert "7" in important_penalty or "important" in important_penalty.lower()
    
    def test_nis2_annexes_documented(self):
        """Verify NIS2 annexes for sector classification"""
        assert "NIS2-ANNEX-I" in NIS2_ARTICLE_MAPPING
        assert "essential" in NIS2_ARTICLE_MAPPING["NIS2-ANNEX-I"].lower()
        
        assert "NIS2-ANNEX-II" in NIS2_ARTICLE_MAPPING
        assert "important" in NIS2_ARTICLE_MAPPING["NIS2-ANNEX-II"].lower()


class TestFindingMappings:
    """Test finding to compliance framework mappings"""
    
    def test_finding_to_soc2_mapping(self):
        """Verify findings are mapped to SOC2 TSC criteria"""
        assert len(FINDING_TO_TSC_MAP) >= 15
        
        assert "Hard-coded AWS access keys" in FINDING_TO_TSC_MAP
        assert "CC6.1" in FINDING_TO_TSC_MAP["Hard-coded AWS access keys"]
        
        assert "Resource with backups disabled" in FINDING_TO_TSC_MAP
        assert any("A1" in c for c in FINDING_TO_TSC_MAP["Resource with backups disabled"])
    
    def test_finding_to_nis2_mapping(self):
        """Verify findings are mapped to NIS2 articles"""
        assert len(FINDING_TO_NIS2_MAP) >= 25
        
        assert "Hard-coded AWS access keys" in FINDING_TO_NIS2_MAP
        assert "NIS2-21.2g" in FINDING_TO_NIS2_MAP["Hard-coded AWS access keys"]
        
        assert "Resource with backups disabled" in FINDING_TO_NIS2_MAP
        assert "NIS2-21.2b" in FINDING_TO_NIS2_MAP["Resource with backups disabled"]
        
        assert "Resource without logging configured" in FINDING_TO_NIS2_MAP
        assert "NIS2-23.1" in FINDING_TO_NIS2_MAP["Resource without logging configured"]
    
    def test_nis2_category_to_articles_mapping(self):
        """Verify NIS2 category fallback mapping"""
        assert len(NIS2_CATEGORY_TO_ARTICLES) == 10
        
        assert "risk_management" in NIS2_CATEGORY_TO_ARTICLES
        assert "NIS2-21.1" in NIS2_CATEGORY_TO_ARTICLES["risk_management"]
        
        assert "incident_handling" in NIS2_CATEGORY_TO_ARTICLES
        assert "NIS2-23.1" in NIS2_CATEGORY_TO_ARTICLES["incident_handling"]


class TestRiskPatterns:
    """Test IaC risk pattern detection"""
    
    def test_terraform_patterns_defined(self):
        """Verify Terraform security patterns are defined"""
        assert len(TERRAFORM_RISK_PATTERNS) >= 10
        
        has_hardcoded_keys = any("access_key" in p or "secret" in p 
                                  for p in TERRAFORM_RISK_PATTERNS.keys())
        assert has_hardcoded_keys
        
        has_ingress_pattern = any("ingress" in p for p in TERRAFORM_RISK_PATTERNS.keys())
        assert has_ingress_pattern
    
    def test_cloudformation_patterns_defined(self):
        """Verify CloudFormation security patterns are defined"""
        assert len(CLOUDFORMATION_RISK_PATTERNS) >= 3
    
    def test_kubernetes_patterns_defined(self):
        """Verify Kubernetes security patterns are defined"""
        assert len(KUBERNETES_RISK_PATTERNS) >= 3
    
    def test_docker_patterns_defined(self):
        """Verify Docker security patterns are defined"""
        assert len(DOCKER_RISK_PATTERNS) >= 3
    
    def test_javascript_patterns_defined(self):
        """Verify JavaScript/Node.js security patterns are defined"""
        assert len(JAVASCRIPT_RISK_PATTERNS) >= 5


class TestIaCFileScanningUnit:
    """Unit tests for IaC file scanning"""
    
    def test_identify_terraform_technology(self):
        """Test Terraform file identification"""
        with tempfile.NamedTemporaryFile(suffix='.tf', delete=False, mode='w') as f:
            f.write('''
provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "example" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
}
''')
            f.flush()
            tech = identify_iac_technology(f.name)
            os.unlink(f.name)
            assert tech == "terraform"
    
    def test_identify_kubernetes_technology(self):
        """Test Kubernetes file identification"""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w') as f:
            f.write('''
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: nginx
''')
            f.flush()
            tech = identify_iac_technology(f.name)
            os.unlink(f.name)
            assert tech == "kubernetes"
    
    def test_identify_docker_technology(self):
        """Test Dockerfile identification"""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write('''
FROM ubuntu:latest
RUN apt-get update
CMD ["bash"]
''')
            f.flush()
            tech = identify_iac_technology(f.name)
            os.unlink(f.name)
            assert tech == "docker"
    
    def test_scan_terraform_hardcoded_secrets(self):
        """Test scanning Terraform for hardcoded secrets"""
        with tempfile.NamedTemporaryFile(suffix='.tf', delete=False, mode='w') as f:
            f.write('''
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  region = "us-west-2"
}
''')
            f.flush()
            findings = scan_iac_file(f.name)
            os.unlink(f.name)
            
            assert len(findings) >= 1
            descriptions = [f.get('description', '') for f in findings]
            assert any('access key' in d.lower() or 'secret' in d.lower() 
                      for d in descriptions)
    
    def test_scan_terraform_unrestricted_ingress(self):
        """Test scanning Terraform for unrestricted ingress"""
        with tempfile.NamedTemporaryFile(suffix='.tf', delete=False, mode='w') as f:
            f.write('''
resource "aws_security_group" "allow_all" {
  name = "allow_all"
  
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
''')
            f.flush()
            findings = scan_iac_file(f.name)
            os.unlink(f.name)
            
            assert len(findings) >= 1
    
    def test_scan_finding_includes_soc2_mapping(self):
        """Test that findings include SOC2 TSC criteria"""
        with tempfile.NamedTemporaryFile(suffix='.tf', delete=False, mode='w') as f:
            f.write('''
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  region = "us-west-2"
}
''')
            f.flush()
            findings = scan_iac_file(f.name)
            os.unlink(f.name)
            
            if findings:
                finding = findings[0]
                assert 'soc2_tsc_criteria' in finding
                assert 'soc2_tsc_details' in finding
    
    def test_scan_finding_includes_nis2_mapping(self):
        """Test that findings include NIS2 article references"""
        with tempfile.NamedTemporaryFile(suffix='.tf', delete=False, mode='w') as f:
            f.write('''
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  region = "us-west-2"
}
''')
            f.flush()
            findings = scan_iac_file(f.name)
            os.unlink(f.name)
            
            if findings:
                finding = findings[0]
                assert 'nis2_articles' in finding
                assert 'nis2_details' in finding


class TestNIS2ComplianceCoverage:
    """Test NIS2 compliance coverage completeness"""
    
    def test_nis2_article_21_complete(self):
        """Verify Article 21 (Risk Management Measures) is fully covered"""
        article_21_subsections = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        
        for subsection in article_21_subsections:
            key = f"NIS2-21.2{subsection}"
            assert key in NIS2_ARTICLE_MAPPING, f"Missing NIS2-21.2{subsection}"
    
    def test_nis2_incident_reporting_complete(self):
        """Verify Article 23 (Incident Reporting) requirements"""
        required_articles = ["NIS2-23.1", "NIS2-23.2", "NIS2-23.3", "NIS2-23.4"]
        
        for article in required_articles:
            assert article in NIS2_ARTICLE_MAPPING, f"Missing {article}"
    
    def test_nis2_governance_articles_present(self):
        """Verify governance articles (Article 20) are present"""
        required_articles = ["NIS2-20.1", "NIS2-20.2", "NIS2-20.3", "NIS2-20.4"]
        
        for article in required_articles:
            assert article in NIS2_ARTICLE_MAPPING, f"Missing {article}"
    
    def test_nis2_supply_chain_articles_present(self):
        """Verify supply chain security articles (Article 22) are present"""
        required_articles = ["NIS2-22.1", "NIS2-22.2", "NIS2-22.3"]
        
        for article in required_articles:
            assert article in NIS2_ARTICLE_MAPPING, f"Missing {article}"


class TestSOC2ComplianceCoverage:
    """Test SOC2 compliance coverage completeness"""
    
    def test_soc2_common_criteria_complete(self):
        """Verify SOC2 Common Criteria (CC) are covered"""
        expected_cc = [
            "CC1.1", "CC1.2", "CC1.3", "CC1.4",
            "CC2.1", "CC2.2", "CC2.3",
            "CC3.1", "CC3.2", "CC3.3", "CC3.4",
            "CC4.1", "CC4.2",
            "CC5.1", "CC5.2", "CC5.3",
            "CC6.1", "CC6.2", "CC6.3", "CC6.4", "CC6.5", "CC6.6", "CC6.7", "CC6.8",
            "CC7.1", "CC7.2", "CC7.3", "CC7.4", "CC7.5",
            "CC8.1",
            "CC9.1", "CC9.2"
        ]
        
        for cc in expected_cc:
            assert cc in SOC2_TSC_MAPPING, f"Missing {cc}"
    
    def test_soc2_availability_criteria_complete(self):
        """Verify SOC2 Availability criteria are covered"""
        expected_a = ["A1.1", "A1.2", "A1.3"]
        
        for a in expected_a:
            assert a in SOC2_TSC_MAPPING, f"Missing {a}"
    
    def test_soc2_privacy_criteria_complete(self):
        """Verify SOC2 Privacy criteria are covered"""
        expected_p = ["P1.1", "P2.1", "P3.1", "P3.2", "P4.1", "P5.1", "P6.1", "P7.1", "P8.1"]
        
        for p in expected_p:
            assert p in SOC2_TSC_MAPPING, f"Missing {p}"


class TestDualFrameworkIntegration:
    """Test integration of SOC2 and NIS2 in findings"""
    
    def test_critical_findings_map_to_both_frameworks(self):
        """Verify critical security findings map to both SOC2 and NIS2"""
        critical_findings = [
            "Hard-coded AWS access keys",
            "Possible hard-coded password",
            "Security group with unrestricted ingress"
        ]
        
        for finding in critical_findings:
            assert finding in FINDING_TO_TSC_MAP, f"{finding} missing SOC2 mapping"
            assert finding in FINDING_TO_NIS2_MAP, f"{finding} missing NIS2 mapping"
    
    def test_business_continuity_findings_map_correctly(self):
        """Verify business continuity findings map to NIS2-21.2b"""
        bc_findings = [
            "Resource with backups disabled",
            "S3 bucket without versioning"
        ]
        
        for finding in bc_findings:
            if finding in FINDING_TO_NIS2_MAP:
                assert "NIS2-21.2b" in FINDING_TO_NIS2_MAP[finding]
    
    def test_incident_handling_findings_map_correctly(self):
        """Verify incident handling findings map to NIS2-23.x"""
        ih_findings = ["Resource without logging configured"]
        
        for finding in ih_findings:
            if finding in FINDING_TO_NIS2_MAP:
                articles = FINDING_TO_NIS2_MAP[finding]
                assert any("NIS2-23" in a or "NIS2-21.2a" in a for a in articles)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
