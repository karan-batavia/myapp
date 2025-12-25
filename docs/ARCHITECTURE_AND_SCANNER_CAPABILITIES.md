# DataGuardian Pro - Architecture & Scanner Capabilities

## Complete Technical Architecture

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DATAGUARDIAN PRO ARCHITECTURE                            │
│                     Enterprise Privacy Compliance Platform                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         FRONTEND LAYER                                   │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │    │
│  │  │  Dashboard  │  │  New Scan   │  │   Results   │  │   Settings  │    │    │
│  │  │   Page      │  │    Page     │  │    Page     │  │    Page     │    │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │    │
│  │  │   History   │  │   Pricing   │  │    Admin    │  │   Privacy   │    │    │
│  │  │    Page     │  │    Page     │  │   Panel     │  │   Rights    │    │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │    │
│  │                                                                         │    │
│  │  Technology: Streamlit + Custom CSS/JS                                  │    │
│  │  Languages: English, Dutch (auto-detect)                               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         AUTHENTICATION LAYER                             │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │ JWT Tokens   │  │ bcrypt Hash  │  │ Role-Based   │                   │    │
│  │  │ (Sessions)   │  │ (Passwords)  │  │ Access (7)   │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  │                                                                          │    │
│  │  Roles: Admin, Enterprise Admin, Manager, Analyst, Auditor, User, Guest │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         SCANNER ENGINE (12 Scanners)                     │    │
│  │                                                                          │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐           │    │
│  │  │   Code     │ │  Website   │ │   Image    │ │   Blob     │           │    │
│  │  │  Scanner   │ │  Scanner   │ │  Scanner   │ │  Scanner   │           │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘           │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐           │    │
│  │  │ Database   │ │ Audio/Video│ │ AI Model   │ │   DPIA     │           │    │
│  │  │  Scanner   │ │ (Deepfake) │ │  Scanner   │ │  Scanner   │           │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘           │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐           │    │
│  │  │   SOC2     │ │Sustainability│ │   API     │ │  Domain    │           │    │
│  │  │  Scanner   │ │  Scanner   │ │  Scanner   │ │  Scanner   │           │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘           │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         PROCESSING LAYER                                 │    │
│  │                                                                          │    │
│  │  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │    │
│  │  │   Redis Queue    │    │  Scanner Workers │    │  AI Risk Engine  │   │    │
│  │  │  (Job Storage)   │◄──►│  (1-N Containers)│◄──►│  (OpenAI GPT-4)  │   │    │
│  │  └──────────────────┘    └──────────────────┘    └──────────────────┘   │    │
│  │                                                                          │    │
│  │  Features: Async processing, auto-scaling, fault tolerance              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         COMPLIANCE ENGINE                                │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │ GDPR 100%    │  │ Netherlands  │  │ EU AI Act    │                   │    │
│  │  │ (99 Articles)│  │ UAVG         │  │ (113 Articles)│                  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │ SOC2 Type II │  │ ISO 27001    │  │ Region Rules │                   │    │
│  │  │ Controls     │  │ Mapping      │  │ (NL/DE/FR/BE)│                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         DATA LAYER                                       │    │
│  │                                                                          │    │
│  │  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │    │
│  │  │   PostgreSQL     │    │   Redis Cache    │    │  File Storage    │   │    │
│  │  │  (Scan Results)  │    │  (Sessions/Jobs) │    │  (Reports/Certs) │   │    │
│  │  └──────────────────┘    └──────────────────┘    └──────────────────┘   │    │
│  │                                                                          │    │
│  │  GDPR Compliant: 365-day retention, PII hashing, data export/delete    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         REPORTING LAYER                                  │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │ PDF Reports  │  │ HTML Reports │  │ Compliance   │                   │    │
│  │  │ (Executive)  │  │ (Interactive)│  │ Certificates │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         PAYMENT & LICENSING                              │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │   Stripe     │  │    iDEAL     │  │   License    │                   │    │
│  │  │  Payments    │  │  (Netherlands)│  │  Management  │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  │                                                                          │    │
│  │  Tiers: Starter (€99), Professional (€299), Business (€599),            │    │
│  │         Enterprise (€999), Ultimate (€1499)                             │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## The 12 Scanners: Complete Capabilities

### 1. CODE SCANNER
**Purpose:** Detect secrets, PII, and compliance issues in source code

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CODE SCANNER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ API Keys (AWS, Azure, GCP, Stripe, OpenAI, etc.)                    │ │
│  │ ✓ Database Credentials (PostgreSQL, MySQL, MongoDB, Redis)            │ │
│  │ ✓ Private Keys (SSH, RSA, PGP, SSL certificates)                      │ │
│  │ ✓ OAuth Tokens (Google, Facebook, Twitter, GitHub)                    │ │
│  │ ✓ Personal Data (emails, phone numbers, addresses)                    │ │
│  │ ✓ Dutch BSN Numbers (Burgerservicenummer)                             │ │
│  │ ✓ IBAN Bank Account Numbers                                            │ │
│  │ ✓ High Entropy Strings (potential hardcoded secrets)                  │ │
│  │ ✓ TODO/FIXME comments with security implications                      │ │
│  │ ✓ Git History Secrets (commits with leaked credentials)               │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  COMPLIANCE COVERAGE:                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • GDPR Article 32 (Security of Processing)                            │ │
│  │ • GDPR Article 25 (Data Protection by Design)                         │ │
│  │ • Netherlands UAVG Article 46 (BSN handling)                          │ │
│  │ • EU AI Act (AI system detection in code)                             │ │
│  │ • SOC2 CC6.1 (Logical access controls)                                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "Find exposed API keys before hackers do. One leaked AWS key can cost    │
│   €50,000+ in unauthorized usage. We scan your entire codebase in minutes."│
│                                                                             │
│  SUPPORTED LANGUAGES: Python, JavaScript, TypeScript, Java, C#, Go, PHP,  │
│                       Ruby, Rust, Swift, Kotlin, Terraform, YAML, JSON    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2. WEBSITE SCANNER
**Purpose:** Scan live websites for privacy compliance issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            WEBSITE SCANNER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ Cookie Consent Issues (missing banner, pre-checked boxes)           │ │
│  │ ✓ Third-Party Trackers (Google Analytics, Facebook Pixel, etc.)       │ │
│  │ ✓ Missing Privacy Policy                                               │ │
│  │ ✓ Missing Cookie Policy                                                 │ │
│  │ ✓ Data Collection Forms (without consent)                              │ │
│  │ ✓ External Scripts Loading Personal Data                               │ │
│  │ ✓ SSL/TLS Configuration Issues                                         │ │
│  │ ✓ Data Transfer to Non-EU Countries                                    │ │
│  │ ✓ Hidden Tracking Pixels                                                │ │
│  │ ✓ Contact Forms Without Privacy Notice                                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  COMPLIANCE COVERAGE:                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • GDPR Article 7 (Consent conditions)                                 │ │
│  │ • GDPR Article 13 (Information to be provided)                        │ │
│  │ • GDPR Articles 44-49 (International transfers)                       │ │
│  │ • ePrivacy Directive (Cookie rules)                                   │ │
│  │ • Netherlands Telecommunicatiewet                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "Your website is often the first place regulators look. Dutch DPA fines  │
│   for cookie violations start at €10,000. We check 50+ compliance points." │
│                                                                             │
│  SCAN DEPTH: Homepage + up to 100 linked pages                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3. IMAGE SCANNER (OCR)
**Purpose:** Extract and detect PII from images and scanned documents

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             IMAGE SCANNER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ Text in Images (OCR - Optical Character Recognition)                │ │
│  │ ✓ Scanned ID Documents (passports, driver's licenses)                 │ │
│  │ ✓ Scanned Contracts with Personal Data                                 │ │
│  │ ✓ Screenshots with Sensitive Information                               │ │
│  │ ✓ Whiteboard Photos with Customer Data                                 │ │
│  │ ✓ Medical Documents and Prescriptions                                  │ │
│  │ ✓ Financial Statements and Invoices                                    │ │
│  │ ✓ Handwritten Notes with Personal Data                                 │ │
│  │ ✓ Business Cards                                                        │ │
│  │ ✓ Embedded EXIF Metadata (GPS location, device info)                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  COMPLIANCE COVERAGE:                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • GDPR Article 4 (Personal data definition)                           │ │
│  │ • GDPR Article 9 (Special categories - health, biometric)             │ │
│  │ • GDPR Article 30 (Records of processing)                             │ │
│  │ • Netherlands UAVG Article 30 (Medical data)                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "That scanned contract from 2018 might contain customer data you forgot  │
│   about. We find PII hidden in images that text searches miss."            │
│                                                                             │
│  SUPPORTED FORMATS: PNG, JPG, JPEG, TIFF, BMP, GIF, WebP, PDF (images)    │
│  LANGUAGES: Dutch, English, German, French, Spanish + 100 more            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 4. AUDIO/VIDEO SCANNER (DEEPFAKE DETECTION)
**Purpose:** Detect AI-generated deepfakes and embedded PII in media files

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUDIO/VIDEO SCANNER (DEEPFAKE)                        │
│                   "The Only Deepfake Detector for EU Compliance"           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ DEEPFAKE DETECTION:                                                    │ │
│  │ ✓ AI-Generated Voices (voice cloning, text-to-speech)                 │ │
│  │ ✓ Face Swaps in Video (DeepFaceLab, FaceSwap detection)               │ │
│  │ ✓ Lip-Sync Manipulation                                                │ │
│  │ ✓ Audio Splicing and Editing                                           │ │
│  │ ✓ Frame Consistency Analysis                                           │ │
│  │ ✓ Spectral Analysis for Synthetic Audio                                │ │
│  │                                                                         │ │
│  │ METADATA & PII:                                                         │ │
│  │ ✓ Embedded Personal Data in Audio/Video                                │ │
│  │ ✓ Speaker Identification Metadata                                      │ │
│  │ ✓ Recording Location (GPS in metadata)                                 │ │
│  │ ✓ Device Fingerprints                                                  │ │
│  │ ✓ Creation/Modification Timestamps                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  COMPLIANCE COVERAGE:                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • EU AI Act Article 50 (Transparency for AI-generated content)        │ │
│  │ • EU AI Act Article 52 (Disclosure of synthetic media)                │ │
│  │ • GDPR Article 22 (Automated decision-making)                         │ │
│  │ • DSA Article 35 (Disinformation obligations)                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "Under EU AI Act 2025, companies must detect and label AI-generated      │
│   content. Fines up to €35 million. We're the only Dutch solution."       │
│                                                                             │
│  SUPPORTED FORMATS:                                                         │
│  Audio: MP3, WAV, FLAC, M4A, OGG, WMA                                      │
│  Video: MP4, AVI, MOV, MKV, WebM, WMV                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 5. DATABASE SCANNER
**Purpose:** Scan databases for unprotected personal data

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE SCANNER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ Unencrypted Personal Data (names, emails, addresses)                 │ │
│  │ ✓ Plain-text Passwords                                                  │ │
│  │ ✓ Financial Data (credit cards, bank accounts, IBAN)                   │ │
│  │ ✓ Health/Medical Records                                                │ │
│  │ ✓ Dutch BSN Numbers in Tables                                           │ │
│  │ ✓ Data Retention Violations (old data that should be deleted)          │ │
│  │ ✓ Missing Audit Trails                                                  │ │
│  │ ✓ Excessive Data Collection                                             │ │
│  │ ✓ Orphaned Personal Records                                             │ │
│  │ ✓ Cross-Reference Privacy Risks                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SUPPORTED DATABASES:                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • PostgreSQL       • MySQL/MariaDB     • Microsoft SQL Server          │ │
│  │ • Oracle           • MongoDB           • SQLite                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  COMPLIANCE COVERAGE:                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • GDPR Article 5 (Data minimization, storage limitation)              │ │
│  │ • GDPR Article 17 (Right to erasure verification)                     │ │
│  │ • GDPR Article 32 (Encryption requirements)                           │ │
│  │ • SOC2 CC6.7 (Data protection in storage)                             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "80% of data breaches involve databases. We find the personal data       │
│   you didn't know you were storing - before regulators find it."          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 6. BLOB/DOCUMENT SCANNER
**Purpose:** Scan documents and files for personal data

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BLOB/DOCUMENT SCANNER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ Personal Data in Documents (PDFs, Word, Excel)                       │ │
│  │ ✓ Customer Lists and Contact Information                               │ │
│  │ ✓ Employment Records and HR Documents                                  │ │
│  │ ✓ Financial Reports with Personal Data                                 │ │
│  │ ✓ Legal Contracts and Agreements                                       │ │
│  │ ✓ Email Archives (PST, MBOX)                                           │ │
│  │ ✓ Presentations with Customer Data                                     │ │
│  │ ✓ Spreadsheets with Personal Information                               │ │
│  │ ✓ Hidden Metadata (author, revision history)                           │ │
│  │ ✓ Document Fraud Detection (altered documents)                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SUPPORTED FORMATS:                                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Documents: PDF, DOCX, DOC, ODT, RTF, TXT                               │ │
│  │ Spreadsheets: XLSX, XLS, CSV, ODS                                      │ │
│  │ Presentations: PPTX, PPT, ODP                                          │ │
│  │ Archives: ZIP, RAR, 7Z, TAR.GZ                                         │ │
│  │ Email: EML, MSG, PST, MBOX                                             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "That 2019 Excel file in your shared drive? It might contain 10,000      │
│   customer emails. We find forgotten personal data across all your files." │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 7. DPIA SCANNER (Data Protection Impact Assessment)
**Purpose:** Automated GDPR Article 35 compliance assessment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DPIA SCANNER                                   │
│                   Data Protection Impact Assessment                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT PROVIDES:                                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ 5-Step DPIA Wizard (guided assessment)                               │ │
│  │ ✓ Processing Activity Analysis                                          │ │
│  │ ✓ Necessity and Proportionality Assessment                             │ │
│  │ ✓ Risk Identification and Evaluation                                   │ │
│  │ ✓ Mitigation Measures Recommendations                                  │ │
│  │ ✓ Stakeholder Consultation Tracking                                    │ │
│  │ ✓ DPO Review Workflow                                                  │ │
│  │ ✓ Regulatory-Ready DPIA Reports                                        │ │
│  │ ✓ Historical DPIA Version Control                                      │ │
│  │ ✓ Integration with Other Scanners                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  COMPLIANCE COVERAGE:                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • GDPR Article 35 (Data Protection Impact Assessment)                 │ │
│  │ • GDPR Article 36 (Prior consultation with DPA)                       │ │
│  │ • Netherlands AP DPIA Guidelines                                       │ │
│  │ • WP29 DPIA Guidelines                                                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "A proper DPIA takes 40+ hours manually. Our wizard completes it in      │
│   2 hours with auto-generated regulatory-ready documentation."            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 8. AI MODEL SCANNER
**Purpose:** Audit AI/ML systems for EU AI Act compliance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI MODEL SCANNER                                  │
│                      EU AI Act 2025 Compliance                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ AI RISK CLASSIFICATION:                                                 │ │
│  │ ✓ Unacceptable Risk AI (banned applications)                           │ │
│  │ ✓ High-Risk AI (requires conformity assessment)                        │ │
│  │ ✓ Limited Risk AI (transparency obligations)                           │ │
│  │ ✓ Minimal Risk AI (voluntary codes)                                    │ │
│  │                                                                         │ │
│  │ TECHNICAL ANALYSIS:                                                     │ │
│  │ ✓ Training Data Documentation                                          │ │
│  │ ✓ Model Bias Detection                                                 │ │
│  │ ✓ Explainability Assessment                                            │ │
│  │ ✓ Human Oversight Mechanisms                                           │ │
│  │ ✓ Robustness and Accuracy Testing                                      │ │
│  │ ✓ Cybersecurity Measures                                               │ │
│  │ ✓ Version Control and Logging                                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  EU AI ACT TIMELINE TRACKING:                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Feb 2025: Prohibited AI practices take effect                         │ │
│  │ Aug 2025: General provisions and GPAI apply                           │ │
│  │ Aug 2026: High-risk AI obligations apply                              │ │
│  │ Aug 2027: Full enforcement                                             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "EU AI Act fines: up to €35 million or 7% global revenue. We audit your  │
│   AI systems against all 113 articles before regulators do."              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 9. SOC2 SCANNER
**Purpose:** Assess SOC2 Type II audit readiness

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SOC2 SCANNER                                    │
│                    Service Organization Control 2                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT ASSESSES:                                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ TRUST SERVICE CRITERIA:                                                 │ │
│  │ ✓ Security (CC1-CC9): Access controls, system operations               │ │
│  │ ✓ Availability (A1): System availability commitments                   │ │
│  │ ✓ Processing Integrity (PI1): Complete, accurate processing           │ │
│  │ ✓ Confidentiality (C1): Protection of confidential data               │ │
│  │ ✓ Privacy (P1-P8): Personal information handling                      │ │
│  │                                                                         │ │
│  │ CONTROL AREAS:                                                          │ │
│  │ ✓ Logical Access Controls                                              │ │
│  │ ✓ Change Management                                                    │ │
│  │ ✓ Risk Assessment                                                      │ │
│  │ ✓ Monitoring and Logging                                               │ │
│  │ ✓ Incident Response                                                    │ │
│  │ ✓ Vendor Management                                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "SOC2 audits cost €50,000-€100,000. Our pre-audit scanner identifies     │
│   gaps before auditors arrive, reducing remediation costs by 60%."        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 10. SUSTAINABILITY SCANNER
**Purpose:** Scan cloud infrastructure files for environmental impact

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SUSTAINABILITY SCANNER                               │
│                   Cloud Carbon Footprint Analysis                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ Oversized Cloud Instances (unnecessary resource allocation)          │ │
│  │ ✓ Missing Auto-Scaling Configurations                                  │ │
│  │ ✓ 24/7 Running Non-Production Resources                                │ │
│  │ ✓ Inefficient Container Configurations                                 │ │
│  │ ✓ Missing Spot/Preemptible Instance Usage                              │ │
│  │ ✓ Inefficient Region Selection (high carbon regions)                   │ │
│  │ ✓ Redundant Resource Definitions                                       │ │
│  │ ✓ Energy-Inefficient Database Configurations                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SUPPORTED FILES:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • Terraform (.tf)            • AWS CloudFormation                      │ │
│  │ • Azure ARM/Bicep            • GCP Deployment Manager                  │ │
│  │ • Kubernetes YAML            • Docker Compose                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "EU CSRD requires sustainability reporting from 2025. We quantify your   │
│   cloud carbon footprint and recommend 20-40% cost/emission reductions."  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 11. API SCANNER
**Purpose:** Scan API endpoints for security and privacy issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API SCANNER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ Personal Data in API Responses                                       │ │
│  │ ✓ Over-Exposure of Sensitive Fields                                    │ │
│  │ ✓ Missing Authentication/Authorization                                 │ │
│  │ ✓ Insecure Data Transmission                                           │ │
│  │ ✓ Excessive Data Return (data minimization violations)                 │ │
│  │ ✓ Missing Rate Limiting                                                 │ │
│  │ ✓ API Documentation Gaps                                               │ │
│  │ ✓ Deprecated Endpoint Usage                                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "APIs are the #1 attack vector. We test your endpoints for GDPR          │
│   compliance and security vulnerabilities before they're exploited."      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 12. DOMAIN SCANNER
**Purpose:** Analyze domain security and email configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DOMAIN SCANNER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IT DETECTS:                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ DNS Configuration Issues                                              │ │
│  │ ✓ Missing/Invalid SPF Records                                          │ │
│  │ ✓ Missing/Invalid DKIM Records                                         │ │
│  │ ✓ Missing/Invalid DMARC Records                                        │ │
│  │ ✓ SSL Certificate Expiration                                           │ │
│  │ ✓ WHOIS Privacy Issues                                                 │ │
│  │ ✓ Subdomain Enumeration                                                 │ │
│  │ ✓ Email Security Posture                                               │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CUSTOMER VALUE:                                                            │
│  "Phishing attacks cost Dutch businesses €2B annually. Proper email       │
│   authentication (SPF, DKIM, DMARC) blocks 99% of spoofing attempts."     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Unique Selling Points (Customer Attraction)

### Why DataGuardian Pro?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPETITIVE ADVANTAGES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ONLY DUTCH DEEPFAKE DETECTOR FOR EU COMPLIANCE                         │
│     "Competitors don't offer AI-generated content detection"               │
│                                                                             │
│  2. 100% GDPR + 100% EU AI ACT COVERAGE                                    │
│     "All 99 GDPR articles + all 113 EU AI Act articles"                    │
│                                                                             │
│  3. NETHERLANDS-SPECIFIC (UAVG, BSN, Dutch DPA)                            │
│     "Built for Dutch businesses, Dutch regulations, Dutch hosting"         │
│                                                                             │
│  4. 12 SCANNERS IN ONE PLATFORM                                            │
│     "Replace 5-6 separate tools with one subscription"                     │
│                                                                             │
│  5. AI-POWERED RISK ANALYSIS                                               │
│     "GPT-4 provides intelligent recommendations, not just findings"        │
│                                                                             │
│  6. ENTERPRISE-READY                                                        │
│     "SSO, role-based access, audit logs, API access"                       │
│                                                                             │
│  7. REGULATORY-READY REPORTS                                                │
│     "PDF/HTML reports ready for Dutch DPA submissions"                     │
│                                                                             │
│  8. HOSTED IN NETHERLANDS                                                   │
│     "Data never leaves EU. Full data sovereignty."                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pricing Tiers & Scanner Access

| Tier | Price | Scanners Included |
|------|-------|-------------------|
| **Starter** | €99/mo | Code, Website, Blob (3 scanners) |
| **Professional** | €299/mo | + Image, Database, DPIA (6 scanners) |
| **Business** | €599/mo | + AI Model, SOC2, API (9 scanners) |
| **Enterprise** | €999/mo | + Audio/Video, Sustainability, Domain (12 scanners) |
| **Ultimate** | €1499/mo | All 12 + Priority Support + Custom Integrations |

---

## Target Customer Segments

| Segment | Pain Point | Solution |
|---------|------------|----------|
| **SMB (50-200 employees)** | Can't afford DPO + expensive tools | All-in-one platform at €299-599/mo |
| **Healthcare** | Patient data everywhere | Image + Database + DPIA scanners |
| **Financial Services** | Audit requirements | SOC2 + Code + Database scanners |
| **Tech Companies** | AI regulations coming | AI Model + Deepfake + Code scanners |
| **E-commerce** | Website compliance | Website + Cookie + Database scanners |
| **Legal/Consulting** | Client confidentiality | Document + Email + Database scanners |

---

This document provides everything you need to understand the architecture and communicate scanner value to potential customers.

Would you like me to create a customer-facing marketing version of this document as well?
