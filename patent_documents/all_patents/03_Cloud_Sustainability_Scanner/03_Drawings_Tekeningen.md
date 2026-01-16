# TEKENINGEN EN FORMULES (DRAWINGS AND FORMULAS)
## Cloud Sustainability Scanner - Patent Tekeningen

**PAGINA 13 van 16**

---

## FIGUUR 1: SYSTEEM ARCHITECTUUR OVERZICHT

```
+-------------------------------------------------------------------------+
|           CLOUD SUSTAINABILITY SCANNER PLATFORM                         |
|         Patent-Pending Zombie Detection + Carbon Calculation            |
+-------------------------------------------------------------------------+
                                    |
     +--------------+--------------+--------------+--------------+
     |   Zombie     |  Regional    |     PUE      | CSRD         |
     |   Detection  |  Carbon      |     Power    | Compliance   |
     |   Engine     |  Intensity   |     Model    | Reporter     |
     +--------------+--------------+--------------+--------------+
```

---

## FIGUUR 2: ZOMBIE RESOURCE DETECTION THRESHOLDS

```
+-------------------------------------------------------------------------+
|                   ZOMBIE DETECTION CRITERIA                             |
+-------------------------------------------------------------------------+

IDLE RESOURCES (CPU <5%, 14+ days):
   Threshold: idle_cpu_percent = 5.0
   Duration: idle_duration_days = 14
   Action: Terminate or downsize
   Savings: 90% of monthly cost

UNDERUTILIZED RESOURCES (<20% util):
   Threshold: low_util_percent = 20.0
   Action: Downsize to smaller SKU
   Savings: 50% of monthly cost

OVERSIZED RESOURCES (2x larger than needed):
   Threshold: oversized_threshold = 2.0
   Action: Right-size to optimal SKU
   Savings: 40-60% of monthly cost

OLD SNAPSHOTS (>90 days):
   Threshold: snapshot_age_days = 90
   Action: Archive to cold storage
   Savings: 80% of snapshot costs

UNATTACHED RESOURCES:
   - Disks not attached to VMs
   - Public IPs not assigned
   - Load balancers with no backends
   Action: Delete after backup verification
   Savings: 100% of resource cost
```

---

**PAGINA 14 van 16**

## FIGUUR 3: REGIONAL CARBON INTENSITY MAP

```
+-------------------------------------------------------------------------+
|              CARBON INTENSITY BY CLOUD REGION (gCO₂/kWh)               |
+-------------------------------------------------------------------------+

AZURE REGIONS:
   Europe:
      ├─ North Europe (Ireland): 210
      ├─ West Europe (Netherlands): 230
      ├─ France Central: 60 ⭐ LOWEST (nuclear)
      ├─ Germany North: 280
      └─ UK South: 215
   
   Americas:
      ├─ East US (Virginia): 390
      ├─ West US (California): 190
      └─ Central US: 420
   
   Asia:
      ├─ East Asia (Hong Kong): 540
      └─ Southeast Asia (Singapore): 470

AWS REGIONS:
   Europe:
      ├─ eu-west-1 (Ireland): 235
      ├─ eu-central-1 (Frankfurt): 280
      └─ eu-north-1 (Stockholm): 50 ⭐ LOWEST (hydro)
   
   Americas:
      ├─ us-east-1 (Virginia): 380
      ├─ us-west-1 (N. California): 210
      └─ us-west-2 (Oregon): 150
   
   Asia:
      ├─ ap-southeast-1 (Singapore): 470
      └─ ap-northeast-1 (Tokyo): 420

GCP REGIONS:
   Europe:
      ├─ europe-west1 (Belgium): 225
      ├─ europe-west4 (Netherlands): 60 ⭐ LOWEST (wind)
      └─ europe-north1 (Finland): 90
   
   Americas:
      ├─ us-central1 (Iowa): 410
      └─ us-west1 (Oregon): 180
   
   Asia:
      ├─ asia-east1 (Taiwan): 520
      └─ asia-southeast1 (Singapore): 470

Default/Unknown: 400 gCO₂/kWh
```

---

**PAGINA 15 van 16**

## FIGUUR 4: CARBON FOOTPRINT CALCULATION FORMULA

```
+-------------------------------------------------------------------------+
|                  COMPLETE CARBON EMISSION CALCULATION                   |
+-------------------------------------------------------------------------+

STEP 1: IT Equipment Power Consumption
   power_consumption_kwh = (vCPUs × watts_per_vCPU × hours_running) / 1000
   
   Where:
      vCPUs = Number of virtual CPUs
      watts_per_vCPU = Provider-specific (Azure 13.5W, AWS 14.2W, GCP 12.8W)
      hours_running = Runtime in hours
      /1000 = Conversion from watt-hours to kilowatt-hours

STEP 2: Total Facility Power (PUE Adjustment)
   facility_power_kwh = power_consumption_kwh × PUE
   
   Where:
      PUE = Power Usage Effectiveness
      Azure PUE = 1.12 (12% datacenter overhead)
      AWS PUE = 1.15 (15% datacenter overhead)
      GCP PUE = 1.10 (10% datacenter overhead, best-in-class)

STEP 3: Carbon Emissions Calculation
   carbon_emissions_kg = facility_power_kwh × (carbon_intensity / 1000)
   
   Where:
      carbon_intensity = gCO₂ per kWh (region-specific)
      /1000 = Conversion from grams to kilograms

COMPLETE FORMULA:
   CO₂_kg = ((vCPUs × watts_per_vCPU × hours) / 1000) × PUE × (gCO₂_per_kWh / 1000)

EXAMPLE CALCULATION:
   Azure VM in West Europe (Netherlands):
      - 4 vCPUs × 13.5 watts = 54 watts
      - Running 720 hours (1 month) = 38,880 watt-hours = 38.88 kWh
      - PUE adjustment: 38.88 × 1.12 = 43.55 kWh facility power
      - Carbon intensity: 230 gCO₂/kWh
      - Total emissions: 43.55 × 0.230 = 10.02 kg CO₂ per month
```

---

## FIGUUR 5: MULTI-CLOUD AUTHENTICATION FLOW

```
+-------------------------------------------------------------------------+
|                   MULTI-CLOUD AUTHENTICATION                            |
+-------------------------------------------------------------------------+

AZURE OAUTH2:
   POST https://login.microsoftonline.com/{tenant_id}/oauth2/token
   ↓
   {
      "grant_type": "client_credentials",
      "client_id": "{CLIENT_ID}",
      "client_secret": "{CLIENT_SECRET}",
      "resource": "https://management.azure.com/"
   }
   ↓
   Access Token → Azure Resource Manager API

AWS BOTO3 SDK:
   import boto3
   ↓
   ec2_client = boto3.client('ec2',
       aws_access_key_id=AWS_ACCESS_KEY,
       aws_secret_access_key=AWS_SECRET_KEY,
       region_name='eu-west-1')
   ↓
   SDK Authentication → AWS APIs

GCP SERVICE ACCOUNT:
   from google.oauth2 import service_account
   ↓
   credentials = service_account.Credentials.from_service_account_file(
       'service-account-key.json')
   ↓
   Service Account Token → Google Cloud APIs
```

---

**PAGINA 16 van 16**

## FIGUUR 6: COMPETITIVE ADVANTAGE MATRIX

```
+-------------------------------------------------------------------------+
|                     MARKET POSITIONING ANALYSIS                         |
+-------------------------------------------------------------------------+

FEATURE COMPARISON:

                          DataGuardian | Cloud      | OneTrust | BigID
                          Pro          | Carbon     |          |
                                       | Footprint  |          |
------------------------------------------------------------------------
Zombie Detection          ✅ YES       | ❌ NO      | ❌ NO    | ❌ NO
Regional CO₂ Calc         ✅ 15+ regions| ✅ AWS only| ❌ NO    | ❌ NO
Multi-Cloud Support       ✅ Az/AWS/GCP| ⚠️ AWS only| ❌ NO    | ❌ NO
PUE Modeling              ✅ YES       | ❌ NO      | ❌ NO    | ❌ NO
Privacy + Sustainability  ✅ COMBINED  | ❌ NO      | ⚠️ Separate| ❌ NO
Code Bloat Analysis       ✅ YES       | ❌ NO      | ❌ NO    | ❌ NO
CSRD Compliance           ✅ YES       | ⚠️ PARTIAL | ❌ NO    | ❌ NO
Pricing (annual)          €300-€3K     | €15K-€40K  | €60K-€180K| €96K-€240K

UNIQUE VALUE PROPOSITION:
   "ONLY tool combining privacy compliance + cloud sustainability in
    single platform. Competitors either focus on FinOps (cost) or 
    privacy, but NOT carbon footprint optimization."

MARKET TIMING:
   ├─ EU Green Deal: Active now (2024-2025)
   ├─ CSRD: Mandatory Scope 3 reporting (2024-2025)
   ├─ ESG Fines: €1M-€10M for non-compliance
   └─ Savings: €50K-€500K/year per organization

REGULATORY DRIVERS:
   - Corporate Sustainability Reporting Directive (CSRD)
   - EU Taxonomy Regulation
   - Scope 3 Emissions Tracking (GHG Protocol)
   - Carbon Border Adjustment Mechanism (CBAM)
```

---

## FIGUUR 7: PROCESSING PIPELINE

```
INPUT: Cloud Credentials (Azure/AWS/GCP)
   ↓
STEP 1: Authentication & Resource Inventory Collection
   ↓
STEP 2: Utilization Analysis (CPU, Memory, Disk, Network)
   ↓
STEP 3: Zombie Detection (Idle, Underutilized, Unattached)
   ↓
STEP 4: Regional Carbon Intensity Lookup
   ↓
STEP 5: PUE-Adjusted Power Consumption Calculation
   ↓
STEP 6: Carbon Footprint Aggregation + Optimization
   ↓
OUTPUT: Sustainability Report + CSRD Scope 3 Emissions
```

---

**EINDE TEKENINGEN**
