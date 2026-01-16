# BESCHRIJVING (DESCRIPTION)
## Cloud Sustainability Scanner - Automated Zombie Resource Detection with Regional CO₂ Calculation

**PAGINA 1 van 8**

---

## TITEL VAN DE UITVINDING

Automated Cloud Sustainability Scanner with Zombie Resource Detection, Regional Carbon Footprint Calculation, and EU Green Deal CSRD Compliance for Multi-Cloud Environments

---

## TECHNISCH GEBIED

Deze uitvinding betreft een geautomatiseerd cloud sustainability assessment systeem dat idle/zombie cloud resources detecteert (CPU <5%, 14+ dagen inactief), regionale CO₂ emissies berekent per cloud provider en geografische locatie (15+ regio's: Azure North Europe 210 gCO₂/kWh, AWS US-East-1 380 gCO₂/kWh, GCP Europe-West-1 225 gCO₂/kWh), Power Usage Effectiveness (PUE) modelleert per provider (Azure 1.12, AWS 1.15, GCP 1.10), en multi-cloud ondersteuning biedt (Azure/AWS/GCP) in single platform voor EU Corporate Sustainability Reporting Directive (CSRD) compliance en Scope 3 emissions tracking.

---

## ACHTERGROND VAN DE UITVINDING

### Stand van de Techniek

De EU Green Deal en Corporate Sustainability Reporting Directive (CSRD) verplichten grote bedrijven vanaf 2024-2025 tot uitgebreide ESG (Environmental, Social, Governance) rapportage inclusief Scope 3 emissies (indirecte emissies via cloud infrastructuur).

**PAGINA 2 van 8**

Cloud computing genereert wereldwijd 2-3% van totale CO₂ emissies (gelijk aan luchtvaartindustrie). Belangrijkste problemen:

1. **Zombie Resources**: Idle virtual machines, underutilized instances, unattached disks, oude snapshots veroorzaken 30-40% verspilde cloud uitgaven en onnodige CO₂ emissies.

2. **Regionale Variatie**: CO₂ intensity varieert 300% tussen regio's (Iceland 25 gCO₂/kWh versus Poland 650 gCO₂/kWh), maar organisaties hebben geen zichtbaarheid.

3. **Multi-Cloud Complexiteit**: Bedrijven gebruiken gemiddeld 2.6 cloud providers, maar geen enkele tool biedt unified sustainability assessment.

4. **CSRD Compliance**: Handmatige Scope 3 emissions tracking kost €50K-€200K/jaar per organisatie.

### Probleem met Bestaande Oplossingen

Huidige cloud tools hebben significante beperkingen:

a) **FinOps Tools (CloudHealth, Cloudability)**: Focus op kosten, **geen** CO₂ berekeningen of sustainability metrics;

b) **Sustainability Tools (Cloud Carbon Footprint)**: Beperkt tot AWS, **geen** Azure/GCP support, **geen** zombie detection;

c) **Privacy Tools (OneTrust, BigID)**: **Geen** sustainability scanning, **geen** carbon footprint;

d) **Handmatige Assessment**: €50K-€200K/jaar, tijdrovend, inaccuraat.

**GEEN ENKELE TOOL** combineert privacy compliance + sustainability assessment in single platform.

**PAGINA 3 van 8**

---

## SAMENVATTING VAN DE UITVINDING

### Doel van de Uitvinding

Deze uitvinding lost bovenstaande problemen op door een volledig geautomatiseerd systeem te verstrekken dat:

1. **Zombie Resource Detection**: Idle resources (CPU <5%, 14+ dagen), underutilized instances (<20% utilization), unattached disks, oude snapshots (>90 dagen), orphaned load balancers;

2. **Regional CO₂ Calculation**: Carbon intensity per cloud region (15+ regio's) gebaseerd op werkelijke grid data: Azure North Europe 210 gCO₂/kWh, AWS EU-West-1 235 gCO₂/kWh, GCP Europe-West-1 225 gCO₂/kWh;

3. **PUE-Based Power Modeling**: Provider-specifieke Power Usage Effectiveness: Azure 1.12, AWS 1.15, GCP 1.10, met watt-per-vCPU berekeningen (Azure 13.5W, AWS 14.2W, GCP 12.8W);

4. **Multi-Cloud Support**: Azure, AWS, GCP in single unified platform met OAuth2 authentication en SDK integration;

5. **Code Bloat Analysis**: Repository sustainability scanning voor inefficiënte code patterns die verspilde compute resources veroorzaken;

6. **CSRD Compliance**: Automated Scope 3 emissions reporting conform EU Green Deal vereisten;

7. **90%+ Cost Savings**: Zombie resource elimination bespaart gemiddeld €50K-€500K/jaar per organisatie.

### Hoofdkenmerken van de Uitvinding

**PAGINA 4 van 8**

---

## A. ZOMBIE RESOURCE DETECTION ENGINE

### 1. Idle Resource Identification

```
DEFAULT_THRESHOLDS:
   idle_cpu_percent: 5.0        # CPU <5% = idle
   idle_duration_days: 14       # 14+ days flagged
   low_util_percent: 20.0       # <20% underutilized
   oversized_threshold: 2.0     # 2x larger than needed
   snapshot_age_days: 90        # 90+ day snapshots

Detection Logic:
   if avg_cpu < 5.0 AND days_running >= 14:
       status = "idle"
       recommendation = "Terminate or downsize"
       potential_savings = monthly_cost * 0.90
   
   elif avg_cpu < 20.0:
       status = "underutilized"
       recommendation = "Downsize to smaller SKU"
       potential_savings = monthly_cost * 0.50
```

### 2. Unattached Resource Detection

```
Unattached Disks:
   - Disks not attached to any VM
   - Billing continues despite no usage
   - Recommendation: Delete after backup

Old Snapshots:
   - Snapshots older than 90 days
   - Rarely restored, accumulating costs
   - Recommendation: Archive to cold storage

Orphaned Resources:
   - Load balancers with no backend VMs
   - Public IPs not assigned
   - Network interfaces detached
```

**PAGINA 5 van 8**

---

## B. REGIONAL CARBON INTENSITY DATABASE

### 1. Azure Regions

```
CARBON_INTENSITY = {
    # Azure Regions (gCO₂ per kWh)
    'eastus': 390,              # US East (Virginia)
    'westus': 190,              # US West (California)
    'northeurope': 210,         # Ireland
    'westeurope': 230,          # Netherlands ⭐
    'eastasia': 540,            # Hong Kong
    'southeastasia': 470,       # Singapore
    'uksouth': 215,             # UK South
    'ukwest': 215,              # UK West
    'francecentral': 60,        # France (nuclear power)
    'germanynorth': 280         # Germany
}
```

### 2. AWS Regions

```
CARBON_INTENSITY = {
    # AWS Regions (gCO₂ per kWh)
    'us-east-1': 380,           # US East (Virginia)
    'us-west-1': 210,           # US West (N. California)
    'us-west-2': 150,           # US West (Oregon)
    'eu-west-1': 235,           # Ireland
    'eu-central-1': 280,        # Frankfurt
    'ap-southeast-1': 470,      # Singapore
    'ap-northeast-1': 420       # Tokyo
}
```

### 3. GCP Regions

```
CARBON_INTENSITY = {
    # GCP Regions (gCO₂ per kWh)
    'us-central1': 410,         # Iowa
    'us-west1': 180,            # Oregon
    'europe-west1': 225,        # Belgium
    'europe-west4': 60,         # Netherlands (wind power)
    'asia-east1': 520,          # Taiwan
    'asia-southeast1': 470      # Singapore
}
```

**PAGINA 6 van 8**

---

## C. POWER USAGE EFFECTIVENESS (PUE) MODELING

### 1. Provider-Specific PUE

```
PUE = {
    'azure': 1.12,    # Microsoft average PUE
    'aws': 1.15,      # Amazon average PUE
    'gcp': 1.10,      # Google average PUE (best-in-class)
    'default': 1.2    # Industry average
}

Definition:
PUE = Total Facility Power / IT Equipment Power

Lower PUE = More efficient datacenter
   PUE 1.0 = Perfect efficiency (theoretical)
   PUE 1.12 = Azure efficiency (12% overhead)
   PUE 1.15 = AWS efficiency (15% overhead)
   PUE 2.0 = Legacy datacenter (100% overhead)
```

### 2. Watt-per-vCPU Calculation

```
WATTS_PER_VCPU = {
    'azure': 13.5,    # Watts per virtual CPU
    'aws': 14.2,
    'gcp': 12.8,      # Most efficient
    'default': 14.0
}

Carbon Footprint Formula:
   power_consumption_kwh = (vCPUs × watts_per_vCPU × hours_running) / 1000
   facility_power_kwh = power_consumption_kwh × PUE
   carbon_emissions_kg = facility_power_kwh × (carbon_intensity / 1000)
```

**PAGINA 7 van 8**

---

## D. MULTI-CLOUD AUTHENTICATION

### 1. Azure OAuth2 Integration

```
Authentication Flow:
   POST https://login.microsoftonline.com/{tenant_id}/oauth2/token
   Body: {
       "grant_type": "client_credentials",
       "client_id": "{CLIENT_ID}",
       "client_secret": "{CLIENT_SECRET}",
       "resource": "https://management.azure.com/"
   }

Resource Enumeration:
   GET https://management.azure.com/subscriptions/{subscription}/
       providers/Microsoft.Compute/virtualMachines

   GET https://management.azure.com/subscriptions/{subscription}/
       providers/Microsoft.Compute/disks
```

### 2. AWS SDK Integration

```
Authentication:
   import boto3
   
   ec2_client = boto3.client('ec2', 
       aws_access_key_id=AWS_KEY,
       aws_secret_access_key=AWS_SECRET,
       region_name='eu-west-1'
   )

Resource Scanning:
   instances = ec2_client.describe_instances()
   volumes = ec2_client.describe_volumes()
   snapshots = ec2_client.describe_snapshots()
```

### 3. GCP SDK Integration

```
Authentication:
   from google.oauth2 import service_account
   
   credentials = service_account.Credentials.from_service_account_file(
       'service-account-key.json'
   )

Resource Scanning:
   from google.cloud import compute_v1
   
   instances_client = compute_v1.InstancesClient(credentials=credentials)
   instances = instances_client.list(project=PROJECT_ID, zone=ZONE)
```

**PAGINA 8 van 8**

---

## E. CODE BLOAT SUSTAINABILITY ANALYSIS

### 1. Repository Scanning

```
Code Inefficiency Detection:
   - Nested loops (O(n²) or worse)
   - Redundant API calls
   - Memory leaks
   - Inefficient database queries
   - Large dependency trees
   - Unused imports/functions

Carbon Impact:
   inefficient_code → longer_execution_time → higher_CPU_usage → 
   more_power_consumption → increased_carbon_emissions
```

### 2. Optimization Recommendations

```
If (nested_loops_detected):
   recommendation = "Optimize algorithm complexity O(n²) → O(n log n)"
   potential_savings = "30-60% CPU reduction"

If (redundant_api_calls):
   recommendation = "Implement caching layer"
   potential_savings = "50-80% API traffic reduction"
```

---

## F. EU CSRD COMPLIANCE

### 1. Scope 3 Emissions Reporting

```
Scope 3 Category 1: Purchased Goods and Services
   - Cloud infrastructure emissions
   - Includes: compute, storage, networking
   - CSRD mandatory disclosure (2024-2025)

Automatic Report Generation:
   - Total carbon footprint (kg CO₂)
   - Breakdown per cloud provider
   - Breakdown per region
   - Optimization potential
   - Year-over-year comparison
```

### 2. Penalties for Non-Compliance

```
EU CSRD Fines:
   - €1M-€10M voor onvolledige/incorrecte ESG rapportage
   - Reputatieschade bij stakeholders
   - Verlies van ESG-focused investeerders
```

---

**EINDE BESCHRIJVING**
