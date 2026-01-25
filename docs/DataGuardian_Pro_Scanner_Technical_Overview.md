# DataGuardian Pro - Scanner Technical Overview

**Document Version:** 1.0  
**Classification:** Customer Confidential  
**Last Updated:** January 2025

---

## Executive Summary

DataGuardian Pro is an enterprise privacy compliance platform featuring **17 specialized scanners** designed to detect personally identifiable information (PII) and ensure regulatory compliance. All scanners operate using **local processing** - your data never leaves your environment and is never sent to external AI services.

**Key Differentiators:**
- 100% local processing - no data sent to ChatGPT or external AI
- EU data residency compliant
- Hash-only storage for verification
- Audit-ready reports for regulatory inspections

---

## Scanner Architecture Overview

### Processing Model

```
┌─────────────────────────────────────────────────────────┐
│                    DATA SOURCE                          │
│  (Files, Databases, Websites, Enterprise Systems)       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              LOCAL PROCESSING ENGINE                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Pattern   │  │  Validation │  │    Risk     │     │
│  │  Matching   │  │   Engine    │  │   Scoring   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│               COMPLIANCE REPORTING                       │
│        (PDF/HTML Reports, Audit Trails)                 │
└─────────────────────────────────────────────────────────┘
```

### Data Flow Principles

| Principle | Implementation |
|-----------|---------------|
| **Data Minimization** | Only metadata and hashes stored, never raw PII |
| **Local Processing** | All analysis runs on your infrastructure |
| **No External AI** | Pattern matching, not ChatGPT/cloud AI |
| **Audit Trail** | Complete logging for compliance verification |

---

## Scanner Details

### 1. Code Scanner

**Purpose:** Detect PII, secrets, and compliance violations in source code repositories.

**How It Works:**
1. **File Ingestion:** Scans .py, .js, .java, .cs, .go, and 50+ file types
2. **Pattern Detection:** 200+ regex patterns for PII identification
3. **Secret Detection:** API keys, tokens, passwords, connection strings
4. **Context Analysis:** Differentiates comments, strings, variable names

**Detection Capabilities:**
| Category | Examples |
|----------|----------|
| Dutch PII | BSN (with 11-proef validation), IBAN |
| Personal Data | Email, phone, addresses, names |
| Secrets | AWS keys, database passwords, JWT tokens |
| Compliance | PII in logs, unencrypted storage |

**Output:** File path, line number, exact location, severity rating, remediation guidance.

---

### 2. Document Scanner

**Purpose:** Extract and analyze PII from business documents.

**How It Works:**
1. **Format Support:** PDF, DOCX, XLSX, TXT, CSV
2. **Text Extraction:** PyPDF2 for PDFs, python-docx for Word
3. **Pattern Matching:** Local regex engine scans extracted text
4. **Classification:** Risk scoring based on data sensitivity

**Processing Pipeline:**
```
Document → Text Extraction → Normalization → Pattern Matching → Risk Classification
```

**No external services used.** All processing is local.

---

### 3. Image Scanner (OCR)

**Purpose:** Detect PII in images, scanned documents, and photographs.

**How It Works:**
1. **OCR Engine:** Tesseract (local, open-source)
2. **Image Preprocessing:** OpenCV for quality enhancement
3. **Text Extraction:** Converts images to searchable text
4. **Pattern Detection:** Same 200+ patterns as other scanners

**Supported Formats:** JPG, PNG, TIFF, BMP, GIF, scanned PDFs

**Use Cases:**
- Scanned contracts with personal data
- ID cards and passports
- Handwritten forms
- Screenshots containing PII

---

### 4. Database Scanner

**Purpose:** Identify PII stored in database tables and columns.

**How It Works:**
1. **Connection:** Direct database connection (PostgreSQL, MySQL, SQL Server)
2. **Schema Analysis:** Maps all tables and columns
3. **Sampling:** Analyzes data samples (configurable sample size)
4. **Column Detection:** Identifies columns likely containing PII
5. **Encryption Check:** Verifies if sensitive columns are encrypted

**Detection Logic:**
| Column Name Pattern | Detected As |
|---------------------|-------------|
| *_bsn, bsn_* | Dutch BSN |
| *email*, *mail* | Email Address |
| *phone*, *tel* | Phone Number |
| *name*, *naam* | Personal Name |
| *address*, *adres* | Physical Address |

---

### 5. Website Scanner

**Purpose:** Audit websites for GDPR compliance and privacy issues.

**How It Works:**
1. **Page Crawling:** Fetches web pages using secure HTTP client
2. **Cookie Analysis:** Detects tracking cookies, consent mechanisms
3. **Privacy Policy:** Analyzes completeness of privacy statements
4. **Dark Patterns:** Identifies manipulative UI designs
5. **Third-Party Trackers:** Detects Google Analytics, Facebook Pixel, etc.

**Compliance Checks:**
- Cookie consent banner presence
- Privacy policy completeness (12 GDPR-required sections)
- Data collection forms
- Third-party data sharing
- AI chatbot presence (EU AI Act)

---

### 6. Enterprise Connector Scanner

**Purpose:** Scan enterprise platforms for PII exposure.

**Supported Platforms:**
| Platform | Access Method | What We Scan |
|----------|--------------|--------------|
| Microsoft 365 | OAuth 2.0 | SharePoint, OneDrive, Teams, Exchange |
| Google Workspace | OAuth 2.0 | Drive, Gmail, Calendar |
| Exact Online | OAuth 2.0 | Accounting records, customer data |
| Salesforce | OAuth 2.0 | CRM records, contacts |

**How It Works:**
1. **OAuth Authentication:** Secure, token-based access
2. **API Integration:** Uses official platform APIs
3. **Local Analysis:** Downloads metadata, scans locally
4. **Continuous Monitoring:** Optional scheduled scans

**Security:** Your credentials are never stored. OAuth tokens expire automatically.

---

### 7. AI Model Scanner

**Purpose:** Assess AI/ML models for EU AI Act 2025 compliance.

**How It Works:**
1. **Model Loading:** Supports pickle, joblib, ONNX, PyTorch, H5 formats
2. **Risk Classification:** Maps to EU AI Act categories
3. **Bias Detection:** Statistical fairness analysis
4. **Explainability Scoring:** Transparency assessment
5. **Governance Audit:** Documentation completeness check

**EU AI Act Risk Categories:**
| Category | Description | Penalty Risk |
|----------|-------------|--------------|
| Prohibited | Social scoring, subliminal manipulation | €35M or 7% turnover |
| High-Risk | Biometric, employment, credit scoring | €15M or 3% turnover |
| Limited Risk | Chatbots, emotion recognition | Transparency obligations |
| Minimal Risk | Spam filters, games | No requirements |

**Analysis Methods:**
- **Demographic Parity:** Checks equal outcome rates across groups
- **Equalized Odds:** Verifies equal error rates
- **Calibration Score:** Measures prediction reliability
- **Feature Importance:** Identifies decision drivers

**All analysis is mathematical/statistical - no external AI used.**

---

### 8. DPIA Scanner

**Purpose:** Guide Data Protection Impact Assessments per GDPR Article 35.

**How It Works:**
1. **Wizard Interface:** 5-step guided assessment
2. **Risk Scoring:** Automated calculation based on inputs
3. **Template Generation:** Pre-filled DPIA documentation
4. **Recommendation Engine:** Mitigation suggestions

**DPIA Triggers Detected:**
- Large-scale processing of sensitive data
- Systematic monitoring of public areas
- Automated decision-making with legal effects
- Processing of children's data

---

### 9. SOC2 & NIS2 Scanner

**Purpose:** Validate security controls against compliance frameworks.

**How It Works:**
1. **Control Mapping:** Maps your controls to SOC2 Trust Service Criteria
2. **Gap Analysis:** Identifies missing or weak controls
3. **Evidence Collection:** Logs configuration states
4. **NIS2 Assessment:** EU cybersecurity directive compliance

**Frameworks Covered:**
- SOC2 Type II (5 Trust Service Criteria)
- NIS2 Directive (EU)
- ISO 27001 mapping

---

### 10. Sustainability Scanner

**Purpose:** Analyze cloud infrastructure for environmental impact.

**How It Works:**
1. **Infrastructure Files:** Scans Terraform, CloudFormation, Kubernetes YAML
2. **Resource Analysis:** Identifies oversized instances
3. **Optimization Suggestions:** Auto-scaling recommendations
4. **Carbon Estimation:** Approximate environmental impact

**Note:** Scans configuration files, not live cloud environments.

---

### 11. Audio/Video Scanner

**Purpose:** Detect deepfakes and manipulated media.

**How It Works:**
1. **Spectral Analysis:** Examines audio frequency patterns
2. **Voice Pattern Detection:** Identifies synthetic voice markers
3. **Frame Consistency:** Video frame-by-frame analysis
4. **Metadata Forensics:** Checks for manipulation artifacts

**Supported Formats:**
- Audio: MP3, WAV, FLAC, M4A
- Video: MP4, AVI, MOV, MKV

**Optional Enhancement:** AI-powered frame analysis available (requires OpenAI API key, disabled by default).

---

### 12. Repository Scanner

**Purpose:** Scan Git repositories for PII and secrets exposure.

**How It Works:**
1. **Clone Repository:** Secure access via HTTPS/SSH
2. **History Analysis:** Scans all commits, not just current state
3. **Branch Coverage:** All branches and tags
4. **Staging Check:** Uncommitted changes

**Sub-Scanners:**
| Scanner | Purpose |
|---------|---------|
| Git Scanner | Overall repository analysis |
| Commit Scanner | Per-commit PII detection |
| Branch Scanner | Branch comparison |
| Staging Scanner | Uncommitted file check |

**Banking Sector Features:**
- PCI-DSS v4.0 compliance checks
- IBAN/PAN detection
- BSN validation (11-proef)

---

## Security & Privacy Guarantees

### Data Handling

| Aspect | Our Approach |
|--------|--------------|
| **Storage** | Hash-only verification, never raw PII |
| **Processing** | 100% local, no cloud AI services |
| **Retention** | Configurable (default: 365 days scans, 90 days analytics) |
| **Deletion** | GDPR Art. 17 compliant right-to-erasure |
| **Export** | GDPR Art. 20 compliant data portability |

### What We Never Do

- Send your data to ChatGPT, OpenAI, or any external AI
- Store unencrypted PII
- Share data with third parties
- Train AI models on your data
- Access data without explicit consent

### Certifications & Compliance

| Standard | Status |
|----------|--------|
| GDPR (99 articles) | 100% coverage |
| Netherlands UAVG (51 articles) | 100% coverage |
| EU AI Act 2025 (113 articles) | 100% coverage |
| AP Guidelines 2024-2025 | Compliant |

---

## Technical Specifications

### Performance

| Metric | Specification |
|--------|--------------|
| File Processing | Up to 100MB per file (streaming for larger) |
| Concurrent Scans | Configurable based on license tier |
| Database Sampling | Configurable sample size (1K - 100K rows) |
| Website Crawl Depth | Configurable (default: 3 levels) |

### Integration Options

| Method | Description |
|--------|-------------|
| Web UI | Streamlit-based interface |
| REST API | Programmatic access (Professional+ tiers) |
| Webhooks | Real-time notifications |
| Enterprise Connectors | OAuth-based platform integrations |

---

## Support & Contact

For technical questions or custom implementation:
- **Email:** support@dataguardianpro.nl
- **Documentation:** docs.dataguardianpro.nl
- **Enterprise Support:** Available with Professional+ plans

---

*This document is intended for customer and executive review. Technical implementation details are available under NDA for enterprise customers.*
