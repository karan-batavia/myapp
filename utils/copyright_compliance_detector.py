"""
Copyright Compliance Detection for AI Training Data
Critical for GPAI models under EU AI Act August 2025 requirements
"""

import re
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import json

class CopyrightComplianceDetector:
    """
    Detects copyright compliance issues in AI training data and model development.
    Critical for EU AI Act Article 53 - GPAI model obligations.
    """
    
    def __init__(self, region: str = "Netherlands"):
        self.region = region
        self.copyright_patterns = self._load_copyright_patterns()
        self.license_patterns = self._load_license_patterns()
        self.attribution_patterns = self._load_attribution_patterns()
        
    def _load_copyright_patterns(self) -> Dict[str, Any]:
        """Load copyright detection patterns"""
        return {
            "copyright_notices": {
                "pattern": r"(?:©|\(c\)|copyright)\s*(?:\d{4}[-\d\s,]*|\d{4})\s*(?:by\s+)?([^.\n\r]+)",
                "description": "Copyright notices and claims",
                "severity": "high"
            },
            "all_rights_reserved": {
                "pattern": r"\b(?:all\s+rights\s+reserved|proprietary|confidential)\b",
                "description": "All rights reserved or proprietary content markers",
                "severity": "high"
            },
            "trademark_content": {
                "pattern": r"(?:™|®|\(tm\)|\(r\))\s*([^.\n\r\s]+)",
                "description": "Trademarked content usage",
                "severity": "medium"
            },
            "publisher_content": {
                "pattern": r"\b(?:published\s+by|publisher|press|publications?)\s*:?\s*([^.\n\r]+)",
                "description": "Published content from commercial publishers",
                "severity": "high"
            },
            "book_references": {
                "pattern": r"\b(?:isbn[-\s]?(?:10|13)?)\s*:?\s*([\d\-\s]+)",
                "description": "Book content with ISBN identifiers",
                "severity": "high"
            },
            "news_content": {
                "pattern": r"\b(?:reuters|associated\s+press|ap\s+news|bloomberg|wall\s+street\s+journal|financial\s+times)\b",
                "description": "Commercial news agency content",
                "severity": "high"
            }
        }
    
    def _load_license_patterns(self) -> Dict[str, Any]:
        """Load open source license patterns and compliance requirements"""
        return {
            "gpl_violations": {
                "pattern": r"\b(?:gnu\s+general\s+public\s+license|gpl\s*[v\d]*)\b",
                "description": "GPL licensed code requiring source disclosure",
                "severity": "critical",
                "compliance_requirement": "Source code disclosure and GPL license propagation required"
            },
            "mit_license": {
                "pattern": r"\b(?:mit\s+license|permission\s+is\s+hereby\s+granted)\b",
                "description": "MIT licensed code requiring attribution",
                "severity": "medium", 
                "compliance_requirement": "Attribution and license text inclusion required"
            },
            "apache_license": {
                "pattern": r"\b(?:apache\s+license|apache\s+software\s+foundation)\b",
                "description": "Apache licensed code requiring attribution",
                "severity": "medium",
                "compliance_requirement": "Attribution and license text inclusion required"
            },
            "creative_commons": {
                "pattern": r"\b(?:creative\s+commons|cc\s+by|cc\s+sa|cc\s+nc)\b",
                "description": "Creative Commons licensed content",
                "severity": "medium",
                "compliance_requirement": "Attribution and share-alike requirements"
            },
            "proprietary_licenses": {
                "pattern": r"\b(?:proprietary\s+license|commercial\s+license|enterprise\s+license)\b",
                "description": "Proprietary licensed content requiring permission",
                "severity": "critical",
                "compliance_requirement": "Explicit permission required for commercial use"
            },
            "no_license": {
                "pattern": r"(?:no\s+license|all\s+rights\s+reserved|unlicensed)",
                "description": "Unlicensed content with all rights reserved",
                "severity": "critical",
                "compliance_requirement": "Cannot be used without explicit permission"
            }
        }
    
    def _load_attribution_patterns(self) -> Dict[str, Any]:
        """Load attribution requirement patterns"""
        return {
            "missing_attribution": {
                "indicators": [
                    r"\b(?:source|author|credit|attribution)\s*:?\s*(?:unknown|missing|none|n/a)\b",
                    r"\b(?:copied\s+from|taken\s+from|extracted\s+from)\s+(?:internet|web|online)\b"
                ],
                "description": "Content without proper attribution",
                "severity": "high"
            },
            "wikipedia_content": {
                "pattern": r"\b(?:wikipedia|wikimedia)\b",
                "description": "Wikipedia content requiring CC-BY-SA attribution",
                "severity": "medium",
                "attribution_requirement": "CC-BY-SA license and author attribution required"
            },
            "stackoverflow_content": {
                "pattern": r"\b(?:stack\s*overflow|stackoverflow)\b", 
                "description": "Stack Overflow content with CC license",
                "severity": "medium",
                "attribution_requirement": "CC-BY-SA license attribution required"
            },
            "github_content": {
                "pattern": r"\b(?:github\.com|raw\.githubusercontent)\b",
                "description": "GitHub hosted content requiring license compliance",
                "severity": "medium",
                "attribution_requirement": "Repository license compliance required"
            }
        }
    
    def detect_copyright_violations(self, content: str, metadata: Optional[Dict[str, Any]] = None, source_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Detect copyright compliance violations in content.
        
        Args:
            content: Text content to analyze
            metadata: Additional metadata about the content source
            source_file: Source file path for actionable location fields
            
        Returns:
            List of copyright compliance findings
        """
        findings = []
        metadata = metadata or {}
        
        findings.extend(self._detect_copyright_claims(content))
        findings.extend(self._detect_license_violations(content))
        findings.extend(self._detect_attribution_issues(content))
        findings.extend(self._detect_proprietary_datasets(content))
        findings.extend(self._analyze_fair_use_compliance(content, metadata))
        findings.extend(self._detect_commercial_content(content))
        
        if source_file:
            for finding in findings:
                loc = finding.get('location', '')
                if re.match(r'^Position \d+-\d+$', loc):
                    finding['location'] = source_file
        
        return findings
    
    def _detect_copyright_claims(self, content: str) -> List[Dict[str, Any]]:
        """Detect copyright notices and claims in content"""
        findings = []
        
        for pattern_name, config in self.copyright_patterns.items():
            matches = re.finditer(config["pattern"], content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                findings.append({
                    'type': 'COPYRIGHT_VIOLATION',
                    'category': f'Copyright Claim - {pattern_name.replace("_", " ").title()}',
                    'value': match.group().strip(),
                    'risk_level': config["severity"].title(),
                    'regulation': 'EU AI Act Article 53 - GPAI Copyright Compliance',
                    'description': config["description"],
                    'location': f"Position {match.start()}-{match.end()}",
                    'remediation': 'Verify copyright ownership or obtain proper licensing/attribution',
                    'ai_act_compliance': 'Critical for GPAI models under Article 53',
                    'penalty_risk': 'Up to €15M or 3% global turnover for GPAI violations'
                })
        
        return findings
    
    def _detect_license_violations(self, content: str) -> List[Dict[str, Any]]:
        """Detect open source license violations"""
        findings = []
        
        for license_type, config in self.license_patterns.items():
            matches = re.finditer(config["pattern"], content, re.IGNORECASE)
            for match in matches:
                findings.append({
                    'type': 'LICENSE_VIOLATION',
                    'category': f'License Compliance - {license_type.replace("_", " ").title()}',
                    'value': match.group().strip(),
                    'risk_level': config["severity"].title(),
                    'regulation': 'EU AI Act Article 53 - GPAI License Compliance',
                    'description': config["description"],
                    'compliance_requirement': config["compliance_requirement"],
                    'location': f"Position {match.start()}-{match.end()}",
                    'remediation': f'Ensure compliance: {config["compliance_requirement"]}',
                    'ai_act_compliance': 'Required for GPAI model training data',
                    'penalty_risk': 'License violation + AI Act penalties'
                })
        
        return findings
    
    def _detect_attribution_issues(self, content: str) -> List[Dict[str, Any]]:
        """Detect missing or inadequate attribution"""
        findings = []
        
        for attr_type, config in self.attribution_patterns.items():
            if "indicators" in config:
                # Check multiple indicators
                for indicator in config["indicators"]:
                    matches = re.finditer(indicator, content, re.IGNORECASE)
                    for match in matches:
                        findings.append({
                            'type': 'ATTRIBUTION_VIOLATION',
                            'category': f'Attribution Issue - {attr_type.replace("_", " ").title()}',
                            'value': match.group().strip(),
                            'risk_level': config["severity"].title(),
                            'regulation': 'EU AI Act Article 53 + Copyright Law',
                            'description': config["description"],
                            'location': f"Position {match.start()}-{match.end()}",
                            'remediation': 'Add proper attribution and source crediting',
                            'ai_act_compliance': 'GPAI models must respect intellectual property rights'
                        })
            else:
                # Single pattern check
                matches = re.finditer(config["pattern"], content, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        'type': 'ATTRIBUTION_VIOLATION', 
                        'category': f'Attribution Required - {attr_type.replace("_", " ").title()}',
                        'value': match.group().strip(),
                        'risk_level': config["severity"].title(),
                        'regulation': 'EU AI Act Article 53 + Source License',
                        'description': config["description"],
                        'attribution_requirement': config.get("attribution_requirement", "Proper attribution required"),
                        'location': f"Position {match.start()}-{match.end()}",
                        'remediation': config.get("attribution_requirement", "Add proper attribution"),
                        'ai_act_compliance': 'Required for GPAI training data transparency'
                    })
        
        return findings
    
    def _detect_proprietary_datasets(self, content: str) -> List[Dict[str, Any]]:
        """Detect usage of proprietary datasets"""
        findings = []
        
        proprietary_indicators = [
            r"\b(?:private\s+dataset|proprietary\s+data|commercial\s+dataset)\b",
            r"\b(?:subscription\s+data|premium\s+data|paid\s+access)\b",
            r"\b(?:internal\s+data|confidential\s+dataset|restricted\s+access)\b",
            r"\b(?:customer\s+data|user\s+data|personal\s+information)\s+(?:training|dataset)\b"
        ]
        
        for pattern in proprietary_indicators:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                findings.append({
                    'type': 'PROPRIETARY_DATASET_VIOLATION',
                    'category': 'Proprietary Dataset Usage',
                    'value': match.group().strip(),
                    'risk_level': 'Critical',
                    'regulation': 'EU AI Act Article 53 + Data Protection Laws',
                    'description': 'Usage of proprietary or restricted datasets',
                    'location': f"Position {match.start()}-{match.end()}",
                    'remediation': 'Verify legal rights to use proprietary datasets in AI training',
                    'ai_act_compliance': 'GPAI models must ensure lawful data acquisition',
                    'gdpr_risk': 'Potential GDPR violations if personal data involved'
                })
        
        return findings
    
    def _analyze_fair_use_compliance(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze fair use compliance for copyrighted content"""
        findings = []
        
        # Check for fair use indicators
        fair_use_indicators = [
            r"\b(?:research|educational|criticism|comment|news\s+reporting)\b",
            r"\b(?:transformative|derivative|parody|commentary)\b",
            r"\b(?:small\s+portion|limited\s+excerpt|brief\s+quote)\b"
        ]
        
        copyright_usage = [
            r"\b(?:full\s+text|complete\s+work|entire\s+article)\b", 
            r"\b(?:commercial\s+use|profit|revenue|monetize)\b",
            r"\b(?:substantial\s+portion|majority|most\s+of)\b"
        ]
        
        fair_use_score = 0
        commercial_use_score = 0
        
        for pattern in fair_use_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                fair_use_score += 1
                
        for pattern in copyright_usage:
            if re.search(pattern, content, re.IGNORECASE):
                commercial_use_score += 1
        
        if commercial_use_score > fair_use_score:
            findings.append({
                'type': 'FAIR_USE_VIOLATION',
                'category': 'Fair Use Compliance Risk',
                'value': f'Commercial use score: {commercial_use_score}, Fair use score: {fair_use_score}',
                'risk_level': 'High',
                'regulation': 'EU AI Act Article 53 + Copyright Fair Use',
                'description': 'Potential fair use violation - commercial usage exceeds fair use indicators',
                'remediation': 'Review fair use justification or obtain proper licensing',
                'ai_act_compliance': 'GPAI models must respect fair use limitations',
                'legal_risk': 'Copyright infringement liability'
            })
        
        return findings
    
    def _detect_commercial_content(self, content: str) -> List[Dict[str, Any]]:
        """Detect commercial content that may require licensing"""
        findings = []
        
        commercial_patterns = [
            r"\b(?:getty\s+images|shutterstock|adobe\s+stock)\b",
            r"\b(?:financial\s+times|wall\s+street\s+journal|bloomberg)\b",
            r"\b(?:premium\s+content|subscription\s+only|paid\s+article)\b",
            r"\b(?:licensing\s+required|commercial\s+license)\b"
        ]
        
        for pattern in commercial_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                findings.append({
                    'type': 'COMMERCIAL_CONTENT_VIOLATION',
                    'category': 'Commercial Content Usage',
                    'value': match.group().strip(),
                    'risk_level': 'High',
                    'regulation': 'EU AI Act Article 53 + Commercial Licensing',
                    'description': 'Commercial content requiring licensing for AI training',
                    'location': f"Position {match.start()}-{match.end()}",
                    'remediation': 'Obtain commercial license or remove from training data',
                    'ai_act_compliance': 'GPAI models must ensure lawful content acquisition',
                    'penalty_risk': 'Commercial licensing violations + AI Act penalties'
                })
        
        return findings
    
    def generate_copyright_compliance_report(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive copyright compliance report"""
        if not findings:
            return {
                'overall_status': 'COMPLIANT',
                'risk_level': 'Low',
                'total_violations': 0,
                'compliance_score': 100
            }
        
        # Categorize findings by severity
        critical_count = len([f for f in findings if f.get('risk_level') == 'Critical'])
        high_count = len([f for f in findings if f.get('risk_level') == 'High'])
        medium_count = len([f for f in findings if f.get('risk_level') == 'Medium'])
        
        # Calculate compliance score
        total_violations = len(findings)
        compliance_score = max(0, 100 - (critical_count * 25 + high_count * 15 + medium_count * 5))
        
        # Determine overall status
        if critical_count > 0:
            overall_status = 'NON_COMPLIANT'
            risk_level = 'Critical'
        elif high_count > 5:
            overall_status = 'HIGH_RISK'
            risk_level = 'High'
        elif total_violations > 10:
            overall_status = 'REVIEW_REQUIRED'
            risk_level = 'Medium'
        else:
            overall_status = 'MOSTLY_COMPLIANT'
            risk_level = 'Low'
        
        return {
            'overall_status': overall_status,
            'risk_level': risk_level,
            'compliance_score': compliance_score,
            'total_violations': total_violations,
            'critical_violations': critical_count,
            'high_risk_violations': high_count,
            'medium_risk_violations': medium_count,
            'ai_act_readiness': compliance_score >= 85,
            'recommendations': self._generate_compliance_recommendations(findings),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_compliance_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate specific compliance recommendations"""
        recommendations = []
        
        violation_types = set(f.get('type') for f in findings)
        
        if 'COPYRIGHT_VIOLATION' in violation_types:
            recommendations.append("🔍 Audit all training data for copyright notices and obtain proper licensing")
            
        if 'LICENSE_VIOLATION' in violation_types:
            recommendations.append("📄 Implement license compliance tracking for all open source content")
            
        if 'ATTRIBUTION_VIOLATION' in violation_types:
            recommendations.append("📝 Add comprehensive attribution documentation for all sources")
            
        if 'PROPRIETARY_DATASET_VIOLATION' in violation_types:
            recommendations.append("🔒 Review proprietary dataset usage rights and permissions")
            
        if 'FAIR_USE_VIOLATION' in violation_types:
            recommendations.append("⚖️ Conduct fair use analysis for all copyrighted content")
            
        if 'COMMERCIAL_CONTENT_VIOLATION' in violation_types:
            recommendations.append("💼 Obtain commercial licenses for premium content usage")
        
        recommendations.append("🤖 Ensure GPAI model compliance with EU AI Act Article 53 requirements")
        recommendations.append("📊 Implement ongoing copyright monitoring for training data updates")
        
        return recommendations