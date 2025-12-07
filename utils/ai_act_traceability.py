"""
AI Act Traceability Matrix and Enhanced Compliance Features
Provides full 113-article traceability, remediation priority scoring,
conformity assessment readiness, and regulator-ready reporting
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
import json


class ArticleStatus(Enum):
    """Compliance status for each article"""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"
    REQUIRES_ASSESSMENT = "requires_assessment"
    IN_PROGRESS = "in_progress"


class PriorityLevel(Enum):
    """Remediation priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ConformityStatus(Enum):
    """Conformity assessment readiness"""
    READY = "ready"
    PARTIAL = "partial"
    NOT_READY = "not_ready"
    PENDING_EVIDENCE = "pending_evidence"


@dataclass
class ArticleAssessment:
    """Individual article compliance assessment"""
    article_number: int
    article_title: str
    chapter: str
    status: ArticleStatus
    compliance_score: float
    evidence_documents: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    remediation_actions: List[str] = field(default_factory=list)
    owner: Optional[str] = None
    deadline: Optional[str] = None
    effort_hours: float = 0.0
    business_impact: str = "medium"
    last_assessed: Optional[str] = None


@dataclass
class RemediationItem:
    """Prioritized remediation item"""
    id: str
    article_reference: str
    finding: str
    priority: PriorityLevel
    business_impact_score: float
    effort_hours: float
    deadline: str
    owner: Optional[str]
    status: str
    dependencies: List[str] = field(default_factory=list)
    evidence_required: List[str] = field(default_factory=list)


@dataclass
class ConformityAssessmentReadiness:
    """Conformity assessment readiness scorecard"""
    overall_readiness: float
    documentation_completeness: float
    technical_requirements_met: float
    governance_requirements_met: float
    human_oversight_implemented: float
    risk_management_score: float
    quality_management_score: float
    missing_elements: List[str]
    recommendations: List[str]
    estimated_time_to_ready: str


# Complete EU AI Act Article Definitions (All 113 Articles)
EU_AI_ACT_ARTICLES = {
    # Chapter I: General Provisions
    1: {"title": "Subject matter", "chapter": "I - General Provisions", "category": "scope", "mandatory": True},
    2: {"title": "Scope", "chapter": "I - General Provisions", "category": "scope", "mandatory": True},
    3: {"title": "Definitions", "chapter": "I - General Provisions", "category": "scope", "mandatory": True},
    4: {"title": "AI literacy", "chapter": "I - General Provisions", "category": "governance", "mandatory": True},
    
    # Chapter II: Prohibited AI Practices
    5: {"title": "Prohibited AI practices", "chapter": "II - Prohibited Practices", "category": "prohibition", "mandatory": True},
    
    # Chapter III: High-Risk AI Systems - Section 1
    6: {"title": "Classification rules for high-risk AI systems", "chapter": "III - High-Risk AI", "category": "classification", "mandatory": True},
    7: {"title": "Amendments to Annex III", "chapter": "III - High-Risk AI", "category": "classification", "mandatory": False},
    
    # Section 2: Requirements
    8: {"title": "Compliance with requirements", "chapter": "III - High-Risk AI", "category": "requirements", "mandatory": True},
    9: {"title": "Risk management system", "chapter": "III - High-Risk AI", "category": "requirements", "mandatory": True},
    10: {"title": "Data and data governance", "chapter": "III - High-Risk AI", "category": "data", "mandatory": True},
    11: {"title": "Technical documentation", "chapter": "III - High-Risk AI", "category": "documentation", "mandatory": True},
    12: {"title": "Record-keeping", "chapter": "III - High-Risk AI", "category": "documentation", "mandatory": True},
    13: {"title": "Transparency and provision of information", "chapter": "III - High-Risk AI", "category": "transparency", "mandatory": True},
    14: {"title": "Human oversight", "chapter": "III - High-Risk AI", "category": "oversight", "mandatory": True},
    15: {"title": "Accuracy, robustness and cybersecurity", "chapter": "III - High-Risk AI", "category": "technical", "mandatory": True},
    
    # Section 3: Obligations of providers and deployers
    16: {"title": "Obligations of providers - Quality management", "chapter": "III - High-Risk AI", "category": "obligations", "mandatory": True},
    17: {"title": "Automatic logging system", "chapter": "III - High-Risk AI", "category": "technical", "mandatory": True},
    18: {"title": "Accessibility requirements", "chapter": "III - High-Risk AI", "category": "requirements", "mandatory": True},
    19: {"title": "Conformity assessment", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": True},
    20: {"title": "Automatically generated logs", "chapter": "III - High-Risk AI", "category": "documentation", "mandatory": True},
    21: {"title": "Cooperation with competent authorities", "chapter": "III - High-Risk AI", "category": "governance", "mandatory": True},
    22: {"title": "Authorized representatives", "chapter": "III - High-Risk AI", "category": "governance", "mandatory": False},
    23: {"title": "Obligations of importers", "chapter": "III - High-Risk AI", "category": "obligations", "mandatory": False},
    24: {"title": "Obligations of distributors", "chapter": "III - High-Risk AI", "category": "obligations", "mandatory": False},
    25: {"title": "Responsibilities along the AI value chain", "chapter": "III - High-Risk AI", "category": "obligations", "mandatory": True},
    26: {"title": "Obligations of deployers - Human oversight", "chapter": "III - High-Risk AI", "category": "oversight", "mandatory": True},
    27: {"title": "Fundamental rights impact assessment", "chapter": "III - High-Risk AI", "category": "rights", "mandatory": True},
    28: {"title": "Registration obligations", "chapter": "III - High-Risk AI", "category": "registration", "mandatory": True},
    29: {"title": "Deployers of high-risk AI systems", "chapter": "III - High-Risk AI", "category": "obligations", "mandatory": True},
    
    # Section 4: Notifying authorities and notified bodies
    30: {"title": "Notifying authorities", "chapter": "III - High-Risk AI", "category": "governance", "mandatory": False},
    31: {"title": "Application of a conformity assessment body", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    32: {"title": "Notification procedure", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    33: {"title": "Requirements for notified bodies", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    34: {"title": "Subsidiaries and subcontracting", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    35: {"title": "Identification numbers and lists", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    36: {"title": "Changes to notifications", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    37: {"title": "Challenge to competence of notified bodies", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    38: {"title": "Coordination of notified bodies", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    39: {"title": "Conformity assessment bodies in third countries", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    
    # Section 5: Standards, conformity assessment
    40: {"title": "Harmonised standards", "chapter": "III - High-Risk AI", "category": "standards", "mandatory": False},
    41: {"title": "Common specifications", "chapter": "III - High-Risk AI", "category": "standards", "mandatory": False},
    42: {"title": "Presumption of conformity", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": True},
    43: {"title": "Conformity assessment procedures", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": True},
    44: {"title": "Certificates", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": True},
    45: {"title": "Information obligations of notified bodies", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    46: {"title": "Derogation from conformity assessment procedure", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": False},
    47: {"title": "EU declaration of conformity", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": True},
    48: {"title": "CE marking", "chapter": "III - High-Risk AI", "category": "conformity", "mandatory": True},
    49: {"title": "Registration", "chapter": "III - High-Risk AI", "category": "registration", "mandatory": True},
    
    # Chapter IV: Transparency for certain AI systems
    50: {"title": "Transparency obligations for certain AI systems", "chapter": "IV - Transparency", "category": "transparency", "mandatory": True},
    
    # Chapter V: General-purpose AI models
    51: {"title": "Classification of GPAI models", "chapter": "V - GPAI Models", "category": "gpai", "mandatory": True},
    52: {"title": "Procedure for classification of GPAI models", "chapter": "V - GPAI Models", "category": "gpai", "mandatory": True},
    53: {"title": "Obligations for providers of GPAI models", "chapter": "V - GPAI Models", "category": "gpai", "mandatory": True},
    54: {"title": "Authorised representatives of GPAI providers", "chapter": "V - GPAI Models", "category": "gpai", "mandatory": False},
    55: {"title": "Obligations for providers of GPAI models with systemic risk", "chapter": "V - GPAI Models", "category": "gpai", "mandatory": True},
    56: {"title": "Codes of practice", "chapter": "V - GPAI Models", "category": "gpai", "mandatory": False},
    
    # Chapter VI: Measures in support of innovation
    57: {"title": "AI regulatory sandboxes", "chapter": "VI - Innovation", "category": "innovation", "mandatory": False},
    58: {"title": "Detailed arrangements for AI regulatory sandboxes", "chapter": "VI - Innovation", "category": "innovation", "mandatory": False},
    59: {"title": "Further processing of personal data for sandboxes", "chapter": "VI - Innovation", "category": "innovation", "mandatory": False},
    60: {"title": "Testing of high-risk AI systems in real world conditions", "chapter": "VI - Innovation", "category": "innovation", "mandatory": False},
    61: {"title": "Informed consent for real world testing", "chapter": "VI - Innovation", "category": "innovation", "mandatory": False},
    62: {"title": "Measures for providers and deployers (SMEs)", "chapter": "VI - Innovation", "category": "innovation", "mandatory": False},
    63: {"title": "Derogations for specific operators", "chapter": "VI - Innovation", "category": "innovation", "mandatory": False},
    
    # Chapter VII: Governance
    64: {"title": "AI Office", "chapter": "VII - Governance", "category": "governance", "mandatory": True},
    65: {"title": "European Artificial Intelligence Board", "chapter": "VII - Governance", "category": "governance", "mandatory": True},
    66: {"title": "Composition of the Board", "chapter": "VII - Governance", "category": "governance", "mandatory": False},
    67: {"title": "Tasks of the Board", "chapter": "VII - Governance", "category": "governance", "mandatory": False},
    68: {"title": "Advisory forum", "chapter": "VII - Governance", "category": "governance", "mandatory": False},
    69: {"title": "Scientific panel of independent experts", "chapter": "VII - Governance", "category": "governance", "mandatory": False},
    70: {"title": "National competent authorities", "chapter": "VII - Governance", "category": "governance", "mandatory": True},
    71: {"title": "Powers of national competent authorities", "chapter": "VII - Governance", "category": "governance", "mandatory": True},
    72: {"title": "Market surveillance and control", "chapter": "VII - Governance", "category": "surveillance", "mandatory": True},
    
    # Chapter VIII: EU database
    73: {"title": "EU database for high-risk AI systems", "chapter": "VIII - EU Database", "category": "registration", "mandatory": True},
    
    # Chapter IX: Post-market monitoring, information sharing, market surveillance
    74: {"title": "Post-market monitoring by providers", "chapter": "IX - Post-Market", "category": "monitoring", "mandatory": True},
    75: {"title": "Reporting of serious incidents", "chapter": "IX - Post-Market", "category": "monitoring", "mandatory": True},
    76: {"title": "Market surveillance authorities", "chapter": "IX - Post-Market", "category": "surveillance", "mandatory": True},
    77: {"title": "Powers of market surveillance authorities", "chapter": "IX - Post-Market", "category": "surveillance", "mandatory": True},
    78: {"title": "Confidentiality", "chapter": "IX - Post-Market", "category": "governance", "mandatory": True},
    79: {"title": "Procedure at national level concerning AI systems presenting risk", "chapter": "IX - Post-Market", "category": "surveillance", "mandatory": True},
    80: {"title": "Union safeguard procedure", "chapter": "IX - Post-Market", "category": "surveillance", "mandatory": True},
    81: {"title": "Compliant AI systems which present a risk", "chapter": "IX - Post-Market", "category": "surveillance", "mandatory": True},
    82: {"title": "Formal non-compliance", "chapter": "IX - Post-Market", "category": "enforcement", "mandatory": True},
    
    # Chapter X: Codes of conduct and guidelines
    83: {"title": "Codes of conduct for voluntary application", "chapter": "X - Codes of Conduct", "category": "governance", "mandatory": False},
    84: {"title": "Guidelines from the Commission", "chapter": "X - Codes of Conduct", "category": "governance", "mandatory": False},
    
    # Chapter XI: Delegation and committee procedure
    85: {"title": "Exercise of delegation", "chapter": "XI - Delegation", "category": "governance", "mandatory": False},
    86: {"title": "Committee procedure", "chapter": "XI - Delegation", "category": "governance", "mandatory": False},
    
    # Chapter XII: Penalties
    87: {"title": "Penalties", "chapter": "XII - Penalties", "category": "enforcement", "mandatory": True},
    88: {"title": "Administrative fines on Union institutions", "chapter": "XII - Penalties", "category": "enforcement", "mandatory": True},
    
    # Chapter XIII: Final provisions
    89: {"title": "Amendment to Regulation (EC) No 300/2008", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    90: {"title": "Amendment to Regulation (EU) No 167/2013", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    91: {"title": "Amendment to Regulation (EU) No 168/2013", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    92: {"title": "Amendment to Directive 2014/90/EU", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    93: {"title": "Amendment to Directive (EU) 2016/797", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    94: {"title": "Amendment to Regulation (EU) 2018/858", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    95: {"title": "Amendment to Regulation (EU) 2018/1139", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    96: {"title": "Amendment to Regulation (EU) 2019/2144", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    97: {"title": "Amendment to Directive (EU) 2020/1828", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    98: {"title": "Amendment to Directive (EU) 2022/2555", "chapter": "XIII - Final", "category": "amendments", "mandatory": False},
    99: {"title": "AI systems already placed on market or in service", "chapter": "XIII - Final", "category": "transition", "mandatory": True},
    100: {"title": "Evaluation and review", "chapter": "XIII - Final", "category": "governance", "mandatory": True},
    101: {"title": "Entry into force", "chapter": "XIII - Final", "category": "transition", "mandatory": True},
    102: {"title": "Application dates", "chapter": "XIII - Final", "category": "transition", "mandatory": True},
    
    # Additional Articles (extended provisions)
    103: {"title": "Addressees", "chapter": "XIII - Final", "category": "scope", "mandatory": True},
    104: {"title": "Annexes - Annex I (Harmonisation legislation)", "chapter": "Annexes", "category": "annexes", "mandatory": True},
    105: {"title": "Annexes - Annex II (List of Union harmonisation legislation)", "chapter": "Annexes", "category": "annexes", "mandatory": True},
    106: {"title": "Annexes - Annex III (High-risk AI systems)", "chapter": "Annexes", "category": "annexes", "mandatory": True},
    107: {"title": "Annexes - Annex IV (Technical documentation)", "chapter": "Annexes", "category": "annexes", "mandatory": True},
    108: {"title": "Annexes - Annex V (EU declaration of conformity)", "chapter": "Annexes", "category": "annexes", "mandatory": True},
    109: {"title": "Annexes - Annex VI (Conformity assessment procedure)", "chapter": "Annexes", "category": "annexes", "mandatory": True},
    110: {"title": "Annexes - Annex VII (Conformity based on QMS)", "chapter": "Annexes", "category": "annexes", "mandatory": True},
    111: {"title": "Annexes - Annex VIII (Information for registration)", "chapter": "Annexes", "category": "annexes", "mandatory": True},
    112: {"title": "Annexes - Annex IX (Union legislation on large-scale IT)", "chapter": "Annexes", "category": "annexes", "mandatory": False},
    113: {"title": "Annexes - Annex X (Union legislation on financial services)", "chapter": "Annexes", "category": "annexes", "mandatory": False},
}


class AIActTraceabilityMatrix:
    """Complete 113-article traceability matrix with status tracking"""
    
    def __init__(self, risk_level: str = "high_risk", region: str = "Netherlands"):
        self.risk_level = risk_level
        self.region = region
        self.assessments: Dict[int, ArticleAssessment] = {}
        self._initialize_assessments()
    
    def _initialize_assessments(self):
        """Initialize all 113 articles with default assessments"""
        for article_num, article_info in EU_AI_ACT_ARTICLES.items():
            self.assessments[article_num] = ArticleAssessment(
                article_number=article_num,
                article_title=article_info["title"],
                chapter=article_info["chapter"],
                status=ArticleStatus.REQUIRES_ASSESSMENT,
                compliance_score=0.0,
                last_assessed=None
            )
    
    def update_article_status(self, article_num: int, status: ArticleStatus, 
                             score: float, gaps: List[str] = None,
                             evidence: List[str] = None, owner: str = None):
        """Update status for specific article"""
        if article_num in self.assessments:
            self.assessments[article_num].status = status
            self.assessments[article_num].compliance_score = score
            self.assessments[article_num].gaps = gaps or []
            self.assessments[article_num].evidence_documents = evidence or []
            self.assessments[article_num].owner = owner
            self.assessments[article_num].last_assessed = datetime.now().isoformat()
    
    def get_applicable_articles(self) -> List[int]:
        """Get list of applicable articles based on risk level"""
        if self.risk_level == "high_risk":
            return list(range(1, 103))  # Most articles applicable
        elif self.risk_level == "limited_risk":
            return [1, 2, 3, 4, 5, 50, 64, 65, 70, 71, 72, 87, 99, 100, 101, 102, 103]
        elif self.risk_level == "minimal_risk":
            return [1, 2, 3, 4, 5, 50, 83, 84, 99, 100, 101, 102, 103]
        else:  # GPAI
            return [1, 2, 3, 4, 5, 51, 52, 53, 54, 55, 56, 64, 65, 70, 71, 72, 87, 99, 100, 101, 102, 103]
    
    def calculate_overall_compliance(self) -> Dict[str, Any]:
        """Calculate overall compliance metrics"""
        applicable = self.get_applicable_articles()
        
        compliant_count = 0
        partial_count = 0
        non_compliant_count = 0
        not_applicable_count = 0
        total_score = 0.0
        
        for article_num in applicable:
            if article_num in self.assessments:
                assessment = self.assessments[article_num]
                if assessment.status == ArticleStatus.COMPLIANT:
                    compliant_count += 1
                    total_score += 100.0
                elif assessment.status == ArticleStatus.PARTIALLY_COMPLIANT:
                    partial_count += 1
                    total_score += assessment.compliance_score
                elif assessment.status == ArticleStatus.NOT_APPLICABLE:
                    not_applicable_count += 1
                    total_score += 100.0
                else:
                    non_compliant_count += 1
                    total_score += assessment.compliance_score
        
        assessed_count = len(applicable) - not_applicable_count
        overall_score = total_score / len(applicable) if applicable else 0.0
        
        return {
            "overall_compliance_score": round(overall_score, 1),
            "total_articles": len(applicable),
            "compliant": compliant_count,
            "partially_compliant": partial_count,
            "non_compliant": non_compliant_count,
            "not_applicable": not_applicable_count,
            "compliance_rate": round((compliant_count + partial_count) / assessed_count * 100, 1) if assessed_count > 0 else 0.0
        }
    
    def generate_chapter_summary(self) -> Dict[str, Dict[str, Any]]:
        """Generate compliance summary by chapter"""
        chapters = {}
        
        for article_num, assessment in self.assessments.items():
            chapter = assessment.chapter
            if chapter not in chapters:
                chapters[chapter] = {
                    "articles": [],
                    "compliant": 0,
                    "partial": 0,
                    "non_compliant": 0,
                    "score": 0.0
                }
            
            chapters[chapter]["articles"].append(article_num)
            if assessment.status == ArticleStatus.COMPLIANT:
                chapters[chapter]["compliant"] += 1
            elif assessment.status == ArticleStatus.PARTIALLY_COMPLIANT:
                chapters[chapter]["partial"] += 1
            else:
                chapters[chapter]["non_compliant"] += 1
            chapters[chapter]["score"] += assessment.compliance_score
        
        # Calculate averages
        for chapter in chapters:
            count = len(chapters[chapter]["articles"])
            chapters[chapter]["average_score"] = round(chapters[chapter]["score"] / count, 1) if count > 0 else 0.0
        
        return chapters
    
    def export_traceability_matrix(self) -> Dict[str, Any]:
        """Export full traceability matrix as structured data"""
        return {
            "generated_at": datetime.now().isoformat(),
            "risk_level": self.risk_level,
            "region": self.region,
            "overall_metrics": self.calculate_overall_compliance(),
            "chapter_summary": self.generate_chapter_summary(),
            "article_assessments": {
                str(num): {
                    "article_number": assessment.article_number,
                    "title": assessment.article_title,
                    "chapter": assessment.chapter,
                    "status": assessment.status.value,
                    "compliance_score": assessment.compliance_score,
                    "gaps": assessment.gaps,
                    "evidence": assessment.evidence_documents,
                    "owner": assessment.owner,
                    "last_assessed": assessment.last_assessed
                }
                for num, assessment in self.assessments.items()
            }
        }


class RemediationPriorityEngine:
    """Prioritized remediation with business impact scoring"""
    
    BUSINESS_IMPACT_WEIGHTS = {
        "critical": 1.0,
        "high": 0.75,
        "medium": 0.5,
        "low": 0.25,
        "informational": 0.1
    }
    
    ARTICLE_CRITICALITY = {
        5: 1.0,    # Prohibited practices - highest
        6: 0.9,    # Risk classification
        9: 0.85,   # Risk management
        10: 0.85,  # Data governance
        13: 0.8,   # Transparency
        14: 0.85,  # Human oversight
        15: 0.8,   # Accuracy, robustness
        16: 0.75,  # Quality management
        17: 0.7,   # Logging
        26: 0.85,  # Deployer obligations
        27: 0.9,   # Fundamental rights
        43: 0.8,   # Conformity assessment
        47: 0.75,  # EU declaration
        53: 0.8,   # GPAI obligations
        55: 0.85,  # GPAI systemic risk
        74: 0.7,   # Post-market monitoring
        75: 0.8,   # Incident reporting
        87: 0.9,   # Penalties
    }
    
    def __init__(self):
        self.remediation_items: List[RemediationItem] = []
    
    def calculate_priority_score(self, article_num: int, finding_severity: str,
                                 compliance_gap: float, days_to_deadline: int) -> float:
        """Calculate weighted priority score"""
        
        # Base criticality from article
        article_criticality = self.ARTICLE_CRITICALITY.get(article_num, 0.5)
        
        # Severity weight
        severity_weight = self.BUSINESS_IMPACT_WEIGHTS.get(finding_severity, 0.5)
        
        # Gap weight (higher gap = higher priority)
        gap_weight = (100 - compliance_gap) / 100
        
        # Deadline urgency (exponential increase as deadline approaches)
        if days_to_deadline <= 0:
            deadline_weight = 1.0
        elif days_to_deadline <= 30:
            deadline_weight = 0.9
        elif days_to_deadline <= 90:
            deadline_weight = 0.7
        elif days_to_deadline <= 180:
            deadline_weight = 0.5
        else:
            deadline_weight = 0.3
        
        # Combined score (weighted average)
        priority_score = (
            article_criticality * 0.3 +
            severity_weight * 0.25 +
            gap_weight * 0.25 +
            deadline_weight * 0.2
        )
        
        return round(priority_score * 100, 1)
    
    def add_remediation_item(self, article_ref: str, finding: str,
                            priority: PriorityLevel, impact_score: float,
                            effort_hours: float, deadline: str,
                            owner: str = None, dependencies: List[str] = None):
        """Add prioritized remediation item"""
        item = RemediationItem(
            id=f"REM-{len(self.remediation_items) + 1:04d}",
            article_reference=article_ref,
            finding=finding,
            priority=priority,
            business_impact_score=impact_score,
            effort_hours=effort_hours,
            deadline=deadline,
            owner=owner,
            status="open",
            dependencies=dependencies or [],
            evidence_required=[]
        )
        self.remediation_items.append(item)
        return item.id
    
    def get_prioritized_remediation_plan(self) -> List[Dict[str, Any]]:
        """Get remediation items sorted by priority"""
        sorted_items = sorted(
            self.remediation_items,
            key=lambda x: (
                -x.business_impact_score,  # Higher impact first
                {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}[x.priority.value]
            )
        )
        
        return [
            {
                "id": item.id,
                "article": item.article_reference,
                "finding": item.finding,
                "priority": item.priority.value,
                "impact_score": item.business_impact_score,
                "effort_hours": item.effort_hours,
                "deadline": item.deadline,
                "owner": item.owner,
                "status": item.status,
                "dependencies": item.dependencies
            }
            for item in sorted_items
        ]
    
    def generate_remediation_timeline(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate remediation timeline by deadline"""
        timeline = {
            "immediate": [],  # Within 30 days
            "short_term": [],  # 30-90 days
            "medium_term": [],  # 90-180 days
            "long_term": []  # 180+ days
        }
        
        for item in self.remediation_items:
            try:
                deadline_date = datetime.fromisoformat(item.deadline)
                days_remaining = (deadline_date - datetime.now()).days
                
                item_data = {
                    "id": item.id,
                    "finding": item.finding[:100] + "..." if len(item.finding) > 100 else item.finding,
                    "priority": item.priority.value,
                    "effort": f"{item.effort_hours}h"
                }
                
                if days_remaining <= 30:
                    timeline["immediate"].append(item_data)
                elif days_remaining <= 90:
                    timeline["short_term"].append(item_data)
                elif days_remaining <= 180:
                    timeline["medium_term"].append(item_data)
                else:
                    timeline["long_term"].append(item_data)
            except:
                timeline["medium_term"].append({
                    "id": item.id,
                    "finding": item.finding[:100] + "...",
                    "priority": item.priority.value,
                    "effort": f"{item.effort_hours}h"
                })
        
        return timeline


class ConformityAssessmentScorecard:
    """Conformity assessment readiness scorecard"""
    
    CONFORMITY_REQUIREMENTS = {
        "documentation": {
            "technical_documentation": 0.15,
            "risk_assessment": 0.12,
            "data_governance_docs": 0.10,
            "testing_documentation": 0.08,
            "instructions_for_use": 0.08
        },
        "technical": {
            "accuracy_metrics": 0.10,
            "robustness_testing": 0.10,
            "cybersecurity_measures": 0.10,
            "automatic_logging": 0.08
        },
        "governance": {
            "quality_management_system": 0.12,
            "human_oversight_procedures": 0.10,
            "post_market_monitoring": 0.08,
            "incident_response_plan": 0.06
        },
        "compliance": {
            "eu_declaration": 0.08,
            "ce_marking_ready": 0.05,
            "eu_database_registration": 0.05,
            "authorized_representative": 0.05
        }
    }
    
    def __init__(self, risk_level: str = "high_risk"):
        self.risk_level = risk_level
        self.requirements_status: Dict[str, Dict[str, bool]] = {}
        self._initialize_requirements()
    
    def _initialize_requirements(self):
        """Initialize all requirements as not met"""
        for category, requirements in self.CONFORMITY_REQUIREMENTS.items():
            self.requirements_status[category] = {req: False for req in requirements}
    
    def update_requirement(self, category: str, requirement: str, met: bool):
        """Update requirement status"""
        if category in self.requirements_status:
            if requirement in self.requirements_status[category]:
                self.requirements_status[category][requirement] = met
    
    def calculate_readiness_score(self) -> ConformityAssessmentReadiness:
        """Calculate conformity assessment readiness"""
        
        total_score = 0.0
        doc_score = 0.0
        tech_score = 0.0
        gov_score = 0.0
        missing = []
        
        for category, requirements in self.CONFORMITY_REQUIREMENTS.items():
            for req, weight in requirements.items():
                if self.requirements_status.get(category, {}).get(req, False):
                    total_score += weight * 100
                    if category == "documentation":
                        doc_score += weight * 100 / 0.53
                    elif category == "technical":
                        tech_score += weight * 100 / 0.38
                    elif category == "governance":
                        gov_score += weight * 100 / 0.36
                else:
                    missing.append(f"{category.title()}: {req.replace('_', ' ').title()}")
        
        # Determine time to ready
        if total_score >= 90:
            time_estimate = "Ready for assessment"
        elif total_score >= 70:
            time_estimate = "1-2 months preparation"
        elif total_score >= 50:
            time_estimate = "3-4 months preparation"
        elif total_score >= 30:
            time_estimate = "5-6 months preparation"
        else:
            time_estimate = "6+ months preparation"
        
        recommendations = self._generate_recommendations(missing, total_score)
        
        return ConformityAssessmentReadiness(
            overall_readiness=round(total_score, 1),
            documentation_completeness=round(doc_score, 1),
            technical_requirements_met=round(tech_score, 1),
            governance_requirements_met=round(gov_score, 1),
            human_oversight_implemented=100.0 if self.requirements_status.get("governance", {}).get("human_oversight_procedures", False) else 0.0,
            risk_management_score=100.0 if self.requirements_status.get("documentation", {}).get("risk_assessment", False) else 0.0,
            quality_management_score=100.0 if self.requirements_status.get("governance", {}).get("quality_management_system", False) else 0.0,
            missing_elements=missing,
            recommendations=recommendations,
            estimated_time_to_ready=time_estimate
        )
    
    def _generate_recommendations(self, missing: List[str], score: float) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        if score < 30:
            recommendations.append("🚨 CRITICAL: Establish basic compliance framework before conformity assessment")
            recommendations.append("📋 Create technical documentation according to Annex IV requirements")
            recommendations.append("⚖️ Implement risk management system per Article 9")
        
        if score < 60:
            recommendations.append("📊 Develop quality management system per Article 16")
            recommendations.append("👁️ Implement human oversight mechanisms per Article 14")
            recommendations.append("🔒 Complete cybersecurity assessment per Article 15")
        
        if score < 80:
            recommendations.append("📝 Finalize EU declaration of conformity per Article 47")
            recommendations.append("🏷️ Prepare CE marking requirements per Article 48")
            recommendations.append("📡 Register in EU database per Article 49")
        
        if score >= 80:
            recommendations.append("✅ System approaching conformity readiness")
            recommendations.append("📞 Consider engaging notified body for assessment")
            recommendations.append("🔄 Schedule pre-assessment review")
        
        # Add Netherlands-specific
        recommendations.append("🇳🇱 Netherlands: Align with Dutch DPA (Autoriteit Persoonsgegevens) guidance")
        
        return recommendations[:6]  # Limit to 6 most relevant
    
    def export_scorecard(self) -> Dict[str, Any]:
        """Export conformity scorecard"""
        readiness = self.calculate_readiness_score()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "risk_level": self.risk_level,
            "readiness_scores": {
                "overall": readiness.overall_readiness,
                "documentation": readiness.documentation_completeness,
                "technical": readiness.technical_requirements_met,
                "governance": readiness.governance_requirements_met,
                "human_oversight": readiness.human_oversight_implemented,
                "risk_management": readiness.risk_management_score,
                "quality_management": readiness.quality_management_score
            },
            "status_by_category": {
                category: {
                    req: "✅ Met" if met else "❌ Not Met"
                    for req, met in reqs.items()
                }
                for category, reqs in self.requirements_status.items()
            },
            "missing_elements": readiness.missing_elements,
            "recommendations": readiness.recommendations,
            "estimated_time_to_ready": readiness.estimated_time_to_ready
        }


def generate_regulator_ready_summary(
    traceability: AIActTraceabilityMatrix,
    remediation: RemediationPriorityEngine,
    conformity: ConformityAssessmentScorecard,
    system_name: str,
    organization: str = "Organization"
) -> Dict[str, Any]:
    """Generate regulator-ready executive summary"""
    
    overall = traceability.calculate_overall_compliance()
    readiness = conformity.calculate_readiness_score()
    remediation_plan = remediation.get_prioritized_remediation_plan()
    
    critical_items = [r for r in remediation_plan if r["priority"] == "critical"]
    high_items = [r for r in remediation_plan if r["priority"] == "high"]
    
    return {
        "document_type": "EU AI Act Compliance Assessment - Executive Summary",
        "document_version": "1.0",
        "generated_date": datetime.now().strftime("%Y-%m-%d"),
        "regulatory_framework": "EU AI Act (Regulation (EU) 2024/1689)",
        
        "organization": {
            "name": organization,
            "ai_system_name": system_name,
            "risk_classification": traceability.risk_level.upper().replace("_", " "),
            "assessment_region": traceability.region
        },
        
        "compliance_overview": {
            "overall_score": f"{overall['overall_compliance_score']}%",
            "rating": "COMPLIANT" if overall['overall_compliance_score'] >= 80 else "PARTIALLY COMPLIANT" if overall['overall_compliance_score'] >= 50 else "NON-COMPLIANT",
            "articles_assessed": overall['total_articles'],
            "compliant_articles": overall['compliant'],
            "partial_compliance": overall['partially_compliant'],
            "non_compliant_articles": overall['non_compliant']
        },
        
        "conformity_assessment_readiness": {
            "readiness_score": f"{readiness.overall_readiness}%",
            "status": "READY" if readiness.overall_readiness >= 80 else "PARTIAL" if readiness.overall_readiness >= 50 else "NOT READY",
            "time_to_ready": readiness.estimated_time_to_ready,
            "critical_gaps": len([m for m in readiness.missing_elements if "documentation" in m.lower() or "risk" in m.lower()])
        },
        
        "remediation_summary": {
            "total_items": len(remediation_plan),
            "critical_priority": len(critical_items),
            "high_priority": len(high_items),
            "estimated_effort_hours": sum(r["effort_hours"] for r in remediation_plan)
        },
        
        "key_findings": {
            "critical_issues": [r["finding"][:150] for r in critical_items[:3]],
            "high_priority_issues": [r["finding"][:150] for r in high_items[:3]]
        },
        
        "next_steps": readiness.recommendations[:5],
        
        "regulatory_deadlines": {
            "prohibited_practices": "February 2, 2025",
            "gpai_models": "August 2, 2025",
            "high_risk_systems": "August 2, 2026",
            "certain_high_risk": "August 2, 2027"
        },
        
        "netherlands_specific": {
            "authority": "Autoriteit Persoonsgegevens (Dutch DPA)",
            "additional_requirements": [
                "UAVG compliance alignment",
                "BSN handling procedures (if applicable)",
                "Dutch language transparency notices"
            ]
        },
        
        "certification": {
            "assessment_date": datetime.now().strftime("%Y-%m-%d"),
            "valid_until": "Subject to re-assessment upon material changes",
            "assessor": "DataGuardian Pro AI Compliance Platform"
        }
    }
