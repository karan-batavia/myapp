# 🎯 Salesforce Testing - Step by Step in UI

## Starting Point: DataGuardian Pro Running
Make sure the app is running at: `http://localhost:5000`

---

## 🗺️ Navigation Path to Salesforce

### Step 1: Open Scan Manager
```
Home Page
   ↓
Click "Scan Manager" (left sidebar)
   ↓
See list of scanners
```

### Step 2: Select Enterprise Connector
```
Scan Manager
   ↓
Click "🏢 Enterprise Connector"
   ↓
Opens Enterprise Connector Scanner interface
```

### Step 3: Find Salesforce Tab
Once in Enterprise Connector, you'll see 4 tabs at the top:
```
┌──────────────────────────────────────────┐
│ 📱 Microsoft 365  │ 📊 Exact Online  │ 🔗 Google Workspace  │ 💼 Salesforce CRM │
└──────────────────────────────────────────┘
```

Click the **💼 Salesforce CRM** tab

---

## 📝 Salesforce Integration Form

After clicking Salesforce tab, you'll see this form:

```
Salesforce CRM Integration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scan Salesforce Accounts, Contacts, and Leads for PII 
with Netherlands BSN/KvK specialization.

[ ℹ️ Enterprise Revenue Driver ]
Salesforce integration enables €5K-10K enterprise deals vs €250 SME pricing. 
Critical for €25K MRR achievement.

Authentication Setup
────────────────────

Salesforce Authentication Method:

  ◉ Username & Password  (selected)
  ○ Access Token
  ○ Demo Mode

Salesforce Username
┌─────────────────────────────────────┐
│ [Text field: Enter your username]    │
└─────────────────────────────────────┘

Consumer Key
┌─────────────────────────────────────┐
│ [Text field: Enter Consumer Key]     │
└─────────────────────────────────────┘

Salesforce Password
┌─────────────────────────────────────┐
│ [Password field - hidden]     [👁]   │
└─────────────────────────────────────┘

Consumer Secret
┌─────────────────────────────────────┐
│ [Password field - hidden]     [👁]   │
└─────────────────────────────────────┘

Security Token
┌─────────────────────────────────────┐
│ [Password field - hidden]     [👁]   │
└─────────────────────────────────────┘

[Connect to Salesforce] [Cancel]
```

---

## ✍️ Filling Out the Form

### Field 1: Salesforce Username
**What to enter:** Your Salesforce email + `.sandbox`

Example:
- Your email: `vishaal05@agensics.com`
- Sandbox domain: `.sandbox`
- **Enter:** `vishaal05@agensics.com.sandbox`

### Field 2: Consumer Key (OAuth Client ID)
**Where to get it:**
1. In Salesforce → Setup
2. Go to "Apps" → "App Manager"
3. Find your app (or create new)
4. Click on it
5. Under "API (Enable OAuth Settings)" section
6. Copy the "Consumer Key" value
7. Paste into form

**Example:** `3MVG9d8...[24-char code]`

### Field 3: Salesforce Password
**What to enter:** Your Salesforce account password (same one you use to log in)

**Example:** `MyPassword123!`

### Field 4: Consumer Secret
**Where to get it:**
1. Same location as Consumer Key
2. Click "Show" button
3. Copy the "Consumer Secret" value
4. Paste into form

**Example:** `987654321ABCDEFGHIJK[30-char code]`

### Field 5: Security Token
**Where to get it:**
1. In Salesforce, click your profile icon (top right)
2. Click "Settings"
3. Search for "Reset Security Token"
4. Click button
5. Check your email
6. Copy the 24-character token
7. Paste into form

**Example:** `AbCd1234efgh5678ijkl9012`

---

## 🎬 Completed Form Example

```
Salesforce Username:  vishaal05@agensics.com.sandbox
Consumer Key:         3MVG9d8...(your key)
Salesforce Password:  ••••••••
Consumer Secret:      987654321...(your secret)
Security Token:       AbCd1234efgh5678ijkl9012
```

---

## ✅ Click "Connect to Salesforce"

**Result 1 - If Successful:**
```
✅ Successfully connected to Salesforce!

Instance URL: https://agensics-dev-ed.my.salesforce.com
API Version: v58.0

🔍 Scanning Salesforce Objects...

Available Objects (45 total):
├─ Accounts (220 records)
├─ Contacts (1,240 records)
├─ Leads (354 records)
├─ Opportunities (89 records)
├─ Cases (156 records)
└─ [+40 more custom objects]

Select objects to scan: [Accounts] [Contacts] [Leads]

[Start PII Scan] [Export Configuration]
```

**Result 2 - If Failed:**
```
❌ Salesforce authentication failed

Error: "Invalid credentials provided"

Troubleshooting:
• Make sure username includes ".sandbox" for sandbox accounts
• Verify Consumer Key and Secret are correct (not expired)
• Check Security Token (reset if >90 days old)
• Verify Salesforce instance is running
```

---

## 🔍 Running the Scan

### Step 1: Select Objects
After successful connection, select which objects to scan:
```
Select Objects to Scan:
☑ Accounts      (220 records)
☑ Contacts    (1,240 records)
☑ Leads         (354 records)
☐ Opportunities (89 records)
☐ Cases         (156 records)
☐ Custom_Objects (45 records)

[ Select All ]  [ Clear All ]
```

### Step 2: Choose Scan Depth
```
Scan Depth:
• Quick Scan (first 50 records per object) - 2 min
◉ Standard (first 100 records per object) - 5 min
• Deep Scan (first 500 records per object) - 15 min
• Full Audit (all records, use with caution) - 30+ min
```

### Step 3: Start Scan
Click **[Start PII Scan]** button

---

## 📊 Viewing Results

### During Scan
```
🔄 Scanning Salesforce Data...

Progress: ████████░░ 80%

Objects scanned: 3/3
Records analyzed: 1,814
PII instances found: 347

Current: Analyzing Leads (89/89 records)...
```

### After Scan Completes
```
✅ Scan Complete!

📈 PII Analysis Summary
━━━━━━━━━━━━━━━━━━━━━━━

Total Objects Scanned: 3
Total Records Analyzed: 1,814
Total PII Instances: 347

Risk Breakdown:
├─ CRITICAL: 12 instances (email fields unencrypted)
├─ HIGH: 156 instances (phone, address, name)
├─ MEDIUM: 156 instances (company, title)
└─ LOW: 23 instances (public fields)

🔐 Objects by Risk Level:

1. Contacts (CRITICAL RISK)
   - 89 email fields with no encryption
   - 98 phone numbers exposed
   - 60 physical addresses
   - Recommendation: Enable field encryption

2. Accounts (HIGH RISK)
   - 45 emails detected
   - 50 phone numbers
   - 32 company names
   - Recommendation: Restrict access via profiles

3. Leads (MEDIUM RISK)
   - 45 emails detected
   - 44 phone numbers
   - Recommendation: Archive inactive leads

📋 Detailed Findings:
┌─────────────────────────────────────┐
│ Object: Contacts                    │
│ Field: Email                        │
│ Type: High PII                      │
│ Count: 89                           │
│ Sample: vi****@agensics.com         │
│ Severity: CRITICAL                  │
│ Recommendation: Enable encryption   │
│                                     │
│ [ Expand for details ]              │
└─────────────────────────────────────┘

[Download Report] [Export to PDF] [Share]
```

---

## 📥 Download Report

Click **[Download Report]** to get:

```
📄 Salesforce_CRM_PII_Scan_Report.pdf

Contents:
✓ Executive Summary
✓ Risk Assessment Dashboard
✓ Object-by-Object Analysis
✓ Detailed Findings (all 347 instances)
✓ GDPR Compliance Check
✓ Netherlands UAVG Compliance
✓ Remediation Recommendations
✓ Next Steps & Timeline
```

---

## 🎯 Common Test Scenarios

### Scenario A: Quick Connection Test (5 minutes)
```
1. Fill in credentials
2. Click "Connect to Salesforce"
3. Wait for objects list
4. If you see ✅ Connected → Success!
5. Close (don't need to scan)
```

### Scenario B: Accounts + Contacts Scan (10 minutes)
```
1. Fill in credentials
2. Click "Connect to Salesforce"
3. Select "Accounts" and "Contacts" only
4. Choose "Standard" scan depth
5. Click "Start PII Scan"
6. Wait for results
7. Review findings
8. Download report
```

### Scenario C: Full Audit (30+ minutes)
```
1. Fill in credentials
2. Click "Connect to Salesforce"
3. Click "Select All" objects
4. Choose "Full Audit" depth
5. Click "Start PII Scan"
6. Let it run (make tea ☕)
7. Review comprehensive report
8. Share findings with team
```

---

## ✨ What You Can Do Next

After successful scan:

✅ **Download Report** → Share with compliance team
✅ **Export Findings** → Send to Salesforce admins
✅ **Schedule Recurring** → Monthly scans for monitoring
✅ **Create Remediation** → Fix high-risk fields
✅ **Update Policies** → Based on findings
✅ **Train Team** → About PII handling

---

## 🔧 Troubleshooting Quick Reference

| Issue | Fix |
|-------|-----|
| Form won't accept input | Check username format includes `.sandbox` |
| "Authentication failed" | Verify all 5 fields are correct, reset Security Token |
| "No objects found" | User needs API permission in Salesforce |
| Scan times out | Try Standard depth (not Full Audit) |
| Can't see Salesforce tab | Refresh page or restart Streamlit server |

---

## 💡 Tips for Better Results

✅ **Test in sandbox first** (not production) - You already have this!
✅ **Start with Quick Scan** - Easier to troubleshoot
✅ **Have all 5 credentials ready** - Before starting
✅ **Use Standard depth** - Balance between speed and coverage
✅ **Review findings carefully** - Some might be false positives
✅ **Save the report** - Useful for compliance documentation

---

## 🚀 Ready to Test?

**Start with the form at the top of this guide and follow these steps:**

1. ✍️ **Gather Credentials** (see separate guide)
2. 🔗 **Navigate to Salesforce Tab**
3. 📝 **Fill out the form** (5 fields)
4. 🟢 **Click Connect** and wait
5. ✅ **Select objects and scan**
6. 📊 **Review and download report**

**Estimated Total Time: 10-15 minutes**

---

Good luck! You've got this! 🚀
