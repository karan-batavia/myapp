# TEKENINGEN EN FORMULES (DRAWINGS AND FORMULAS)
## Enterprise Connector Platform - Patent Tekeningen

**PAGINA 13 van 18**

---

## FIGUUR 1: SYSTEEM ARCHITECTUUR OVERZICHT

```
+-------------------------------------------------------------------------+
|              ENTERPRISE CONNECTOR PLATFORM                              |
|         Patent-Pending Multi-System PII Discovery                       |
+-------------------------------------------------------------------------+
                                    |
                                    |
     +--------------+--------------+--------------+--------------+
     |  Exact       | Microsoft   | Google       |  Other       |
     |  Online      | 365         | Workspace    |  Systems     |
     +--------------+--------------+--------------+--------------+
```

---

## FIGUUR 2: EXACT ONLINE CONNECTOR ARCHITECTURE

```
+-------------------------------------------------------------------------+
|                    EXACT ONLINE CONNECTOR MODULE                        |
|                     FIRST IN MARKET - 900,000+ Users                    |
+-------------------------------------------------------------------------+
                                    |
     +------------------+------------------+------------------+
     |   OAuth2         |   API Endpoints  |   PII Detection  |
     |   Authentication |   Integration    |   Engine         |
     +------------------+------------------+------------------+
     | - Auth Code Flow | - /hrm/Employees | - BSN Detection  |
     | - Token Exchange | - /crm/Contacts  | - KvK Numbers    |
     | - Auto Refresh   | - /salesinvoice  | - IBAN NL        |
     +------------------+------------------+------------------+
```

---

**PAGINA 14 van 18**

## FIGUUR 3: OAUTH2 TOKEN REFRESH FLOW

```
+-------------------------------------------------------------------------+
|                   ADVANCED OAUTH2 TOKEN REFRESH ENGINE                  |
+-------------------------------------------------------------------------+

STEP 1: Initial Authentication
   User → Authorization Server → Auth Code → Access Token + Refresh Token

STEP 2: Token Storage
   access_token: "eyJhbGciOiJSUzI1NiIs..."
   refresh_token: "def502000a1b2c3d4e5f..."
   expires_in: 3600 seconds
   token_expires: datetime.now() + timedelta(seconds=3600)

STEP 3: Pre-emptive Refresh (5-minute buffer)
   if (token_expires - datetime.now()).total_seconds() < 300:
       POST /oauth2/token
       Body: {
           "grant_type": "refresh_token",
           "refresh_token": "{REFRESH_TOKEN}",
           "client_id": "{CLIENT_ID}",
           "client_secret": "{CLIENT_SECRET}"
       }

STEP 4: Automatic Retry Logic
   401 Unauthorized → Refresh token + retry (max 3 attempts)
   429 Too Many Requests → Exponential backoff (1s, 2s, 4s, 8s)
   500-503 Errors → Linear backoff (5s, 10s, 15s)
```

---

## FIGUUR 4: ENTERPRISE RATE LIMITING SYSTEM

```
+-------------------------------------------------------------------------+
|              THREAD-SAFE ENTERPRISE RATE LIMITING                       |
+-------------------------------------------------------------------------+

RATE LIMITS BY CONNECTOR:

Microsoft Graph API:
   ├─ Calls per minute: 10,000
   ├─ Calls per hour: 600,000
   └─ Per-second derived: 166.67

Google Workspace API:
   ├─ Calls per minute: 1,000
   ├─ Calls per hour: 100,000
   └─ Per-second derived: 16.67

Exact Online API:
   ├─ Calls per minute: 60
   ├─ Calls per hour: 5,000
   └─ Per-second derived: 1.0

IMPLEMENTATION:
   self._rate_limit_lock = threading.Lock()
   
   with self._rate_limit_lock:
       time_since_last = current_time - self._last_api_call_time
       if time_since_last < min_interval:
           sleep_time = min_interval - time_since_last
           time.sleep(sleep_time)
       self._last_api_call_time = time.time()
```

---

**PAGINA 15 van 18**

## FIGUUR 5: NETHERLANDS SPECIALIZATION MODULE

```
+-------------------------------------------------------------------------+
|               NETHERLANDS DATA TYPE DETECTION ENGINE                    |
+-------------------------------------------------------------------------+

BSN (Burgerservicenummer) Detection:
   Pattern: \b\d{9}\b
   
   Checksum Validation (11-proef):
   checksum = (digit_0 × 9) + (digit_1 × 8) + (digit_2 × 7) +
              (digit_3 × 6) + (digit_4 × 5) + (digit_5 × 4) +
              (digit_6 × 3) + (digit_7 × 2) - (digit_8 × 1)
   
   Valid if: checksum mod 11 == 0
   
   Example: BSN 111222333
   = (1×9) + (1×8) + (1×7) + (2×6) + (2×5) + (2×4) + (3×3) + (3×2) - (3×1)
   = 9 + 8 + 7 + 12 + 10 + 8 + 9 + 6 - 3 = 66
   66 mod 11 = 0 → VALID

KvK (Kamer van Koophandel):
   Pattern: \b\d{8}\b
   Format: 8-digit Chamber of Commerce number
   Example: 12345678

Dutch Banking (IBAN):
   Pattern: NL\d{2}[A-Z]{4}\d{10}
   Example: NL91ABNA0417164300

Dutch Phone Numbers:
   Pattern: \+31\d{9}
   Example: +31612345678

UAVG Compliance:
   ├─ Data Residency: Netherlands/EU verification
   ├─ AP Authority: Autoriteit Persoonsgegevens integration
   └─ Legal Framework: UAVG + GDPR combined
```

---

**PAGINA 16 van 18**

## FIGUUR 6: MULTI-CONNECTOR ARCHITECTURE

```
+-------------------------------------------------------------------------+
|                  13 CONNECTOR TYPES - UNIFIED PLATFORM                  |
+-------------------------------------------------------------------------+

ERP & Finance:
   ├─ Exact Online (NL) ⭐ UNIQUE - First in Market
   ├─ SAP ERP
   └─ Salesforce CRM

Microsoft 365 Ecosystem:
   ├─ SharePoint Online
   ├─ OneDrive for Business
   ├─ Exchange Online
   └─ Microsoft Teams

Google Workspace Ecosystem:
   ├─ Google Drive
   ├─ Gmail
   └─ Google Docs/Sheets

Banking & Financial:
   ├─ Dutch Banking APIs (Rabobank, ING, ABN AMRO)
   └─ General SEPA/IBAN integration

CONNECTOR INTERFACE:
   class EnterpriseConnectorScanner:
       def __init__(self, connector_type, credentials):
           self.connector_type = connector_type  # 13 types supported
           self.credentials = credentials
           self._initialize_rate_limiting()
           self._setup_oauth2_refresh()
       
       def scan(self, scan_config):
           self._authenticate()
           return self._execute_scan(scan_config)
```

---

**PAGINA 17 van 18**

## FIGUUR 7: EXACT ONLINE API ENDPOINTS

```
+-------------------------------------------------------------------------+
|                  EXACT ONLINE API ENDPOINT MAPPING                      |
+-------------------------------------------------------------------------+

Base URL: https://start.exactonline.nl/api/v1

Authentication:
   GET  /api/oauth2/auth
   POST /api/oauth2/token

Division Management:
   GET /current/Me
   GET /{division}/system/Divisions

HR & Employee Data:
   GET /{division}/hrm/Employees
   Response: {
       "EmployeeID": "12345",
       "FirstName": "Jan",
       "LastName": "de Vries",
       "Email": "jan.devries@example.nl",
       "BirthDate": "1985-03-15",
       "Phone": "+31612345678",
       "Mobile": "+31687654321"
   }

CRM & Contacts:
   GET /{division}/crm/Contacts
   GET /{division}/crm/Accounts
   Response: {
       "ContactID": "guid",
       "FirstName": "Anna",
       "LastName": "Jansen",
       "Email": "anna@bedrijf.nl",
       "AccountName": "Bedrijf BV",
       "ChamberOfCommerce": "12345678"  ← KvK Number
   }

Financial Records:
   GET /{division}/read/financial/GLAccounts
   GET /{division}/salesinvoice/SalesInvoices
   Response: {
       "InvoiceID": "guid",
       "DebtorName": "Klant BV",
       "InvoiceToContactPerson": "Piet Bakker",
       "AmountDC": 1250.00,
       "VATNumber": "NL123456789B01"
   }
```

---

**PAGINA 18 van 18**

## FIGUUR 8: COMPETITIVE ADVANTAGE MATRIX

```
+-------------------------------------------------------------------------+
|                     MARKET POSITIONING ANALYSIS                         |
+-------------------------------------------------------------------------+

FEATURE COMPARISON:

                          DataGuardian | OneTrust | BigID | TrustArc
                          Pro          |          |       |
------------------------------------------------------------------------
Exact Online Connector    ✅ YES       | ❌ NO    | ❌ NO | ❌ NO
Microsoft 365 Connector   ✅ YES       | ✅ YES   | ✅ YES| ✅ YES
Google Workspace          ✅ YES       | ✅ YES   | ✅ YES| ✅ YES
Auto Token Refresh        ✅ YES       | ⚠️ BASIC | ⚠️ BASIC| ⚠️ BASIC
Enterprise Rate Limiting  ✅ 10K/min   | ⚠️ 1K/min| ⚠️ 2K/min| ⚠️ 1.5K/min
BSN Detection             ✅ YES       | ❌ NO    | ❌ NO | ❌ NO
KvK Detection             ✅ YES       | ❌ NO    | ❌ NO | ❌ NO
UAVG Compliance           ✅ YES       | ⚠️ PARTIAL| ⚠️ PARTIAL| ⚠️ PARTIAL
Thread-Safe Architecture  ✅ YES       | ⚠️ LIMITED| ⚠️ LIMITED| ⚠️ LIMITED
Pricing (monthly)         €25-€250     | €5K-€15K | €8K-€20K | €6K-€18K

COST SAVINGS: 95% reduction versus competitors

NETHERLANDS MARKET:
   ├─ Exact Online Users: 900,000+ businesses (60% SME market)
   ├─ Target Market: Dutch SMEs using Exact Online
   ├─ Competitive Moat: ONLY tool with Exact Online integration
   └─ Revenue Potential: €500K-€2M (Netherlands market alone)

UNIQUE VALUE PROPOSITION:
   "First and only privacy compliance tool with native Exact Online 
    integration, serving 900,000+ Dutch businesses that competitors 
    cannot reach."
```

---

## FIGUUR 9: PROCESSING FLOW

```
INPUT: Enterprise System Credentials
   ↓
STEP 1: Connector Type Selection (13 options)
   ↓
STEP 2: OAuth2 Authentication + Token Acquisition
   ↓
STEP 3: Rate-Limited API Calls (thread-safe queuing)
   ↓
STEP 4: PII Extraction (Netherlands-specific detection)
   ↓
STEP 5: Compliance Analysis (GDPR Article 30 register)
   ↓
OUTPUT: Multi-System PII Discovery Report
```

---

**EINDE TEKENINGEN**
