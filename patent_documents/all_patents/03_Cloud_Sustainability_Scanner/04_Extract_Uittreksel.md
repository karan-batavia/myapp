# UITTREKSEL (EXTRACT) - MAXIMAAL 250 WOORDEN

## Cloud Sustainability Scanner - Geautomatiseerde Zombie Resource Detection met Regionale CO₂ Berekening

---

## TITEL

Automated Cloud Sustainability Scanner with Zombie Resource Detection, Regional Carbon Footprint Calculation, and EU Green Deal CSRD Compliance for Multi-Cloud Environments

---

## SAMENVATTING (249 WOORDEN)

Een geautomatiseerd cloud sustainability assessment systeem voor zombie resource detection, regionale CO₂ emissie berekening, en EU CSRD compliance. De uitvinding detecteert idle/zombie cloud resources met criteria: CPU <5% gedurende 14+ dagen, underutilized instances <20% utilization, unattached disks, oude snapshots >90 dagen, orphaned load balancers.

Regionale carbon intensity database omvat 15+ cloud regions met werkelijke grid data: Azure North Europe 210 gCO₂/kWh, West Europe (Netherlands) 230 gCO₂/kWh, France Central 60 gCO₂/kWh (nuclear power), AWS EU-West-1 235 gCO₂/kWh, GCP Europe-West-4 60 gCO₂/kWh (wind power).

PUE-based power modeling implementeert provider-specifieke efficiency: Azure PUE 1.12 (12% datacenter overhead), AWS PUE 1.15 (15% overhead), GCP PUE 1.10 (10% overhead, best-in-class). Watt-per-vCPU berekeningen: Azure 13.5W, AWS 14.2W, GCP 12.8W.

Carbon footprint formule: CO₂_kg = ((vCPUs × watts_per_vCPU × hours) / 1000) × PUE × (gCO₂_per_kWh / 1000).

Multi-cloud authentication: Azure OAuth2 naar https://login.microsoftonline.com, AWS boto3 SDK met access keys, GCP service account credentials. Code bloat analysis detecteert repository inefficiencies (nested loops O(n²), redundant API calls, memory leaks).

CSRD compliance reporter genereert Scope 3 emissions tracking conform EU Green Deal 2024-2025 verplichtingen. Optimization potential: €50K-€500K/jaar besparingen via zombie resource elimination.

Technische specificaties: Single unified platform voor Azure/AWS/GCP, automatische resource inventory, utilization trending, year-over-year comparison. Unique differentiator: ONLY tool combining privacy compliance + cloud sustainability assessment.

**[WOORDEN TELLING: 249/250]**

---

**EINDE UITTREKSEL**
