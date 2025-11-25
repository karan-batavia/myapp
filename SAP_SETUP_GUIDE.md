# 🔗 SAP Connector Setup Guide for DataGuardian Pro

## Overview
SAP integration allows you to scan your SAP system for personally identifiable information (PII) and ensure GDPR/UAVG compliance.

---

## 📋 What You Need for SAP Connection

### 5 Required Credentials:

```
1️⃣  SAP HOST/SERVER
    Example: sap.yourcompany.com  or  192.168.1.100
    
2️⃣  SAP PORT
    Example: 8000 or 443 (HTTPS)
    Default: 8000 (HTTP) or 443 (HTTPS)
    
3️⃣  SAP CLIENT (Mandant)
    Example: 100, 200, 300
    This is the client/tenant ID in your SAP system
    
4️⃣  SAP USERNAME
    Example: DATAGUARDIAN or ADMIN
    SAP user account with RFC/API access
    
5️⃣  SAP PASSWORD
    The password for the SAP user account
```

---

## 🔐 Step 1: Find Your SAP Connection Details

### From Your SAP System Administrator:

Contact your **SAP System Administrator** and request:

```
□ SAP Host Name or IP Address
  What is the SAP application server address?
  Answer: ________________________

□ SAP Port Number
  What port is SAP running on? (Usually 8000 or 443)
  Answer: ________________________

□ SAP Client Number
  What is the client ID? (Usually 100, 200, or 300)
  Answer: ________________________

□ Optional - System ID (SID)
  What is your SAP System ID? (e.g., PRD, DEV, TST)
  Answer: ________________________
```

---

## 👤 Step 2: Create SAP User Account for DataGuardian

### Option A: Use Existing Admin User (Easiest)
If you already have SAP administrator access:
- Use your existing credentials
- Has required RFC/API permissions

### Option B: Create New Technical User (Recommended for Production)

**In your SAP System:**

1. **Logon to SAP** using admin account
2. **Go to:** Transaction Code `SU01`
3. **Click:** "Create New User"

Fill in:
```
User Name:           DATAGUARDIAN
Full Name:           DataGuardian PII Scanner
User Type:           Dialog  (or System)
Password:            [Create secure password]
Language:            EN
Assign Groups:       (see below)
```

4. **Assign Required Roles:**
   - `SAP_ALL` (simplest - all access)
   - OR specific roles (more secure):
     - `SAP_BC_UTILITY`
     - `SAP_BASIS`
     - RFC access to tables

5. **Assign Authorizations:**
   - S_TABU_DIS: Display table contents
   - S_RFC: Remote Function Call
   - S_DATASET: File/data access

6. **Click:** "Save"

7. **Activate User** (set password, logon allowed)

---

## 🔌 Step 3: Test SAP Connection

### From Your Computer (Before Using DataGuardian):

You can verify connectivity using SAP GUI or command line:

```bash
# Test port is open (replace with your SAP server)
telnet sap.yourcompany.com 8000

# Or test with curl
curl -u DATAGUARDIAN:password https://sap.yourcompany.com:443/sap/bc/rest/system/info
```

**Expected Response:** Connection accepted or HTTP 200

---

## 🛡️ Step 4: Enable Required RFC Connections

**In your SAP System:**

1. Go to: Transaction Code `SM59`
2. Find your HTTP/HTTPS connections
3. Verify `RFC Enabled` checkbox is checked
4. Test connection: Click "Test Connection" button

---

## 📊 SAP Tables DataGuardian Scans

When connected, DataGuardian Pro will scan for PII in these key tables:

### HR Module (contains most PII):
```
PA0002    HR Master Record - Personal Data
          Contains: Names, dates of birth, personnel IDs
          
PA0001    HR Master Record - Org Assignment
          
PA0185    ID Numbers (Passport, License, etc.)
          
PA0041    Date Specifications
```

### Master Data:
```
ADRC      Address Master
          Contains: Names, addresses, phone numbers
          
KNA1      Customer Master
          Contains: Customer names, tax numbers
          
LFA1      Vendor Master
          Contains: Vendor information, contacts
          
BUT000    Business Partner Master
```

### User Management:
```
USR21     User Master Records
          Contains: Usernames, employee IDs
```

### Sales:
```
VBPA      Sales Document Partner
          Contains: Names, addresses, contacts
```

---

## 🇳🇱 Netherlands-Specific Compliance

DataGuardian Pro checks for:

✅ **BSN (Burgerservicenummer)** - Dutch Social Security Numbers
   - Typically stored in: PA0185, PA0002
   - Requires encryption and access logging under UAVG

✅ **UAVG Compliance**
   - Autoriteit Persoonsgegevens (AP) reporting requirements
   - Data retention policies
   - Consent management

✅ **GDPR Articles**
   - Article 25: Privacy by Design
   - Article 28: Data Processing Agreements
   - Article 32: Security measures
   - Articles 44-49: International transfers

---

## 🚀 Step 5: Connect in DataGuardian Pro

Once you have all 5 credentials:

1. **Open DataGuardian Pro** → http://localhost:5000
2. **Go to:** Scan Manager → Enterprise Connector → SAP
3. **Fill in the form:**

```
SAP Host:           [your SAP host/IP]
SAP Port:           [e.g., 8000]
SAP Client:         [e.g., 100]
SAP Username:       [your SAP user]
SAP Password:       [your SAP password]
```

4. **Click:** "Connect to SAP"
5. **Select tables** to scan for PII
6. **Click:** "Start Scan"

---

## ✅ Security Best Practices

### 1. User Account Restrictions
- Create dedicated technical user (not admin account)
- Limit access to only required tables
- Set password expiration policy

### 2. Network Security
- Use HTTPS/SSL (port 443, not 8000)
- Enable `SAP_SSL_VERIFY` environment variable
- Restrict access by IP address if possible

### 3. Data Protection
- Don't scan production systems without approval
- Scan test/quality systems first
- Enable SAP audit logging for scanning activity
- Encrypt SAP credentials in DataGuardian Pro

### 4. Access Control
- Enable SAP Security Audit Log (transaction SM19)
- Monitor for unauthorized access attempts
- Implement segregation of duties
- Use multi-factor authentication if available

---

## 🔍 Troubleshooting

### Connection Fails
```
❌ Error: Cannot connect to SAP host

Check:
□ Hostname/IP is correct
□ Port number is correct (8000 for HTTP, 443 for HTTPS)
□ SAP server is running (ask admin)
□ Firewall allows connection
□ Network connectivity (ping/telnet works)
```

### Authentication Fails
```
❌ Error: Invalid credentials

Check:
□ Username is correct (case-sensitive in SAP)
□ Password is correct
□ User account is active
□ User has RFC/API permissions
□ User hasn't exceeded logon attempts
```

### No Tables Found
```
❌ Error: Cannot retrieve table list

Check:
□ User has S_TABU_DIS authorization
□ User has RFC permissions
□ SAP API gateway is enabled
□ Client number is correct
```

### SSL/Certificate Error
```
❌ Error: SSL certificate validation failed

Solutions:
1. Use HTTP instead of HTTPS (if testing)
2. Add SAP certificate to trusted store
3. Set SAP_SSL_VERIFY=false (testing only!)
4. Check certificate expiration date
```

---

## 📞 Need Help?

Contact your:
- **SAP System Administrator** - for host/port/client info
- **SAP Security Team** - for user account creation
- **SAP Basis Team** - for RFC/API troubleshooting
- **DataGuardian Pro Support** - for scanning/compliance questions

---

## 🎯 Example Configuration

### Development System:
```
Host:     sap-dev.company.nl
Port:     8000
Client:   100
User:     DATAGUARDIAN_DEV
Protocol: HTTP
```

### Production System:
```
Host:     sap.company.nl
Port:     443
Client:   200
User:     DATAGUARDIAN_PROD
Protocol: HTTPS
```

---

**Ready to connect? Gather your 5 credentials and start scanning! 🚀**
