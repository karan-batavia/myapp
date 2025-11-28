# DataGuardian Pro - Enterprise Privacy Compliance Platform

## Overview
DataGuardian Pro is a comprehensive enterprise privacy compliance platform built with Streamlit. Its primary purpose is to detect, analyze, and report on personally identifiable information (PII) across multiple data sources. The platform offers AI-powered risk assessment, multilingual support, and extensive reporting capabilities for GDPR and UAVG compliance, specifically targeting the Netherlands market. It aims to achieve €25K MRR through both SaaS and standalone enterprise licenses, offering significant cost savings compared to competitors while providing enterprise-grade features and Netherlands-specific compliance.

## User Preferences
Preferred communication style: Simple, everyday language.
Interface preferences: Clean interface without additional assessment sections on main landing page.
Data residency requirement: Netherlands/EU only hosting for GDPR compliance.
Deployment preference: Dutch hosting providers for complete data sovereignty.
Payment system preference: iDEAL for Netherlands, full GDPR compliance, transparent policies.

## System Architecture
### Frontend Architecture
- **Framework**: Streamlit-based web application.
- **Language Support**: Internationalization with English and Dutch translations, including automated browser language detection.
- **Authentication**: Role-based access control with 7 predefined user roles, using bcrypt for password hashing and JWT for token authentication.
- **UI Components**: Modular design with reusable components, animated language switcher, professional styling, and a 6-tab settings system, including a new billing tab with subscription management.

### Backend Architecture
- **Language**: Python 3.11.
- **Database**: PostgreSQL 16 with connection pooling and schema management.
- **Containerization**: Docker with multi-stage builds and Docker Compose.
- **Deployment**: Support for Azure DevOps, GitHub workflows, and local deployments; also supports a hybrid deployment model with SaaS (Hetzner Cloud) and standalone enterprise packages (Docker, VM, native installation).
- **Core Scanning Services**: Includes Code, Blob, Image (OCR-based), Website, Database, DPIA, AI Model, SOC2, and Sustainability scanners.
- **Risk Analysis Engine**: AI-powered Smart Risk Analyzer for severity assessment and region-specific GDPR rules (Netherlands, Germany, France, Belgium).
- **Report Generation**: Multi-format (PDF, HTML) report generation with professional styling, certificate generation, and centralized results aggregation.
- **Performance Optimization**: Redis caching layer, optimized database operations, async processing, and session isolation.
- **Security**: Environmental variable-based configuration for credentials, rate limiting, and comprehensive exception handling.
- **GDPR Compliance**: Achieves 100% GDPR coverage including Articles 25, 28, and 44-49, with specific Netherlands UAVG specialization.
- **Visitor Tracking**: 100% GDPR-compliant, zero-trust visitor tracking with PII hashing, 90-day retention, and cookieless design, integrated with an admin-only analytics dashboard.
- **Payment System**: Production-ready payment system with iDEAL and SEPA support, 30-day money-back guarantee, automatic renewal, and license expiry management.
- **Fraud Detection**: AI-powered fraud detection for document scanning using ChatGPT patterns, statistical anomaly analysis, and metadata forensics, integrated with professional UI components and reporting.
- **Enterprise Connectors**: Advanced OAuth2 token refresh and API rate limiting for Microsoft 365, Google Workspace, and Exact Online APIs.
- **License System**: Fully operational license management with usage tracking and tier-based access control.
- **AI Act Calculator**: Integrated 4-step wizard for EU AI Act 2025 compliance, including risk classification and Netherlands-specific features.
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