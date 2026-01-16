# BESCHRIJVING (DESCRIPTION)
## Enterprise Connector Platform - Automated Multi-System PII Discovery

**PAGINA 1 van 8**

---

## TITEL VAN DE UITVINDING

Automated Enterprise Connector Platform for Multi-System Privacy Compliance with Exact Online Integration and Netherlands Market Specialization

---

## TECHNISCH GEBIED

Deze uitvinding betreft een geautomatiseerd enterprise connector platform voor het scannen van persoonlijke gegevens (PII) en privacy compliance verificatie over meerdere zakelijke systemen, inclusief Exact Online (Nederlands ERP systeem), Microsoft 365 (SharePoint, OneDrive, Exchange, Teams), Google Workspace (Drive, Gmail, Docs), en andere enterprise applicaties. Het systeem implementeert geavanceerde OAuth2 token refresh mechanismen, enterprise-grade rate limiting (10,000 API calls/minuut voor Microsoft Graph), thread-safe architectuur, en Nederland-specifieke gegevenstype detectie inclusief BSN (Burgerservicenummer), KvK (Kamer van Koophandel) nummers, en UAVG compliance validatie.

---

## ACHTERGROND VAN DE UITVINDING

### Stand van de Techniek

Moderne organisaties gebruiken gemiddeld 15-30 verschillende SaaS applicaties en enterprise systemen voor bedrijfsvoering. Deze systemen bevatten persoonlijke gegevens (PII) verspreid over verschillende platforms:

1. **ERP Systemen**: Werknemersgegevens, salarisadministratie, klantinformatie, factuurgegevens
2. **Cloud Productivity Suites**: Documenten, emails, communicatie, gedeelde bestanden
3. **CRM Systemen**: Klantgegevens, contactinformatie, verkoop historie
4. **HR Systemen**: Personeelsdossiers, beoordelingen, medische informatie
5. **Financiële Systemen**: Bankgegevens, betalingsinformatie, belastingdocumenten

**PAGINA 2 van 8**

GDPR Artikel 30 vereist dat organisaties een register van verwerkingsactiviteiten bijhouden, maar bestaande oplossingen hebben significante beperkingen:

### Probleem met Bestaande Oplossingen

Huidige enterprise privacy compliance tools:

a) **Ontbrekende Exact Online Integratie**: Geen enkele concurrent (OneTrust, BigID, TrustArc) biedt native Exact Online connector, ondanks 900,000+ Nederlandse zakelijke gebruikers (60% SME markt share);

b) **Handmatige Configuratie Vereist**: Extensieve setup tijd (40-80 uur) voor elke connector per systeem;

c) **Beperkte Rate Limiting**: Geen enterprise-grade rate limiting resulteert in API throttling en onderbroken scans;

d) **Token Expiratie Problemen**: Vaste token expiratie zonder automatische refresh veroorzaakt scan failures na 60 minuten;

e) **Geen Nederlandse Specialisatie**: Mist BSN detectie, KvK nummer validatie, Nederlandse banking formats (IBAN NL), en UAVG compliance;

f) **Hoge Kosten**: OneTrust enterprise connectors: EUR 5,000-15,000/maand; BigID: EUR 8,000-20,000/maand; TrustArc: EUR 6,000-18,000/maand.

Voor Nederlandse MKB bedrijven die Exact Online gebruiken (900,000+ organisaties), bestaat er **geen enkele oplossing** die geautomatiseerde PII discovery biedt binnen hun ERP systeem.

---

## SAMENVATTING VAN DE UITVINDING

### Doel van de Uitvinding

Deze uitvinding lost bovenstaande problemen op door een volledig geautomatiseerd enterprise connector platform te verstrekken dat:

**PAGINA 3 van 8**

1. **Exact Online Integration - FIRST IN MARKET**: Native Exact Online connector met OAuth2 authenticatie naar https://start.exactonline.nl/api/v1, employee/HR data scanning, financial record analysis, en customer contact discovery;

2. **Advanced OAuth2 Token Refresh**: Automatische token refresh met 5-minuut expiratie buffer, 401/429 retry logic, en credential persistence voor lange scans (4+ uur);

3. **Enterprise Rate Limiting**: Thread-safe rate limiting met per-minuut en per-uur limits:
   - Microsoft Graph: 10,000 calls/minuut, 600,000 calls/uur
   - Google Workspace: 1,000 calls/minuut, 100,000 calls/uur
   - Exact Online: 60 calls/minuut, 5,000 calls/uur

4. **Netherlands Data Type Detection**: BSN detectie met 9-cijferige patroon + checksum validatie, KvK nummer herkenning, Nederlandse adres formaten, Nederlandse telefoon nummers (+31), IBAN NL banking detectie;

5. **Multi-Connector Architecture**: 13 connector types in single platform (Microsoft 365, Exact Online, Google Workspace, Salesforce, SAP, SharePoint, OneDrive, Exchange, Teams, Gmail, Google Drive, Dutch Banking APIs);

6. **95% Cost Reduction**: EUR 25-250/maand versus EUR 5,000-15,000/maand competitor pricing.

### Hoofdkenmerken van de Uitvinding

De uitvinding omvat de volgende hoofdcomponenten:

---

## A. EXACT ONLINE CONNECTOR MODULE

De Exact Online connector module biedt **first-in-market** integratie met Nederlands #1 ERP systeem:

**PAGINA 4 van 8**

### 1. OAuth2 Authenticatie Flow

```
Stap 1 - Authorization Code Request:
GET https://start.exactonline.nl/api/oauth2/auth?
    client_id={CLIENT_ID}&
    redirect_uri={REDIRECT_URI}&
    response_type=code&
    scope=read write

Stap 2 - Token Exchange:
POST https://start.exactonline.nl/api/oauth2/token
Body: {
    "grant_type": "authorization_code",
    "code": "{AUTH_CODE}",
    "client_id": "{CLIENT_ID}",
    "client_secret": "{CLIENT_SECRET}",
    "redirect_uri": "{REDIRECT_URI}"
}

Response: {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 3600
}

Stap 3 - Division/Company Enumeration:
GET https://start.exactonline.nl/api/v1/current/Me
GET https://start.exactonline.nl/api/v1/{division}/system/Divisions
```

### 2. Employee/HR Data Scanning

```
Endpoint: /api/v1/{division}/hrm/Employees
PII Detectie:
- Employee full names (FirstName, LastName, MiddleName)
- Employee IDs (EmployeeID field)
- Email addresses (Email field)
- Dutch BSN detection in custom fields
- Birth dates (BirthDate field)
- Phone numbers (Phone, Mobile fields)
```

**PAGINA 5 van 8**

### 3. Financial Record Analysis

```
Endpoint: /api/v1/{division}/read/financial/GLAccounts
Endpoint: /api/v1/{division}/salesinvoice/SalesInvoices

PII Detectie:
- Customer names (DebtorName, InvoiceToContactPerson)
- IBAN banking details (via payment methods)
- Invoice amounts (AmountDC field)
- Dutch tax identifiers (VATNumber field)
```

### 4. Contact Discovery

```
Endpoint: /api/v1/{division}/crm/Contacts
Endpoint: /api/v1/{division}/crm/Accounts

PII Detectie:
- Contact names (FirstName, LastName)
- Email addresses (Email field)
- Phone numbers (Phone, Mobile fields)
- Company names (AccountName field)
- KvK numbers (ChamberOfCommerce field)
```

### 5. Rate Limiting - Exact Online Specific

```
Rate Limits:
- 60 API calls per minuut
- 5,000 API calls per uur
- Thread-safe implementation met threading.Lock()

Implementatie:
self._rate_limit_lock = threading.Lock()

with self._rate_limit_lock:
    time_since_last = current_time - self._last_api_call_time
    if time_since_last < 1.0:
        sleep_time = 1.0 - time_since_last
        time.sleep(sleep_time)
    self._last_api_call_time = time.time()
```

**PAGINA 6 van 8**

---

## B. MICROSOFT 365 CONNECTOR MODULE

### 1. Microsoft Graph API Integration

```
Base URL: https://graph.microsoft.com/v1.0
Beta URL: https://graph.microsoft.com/beta

Rate Limiting:
- 10,000 calls per minuut
- 600,000 calls per uur
```

### 2. Multi-Service Scanning

```
SharePoint Scanning:
GET /sites/{site-id}/lists
GET /sites/{site-id}/drive/root/children

OneDrive Scanning:
GET /users/{user-id}/drive/root/children
GET /drive/items/{item-id}/content

Exchange Online Scanning:
GET /users/{user-id}/messages
GET /users/{user-id}/mailFolders

Teams Scanning:
GET /teams/{team-id}/channels
GET /teams/{team-id}/channels/{channel-id}/messages
```

---

## C. GOOGLE WORKSPACE CONNECTOR MODULE

### 1. Google APIs Integration

```
Base URL: https://www.googleapis.com

Rate Limiting:
- 1,000 calls per minuut
- 100,000 calls per uur
```

**PAGINA 7 van 8**

### 2. Multi-Service Scanning

```
Google Drive Scanning:
GET /drive/v3/files
GET /drive/v3/files/{fileId}/export

Gmail Scanning:
GET /gmail/v1/users/{userId}/messages
GET /gmail/v1/users/{userId}/messages/{id}

Google Docs Scanning:
GET /docs/v1/documents/{documentId}
```

---

## D. ADVANCED OAUTH2 TOKEN REFRESH ENGINE

### 1. Token Expiration Buffer System

```
Token Management:
- Seed tokens from credentials (access_token, refresh_token)
- Set expiration: datetime.now() + timedelta(seconds=expires_in)
- Pre-emptive refresh: 5 minutes before expiration

if 'expires_in' in credentials:
    expires_seconds = int(credentials['expires_in'])
    self.token_expires = datetime.now() + timedelta(seconds=expires_seconds)

# Check if token needs refresh (5-minute buffer)
time_until_expiry = self.token_expires - datetime.now()
if time_until_expiry.total_seconds() < 300:  # 5 minutes
    self._refresh_token()
```

### 2. Automatic Retry Logic

```
HTTP Status Handling:
- 401 Unauthorized → Refresh token + retry (max 3 attempts)
- 429 Too Many Requests → Exponential backoff + retry
- 500-503 Server Errors → Linear backoff + retry
```

**PAGINA 8 van 8**

---

## E. NETHERLANDS SPECIALIZATION MODULE

### 1. BSN (Burgerservicenummer) Detection

```
Patroon Herkenning: \b\d{9}\b

Checksum Validatie (11-proef):
checksum = (digit_0 × 9) + (digit_1 × 8) + (digit_2 × 7) +
           (digit_3 × 6) + (digit_4 × 5) + (digit_5 × 4) +
           (digit_6 × 3) + (digit_7 × 2) - (digit_8 × 1)

BSN geldig als: checksum mod 11 == 0
```

### 2. KvK (Kamer van Koophandel) Detection

```
Patroon: \b\d{8}\b
Format: 8-cijferige nummers (Nederlands Chamber of Commerce)
```

### 3. Dutch Banking Detection

```
IBAN NL Format: NL\d{2}[A-Z]{4}\d{10}
Voorbeeld: NL91ABNA0417164300
```

### 4. UAVG Compliance

```
Data Residency: Verificatie Nederland/EU jurisdictie
AP Authority: Autoriteit Persoonsgegevens integration
Legal Framework: UAVG + GDPR combined compliance
```

---

## F. MARKET OPPORTUNITY

### Netherlands Market

1. **Exact Online**: 900,000+ Dutch businesses (60% SME market share)
2. **Microsoft 365**: 85% Fortune 500, 70% Netherlands enterprises
3. **Google Workspace**: 6M+ businesses globally

### Competitor Gap

- OneTrust: ❌ NO Exact Online connector
- BigID: ❌ NO Exact Online connector
- TrustArc: ❌ NO Exact Online connector
- **DataGuardian Pro**: ✅ ONLY tool with Exact Online

### ROI

- €500K-€2M revenue opportunity (Netherlands alone)
- 95% cost savings versus competitors
- Exact Online = mandatory for Dutch market penetration

---

**EINDE BESCHRIJVING**
