# ✅ Salesforce OAuth Connected App Setup - Working Guide 2025

Since YouTube videos get removed, here's the **official Salesforce documentation** + step-by-step guide.

---

## 📖 Official Salesforce Documentation (ALWAYS UP-TO-DATE)

### **#1 BEST RESOURCE: Official Salesforce Create Connected App Guide**
**Link:** https://help.salesforce.com/s/articleView?id=sf.connected_app_create.htm

This is the **official Salesforce documentation** - always current, never gets taken down.

**What it covers:**
- Creating Connected App
- Enabling OAuth Settings
- Setting Callback URL
- Selecting OAuth Scopes
- Getting Consumer Key & Secret

---

## 🎬 YouTube - How to Search for Current Videos

Since specific videos get deleted, search YouTube directly for these terms:

**Search YouTube for:**
1. `"Salesforce Connected App OAuth setup 2025"`
2. `"How to create Salesforce Connected App"`
3. `"Salesforce Consumer Key and Consumer Secret"`
4. `"Salesforce API setup tutorial"`
5. `"Salesforce OAuth 2.0 tutorial"`

**Why search directly?** New videos uploaded constantly, and you'll get the most current ones with the latest Salesforce UI.

---

## 📋 Step-by-Step Setup (Official Salesforce Instructions)

### **Step 1: Go to Setup**

1. Click the **gear icon** (top-right of Salesforce)
2. Select **"Setup"**
3. In the **Quick Find** box, type: `"App Manager"`
4. Click **"App Manager"** from results

---

### **Step 2: Create New Connected App**

1. Click **"New Connected App"** button (top-right)
2. You'll see a form with fields:

```
Connected App Name:        [Enter a name like "DataGuardian Pro"]
API Name:                  [Auto-fills - don't change]
Contact Email:             [Your Salesforce admin email]
```

3. Fill these in, then scroll down

---

### **Step 3: ENABLE OAUTH SETTINGS (CRITICAL!)**

This is the step that was missing before!

✅ Check the box: **"Enable OAuth Settings"**

Once checked, you'll see new fields:

```
Callback URL:  https://login.salesforce.com/services/oauth2/callback
```

For **OAuth Scopes**, click the arrow next to **"Available OAuth Scopes"** on the LEFT

Select these scopes (click → to move to the RIGHT):
- ✅ **Access and manage your data (api)**
- ✅ **Perform requests on your behalf at any time (refresh_token, offline_access)**

Your screen should show these in the "Selected OAuth Scopes" box on the right.

---

### **Step 4: Save**

1. Click **"Save"** button at bottom
2. Wait 2-5 minutes for changes to take effect
3. You'll see a confirmation page

---

### **Step 5: Get Consumer Key & Secret**

**THE MOST IMPORTANT STEP!**

1. Go back to **App Manager**
   - Setup → App Manager (use Quick Find)

2. Find your Connected App in the list

3. Click the **dropdown arrow** on the far right of your app row

4. Select **"View"** (NOT "Edit")

5. Look for section: **"API (Enable OAuth Settings)"**

6. Click button: **"Manage Consumer Details"**

7. Salesforce may ask you to verify your identity (MFA)

8. You'll see:
   ```
   Consumer Key:    [A long alphanumeric string]
   Consumer Secret: [Another long alphanumeric string]
   ```

9. **COPY BOTH** and save them in a secure location

---

## ✅ Now You Have Your 3 Credentials

```
1. Consumer Key:     [copied from above]
2. Consumer Secret:  [copied from above]
3. Instance URL:     https://login.salesforce.com (or your custom)
```

---

## 🚀 Use in DataGuardian Pro

1. Open browser: http://localhost:5000

2. Go to: **Scan Manager → Enterprise Connector → Salesforce**

3. Fill in form:
   ```
   Salesforce Instance URL:  https://login.salesforce.com
   Consumer Key:             [your Consumer Key]
   Consumer Secret:          [your Consumer Secret]
   ```

4. Click: **[Connect to Salesforce]**

5. You'll be redirected to authorize the app

6. Click **[Allow]** or **[Authorize]**

7. Back in DataGuardian Pro you'll see: ✅ **Connection Successful**

---

## 🔍 Where Things Are Located (Visual Guide)

```
SALESFORCE SETUP SCREEN LAYOUT
╔══════════════════════════════════════════╗
║  Gear Icon (top-right) → Setup           ║
║  Quick Find → "App Manager"              ║
║  New Connected App button → Click        ║
║                                          ║
║  FORM FIELDS:                            ║
║  ├─ Connected App Name                   ║
║  ├─ API Name (auto)                      ║
║  ├─ Contact Email                        ║
║  │                                       ║
║  ├─ ☑ Enable OAuth Settings (CHECK!)     ║
║  │   ├─ Callback URL                     ║
║  │   ├─ OAuth Scopes (select 2)          ║
║  │       ├─ api ✓                        ║
║  │       └─ refresh_token ✓              ║
║  │                                       ║
║  └─ [Save] button                        ║
╚══════════════════════════════════════════╝

After Save → App Manager → View → Manage Consumer Details
```

---

## ⚠️ Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Can't see "Enable OAuth Settings" checkbox | Scroll down on form, it's below Contact Email |
| Consumer Key/Secret not visible | Click "Manage Consumer Details" button (NOT Edit) |
| "Invalid Consumer Key" error in DataGuardian | Check spelling - copy directly, don't retype |
| Still can't find the button | Try official Salesforce doc: https://help.salesforce.com/s/articleView?id=sf.connected_app_create.htm |
| MFA verification fails | Try again, or contact Salesforce admin |

---

## 📞 Official Resources

| Resource | Link | Type |
|----------|------|------|
| **Create Connected App** | https://help.salesforce.com/s/articleView?id=sf.connected_app_create.htm | Official Doc |
| **OAuth Documentation** | https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_oauth_and_connected_apps.htm | Developer Guide |
| **Consumer Key/Secret Info** | https://help.salesforce.com/s/articleView?id=sf.connected_app_rotate_consumer_details.htm | Official Doc |
| **Trailhead Course** | https://trailhead.salesforce.com/ | Free Video Course |

---

## 🎯 YouTube Search Strategy

Don't use specific video links (they get deleted). Instead:

1. **Go to YouTube**
2. **Search:** `"Salesforce Connected App OAuth setup"`
3. **Filter:** Upload date → Last month
4. **Watch:** First 5 minutes to see if it matches what you need
5. **Quality:** Look for videos from official Salesforce channels or popular integration channels

**Current Popular Channels:**
- Salesforce Developers (official)
- Trailhead
- Cloud Custodian
- Integration-specific channels (Zapier, MuleSoft, etc.)

---

## ✨ My Recommendation

**Follow this path:**

1. **Read:** This guide (SAP_OAUTH_SETUP_WORKING_GUIDE.md) section "Step-by-Step Setup"

2. **Use:** Official Salesforce documentation
   - Link: https://help.salesforce.com/s/articleView?id=sf.connected_app_create.htm
   - Keep this open while you work

3. **Optional - YouTube:** Search `"Salesforce Connected App OAuth"` to SEE the UI in action
   - Great for visual learners
   - But written guide above is complete

4. **Execute:** Follow steps 1-5 above

5. **Test:** In DataGuardian Pro
   - Use Consumer Key & Secret
   - Connect and scan

---

## 🔐 Security Notes

- **Consumer Secret** is like a password - keep it PRIVATE
- Never put it in public code or GitHub
- Don't share via email
- Store in secure password manager or DataGuardian Pro secrets

---

## 🚀 Next Steps - Start NOW

1. **Open Salesforce** in browser
2. **Click gear icon** → Setup
3. **Type "App Manager"** in Quick Find
4. **Click "New Connected App"**
5. **Fill in the form** using steps above
6. **CHECK: "Enable OAuth Settings"** ← Most important!
7. **Select scopes** (api + refresh_token)
8. **Click Save**
9. **Wait 2-5 minutes**
10. **Go back to App Manager**
11. **Click View** on your app
12. **Click "Manage Consumer Details"**
13. **Copy Consumer Key**
14. **Copy Consumer Secret**
15. **Use in DataGuardian Pro** ✅

---

## 💡 Key Takeaway

The **official Salesforce documentation** (link above) is the most reliable source - it's always kept up-to-date and never gets removed like YouTube videos do.

This written guide mirrors the official docs, so you're following best practices.

---

**Ready to get started?** Follow the "Step-by-Step Setup" section above! 🎉
