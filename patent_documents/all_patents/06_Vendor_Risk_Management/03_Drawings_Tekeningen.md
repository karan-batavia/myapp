# TEKENINGEN EN FORMULES (DRAWINGS AND FORMULAS)
## Vendor Risk Management - Patent Tekeningen

**PAGINA 13 van 16**

---

## FIGUUR 1: SYSTEEM ARCHITECTUUR OVERZICHT

```
+-------------------------------------------------------------------------+
|         VENDOR RISK MANAGEMENT AUTOMATION PLATFORM                      |
|         Patent-Pending GDPR Article 28 + Schrems II                     |
+-------------------------------------------------------------------------+
                                    |
     +--------------+--------------+--------------+--------------+
     | Article 28   | Schrems II   | Risk         | Netherlands  |
     | Validation   | Transfer     | Scoring      | AP           |
     | (7 checks)   | Assessment   | (Weighted)   | Integration  |
     +--------------+--------------+--------------+--------------+
```

---

## FIGUUR 2: GDPR ARTICLE 28 VALIDATION

```
+-------------------------------------------------------------------------+
|              7 CONTRACTUAL REQUIREMENTS VALIDATION                      |
+-------------------------------------------------------------------------+

REQUIREMENT 1: Processing Instructions (Article 28(3)(a))
   Weight: 20%
   Validation: lawful_basis_documentation == True
   Critical: YES
   
REQUIREMENT 2: Confidentiality (Article 28(3)(b))
   Weight: 15%
   Validation: access_controls != []
   Critical: YES

REQUIREMENT 3: Security Measures (Article 28(3)(c) + Article 32)
   Weight: 25% (HIGHEST)
   Validation: encryption_in_transit AND encryption_at_rest AND audit_logging
   Critical: YES
   
REQUIREMENT 4: Sub-Processors (Article 28(3)(d))
   Weight: 15%
   Validation: sub_processors is not None AND len(sub_processors) ≥ 0
   Critical: YES

REQUIREMENT 5: Data Subject Rights (Article 28(3)(e))
   Weight: 10%
   Validation: data_subject_rights_support == True
   Critical: MEDIUM

REQUIREMENT 6: Deletion/Return (Article 28(3)(g))
   Weight: 10%
   Validation: deletion_procedures != ""
   Critical: MEDIUM

REQUIREMENT 7: Audit Rights (Article 28(3)(h))
   Weight: 5%
   Validation: last_security_review is not None
   Critical: LOW

COMPLIANCE CALCULATION:
   validated_weight = sum(weight for validated requirements)
   total_weight = sum(all weights) = 100%
   compliance_percentage = (validated_weight / total_weight) × 100
   
   article_28_compliant = (compliance_percentage ≥ 95)

EXAMPLE:
   6 of 7 requirements met (missing audit rights, 5% weight)
   validated_weight = 95%
   compliance_percentage = 95%
   article_28_compliant = TRUE ✅
```

---

**PAGINA 14 van 16**

## FIGUUR 3: SCHREMS II TRANSFER ASSESSMENT

```
+-------------------------------------------------------------------------+
|           DATA PROCESSING LOCATION CLASSIFICATION                       |
+-------------------------------------------------------------------------+

LOCATION TYPE               | COMPLIANT | REQUIREMENTS           | ACTION
--------------------------- | --------- | ---------------------- | --------------
EU_EEA                      | ✅ YES    | None                   | No restrictions
ADEQUATE_COUNTRY            | ✅ YES    | Adequacy decision      | Verify decision
USA_PRIVACY_SHIELD          | ❌ NO     | INVALID (Schrems II)   | IMMEDIATE fix
USA_DPF                     | ✅ YES    | DPF certification      | Verify cert
NON_ADEQUATE_COUNTRY        | ⚠️ CONDITIONAL | SCCs or BCRs    | Validate safeguards
UNKNOWN                     | ❌ NO     | Disclosure required    | Request info

+-------------------------------------------------------------------------+
|           TRANSFER MECHANISM VALIDATION LOGIC                           |
+-------------------------------------------------------------------------+

IF location == USA_PRIVACY_SHIELD:
    compliant = FALSE
    severity = "Critical"
    issue = "Privacy Shield invalidated by Schrems II ruling"
    regulation = "CJEU Case C-311/18 (Schrems II)"
    action = "IMMEDIATE: Replace with SCCs or Data Privacy Framework"
    penalty_risk = "€20M or 4% global turnover"

ELIF location == NON_ADEQUATE_COUNTRY:
    IF 'SCCs' not in transfer_mechanisms AND 'BCRs' not in transfer_mechanisms:
        compliant = FALSE
        severity = "Critical"
        issue = "Transfer to non-adequate country without safeguards"
        regulation = "GDPR Articles 46-47"
        action = "IMMEDIATE: Implement Standard Contractual Clauses (SCCs) or Binding Corporate Rules (BCRs)"

ELIF location == USA_DPF:
    # Valid post-Schrems II mechanism
    recommendation = "Verify vendor DPF certification status annually"
    reference = "EU-US Data Privacy Framework (2023)"

TRANSFER MECHANISMS:
   ├─ SCCs (Standard Contractual Clauses) - Approved by European Commission
   ├─ BCRs (Binding Corporate Rules) - Approved by DPA
   ├─ Adequacy Decision - Article 45 GDPR
   ├─ Data Privacy Framework (USA) - Post-Schrems II
   └─ Derogations (Article 49) - Limited use only
```

---

## FIGUUR 4: COMPREHENSIVE RISK SCORING

```
+-------------------------------------------------------------------------+
|              WEIGHTED RISK CALCULATION FORMULA                          |
+-------------------------------------------------------------------------+

COMPONENT SCORES (each 0-100):
   security_score           → S
   compliance_score         → C
   data_processing_score    → D
   financial_stability_score → F
   service_quality_score    → Q

WEIGHTS (industry standard):
   Security: 30% (highest)
   Compliance: 25%
   Data Processing: 25%
   Financial Stability: 10%
   Service Quality: 10%
   TOTAL: 100%

OVERALL RISK SCORE FORMULA:
   overall_risk_score = (S × 0.30) + (C × 0.25) + (D × 0.25) + (F × 0.10) + (Q × 0.10)

RISK LEVEL CLASSIFICATION:
   if overall_risk_score ≥ 80:
       risk_level = MINIMAL     🟢 Low risk, approved
   elif overall_risk_score ≥ 60:
       risk_level = LOW         🟡 Acceptable with monitoring
   elif overall_risk_score ≥ 40:
       risk_level = MEDIUM      🟠 Requires remediation
   elif overall_risk_score ≥ 20:
       risk_level = HIGH        🔴 High priority fixes needed
   else:
       risk_level = CRITICAL    ⛔ Do not use

APPROVAL LOGIC:
   approved_for_use = (overall_risk_score ≥ 60) AND 
                      (compliance_score ≥ 70) AND 
                      (security_score ≥ 65)

EXAMPLE CALCULATION:
   Security: 85
   Compliance: 90
   Data Processing: 75
   Financial: 80
   Service Quality: 70
   
   Overall = (85×0.30) + (90×0.25) + (75×0.25) + (80×0.10) + (70×0.10)
          = 25.5 + 22.5 + 18.75 + 8 + 7
          = 81.75
   
   Risk Level: MINIMAL (≥80) ✅
   Approved: TRUE (81.75≥60, 90≥70, 85≥65) ✅
```

---

**PAGINA 15 van 16**

## FIGUUR 5: SECURITY SCORE CALCULATION

```
+-------------------------------------------------------------------------+
|              SECURITY COMPONENT SCORING BREAKDOWN                       |
+-------------------------------------------------------------------------+

MAX SCORE: 100 points

CATEGORY 1: Encryption (25 points max)
   ├─ encryption_in_transit AND encryption_at_rest → 25 points
   ├─ encryption_in_transit OR encryption_at_rest  → 12 points
   └─ Neither                                      → 0 points

CATEGORY 2: Access Controls (20 points max)
   ├─ ≥3 access control mechanisms → 20 points
   ├─ ≥1 access control mechanism  → 10 points
   └─ No access controls           → 0 points

CATEGORY 3: Audit Logging (15 points max)
   ├─ audit_logging == True  → 15 points
   └─ audit_logging == False → 0 points

CATEGORY 4: Incident Response (15 points max)
   ├─ incident_response_plan == True  → 15 points
   └─ incident_response_plan == False → 0 points

CATEGORY 5: Business Continuity (10 points max)
   ├─ business_continuity_plan == True  → 10 points
   └─ business_continuity_plan == False → 0 points

CATEGORY 6: Security Testing (15 points max)
   ├─ penetration_testing AND vulnerability_management → 15 points
   ├─ penetration_testing OR vulnerability_management  → 7 points
   └─ Neither                                          → 0 points

BONUS CERTIFICATIONS (up to +20 points, capped at 100):
   ├─ ISO27001 certification → +10 points
   ├─ SOC2 certification     → +10 points
   ├─ ISO27018               → +5 points
   └─ PCI-DSS                → +5 points

FINAL CALCULATION:
   security_score = min(base_score + certification_bonus, 100)

EXAMPLE:
   Encryption both: 25
   Access controls (4): 20
   Audit logging: 15
   Incident response: 15
   Business continuity: 10
   Security testing both: 15
   BASE: 100 points
   
   ISO27001: +10
   SOC2: +10
   BONUS: +20 (but capped at 100)
   
   Final: 100 points → EXCELLENT ✅
```

---

## FIGUUR 6: NETHERLANDS AP INTEGRATION

```
+-------------------------------------------------------------------------+
|           ARTICLE 27 LOCAL REPRESENTATIVE VALIDATION                    |
+-------------------------------------------------------------------------+

REQUIREMENT: GDPR Article 27 Local Representative

TRIGGER CONDITIONS:
   IF (vendor.headquarters_country NOT IN EU_EEA_COUNTRIES) AND
      (processing data of Netherlands data subjects):
       
       local_representative_required = TRUE

VALIDATION LOGIC:
   IF local_representative_required:
       IF vendor.responsible_person == "" OR '@' not in responsible_person:
           ap_compliance = FALSE
           
           Issue:
              severity = "High"
              article = "GDPR Article 27"
              requirement = "Vendor must appoint representative in Netherlands or EU"
              ap_reference = "AP Guideline: Article 27 Representatives (2024)"
              penalty = "€10M or 2% global turnover (GDPR Article 83(4))"

EU/EEA COUNTRIES (27 + 3):
   EU Member States (27):
      Austria, Belgium, Bulgaria, Croatia, Cyprus, Czech Republic,
      Denmark, Estonia, Finland, France, Germany, Greece, Hungary,
      Ireland, Italy, Latvia, Lithuania, Luxembourg, Malta,
      Netherlands, Poland, Portugal, Romania, Slovakia, Slovenia,
      Spain, Sweden
   
   EEA Members (non-EU):
      Iceland, Liechtenstein, Norway

DATA RESIDENCY VERIFICATION:
   IF non_eu_locations detected:
       recommendation = "Consider EU data residency for Netherlands customers"
       regulation = "Netherlands UAVG + GDPR Articles 44-49"
       priority = "High"

AP NOTIFICATION TEMPLATES:
   ├─ Data breach notification (< 72 hours)
   ├─ DPIA consultation
   ├─ International transfer notification
   └─ Compliance certificate requests
```

---

**PAGINA 16 van 16**

## FIGUUR 7: VENDOR TYPE CLASSIFICATION

```
+-------------------------------------------------------------------------+
|              7 VENDOR TYPES WITH ASSESSMENT CRITERIA                    |
+-------------------------------------------------------------------------+

TYPE 1: DATA_PROCESSOR
   GDPR Article: 28
   Required Docs: [DPA, Security Documentation, Sub-processor List]
   Critical Requirements:
      ├─ DPA signed
      ├─ Security certifications (ISO27001/SOC2)
      └─ Data breach notification < 72 hours
   Min Compliance Score: 90%

TYPE 2: JOINT_CONTROLLER
   GDPR Article: 26
   Required Docs: [Joint Controller Agreement, Transparency Documentation]
   Critical Requirements:
      ├─ Joint controller arrangement documented
      ├─ Responsibilities clearly defined
      └─ Transparent to data subjects
   Min Compliance Score: 85%

TYPE 3: CLOUD_PROVIDER
   GDPR Article: 28 + 32
   Required Docs: [DPA, Security Certifications, Data Location Map]
   Critical Requirements:
      ├─ Encryption at rest and in transit
      ├─ Data residency controls
      └─ ISO27001 + SOC2 Type II
   Min Compliance Score: 85%

TYPE 4: SAAS_PROVIDER
   GDPR Article: 28
   Required Docs: [DPA, Privacy Policy, Data Flow Diagrams]
   Critical Requirements:
      ├─ Clear data processing purposes
      ├─ Sub-processor disclosure
      └─ Data portability mechanisms
   Min Compliance Score: 80%

TYPE 5: MARKETING_PARTNER
   GDPR Article: 28 + 6
   Required Docs: [DPA, Lawful Basis Documentation, Consent Management]
   Critical Requirements:
      ├─ Lawful basis for processing
      ├─ Consent management system
      └─ Unsubscribe mechanisms
   Min Compliance Score: 80%

TYPE 6: SUB_PROCESSOR
   GDPR Article: 28(2) + 28(4)
   Required Docs: [Sub-processor Agreement, Security Documentation]
   Critical Requirements:
      ├─ Prior authorization obtained
      ├─ Same data protection obligations
      └─ Liability chain documented
   Min Compliance Score: 90%

TYPE 7: CONSULTING_SERVICE
   GDPR Article: 28 (if processing PII)
   Required Docs: [Confidentiality Agreement, Security Policy]
   Critical Requirements:
      ├─ Confidentiality obligations
      ├─ Limited access to data
      └─ Data deletion after engagement
   Min Compliance Score: 75%
```

---

## FIGUUR 8: COMPETITIVE ADVANTAGE

```
+-------------------------------------------------------------------------+
|                     VENDOR RISK MANAGEMENT COMPARISON                   |
+-------------------------------------------------------------------------+

Feature                  | DataGuardian | OneTrust | TrustArc | Manual
                         | Pro          |          |          |
-------------------------|--------------|----------|----------|--------
Article 28 Automation    | ✅ 7 checks  | ⚠️ Partial| ⚠️ Partial| ❌ Manual
Schrems II Assessment    | ✅ Auto      | ❌ NO    | ⚠️ Basic | ❌ Manual
Weighted Risk Scoring    | ✅ 5 factors | ⚠️ Simple| ⚠️ Simple| ❌ Subjective
Netherlands AP Integration| ✅ YES      | ❌ NO    | ❌ NO    | ⚠️ Manual
Article 27 Validation    | ✅ Auto      | ❌ NO    | ❌ NO    | ❌ Manual
Vendor Type Classification| ✅ 7 types  | ⚠️ Basic | ⚠️ Basic | ⚠️ Manual
Privacy Shield Detection | ✅ INVALID   | ❌ NO    | ⚠️ Warning| ❌ NO
Time per Vendor          | ⏱️ 2-3 hrs   | ⏱️ 6 hrs | ⏱️ 8 hrs | ⏱️ 12 hrs
Cost per Vendor          | €500-1.5K    | €2K-5K   | €3K-10K  | €3K-10K

VALUE PROPOSITION:
   "First and only vendor risk platform with automated GDPR Article 28
    validation (7 contractual requirements), Schrems II transfer assessment,
    and Netherlands AP integration for complete compliance automation."

TIME SAVINGS: 75% faster (2-3 hours vs 8-12 hours)
COST SAVINGS: 85% reduction (€500-€1,500 vs €3,000-€10,000)
ACCURACY: Automated validation eliminates human errors
ANNUAL SAVINGS: €50K-€200K for 20-50 vendors
```

---

**EINDE TEKENINGEN**
