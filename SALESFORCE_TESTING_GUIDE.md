# 🧪 Salesforce Integration Testing Guide

## Overview
This guide helps you test the Salesforce CRM integration for PII detection with DataGuardian Pro. Your Salesforce account (Vishaal Kumar) is already set up and ready for testing.

---

## 📋 What You Need

From your Salesforce account (from the screenshot):

| Item | What It Is | Where to Find |
|------|-----------|---------------|
| **Salesforce Username** | Your login email | `vishaal05@agensics.com.sandbox` (for sandbox) or your production username |
| **Consumer Key** | OAuth2 Client ID | Setup → Integrations → OAuth Connected Apps |
| **Consumer Secret** | OAuth2 Client Secret | Same location as Consumer Key |
| **Salesforce Password** | Your Salesforce password | Your account password |
| **Security Token** | 24-character token | Settings → My Personal Info → Reset Security Token |

---

## 🔑 Step 1: Get Your Security Token

The Security Token is required to authenticate. Here's how:

### In Your Salesforce Account:
1. Click your **profile icon** (top right)
2. Click **Settings**
3. Search for **"Reset Security Token"** in left menu
4. Click **Reset Security Token**
5. **Check your email** - Salesforce sends the new token
6. **Copy the token** (24-character code)
7. **Save it somewhere safe**

**Example token format:** `AbCd1234efgh5678ijkl9012`

---

## 🔐 Step 2: Get OAuth Credentials (Consumer Key & Secret)

### In Your Salesforce Account:
1. Go to **Setup** → **Apps → App Manager**
2. Click **New Connected App**
3. Fill in:
   - **Connected App Name:** `DataGuardian Pro`
   - **API Name:** `DataGuardian_Pro`
   - Check ✓ **Enable OAuth Settings**
4. Set **Callback URL:** `https://localhost:3000/auth/callback` (for testing)
5. Under **Selected OAuth Scopes**, add:
   - `api`
   - `web`
   - `full`
6. Click **Save**
7. When created, click it and find:
   - **Consumer Key** - Copy this
   - **Consumer Secret** - Click "Show" and copy

---

## 📝 Step 3: Prepare Your Test Credentials

Gather these values from the steps above:

```
Salesforce Username: [your username - likely a sandbox account like vishaal05@agensics.com.sandbox]
Salesforce Password: [your Salesforce password]
Consumer Key:        [Get from OAuth section]
Consumer Secret:     [Get from OAuth section]
Security Token:      [Get from Security Token reset email]
```

---

## 🚀 Step 4: Test in DataGuardian Pro

### Option A: Via UI (Recommended for First Test)

1. **Open DataGuardian Pro** → `http://localhost:5000`
2. Navigate to **Scan Manager → Enterprise Connectors**
3. Click **Salesforce CRM Integration**
4. Select **Authentication Method:** Username & Password
5. Fill in the form:
   - **Salesforce Username:** `vishaal05@agensics.com.sandbox`
   - **Salesforce Password:** [your password]
   - **Consumer Key:** [from Step 2]
   - **Consumer Secret:** [from Step 2]
   - **Security Token:** [from Step 1]
6. Click **Connect to Salesforce**
7. If successful → **✅ Connected!**

### Option B: Via Python Shell (For Advanced Testing)

Open Replit Shell and run:

```bash
python3 << 'EOF'
from services.salesforce_connector import SalesforceConnector, SalesforceConfig

# Configure with your credentials
config = SalesforceConfig(
    client_id="YOUR_CONSUMER_KEY",
    client_secret="YOUR_CONSUMER_SECRET",
    username="vishaal05@agensics.com.sandbox",
    password="YOUR_PASSWORD",
    security_token="YOUR_SECURITY_TOKEN",
    sandbox=True  # Set to True for sandbox account
)

# Create connector and test authentication
connector = SalesforceConnector(config)
if connector.authenticate():
    print("✅ Authentication successful!")
    print(f"Instance URL: {connector.instance_url}")
else:
    print("❌ Authentication failed")
EOF
```

---

## 📊 Step 5: Scan Salesforce Data

Once connected, the system will:

1. **List all Salesforce objects** (Accounts, Contacts, Leads, etc.)
2. **Identify PII-sensitive fields** in each object:
   - Email addresses → HIGH PII
   - Phone numbers → HIGH PII
   - Names → MEDIUM PII
   - Addresses → HIGH PII
   - Social Security Numbers → HIGH PII
3. **Scan sample records** (first 100 by default)
4. **Generate findings** with:
   - Field name where PII was found
   - PII type (Email, Phone, Name, etc.)
   - Severity level (HIGH, MEDIUM, LOW)
   - Record ID
   - Masked sample value
5. **Create compliance report** showing:
   - Total PII instances found
   - Risk breakdown by object
   - GDPR compliance recommendations
   - Remediation steps

---

## 🧮 What Gets Scanned

### Standard Salesforce Objects Checked:
- ✅ **Accounts** - Company information, email, phone
- ✅ **Contacts** - Names, email, phone, mailing address
- ✅ **Leads** - Prospect info, email, phone
- ✅ **Opportunities** - Deal info (usually low PII)
- ✅ **Custom Objects** - Your private fields
- ✅ **Cases** - Support tickets (may contain PII)
- ✅ **Users** - Internal staff information

### What the Scanner Looks For:
✅ Email addresses (`*@*.com`)
✅ Phone numbers (10+ digits)
✅ Personal names (alphabetic words)
✅ Addresses (street, city, zip, postal codes)
✅ Social Security numbers (XXX-XX-XXXX format)
✅ Dates of birth
✅ Passport numbers
✅ Encrypted fields (flagged as HIGH risk)

---

## ✅ Expected Test Results

### Successful Connection Indicators:
- ✅ Authentication successful message
- ✅ System lists 20-50+ Salesforce objects
- ✅ Fields are categorized by PII risk level
- ✅ Sample records are retrieved
- ✅ PII findings are displayed

### Example Output:
```
Salesforce Connection: ✅ Connected
Sandbox Mode: ON
Instance URL: https://agensics-dev-ed.my.salesforce.com

Objects Found: 45
├─ Accounts (HIGH PII potential)
│  ├─ BillingEmail (HIGH)
│  ├─ Phone (HIGH)
│  └─ Name (MEDIUM)
├─ Contacts (HIGH PII potential)
│  ├─ Email (HIGH)
│  ├─ Phone (HIGH)
│  └─ MailingAddress (HIGH)
└─ Leads (MEDIUM PII potential)

PII Findings:
- 127 email addresses detected
- 43 phone numbers detected
- 156 personal names detected
- 38 physical addresses detected

Total PII Instances: 364
Risk Level: HIGH (>100 instances)
```

---

## 🔧 Troubleshooting

### Error: "Authentication failed"
**Cause:** Wrong credentials
**Solution:**
- ✓ Verify username includes `.sandbox` for sandbox accounts
- ✓ Verify password is correct (try logging in to Salesforce web UI first)
- ✓ Check Security Token hasn't expired (reset it again if needed)
- ✓ Verify Consumer Key/Secret are correct (copy from OAuth section)

### Error: "Connection refused"
**Cause:** Network or Salesforce API issue
**Solution:**
- ✓ Check internet connection
- ✓ Verify Salesforce status: https://status.salesforce.com
- ✓ Try reconnecting after 5 minutes

### Error: "No objects returned"
**Cause:** User permissions issue
**Solution:**
- ✓ In Salesforce, go to **Setup → Users → [Your User]**
- ✓ Check that your profile has **API Enabled** permission
- ✓ Verify you have Read access to objects you want to scan

### Error: "Rate limit exceeded"
**Cause:** Too many API calls
**Solution:**
- ✓ Wait 1 minute before retrying
- ✓ The connector automatically limits to 100 records per object
- ✓ Salesforce has built-in rate limiting (~15 min per 24 hrs)

---

## 📊 Netherlands Compliance Features

Once connected, DataGuardian Pro will:

✅ **Detect BSN patterns** (Dutch personal ID numbers)
✅ **Apply UAVG compliance rules** (Netherlands privacy law)
✅ **Calculate compliance penalties** under Dutch law
✅ **Generate GDPR report** with Dutch-specific recommendations
✅ **Recommend remediation** for Dutch privacy violations

---

## 📈 Using Test Data (Optional)

### To Test with Sample Data:
1. In your Salesforce sandbox, create test data:
   - 2-3 sample Accounts with email/phone
   - 5-10 sample Contacts with various fields
   - 3-5 sample Leads

2. The scanner will detect:
   - All email addresses
   - All phone numbers
   - Names
   - Addresses
   - Custom fields you've marked as PII

---

## 🎯 Next Steps After Testing

### If Connection Works:
1. **Document findings** in compliance report
2. **Review PII risk** by object type
3. **Export report** as PDF
4. **Share with stakeholders**
5. **Create remediation plan** (next slide)

### If Issues Occur:
1. **Check credentials again** (Step 1-3)
2. **Verify sandbox vs. production** (sandbox = test account)
3. **Try demo mode** first (no credentials needed)
4. **Contact Salesforce support** if API is down

---

## 💾 Saving Your Test Configuration

Once your credentials work, you can save them in DataGuardian Pro:

1. Check "**Save Configuration**" in the UI
2. Your credentials are encrypted and stored
3. Next time, just click "**Salesforce CRM Integration**" to reconnect
4. No need to re-enter credentials each time

---

## 🔐 Security Notes

✅ All credentials are encrypted in DataGuardian Pro
✅ Security Token can be reset anytime if compromised
✅ Test in sandbox first (not production data)
✅ Consumer Secret should never be shared
✅ Revoke OAuth apps in Salesforce if you stop using them

---

## 📞 Support

If you encounter issues:

1. **Check this guide** for troubleshooting steps
2. **Verify Salesforce status** at https://status.salesforce.com
3. **Test login** directly in Salesforce to verify credentials
4. **Check API limits** in Salesforce Setup → System Overview

---

## 🎉 You're Ready to Test!

1. Follow Steps 1-2 to gather credentials
2. Follow Step 4 to connect in DataGuardian Pro
3. Let the scanner run and analyze your Salesforce data
4. Review the compliance findings
5. Generate and export your report

**Happy scanning! 🚀**
