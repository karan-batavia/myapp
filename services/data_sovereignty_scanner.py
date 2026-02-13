"""
Data Sovereignty Scanner - Enterprise-grade data sovereignty and cross-border transfer analysis.

This scanner analyzes data flows, locations, access patterns, and jurisdictional exposure
to help organizations maintain compliance with GDPR, EU AI Act, and data sovereignty requirements.

Key Features:
- Cross-border transfer identification
- Data origin and location detection  
- Access rights analysis
- Jurisdiction and legal mapping
- Sovereignty risk scoring
- HTML compliance report generation
"""

import os
import re
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("data_sovereignty_scanner")
except ImportError:
    logger = logging.getLogger(__name__)


class SovereigntyRiskLevel(Enum):
    """Risk levels for sovereignty assessment"""
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class DataClassification(Enum):
    """Data classification types"""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_DATA = "sensitive_data"
    OPERATIONAL_DATA = "operational_data"
    AI_TRAINING_DATA = "ai_training_data"
    AI_INFERENCE_DATA = "ai_inference_data"


class JurisdictionType(Enum):
    """Jurisdiction types for legal mapping"""
    EU = "eu"
    EEA = "eea"
    ADEQUACY = "adequacy"
    THIRD_COUNTRY = "third_country"
    US_CLOUD_ACT = "us_cloud_act"


@dataclass
class DataLocation:
    """Represents a data storage location"""
    region: str
    country: str
    cloud_provider: Optional[str] = None
    service_type: Optional[str] = None
    is_eu: bool = False
    is_adequacy_decision: bool = False
    legal_jurisdiction: str = ""
    
    
@dataclass 
class DataFlow:
    """Represents a data flow between systems"""
    source: str
    destination: str
    source_country: str
    destination_country: str
    is_cross_border: bool = False
    is_eu_to_third_country: bool = False
    timestamp: Optional[str] = None
    flow_type: str = "continuous"
    data_types: List[str] = field(default_factory=list)
    
    
@dataclass
class AccessPath:
    """Represents an access path to data"""
    accessor_type: str
    accessor_country: str
    privilege_level: str
    is_eu_access: bool = True
    is_monitored: bool = True
    accessor_name: Optional[str] = None


@dataclass
class SovereigntyFinding:
    """A finding from sovereignty analysis"""
    finding_type: str
    severity: str
    title: str
    description: str
    affected_data: List[str]
    legal_reference: str
    recommendation: str
    risk_score: float = 0.0


@dataclass
class DataOrigin:
    """Tracks where data originates from"""
    source_name: str
    source_type: str  # "user_input", "api", "database", "file_upload", "external_service"
    country: str
    collection_method: str
    legal_basis: str = ""
    data_categories: List[str] = field(default_factory=list)
    is_eu_origin: bool = True


@dataclass
class LegalJurisdiction:
    """Legal jurisdiction analysis"""
    location: str
    country: str
    applicable_laws: List[str] = field(default_factory=list)
    adequacy_status: str = ""  # "EU", "Adequacy Decision", "SCCs Required", "No Basis"
    sccs_in_place: bool = False
    bcrs_in_place: bool = False
    tia_completed: bool = False
    dpa_in_place: bool = False
    risk_level: str = "low"


@dataclass
class ComplianceCheck:
    """Individual compliance check result"""
    check_name: str
    check_category: str  # "sccs", "tia", "encryption", "retention", "backup", "dpa", "bcr", "uavg"
    status: str  # "pass", "fail", "warning", "not_applicable"
    description: str
    legal_reference: str
    recommendation: str = ""


@dataclass
class SovereigntyScanResult:
    """Complete scan result"""
    scan_id: str
    scan_type: str = "Data Sovereignty Scanner"
    timestamp: str = ""
    target_name: str = ""
    data_locations: List[DataLocation] = field(default_factory=list)
    data_flows: List[DataFlow] = field(default_factory=list)
    access_paths: List[AccessPath] = field(default_factory=list)
    data_origins: List[DataOrigin] = field(default_factory=list)
    legal_jurisdictions: List[LegalJurisdiction] = field(default_factory=list)
    compliance_checks: List[ComplianceCheck] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    sovereignty_risk_score: float = 0.0
    risk_level: SovereigntyRiskLevel = SovereigntyRiskLevel.GREEN
    recommendations: List[str] = field(default_factory=list)
    cross_border_transfers: int = 0
    non_eu_access_count: int = 0
    third_country_processors: int = 0
    processing_time_ms: int = 0
    region: str = "Netherlands"
    encryption_at_rest: bool = False
    encryption_in_transit: bool = False
    data_retention_policy: str = ""
    backup_locations: List[str] = field(default_factory=list)


class DataSovereigntyScanner:
    """
    Enterprise scanner for data sovereignty and cross-border transfer analysis.
    
    Designed for Government and Enterprise license tiers to ensure:
    - GDPR cross-border transfer compliance (Chapter V)
    - EU AI Act data provenance requirements
    - Netherlands UAVG data residency requirements
    - CLOUD Act risk assessment
    """
    
    EU_COUNTRIES = {
        'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
        'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
        'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'
    }
    
    EEA_COUNTRIES = EU_COUNTRIES | {'IS', 'LI', 'NO'}
    
    ADEQUACY_COUNTRIES = {
        'AD', 'AR', 'CA', 'FO', 'GG', 'IL', 'IM', 'JP', 'JE', 'NZ',
        'KR', 'CH', 'GB', 'UY', 'US'
    }
    
    CLOUD_ACT_RISK_PROVIDERS = {
        'aws', 'amazon', 'microsoft', 'azure', 'google', 'gcp',
        'oracle', 'ibm', 'salesforce', 'dropbox', 'box'
    }
    
    CLOUD_REGIONS = {
        'eu-west-1': {'country': 'IE', 'name': 'Ireland'},
        'eu-west-2': {'country': 'GB', 'name': 'London'},
        'eu-west-3': {'country': 'FR', 'name': 'Paris'},
        'eu-central-1': {'country': 'DE', 'name': 'Frankfurt'},
        'eu-north-1': {'country': 'SE', 'name': 'Stockholm'},
        'eu-south-1': {'country': 'IT', 'name': 'Milan'},
        'eu-south-2': {'country': 'ES', 'name': 'Spain'},
        'eu-central-2': {'country': 'CH', 'name': 'Zurich'},
        'us-east-1': {'country': 'US', 'name': 'N. Virginia'},
        'us-east-2': {'country': 'US', 'name': 'Ohio'},
        'us-west-1': {'country': 'US', 'name': 'N. California'},
        'us-west-2': {'country': 'US', 'name': 'Oregon'},
        'ap-northeast-1': {'country': 'JP', 'name': 'Tokyo'},
        'ap-northeast-2': {'country': 'KR', 'name': 'Seoul'},
        'ap-northeast-3': {'country': 'JP', 'name': 'Osaka'},
        'ap-southeast-1': {'country': 'SG', 'name': 'Singapore'},
        'ap-southeast-2': {'country': 'AU', 'name': 'Sydney'},
        'ap-south-1': {'country': 'IN', 'name': 'Mumbai'},
        'ca-central-1': {'country': 'CA', 'name': 'Canada Central'},
        'sa-east-1': {'country': 'BR', 'name': 'Sao Paulo'},
        'me-south-1': {'country': 'BH', 'name': 'Bahrain'},
        'me-central-1': {'country': 'AE', 'name': 'UAE'},
        'af-south-1': {'country': 'ZA', 'name': 'Cape Town'},
        'il-central-1': {'country': 'IL', 'name': 'Tel Aviv'},
        'westeurope': {'country': 'NL', 'name': 'Netherlands'},
        'northeurope': {'country': 'IE', 'name': 'Ireland'},
        'germanywestcentral': {'country': 'DE', 'name': 'Frankfurt'},
        'francecentral': {'country': 'FR', 'name': 'Paris'},
        'francesouth': {'country': 'FR', 'name': 'France South (Marseille)'},
        'uksouth': {'country': 'GB', 'name': 'London'},
        'ukwest': {'country': 'GB', 'name': 'UK West (Cardiff)'},
        'eastus': {'country': 'US', 'name': 'East US (Virginia)'},
        'eastus2': {'country': 'US', 'name': 'East US 2 (Virginia)'},
        'westus': {'country': 'US', 'name': 'West US (California)'},
        'westus2': {'country': 'US', 'name': 'West US 2 (Washington)'},
        'westus3': {'country': 'US', 'name': 'West US 3 (Arizona)'},
        'centralus': {'country': 'US', 'name': 'Central US (Iowa)'},
        'northcentralus': {'country': 'US', 'name': 'North Central US (Illinois)'},
        'southcentralus': {'country': 'US', 'name': 'South Central US (Texas)'},
        'canadacentral': {'country': 'CA', 'name': 'Canada Central (Toronto)'},
        'canadaeast': {'country': 'CA', 'name': 'Canada East (Quebec)'},
        'brazilsouth': {'country': 'BR', 'name': 'Brazil South (Sao Paulo)'},
        'switzerlandnorth': {'country': 'CH', 'name': 'Switzerland North (Zurich)'},
        'switzerlandwest': {'country': 'CH', 'name': 'Switzerland West (Geneva)'},
        'norwayeast': {'country': 'NO', 'name': 'Norway East (Oslo)'},
        'norwaywest': {'country': 'NO', 'name': 'Norway West (Stavanger)'},
        'swedencentral': {'country': 'SE', 'name': 'Sweden Central (Gavle)'},
        'japaneast': {'country': 'JP', 'name': 'Japan East (Tokyo)'},
        'japanwest': {'country': 'JP', 'name': 'Japan West (Osaka)'},
        'southeastasia': {'country': 'SG', 'name': 'Southeast Asia (Singapore)'},
        'eastasia': {'country': 'HK', 'name': 'East Asia (Hong Kong)'},
        'australiaeast': {'country': 'AU', 'name': 'Australia East (Sydney)'},
        'australiasoutheast': {'country': 'AU', 'name': 'Australia Southeast (Melbourne)'},
        'koreacentral': {'country': 'KR', 'name': 'Korea Central (Seoul)'},
        'koreasouth': {'country': 'KR', 'name': 'Korea South (Busan)'},
        'centralindia': {'country': 'IN', 'name': 'Central India (Pune)'},
        'southindia': {'country': 'IN', 'name': 'South India (Chennai)'},
        'italynorth': {'country': 'IT', 'name': 'Italy North (Milan)'},
        'polandcentral': {'country': 'PL', 'name': 'Poland Central (Warsaw)'},
        'qatarcentral': {'country': 'QA', 'name': 'Qatar Central (Doha)'},
        'uaenorth': {'country': 'AE', 'name': 'UAE North (Dubai)'},
        'southafricanorth': {'country': 'ZA', 'name': 'South Africa North (Johannesburg)'},
        'europe-west1': {'country': 'BE', 'name': 'Belgium'},
        'europe-west2': {'country': 'GB', 'name': 'London'},
        'europe-west3': {'country': 'DE', 'name': 'Frankfurt'},
        'europe-west4': {'country': 'NL', 'name': 'Netherlands'},
        'europe-north1': {'country': 'FI', 'name': 'Finland'},
        'europe-west6': {'country': 'CH', 'name': 'Zurich'},
        'europe-west8': {'country': 'IT', 'name': 'Milan'},
        'europe-west9': {'country': 'FR', 'name': 'Paris'},
        'europe-west10': {'country': 'DE', 'name': 'Berlin'},
        'europe-west12': {'country': 'IT', 'name': 'Turin'},
        'europe-southwest1': {'country': 'ES', 'name': 'Madrid'},
        'europe-central2': {'country': 'PL', 'name': 'Warsaw'},
        'us-central1': {'country': 'US', 'name': 'Iowa'},
        'us-east1': {'country': 'US', 'name': 'South Carolina'},
        'us-east4': {'country': 'US', 'name': 'Northern Virginia'},
        'us-east5': {'country': 'US', 'name': 'Columbus'},
        'us-south1': {'country': 'US', 'name': 'Dallas'},
        'us-west1': {'country': 'US', 'name': 'Oregon'},
        'us-west2': {'country': 'US', 'name': 'Los Angeles'},
        'us-west3': {'country': 'US', 'name': 'Salt Lake City'},
        'us-west4': {'country': 'US', 'name': 'Las Vegas'},
        'northamerica-northeast1': {'country': 'CA', 'name': 'Montreal'},
        'northamerica-northeast2': {'country': 'CA', 'name': 'Toronto'},
        'southamerica-east1': {'country': 'BR', 'name': 'Sao Paulo'},
        'asia-east1': {'country': 'TW', 'name': 'Taiwan'},
        'asia-east2': {'country': 'HK', 'name': 'Hong Kong'},
        'asia-northeast1': {'country': 'JP', 'name': 'Tokyo'},
        'asia-northeast2': {'country': 'JP', 'name': 'Osaka'},
        'asia-northeast3': {'country': 'KR', 'name': 'Seoul'},
        'asia-south1': {'country': 'IN', 'name': 'Mumbai'},
        'asia-south2': {'country': 'IN', 'name': 'Delhi'},
        'asia-southeast1': {'country': 'SG', 'name': 'Singapore'},
        'asia-southeast2': {'country': 'ID', 'name': 'Jakarta'},
        'australia-southeast1': {'country': 'AU', 'name': 'Sydney'},
        'australia-southeast2': {'country': 'AU', 'name': 'Melbourne'},
        'me-west1': {'country': 'IL', 'name': 'Tel Aviv'},
        'me-central1': {'country': 'QA', 'name': 'Doha'},
        'me-central2': {'country': 'SA', 'name': 'Dammam'},
        'africa-south1': {'country': 'ZA', 'name': 'Johannesburg'},
        'fsn1': {'country': 'DE', 'name': 'Hetzner Falkenstein'},
        'nbg1': {'country': 'DE', 'name': 'Hetzner Nuremberg'},
        'hel1': {'country': 'FI', 'name': 'Hetzner Helsinki'},
        'ash': {'country': 'US', 'name': 'Hetzner Ashburn'},
        'gra': {'country': 'FR', 'name': 'OVH Gravelines'},
        'sbg': {'country': 'FR', 'name': 'OVH Strasbourg'},
        'rbx': {'country': 'FR', 'name': 'OVH Roubaix'},
        'bhs': {'country': 'CA', 'name': 'OVH Beauharnois'},
        'waw': {'country': 'PL', 'name': 'OVH Warsaw'},
        'de1': {'country': 'DE', 'name': 'OVH Frankfurt'},
        'uk1': {'country': 'GB', 'name': 'OVH London'},
        'fr-par': {'country': 'FR', 'name': 'Scaleway Paris'},
        'nl-ams': {'country': 'NL', 'name': 'Scaleway Amsterdam'},
        'pl-waw': {'country': 'PL', 'name': 'Scaleway Warsaw'},
        'ams2': {'country': 'NL', 'name': 'DigitalOcean Amsterdam 2'},
        'ams3': {'country': 'NL', 'name': 'DigitalOcean Amsterdam 3'},
        'fra1': {'country': 'DE', 'name': 'DigitalOcean Frankfurt'},
        'lon1': {'country': 'GB', 'name': 'DigitalOcean London'},
        'sgp1': {'country': 'SG', 'name': 'DigitalOcean Singapore'},
        'nyc1': {'country': 'US', 'name': 'DigitalOcean New York 1'},
        'nyc3': {'country': 'US', 'name': 'DigitalOcean New York 3'},
        'sfo1': {'country': 'US', 'name': 'DigitalOcean San Francisco 1'},
        'sfo3': {'country': 'US', 'name': 'DigitalOcean San Francisco 3'},
        'ams0': {'country': 'NL', 'name': 'TransIP Amsterdam'},
        'de-fra': {'country': 'DE', 'name': 'IONOS Frankfurt'},
        'de-txl': {'country': 'DE', 'name': 'IONOS Berlin'},
        'es-vit': {'country': 'ES', 'name': 'IONOS Vitoria'},
        'gb-lhr': {'country': 'GB', 'name': 'IONOS London'},
        'us-ewr': {'country': 'US', 'name': 'IONOS Newark'},
        'us-las': {'country': 'US', 'name': 'IONOS Las Vegas'}
    }
    
    def __init__(self, region: str = "Netherlands"):
        """
        Initialize the Data Sovereignty Scanner.
        
        Args:
            region: Primary region for compliance analysis
        """
        self.region = region
        self.scan_id = ""
        self.start_time = None
        
    def scan_infrastructure(self, config: Dict[str, Any]) -> SovereigntyScanResult:
        """
        Scan infrastructure configuration for sovereignty issues.
        
        Args:
            config: Infrastructure configuration containing:
                - cloud_resources: List of cloud resources with regions
                - data_stores: Database and storage configurations
                - integrations: Third-party service integrations
                - access_controls: Access control configurations
                
        Returns:
            SovereigntyScanResult with complete analysis
        """
        import uuid
        self.scan_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        
        result = SovereigntyScanResult(
            scan_id=self.scan_id,
            timestamp=datetime.now().isoformat(),
            target_name=config.get('name', 'Infrastructure Scan'),
            region=self.region
        )
        
        try:
            result.data_locations = self._analyze_data_locations(config)
            result.data_flows = self._analyze_data_flows(config)
            result.access_paths = self._analyze_access_paths(config)
            result.data_origins = self._analyze_data_origins(config)
            result.legal_jurisdictions = self._analyze_legal_jurisdictions(result.data_locations)
            result.compliance_checks = self._run_compliance_checks(config, result)
            
            result.encryption_at_rest = self._detect_encryption_at_rest(config)
            result.encryption_in_transit = self._detect_encryption_in_transit(config)
            result.data_retention_policy = self._detect_retention_policy(config)
            result.backup_locations = self._detect_backup_locations(config)
            
            result.findings = self._generate_findings(result)
            result.recommendations = self._generate_recommendations(result)
            
            result.sovereignty_risk_score = self._calculate_risk_score(result)
            result.risk_level = self._determine_risk_level(result.sovereignty_risk_score)
            
            result.cross_border_transfers = sum(1 for f in result.data_flows if f.is_cross_border)
            result.non_eu_access_count = sum(1 for a in result.access_paths if not a.is_eu_access)
            result.third_country_processors = sum(1 for l in result.data_locations 
                                                   if not l.is_eu and not l.is_adequacy_decision)
            
            result.processing_time_ms = int((datetime.now() - self.start_time).total_seconds() * 1000)
            
        except Exception as e:
            logger.error(f"Error during sovereignty scan: {e}")
            result.findings.append({
                'type': 'scan_error',
                'severity': 'high',
                'title': 'Scan Error',
                'description': f'Error during sovereignty analysis: {str(e)}',
                'legal_reference': 'N/A',
                'recommendation': 'Review configuration and retry scan'
            })
            
        return result
    
    def scan_terraform(self, terraform_content: str, filename: str = "main.tf") -> SovereigntyScanResult:
        """
        Scan Terraform configuration for sovereignty issues.
        
        Args:
            terraform_content: Terraform file content
            filename: Name of the Terraform file
            
        Returns:
            SovereigntyScanResult with analysis
        """
        import uuid
        self.scan_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        
        result = SovereigntyScanResult(
            scan_id=self.scan_id,
            timestamp=datetime.now().isoformat(),
            target_name=filename,
            region=self.region
        )
        
        try:
            result.data_locations = self._parse_terraform_locations(terraform_content)
            result.data_flows = self._detect_terraform_flows(terraform_content)
            result.access_paths = self._detect_terraform_access(terraform_content)
            result.data_origins = self._analyze_terraform_origins(terraform_content)
            result.legal_jurisdictions = self._analyze_legal_jurisdictions(result.data_locations)
            result.compliance_checks = self._run_terraform_compliance_checks(terraform_content, result)
            result.compliance_checks.extend(self._run_nis2_compliance_checks(terraform_content, result))
            
            result.encryption_at_rest = self._detect_terraform_encryption(terraform_content, "at_rest")
            result.encryption_in_transit = self._detect_terraform_encryption(terraform_content, "in_transit")
            result.data_retention_policy = self._detect_terraform_retention(terraform_content)
            result.backup_locations = self._detect_terraform_backups(terraform_content)
            
            result.findings = self._generate_findings(result)
            result.recommendations = self._generate_recommendations(result)
            
            result.sovereignty_risk_score = self._calculate_risk_score(result)
            result.risk_level = self._determine_risk_level(result.sovereignty_risk_score)
            
            result.cross_border_transfers = sum(1 for f in result.data_flows if f.is_cross_border)
            result.non_eu_access_count = sum(1 for a in result.access_paths if not a.is_eu_access)
            result.third_country_processors = sum(1 for l in result.data_locations 
                                                   if not l.is_eu and not l.is_adequacy_decision)
            
            result.processing_time_ms = int((datetime.now() - self.start_time).total_seconds() * 1000)
            
        except Exception as e:
            logger.error(f"Error parsing Terraform: {e}")
            result.findings.append({
                'type': 'parse_error',
                'severity': 'medium',
                'title': 'Terraform Parse Error',
                'description': f'Could not fully parse Terraform configuration: {str(e)}',
                'legal_reference': 'N/A',
                'recommendation': 'Ensure valid Terraform syntax'
            })
            
        return result
    
    def scan_cloud_config(self, config_content: str, config_type: str = "aws") -> SovereigntyScanResult:
        """
        Scan cloud configuration files (AWS CloudFormation, Azure ARM, etc.)
        
        Args:
            config_content: Configuration file content
            config_type: Type of configuration (aws, azure, gcp, kubernetes, generic)
            
        Returns:
            SovereigntyScanResult with analysis
        """
        import uuid
        self.scan_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        
        detected_provider = self._detect_terraform_provider(config_content)
        if config_type == "generic" and detected_provider != 'Unknown':
            config_type = detected_provider.lower()
        
        config_type_labels = {
            "kubernetes": "Kubernetes",
            "docker": "Docker Compose",
            "dockerfile": "Dockerfile",
        }
        if config_type in config_type_labels:
            target_label = f"{config_type_labels[config_type]} Configuration"
        elif detected_provider != 'Unknown':
            target_label = f"{detected_provider} Configuration"
        else:
            target_label = f"{config_type.upper()} Configuration"
        
        result = SovereigntyScanResult(
            scan_id=self.scan_id,
            timestamp=datetime.now().isoformat(),
            target_name=target_label,
            region=self.region
        )
        
        try:
            if config_type in ("aws", "AWS"):
                result.data_locations = self._parse_aws_config(config_content)
            elif config_type in ("azure", "Azure"):
                result.data_locations = self._parse_azure_config(config_content)
            elif config_type in ("gcp", "GCP"):
                result.data_locations = self._parse_gcp_config(config_content)
            elif config_type == "kubernetes":
                result.data_locations = self._parse_kubernetes_config(config_content)
            elif config_type == "docker":
                result.data_locations = self._parse_docker_compose(config_content)
            elif config_type == "dockerfile":
                result.data_locations = self._parse_dockerfile(config_content)
            else:
                result.data_locations = self._parse_generic_config(config_content)
            
            if not result.data_locations:
                result.data_locations = self._parse_terraform_locations(config_content)
            
            if config_type == "kubernetes":
                result.data_flows = self._detect_kubernetes_flows(config_content)
                result.access_paths = self._detect_kubernetes_access(config_content)
                result.data_origins = self._analyze_kubernetes_origins(config_content)
            else:
                result.data_flows = self._detect_terraform_flows(config_content)
                result.access_paths = self._detect_terraform_access(config_content)
                result.data_origins = self._analyze_terraform_origins(config_content)
            result.legal_jurisdictions = self._analyze_legal_jurisdictions(result.data_locations)
            result.compliance_checks = self._run_terraform_compliance_checks(config_content, result)
            result.compliance_checks.extend(self._run_nis2_compliance_checks(config_content, result))
            
            result.encryption_at_rest = self._detect_terraform_encryption(config_content, "at_rest")
            result.encryption_in_transit = self._detect_terraform_encryption(config_content, "in_transit")
            result.data_retention_policy = self._detect_terraform_retention(config_content)
            result.backup_locations = self._detect_terraform_backups(config_content)
            
            result.findings = self._generate_findings(result)
            result.recommendations = self._generate_recommendations(result)
            
            result.sovereignty_risk_score = self._calculate_risk_score(result)
            result.risk_level = self._determine_risk_level(result.sovereignty_risk_score)
            
            result.cross_border_transfers = sum(1 for f in result.data_flows if f.is_cross_border)
            result.non_eu_access_count = sum(1 for a in result.access_paths if not a.is_eu_access)
            result.third_country_processors = sum(1 for l in result.data_locations 
                                                   if not l.is_eu and not l.is_adequacy_decision)
            
            result.processing_time_ms = int((datetime.now() - self.start_time).total_seconds() * 1000)
            
        except Exception as e:
            logger.error(f"Error parsing {config_type} config: {e}")
            result.findings.append({
                'type': 'parse_error',
                'severity': 'medium',
                'title': 'Configuration Parse Error',
                'description': f'Could not fully parse configuration: {str(e)}',
                'legal_reference': 'N/A',
                'recommendation': 'Ensure valid configuration syntax'
            })
            
        return result
    
    def _analyze_data_locations(self, config: Dict[str, Any]) -> List[DataLocation]:
        """Analyze data storage locations from configuration"""
        locations = []
        
        cloud_resources = config.get('cloud_resources', [])
        for resource in cloud_resources:
            region = resource.get('region', '')
            provider = resource.get('provider', '')
            
            region_info = self.CLOUD_REGIONS.get(region.lower(), {})
            country = region_info.get('country', self._detect_country_from_region(region))
            
            location = DataLocation(
                region=region,
                country=country,
                cloud_provider=provider,
                service_type=resource.get('type', 'unknown'),
                is_eu=country in self.EU_COUNTRIES,
                is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                legal_jurisdiction=self._get_jurisdiction(country)
            )
            locations.append(location)
            
        data_stores = config.get('data_stores', [])
        for store in data_stores:
            region = store.get('region', store.get('location', ''))
            country = self._detect_country_from_region(region)
            
            location = DataLocation(
                region=region,
                country=country,
                cloud_provider=store.get('provider', 'on-premises'),
                service_type=store.get('type', 'database'),
                is_eu=country in self.EU_COUNTRIES,
                is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                legal_jurisdiction=self._get_jurisdiction(country)
            )
            locations.append(location)
            
        return locations
    
    def _analyze_data_flows(self, config: Dict[str, Any]) -> List[DataFlow]:
        """Analyze data flows between systems"""
        flows = []
        
        integrations = config.get('integrations', [])
        for integration in integrations:
            source = integration.get('source', '')
            dest = integration.get('destination', '')
            source_country = self._detect_country_from_service(source)
            dest_country = self._detect_country_from_service(dest)
            
            is_cross_border = source_country != dest_country
            is_eu_to_third = (source_country in self.EU_COUNTRIES and 
                             dest_country not in self.EU_COUNTRIES and
                             dest_country not in self.ADEQUACY_COUNTRIES)
            
            flow = DataFlow(
                source=source,
                destination=dest,
                source_country=source_country,
                destination_country=dest_country,
                is_cross_border=is_cross_border,
                is_eu_to_third_country=is_eu_to_third,
                timestamp=datetime.now().isoformat(),
                flow_type=integration.get('flow_type', 'continuous'),
                data_types=integration.get('data_types', [])
            )
            flows.append(flow)
            
        return flows
    
    def _analyze_access_paths(self, config: Dict[str, Any]) -> List[AccessPath]:
        """Analyze access control configurations"""
        paths = []
        
        access_controls = config.get('access_controls', [])
        for access in access_controls:
            country = access.get('country', 'NL')
            
            path = AccessPath(
                accessor_type=access.get('type', 'user'),
                accessor_country=country,
                privilege_level=access.get('privilege', 'read'),
                is_eu_access=country in self.EU_COUNTRIES,
                is_monitored=access.get('monitored', True),
                accessor_name=access.get('name')
            )
            paths.append(path)
            
        return paths
    
    def _parse_terraform_locations(self, content: str) -> List[DataLocation]:
        """Parse Terraform content for data locations"""
        locations = []
        seen_regions = set()
        
        provider = self._detect_terraform_provider(content)
        
        region_patterns = [
            r'region\s*=\s*["\']([^"\']+)["\']',
            r'location\s*=\s*["\']([^"\']+)["\']',
            r'zone\s*=\s*["\']([^"\']+)["\']'
        ]
        
        service_patterns = [
            (r'resource\s+"aws_s3_bucket"', 'S3 Object Storage'),
            (r'resource\s+"aws_rds_', 'RDS Database'),
            (r'resource\s+"aws_dynamodb_', 'DynamoDB'),
            (r'resource\s+"aws_lambda_', 'Lambda Function'),
            (r'resource\s+"aws_ec2_', 'EC2 Compute'),
            (r'resource\s+"aws_instance"', 'EC2 Instance'),
            (r'resource\s+"aws_ecs_', 'ECS Container'),
            (r'resource\s+"aws_eks_', 'EKS Kubernetes'),
            (r'resource\s+"aws_sqs_', 'SQS Queue'),
            (r'resource\s+"aws_sns_', 'SNS Notification'),
            (r'resource\s+"aws_kinesis_', 'Kinesis Stream'),
            (r'resource\s+"aws_elasticsearch_', 'Elasticsearch'),
            (r'resource\s+"aws_opensearch_', 'OpenSearch'),
            (r'resource\s+"aws_redshift_', 'Redshift Data Warehouse'),
            (r'resource\s+"aws_elasticache_', 'ElastiCache'),
            (r'resource\s+"azurerm_storage_', 'Azure Storage'),
            (r'resource\s+"azurerm_sql_', 'Azure SQL'),
            (r'resource\s+"azurerm_cosmosdb_', 'Cosmos DB'),
            (r'resource\s+"azurerm_kubernetes_cluster"', 'AKS Kubernetes Cluster'),
            (r'resource\s+"azurerm_function_app"', 'Azure Functions'),
            (r'resource\s+"azurerm_linux_function_app"', 'Azure Functions (Linux)'),
            (r'resource\s+"azurerm_windows_function_app"', 'Azure Functions (Windows)'),
            (r'resource\s+"azurerm_redis_cache"', 'Azure Redis Cache'),
            (r'resource\s+"azurerm_servicebus_', 'Azure Service Bus'),
            (r'resource\s+"azurerm_eventhub', 'Azure Event Hub'),
            (r'resource\s+"azurerm_virtual_machine"', 'Azure Virtual Machine'),
            (r'resource\s+"azurerm_linux_virtual_machine"', 'Azure Linux VM'),
            (r'resource\s+"azurerm_windows_virtual_machine"', 'Azure Windows VM'),
            (r'resource\s+"azurerm_mssql_', 'Azure SQL Database'),
            (r'resource\s+"azurerm_postgresql_', 'Azure PostgreSQL'),
            (r'resource\s+"azurerm_mysql_', 'Azure MySQL'),
            (r'resource\s+"azurerm_key_vault"', 'Azure Key Vault'),
            (r'resource\s+"azurerm_cognitive_account"', 'Azure Cognitive Services'),
            (r'resource\s+"azurerm_search_service"', 'Azure Cognitive Search'),
            (r'resource\s+"azurerm_container_', 'Azure Container Instance/Registry'),
            (r'resource\s+"azurerm_app_service"', 'Azure App Service'),
            (r'resource\s+"azurerm_linux_web_app"', 'Azure Web App (Linux)'),
            (r'resource\s+"azurerm_windows_web_app"', 'Azure Web App (Windows)'),
            (r'resource\s+"azurerm_data_factory"', 'Azure Data Factory'),
            (r'resource\s+"azurerm_synapse_', 'Azure Synapse Analytics'),
            (r'resource\s+"azurerm_monitor_', 'Azure Monitor'),
            (r'resource\s+"azurerm_log_analytics_', 'Azure Log Analytics'),
            (r'resource\s+"azurerm_application_insights"', 'Azure Application Insights'),
            (r'resource\s+"google_storage_', 'Cloud Storage'),
            (r'resource\s+"google_bigquery_', 'BigQuery'),
            (r'resource\s+"google_sql_', 'Cloud SQL'),
            (r'resource\s+"google_compute_instance"', 'GCE Compute Instance'),
            (r'resource\s+"google_container_cluster"', 'GKE Kubernetes Cluster'),
            (r'resource\s+"google_cloud_run_', 'Cloud Run'),
            (r'resource\s+"google_cloudfunctions2_', 'Cloud Functions v2'),
            (r'resource\s+"google_redis_instance"', 'Cloud Memorystore (Redis)'),
            (r'resource\s+"google_pubsub_', 'Cloud Pub/Sub'),
            (r'resource\s+"google_spanner_', 'Cloud Spanner'),
            (r'resource\s+"google_firestore_', 'Cloud Firestore'),
            (r'resource\s+"google_bigtable_', 'Cloud Bigtable'),
            (r'resource\s+"google_dataflow_', 'Cloud Dataflow'),
            (r'resource\s+"google_dataproc_', 'Cloud Dataproc'),
            (r'resource\s+"google_kms_', 'Cloud KMS'),
            (r'resource\s+"google_secret_manager_', 'Secret Manager'),
            (r'resource\s+"google_app_engine_', 'App Engine'),
            (r'resource\s+"google_vertex_ai_', 'Vertex AI'),
            (r'resource\s+"google_logging_', 'Cloud Logging'),
            (r'resource\s+"google_monitoring_', 'Cloud Monitoring'),
            (r'resource\s+"google_dns_', 'Cloud DNS'),
        ]
        
        detected_services = []
        for pattern, service_name in service_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                detected_services.append(service_name)
        
        for pattern in region_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for region in matches:
                if region.lower() in seen_regions:
                    continue
                
                region_info = self.CLOUD_REGIONS.get(region.lower(), {})
                country = region_info.get('country', self._detect_country_from_region(region))
                
                if country == 'unknown':
                    continue
                
                seen_regions.add(region.lower())
                
                service_desc = ', '.join(detected_services[:3]) if detected_services else 'Infrastructure'
                
                location = DataLocation(
                    region=region,
                    country=country,
                    cloud_provider=provider,
                    service_type=service_desc,
                    is_eu=country in self.EU_COUNTRIES,
                    is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                    legal_jurisdiction=self._get_jurisdiction(country)
                )
                locations.append(location)
                
        return locations
    
    def _detect_terraform_provider(self, content: str) -> str:
        """Detect cloud provider from Terraform content"""
        content_lower = content.lower()
        if re.search(r'provider\s+["\']?aws', content_lower) or 'aws_' in content_lower:
            return 'AWS'
        elif re.search(r'provider\s+["\']?azurerm', content_lower) or 'azurerm_' in content_lower:
            return 'Azure'
        elif re.search(r'provider\s+["\']?google', content_lower) or 'google_' in content_lower:
            return 'GCP'
        elif re.search(r'provider\s+["\']?hcloud', content_lower) or 'hcloud_' in content_lower or 'hetzner' in content_lower:
            return 'Hetzner'
        elif re.search(r'provider\s+["\']?ovh', content_lower) or 'ovh_' in content_lower or 'ovhcloud' in content_lower:
            return 'OVH'
        elif re.search(r'provider\s+["\']?scaleway', content_lower) or 'scaleway_' in content_lower:
            return 'Scaleway'
        elif re.search(r'provider\s+["\']?digitalocean', content_lower) or 'digitalocean_' in content_lower:
            return 'DigitalOcean'
        elif 'transip' in content_lower:
            return 'TransIP'
        elif re.search(r'provider\s+["\']?ionos', content_lower) or 'ionos' in content_lower:
            return 'IONOS'
        elif 'aws' in content_lower:
            return 'AWS'
        elif 'azure' in content_lower:
            return 'Azure'
        elif 'gcp' in content_lower or 'google' in content_lower:
            return 'GCP'
        return 'Unknown'
    
    def _detect_terraform_flows(self, content: str) -> List[DataFlow]:
        """Detect data flows from Terraform configuration"""
        flows = []
        base_country = self._get_country_from_region(self.region)
        
        replication_patterns = [
            r'replica.*region\s*=\s*["\']([^"\']+)["\']',
            r'destination.*region\s*=\s*["\']([^"\']+)["\']',
            r'target.*region\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in replication_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for region in matches:
                dest_country = self._detect_country_from_region(region)
                
                flow = DataFlow(
                    source="primary",
                    destination=region,
                    source_country=base_country,
                    destination_country=dest_country,
                    is_cross_border=dest_country != base_country,
                    is_eu_to_third_country=(base_country in self.EU_COUNTRIES and 
                                           dest_country not in self.EU_COUNTRIES and 
                                           dest_country not in self.ADEQUACY_COUNTRIES),
                    flow_type="replication"
                )
                flows.append(flow)
        
        region_patterns = [
            r'region\s*=\s*["\']([^"\']+)["\']',
            r'location\s*=\s*["\']([^"\']+)["\']',
        ]
        
        seen_regions = set()
        for pattern in region_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for region in matches:
                region_lower = region.lower()
                if region_lower in seen_regions:
                    continue
                    
                dest_country = self._detect_country_from_region(region)
                if dest_country == 'unknown':
                    continue
                    
                if dest_country != base_country:
                    seen_regions.add(region_lower)
                    is_eu_to_third = (base_country in self.EU_COUNTRIES and 
                                     dest_country not in self.EU_COUNTRIES and 
                                     dest_country not in self.ADEQUACY_COUNTRIES)
                    
                    region_info = self.CLOUD_REGIONS.get(region_lower, {})
                    dest_name = region_info.get('name', region)
                    
                    flow = DataFlow(
                        source=f"{self.region} (Organization)",
                        destination=f"{dest_name} ({region})",
                        source_country=base_country,
                        destination_country=dest_country,
                        is_cross_border=True,
                        is_eu_to_third_country=is_eu_to_third,
                        flow_type="infrastructure_deployment",
                        data_types=["infrastructure_data", "application_data"]
                    )
                    flows.append(flow)
        
        provider = self._detect_terraform_provider(content)
        if provider in ['AWS', 'Azure', 'GCP']:
            provider_country = 'US'
            if provider_country != base_country:
                flows.append(DataFlow(
                    source=f"{self.region} (Data Controller)",
                    destination=f"{provider} (Cloud Provider - US HQ)",
                    source_country=base_country,
                    destination_country=provider_country,
                    is_cross_border=True,
                    is_eu_to_third_country=(base_country in self.EU_COUNTRIES),
                    flow_type="cloud_provider_processing",
                    data_types=["metadata", "telemetry", "billing_data"]
                ))
                
        return flows
    
    def _detect_terraform_access(self, content: str) -> List[AccessPath]:
        """Detect access patterns from Terraform configuration"""
        paths = []
        content_lower = content.lower()
        provider = self._detect_terraform_provider(content)
        
        primary_region = "Unknown"
        region_match = re.search(r'region\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
        if region_match:
            primary_region = region_match.group(1)
        primary_country = self._detect_country_from_region(primary_region)
        is_eu = primary_country in self.EU_COUNTRIES
        
        access_patterns = [
            {
                'patterns': [r'aws_iam_role', r'iam_role', r'azurerm_role_assignment', r'google_project_iam'],
                'type': 'IAM Role',
                'name': f'{provider} IAM Service Role',
                'privilege': 'service_role',
                'monitored': True
            },
            {
                'patterns': [r'aws_iam_user', r'azurerm_user_assigned_identity', r'google_service_account'],
                'type': 'IAM User/Identity',
                'name': f'{provider} IAM User',
                'privilege': 'user_access',
                'monitored': True
            },
            {
                'patterns': [r'aws_iam_policy', r'iam_policy_document', r'azurerm_role_definition'],
                'type': 'IAM Policy',
                'name': f'{provider} Access Policy',
                'privilege': 'policy_based',
                'monitored': True
            },
            {
                'patterns': [r'aws_security_group', r'azurerm_network_security_group', r'google_compute_firewall'],
                'type': 'Network Security',
                'name': 'Network Security Group / Firewall',
                'privilege': 'network_level',
                'monitored': True
            },
            {
                'patterns': [r'allowed_ip_ranges', r'ip_whitelist', r'source_ranges', r'cidr_blocks.*0\.0\.0\.0'],
                'type': 'IP-Based Access',
                'name': 'IP Allowlist / CIDR Range',
                'privilege': 'network',
                'monitored': False
            },
            {
                'patterns': [r'service_account', r'managed_identity', r'workload_identity'],
                'type': 'Service Account',
                'name': f'{provider} Service Account',
                'privilege': 'automated',
                'monitored': True
            }
        ]
        
        public_access = re.search(r'cidr_blocks\s*=\s*\[\s*["\']0\.0\.0\.0/0["\']', content_lower)
        if public_access or re.search(r'publicly_accessible\s*=\s*true', content_lower):
            paths.append(AccessPath(
                accessor_type="Public Internet Access",
                accessor_country="Global (Any Country)",
                privilege_level="public_endpoint",
                is_eu_access=False,
                is_monitored=False,
                accessor_name="Open Internet Access (0.0.0.0/0)"
            ))
        
        for access_def in access_patterns:
            matched = False
            for pattern in access_def['patterns']:
                if re.search(pattern, content_lower):
                    matched = True
                    break
            
            if matched:
                paths.append(AccessPath(
                    accessor_type=access_def['type'],
                    accessor_country=primary_country if primary_country != 'unknown' else 'Unknown',
                    privilege_level=access_def['privilege'],
                    is_eu_access=is_eu,
                    is_monitored=access_def['monitored'],
                    accessor_name=access_def['name']
                ))
        
        if provider in ['AWS', 'Azure', 'GCP']:
            paths.append(AccessPath(
                accessor_type="Cloud Provider Admin",
                accessor_country="US",
                privilege_level="provider_admin",
                is_eu_access=False,
                is_monitored=True,
                accessor_name=f"{provider} Support/Operations (US-headquartered)"
            ))
            
        return paths
    
    def _parse_aws_config(self, content: str) -> List[DataLocation]:
        """Parse AWS CloudFormation configuration"""
        locations = []
        seen_regions = set()
        
        region_patterns = [
            r'Region["\']?\s*[:=]\s*["\']?([a-z]{2}-[a-z]+-\d)["\']?',
            r'region\s*[:=]\s*["\']([a-z]{2}-[a-z]+-\d)["\']',
            r'"AWS::Region"\s*[:=]\s*["\']([^"\']+)["\']'
        ]
        
        service_patterns = [
            (r'AWS::S3::Bucket|aws_s3_bucket', 'S3 Object Storage'),
            (r'AWS::RDS::DBInstance|aws_rds_|aws_db_instance', 'RDS Database'),
            (r'AWS::DynamoDB::Table|aws_dynamodb', 'DynamoDB'),
            (r'AWS::Lambda::Function|aws_lambda', 'Lambda Function'),
            (r'AWS::EC2::Instance|aws_instance', 'EC2 Compute'),
            (r'AWS::ECS|aws_ecs_', 'ECS Container'),
            (r'AWS::EKS|aws_eks_', 'EKS Kubernetes'),
            (r'AWS::SQS|aws_sqs_', 'SQS Queue'),
            (r'AWS::SNS|aws_sns_', 'SNS Notification'),
            (r'AWS::Kinesis|aws_kinesis', 'Kinesis Stream'),
            (r'AWS::Elasticsearch|aws_elasticsearch|aws_opensearch', 'OpenSearch'),
            (r'AWS::Redshift|aws_redshift', 'Redshift Data Warehouse'),
            (r'AWS::ElastiCache|aws_elasticache', 'ElastiCache'),
            (r'AWS::ApiGateway|aws_api_gateway|aws_apigateway', 'API Gateway'),
            (r'AWS::Cognito|aws_cognito', 'Cognito Identity'),
        ]
        
        detected_services = []
        for pattern, service_name in service_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                detected_services.append(service_name)
        
        for rp in region_patterns:
            matches = re.findall(rp, content, re.IGNORECASE)
            for region in matches:
                if region.lower() in seen_regions:
                    continue
                seen_regions.add(region.lower())
                
                region_info = self.CLOUD_REGIONS.get(region.lower(), {})
                country = region_info.get('country', 'US')
                service_desc = ', '.join(detected_services[:3]) if detected_services else 'AWS Infrastructure'
                
                locations.append(DataLocation(
                    region=region,
                    country=country,
                    cloud_provider='AWS',
                    service_type=service_desc,
                    is_eu=country in self.EU_COUNTRIES,
                    is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                    legal_jurisdiction=self._get_jurisdiction(country)
                ))
            
        return locations
    
    def _parse_azure_config(self, content: str) -> List[DataLocation]:
        """Parse Azure ARM/Bicep configuration"""
        locations = []
        seen_regions = set()
        
        location_patterns = [
            r'location["\']?\s*[:=]\s*["\']([a-zA-Z]+)["\']',
            r'"location"\s*:\s*"([^"]+)"',
            r'location\s*=\s*["\']([^"\']+)["\']'
        ]
        
        service_patterns = [
            (r'Microsoft\.Storage|azurerm_storage', 'Azure Storage'),
            (r'Microsoft\.Sql|azurerm_mssql|azurerm_sql', 'Azure SQL Database'),
            (r'Microsoft\.DocumentDB|azurerm_cosmosdb', 'Cosmos DB'),
            (r'Microsoft\.DBforPostgreSQL|azurerm_postgresql', 'Azure PostgreSQL'),
            (r'Microsoft\.DBforMySQL|azurerm_mysql', 'Azure MySQL'),
            (r'Microsoft\.ContainerService|azurerm_kubernetes', 'AKS Kubernetes'),
            (r'Microsoft\.Web|azurerm_function_app|azurerm_app_service|azurerm_linux_web_app', 'Azure App Service/Functions'),
            (r'Microsoft\.Compute|azurerm_virtual_machine|azurerm_linux_virtual_machine', 'Azure Virtual Machine'),
            (r'Microsoft\.KeyVault|azurerm_key_vault', 'Azure Key Vault'),
            (r'Microsoft\.CognitiveServices|azurerm_cognitive', 'Azure Cognitive Services'),
            (r'Microsoft\.ServiceBus|azurerm_servicebus', 'Azure Service Bus'),
            (r'Microsoft\.EventHub|azurerm_eventhub', 'Azure Event Hub'),
            (r'Microsoft\.Cache|azurerm_redis_cache', 'Azure Redis Cache'),
        ]
        
        detected_services = []
        for pattern, service_name in service_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                detected_services.append(service_name)
        
        for lp in location_patterns:
            matches = re.findall(lp, content, re.IGNORECASE)
            for location in matches:
                loc_lower = location.lower().strip()
                if loc_lower in seen_regions or len(loc_lower) < 3:
                    continue
                
                region_info = self.CLOUD_REGIONS.get(loc_lower, {})
                if not region_info:
                    continue
                    
                seen_regions.add(loc_lower)
                country = region_info.get('country', 'NL')
                service_desc = ', '.join(detected_services[:3]) if detected_services else 'Azure Infrastructure'
                
                locations.append(DataLocation(
                    region=location,
                    country=country,
                    cloud_provider='Azure',
                    service_type=service_desc,
                    is_eu=country in self.EU_COUNTRIES,
                    is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                    legal_jurisdiction=self._get_jurisdiction(country)
                ))
            
        return locations
    
    def _parse_gcp_config(self, content: str) -> List[DataLocation]:
        """Parse GCP Deployment Manager configuration"""
        locations = []
        seen_regions = set()
        
        region_patterns = [
            r'region["\']?\s*[:=]\s*["\']([a-z]+-[a-z]+\d*)["\']',
            r'location["\']?\s*[:=]\s*["\']([a-z]+-[a-z]+\d*)["\']',
            r'zone["\']?\s*[:=]\s*["\']([a-z]+-[a-z]+\d+-[a-z])["\']'
        ]
        
        service_patterns = [
            (r'google_storage_bucket|compute\.googleapis\.com/Disk', 'Cloud Storage'),
            (r'google_sql_database|sqladmin\.googleapis\.com', 'Cloud SQL'),
            (r'google_bigquery|bigquery\.googleapis\.com', 'BigQuery'),
            (r'google_compute_instance|compute\.googleapis\.com', 'GCE Compute'),
            (r'google_container_cluster|container\.googleapis\.com', 'GKE Kubernetes'),
            (r'google_cloud_run|run\.googleapis\.com', 'Cloud Run'),
            (r'google_cloudfunctions|cloudfunctions\.googleapis\.com', 'Cloud Functions'),
            (r'google_pubsub|pubsub\.googleapis\.com', 'Cloud Pub/Sub'),
            (r'google_spanner|spanner\.googleapis\.com', 'Cloud Spanner'),
            (r'google_firestore|firestore\.googleapis\.com', 'Cloud Firestore'),
            (r'google_redis_instance|redis\.googleapis\.com', 'Cloud Memorystore'),
            (r'google_vertex_ai|aiplatform\.googleapis\.com', 'Vertex AI'),
            (r'google_kms|cloudkms\.googleapis\.com', 'Cloud KMS'),
        ]
        
        detected_services = []
        for pattern, service_name in service_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                detected_services.append(service_name)
        
        for rp in region_patterns:
            matches = re.findall(rp, content, re.IGNORECASE)
            for region in matches:
                region_base = re.sub(r'-[a-z]$', '', region.lower())
                if region_base in seen_regions:
                    continue
                    
                region_info = self.CLOUD_REGIONS.get(region_base, self.CLOUD_REGIONS.get(region.lower(), {}))
                if not region_info:
                    country = self._detect_country_from_region(region)
                    if country == 'unknown':
                        continue
                else:
                    country = region_info.get('country', 'US')
                
                seen_regions.add(region_base)
                service_desc = ', '.join(detected_services[:3]) if detected_services else 'GCP Infrastructure'
                
                locations.append(DataLocation(
                    region=region_base,
                    country=country,
                    cloud_provider='GCP',
                    service_type=service_desc,
                    is_eu=country in self.EU_COUNTRIES,
                    is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                    legal_jurisdiction=self._get_jurisdiction(country)
                ))
            
        return locations
    
    def _parse_kubernetes_config(self, content: str) -> List[DataLocation]:
        """Parse Kubernetes YAML configuration for data sovereignty locations.
        
        Detects container image origins, external service endpoints, storage classes,
        LoadBalancer annotations, namespace region hints, ingress hostnames,
        topology labels, and Helm chart values.
        """
        locations = []
        seen = set()
        
        def _add_location(region, country, provider, service_type):
            key = (region, country, provider, service_type)
            if key not in seen and country != 'unknown':
                seen.add(key)
                locations.append(DataLocation(
                    region=region,
                    country=country,
                    cloud_provider=provider,
                    service_type=service_type,
                    is_eu=country in self.EU_COUNTRIES,
                    is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                    legal_jurisdiction=self._get_jurisdiction(country)
                ))
        
        region_matches = re.findall(r'topology\.kubernetes\.io/region["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)["\']?', content)
        zone_matches = re.findall(r'topology\.kubernetes\.io/zone["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)["\']?', content)
        for region in region_matches + zone_matches:
            country = self._detect_country_from_region(region)
            _add_location(region, country, 'Kubernetes', 'k8s_topology')
        
        image_registry_map = {
            r'docker\.io/': ('US', 'Docker Hub'),
            r'gcr\.io/': ('US', 'Google Container Registry'),
            r'ghcr\.io/': ('US', 'GitHub Container Registry'),
            r'quay\.io/': ('US', 'Red Hat Quay'),
            r'mcr\.microsoft\.com/': ('US', 'Microsoft Container Registry'),
            r'public\.ecr\.aws/': ('US', 'AWS ECR Public'),
            r'registry\.k8s\.io/': ('US', 'Kubernetes Registry'),
            r'docker\.elastic\.co/': ('US', 'Elastic Registry'),
            r'registry\.hub\.docker\.com/': ('US', 'Docker Hub'),
        }
        
        image_matches = re.findall(r'image\s*:\s*["\']?([^\s"\']+)["\']?', content)
        for image in image_matches:
            matched_registry = False
            for pattern, (country, registry_name) in image_registry_map.items():
                if re.search(pattern, image, re.IGNORECASE):
                    _add_location(registry_name, country, registry_name, 'container_image')
                    matched_registry = True
                    break
            
            if not matched_registry:
                ecr_match = re.search(r'(\d+)\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com', image)
                if ecr_match:
                    ecr_region = ecr_match.group(2)
                    country = self._detect_country_from_region(ecr_region)
                    _add_location(ecr_region, country, 'AWS ECR', 'container_image')
                
                acr_match = re.search(r'([a-z0-9]+)\.azurecr\.io', image, re.IGNORECASE)
                if acr_match:
                    _add_location('Azure ACR', 'US', 'Azure Container Registry', 'container_image')
                
                gar_match = re.search(r'([a-z]+-[a-z0-9]+)-docker\.pkg\.dev', image)
                if gar_match:
                    gar_region = gar_match.group(1)
                    country = self._detect_country_from_region(gar_region)
                    _add_location(gar_region, country, 'Google Artifact Registry', 'container_image')
                
                if not ecr_match and not acr_match and not gar_match and '/' in image and '.' in image.split('/')[0]:
                    _add_location(image.split('/')[0], 'unknown', 'Custom Registry', 'container_image')
        
        env_patterns = [
            r'value\s*:\s*["\']?((?:https?://|postgres(?:ql)?://|mysql://|mongodb(?:\+srv)?://|redis://|amqp://)[^\s"\']+)["\']?',
            r'DATABASE_URL["\']?\s*:\s*["\']?([^\s"\']+)["\']?',
            r'REDIS_URL["\']?\s*:\s*["\']?([^\s"\']+)["\']?',
            r'API_ENDPOINT["\']?\s*:\s*["\']?([^\s"\']+)["\']?',
            r'ELASTICSEARCH_URL["\']?\s*:\s*["\']?([^\s"\']+)["\']?',
        ]
        for pat in env_patterns:
            for endpoint in re.findall(pat, content, re.IGNORECASE):
                for region_key, region_info in self.CLOUD_REGIONS.items():
                    if region_key in endpoint.lower():
                        _add_location(region_key, region_info['country'], 'External Service', 'env_endpoint')
                        break
                else:
                    cloud_hints = [
                        (r'\.rds\.amazonaws\.com', 'US', 'AWS RDS'),
                        (r'\.cache\.amazonaws\.com', 'US', 'AWS ElastiCache'),
                        (r'\.database\.azure\.com', 'US', 'Azure Database'),
                        (r'\.redis\.cache\.windows\.net', 'US', 'Azure Redis'),
                        (r'\.cloudsql\.', 'US', 'GCP Cloud SQL'),
                    ]
                    for hint_pat, hint_country, hint_svc in cloud_hints:
                        if re.search(hint_pat, endpoint, re.IGNORECASE):
                            region_in_endpoint = None
                            for rk in self.CLOUD_REGIONS:
                                if rk in endpoint.lower():
                                    region_in_endpoint = rk
                                    break
                            if region_in_endpoint:
                                _add_location(region_in_endpoint, self.CLOUD_REGIONS[region_in_endpoint]['country'], hint_svc, 'env_endpoint')
                            else:
                                _add_location(hint_svc, hint_country, hint_svc, 'env_endpoint')
                            break
        
        sc_matches = re.findall(r'storageClassName\s*:\s*["\']?([^\s"\']+)["\']?', content)
        for sc in sc_matches:
            sc_lower = sc.lower()
            if any(p in sc_lower for p in ['gp2', 'gp3', 'io1', 'io2', 'ebs']):
                _add_location('AWS EBS', 'US', 'AWS', 'persistent_storage')
            elif any(p in sc_lower for p in ['azure-disk', 'managed-premium', 'azurefile']):
                _add_location('Azure Disk', 'US', 'Azure', 'persistent_storage')
            elif any(p in sc_lower for p in ['pd-standard', 'pd-ssd', 'pd-balanced']):
                _add_location('GCP PD', 'US', 'GCP', 'persistent_storage')
            elif 'hcloud' in sc_lower:
                _add_location('Hetzner Volume', 'DE', 'Hetzner', 'persistent_storage')
        
        if re.search(r'type\s*:\s*LoadBalancer', content):
            lb_annotations = {
                r'service\.beta\.kubernetes\.io/aws-load-balancer': ('AWS', 'US'),
                r'service\.beta\.kubernetes\.io/azure-load-balancer': ('Azure', 'US'),
                r'cloud\.google\.com/load-balancer': ('GCP', 'US'),
                r'load-balancer\.hetzner\.cloud': ('Hetzner', 'DE'),
            }
            for ann_pat, (provider, country) in lb_annotations.items():
                if re.search(ann_pat, content, re.IGNORECASE):
                    _add_location(f'{provider} LB', country, provider, 'load_balancer')
        
        ns_region_patterns = [
            r'namespace.*?region["\']?\s*:\s*["\']?([^"\'}\s]+)["\']?',
            r'annotations.*?region["\']?\s*:\s*["\']?([^"\'}\s]+)["\']?',
        ]
        for pat in ns_region_patterns:
            for match in re.findall(pat, content, re.IGNORECASE | re.DOTALL):
                country = self._detect_country_from_region(match)
                _add_location(match, country, 'Kubernetes', 'namespace_annotation')
        
        ingress_hosts = re.findall(r'host\s*:\s*["\']?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']?', content)
        cdn_patterns = {
            r'\.cloudfront\.net': ('US', 'AWS CloudFront'),
            r'\.akamaized\.net': ('US', 'Akamai CDN'),
            r'\.azureedge\.net': ('US', 'Azure CDN'),
            r'\.cdn\.cloudflare\.net': ('US', 'Cloudflare CDN'),
            r'\.fastly\.net': ('US', 'Fastly CDN'),
        }
        for host in ingress_hosts:
            for cdn_pat, (cdn_country, cdn_name) in cdn_patterns.items():
                if re.search(cdn_pat, host, re.IGNORECASE):
                    _add_location(cdn_name, cdn_country, cdn_name, 'ingress_cdn')
                    break
        
        helm_region_patterns = [
            r'global\.region\s*:\s*["\']?([^"\'}\s]+)["\']?',
            r'global\.cloud\.region\s*:\s*["\']?([^"\'}\s]+)["\']?',
            r'\.Values\.global\.region["\s}]',
            r'global:\s*\n\s+region\s*:\s*["\']?([^"\'}\s]+)["\']?',
            r'global:\s*\n\s+cloud:\s*\n\s+region\s*:\s*["\']?([^"\'}\s]+)["\']?',
        ]
        for pat in helm_region_patterns:
            for match in re.findall(pat, content, re.IGNORECASE):
                if match:
                    country = self._detect_country_from_region(match)
                    _add_location(match, country, 'Helm', 'helm_global_region')
        
        helm_sc_matches = re.findall(
            r'(?:persistence\.storageClass|persistence:\s*\n\s+storageClass)\s*:\s*["\']?([^\s"\']+)["\']?',
            content, re.IGNORECASE
        )
        for sc in helm_sc_matches:
            sc_lower = sc.lower()
            if any(p in sc_lower for p in ['gp2', 'gp3', 'ebs']):
                _add_location('AWS EBS (Helm)', 'US', 'AWS', 'helm_storage')
            elif any(p in sc_lower for p in ['azure', 'managed']):
                _add_location('Azure (Helm)', 'US', 'Azure', 'helm_storage')
            elif any(p in sc_lower for p in ['pd-', 'standard']):
                _add_location('GCP (Helm)', 'US', 'GCP', 'helm_storage')
        
        helm_image_repos = re.findall(
            r'(?:image\.repository|image:\s*\n\s+repository)\s*:\s*["\']?([^\s"\']+)["\']?',
            content, re.IGNORECASE
        )
        for repo in helm_image_repos:
            for pattern, (country, registry_name) in image_registry_map.items():
                if re.search(pattern, repo, re.IGNORECASE):
                    _add_location(registry_name + ' (Helm)', country, registry_name, 'helm_image')
                    break
        
        helm_ingress_hosts = re.findall(
            r'(?:ingress\.hosts|ingress:\s*\n\s+hosts)\s*:\s*\n?\s*-\s*["\']?([a-zA-Z0-9.-]+)["\']?',
            content, re.IGNORECASE
        )
        for host in helm_ingress_hosts:
            for cdn_pat, (cdn_country, cdn_name) in cdn_patterns.items():
                if re.search(cdn_pat, host, re.IGNORECASE):
                    _add_location(cdn_name + ' (Helm)', cdn_country, cdn_name, 'helm_ingress')
                    break
        
        helm_ext_db = re.findall(
            r'(?:externalDatabase\.host|externalDatabase:\s*\n\s+host)\s*:\s*["\']?([^\s"\']+)["\']?',
            content, re.IGNORECASE
        )
        for db_host in helm_ext_db:
            for region_key, region_info in self.CLOUD_REGIONS.items():
                if region_key in db_host.lower():
                    _add_location(region_key, region_info['country'], 'External DB (Helm)', 'helm_external_db')
                    break
        
        return locations
    
    def _detect_kubernetes_flows(self, content: str) -> List[DataFlow]:
        """Detect data flows from Kubernetes configurations.
        
        Identifies external service endpoints, database connection strings in env vars,
        and ingress to external backends.
        """
        flows = []
        base_country = self._get_country_from_region(self.region)
        seen_flows = set()
        
        endpoint_patterns = [
            r'value\s*:\s*["\']?((?:https?://|postgres(?:ql)?://|mysql://|mongodb(?:\+srv)?://|redis://|amqp://)[^\s"\']+)["\']?',
        ]
        for pat in endpoint_patterns:
            for endpoint in re.findall(pat, content, re.IGNORECASE):
                dest_country = 'unknown'
                dest_name = endpoint[:80]
                for region_key, region_info in self.CLOUD_REGIONS.items():
                    if region_key in endpoint.lower():
                        dest_country = region_info['country']
                        dest_name = f"{region_info['name']} ({region_key})"
                        break
                
                if dest_country == 'unknown':
                    cloud_svc = [
                        (r'\.amazonaws\.com', 'US', 'AWS Service'),
                        (r'\.azure\.com|\.windows\.net', 'US', 'Azure Service'),
                        (r'\.googleapis\.com', 'US', 'GCP Service'),
                    ]
                    for svc_pat, svc_country, svc_name in cloud_svc:
                        if re.search(svc_pat, endpoint, re.IGNORECASE):
                            dest_country = svc_country
                            dest_name = svc_name
                            break
                
                if dest_country != 'unknown':
                    flow_key = (base_country, dest_country, dest_name)
                    if flow_key not in seen_flows:
                        seen_flows.add(flow_key)
                        flows.append(DataFlow(
                            source=f"{self.region} (K8s Cluster)",
                            destination=dest_name,
                            source_country=base_country,
                            destination_country=dest_country,
                            is_cross_border=dest_country != base_country,
                            is_eu_to_third_country=(base_country in self.EU_COUNTRIES and
                                                    dest_country not in self.EU_COUNTRIES and
                                                    dest_country not in self.EEA_COUNTRIES and
                                                    dest_country not in self.ADEQUACY_COUNTRIES),
                            flow_type="k8s_external_service",
                            data_types=["application_data"]
                        ))
        
        if re.search(r'kind\s*:\s*Ingress', content, re.IGNORECASE):
            backend_matches = re.findall(r'host\s*:\s*["\']?([a-zA-Z0-9.-]+)["\']?', content)
            for host in backend_matches:
                if '.' in host and not host.endswith('.local') and not host.endswith('.cluster.local'):
                    flows.append(DataFlow(
                        source="Internet (Ingress)",
                        destination=f"{self.region} (K8s Cluster)",
                        source_country="global",
                        destination_country=base_country,
                        is_cross_border=True,
                        is_eu_to_third_country=False,
                        flow_type="k8s_ingress",
                        data_types=["user_request_data"]
                    ))
                    break
        
        image_registry_flows = {
            r'gcr\.io/': ('US', 'Google Container Registry'),
            r'docker\.io/': ('US', 'Docker Hub'),
            r'ghcr\.io/': ('US', 'GitHub Container Registry'),
            r'quay\.io/': ('US', 'Red Hat Quay'),
            r'mcr\.microsoft\.com/': ('US', 'Microsoft Container Registry'),
            r'public\.ecr\.aws/': ('US', 'AWS ECR Public'),
            r'registry\.eu-central-1': ('DE', 'EU Registry'),
            r'registry\.eu-west-1': ('IE', 'EU Registry'),
        }
        for pattern, (registry_country, registry_name) in image_registry_flows.items():
            if re.search(pattern, content, re.IGNORECASE):
                if registry_country != base_country:
                    flow_key = (base_country, registry_country, registry_name)
                    if flow_key not in seen_flows:
                        seen_flows.add(flow_key)
                        flows.append(DataFlow(
                            source=registry_name,
                            destination=f"{self.region} (K8s Cluster)",
                            source_country=registry_country,
                            destination_country=base_country,
                            is_cross_border=True,
                            is_eu_to_third_country=False,
                            flow_type="container_image_pull",
                            data_types=["container_images", "application_artifacts"]
                        ))
        
        return flows
    
    def _detect_kubernetes_access(self, content: str) -> List[AccessPath]:
        """Detect access patterns from Kubernetes configurations.
        
        Identifies ServiceAccount usage, RBAC roles, network policies,
        and ingress from internet.
        """
        paths = []
        base_country = self._get_country_from_region(self.region)
        is_eu = base_country in self.EU_COUNTRIES
        
        sa_matches = re.findall(r'serviceAccountName\s*:\s*["\']?([^\s"\']+)["\']?', content)
        for sa in sa_matches:
            paths.append(AccessPath(
                accessor_type="ServiceAccount",
                accessor_country=base_country,
                privilege_level="service",
                is_eu_access=is_eu,
                is_monitored=True,
                accessor_name=sa
            ))
        
        if re.search(r'kind\s*:\s*(?:ClusterRole|Role)\b', content, re.IGNORECASE):
            is_cluster_role = bool(re.search(r'kind\s*:\s*ClusterRole\b', content, re.IGNORECASE))
            paths.append(AccessPath(
                accessor_type="RBAC Role" if not is_cluster_role else "RBAC ClusterRole",
                accessor_country=base_country,
                privilege_level="admin" if is_cluster_role else "namespace",
                is_eu_access=is_eu,
                is_monitored=True,
                accessor_name="Cluster RBAC"
            ))
        
        if re.search(r'kind\s*:\s*NetworkPolicy', content, re.IGNORECASE):
            paths.append(AccessPath(
                accessor_type="NetworkPolicy",
                accessor_country=base_country,
                privilege_level="network",
                is_eu_access=is_eu,
                is_monitored=True,
                accessor_name="K8s Network Policy"
            ))
        
        if re.search(r'kind\s*:\s*Ingress', content, re.IGNORECASE):
            paths.append(AccessPath(
                accessor_type="Ingress",
                accessor_country="global",
                privilege_level="read",
                is_eu_access=False,
                is_monitored=bool(re.search(r'nginx\.ingress\.kubernetes\.io/enable-access-log', content, re.IGNORECASE)),
                accessor_name="Internet Ingress"
            ))
        
        if re.search(r'type\s*:\s*LoadBalancer', content):
            paths.append(AccessPath(
                accessor_type="LoadBalancer",
                accessor_country="global",
                privilege_level="read",
                is_eu_access=False,
                is_monitored=False,
                accessor_name="Public LoadBalancer"
            ))
        
        return paths
    
    def _analyze_kubernetes_origins(self, content: str) -> List[DataOrigin]:
        """Detect data origins from Kubernetes configurations.
        
        Identifies container registries, external APIs referenced in env vars,
        and mounted secrets/configmaps.
        """
        origins = []
        base_country = self._get_country_from_region(self.region)
        is_eu = base_country in self.EU_COUNTRIES
        
        registry_origins = {
            r'docker\.io|registry\.hub\.docker\.com': ('Docker Hub', 'US'),
            r'gcr\.io|pkg\.dev': ('Google Container Registry', 'US'),
            r'ghcr\.io': ('GitHub Container Registry', 'US'),
            r'quay\.io': ('Red Hat Quay', 'US'),
            r'mcr\.microsoft\.com': ('Microsoft Container Registry', 'US'),
            r'public\.ecr\.aws': ('AWS ECR Public', 'US'),
            r'registry\.k8s\.io': ('Kubernetes Registry', 'US'),
        }
        
        images = re.findall(r'image\s*:\s*["\']?([^\s"\']+)["\']?', content)
        seen_registries = set()
        for image in images:
            for pat, (name, country) in registry_origins.items():
                if re.search(pat, image, re.IGNORECASE) and name not in seen_registries:
                    seen_registries.add(name)
                    origins.append(DataOrigin(
                        source_name=name,
                        source_type="container_registry",
                        country=country,
                        collection_method="Container Image Pull",
                        legal_basis="Legitimate Interest (Art. 6(1)(f))",
                        data_categories=["application_artifacts", "container_images"],
                        is_eu_origin=country in self.EU_COUNTRIES
                    ))
                    break
            else:
                ecr_match = re.search(r'\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com', image)
                if ecr_match:
                    ecr_region = ecr_match.group(1)
                    ecr_country = self._detect_country_from_region(ecr_region)
                    origin_name = f"AWS ECR ({ecr_region})"
                    if origin_name not in seen_registries:
                        seen_registries.add(origin_name)
                        origins.append(DataOrigin(
                            source_name=origin_name,
                            source_type="container_registry",
                            country=ecr_country,
                            collection_method="Container Image Pull",
                            legal_basis="Legitimate Interest (Art. 6(1)(f))",
                            data_categories=["application_artifacts"],
                            is_eu_origin=ecr_country in self.EU_COUNTRIES
                        ))
        
        api_endpoints = re.findall(r'value\s*:\s*["\']?(https?://[^\s"\']+)["\']?', content, re.IGNORECASE)
        seen_apis = set()
        internal_service_patterns = re.compile(
            r'^https?://[a-z0-9-]+:\d+$|'
            r'^https?://[a-z0-9-]+\.[a-z0-9-]+\.svc(\.cluster\.local)?|'
            r'^https?://localhost|'
            r'^https?://127\.0\.0\.',
            re.IGNORECASE
        )
        for endpoint in api_endpoints:
            if internal_service_patterns.search(endpoint):
                continue
            api_host = endpoint.split('/')[2] if len(endpoint.split('/')) > 2 else endpoint
            if api_host not in seen_apis:
                seen_apis.add(api_host)
                api_country = 'unknown'
                for region_key, region_info in self.CLOUD_REGIONS.items():
                    if region_key in endpoint.lower():
                        api_country = region_info['country']
                        break
                if api_country == 'unknown':
                    api_country = base_country
                origins.append(DataOrigin(
                    source_name=f"External API ({api_host})",
                    source_type="api",
                    country=api_country,
                    collection_method="HTTP API Call",
                    legal_basis="Contract (Art. 6(1)(b))",
                    data_categories=["api_data"],
                    is_eu_origin=api_country in self.EU_COUNTRIES
                ))
        
        if re.search(r'secretKeyRef|secretRef|kind\s*:\s*Secret', content, re.IGNORECASE):
            origins.append(DataOrigin(
                source_name="Kubernetes Secrets",
                source_type="secret_store",
                country=base_country,
                collection_method="K8s Secret Mount/Ref",
                legal_basis="Legitimate Interest (Art. 6(1)(f))",
                data_categories=["credentials", "secrets"],
                is_eu_origin=is_eu
            ))
        
        if re.search(r'configMapKeyRef|configMapRef|kind\s*:\s*ConfigMap', content, re.IGNORECASE):
            origins.append(DataOrigin(
                source_name="Kubernetes ConfigMaps",
                source_type="configuration",
                country=base_country,
                collection_method="K8s ConfigMap Mount/Ref",
                legal_basis="Legitimate Interest (Art. 6(1)(f))",
                data_categories=["configuration_data"],
                is_eu_origin=is_eu
            ))
        
        if not origins:
            origins.append(DataOrigin(
                source_name="Kubernetes Cluster",
                source_type="cloud_infrastructure",
                country=base_country,
                collection_method="Container Orchestration",
                legal_basis="Legitimate Interest (Art. 6(1)(f))",
                data_categories=["operational_data"],
                is_eu_origin=is_eu
            ))
        
        return origins
    
    def _parse_docker_compose(self, content: str) -> List[DataLocation]:
        """Parse docker-compose.yml for data sovereignty locations.
        
        Detects image origins, external volume mounts, network endpoints,
        and environment variables with URLs/regions.
        """
        locations = []
        seen = set()
        
        def _add(region, country, provider, service_type):
            key = (region, country, provider, service_type)
            if key not in seen and country != 'unknown':
                seen.add(key)
                locations.append(DataLocation(
                    region=region,
                    country=country,
                    cloud_provider=provider,
                    service_type=service_type,
                    is_eu=country in self.EU_COUNTRIES,
                    is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                    legal_jurisdiction=self._get_jurisdiction(country)
                ))
        
        image_registry_map = {
            r'docker\.io/': ('US', 'Docker Hub'),
            r'gcr\.io/': ('US', 'Google Container Registry'),
            r'ghcr\.io/': ('US', 'GitHub Container Registry'),
            r'quay\.io/': ('US', 'Red Hat Quay'),
            r'mcr\.microsoft\.com/': ('US', 'Microsoft Container Registry'),
            r'public\.ecr\.aws/': ('US', 'AWS ECR Public'),
        }
        
        image_matches = re.findall(r'image\s*:\s*["\']?([^\s"\']+)["\']?', content)
        for image in image_matches:
            for pattern, (country, registry_name) in image_registry_map.items():
                if re.search(pattern, image, re.IGNORECASE):
                    _add(registry_name, country, registry_name, 'docker_compose_image')
                    break
            else:
                ecr_match = re.search(r'\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com', image)
                if ecr_match:
                    ecr_region = ecr_match.group(1)
                    country = self._detect_country_from_region(ecr_region)
                    _add(ecr_region, country, 'AWS ECR', 'docker_compose_image')
        
        env_url_patterns = [
            r'(?:DATABASE_URL|REDIS_URL|MONGO_URL|ELASTICSEARCH_URL|API_URL|BROKER_URL)\s*[:=]\s*["\']?([^\s"\']+)["\']?',
            r'(?:https?://|postgres(?:ql)?://|mysql://|mongodb(?:\+srv)?://|redis://|amqp://)[^\s"\']+',
        ]
        for pat in env_url_patterns:
            for endpoint in re.findall(pat, content, re.IGNORECASE):
                for region_key, region_info in self.CLOUD_REGIONS.items():
                    if region_key in endpoint.lower():
                        _add(region_key, region_info['country'], 'External Service', 'docker_compose_env')
                        break
        
        region_env_patterns = [
            r'(?:AWS_REGION|AWS_DEFAULT_REGION|REGION|CLOUD_REGION)\s*[:=]\s*["\']?([a-zA-Z0-9-]+)["\']?',
        ]
        for pat in region_env_patterns:
            for region in re.findall(pat, content, re.IGNORECASE):
                country = self._detect_country_from_region(region)
                _add(region, country, 'Cloud', 'docker_compose_region')
        
        volume_patterns = re.findall(r'volumes\s*:\s*\n(?:\s+-\s*[^\n]+\n?)+', content, re.IGNORECASE)
        for vol_block in volume_patterns:
            if re.search(r'nfs|cifs|s3|azure|gcs', vol_block, re.IGNORECASE):
                if 's3' in vol_block.lower():
                    _add('AWS S3 Volume', 'US', 'AWS', 'docker_volume')
                elif 'azure' in vol_block.lower():
                    _add('Azure Volume', 'US', 'Azure', 'docker_volume')
                elif 'gcs' in vol_block.lower():
                    _add('GCS Volume', 'US', 'GCP', 'docker_volume')
        
        return locations
    
    def _parse_dockerfile(self, content: str) -> List[DataLocation]:
        """Parse Dockerfile for data sovereignty locations.
        
        Detects FROM image origins (registry country) and ENV with region/endpoint hints.
        """
        locations = []
        seen = set()
        
        def _add(region, country, provider, service_type):
            key = (region, country, provider, service_type)
            if key not in seen and country != 'unknown':
                seen.add(key)
                locations.append(DataLocation(
                    region=region,
                    country=country,
                    cloud_provider=provider,
                    service_type=service_type,
                    is_eu=country in self.EU_COUNTRIES,
                    is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                    legal_jurisdiction=self._get_jurisdiction(country)
                ))
        
        from_images = re.findall(r'^FROM\s+([^\s]+)', content, re.MULTILINE | re.IGNORECASE)
        image_registry_map = {
            r'docker\.io/': ('US', 'Docker Hub'),
            r'gcr\.io/': ('US', 'Google Container Registry'),
            r'ghcr\.io/': ('US', 'GitHub Container Registry'),
            r'quay\.io/': ('US', 'Red Hat Quay'),
            r'mcr\.microsoft\.com/': ('US', 'Microsoft Container Registry'),
            r'public\.ecr\.aws/': ('US', 'AWS ECR Public'),
        }
        
        for image in from_images:
            matched = False
            for pattern, (country, registry_name) in image_registry_map.items():
                if re.search(pattern, image, re.IGNORECASE):
                    _add(registry_name, country, registry_name, 'dockerfile_from')
                    matched = True
                    break
            if not matched:
                ecr_match = re.search(r'\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com', image)
                if ecr_match:
                    ecr_region = ecr_match.group(1)
                    country = self._detect_country_from_region(ecr_region)
                    _add(ecr_region, country, 'AWS ECR', 'dockerfile_from')
                elif '/' not in image or '.' not in image.split('/')[0]:
                    _add('Docker Hub (implicit)', 'US', 'Docker Hub', 'dockerfile_from')
        
        env_patterns = re.findall(r'^ENV\s+(\S+)\s+(.+)$', content, re.MULTILINE | re.IGNORECASE)
        for key, value in env_patterns:
            key_upper = key.upper()
            if key_upper in ('AWS_REGION', 'AWS_DEFAULT_REGION', 'REGION', 'CLOUD_REGION'):
                country = self._detect_country_from_region(value.strip().strip('"').strip("'"))
                _add(value.strip(), country, 'Cloud', 'dockerfile_env_region')
            
            value_clean = value.strip().strip('"').strip("'")
            for region_key, region_info in self.CLOUD_REGIONS.items():
                if region_key in value_clean.lower():
                    _add(region_key, region_info['country'], 'Cloud', 'dockerfile_env')
                    break
        
        return locations
    
    def _run_nis2_compliance_checks(self, content: str, result: SovereigntyScanResult) -> List[ComplianceCheck]:
        """Run NIS2 Directive compliance checks.
        
        Checks incident reporting readiness, supply chain security, encryption requirements,
        access control/authentication, business continuity, and network security monitoring
        per the EU NIS2 Directive (Directive (EU) 2022/2555).
        """
        checks = []
        content_lower = content.lower()
        
        has_incident_reporting = bool(re.search(
            r'incident[_\-\s]?report|alert[_\-\s]?manager|pagerduty|opsgenie|csirt|siem|'
            r'notification[_\-\s]?channel|slack[_\-\s]?webhook|sns[_\-\s]?topic|'
            r'event[_\-\s]?bridge|cloud[_\-\s]?watch[_\-\s]?alarm',
            content_lower
        ))
        checks.append(ComplianceCheck(
            check_name="NIS2 Incident Reporting Readiness",
            check_category="nis2_incident",
            status="pass" if has_incident_reporting else "fail",
            description="Incident reporting/alerting configuration detected" if has_incident_reporting else "No incident reporting mechanism found - NIS2 requires 24h early warning + 72h full notification to CSIRT",
            legal_reference="NIS2 Directive Art. 23 (Incident Reporting), Art. 23(4)(a-b)",
            recommendation="" if has_incident_reporting else "Implement automated incident alerting with 24h early warning and 72h full notification capabilities to national CSIRT"
        ))
        
        has_supply_chain = bool(re.search(
            r'dependab|renovate|snyk|trivy|grype|clair|vulnerability[_\-\s]?scan|'
            r'sbom|software[_\-\s]?bill|supply[_\-\s]?chain|'
            r'sub[_\-\s]?processor|third[_\-\s]?party|vendor[_\-\s]?management',
            content_lower
        ))
        checks.append(ComplianceCheck(
            check_name="NIS2 Supply Chain Security",
            check_category="nis2_supply_chain",
            status="pass" if has_supply_chain else "warning",
            description="Supply chain security controls detected" if has_supply_chain else "No supply chain security controls found",
            legal_reference="NIS2 Directive Art. 21(2)(d) (Supply Chain Security)",
            recommendation="" if has_supply_chain else "Implement dependency scanning, SBOM generation, and third-party vendor risk assessments"
        ))
        
        has_encryption = bool(re.search(
            r'encrypt|kms|tls|ssl|certificate|aes|rsa|cmk|customer[_\-\s]?managed[_\-\s]?key|'
            r'key[_\-\s]?vault|secret[_\-\s]?manager|hashicorp[_\-\s]?vault',
            content_lower
        ))
        checks.append(ComplianceCheck(
            check_name="NIS2 Encryption & Cryptography",
            check_category="nis2_encryption",
            status="pass" if has_encryption else "fail",
            description="Encryption/cryptography measures detected" if has_encryption else "No encryption or cryptographic controls found",
            legal_reference="NIS2 Directive Art. 21(2)(e) (Cryptography & Encryption)",
            recommendation="" if has_encryption else "Implement encryption at rest (AES-256) and in transit (TLS 1.2+), with proper key management"
        ))
        
        has_access_control = bool(re.search(
            r'mfa|multi[_\-\s]?factor|two[_\-\s]?factor|2fa|totp|'
            r'iam|rbac|role[_\-\s]?based|least[_\-\s]?privilege|'
            r'identity[_\-\s]?provider|oauth|saml|oidc|sso|'
            r'access[_\-\s]?control|access[_\-\s]?policy|'
            r'cognito|active[_\-\s]?directory|keycloak',
            content_lower
        ))
        checks.append(ComplianceCheck(
            check_name="NIS2 Access Control & Authentication",
            check_category="nis2_access_control",
            status="pass" if has_access_control else "warning",
            description="Access control and authentication mechanisms detected" if has_access_control else "No explicit MFA/RBAC/IAM configuration found",
            legal_reference="NIS2 Directive Art. 21(2)(i) (MFA, Access Control)",
            recommendation="" if has_access_control else "Implement MFA for all privileged access, RBAC with least-privilege principle, and centralized identity management"
        ))
        
        has_continuity = bool(re.search(
            r'backup|disaster[_\-\s]?recovery|business[_\-\s]?continuity|'
            r'replicat|failover|auto[_\-\s]?scaling|high[_\-\s]?availability|'
            r'snapshot|recovery[_\-\s]?point|rpo|rto|'
            r'availability[_\-\s]?zone|multi[_\-\s]?az',
            content_lower
        ))
        checks.append(ComplianceCheck(
            check_name="NIS2 Business Continuity & Backup",
            check_category="nis2_continuity",
            status="pass" if has_continuity else "warning",
            description="Business continuity/backup mechanisms detected" if has_continuity else "No backup or disaster recovery configuration found",
            legal_reference="NIS2 Directive Art. 21(2)(c) (Business Continuity & Crisis Management)",
            recommendation="" if has_continuity else "Implement automated backups, define RPO/RTO targets, and establish disaster recovery procedures"
        ))
        
        has_monitoring = bool(re.search(
            r'cloudwatch|cloudtrail|monitor|log[_\-\s]?analytics|'
            r'application[_\-\s]?insights|stackdriver|datadog|'
            r'prometheus|grafana|elastic[_\-\s]?search|kibana|'
            r'network[_\-\s]?policy|firewall|waf|ids|ips|'
            r'security[_\-\s]?group|nacl|nsg',
            content_lower
        ))
        checks.append(ComplianceCheck(
            check_name="NIS2 Network Security Monitoring",
            check_category="nis2_monitoring",
            status="pass" if has_monitoring else "warning",
            description="Network security monitoring detected" if has_monitoring else "No network monitoring or security controls found",
            legal_reference="NIS2 Directive Art. 21(2)(b) (Incident Handling), Art. 21(2)(g) (Network Security)",
            recommendation="" if has_monitoring else "Deploy network monitoring (IDS/IPS), web application firewall (WAF), and centralized log analysis (SIEM)"
        ))
        
        return checks
    
    def _parse_generic_config(self, content: str) -> List[DataLocation]:
        """Parse generic configuration for locations with auto-detection"""
        locations = []
        seen_regions = set()
        
        provider = self._detect_terraform_provider(content)
        if provider != 'Unknown':
            if provider == 'AWS':
                return self._parse_aws_config(content)
            elif provider == 'Azure':
                return self._parse_azure_config(content)
            elif provider == 'GCP':
                return self._parse_gcp_config(content)
        
        generic_patterns = [
            r'region\s*[:=]\s*["\']([a-zA-Z0-9-]+)["\']',
            r'location\s*[:=]\s*["\']([a-zA-Z0-9-]+)["\']',
            r'datacenter\s*[:=]\s*["\']([a-zA-Z0-9-]+)["\']',
            r'zone\s*[:=]\s*["\']([a-zA-Z0-9-]+)["\']'
        ]
        
        for pattern in generic_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                match_lower = match.lower().strip()
                if match_lower in seen_regions or len(match_lower) < 3:
                    continue
                    
                region_info = self.CLOUD_REGIONS.get(match_lower, {})
                if region_info:
                    country = region_info['country']
                else:
                    country = self._detect_country_from_region(match)
                    if country == 'unknown':
                        continue
                
                seen_regions.add(match_lower)
                locations.append(DataLocation(
                    region=match,
                    country=country,
                    cloud_provider=provider if provider != 'Unknown' else 'Cloud',
                    service_type='Cloud Infrastructure',
                    is_eu=country in self.EU_COUNTRIES,
                    is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                    legal_jurisdiction=self._get_jurisdiction(country)
                ))
                
        return locations
    
    def _detect_config_flows(self, content: str, config_type: str) -> List[DataFlow]:
        """Detect data flows from configuration"""
        flows = []
        
        replication_keywords = ['replica', 'backup', 'mirror', 'sync', 'copy', 'transfer']
        
        for keyword in replication_keywords:
            if keyword in content.lower():
                flows.append(DataFlow(
                    source="primary",
                    destination="replica",
                    source_country="NL",
                    destination_country="unknown",
                    is_cross_border=False,
                    flow_type="replication"
                ))
                break
                
        return flows
    
    def _detect_config_access(self, content: str, config_type: str) -> List[AccessPath]:
        """Detect access patterns from configuration"""
        paths = []
        
        if 'public' in content.lower() or 'internet' in content.lower():
            paths.append(AccessPath(
                accessor_type="public",
                accessor_country="global",
                privilege_level="read",
                is_eu_access=False,
                is_monitored=False
            ))
            
        return paths
    
    def _detect_country_from_region(self, region: str) -> str:
        """Detect country code from region name"""
        region_lower = region.lower()
        
        region_info = self.CLOUD_REGIONS.get(region_lower)
        if region_info:
            return region_info['country']
        
        country_hints = {
            'eu-': 'EU', 'europe': 'EU', 'frankfurt': 'DE', 'amsterdam': 'NL',
            'netherlands': 'NL', 'ireland': 'IE', 'paris': 'FR', 'london': 'GB',
            'stockholm': 'SE', 'milan': 'IT', 'us-': 'US', 'america': 'US',
            'virginia': 'US', 'oregon': 'US', 'ohio': 'US', 'california': 'US',
            'asia': 'SG', 'singapore': 'SG', 'tokyo': 'JP', 'sydney': 'AU',
            'canada': 'CA', 'brazil': 'BR', 'india': 'IN', 'mumbai': 'IN',
            'falkenstein': 'DE', 'nuremberg': 'DE', 'helsinki': 'FI',
            'ashburn': 'US', 'gravelines': 'FR', 'strasbourg': 'FR',
            'roubaix': 'FR', 'beauharnois': 'CA', 'warsaw': 'PL',
            'newark': 'US', 'las vegas': 'US', 'berlin': 'DE',
            'vitoria': 'ES', 'hetzner': 'DE', 'ovh': 'FR', 'scaleway': 'FR',
            'digitalocean': 'US', 'transip': 'NL', 'ionos': 'DE'
        }
        
        for hint, country in country_hints.items():
            if hint in region_lower:
                if country == 'EU':
                    return 'NL'
                return country
                
        return 'unknown'
    
    def _detect_country_from_service(self, service: str) -> str:
        """Detect country from service name/URL"""
        service_lower = service.lower()
        
        if any(p in service_lower for p in self.CLOUD_ACT_RISK_PROVIDERS):
            for region, info in self.CLOUD_REGIONS.items():
                if region in service_lower:
                    return info['country']
            return 'US'
        
        return 'NL'
    
    def _get_jurisdiction(self, country: str) -> str:
        """Get legal jurisdiction for a country"""
        if country in self.EU_COUNTRIES:
            return "EU/GDPR"
        elif country in self.EEA_COUNTRIES:
            return "EEA/GDPR"
        elif country in self.ADEQUACY_COUNTRIES:
            return f"Adequacy Decision ({country})"
        elif country == 'US':
            return "US (CLOUD Act Risk)"
        else:
            return f"Third Country ({country})"
    
    def _analyze_data_origins(self, config: Dict[str, Any]) -> List[DataOrigin]:
        """Analyze where data originates from"""
        origins = []
        data_sources = config.get('data_sources', [])
        
        for source in data_sources:
            country = source.get('country', 'Unknown')
            origins.append(DataOrigin(
                source_name=source.get('name', 'Unknown Source'),
                source_type=source.get('type', 'external_service'),
                country=country,
                collection_method=source.get('collection_method', 'API'),
                legal_basis=source.get('legal_basis', 'Consent'),
                data_categories=source.get('categories', ['personal_data']),
                is_eu_origin=country in self.EU_COUNTRIES or country in self.EEA_COUNTRIES
            ))
        
        if not origins:
            origins.append(DataOrigin(
                source_name="Primary Application",
                source_type="user_input",
                country=self._get_country_from_region(self.region),
                collection_method="Direct Collection",
                legal_basis="Consent (Art. 6(1)(a))",
                data_categories=["personal_data"],
                is_eu_origin=True
            ))
        
        return origins
    
    def _analyze_terraform_origins(self, content: str) -> List[DataOrigin]:
        """Analyze data origins from Terraform configuration"""
        origins = []
        content_lower = content.lower()
        provider = self._detect_terraform_provider(content)
        
        primary_region = "Unknown"
        region_match = re.search(r'region\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
        if region_match:
            primary_region = region_match.group(1)
        
        primary_country = self._detect_country_from_region(primary_region)
        is_eu = primary_country in self.EU_COUNTRIES
        
        origin_patterns = [
            {
                'patterns': [r'api[_\-]?gateway', r'aws_apigateway', r'azurerm_api_management', r'google_api_gateway'],
                'name': f'{provider} API Gateway',
                'type': 'api',
                'method': 'REST/HTTP API',
                'legal_basis': 'Contract (Art. 6(1)(b))',
                'categories': ['personal_data', 'request_data']
            },
            {
                'patterns': [r'aws_rds_', r'aws_db_instance', r'dynamodb', r'aurora', r'postgres', r'mysql', r'azurerm_sql_', r'azurerm_cosmosdb', r'google_sql_'],
                'name': f'{provider} Database Service',
                'type': 'database',
                'method': 'Database Storage & Processing',
                'legal_basis': 'Contract (Art. 6(1)(b))',
                'categories': ['personal_data', 'operational_data', 'transactional_data']
            },
            {
                'patterns': [r'aws_s3_bucket', r's3_bucket', r'azurerm_storage_', r'google_storage_bucket', r'blob_storage'],
                'name': f'{provider} Object Storage',
                'type': 'file_upload',
                'method': 'File Upload / Object Storage',
                'legal_basis': 'Consent (Art. 6(1)(a))',
                'categories': ['personal_data', 'documents', 'media']
            },
            {
                'patterns': [r'aws_lambda', r'azurerm_function_app', r'google_cloudfunctions'],
                'name': f'{provider} Serverless Functions',
                'type': 'compute',
                'method': 'Serverless Processing',
                'legal_basis': 'Contract (Art. 6(1)(b))',
                'categories': ['personal_data', 'processed_data']
            },
            {
                'patterns': [r'aws_sqs_', r'aws_sns_', r'aws_kinesis', r'azurerm_servicebus', r'google_pubsub'],
                'name': f'{provider} Message Queue/Stream',
                'type': 'messaging',
                'method': 'Event Streaming',
                'legal_basis': 'Legitimate Interest (Art. 6(1)(f))',
                'categories': ['event_data', 'operational_data']
            },
            {
                'patterns': [r'aws_cognito', r'azurerm_active_directory', r'google_identity'],
                'name': f'{provider} Identity Service',
                'type': 'authentication',
                'method': 'User Authentication',
                'legal_basis': 'Contract (Art. 6(1)(b))',
                'categories': ['personal_data', 'identity_data', 'credentials']
            },
            {
                'patterns': [r'aws_cloudwatch', r'aws_cloudtrail', r'azurerm_monitor_', r'google_logging'],
                'name': f'{provider} Logging/Monitoring',
                'type': 'monitoring',
                'method': 'System Monitoring',
                'legal_basis': 'Legitimate Interest (Art. 6(1)(f))',
                'categories': ['log_data', 'telemetry', 'operational_data']
            },
            {
                'patterns': [r'aws_instance', r'aws_ec2_', r'aws_ecs_', r'aws_eks_', r'azurerm_virtual_machine', r'azurerm_kubernetes_', r'google_compute_'],
                'name': f'{provider} Compute Service',
                'type': 'compute',
                'method': 'Server/Container Processing',
                'legal_basis': 'Contract (Art. 6(1)(b))',
                'categories': ['application_data', 'operational_data']
            },
            {
                'patterns': [r'azurerm_data_factory', r'azurerm_synapse_', r'azurerm_databricks_'],
                'name': f'{provider} Data Analytics',
                'type': 'analytics',
                'method': 'Data Analytics & ETL',
                'legal_basis': 'Legitimate Interest (Art. 6(1)(f))',
                'categories': ['operational_data', 'analytics_data', 'aggregated_data']
            },
            {
                'patterns': [r'azurerm_key_vault', r'google_kms_', r'google_secret_manager'],
                'name': f'{provider} Key/Secret Management',
                'type': 'security',
                'method': 'Key & Secret Management',
                'legal_basis': 'Legitimate Interest (Art. 6(1)(f))',
                'categories': ['encryption_keys', 'secrets', 'certificates']
            },
            {
                'patterns': [r'azurerm_redis_cache', r'aws_elasticache', r'google_redis_instance'],
                'name': f'{provider} Cache Service',
                'type': 'cache',
                'method': 'In-Memory Caching',
                'legal_basis': 'Contract (Art. 6(1)(b))',
                'categories': ['session_data', 'cached_data', 'temporary_data']
            },
            {
                'patterns': [r'azurerm_cognitive_account', r'google_vertex_ai', r'aws_sagemaker', r'azurerm_machine_learning'],
                'name': f'{provider} AI/ML Service',
                'type': 'ai_ml',
                'method': 'AI/ML Processing',
                'legal_basis': 'Consent (Art. 6(1)(a))',
                'categories': ['training_data', 'inference_data', 'model_data']
            },
            {
                'patterns': [r'azurerm_container_registry', r'google_artifact_registry', r'aws_ecr_'],
                'name': f'{provider} Container Registry',
                'type': 'container_registry',
                'method': 'Container Image Storage',
                'legal_basis': 'Legitimate Interest (Art. 6(1)(f))',
                'categories': ['application_artifacts', 'container_images']
            }
        ]
        
        for origin_def in origin_patterns:
            matched = False
            for pattern in origin_def['patterns']:
                if re.search(pattern, content_lower):
                    matched = True
                    break
            
            if matched:
                origins.append(DataOrigin(
                    source_name=origin_def['name'],
                    source_type=origin_def['type'],
                    country=primary_country if primary_country != 'unknown' else 'Configured Region',
                    collection_method=origin_def['method'],
                    legal_basis=origin_def['legal_basis'],
                    data_categories=origin_def['categories'],
                    is_eu_origin=is_eu
                ))
        
        if not origins:
            origins.append(DataOrigin(
                source_name=f"{provider} Infrastructure",
                source_type="cloud_infrastructure",
                country=primary_country if primary_country != 'unknown' else 'Configured Region',
                collection_method="Cloud Infrastructure",
                legal_basis="Legitimate Interest (Art. 6(1)(f))",
                data_categories=["operational_data", "infrastructure_data"],
                is_eu_origin=is_eu
            ))
        
        return origins
    
    def _analyze_legal_jurisdictions(self, locations: List[DataLocation]) -> List[LegalJurisdiction]:
        """Map data locations to legal jurisdictions"""
        jurisdictions = []
        
        for loc in locations:
            applicable_laws = []
            adequacy_status = "No Basis"
            risk_level = "high"
            
            if loc.country in self.EU_COUNTRIES:
                applicable_laws = ["GDPR", "ePrivacy Directive"]
                if loc.country == 'NL':
                    applicable_laws.append("UAVG (Netherlands)")
                elif loc.country == 'DE':
                    applicable_laws.append("BDSG (Germany)")
                elif loc.country == 'FR':
                    applicable_laws.append("Loi Informatique (France)")
                adequacy_status = "EU Member State"
                risk_level = "low"
            elif loc.country in self.EEA_COUNTRIES:
                applicable_laws = ["GDPR (via EEA)", "Local Data Protection"]
                adequacy_status = "EEA Member State"
                risk_level = "low"
            elif loc.country == 'US':
                applicable_laws = ["EU-US Data Privacy Framework", "US CLOUD Act", "CCPA/CPRA"]
                adequacy_status = "EU-US Data Privacy Framework (Conditional)"
                risk_level = "medium"
            elif loc.country in self.ADEQUACY_COUNTRIES:
                applicable_laws = ["Local Data Protection Law"]
                adequacy_status = f"EU Adequacy Decision"
                risk_level = "low"
            else:
                applicable_laws = ["Local Data Protection Law (if any)"]
                adequacy_status = "No Adequacy - SCCs/BCRs Required"
                risk_level = "high"
            
            jurisdictions.append(LegalJurisdiction(
                location=loc.region,
                country=loc.country,
                applicable_laws=applicable_laws,
                adequacy_status=adequacy_status,
                sccs_in_place=False,
                bcrs_in_place=False,
                tia_completed=False,
                dpa_in_place=loc.country in self.EU_COUNTRIES,
                risk_level=risk_level
            ))
        
        return jurisdictions
    
    def _run_compliance_checks(self, config: Dict[str, Any], result: SovereigntyScanResult) -> List[ComplianceCheck]:
        """Run comprehensive compliance checks"""
        checks = []
        
        has_third_country = any(not loc.is_eu and not loc.is_adequacy_decision for loc in result.data_locations)
        
        checks.append(ComplianceCheck(
            check_name="Standard Contractual Clauses (SCCs)",
            check_category="sccs",
            status="fail" if has_third_country else "pass",
            description="SCCs are required for transfers to third countries without adequacy decisions" if has_third_country else "No third country transfers detected requiring SCCs",
            legal_reference="GDPR Article 46(2)(c)",
            recommendation="Implement EU Commission's 2021 SCCs for all third-country transfers" if has_third_country else ""
        ))
        
        checks.append(ComplianceCheck(
            check_name="Transfer Impact Assessment (TIA)",
            check_category="tia",
            status="warning" if has_third_country else "not_applicable",
            description="TIA required per Schrems II for third country transfers" if has_third_country else "No third country transfers requiring TIA",
            legal_reference="CJEU Schrems II Judgment (Case C-311/18)",
            recommendation="Complete TIA documenting legal framework and supplementary measures" if has_third_country else ""
        ))
        
        encryption_detected = config.get('encryption_enabled', False)
        checks.append(ComplianceCheck(
            check_name="Encryption at Rest",
            check_category="encryption",
            status="pass" if encryption_detected else "warning",
            description="Data encryption at rest detected" if encryption_detected else "No explicit encryption configuration found",
            legal_reference="GDPR Article 32 (Security of Processing)",
            recommendation="" if encryption_detected else "Enable encryption for all data stores"
        ))
        
        checks.append(ComplianceCheck(
            check_name="Encryption in Transit",
            check_category="encryption",
            status="warning",
            description="TLS/SSL configuration should be verified",
            legal_reference="GDPR Article 32 (Security of Processing)",
            recommendation="Ensure TLS 1.2+ for all data transfers"
        ))
        
        checks.append(ComplianceCheck(
            check_name="Data Processing Agreement (DPA)",
            check_category="dpa",
            status="warning",
            description="DPA status with cloud providers needs verification",
            legal_reference="GDPR Article 28 (Processor)",
            recommendation="Verify DPA is in place with all data processors"
        ))
        
        checks.append(ComplianceCheck(
            check_name="Data Retention Policy",
            check_category="retention",
            status="warning",
            description="No explicit retention policy detected in configuration",
            legal_reference="GDPR Article 5(1)(e) (Storage Limitation)",
            recommendation="Define and implement data retention policies"
        ))
        
        checks.append(ComplianceCheck(
            check_name="Backup Location Compliance",
            check_category="backup",
            status="warning" if has_third_country else "pass",
            description="Verify backup storage locations are GDPR compliant",
            legal_reference="GDPR Article 32 + Chapter V",
            recommendation="Ensure backups are stored in EU/EEA or adequacy countries"
        ))
        
        checks.append(ComplianceCheck(
            check_name="Netherlands UAVG Compliance",
            check_category="uavg",
            status="pass" if self.region == "Netherlands" else "not_applicable",
            description="Netherlands-specific requirements apply" if self.region == "Netherlands" else "UAVG applies only to Netherlands operations",
            legal_reference="UAVG (Uitvoeringswet AVG)",
            recommendation="Ensure BSN processing follows UAVG Article 46" if self.region == "Netherlands" else ""
        ))
        
        return checks
    
    def _run_terraform_compliance_checks(self, content: str, result: SovereigntyScanResult) -> List[ComplianceCheck]:
        """Run compliance checks on Terraform configuration"""
        checks = []
        content_lower = content.lower()
        provider = self._detect_terraform_provider(content)
        
        has_third_country = any(not loc.is_eu and not loc.is_adequacy_decision for loc in result.data_locations)
        has_non_eu = any(not loc.is_eu for loc in result.data_locations)
        has_us_storage = any(loc.country == 'US' for loc in result.data_locations)
        has_adequacy_only = has_non_eu and not has_third_country
        non_eu_countries = ', '.join(set(l.country for l in result.data_locations if not l.is_eu))
        
        if has_third_country:
            sccs_status = "fail"
            sccs_desc = f"Third country storage detected ({non_eu_countries}) - EU Commission 2021 SCCs required for lawful transfers"
            sccs_rec = "Execute EU Commission's 2021 Standard Contractual Clauses with all third-country processors"
        elif has_adequacy_only:
            sccs_status = "pass"
            sccs_desc = f"Non-EU storage in adequacy countries ({non_eu_countries}) - SCCs not strictly required but recommended as supplementary safeguard"
            sccs_rec = ""
        else:
            sccs_status = "pass"
            sccs_desc = "All storage in EU/EEA - no SCCs needed"
            sccs_rec = ""
        
        checks.append(ComplianceCheck(
            check_name="Standard Contractual Clauses (SCCs)",
            check_category="sccs",
            status=sccs_status,
            description=sccs_desc,
            legal_reference="GDPR Article 46(2)(c)",
            recommendation=sccs_rec
        ))
        
        if has_third_country:
            tia_status = "fail"
            tia_desc = f"TIA mandatory per Schrems II for {provider} processing in third countries. Must assess local surveillance laws."
            tia_rec = "Complete TIA documenting: (1) legal framework assessment, (2) supplementary technical measures, (3) ongoing monitoring plan"
        elif has_us_storage:
            tia_status = "warning"
            tia_desc = f"US storage detected - TIA recommended despite EU-US Data Privacy Framework due to CLOUD Act exposure and conditional adequacy status"
            tia_rec = "Complete TIA documenting supplementary measures for US-based processing (EDPB Recommendations 01/2020)"
        else:
            tia_status = "not_applicable"
            tia_desc = "No third country transfers requiring TIA"
            tia_rec = ""
        
        checks.append(ComplianceCheck(
            check_name="Transfer Impact Assessment (TIA)",
            check_category="tia",
            status=tia_status,
            description=tia_desc,
            legal_reference="CJEU Schrems II (Case C-311/18), EDPB Recommendations 01/2020",
            recommendation=tia_rec
        ))
        
        encryption_patterns = re.findall(r'\bencrypt(?:ion|ed)?\b|\bkms\b|\bkey_id\b|\bserver_side_encryption\b|\bsse[-_](?:s3|kms)\b|\bcmk\b|\bcustomer_managed_key\b|\bkey_vault\b|\bdisk_encryption\b|\bgoogle_kms\b|\bcmek\b|\bazurerm_key_vault\b', content_lower)
        has_encryption = len(encryption_patterns) > 0
        has_customer_key = bool(re.search(r'\bkms\b|\bcmk\b|\bcustomer_managed_key\b|\bkey_id\b|\bkey_vault\b|\bdisk_encryption_set\b|\bgoogle_kms_crypto_key\b|\bcmek\b', content_lower))
        checks.append(ComplianceCheck(
            check_name="Encryption at Rest",
            check_category="encryption",
            status="pass" if has_encryption else "fail",
            description=f"Encryption detected{' with customer-managed keys' if has_customer_key else ' (provider-managed keys)'}" if has_encryption else "No encryption configuration found - data at rest is unprotected",
            legal_reference="GDPR Article 32 (Security of Processing)",
            recommendation="" if has_encryption else "Enable AES-256 encryption with customer-managed keys for all storage resources"
        ))
        
        tls_patterns = re.findall(r'\bhttps://|\btls[_\s]|\bssl[_\s]|\bcertificate\b|\bacm_certificate\b|\bmin_tls_version\b|\bssl_enforcement\b', content_lower)
        has_tls = len(tls_patterns) > 0
        checks.append(ComplianceCheck(
            check_name="Encryption in Transit (TLS)",
            check_category="encryption",
            status="pass" if has_tls else "warning",
            description="TLS/HTTPS configuration found for data in transit" if has_tls else "No explicit TLS configuration - verify all endpoints enforce HTTPS",
            legal_reference="GDPR Article 32 (Security of Processing)",
            recommendation="" if has_tls else "Enforce TLS 1.2+ for all endpoints and inter-service communication"
        ))
        
        detected_providers = set()
        for loc in result.data_locations:
            if loc.cloud_provider:
                detected_providers.add(loc.cloud_provider)
        provider_label = ', '.join(detected_providers) if detected_providers else provider
        
        dpa_check = "warning" if has_third_country or has_us_storage else "pass"
        checks.append(ComplianceCheck(
            check_name="Data Processing Agreement (DPA)",
            check_category="dpa",
            status=dpa_check,
            description=f"DPA with {provider_label} required under GDPR Art. 28. Verify DPA covers all deployed services and regions." if has_third_country else f"DPA with {provider_label} should be in place for EU processing" if has_non_eu else f"DPA with {provider_label} should be in place for EU processing",
            legal_reference="GDPR Article 28 (Processor Obligations)",
            recommendation=f"Verify signed DPA with {provider_label} covers: data categories, processing purposes, sub-processor controls, and audit rights" if has_third_country or has_us_storage else ""
        ))
        
        if has_third_country:
            bcr_status = "warning"
            bcr_desc = "BCRs may be required as additional transfer mechanism for intra-group transfers to third countries"
            bcr_rec = "Consider BCRs for systematic intra-group transfers alongside SCCs"
        elif has_adequacy_only:
            bcr_status = "not_applicable"
            bcr_desc = f"Non-EU storage in adequacy countries ({non_eu_countries}) - BCRs not required but may strengthen compliance posture"
            bcr_rec = ""
        else:
            bcr_status = "not_applicable"
            bcr_desc = "No BCRs needed - all processing within EU/EEA"
            bcr_rec = ""
        
        checks.append(ComplianceCheck(
            check_name="Binding Corporate Rules (BCRs)",
            check_category="bcr",
            status=bcr_status,
            description=bcr_desc,
            legal_reference="GDPR Article 47 (Binding Corporate Rules)",
            recommendation=bcr_rec
        ))
        
        retention_patterns = re.findall(r'\bretention\b|\blifecycle_rule\b|\blifecycle_policy\b|\bexpiration\b|\bttl\b|\bretention_days\b|\bretention_period\b|\bdata_retention\b|\blifecycle\s*\{[^}]*expiration', content_lower)
        has_retention = len(retention_patterns) > 0
        checks.append(ComplianceCheck(
            check_name="Data Retention Policy",
            check_category="retention",
            status="pass" if has_retention else "warning",
            description="Lifecycle/retention policy found in infrastructure configuration" if has_retention else "No data retention or lifecycle policy defined in configuration",
            legal_reference="GDPR Article 5(1)(e) (Storage Limitation Principle)",
            recommendation="" if has_retention else "Define retention periods and implement automatic data lifecycle management"
        ))
        
        backup_patterns = re.findall(r'\bbackup\b|\breplication\b|\bsnapshot\b|\bdr_\w|\bdisaster[_\s]recovery\b|\brecovery_point\b|\bbackup_policy\b|\bbackup_retention\b', content_lower)
        has_backups = len(backup_patterns) > 0
        backup_in_third = has_backups and has_third_country
        checks.append(ComplianceCheck(
            check_name="Backup Location Compliance",
            check_category="backup",
            status="warning" if backup_in_third else ("pass" if has_backups else "fail"),
            description="Backup configuration detected - verify backup storage stays within EU/EEA" if has_backups else "No backup/disaster recovery configuration found",
            legal_reference="GDPR Article 32 + Chapter V (International Transfers)",
            recommendation="Ensure all backup and DR storage locations are within EU/EEA jurisdictions" if backup_in_third else ("Implement backup strategy with EU/EEA-only storage" if not has_backups else "")
        ))
        
        logging_patterns = re.findall(r'\bcloudwatch\b|\bcloudtrail\b|\blogging_service\b|\baudit_log\b|\bmonitor(?:ing)?\b|\blog_analytics\b|\bazurerm_monitor_\w|\bapplication_insights\b|\bgoogle_logging\b|\bgoogle_monitoring\b|\bstackdriver\b|\bfluentd\b|\bprometheus\b|\bgrafana\b|\belastic\w*search\b|\bsplunk\b', content_lower)
        has_logging = len(logging_patterns) > 0
        checks.append(ComplianceCheck(
            check_name="Audit Logging & Monitoring",
            check_category="monitoring",
            status="pass" if has_logging else "warning",
            description="Logging/monitoring configuration detected" if has_logging else "No audit logging or monitoring configuration found",
            legal_reference="GDPR Article 5(2) (Accountability), Article 30 (Records of Processing)",
            recommendation="" if has_logging else "Enable audit logging (AWS CloudTrail / Azure Monitor / GCP Cloud Audit Logs) for all data access and processing activities"
        ))
        
        if has_us_storage:
            checks.append(ComplianceCheck(
                check_name="US CLOUD Act Risk Assessment",
                check_category="cloud_act",
                status="warning",
                description=f"US-based storage with {provider_label} (US-headquartered) - subject to CLOUD Act disclosure orders. Supplementary measures required.",
                legal_reference="US CLOUD Act (2018), CJEU Schrems II, EDPB Recommendations 01/2020",
                recommendation="Implement supplementary measures: customer-managed encryption keys, pseudonymization, and contractual restrictions on government access"
            ))
        
        uavg_status = "pass" if self.region == "Netherlands" else "not_applicable"
        checks.append(ComplianceCheck(
            check_name="Netherlands UAVG Compliance",
            check_category="uavg",
            status=uavg_status,
            description="Netherlands UAVG (Uitvoeringswet AVG) applies as data controller is Netherlands-based. Ensure BSN/special categories processing complies." if self.region == "Netherlands" else "Not applicable outside Netherlands",
            legal_reference="UAVG (Uitvoeringswet AVG), Articles 22-31 (Special Categories), Article 46 (BSN Processing)",
            recommendation="Verify BSN processing follows UAVG Article 46; report to Autoriteit Persoonsgegevens within 72 hours of any breach" if self.region == "Netherlands" else ""
        ))
        
        return checks
    
    def _detect_encryption_at_rest(self, config: Dict[str, Any]) -> bool:
        """Detect if encryption at rest is configured"""
        return config.get('encryption_at_rest', False)
    
    def _detect_encryption_in_transit(self, config: Dict[str, Any]) -> bool:
        """Detect if encryption in transit is configured"""
        return config.get('encryption_in_transit', config.get('tls_enabled', False))
    
    def _detect_retention_policy(self, config: Dict[str, Any]) -> str:
        """Detect data retention policy"""
        return config.get('retention_policy', 'Not specified')
    
    def _detect_backup_locations(self, config: Dict[str, Any]) -> List[str]:
        """Detect backup storage locations"""
        return config.get('backup_locations', [])
    
    def _detect_terraform_encryption(self, content: str, enc_type: str) -> bool:
        """Detect encryption settings in Terraform/cloud config"""
        content_lower = content.lower()
        if enc_type == "at_rest":
            return bool(re.search(r'\bencrypt(?:ion|ed)?\b|\bkms\b|\bserver_side_encryption\b|\bsse[-_](?:s3|kms)\b|\bkey_vault\b|\bdisk_encryption\b|\bcustomer_managed_key\b|\bgoogle_kms_crypto_key\b|\bcmek\b|\bazurerm_key_vault\b', content_lower))
        else:
            return bool(re.search(r'\bhttps://|\btls[_\s]|\bssl[_\s]|\bcertificate_arn\b|\bmin_tls_version\b|\bssl_enforcement\b|\bcertificate\b', content_lower))
    
    def _detect_terraform_retention(self, content: str) -> str:
        """Detect retention policies in Terraform"""
        retention_match = re.search(r'(?:retention|expiration)[_\-]?(?:days|period)?\s*[=:]\s*(\d+)', content.lower())
        if retention_match:
            return f"{retention_match.group(1)} days"
        
        lifecycle_match = re.search(r'lifecycle[_\s]*\{[^}]*expiration', content.lower())
        if lifecycle_match:
            return "Lifecycle policy defined"
        
        return "Not specified"
    
    def _detect_terraform_backups(self, content: str) -> List[str]:
        """Detect backup locations in Terraform"""
        backups = []
        
        for region, info in self.CLOUD_REGIONS.items():
            if f'backup' in content.lower() and region in content.lower():
                backups.append(f"{region} ({info['country']})")
        
        replica_match = re.findall(r'replica[_\-]?region\s*=\s*["\']([^"\']+)["\']', content)
        backups.extend(replica_match)
        
        return backups
    
    def _get_country_from_region(self, region: str) -> str:
        """Get country code from region name"""
        region_map = {
            'Netherlands': 'NL',
            'Germany': 'DE',
            'France': 'FR',
            'Belgium': 'BE',
            'United Kingdom': 'GB',
            'Ireland': 'IE',
            'United States': 'US'
        }
        return region_map.get(region, 'NL')
    
    def _generate_findings(self, result: SovereigntyScanResult) -> List[Dict[str, Any]]:
        """Generate sovereignty findings from analysis"""
        findings = []
        
        for flow in result.data_flows:
            if flow.is_eu_to_third_country:
                findings.append({
                    'type': 'cross_border_transfer',
                    'severity': 'high',
                    'title': f'EU to Third Country Transfer: {flow.source} → {flow.destination}',
                    'description': f'Data transfer from EU ({flow.source_country}) to third country ({flow.destination_country}) detected. This requires appropriate safeguards under GDPR Chapter V.',
                    'affected_data': flow.data_types,
                    'legal_reference': 'GDPR Article 44-49 (Transfers to Third Countries)',
                    'recommendation': 'Implement Standard Contractual Clauses (SCCs) or verify adequacy decision',
                    'risk_score': 0.8
                })
            elif flow.is_cross_border:
                findings.append({
                    'type': 'cross_border_transfer',
                    'severity': 'medium',
                    'title': f'Cross-Border Transfer: {flow.source} → {flow.destination}',
                    'description': f'Data transfer between {flow.source_country} and {flow.destination_country} detected.',
                    'affected_data': flow.data_types,
                    'legal_reference': 'GDPR Article 44 (General Transfer Principle)',
                    'recommendation': 'Document the transfer and ensure appropriate legal basis',
                    'risk_score': 0.4
                })
        
        for location in result.data_locations:
            if not location.is_eu and not location.is_adequacy_decision:
                findings.append({
                    'type': 'third_country_storage',
                    'severity': 'high',
                    'title': f'Data Storage in Third Country: {location.region}',
                    'description': f'Data stored in {location.country} which lacks EU adequacy decision. Legal basis required for processing.',
                    'affected_data': [location.service_type],
                    'legal_reference': 'GDPR Article 45-46 (Adequacy and Appropriate Safeguards)',
                    'recommendation': 'Migrate to EU region or implement binding corporate rules (BCRs)',
                    'risk_score': 0.7
                })
            
            if location.cloud_provider and location.cloud_provider.lower() in ['aws', 'azure', 'gcp', 'microsoft', 'amazon', 'google']:
                findings.append({
                    'type': 'cloud_act_risk',
                    'severity': 'medium',
                    'title': f'US CLOUD Act Risk: {location.cloud_provider}',
                    'description': f'Data stored with US-headquartered provider ({location.cloud_provider}) may be subject to US CLOUD Act disclosure requirements.',
                    'affected_data': [location.service_type],
                    'legal_reference': 'CJEU Schrems II Judgment, US CLOUD Act',
                    'recommendation': 'Conduct Transfer Impact Assessment (TIA) and implement supplementary measures',
                    'risk_score': 0.5
                })
        
        seen_access_findings = set()
        for access in result.access_paths:
            accessor_label = access.accessor_name or access.accessor_type
            if not access.is_eu_access:
                finding_key = f"non_eu_access:{accessor_label}:{access.accessor_country}"
                if finding_key not in seen_access_findings:
                    seen_access_findings.add(finding_key)
                    findings.append({
                        'type': 'non_eu_access',
                        'severity': 'high',
                        'title': f'Non-EU Access Detected: {accessor_label} ({access.accessor_country})',
                        'description': f'Access from non-EU country ({access.accessor_country}) via {accessor_label} with {access.privilege_level} privileges detected.',
                        'affected_data': [access.accessor_type],
                        'legal_reference': 'GDPR Article 44 (Transfer Restrictions)',
                        'recommendation': 'Implement access controls to restrict non-EU access or establish legal basis',
                        'risk_score': 0.7
                    })
            
            if not access.is_monitored:
                finding_key = f"unmonitored:{accessor_label}"
                if finding_key not in seen_access_findings:
                    seen_access_findings.add(finding_key)
                    findings.append({
                        'type': 'unmonitored_access',
                        'severity': 'medium',
                        'title': f'Unmonitored Access Path: {accessor_label}',
                        'description': f'Access path for {accessor_label} is not being actively monitored.',
                        'affected_data': [access.accessor_type],
                        'legal_reference': 'GDPR Article 32 (Security of Processing)',
                        'recommendation': 'Implement logging and monitoring for all access paths',
                        'risk_score': 0.5
                    })
        
        return findings
    
    def _generate_recommendations(self, result: SovereigntyScanResult) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        non_eu_locations = [l for l in result.data_locations if not l.is_eu]
        if non_eu_locations:
            regions = ', '.join(set(f"{l.region} ({l.country})" for l in non_eu_locations))
            recommendations.append(f"CRITICAL: Migrate data storage from non-EU regions ({regions}) to EU regions (e.g., eu-central-1 Frankfurt, eu-west-1 Ireland) to simplify GDPR compliance")
        
        eu_to_third = [f for f in result.data_flows if f.is_eu_to_third_country]
        if eu_to_third:
            recommendations.append("Execute EU Commission's 2021 Standard Contractual Clauses (SCCs) for all EU-to-third-country transfers before go-live")
            recommendations.append("Complete Transfer Impact Assessments (TIAs) documenting: legal framework analysis, supplementary technical measures, and ongoing monitoring plan")
        
        us_locations = [l for l in result.data_locations if l.country == 'US']
        if us_locations:
            recommendations.append("Implement customer-managed encryption keys (BYOK/CMK) to mitigate US CLOUD Act disclosure risks")
            recommendations.append("Document supplementary technical measures per EDPB Recommendations 01/2020 (pseudonymization, split processing, encryption)")
        
        us_providers = [l for l in result.data_locations 
                       if l.cloud_provider and l.cloud_provider.lower() in ['aws', 'azure', 'gcp']]
        if us_providers:
            provider_names = ', '.join(set(str(l.cloud_provider) for l in us_providers if l.cloud_provider))
            recommendations.append(f"Verify signed Data Processing Agreement (DPA) with {provider_names} covers all deployed regions and services (GDPR Art. 28)")
        
        non_eu_access = [a for a in result.access_paths if not a.is_eu_access]
        if non_eu_access:
            recommendations.append("Implement geo-fencing to restrict administrative access to EU locations only")
            recommendations.append("Review and document all third-party vendor access from non-EU countries with appropriate legal basis")
        
        unmonitored = [a for a in result.access_paths if not a.is_monitored]
        if unmonitored:
            recommendations.append("Enable comprehensive audit logging and real-time monitoring for all data access paths (GDPR Art. 5(2) Accountability)")
        
        failed_checks = [c for c in result.compliance_checks if c.status == 'fail']
        if failed_checks:
            for check in failed_checks:
                if check.recommendation and check.recommendation not in recommendations:
                    recommendations.append(f"{check.check_name}: {check.recommendation}")
        
        encryption_check_passed = any(c.check_name == "Encryption at Rest" and c.status == "pass" for c in result.compliance_checks)
        if not result.encryption_at_rest and not encryption_check_passed:
            recommendations.append("Enable encryption at rest (AES-256) for all data stores to comply with GDPR Article 32")
        
        if self.region == "Netherlands":
            recommendations.append("Ensure all data breach notifications are filed with Autoriteit Persoonsgegevens (Dutch DPA) within 72 hours as required by GDPR Art. 33 and UAVG")
        
        if not recommendations:
            recommendations.append("Current configuration demonstrates good data sovereignty practices - maintain ongoing compliance monitoring")
        
        return recommendations
    
    def _calculate_risk_score(self, result: SovereigntyScanResult) -> float:
        """Calculate overall sovereignty risk score (0.0 - 1.0)"""
        if not result.findings:
            return 0.0
        
        total_risk = sum(f.get('risk_score', 0.0) for f in result.findings)
        
        weighted_score = min(1.0, total_risk / max(len(result.findings), 1))
        
        high_severity = sum(1 for f in result.findings if f.get('severity') == 'high')
        if high_severity > 2:
            weighted_score = min(1.0, weighted_score + 0.2)
        
        return round(weighted_score, 2)
    
    def _determine_risk_level(self, score: float) -> SovereigntyRiskLevel:
        """Determine risk level from score"""
        if score >= 0.7:
            return SovereigntyRiskLevel.RED
        elif score >= 0.4:
            return SovereigntyRiskLevel.AMBER
        else:
            return SovereigntyRiskLevel.GREEN
    
    def generate_html_report(self, result: SovereigntyScanResult) -> str:
        """Generate comprehensive HTML compliance report"""
        risk_color = {
            SovereigntyRiskLevel.GREEN: '#28a745',
            SovereigntyRiskLevel.AMBER: '#fd7e14',
            SovereigntyRiskLevel.RED: '#dc3545'
        }.get(result.risk_level, '#6c757d')
        
        risk_label = result.risk_level.value.upper()
        
        locations_html = ""
        for loc in result.data_locations:
            eu_badge = '<span style="background:#28a745;color:white;padding:2px 8px;border-radius:12px;font-size:0.75rem;">EU</span>' if loc.is_eu else '<span style="background:#dc3545;color:white;padding:2px 8px;border-radius:12px;font-size:0.75rem;">Non-EU</span>'
            locations_html += f"""
            <div class="location-card">
                <div class="location-header">
                    <strong>{loc.region}</strong> {eu_badge}
                </div>
                <div class="location-details">
                    <p><strong>Country:</strong> {loc.country}</p>
                    <p><strong>Provider:</strong> {loc.cloud_provider or 'N/A'}</p>
                    <p><strong>Service:</strong> {loc.service_type}</p>
                    <p><strong>Jurisdiction:</strong> {loc.legal_jurisdiction}</p>
                </div>
            </div>
            """
        
        flows_html = ""
        for flow in result.data_flows:
            flow_class = "critical" if flow.is_eu_to_third_country else ("warning" if flow.is_cross_border else "")
            flows_html += f"""
            <div class="flow-item {flow_class}">
                <div class="flow-arrow">
                    <span class="flow-source">{flow.source} ({flow.source_country})</span>
                    <span class="arrow">→</span>
                    <span class="flow-dest">{flow.destination} ({flow.destination_country})</span>
                </div>
                <div class="flow-meta">
                    {'<span class="badge danger">EU → Third Country</span>' if flow.is_eu_to_third_country else ''}
                    {'<span class="badge warning">Cross-Border</span>' if flow.is_cross_border and not flow.is_eu_to_third_country else ''}
                    <span class="badge info">{flow.flow_type}</span>
                </div>
            </div>
            """
        
        findings_html = ""
        for finding in result.findings:
            severity_class = finding.get('severity', 'medium')
            findings_html += f"""
            <div class="finding-card {severity_class}">
                <div class="finding-header">
                    <h4>{finding.get('title', 'Finding')}</h4>
                    <span class="severity-badge {severity_class}">{severity_class.upper()}</span>
                </div>
                <p class="finding-description">{finding.get('description', '')}</p>
                <div class="finding-details">
                    <p><strong>Legal Reference:</strong> {finding.get('legal_reference', 'N/A')}</p>
                    <p><strong>Recommendation:</strong> {finding.get('recommendation', 'N/A')}</p>
                </div>
            </div>
            """
        
        recommendations_html = ""
        for i, rec in enumerate(result.recommendations, 1):
            recommendations_html += f"""
            <div class="recommendation-item">
                <span class="rec-number">{i}</span>
                <span class="rec-text">{rec}</span>
            </div>
            """
        
        origins_html = ""
        for origin in result.data_origins:
            eu_badge = '<span class="badge success">EU Origin</span>' if origin.is_eu_origin else '<span class="badge danger">Non-EU Origin</span>'
            origins_html += f"""
            <div class="origin-card">
                <div class="origin-header">
                    <strong>{origin.source_name}</strong> {eu_badge}
                </div>
                <div class="origin-details">
                    <p><strong>Source Type:</strong> {origin.source_type.replace('_', ' ').title()}</p>
                    <p><strong>Country:</strong> {origin.country}</p>
                    <p><strong>Collection Method:</strong> {origin.collection_method}</p>
                    <p><strong>Legal Basis:</strong> {origin.legal_basis}</p>
                    <p><strong>Data Categories:</strong> {', '.join(origin.data_categories)}</p>
                </div>
            </div>
            """
        
        jurisdictions_html = ""
        for jur in result.legal_jurisdictions:
            risk_badge = {
                'low': '<span class="badge success">Low Risk</span>',
                'medium': '<span class="badge warning">Medium Risk</span>',
                'high': '<span class="badge danger">High Risk</span>'
            }.get(jur.risk_level, '<span class="badge info">Unknown</span>')
            
            safeguards = []
            if jur.sccs_in_place:
                safeguards.append("✓ SCCs")
            if jur.bcrs_in_place:
                safeguards.append("✓ BCRs")
            if jur.tia_completed:
                safeguards.append("✓ TIA")
            if jur.dpa_in_place:
                safeguards.append("✓ DPA")
            
            jurisdictions_html += f"""
            <div class="jurisdiction-card" style="border-left-color: {'#28a745' if jur.risk_level == 'low' else ('#fd7e14' if jur.risk_level == 'medium' else '#dc3545')};">
                <div class="jurisdiction-header">
                    <strong>{jur.location}</strong> ({jur.country}) {risk_badge}
                </div>
                <div class="jurisdiction-details">
                    <p><strong>Applicable Laws:</strong> {', '.join(jur.applicable_laws)}</p>
                    <p><strong>Adequacy Status:</strong> {jur.adequacy_status}</p>
                    <p><strong>Safeguards:</strong> {', '.join(safeguards) if safeguards else '❌ None documented'}</p>
                </div>
            </div>
            """
        
        access_html = ""
        for access in result.access_paths:
            access_badge = '<span class="badge success">EU</span>' if access.is_eu_access else '<span class="badge danger">Non-EU</span>'
            monitor_badge = '<span class="badge info">Monitored</span>' if access.is_monitored else '<span class="badge warning">Unmonitored</span>'
            access_html += f"""
            <div class="access-card">
                <div class="access-header">
                    <strong>{access.accessor_name or access.accessor_type}</strong> {access_badge} {monitor_badge}
                </div>
                <div class="access-details">
                    <p><strong>Type:</strong> {access.accessor_type}</p>
                    <p><strong>Country:</strong> {access.accessor_country}</p>
                    <p><strong>Privilege Level:</strong> {access.privilege_level}</p>
                </div>
            </div>
            """
        
        compliance_html = ""
        for check in result.compliance_checks:
            status_badge = {
                'pass': '<span class="status-badge pass">✓ PASS</span>',
                'fail': '<span class="status-badge fail">✗ FAIL</span>',
                'warning': '<span class="status-badge warning">⚠ WARNING</span>',
                'not_applicable': '<span class="status-badge na">N/A</span>'
            }.get(check.status, '<span class="status-badge">Unknown</span>')
            
            compliance_html += f"""
            <tr>
                <td><strong>{check.check_name}</strong></td>
                <td>{status_badge}</td>
                <td>{check.description}</td>
                <td><small>{check.legal_reference}</small></td>
            </tr>
            """
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataGuardian Pro - Data Sovereignty Compliance Report</title>
    <style>
        :root {{
            --primary: #667eea;
            --primary-dark: #764ba2;
            --success: #28a745;
            --warning: #fd7e14;
            --danger: #dc3545;
            --info: #17a2b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
            color: white;
            padding: 2.5rem;
        }}
        .header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .header .subtitle {{ opacity: 0.85; font-size: 1.1rem; }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }}
        .meta-item {{
            background: rgba(255,255,255,0.1);
            padding: 1rem;
            border-radius: 10px;
        }}
        .meta-item label {{
            font-size: 0.75rem;
            opacity: 0.7;
            display: block;
            text-transform: uppercase;
        }}
        .meta-item span {{ font-size: 1rem; font-weight: 600; }}
        .executive-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }}
        .summary-card h3 {{
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
        }}
        .summary-card .value {{
            font-size: 2.5rem;
            font-weight: 800;
        }}
        .risk-badge {{
            display: inline-block;
            padding: 0.5rem 1.5rem;
            border-radius: 25px;
            font-weight: 700;
            font-size: 1rem;
            color: white;
            background: {risk_color};
        }}
        .section {{
            padding: 2rem;
            border-bottom: 1px solid #eee;
        }}
        .section h3 {{
            font-size: 1.4rem;
            margin-bottom: 1.5rem;
            color: #1a237e;
        }}
        .location-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid var(--primary);
        }}
        .location-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }}
        .location-details p {{
            margin: 0.25rem 0;
            font-size: 0.9rem;
        }}
        .flow-item {{
            background: white;
            border: 1px solid #eee;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }}
        .flow-item.critical {{ border-left: 4px solid var(--danger); background: #fff5f5; }}
        .flow-item.warning {{ border-left: 4px solid var(--warning); background: #fffbeb; }}
        .flow-arrow {{
            display: flex;
            align-items: center;
            gap: 1rem;
            font-weight: 600;
        }}
        .arrow {{ color: var(--primary); font-size: 1.5rem; }}
        .flow-meta {{ margin-top: 0.5rem; }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }}
        .badge.danger {{ background: #dc3545; color: white; }}
        .badge.warning {{ background: #fd7e14; color: white; }}
        .badge.info {{ background: #17a2b8; color: white; }}
        .badge.success {{ background: #28a745; color: white; }}
        .origin-card, .jurisdiction-card, .access-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid var(--primary);
        }}
        .origin-header, .jurisdiction-header, .access-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
            flex-wrap: wrap;
        }}
        .origin-details p, .jurisdiction-details p, .access-details p {{
            margin: 0.25rem 0;
            font-size: 0.9rem;
        }}
        .compliance-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        .compliance-table th, .compliance-table td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .compliance-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #1a237e;
        }}
        .status-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.75rem;
            font-weight: 700;
        }}
        .status-badge.pass {{ background: #28a745; color: white; }}
        .status-badge.fail {{ background: #dc3545; color: white; }}
        .status-badge.warning {{ background: #fd7e14; color: white; }}
        .status-badge.na {{ background: #6c757d; color: white; }}
        .key-questions {{
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .key-questions h4 {{
            color: #1b5e20;
            margin-bottom: 1rem;
        }}
        .key-questions ul {{
            list-style: none;
        }}
        .key-questions li {{
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }}
        .key-questions li:last-child {{
            border-bottom: none;
        }}
        .finding-card {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid #eee;
            border-left: 5px solid #ddd;
        }}
        .finding-card.high {{ border-left-color: var(--danger); background: linear-gradient(90deg, #fff5f5 0%, white 100%); }}
        .finding-card.medium {{ border-left-color: var(--warning); background: linear-gradient(90deg, #fffbeb 0%, white 100%); }}
        .finding-card.low {{ border-left-color: var(--success); }}
        .finding-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.75rem;
        }}
        .finding-header h4 {{ color: #333; font-size: 1.1rem; }}
        .severity-badge {{
            padding: 0.35rem 0.85rem;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .severity-badge.high {{ background: var(--danger); color: white; }}
        .severity-badge.medium {{ background: var(--warning); color: #333; }}
        .severity-badge.low {{ background: var(--success); color: white; }}
        .finding-description {{ color: #555; margin-bottom: 1rem; }}
        .finding-details {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
        }}
        .finding-details p {{ margin: 0.5rem 0; font-size: 0.9rem; }}
        .recommendation-item {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            background: white;
            padding: 1.25rem;
            border-radius: 10px;
            margin-bottom: 0.75rem;
            border: 1px solid #eee;
        }}
        .rec-number {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
            flex-shrink: 0;
        }}
        .rec-text {{ color: #333; line-height: 1.6; }}
        .footer {{
            background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        .footer-logo {{ font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; }}
        .footer-meta {{ opacity: 0.8; font-size: 0.85rem; }}
        .footer-badges {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}
        .footer-badge {{
            background: rgba(255,255,255,0.15);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.75rem;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">DATAGUARDIAN PRO</div>
            <h1>Data Sovereignty Compliance Report</h1>
            <p class="subtitle">Cross-Border Transfer & Jurisdictional Analysis</p>
            
            <div class="meta-grid">
                <div class="meta-item">
                    <label>Scan ID</label>
                    <span>{result.scan_id}</span>
                </div>
                <div class="meta-item">
                    <label>Target</label>
                    <span>{result.target_name}</span>
                </div>
                <div class="meta-item">
                    <label>Timestamp</label>
                    <span>{result.timestamp[:19]}</span>
                </div>
                <div class="meta-item">
                    <label>Region</label>
                    <span>{result.region}</span>
                </div>
            </div>
        </div>
        
        <div class="executive-summary">
            <div class="summary-card">
                <h3>Sovereignty Risk</h3>
                <div class="risk-badge">{risk_label}</div>
                <p style="margin-top:0.5rem;color:#666;">Score: {result.sovereignty_risk_score:.0%}</p>
            </div>
            <div class="summary-card">
                <h3>Cross-Border Transfers</h3>
                <div class="value" style="color:{'var(--danger)' if result.cross_border_transfers > 0 else 'var(--success)'};">{result.cross_border_transfers}</div>
            </div>
            <div class="summary-card">
                <h3>Non-EU Access</h3>
                <div class="value" style="color:{'var(--danger)' if result.non_eu_access_count > 0 else 'var(--success)'};">{result.non_eu_access_count}</div>
            </div>
            <div class="summary-card">
                <h3>Third Country Processors</h3>
                <div class="value" style="color:{'var(--danger)' if result.third_country_processors > 0 else 'var(--success)'};">{result.third_country_processors}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="key-questions">
                <h4>🔑 Key Sovereignty Questions Answered</h4>
                <ul>
                    <li><strong>Where did this data originate?</strong> {len(result.data_origins)} data source(s) identified - See Data Origins section below</li>
                    <li><strong>Where does it actually travel?</strong> {result.cross_border_transfers} cross-border transfer(s) detected - See Data Flows section</li>
                    <li><strong>Who can access it — and from which country?</strong> {len(result.access_paths)} access path(s) mapped ({result.non_eu_access_count} from non-EU) - See Access Control Matrix</li>
                    <li><strong>Under which legal jurisdiction is it processed?</strong> {len(result.legal_jurisdictions)} jurisdiction(s) analyzed - See Legal Jurisdictions section</li>
                </ul>
            </div>
        </div>
        
        <div class="section">
            <h3>🌐 Data Origins</h3>
            <p style="color:#666;margin-bottom:1rem;">Where your data originates and how it is collected</p>
            {origins_html if origins_html else '<p style="color:#888;">No specific data origins detected</p>'}
        </div>
        
        <div class="section">
            <h3>📍 Data Locations</h3>
            <p style="color:#666;margin-bottom:1rem;">Detected storage locations and their jurisdictional classification</p>
            {locations_html if locations_html else '<p style="color:#888;">No specific locations detected in configuration</p>'}
        </div>
        
        <div class="section">
            <h3>🔄 Data Flows & Journey</h3>
            <p style="color:#666;margin-bottom:1rem;">Where data travels between systems and regions</p>
            {flows_html if flows_html else '<p style="color:#888;">No cross-border flows detected</p>'}
        </div>
        
        <div class="section">
            <h3>👥 Access Control Matrix</h3>
            <p style="color:#666;margin-bottom:1rem;">Who can access your data and from which country</p>
            {access_html if access_html else '<p style="color:#888;">No specific access paths detected in configuration</p>'}
        </div>
        
        <div class="section">
            <h3>⚖️ Legal Jurisdictions</h3>
            <p style="color:#666;margin-bottom:1rem;">Applicable laws and adequacy status for each processing location</p>
            {jurisdictions_html if jurisdictions_html else '<p style="color:#888;">No jurisdictional analysis available</p>'}
        </div>
        
        <div class="section">
            <h3>✅ Compliance Checks</h3>
            <p style="color:#666;margin-bottom:1rem;">SCCs, TIA, Encryption, Retention, and other compliance requirements</p>
            <table class="compliance-table">
                <thead>
                    <tr>
                        <th>Check</th>
                        <th>Status</th>
                        <th>Description</th>
                        <th>Legal Reference</th>
                    </tr>
                </thead>
                <tbody>
                    {compliance_html if compliance_html else '<tr><td colspan="4">No compliance checks performed</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h3>⚠️ Sovereignty Findings</h3>
            <p style="color:#666;margin-bottom:1rem;">Identified risks and compliance issues</p>
            {findings_html if findings_html else '<p style="color:#28a745;font-weight:600;">✓ No sovereignty issues detected</p>'}
        </div>
        
        <div class="section" style="background:#f8f9fa;">
            <h3>📋 Recommendations</h3>
            <p style="color:#666;margin-bottom:1rem;">Actionable steps to improve sovereignty posture</p>
            {recommendations_html}
        </div>
        
        <div class="footer">
            <div class="footer-logo">DataGuardian Pro</div>
            <p class="footer-meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Processing Time: {result.processing_time_ms}ms</p>
            <div class="footer-badges">
                <span class="footer-badge">GDPR Compliant</span>
                <span class="footer-badge">EU AI Act Ready</span>
                <span class="footer-badge">Netherlands UAVG</span>
                <span class="footer-badge">Enterprise Grade</span>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return html
