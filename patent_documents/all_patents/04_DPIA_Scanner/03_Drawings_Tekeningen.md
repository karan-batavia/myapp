# TEKENINGEN EN FORMULES (DRAWINGS AND FORMULAS)
## DPIA Scanner - Patent Tekeningen

**PAGINA 13 van 16**

---

## FIGUUR 1: SYSTEEM ARCHITECTUUR OVERZICHT

```
+-------------------------------------------------------------------------+
|                  DPIA SCANNER PLATFORM                                  |
|         Patent-Pending GDPR Article 35 Automation                       |
+-------------------------------------------------------------------------+
                                    |
     +--------------+--------------+--------------+--------------+
     | Legal        | Technical    | Risk         | Netherlands  |
     | Assessment   | Code Scan    | Scoring      | UAVG         |
     | (5 Categories)| (Repository) | (Thresholds) | (AP + BSN)   |
     +--------------+--------------+--------------+--------------+
```

---

## FIGUUR 2: GDPR ARTICLE 35 ASSESSMENT CATEGORIES

```
+-------------------------------------------------------------------------+
|              5-CATEGORY DPIA ASSESSMENT FRAMEWORK                       |
+-------------------------------------------------------------------------+

CATEGORY 1: DATA CATEGORY (Type Gegevens)
   Questions (5):
      ├─ Sensitive/special category data processed?
      ├─ Vulnerable persons data processed?
      ├─ Children's data processed?
      ├─ Large-scale processing?
      └─ Biometric/genetic data processed?

CATEGORY 2: PROCESSING ACTIVITY (Verwerkingsactiviteit)
   Questions (5):
      ├─ Automated decision-making?
      ├─ Systematic and extensive monitoring?
      ├─ Innovative technologies used?
      ├─ Profiling taking place?
      └─ Data combined from multiple sources?

CATEGORY 3: RIGHTS IMPACT (Impact Rechten)
   Questions (5):
      ├─ Could lead to discrimination?
      ├─ Could lead to financial loss?
      ├─ Could lead to reputational damage?
      ├─ Could lead to physical harm?
      └─ Restriction of data subject rights?

CATEGORY 4: TRANSFER & SHARING (Doorgifte & Delen)
   Questions (5):
      ├─ Data transferred outside EU/EEA?
      ├─ Shared with multiple processors?
      ├─ Shared with third parties?
      ├─ International data exchange?
      └─ Data published/publicly available?

CATEGORY 5: SECURITY MEASURES (Beveiligingsmaatregelen)
   Questions (5):
      ├─ Adequate access controls implemented?
      ├─ Data encrypted (at rest + in transit)?
      ├─ Data breach notification procedure?
      ├─ Data minimization measures?
      └─ Security audits performed regularly?

TOTAL: 25 questions across 5 categories
```

---

**PAGINA 14 van 16**

## FIGUUR 3: RISK SCORING ALGORITHM

```
+-------------------------------------------------------------------------+
|                   AUTOMATED RISK SCORING LOGIC                          |
+-------------------------------------------------------------------------+

PER-CATEGORY SCORING:
   category_score = sum(answer_values)
      Where each answer = 0 (No), 1 (Partial), or 2 (Yes) points
   
   max_possible = number_of_questions × 2
   
   percentage = (category_score / max_possible) × 10
      Scale: 0-10 for risk assessment

RISK LEVEL DETERMINATION:
   if percentage >= 7:
       risk_level = "High"       ← DPIA MANDATORY
   elif percentage >= 4:
       risk_level = "Medium"     ← DPIA RECOMMENDED
   else:
       risk_level = "Low"        ← DPIA OPTIONAL

OVERALL DPIA REQUIREMENT:
   dpia_required = (overall_risk == "High") OR
                   (high_risk_categories >= 2) OR
                   (file_high_risk_findings > 0)

EXAMPLE CALCULATION:
   Category: Data Category
   Answers: [2, 2, 0, 2, 2] = 8 points
   Max: 5 questions × 2 = 10 points
   Percentage: (8/10) × 10 = 8.0
   Risk Level: 8.0 >= 7 → "High" → DPIA MANDATORY ✅
```

---

## FIGUUR 4: CODE REPOSITORY INTEGRATION

```
+-------------------------------------------------------------------------+
|              TECHNICAL + LEGAL ASSESSMENT COMBINATION                   |
+-------------------------------------------------------------------------+

MULTI-SOURCE SCANNING:

INPUT OPTION 1: Uploaded Files
   file_paths = ['app.py', 'models.py', 'database.sql']
   ↓
   PII Detection in code, comments, SQL queries

INPUT OPTION 2: GitHub Repository
   github_repo = 'company/privacy-app'
   github_branch = 'main'
   github_token = 'ghp_xxxxx'
   ↓
   Clone → Scan all files → PII detection

INPUT OPTION 3: Local Repository
   repo_path = '/home/user/project'
   ↓
   Walk directory → Scan files → PII detection

PII DETECTION PATTERNS:
   ├─ Email: \b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b
   ├─ Phone: \+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}
   ├─ Credit Card: \b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b
   ├─ SSN: \b\d{3}-\d{2}-\d{4}\b
   ├─ BSN (NL): \b\d{9}\b + checksum validation
   └─ IP Address: \b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b

RISK CLASSIFICATION:
   HIGH Risk Findings:
      ├─ PII hardcoded in production code
      ├─ Database credentials in source files
      ├─ Unencrypted sensitive data storage
      └─ BSN without proper protection

   MEDIUM Risk Findings:
      ├─ PII in test data/fixtures
      ├─ Weak encryption algorithms (MD5, SHA1)
      └─ Missing data minimization

   LOW Risk Findings:
      ├─ PII in code comments
      ├─ Secure credential storage (env vars)
      └─ Encrypted PII with strong algorithms

OVERRIDE LOGIC:
   if file_high_risk > 0:
       overall_risk = "High"      ← Technical findings override
       dpia_required = True        ← questionnaire scores
```

---

**PAGINA 15 van 16**

## FIGUUR 5: ENHANCED REAL-TIME MONITORING

```
+-------------------------------------------------------------------------+
|            MULTI-REGULATORY COMPLIANCE INTEGRATION                      |
+-------------------------------------------------------------------------+

COMPREHENSIVE GDPR VALIDATOR:
   Articles Covered: 25, 30, 35, 37, 44-49
   ↓
   Findings: {
       'total_findings': 15,
       'articles_violated': ['Art. 25', 'Art. 30', 'Art. 35'],
       'severity': 'High'
   }

EU AI ACT COMPLIANCE CHECKER:
   Articles Covered: 5, 6, 16, 17, 26, 29
   ↓
   Violations: [
       'Article 5: Prohibited practices detected',
       'Article 16: Transparency obligations missing'
   ]

NETHERLANDS UAVG VALIDATOR:
   Requirements: AP Guidelines 2024-2025, BSN processing, Data residency
   ↓
   Gaps: [
       'BSN detected without proper safeguards',
       'AP notification template missing'
   ]

AUTOMATIC RISK ESCALATION:
   if critical_violations > 0:
       overall_risk = "High"
       dpia_required = True
   
   elif high_priority_items > 2:
       overall_risk = "High"
       dpia_required = True
```

---

## FIGUUR 6: NETHERLANDS SPECIALIZATION

```
+-------------------------------------------------------------------------+
|              DUTCH LANGUAGE + AP AUTHORITY INTEGRATION                  |
+-------------------------------------------------------------------------+

BILINGUAL SUPPORT (NL/EN):
   language = 'nl':
      ├─ Category names in Dutch
      ├─ Questions in Dutch
      ├─ Recommendations in Dutch
      └─ Legal framework: AVG (not GDPR)
   
   language = 'en':
      ├─ Category names in English
      ├─ Questions in English
      ├─ Recommendations in English
      └─ Legal framework: GDPR

AP AUTHORITY INTEGRATION:
   ├─ AP notification templates (data breach reporting)
   ├─ AP verification URLs (compliance certificate validation)
   ├─ AP reporting standards (UAVG Article 62)
   └─ Data residency verification (Netherlands/EU only)

BSN DETECTION + VALIDATION:
   Pattern: \b\d{9}\b
   
   Checksum (11-proef):
      checksum = (d₀×9) + (d₁×8) + (d₂×7) + (d₃×6) + (d₄×5) +
                 (d₅×4) + (d₆×3) + (d₇×2) - (d₈×1)
      
      Valid if: checksum mod 11 == 0
   
   If BSN detected without protection:
      risk_level = "High"
      recommendation = "Remove BSN or implement Article 9 safeguards"
      article = "GDPR Article 9 (Special Category Data)"
```

---

**PAGINA 16 van 16**

## FIGUUR 7: COMPETITIVE ADVANTAGE MATRIX

```
+-------------------------------------------------------------------------+
|                     MARKET POSITIONING ANALYSIS                         |
+-------------------------------------------------------------------------+

FEATURE COMPARISON:

                          DataGuardian | OneTrust | TrustArc | Manual
                          Pro          | DPIA     | DPIA     | Process
------------------------------------------------------------------------
Code Repository Scan      ✅ YES       | ❌ NO    | ❌ NO    | ❌ NO
Automated Risk Scoring    ✅ Objective | ⚠️ Manual| ⚠️ Manual| ⚠️ Subjective
GitHub Integration        ✅ YES       | ❌ NO    | ❌ NO    | ❌ NO
Technical + Legal         ✅ COMBINED  | ⚠️ Legal | ⚠️ Legal | ⚠️ Legal
BSN Detection             ✅ YES       | ❌ NO    | ❌ NO    | ⚠️ Manual
Dutch Language            ✅ FULL      | ⚠️ Partial| ⚠️ Partial| ✅ YES
AP Integration            ✅ YES       | ❌ NO    | ❌ NO    | ⚠️ Manual
Time Required             ⏱️ 2 hours   | ⏱️ 8 hrs | ⏱️ 12 hrs| ⏱️ 20 hrs
Cost per DPIA             €500-€2K     | €2K-€8K  | €3K-€10K | €5K-€25K

TIME SAVINGS: 90% faster (2 hours vs 20 hours)
COST SAVINGS: 75-90% reduction

UNIQUE VALUE PROPOSITION:
   "First and only DPIA tool combining legal questionnaires with
    automated code repository scanning for technical + legal assessment."
```

---

## FIGUUR 8: PROCESSING FLOW

```
INPUT: Questionnaire Answers + Code Repository
   ↓
STEP 1: 5-Category Assessment (25 questions)
   ↓
STEP 2: Code Repository Scanning (GitHub/Local/Files)
   ↓
STEP 3: Automated PII Detection (Email, Phone, BSN, etc.)
   ↓
STEP 4: Risk Scoring (Per-category + Overall)
   ↓
STEP 5: Enhanced Monitoring (GDPR/AI Act/UAVG)
   ↓
STEP 6: DPIA Necessity Determination (Threshold Logic)
   ↓
STEP 7: Recommendation Generation (Category + Technical)
   ↓
OUTPUT: DPIA Report + Remediation Roadmap
```

---

**EINDE TEKENINGEN**
