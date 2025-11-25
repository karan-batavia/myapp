# ⚡ SAP Integration - Quick Reference

## 5 Credentials You Need

```
1. SAP Host          sap.yourcompany.com or 192.168.1.100
2. SAP Port          8000 (HTTP) or 443 (HTTPS)
3. SAP Client        100, 200, or 300
4. SAP Username      Your SAP user account
5. SAP Password      Your SAP password
```

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Get Credentials from Admin
**Email your SAP admin:**
```
Hi,

I need SAP connection details for PII scanning:
- SAP Host/Server address
- SAP Port number
- SAP Client number
- Can create dedicated user? (DATAGUARDIAN)

Thanks,
[Your Name]
```

**OR** Contact: SAP System Administrator / SAP Basis Team

---

### Step 2: Create SAP User (if needed)
In SAP (Transaction `SU01`):
- User Name: `DATAGUARDIAN`
- Password: [secure password]
- Give RFC and data access permissions
- Save and activate

---

### Step 3: Verify Connection
```bash
# From Replit Shell - test connection
telnet sap.yourcompany.com 8000
```
Should show: "Connected" or similar

---

### Step 4: Collect Credentials
```bash
python GET_SAP_CREDENTIALS.py
```
This script will:
- Ask you for all 5 credentials
- Save them to `sap_credentials.txt`
- Show next steps

---

### Step 5: Connect in DataGuardian Pro
1. Open: http://localhost:5000
2. Go to: **Scan Manager** → **Enterprise Connector** → **SAP**
3. Fill in your credentials
4. Click **"Connect to SAP"**
5. Select tables and start scanning

---

## 📊 Tables DataGuardian Scans

### HR Tables (Most PII):
- **PA0002** - Personal Data (names, birth dates, IDs)
- **PA0001** - Org Assignment
- **PA0185** - ID Numbers (passport, license)

### Master Data:
- **ADRC** - Addresses (names, phone, streets)
- **KNA1** - Customers
- **LFA1** - Vendors
- **USR21** - User accounts

### Sales:
- **VBPA** - Sales Document Partners

---

## 🇳🇱 Netherlands Compliance

DataGuardian Pro automatically checks for:

✅ **BSN** - Dutch Social Security Numbers  
✅ **UAVG** - Netherlands privacy law  
✅ **GDPR** - All 99 articles  
✅ **Encryption** - Field-level requirements  

---

## ✅ Security Tips

- Create **dedicated SAP user** (not admin account)
- Use **HTTPS** (port 443) for production
- **Limit user permissions** to required tables
- **Enable audit logging** in SAP
- **Delete credentials file** after using

---

## ❌ Troubleshooting

| Problem | Solution |
|---------|----------|
| Cannot connect | Check host/port/firewall with admin |
| Authentication fails | Verify username/password |
| No tables found | Ensure user has RFC permissions |
| SSL error | Use HTTP for testing, HTTPS for production |

---

## 📞 Who to Contact

- **Connection issues** → SAP System Administrator
- **User account** → SAP Security/Basis team
- **PII scanning** → DataGuardian Pro support

---

## 🎯 Example Configuration

**Development:**
```
Host:   sap-dev.company.nl
Port:   8000
Client: 100
User:   DATAGUARDIAN_DEV
```

**Production:**
```
Host:   sap.company.nl
Port:   443
Client: 200
User:   DATAGUARDIAN_PROD
```

---

## 📖 Full Guide

For detailed instructions, see: **SAP_SETUP_GUIDE.md**

---

**Ready? Run:** `python GET_SAP_CREDENTIALS.py` 🚀
