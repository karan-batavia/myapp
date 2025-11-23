# 🔴 Problem: OAuth Not Enabled on This App

## What You're Seeing ✓
This connected app ("orgform_app_1") shows:
- ✅ Session policies
- ✅ User profile settings
- ❌ **NO Consumer Key/Secret**

The "CONSUMER DETAIL 0/0" in the top right means this app **doesn't have OAuth enabled**.

---

## ✅ Solution: Create NEW App with OAuth

### Step 1: Go Back to Connected Apps List
Click **"Back to list: Connected apps"** link at the top of the page

Or go to: **Setup → Manage apps → Connected apps**

---

### Step 2: Click "New Connected App" Button
```
[New Connected App]  ← Click this button
```

---

### Step 3: Fill Out the Form - EXACTLY Like This

```
CONNECTED APP SETUP
════════════════════════════════════════════

BASIC INFORMATION
┌────────────────────────────────────────┐
│ * Connected App Name:                  │
│   DataGuardian Pro                     │
│                                        │
│ * API Name:                            │
│   DataGuardian_Pro                     │
│                                        │
│ * Contact Email:                       │
│   [your email]                         │
└────────────────────────────────────────┘

[ ] Allow external clients...
    (leave unchecked)

[ ] Require Proof Key (PKCE)...
    (leave unchecked)
```

**Fill in the 3 basic fields**

---

### Step 4: SCROLL DOWN - Find OAuth Settings

Look for this checkbox:
```
☐ Enable OAuth Settings
  (checkbox to check)
```

**☑ CHECK THIS BOX**

After checking, a new section appears:

```
OAUTH SETTINGS (appears after checking the box)
┌────────────────────────────────────────┐
│ * Callback URLs:                       │
│   http://localhost:5000                │
│   (one per line)                       │
│                                        │
│ * Allowed OAuth Scopes:                │
│   Available:        →→   Selected:     │
│   api               →→   [api]         │
│   web               →→   [web]         │
│   full              →→   [full]        │
│   refresh_token                        │
│                                        │
│ Require Secret...                      │
│ ☑ Require Proof Key (PKCE)             │
└────────────────────────────────────────┘
```

**Fill in:**
- Callback URL: `http://localhost:5000`
- Move `api`, `web`, `full` to Selected scopes

---

### Step 5: Click [Save]

At the bottom of the form:
```
[Save]  ← Click this button
```

---

## 🎉 After Saving - Your Keys Appear!

You'll see a new page showing:

```
DataGuardian Pro (App Details)
════════════════════════════════════════════

CONSUMER DETAILS
┌────────────────────────────────────────┐
│ Consumer Key                           │
│ 3MVG9d8._XXXXXXXXXXXXXXXXXXXXXXXXXX   │
│                            [Copy]     │
│                                        │
│ Consumer Secret                        │
│ ••••••••••••••••••••••••••••••••      │
│                   [Show]  [Copy]      │
└────────────────────────────────────────┘
```

---

## ✅ Copy Your Keys NOW

1. **Consumer Key:**
   - Click [Copy]
   - Save it

2. **Consumer Secret:**
   - Click [Show]
   - Click [Copy]
   - Save it

---

## 📋 Your Complete Checklist

```
NEW CONNECTED APP:
☐ Name: DataGuardian Pro
☐ API Name: DataGuardian_Pro
☐ Contact Email: your@email.com
☐ ☑ Enable OAuth Settings (MUST CHECK)
☐ Callback URL: http://localhost:5000
☐ Scopes: api, web, full
☐ Click [Save]

THEN COPY:
☐ Consumer Key
☐ Consumer Secret
```

---

## 🚀 Why the Old App Doesn't Have Keys

The "orgform_app_1" app you were looking at was created **without OAuth enabled**, so it:
- ✅ Exists as a connected app
- ✅ Can be used for some integrations
- ❌ Has NO OAuth credentials (no Consumer Key/Secret)

For Salesforce OAuth authentication, you NEED a new app with OAuth enabled.

---

## 🎯 Next Steps

1. Go back to Connected apps list
2. Click "New Connected App"
3. Create "DataGuardian Pro" with OAuth enabled
4. Save and get your keys
5. Copy both keys
6. Get Security Token from email
7. Come back ready to test!

---

**Do this NOW - takes 5 minutes!** ⚡

The "DataGuardian Pro" app with OAuth will have your Consumer Key & Secret waiting on the next page after you click Save.
