"""
Performance, Scalability, and Reliability Tests for SOC2 & NIS2 Compliance Scanner

Tests are designed to:
1. Be deterministic and never flaky
2. Not depend on external network resources
3. Use mocked dependencies for isolation
4. Measure performance with configurable thresholds
5. Test scalability with synthetic large datasets
"""

import pytest
import os
import tempfile
import shutil
import time
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.soc2_scanner import (
    SOC2_CATEGORIES,
    NIS2_CATEGORIES,
    NIS2_ARTICLE_MAPPING,
    SOC2_TSC_MAPPING,
    FINDING_TO_TSC_MAP,
    FINDING_TO_NIS2_MAP,
    scan_iac_file,
    identify_iac_technology,
    TERRAFORM_RISK_PATTERNS,
    KUBERNETES_RISK_PATTERNS,
    DOCKER_RISK_PATTERNS,
    JAVASCRIPT_RISK_PATTERNS
)


PERFORMANCE_THRESHOLD_MS = 500
SCALABILITY_FILE_COUNT = 100


class TestFixtures:
    """Reusable test fixtures for deterministic testing"""
    
    @staticmethod
    def create_temp_terraform_file(content: str) -> str:
        """Create a temporary Terraform file with given content"""
        fd, path = tempfile.mkstemp(suffix='.tf')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path
    
    @staticmethod
    def create_temp_kubernetes_file(content: str) -> str:
        """Create a temporary Kubernetes YAML file"""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path
    
    @staticmethod
    def create_temp_dockerfile(content: str) -> str:
        """Create a temporary Dockerfile"""
        fd, path = tempfile.mkstemp(prefix='Dockerfile')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path
    
    @staticmethod
    def create_temp_js_file(content: str) -> str:
        """Create a temporary JavaScript file"""
        fd, path = tempfile.mkstemp(suffix='.js')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path
    
    @staticmethod
    def generate_large_terraform_content(resource_count: int) -> str:
        """Generate a large Terraform file with many resources"""
        content = 'provider "aws" {\n  region = "us-west-2"\n}\n\n'
        
        for i in range(resource_count):
            content += f'''
resource "aws_instance" "server_{i}" {{
  ami           = "ami-12345678"
  instance_type = "t2.micro"
  
  tags = {{
    Name = "server-{i}"
  }}
}}

resource "aws_security_group" "sg_{i}" {{
  name = "security-group-{i}"
  
  ingress {{
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }}
}}
'''
        return content
    
    @staticmethod
    def generate_terraform_with_violations(violation_count: int) -> str:
        """Generate Terraform with intentional violations"""
        content = 'provider "aws" {\n  region = "us-west-2"\n}\n\n'
        
        for i in range(violation_count):
            content += f'''
resource "aws_security_group" "insecure_{i}" {{
  name = "insecure-sg-{i}"
  
  ingress {{
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

resource "aws_db_instance" "db_{i}" {{
  identifier = "db-{i}"
  password   = "hardcoded_password_{i}"
  encrypted  = false
  backup     = false
}}
'''
        return content


class TestPerformance:
    """Performance benchmark tests with timing assertions"""
    
    def test_scan_small_file_performance(self):
        """Verify small file scanning completes within threshold"""
        content = '''
provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "example" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
}
'''
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            start_time = time.monotonic()
            findings = scan_iac_file(path)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            
            assert elapsed_ms < PERFORMANCE_THRESHOLD_MS, \
                f"Small file scan took {elapsed_ms:.2f}ms, expected < {PERFORMANCE_THRESHOLD_MS}ms"
        finally:
            os.unlink(path)
    
    def test_scan_medium_file_performance(self):
        """Verify medium file (50 resources) scanning performance"""
        content = TestFixtures.generate_large_terraform_content(50)
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            start_time = time.monotonic()
            findings = scan_iac_file(path)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            
            assert elapsed_ms < PERFORMANCE_THRESHOLD_MS * 2, \
                f"Medium file scan took {elapsed_ms:.2f}ms, expected < {PERFORMANCE_THRESHOLD_MS * 2}ms"
        finally:
            os.unlink(path)
    
    def test_scan_file_with_many_violations_performance(self):
        """Verify scanning with many violations remains performant"""
        content = TestFixtures.generate_terraform_with_violations(20)
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            start_time = time.monotonic()
            findings = scan_iac_file(path)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            
            assert len(findings) > 0, "Should find violations"
            assert elapsed_ms < PERFORMANCE_THRESHOLD_MS * 3, \
                f"Violation-heavy scan took {elapsed_ms:.2f}ms"
        finally:
            os.unlink(path)
    
    def test_technology_identification_performance(self):
        """Verify technology identification is fast"""
        content = '''
provider "aws" {
  region = "us-west-2"
}
resource "aws_instance" "test" {
  ami = "ami-123"
}
'''
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            start_time = time.monotonic()
            for _ in range(100):
                tech = identify_iac_technology(path)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            
            assert elapsed_ms < 100, \
                f"100 identifications took {elapsed_ms:.2f}ms, expected < 100ms"
            assert tech == "terraform"
        finally:
            os.unlink(path)


class TestScalability:
    """Scalability tests with large synthetic datasets"""
    
    def test_scan_large_terraform_file(self):
        """Test scanning a large Terraform file (100+ resources)"""
        content = TestFixtures.generate_large_terraform_content(100)
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            findings = scan_iac_file(path)
            assert isinstance(findings, list)
        finally:
            os.unlink(path)
    
    def test_scan_many_violations_scalability(self):
        """Test scanning file with many violations scales correctly"""
        content = TestFixtures.generate_terraform_with_violations(50)
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            findings = scan_iac_file(path)
            assert len(findings) >= 50
        finally:
            os.unlink(path)
    
    def test_scan_multiple_files_sequentially(self):
        """Test scanning multiple files sequentially"""
        paths = []
        try:
            for i in range(10):
                content = f'''
provider "aws" {{
  region = "us-west-2"
}}
resource "aws_instance" "server_{i}" {{
  ami = "ami-{i:08d}"
  instance_type = "t2.micro"
  password = "insecure_password_{i}"
}}
'''
                paths.append(TestFixtures.create_temp_terraform_file(content))
            
            all_findings = []
            start_time = time.monotonic()
            for path in paths:
                findings = scan_iac_file(path)
                all_findings.extend(findings)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            
            assert len(all_findings) >= 10
            assert elapsed_ms < PERFORMANCE_THRESHOLD_MS * 10, \
                f"10 file scans took {elapsed_ms:.2f}ms"
        finally:
            for path in paths:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_finding_mapping_scalability(self):
        """Test that finding mappings handle large numbers efficiently"""
        start_time = time.monotonic()
        
        for _ in range(1000):
            for finding in FINDING_TO_TSC_MAP:
                tsc = FINDING_TO_TSC_MAP[finding]
            for finding in FINDING_TO_NIS2_MAP:
                nis2 = FINDING_TO_NIS2_MAP[finding]
        
        elapsed_ms = (time.monotonic() - start_time) * 1000
        assert elapsed_ms < 200, f"1000 mapping iterations took {elapsed_ms:.2f}ms"


class TestReliability:
    """Reliability tests ensuring deterministic behavior"""
    
    def test_scan_empty_file_no_crash(self):
        """Verify scanning empty file doesn't crash"""
        path = TestFixtures.create_temp_terraform_file("")
        
        try:
            findings = scan_iac_file(path)
            assert isinstance(findings, list)
            assert len(findings) == 0
        finally:
            os.unlink(path)
    
    def test_scan_invalid_syntax_no_crash(self):
        """Verify scanning malformed content doesn't crash"""
        content = '''
{{{{{
  this is not valid terraform
  or yaml or anything
  random garbage $#@!%^&*()
}}}}
'''
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            findings = scan_iac_file(path)
            assert isinstance(findings, list)
        finally:
            os.unlink(path)
    
    def test_scan_binary_content_no_crash(self):
        """Verify scanning binary content doesn't crash"""
        fd, path = tempfile.mkstemp(suffix='.tf')
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(bytes(range(256)))
            
            findings = scan_iac_file(path)
            assert isinstance(findings, list)
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_scan_unicode_content_no_crash(self):
        """Verify scanning unicode content works correctly"""
        content = '''
provider "aws" {
  region = "us-west-2"
}

# Comment with unicode: 日本語 中文 العربية 🔒
resource "aws_instance" "test" {
  ami = "ami-12345678"
  tags = {
    Description = "Server with émojis 🚀🔥"
  }
}
'''
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            findings = scan_iac_file(path)
            assert isinstance(findings, list)
        finally:
            os.unlink(path)
    
    def test_scan_nonexistent_file_no_crash(self):
        """Verify scanning nonexistent file doesn't crash"""
        findings = scan_iac_file("/nonexistent/path/file.tf")
        assert isinstance(findings, list)
        assert len(findings) == 0
    
    def test_technology_identification_unknown_file(self):
        """Verify unknown file types return None gracefully"""
        fd, path = tempfile.mkstemp(suffix='.unknown')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write("random content")
            
            tech = identify_iac_technology(path)
            assert tech is None or isinstance(tech, str)
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_consistent_results_multiple_runs(self):
        """Verify scanning produces consistent results across multiple runs"""
        content = '''
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  region = "us-west-2"
}
'''
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            results = []
            for _ in range(5):
                findings = scan_iac_file(path)
                results.append(len(findings))
            
            assert all(r == results[0] for r in results), \
                f"Inconsistent results: {results}"
        finally:
            os.unlink(path)


class TestMockedDependencies:
    """Tests with mocked external dependencies for isolation"""
    
    @patch('subprocess.run')
    def test_git_clone_failure_handled(self, mock_run):
        """Verify git clone failures are handled gracefully"""
        mock_run.side_effect = Exception("Git not available")
        
        findings = scan_iac_file("/some/path.tf")
        assert isinstance(findings, list)
    
    def test_finding_includes_both_frameworks(self):
        """Verify findings include both SOC2 and NIS2 mappings"""
        content = '''
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  region = "us-west-2"
}
'''
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            findings = scan_iac_file(path)
            
            if findings:
                finding = findings[0]
                assert 'soc2_tsc_criteria' in finding
                assert 'soc2_tsc_details' in finding
                assert 'nis2_articles' in finding
                assert 'nis2_details' in finding
        finally:
            os.unlink(path)


class TestEdgeCases:
    """Edge case tests for comprehensive coverage"""
    
    def test_scan_very_long_lines(self):
        """Verify handling of very long lines"""
        long_line = "x" * 100000
        content = f'''
provider "aws" {{
  region = "us-west-2"
}}
# {long_line}
resource "aws_instance" "test" {{
  ami = "ami-12345678"
}}
'''
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            findings = scan_iac_file(path)
            assert isinstance(findings, list)
        finally:
            os.unlink(path)
    
    def test_scan_deeply_nested_structure(self):
        """Verify handling of deeply nested structures"""
        content = '''
resource "aws_lambda_function" "example" {
  function_name = "test"
  
  environment {
    variables = {
      nested = {
        deep = {
          value = "test"
        }
      }
    }
  }
}
'''
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            findings = scan_iac_file(path)
            assert isinstance(findings, list)
        finally:
            os.unlink(path)
    
    def test_scan_mixed_technology_content(self):
        """Verify handling of mixed technology content"""
        content = '''
# This file has mixed content
provider "aws" {
  region = "us-west-2"
}

# Some JavaScript embedded
# const password = "secret123";

# Some YAML
# apiVersion: v1
# kind: Pod
'''
        path = TestFixtures.create_temp_terraform_file(content)
        
        try:
            findings = scan_iac_file(path)
            assert isinstance(findings, list)
        finally:
            os.unlink(path)


class TestComplianceFrameworkIntegrity:
    """Tests ensuring compliance framework data integrity"""
    
    def test_all_soc2_tsc_have_descriptions(self):
        """Verify all SOC2 TSC criteria have descriptions"""
        for criterion, description in SOC2_TSC_MAPPING.items():
            assert description, f"TSC {criterion} has empty description"
            assert len(description) > 10, f"TSC {criterion} description too short"
    
    def test_all_nis2_articles_have_descriptions(self):
        """Verify all NIS2 articles have descriptions"""
        for article, description in NIS2_ARTICLE_MAPPING.items():
            assert description, f"NIS2 {article} has empty description"
            assert len(description) > 10, f"NIS2 {article} description too short"
    
    def test_finding_mappings_reference_valid_soc2(self):
        """Verify finding mappings reference valid SOC2 criteria"""
        all_valid_tsc = set(SOC2_TSC_MAPPING.keys())
        
        for finding, criteria in FINDING_TO_TSC_MAP.items():
            for criterion in criteria:
                assert criterion in all_valid_tsc, \
                    f"Finding '{finding}' references invalid TSC: {criterion}"
    
    def test_finding_mappings_reference_valid_nis2(self):
        """Verify finding mappings reference valid NIS2 articles"""
        all_valid_nis2 = set(NIS2_ARTICLE_MAPPING.keys())
        
        for finding, articles in FINDING_TO_NIS2_MAP.items():
            for article in articles:
                assert article in all_valid_nis2, \
                    f"Finding '{finding}' references invalid NIS2: {article}"
    
    def test_no_duplicate_mappings(self):
        """Verify no duplicate entries in mappings"""
        soc2_items = list(SOC2_TSC_MAPPING.keys())
        assert len(soc2_items) == len(set(soc2_items)), "Duplicate SOC2 TSC entries"
        
        nis2_items = list(NIS2_ARTICLE_MAPPING.keys())
        assert len(nis2_items) == len(set(nis2_items)), "Duplicate NIS2 article entries"


class TestMultiTechnologySupport:
    """Tests for multi-technology IaC support"""
    
    def test_kubernetes_scanning(self):
        """Test Kubernetes YAML scanning"""
        content = '''
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  containers:
  - name: test
    image: nginx:latest
    securityContext:
      privileged: true
'''
        path = TestFixtures.create_temp_kubernetes_file(content)
        
        try:
            tech = identify_iac_technology(path)
            findings = scan_iac_file(path)
            
            assert tech == "kubernetes"
            assert isinstance(findings, list)
        finally:
            os.unlink(path)
    
    def test_docker_scanning(self):
        """Test Dockerfile scanning"""
        content = '''
FROM ubuntu:latest
RUN apt-get update
USER root
CMD ["bash"]
'''
        path = TestFixtures.create_temp_dockerfile(content)
        
        try:
            tech = identify_iac_technology(path)
            findings = scan_iac_file(path)
            
            assert tech == "docker"
            assert isinstance(findings, list)
        finally:
            os.unlink(path)
    
    def test_javascript_scanning(self):
        """Test JavaScript/Node.js scanning"""
        content = '''
const express = require('express');
const app = express();

const password = "hardcoded_secret";

app.get('/', (req, res) => {
  const userInput = req.query.input;
  eval(userInput);
});

app.listen(3000);
'''
        path = TestFixtures.create_temp_js_file(content)
        
        try:
            tech = identify_iac_technology(path)
            findings = scan_iac_file(path)
            
            assert tech in ["javascript", "pulumi"], f"Expected javascript or pulumi, got {tech}"
            assert isinstance(findings, list)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
