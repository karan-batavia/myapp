# DataGuardian Pro - Enterprise Privacy Compliance Platform

**The only deepfake detector built for European compliance**

DataGuardian Pro is a comprehensive enterprise privacy compliance platform designed to detect, analyze, and report on personally identifiable information (PII) across multiple data sources. With 100% GDPR coverage (99 articles), 100% Netherlands UAVG coverage (51 articles), and 100% EU AI Act coverage (113 articles), it provides organizations with enterprise-grade tools for complete data privacy compliance.

![DataGuardian Pro Logo](generated-icon.png)

## Key Features

### Compliance Coverage
- **100% GDPR Compliance**: All 99 articles across 11 chapters
- **100% UAVG Compliance**: All 51 Dutch articles including BSN processing, AP Guidelines 2024-2025
- **100% EU AI Act Compliance**: All 113 articles with phased implementation tracking (Feb 2025 - Aug 2027)
- **Maximum Penalty Tracking**: Up to €35M or 7% global turnover for prohibited AI practices

### 15 Enterprise Scanners
1. **Code Scanner**: Detects PII, credentials, and sensitive data in source code
2. **Blob/Document Scanner**: Finds PII in documents (PDFs, Word, Excel, etc.)
3. **Image OCR Scanner**: Identifies PII in images using advanced OCR
4. **Website Scanner**: Crawls websites to discover PII and compliance issues
5. **Database Scanner**: Locates PII in database systems (PostgreSQL, MySQL, SQLite)
6. **DPIA Scanner**: 5-step wizard for GDPR Article 35 Data Protection Impact Assessment
7. **AI Model Scanner**: Evaluates AI models for EU AI Act compliance with 38+ detection functions
8. **SOC2 Scanner**: Security and compliance assessment
9. **Sustainability Scanner**: Cloud infrastructure sustainability analysis
10. **Audio/Video Deepfake Scanner**: Enterprise deepfake detection for audio (MP3, WAV, FLAC, M4A) and video (MP4, AVI, MOV, MKV)
11. **Enterprise Connector Scanner**: Microsoft 365, Google Workspace, Exact Online integration
12. **Repository Scanner**: Banking-sector code repository scanner for PCI-DSS v4.0 compliance

#### Repository Sub-Scanners
- Git History Scanner
- Commit Scanner
- Branch Scanner
- Tag Scanner
- Staging/Submodule Scanner

### Security Features
- **Two-Factor Authentication (2FA)**: TOTP-based MFA with QR code setup
- **Role-Based Access Control**: 7 predefined enterprise roles
- **JWT Authentication**: Secure token-based sessions
- **Bcrypt Password Hashing**: Industry-standard password security
- **GDPR Data Protection Layer**: Consent management, data retention enforcement, PII anonymization

### Enterprise Features
- **AI-Powered Fraud Detection**: Document scanning with ChatGPT patterns, statistical anomaly analysis
- **Smart Risk Analyzer**: AI-powered severity assessment with region-specific rules
- **Multi-format Reports**: Professional PDF and HTML reports with certificate generation
- **Multilingual Support**: English and Dutch with automatic browser language detection
- **EU AI Act Calculator**: 4-step wizard for risk classification

## Pricing

| Plan | Price | Ideal For |
|------|-------|-----------|
| **Startup** | €59/month | Small teams getting started |
| **Professional** | €99/month | Growing businesses |
| **Growth** | €179/month | Scaling organizations |
| **Scale** | €499/month | Enterprise deployments |

*All plans include iDEAL and SEPA payment options, 30-day money-back guarantee*

## Technical Stack

- **Frontend**: Streamlit web application with multi-page architecture
- **Database**: PostgreSQL 16 with connection pooling
- **Caching**: Redis for high-performance caching
- **Backend**: Python 3.11 with specialized scanning services
- **Containerization**: Docker with multi-stage builds
- **CI/CD**: GitHub Actions with automated Docker Hub deployment
- **Security**: JWT authentication, bcrypt hashing, 2FA support

## Deployment

### Production Deployment (Recommended)

DataGuardian Pro uses GitHub Actions for automated deployment:

1. **Push to GitHub**: Changes trigger the CI/CD pipeline
2. **Docker Build**: Image built and pushed to Docker Hub
3. **Auto Deploy**: Container deployed to production server

```bash
# Production environment
Domain: dataguardianpro.nl
Server: 45.81.35.202
Port: 5000 (main app), 5001 (webhook server)
```

### Docker Deployment

```bash
# Pull the latest image
docker pull vishaalnoord7/myapp:latest

# Run with environment file
docker run -d --name dataguardian \
  -p 5000:5000 \
  --env-file /opt/dataguardian/.env \
  --network dataguardian-net \
  vishaalnoord7/myapp:latest
```

### Environment Variables

Create a `.env` file with:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY=sk_live_...
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
│   ├── session_cache.py
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

## Support

For enterprise support and custom deployments, contact us at support@dataguardianpro.nl

## License

Copyright © 2025 DataGuardian Pro - All rights reserved.

---

**Built for European Compliance** | **Netherlands Data Residency** | **Enterprise-Grade Security**
