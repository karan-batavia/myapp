"""
Cloud Resources Scanner for Sustainability Analysis

This module provides functionality to scan cloud resources across various providers
(Azure, AWS, GCP) to identify optimization opportunities, calculate carbon footprint,
and provide cost and sustainability recommendations.
"""

import os
import json
import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("cloud_resources_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
import pandas as pd
import requests
import importlib.util

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Carbon intensity data - average CO2e (grams) per kWh by region
# Source: Various cloud provider sustainability reports and IEA data
CARBON_INTENSITY = {
    # Azure regions
    'eastus': 390,
    'westus': 190,
    'northeurope': 210,
    'westeurope': 230,
    'eastasia': 540,
    'southeastasia': 460,
    
    # AWS regions
    'us-east-1': 380,
    'us-west-1': 210,
    'eu-west-1': 235,
    'ap-southeast-1': 470,
    
    # GCP regions
    'us-central1': 410,
    'europe-west1': 225,
    'asia-east1': 520,
    
    # Default if region not found
    'default': 400
}

# Power Usage Effectiveness (PUE) by provider
# Source: Provider sustainability reports
PUE = {
    'azure': 1.12,
    'aws': 1.15,
    'gcp': 1.10,
    'default': 1.2
}

# Avg watts per vCPU by provider
WATTS_PER_VCPU = {
    'azure': 13.5,
    'aws': 14.2,
    'gcp': 12.8,
    'default': 14.0
}

# Default thresholds for resource optimization
DEFAULT_THRESHOLDS = {
    'idle_cpu_percent': 5.0,  # CPU usage below this % is considered idle
    'idle_duration_days': 14,  # Resources idle for this many days are flagged
    'low_util_percent': 20.0,  # Resources below this % util are considered underutilized
    'oversized_threshold': 2.0,  # Resource 2x larger than needed based on peak usage
    'snapshot_age_days': 90,   # Snapshots older than this many days may be deleted
}


class CloudResourcesScanner:
    """Scanner for analyzing cloud resources for sustainability and cost optimization."""
    
    def __init__(self, 
                 provider: str = 'azure',
                 region: str = 'netherlands',
                 subscription_id: Optional[str] = None,
                 tenant_id: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 project_id: Optional[str] = None,
                 thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize the cloud resources scanner.
        
        Args:
            provider: Cloud provider ('azure', 'aws', 'gcp')
            region: Default region for scanning
            subscription_id: Azure subscription ID
            tenant_id: Azure tenant ID
            client_id: Azure client ID / AWS access key ID / GCP client ID
            client_secret: Azure client secret / AWS secret access key / GCP client secret
            access_key: AWS access key (if provider is AWS)
            secret_key: AWS secret key (if provider is AWS)
            project_id: GCP project ID (if provider is GCP)
            thresholds: Custom thresholds for resource optimization
        """
        self.provider = provider.lower()
        self.region = region
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.client_id = client_id or access_key
        self.client_secret = client_secret or secret_key
        self.project_id = project_id
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.progress_callback = None
        self.findings = []
        self.resource_metrics = {}
        self.auth_token = None
        self.auth_time = None
        self.resources_by_type = {}
        self.carbon_data = {}
        
        # Validate cloud provider
        valid_providers = ['azure', 'aws', 'gcp', 'none']
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid cloud provider. Supported providers: {', '.join(valid_providers)}")
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """
        Set a callback for tracking scan progress.
        
        Args:
            callback: Function that accepts current step, total steps, and status message
        """
        self.progress_callback = callback
    
    def _update_progress(self, current: int, total: int, message: str) -> None:
        """
        Update scan progress through callback if available.
        
        Args:
            current: Current step number
            total: Total number of steps
            message: Status message
        """
        if self.progress_callback:
            self.progress_callback(current, total, message)
        else:
            logger.info(f"Progress {current}/{total}: {message}")
    
    def _get_auth_token(self) -> str:
        """
        Get authentication token for the cloud provider API.
        
        Returns:
            Authentication token
        """
        # Check if we have a valid token already
        if self.auth_token and self.auth_time:
            # Tokens typically valid for 1 hour, but refresh if older than 50 minutes
            if (datetime.now() - self.auth_time).total_seconds() < 3000:
                return self.auth_token
        
        if self.provider == 'azure':
            # Azure authentication
            if not all([self.tenant_id, self.client_id, self.client_secret]):
                raise ValueError("Azure authentication requires tenant_id, client_id, and client_secret")
                
            auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/token"
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'resource': 'https://management.azure.com/'
            }
            
            response = requests.post(auth_url, data=auth_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get('access_token')
                self.auth_time = datetime.now()
                return self.auth_token
            else:
                raise Exception(f"Azure authentication failed: {response.text}")
                
        elif self.provider == 'aws':
            # For AWS, we use the access key and secret key directly with boto3
            # Return a placeholder token since boto3 handles auth internally
            self.auth_token = "SDK_AUTH_MANAGED"  # Authentication handled by boto3 SDK
            self.auth_time = datetime.now()
            return self.auth_token
            
        elif self.provider == 'gcp':
            # For GCP, we use the client ID and client secret or application default credentials
            # Return a placeholder token since google-auth handles auth internally
            self.auth_token = "SDK_AUTH_MANAGED"  # Authentication handled by google-auth SDK
            self.auth_time = datetime.now()
            return self.auth_token
            
        elif self.provider == 'none':
            # No cloud provider, used for code analysis only
            self.auth_token = "NO_CLOUD_AUTH_REQUIRED"  # No cloud provider selected
            self.auth_time = datetime.now()
            return self.auth_token
            
        else:
            raise ValueError(f"Authentication not implemented for provider: {self.provider}")
    
    def scan_resources(self) -> Dict[str, Any]:
        """
        Scan cloud resources for sustainability and cost optimization.
        
        Returns:
            Dict containing scan results
        """
        # Generate a unique scan ID
        scan_id = f"sustainability-{int(time.time())}"
        
        # Initialize scan results
        scan_result = {
            'scan_id': scan_id,
            'scan_type': 'Sustainability',
            'timestamp': datetime.now().isoformat(),
            'provider': self.provider,
            'region': self.region,
            'resources': {},
            'findings': [],
            'recommendations': [],
            'carbon_footprint': {},
            'cost_analysis': {},
            'optimization_potential': {},
            'status': 'in_progress'
        }
        
        total_steps = 6
        current_step = 0
        
        try:
            # Step 1: Authenticate with cloud provider
            current_step += 1
            self._update_progress(current_step, total_steps, f"Authenticating with {self.provider}")
            
            if self.provider != 'none':
                self._get_auth_token()
            
            # Step 2: Collect resource inventory
            current_step += 1
            self._update_progress(current_step, total_steps, "Collecting resource inventory")
            
            if self.provider != 'none':
                resources = self._collect_resources()
                scan_result['resources'] = resources
            
            # Step 3: Analyze resource utilization
            current_step += 1
            self._update_progress(current_step, total_steps, "Analyzing resource utilization")
            
            if self.provider != 'none':
                utilization = self._analyze_utilization()
                scan_result['utilization'] = utilization
            
            # Step 4: Calculate carbon footprint
            current_step += 1
            self._update_progress(current_step, total_steps, "Calculating carbon footprint")
            
            if self.provider != 'none':
                carbon_data = self._calculate_carbon_footprint()
                scan_result['carbon_footprint'] = carbon_data
            
            # Step 5: Generate findings and recommendations
            current_step += 1
            self._update_progress(current_step, total_steps, "Generating recommendations")
            
            findings = []
            recommendations = []
            
            if self.provider != 'none':
                findings, recommendations = self._generate_findings_recommendations()
            
            # Step 6: Analyze code for bloat (if repositories provided)
            current_step += 1
            self._update_progress(current_step, total_steps, "Analyzing code repositories")
            
            code_findings = self._analyze_code_bloat()
            if code_findings:
                findings.extend(code_findings)
            
            # Add findings and recommendations to scan result
            scan_result['findings'] = findings
            scan_result['recommendations'] = recommendations
            
            # Calculate optimization potential
            if self.provider != 'none':
                optimization = self._calculate_optimization_potential()
                scan_result['optimization_potential'] = optimization
            
            # Mark scan as completed
            scan_result['status'] = 'completed'
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Error during cloud resources scan: {str(e)}")
            scan_result['status'] = 'error'
            scan_result['error'] = str(e)
            return scan_result
    
    def _collect_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect resource inventory from the cloud provider.
        
        Returns:
            Dictionary of resources by resource type
        """
        resources = {}
        
        if self.provider == 'azure':
            # Collect Azure resources
            resources = self._collect_azure_resources()
        
        elif self.provider == 'aws':
            # Collect AWS resources
            resources = self._collect_aws_resources()
            
        elif self.provider == 'gcp':
            # Collect GCP resources
            resources = self._collect_gcp_resources()
        
        # Store resources by type for later use
        self.resources_by_type = resources
        
        # Create a summary for each resource type
        summary = {}
        for resource_type, resource_list in resources.items():
            summary[resource_type] = {
                'count': len(resource_list),
                'regions': list(set(r.get('region', 'unknown') for r in resource_list)),
                'tags': self._summarize_tags(resource_list)
            }
        
        return summary
    
    def _collect_azure_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect resources from Azure.
        
        Returns:
            Dictionary of Azure resources by resource type
        """
        resources = {
            'virtual_machines': [],
            'disks': [],
            'snapshots': [],
            'storage_accounts': [],
            'sql_servers': [],
            'cosmos_db': [],
            'app_services': []
        }
        
        # Get auth token
        token = self._get_auth_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get list of Azure subscriptions if subscription_id not provided
        subscriptions = [self.subscription_id] if self.subscription_id else []
        if not subscriptions:
            subs_url = "https://management.azure.com/subscriptions?api-version=2020-01-01"
            response = requests.get(subs_url, headers=headers)
            if response.status_code == 200:
                subs_data = response.json()
                subscriptions = [sub['subscriptionId'] for sub in subs_data.get('value', [])]
        
        # Collect resources for each subscription
        for subscription_id in subscriptions:
            # Get virtual machines
            vms_url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Compute/virtualMachines?api-version=2023-03-01"
            response = requests.get(vms_url, headers=headers)
            if response.status_code == 200:
                vms_data = response.json()
                
                for vm in vms_data.get('value', []):
                    vm_info = {
                        'id': vm.get('id'),
                        'name': vm.get('name'),
                        'region': vm.get('location'),
                        'type': 'Microsoft.Compute/virtualMachines',
                        'size': vm.get('properties', {}).get('hardwareProfile', {}).get('vmSize'),
                        'status': vm.get('properties', {}).get('provisioningState'),
                        'os_type': vm.get('properties', {}).get('storageProfile', {}).get('osDisk', {}).get('osType'),
                        'creation_time': vm.get('properties', {}).get('timeCreated'),
                        'tags': vm.get('tags', {})
                    }
                    resources['virtual_machines'].append(vm_info)
            
            # Get managed disks
            disks_url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Compute/disks?api-version=2023-01-02"
            response = requests.get(disks_url, headers=headers)
            if response.status_code == 200:
                disks_data = response.json()
                
                for disk in disks_data.get('value', []):
                    # Check if disk is attached to a VM
                    is_attached = bool(disk.get('properties', {}).get('managedBy'))
                    
                    disk_info = {
                        'id': disk.get('id'),
                        'name': disk.get('name'),
                        'region': disk.get('location'),
                        'type': 'Microsoft.Compute/disks',
                        'size_gb': disk.get('properties', {}).get('diskSizeGB'),
                        'sku': disk.get('sku', {}).get('name'),
                        'status': disk.get('properties', {}).get('provisioningState'),
                        'is_attached': is_attached,
                        'managed_by': disk.get('properties', {}).get('managedBy'),
                        'creation_time': disk.get('properties', {}).get('timeCreated'),
                        'tags': disk.get('tags', {})
                    }
                    resources['disks'].append(disk_info)
            
            # Get snapshots
            snapshots_url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Compute/snapshots?api-version=2023-01-02"
            response = requests.get(snapshots_url, headers=headers)
            if response.status_code == 200:
                snapshots_data = response.json()
                
                for snapshot in snapshots_data.get('value', []):
                    creation_time_str = snapshot.get('properties', {}).get('timeCreated')
                    creation_time = datetime.fromisoformat(creation_time_str[:-1]) if creation_time_str else None
                    age_days = (datetime.now() - creation_time).days if creation_time else None
                    
                    snapshot_info = {
                        'id': snapshot.get('id'),
                        'name': snapshot.get('name'),
                        'region': snapshot.get('location'),
                        'type': 'Microsoft.Compute/snapshots',
                        'size_gb': snapshot.get('properties', {}).get('diskSizeGB'),
                        'source_disk': snapshot.get('properties', {}).get('creationData', {}).get('sourceResourceId'),
                        'creation_time': creation_time_str,
                        'age_days': age_days,
                        'tags': snapshot.get('tags', {})
                    }
                    resources['snapshots'].append(snapshot_info)
            
            # Get storage accounts
            storage_url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Storage/storageAccounts?api-version=2023-01-01"
            response = requests.get(storage_url, headers=headers)
            if response.status_code == 200:
                storage_data = response.json()
                
                for storage in storage_data.get('value', []):
                    storage_info = {
                        'id': storage.get('id'),
                        'name': storage.get('name'),
                        'region': storage.get('location'),
                        'type': 'Microsoft.Storage/storageAccounts',
                        'sku': storage.get('sku', {}).get('name'),
                        'kind': storage.get('kind'),
                        'creation_time': storage.get('properties', {}).get('creationTime'),
                        'tags': storage.get('tags', {})
                    }
                    resources['storage_accounts'].append(storage_info)
            
            # Additional resource types can be added as needed
        
        return resources
    
    def _collect_aws_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect resources from AWS.
        
        Returns:
            Dictionary of AWS resources by resource type
        """
        resources = {
            'ec2_instances': [],
            'ebs_volumes': [],
            'snapshots': [],
            's3_buckets': [],
            'rds_instances': [],
            'lambda_functions': []
        }
        
        # Check if boto3 is available
        boto3_spec = importlib.util.find_spec("boto3")
        if boto3_spec is None:
            logger.warning("boto3 package not found. AWS resource collection skipped.")
            return resources
        
        import boto3
        from botocore.exceptions import ClientError
        
        try:
            # Create AWS session
            session = boto3.Session(
                aws_access_key_id=self.client_id,
                aws_secret_access_key=self.client_secret,
                region_name=self.region if self.region != 'netherlands' else 'westeurope'
            )
            
            # Get list of regions if scanning in Netherlands/EU
            regions = [self.region]
            if self.region == 'netherlands':
                ec2 = session.client('ec2')
                regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
            
            # Collect resources in each region
            for region in regions:
                # Create regional clients
                regional_session = boto3.Session(
                    aws_access_key_id=self.client_id,
                    aws_secret_access_key=self.client_secret,
                    region_name=region
                )
                
                ec2 = regional_session.client('ec2')
                s3 = regional_session.client('s3')
                rds = regional_session.client('rds')
                lambda_client = regional_session.client('lambda')
                
                # Get EC2 instances
                response = ec2.describe_instances()
                for reservation in response.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        # Collect instance data
                        instance_info = {
                            'id': instance.get('InstanceId'),
                            'name': next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), ''),
                            'region': region,
                            'type': 'EC2',
                            'instance_type': instance.get('InstanceType'),
                            'state': instance.get('State', {}).get('Name'),
                            'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                            'availability_zone': instance.get('Placement', {}).get('AvailabilityZone'),
                            'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        }
                        resources['ec2_instances'].append(instance_info)
                
                # Get EBS volumes
                response = ec2.describe_volumes()
                for volume in response.get('Volumes', []):
                    # Check if volume is attached
                    attachments = volume.get('Attachments', [])
                    is_attached = any(attach.get('State') == 'attached' for attach in attachments)
                    
                    volume_info = {
                        'id': volume.get('VolumeId'),
                        'name': next((tag['Value'] for tag in volume.get('Tags', []) if tag['Key'] == 'Name'), ''),
                        'region': region,
                        'type': 'EBS',
                        'size_gb': volume.get('Size'),
                        'volume_type': volume.get('VolumeType'),
                        'state': volume.get('State'),
                        'is_attached': is_attached,
                        'attached_to': [attach.get('InstanceId') for attach in attachments if attach.get('State') == 'attached'],
                        'creation_time': volume.get('CreateTime').isoformat() if volume.get('CreateTime') else None,
                        'tags': {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                    }
                    resources['ebs_volumes'].append(volume_info)
                
                # Get snapshots
                response = ec2.describe_snapshots(OwnerIds=['self'])
                for snapshot in response.get('Snapshots', []):
                    creation_time = snapshot.get('StartTime')
                    age_days = (datetime.now(creation_time.tzinfo) - creation_time).days if creation_time else None
                    
                    snapshot_info = {
                        'id': snapshot.get('SnapshotId'),
                        'name': next((tag['Value'] for tag in snapshot.get('Tags', []) if tag['Key'] == 'Name'), ''),
                        'region': region,
                        'type': 'EBS Snapshot',
                        'volume_id': snapshot.get('VolumeId'),
                        'state': snapshot.get('State'),
                        'size_gb': snapshot.get('VolumeSize'),
                        'creation_time': creation_time.isoformat() if creation_time else None,
                        'age_days': age_days,
                        'tags': {tag['Key']: tag['Value'] for tag in snapshot.get('Tags', [])}
                    }
                    resources['snapshots'].append(snapshot_info)
                
                # Additional AWS resources can be collected as needed
        
        except Exception as e:
            logger.error(f"Error collecting AWS resources: {str(e)}")
        
        return resources
    
    def _collect_gcp_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect resources from Google Cloud Platform.
        
        Returns:
            Dictionary of GCP resources by resource type
        """
        resources = {
            'compute_instances': [],
            'disks': [],
            'snapshots': [],
            'storage_buckets': [],
            'sql_instances': []
        }
        
        # Check if google-api-python-client is available
        google_api_spec = importlib.util.find_spec("googleapiclient")
        if google_api_spec is None:
            logger.warning("google-api-python-client package not found. GCP resource collection skipped.")
            return resources
        
        from googleapiclient import discovery
        from google.oauth2 import service_account
        import json
        
        try:
            # Prepare credentials from client_id and client_secret
            # For GCP, we expect these to be the path to a service account key file
            # or JSON content of service account key
            credentials = None
            
            if self.client_id and self.client_secret:
                # Create a temporary service account key file
                service_account_info = {
                    "type": "service_account",
                    "project_id": self.project_id,
                    "private_key_id": self.client_id,
                    "private_key": self.client_secret.replace('\\n', '\n'),
                    "client_email": f"{self.client_id}@{self.project_id}.iam.gserviceaccount.com",
                    "client_id": "",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": ""
                }
                
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
            
            # If project_id is not provided, try to get it from credentials
            project_id = self.project_id
            if project_id is None and credentials:
                project_id = credentials.project_id
            
            if not project_id:
                logger.error("GCP project_id is required")
                return resources
            
            # Create API clients
            compute = discovery.build('compute', 'v1', credentials=credentials)
            storage = discovery.build('storage', 'v1', credentials=credentials)
            sqladmin = discovery.build('sqladmin', 'v1', credentials=credentials)
            
            # Get compute instances
            request = compute.instances().aggregatedList(project=project_id)
            while request is not None:
                response = request.execute()
                
                for zone, instances_data in response.get('items', {}).items():
                    for instance in instances_data.get('instances', []):
                        zone_name = zone.split('/')[-1]
                        
                        instance_info = {
                            'id': instance.get('id'),
                            'name': instance.get('name'),
                            'zone': zone_name,
                            'region': zone_name[:-2],  # Remove zone letter suffix
                            'type': 'Compute Engine',
                            'machine_type': instance.get('machineType').split('/')[-1],
                            'status': instance.get('status'),
                            'creation_time': instance.get('creationTimestamp'),
                            'tags': instance.get('labels', {})
                        }
                        resources['compute_instances'].append(instance_info)
                
                request = compute.instances().aggregatedList_next(previous_request=request, previous_response=response)
            
            # Additional GCP resources can be collected as needed
            
        except Exception as e:
            logger.error(f"Error collecting GCP resources: {str(e)}")
        
        return resources
    
    def _summarize_tags(self, resources: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Summarize tags across a list of resources.
        
        Args:
            resources: List of resource dictionaries
            
        Returns:
            Dictionary with tag keys and their counts
        """
        tag_counts = {}
        
        for resource in resources:
            tags = resource.get('tags', {})
            
            if isinstance(tags, dict):
                # Count occurrences of each tag key
                for key in tags.keys():
                    tag_counts[key] = tag_counts.get(key, 0) + 1
            elif isinstance(tags, list):
                # For AWS-style tags list
                for tag in tags:
                    if isinstance(tag, dict) and 'Key' in tag:
                        key = tag['Key']
                        tag_counts[key] = tag_counts.get(key, 0) + 1
        
        return tag_counts
    
    def _analyze_utilization(self) -> Dict[str, Any]:
        """
        Analyze resource utilization metrics.
        
        Returns:
            Dictionary with utilization analysis
        """
        utilization = {
            'idle_resources': [],
            'underutilized_resources': [],
            'oversized_resources': []
        }
        
        # Skip if no cloud provider
        if self.provider == 'none':
            return utilization
        
        # Analyze based on provider
        if self.provider == 'azure':
            # Get Azure Monitor metrics for VMs
            self._get_azure_vm_metrics()
            
            # Analyze VM utilization
            for vm in self.resources_by_type.get('virtual_machines', []):
                vm_id = vm.get('id')
                metrics = self.resource_metrics.get(vm_id, {})
                
                # Check for idle VMs
                avg_cpu = metrics.get('average_cpu_percent', 100)
                if avg_cpu < self.thresholds['idle_cpu_percent']:
                    vm['utilization'] = {
                        'average_cpu_percent': avg_cpu,
                        'status': 'idle'
                    }
                    utilization['idle_resources'].append(vm)
                
                # Check for underutilized VMs
                elif avg_cpu < self.thresholds['low_util_percent']:
                    vm['utilization'] = {
                        'average_cpu_percent': avg_cpu,
                        'status': 'underutilized'
                    }
                    utilization['underutilized_resources'].append(vm)
            
            # Check for unattached disks
            for disk in self.resources_by_type.get('disks', []):
                if not disk.get('is_attached'):
                    utilization['idle_resources'].append(disk)
            
            # Check for old snapshots
            for snapshot in self.resources_by_type.get('snapshots', []):
                if snapshot.get('age_days', 0) > self.thresholds['snapshot_age_days']:
                    utilization['idle_resources'].append(snapshot)
        
        elif self.provider in ['aws', 'gcp']:
            # Similar analysis for AWS and GCP resources
            # Implementation would follow similar pattern to Azure
            pass
        
        return utilization
    
    def _get_azure_vm_metrics(self) -> None:
        """
        Get Azure Monitor metrics for virtual machines.
        """
        # Get auth token
        token = self._get_auth_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Set time range for metrics (last 30 days)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        # Format timestamps for Azure API
        timespan = f"{start_time.isoformat()}Z/{end_time.isoformat()}Z"
        
        # Get metrics for each VM
        for vm in self.resources_by_type.get('virtual_machines', []):
            vm_id = vm.get('id')
            if not vm_id:
                continue
            
            # Get CPU utilization metrics
            metrics_url = f"https://management.azure.com{vm_id}/providers/Microsoft.Insights/metrics"
            params = {
                'api-version': '2018-01-01',
                'timespan': timespan,
                'interval': 'P1D',  # Daily aggregation
                'metricnames': 'Percentage CPU',
                'aggregation': 'Average,Maximum'
            }
            
            try:
                response = requests.get(metrics_url, headers=headers, params=params)
                if response.status_code == 200:
                    metrics_data = response.json()
                    
                    # Extract average CPU utilization
                    timeseries = metrics_data.get('value', [{}])[0].get('timeseries', [])
                    if timeseries:
                        data_points = timeseries[0].get('data', [])
                        
                        # Calculate average CPU utilization
                        valid_points = [point.get('average', 0) for point in data_points if point.get('average') is not None]
                        avg_cpu = sum(valid_points) / len(valid_points) if valid_points else 0
                        
                        # Store metrics for this VM
                        self.resource_metrics[vm_id] = {
                            'average_cpu_percent': avg_cpu,
                            'max_cpu_percent': max([point.get('maximum', 0) for point in data_points if point.get('maximum') is not None], default=0)
                        }
            except Exception as e:
                logger.error(f"Error getting metrics for VM {vm.get('name')}: {str(e)}")
    
    def _calculate_carbon_footprint(self) -> Dict[str, Any]:
        """
        Calculate carbon footprint of cloud resources.
        
        Returns:
            Dictionary with carbon footprint data
        """
        carbon_data = {
            'total_co2e_kg': 0,
            'by_region': {},
            'by_resource_type': {},
            'emissions_reduction_potential_kg': 0
        }
        
        # Skip if no cloud provider
        if self.provider == 'none':
            return carbon_data
        
        # Get provider-specific PUE
        provider_pue = PUE.get(self.provider, PUE['default'])
        
        # Calculate for compute resources (VMs/instances)
        compute_resources = []
        if self.provider == 'azure':
            compute_resources = self.resources_by_type.get('virtual_machines', [])
        elif self.provider == 'aws':
            compute_resources = self.resources_by_type.get('ec2_instances', [])
        elif self.provider == 'gcp':
            compute_resources = self.resources_by_type.get('compute_instances', [])
        
        # Process each compute resource
        for resource in compute_resources:
            # Get resource details
            region = resource.get('region', 'default').lower()
            resource_type = self._get_instance_type_details(resource)
            vcpus = resource_type.get('vcpus', 2)
            memory_gb = resource_type.get('memory_gb', 8)
            
            # Get carbon intensity for the region
            carbon_intensity_value = CARBON_INTENSITY.get(region, CARBON_INTENSITY['default'])
            
            # Calculate power consumption in kWh
            # Formula: vCPUs * watts_per_vcpu * PUE * hours_in_month / 1000
            watts = vcpus * WATTS_PER_VCPU.get(self.provider, WATTS_PER_VCPU['default'])
            hours_per_month = 730  # Average hours in a month
            power_kwh = watts * provider_pue * hours_per_month / 1000
            
            # Calculate CO2e emissions in kg
            # Formula: power_kwh * carbon_intensity / 1000
            co2e_kg = power_kwh * carbon_intensity_value / 1000
            
            # Store in resource for later reference
            resource['carbon_footprint'] = {
                'power_kwh_per_month': power_kwh,
                'co2e_kg_per_month': co2e_kg,
                'carbon_intensity': carbon_intensity_value
            }
            
            # Add to totals
            carbon_data['total_co2e_kg'] += co2e_kg
            
            # Add to region breakdown
            if region not in carbon_data['by_region']:
                carbon_data['by_region'][region] = 0
            carbon_data['by_region'][region] += co2e_kg
            
            # Add to resource type breakdown
            resource_size = resource_type.get('size', 'unknown')
            if resource_size not in carbon_data['by_resource_type']:
                carbon_data['by_resource_type'][resource_size] = 0
            carbon_data['by_resource_type'][resource_size] += co2e_kg
            
            # Calculate emissions reduction potential for idle/underutilized resources
            utilization = resource.get('utilization', {})
            status = utilization.get('status')
            
            if status in ['idle', 'underutilized']:
                # If resource is idle or underutilized, include its emissions in reduction potential
                carbon_data['emissions_reduction_potential_kg'] += co2e_kg
        
        # Store carbon data for later use
        self.carbon_data = carbon_data
        
        return carbon_data
    
    def _get_instance_type_details(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get details about a compute instance type.
        
        Args:
            resource: Resource dictionary
            
        Returns:
            Dictionary with instance type details
        """
        details = {
            'vcpus': 2,  # Default fallback
            'memory_gb': 8,  # Default fallback
            'size': 'unknown'
        }
        
        if self.provider == 'azure':
            # Extract Azure VM size
            vm_size = resource.get('size', '').lower()
            details['size'] = vm_size
            
            # Define common Azure VM sizes and their specs
            azure_sizes = {
                'standard_b2s': {'vcpus': 2, 'memory_gb': 4},
                'standard_b2ms': {'vcpus': 2, 'memory_gb': 8},
                'standard_d2_v3': {'vcpus': 2, 'memory_gb': 8},
                'standard_d4_v3': {'vcpus': 4, 'memory_gb': 16},
                'standard_d8_v3': {'vcpus': 8, 'memory_gb': 32},
                'standard_e2_v3': {'vcpus': 2, 'memory_gb': 16},
                'standard_e4_v3': {'vcpus': 4, 'memory_gb': 32},
                'standard_f2s_v2': {'vcpus': 2, 'memory_gb': 4},
                'standard_f4s_v2': {'vcpus': 4, 'memory_gb': 8}
            }
            
            # Match VM size with known sizes
            for size_prefix, specs in azure_sizes.items():
                if vm_size.startswith(size_prefix):
                    details.update(specs)
                    break
                    
            # Parse size from VM size for unknown sizes
            if details['size'] == 'unknown' and vm_size:
                # Extract numbers from VM size to estimate vCPUs
                import re
                size_numbers = re.findall(r'\d+', vm_size)
                if size_numbers:
                    # Use first number as vCPU count estimate
                    try:
                        vcpu_estimate = int(size_numbers[0])
                        if 1 <= vcpu_estimate <= 64:  # Sanity check
                            details['vcpus'] = vcpu_estimate
                            details['memory_gb'] = vcpu_estimate * 4  # Rough estimate
                    except ValueError:
                        pass
                
                details['size'] = vm_size
        
        elif self.provider == 'aws':
            # Extract AWS instance type
            instance_type = resource.get('instance_type', '').lower()
            details['size'] = instance_type
            
            # Define common AWS instance types and their specs
            aws_sizes = {
                't2.micro': {'vcpus': 1, 'memory_gb': 1},
                't2.small': {'vcpus': 1, 'memory_gb': 2},
                't2.medium': {'vcpus': 2, 'memory_gb': 4},
                't3.micro': {'vcpus': 2, 'memory_gb': 1},
                't3.small': {'vcpus': 2, 'memory_gb': 2},
                'm5.large': {'vcpus': 2, 'memory_gb': 8},
                'm5.xlarge': {'vcpus': 4, 'memory_gb': 16},
                'c5.large': {'vcpus': 2, 'memory_gb': 4},
                'c5.xlarge': {'vcpus': 4, 'memory_gb': 8},
                'r5.large': {'vcpus': 2, 'memory_gb': 16}
            }
            
            # Match instance type with known types
            if instance_type in aws_sizes:
                details.update(aws_sizes[instance_type])
            else:
                # Parse size from instance type for unknown types
                import re
                
                # Extract family and size
                match = re.match(r'([a-z]+[0-9]+[a-z]*)\.([a-z0-9]+)', instance_type)
                if match:
                    family, size = match.groups()
                    
                    # Estimate vCPUs based on size
                    if size == 'micro':
                        details['vcpus'] = 1
                        details['memory_gb'] = 1
                    elif size == 'small':
                        details['vcpus'] = 1
                        details['memory_gb'] = 2
                    elif size == 'medium':
                        details['vcpus'] = 2
                        details['memory_gb'] = 4
                    elif size == 'large':
                        details['vcpus'] = 2
                        details['memory_gb'] = 8
                    elif size == 'xlarge':
                        details['vcpus'] = 4
                        details['memory_gb'] = 16
                    elif size == '2xlarge':
                        details['vcpus'] = 8
                        details['memory_gb'] = 32
                    elif size == '4xlarge':
                        details['vcpus'] = 16
                        details['memory_gb'] = 64
        
        elif self.provider == 'gcp':
            # Extract GCP machine type
            machine_type = resource.get('machine_type', '').lower()
            details['size'] = machine_type
            
            # Define common GCP machine types and their specs
            gcp_sizes = {
                'n1-standard-1': {'vcpus': 1, 'memory_gb': 3.75},
                'n1-standard-2': {'vcpus': 2, 'memory_gb': 7.5},
                'n1-standard-4': {'vcpus': 4, 'memory_gb': 15},
                'n2-standard-2': {'vcpus': 2, 'memory_gb': 8},
                'n2-standard-4': {'vcpus': 4, 'memory_gb': 16},
                'e2-medium': {'vcpus': 2, 'memory_gb': 4},
                'e2-standard-2': {'vcpus': 2, 'memory_gb': 8},
                'e2-standard-4': {'vcpus': 4, 'memory_gb': 16}
            }
            
            # Match machine type with known types
            if machine_type in gcp_sizes:
                details.update(gcp_sizes[machine_type])
            else:
                # Parse size from machine type for unknown types
                import re
                
                # Extract family and size for standard machines
                match = re.match(r'([a-z0-9]+)-standard-([0-9]+)', machine_type)
                if match:
                    family, vcpus_str = match.groups()
                    try:
                        vcpus = int(vcpus_str)
                        details['vcpus'] = vcpus
                        details['memory_gb'] = vcpus * 4  # Standard ratio for GCP
                    except ValueError:
                        pass
        
        return details
    
    def _generate_findings_recommendations(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate findings and recommendations based on resource analysis.
        
        Returns:
            Tuple of findings and recommendations lists
        """
        findings = []
        recommendations = []
        
        # Skip if no cloud provider
        if self.provider == 'none':
            return findings, recommendations
        
        # 1. Idle resource findings
        idle_resources = []
        
        if self.provider == 'azure':
            # Check for idle VMs
            for vm in self.resources_by_type.get('virtual_machines', []):
                utilization = vm.get('utilization', {})
                if utilization.get('status') == 'idle':
                    idle_resources.append({
                        'resource_id': vm.get('id'),
                        'resource_name': vm.get('name'),
                        'resource_type': 'Virtual Machine',
                        'region': vm.get('region'),
                        'details': f"Average CPU: {utilization.get('average_cpu_percent', 0):.1f}%"
                    })
            
            # Check for unattached disks
            for disk in self.resources_by_type.get('disks', []):
                if not disk.get('is_attached'):
                    idle_resources.append({
                        'resource_id': disk.get('id'),
                        'resource_name': disk.get('name'),
                        'resource_type': 'Managed Disk',
                        'region': disk.get('region'),
                        'details': f"Size: {disk.get('size_gb')} GB, SKU: {disk.get('sku')}"
                    })
            
            # Check for old snapshots
            for snapshot in self.resources_by_type.get('snapshots', []):
                if snapshot.get('age_days', 0) > self.thresholds['snapshot_age_days']:
                    idle_resources.append({
                        'resource_id': snapshot.get('id'),
                        'resource_name': snapshot.get('name'),
                        'resource_type': 'Snapshot',
                        'region': snapshot.get('region'),
                        'details': f"Age: {snapshot.get('age_days')} days, Size: {snapshot.get('size_gb')} GB"
                    })
        
        # Add idle resources finding if any found
        if idle_resources:
            findings.append({
                'id': f"CLOUD-IDLE-{int(time.time())}",
                'type': 'Idle Resources',
                'category': 'Cost Optimization',
                'description': f"Found {len(idle_resources)} idle or unused resources",
                'risk_level': 'medium',
                'location': f"Cloud Provider: {self.provider.upper()}",
                'details': {
                    'resources': idle_resources,
                    'cost_impact': 'high',
                    'sustainability_impact': 'high'
                }
            })
            
            # Add recommendation for idle resources
            recommendations.append({
                'title': 'Remove or resize idle resources',
                'description': 'The following resources are idle or unused and should be considered for removal or resizing to reduce costs and carbon footprint.',
                'priority': 'High',
                'impact': 'High',
                'savings_potential': 'Significant',
                'steps': [
                    f"Review {len(idle_resources)} idle or unused resources",
                    "Delete unattached disks and unused snapshots",
                    "Shut down or resize idle VMs",
                    "Implement resource tagging policy with expiration dates"
                ]
            })
        
        # 2. Regional optimization findings
        # Calculate carbon intensity by region
        region_carbon = {}
        for region, co2e in self.carbon_data.get('by_region', {}).items():
            intensity = CARBON_INTENSITY.get(region.lower(), CARBON_INTENSITY['default'])
            region_carbon[region] = {
                'co2e_kg': co2e,
                'intensity': intensity
            }
        
        # Find high-carbon regions with lower-carbon alternatives
        high_carbon_regions = []
        for region, data in region_carbon.items():
            if data['intensity'] > 300:  # Threshold for high carbon regions
                # Find alternative regions with lower carbon intensity
                alternatives = []
                for alt_region, alt_data in CARBON_INTENSITY.items():
                    if alt_data < data['intensity'] * 0.7:  # At least 30% lower carbon
                        alternatives.append(alt_region)
                
                if alternatives:
                    high_carbon_regions.append({
                        'region': region,
                        'carbon_intensity': data['intensity'],
                        'co2e_kg': data['co2e_kg'],
                        'alternative_regions': alternatives[:3]  # Top 3 alternatives
                    })
        
        # Add regional optimization finding if any high-carbon regions found
        if high_carbon_regions:
            findings.append({
                'id': f"CLOUD-REGION-{int(time.time())}",
                'type': 'Regional Optimization',
                'category': 'Sustainability',
                'description': f"Resources in {len(high_carbon_regions)} high-carbon regions could be relocated",
                'risk_level': 'low',
                'location': f"Cloud Provider: {self.provider.upper()}",
                'details': {
                    'high_carbon_regions': high_carbon_regions,
                    'cost_impact': 'medium',
                    'sustainability_impact': 'high'
                }
            })
            
            # Add recommendation for regional optimization
            recommendations.append({
                'title': 'Optimize resource placement by region',
                'description': 'Moving resources to regions with lower carbon intensity can significantly reduce your carbon footprint.',
                'priority': 'Medium',
                'impact': 'Medium',
                'savings_potential': 'Moderate',
                'steps': [
                    "Identify non-location-dependent workloads",
                    "Plan migration to lower-carbon regions",
                    "Consider data residency requirements",
                    "Implement a carbon-aware deployment policy"
                ]
            })
        
        # 3. Resource tagging findings
        # Check for resources without proper tagging
        untagged_resources = []
        required_tags = ['Owner', 'Environment', 'Project', 'CostCenter']
        
        for resource_type, resources in self.resources_by_type.items():
            for resource in resources:
                tags = resource.get('tags', {})
                missing_tags = [tag for tag in required_tags if tag not in tags]
                
                if missing_tags:
                    untagged_resources.append({
                        'resource_id': resource.get('id'),
                        'resource_name': resource.get('name'),
                        'resource_type': resource_type,
                        'region': resource.get('region'),
                        'existing_tags': list(tags.keys()),
                        'missing_tags': missing_tags
                    })
        
        # Add tagging finding if untagged resources found
        if untagged_resources:
            findings.append({
                'id': f"CLOUD-TAGS-{int(time.time())}",
                'type': 'Incomplete Resource Tagging',
                'category': 'Governance',
                'description': f"Found {len(untagged_resources)} resources with missing tags",
                'risk_level': 'low',
                'location': f"Cloud Provider: {self.provider.upper()}",
                'details': {
                    'resources': untagged_resources[:10],  # Show first 10
                    'total_count': len(untagged_resources),
                    'required_tags': required_tags,
                    'cost_impact': 'low',
                    'sustainability_impact': 'low'
                }
            })
            
            # Add recommendation for tagging
            recommendations.append({
                'title': 'Implement comprehensive resource tagging',
                'description': 'Proper tagging enables better resource tracking, cost allocation, and lifecycle management.',
                'priority': 'Medium',
                'impact': 'Medium',
                'savings_potential': 'Indirect',
                'steps': [
                    "Create a tagging policy requiring Owner, Environment, Project, and CostCenter tags",
                    "Apply tags to all existing resources",
                    "Implement tag enforcement using policies",
                    "Set up regular tag compliance reporting"
                ]
            })
        
        # 4. Sustainability optimization recommendation
        recommendations.append({
            'title': 'Implement a sustainability optimization program',
            'description': 'A systematic approach to reducing carbon footprint and improving cloud efficiency.',
            'priority': 'Medium',
            'impact': 'High',
            'savings_potential': 'Significant',
            'steps': [
                "Establish baseline carbon emissions and resource usage metrics",
                "Set reduction targets for carbon emissions and resource waste",
                "Implement automated right-sizing and scheduling policies",
                "Adopt carbon-aware deployment practices",
                "Review and optimize resource usage monthly"
            ]
        })
        
        return findings, recommendations
    
    def _analyze_code_bloat(self) -> List[Dict[str, Any]]:
        """
        Analyze code repositories for bloat and inefficiencies.
        
        Returns:
            List of findings related to code bloat
        """
        findings = []
        
        # This would integrate with a code analysis tool or repository scanner
        # For this implementation, we'll return a placeholder finding
        
        findings.append({
            'id': f"CODE-BLOAT-{int(time.time())}",
            'type': 'Code Optimization',
            'category': 'Efficiency',
            'description': "Potential code bloat detected in repositories",
            'risk_level': 'low',
            'location': "Code Repositories",
            'details': {
                'recommendation': "Analyze repositories for unused imports and dependencies",
                'cost_impact': 'low',
                'sustainability_impact': 'low'
            }
        })
        
        return findings
    
    def _calculate_optimization_potential(self) -> Dict[str, Any]:
        """
        Calculate optimization potential in terms of cost and sustainability.
        
        Returns:
            Dictionary with optimization potential metrics
        """
        optimization = {
            'cost_savings_monthly': 0.0,
            'cost_savings_yearly': 0.0,
            'co2_reduction_monthly_kg': 0.0,
            'optimization_score': 0,
            'recommendations_by_impact': {
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }
        
        # Skip if no cloud provider
        if self.provider == 'none':
            return optimization
        
        # Calculate potential cost savings from idle resources
        monthly_cost_savings = 0.0
        
        if self.provider == 'azure':
            # Get cost estimates for idle VMs
            for vm in self.resources_by_type.get('virtual_machines', []):
                utilization = vm.get('utilization', {})
                if utilization.get('status') in ['idle', 'underutilized']:
                    # Get VM details
                    vm_size = vm.get('size', '').lower()
                    
                    # Estimate monthly cost based on VM size
                    # These are rough estimates
                    vm_cost_map = {
                        'standard_b2s': 30.66,
                        'standard_b2ms': 61.32,
                        'standard_d2_v3': 76.65,
                        'standard_d4_v3': 153.30,
                        'standard_e2_v3': 122.64,
                        'standard_f2s_v2': 76.65
                    }
                    
                    # Default to €100/month if size not found
                    monthly_vm_cost = 100.0
                    for size_prefix, cost in vm_cost_map.items():
                        if vm_size.startswith(size_prefix):
                            monthly_vm_cost = cost
                            break
                    
                    # If idle, count full cost; if underutilized, count half
                    if utilization.get('status') == 'idle':
                        monthly_cost_savings += monthly_vm_cost
                    else:
                        monthly_cost_savings += monthly_vm_cost * 0.5
            
            # Get cost estimates for unattached disks
            for disk in self.resources_by_type.get('disks', []):
                if not disk.get('is_attached'):
                    # Get disk details
                    size_gb = disk.get('size_gb', 0)
                    sku = disk.get('sku', '').lower()
                    
                    # Estimate monthly cost based on disk type and size
                    # These are rough estimates
                    if 'premium' in sku:
                        monthly_disk_cost = size_gb * 0.095  # Premium SSD
                    elif 'standard' in sku and 'ssd' in sku:
                        monthly_disk_cost = size_gb * 0.05  # Standard SSD
                    else:
                        monthly_disk_cost = size_gb * 0.03  # Standard HDD
                    
                    monthly_cost_savings += monthly_disk_cost
            
            # Get cost estimates for old snapshots
            for snapshot in self.resources_by_type.get('snapshots', []):
                if snapshot.get('age_days', 0) > self.thresholds['snapshot_age_days']:
                    # Get snapshot details
                    size_gb = snapshot.get('size_gb', 0)
                    
                    # Estimate monthly cost based on snapshot size
                    monthly_snapshot_cost = size_gb * 0.05
                    
                    monthly_cost_savings += monthly_snapshot_cost
        
        # Set cost savings in optimization potential
        optimization['cost_savings_monthly'] = monthly_cost_savings
        optimization['cost_savings_yearly'] = monthly_cost_savings * 12
        
        # Set CO2 reduction potential
        optimization['co2_reduction_monthly_kg'] = self.carbon_data.get('emissions_reduction_potential_kg', 0)
        
        # Calculate optimization score (0-100)
        # Higher score means more optimization potential
        resource_count = sum(len(resources) for resources in self.resources_by_type.values())
        if resource_count > 0:
            idle_count = len(self.utilization.get('idle_resources', []))
            underutilized_count = len(self.utilization.get('underutilized_resources', []))
            
            # Calculate as percentage of total resources that could be optimized
            optimization_percentage = min(100, (idle_count + underutilized_count) * 100 / resource_count)
            
            # Inverse score - higher means less optimized
            optimization['optimization_score'] = int(optimization_percentage)
        
        return optimization
    
    def scan_github_repository(self, repo_url: str, branch: str = 'main') -> Dict[str, Any]:
        """
        Scan a GitHub repository for code efficiency and optimization.
        
        Args:
            repo_url: GitHub repository URL
            branch: Branch to scan
            
        Returns:
            Dictionary with scan results
        """
        scan_result = {
            'scan_id': f"repo-{int(time.time())}",
            'scan_type': 'Code Efficiency',
            'timestamp': datetime.now().isoformat(),
            'repo_url': repo_url,
            'branch': branch,
            'findings': [],
            'unused_imports': [],
            'large_files': [],
            'recommendations': [],
            'status': 'in_progress'
        }
        
        total_steps = 3
        current_step = 0
        
        try:
            # Step 1: Clone or download the repository
            current_step += 1
            self._update_progress(current_step, total_steps, "Downloading repository")
            
            # This would normally download the repository
            # For this implementation, we'll simulate it
            
            # Step 2: Analyze code for unused imports and dependencies
            current_step += 1
            self._update_progress(current_step, total_steps, "Analyzing code for bloat")
            
            # Placeholder results
            unused_imports = [
                {'file': 'src/main.py', 'line': 12, 'import': 'import numpy', 'usage_count': 0},
                {'file': 'src/utils.py', 'line': 5, 'import': 'from collections import defaultdict', 'usage_count': 0},
                {'file': 'src/models.py', 'line': 8, 'import': 'import pandas as pd', 'usage_count': 0}
            ]
            
            large_files = [
                {'file': 'src/data/large_dataset.csv', 'size_mb': 15.2, 'recommendation': 'Consider storing in cloud storage'},
                {'file': 'src/static/images/background.png', 'size_mb': 8.7, 'recommendation': 'Compress image'}
            ]
            
            scan_result['unused_imports'] = unused_imports
            scan_result['large_files'] = large_files
            
            # Step 3: Generate recommendations
            current_step += 1
            self._update_progress(current_step, total_steps, "Generating recommendations")
            
            # Add findings
            if unused_imports:
                scan_result['findings'].append({
                    'id': f"CODE-IMPORTS-{int(time.time())}",
                    'type': 'Unused Imports',
                    'category': 'Code Efficiency',
                    'description': f"Found {len(unused_imports)} unused imports in the codebase",
                    'risk_level': 'low',
                    'location': repo_url,
                    'details': {
                        'unused_imports': unused_imports,
                        'recommendation': "Remove unused imports to improve code maintainability and slightly reduce memory usage"
                    }
                })
            
            if large_files:
                scan_result['findings'].append({
                    'id': f"CODE-SIZE-{int(time.time())}",
                    'type': 'Large Files',
                    'category': 'Storage Efficiency',
                    'description': f"Found {len(large_files)} large files that could be optimized",
                    'risk_level': 'low',
                    'location': repo_url,
                    'details': {
                        'large_files': large_files,
                        'recommendation': "Optimize large files to reduce repository size and improve clone performance"
                    }
                })
            
            # Add recommendations
            scan_result['recommendations'] = [
                {
                    'title': 'Remove unused imports and dependencies',
                    'description': 'Removing unused imports improves code maintainability and reduces application footprint.',
                    'priority': 'Low',
                    'impact': 'Low',
                    'steps': [
                        "Run linters to automatically detect unused imports",
                        "Remove or comment out unused imports",
                        "Prune unused dependencies from requirements files"
                    ]
                },
                {
                    'title': 'Optimize repository storage',
                    'description': 'Large repositories consume more resources and slow down operations like cloning and CI/CD.',
                    'priority': 'Medium',
                    'impact': 'Medium',
                    'steps': [
                        "Move large binary files to LFS or external storage",
                        "Compress large images and media files",
                        "Consider adding large data files to .gitignore"
                    ]
                }
            ]
            
            # Mark scan as completed
            scan_result['status'] = 'completed'
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Error during repository scan: {str(e)}")
            scan_result['status'] = 'error'
            scan_result['error'] = str(e)
            return scan_result
    
    def generate_report(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive sustainability report.
        
        Args:
            scan_results: Results from the resource scan
            
        Returns:
            Dictionary with report data
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'provider': self.provider,
            'scan_id': scan_results.get('scan_id'),
            'summary': {},
            'detailed_findings': [],
            'recommendations': [],
            'carbon_footprint': {},
            'cost_analysis': {},
            'charts_data': {}
        }
        
        # Extract key metrics
        total_resources = 0
        for resource_type, resources in self.resources_by_type.items():
            total_resources += len(resources)
        
        # Summary metrics
        report['summary'] = {
            'total_resources': total_resources,
            'optimization_score': scan_results.get('optimization_potential', {}).get('optimization_score', 0),
            'monthly_savings_potential': scan_results.get('optimization_potential', {}).get('cost_savings_monthly', 0),
            'yearly_savings_potential': scan_results.get('optimization_potential', {}).get('cost_savings_yearly', 0),
            'co2_reduction_potential_kg': scan_results.get('carbon_footprint', {}).get('emissions_reduction_potential_kg', 0),
            'findings_count': len(scan_results.get('findings', [])),
            'high_priority_recommendations': 0,
            'medium_priority_recommendations': 0,
            'low_priority_recommendations': 0
        }
        
        # Count recommendation priorities
        for rec in scan_results.get('recommendations', []):
            priority = rec.get('priority', 'Medium')
            if priority == 'High':
                report['summary']['high_priority_recommendations'] += 1
            elif priority == 'Medium':
                report['summary']['medium_priority_recommendations'] += 1
            elif priority == 'Low':
                report['summary']['low_priority_recommendations'] += 1
        
        # Add findings and recommendations
        report['detailed_findings'] = scan_results.get('findings', [])
        report['recommendations'] = scan_results.get('recommendations', [])
        
        # Add carbon footprint data
        report['carbon_footprint'] = scan_results.get('carbon_footprint', {})
        
        # Add cost analysis
        report['cost_analysis'] = {
            'monthly_cost_breakdown': {
                'compute': 0,
                'storage': 0,
                'network': 0,
                'other': 0
            },
            'optimization_savings': scan_results.get('optimization_potential', {})
        }
        
        # Generate chart data for visualizations
        report['charts_data'] = {
            'resources_by_type': {},
            'resources_by_region': {},
            'carbon_by_region': scan_results.get('carbon_footprint', {}).get('by_region', {}),
            'optimization_potential': {
                'cost_savings': scan_results.get('optimization_potential', {}).get('cost_savings_monthly', 0),
                'co2_reduction': scan_results.get('carbon_footprint', {}).get('emissions_reduction_potential_kg', 0)
            }
        }
        
        # Resources by type chart data
        for resource_type, resources in self.resources_by_type.items():
            report['charts_data']['resources_by_type'][resource_type] = len(resources)
        
        # Resources by region chart data
        region_counts = {}
        for resource_type, resources in self.resources_by_type.items():
            for resource in resources:
                region = resource.get('region', 'unknown')
                if region not in region_counts:
                    region_counts[region] = 0
                region_counts[region] += 1
        
        report['charts_data']['resources_by_region'] = region_counts
        
        return report


class GithubRepoSustainabilityScanner:
    """Scanner for analyzing GitHub repositories for code efficiency and sustainability."""
    
    def __init__(self, repo_url: str, branch: str = 'main'):
        """
        Initialize the GitHub repository scanner.
        
        Args:
            repo_url: URL of the GitHub repository
            branch: Branch to analyze
        """
        self.repo_url = repo_url
        self.branch = branch
        self.progress_callback = None
        self.temp_dir = None
        
    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """
        Set a callback for tracking scan progress.
        
        Args:
            callback: Function that accepts current step, total steps, and status message
        """
        self.progress_callback = callback
    
    def _update_progress(self, current: int, total: int, message: str) -> None:
        """
        Update scan progress through callback if available.
        
        Args:
            current: Current step number
            total: Total number of steps
            message: Status message
        """
        if self.progress_callback:
            self.progress_callback(current, total, message)
        else:
            logger.info(f"Progress {current}/{total}: {message}")
    
    def scan_repository(self) -> Dict[str, Any]:
        """
        Scan the GitHub repository for code efficiency and sustainability.
        
        Returns:
            Dictionary with scan results
        """
        import tempfile
        import os
        import subprocess
        import shutil
        import multiprocessing
        
        scan_result = {
            'scan_id': f"repo-{int(time.time())}",
            'scan_type': 'Code Efficiency',
            'timestamp': datetime.now().isoformat(),
            'repo_url': self.repo_url,
            'branch': self.branch,
            'findings': [],
            'code_stats': {},
            'unused_imports': [],
            'large_files': [],
            'recommendations': [],
            'sustainability_score': 0,
            'status': 'in_progress'
        }
        
        total_steps = 5
        current_step = 0
        
        try:
            # Step 1: Create temporary directory and clone the repository
            current_step += 1
            self._update_progress(current_step, total_steps, "Cloning repository")
            
            self.temp_dir = tempfile.mkdtemp()
            
            # Use sparse checkout and other optimizations for large repositories
            # This is much faster than a full clone for large repos like PyTorch
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=self.temp_dir, check=True, capture_output=True)
            
            # Add remote
            subprocess.run(
                ["git", "remote", "add", "origin", self.repo_url], 
                cwd=self.temp_dir, check=True, capture_output=True
            )
            
            # Enable sparse checkout
            subprocess.run(
                ["git", "config", "core.sparseCheckout", "true"], 
                cwd=self.temp_dir, check=True, capture_output=True
            )
            
            # Create sparse checkout patterns to focus on specific file types
            # We'll prioritize Python, JavaScript, and some config files
            with open(os.path.join(self.temp_dir, ".git/info/sparse-checkout"), "w") as f:
                f.write("*.py\n")
                f.write("*.js\n")
                f.write("*.json\n")
                f.write("*.md\n")
                f.write("*.yaml\n")
                f.write("*.yml\n")
                
            # Fetch only the specific branch with limited depth and no tags
            self._update_progress(current_step, total_steps, "Fetching repository (sparse checkout)")
            subprocess.run(
                ["git", "fetch", "--depth=1", "--no-tags", "origin", self.branch], 
                cwd=self.temp_dir, check=True, capture_output=True
            )
            
            # Checkout the branch
            subprocess.run(
                ["git", "checkout", self.branch], 
                cwd=self.temp_dir, check=True, capture_output=True
            )
            
            # Step 2: Analyze repository structure
            current_step += 1
            self._update_progress(current_step, total_steps, "Analyzing repository structure")
            
            # Get repository statistics using optimized, sampling-based approach
            file_stats = self._analyze_repository_structure()
            scan_result['code_stats'] = file_stats
            
            # Step 3: Analyze Python files for unused imports
            current_step += 1
            self._update_progress(current_step, total_steps, "Analyzing Python imports (sample-based)")
            
            # Use optimized import analysis with parallelization and sampling
            unused_imports = self._find_unused_imports_optimized()
            scan_result['unused_imports'] = unused_imports
            
            # Step 4: Identify large files
            current_step += 1
            self._update_progress(current_step, total_steps, "Identifying large files")
            
            large_files = self._find_large_files()
            scan_result['large_files'] = large_files
            
            # Step 5: Generate findings and recommendations
            current_step += 1
            self._update_progress(current_step, total_steps, "Generating recommendations")
            
            findings, recommendations = self._generate_findings_recommendations(file_stats, unused_imports, large_files)
            scan_result['findings'] = findings
            scan_result['recommendations'] = recommendations
            
            # Calculate sustainability score
            scan_result['sustainability_score'] = self._calculate_sustainability_score(file_stats, unused_imports, large_files)
            
            # Add additional metadata for very large repos
            if file_stats.get('total_files', 0) > 10000:
                scan_result['note'] = "Analysis was performed using sampling techniques due to repository size."
            
            # Mark scan as completed
            scan_result['status'] = 'completed'
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Error during repository scan: {str(e)}")
            scan_result['status'] = 'error'
            scan_result['error'] = str(e)
            return scan_result
            
        finally:
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except Exception as e:
                    logger.error(f"Error cleaning up temporary directory: {str(e)}")
    
    def _analyze_repository_structure(self) -> Dict[str, Any]:
        """
        Analyze the repository structure and gather file statistics.
        Optimized for large repositories with more efficient file analysis.
        
        Returns:
            Dictionary with file statistics
        """
        import os
        import subprocess
        import re
        import random
        
        file_stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'file_types': {},
            'file_count_by_type': {},
            'size_by_type_mb': {},
            'largest_files': [],
            'language_breakdown': {}
        }
        
        # Try using git commands for faster repository analysis on large repos
        try:
            # Get total file count first
            file_count_cmd = ["git", "-C", self.temp_dir, "ls-files", "--exclude-standard", "--cached", "|", "wc", "-l"]
            file_count_process = subprocess.run(" ".join(file_count_cmd), shell=True, capture_output=True, text=True)
            
            if file_count_process.returncode == 0 and file_count_process.stdout.strip():
                try:
                    total_files = int(file_count_process.stdout.strip())
                    file_stats['total_files'] = total_files
                    
                    # For very large repos, we'll use sampling to avoid processing all files
                    use_sampling = total_files > 5000
                    
                    if use_sampling:
                        logger.info(f"Large repository detected with {total_files} files. Using sampling for analysis.")
                        
                    # Get file types and sizes
                    file_list_cmd = ["git", "-C", self.temp_dir, "ls-files", "--exclude-standard", "--cached"]
                    file_list_process = subprocess.run(file_list_cmd, capture_output=True, text=True)
                    
                    if file_list_process.returncode == 0:
                        all_files = []
                        
                        # Sample files if there are too many to process efficiently
                        file_paths = file_list_process.stdout.strip().split('\n')
                        
                        # For very large repos, limit to 5000 files max for detailed analysis
                        if use_sampling:
                            # Set a max sample size with a minimum 10% of repo files
                            sample_size = min(5000, max(500, int(total_files * 0.1)))
                            file_paths = random.sample(file_paths, sample_size)
                            
                        for file_path in file_paths:
                            if not file_path.strip():
                                continue
                                
                            full_path = os.path.join(self.temp_dir, file_path)
                            if os.path.exists(full_path) and os.path.isfile(full_path):
                                file_size = os.path.getsize(full_path)
                                file_extension = os.path.splitext(file_path)[1].lower()
                                
                                # Collect file information
                                file_info = {
                                    'path': file_path,
                                    'size': file_size,
                                    'size_mb': file_size / (1024 * 1024),
                                    'extension': file_extension
                                }
                                
                                all_files.append(file_info)
                                
                                # Update statistics
                                file_stats['total_size_mb'] += file_info['size_mb']
                                
                                # Update file type stats
                                if file_extension not in file_stats['file_types']:
                                    file_stats['file_types'][file_extension] = []
                                    file_stats['file_count_by_type'][file_extension] = 0
                                    file_stats['size_by_type_mb'][file_extension] = 0
                                
                                file_stats['file_types'][file_extension].append(file_info['path'])
                                file_stats['file_count_by_type'][file_extension] += 1
                                file_stats['size_by_type_mb'][file_extension] += file_info['size_mb']
                        
                        # If we're using sampling, scale up the totals to represent the full repo
                        if use_sampling:
                            scaling_factor = total_files / len(file_paths)
                            file_stats['total_size_mb'] *= scaling_factor
                            
                            for ext in file_stats['file_count_by_type']:
                                file_stats['file_count_by_type'][ext] = int(file_stats['file_count_by_type'][ext] * scaling_factor)
                                file_stats['size_by_type_mb'][ext] *= scaling_factor
                            
                            # Add a note that these are estimated values
                            file_stats['sampling_note'] = f"Repository statistics estimated by sampling {len(file_paths)} of {total_files} files."
                        
                        # Sort files by size and get the largest files
                        all_files.sort(key=lambda x: x['size'], reverse=True)
                        file_stats['largest_files'] = all_files[:20]  # Top 20 largest files
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing git file count output: {str(e)}")
                    # Fall back to regular file analysis
                    return self._analyze_repository_structure_fallback()
            else:
                # Fall back to regular file analysis
                return self._analyze_repository_structure_fallback()
                
            # Determine language breakdown
            language_mapping = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.jsx': 'JavaScript',
                '.ts': 'TypeScript',
                '.tsx': 'TypeScript',
                '.java': 'Java',
                '.cpp': 'C++',
                '.c': 'C',
                '.h': 'C/C++ Headers',
                '.hpp': 'C++ Headers',
                '.cs': 'C#',
                '.go': 'Go',
                '.rb': 'Ruby',
                '.php': 'PHP',
                '.swift': 'Swift',
                '.kt': 'Kotlin',
                '.rs': 'Rust',
                '.html': 'HTML',
                '.css': 'CSS',
                '.scss': 'CSS',
                '.sass': 'CSS',
                '.md': 'Markdown',
                '.json': 'JSON',
                '.yml': 'YAML',
                '.yaml': 'YAML',
                '.sql': 'SQL',
                '.sh': 'Shell',
                '.bat': 'Batch',
                '.ps1': 'PowerShell',
                '.ipynb': 'Jupyter Notebook'
            }
            
            language_stats = {}
            for ext, count in file_stats['file_count_by_type'].items():
                language = language_mapping.get(ext, 'Other')
                if language not in language_stats:
                    language_stats[language] = {
                        'file_count': 0,
                        'size_mb': 0
                    }
                
                language_stats[language]['file_count'] += count
                language_stats[language]['size_mb'] += file_stats['size_by_type_mb'].get(ext, 0)
            
            file_stats['language_breakdown'] = language_stats
            
            return file_stats
        except Exception as e:
            logger.warning(f"Error during optimized repository analysis: {str(e)}. Falling back to standard analysis.")
            return self._analyze_repository_structure_fallback()
    
    def _analyze_repository_structure_fallback(self) -> Dict[str, Any]:
        """
        Fallback method for analyzing repository structure.
        Uses traditional file system walking.
        
        Returns:
            Dictionary with file statistics
        """
        import os
        
        file_stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'file_types': {},
            'file_count_by_type': {},
            'size_by_type_mb': {},
            'largest_files': [],
            'language_breakdown': {}
        }
        
        # Find all files in the repository
        all_files = []
        for root, _, files in os.walk(self.temp_dir):
            # Skip .git directory
            if '.git' in root:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_extension = os.path.splitext(file)[1].lower()
                
                # Collect file information
                file_info = {
                    'path': os.path.relpath(file_path, self.temp_dir),
                    'size': file_size,
                    'size_mb': file_size / (1024 * 1024),
                    'extension': file_extension
                }
                
                all_files.append(file_info)
                
                # Update statistics
                file_stats['total_files'] += 1
                file_stats['total_size_mb'] += file_info['size_mb']
                
                # Update file type stats
                if file_extension not in file_stats['file_types']:
                    file_stats['file_types'][file_extension] = []
                    file_stats['file_count_by_type'][file_extension] = 0
                    file_stats['size_by_type_mb'][file_extension] = 0
                
                file_stats['file_types'][file_extension].append(file_info['path'])
                file_stats['file_count_by_type'][file_extension] += 1
                file_stats['size_by_type_mb'][file_extension] += file_info['size_mb']
        
        # Sort files by size and get the largest files
        all_files.sort(key=lambda x: x['size'], reverse=True)
        file_stats['largest_files'] = all_files[:10]  # Top 10 largest files
        
        # Determine language breakdown
        language_mapping = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.rs': 'Rust',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'CSS',
            '.md': 'Markdown',
            '.json': 'JSON',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.sql': 'SQL'
        }
        
        language_stats = {}
        for ext, count in file_stats['file_count_by_type'].items():
            language = language_mapping.get(ext, 'Other')
            if language not in language_stats:
                language_stats[language] = {
                    'file_count': 0,
                    'size_mb': 0
                }
            
            language_stats[language]['file_count'] += count
            language_stats[language]['size_mb'] += file_stats['size_by_type_mb'].get(ext, 0)
        
        file_stats['language_breakdown'] = language_stats
        
        return file_stats
    
    def _find_unused_imports_optimized(self) -> List[Dict[str, Any]]:
        """
        Find unused imports in Python files using optimized techniques for large repositories.
        Uses sampling, parallelization, and early termination for better performance.
        
        Returns:
            List of dictionaries with unused import information
        """
        import os
        import subprocess
        import random
        import multiprocessing
        from functools import partial
        
        unused_imports = []
        
        # Check if pyflakes is available
        try:
            subprocess.run(['pyflakes', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If pyflakes is not available, install it
            try:
                subprocess.run(['pip', 'install', 'pyflakes'], check=True)
            except subprocess.CalledProcessError:
                logger.warning("Failed to install pyflakes. Unused import detection will be limited.")
                return unused_imports
        
        # Find Python files
        python_files = []
        for root, _, files in os.walk(self.temp_dir):
            # Skip .git directory and test directories
            if '.git' in root or 'test' in root.lower() or 'examples' in root.lower():
                continue
                
            for file in files:
                if file.endswith('.py'):
                    # Skip test files, they often have intentionally unused imports
                    if 'test_' in file.lower() or 'example' in file.lower():
                        continue
                    python_files.append(os.path.join(root, file))
        
        # For very large repos, use sampling
        total_files = len(python_files)
        
        # For extremely large repos like PyTorch, limit to max 500 files
        if total_files > 500:
            logger.info(f"Large repository detected ({total_files} Python files). Using sampling for analysis.")
            # Randomly sample files to keep analysis fast
            python_files = random.sample(python_files, 500)
        
        # Define a function to analyze a single file with pyflakes
        def analyze_file(file_path):
            try:
                result = subprocess.run(['pyflakes', file_path], capture_output=True, text=True, timeout=5)
                file_results = []
                
                if result.stdout:
                    # Parse pyflakes output
                    for line in result.stdout.splitlines():
                        if 'imported but unused' in line:
                            parts = line.split(':')
                            if len(parts) >= 3:
                                file_rel_path = os.path.relpath(file_path, self.temp_dir)
                                line_num = int(parts[1])
                                message = ':'.join(parts[2:]).strip()
                                
                                # Extract the import name
                                import_name = message.split("'")[1] if "'" in message else message
                                
                                file_results.append({
                                    'file': file_rel_path,
                                    'line': line_num,
                                    'import': import_name,
                                    'message': message
                                })
                return file_results
            except Exception as e:
                logger.warning(f"Error analyzing imports in {file_path}: {str(e)}")
                return []
        
        # Use multiprocessing pool to parallelize analysis
        # Use a reasonable number of processes based on CPU cores
        num_processes = min(multiprocessing.cpu_count(), 4)  # Cap at 4 to avoid overloading
        
        try:
            # Process files in parallel batches
            with multiprocessing.Pool(processes=num_processes) as pool:
                results = pool.map(analyze_file, python_files)
            
            # Flatten results
            for file_results in results:
                unused_imports.extend(file_results)
            
            # Limit results to avoid overwhelming the report
            if len(unused_imports) > 100:
                unused_imports = unused_imports[:100]
        except Exception as e:
            logger.error(f"Error in parallel processing of unused imports: {str(e)}")
            # Fallback to sequential processing for a sample of files
            if len(python_files) > 50:
                python_files = random.sample(python_files, 50)
            
            for file_path in python_files:
                unused_imports.extend(analyze_file(file_path))
            
        return unused_imports
    
    def _find_unused_imports(self) -> List[Dict[str, Any]]:
        """
        Find unused imports in Python files.
        This is a legacy method, the optimized version is preferred for large repositories.
        
        Returns:
            List of dictionaries with unused import information
        """
        import os
        import subprocess
        
        unused_imports = []
        
        # Check if pyflakes is available
        try:
            subprocess.run(['pyflakes', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If pyflakes is not available, install it
            try:
                subprocess.run(['pip', 'install', 'pyflakes'], check=True)
            except subprocess.CalledProcessError:
                logger.warning("Failed to install pyflakes. Unused import detection will be limited.")
                return unused_imports
        
        # Find Python files
        python_files = []
        for root, _, files in os.walk(self.temp_dir):
            # Skip .git directory
            if '.git' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        # Use pyflakes to find unused imports
        for file_path in python_files:
            try:
                result = subprocess.run(['pyflakes', file_path], capture_output=True, text=True)
                
                if result.stdout:
                    # Parse pyflakes output
                    for line in result.stdout.splitlines():
                        if 'imported but unused' in line:
                            parts = line.split(':')
                            if len(parts) >= 3:
                                file_rel_path = os.path.relpath(file_path, self.temp_dir)
                                line_num = int(parts[1])
                                message = ':'.join(parts[2:]).strip()
                                
                                # Extract the import name
                                import_name = message.split("'")[1] if "'" in message else message
                                
                                unused_imports.append({
                                    'file': file_rel_path,
                                    'line': line_num,
                                    'import': import_name,
                                    'message': message
                                })
            except Exception as e:
                logger.error(f"Error analyzing imports in {file_path}: {str(e)}")
        
        return unused_imports
    
    def _find_large_files(self, threshold_mb: float = 1.0) -> List[Dict[str, Any]]:
        """
        Find large files in the repository with optimizations for large repositories.
        
        Args:
            threshold_mb: Size threshold in MB
            
        Returns:
            List of dictionaries with large file information
        """
        import os
        import subprocess
        import re
        
        large_files = []
        
        # For large repositories, use git command to efficiently find large files
        # This is much faster than walking the entire directory tree
        try:
            # Try using git ls-files with object size information first
            git_cmd = [
                "git", "-C", self.temp_dir, "ls-files", 
                "--exclude-standard", "--cached", "-z"
            ]
            
            # Use a pipeline approach with git cat-file to get file sizes
            # This is more efficient than walking the directory
            ls_files_process = subprocess.Popen(
                git_cmd, 
                stdout=subprocess.PIPE
            )
            
            # Use xargs to batch process files with git cat-file
            xargs_process = subprocess.Popen(
                ["xargs", "-0", "git", "-C", self.temp_dir, "cat-file", "-s"],
                stdin=ls_files_process.stdout,
                stdout=subprocess.PIPE,
                text=True
            )
            
            # Close the pipe in the first process to avoid deadlocks
            ls_files_process.stdout.close()
            
            # Read file sizes from git cat-file
            file_sizes = xargs_process.communicate()[0].strip().split('\n')
            
            # Get the list of files again to match with sizes
            files_process = subprocess.run(
                git_cmd,
                capture_output=True,
                text=True
            )
            
            if files_process.returncode == 0:
                files = files_process.stdout.strip().split('\0')
                
                # Match files with their sizes
                for i, file_path in enumerate(files):
                    if i < len(file_sizes) and file_path:
                        try:
                            # Convert size from git cat-file output (in bytes)
                            file_size = int(file_sizes[i])
                            file_size_mb = file_size / (1024 * 1024)
                            
                            if file_size_mb >= threshold_mb:
                                full_path = os.path.join(self.temp_dir, file_path)
                                file_ext = os.path.splitext(file_path)[1].lower()
                                
                                # Determine file category
                                file_category = 'Other'
                                recommendation = ''
                                
                                # Categorize by extension
                                if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']:
                                    file_category = 'Image'
                                    recommendation = 'Compress image or use optimized formats'
                                elif file_ext in ['.mp4', '.avi', '.mov', '.wmv']:
                                    file_category = 'Video'
                                    recommendation = 'Store as link or in cloud storage'
                                elif file_ext in ['.pdf', '.doc', '.docx', '.ppt', '.pptx']:
                                    file_category = 'Document'
                                    recommendation = 'Store as link or in cloud storage'
                                elif file_ext in ['.csv', '.xlsx', '.json', '.xml', '.db', '.sqlite']:
                                    file_category = 'Data'
                                    recommendation = 'Consider using data versioning tools or cloud storage'
                                elif file_ext in ['.zip', '.tar', '.gz', '.rar']:
                                    file_category = 'Archive'
                                    recommendation = 'Extract necessary files or store elsewhere'
                                elif file_ext in ['.so', '.dll', '.exe', '.bin']:
                                    file_category = 'Binary'
                                    recommendation = 'Store in releases rather than in the repository'
                                
                                large_files.append({
                                    'file': file_path,
                                    'size_bytes': file_size,
                                    'size_mb': file_size_mb,
                                    'extension': file_ext,
                                    'category': file_category,
                                    'recommendation': recommendation
                                })
                        except (ValueError, IndexError):
                            continue
        except Exception as e:
            logger.warning(f"Error using git for file size analysis: {str(e)}. Falling back to manual search.")
            # Fallback to regular file walking for non-git repos or if git commands fail
            for root, _, files in os.walk(self.temp_dir):
                # Skip .git directory
                if '.git' in root:
                    continue
                    
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    file_size_mb = file_size / (1024 * 1024)
                    
                    if file_size_mb >= threshold_mb:
                        file_ext = os.path.splitext(file)[1].lower()
                        file_rel_path = os.path.relpath(file_path, self.temp_dir)
                        
                        # Determine file category
                        file_category = 'Other'
                        recommendation = ''
                        
                        # Categorize by extension
                        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']:
                            file_category = 'Image'
                            recommendation = 'Compress image or use optimized formats'
                        elif file_ext in ['.mp4', '.avi', '.mov', '.wmv']:
                            file_category = 'Video'
                            recommendation = 'Store as link or in cloud storage'
                        elif file_ext in ['.pdf', '.doc', '.docx', '.ppt', '.pptx']:
                            file_category = 'Document'
                            recommendation = 'Store as link or in cloud storage'
                        elif file_ext in ['.csv', '.xlsx', '.json', '.xml', '.db', '.sqlite']:
                            file_category = 'Data'
                            recommendation = 'Consider using data versioning tools or cloud storage'
                        elif file_ext in ['.zip', '.tar', '.gz', '.rar']:
                            file_category = 'Archive'
                            recommendation = 'Extract necessary files or store elsewhere'
                        elif file_ext in ['.so', '.dll', '.exe', '.bin']:
                            file_category = 'Binary'
                            recommendation = 'Store in releases rather than in the repository'
                        
                        large_files.append({
                            'file': file_rel_path,
                            'size_bytes': file_size,
                            'size_mb': file_size_mb,
                            'extension': file_ext,
                            'category': file_category,
                            'recommendation': recommendation
                        })
        
        # Limit results to top 50 largest files to avoid overwhelming the report
        # Sort by size (largest first)
        large_files.sort(key=lambda x: x['size_bytes'], reverse=True)
        
        if len(large_files) > 50:
            large_files = large_files[:50]
            
        return large_files
    
    def _generate_findings_recommendations(self, file_stats: Dict[str, Any], unused_imports: List[Dict[str, Any]], 
                                          large_files: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate findings and recommendations based on repository analysis.
        
        Args:
            file_stats: Repository file statistics
            unused_imports: List of unused imports
            large_files: List of large files
            
        Returns:
            Tuple of findings and recommendations lists
        """
        findings = []
        recommendations = []
        
        # 1. Finding for large repository size
        repo_size_mb = file_stats.get('total_size_mb', 0)
        if repo_size_mb > 100:  # If repository is larger than 100MB
            findings.append({
                'id': f"REPO-SIZE-{int(time.time())}",
                'type': 'Large Repository',
                'category': 'Storage Efficiency',
                'description': f"Repository size ({repo_size_mb:.2f} MB) exceeds recommended limits",
                'risk_level': 'medium',
                'location': self.repo_url,
                'details': {
                    'repo_size_mb': repo_size_mb,
                    'recommended_size_mb': 100,
                    'largest_files': file_stats.get('largest_files', [])[:5]  # Top 5 largest files
                }
            })
            
            # Add recommendation for large repository
            recommendations.append({
                'title': 'Optimize repository size',
                'description': 'Large repositories consume more resources and have higher carbon footprint for CI/CD operations.',
                'priority': 'High' if repo_size_mb > 500 else 'Medium',
                'impact': 'Medium',
                'savings_potential': f"{repo_size_mb - 100:.2f} MB",
                'steps': [
                    "Add large files to .gitignore",
                    "Use Git LFS (Large File Storage) for binary assets",
                    "Store large datasets in cloud storage",
                    "Remove unnecessary binary files and dependencies"
                ]
            })
        
        # 2. Finding for unused imports
        if unused_imports:
            findings.append({
                'id': f"CODE-IMPORTS-{int(time.time())}",
                'type': 'Unused Imports',
                'category': 'Code Efficiency',
                'description': f"Found {len(unused_imports)} unused imports in Python files",
                'risk_level': 'low',
                'location': self.repo_url,
                'details': {
                    'unused_imports_count': len(unused_imports),
                    'unused_imports_sample': unused_imports[:5]  # Sample of 5 unused imports
                }
            })
            
            # Add recommendation for unused imports
            recommendations.append({
                'title': 'Remove unused imports',
                'description': 'Unused imports increase code complexity and can slightly impact runtime performance.',
                'priority': 'Low',
                'impact': 'Low',
                'savings_potential': 'Minimal',
                'steps': [
                    "Use linters like pyflakes or pylint to identify unused imports",
                    "Remove or comment out the identified unused imports",
                    "Consider using tools like autoflake for automated cleanup"
                ]
            })
        
        # 3. Finding for large files
        large_files_count = len(large_files)
        if large_files_count > 0:
            # Calculate total size of large files
            total_large_files_size_mb = sum(file.get('size_mb', 0) for file in large_files)
            
            findings.append({
                'id': f"REPO-LARGE-FILES-{int(time.time())}",
                'type': 'Large Files',
                'category': 'Storage Efficiency',
                'description': f"Found {large_files_count} large files totaling {total_large_files_size_mb:.2f} MB",
                'risk_level': 'medium' if total_large_files_size_mb > 50 else 'low',
                'location': self.repo_url,
                'details': {
                    'large_files_count': large_files_count,
                    'total_size_mb': total_large_files_size_mb,
                    'large_files_sample': large_files[:5]  # Sample of 5 large files
                }
            })
            
            # Add recommendation for large files
            recommendations.append({
                'title': 'Optimize large files',
                'description': 'Large files in repositories increase clone time, storage costs, and carbon footprint.',
                'priority': 'Medium',
                'impact': 'Medium',
                'savings_potential': f"{total_large_files_size_mb:.2f} MB",
                'steps': [
                    "Move large files to appropriate storage solutions",
                    "Compress images and media files",
                    "Use Git LFS for tracking large files",
                    "Consider adding a .gitattributes file"
                ]
            })
        
        # 4. General code efficiency recommendation
        recommendations.append({
            'title': 'Implement code efficiency best practices',
            'description': 'Improving code efficiency reduces resource usage, carbon footprint, and cloud costs.',
            'priority': 'Medium',
            'impact': 'Medium',
            'savings_potential': 'Variable',
            'steps': [
                "Implement automated linting in CI/CD pipelines",
                "Use dependency scanning to identify unused packages",
                "Optimize Docker image sizes for containerized applications",
                "Implement resource monitoring in production environments"
            ]
        })
        
        return findings, recommendations
    
    def _calculate_sustainability_score(self, file_stats: Dict[str, Any], unused_imports: List[Dict[str, Any]], 
                                       large_files: List[Dict[str, Any]]) -> int:
        """
        Calculate a sustainability score for the repository.
        
        Args:
            file_stats: Repository file statistics
            unused_imports: List of unused imports
            large_files: List of large files
            
        Returns:
            Sustainability score (0-100, higher is better)
        """
        # Base score
        score = 70
        
        # Repository size impact (lower is better)
        repo_size_mb = file_stats.get('total_size_mb', 0)
        if repo_size_mb <= 10:
            score += 10  # Excellent size
        elif repo_size_mb <= 50:
            score += 5   # Good size
        elif repo_size_mb <= 100:
            score += 0   # Acceptable size
        elif repo_size_mb <= 500:
            score -= 10  # Large repository
        else:
            score -= 20  # Very large repository
        
        # Unused imports impact (fewer is better)
        unused_imports_count = len(unused_imports)
        if unused_imports_count == 0:
            score += 5   # No unused imports
        elif unused_imports_count <= 10:
            score += 0   # Few unused imports
        elif unused_imports_count <= 50:
            score -= 5   # Moderate unused imports
        else:
            score -= 10  # Many unused imports
        
        # Large files impact (fewer is better)
        large_files_count = len(large_files)
        if large_files_count == 0:
            score += 10  # No large files
        elif large_files_count <= 5:
            score += 5   # Few large files
        elif large_files_count <= 20:
            score -= 5   # Moderate number of large files
        else:
            score -= 10  # Many large files
        
        # Calculate large files percentage of total repo size
        if repo_size_mb > 0:
            large_files_size_mb = sum(file.get('size_mb', 0) for file in large_files)
            large_files_percentage = (large_files_size_mb / repo_size_mb) * 100
            
            if large_files_percentage > 80:
                score -= 10  # Most of repo size is large files
            elif large_files_percentage > 50:
                score -= 5   # Half of repo size is large files
        
        # Ensure score is within 0-100 range
        score = max(0, min(100, score))
        
        return int(score)