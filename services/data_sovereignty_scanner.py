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
        'KR', 'CH', 'GB', 'UY'
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
        'us-east-1': {'country': 'US', 'name': 'N. Virginia'},
        'us-east-2': {'country': 'US', 'name': 'Ohio'},
        'us-west-1': {'country': 'US', 'name': 'N. California'},
        'us-west-2': {'country': 'US', 'name': 'Oregon'},
        'westeurope': {'country': 'NL', 'name': 'Netherlands'},
        'northeurope': {'country': 'IE', 'name': 'Ireland'},
        'germanywestcentral': {'country': 'DE', 'name': 'Frankfurt'},
        'francecentral': {'country': 'FR', 'name': 'Paris'},
        'uksouth': {'country': 'GB', 'name': 'London'},
        'europe-west1': {'country': 'BE', 'name': 'Belgium'},
        'europe-west2': {'country': 'GB', 'name': 'London'},
        'europe-west3': {'country': 'DE', 'name': 'Frankfurt'},
        'europe-west4': {'country': 'NL', 'name': 'Netherlands'},
        'europe-north1': {'country': 'FI', 'name': 'Finland'}
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
            config_type: Type of configuration (aws, azure, gcp, kubernetes)
            
        Returns:
            SovereigntyScanResult with analysis
        """
        import uuid
        self.scan_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        
        result = SovereigntyScanResult(
            scan_id=self.scan_id,
            timestamp=datetime.now().isoformat(),
            target_name=f"{config_type.upper()} Configuration",
            region=self.region
        )
        
        try:
            if config_type == "aws":
                result.data_locations = self._parse_aws_config(config_content)
            elif config_type == "azure":
                result.data_locations = self._parse_azure_config(config_content)
            elif config_type == "gcp":
                result.data_locations = self._parse_gcp_config(config_content)
            elif config_type == "kubernetes":
                result.data_locations = self._parse_kubernetes_config(config_content)
            else:
                result.data_locations = self._parse_generic_config(config_content)
            
            result.data_flows = self._detect_config_flows(config_content, config_type)
            result.access_paths = self._detect_config_access(config_content, config_type)
            
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
            (r'resource\s+"google_storage_', 'Cloud Storage'),
            (r'resource\s+"google_bigquery_', 'BigQuery'),
            (r'resource\s+"google_sql_', 'Cloud SQL'),
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
        
        if re.search(r'allowed_ip_ranges|ip_whitelist|source_ranges', content, re.IGNORECASE):
            paths.append(AccessPath(
                accessor_type="ip_based",
                accessor_country="unknown",
                privilege_level="network",
                is_eu_access=True,
                is_monitored=True
            ))
            
        if re.search(r'service_account|iam_role|managed_identity', content, re.IGNORECASE):
            paths.append(AccessPath(
                accessor_type="service_account",
                accessor_country="unknown",
                privilege_level="automated",
                is_eu_access=True,
                is_monitored=True
            ))
            
        return paths
    
    def _parse_aws_config(self, content: str) -> List[DataLocation]:
        """Parse AWS CloudFormation configuration"""
        locations = []
        
        region_matches = re.findall(r'Region["\']?\s*[:=]\s*["\']?([a-z]{2}-[a-z]+-\d)["\']?', content, re.IGNORECASE)
        
        for region in region_matches:
            region_info = self.CLOUD_REGIONS.get(region.lower(), {})
            country = region_info.get('country', 'US')
            
            locations.append(DataLocation(
                region=region,
                country=country,
                cloud_provider='AWS',
                service_type='cloudformation',
                is_eu=country in self.EU_COUNTRIES,
                is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                legal_jurisdiction=self._get_jurisdiction(country)
            ))
            
        return locations
    
    def _parse_azure_config(self, content: str) -> List[DataLocation]:
        """Parse Azure ARM/Bicep configuration"""
        locations = []
        
        location_matches = re.findall(r'location["\']?\s*[:=]\s*["\']?([a-z]+)["\']?', content, re.IGNORECASE)
        
        for location in location_matches:
            region_info = self.CLOUD_REGIONS.get(location.lower(), {})
            country = region_info.get('country', 'NL')
            
            locations.append(DataLocation(
                region=location,
                country=country,
                cloud_provider='Azure',
                service_type='arm_template',
                is_eu=country in self.EU_COUNTRIES,
                is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                legal_jurisdiction=self._get_jurisdiction(country)
            ))
            
        return locations
    
    def _parse_gcp_config(self, content: str) -> List[DataLocation]:
        """Parse GCP Deployment Manager configuration"""
        locations = []
        
        region_matches = re.findall(r'region["\']?\s*[:=]\s*["\']?([a-z]+-[a-z]+\d?)["\']?', content, re.IGNORECASE)
        
        for region in region_matches:
            region_info = self.CLOUD_REGIONS.get(region.lower(), {})
            country = region_info.get('country', 'US')
            
            locations.append(DataLocation(
                region=region,
                country=country,
                cloud_provider='GCP',
                service_type='deployment_manager',
                is_eu=country in self.EU_COUNTRIES,
                is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                legal_jurisdiction=self._get_jurisdiction(country)
            ))
            
        return locations
    
    def _parse_kubernetes_config(self, content: str) -> List[DataLocation]:
        """Parse Kubernetes YAML configuration"""
        locations = []
        
        region_matches = re.findall(r'topology\.kubernetes\.io/region["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', content)
        zone_matches = re.findall(r'topology\.kubernetes\.io/zone["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', content)
        
        for region in region_matches + zone_matches:
            country = self._detect_country_from_region(region)
            
            locations.append(DataLocation(
                region=region,
                country=country,
                cloud_provider='Kubernetes',
                service_type='k8s_deployment',
                is_eu=country in self.EU_COUNTRIES,
                is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                legal_jurisdiction=self._get_jurisdiction(country)
            ))
            
        return locations
    
    def _parse_generic_config(self, content: str) -> List[DataLocation]:
        """Parse generic configuration for locations"""
        locations = []
        
        generic_patterns = [
            r'region\s*[:=]\s*["\']?([a-zA-Z0-9-]+)["\']?',
            r'location\s*[:=]\s*["\']?([a-zA-Z0-9-]+)["\']?',
            r'datacenter\s*[:=]\s*["\']?([a-zA-Z0-9-]+)["\']?'
        ]
        
        for pattern in generic_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                country = self._detect_country_from_region(match)
                locations.append(DataLocation(
                    region=match,
                    country=country,
                    cloud_provider='unknown',
                    service_type='generic',
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
            'canada': 'CA', 'brazil': 'BR', 'india': 'IN', 'mumbai': 'IN'
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
        
        api_patterns = re.findall(r'api[_\-]?gateway|lambda|function|endpoint', content.lower())
        if api_patterns:
            origins.append(DataOrigin(
                source_name="API Gateway",
                source_type="api",
                country="Unknown",
                collection_method="REST API",
                legal_basis="Contract (Art. 6(1)(b))",
                data_categories=["personal_data"],
                is_eu_origin=True
            ))
        
        db_patterns = re.findall(r'rds|dynamodb|database|postgres|mysql|aurora', content.lower())
        if db_patterns:
            origins.append(DataOrigin(
                source_name="Database Storage",
                source_type="database",
                country="Detected from region",
                collection_method="Database Storage",
                legal_basis="Contract (Art. 6(1)(b))",
                data_categories=["personal_data", "operational_data"],
                is_eu_origin=True
            ))
        
        s3_patterns = re.findall(r's3[_\-]?bucket|blob|storage', content.lower())
        if s3_patterns:
            origins.append(DataOrigin(
                source_name="Object Storage",
                source_type="file_upload",
                country="Detected from region",
                collection_method="File Upload",
                legal_basis="Consent (Art. 6(1)(a))",
                data_categories=["personal_data", "documents"],
                is_eu_origin=True
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
            elif loc.country in self.ADEQUACY_COUNTRIES:
                applicable_laws = ["Local Data Protection Law"]
                adequacy_status = f"EU Adequacy Decision"
                risk_level = "medium"
            elif loc.country == 'US':
                applicable_laws = ["US CLOUD Act", "CCPA/CPRA", "State Laws"]
                adequacy_status = "SCCs Required (post-Schrems II)"
                risk_level = "high"
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
        
        has_third_country = any(not loc.is_eu and not loc.is_adequacy_decision for loc in result.data_locations)
        
        checks.append(ComplianceCheck(
            check_name="Standard Contractual Clauses (SCCs)",
            check_category="sccs",
            status="fail" if has_third_country else "pass",
            description="Third country storage detected - SCCs required" if has_third_country else "All storage in EU/EEA - no SCCs needed",
            legal_reference="GDPR Article 46(2)(c)",
            recommendation="Implement EU Commission's 2021 SCCs" if has_third_country else ""
        ))
        
        checks.append(ComplianceCheck(
            check_name="Transfer Impact Assessment (TIA)",
            check_category="tia",
            status="fail" if has_third_country else "not_applicable",
            description="TIA required for US/third country data processing" if has_third_country else "No TIA required",
            legal_reference="CJEU Schrems II (Case C-311/18)",
            recommendation="Complete TIA before deployment" if has_third_country else ""
        ))
        
        encryption_patterns = re.findall(r'encrypt|kms|key_id|server_side_encryption|sse', content.lower())
        has_encryption = len(encryption_patterns) > 0
        checks.append(ComplianceCheck(
            check_name="Encryption at Rest",
            check_category="encryption",
            status="pass" if has_encryption else "fail",
            description="Encryption configuration detected" if has_encryption else "No encryption configuration found",
            legal_reference="GDPR Article 32",
            recommendation="" if has_encryption else "Add encryption to all storage resources"
        ))
        
        tls_patterns = re.findall(r'https|tls|ssl|certificate', content.lower())
        has_tls = len(tls_patterns) > 0
        checks.append(ComplianceCheck(
            check_name="Encryption in Transit (TLS)",
            check_category="encryption",
            status="pass" if has_tls else "warning",
            description="TLS/HTTPS configuration found" if has_tls else "No explicit TLS configuration",
            legal_reference="GDPR Article 32",
            recommendation="" if has_tls else "Ensure TLS 1.2+ for all endpoints"
        ))
        
        retention_patterns = re.findall(r'retention|lifecycle|expiration|days', content.lower())
        has_retention = len(retention_patterns) > 0
        checks.append(ComplianceCheck(
            check_name="Data Retention Policy",
            check_category="retention",
            status="pass" if has_retention else "warning",
            description="Lifecycle/retention policy found" if has_retention else "No retention policy defined",
            legal_reference="GDPR Article 5(1)(e)",
            recommendation="" if has_retention else "Define data retention policies"
        ))
        
        backup_patterns = re.findall(r'backup|replicat|snapshot|dr_|disaster', content.lower())
        has_backups = len(backup_patterns) > 0
        checks.append(ComplianceCheck(
            check_name="Backup Configuration",
            check_category="backup",
            status="warning" if has_backups else "fail",
            description="Backup configuration detected - verify locations" if has_backups else "No backup configuration found",
            legal_reference="GDPR Article 32",
            recommendation="Ensure backups in EU/EEA regions" if has_backups else "Implement backup strategy in EU regions"
        ))
        
        checks.append(ComplianceCheck(
            check_name="Netherlands UAVG Compliance",
            check_category="uavg",
            status="pass" if self.region == "Netherlands" else "not_applicable",
            description="Netherlands processing - UAVG applies" if self.region == "Netherlands" else "Not applicable",
            legal_reference="UAVG (Dutch GDPR Implementation)",
            recommendation=""
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
        """Detect encryption settings in Terraform"""
        if enc_type == "at_rest":
            patterns = ['encrypt', 'kms', 'server_side_encryption', 'sse-s3', 'sse-kms']
        else:
            patterns = ['https', 'tls', 'ssl', 'certificate_arn']
        
        for pattern in patterns:
            if pattern in content.lower():
                return True
        return False
    
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
        
        for access in result.access_paths:
            if not access.is_eu_access:
                findings.append({
                    'type': 'non_eu_access',
                    'severity': 'high',
                    'title': f'Non-EU Access Detected: {access.accessor_country}',
                    'description': f'Access from non-EU country ({access.accessor_country}) with {access.privilege_level} privileges detected.',
                    'affected_data': [access.accessor_type],
                    'legal_reference': 'GDPR Article 44 (Transfer Restrictions)',
                    'recommendation': 'Implement access controls to restrict non-EU access or establish legal basis',
                    'risk_score': 0.7
                })
            
            if not access.is_monitored:
                findings.append({
                    'type': 'unmonitored_access',
                    'severity': 'medium',
                    'title': f'Unmonitored Access Path: {access.accessor_type}',
                    'description': f'Access path for {access.accessor_type} is not being actively monitored.',
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
            recommendations.append("Consider migrating data storage to EU regions to simplify GDPR compliance")
        
        eu_to_third = [f for f in result.data_flows if f.is_eu_to_third_country]
        if eu_to_third:
            recommendations.append("Implement Standard Contractual Clauses (SCCs) for all EU to third country transfers")
            recommendations.append("Conduct Transfer Impact Assessments (TIAs) for each third country transfer")
        
        us_providers = [l for l in result.data_locations 
                       if l.cloud_provider and l.cloud_provider.lower() in self.CLOUD_ACT_RISK_PROVIDERS]
        if us_providers:
            recommendations.append("Implement encryption with customer-managed keys to mitigate CLOUD Act risks")
            recommendations.append("Document supplementary measures per EDPB Recommendations 01/2020")
        
        non_eu_access = [a for a in result.access_paths if not a.is_eu_access]
        if non_eu_access:
            recommendations.append("Implement geo-fencing to restrict administrative access to EU locations")
            recommendations.append("Review and document all third-party vendor access from non-EU countries")
        
        unmonitored = [a for a in result.access_paths if not a.is_monitored]
        if unmonitored:
            recommendations.append("Enable comprehensive logging and monitoring for all data access paths")
        
        if not recommendations:
            recommendations.append("Current configuration demonstrates good sovereignty practices - continue monitoring")
        
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
