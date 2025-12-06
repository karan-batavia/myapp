"""
SOC2 & NIS2 Compliance Scanner for IaC Code

This module provides functionality to scan infrastructure-as-code (IaC) repositories
for SOC2 and NIS2 (EU Directive 2022/2555) compliance issues. It focuses on common 
security and compliance issues in Terraform, CloudFormation, Ansible, and other IaC tools.

NIS2 Directive: EU cybersecurity law requiring organizations in critical sectors to 
implement comprehensive cybersecurity measures including risk management, incident 
reporting, business continuity, and supply chain security.
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Tuple, Optional, Set
import tempfile
import glob
import shutil
import subprocess
from datetime import datetime
import traceback

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("soc2_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)

# SOC2 Compliance categories
SOC2_CATEGORIES = {
    "security": "Security",
    "availability": "Availability",
    "processing_integrity": "Processing Integrity",
    "confidentiality": "Confidentiality",
    "privacy": "Privacy"
}

# NIS2 Directive Compliance Categories (EU 2022/2555)
NIS2_CATEGORIES = {
    "risk_management": "Risk Management",
    "incident_handling": "Incident Handling",
    "business_continuity": "Business Continuity",
    "supply_chain": "Supply Chain Security",
    "network_security": "Network Security",
    "access_control": "Access Control & MFA",
    "cryptography": "Cryptography & Encryption",
    "asset_management": "Asset Management",
    "cybersecurity_training": "Cybersecurity Training",
    "vulnerability_management": "Vulnerability Management"
}

# NIS2 Article Mapping (EU Directive 2022/2555) - Complete Coverage
# 47 Articles across 11 Chapters - Focus on technically verifiable requirements
NIS2_ARTICLE_MAPPING = {
    # Chapter I - General Provisions
    "NIS2-1": "Subject matter: High common level of cybersecurity across the Union",
    "NIS2-2": "Scope: Essential and important entities in critical sectors",
    "NIS2-6": "Definitions: Key terms for NIS2 compliance",
    
    # Chapter II - Strategic Framework
    "NIS2-7": "National cybersecurity strategy requirements",
    "NIS2-8": "Cooperation at national level",
    
    # Chapter III - Governance Framework
    "NIS2-15": "Competent authorities designation",
    "NIS2-18": "CSIRT establishment requirements",
    "NIS2-19": "CSIRT tasks and capabilities",
    
    # Corporate Accountability (Article 20) - Management Governance
    "NIS2-20.1": "Management body approval of cybersecurity risk-management measures",
    "NIS2-20.2": "Management body oversight of implementation of measures",
    "NIS2-20.3": "Management accountability and liability for non-compliance",
    "NIS2-20.4": "Cybersecurity training requirements for management and staff",
    
    # Cybersecurity Risk-Management Measures (Article 21) - NEW NIS2 Article 22
    "NIS2-21.1": "Policies on risk analysis and information system security",
    "NIS2-21.2a": "Incident handling procedures and response capabilities",
    "NIS2-21.2b": "Business continuity (backup management, disaster recovery, crisis management)",
    "NIS2-21.2c": "Supply chain security including security aspects of supplier relationships",
    "NIS2-21.2d": "Security in network and information systems acquisition, development, maintenance",
    "NIS2-21.2e": "Policies and procedures to assess effectiveness of cybersecurity risk-management measures",
    "NIS2-21.2f": "Basic cyber hygiene practices and cybersecurity training",
    "NIS2-21.2g": "Policies and procedures for use of cryptography and encryption",
    "NIS2-21.2h": "Human resources security, access control policies, asset management",
    "NIS2-21.2i": "Use of multi-factor authentication (MFA), secured voice/video/text communications",
    "NIS2-21.2j": "Vulnerability handling and disclosure policies and procedures",
    
    # Article 22 - Coordinated vulnerability disclosure
    "NIS2-22.1": "Assessment of security of supply chain and direct suppliers",
    "NIS2-22.2": "Security requirements incorporated in contracts with suppliers",
    "NIS2-22.3": "Coordinated security risk assessments of critical supply chains",
    
    # Incident Reporting Obligations (Article 23)
    "NIS2-23.1": "24-hour early warning notification for significant incidents",
    "NIS2-23.2": "72-hour incident notification with initial assessment and severity",
    "NIS2-23.3": "Intermediate report upon request and final report within one month",
    "NIS2-23.4": "Notification to affected service recipients of significant incidents",
    "NIS2-23.5": "Cross-border incident notification to relevant Member States",
    
    # Article 25 - Responsible vulnerability disclosure
    "NIS2-25.1": "Coordinated vulnerability disclosure policy establishment",
    "NIS2-25.2": "CSIRT coordination for vulnerability disclosure",
    
    # Article 26 - European vulnerability database
    "NIS2-26.1": "Participation in European vulnerability database",
    "NIS2-26.2": "Vulnerability information sharing requirements",
    
    # Chapter V - Information Sharing (Article 27)
    "NIS2-27.1": "Cybersecurity information sharing arrangements",
    "NIS2-27.2": "Trusted information sharing communities",
    
    # Chapter VI - Jurisdiction (Article 28)
    "NIS2-28.1": "Jurisdiction rules for essential and important entities",
    "NIS2-28.2": "Main establishment determination",
    
    # Chapter VII - Domain Names (Articles 29-32)
    "NIS2-29": "WHOIS database requirements for domain registries",
    "NIS2-30": "Access to domain registration data",
    "NIS2-31": "Accuracy of domain name registration data",
    
    # Chapter VIII - Supervision and Enforcement
    "NIS2-33": "Ex ante supervision requirements for essential entities",
    "NIS2-34": "Ex post supervision requirements for important entities",
    "NIS2-35": "Identification of essential and important entities",
    "NIS2-37": "Registry of entities requirements",
    
    # Administrative Sanctions (Article 38)
    "NIS2-38.1": "Essential entities: Administrative fines up to €10,000,000 or 2% of total worldwide annual turnover",
    "NIS2-38.2": "Important entities: Administrative fines up to €7,000,000 or 1.4% of total worldwide annual turnover",
    "NIS2-38.3": "Periodic penalty payments for continued infringements",
    "NIS2-38.4": "Suspension of certification or authorization",
    "NIS2-38.5": "Temporary ban of management from exercising managerial functions",
    
    # Chapter XI - Final Provisions
    "NIS2-43": "Review of the directive by October 17, 2027",
    "NIS2-45": "Transposition deadline: October 17, 2024",
    "NIS2-46": "Entry into force: January 16, 2023",
    
    # Annexes - Sector Classification
    "NIS2-ANNEX-I": "Sectors of high criticality (Essential entities): Energy, Transport, Banking, Financial market, Health, Drinking water, Waste water, Digital infrastructure, ICT service management, Public administration, Space",
    "NIS2-ANNEX-II": "Other critical sectors (Important entities): Postal services, Waste management, Manufacture, Digital providers, Research"
}

# Map findings to NIS2 articles - Comprehensive mapping for IaC scanning
FINDING_TO_NIS2_MAP = {
    # Cryptography & Secrets Management (Article 21.2g)
    "Hard-coded AWS access keys": ["NIS2-21.2g", "NIS2-21.2h", "NIS2-38.1"],
    "Hard-coded AWS secret keys": ["NIS2-21.2g", "NIS2-21.2h", "NIS2-38.1"],
    "Hard-coded API keys": ["NIS2-21.2g", "NIS2-21.2h"],
    "Possible hard-coded secrets": ["NIS2-21.2g", "NIS2-21.2h"],
    "Possible hard-coded password": ["NIS2-21.2g", "NIS2-21.2h", "NIS2-20.3"],
    "Hard-coded credentials or secrets": ["NIS2-21.2g", "NIS2-21.2h", "NIS2-21.2i"],
    "Resource with encryption disabled": ["NIS2-21.2g", "NIS2-21.1"],
    "Crypto usage without proper configuration": ["NIS2-21.2g", "NIS2-21.2e"],
    
    # Network Security (Article 21.2d)
    "Security group with unrestricted ingress": ["NIS2-21.2d", "NIS2-21.1", "NIS2-38.1"],
    "Security group with unrestricted access": ["NIS2-21.2d", "NIS2-21.1"],
    "CORS allowing all origins": ["NIS2-21.2d", "NIS2-21.1"],
    "Serving static files without proper restrictions": ["NIS2-21.2d", "NIS2-21.2h"],
    
    # Access Control (Article 21.2h, 21.2i)
    "IAM policy with unrestricted access": ["NIS2-21.2h", "NIS2-21.1", "NIS2-20.2"],
    "Container running in privileged mode": ["NIS2-21.2d", "NIS2-21.2h"],
    "Pod using hostPath volume": ["NIS2-21.2d", "NIS2-21.2h"],
    "JWT token generation without expiration": ["NIS2-21.2h", "NIS2-21.2i"],
    "Unrestricted data access": ["NIS2-21.2h", "NIS2-21.1"],
    
    # Business Continuity (Article 21.2b)
    "Resource with backups disabled": ["NIS2-21.2b", "NIS2-21.1"],
    "EC2 instance without termination protection": ["NIS2-21.2b"],
    "S3 bucket without versioning": ["NIS2-21.2b", "NIS2-21.1"],
    "Resource without deletion protection": ["NIS2-21.2b"],
    "Database connection without proper error handling": ["NIS2-21.2a", "NIS2-21.2b"],
    
    # Incident Handling & Monitoring (Article 21.2a, 23)
    "Resource without logging configured": ["NIS2-21.2a", "NIS2-23.1", "NIS2-21.2e"],
    "Resource with monitoring disabled": ["NIS2-21.2e", "NIS2-21.2a", "NIS2-23.1"],
    
    # Vulnerability Management (Article 21.2j, 25)
    "Using 'latest' tag for base image": ["NIS2-21.2j", "NIS2-21.2d", "NIS2-25.1"],
    "AWS provider without version constraint": ["NIS2-21.2j", "NIS2-21.2d"],
    "Use of eval() function": ["NIS2-21.2d", "NIS2-21.2j"],
    "Use of document.write()": ["NIS2-21.2j", "NIS2-21.2d"],
    "Direct manipulation of innerHTML": ["NIS2-21.2j", "NIS2-21.2d"],
    "Use of exec function": ["NIS2-21.2j", "NIS2-21.2d"],
    "Use of child_process.exec": ["NIS2-21.2j", "NIS2-21.2d"],
    "MongoDB update without input validation": ["NIS2-21.2j", "NIS2-21.2d"],
    
    # Confidentiality (Article 21.2g, 21.2h)
    "S3 bucket with public read access": ["NIS2-21.2g", "NIS2-21.2h", "NIS2-38.1"],
    "Container with potential PII exposure": ["NIS2-21.2g", "NIS2-21.2h"],
    
    # Supply Chain Security (Article 22)
    "Hardcoded port in server configuration": ["NIS2-21.2d", "NIS2-22.2"]
}

# NIS2 Category to Article mapping for fallback
NIS2_CATEGORY_TO_ARTICLES = {
    "risk_management": ["NIS2-21.1", "NIS2-21.2e", "NIS2-20.1", "NIS2-20.2"],
    "incident_handling": ["NIS2-21.2a", "NIS2-23.1", "NIS2-23.2", "NIS2-23.3", "NIS2-23.4"],
    "business_continuity": ["NIS2-21.2b"],
    "supply_chain": ["NIS2-21.2c", "NIS2-22.1", "NIS2-22.2", "NIS2-22.3"],
    "network_security": ["NIS2-21.2d"],
    "access_control": ["NIS2-21.2h", "NIS2-21.2i"],
    "cryptography": ["NIS2-21.2g"],
    "asset_management": ["NIS2-21.2h"],
    "cybersecurity_training": ["NIS2-21.2f", "NIS2-20.4"],
    "vulnerability_management": ["NIS2-21.2j", "NIS2-25.1", "NIS2-26.1"]
}

# SOC2 Trust Services Criteria (TSC) mapping
# This maps the SOC2 criteria to their descriptions for reporting
SOC2_TSC_MAPPING = {
    # Common Criteria (Security)
    "CC1.1": "The entity demonstrates a commitment to integrity and ethical values.",
    "CC1.2": "The board of directors demonstrates independence from management and exercises oversight responsibility.",
    "CC1.3": "Management establishes structures, reporting lines, and authorities and responsibilities.",
    "CC1.4": "The entity demonstrates a commitment to attract, develop, and retain competent individuals.",
    "CC2.1": "The entity specifies objectives with sufficient clarity to enable risks to be identified.",
    "CC2.2": "The entity identifies and assesses risks to the achievement of its objectives.",
    "CC2.3": "The entity considers the potential for fraud in assessing risks.",
    "CC3.1": "The entity selects and develops control activities that mitigate risks.",
    "CC3.2": "The entity selects and develops general controls over technology.",
    "CC3.3": "The entity deploys control activities through policies and procedures.",
    "CC3.4": "The entity obtains or generates relevant, quality information to support the functioning of controls.",
    "CC4.1": "The entity communicates information internally to support the functioning of controls.",
    "CC4.2": "The entity communicates with external parties regarding matters affecting the functioning of controls.",
    "CC5.1": "The entity selects, develops, and performs ongoing evaluations to ascertain whether controls are functioning.",
    "CC5.2": "The entity evaluates and communicates control deficiencies in a timely manner.",
    "CC5.3": "The entity identifies, develops, and implements activities to mitigate risks.",
    "CC6.1": "The entity implements logical access security software, infrastructure, and architectures.",
    "CC6.2": "Prior to issuing system credentials and granting system access, the entity registers and authorizes new users.",
    "CC6.3": "The entity authorizes, modifies, or removes access to data, software, functions, and other IT resources.",
    "CC6.4": "The entity restricts physical access to facilities and protected information assets.",
    "CC6.5": "The entity discontinues logical and physical protections over physical assets only after the ability to read or recover data has been diminished.",
    "CC6.6": "The entity implements logical access security measures to protect against threats from sources outside its system boundaries.",
    "CC6.7": "The entity restricts the transmission, movement, and removal of information to authorized users and processes.",
    "CC6.8": "The entity implements controls to prevent or detect and act upon the introduction of unauthorized or malicious software.",
    "CC7.1": "The entity selects and develops security incident identification and response activities.",
    "CC7.2": "The entity monitors the information system and environments for potential security breaches and vulnerabilities.",
    "CC7.3": "The entity evaluates security events for significance and communicates breaches and other incidents.",
    "CC7.4": "The entity responds to identified security incidents by executing a defined incident response program.",
    "CC7.5": "The entity implements recovery plan procedures to restore systems operations in the event of incidents.",
    "CC8.1": "The entity authorizes, designs, develops or acquires, implements, operates, approves, maintains, and monitors environmental protections, software, data, infrastructure, and procedures to meet its objectives.",
    "CC9.1": "The entity identifies, selects, and develops risk mitigation activities for risks arising from business disruptions.",
    "CC9.2": "The entity assesses and manages risks associated with vendors and business partners.",
    
    # Availability
    "A1.1": "The entity maintains, monitors, and evaluates current processing capacity and use of system components.",
    "A1.2": "The entity authorizes, designs, develops, or acquires, implements, operates, approves, maintains, and monitors environmental protections.",
    "A1.3": "The entity authorizes, designs, develops or acquires, implements, operates, approves, maintains, and monitors recovery plans and recovery infrastructure.",
    
    # Processing Integrity
    "PI1.1": "The entity obtains or generates, uses, and communicates relevant, quality information regarding the objectives of processing.",
    "PI1.2": "The entity implements policies and procedures over system inputs to result in products, services, and reporting that meet the entity's objectives.",
    "PI1.3": "The entity implements policies and procedures over system processing to result in products and services that meet objectives.",
    "PI1.4": "The entity implements policies and procedures to make available or deliver outputs that meet entity objectives.",
    "PI1.5": "The entity implements policies and procedures to store inputs, items in processing, and outputs.",
    
    # Confidentiality
    "C1.1": "The entity identifies and maintains confidential information to meet the entity's objectives.",
    "C1.2": "The entity disposes of confidential information to meet the entity's objectives.",
    
    # Privacy
    "P1.1": "The entity provides notice of its privacy practices to data subjects.",
    "P2.1": "The entity communicates choices available regarding the collection, use, retention, disclosure, and disposal of personal information.",
    "P3.1": "Personal information is collected consistent with the entity's objectives.",
    "P3.2": "The entity collects personal information with the consent of the data subjects.",
    "P4.1": "The entity limits the use of personal information to the purposes identified in the entity's objectives.",
    "P5.1": "The entity grants data subjects the ability to access their personal information.",
    "P6.1": "The entity discloses personal information to third parties with the consent of data subjects.",
    "P7.1": "The entity secures personal information during collection, use, retention, disclosure, and disposal.",
    "P8.1": "The entity maintains accurate and complete personal information."
}

# SOC2 Compliance risk levels
RISK_LEVELS = ["high", "medium", "low"]

# Map from category to SOC2 TSC criteria
CATEGORY_TO_TSC_MAP = {
    "security": [
        "CC1.1", "CC1.2", "CC1.3", "CC1.4", "CC2.1", "CC2.2", "CC2.3", 
        "CC3.1", "CC3.2", "CC3.3", "CC3.4", "CC4.1", "CC4.2", "CC5.1", 
        "CC5.2", "CC5.3", "CC6.1", "CC6.2", "CC6.3", "CC6.4", "CC6.5", 
        "CC6.6", "CC6.7", "CC6.8", "CC7.1", "CC7.2", "CC7.3", "CC7.4", 
        "CC7.5", "CC8.1", "CC9.1", "CC9.2"
    ],
    "availability": ["A1.1", "A1.2", "A1.3"],
    "processing_integrity": ["PI1.1", "PI1.2", "PI1.3", "PI1.4", "PI1.5"],
    "confidentiality": ["C1.1", "C1.2"],
    "privacy": ["P1.1", "P2.1", "P3.1", "P3.2", "P4.1", "P5.1", "P6.1", "P7.1", "P8.1"]
}

# More specific mapping for common findings to specific TSC criteria
FINDING_TO_TSC_MAP = {
    # Security mappings for IaC
    "Hard-coded AWS access keys": ["CC6.1", "CC6.7"],
    "Possible hard-coded secrets": ["CC6.1", "CC6.7"],
    "Possible hard-coded password": ["CC6.1", "CC6.7"],
    "Security group with unrestricted ingress": ["CC6.6", "CC6.7"],
    "IAM policy with unrestricted access": ["CC6.1", "CC6.3"],
    "Container running in privileged mode": ["CC6.8", "CC7.2"],
    "Pod using hostPath volume": ["CC6.1", "CC6.8"],
    
    # Availability mappings for IaC
    "Resource with backups disabled": ["A1.2", "A1.3"],
    "EC2 instance without termination protection": ["A1.2"],
    "S3 bucket without versioning": ["A1.3"],
    "Resource with monitoring disabled": ["A1.1"],
    "Resource without deletion protection": ["A1.2"],
    
    # Processing Integrity mappings for IaC
    "Resource without logging configured": ["PI1.3", "PI1.4"],
    "Using 'latest' tag for base image": ["PI1.2", "PI1.3"],
    
    # Confidentiality mappings for IaC
    "S3 bucket with public read access": ["C1.1"],
    "Resource with encryption disabled": ["C1.1"],
    
    # Privacy mappings for IaC
    "Container with potential PII exposure": ["P7.1"],
    "Unrestricted data access": ["P4.1", "P7.1"],
    
    # JavaScript/Node.js Security mappings
    "Hard-coded credentials or secrets": ["CC6.1", "CC6.6", "CC6.7"],
    "Use of eval() function": ["CC5.1", "CC6.8", "CC7.2"],
    "Use of document.write()": ["CC6.6", "CC6.8"],
    "Direct manipulation of innerHTML": ["CC6.6", "CC6.8"],
    "Use of exec function": ["CC6.1", "CC6.8", "CC7.2"],
    "Use of child_process.exec": ["CC6.1", "CC6.8", "CC7.2"],
    "Serving static files without proper restrictions": ["CC6.6", "CC6.7"],
    "CORS allowing all origins": ["CC6.6", "CC6.7", "C1.1"],
    "Crypto usage without proper configuration": ["CC6.1", "CC8.1", "C1.1"],
    "JWT token generation without expiration": ["CC6.1", "CC6.6"],
    "MongoDB update without input validation": ["CC6.6", "PI1.2", "PI1.3"],
    
    # JavaScript/Node.js Availability mappings
    "Database connection without proper error handling": ["A1.1", "CC7.2", "CC7.5"],
    "Hardcoded port in server configuration": ["CC3.2", "A1.1"],
    
    # Azure-specific mappings
    "Azure Storage without HTTPS enforcement": ["CC6.6", "CC6.7", "C1.1"],
    "Azure Storage blob public access enabled": ["CC6.6", "C1.1"],
    "Azure Key Vault without purge protection": ["A1.2", "A1.3"],
    "Azure SQL using outdated TLS version": ["CC6.6", "CC6.7"],
    "Azure NSG with unrestricted access": ["CC6.6", "CC6.7"],
    "Azure NSG with unrestricted source access": ["CC6.6", "CC6.7"],
    "Azure NSG with unrestricted destination access": ["CC6.6", "CC6.7"],
    "Azure Storage without infrastructure encryption": ["C1.1", "CC6.1"],
    "Azure SQL Database without TDE": ["C1.1", "CC6.1"],
    "Azure VM disk deleted on termination": ["A1.2", "A1.3"],
    "Azure resource using outdated TLS version": ["CC6.6", "CC6.7"],
    "Azure resource without infrastructure encryption": ["C1.1", "CC6.1"],
    "Azure resource with public network access enabled": ["CC6.6", "CC6.7"],
    
    # GCP-specific mappings
    "GCP firewall with unrestricted access": ["CC6.6", "CC6.7"],
    "GCP bucket without uniform access control": ["CC6.1", "CC6.3"],
    "GCP bucket without public access prevention": ["CC6.6", "C1.1"],
    "GCP Cloud SQL without SSL requirement": ["CC6.6", "CC6.7", "C1.1"],
    "GCP instance without deletion protection": ["A1.2"],
    "GCP KMS key rotation configured": ["CC6.1"],
    "GKE cluster with legacy ABAC enabled": ["CC6.1", "CC6.3"],
    "GKE cluster with master authorized networks": ["CC6.6"],
    "GCP BigQuery dataset with public access": ["C1.1", "CC6.6"],
    "GCP project with owner role binding": ["CC6.1", "CC6.3"],
    "GCP IAM binding with owner role": ["CC6.1", "CC6.3"],
    "GCP bucket without explicit public access settings": ["CC6.6", "C1.1"]
}

# IaC file patterns to identify
IaC_FILE_PATTERNS = {
    "terraform": [r"\.tf$", r"\.tfvars$", r"terraform\..*\.json$", r"\.hcl$", r"terragrunt\.hcl$"],
    "cloudformation": [r"\.yaml$", r"\.yml$", r"\.json$"],
    "azure_arm": [r"azuredeploy\.json$", r"mainTemplate\.json$", r"\.arm\.json$", r"parameters\.json$"],
    "gcp_deployment": [r"\.jinja$", r"\.jinja2$", r"deployment\.yaml$", r"\.dm\.yaml$"],
    "ansible": [r"\.ya?ml$", r"playbook\..*\.ya?ml$", r"inventory\..*"],
    "kubernetes": [r"\.ya?ml$", r"kustomization\.ya?ml$"],
    "docker": [r"Dockerfile$", r"docker-compose\.ya?ml$"],
    "pulumi": [r"\.ts$", r"\.js$", r"\.py$", r"Pulumi\.yaml$"],
    "chef": [r"\.rb$", r"Berksfile$", r"metadata\.rb$"],
    "puppet": [r"\.pp$", r"Puppetfile$"],
    "javascript": [r"\.js$", r"\.jsx$", r"package\.json$", r"\.ts$", r"\.tsx$", r"package-lock\.json$"]
}

# Risk patterns for each IaC tool
# Format: {pattern: (description, severity, recommendation, category)}
TERRAFORM_RISK_PATTERNS = {
    r"provider\s+\"aws\"\s*{[^}]*(?!version\s*=)": (
        "AWS provider without version constraint",
        "medium",
        "Add version constraint to AWS provider block. For Terraform: 'version = \"~> 5.0\"'. For Terragrunt: add 'required_providers { aws = { source = \"hashicorp/aws\", version = \"~> 5.0\" } }' in generate block or terraform { } block",
        "security"
    ),
    r"(?:access_key|aws_access_key_id)\s*=\s*[\"'][A-Z0-9]{20}[\"']": (
        "Hard-coded AWS access keys",
        "high",
        "Use environment variables, instance profiles, or secret management tools instead of hard-coded credentials",
        "security"
    ),
    r"(?:secret|aws_secret_access_key)\s*=\s*[\"'][A-Za-z0-9/+]{40}[\"']": (
        "Hard-coded AWS secret keys",
        "high",
        "Store secrets in a dedicated secret management service",
        "security"
    ),
    r"(?:password|passwd|pwd)\s*=\s*[\"'][^\"']{3,}[\"']": (
        "Possible hard-coded password",
        "high", 
        "Use secrets manager instead of hard-coded passwords",
        "security"
    ),
    r"(?:api_key|apikey)\s*=\s*[\"'][A-Za-z0-9]{16,}[\"']": (
        "Hard-coded API keys",
        "high",
        "Store API keys in environment variables or secret management services",
        "security"
    ),
    r"ingress\s+{[^}]*0\.0\.0\.0/0": (
        "Security group with unrestricted ingress",
        "high",
        "Restrict ingress traffic to known IP ranges or specific sources",
        "security"
    ),
    r"acl\s*=\s*\"public-read\"": (
        "S3 bucket with public read access",
        "high",
        "Restrict S3 bucket access to only required principals",
        "confidentiality"
    ),
    r"encrypted\s*=\s*false": (
        "Resource with encryption disabled",
        "high",
        "Enable encryption for data protection",
        "confidentiality"
    ),
    r"logging[^}]*=\s*\{\s*\}": (
        "Resource without logging configured",
        "medium",
        "Enable logging for audit and compliance purposes",
        "processing_integrity"
    ),
    r"backup[^}]*=\s*false": (
        "Resource with backups disabled",
        "medium",
        "Enable backup for data protection and availability",
        "availability"
    ),
    r"disable_api_termination\s*=\s*false": (
        "EC2 instance without termination protection",
        "low",
        "Enable termination protection for critical resources",
        "availability"
    ),
    r"versioning[^}]*=\s*\{\s*enabled\s*=\s*false": (
        "S3 bucket without versioning",
        "medium", 
        "Enable versioning for data protection and recovery",
        "availability"
    ),
    r"monitoring\s*=\s*false": (
        "Resource with monitoring disabled",
        "medium",
        "Enable monitoring for effective operational oversight",
        "availability"
    ),
    # Azure Terraform patterns
    r"azurerm_storage_account[^}]*enable_https_traffic_only\s*=\s*false": (
        "Azure Storage without HTTPS enforcement",
        "high",
        "Enable HTTPS-only traffic for Azure Storage accounts",
        "security"
    ),
    r"azurerm_storage_account[^}]*allow_blob_public_access\s*=\s*true": (
        "Azure Storage blob public access enabled",
        "high",
        "Disable public blob access for Azure Storage accounts",
        "confidentiality"
    ),
    r"azurerm_key_vault[^}]*purge_protection_enabled\s*=\s*false": (
        "Azure Key Vault without purge protection",
        "high",
        "Enable purge protection for Azure Key Vault",
        "availability"
    ),
    r"azurerm_sql_server[^}]*minimum_tls_version\s*=\s*\"1\.[01]\"": (
        "Azure SQL using outdated TLS version",
        "high",
        "Use TLS 1.2 or higher for Azure SQL Server",
        "security"
    ),
    r"azurerm_network_security_rule[^}]*0\.0\.0\.0/0": (
        "Azure NSG with unrestricted access",
        "high",
        "Restrict network security group access to specific IP ranges",
        "security"
    ),
    r"azurerm_storage_account[^}]*infrastructure_encryption_enabled\s*=\s*false": (
        "Azure Storage without infrastructure encryption",
        "high",
        "Enable infrastructure encryption for Azure Storage",
        "confidentiality"
    ),
    r"azurerm_mssql_database[^}]*transparent_data_encryption_enabled\s*=\s*false": (
        "Azure SQL Database without TDE",
        "high",
        "Enable Transparent Data Encryption for Azure SQL Database",
        "confidentiality"
    ),
    r"azurerm_virtual_machine[^}]*delete_os_disk_on_termination\s*=\s*true": (
        "Azure VM disk deleted on termination",
        "medium",
        "Consider retaining OS disk for data recovery",
        "availability"
    ),
    # Google Cloud Platform (GCP) Terraform patterns
    r"google_compute_firewall[^}]*0\.0\.0\.0/0": (
        "GCP firewall with unrestricted access",
        "high",
        "Restrict GCP firewall rules to specific IP ranges",
        "security"
    ),
    r"google_storage_bucket[^}]*uniform_bucket_level_access\s*=\s*false": (
        "GCP bucket without uniform access control",
        "medium",
        "Enable uniform bucket-level access for GCP Storage",
        "security"
    ),
    r"google_storage_bucket[^}]*public_access_prevention\s*=\s*\"inherited\"": (
        "GCP bucket without public access prevention",
        "high",
        "Set public access prevention to enforced for GCP Storage",
        "confidentiality"
    ),
    r"google_sql_database_instance[^}]*require_ssl\s*=\s*false": (
        "GCP Cloud SQL without SSL requirement",
        "high",
        "Enable SSL for GCP Cloud SQL connections",
        "security"
    ),
    r"google_compute_instance[^}]*deletion_protection\s*=\s*false": (
        "GCP instance without deletion protection",
        "medium",
        "Enable deletion protection for critical GCP instances",
        "availability"
    ),
    r"google_kms_crypto_key[^}]*rotation_period": (
        "GCP KMS key rotation configured",
        "low",
        "Verify key rotation period meets compliance requirements",
        "security"
    ),
    r"google_container_cluster[^}]*enable_legacy_abac\s*=\s*true": (
        "GKE cluster with legacy ABAC enabled",
        "high",
        "Disable legacy ABAC in favor of RBAC for GKE",
        "security"
    ),
    r"google_container_cluster[^}]*master_authorized_networks_config": (
        "GKE cluster with master authorized networks",
        "low",
        "Good practice: Master authorized networks configured",
        "security"
    ),
    r"google_bigquery_dataset[^}]*access[^}]*\"allUsers\"": (
        "GCP BigQuery dataset with public access",
        "high",
        "Remove public access from BigQuery datasets",
        "confidentiality"
    ),
    r"google_project_iam_binding[^}]*\"roles/owner\"": (
        "GCP project with owner role binding",
        "high",
        "Use more granular IAM roles instead of owner",
        "security"
    ),
}

CLOUDFORMATION_RISK_PATTERNS = {
    r"Effect\"\s*:\s*\"Allow\"[^{]*\"\*\"": (
        "IAM policy with unrestricted access",
        "high",
        "Follow the principle of least privilege by limiting permissions",
        "security"
    ),
    r"\"CidrIp\"\s*:\s*\"0\.0\.0\.0/0\"": (
        "Security group with unrestricted access",
        "high",
        "Restrict access to specific IP ranges or security groups",
        "security"
    ),
    r"\"AccessControl\"\s*:\s*\"PublicRead\"": (
        "S3 bucket with public read access",
        "high",
        "Restrict S3 bucket access to only required principals",
        "confidentiality"
    ),
    r"\"DeletionPolicy\"\s*:\s*\"Delete\"": (
        "Resource without deletion protection",
        "medium",
        "Use 'Retain' for critical resources to prevent accidental deletion",
        "availability"
    ),
    r"\"Encrypted\"\s*:\s*false": (
        "Resource with encryption disabled",
        "high",
        "Enable encryption for data protection",
        "confidentiality"
    ),
}

# Azure ARM Template patterns
AZURE_ARM_RISK_PATTERNS = {
    r"\"properties\"[^}]*\"supportsHttpsTrafficOnly\":\s*false": (
        "Azure Storage without HTTPS enforcement",
        "high",
        "Enable HTTPS-only traffic for Azure Storage accounts",
        "security"
    ),
    r"\"properties\"[^}]*\"allowBlobPublicAccess\":\s*true": (
        "Azure Storage blob public access enabled",
        "high",
        "Disable public blob access for Azure Storage accounts",
        "confidentiality"
    ),
    r"\"properties\"[^}]*\"enablePurgeProtection\":\s*false": (
        "Azure Key Vault without purge protection",
        "high",
        "Enable purge protection for Azure Key Vault",
        "availability"
    ),
    r"\"properties\"[^}]*\"minimalTlsVersion\":\s*\"TLS1_[01]\"": (
        "Azure resource using outdated TLS version",
        "high",
        "Use TLS 1.2 or higher for Azure resources",
        "security"
    ),
    r"\"sourceAddressPrefix\":\s*\"\*\"": (
        "Azure NSG with unrestricted source access",
        "high",
        "Restrict network security group access to specific IP ranges",
        "security"
    ),
    r"\"destinationAddressPrefix\":\s*\"\*\"": (
        "Azure NSG with unrestricted destination access",
        "high",
        "Restrict network security group destination to specific ranges",
        "security"
    ),
    r"\"properties\"[^}]*\"transparentDataEncryption\"[^}]*\"status\":\s*\"Disabled\"": (
        "Azure SQL Database without TDE",
        "high",
        "Enable Transparent Data Encryption for Azure SQL Database",
        "confidentiality"
    ),
    r"\"properties\"[^}]*\"infrastructureEncryption\":\s*\"Disabled\"": (
        "Azure resource without infrastructure encryption",
        "high",
        "Enable infrastructure encryption for Azure resources",
        "confidentiality"
    ),
    r"\"publicNetworkAccess\":\s*\"Enabled\"": (
        "Azure resource with public network access enabled",
        "medium",
        "Consider disabling public network access and using private endpoints",
        "security"
    ),
}

# GCP Deployment Manager patterns
GCP_DEPLOYMENT_MANAGER_RISK_PATTERNS = {
    r"sourceRanges:\s*-\s*0\.0\.0\.0/0": (
        "GCP firewall with unrestricted access",
        "high",
        "Restrict GCP firewall rules to specific IP ranges",
        "security"
    ),
    r"\"uniformBucketLevelAccess\"[^}]*\"enabled\":\s*false": (
        "GCP bucket without uniform access control",
        "medium",
        "Enable uniform bucket-level access for GCP Storage",
        "security"
    ),
    r"\"publicAccessPrevention\":\s*\"inherited\"": (
        "GCP bucket without public access prevention",
        "high",
        "Set public access prevention to enforced for GCP Storage",
        "confidentiality"
    ),
    r"\"requireSsl\":\s*false": (
        "GCP Cloud SQL without SSL requirement",
        "high",
        "Enable SSL for GCP Cloud SQL connections",
        "security"
    ),
    r"\"deletionProtection\":\s*false": (
        "GCP instance without deletion protection",
        "medium",
        "Enable deletion protection for critical GCP instances",
        "availability"
    ),
    r"\"legacyAbac\"[^}]*\"enabled\":\s*true": (
        "GKE cluster with legacy ABAC enabled",
        "high",
        "Disable legacy ABAC in favor of RBAC for GKE",
        "security"
    ),
    r"\"bindings\"[^}]*\"role\":\s*\"roles/owner\"": (
        "GCP IAM binding with owner role",
        "high",
        "Use more granular IAM roles instead of owner",
        "security"
    ),
    r"\"iamConfiguration\"[^}]*\"publicAccessPrevention\":\s*\"unspecified\"": (
        "GCP bucket without explicit public access settings",
        "medium",
        "Explicitly configure public access prevention",
        "security"
    ),
}

KUBERNETES_RISK_PATTERNS = {
    r"privileged:\s*true": (
        "Container running in privileged mode",
        "high",
        "Avoid running containers in privileged mode",
        "security"
    ),
    r"hostPath:": (
        "Pod using hostPath volume",
        "high",
        "Avoid using hostPath as it allows access to host filesystem",
        "security"
    ),
    r"readOnlyRootFilesystem:\s*false": (
        "Container without read-only root filesystem",
        "medium",
        "Enable readOnlyRootFilesystem for better security",
        "security"
    ),
    r"runAsNonRoot:\s*false": (
        "Container not running as non-root user",
        "medium",
        "Run containers as non-root users",
        "security"
    ),
    r"allowPrivilegeEscalation:\s*true": (
        "Container allowed to escalate privileges",
        "high",
        "Disable privilege escalation for containers",
        "security"
    ),
    r"namespace:\s*default": (
        "Resources in default namespace",
        "low",
        "Use dedicated namespaces for better isolation",
        "security"
    ),
}

DOCKER_RISK_PATTERNS = {
    r"FROM\s+.*latest": (
        "Using 'latest' tag for base image",
        "medium",
        "Use specific version tags for base images",
        "processing_integrity"
    ),
    r"ADD\s+http": (
        "Using ADD with HTTP source",
        "medium",
        "Use COPY instead of ADD and download files in a separate step",
        "security"
    ),
    r"ENV\s+AWS_SECRET": (
        "AWS secrets in environment variables",
        "high",
        "Don't store secrets in Docker environment variables",
        "security"
    ),
    r"USER\s+root": (
        "Running container as root",
        "high",
        "Create and use non-root users in containers",
        "security"
    ),
    r"RUN\s+.*curl.*(sh|bash)": (
        "Executing scripts directly from URLs",
        "high",
        "Download scripts first and verify before executing",
        "security"
    ),
}

# JavaScript/Node.js risk patterns
JAVASCRIPT_RISK_PATTERNS = {
    r"(password|secret|key|token|auth).*=.*['\"][^'\"]+['\"]": (
        "Hard-coded credentials or secrets",
        "high",
        "Store sensitive information in environment variables or a secure vault",
        "security"
    ),
    r"eval\s*\(": (
        "Use of eval() function",
        "high",
        "Avoid using eval() as it can lead to code injection vulnerabilities",
        "security"
    ),
    r"document\.write\s*\(": (
        "Use of document.write()",
        "medium",
        "Avoid document.write() to prevent XSS vulnerabilities",
        "security"
    ),
    r"\.innerHTML\s*=": (
        "Direct manipulation of innerHTML",
        "medium",
        "Use safer alternatives like textContent or DOM methods to prevent XSS",
        "security"
    ),
    r"exec\s*\(": (
        "Use of exec function",
        "high",
        "Avoid using exec() as it can lead to command injection vulnerabilities",
        "security"
    ),
    r"child_process\.exec\s*\(": (
        "Use of child_process.exec",
        "high",
        "Use child_process.execFile or spawn with proper input validation",
        "security"
    ),
    r"express\.static\s*\(.*\)": (
        "Serving static files without proper restrictions",
        "medium",
        "Use middleware to set appropriate security headers",
        "security"
    ),
    r"(?:mongoose|sequelize|knex)\.connect.*\(": (
        "Database connection without proper error handling",
        "medium",
        "Implement proper error handling for database connections",
        "availability"
    ),
    r"app\.listen\s*\(\s*\d+": (
        "Hardcoded port in server configuration",
        "low",
        "Use environment variables for port configuration",
        "processing_integrity"
    ),
    r"\.createServer\s*\(\s*\)\s*\.listen\s*\(\s*\d+": (
        "Hardcoded port in server configuration",
        "low",
        "Use environment variables for port configuration",
        "processing_integrity"
    ),
    r"cors\s*\(\s*\{\s*origin\s*:\s*[\'\"]?\*[\'\"]?": (
        "CORS allowing all origins",
        "high",
        "Restrict CORS to specific trusted origins",
        "confidentiality"
    ),
    r"require\s*\(\s*['\"]crypto['\"]": (
        "Crypto usage without proper configuration",
        "medium",
        "Ensure proper cryptographic configurations and use modern algorithms",
        "confidentiality"
    ),
    r"JWT\.sign\s*\(": (
        "JWT token generation without expiration",
        "medium",
        "Set appropriate expiration for JWT tokens",
        "security"
    ),
    r"\.update\s*\(\s*\{\s*\$set": (
        "MongoDB update without input validation",
        "high",
        "Validate user input before database operations",
        "security"
    )
}

# Combine all patterns for use in scanning
IaC_RISK_PATTERNS = {
    "terraform": TERRAFORM_RISK_PATTERNS,
    "cloudformation": CLOUDFORMATION_RISK_PATTERNS,
    "azure_arm": AZURE_ARM_RISK_PATTERNS,
    "gcp_deployment": GCP_DEPLOYMENT_MANAGER_RISK_PATTERNS,
    "kubernetes": KUBERNETES_RISK_PATTERNS,
    "docker": DOCKER_RISK_PATTERNS,
    "javascript": JAVASCRIPT_RISK_PATTERNS,
}

def identify_iac_technology(file_path: str) -> Optional[str]:
    """
    Identify the IaC technology used in the given file.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        String identifying the IaC technology or None if not identified
    """
    if not os.path.isfile(file_path):
        return None
        
    file_name = os.path.basename(file_path)
    file_content = None
    
    # First try to identify by filename pattern
    for tech, patterns in IaC_FILE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, file_name, re.IGNORECASE):
                # For ambiguous patterns (like .yaml, .json), check content
                if tech in ["cloudformation", "kubernetes", "ansible"] and file_name.endswith((".yaml", ".yml", ".json")):
                    # Load content if not already loaded
                    if file_content is None:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                        except:
                            return None
                    
                    # Check for Azure ARM template first (takes precedence over CloudFormation for JSON)
                    if file_name.endswith(".json"):
                        if "$schema" in file_content and ("deploymentTemplate.json" in file_content or "Microsoft." in file_content):
                            return "azure_arm"
                        if "contentVersion" in file_content and "Microsoft." in file_content:
                            return "azure_arm"
                    
                    # Additional checks for specific technologies
                    if tech == "cloudformation" and ("AWSTemplateFormatVersion" in file_content or ("Resources" in file_content and "AWS::" in file_content)):
                        return "cloudformation"
                    elif tech == "kubernetes" and ("apiVersion" in file_content and "kind" in file_content):
                        return "kubernetes"
                    elif tech == "ansible" and ("hosts:" in file_content or "tasks:" in file_content):
                        return "ansible"
                else:
                    return tech
    
    # If not identified by name, try content-based identification
    if file_content is None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except:
            return None
            
    # Content-based checks
    if "resource" in file_content and "provider" in file_content:
        # Check if it's Terraform with Azure or GCP provider
        if "azurerm" in file_content or "provider \"azure" in file_content.lower():
            return "terraform"  # Azure Terraform
        elif "google" in file_content or "provider \"google" in file_content.lower():
            return "terraform"  # GCP Terraform
        return "terraform"
    # Azure ARM Template detection (check BEFORE CloudFormation for JSON files)
    elif "$schema" in file_content and ("deploymentTemplate.json" in file_content or "Microsoft." in file_content):
        return "azure_arm"
    elif "contentVersion" in file_content and ("Microsoft." in file_content or ("resources" in file_content and "type" in file_content.lower())):
        return "azure_arm"
    elif "AWSTemplateFormatVersion" in file_content or ("Resources" in file_content and "Type" in file_content and "AWS::" in file_content):
        return "cloudformation"
    # GCP Deployment Manager detection
    elif "type:" in file_content and ("compute.v1.instance" in file_content or "storage.v1.bucket" in file_content):
        return "gcp_deployment"
    elif "imports:" in file_content and (".jinja" in file_content or ".py" in file_content) and "resources:" in file_content:
        return "gcp_deployment"
    elif "apiVersion" in file_content and "kind" in file_content:
        return "kubernetes"
    elif "FROM" in file_content and ("RUN" in file_content or "CMD" in file_content):
        return "docker"
    # Check for JavaScript files
    elif (file_path.endswith('.js') or file_path.endswith('.jsx') or 
          file_path.endswith('.ts') or file_path.endswith('.tsx') or
          file_path.endswith('package.json')):
        return "javascript"
    elif any(js_indicator in file_content for js_indicator in [
        "function", "const", "let", "var", "import", "export", "require(", 
        "module.exports", "addEventListener", "document.", "window."
    ]):
        return "javascript"
            
    return None

def scan_iac_file(file_path: str, tech: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scan an IaC file for compliance issues.
    
    Args:
        file_path: Path to the file to scan
        tech: Optional technology identifier. If None, it will be detected
        
    Returns:
        List of findings, each a dictionary with issue details
    """
    findings = []
    
    # Identify technology if not provided
    if tech is None:
        tech = identify_iac_technology(file_path)
        
    if tech is None or tech not in IaC_RISK_PATTERNS:
        return findings
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Get risk patterns for this technology
        risk_patterns = IaC_RISK_PATTERNS[tech]
        
        # Check each pattern
        for pattern, (description, severity, recommendation, category) in risk_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                context_start = max(0, content.rfind('\n', 0, match.start()) + 1)
                context_end = content.find('\n', match.end())
                if context_end == -1:
                    context_end = len(content)
                    
                code_snippet = content[context_start:context_end].strip()
                
                # Get SOC2 TSC criteria mapping for this finding
                tsc_criteria = []
                
                # Check if we have a specific mapping for this description
                if description in FINDING_TO_TSC_MAP:
                    tsc_criteria = FINDING_TO_TSC_MAP[description]
                else:
                    # Fall back to category-based mapping
                    tsc_criteria = CATEGORY_TO_TSC_MAP.get(category, [])
                
                # Create tsc_details with criterion and description pairs
                tsc_details = []
                for criterion in tsc_criteria:
                    criterion_description = SOC2_TSC_MAPPING.get(criterion, "")
                    tsc_details.append({
                        "criterion": criterion,
                        "description": criterion_description
                    })
                
                # Get NIS2 article mapping for this finding
                nis2_articles = []
                if description in FINDING_TO_NIS2_MAP:
                    nis2_articles = FINDING_TO_NIS2_MAP[description]
                
                # Create nis2_details with article and description pairs
                nis2_details = []
                for article in nis2_articles:
                    article_description = NIS2_ARTICLE_MAPPING.get(article, "")
                    nis2_details.append({
                        "article": article,
                        "description": article_description
                    })
                
                finding = {
                    "file": file_path,
                    "line": line_num,
                    "description": description,
                    "risk_level": severity,
                    "recommendation": recommendation,
                    "category": category,
                    "location": f"{os.path.basename(file_path)}:{line_num}",
                    "code_snippet": code_snippet,
                    "technology": tech,
                    "soc2_tsc_criteria": tsc_criteria,
                    "soc2_tsc_details": tsc_details,
                    "nis2_articles": nis2_articles,
                    "nis2_details": nis2_details
                }
                
                findings.append(finding)
    except Exception as e:
        logger.error(f"Error scanning file {file_path}: {str(e)}")
        traceback.print_exc()
        
    return findings

def scan_github_repo_for_soc2(repo_url: str, branch: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Scan a GitHub repository for SOC2 compliance issues in IaC code.
    
    Args:
        repo_url: GitHub repository URL
        branch: Optional branch name
        token: Optional GitHub access token for private repos
        
    Returns:
        Dictionary with scan results
    """
    # Initialize results
    results = {
        "scan_type": "soc2",
        "timestamp": datetime.now().isoformat(),
        "repo_url": repo_url,
        "branch": branch or "main",
        "findings": [],
        "summary": {
            "security": {"high": 0, "medium": 0, "low": 0},
            "availability": {"high": 0, "medium": 0, "low": 0},
            "processing_integrity": {"high": 0, "medium": 0, "low": 0},
            "confidentiality": {"high": 0, "medium": 0, "low": 0},
            "privacy": {"high": 0, "medium": 0, "low": 0}
        },
        "scan_status": "failed",
        "technologies_detected": [],
        "total_files_scanned": 0,
        "iac_files_found": 0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
    }
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    clone_successful = False
    
    try:
        # Prepare clone command
        if token:
            # Use token for authentication
            auth_repo_url = repo_url.replace("https://", f"https://{token}@")
        else:
            auth_repo_url = repo_url
            
        # Clone repository with fallback for different default branches
        logger.info(f"Cloning repository {repo_url}...")
        
        # Try cloning with specified branch or main first
        target_branch = branch or "main"
        process = subprocess.run(
            ["git", "clone", "--depth", "1", "-b", target_branch, auth_repo_url, temp_dir],
            capture_output=True,
            text=True
        )
        
        # If main branch fails, try master branch
        if process.returncode != 0 and target_branch == "main":
            logger.info("Main branch not found, trying master branch...")
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir = tempfile.mkdtemp()
            
            process = subprocess.run(
                ["git", "clone", "--depth", "1", "-b", "master", auth_repo_url, temp_dir],
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                results["branch"] = "master"
        
        # If still failed, try cloning without specifying branch
        if process.returncode != 0:
            logger.info("Specified branch not found, trying default branch...")
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir = tempfile.mkdtemp()
            
            process = subprocess.run(
                ["git", "clone", "--depth", "1", auth_repo_url, temp_dir],
                capture_output=True,
                text=True
            )
        
        if process.returncode != 0:
            error_msg = process.stderr.strip()
            logger.error(f"Failed to clone repo: {error_msg}")
            results["error"] = f"Failed to clone repository: {error_msg}"
            return results
            
        clone_successful = True
        
        # Scan all files in the repository
        logger.info("Scanning repository files...")
        
        # Find all files recursively
        all_files = []
        for root, dirs, files in os.walk(temp_dir):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
                
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        results["total_files_scanned"] = len(all_files)
        
        # Scan each file
        for file_path in all_files:
            tech = identify_iac_technology(file_path)
            if tech:
                results["iac_files_found"] += 1
                if tech not in results["technologies_detected"]:
                    results["technologies_detected"].append(tech)
                
                file_findings = scan_iac_file(file_path, tech)
                
                # Make file paths relative to repo
                for finding in file_findings:
                    finding["file"] = os.path.relpath(finding["file"], temp_dir)
                    
                    # Update summary counts
                    category = finding["category"]
                    risk_level = finding["risk_level"]
                    
                    if category in results["summary"]:
                        if risk_level in results["summary"][category]:
                            results["summary"][category][risk_level] += 1
                            
                    # Update risk counts
                    if risk_level == "high":
                        results["high_risk_count"] += 1
                    elif risk_level == "medium":
                        results["medium_risk_count"] += 1
                    elif risk_level == "low":
                        results["low_risk_count"] += 1
                
                # Add findings
                results["findings"].extend(file_findings)
        
        # Convert technologies_detected from set to list for JSON serialization
        results["technologies_detected"] = list(results["technologies_detected"])
        
        # Calculate compliance score based on findings
        total_findings = len(results["findings"])
        high_risk = results["high_risk_count"]
        medium_risk = results["medium_risk_count"]
        low_risk = results["low_risk_count"]
        
        # Realistic compliance scoring that provides actionable insights
        base_score = 100
        if total_findings > 0:
            # More balanced scoring approach
            # Scale impact based on finding density relative to codebase size
            total_files = results.get("total_files_scanned", 1)
            finding_density = total_findings / max(total_files, 1) * 100
            
            # Base deductions per finding type
            high_risk_deduction = min(3, finding_density * 0.1)  # 1-3 points per high risk
            medium_risk_deduction = min(1.5, finding_density * 0.05)  # 0.5-1.5 points per medium risk
            low_risk_deduction = min(0.5, finding_density * 0.02)  # 0.1-0.5 points per low risk
            
            total_deduction = (high_risk * high_risk_deduction + 
                             medium_risk * medium_risk_deduction + 
                             low_risk * low_risk_deduction)
            
            # Cap maximum deduction to ensure reasonable scores
            max_deduction = 70  # Never go below 30/100
            total_deduction = min(total_deduction, max_deduction)
            
            compliance_score = base_score - total_deduction
            
            # Ensure minimum score for repositories with findings
            compliance_score = max(15, compliance_score)
        else:
            compliance_score = base_score
            
        results["compliance_score"] = round(compliance_score, 1)
        
        # Add recommendations based on actual findings
        results["recommendations"] = generate_recommendations(results)
        
        # Generate SOC2 TSC checklist based on actual findings
        results["soc2_tsc_checklist"] = generate_soc2_tsc_checklist(results)
        
        # Update scan status
        results["scan_status"] = "completed"
        
    except Exception as e:
        logger.error(f"Error scanning repository: {str(e)}")
        traceback.print_exc()
        results["error"] = f"Error scanning repository: {str(e)}"
    finally:
        # Clean up temp directory
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                logger.warning(f"Failed to clean up temp directory: {temp_dir}")
    
    return results

def scan_azure_repo_for_soc2(repo_url: str, project: str, branch: Optional[str] = None, 
                          token: Optional[str] = None, organization: Optional[str] = None) -> Dict[str, Any]:
    """
    Scan an Azure DevOps repository for SOC2 compliance issues in IaC code.
    
    Args:
        repo_url: Azure DevOps repository URL
        project: Azure DevOps project name
        branch: Optional branch name
        token: Optional Azure personal access token
        organization: Optional Azure DevOps organization name (can be extracted from URL)
        
    Returns:
        Dictionary with scan results
    """
    # Initialize results with same structure as GitHub scan
    results = {
        "scan_type": "soc2",
        "timestamp": datetime.now().isoformat(),
        "repo_url": repo_url,
        "project": project,
        "branch": branch or "main",
        "findings": [],
        "summary": {
            "security": {"high": 0, "medium": 0, "low": 0},
            "availability": {"high": 0, "medium": 0, "low": 0},
            "processing_integrity": {"high": 0, "medium": 0, "low": 0},
            "confidentiality": {"high": 0, "medium": 0, "low": 0},
            "privacy": {"high": 0, "medium": 0, "low": 0}
        },
        "scan_status": "failed",
        "technologies_detected": [],
        "total_files_scanned": 0,
        "iac_files_found": 0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
    }
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    clone_successful = False
    
    try:
        # Extract organization from URL if not provided
        if not organization and "dev.azure.com" in repo_url:
            # Format: https://dev.azure.com/{organization}/{project}/_git/{repository}
            url_parts = repo_url.split('/')
            org_index = url_parts.index("dev.azure.com") + 1
            if org_index < len(url_parts):
                organization = url_parts[org_index]
        
        # Build the clone URL with authentication if token is provided
        if token:
            # Format: https://{token}@dev.azure.com/{organization}/{project}/_git/{repository}
            clone_url = repo_url.replace("https://", f"https://{token}@")
        else:
            clone_url = repo_url
        
        # Clone repository
        logger.info(f"Cloning Azure repository: {repo_url} (branch: {branch})")
        
        # Prepare git command
        git_cmd = ["git", "clone", clone_url, temp_dir]
        if branch:
            git_cmd.extend(["--branch", branch])
        git_cmd.extend(["--single-branch", "--depth", "1"])
        
        # Execute clone
        subprocess.run(git_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        clone_successful = True
        
        # Once cloned, process it the same way as GitHub repositories
        # Count total files
        total_files = 0
        for root, dirs, files in os.walk(temp_dir):
            if '.git' in dirs:
                dirs.remove('.git')  # Skip .git directory
            total_files += len(files)
        
        results["total_files_scanned"] = total_files
        
        # Find IaC files
        iac_files = []
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, temp_dir)
                
                # Skip .git directory
                if '.git' in rel_path.split(os.sep):
                    continue
                
                # Check if it's an IaC file
                for tech, patterns in IaC_FILE_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, file):
                            iac_files.append((file_path, tech, rel_path))
                            if tech not in results["technologies_detected"]:
                                results["technologies_detected"].append(tech)
                            break
        
        results["iac_files_found"] = len(iac_files)
        
        # If we found IaC files, scan them
        if iac_files:
            # Process each file
            for file_path, tech, rel_path in iac_files:
                # Scan file
                file_findings = scan_iac_file(file_path, tech)
                
                # Add file path to each finding
                for finding in file_findings:
                    finding["file"] = rel_path
                    
                    # Update risk counts and categories
                    risk_level = finding["risk_level"]
                    category = finding["category"]
                    
                    if risk_level in ["high", "medium", "low"]:
                        results["summary"][category][risk_level] += 1
                        
                        if risk_level == "high":
                            results["high_risk_count"] += 1
                        elif risk_level == "medium":
                            results["medium_risk_count"] += 1
                        elif risk_level == "low":
                            results["low_risk_count"] += 1
                
                results["findings"].extend(file_findings)
            
            # Calculate compliance score based on findings
            if results["high_risk_count"] > 0 or results["medium_risk_count"] > 0 or results["low_risk_count"] > 0:
                total_issues = results["high_risk_count"] * 3 + results["medium_risk_count"] * 2 + results["low_risk_count"]
                max_score = 100
                penalty_per_point = min(3, max(1, total_issues / 10))  # Dynamic penalty based on total issues
                compliance_score = max(0, max_score - int(total_issues * penalty_per_point))
                results["compliance_score"] = compliance_score
            else:
                results["compliance_score"] = 100  # Perfect score if no issues
                
            # Generate recommendations
            results["recommendations"] = generate_recommendations(results)
            
            # Mark scan as successful
            results["scan_status"] = "success"
        else:
            # No IaC files found
            results["scan_status"] = "success"
            results["compliance_score"] = 100  # Perfect score if no issues
            results["warning"] = "No Infrastructure-as-Code files found in the repository."
    
    except Exception as e:
        logger.error(f"Error scanning Azure repository: {str(e)}")
        traceback.print_exc()
        results["error"] = f"Error scanning Azure repository: {str(e)}"
    finally:
        # Clean up temp directory
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                logger.warning(f"Failed to clean up temp directory: {temp_dir}")
    
    return results

def generate_recommendations(scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate recommendations based on scan results.
    
    Args:
        scan_results: Scan results dictionary
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    # Extract unique recommendations to avoid duplication
    unique_recs = {}
    for finding in scan_results.get("findings", []):
        # Skip invalid findings that are not dictionaries
        if not isinstance(finding, dict):
            logger.warning(f"Skipping invalid finding in recommendations: {type(finding)} - {finding}")
            continue
            
        recommendation = finding.get("recommendation", "No recommendation")
        category = finding.get("category", "unknown")
        risk_level = finding.get("risk_level", "medium")
        
        rec_key = (recommendation, category, risk_level)
        if rec_key not in unique_recs:
            unique_recs[rec_key] = {
                "description": f"SOC2 {category.capitalize()} - {recommendation}",
                "severity": risk_level,
                "impact": "High" if risk_level == "high" else "Medium" if risk_level == "medium" else "Low",
                "category": category,
                "steps": [],
                "affected_files": [],
                "soc2_tsc_criteria": finding.get("soc2_tsc_criteria", []),
                "soc2_tsc_details": finding.get("soc2_tsc_details", [])
            }
        else:
            # Merge TSC criteria if not already present
            existing_criteria = unique_recs[rec_key].get("soc2_tsc_criteria", [])
            for criterion in finding.get("soc2_tsc_criteria", []):
                if criterion not in existing_criteria:
                    unique_recs[rec_key]["soc2_tsc_criteria"].append(criterion)
                    
                    # Also add the criterion details
                    for detail in finding.get("soc2_tsc_details", []):
                        if detail["criterion"] == criterion:
                            unique_recs[rec_key]["soc2_tsc_details"].append(detail)
        
        # Add file to affected files if not already there
        file_info = f"{finding.get('file', 'Unknown')}:{finding.get('line', 'N/A')}"
        if file_info not in unique_recs[rec_key]["affected_files"]:
            unique_recs[rec_key]["affected_files"].append(file_info)
    
    # Create recommendations list
    for rec_data in unique_recs.values():
        # Create steps based on category and severity
        if rec_data["category"] == "security":
            if rec_data["severity"] == "high":
                rec_data["steps"] = [
                    "Review and remove hard-coded credentials and secrets",
                    "Implement proper secret management",
                    "Update security configurations to follow least privilege principle",
                    f"Focus on files: {', '.join(rec_data['affected_files'][:3])}" + ("..." if len(rec_data["affected_files"]) > 3 else "")
                ]
            else:
                rec_data["steps"] = [
                    "Update security configurations to follow best practices",
                    "Implement proper access controls",
                    f"Focus on files: {', '.join(rec_data['affected_files'][:3])}" + ("..." if len(rec_data["affected_files"]) > 3 else "")
                ]
        elif rec_data["category"] == "availability":
            rec_data["steps"] = [
                "Enable backup and disaster recovery features",
                "Implement proper redundancy and failover mechanisms",
                f"Focus on files: {', '.join(rec_data['affected_files'][:3])}" + ("..." if len(rec_data["affected_files"]) > 3 else "")
            ]
        elif rec_data["category"] == "confidentiality":
            rec_data["steps"] = [
                "Enable encryption for data at rest and in transit",
                "Review and update access controls",
                f"Focus on files: {', '.join(rec_data['affected_files'][:3])}" + ("..." if len(rec_data["affected_files"]) > 3 else "")
            ]
        elif rec_data["category"] == "processing_integrity":
            rec_data["steps"] = [
                "Implement proper logging and monitoring",
                "Enable version control for infrastructure changes",
                f"Focus on files: {', '.join(rec_data['affected_files'][:3])}" + ("..." if len(rec_data["affected_files"]) > 3 else "")
            ]
        elif rec_data["category"] == "privacy":
            rec_data["steps"] = [
                "Review data collection and storage practices",
                "Implement data minimization principles",
                f"Focus on files: {', '.join(rec_data['affected_files'][:3])}" + ("..." if len(rec_data["affected_files"]) > 3 else "")
            ]
        
        # Add SOC2 TSC reference to steps if available
        if rec_data["soc2_tsc_criteria"]:
            criteria_str = ", ".join(rec_data["soc2_tsc_criteria"])
            rec_data["steps"].append(f"SOC2 TSC Criteria: {criteria_str}")
        
        # Remove affected_files before adding to recommendations
        affected_files = rec_data.pop("affected_files")
        recommendations.append(rec_data)
    
    # Sort recommendations by severity (high -> medium -> low)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: severity_order.get(x["severity"], 3))
    
    # Add a SOC2 TSC compliance checklist to the scan results
    scan_results["soc2_tsc_checklist"] = generate_soc2_tsc_checklist(scan_results)
    
    return recommendations

def generate_soc2_tsc_checklist(scan_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a SOC2 TSC checklist based on the scan results.
    
    Args:
        scan_results: Scan results dictionary
        
    Returns:
        Dictionary with SOC2 TSC checklist
    """
    # Initialize checklist with all criteria as "not_assessed"
    checklist = {}
    for criterion, description in SOC2_TSC_MAPPING.items():
        checklist[criterion] = {
            "criterion": criterion,
            "description": description,
            "status": "not_assessed",
            "violations": [],
            "category": get_criterion_category(criterion)
        }
    
    # Update status based on findings
    for finding in scan_results.get("findings", []):
        # Skip invalid findings that are not dictionaries
        if not isinstance(finding, dict):
            logger.warning(f"Skipping invalid finding: {type(finding)} - {finding}")
            continue
            
        for criterion in finding.get("soc2_tsc_criteria", []):
            if criterion in checklist:
                # If any high risk finding, mark as "failed"
                if finding.get("risk_level") == "high":
                    checklist[criterion]["status"] = "failed"
                # If medium risk and not already failed, mark as "warning"
                elif finding.get("risk_level") == "medium" and checklist[criterion]["status"] != "failed":
                    checklist[criterion]["status"] = "warning"
                # If low risk and not already failed or warning, mark as "info"
                elif finding.get("risk_level") == "low" and checklist[criterion]["status"] not in ["failed", "warning"]:
                    checklist[criterion]["status"] = "info"
                
                # Add violation
                violation = {
                    "description": finding.get("description", "No description"),
                    "file": finding.get("file", "Unknown"),
                    "line": finding.get("line", "N/A"),
                    "risk_level": finding.get("risk_level", "medium"),
                    "recommendation": finding.get("recommendation", "No recommendation")
                }
                checklist[criterion]["violations"].append(violation)
    
    # For any criterion with no findings, mark as "passed" if it was previously "not_assessed"
    for criterion in checklist:
        if checklist[criterion]["status"] == "not_assessed":
            checklist[criterion]["status"] = "passed"
    
    return checklist

def get_criterion_category(criterion: str) -> str:
    """
    Get the category of a SOC2 TSC criterion based on its prefix.
    
    Args:
        criterion: SOC2 TSC criterion code (e.g., "CC1.1", "A1.2", etc.)
        
    Returns:
        Category of the criterion
    """
    prefix = criterion.split(".")[0]
    if prefix.startswith("CC"):
        return "security"
    elif prefix.startswith("A"):
        return "availability"
    elif prefix.startswith("PI"):
        return "processing_integrity"
    elif prefix.startswith("C"):
        return "confidentiality"
    elif prefix.startswith("P"):
        return "privacy"
    else:
        return "unknown"