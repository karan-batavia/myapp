# 🔰 SAP Credentials - Complete Beginner's Guide

If you've never used SAP before, this guide explains each credential in simple terms.

---

## 📌 Important First Question

**Do you have a SAP system in your company?**

- **YES** → Follow "I Have Access to SAP" section
- **NO** → Follow "I Don't Have SAP" section
- **MAYBE** → Follow "How to Find Out" section

---

## ❓ How to Find Out if Your Company Has SAP

### Ask Your Manager or IT Department

Send an email:
```
Subject: Does our company use SAP?

Hi,

Do we have SAP (Enterprise Resource Planning system) 
in our company?

If yes, who is the SAP administrator?

Thanks!
```

### Look for These Signs:

**In your company's systems:**
- Do you see "SAP" in any software you use?
- Is there an "SAP Portal" or "SAP Start Center"?
- Do finance/HR people use SAP?

**In your IT documentation:**
- Search your company's wiki/knowledge base for "SAP"
- Ask IT: "What ERP system do we use?"

**Common in these industries:**
- Manufacturing
- Logistics
- Finance/Banking
- Large enterprises (100+ employees)
- Government agencies

---

## ✅ Scenario 1: "I Have Access to SAP"

### What You Need to Do:

#### Step 1: Find Your SAP System's Address
**Contact:** Your SAP Administrator or IT Helpdesk

Email them:
```
Hi,

I need to set up PII scanning for compliance.

Can you provide:
1. SAP server address (hostname or IP)
2. SAP port number
3. SAP client number
4. Can I get a technical user account?

Thanks!
```

**They will give you something like:**
```
- SAP Host: sap.company.com
- SAP Port: 8000
- SAP Client: 100
```

#### Step 2: Get a User Account
**Contact:** SAP Security Team or System Administrator

**Two options:**

**Option A: Use Your Existing Account (Easiest)**
- Ask if you can use your normal SAP logon
- Get password reset if needed

**Option B: Create New Technical Account (Recommended)**
Ask them to create:
```
User Name: DATAGUARDIAN (or similar)
Account Type: Technical/Service User
Password: [they provide this]
Permissions: 
  - Table/Data access
  - RFC (Remote Function Call) permissions
```

#### Step 3: Get the Credentials

```
1️⃣  SAP HOST
    What you get: sap.company.com
    OR: 192.168.1.100
    
    👉 Ask admin: "What is the SAP application server address?"
    
2️⃣  SAP PORT
    What you get: 8000 or 443
    
    👉 Ask admin: "What port is SAP running on?"
    
3️⃣  SAP CLIENT
    What you get: 100, 200, or 300 (or another number)
    
    👉 Ask admin: "What is the SAP client number?"
    (This is like a "branch" - big companies have multiple)
    
4️⃣  SAP USERNAME
    What you get: DATAGUARDIAN (or your username)
    
    👉 Your account name in SAP (case matters!)
    
5️⃣  SAP PASSWORD
    What you get: Your SAP password
    
    👉 Same as when you log into SAP normally
```

#### Step 4: Test the Credentials

Before using in DataGuardian Pro, verify:

```bash
# From Replit Shell
telnet sap.company.com 8000
```

Expected output:
```
Connected to sap.company.com
Escape character is '^]'
```

If you see "Connected", you're good! ✅

If you get "Connection refused", SAP might be on a different port or server is down.

---

## ❌ Scenario 2: "I Don't Have SAP"

### Option A: Use Demo/Test System

**SAP Offers Free Training Systems:**

1. **SAP Community Cloud**
   - Free trial environment
   - URL: https://www.sap.com/cdc/en/marketing/trial.html
   - Go to: Products → ERP → Start Trial
   - Create account and you get a demo SAP instance
   - Takes 10-15 minutes to set up
   - Includes sample data with PII

2. **What You Get After Setup:**
   - SAP Host (automatically provided)
   - SAP Port (usually 443 for HTTPS)
   - SAP Client (usually 100)
   - SAP Username (your email)
   - SAP Password (you create it)

### Option B: Use Sample Data Without SAP

If you don't want to set up SAP, DataGuardian Pro can:
1. Show mock SAP data for demo
2. Scan sample tables
3. Generate compliance reports

**Contact support or ask for:**
- Demo credentials file
- Mock data for testing

### Option C: Skip SAP for Now

- Focus on other scanners (Code, Database, Website)
- Come back to SAP when you have access
- SAP scanning is optional

---

## 📝 Step-by-Step: Getting Each Credential

### 1️⃣ SAP HOST/SERVER

**What is it?**
- The computer address where SAP runs
- Can be a hostname or IP address

**Examples:**
```
sap.company.com          ← Hostname (easier)
sap.company.nl           
sap-prod.company.com     
192.168.1.100            ← IP address (harder to remember)
10.20.30.40
```

**How to Find It:**

```
IF you have SAP on your computer:
  1. Open SAP Logon Pad
  2. Look at your saved connections
  3. See the "Host" field
  4. Copy that value
  
OR ask IT:
  "What is the SAP application server address?"
  
OR check email:
  Look for SAP setup instructions or welcome emails
```

---

### 2️⃣ SAP PORT

**What is it?**
- A "connection point" on the SAP server
- Like apartment numbers in a building
- SAP usually runs on: 8000, 8001, or 443

**Examples:**
```
8000    ← Most common (HTTP - not secure)
8001    
443     ← For HTTPS (secure - recommended)
```

**How to Find It:**

```
IF you have SAP on your computer:
  1. Open SAP Logon Pad
  2. Right-click your connection
  3. Click "Properties"
  4. Look for "Port" field
  
OR ask IT:
  "What port is SAP on? 8000 or 443?"
  
Default is usually: 8000
```

---

### 3️⃣ SAP CLIENT

**What is it?**
- A "branch" or "tenant" within SAP
- Large companies might have: Production (100), Testing (200), Development (300)
- Like different offices of same company

**Examples:**
```
100     ← Production
200     ← Quality/Testing
300     ← Development
```

**How to Find It:**

```
IF you have SAP on your computer:
  1. Open SAP
  2. Look at login screen - top right corner
  3. Field labeled "Client"
  4. You'll see: 100, 200, or 300
  
OR ask IT:
  "Which SAP client should I connect to?"
  
IF you're just testing:
  Use: 100 (most common for production)
```

---

### 4️⃣ SAP USERNAME

**What is it?**
- Your login name in SAP
- Same username you use to log in to SAP daily

**Examples:**
```
JSMITH              ← Your SAP username
ADMIN               ← Administrator
DATAGUARDIAN        ← Technical user
```

**How to Find It:**

```
IF you use SAP daily:
  That's your username!
  
IF creating new account:
  Ask IT: "Can you create user: DATAGUARDIAN?"
  They will give you the username
  
NOTE: SAP usernames are case-sensitive!
  JSMITH ≠ jsmith ≠ JSmith
```

---

### 5️⃣ SAP PASSWORD

**What is it?**
- The password to log in to SAP
- Same as your normal SAP password

**Examples:**
```
MySecurePassword123!    ← Your password
```

**How to Find It:**

```
IF you use SAP daily:
  Use your normal SAP password
  
IF creating new account:
  IT department will give you temporary password
  You can change it yourself in SAP
  
IF you forgot:
  Contact IT Helpdesk
  They can reset it
```

---

## 🛠️ Complete Checklist

Print this and fill it in:

```
SAP Connection Checklist
═══════════════════════════════════════════════════

☐ SAP Host/Server:     _______________________
  Asked IT? Yes / No
  
☐ SAP Port:            _______________________
  (Usually 8000 or 443)
  
☐ SAP Client:          _______________________
  (Usually 100)
  
☐ SAP Username:        _______________________
  (Case sensitive!)
  
☐ SAP Password:        _______________________
  (Keep secure!)
  
☐ HTTPS?               Yes / No
  (Use Yes for production)

═══════════════════════════════════════════════════
```

---

## 📞 Who to Contact at Your Company

### Best Contacts (in order):

1. **SAP System Administrator**
   - Usually in IT department
   - Knows SAP server details
   - Can create user accounts
   
2. **SAP Security Team**
   - Handles user accounts
   - Assigns permissions
   
3. **IT Helpdesk**
   - Can direct you to right person
   - Can answer basic questions
   
4. **Your Manager**
   - Can connect you to IT
   - Can explain company's SAP setup

### Sample Email

```
Subject: Need SAP connection info for compliance scanning

Hi [IT Manager],

I'm setting up a PII/privacy compliance scanner 
(DataGuardian Pro) for our organization.

Can you provide the following SAP details:

1. SAP server address (hostname or IP)
2. SAP port number
3. SAP client number
4. Can I get a technical user account created?

Please reply with these details. If it's easier, 
we can set up a quick call to discuss.

Thanks!
[Your Name]
```

---

## ✅ Verification Checklist

Once you have all 5 credentials, verify they work:

```bash
# Step 1: Test connectivity
telnet sap.company.com 8000
→ Should see: "Connected"

# Step 2: Try credentials in DataGuardian Pro
Open: http://localhost:5000
Go to: Scan Manager → Enterprise Connector → SAP
Fill in all 5 fields
Click: "Connect to SAP"

→ Should see: "Connection successful"
  and list of SAP tables
```

---

## 🚨 If You Still Can't Find Credentials

### Option 1: Talk to Your Manager
```
"I need to set up SAP PII scanning. 
Who in IT can give me SAP server details?"
```

### Option 2: Check Company Documentation
- Internal wiki/knowledge base
- IT documentation
- Employee handbook
- Previous IT tickets/emails

### Option 3: Set Up Demo SAP
- Use free SAP trial
- Get demo credentials
- Test DataGuardian Pro with demo data

### Option 4: Use Other Scanners
- Database scanner (if you have database)
- Code scanner (if you have code)
- Website scanner
- Skip SAP for now

---

## 🎯 What's Next?

**Once you have all 5 credentials:**

1. Run credential collector:
   ```bash
   python GET_SAP_CREDENTIALS.py
   ```

2. Open DataGuardian Pro:
   ```
   http://localhost:5000
   ```

3. Go to: **Scan Manager → Enterprise Connector → SAP**

4. Fill in your 5 credentials

5. Click **"Connect to SAP"**

6. Select tables and start scanning!

---

## 💡 Pro Tips

- **Start with test client** (100) before production
- **Create dedicated user** (DATAGUARDIAN) instead of using admin
- **Use HTTPS** (port 443) for security
- **Ask IT for read-only access** to tables
- **Save credentials securely** (don't share)

---

**Need more help? Ask your SAP Administrator!** 👨‍💼
