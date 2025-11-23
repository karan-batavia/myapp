# 🎯 Finding Your Salesforce Credentials - Visual Guide

## You're Currently Here (in Setup)
You can see the left menu with "Manage apps", "Manage users", etc. - Perfect!

---

## 📍 STEP 1: Get Consumer Key & Consumer Secret

### Navigate to App Manager
From your current Setup page:

**In the left sidebar, look for "Manage apps" section**

```
Left Menu:
├─ Home page
├─ To manage
│  ├─ Release updates
│  ├─ Manage users        ← Your screenshot shows this
│  ├─ Manage apps         ← CLICK HERE
│  └─ [other options]
```

**Click on "Manage apps"**

### You'll see a submenu appear:
```
Manage apps
├─ Integrations
├─ Connected apps
│  ├─ Connected apps     ← This is what you need
│  └─ Manage connected apps
└─ Extensibility
```

**Click "Connected apps"** (or "Manage connected apps")

---

### What You'll See Next

You'll see a list of apps:
```
Connected Apps
┌──────────────────────────────────────────────────┐
│ Name                      │ Type     │ Created   │
├──────────────────────────────────────────────────┤
│ TestAPIApp               │ OAuth    │ Sept 2024 │
│ TestAPIApp (Dev)         │ OAuth    │ Sept 2024 │
│ DataGuardian Pro         │ OAuth    │ Nov 2024  │ ← If you created one
└──────────────────────────────────────────────────┘
```

**If you see "DataGuardian Pro" already created:**
- Click on it → Go to Step 2 below

**If you DON'T see "DataGuardian Pro":**
- Click "New Connected App" button
- Name it: `DataGuardian Pro`
- Check "Enable OAuth Settings"
- Fill in callback URL: `http://localhost:5000`
- Save → Continue to Step 2

---

## 🔑 STEP 2: Copy Consumer Key & Secret

### After clicking on your app (DataGuardian Pro):

You'll see the app details page with this layout:

```
DataGuardian Pro (Connected App Details)

Application Settings
┌─────────────────────────────────────────┐
│ Basic Information                       │
│ Connected App Name: DataGuardian Pro   │
│ Developer Name: Vishaal Kumar          │
│ ................                        │
└─────────────────────────────────────────┘

API Settings (Enable OAuth Settings)
┌─────────────────────────────────────────┐
│ Callback URL: http://localhost:5000    │
│ Selected Scopes: full, api              │
│ ................                        │
└─────────────────────────────────────────┘
```

### Scroll Down to Find OAuth Keys Section

Look for a section that says:

```
OAuth Client Identifier (or "Consumer Details")
┌─────────────────────────────────────────────────┐
│ Consumer Key                                    │
│ 3MVG9d8...[24-character code]                   │ ← COPY THIS
│ [Copy button]                                   │
│                                                 │
│ Consumer Secret                                 │
│ ••••••••••••••••••• [Show] [Copy]              │ ← CLICK "Show" first
│                                                 │
│ After clicking Show:                           │
│ 987654321ABCD...[30-character code]            │ ← COPY THIS
│ [Copy button]                                   │
└─────────────────────────────────────────────────┘
```

### Your Actions:
1. ✅ **Copy Consumer Key** (the first long code starting with 3MVG9d8...)
2. ✅ **Click "Show"** button next to Consumer Secret
3. ✅ **Copy Consumer Secret** (the hidden code that appears)

---

## 🔐 STEP 3: Get Security Token

### Go to Your Personal Settings

**At the top right of Salesforce, look for your profile icon/name:**

```
Top right corner:
┌──────────────────────────────┐
│  Help  |  Setup  |  👤 ▼    │
│        |         | Vishaal  │
│        |         | Kumar    │
│        |         |  [▼]     │ ← CLICK THIS DROPDOWN
└──────────────────────────────┘
```

**Click on your name (Vishaal Kumar) dropdown**

---

### You'll See a Menu:

```
User Menu:
├─ Profile            ← NOT this one
├─ Settings           ← CLICK THIS ONE
├─ Chatter Profile
├─ Change Password
├─ Logout
└─ [other options]
```

**Click "Settings"**

---

### You're Now in Your Personal Settings

**Look for the search box at the top** (where it says "Snel zoeken / Zoeken")

```
┌─────────────────────────────┐
│ Snel zoeken / Zoeken        │
│ [Search box]                │
└─────────────────────────────┘
```

**Type "Reset Security Token"** in the search box

---

### Search Results

```
Search Results:
├─ Reset security token     ← THIS ONE
├─ Security token settings
└─ [other results]
```

**Click "Reset security token"**

---

### Action Required

You'll see:

```
Reset Security Token
┌────────────────────────────────────────────┐
│ ⚠️  Warning: Resetting your security token │
│ will invalidate all existing tokens.       │
│                                            │
│ Are you sure you want to proceed?          │
│                                            │
│ [Cancel]  [Reset]  ← CLICK Reset         │
└────────────────────────────────────────────┘
```

**Click "Reset" button**

---

### Check Your Email

After clicking Reset:

```
You'll see:
✅ "Security token was sent to your email"

Go to your email (Vishaal's email account)
Subject: "Salesforce Security Token"

Email content:
────────────────────────────────
Your new security token is:

    AbCd1234efgh5678ijkl9012

────────────────────────────────

✅ COPY THIS 24-CHARACTER CODE
```

---

## 📋 Summary: Where to Find Everything

| What | Where | Steps |
|-----|-------|-------|
| **Consumer Key** | Setup → Manage apps → Connected apps → Your app | Scroll down, see "Consumer Key", copy it |
| **Consumer Secret** | Same location as Consumer Key | Click "Show", then copy the code |
| **Security Token** | Top right profile → Settings → Search "Reset security token" | Click Reset, check email for token |

---

## ✅ Your Complete Credentials Checklist

After following these steps, you'll have:

```
☐ Salesforce Username: vishaal05@agensics.com.sandbox
☐ Salesforce Password: [your password]
☐ Consumer Key: 3MVG9d8..... (24 chars, copied from Connected App)
☐ Consumer Secret: 987654321.... (30 chars, copied after clicking Show)
☐ Security Token: AbCd1234.... (24 chars, from email)
```

---

## 🎯 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Can't find "Connected apps" | Make sure you clicked "Manage apps" in left sidebar, not the main menu |
| Consumer Secret shows asterisks | You must click "Show" button first to reveal it |
| Security token not in email | Check spam folder, or wait 5 minutes and try resetting again |
| No "DataGuardian Pro" app exists | Create a new Connected App with that name and OAuth enabled |

---

## 🚀 Next Steps After Getting Credentials

1. Have all 5 values ready:
   - ✅ Username
   - ✅ Password
   - ✅ Consumer Key
   - ✅ Consumer Secret
   - ✅ Security Token

2. Open DataGuardian Pro: http://localhost:5000

3. Go to: Scan Manager → Enterprise Connector → Salesforce CRM tab

4. Fill in all 5 fields and click "Connect"

5. Let it scan your Salesforce data for PII!

---

**Got your credentials? Ready to test!** 🎉
