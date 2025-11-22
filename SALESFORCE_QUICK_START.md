# ⚡ Salesforce Integration - Quick Start Checklist

## 📋 What You Have Ready
✅ Salesforce sandbox account (agensics.com.sandbox)
✅ User account: Vishaal Kumar
✅ DataGuardian Pro Salesforce connector module
✅ Streamlit app already running at http://localhost:5000

---

## 🚀 5-Minute Setup

### Prerequisites (Get These First)
- [ ] **Salesforce Username:** Your email + `.sandbox` (e.g., `vishaal05@agensics.com.sandbox`)
- [ ] **Salesforce Password:** Your account password
- [ ] **Consumer Key:** From Setup → Integrations → OAuth Apps (25-char code)
- [ ] **Consumer Secret:** From same location (30-char code)
- [ ] **Security Token:** From Settings → Reset Security Token (24-char, sent via email)

### Testing Steps

#### Option 1: Quick Test via Python (2 minutes)
```bash
# In Replit Shell:
python3 << 'EOF'
from services.salesforce_connector import SalesforceConnector, SalesforceConfig

config = SalesforceConfig(
    client_id="YOUR_CONSUMER_KEY_HERE",
    client_secret="YOUR_CONSUMER_SECRET_HERE",
    username="vishaal05@agensics.com.sandbox",
    password="YOUR_PASSWORD_HERE",
    security_token="YOUR_SECURITY_TOKEN_HERE",
    sandbox=True
)

connector = SalesforceConnector(config)
if connector.authenticate():
    print("✅ SUCCESS! Connected to Salesforce")
    # Get list of objects
    objects = connector.get_sobjects()
    print(f"Found {len(objects)} objects")
    for obj in objects[:5]:
        print(f"  - {obj.label} ({obj.name})")
else:
    print("❌ Connection failed - check credentials")
EOF
```

#### Option 2: Full UI Test (3 minutes)
1. Open http://localhost:5000 in browser
2. Navigate to **Scan Manager → Enterprise Connectors**
3. Click **Salesforce CRM Integration**
4. Select **Authentication Method: Username & Password**
5. Fill in your credentials
6. Click **Connect**
7. Wait for object list to load
8. See PII analysis by object

---

## ✨ What Will Happen

After connecting:
```
📊 Salesforce Data Analysis
├─ Accounts (127 PII instances)
│  ├─ Emails: 45 found
│  ├─ Phones: 50 found
│  └─ Names: 32 found
├─ Contacts (256 PII instances)
│  ├─ Emails: 98 found
│  ├─ Phones: 98 found
│  └─ Addresses: 60 found
└─ Leads (89 PII instances)
   ├─ Emails: 45 found
   └─ Phones: 44 found

🎯 Total Risk: HIGH (>100 instances)
⚠️  Compliance Issue: No encryption on Email fields
✅ Recommendation: Enable field encryption for Contact emails
```

---

## 🔧 Credential Reference

| Field | Example | Get From |
|-------|---------|----------|
| Username | `vishaal05@agensics.com.sandbox` | Your login email + `.sandbox` |
| Password | `MyPassword123!` | Your account password |
| Consumer Key | `3MVG9d8...[25 chars]` | Setup → App Manager → Your App → Copy |
| Consumer Secret | `987654321ABCDEFGHIJklmnopqr...` | Same location as Key |
| Security Token | `AbCd1234efgh5678ijkl9012` | Settings → Reset Security Token → Email |

---

## 🎯 Expected Outcomes

### ✅ If It Works:
- App says "✅ Connected!"
- Lists 20+ Salesforce objects
- Shows PII breakdown for each object
- Generates compliance report
- Allows data export

### ❌ If It Fails:
| Error | Fix |
|-------|-----|
| "Auth failed" | Verify password + security token |
| "Invalid credentials" | Check username includes `.sandbox` |
| "No objects found" | Check user has API permission |
| "Rate limit" | Wait 1 min, try again |

---

## 🧪 Test Scenarios

### Scenario 1: Connection Only (Quick Verify)
- Just test authentication
- Don't scan any data
- Time: 1 minute

### Scenario 2: Scan Standard Objects
- Connect
- Scan Accounts, Contacts, Leads
- Generate report
- Time: 3-5 minutes

### Scenario 3: Full Audit (Deep Dive)
- Connect
- Scan all queryable objects (20+)
- Check all custom fields
- Generate comprehensive report
- Time: 10-15 minutes

---

## 🎓 Troubleshooting Quick Links

**Can't find Consumer Key?** → Setup → Apps → App Manager → New/Existing App
**Need Security Token?** → Settings → My Personal Info → Reset Security Token
**Wrong environment?** → Make sure username ends with `.sandbox` for sandbox account
**Still stuck?** → See SALESFORCE_TESTING_GUIDE.md for detailed troubleshooting

---

## 🚀 Ready? Start Here:

1. **Gather credentials** (see table above) - 2 min
2. **Test connection** - Choose Option 1 or 2 above - 2 min
3. **If successful** → Run full scan and generate report - 5 min
4. **Export findings** → Share with stakeholders - 1 min

**Total Time: ~10 minutes** ⏱️

---

**Next Step:** Follow the 5-minute setup above! 🎯
