# ✅ SAP Free Trial - Quick Checklist

Print this and check off as you go through setup.

---

## 📝 Pre-Setup Checklist

```
☐ Browser is open (Chrome, Firefox, Safari, Edge)
☐ Internet connection working
☐ Have 15-20 minutes available
☐ Notepad ready to save credentials
☐ Email access ready (to receive trial credentials)
```

---

## 🔗 Setup Steps

### Part 1: Create Trial Account (5 minutes)

```
☐ Go to: https://www.sap.com/cdc/en/marketing/trial.html
☐ Find and click: [Start Your Trial]
☐ Select: SAP Enterprise Resource Planning (ERP) or S/4HANA
☐ Fill in account details:
   ☐ Email: ___________________________
   ☐ Password: ________________________
   ☐ First Name: ______________________
   ☐ Last Name: _______________________
   ☐ Company: _________________________
   ☐ Country: __________________________
☐ Check: "I accept the terms of service"
☐ Click: [Create Account] or [Continue]
```

### Part 2: Wait for System Provisioning (5-15 minutes)

```
☐ You see: "Your system is being provisioned..."
☐ DO NOT REFRESH - just wait!
☐ Progress bar is showing
☐ System is being created
☐ Check: 5 min, 10 min, 15 min...
```

### Part 3: Receive Credentials Email (within 30 minutes)

```
☐ Check email for: "Your SAP Cloud Trial System is Ready"
☐ Open email from SAP
☐ Find and copy:
   
   ☐ System URL:  ____________________________________
   ☐ Username:    ____________________________________
   ☐ Password:    ____________________________________
   
☐ Save this info to a notepad file
```

### Part 4: Extract Your 5 Credentials

From the email, get these 5 items:

```
1️⃣  SAP HOST
   From email URL: https://xxxxxxx.us10.hana.ondemand.com
   Extract (just the domain):  _______________________
   
2️⃣  SAP PORT
   For SAP Cloud trial, use:   443
   
3️⃣  SAP CLIENT
   For trial systems, use:     100
   
4️⃣  SAP USERNAME
   From email:                 _______________________
   
5️⃣  SAP PASSWORD (initial)
   From email:                 _______________________
```

### Part 5: First Login to SAP (5 minutes)

```
☐ Open browser: https://[YOUR-HOST-FROM-EMAIL]
  Example: https://p2500123456-us10.hana.ondemand.com
  
☐ You see SAP login screen

☐ Fill in:
   Client:   100
   Username: [from email]
   Password: [from email]
   
☐ Click: [Log In]

☐ SAP may ask to change password:
   Old Password: [from email]
   New Password: [create new]
   Confirm:      [repeat]
   ☐ Click: [Change]
   
   IMPORTANT: Remember your NEW password!

☐ You should see SAP Fiori/Start Center
```

### Part 6: Verify Connection (2 minutes)

```
☐ Open Replit Shell

☐ Run this command:
   telnet [YOUR-HOST].hana.ondemand.com 443
   
   Example:
   telnet p2500123456-us10.hana.ondemand.com 443

☐ You see: "Connected to..."
   ✅ Connection successful!
   
If error:
   ☐ Check host is correct
   ☐ Try again in 1-2 minutes
```

### Part 7: Collect Credentials in Python (3 minutes)

```
☐ Open Replit Shell

☐ Run command:
   python GET_SAP_CREDENTIALS.py

☐ When prompted, enter:
   1. SAP Host:       [your host].hana.ondemand.com
   2. SAP Port:       443
   3. SAP Client:     100
   4. SAP Username:   [from email]
   5. SAP Password:   [your NEW password - not initial]
   6. Protocol:       https
   
☐ File created: sap_credentials.txt
```

### Part 8: Connect in DataGuardian Pro (3 minutes)

```
☐ Open browser: http://localhost:5000

☐ Click: Scan Manager

☐ Click: Enterprise Connector

☐ Click: SAP

☐ Fill in form:
   SAP Host:       [your host].hana.ondemand.com
   SAP Port:       443
   SAP Client:     100
   SAP Username:   [from credentials.txt]
   SAP Password:   [from credentials.txt]

☐ Click: [Connect to SAP]

☐ Wait for connection...

☐ You see: "Connected successfully!"
   ✅ Connection successful!
   
If error:
   ☐ Double-check hostname spelling
   ☐ Try again in 1-2 minutes
   ☐ Check Replit console for errors
```

### Part 9: Scan for PII (5-10 minutes)

```
☐ You see table selection

☐ Check these tables:
   ☐ PA0002 (HR Personal Data) - Most PII
   ☐ ADRC (Addresses)
   ☐ KNA1 (Customers)
   
☐ Or select all: ☐ [Select All]

☐ Click: [Start Scan]

☐ DataGuardian Pro scans tables

☐ You see: "Scan in progress..."

☐ Wait 1-2 minutes...

☐ You see results:
   - Names found
   - Phone numbers found
   - Birth dates found
   - Addresses found
   
   ✅ Scan complete!
```

### Part 10: Review Results (5 minutes)

```
☐ You see: PII Findings

☐ Check results:
   ☐ Tables scanned
   ☐ PII instances found
   ☐ Risk level
   ☐ Compliance score

☐ Click: [Generate Report]

☐ Choose format:
   ☐ PDF report
   ☐ HTML report
   
☐ Click: [Download]

☐ Report includes:
   ☐ Compliance score
   ☐ GDPR articles
   ☐ UAVG requirements
   ☐ Recommendations
   
   ✅ Report generated!
```

---

## 🎯 Final Credentials Template

Save this:

```
═══════════════════════════════════════════════════════
SAP TRIAL - YOUR CREDENTIALS
═══════════════════════════════════════════════════════

1️⃣  SAP HOST:         _______________________________
2️⃣  SAP PORT:         443
3️⃣  SAP CLIENT:       100
4️⃣  SAP USERNAME:     _______________________________
5️⃣  SAP PASSWORD:     _______________________________

═══════════════════════════════════════════════════════

For DataGuardian Pro:
- Use Host 1
- Use Port 443
- Use Client 100
- Use Username 4
- Use Password 5

═══════════════════════════════════════════════════════
```

---

## ⏱️ Timeline

```
0-5 min:    Create SAP trial account
5-15 min:   System provisioning (wait)
15-20 min:  Receive email, extract credentials
20-25 min:  First login to SAP, change password
25-30 min:  Test connection with telnet
30-35 min:  Run Python credential collector
35-40 min:  Open DataGuardian Pro, fill credentials
40-45 min:  Select tables and start scan
45-55 min:  Wait for scan to complete
55-60 min:  Review results and generate report

TOTAL: ~60 minutes
```

---

## ✨ Success Indicators

```
✅ You get email from SAP
✅ You can login to SAP website
✅ Telnet shows "Connected"
✅ Python script saves credentials
✅ DataGuardian connects to SAP
✅ You can select tables
✅ Scan finds PII
✅ Report generates
```

---

## 🚨 Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| No email from SAP | Wait 30 min, check spam |
| Can't login to SAP | Verify password, try again |
| Telnet fails | Wait 5 min, SAP may be starting |
| DataGuardian won't connect | Check host/port, refresh page |
| No tables found | Wait 1 min, refresh page |
| Scan fails | Select fewer tables, try again |

---

## 🎉 You're Done When:

```
☐ You have 5 credentials
☐ Telnet connection works
☐ DataGuardian connects to SAP
☐ Tables are selectable
☐ PII findings are showing
☐ Report is downloaded
```

---

**Start here:** https://www.sap.com/cdc/en/marketing/trial.html

**Good luck!** 🚀
