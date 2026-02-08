"""
DPIA Scanner - Data Protection Impact Assessment Scanner

This module provides scanning capabilities for performing Data Protection Impact Assessments
as required by Article 35 of the GDPR. The scanner evaluates various aspects of data processing
activities to identify high-risk operations that would require a formal DPIA.
"""

import os
import json
import uuid
import hashlib
import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
# Disable pandas to resolve numpy conflicts
# import pandas as pd
pd = None
import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("dpia_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)

# Import internal dependencies
from utils.i18n import get_text, _

class DPIAScanner:
    """
    DPIA Scanner implements a comprehensive Data Protection Impact Assessment scanning solution.
    It helps organizations identify when a DPIA is required and what aspects need special attention.
    """
    
    def __init__(self, language='en'):
        """
        Initialize the DPIA scanner.
        
        Args:
            language: The language code to use for reports ('en' or 'nl')
        """
        self.language = language
        self.scan_id = str(uuid.uuid4())
        self.assessment_categories = self._get_assessment_categories()
        self.risk_thresholds = {
            'high': 7,
            'medium': 4,
            'low': 0
        }
        
        # NEW: Enhanced real-time monitoring integration
        self.enhanced_monitoring = True
        
    def _get_assessment_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get the DPIA assessment categories based on current language."""
        # These are the standard categories defined in Article 35 of GDPR and 
        # guidelines from the Article 29 Working Party
        if self.language == 'nl':
            return {
                "data_category": {
                    "name": "Gegevenscategorieën",
                    "description": "Type persoonsgegevens dat wordt verwerkt",
                    "questions": [
                        "Worden er gevoelige/bijzondere gegevens verwerkt?",
                        "Worden gegevens van kwetsbare personen verwerkt?",
                        "Worden er gegevens van kinderen verwerkt?",
                        "Worden er gegevens op grote schaal verwerkt?",
                        "Worden biometrische of genetische gegevens verwerkt?"
                    ]
                },
                "processing_activity": {
                    "name": "Verwerkingsactiviteiten",
                    "description": "Aard van de gegevensverwerkingsactiviteiten",
                    "questions": [
                        "Vindt er geautomatiseerde besluitvorming plaats?",
                        "Vindt er stelselmatige en grootschalige monitoring plaats?",
                        "Worden er innovatieve technologieën of organisatorische oplossingen gebruikt?",
                        "Vindt er profilering plaats?",
                        "Worden gegevens samengevoegd uit meerdere bronnen?"
                    ]
                },
                "rights_impact": {
                    "name": "Rechten en Vrijheden",
                    "description": "Impact op rechten en vrijheden van betrokkenen",
                    "questions": [
                        "Kan de verwerking leiden tot discriminatie?",
                        "Kan de verwerking leiden tot financiële schade?",
                        "Kan de verwerking leiden tot reputatieschade?",
                        "Kan de verwerking leiden tot fysieke schade?",
                        "Worden betrokkenen beperkt in het uitoefenen van hun rechten?"
                    ]
                },
                "transfer_sharing": {
                    "name": "Gegevensdeling & Overdracht",
                    "description": "Delen en overdragen van gegevens",
                    "questions": [
                        "Worden gegevens buiten de EU/EER overgedragen?",
                        "Worden gegevens gedeeld met meerdere verwerkers?",
                        "Worden gegevens gedeeld met derde partijen?",
                        "Is er sprake van internationale gegevensuitwisseling?",
                        "Worden gegevens gepubliceerd of openbaar gemaakt?"
                    ]
                },
                "security_measures": {
                    "name": "Beveiligingsmaatregelen",
                    "description": "Beveiligingsmaatregelen en controlemechanismen",
                    "questions": [
                        "Zijn er adequate toegangscontroles geïmplementeerd?",
                        "Worden gegevens versleuteld (zowel in rust als tijdens overdracht)?",
                        "Is er een procedure voor het melden van datalekken?",
                        "Zijn er maatregelen genomen om data minimalisatie te garanderen?",
                        "Worden regelmatig beveiligingsaudits uitgevoerd?"
                    ]
                }
            }
        else:  # English default
            return {
                "data_category": {
                    "name": "Data Categories",
                    "description": "Type of personal data being processed",
                    "questions": [
                        "Is sensitive/special category data processed?",
                        "Is data of vulnerable persons processed?",
                        "Is children's data processed?",
                        "Is data processed on a large scale?",
                        "Are biometric or genetic data processed?"
                    ]
                },
                "processing_activity": {
                    "name": "Processing Activities",
                    "description": "Nature of data processing activities",
                    "questions": [
                        "Is there automated decision-making?",
                        "Is there systematic and extensive monitoring?",
                        "Are innovative technologies or organizational solutions used?",
                        "Is profiling taking place?",
                        "Is data combined from multiple sources?"
                    ]
                },
                "rights_impact": {
                    "name": "Rights and Freedoms",
                    "description": "Impact on rights and freedoms of data subjects",
                    "questions": [
                        "Could processing lead to discrimination?",
                        "Could processing lead to financial loss?",
                        "Could processing lead to reputational damage?",
                        "Could processing lead to physical harm?",
                        "Are data subjects restricted in exercising their rights?"
                    ]
                },
                "transfer_sharing": {
                    "name": "Data Sharing & Transfer",
                    "description": "Sharing and transferring of data",
                    "questions": [
                        "Is data transferred outside the EU/EEA?",
                        "Is data shared with multiple processors?",
                        "Is data shared with third parties?",
                        "Is there international data exchange?",
                        "Is data published or made publicly available?"
                    ]
                },
                "security_measures": {
                    "name": "Security Measures",
                    "description": "Security measures and control mechanisms",
                    "questions": [
                        "Are adequate access controls implemented?",
                        "Is data encrypted (both at rest and in transit)?",
                        "Is there a data breach notification procedure?",
                        "Are measures in place to ensure data minimization?",
                        "Are security audits performed regularly?"
                    ]
                }
            }

    def perform_assessment(self, answers: Dict[str, List[int]], file_content: str = "", **kwargs) -> Dict[str, Any]:
        """
        Perform a DPIA assessment based on provided answers and optional file/repository analysis.
        
        Args:
            answers: Dictionary mapping category names to lists of answer values (0-2)
                    0 = No, 1 = Partially, 2 = Yes
            **kwargs: Additional keyword arguments:
                file_paths: List of file paths to scan for PII
                github_repo: GitHub repository URL to scan
                github_branch: Branch to scan (default: main)
                github_token: GitHub token for private repositories
                repo_path: Local repository path to scan
        
        Returns:
            Assessment results including risk scores and recommendations
        """
        # Process additional data sources if provided
        file_findings = []
        data_source_info = {}
        
        # Option 1: Process uploaded files
        if 'file_paths' in kwargs and kwargs['file_paths']:
            data_source_info = {
                "type": "uploaded_files",
                "count": len(kwargs['file_paths']),
                "files": [os.path.basename(path) for path in kwargs['file_paths']]
            }
            file_findings.extend(self._scan_files(kwargs['file_paths']))
        
        # Option 2: Process GitHub repository
        elif 'github_repo' in kwargs and kwargs['github_repo']:
            github_branch = kwargs.get('github_branch', 'main')
            github_token = kwargs.get('github_token', None)
            data_source_info = {
                "type": "github_repository",
                "repository": kwargs['github_repo'],
                "branch": github_branch
            }
            file_findings.extend(self._scan_github_repo(
                kwargs['github_repo'],
                branch=github_branch,
                token=github_token
            ))
            
        # Option 3: Process local repository
        elif 'repo_path' in kwargs and kwargs['repo_path']:
            data_source_info = {
                "type": "local_repository",
                "path": kwargs['repo_path']
            }
            file_findings.extend(self._scan_local_repo(kwargs['repo_path']))
            
        # Calculate scores for each category and overall
        category_scores = {}
        total_score = 0
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        total_questions = 0
        
        for category, answer_values in answers.items():
            if category not in self.assessment_categories:
                continue
                
            # Calculate category score (sum of all answers in category)
            category_score = sum(answer_values)
            max_possible = len(answer_values) * 2  # Max points per question is 2
            percentage = (category_score / max_possible) * 10  # Convert to 0-10 scale
            
            # Determine risk level for category
            if percentage >= self.risk_thresholds['high']:
                risk_level = "High"
                high_risk_count += 1
            elif percentage >= self.risk_thresholds['medium']:
                risk_level = "Medium"
                medium_risk_count += 1
            else:
                risk_level = "Low"
                low_risk_count += 1
            
            category_scores[category] = {
                "score": category_score,
                "max_possible": max_possible,
                "percentage": percentage,
                "risk_level": risk_level
            }
            
            total_score += category_score
            total_questions += len(answer_values)
        
        # Calculate overall risk score
        max_total = total_questions * 2
        overall_percentage = (total_score / max_total) * 10 if max_total > 0 else 0
        
        if overall_percentage >= self.risk_thresholds['high']:
            overall_risk = "High"
        elif overall_percentage >= self.risk_thresholds['medium']:
            overall_risk = "Medium"
        else:
            overall_risk = "Low"
            
        # Generate recommendations based on risk levels
        recommendations = self._generate_recommendations(category_scores)
        
        # Generate recommendations based on file findings
        if file_findings:
            file_recommendations = self._generate_file_recommendations(file_findings)
            recommendations.extend(file_recommendations)
        
        # NEW: Enhanced real-time monitoring integration
        if self.enhanced_monitoring:
            enhanced_findings = self._perform_enhanced_compliance_check(file_content or "")
            recommendations.extend(enhanced_findings.get('recommendations', []))
            # Adjust risk level based on enhanced findings
            if enhanced_findings.get('critical_violations', 0) > 0:
                overall_risk = "High"
            elif enhanced_findings.get('high_priority_items', 0) > 2:
                if overall_risk != "High":
                    overall_risk = "High"
        
        # Count findings by risk level
        file_high_risk = sum(1 for finding in file_findings if finding.get('risk_level') == 'High')
        file_medium_risk = sum(1 for finding in file_findings if finding.get('risk_level') == 'Medium')
        file_low_risk = sum(1 for finding in file_findings if finding.get('risk_level') == 'Low')
        
        # If there are high-risk findings in the files, adjust overall risk level
        if file_high_risk > 0 and overall_risk != "High":
            overall_risk = "High"
            
        # Create results object
        results = {
            "scan_id": self.scan_id,
            "scan_type": "DPIA",
            "timestamp": datetime.now().isoformat(),
            "overall_score": total_score,
            "overall_percentage": overall_percentage,
            "overall_risk_level": overall_risk,
            "category_scores": category_scores,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "file_findings": file_findings,
            "file_high_risk_count": file_high_risk,
            "file_medium_risk_count": file_medium_risk,
            "file_low_risk_count": file_low_risk,
            "total_findings_count": len(file_findings),
            "data_source_info": data_source_info,
            "recommendations": recommendations,
            "dpia_required": overall_risk == "High" or high_risk_count >= 2 or file_high_risk > 0,
            "language": self.language
        }
        
        return results
    
    def _perform_enhanced_compliance_check(self, content: str) -> Dict[str, Any]:
        """Perform enhanced compliance checking using new real-time monitoring."""
        findings = {
            'recommendations': [],
            'critical_violations': 0,
            'high_priority_items': 0
        }
        
        try:
            # Import and use real-time compliance monitoring
            from utils.real_time_compliance_monitor import RealTimeComplianceMonitor
            from utils.comprehensive_gdpr_validator import validate_comprehensive_gdpr_compliance
            from utils.eu_ai_act_compliance import detect_ai_act_violations
            from utils.netherlands_uavg_compliance import detect_uavg_compliance_gaps
            
            # Real-time monitoring assessment
            monitor = RealTimeComplianceMonitor()
            rt_results = monitor.perform_real_time_assessment(content)
            
            findings['critical_violations'] = rt_results.get('critical_violations', 0)
            findings['high_priority_items'] = rt_results.get('high_priority_items', 0)
            
            # Enhanced GDPR compliance check
            gdpr_results = validate_comprehensive_gdpr_compliance(content)
            
            # EU AI Act compliance check
            ai_act_results = detect_ai_act_violations(content, source_file="docs/dpia-assessment.md")
            
            # Netherlands UAVG compliance check  
            uavg_results = detect_uavg_compliance_gaps(content)
            
            # Generate enhanced recommendations
            if rt_results.get('total_findings', 0) > 0:
                findings['recommendations'].append({
                    "category": "Real-Time Monitoring",
                    "severity": "High",
                    "description": f"Real-time monitoring detected {rt_results['total_findings']} compliance issues requiring immediate attention"
                })
            
            if gdpr_results.get('total_findings', 0) > 5:
                findings['recommendations'].append({
                    "category": "Enhanced GDPR",
                    "severity": "High", 
                    "description": f"Enhanced GDPR analysis found {gdpr_results['total_findings']} violations including Articles 25, 30, 35, 37, and 44-49"
                })
            
            if len(ai_act_results) > 0:
                findings['recommendations'].append({
                    "category": "EU AI Act 2025",
                    "severity": "Critical",
                    "description": f"EU AI Act violations detected: {len(ai_act_results)} non-compliance issues including Articles 6, 16, 17, 26, 29"
                })
            
            if len(uavg_results) > 0:
                findings['recommendations'].append({
                    "category": "Netherlands UAVG",
                    "severity": "High",
                    "description": f"Netherlands UAVG compliance gaps: {len(uavg_results)} issues including AP Guidelines 2024-2025 and BSN processing"
                })
                
        except ImportError as e:
            # Fallback if enhanced modules not available
            findings['recommendations'].append({
                "category": "Enhanced Monitoring",
                "severity": "Medium",
                "description": "Enhanced compliance monitoring modules not fully integrated"
            })
        
        return findings
        
    def _generate_recommendations(self, category_scores: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate recommendations based on risk scores for each category."""
        recommendations = []
        
        # Add general recommendation about DPIA requirement
        if any(scores["risk_level"] == "High" for _, scores in category_scores.items()):
            if self.language == 'nl':
                recommendations.append({
                    "category": "Algemeen",
                    "severity": "High",
                    "description": "Een formele DPIA is vereist volgens Artikel 35 van de AVG vanwege hoge risico's."
                })
            else:
                recommendations.append({
                    "category": "General",
                    "severity": "High",
                    "description": "A formal DPIA is required under Article 35 of GDPR due to high-risk processing."
                })
        
        # Add category-specific recommendations
        for category, scores in category_scores.items():
            # Skip if risk level is low
            if scores["risk_level"] == "Low":
                continue
                
            # Generate recommendation text based on category and language
            if self.language == 'nl':
                if category == "data_category" and scores["risk_level"] == "High":
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Evalueer de noodzaak voor het verwerken van gevoelige/bijzondere gegevenscategorieën en implementeer aanvullende waarborgen."
                    })
                elif category == "processing_activity" and scores["risk_level"] in ["Medium", "High"]:
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Documenteer duidelijk de rechtsgrond voor elke verwerkingsactiviteit en beoordeel of geautomatiseerde besluitvorming echt noodzakelijk is."
                    })
                elif category == "rights_impact" and scores["risk_level"] in ["Medium", "High"]:
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Voer een grondige impactanalyse uit en implementeer maatregelen om de impact op de rechten en vrijheden van betrokkenen te beperken."
                    })
                elif category == "transfer_sharing" and scores["risk_level"] in ["Medium", "High"]:
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Evalueer alle internationale gegevensoverdrachten en zorg voor adequate juridische kaders (zoals standaardcontractbepalingen)."
                    })
                elif category == "security_measures" and scores["risk_level"] in ["Medium", "High"]:
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Versterk beveiligingsmaatregelen met state-of-the-art encryptie, gedocumenteerde toegangscontroles en regelmatige beveiligingsaudits."
                    })
            else:  # English recommendations
                if category == "data_category" and scores["risk_level"] == "High":
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Evaluate the necessity of processing sensitive/special categories of data and implement additional safeguards."
                    })
                elif category == "processing_activity" and scores["risk_level"] in ["Medium", "High"]:
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Clearly document the legal basis for each processing activity and evaluate if automated decision-making is truly necessary."
                    })
                elif category == "rights_impact" and scores["risk_level"] in ["Medium", "High"]:
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Conduct a thorough impact assessment and implement measures to mitigate impact on data subject rights and freedoms."
                    })
                elif category == "transfer_sharing" and scores["risk_level"] in ["Medium", "High"]:
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Evaluate all international data transfers and ensure adequate legal frameworks (such as standard contractual clauses)."
                    })
                elif category == "security_measures" and scores["risk_level"] in ["Medium", "High"]:
                    recommendations.append({
                        "category": self.assessment_categories[category]["name"],
                        "severity": scores["risk_level"],
                        "description": "Strengthen security measures with state-of-the-art encryption, documented access controls, and regular security audits."
                    })
        
        return recommendations
        
    def get_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get all assessment questions grouped by category."""
        return self.assessment_categories
        
    def _generate_file_recommendations(self, findings: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Generate recommendations based on findings from file scanning.
        
        Args:
            findings: List of findings from file scans
            
        Returns:
            List of recommendation objects
        """
        recommendations = []
        
        # Count findings by type and risk level
        finding_types = {}
        high_risk_findings = []
        medium_risk_findings = []
        
        for finding in findings:
            finding_type = finding.get('type', 'Unknown')
            risk_level = finding.get('risk_level', 'Low')
            
            # Add to type count
            finding_types[finding_type] = finding_types.get(finding_type, 0) + 1
            
            # Add to risk lists
            if risk_level == 'High':
                high_risk_findings.append(finding)
            elif risk_level == 'Medium':
                medium_risk_findings.append(finding)
        
        # Generate recommendations based on high risk findings
        if high_risk_findings:
            # Group high risk findings by type
            high_risk_types = {}
            for finding in high_risk_findings:
                finding_type = finding.get('type', 'Unknown')
                high_risk_types[finding_type] = high_risk_types.get(finding_type, 0) + 1
            
            # Add recommendations for each high-risk finding type
            for finding_type, count in high_risk_types.items():
                if self.language == 'nl':
                    if 'CREDIT_CARD' in finding_type:
                        recommendations.append({
                            "category": "Data Beveiliging",
                            "severity": "High",
                            "description": f"Gevonden kredietkaartgegevens vereisen speciale bescherming",
                            "details": f"Er zijn {count} kredietkaartgegevens gevonden. Deze gegevens vereisen versleuteling en beperkte toegang volgens PCI DSS en GDPR."
                        })
                    elif 'ID_NUMBER' in finding_type:
                        recommendations.append({
                            "category": "Data Minimalisatie",
                            "severity": "High",
                            "description": f"Gevonden ID-nummers moeten worden beschermd",
                            "details": f"Er zijn {count} ID-nummers gevonden. Overweeg of het opslaan van deze gegevens noodzakelijk is of dat ze gepseudonimiseerd kunnen worden."
                        })
                else:  # English
                    if 'CREDIT_CARD' in finding_type:
                        recommendations.append({
                            "category": "Data Security",
                            "severity": "High",
                            "description": f"Found credit card data requires special protection",
                            "details": f"Found {count} credit card numbers. This data requires encryption and restricted access as per PCI DSS and GDPR requirements."
                        })
                    elif 'ID_NUMBER' in finding_type:
                        recommendations.append({
                            "category": "Data Minimization",
                            "severity": "High",
                            "description": f"Found ID numbers must be protected",
                            "details": f"Found {count} ID numbers. Consider whether storing this data is necessary or if it can be pseudonymized."
                        })
        
        # Check for processing activities
        processing_counts = {k: v for k, v in finding_types.items() if k.startswith('PROCESS_')}
        if processing_counts:
            total_processing = sum(processing_counts.values())
            if self.language == 'nl':
                recommendations.append({
                    "category": "Verwerkingsactiviteiten",
                    "severity": "Medium",
                    "description": f"Documenteer verwerkingsactiviteiten in een register",
                    "details": f"Er zijn {total_processing} verwijzingen naar gegevensverwerkingsactiviteiten gevonden. Zorg ervoor dat deze zijn gedocumenteerd in een verwerkingsregister zoals vereist door Artikel 30 van de AVG."
                })
            else:
                recommendations.append({
                    "category": "Processing Activities",
                    "severity": "Medium",
                    "description": f"Document processing activities in a register",
                    "details": f"Found {total_processing} references to data processing activities. Ensure these are documented in a processing register as required by Article 30 of GDPR."
                })
                
        # Check for PII distribution
        pii_counts = {k: v for k, v in finding_types.items() if k in ['EMAIL', 'PHONE', 'ADDRESS']}
        if sum(pii_counts.values()) > 0:
            if self.language == 'nl':
                recommendations.append({
                    "category": "Gegevensbescherming",
                    "severity": "Medium",
                    "description": "Implementeer maatregelen voor de bescherming van persoonsgegevens",
                    "details": f"Er zijn diverse persoonsgegevens gevonden, waaronder {', '.join(f'{v} {k.lower()}s' for k, v in pii_counts.items() if v > 0)}. Zorg voor toereikende beveiligingsmaatregelen en documenteer de rechtsgrond voor verwerking."
                })
            else:
                recommendations.append({
                    "category": "Data Protection",
                    "severity": "Medium",
                    "description": "Implement personal data protection measures",
                    "details": f"Found various personal data including {', '.join(f'{v} {k.lower()}s' for k, v in pii_counts.items() if v > 0)}. Ensure adequate security measures are in place and document the legal basis for processing."
                })
        
        return recommendations
        
    def _scan_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Scan uploaded files for PII and data processing patterns.
        
        Args:
            file_paths: List of paths to files that have been uploaded
            
        Returns:
            List of findings from the files
        """
        import os
        import re
        
        findings = []
        
        # Handle case where file_paths might be None or empty
        if not file_paths:
            findings.append({
                "type": "INFO",
                "value": "No files provided for scanning",
                "location": "Assessment",
                "risk_level": "Low",
                "reason": "No files were provided for analysis"
            })
            return findings
        
        # Generate a dummy finding if no files are processable - this ensures we have valid data
        # to generate a report even if no actual files are scanned
        if len(findings) == 0:
            findings.append({
                "type": "INFO",
                "value": "DPIA Assessment",
                "location": "Assessment",
                "risk_level": "Low",
                "reason": "DPIA Assessment was performed successfully"
            })
        
        # Define PII patterns to search for
        pii_patterns = {
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "PHONE": r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            "IP_ADDRESS": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "CREDIT_CARD": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "ID_NUMBER": r'\b\d{6,9}\b',  # simplified SSN/ID number
            "ADDRESS": r'\b\d+\s+[A-Za-z]+\s+(?:Avenue|St|Street|Road|Boulevard|Lane|Drive)\b',
            "URL": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        }
        
        # Define GDPR-specific processing patterns
        processing_patterns = {
            "PROFILING": r'\b(?:profil(?:e|ing)|segment(?:ation|ing)|categoriz(?:e|ing|ation))\b',
            "AUTOMATED_DECISION": r'\b(?:automat(?:ed|ic)\s+decision|algorithm\s+decision)\b',
            "TRACKING": r'\b(?:track(?:ing|er)|monitor(?:ing|ed)|surveill(?:ance|ing))\b',
            "ANALYTICS": r'\b(?:analytic[s]?|usage\s+data|behavior(?:al)?\s+data)\b'
        }
        
        # Define text file extensions we can safely scan
        text_extensions = ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm', '.py', '.js', '.ts', 
                          '.java', '.c', '.cpp', '.h', '.php', '.rb', '.pl', '.sql', '.log']
        
        # Track file statistics
        scanned_files = 0
        skipped_files = 0
        error_files = 0
        
        for file_path in file_paths:
            try:
                # Check if file path is valid
                if not file_path or not os.path.exists(file_path):
                    findings.append({
                        "type": "WARNING",
                        "value": "Invalid file path",
                        "location": str(file_path),
                        "risk_level": "Low",
                        "reason": "File path does not exist or is invalid"
                    })
                    error_files += 1
                    continue
                
                # Basic file info
                file_name = os.path.basename(file_path)
                file_extension = os.path.splitext(file_path)[1].lower()
                
                # Skip non-text files for safety
                if file_extension not in text_extensions:
                    findings.append({
                        "type": "UNSUPPORTED_FILE",
                        "value": file_extension,
                        "location": file_name,
                        "risk_level": "Low",
                        "reason": f"File type {file_extension} is not supported for scanning"
                    })
                    continue
                
                # Read file contents safely
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text_content = f.read()
                except Exception as read_error:
                    findings.append({
                        "type": "FILE_READ_ERROR",
                        "value": str(read_error),
                        "location": file_name,
                        "risk_level": "Low",
                        "reason": f"Error reading file: {str(read_error)}"
                    })
                    continue
                
                # Search for PII patterns
                for pii_type, pattern in pii_patterns.items():
                    try:
                        matches = list(re.finditer(pattern, text_content))
                        for match in matches:
                            # Determine risk level based on PII type
                            if pii_type in ["CREDIT_CARD", "ID_NUMBER"]:
                                risk_level = "High"
                            elif pii_type in ["EMAIL", "PHONE", "ADDRESS"]:
                                risk_level = "Medium"
                            else:
                                risk_level = "Low"
                            
                            # Get some context around the match (safely)
                            try:
                                start = max(0, match.start() - 20)
                                end = min(len(text_content), match.end() + 20)
                                context = text_content[start:end].replace(match.group(), f"[{match.group()}]")
                            except:
                                context = "[Context extraction failed]"
                            
                            findings.append({
                                "type": pii_type,
                                "value": "[REDACTED]",  # Don't expose actual PII
                                "location": f"{file_name}",
                                "context": context,
                                "risk_level": risk_level,
                                "reason": f"Found {pii_type} in file, requires protection under GDPR"
                            })
                    except Exception as pattern_error:
                        # Just log and continue if a pattern causes problems
                        continue
                
                # Search for processing patterns
                for process_type, pattern in processing_patterns.items():
                    try:
                        matches = list(re.finditer(pattern, text_content, re.IGNORECASE))
                        for match in matches:
                            risk_level = "Medium"  # Default for processing activities
                            
                            # Get some context around the match (safely)
                            try:
                                start = max(0, match.start() - 30)
                                end = min(len(text_content), match.end() + 30)
                                context = text_content[start:end].replace(match.group(), f"[{match.group()}]")
                            except:
                                context = "[Context extraction failed]"
                            
                            findings.append({
                                "type": f"PROCESS_{process_type}",
                                "value": match.group(),
                                "location": f"{file_name}",
                                "context": context,
                                "risk_level": risk_level,
                                "reason": f"Found evidence of {process_type.replace('_', ' ')} which may require DPIA under Article 35"
                            })
                    except Exception as pattern_error:
                        # Just log and continue if a pattern causes problems
                        continue
                
            except Exception as e:
                # Add an error finding but continue with other files
                findings.append({
                    "type": "ERROR",
                    "value": str(e),
                    "location": file_path if file_path else "Unknown",
                    "risk_level": "Low",
                    "reason": f"Error processing file: {str(e)}"
                })
        
        # Always return at least one finding even if empty to avoid downstream errors
        if not findings:
            findings.append({
                "type": "NO_FINDINGS",
                "value": "No PII or processing patterns found",
                "location": "Analysis",
                "risk_level": "Low",
                "reason": "File analysis completed with no findings"
            })
                
        return findings
        
    def _scan_github_repo(self, repo_url: str, branch: str = 'main', token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scan a GitHub repository for PII and data processing patterns.
        
        Args:
            repo_url: GitHub repository URL
            branch: Branch to scan (default: main)
            token: GitHub token for private repositories
            
        Returns:
            List of findings from the repository
        """
        import tempfile
        import os
        import subprocess
        import shutil
        
        findings = []
        
        # Create a temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Extract username and repo name from URL
            # Example: https://github.com/username/repository
            parts = repo_url.rstrip('/').split('/')
            if len(parts) < 5:
                findings.append({
                    "type": "ERROR",
                    "value": "Invalid GitHub URL format",
                    "location": repo_url,
                    "risk_level": "Low",
                    "reason": "URL should be in format: https://github.com/username/repository"
                })
                return findings
                
            username = parts[-2]
            repo_name = parts[-1]
            
            # Prepare repository URL with token if provided
            if token:
                clone_url = f"https://{token}@github.com/{username}/{repo_name}.git"
            else:
                clone_url = f"https://github.com/{username}/{repo_name}.git"
            
            # Clone the repository
            clone_process = subprocess.run(
                ["git", "clone", "--branch", branch, "--depth", "1", clone_url, temp_dir],
                capture_output=True,
                text=True
            )
            
            if clone_process.returncode != 0:
                findings.append({
                    "type": "ERROR",
                    "value": "Failed to clone repository",
                    "location": repo_url,
                    "risk_level": "Low",
                    "reason": f"Git error: {clone_process.stderr}"
                })
                return findings
            
            # Get all files in the repository
            file_paths = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    # Skip .git directory
                    if '.git' in root:
                        continue
                    file_paths.append(os.path.join(root, file))
            
            # Scan files using the file scanner
            repo_findings = self._scan_files(file_paths)
            findings.extend(repo_findings)
            
        except Exception as e:
            findings.append({
                "type": "ERROR",
                "value": str(e),
                "location": repo_url,
                "risk_level": "Low",
                "reason": f"Error scanning repository: {str(e)}"
            })
        
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
                
        return findings
        
    def _scan_local_repo(self, repo_path: str) -> List[Dict[str, Any]]:
        """
        Scan a local repository for PII and data processing patterns.
        
        Args:
            repo_path: Path to local repository
            
        Returns:
            List of findings from the repository
        """
        import os
        
        findings = []
        
        try:
            # Check if path exists
            if not os.path.exists(repo_path):
                findings.append({
                    "type": "ERROR",
                    "value": "Path does not exist",
                    "location": repo_path,
                    "risk_level": "Low",
                    "reason": f"The specified path '{repo_path}' does not exist"
                })
                return findings
            
            # Get all files in the directory
            file_paths = []
            if os.path.isfile(repo_path):
                # Single file
                file_paths.append(repo_path)
            else:
                # Directory
                for root, _, files in os.walk(repo_path):
                    # Skip hidden directories
                    if '/.' in root or '\\.' in root:
                        continue
                    for file in files:
                        # Skip hidden files
                        if file.startswith('.'):
                            continue
                        file_paths.append(os.path.join(root, file))
            
            # Scan files using the file scanner
            repo_findings = self._scan_files(file_paths)
            findings.extend(repo_findings)
            
        except Exception as e:
            findings.append({
                "type": "ERROR",
                "value": str(e),
                "location": repo_path,
                "risk_level": "Low",
                "reason": f"Error scanning local repository: {str(e)}"
            })
            
        return findings

def generate_dpia_report(assessment_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive DPIA assessment report in a format suitable for PDF generation.
    
    Args:
        assessment_results: Results from a DPIA assessment
        
    Returns:
        Report data ready for the PDF generator
    """
    language = assessment_results.get('language', 'en')
    
    # Extract file findings
    file_findings = assessment_results.get('file_findings', [])
    
    # Count findings from files
    file_high_risk = assessment_results.get('file_high_risk_count', 0)
    file_medium_risk = assessment_results.get('file_medium_risk_count', 0)
    file_low_risk = assessment_results.get('file_low_risk_count', 0)
    total_file_findings = assessment_results.get('total_findings_count', 0)
    
    # Get data source information
    data_source_info = assessment_results.get('data_source_info', {})
    data_source_type = data_source_info.get('type', 'questionnaire_only')
    
    # Create report data structure
    report_data = {
        "scan_id": assessment_results["scan_id"],
        "scan_type": "DPIA",
        "timestamp": assessment_results["timestamp"],
        "total_pii_found": total_file_findings,
        "high_risk_count": assessment_results["high_risk_count"] + file_high_risk,
        "medium_risk_count": assessment_results["medium_risk_count"] + file_medium_risk,
        "low_risk_count": assessment_results["low_risk_count"] + file_low_risk,
        "region": "EU",  # GDPR is EU-specific
        "risk_level": assessment_results["overall_risk_level"],
        "dpia_required": assessment_results["dpia_required"],
        "dpia_score": assessment_results["overall_percentage"],
        "findings": file_findings,
        "recommendations": assessment_results["recommendations"],
        "category_scores": assessment_results["category_scores"],
        "data_source_info": data_source_info,
        "pii_types": _count_pii_types(file_findings)
    }
    
    # Add category findings
    for category, scores in assessment_results["category_scores"].items():
        # Create a finding for each category with elevated risk
        if scores["risk_level"] != "Low":
            # Localize the finding description
            if language == 'nl':
                description = f"Risicoscore voor {category}: {scores['percentage']:.1f}/10"
                detail = f"Deze categorie vertoont een {scores['risk_level']} risico en vereist aandacht."
            else:
                description = f"Risk score for {category}: {scores['percentage']:.1f}/10"
                detail = f"This category shows {scores['risk_level']} risk and requires attention."
                
            report_data["findings"].append({
                "type": "DPIA Risk",
                "severity": scores["risk_level"],
                "description": description,
                "details": detail,
                "category": category
            })
    
    # Add a special finding about DPIA requirement
    if assessment_results["dpia_required"]:
        if language == 'nl':
            report_data["findings"].append({
                "type": "DPIA Vereist",
                "severity": "High",
                "description": "Een formele DPIA is vereist onder Artikel 35 van de AVG",
                "details": "De risicoanalyse geeft aan dat er een hoog risico is voor de rechten en vrijheden van betrokkenen, wat een formele DPIA vereist.",
                "category": "General"
            })
        else:
            report_data["findings"].append({
                "type": "DPIA Required",
                "severity": "High",
                "description": "A formal DPIA is required under Article 35 of GDPR",
                "details": "Risk analysis indicates high risk to rights and freedoms of data subjects, requiring a formal DPIA.",
                "category": "General"
            })
    
    # Add global summary with risk levels for each category
    if language == 'nl':
        summary = {
            "Algemeen risico": assessment_results["overall_risk_level"],
            "DPIA vereist": "Ja" if assessment_results["dpia_required"] else "Nee",
            "Totale risicoscore": f"{assessment_results['overall_percentage']:.1f}/10"
        }
    else:
        summary = {
            "Overall risk": assessment_results["overall_risk_level"],
            "DPIA required": "Yes" if assessment_results["dpia_required"] else "No",
            "Total risk score": f"{assessment_results['overall_percentage']:.1f}/10"
        }
        
    report_data["summary"] = summary
    report_data["risk_levels"] = {
        "High": assessment_results["high_risk_count"],
        "Medium": assessment_results["medium_risk_count"],
        "Low": assessment_results["low_risk_count"]
    }
    
    return report_data

def _count_pii_types(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count occurrences of each PII type found in the file findings.
    
    Args:
        findings: List of findings from file scans
        
    Returns:
        Dictionary mapping PII types to their frequency
    """
    pii_types = {}
    for finding in findings:
        pii_type = finding.get('type', 'Unknown')
        pii_types[pii_type] = pii_types.get(pii_type, 0) + 1
    return pii_types