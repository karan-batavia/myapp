# 🚀 Use the Credentials Script

## What This Does
The script `GET_SALESFORCE_CREDENTIALS.py` will:
1. Ask you for each credential one by one
2. Validate that you have all 5 values
3. Save them to a file you can use in DataGuardian Pro
4. Show you next steps

---

## 📋 Prerequisites - Have These Ready

Before running the script, gather these from Salesforce:

```
1. Username:        vishaal05@agensics.com.sandbox
2. Password:        [your password]
3. Consumer Key:    3MVG9d8._XXXXXXXXXXXXXXXX...
4. Consumer Secret: 987654321XXXXXXXXXXXXXXX...
5. Security Token:  AbCd1234efgh5678ijkl9012
```

---

## ▶️ RUN THE SCRIPT

### Step 1: Open Replit Shell
Click the **Shell** tab at the bottom of Replit

### Step 2: Run This Command
```bash
python GET_SALESFORCE_CREDENTIALS.py
```

### Step 3: Answer Each Question

The script will ask:

```
1️⃣  SALESFORCE USERNAME
   This should be your email with .sandbox
   Example: vishaal05@agensics.com.sandbox
   Enter your username: 
   → Type: vishaal05@agensics.com.sandbox
   → Press Enter

2️⃣  SALESFORCE PASSWORD
   Your account password
   Enter your password: 
   → Type: [your password]
   → Press Enter

3️⃣  CONSUMER KEY
   From Salesforce: Setup → Connected apps → Your app
   Starts with '3MVG9d8._' and is ~80 characters long
   Paste your Consumer Key: 
   → Paste: 3MVG9d8._XXXXXXXXXXXXXXXX...
   → Press Enter

4️⃣  CONSUMER SECRET
   From Salesforce: Click [Show] then [Copy]
   Is ~40+ alphanumeric characters
   Paste your Consumer Secret: 
   → Paste: 987654321XXXXXXXXXXXXXXXX...
   → Press Enter

5️⃣  SECURITY TOKEN
   From email sent by Salesforce after Reset Security Token
   Is 24 alphanumeric characters
   Paste your Security Token: 
   → Paste: AbCd1234efgh5678ijkl9012
   → Press Enter
```

---

## ✅ What Happens After

After you enter all 5 values, the script will:

```
VALIDATING CREDENTIALS
══════════════════════════════════════════
✓ USERNAME: Provided
✓ PASSWORD: Provided
✓ CONSUMER KEY: Provided
✓ CONSUMER SECRET: Provided
✓ SECURITY TOKEN: Provided

✓ Credentials saved to: salesforce_credentials.py

CREDENTIALS SUMMARY
══════════════════════════════════════════
Username:          vishaal05@agensics.com.sandbox
Password:          **************
Consumer Key:      3MVG9d8._XXXX...XXXXXX
Consumer Secret:   987654321XXX...XXXXX
Security Token:    AbCd1234...9012

READY FOR TESTING!
══════════════════════════════════════════
Next steps:
1. Open DataGuardian Pro at http://localhost:5000
2. Go to: Scan Manager → Enterprise Connector → Salesforce CRM
3. Fill in the form with these credentials
4. Click 'Connect to Salesforce'
5. Select objects to scan (Accounts, Contacts, Leads)
6. Run the PII scan!

✓ Script complete!
```

---

## 📁 File Created

After running the script, a new file is created:
```
salesforce_credentials.py
```

This file contains all your credentials in a Python format that can be used by DataGuardian Pro.

---

## 🎯 Now You're Ready!

With your credentials gathered, you can:

**Option A: Test in Python (Verify Connection)**
```bash
python3 << 'EOF'
from salesforce_credentials import SALESFORCE_CONFIG
from services.salesforce_connector import SalesforceConnector, SalesforceConfig

config = SalesforceConfig(**SALESFORCE_CONFIG)
connector = SalesforceConnector(config)
if connector.authenticate():
    print("✅ SUCCESS! Connected to Salesforce")
else:
    print("❌ Connection failed - check credentials")
EOF
```

**Option B: Test in DataGuardian Pro UI**
1. Open http://localhost:5000
2. Scan Manager → Enterprise Connector → Salesforce CRM
3. Fill in the 5 fields (copy from `salesforce_credentials.py`)
4. Click "Connect to Salesforce"
5. Scan for PII!

---

## 🔐 Security Notes

✅ The `salesforce_credentials.py` file is created locally
✅ It's stored in your Replit workspace (not shared)
✅ Keep it safe - contains your actual credentials
✅ If you push to GitHub, add it to `.gitignore` first!

---

## 🚀 Ready?

1. Gather your 5 credentials from Salesforce
2. Open Replit Shell
3. Run: `python GET_SALESFORCE_CREDENTIALS.py`
4. Answer the 5 questions
5. Done! Your credentials are saved and ready to use

---

**Run the script NOW!** ⚡
