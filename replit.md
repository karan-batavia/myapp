# DataGuardian Pro - Enterprise Privacy Compliance Platform

## Overview
DataGuardian Pro is a comprehensive enterprise privacy compliance platform built with Streamlit. Its primary purpose is to detect, analyze, and report on personally identifiable information (PII) across multiple data sources. The platform offers AI-powered risk assessment, multilingual support, and extensive reporting capabilities for GDPR and UAVG compliance, specifically targeting the Netherlands market. It aims to achieve €25K MRR through both SaaS and standalone enterprise licenses, offering enterprise-grade features and Netherlands-specific compliance with transparent, competitive pricing.

## User Preferences
Preferred communication style: Simple, everyday language.
Interface preferences: Clean interface without additional assessment sections on main landing page.
Data residency requirement: Netherlands/EU only hosting for GDPR compliance.
Deployment preference: Dutch hosting providers for complete data sovereignty.
Payment system preference: iDEAL for Netherlands, full GDPR compliance, transparent policies.

## System Architecture
### Frontend Architecture
- **Framework**: Streamlit-based web application with multi-page architecture.
- **Main Entry Point**: `app.py` handles authentication, session management, and primary navigation (12,768 lines - gradual refactoring in progress).
- **Multi-Page Structure**: 7 pages in `pages/` directory (New Scan, Dashboard, Results, History, Settings, Pricing, Admin) with authentication wrapper.
- **Page Modules**: Reusable page logic in `page_modules/` (scanner.py, dashboard.py, results.py, history.py, settings.py, pricing.py, admin.py).
- **Auth Wrapper**: `page_modules/auth_wrapper.py` provides shared authentication, session initialization, and role-based access control for multi-page navigation.
- **Language Support**: Internationalization with English and Dutch translations, including automated browser language detection.
- **Authentication**: Role-based access control with 7 predefined user roles, using bcrypt for password hashing and JWT for token authentication.
- **UI Components**: Modular design with reusable components, animated language switcher, professional styling, and a 6-tab settings system, including a new billing tab with subscription management.

### API Architecture (Development)
- **REST API**: Flask-based API endpoints in `api/` directory (planned for external integrations).
- **Endpoints**: Health check, scans list/create/get, compliance status, license info (api/routes.py).
- **Webhooks**: Active webhook server in `services/webhook_server.py` for Stripe payments; additional webhook handlers in `api/webhooks.py` for Microsoft 365/Google/Exact Online.
- **Middleware**: Rate limiting, JWT authentication, CORS headers, request logging (api/middleware.py).
- **Status**: Webhook server active on port 5001; REST API blueprints planned for future integration.

### Backend Architecture
- **Language**: Python 3.11.
- **Database**: PostgreSQL 16 with connection pooling and schema management.
- **Containerization**: Docker with multi-stage builds and Docker Compose.
- **Deployment**: Support for Azure DevOps, GitHub workflows, and local deployments; also supports a hybrid deployment model with SaaS (Hetzner Cloud) and standalone enterprise packages (Docker, VM, native installation).
- **Core Scanning Services**: 13 scanners including Code, Blob, Image (OCR-based), Website, Database, DPIA, AI Model, SOC2, Sustainability, Audio/Video (Deepfake Detection), and Repository (PCI-DSS) scanners.
- **Repository Scanner** (Added Dec 2025): Banking-sector code repository scanner for PCI-DSS v4.0, GDPR, and UAVG compliance. Features hardcoded PII detection (IBAN, BSN with 11-proef validation, PAN), secrets exposure detection (API keys, tokens, passwords), PII logging violations, weak encryption detection, and secure coding validation. Generates audit-ready HTML reports with risk scoring. Security: URL validation, branch sanitization, HTML escaping for XSS prevention, read-only access, data masking, hash-only storage.
- **Audio/Video Scanner**: Enterprise deepfake detection for audio (MP3, WAV, FLAC, M4A) and video (MP4, AVI, MOV, MKV) files. Features spectral analysis, voice cloning detection, face swap detection, frame consistency analysis, metadata forensics, and EU AI Act compliance flagging. Generates comprehensive HTML reports with authenticity scores and recommendations.
- **Sustainability Scanner**: Scans code repositories (not live cloud environments) for cloud infrastructure files including Terraform (.tf), AWS CloudFormation, Azure ARM/Bicep, GCP Deployment Manager, Kubernetes YAML, and Docker files. Detects oversized instances, missing auto-scaling, and sustainability issues.
- **GDPR Data Protection Layer**: Database-persisted consent management, automatic data retention enforcement (365 days scans, 90 days analytics), PII anonymization with SHA256 hashing, user data export (GDPR Art. 20), and user data deletion (GDPR Art. 17). Privacy & GDPR tab in Settings page.
- **Risk Analysis Engine**: AI-powered Smart Risk Analyzer for severity assessment and region-specific GDPR rules (Netherlands, Germany, France, Belgium).
- **Report Generation**: Multi-format (PDF, HTML) report generation with professional styling, certificate generation, and centralized results aggregation.
- **Performance Optimization**: Redis caching layer with strict mode for production, optimized database operations, async processing, and session isolation.
- **Scalability Infrastructure** (Added Dec 2025):
  - **Startup Validator**: Hard-fails in production if critical modules (license, security) are missing (`utils/startup_validator.py`)
  - **Scanner Job Queue**: Redis-backed async job queue for scanner execution with progress tracking (`services/scanner_queue.py`)
  - **Distributed Rate Limiting**: Redis-backed rate limiting for multi-instance deployments (`utils/redis_rate_limiter.py`)
  - **Bounded File Processing**: Streaming processor for large files (>100MB) to prevent OOM (`utils/streaming_file_processor.py`)
  - **Redis Strict Mode**: Cache layer raises error in production if Redis unavailable
- **Performance Caching** (Added Dec 2025):
  - **Dashboard Metrics**: `@st.cache_data` with 60s TTL for scan metrics (`page_modules/dashboard.py`)
  - **Pricing Config**: `@lru_cache` for pricing tier data (`components/pricing_display.py`)
  - **Session State Cache**: Cached license/tier/compliance lookups with 5-min TTL (`utils/session_cache.py`)
  - **API Response Caching**: Redis-backed caching for `/api/v1/scans` (60s) and `/api/v1/compliance/status` (120s)
  - **Database Indexes**: 30+ indexes on scans, audit_log, analytics_events tables
- **Security**: Environmental variable-based configuration for credentials, rate limiting, and comprehensive exception handling.
- **GDPR Compliance**: Achieves 100% GDPR coverage (99 articles across 11 chapters) with 100% Netherlands UAVG coverage (51 articles including BSN processing, AP Guidelines 2024-2025, Telecommunicatiewet).
- **Visitor Tracking**: 100% GDPR-compliant, zero-trust visitor tracking with PII hashing, 90-day retention, and cookieless design, integrated with an admin-only analytics dashboard.
- **Payment System**: Production-ready payment system with iDEAL and SEPA support, 30-day money-back guarantee, automatic renewal, and license expiry management.
- **Fraud Detection**: AI-powered fraud detection for document scanning using ChatGPT patterns, statistical anomaly analysis, and metadata forensics, integrated with professional UI components and reporting.
- **Enterprise Connectors**: Advanced OAuth2 token refresh and API rate limiting for Microsoft 365, Google Workspace, and Exact Online APIs.
- **License System**: Fully operational license management with usage tracking and tier-based access control.
- **AI Act Calculator**: Integrated 4-step wizard for EU AI Act 2025 compliance, including risk classification and Netherlands-specific features.
- **EU AI Act Compliance**: Complete 100% coverage of all 113 EU AI Act articles with 38+ detection functions integrated in AI Model Scanner, comprehensive HTML reporting, and phased implementation timeline tracking (Feb 2025, Aug 2025, Aug 2026, Aug 2027). Maximum penalties tracked: €35M or 7% global turnover for prohibited practices.
- **DPIA Implementation**: 5-step wizard interface for GDPR Article 35 compliance.

## External Dependencies
- **Streamlit**: Web application framework.
- **PostgreSQL**: Primary database.
- **OpenAI**: AI-powered analysis.
- **Stripe**: Payment processing.
- **TextRact**: Document text extraction.
- **PyPDF2**: PDF processing.
- **ReportLab**: PDF report generation.
- **Pillow**: Image processing.
- **BeautifulSoup4**: HTML parsing.
- **Requests**: HTTP client.
- **Trafilatura**: Web content extraction.
- **TLDExtract**: Domain analysis.
- **pytesseract**: OCR functionality for image scanning.
- **opencv-python-headless**: Image processing for OCR.
- **bcrypt**: Password hashing.
- **PyJWT**: JSON Web Token authentication.
- **Redis**: Caching layer.