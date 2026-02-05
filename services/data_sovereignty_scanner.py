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
class SovereigntyScanResult:
    """Complete scan result"""
    scan_id: str
    scan_type: str = "Data Sovereignty Scanner"
    timestamp: str = ""
    target_name: str = ""
    data_locations: List[DataLocation] = field(default_factory=list)
    data_flows: List[DataFlow] = field(default_factory=list)
    access_paths: List[AccessPath] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    sovereignty_risk_score: float = 0.0
    risk_level: SovereigntyRiskLevel = SovereigntyRiskLevel.GREEN
    recommendations: List[str] = field(default_factory=list)
    cross_border_transfers: int = 0
    non_eu_access_count: int = 0
    third_country_processors: int = 0
    processing_time_ms: int = 0
    region: str = "Netherlands"


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
        
        region_patterns = [
            r'region\s*=\s*["\']([^"\']+)["\']',
            r'location\s*=\s*["\']([^"\']+)["\']',
            r'zone\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in region_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for region in matches:
                region_info = self.CLOUD_REGIONS.get(region.lower(), {})
                country = region_info.get('country', self._detect_country_from_region(region))
                
                provider = 'unknown'
                if 'aws_' in content.lower():
                    provider = 'AWS'
                elif 'azurerm_' in content.lower():
                    provider = 'Azure'
                elif 'google_' in content.lower():
                    provider = 'GCP'
                
                location = DataLocation(
                    region=region,
                    country=country,
                    cloud_provider=provider,
                    service_type='terraform_resource',
                    is_eu=country in self.EU_COUNTRIES,
                    is_adequacy_decision=country in self.ADEQUACY_COUNTRIES,
                    legal_jurisdiction=self._get_jurisdiction(country)
                )
                locations.append(location)
                
        return locations
    
    def _detect_terraform_flows(self, content: str) -> List[DataFlow]:
        """Detect data flows from Terraform configuration"""
        flows = []
        
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
                    source_country="NL",
                    destination_country=dest_country,
                    is_cross_border=dest_country != "NL",
                    is_eu_to_third_country=dest_country not in self.EU_COUNTRIES and dest_country not in self.ADEQUACY_COUNTRIES,
                    flow_type="replication"
                )
                flows.append(flow)
                
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
            <h3>📍 Data Locations</h3>
            <p style="color:#666;margin-bottom:1rem;">Detected storage locations and their jurisdictional classification</p>
            {locations_html if locations_html else '<p style="color:#888;">No specific locations detected in configuration</p>'}
        </div>
        
        <div class="section">
            <h3>🔄 Data Flows</h3>
            <p style="color:#666;margin-bottom:1rem;">Detected data transfer paths between systems and regions</p>
            {flows_html if flows_html else '<p style="color:#888;">No cross-border flows detected</p>'}
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
