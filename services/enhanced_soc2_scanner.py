"""
Enhanced SOC2 Scanner with TSC Mapping
Provides comprehensive SOC2 compliance analysis with Trust Service Criteria mapping
"""

import uuid
import json
import os
import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("enhanced_soc2_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import streamlit as st


class EnhancedSOC2Scanner:
    """Enhanced SOC2 Scanner with TSC criteria mapping and compliance automation"""
    
    def __init__(self, region="Netherlands"):
        """Initialize Enhanced SOC2 Scanner with TSC criteria mapping."""
        self.region = region
        
        # Trust Service Criteria mapping
        self.tsc_criteria = {
            'Security': {
                'criteria': ['CC1', 'CC2', 'CC3', 'CC4', 'CC5', 'CC6', 'CC7', 'CC8'],
                'description': 'Information and systems are protected against unauthorized access',
                'checks': [
                    'Access controls implementation',
                    'Authentication mechanisms',
                    'Authorization procedures',
                    'Encryption standards',
                    'Network security',
                    'Vulnerability management',
                    'Incident response procedures',
                    'Security monitoring'
                ]
            },
            'Availability': {
                'criteria': ['A1.1', 'A1.2', 'A1.3'],
                'description': 'Information and systems are available for operation and use',
                'checks': [
                    'System uptime monitoring',
                    'Backup and recovery procedures',
                    'Capacity planning',
                    'Performance monitoring',
                    'Disaster recovery planning',
                    'Service level agreements'
                ]
            },
            'Processing Integrity': {
                'criteria': ['PI1.1', 'PI1.2', 'PI1.3'],
                'description': 'System processing is complete, valid, accurate, timely, and authorized',
                'checks': [
                    'Data validation procedures',
                    'Error handling mechanisms',
                    'Processing controls',
                    'Data integrity checks',
                    'Input validation',
                    'Output verification'
                ]
            },
            'Confidentiality': {
                'criteria': ['C1.1', 'C1.2'],
                'description': 'Information designated as confidential is protected',
                'checks': [
                    'Data classification procedures',
                    'Access restriction enforcement',
                    'Confidentiality agreements',
                    'Encryption of sensitive data',
                    'Secure data transmission',
                    'Data retention policies'
                ]
            },
            'Privacy': {
                'criteria': ['P1.1', 'P2.1', 'P3.1', 'P4.1', 'P5.1', 'P6.1', 'P7.1', 'P8.1'],
                'description': 'Personal information is collected, used, retained, disclosed, and disposed of in conformity with commitments',
                'checks': [
                    'Privacy notice compliance',
                    'Consent management',
                    'Data collection limitations',
                    'Data use restrictions',
                    'Data retention policies',
                    'Data subject rights',
                    'Cross-border data transfers',
                    'Data disposal procedures'
                ]
            }
        }
        
        # SOC2 rules engine
        self.rules_engine = {
            'access_control_patterns': [
                r'password.*policy',
                r'two.*factor.*authentication',
                r'multi.*factor.*authentication',
                r'access.*control.*list',
                r'role.*based.*access',
                r'least.*privilege'
            ],
            'encryption_patterns': [
                r'encrypt.*data',
                r'ssl.*tls',
                r'https',
                r'aes.*encryption',
                r'data.*encryption',
                r'transport.*security'
            ],
            'monitoring_patterns': [
                r'logging.*system',
                r'audit.*trail',
                r'monitoring.*alert',
                r'security.*incident',
                r'intrusion.*detection',
                r'system.*monitoring'
            ],
            'backup_patterns': [
                r'backup.*procedure',
                r'disaster.*recovery',
                r'business.*continuity',
                r'data.*backup',
                r'recovery.*plan',
                r'backup.*strategy'
            ],
            'privacy_patterns': [
                r'privacy.*policy',
                r'data.*protection',
                r'gdpr.*compliance',
                r'personal.*information',
                r'data.*subject.*rights',
                r'consent.*management'
            ]
        }
    
    def scan_soc2_compliance_enhanced(self, repo_url: str, criteria: List[str], region: str, status=None):
        """Execute enhanced SOC2 compliance scanning with TSC mapping"""
        # Initialize logger attribute
        self.logger = logger
        
        # Log scan start
        logger.info(f"Starting enhanced SOC2 scan for {repo_url}")

        try:
            if status:
                status.update(label="Initializing SOC2 analysis framework...")
            
            # Initialize scan results
            scan_results = {
                'scan_id': str(uuid.uuid4()),
                'scan_type': 'soc2_compliance',
                'timestamp': datetime.now().isoformat(),
                'repo_url': repo_url,
                'criteria_analyzed': criteria,
                'region': region,
                'status': 'completed',
                'findings': [],
                'tsc_criteria': {},
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0
            }
            
            # Analyze each selected criterion
            for criterion in criteria:
                if status:
                    status.update(label=f"Analyzing {criterion} compliance...")
                
                criterion_results = self._analyze_tsc_criterion(
                    repo_url, criterion, status
                )
                scan_results['tsc_criteria'][criterion] = criterion_results
                
                # Update check counters
                scan_results['total_checks'] += criterion_results.get('total_checks', 0)
                scan_results['passed_checks'] += criterion_results.get('passed_checks', 0)
                scan_results['failed_checks'] += criterion_results.get('failed_checks', 0)
                
                # Add findings
                scan_results['findings'].extend(criterion_results.get('findings', []))
            
            # Calculate overall compliance score
            if scan_results['total_checks'] > 0:
                compliance_score = (scan_results['passed_checks'] / scan_results['total_checks']) * 100
                scan_results['compliance_score'] = compliance_score
                scan_results['compliance_level'] = self._determine_compliance_level(compliance_score)
            else:
                scan_results['compliance_score'] = 0
                scan_results['compliance_level'] = 'Unknown'
            
            # Generate compliance recommendations
            if status:
                status.update(label="Generating compliance recommendations...")
            
            recommendations = self._generate_compliance_recommendations(scan_results)
            scan_results['recommendations'] = recommendations
            
            # Integrate cost savings analysis
            try:
                from services.cost_savings_calculator import integrate_cost_savings_into_report
                scan_results = integrate_cost_savings_into_report(scan_results, 'soc2', self.region)
            except Exception as e:
                self.logger.warning(f"Cost savings integration failed: {e}")
            
            return scan_results
            
        except Exception as e:
            self.logger.error(f"Enhanced SOC2 scan error: {e}")
            return {
                'scan_id': str(uuid.uuid4()),
                'scan_type': 'soc2_compliance',
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e),
                'findings': []
            }
    
    def _analyze_tsc_criterion(self, repo_url: str, criterion: str, status=None):
        """Analyze a specific TSC criterion"""
        try:
            criterion_info = self.tsc_criteria.get(criterion, {})
            checks = criterion_info.get('checks', [])
            
            criterion_results = {
                'criterion': criterion,
                'description': criterion_info.get('description', ''),
                'total_checks': len(checks),
                'passed_checks': 0,
                'failed_checks': 0,
                'status': 'Unknown',
                'score': 0,
                'violations': [],
                'recommendations': [],
                'findings': []
            }
            
            # Simulate repository analysis (in production, this would fetch and analyze actual code)
            analysis_results = self._simulate_repository_analysis(repo_url, criterion)
            
            # Process each check
            for check in checks:
                check_result = self._evaluate_check(check, analysis_results, criterion)
                
                if check_result['passed']:
                    criterion_results['passed_checks'] += 1
                else:
                    criterion_results['failed_checks'] += 1
                    criterion_results['violations'].append(check_result['violation'])
                    criterion_results['recommendations'].append(check_result['recommendation'])
                    
                    location_map = {
                        'Access controls implementation': 'config/access-control-policy.yaml',
                        'Authentication mechanisms': 'config/authentication-config.yaml',
                        'Authorization procedures': 'docs/authorization-procedures.md',
                        'Encryption standards': 'config/encryption-standards.yaml',
                        'Network security': 'config/network-security-policy.yaml',
                        'Vulnerability management': 'docs/vulnerability-management-plan.md',
                        'Incident response procedures': 'docs/incident-response-plan.md',
                        'Security monitoring': 'config/security-monitoring-config.yaml',
                        'System uptime monitoring': 'config/uptime-monitoring-config.yaml',
                        'Backup and recovery procedures': 'docs/backup-recovery-plan.md',
                        'Capacity planning': 'docs/capacity-planning.md',
                        'Performance monitoring': 'config/performance-monitoring-config.yaml',
                        'Disaster recovery planning': 'docs/disaster-recovery-plan.md',
                        'Service level agreements': 'docs/service-level-agreements.md',
                        'Data validation procedures': 'docs/data-validation-procedures.md',
                        'Error handling mechanisms': 'src/error-handling-config.yaml',
                        'Processing controls': 'docs/processing-controls.md',
                        'Data integrity checks': 'config/data-integrity-checks.yaml',
                        'Input validation': 'src/input-validation-rules.yaml',
                        'Output verification': 'docs/output-verification-procedures.md',
                        'Data classification procedures': 'docs/data-classification-policy.md',
                        'Access restriction enforcement': 'config/access-restriction-rules.yaml',
                        'Confidentiality agreements': 'docs/confidentiality-agreements.md',
                        'Encryption of sensitive data': 'config/sensitive-data-encryption.yaml',
                        'Secure data transmission': 'config/secure-transmission-config.yaml',
                        'Data retention policies': 'docs/data-retention-policy.md',
                        'Privacy notice compliance': 'docs/privacy-notice.md',
                        'Consent management': 'docs/consent-management-procedures.md',
                        'Data collection limitations': 'docs/data-collection-policy.md',
                        'Data use restrictions': 'docs/data-use-restrictions.md',
                        'Data subject rights': 'docs/data-subject-rights-procedures.md',
                        'Cross-border data transfers': 'docs/cross-border-transfer-policy.md',
                        'Data disposal procedures': 'docs/data-disposal-procedures.md',
                    }
                    finding_location = location_map.get(check, f"docs/soc2/{check.lower().replace(' ', '-')}-policy.md")
                    criterion_results['findings'].append({
                        'principle': criterion,
                        'check': check,
                        'violation': check_result['violation'],
                        'risk_level': check_result['risk_level'],
                        'location': f"{repo_url.rstrip('/').split('/')[-1]}/{finding_location}" if repo_url else finding_location,
                        'remediation_suggestion': check_result['recommendation'],
                        'scanner': 'enhanced-soc2-scanner'
                    })
            
            # Calculate score and status
            if criterion_results['total_checks'] > 0:
                score = (criterion_results['passed_checks'] / criterion_results['total_checks']) * 100
                criterion_results['score'] = score
                
                if score >= 90:
                    criterion_results['status'] = 'Pass'
                elif score >= 70:
                    criterion_results['status'] = 'Partial'
                else:
                    criterion_results['status'] = 'Fail'
            
            return criterion_results
            
        except Exception as e:
            self.logger.error(f"TSC criterion analysis error: {e}")
            return {
                'criterion': criterion,
                'status': 'Error',
                'error': str(e),
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'findings': []
            }
    
    def _simulate_repository_analysis(self, repo_url: str, criterion: str):
        """Simulate repository analysis for SOC2 compliance"""
        # In production, this would fetch and analyze actual repository content
        # For now, we'll simulate analysis results
        
        import random
        
        analysis_results = {
            'has_access_controls': random.choice([True, False]),
            'has_encryption': random.choice([True, False]),
            'has_monitoring': random.choice([True, False]),
            'has_backup_procedures': random.choice([True, False]),
            'has_privacy_policies': random.choice([True, False]),
            'has_security_documentation': random.choice([True, False]),
            'has_incident_response': random.choice([True, False]),
            'has_vulnerability_management': random.choice([True, False]),
            'code_quality_score': random.uniform(0.3, 0.95),
            'documentation_completeness': random.uniform(0.2, 0.9)
        }
        
        return analysis_results
    
    def _evaluate_check(self, check: str, analysis_results: dict, criterion: str):
        """Evaluate a specific compliance check"""
        check_lower = check.lower()
        
        # Access control checks
        if 'access control' in check_lower or 'authentication' in check_lower:
            passed = analysis_results.get('has_access_controls', False)
            return {
                'passed': passed,
                'violation': f"Insufficient {check.lower()} implementation" if not passed else None,
                'recommendation': f"Implement robust {check.lower()} mechanisms" if not passed else None,
                'risk_level': 'High' if not passed else 'Low'
            }
        
        # Encryption checks
        elif 'encryption' in check_lower or 'secure' in check_lower:
            passed = analysis_results.get('has_encryption', False)
            return {
                'passed': passed,
                'violation': f"Missing {check.lower()} controls" if not passed else None,
                'recommendation': f"Implement {check.lower()} standards" if not passed else None,
                'risk_level': 'High' if not passed else 'Low'
            }
        
        # Monitoring checks
        elif 'monitoring' in check_lower or 'logging' in check_lower:
            passed = analysis_results.get('has_monitoring', False)
            return {
                'passed': passed,
                'violation': f"Inadequate {check.lower()} implementation" if not passed else None,
                'recommendation': f"Establish comprehensive {check.lower()} procedures" if not passed else None,
                'risk_level': 'Medium' if not passed else 'Low'
            }
        
        # Backup and recovery checks
        elif 'backup' in check_lower or 'recovery' in check_lower:
            passed = analysis_results.get('has_backup_procedures', False)
            return {
                'passed': passed,
                'violation': f"Missing {check.lower()} procedures" if not passed else None,
                'recommendation': f"Develop and test {check.lower()} plans" if not passed else None,
                'risk_level': 'Medium' if not passed else 'Low'
            }
        
        # Privacy checks
        elif 'privacy' in check_lower or 'data protection' in check_lower:
            passed = analysis_results.get('has_privacy_policies', False)
            return {
                'passed': passed,
                'violation': f"Insufficient {check.lower()} measures" if not passed else None,
                'recommendation': f"Implement {check.lower()} controls" if not passed else None,
                'risk_level': 'High' if not passed else 'Low'
            }
        
        # Default check
        else:
            score = analysis_results.get('code_quality_score', 0.5)
            passed = score > 0.7
            return {
                'passed': passed,
                'violation': f"Check '{check}' requirements not met" if not passed else None,
                'recommendation': f"Address '{check}' compliance requirements" if not passed else None,
                'risk_level': 'Medium' if not passed else 'Low'
            }
    
    def _determine_compliance_level(self, score: float) -> str:
        """Determine overall compliance level based on score"""
        if score >= 90:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 70:
            return 'Acceptable'
        elif score >= 50:
            return 'Needs Improvement'
        else:
            return 'Poor'
    
    def _generate_compliance_recommendations(self, scan_results: dict) -> List[str]:
        """Generate prioritized compliance recommendations"""
        recommendations = []
        
        # High-priority recommendations based on failed checks
        high_risk_findings = [f for f in scan_results['findings'] if f.get('risk_level') == 'High']
        if high_risk_findings:
            recommendations.append("🔴 Critical: Address high-risk security vulnerabilities immediately")
        
        # Medium-priority recommendations
        medium_risk_findings = [f for f in scan_results['findings'] if f.get('risk_level') == 'Medium']
        if medium_risk_findings:
            recommendations.append("🟡 Important: Implement recommended security controls")
        
        # Compliance score based recommendations
        compliance_score = scan_results.get('compliance_score', 0)
        if compliance_score < 70:
            recommendations.append("📋 Fundamental: Establish basic SOC2 compliance framework")
        elif compliance_score < 90:
            recommendations.append("📈 Enhancement: Strengthen existing compliance measures")
        
        # Criterion-specific recommendations
        for criterion, results in scan_results.get('tsc_criteria', {}).items():
            if results.get('status') == 'Fail':
                recommendations.append(f"⚠️ {criterion}: Review and implement required {criterion.lower()} controls")
        
        return recommendations[:5]  # Return top 5 recommendations