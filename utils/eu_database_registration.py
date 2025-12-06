"""
EU Database Registration Automation (Article 49)
Automated registration workflow for high-risk AI systems in EU database
"""

import json
import re
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class AISystemCategory(Enum):
    """AI system categories requiring EU database registration"""
    BIOMETRIC_IDENTIFICATION = "biometric_identification"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure" 
    EDUCATION_TRAINING = "education_training"
    EMPLOYMENT = "employment"
    ESSENTIAL_SERVICES = "essential_services"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION_BORDER = "migration_border"
    JUSTICE_DEMOCRACY = "justice_democracy"

class RegistrationStatus(Enum):
    """Registration workflow status"""
    NOT_REQUIRED = "not_required"
    PREPARATION_NEEDED = "preparation_needed"
    READY_FOR_SUBMISSION = "ready_for_submission"
    SUBMITTED = "submitted"
    REGISTERED = "registered"
    UPDATE_REQUIRED = "update_required"

@dataclass
class RegistrationRequirement:
    """Single registration requirement with validation"""
    requirement_id: str
    title: str
    description: str
    is_mandatory: bool
    validation_pattern: Optional[str]
    examples: List[str]
    completed: bool = False
    evidence_provided: Optional[str] = None

@dataclass
class SystemRegistrationProfile:
    """Complete registration profile for an AI system"""
    system_id: str
    system_name: str
    category: AISystemCategory
    provider_info: Dict[str, str]
    deployer_info: Dict[str, str]
    technical_specs: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    conformity_assessment: Dict[str, Any]
    requirements: List[RegistrationRequirement]
    status: RegistrationStatus
    submission_deadline: Optional[datetime]
    created_date: datetime
    last_updated: datetime

class EUDatabaseRegistration:
    """
    Automates EU database registration process for high-risk AI systems
    per EU AI Act Article 49
    """
    
    def __init__(self, region: str = "Netherlands"):
        self.region = region
        self.registration_requirements = self._load_registration_requirements()
        self.validation_rules = self._load_validation_rules()
        
    def _load_registration_requirements(self) -> Dict[str, List[RegistrationRequirement]]:
        """Load registration requirements by AI system category"""
        return {
            "biometric_identification": [
                RegistrationRequirement(
                    requirement_id="bio_001",
                    title="System Purpose and Scope",
                    description="Detailed description of biometric identification system purpose, scope, and use cases",
                    is_mandatory=True,
                    validation_pattern=r".{100,}",  # Minimum 100 characters
                    examples=["Real-time facial recognition for access control", "Voice authentication for secure facilities"]
                ),
                RegistrationRequirement(
                    requirement_id="bio_002", 
                    title="Biometric Data Types",
                    description="Specification of biometric data types processed (facial, voice, fingerprint, etc.)",
                    is_mandatory=True,
                    validation_pattern=r"\b(?:facial|voice|fingerprint|iris|palm|gait|behavioral)\b",
                    examples=["Facial geometry features", "Voice pattern analysis", "Fingerprint minutiae"]
                ),
                RegistrationRequirement(
                    requirement_id="bio_003",
                    title="Accuracy Performance Metrics", 
                    description="Documented accuracy rates, false positive/negative rates, and performance benchmarks",
                    is_mandatory=True,
                    validation_pattern=r"(?:accuracy|precision|recall|f1[-_]score).*\d+\.?\d*%?",
                    examples=["Accuracy: 99.2%, FPR: 0.01%", "Precision: 98.5%, Recall: 97.3%"]
                ),
                RegistrationRequirement(
                    requirement_id="bio_004",
                    title="Human Oversight Mechanisms",
                    description="Human oversight procedures and intervention capabilities",
                    is_mandatory=True,
                    validation_pattern=r"\b(?:human|manual|operator|supervisor)\s+(?:oversight|review|intervention|control)\b",
                    examples=["Manual review of all matches", "Human operator approval required"]
                ),
                RegistrationRequirement(
                    requirement_id="bio_005",
                    title="Fundamental Rights Assessment",
                    description="Impact assessment on fundamental rights and freedoms",
                    is_mandatory=True,
                    validation_pattern=r"\b(?:fundamental\s+rights|privacy|dignity|non-discrimination)\b",
                    examples=["Privacy impact assessment completed", "Non-discrimination analysis conducted"]
                )
            ],
            "employment": [
                RegistrationRequirement(
                    requirement_id="emp_001",
                    title="Employment Process Scope",
                    description="Definition of employment processes covered (recruitment, evaluation, promotion, termination)",
                    is_mandatory=True,
                    validation_pattern=r"\b(?:recruitment|hiring|evaluation|promotion|termination|performance)\b",
                    examples=["CV screening and candidate ranking", "Performance evaluation scoring"]
                ),
                RegistrationRequirement(
                    requirement_id="emp_002",
                    title="Decision Criteria and Logic",
                    description="Transparent explanation of decision-making criteria and algorithmic logic",
                    is_mandatory=True,
                    validation_pattern=r".{150,}",  # Detailed explanation required
                    examples=["Skills matching algorithm based on job requirements", "Performance metrics weighted scoring"]
                ),
                RegistrationRequirement(
                    requirement_id="emp_003",
                    title="Bias Mitigation Measures",
                    description="Bias detection, testing, and mitigation strategies implemented",
                    is_mandatory=True,
                    validation_pattern=r"\b(?:bias|fairness|discrimination|equal\s+opportunity)\b",
                    examples=["Demographic parity testing", "Adverse impact analysis"]
                ),
                RegistrationRequirement(
                    requirement_id="emp_004",
                    title="Data Protection Compliance",
                    description="GDPR compliance measures for employee/candidate data processing",
                    is_mandatory=True,
                    validation_pattern=r"\b(?:gdpr|consent|data\s+protection|privacy|lawful\s+basis)\b",
                    examples=["Explicit consent obtained", "Legitimate interest assessment"]
                )
            ],
            "critical_infrastructure": [
                RegistrationRequirement(
                    requirement_id="crit_001",
                    title="Infrastructure System Identification",
                    description="Identification of critical infrastructure systems managed by AI",
                    is_mandatory=True,
                    validation_pattern=r"\b(?:power|energy|water|transport|telecom|financial|health)\b",
                    examples=["Power grid management", "Water treatment control", "Transportation routing"]
                ),
                RegistrationRequirement(
                    requirement_id="crit_002",
                    title="Safety and Security Measures",
                    description="Comprehensive safety and cybersecurity protections implemented",
                    is_mandatory=True,
                    validation_pattern=r"\b(?:safety|security|protection|resilience|redundancy)\b",
                    examples=["Fail-safe mechanisms", "Cybersecurity monitoring", "Backup systems"]
                ),
                RegistrationRequirement(
                    requirement_id="crit_003",
                    title="Risk Management Framework",
                    description="Risk management system for identifying and mitigating infrastructure risks",
                    is_mandatory=True,
                    validation_pattern=r"\b(?:risk\s+management|hazard|mitigation|contingency)\b",
                    examples=["Hazard identification procedures", "Emergency response protocols"]
                )
            ]
        }
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for registration data"""
        return {
            "provider_validation": {
                "name": {"required": True, "min_length": 2, "pattern": r"^[A-Za-z\s\-\.]+$"},
                "registration_number": {"required": True, "pattern": r"^[A-Z0-9\-]+$"},
                "address": {"required": True, "min_length": 10},
                "contact_email": {"required": True, "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
                "authorized_representative": {"required": True, "min_length": 2}
            },
            "system_validation": {
                "name": {"required": True, "min_length": 5, "max_length": 200},
                "version": {"required": True, "pattern": r"^\d+\.\d+(\.\d+)?$"},
                "intended_purpose": {"required": True, "min_length": 50},
                "deployment_date": {"required": True, "format": "date"},
                "geographic_scope": {"required": True, "values": ["National", "EU-wide", "Regional"]}
            }
        }
    
    def assess_registration_requirement(self, ai_system_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess whether an AI system requires EU database registration
        
        Args:
            ai_system_metadata: Metadata about the AI system
            
        Returns:
            Assessment result with registration requirements
        """
        system_category = self._classify_ai_system(ai_system_metadata)
        
        if not system_category:
            return {
                'registration_required': False,
                'reason': 'System does not fall under high-risk AI categories',
                'category': None,
                'deadline': None
            }
        
        # Calculate registration deadline (August 2, 2027 for existing systems)
        deadline = datetime(2027, 8, 2)
        if datetime.now() > deadline:
            deadline = datetime.now() + timedelta(days=180)  # 6 months for new systems
        
        return {
            'registration_required': True,
            'category': system_category.value,
            'deadline': deadline.isoformat(),
            'urgency': self._calculate_urgency(deadline),
            'requirements_count': len(self.registration_requirements.get(system_category.value, [])),
            'estimated_completion_time': '4-8 weeks',
            'next_steps': self._generate_next_steps(system_category)
        }
    
    def _classify_ai_system(self, metadata: Dict[str, Any]) -> Optional[AISystemCategory]:
        """Classify AI system into high-risk category"""
        purpose = metadata.get('intended_purpose', '').lower()
        use_case = metadata.get('use_case', '').lower()
        domain = metadata.get('domain', '').lower()
        
        classification_rules = {
            AISystemCategory.BIOMETRIC_IDENTIFICATION: [
                r'\b(?:biometric|facial\s+recognition|voice\s+recognition|fingerprint|iris\s+scan)\b',
                r'\b(?:identity\s+verification|authentication|access\s+control)\b'
            ],
            AISystemCategory.EMPLOYMENT: [
                r'\b(?:recruitment|hiring|cv\s+screening|candidate\s+selection)\b',
                r'\b(?:performance\s+evaluation|promotion|termination|hr)\b'
            ],
            AISystemCategory.CRITICAL_INFRASTRUCTURE: [
                r'\b(?:power\s+grid|energy\s+management|water\s+treatment)\b',
                r'\b(?:transportation|traffic\s+control|infrastructure)\b'
            ],
            AISystemCategory.EDUCATION_TRAINING: [
                r'\b(?:student\s+assessment|educational\s+evaluation|academic\s+performance)\b',
                r'\b(?:learning\s+analytics|admission\s+decision)\b'
            ],
            AISystemCategory.ESSENTIAL_SERVICES: [
                r'\b(?:healthcare|medical\s+diagnosis|emergency\s+services)\b',
                r'\b(?:social\s+services|welfare|benefit\s+allocation)\b'
            ],
            AISystemCategory.LAW_ENFORCEMENT: [
                r'\b(?:law\s+enforcement|police|criminal\s+investigation)\b',
                r'\b(?:surveillance|predictive\s+policing|crime\s+analysis)\b'
            ]
        }
        
        full_text = f"{purpose} {use_case} {domain}"
        
        for category, patterns in classification_rules.items():
            if any(re.search(pattern, full_text, re.IGNORECASE) for pattern in patterns):
                return category
        
        return None
    
    def _calculate_urgency(self, deadline: datetime) -> str:
        """Calculate urgency level based on deadline"""
        days_remaining = (deadline - datetime.now()).days
        
        if days_remaining < 30:
            return "CRITICAL"
        elif days_remaining < 90:
            return "HIGH" 
        elif days_remaining < 180:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_next_steps(self, category: AISystemCategory) -> List[str]:
        """Generate specific next steps for registration process"""
        base_steps = [
            "Gather all required system documentation",
            "Complete conformity assessment procedures",
            "Prepare technical documentation",
            "Conduct risk assessment review"
        ]
        
        category_specific = {
            AISystemCategory.BIOMETRIC_IDENTIFICATION: [
                "Document biometric data processing procedures",
                "Prepare fundamental rights impact assessment",
                "Validate accuracy performance metrics"
            ],
            AISystemCategory.EMPLOYMENT: [
                "Conduct bias testing and documentation", 
                "Prepare GDPR compliance evidence",
                "Document human oversight procedures"
            ],
            AISystemCategory.CRITICAL_INFRASTRUCTURE: [
                "Complete safety and security assessments",
                "Prepare emergency response procedures",
                "Document backup and redundancy systems"
            ]
        }
        
        return base_steps + category_specific.get(category, [])
    
    def create_registration_profile(self, ai_system_metadata: Dict[str, Any]) -> SystemRegistrationProfile:
        """Create complete registration profile for AI system"""
        system_id = f"AI-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        assessment = self.assess_registration_requirement(ai_system_metadata)
        if not assessment['registration_required']:
            raise ValueError("System does not require EU database registration")
        
        category = AISystemCategory(assessment['category'])
        requirements = []
        
        # Load requirements for the system category
        for req_data in self.registration_requirements.get(category.value, []):
            requirements.append(req_data)
        
        return SystemRegistrationProfile(
            system_id=system_id,
            system_name=ai_system_metadata.get('name', 'Unnamed AI System'),
            category=category,
            provider_info={
                'name': ai_system_metadata.get('provider_name', ''),
                'registration_number': ai_system_metadata.get('provider_registration', ''),
                'address': ai_system_metadata.get('provider_address', ''),
                'contact_email': ai_system_metadata.get('contact_email', ''),
                'authorized_representative': ai_system_metadata.get('authorized_rep', '')
            },
            deployer_info={
                'name': ai_system_metadata.get('deployer_name', ''),
                'address': ai_system_metadata.get('deployer_address', ''),
                'contact_email': ai_system_metadata.get('deployer_email', '')
            },
            technical_specs={
                'version': ai_system_metadata.get('version', '1.0'),
                'intended_purpose': ai_system_metadata.get('intended_purpose', ''),
                'deployment_date': ai_system_metadata.get('deployment_date', ''),
                'geographic_scope': ai_system_metadata.get('geographic_scope', 'National'),
                'performance_metrics': ai_system_metadata.get('performance_metrics', {})
            },
            risk_assessment={
                'completed': False,
                'assessment_date': None,
                'risk_level': ai_system_metadata.get('risk_level', 'High'),
                'mitigation_measures': []
            },
            conformity_assessment={
                'completed': False,
                'assessment_body': None,
                'certificate_number': None,
                'validity_date': None
            },
            requirements=requirements,
            status=RegistrationStatus.PREPARATION_NEEDED,
            submission_deadline=datetime.fromisoformat(assessment['deadline']),
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
    
    def validate_registration_readiness(self, profile: SystemRegistrationProfile) -> Dict[str, Any]:
        """Validate registration readiness and identify missing requirements"""
        validation_result = {
            'ready_for_submission': False,
            'completion_percentage': 0,
            'missing_requirements': [],
            'validation_errors': [],
            'recommendations': []
        }
        
        # Check requirement completion
        completed_requirements = sum(1 for req in profile.requirements if req.completed)
        mandatory_requirements = sum(1 for req in profile.requirements if req.is_mandatory)
        
        completion_percentage = (completed_requirements / len(profile.requirements)) * 100 if profile.requirements else 0
        validation_result['completion_percentage'] = round(completion_percentage, 1)
        
        # Identify missing mandatory requirements
        missing_mandatory = [req for req in profile.requirements if req.is_mandatory and not req.completed]
        validation_result['missing_requirements'] = [
            {
                'requirement_id': req.requirement_id,
                'title': req.title,
                'description': req.description,
                'examples': req.examples
            }
            for req in missing_mandatory
        ]
        
        # Validate provider information
        provider_errors = self._validate_provider_info(profile.provider_info)
        validation_result['validation_errors'].extend(provider_errors)
        
        # Validate technical specifications
        tech_errors = self._validate_technical_specs(profile.technical_specs)
        validation_result['validation_errors'].extend(tech_errors)
        
        # Check overall readiness
        validation_result['ready_for_submission'] = (
            len(missing_mandatory) == 0 and 
            len(validation_result['validation_errors']) == 0 and
            completion_percentage >= 90
        )
        
        # Generate recommendations
        if not validation_result['ready_for_submission']:
            validation_result['recommendations'] = self._generate_completion_recommendations(
                missing_mandatory, validation_result['validation_errors'], completion_percentage
            )
        
        return validation_result
    
    def _validate_provider_info(self, provider_info: Dict[str, str]) -> List[str]:
        """Validate provider information"""
        errors = []
        rules = self.validation_rules['provider_validation']
        
        for field, rule in rules.items():
            value = provider_info.get(field, '')
            
            if rule.get('required', False) and not value:
                errors.append(f"Provider {field} is required")
                continue
                
            if 'min_length' in rule and len(value) < rule['min_length']:
                errors.append(f"Provider {field} must be at least {rule['min_length']} characters")
                
            if 'pattern' in rule and not re.match(rule['pattern'], value):
                errors.append(f"Provider {field} format is invalid")
        
        return errors
    
    def _validate_technical_specs(self, tech_specs: Dict[str, Any]) -> List[str]:
        """Validate technical specifications"""
        errors = []
        rules = self.validation_rules['system_validation']
        
        for field, rule in rules.items():
            value = tech_specs.get(field, '')
            
            if rule.get('required', False) and not value:
                errors.append(f"Technical specification '{field}' is required")
                continue
                
            if isinstance(value, str):
                if 'min_length' in rule and len(value) < rule['min_length']:
                    errors.append(f"Technical specification '{field}' must be at least {rule['min_length']} characters")
                    
                if 'max_length' in rule and len(value) > rule['max_length']:
                    errors.append(f"Technical specification '{field}' must be no more than {rule['max_length']} characters")
                    
                if 'pattern' in rule and not re.match(rule['pattern'], value):
                    errors.append(f"Technical specification '{field}' format is invalid")
                    
            if 'values' in rule and value not in rule['values']:
                errors.append(f"Technical specification '{field}' must be one of: {', '.join(rule['values'])}")
        
        return errors
    
    def _generate_completion_recommendations(self, missing_requirements: List[RegistrationRequirement], 
                                           validation_errors: List[str], completion_percentage: float) -> List[str]:
        """Generate specific recommendations for completing registration"""
        recommendations = []
        
        if missing_requirements:
            recommendations.append(f"📋 Complete {len(missing_requirements)} mandatory requirements")
            for req in missing_requirements[:3]:  # Show top 3
                recommendations.append(f"  • {req.title}")
        
        if validation_errors:
            recommendations.append(f"🔧 Fix {len(validation_errors)} validation errors")
            
        if completion_percentage < 50:
            recommendations.append("📊 Registration is less than 50% complete - focus on mandatory requirements first")
        elif completion_percentage < 80:
            recommendations.append("📊 Registration is progressing well - complete remaining mandatory items")
        else:
            recommendations.append("📊 Registration is nearly complete - review all details before submission")
            
        recommendations.extend([
            "📅 Monitor submission deadline and plan accordingly",
            "🔍 Review EU AI Act Article 49 requirements",
            "📞 Consider consulting with AI Act legal experts",
            "💾 Maintain backup copies of all registration documents"
        ])
        
        return recommendations
    
    def generate_submission_package(self, profile: SystemRegistrationProfile) -> Dict[str, Any]:
        """Generate complete submission package for EU database"""
        validation = self.validate_registration_readiness(profile)
        
        if not validation['ready_for_submission']:
            raise ValueError(f"Registration not ready for submission. Completion: {validation['completion_percentage']}%")
        
        return {
            'submission_id': f"SUB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
            'system_profile': {
                'system_id': profile.system_id,
                'system_name': profile.system_name,
                'category': profile.category.value,
                'provider_info': profile.provider_info,
                'deployer_info': profile.deployer_info,
                'technical_specifications': profile.technical_specs,
                'risk_assessment': profile.risk_assessment,
                'conformity_assessment': profile.conformity_assessment
            },
            'requirements_evidence': [
                {
                    'requirement_id': req.requirement_id,
                    'title': req.title,
                    'completed': req.completed,
                    'evidence': req.evidence_provided
                }
                for req in profile.requirements
            ],
            'submission_metadata': {
                'preparation_date': profile.created_date.isoformat(),
                'submission_date': datetime.now().isoformat(),
                'submitter_contact': profile.provider_info.get('contact_email'),
                'estimated_review_time': '60-90 days',
                'next_steps': [
                    "Submit package to EU AI database portal",
                    "Await confirmation of receipt",
                    "Respond to any requests for additional information",
                    "Receive registration confirmation"
                ]
            },
            'legal_declarations': {
                'conformity_declaration': True,
                'accuracy_declaration': True,
                'completeness_declaration': True,
                'authorized_signature_required': True
            }
        }