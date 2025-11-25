# 🔴 Problem: This App Can't Be Fixed

## What Happened
The app "orgform_app_1" was created **WITHOUT OAuth enabled from the start**.

Once created without OAuth, you cannot add Consumer Key/Secret by editing it.

The "OAuth policies" you see are just **policy settings**, not actual OAuth enablement.

---

## ✅ Solution: Create a BRAND NEW Connected App with OAuth

### Step 1: Go Back to Connected Apps List
Click: **Setup → Manage apps → Connected apps**

---

### Step 2: Delete or Ignore Old App
You can ignore "orgform_app_1" - it won't work for OAuth.

(Optional: Click it and delete if you want, but not necessary)

---

### Step 3: Click "New Connected App"
Find and click the:
```
[New Connected App]  button
```

---

### Step 4: Fill Out the Form EXACTLY

```
CREATE A NEW CONNECTED APP
═════════════════════════════════════════════

BASIC INFORMATION SECTION:
┌─────────────────────────────────────────┐
│ * Connected App Name:                   │
│   DataGuardian Pro                      │
│                                         │
│ * API Name:                             │
│   DataGuardian_Pro                      │
│                                         │
│ * Contact Email:                        │
│   [your email]                          │
│                                         │
│ ☐ Allow external clients...             │
│   (leave unchecked)                     │
│                                         │
│ ☐ Require Proof Key (PKCE)...           │
│   (leave unchecked)                     │
└─────────────────────────────────────────┘

SCROLL DOWN →
```

---

### Step 5: Find and CHECK "Enable OAuth Settings"

```
OAuth Settings Section:
┌─────────────────────────────────────────┐
│ ☑ Enable OAuth Settings                 │
│   (MUST CHECK THIS BOX!)                │
│                                         │
│ After checking, fields appear:          │
│                                         │
│ * Callback URLs:                        │
│   http://localhost:5000                 │
│   (one per line, add more with + icon)  │
│                                         │
│ * Allowed OAuth Scopes:                 │
│   [Available]        →→      [Selected] │
│                                         │
│   Move to Selected:                     │
│   - api                                 │
│   - web                                 │
│   - full                                │
│   - refresh_token                       │
│                                         │
│ ☑ Require Secret For Web Server Flow    │
│   (check this box)                      │
└─────────────────────────────────────────┘
```

---

### Step 6: Click [Save]

At the bottom of the form:
```
[Save]  ← CLICK THIS
```

---

## 🎉 IMMEDIATELY After Saving

You'll see the app details page showing:

```
DataGuardian Pro (New App Details)
═════════════════════════════════════════════

CONSUMER DETAILS
┌─────────────────────────────────────┐
│ Consumer Key                        │
│ 3MVG9d8._XXXXXXXXXXXXXXXXXXXXXXX   │
│ [Copy]  ← CLICK THIS                │
│                                     │
│ Consumer Secret                     │
│ ••••••••••••••••••••••••••         │
│ [Show] [Copy]  ← CLICK Show First  │
└─────────────────────────────────────┘
```

---

## ✅ Now Copy Your Keys

1. **Consumer Key:** Click [Copy] → Save it
2. **Consumer Secret:** Click [Show] → Click [Copy] → Save it

---

## 🚀 Then Use Python Script

```bash
python GET_SALESFORCE_OAUTH_KEYS.py
```

Paste your keys when prompted!

---

## 📋 Checklist for NEW App

```
☐ Name: DataGuardian Pro
☐ API Name: DataGuardian_Pro
☐ Email: your@email.com
☐ ☑ Enable OAuth Settings (MUST CHECK)
☐ Callback URL: http://localhost:5000
☐ Scopes: api, web, full
☐ ☑ Require Secret For Web Server Flow
☐ Click [Save]
☐ Copy Consumer Key
☐ Copy Consumer Secret
```

---

## ⚠️ Key Point

**The old app (orgform_app_1) cannot be fixed!**

You MUST create a new app with OAuth enabled during creation.
Only then will you get Consumer Key & Secret.

---

**Do this NOW:**

1. Go to Connected apps
2. Click [New Connected App]
3. Create "DataGuardian Pro" with OAuth enabled
4. Save and copy your keys!

Then you're ready to test in DataGuardian Pro! 🎉
