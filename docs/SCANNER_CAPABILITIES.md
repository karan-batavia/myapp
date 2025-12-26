# DataGuardian Pro - Scanner Capabilities & Compliance Coverage

## Scanner Suite Overview

DataGuardian Pro includes **12 enterprise-grade scanners** providing comprehensive privacy compliance coverage across GDPR, UAVG (Netherlands), and EU AI Act 2025.

---

## Compliance Coverage Matrix

| Scanner | GDPR | UAVG (NL) | EU AI Act | NIS2 |
|---------|:----:|:---------:|:---------:|:----:|
| 1. Code Scanner | 100% (99 articles) | 100% (51 articles) | Partial | Partial |
| 2. Document Scanner | High | High | High | - |
| 3. Image Scanner | High | High | High | - |
| 4. Database Scanner | High | High | - | Partial |
| 5. Website Scanner | High | High | - | - |
| 6. Audio/Video Scanner | Medium | Medium | 100% (Art. 50, 52) | - |
| 7. AI Model Scanner | Medium | - | 100% (113 articles) | - |
| 8. DPIA Scanner | 100% (Art. 35) | 100% | Partial | - |
| 9. SOC2/NIS2 Scanner | Partial | - | - | 100% |
| 10. Sustainability Scanner | - | - | Partial | - |
| 11. Enterprise Connector | High | High | - | - |
| 12. Advanced AI Scanner | - | - | 100% (113 articles) | - |

---

## Detailed Scanner Capabilities

### 1. Code Scanner
**Purpose**: Detect secrets, PII, and compliance violations in source code

#### Capabilities
| Capability | Description |
|------------|-------------|
| **Secrets Detection** | API keys, tokens, passwords, private keys, connection strings |
| **PII Detection** | Email, phone, SSN, BSN (Dutch), credit cards, IP addresses, names |
| **AI-Generated Code Detection** | Identify AI-generated code patterns and potential security risks |
| **Hardcoded Credentials** | AWS keys, Azure tokens, GCP service accounts, database credentials |
| **Code Fraud Detection** | Backdoors, obfuscation, suspicious code origins |
| **UAVG Pattern Detection** | Dutch-specific patterns (BSN, KvK numbers, IBAN) |

#### Compliance Coverage
| Framework | Coverage | Articles/Controls |
|-----------|----------|-------------------|
| GDPR | 100% | All 99 articles across 11 chapters |
| UAVG (Netherlands) | 100% | All 51 articles including BSN processing, AP Guidelines 2024-2025 |
| EU AI Act | Partial | Art. 52 (Transparency), Art. 5 (Prohibited practices) |
| NIS2 | Partial | Art. 21 (Security measures), Art. 32 (Risk management) |

#### Supported Languages
Python, JavaScript, TypeScript, Java, C#, Go, Ruby, PHP, Rust, SQL, YAML, JSON, XML

---

### 2. Document Scanner (Blob Scanner)
**Purpose**: Extract and analyze PII from documents

#### Capabilities
| Capability | Description |
|------------|-------------|
| **Text Extraction** | PDF, DOCX, XLSX, TXT, RTF, ODT |
| **PII Extraction** | Names, addresses, dates, financial data, health records |
| **AI-Generated Document Detection** | Detect ChatGPT/AI-generated content |
| **Netherlands UAVG Violations** | BSN detection, special category data |
| **EU AI Act Violations** | Detect high-risk AI documentation gaps |
| **Metadata Analysis** | Author, creation date, modification history |

#### Compliance Coverage
| Framework | Coverage | Key Articles |
|-----------|----------|--------------|
| GDPR | High | Art. 5, 6, 9, 17, 25, 30, 32 |
| UAVG | High | Art. 46 (BSN), Art. 22 (Special categories) |
| EU AI Act | High | Art. 11-12 (Technical documentation) |

#### Supported Formats
PDF, DOCX, DOC, XLSX, XLS, PPTX, TXT, RTF, ODT, ODS, CSV

---

### 3. Image Scanner
**Purpose**: OCR-based PII extraction and biometric detection

#### Capabilities
| Capability | Description |
|------------|-------------|
| **OCR Text Extraction** | Multi-language OCR with region-specific optimization |
| **Face Detection** | Identify faces in images for biometric compliance |
| **Document Detection** | ID cards, passports, driver licenses |
| **Card Detection** | Credit/debit cards, bank cards |
| **EXIF Metadata Extraction** | GPS location, device info, timestamps |
| **QR/Barcode Scanning** | Detect embedded data in codes |
| **Watermark Detection** | Identify document watermarks |
| **Screenshot Detection** | Detect screen captures |
| **Signature Detection** | Identify handwritten signatures |
| **Steganography Detection** | Detect hidden data in images |
| **Deepfake Detection** | AI-generated face detection |

#### Compliance Coverage
| Framework | Coverage | Key Articles |
|-----------|----------|--------------|
| GDPR | High | Art. 9 (Biometrics), Art. 5 (Data minimization) |
| UAVG | High | Art. 29 (Photo ID restrictions) |
| EU AI Act | High | Art. 5 (Biometric identification), Art. 6 (High-risk systems) |

#### Supported Formats
JPEG, PNG, GIF, BMP, TIFF, WEBP, HEIC

---

### 4. Database Scanner
**Purpose**: Detect PII and retention violations in databases

#### Capabilities
| Capability | Description |
|------------|-------------|
| **Schema Analysis** | Identify PII-containing columns by name patterns |
| **Content Sampling** | Analyze sample data for PII patterns |
| **Retention Violations** | Detect data exceeding retention periods |
| **Access Patterns** | Analyze who has access to sensitive data |
| **Encryption Status** | Check for encrypted columns |
| **Audit Trail Analysis** | Verify audit logging exists |
| **Google Cloud SQL Detection** | Identify cloud-hosted databases |

#### Compliance Coverage
| Framework | Coverage | Key Articles |
|-----------|----------|--------------|
| GDPR | High | Art. 5 (Storage limitation), Art. 17 (Erasure), Art. 30 (Records) |
| UAVG | High | Art. 46 (BSN storage), Art. 22 (Special categories) |
| NIS2 | Partial | Art. 21 (Security measures) |

#### Supported Databases
PostgreSQL, MySQL, MariaDB, SQLite, SQL Server, Oracle (via ODBC)

---

### 5. Website Scanner
**Purpose**: Cookie consent, trackers, and privacy policy compliance

#### Capabilities
| Capability | Description |
|------------|-------------|
| **Cookie Analysis** | Identify all cookies (essential, analytics, marketing, third-party) |
| **Consent Mechanism Detection** | Cookiebot, CookiePro, CivicUK, CookieYes, etc. |
| **Tracker Detection** | Google Analytics, Facebook Pixel, LinkedIn Insight, Hotjar, etc. |
| **Privacy Policy Analysis** | Check for required disclosures |
| **Third-Party Scripts** | Identify external JavaScript |
| **Data Collection Forms** | Analyze form fields for PII collection |
| **SSL/TLS Analysis** | Certificate and encryption status |

#### Tracker Risk Classification
| Tracker | Privacy Risk | GDPR Basis |
|---------|--------------|------------|
| Google Analytics | Medium | Consent/Legitimate interest |
| Facebook Pixel | High | Consent required |
| Hotjar | High | Consent required |
| LinkedIn Insight | High | Consent required |
| Crisp Chat | Medium | Legitimate interest |

#### Compliance Coverage
| Framework | Coverage | Key Articles |
|-----------|----------|--------------|
| GDPR | High | Art. 6, 7 (Consent), Art. 13-14 (Transparency) |
| UAVG | High | Telecommunicatiewet (Cookie law) |
| ePrivacy | High | Cookie consent requirements |

---

### 6. Audio/Video Scanner (Deepfake Detection)
**Purpose**: Detect synthetic media and deepfakes

#### Capabilities
| Capability | Description |
|------------|-------------|
| **Spectral Analysis** | Detect unnatural frequency patterns in audio |
| **Voice Cloning Detection** | Identify AI-generated speech |
| **Face Swap Detection** | Detect deepfake face replacements |
| **Frame Consistency Analysis** | Identify video manipulation artifacts |
| **Metadata Forensics** | Analyze file metadata for tampering |
| **Lip-Sync Analysis** | Detect audio-video mismatch |
| **AI Generation Markers** | Identify synthetic media signatures |
| **Authenticity Scoring** | 0-100 authenticity score |

#### Detection Types
| Type | Description |
|------|-------------|
| `AUDIO_DEEPFAKE` | AI-generated or cloned voice |
| `AUDIO_SPLICING` | Audio segments merged together |
| `VIDEO_DEEPFAKE` | Face swap or replacement |
| `VIDEO_SPLICING` | Video segments merged |
| `AI_GENERATED_VIDEO` | Fully AI-generated video |

#### Compliance Coverage
| Framework | Coverage | Key Articles |
|-----------|----------|--------------|
| EU AI Act | 100% | Art. 50 (Transparency for deepfakes), Art. 52 (Disclosure requirements) |
| GDPR | Medium | Art. 5 (Accuracy), Art. 22 (Automated decisions) |

#### Supported Formats
**Audio**: MP3, WAV, FLAC, M4A, OGG, AAC
**Video**: MP4, AVI, MOV, MKV, WEBM, WMV

---

### 7. AI Model Scanner
**Purpose**: EU AI Act compliance and risk classification

#### Capabilities
| Capability | Description |
|------------|-------------|
| **Risk Classification** | Prohibited, High-Risk, Limited, Minimal, General Purpose |
| **Framework Detection** | TensorFlow, PyTorch, ONNX, scikit-learn |
| **Prohibited Practice Detection** | Social scoring, subliminal manipulation |
| **High-Risk Requirements Check** | Conformity assessment, documentation |
| **GPAI Compliance** | General Purpose AI model requirements |
| **Penalty Assessment** | Calculate potential fine exposure |
| **Enforcement Timeline** | Track compliance deadlines |

#### Risk Categories
| Category | Description | Max Penalty |
|----------|-------------|-------------|
| Prohibited | Banned AI practices | €35M / 7% turnover |
| High-Risk | Biometrics, healthcare, employment | €15M / 3% turnover |
| Limited Risk | User-facing AI (chatbots) | €7.5M / 1.5% turnover |
| Minimal Risk | Low-impact applications | None |
| GPAI | Large language models | Varies |

#### Compliance Coverage
| Framework | Coverage | Articles |
|-----------|----------|----------|
| EU AI Act | 100% | All 113 articles across 12 chapters |
| Enforcement Timeline | Feb 2025 (Prohibited), Aug 2025 (GPAI), Aug 2027 (High-risk) |

---

### 8. DPIA Scanner
**Purpose**: GDPR Article 35 Data Protection Impact Assessment

#### Capabilities
| Capability | Description |
|------------|-------------|
| **5-Step Wizard** | Guided DPIA process |
| **Risk Scoring** | Low, Medium, High, Critical assessment |
| **Processing Activity Analysis** | Identify high-risk processing |
| **Rights Impact Assessment** | Evaluate data subject rights impact |
| **Automated Recommendations** | Generate mitigation measures |
| **PDF Report Generation** | Formal DPIA documentation |
| **Enhanced GDPR Validation** | Art. 25, 30, 35, 37, 44-49 checks |

#### Assessment Categories
| Category | Description |
|----------|-------------|
| Data Collection | Nature and scope of data collected |
| Processing Purpose | Lawfulness of processing activities |
| Data Sharing | Third-party and cross-border transfers |
| Security Measures | Technical and organizational controls |
| Rights Impact | Effect on data subject rights |

#### Compliance Coverage
| Framework | Coverage | Key Articles |
|-----------|----------|--------------|
| GDPR | 100% | Art. 35 (DPIA requirement), Art. 36 (Prior consultation) |
| UAVG | 100% | Dutch AP Guidelines for DPIA |

---

### 9. SOC2/NIS2 Scanner
**Purpose**: Security compliance for infrastructure-as-code

#### Capabilities
| Capability | Description |
|------------|-------------|
| **SOC2 Trust Principles** | Security, Availability, Processing Integrity, Confidentiality, Privacy |
| **NIS2 Directive Coverage** | EU 2022/2555 cybersecurity requirements |
| **IaC Analysis** | Terraform, CloudFormation, Ansible, Kubernetes |
| **Encryption Checks** | Data-at-rest and in-transit encryption |
| **Access Control** | IAM, RBAC, MFA requirements |
| **Logging/Monitoring** | Audit trail and alerting requirements |
| **Incident Response** | Breach notification compliance |

#### NIS2 Article Coverage
| Article | Description |
|---------|-------------|
| NIS2-20 | Management body oversight and accountability |
| NIS2-21 | Cybersecurity risk-management measures |
| NIS2-22 | Supply chain security assessment |
| NIS2-23 | 24/72-hour incident notification |

#### Compliance Coverage
| Framework | Coverage | Controls |
|-----------|----------|----------|
| SOC2 | High | 5 Trust Service Criteria |
| NIS2 | 100% | All applicable articles for essential entities |
| ISO 27001 | Partial | Mapped controls |

---

### 10. Sustainability Scanner
**Purpose**: Cloud carbon footprint and resource optimization

#### Capabilities
| Capability | Description |
|------------|-------------|
| **IaC File Analysis** | Terraform, CloudFormation, ARM, Bicep, Kubernetes |
| **Carbon Footprint Calculation** | CO2 emissions per resource |
| **Oversized Instance Detection** | Identify right-sizing opportunities |
| **Auto-Scaling Analysis** | Check for scaling policies |
| **Region Carbon Intensity** | Compare regional emissions |
| **Cost Optimization** | Identify savings opportunities |
| **Sustainability Score** | 0-100 environmental rating |

#### Supported Cloud Providers
| Provider | File Types |
|----------|-----------|
| AWS | CloudFormation (JSON/YAML), Terraform |
| Azure | ARM templates, Bicep, Terraform |
| GCP | Deployment Manager, Terraform |
| Kubernetes | YAML manifests |
| Docker | Dockerfile, docker-compose |

#### Compliance Coverage
| Framework | Coverage | Notes |
|-----------|----------|-------|
| EU AI Act | Partial | Art. 40 (Energy efficiency) |
| CSRD | Partial | Climate reporting requirements |

---

### 11. Enterprise Connector Scanner
**Purpose**: PII detection in enterprise cloud platforms

#### Capabilities
| Capability | Description |
|------------|-------------|
| **Microsoft 365 Integration** | SharePoint, OneDrive, Exchange, Teams |
| **Google Workspace Integration** | Drive, Gmail, Docs, Sheets |
| **Exact Online Integration** | Dutch ERP system (60% NL SME market) |
| **OAuth2 Token Management** | Automatic token refresh |
| **Rate Limiting** | API quota management |
| **Checkpoint/Resume** | Resume interrupted scans |
| **Multi-Company Support** | Exact Online divisions |

#### Microsoft 365 Scanning
| Service | Scanned Content |
|---------|-----------------|
| SharePoint | Documents, lists, sites |
| OneDrive | Personal files, shared files |
| Exchange | Emails, attachments |
| Teams | Messages, files, channels |

#### Google Workspace Scanning
| Service | Scanned Content |
|---------|-----------------|
| Drive | Documents, spreadsheets, PDFs |
| Gmail | Email bodies, attachments |
| Docs | Document content |

#### Compliance Coverage
| Framework | Coverage | Key Articles |
|-----------|----------|--------------|
| GDPR | High | Art. 30 (Processing records), Art. 44-49 (Transfers) |
| UAVG | High | Art. 46 (BSN in enterprise systems) |

---

### 12. Advanced AI Scanner
**Purpose**: Deep AI model analysis with bias and explainability assessment

#### Capabilities
| Capability | Description |
|------------|-------------|
| **Bias Detection** | Demographic parity, equalized odds, calibration |
| **Explainability Assessment** | SHAP, LIME, feature importance scoring |
| **Governance Evaluation** | Risk management, documentation, oversight |
| **EU AI Act 18-Phase Analysis** | Complete article coverage |
| **Fairness Metrics** | Individual and group fairness |
| **Model Transparency Rating** | Black-box to glass-box classification |
| **Audit Trail Quality** | Documentation completeness |

#### Bias Detection Algorithms
| Algorithm | Description | Threshold |
|-----------|-------------|-----------|
| Demographic Parity | Statistical parity across groups | 0.8 |
| Equalized Odds | Equal TPR/FPR across groups | 0.8 |
| Calibration | Prediction accuracy per group | 0.1 |
| Individual Fairness | Similar inputs → similar outputs | 0.9 |

#### Explainability Methods
| Method | Techniques |
|--------|------------|
| Feature Importance | SHAP, LIME, Permutation |
| Counterfactual | Contrastive examples |
| Example-Based | Prototypes, criticisms |
| Attention-Based | Attention maps, Grad-CAM |
| Rule-Based | Decision trees, rule extraction |

#### Compliance Coverage
| Framework | Coverage | Articles |
|-----------|----------|----------|
| EU AI Act | 100% | All 113 articles (18 assessment phases) |
| Bias Regulations | High | Art. 10 (Data governance), Art. 15 (Accuracy) |

---

## Summary: Full Compliance Coverage

| Framework | Total Articles | Coverage | Primary Scanners |
|-----------|---------------|----------|------------------|
| **GDPR** | 99 | 100% | Code Scanner, DPIA Scanner |
| **UAVG (Netherlands)** | 51 | 100% | Code Scanner |
| **EU AI Act 2025** | 113 | 100% | AI Model + Advanced AI Scanner |
| **NIS2 Directive** | 46 | 100% | SOC2/NIS2 Scanner |

---

*Document Version: 1.0*
*Last Updated: December 2025*
