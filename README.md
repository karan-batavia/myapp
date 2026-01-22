# DataGuardian Pro - Enterprise Privacy Compliance Platform

**The only deepfake detector built for European compliance**

DataGuardian Pro is a comprehensive enterprise privacy compliance platform designed to detect, analyze, and report on personally identifiable information (PII) across multiple data sources. With 100% GDPR coverage (99 articles across 11 chapters), 100% Netherlands UAVG coverage (51 articles including BSN processing and AP Guidelines 2024-2025), and 100% EU AI Act coverage (113 articles), it provides organizations with enterprise-grade tools for complete data privacy compliance.

![DataGuardian Pro Logo](generated-icon.png)

## Key Features

### Compliance Coverage
- **100% GDPR Compliance**: All 99 articles across 11 chapters
- **100% UAVG Compliance**: All 51 Dutch articles including BSN processing, AP Guidelines 2024-2025, Telecommunicatiewet
- **100% EU AI Act Compliance**: All 113 articles with 38+ detection functions and phased implementation tracking (Feb 2025 - Aug 2027)
- **Maximum Penalty Tracking**: Up to €35M or 7% global turnover for prohibited AI practices

### 17 Enterprise Scanners

#### 12 Core Scanners
1. **Code Scanner**: Detects PII, credentials, and sensitive data in source code
2. **Blob/Document Scanner**: Finds PII in documents (PDFs, Word, Excel, etc.)
3. **Image OCR Scanner**: Identifies PII in images using advanced OCR with pytesseract
4. **Website Scanner**: Crawls websites to discover PII and compliance issues
5. **Database Scanner**: Locates PII in database systems (PostgreSQL, MySQL, SQLite)
6. **DPIA Scanner**: 5-step wizard for GDPR Article 35 Data Protection Impact Assessment
7. **AI Model Scanner**: Evaluates AI models for EU AI Act compliance with 38+ detection functions
8. **SOC2 Scanner**: Security and compliance assessment
9. **Sustainability Scanner**: Cloud infrastructure sustainability analysis for Terraform, CloudFormation, Azure ARM/Bicep, Kubernetes, Docker files
10. **Audio/Video Deepfake Scanner**: Enterprise deepfake detection with spectral analysis, voice cloning detection, face swap detection, and EU AI Act compliance flagging
11. **Enterprise Connector Scanner**: Microsoft 365, Google Workspace, and Exact Online integration with OAuth2 token refresh
12. **Repository Scanner**: Banking-sector code repository scanner for PCI-DSS v4.0, GDPR, and UAVG compliance

#### 5 Repository Sub-Scanners
13. **Git History Scanner**: Analyzes git history for exposed secrets
14. **Commit Scanner**: Scans individual commits for PII violations
15. **Branch Scanner**: Branch-level security analysis
16. **Tag Scanner**: Release tag compliance verification
17. **Staging/Submodule Scanner**: Submodule and staging area analysis

### Security Features
- **Two-Factor Authentication (2FA)**: TOTP-based MFA with QR code setup
- **Role-Based Access Control**: 7 predefined enterprise roles
- **JWT Authentication**: Secure token-based sessions
- **Bcrypt Password Hashing**: Industry-standard password security
- **GDPR Data Protection Layer**: Database-persisted consent management, automatic data retention enforcement (365 days scans, 90 days analytics), PII anonymization with SHA256 hashing
- **User Data Rights**: GDPR Art. 20 data export and Art. 17 data deletion

### Enterprise Features
- **AI-Powered Fraud Detection**: Document scanning with ChatGPT patterns, statistical anomaly analysis, and metadata forensics
- **Smart Risk Analyzer**: AI-powered severity assessment with region-specific GDPR rules (Netherlands, Germany, France, Belgium)
- **Multi-format Reports**: Professional PDF and HTML reports with certificate generation
- **Multilingual Support**: English and Dutch with automatic browser language detection
- **EU AI Act Calculator**: 4-step wizard for risk classification with Netherlands-specific features
- **Visitor Analytics**: 100% GDPR-compliant, zero-trust visitor tracking with PII hashing, 90-day retention, and cookieless design

### Scalability Infrastructure
- **Scanner Job Queue**: Redis-backed async job queue for scanner execution with progress tracking
- **Distributed Rate Limiting**: Redis-backed rate limiting for multi-instance deployments
- **Bounded File Processing**: Streaming processor for large files (>100MB) to prevent OOM
- **Performance Caching**: Dashboard metrics caching (60s TTL), pricing config caching, session state cache (5-min TTL)
- **Database Optimization**: 30+ indexes on scans, audit_log, and analytics_events tables

## Pricing

| Plan | Price | Ideal For |
|------|-------|-----------|
| **Startup** | €59/month | Small teams getting started |
| **Professional** | €99/month | Growing businesses |
| **Growth** | €179/month | Scaling organizations |
| **Scale** | €499/month | Enterprise deployments |

- iDEAL and SEPA payment options
- 30-day money-back guarantee
- Automatic renewal with license expiry management

## Technical Stack

- **Frontend**: Streamlit web application with multi-page architecture (7 pages)
- **Database**: PostgreSQL 16 with connection pooling and schema management
- **Caching**: Redis with strict mode for production
- **Backend**: Python 3.11 with specialized scanning services
- **AI Integration**: OpenAI for AI-powered analysis
- **Payments**: Stripe with iDEAL and SEPA support
- **Containerization**: Docker with multi-stage builds
- **CI/CD**: GitHub Actions with automated deployment
- **Security**: JWT authentication, bcrypt hashing, 2FA support, rate limiting

## Deployment Options

### Docker Deployment

```bash
# Pull the latest image
docker pull vishaalnoord7/myapp:latest

# Run with environment file
docker run -d --name dataguardian \
  -p 5000:5000 \
  --env-file .env \
  --network dataguardian-net \
  vishaalnoord7/myapp:latest
```

### Standalone Enterprise Packages
- Docker deployment
- VM installation
- Native installation

### SaaS Deployment
- Hosted on Hetzner Cloud (Netherlands/EU)
- Complete data sovereignty

### Environment Variables

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
JWT_SECRET=your-jwt-secret
DATAGUARDIAN_MASTER_KEY=your-master-key
OPENAI_API_KEY=sk-...
```

## Architecture

```
dataguardian-pro/
├── app.py                 # Main application entry point
├── pages/                 # Multi-page Streamlit pages
│   ├── 1_New_Scan.py
│   ├── 2_Dashboard.py
│   ├── 3_Results.py
│   ├── 4_History.py
│   ├── 5_Settings.py
│   ├── 6_Pricing.py
│   └── 7_Admin.py
├── page_modules/          # Reusable page logic
├── services/              # Scanner implementations
│   ├── scanner_code.py
│   ├── scanner_blob.py
│   ├── scanner_image.py
│   ├── scanner_website.py
│   ├── scanner_database.py
│   ├── scanner_ai_model.py
│   ├── scanner_dpia.py
│   ├── scanner_soc2.py
│   ├── scanner_sustainability.py
│   ├── scanner_deepfake.py
│   ├── scanner_enterprise.py
│   ├── scanner_repository.py
│   ├── auth.py
│   └── webhook_server.py
├── utils/                 # Utility functions
│   ├── db_cache.py
│   ├── redis_cache.py
│   ├── redis_rate_limiter.py
│   ├── session_cache.py
│   ├── startup_validator.py
│   └── streaming_file_processor.py
├── api/                   # REST API endpoints
├── translations/          # i18n files (EN, NL)
├── components/            # Reusable UI components
└── database/              # Schema and migrations
```

## Data Residency

DataGuardian Pro is hosted exclusively in the Netherlands/EU for complete GDPR compliance:

- **Primary Hosting**: Netherlands (Hetzner Cloud)
- **Data Processing**: EU-only
- **No US Data Transfer**: Complete data sovereignty

## External Dependencies

- Streamlit, PostgreSQL, Redis, OpenAI, Stripe
- PyPDF2, ReportLab, Pillow, BeautifulSoup4
- pytesseract, opencv-python-headless
- bcrypt, PyJWT, pyotp, qrcode
- Trafilatura, TLDExtract, python-docx, openpyxl

## License

Copyright © 2025 DataGuardian Pro - All rights reserved.

---

**Built for European Compliance** | **Netherlands Data Residency** | **Enterprise-Grade Security**
