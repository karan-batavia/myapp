"""
Enhanced Finding Generator - Provides specific, contextual analysis and actionable recommendations
for all scanner types. This module transforms generic findings into professional, actionable insights.
"""

import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ActionableRecommendation:
    """Structured recommendation with implementation details"""
    action: str
    description: str
    implementation: str
    effort_estimate: str
    priority: str  # Critical, High, Medium, Low
    verification: str
    business_impact: Optional[str] = None
    compliance_requirement: Optional[str] = None

@dataclass 
class EnhancedFinding:
    """Enhanced finding with comprehensive context and recommendations"""
    type: str
    subtype: str
    title: str
    description: str
    location: str
    context: str
    risk_level: str
    severity: str
    business_impact: str
    gdpr_articles: List[str]
    compliance_requirements: List[str]
    recommendations: List[ActionableRecommendation]
    remediation_priority: str
    estimated_effort: str
    affected_systems: List[str]
    data_classification: str
    exposure_risk: str

class EnhancedFindingGenerator:
    """
    Generates enhanced findings with specific, contextual analysis and actionable recommendations
    for all scanner types in DataGuardian Pro.
    """
    
    def __init__(self, region: str = "Netherlands"):
        self.region = region
        self.gdpr_articles = self._load_gdpr_articles()
        self.finding_templates = self._load_finding_templates()
        
    def _load_gdpr_articles(self) -> Dict[str, str]:
        """Load GDPR article references for compliance mapping"""
        return {
            'lawful_basis': 'Article 6 - Lawfulness of processing',
            'consent': 'Article 7 - Conditions for consent',
            'data_subjects_rights': 'Article 12-23 - Rights of the data subject',
            'security': 'Article 32 - Security of processing',
            'breach_notification': 'Article 33-34 - Personal data breach notification',
            'dpia': 'Article 35 - Data protection impact assessment',
            'transfers': 'Article 44-49 - Transfers of personal data to third countries',
            'accountability': 'Article 5(2) - Principles relating to processing'
        }
    
    def _load_finding_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load finding templates for different scanner types"""
        return {
            'code_scanner': {
                'aws_access_key': {
                    'title': 'AWS Access Key Exposure',
                    'context_analyzer': self._analyze_aws_key_context,
                    'risk_calculator': self._calculate_cloud_credential_risk,
                    'recommendation_generator': self._generate_aws_remediation
                },
                'email_pii': {
                    'title': 'Email Address Exposure',
                    'context_analyzer': self._analyze_email_context,
                    'risk_calculator': self._calculate_pii_risk,
                    'recommendation_generator': self._generate_pii_remediation
                },
                'bsn_netherlands': {
                    'title': 'Dutch BSN (Burgerservicenummer) Exposure',
                    'context_analyzer': self._analyze_bsn_context,
                    'risk_calculator': self._calculate_bsn_risk,
                    'recommendation_generator': self._generate_bsn_remediation
                }
            },
            'website_scanner': {
                'high_risk_cookie': {
                    'title': 'High-Risk Cookie Detected',
                    'context_analyzer': self._analyze_cookie_context,
                    'risk_calculator': self._calculate_cookie_risk,
                    'recommendation_generator': self._generate_cookie_remediation
                },
                'dark_pattern': {
                    'title': 'Cookie Consent Dark Pattern',
                    'context_analyzer': self._analyze_dark_pattern_context,
                    'risk_calculator': self._calculate_consent_risk,
                    'recommendation_generator': self._generate_consent_remediation
                }
            },
            'ai_model_scanner': {
                'demographic_bias': {
                    'title': 'AI Model Demographic Bias',
                    'context_analyzer': self._analyze_bias_context,
                    'risk_calculator': self._calculate_ai_bias_risk,
                    'recommendation_generator': self._generate_bias_remediation
                },
                'pii_leakage': {
                    'title': 'AI Model PII Leakage',
                    'context_analyzer': self._analyze_ai_pii_context,
                    'risk_calculator': self._calculate_ai_pii_risk,
                    'recommendation_generator': self._generate_ai_pii_remediation
                }
            },
            'image_scanner': {
                'DEEPFAKE_SYNTHETIC_MEDIA': {
                    'title': 'Potential Deepfake/Synthetic Media',
                    'context_analyzer': self._analyze_deepfake_context,
                    'risk_calculator': self._calculate_deepfake_risk,
                    'recommendation_generator': self._generate_deepfake_remediation
                }
            }
        }
    
    def enhance_finding(self, scanner_type: str, finding: Dict[str, Any]) -> EnhancedFinding:
        """
        Transform a generic finding into an enhanced finding with specific context and recommendations.
        
        Args:
            scanner_type: Type of scanner that generated the finding
            finding: Original finding dictionary
            
        Returns:
            Enhanced finding with comprehensive context and actionable recommendations
        """
        finding_type = finding.get('type', 'unknown')
        subtype = finding.get('subtype', finding_type)
        
        # Get template for this finding type
        template = self.finding_templates.get(scanner_type, {}).get(subtype, {})
        
        if not template:
            # Fallback to generic enhancement
            return self._create_generic_enhanced_finding(finding)
        
        # Analyze context using template
        context_analysis = template['context_analyzer'](finding)
        risk_analysis = template['risk_calculator'](finding, context_analysis)
        recommendations = template['recommendation_generator'](finding, context_analysis, risk_analysis)
        
        return EnhancedFinding(
            type=finding_type,
            subtype=subtype,
            title=template['title'],
            description=context_analysis['detailed_description'],
            location=finding.get('location', 'Unknown'),
            context=context_analysis['business_context'],
            risk_level=risk_analysis['risk_level'],
            severity=risk_analysis['severity'],
            business_impact=risk_analysis['business_impact'],
            gdpr_articles=context_analysis['gdpr_articles'],
            compliance_requirements=context_analysis['compliance_requirements'],
            recommendations=recommendations,
            remediation_priority=risk_analysis['remediation_priority'],
            estimated_effort=risk_analysis['estimated_effort'],
            affected_systems=context_analysis['affected_systems'],
            data_classification=context_analysis['data_classification'],
            exposure_risk=risk_analysis['exposure_risk']
        )
    
    def _analyze_aws_key_context(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze AWS access key exposure context"""
        location = finding.get('location', '')
        value = finding.get('value', '')
        
        # Determine context based on file location
        context_clues = {
            'config': 'configuration file',
            'env': 'environment file',
            'test': 'test file',
            'example': 'example/template file',
            'docker': 'Docker configuration',
            'k8s': 'Kubernetes manifest',
            'terraform': 'Infrastructure as Code'
        }
        
        file_context = 'source code'
        for clue, description in context_clues.items():
            if clue in location.lower():
                file_context = description
                break
        
        # Calculate exposure level
        exposure_level = 'High'
        if 'test' in location.lower() or 'example' in location.lower():
            exposure_level = 'Medium'
        elif 'prod' in location.lower() or 'main' in location.lower():
            exposure_level = 'Critical'
        
        return {
            'detailed_description': f'AWS access key found in {file_context} at {location}. This credential provides programmatic access to AWS services and could lead to unauthorized resource access, data breaches, and significant AWS billing charges if exploited.',
            'business_context': f'Exposed AWS credentials in {file_context} pose immediate security and financial risks. Attackers could provision expensive resources, access confidential data, or compromise your entire AWS infrastructure.',
            'gdpr_articles': ['Article 32 - Security of processing', 'Article 33 - Personal data breach notification'],
            'compliance_requirements': [
                'GDPR Article 32 - Technical and organizational measures',
                'ISO 27001 - Access control',
                'SOC 2 Type II - Logical access controls'
            ],
            'affected_systems': ['AWS Infrastructure', 'Cloud Resources', 'Data Storage'],
            'data_classification': 'Critical Security Credential',
            'exposure_level': exposure_level
        }
    
    def _calculate_cloud_credential_risk(self, finding: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk for cloud credential exposure"""
        exposure_level = context['exposure_level']
        
        risk_mapping = {
            'Critical': {
                'risk_level': 'Critical',
                'severity': 'Critical',
                'business_impact': 'Potential AWS bill of €10,000+ per day, complete infrastructure compromise, regulatory fines up to €20M under GDPR',
                'remediation_priority': 'Immediate - Fix within 1 hour',
                'estimated_effort': '15-30 minutes - Rotate key and update configuration',
                'exposure_risk': 'Public exposure in version control history'
            },
            'High': {
                'risk_level': 'High', 
                'severity': 'High',
                'business_impact': 'Unauthorized AWS resource access, potential data breach, compliance violations',
                'remediation_priority': 'Urgent - Fix within 4 hours',
                'estimated_effort': '30-60 minutes - Remove from code and implement secure storage',
                'exposure_risk': 'Accessible to development team members'
            },
            'Medium': {
                'risk_level': 'Medium',
                'severity': 'Medium',
                'business_impact': 'Limited unauthorized access, potential service disruption',
                'remediation_priority': 'High - Fix within 24 hours', 
                'estimated_effort': '1-2 hours - Security review and remediation',
                'exposure_risk': 'Limited to specific environments or contexts'
            }
        }
        
        return risk_mapping.get(exposure_level, risk_mapping['High'])
    
    def _generate_aws_remediation(self, finding: Dict[str, Any], context: Dict[str, Any], risk: Dict[str, Any]) -> List[ActionableRecommendation]:
        """Generate specific AWS credential remediation steps"""
        recommendations = []
        
        # Immediate action
        recommendations.append(ActionableRecommendation(
            action="Immediate credential rotation",
            description="Rotate the exposed AWS access key immediately to prevent unauthorized usage",
            implementation="1. Log into AWS Console → IAM → Users → Select user → Security credentials → Make inactive → Create new access key",
            effort_estimate="5-10 minutes",
            priority="Critical",
            verification="Verify old key is deactivated and new key works in applications",
            business_impact="Prevents immediate security breach and unauthorized AWS charges",
            compliance_requirement="GDPR Article 32 - Security of processing"
        ))
        
        # Secure storage implementation
        recommendations.append(ActionableRecommendation(
            action="Implement secure credential storage",
            description="Replace hardcoded credentials with secure credential management system",
            implementation="Options: AWS Secrets Manager, AWS Parameter Store, HashiCorp Vault, or environment variables with restricted access",
            effort_estimate="30-60 minutes",
            priority="High",
            verification="Confirm no hardcoded credentials remain in codebase",
            business_impact="Establishes secure credential management preventing future exposures"
        ))
        
        # Monitoring and detection
        recommendations.append(ActionableRecommendation(
            action="Implement credential monitoring",
            description="Add monitoring to detect future credential exposures",
            implementation="Configure pre-commit hooks with TruffleHog, enable AWS CloudTrail for access monitoring, set up billing alerts",
            effort_estimate="2-4 hours",
            priority="Medium",
            verification="Test with dummy credential to confirm detection works",
            business_impact="Prevents future credential exposures and provides audit trail"
        ))
        
        # Code review and training
        recommendations.append(ActionableRecommendation(
            action="Security training and policy update",
            description="Update development practices to prevent credential exposure",
            implementation="Conduct team training on secure credential handling, update code review checklist, implement security policies",
            effort_estimate="4-8 hours",
            priority="Medium",
            verification="Verify team completion of security training",
            business_impact="Reduces risk of future security incidents through improved practices"
        ))
        
        return recommendations
    
    def _analyze_email_context(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email PII exposure context"""
        location = finding.get('location', '')
        value = finding.get('value', '')
        
        # Determine email type and context
        email_domain = value.split('@')[1] if '@' in value else 'unknown'
        
        context_analysis = {
            'detailed_description': f'Email address "{value}" found in source code at {location}. Email addresses are considered personal data under GDPR and require proper handling and legal basis for processing.',
            'business_context': f'Hardcoded email addresses in source code create privacy compliance risks and maintenance challenges. This email appears to be from domain "{email_domain}".',
            'gdpr_articles': ['Article 6 - Lawfulness of processing', 'Article 13 - Information to be provided'],
            'compliance_requirements': [
                'GDPR Article 6 - Establish lawful basis for processing',
                'Dutch UAVG - Email address protection requirements',
                'Data minimization principle compliance'
            ],
            'affected_systems': ['Application Code', 'Email Processing', 'User Communications'],
            'data_classification': 'Personal Identifiable Information (PII)'
        }
        
        return context_analysis
    
    def _calculate_pii_risk(self, finding: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk for PII exposure"""
        return {
            'risk_level': 'Medium',
            'severity': 'Medium',
            'business_impact': 'GDPR compliance violation, potential privacy complaint, reduced user trust',
            'remediation_priority': 'High - Fix within 48 hours',
            'estimated_effort': '15-30 minutes - Move to configuration management',
            'exposure_risk': 'Personal data accessible to all developers'
        }
    
    def _generate_pii_remediation(self, finding: Dict[str, Any], context: Dict[str, Any], risk: Dict[str, Any]) -> List[ActionableRecommendation]:
        """Generate PII remediation recommendations"""
        return [
            ActionableRecommendation(
                action="Remove hardcoded email from source code",
                description="Move email address to secure configuration management",
                implementation="Replace with environment variable or encrypted configuration file",
                effort_estimate="15-30 minutes",
                priority="High",
                verification="Confirm email no longer appears in source code search",
                compliance_requirement="GDPR Article 25 - Data protection by design"
            ),
            ActionableRecommendation(
                action="Implement data handling procedures",
                description="Establish proper procedures for handling personal data in development",
                implementation="Create data handling guidelines, implement data discovery tools, train development team",
                effort_estimate="4-8 hours",
                priority="Medium", 
                verification="Verify team understands PII handling requirements"
            )
        ]
    
    def _analyze_bsn_context(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Dutch BSN (Burgerservicenummer) exposure context"""
        return {
            'detailed_description': f'Dutch BSN (Burgerservicenummer) detected in source code. BSNs are highly sensitive personal identifiers in the Netherlands with strict processing requirements under Dutch UAVG law.',
            'business_context': 'BSN exposure creates significant compliance risks under Dutch privacy law (UAVG) and may trigger mandatory breach notification to Dutch DPA (Autoriteit Persoonsgegevens).',
            'gdpr_articles': ['Article 9 - Processing of special categories', 'Article 33 - Breach notification'],
            'compliance_requirements': [
                'Dutch UAVG - BSN processing restrictions',
                'Autoriteit Persoonsgegevens (AP) notification requirements',
                'BSN-specific security measures mandatory'
            ],
            'affected_systems': ['Identity Management', 'Government Integration', 'Citizen Services'],
            'data_classification': 'Special Category Personal Data (Netherlands)'
        }
    
    def _calculate_bsn_risk(self, finding: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk for BSN exposure"""
        return {
            'risk_level': 'Critical',
            'severity': 'Critical', 
            'business_impact': 'Mandatory breach notification to Dutch AP, potential €20M fine, citizen identity theft risk',
            'remediation_priority': 'Critical - Fix immediately',
            'estimated_effort': '1-2 hours - Immediate removal and security review',
            'exposure_risk': 'Dutch citizen privacy violation, regulatory investigation'
        }
    
    def _generate_bsn_remediation(self, finding: Dict[str, Any], context: Dict[str, Any], risk: Dict[str, Any]) -> List[ActionableRecommendation]:
        """Generate BSN-specific remediation recommendations"""
        return [
            ActionableRecommendation(
                action="Immediate BSN removal and breach assessment",
                description="Remove BSN from code and assess if breach notification to Dutch AP is required",
                implementation="1. Remove BSN immediately 2. Review commit history 3. Assess exposure timeline 4. Prepare breach notification if required",
                effort_estimate="1-2 hours",
                priority="Critical",
                verification="Confirm no BSN data remains in codebase or version history",
                compliance_requirement="Dutch UAVG Article 34 - 72-hour breach notification"
            ),
            ActionableRecommendation(
                action="Implement BSN-specific security controls",
                description="Establish proper BSN handling procedures compliant with Dutch law",
                implementation="Use BSN hashing/pseudonymization, implement access controls, establish audit logging",
                effort_estimate="8-16 hours",
                priority="High",
                verification="Verify BSN handling meets Dutch AP guidelines"
            )
        ]
    
    def _analyze_cookie_context(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cookie privacy context"""
        cookie_name = finding.get('location', '').replace('Cookie: ', '')
        
        return {
            'detailed_description': f'High-risk cookie "{cookie_name}" detected without proper consent mechanism. This cookie likely tracks user behavior and requires explicit consent under GDPR.',
            'business_context': 'Tracking cookies without proper consent violate GDPR and Dutch cookie law, potentially resulting in regulatory action by Dutch AP.',
            'gdpr_articles': ['Article 7 - Conditions for consent', 'Article 21 - Right to object'],
            'compliance_requirements': [
                'Dutch Telecommunications Act - Cookie consent requirements',
                'GDPR consent validity requirements',
                'Dutch AP cookie guidelines (February 2024)'
            ],
            'affected_systems': ['Website', 'Analytics Platform', 'Marketing Tools'],
            'data_classification': 'Behavioral Tracking Data'
        }
    
    def _calculate_cookie_risk(self, finding: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cookie compliance risk"""
        return {
            'risk_level': 'High',
            'severity': 'High',
            'business_impact': 'Dutch AP investigation, user complaints, competitive disadvantage',
            'remediation_priority': 'High - Fix within 7 days',
            'estimated_effort': '2-4 hours - Implement proper consent',
            'exposure_risk': 'Ongoing GDPR violation for all website visitors'
        }
    
    def _generate_cookie_remediation(self, finding: Dict[str, Any], context: Dict[str, Any], risk: Dict[str, Any]) -> List[ActionableRecommendation]:
        """Generate cookie compliance recommendations"""
        return [
            ActionableRecommendation(
                action="Implement proper cookie consent",
                description="Add explicit consent mechanism for tracking cookies",
                implementation="Deploy cookie consent banner with granular controls, implement consent validation, add 'Reject All' button",
                effort_estimate="2-4 hours",
                priority="High",
                verification="Test consent flow and verify cookie blocking works",
                compliance_requirement="Dutch AP cookie guidelines compliance"
            ),
            ActionableRecommendation(
                action="Cookie audit and categorization",
                description="Conduct comprehensive audit of all website cookies",
                implementation="Categorize all cookies (essential, functional, analytics, marketing), document purposes, implement cookie policy",
                effort_estimate="4-8 hours",
                priority="Medium",
                verification="Verify cookie policy accuracy and completeness"
            )
        ]
    
    def _create_generic_enhanced_finding(self, finding: Dict[str, Any]) -> EnhancedFinding:
        """Create enhanced finding with intelligent context based on finding type"""
        finding_type = finding.get('type', 'unknown').lower().replace('_', ' ')
        
        # Extract description from multiple possible fields (different scanners use different fields)
        description = (finding.get('description') or 
                       finding.get('reason') or 
                       finding.get('context') or 
                       'Security or privacy issue detected')
        
        # For EXIF findings, use reason as it contains the detailed explanation
        if 'exif' in finding_type and finding.get('reason'):
            description = finding.get('reason')
        
        location = finding.get('location', 'Unknown location')
        severity = finding.get('severity', finding.get('risk_level', 'Medium'))
        
        # Generate intelligent context based on finding type
        context, gdpr_articles, compliance_reqs, business_impact, recommendations = self._get_type_specific_context(
            finding_type, description, location, severity
        )
        
        return EnhancedFinding(
            type=finding.get('type', 'unknown'),
            subtype=finding.get('subtype', 'generic'),
            title=f"Security Finding: {finding.get('type', 'Unknown').replace('_', ' ').title()}",
            description=description,
            location=location,
            context=context,
            risk_level=severity,
            severity=severity,
            business_impact=business_impact,
            gdpr_articles=gdpr_articles,
            compliance_requirements=compliance_reqs,
            recommendations=recommendations,
            remediation_priority=f"{severity} - Review within {'24 hours' if severity == 'Critical' else '3 days' if severity == 'High' else '7 days'}",
            estimated_effort="1-4 hours - Investigation and remediation",
            affected_systems=self._infer_affected_systems(finding_type),
            data_classification=self._infer_data_classification(finding_type),
            exposure_risk=self._infer_exposure_risk(severity)
        )
    
    def _get_type_specific_context(self, finding_type: str, description: str, location: str, severity: str):
        """Generate context based on finding type"""
        
        # AI Act related findings
        if 'ai act' in finding_type or 'gpai' in finding_type:
            if 'quality management' in finding_type:
                return (
                    "EU AI Act Article 16 requires quality management systems for high-risk AI. Missing elements indicate compliance gaps.",
                    ['EU AI Act Article 16 - Quality Management Systems'],
                    ['Implement documented QMS procedures', 'Establish risk management processes', 'Create audit trails'],
                    "Non-compliance with EU AI Act QMS requirements can result in fines up to €15M or 3% of global turnover",
                    [ActionableRecommendation(action="Implement Quality Management System", description="Establish AI-specific QMS per Article 16", implementation="Document procedures, risk assessments, testing protocols, and incident response", effort_estimate="8-16 hours", priority=severity, verification="Third-party QMS audit")]
                )
            elif 'human oversight' in finding_type:
                return (
                    "EU AI Act Article 26 requires human oversight mechanisms for high-risk AI systems to ensure human control.",
                    ['EU AI Act Article 26 - Human Oversight'],
                    ['Implement human-in-the-loop controls', 'Enable operator intervention', 'Provide override capabilities'],
                    "Missing human oversight can lead to uncontrolled AI decisions and regulatory non-compliance",
                    [ActionableRecommendation(action="Implement Human Oversight Controls", description="Add human-in-the-loop mechanisms per Article 26", implementation="Design intervention points, override controls, and monitoring dashboards", effort_estimate="4-8 hours", priority=severity, verification="Test human override capabilities")]
                )
            elif 'logging' in finding_type:
                return (
                    "EU AI Act Article 17 requires automatic logging for high-risk AI systems to ensure traceability.",
                    ['EU AI Act Article 17 - Automatic Logging'],
                    ['Implement comprehensive event logging', 'Maintain audit trails', 'Enable log retention'],
                    "Insufficient logging prevents incident investigation and violates transparency requirements",
                    [ActionableRecommendation(action="Implement Comprehensive Logging", description="Add automatic logging per Article 17", implementation="Log inputs, outputs, decisions, and system events with timestamps", effort_estimate="4-8 hours", priority=severity, verification="Verify log completeness and retention")]
                )
            elif 'fundamental rights' in finding_type:
                return (
                    "EU AI Act Article 29 requires consideration of fundamental rights impact for high-risk AI systems.",
                    ['EU AI Act Article 29 - Fundamental Rights Impact Assessment'],
                    ['Conduct fundamental rights assessment', 'Document impact on individuals', 'Implement safeguards'],
                    "AI systems affecting fundamental rights require documented impact assessments and mitigation measures",
                    [ActionableRecommendation(action="Conduct Fundamental Rights Assessment", description="Assess AI impact on fundamental rights per Article 29", implementation="Document potential impacts on privacy, non-discrimination, due process", effort_estimate="4-8 hours", priority=severity, verification="Legal review of assessment")]
                )
            elif 'data governance' in finding_type:
                return (
                    "EU AI Act Article 10 requires robust data governance for AI training data quality and representativeness.",
                    ['EU AI Act Article 10 - Data Governance'],
                    ['Implement data quality measures', 'Ensure representative datasets', 'Document data provenance'],
                    "Poor data governance leads to biased AI outputs and regulatory non-compliance",
                    [ActionableRecommendation(action="Implement Data Governance Framework", description="Establish data governance per Article 10", implementation="Document data sources, quality checks, bias mitigation, and provenance tracking", effort_estimate="8-16 hours", priority=severity, verification="Data quality audit")]
                )
            elif 'risk classification' in finding_type:
                return (
                    "EU AI Act Article 6 requires risk classification of AI systems to determine applicable requirements.",
                    ['EU AI Act Article 6 - Risk Classification'],
                    ['Classify AI system risk level', 'Apply appropriate controls', 'Document classification rationale'],
                    "Incorrect risk classification can lead to inadequate compliance measures or unnecessary burdens",
                    [ActionableRecommendation(action="Complete Risk Classification", description="Classify AI system per Article 6 Annex III", implementation="Evaluate use cases against high-risk categories, document classification", effort_estimate="2-4 hours", priority=severity, verification="Legal review of classification")]
                )
            elif 'scope' in finding_type or 'definition' in finding_type:
                return (
                    "EU AI Act Articles 1-4 define scope and key terms. Clear definitions ensure proper compliance scope.",
                    ['EU AI Act Articles 1-4 - Scope and Definitions'],
                    ['Define AI system boundaries', 'Identify provider/deployer roles', 'Document applicability'],
                    "Unclear scope can lead to missed compliance requirements or wasted effort on non-applicable rules",
                    [ActionableRecommendation(action="Define AI Act Applicability", description="Document AI system scope and role definitions", implementation="Identify if you are provider, deployer, or distributor; document AI system boundaries", effort_estimate="2-4 hours", priority=severity, verification="Legal review of applicability")]
                )
            else:
                return (
                    f"EU AI Act compliance finding: {description}",
                    ['EU AI Act - General Requirements'],
                    ['Review specific EU AI Act article requirements', 'Implement appropriate controls'],
                    "EU AI Act non-compliance can result in significant fines and market access restrictions",
                    [ActionableRecommendation(action="Address EU AI Act Requirement", description=description, implementation="Review applicable EU AI Act article and implement required controls", effort_estimate="2-8 hours", priority=severity, verification="Compliance audit")]
                )
        
        # License detection
        elif 'license' in finding_type:
            return (
                f"License detected: {description}. Open source licenses may have attribution or copyleft requirements.",
                ['EU AI Act Article 53 - Copyright Compliance for GPAI'],
                ['Verify license compliance', 'Document attribution requirements', 'Ensure commercial use permitted'],
                "License violations can result in legal action and copyright infringement claims",
                [ActionableRecommendation(action="Verify License Compliance", description="Review license terms and ensure compliance", implementation="Check attribution requirements, commercial use permissions, and derivative work rules", effort_estimate="1-2 hours", priority="Low", verification="Legal review of license terms")]
            )
        
        # Documentation findings
        elif 'documentation' in finding_type:
            return (
                f"Documentation review: {description}. Proper documentation supports transparency and accountability.",
                ['EU AI Act Article 11 - Technical Documentation', 'GDPR Article 30 - Records of Processing'],
                ['Maintain comprehensive documentation', 'Document AI system design decisions', 'Keep records up to date'],
                "Inadequate documentation hinders transparency and complicates regulatory compliance",
                [ActionableRecommendation(action="Enhance Documentation", description="Improve AI system documentation", implementation="Document architecture, training data, testing results, and operational procedures", effort_estimate="4-8 hours", priority="Medium", verification="Documentation completeness review")]
            )
        
        # Opt-out mechanisms
        elif 'opt' in finding_type:
            return (
                f"Opt-out mechanism detected: {description}. Ensure proper exclusion handling for data collection.",
                ['GDPR Article 21 - Right to Object', 'EU AI Act Article 53 - Training Data Opt-Out'],
                ['Respect opt-out preferences', 'Implement exclusion mechanisms', 'Document compliance'],
                "Failure to honor opt-out requests violates data subject rights",
                [ActionableRecommendation(action="Verify Opt-Out Compliance", description="Ensure opt-out mechanisms are properly implemented", implementation="Test exclusion functionality, verify data is excluded from training", effort_estimate="1-2 hours", priority="Medium", verification="Test opt-out flow")]
            )
        
        # Model architecture
        elif 'model' in finding_type or 'architecture' in finding_type:
            return (
                f"Model architecture finding: {description}. Architecture decisions affect compliance requirements.",
                ['EU AI Act Article 9 - Risk Management', 'EU AI Act Article 15 - Accuracy and Robustness'],
                ['Document architecture decisions', 'Assess accuracy and robustness', 'Implement appropriate testing'],
                "Model architecture affects system capabilities and associated compliance requirements",
                [ActionableRecommendation(action="Document Model Architecture", description="Complete model architecture documentation", implementation="Document model type, parameters, training approach, and performance characteristics", effort_estimate="2-4 hours", priority="Medium", verification="Technical review of documentation")]
            )
        
        # Accountability
        elif 'accountability' in finding_type or 'governance' in finding_type:
            return (
                f"Accountability finding: {description}. AI systems require clear governance and accountability frameworks.",
                ['EU AI Act Articles 14-15 - Human Oversight and Accountability', 'GDPR Article 5(2) - Accountability'],
                ['Establish governance framework', 'Assign clear responsibilities', 'Implement audit mechanisms'],
                "Lack of accountability framework creates compliance and liability risks",
                [ActionableRecommendation(action="Establish Accountability Framework", description="Implement AI governance structure", implementation="Define roles, responsibilities, decision-making processes, and escalation procedures", effort_estimate="8-16 hours", priority=severity, verification="Governance framework review")]
            )
        
        # EXIF metadata findings
        elif 'exif' in finding_type:
            if 'gps' in finding_type or 'location' in finding_type:
                return (
                    f"GPS location data embedded in image metadata. {description}",
                    ['GDPR Article 4(1) - Personal Data Definition', 'GDPR Article 9 - Special Categories'],
                    ['Strip GPS metadata before sharing', 'Implement metadata removal pipeline', 'Document data handling'],
                    "GPS coordinates can reveal exact physical locations, identifying individuals when combined with other data",
                    [ActionableRecommendation(action="Remove GPS Metadata", description="Strip location data from images", implementation="Use EXIF removal tools, implement automated stripping in upload pipeline", effort_estimate="1-2 hours", priority="High", verification="Verify GPS data removed from processed images")]
                )
            elif 'timestamp' in finding_type or 'date' in finding_type:
                return (
                    f"Timestamp metadata found in image. {description}",
                    ['GDPR Article 4(1) - Personal Data Definition'],
                    ['Consider timestamp implications', 'Strip if privacy-sensitive', 'Document retention policy'],
                    "Timestamps can reveal patterns of behavior and location when combined with other data",
                    [ActionableRecommendation(action="Review Timestamp Data", description="Assess timestamp privacy implications", implementation="Determine if timestamps need stripping for privacy, implement if needed", effort_estimate="30 mins", priority="Medium", verification="Verify timestamp handling policy")]
                )
            elif 'author' in finding_type or 'artist' in finding_type:
                return (
                    f"Author/creator information in image metadata. {description}",
                    ['GDPR Article 4(1) - Personal Data Definition'],
                    ['Remove author info if anonymity required', 'Strip PII from metadata', 'Document handling'],
                    "Author names and creator info directly identify individuals - this is PII under GDPR",
                    [ActionableRecommendation(action="Remove Author Metadata", description="Strip author/creator PII from images", implementation="Remove Artist, Copyright, XPAuthor fields from EXIF", effort_estimate="30 mins", priority="Medium", verification="Verify author data removed")]
                )
            elif 'device' in finding_type or 'camera' in finding_type:
                return (
                    f"Device identification data in image metadata. {description}",
                    ['GDPR Article 4(1) - Personal Data Definition'],
                    ['Strip device identifiers', 'Remove serial numbers', 'Implement metadata cleaning'],
                    "Device serial numbers and camera identifiers create persistent identifiers that can track individuals across images",
                    [ActionableRecommendation(action="Remove Device Identifiers", description="Strip device/camera serial numbers", implementation="Remove Make, Model, BodySerialNumber, LensSerialNumber from EXIF", effort_estimate="30 mins", priority="High", verification="Verify device identifiers removed")]
                )
            else:
                return (
                    f"Image metadata privacy finding: {description}",
                    ['GDPR Article 4(1) - Personal Data Definition', 'GDPR Article 5 - Data Minimization'],
                    ['Review all metadata fields', 'Strip privacy-sensitive data', 'Implement metadata policy'],
                    "Image metadata can contain various forms of PII requiring GDPR-compliant handling",
                    [ActionableRecommendation(action="Audit Image Metadata", description="Review and sanitize image metadata", implementation="Scan all metadata fields, strip PII, implement automated cleaning", effort_estimate="1-2 hours", priority="Medium", verification="Verify metadata sanitization")]
                )
        
        # Watermark findings
        elif 'watermark' in finding_type:
            return (
                f"Watermark detected in image. {description}",
                ['Copyright Law', 'GDPR Article 4(1) if watermark contains PII'],
                ['Verify watermark ownership', 'Respect copyright', 'Document source'],
                "Watermarks may indicate copyrighted content or contain identifying information",
                [ActionableRecommendation(action="Review Watermark", description="Assess watermark implications", implementation="Verify content ownership, check for PII in watermark, document source", effort_estimate="30 mins", priority="Medium", verification="Document watermark review")]
            )
        
        # Signature findings
        elif 'signature' in finding_type:
            return (
                f"Signature pattern detected. {description}",
                ['GDPR Article 4(1) - Personal Data Definition', 'eIDAS Regulation'],
                ['Verify signature authenticity', 'Protect as biometric data', 'Document handling'],
                "Signatures are biometric identifiers and personal data under GDPR",
                [ActionableRecommendation(action="Handle Signature Data", description="Process signature as sensitive PII", implementation="Apply appropriate access controls, encryption, and retention policies", effort_estimate="1 hour", priority="High", verification="Verify signature protection measures")]
            )
        
        # Deepfake/synthetic media findings
        elif 'deepfake' in finding_type or 'synthetic' in finding_type:
            return (
                f"Synthetic/AI-generated media analysis: {description}",
                ['EU AI Act Article 50(2) - Transparency for AI-generated content'],
                ['Verify content authenticity', 'Add disclosure labels if synthetic', 'Document verification'],
                "AI-generated content requires transparency labeling under EU AI Act to prevent misinformation",
                [ActionableRecommendation(action="Verify Content Authenticity", description="Confirm if content is AI-generated", implementation="Cross-reference sources, check provenance, add disclosure if synthetic", effort_estimate="1-2 hours", priority=severity, verification="Document authenticity verification")]
            )
        
        # Default fallback with description-based context
        else:
            return (
                description if len(description) > 30 else f"Compliance finding requiring review: {description}",
                ['Article 32 - Security of processing'],
                ['Review specific requirements', 'Implement appropriate controls'],
                "Potential security or compliance impact requiring investigation",
                [ActionableRecommendation(action="Review and Remediate", description=f"Address: {description}", implementation="Investigate the finding and implement appropriate remediation", effort_estimate="1-4 hours", priority=severity, verification="Confirm remediation complete")]
            )
    
    def _infer_affected_systems(self, finding_type: str) -> List[str]:
        """Infer affected systems from finding type"""
        if 'ai' in finding_type or 'model' in finding_type:
            return ['AI/ML Systems', 'Model Pipeline', 'Inference Services']
        elif 'data' in finding_type:
            return ['Data Storage', 'Data Processing', 'Data Governance']
        elif 'document' in finding_type or 'license' in finding_type:
            return ['Documentation Systems', 'Repository']
        else:
            return ['Application Systems']
    
    def _infer_data_classification(self, finding_type: str) -> str:
        """Infer data classification from finding type"""
        if 'pii' in finding_type or 'personal' in finding_type:
            return 'Personal Data'
        elif 'training' in finding_type or 'data' in finding_type:
            return 'Training Data'
        elif 'model' in finding_type:
            return 'Model Assets'
        else:
            return 'System Configuration'
    
    def _infer_exposure_risk(self, severity: str) -> str:
        """Infer exposure risk from severity"""
        risk_map = {
            'Critical': 'Immediate regulatory and business risk',
            'High': 'Significant compliance exposure',
            'Medium': 'Moderate compliance risk',
            'Low': 'Minor compliance consideration'
        }
        return risk_map.get(severity, 'Unknown risk level')
    
    # Placeholder methods for other scanner types
    def _analyze_bias_context(self, finding): return {'detailed_description': 'AI bias detected', 'business_context': 'AI fairness issue', 'gdpr_articles': [], 'compliance_requirements': [], 'affected_systems': [], 'data_classification': 'Unknown'}
    def _calculate_ai_bias_risk(self, finding, context): return {'risk_level': 'High', 'severity': 'High', 'business_impact': 'AI fairness concerns', 'remediation_priority': 'High', 'estimated_effort': '4-8 hours', 'exposure_risk': 'Medium'}
    def _generate_bias_remediation(self, finding, context, risk): return []
    def _analyze_ai_pii_context(self, finding): return {'detailed_description': 'AI PII leak', 'business_context': 'Privacy issue', 'gdpr_articles': [], 'compliance_requirements': [], 'affected_systems': [], 'data_classification': 'Unknown'}
    def _calculate_ai_pii_risk(self, finding, context): return {'risk_level': 'High', 'severity': 'High', 'business_impact': 'Privacy violation', 'remediation_priority': 'High', 'estimated_effort': '2-4 hours', 'exposure_risk': 'High'}
    def _generate_ai_pii_remediation(self, finding, context, risk): return []
    def _analyze_dark_pattern_context(self, finding): return {'detailed_description': 'Dark pattern', 'business_context': 'UX issue', 'gdpr_articles': [], 'compliance_requirements': [], 'affected_systems': [], 'data_classification': 'Unknown'}
    def _calculate_consent_risk(self, finding, context): return {'risk_level': 'High', 'severity': 'High', 'business_impact': 'Consent violation', 'remediation_priority': 'High', 'estimated_effort': '2-4 hours', 'exposure_risk': 'Medium'}
    def _generate_consent_remediation(self, finding, context, risk): return []
    
    def _analyze_deepfake_context(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze deepfake/synthetic media context"""
        import os
        source = finding.get('source', '')
        filename = os.path.basename(source) if source else 'Unknown file'
        analysis = finding.get('analysis_details', {})
        overall_score = analysis.get('overall_score', 0)
        
        likelihood = "high likelihood" if overall_score >= 0.6 else "moderate likelihood" if overall_score >= 0.4 else "potential indicators"
        
        return {
            'detailed_description': f'Synthetic/AI-generated media detected in "{filename}" with {likelihood} ({overall_score:.1%} confidence). This content may require transparency labeling under EU AI Act Article 50(2).',
            'business_context': f'Under EU AI Act 2025, synthetic media must be clearly disclosed. Failure to label AI-generated content can result in fines up to €15M or 3% of global turnover.',
            'gdpr_articles': ['EU AI Act Article 50(2) - Transparency obligations for AI-generated content'],
            'compliance_requirements': [
                'EU AI Act Article 50(2) - Synthetic media transparency',
                'Label AI-generated content clearly',
                'Maintain records of AI-generated materials'
            ],
            'affected_systems': ['Media Content', 'Marketing Materials', 'Communications'],
            'data_classification': 'AI-Generated Content'
        }
    
    def _calculate_deepfake_risk(self, finding: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk for deepfake detection"""
        analysis = finding.get('analysis_details', {})
        overall_score = analysis.get('overall_score', 0)
        
        if overall_score >= 0.6:
            return {
                'risk_level': 'Critical',
                'severity': 'High',
                'business_impact': 'High probability of synthetic media requiring immediate transparency labeling. Non-compliance with EU AI Act can result in penalties up to €15M.',
                'remediation_priority': 'Immediate - Verify and label within 24 hours',
                'estimated_effort': '1-2 hours - Verify authenticity and add disclosures',
                'exposure_risk': 'Public-facing content may violate transparency requirements'
            }
        elif overall_score >= 0.4:
            return {
                'risk_level': 'High',
                'severity': 'Medium',
                'business_impact': 'Moderate probability of synthetic media. Verify content origin and consider adding transparency labels.',
                'remediation_priority': 'High - Verify within 48 hours',
                'estimated_effort': '2-4 hours - Investigation and verification',
                'exposure_risk': 'Potential compliance gap if content is AI-generated'
            }
        else:
            return {
                'risk_level': 'Medium',
                'severity': 'Low',
                'business_impact': 'Low probability but some indicators present. Document verification for compliance records.',
                'remediation_priority': 'Medium - Review within 7 days',
                'estimated_effort': '1-2 hours - Quick verification',
                'exposure_risk': 'Low risk but worth monitoring'
            }
    
    def _generate_deepfake_remediation(self, finding: Dict[str, Any], context: Dict[str, Any], risk: Dict[str, Any]) -> List[ActionableRecommendation]:
        """Generate remediation for deepfake findings"""
        return [
            ActionableRecommendation(
                action="Verify content authenticity",
                description="Determine if content is genuinely AI-generated or false positive",
                implementation="(1) Check content origin and creation records, (2) Contact content creator for verification, (3) Use additional forensic tools if needed",
                effort_estimate="1-2 hours",
                priority="High",
                verification="Document verification results with evidence",
                business_impact="Avoid false disclosures while ensuring compliance",
                compliance_requirement="EU AI Act Article 50(2)"
            ),
            ActionableRecommendation(
                action="Add transparency labels if confirmed",
                description="Clearly disclose AI-generated content to viewers",
                implementation="(1) Add visible label 'AI-Generated' or 'Synthetic Media', (2) Update metadata with AI disclosure, (3) Document in content registry",
                effort_estimate="30 minutes",
                priority="Critical" if risk.get('risk_level') == 'Critical' else "High",
                verification="Verify label is visible and compliant with EU AI Act requirements",
                business_impact="Avoid €15M penalties for non-disclosure",
                compliance_requirement="EU AI Act Article 50(2) transparency"
            ),
            ActionableRecommendation(
                action="Update content management policy",
                description="Establish procedures for AI-generated content handling",
                implementation="(1) Create AI content registry, (2) Define labeling standards, (3) Train team on compliance requirements",
                effort_estimate="4-8 hours",
                priority="Medium",
                verification="Policy documented and team trained",
                business_impact="Prevent future compliance issues",
                compliance_requirement="EU AI Act organizational compliance"
            )
        ]

def enhance_findings_for_report(scanner_type: str, findings: List[Dict[str, Any]], region: str = "Netherlands") -> List[Dict[str, Any]]:
    """
    Enhance all findings in a scan result with specific context and actionable recommendations.
    
    Args:
        scanner_type: Type of scanner (code_scanner, website_scanner, etc.)
        findings: List of original findings
        region: Region for compliance requirements
        
    Returns:
        List of enhanced findings suitable for professional reporting
    """
    generator = EnhancedFindingGenerator(region=region)
    enhanced_findings = []
    
    for finding in findings:
        try:
            enhanced = generator.enhance_finding(scanner_type, finding)
            
            # Convert to dictionary format for compatibility
            enhanced_dict = {
                'type': enhanced.type,
                'subtype': enhanced.subtype,
                'title': enhanced.title,
                'description': enhanced.description,
                'location': enhanced.location,
                'context': enhanced.context,
                'risk_level': enhanced.risk_level,
                'severity': enhanced.severity,
                'business_impact': enhanced.business_impact,
                'gdpr_articles': enhanced.gdpr_articles,
                'compliance_requirements': enhanced.compliance_requirements,
                'recommendations': [
                    {
                        'action': rec.action,
                        'description': rec.description,
                        'implementation': rec.implementation,
                        'effort_estimate': rec.effort_estimate,
                        'priority': rec.priority,
                        'verification': rec.verification,
                        'business_impact': rec.business_impact,
                        'compliance_requirement': rec.compliance_requirement
                    }
                    for rec in enhanced.recommendations
                ],
                'remediation_priority': enhanced.remediation_priority,
                'estimated_effort': enhanced.estimated_effort,
                'affected_systems': enhanced.affected_systems,
                'data_classification': enhanced.data_classification,
                'exposure_risk': enhanced.exposure_risk,
                
                # Preserve SOC2/NIS2 specific fields from original finding
                'tsc_criteria': finding.get('tsc_criteria', finding.get('soc2_tsc_criteria', [])),
                'soc2_tsc_criteria': finding.get('soc2_tsc_criteria', finding.get('tsc_criteria', [])),
                'nis2_articles': finding.get('nis2_articles', []),
                'soc2_tsc_details': finding.get('soc2_tsc_details', []),
                'nis2_details': finding.get('nis2_details', []),
                
                # Preserve deepfake/image scanner specific fields
                'source': finding.get('source', ''),
                'analysis_details': finding.get('analysis_details', {}),
                'eu_ai_act_compliance': finding.get('eu_ai_act_compliance', {}),
                'confidence': finding.get('confidence', 0),
                'reason': finding.get('reason', ''),
                
                # Preserve original finding data
                'original_finding': finding
            }
            
            enhanced_findings.append(enhanced_dict)
            
        except Exception as e:
            # Fallback to original finding if enhancement fails
            finding['enhancement_error'] = str(e)
            enhanced_findings.append(finding)
    
    return enhanced_findings