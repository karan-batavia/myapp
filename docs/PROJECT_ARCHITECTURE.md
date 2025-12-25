# DataGuardian Pro - Project Architecture

## High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATAGUARDIAN PRO                                  │
│                    Enterprise Privacy Compliance Platform                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Frontend Layer          │  Business Logic        │  Data Layer             │
│  (Streamlit UI)          │  (Services)            │  (PostgreSQL + Redis)   │
├──────────────────────────┼────────────────────────┼─────────────────────────┤
│  app.py                  │  12 Scanner Suite      │  PostgreSQL Database    │
│  pages/                  │  Payment Processing    │  Redis Cache            │
│  page_modules/           │  License Management    │  File Storage           │
│  components/             │  Compliance Engines    │  Session State          │
└──────────────────────────┴────────────────────────┴─────────────────────────┘
```

---

## Directory Structure

```
dataguardian-pro/
├── app.py                    # Main application entry point
├── pages/                    # Streamlit multi-page navigation
├── page_modules/             # Reusable page logic
├── components/               # UI components
├── services/                 # Core business logic & scanners
├── utils/                    # Utility functions & validators
├── api/                      # REST API endpoints
├── config/                   # Configuration files
├── database/                 # Database schemas & migrations
├── translations/             # i18n language files
├── docs/                     # Documentation
├── tests/                    # Test suites
├── docker/                   # Container configuration
├── static/                   # Static assets
└── reports/                  # Generated reports
```

---

## Module Breakdown

### 1. Frontend Layer (`pages/`, `page_modules/`, `components/`)

#### `pages/` - Streamlit Multi-Page Navigation
| File | Responsibility |
|------|----------------|
| `1_🔍_New_Scan.py` | Scanner selection and execution interface |
| `2_🏠_Dashboard.py` | Compliance metrics and overview |
| `3_📊_Results.py` | Scan results display and analysis |
| `4_📋_History.py` | Historical scan records |
| `5_⚙️_Settings.py` | User preferences and configuration |
| `6_💰_Pricing.py` | Subscription plans and billing |
| `7_👥_Admin.py` | Admin panel (user management, analytics) |

#### `page_modules/` - Reusable Page Logic
| Module | Responsibility | Interface |
|--------|----------------|-----------|
| `auth_wrapper.py` | Authentication, session management, RBAC | `require_auth()`, `check_role()` |
| `scanner.py` | Scanner orchestration logic | `run_scan()`, `get_scanner_options()` |
| `dashboard.py` | Dashboard metrics computation | `get_metrics()`, `render_charts()` |
| `results.py` | Results aggregation and display | `display_findings()`, `export_results()` |
| `history.py` | Scan history retrieval | `get_scan_history()`, `filter_scans()` |
| `settings.py` | Settings management | `save_settings()`, `load_settings()` |
| `pricing.py` | Pricing display logic | `get_plans()`, `calculate_price()` |
| `admin.py` | Admin functionality | `manage_users()`, `view_analytics()` |
| `dpia_ui.py` | DPIA wizard interface | `run_dpia_wizard()` |
| `privacy_rights.py` | Privacy rights portal | `handle_dsar()`, `manage_consent()` |

#### `components/` - Reusable UI Components
| Component | Responsibility | Interface |
|-----------|----------------|-----------|
| `auth_manager.py` | Login/logout UI | `render_login()`, `render_logout()` |
| `scanner_interface.py` | Scanner selection UI | `render_scanner_selector()` |
| `compliance_dashboard.py` | Compliance visualization | `render_compliance_gauge()` |
| `pricing_display.py` | Pricing tier cards | `render_pricing_cards()` |
| `fraud_risk_display.py` | Fraud detection results UI | `render_fraud_findings()` |
| `ai_act_calculator_ui.py` | EU AI Act calculator wizard | `render_ai_act_wizard()` |
| `license_upgrade.py` | License upgrade flow | `render_upgrade_modal()` |
| `visitor_analytics_dashboard.py` | Analytics visualization | `render_visitor_stats()` |
| `enterprise_ui.py` | Enterprise features UI | `render_enterprise_options()` |
| `navigation_manager.py` | Navigation state | `handle_navigation()` |

---

### 2. Scanner Suite (`services/`)

#### Core Scanners (12 Total)
| Scanner | File | Responsibility | Input | Output |
|---------|------|----------------|-------|--------|
| **1. Code Scanner** | `code_scanner.py` | Source code PII detection, GDPR/UAVG validation | Source files | Findings list |
| **2. Document Scanner** | `blob_scanner.py` | Document content analysis (PDF, DOCX, XLS) | Binary files | PII findings |
| **3. Image Scanner** | `image_scanner.py` | OCR-based PII extraction | Image files | Text findings |
| **4. Database Scanner** | `db_scanner.py` | Database schema/content PII detection | DB connection | Schema findings |
| **5. Website Scanner** | `website_scanner.py` | Web page content analysis | URLs | Web findings |
| **6. Audio/Video Scanner** | `audio_video_scanner.py` | Deepfake detection, media analysis | Media files | Authenticity report |
| **7. AI Model Scanner** | `ai_model_scanner.py` | EU AI Act compliance, model analysis | Model files | Compliance report |
| **8. DPIA Scanner** | `dpia_scanner.py` | Data Protection Impact Assessment | Project metadata | DPIA report |
| **9. SOC2/NIS2 Scanner** | `soc2_scanner.py` | Security compliance assessment | Infrastructure | Audit report |
| **10. Sustainability Scanner** | `cloud_resources_scanner.py` | Cloud infrastructure analysis | IaC files | Sustainability score |
| **11. Enterprise Connector** | `enterprise_connector_scanner.py` | Microsoft 365, Google, Exact Online | OAuth tokens | Integration findings |
| **12. Advanced AI Scanner** | `advanced_ai_scanner.py` | Deep AI model analysis, bias detection | Model files | Comprehensive report |

#### Scanner Interface Contract
```python
class BaseScanner:
    def scan(self, input_data: Any, options: Dict) -> ScanResult:
        """Execute scan and return findings"""
        pass
    
    def get_supported_formats(self) -> List[str]:
        """Return supported input formats"""
        pass
    
    def estimate_duration(self, input_data: Any) -> int:
        """Estimate scan duration in seconds"""
        pass

@dataclass
class ScanResult:
    scan_id: str
    findings: List[Finding]
    compliance_score: float
    metadata: Dict[str, Any]
    timestamp: datetime
```

#### Supporting Services
| Service | File | Responsibility |
|---------|------|----------------|
| `results_aggregator.py` | Combine findings from multiple scanners |
| `report_generator.py` | Generate PDF/HTML reports |
| `certificate_generator.py` | Create compliance certificates |
| `intelligent_scanner_manager.py` | Smart scanner orchestration |
| `scanner_queue.py` | Redis-backed job queue |

---

### 3. Payment & Licensing (`services/`)

| Service | File | Responsibility | Interface |
|---------|------|----------------|-----------|
| Stripe Integration | `stripe_payment.py` | Payment processing | `create_checkout()`, `handle_webhook()` |
| Webhook Handler | `stripe_webhooks.py` | Stripe event processing | `process_event()` |
| Subscription Manager | `subscription_manager.py` | Subscription lifecycle | `create()`, `cancel()`, `upgrade()` |
| License Manager | `license_manager.py` | License validation | `validate()`, `check_tier()`, `get_limits()` |
| Invoice Generator | `invoice_generator.py` | Invoice creation | `generate_invoice()` |
| Scan Limit Manager | `scan_limit_manager.py` | Usage enforcement | `check_limit()`, `increment_usage()` |

#### License Tier Interface
```python
class LicenseTier(Enum):
    STARTER = "starter"      # €500/month - 5 scanners
    PROFESSIONAL = "professional"  # €1000/month - 8 scanners
    ENTERPRISE = "enterprise"  # €2000/month - 12 scanners

def get_tier_limits(tier: LicenseTier) -> Dict:
    return {
        "max_scans_per_month": ...,
        "max_users": ...,
        "scanners_enabled": [...],
        "features": [...]
    }
```

---

### 4. Compliance Engines (`utils/`)

| Validator | File | Coverage | Articles |
|-----------|------|----------|----------|
| GDPR Validator | `complete_gdpr_99_validator.py` | 100% GDPR | 99 articles |
| UAVG Validator | `netherlands_uavg_compliance.py` | 100% UAVG | 51 articles |
| EU AI Act Validator | `eu_ai_act_compliance.py` | 100% EU AI Act | 113 articles |
| Netherlands GDPR | `netherlands_gdpr.py` | Netherlands-specific rules | Regional |

#### Compliance Interface
```python
def validate_compliance(content: str, region: str = "Netherlands") -> ComplianceResult:
    """Validate content against applicable regulations"""
    pass

@dataclass
class ComplianceResult:
    violations: List[Violation]
    coverage_percentage: float
    applicable_articles: List[str]
    recommendations: List[str]
```

---

### 5. Authentication & Security (`services/`, `utils/`)

| Module | File | Responsibility |
|--------|------|----------------|
| Auth Service | `services/auth.py` | User authentication, JWT tokens |
| Auth Hardening | `services/auth_hardening.py` | Security enhancements |
| Secure Session | `utils/secure_session_manager.py` | Session management |
| Bot Protection | `services/bot_protection.py` | Anti-bot measures |
| Enterprise Auth | `services/enterprise_auth.py` | SSO, SAML integration |
| Encryption | `services/encryption_service.py` | Data encryption |

#### Authentication Interface
```python
def authenticate(username: str, password: str) -> AuthResult:
    """Authenticate user and return JWT token"""
    pass

def authorize(token: str, required_role: str) -> bool:
    """Check if token has required role"""
    pass

class UserRole(Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
```

---

### 6. API Layer (`api/`)

| File | Responsibility | Endpoints |
|------|----------------|-----------|
| `routes.py` | REST API endpoints | `/api/v1/scans`, `/api/v1/compliance` |
| `middleware.py` | Rate limiting, auth, CORS | Request interceptors |
| `webhooks.py` | External webhook handlers | Microsoft 365, Google, Exact Online |

#### API Interface
```
GET    /api/v1/health           # Health check
GET    /api/v1/scans            # List scans
POST   /api/v1/scans            # Create scan
GET    /api/v1/scans/{id}       # Get scan details
GET    /api/v1/compliance/status # Compliance summary
GET    /api/v1/license          # License info
```

---

### 7. Data Layer (`database/`, `utils/`)

#### Database Schema
| Table | Responsibility |
|-------|----------------|
| `users` | User accounts and roles |
| `scans` | Scan records and metadata |
| `scan_results` | Detailed scan findings |
| `licenses` | License information |
| `subscriptions` | Subscription records |
| `audit_log` | Security audit trail |
| `analytics_events` | Usage analytics |
| `consent_records` | GDPR consent tracking |

#### Database Interface
```python
class DatabaseManager:
    def get_connection(self) -> Connection
    def execute_query(self, sql: str, params: tuple) -> Result
    def get_user(self, user_id: str) -> User
    def save_scan(self, scan: Scan) -> str
    def get_scan_history(self, user_id: str) -> List[Scan]
```

#### Caching Layer
| Component | Responsibility |
|-----------|----------------|
| `utils/redis_cache.py` | Redis cache operations |
| `utils/session_cache.py` | Session state caching |
| `utils/translation_performance_cache.py` | Translation caching |

---

### 8. Configuration (`config/`)

| File | Responsibility |
|------|----------------|
| `logging_config.py` | Centralized logging configuration |
| `pricing_config.py` | Pricing tiers and limits |
| `report_config.py` | Report generation settings |
| `translation_mappings.py` | i18n key mappings |

---

### 9. Internationalization (`translations/`)

| File | Language | Coverage |
|------|----------|----------|
| `en.json` | English | 100% |
| `nl.json` | Dutch (Nederlands) | 100% |

---

## Inter-Module Communication

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Pages     │────▶│ Page Modules│────▶│  Services   │
│ (UI Layer)  │     │ (Logic)     │     │ (Business)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Components  │     │   Utils     │     │  Database   │
│ (Reusable)  │     │ (Helpers)   │     │ (Postgres)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Redis     │
                    │  (Cache)    │
                    └─────────────┘
```

---

## Workflow Processes

### 1. Scan Execution Flow
```
User Request → page_modules/scanner.py → services/scanner_queue.py
    → Selected Scanner(s) → services/results_aggregator.py
    → services/report_generator.py → Database Storage → UI Display
```

### 2. Authentication Flow
```
Login Request → services/auth.py → JWT Token Generation
    → utils/secure_session_manager.py → Session Storage
    → page_modules/auth_wrapper.py → Role-Based Access
```

### 3. Payment Flow
```
Subscription → services/stripe_payment.py → Stripe API
    → Webhook → services/stripe_webhooks.py
    → services/license_manager.py → Database Update
```

---

## Production Deployment

### Running Workflows
| Workflow | Command | Port |
|----------|---------|------|
| Streamlit Server | `streamlit run app.py --server.port 5000` | 5000 |
| Redis Server | `redis-server --port 6379` | 6379 |
| Webhook Server | `python services/webhook_server.py` | 5001 |

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection |
| `STRIPE_SECRET_KEY` | Payment processing |
| `OPENAI_API_KEY` | AI-powered analysis |
| `JWT_SECRET` | Token signing |
| `DATAGUARDIAN_MASTER_KEY` | Encryption key |

---

## Scanner Coverage Summary

| Framework | Coverage | Articles | Scanners |
|-----------|----------|----------|----------|
| GDPR | 100% | 99 | Code Scanner |
| UAVG (Netherlands) | 100% | 51 | Code Scanner |
| EU AI Act 2025 | 100% | 113 | AI Model + Advanced AI Scanner |

---

*Document Version: 1.0*
*Last Updated: December 2025*
