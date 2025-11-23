# 🔧 Fix: "No records to display" Problem

## The Issue
You selected "DataGuardianPro" from dropdown, but the table still shows:
```
"No records to display"
```

This means the app either:
1. ❌ Doesn't exist yet
2. ❌ Isn't selected properly

---

## ✅ Solution: Create the App NOW

### Step 1: Look for "New Connected App" Button
On the Connected apps page, find a button at the top that says:
```
[New Connected App]
or
[New]
or
[+ Add]
```

**Click it**

---

### Step 2: Fill Out the Form

```
Connected App Form:
┌──────────────────────────────────────┐
│ * Connected App Name:                │
│   ┌──────────────────────────────┐   │
│   │ DataGuardian Pro             │   │
│   └──────────────────────────────┘   │
│                                      │
│ * API Name:                          │
│   ┌──────────────────────────────┐   │
│   │ DataGuardian_Pro             │   │
│   └──────────────────────────────┘   │
│                                      │
│ * Contact Email:                     │
│   ┌──────────────────────────────┐   │
│   │ [your email]                 │   │
│   └──────────────────────────────┘   │
│                                      │
│ [ ] Enable OAuth Settings            │ ← Scroll down
└──────────────────────────────────────┘
```

**Fill in:**
- Connected App Name: `DataGuardian Pro`
- API Name: `DataGuardian_Pro`
- Contact Email: Your email

---

### Step 3: Scroll Down - Find OAuth Settings

Scroll down and find:
```
☐ Enable OAuth Settings
  (checkbox)
```

**CHECK this box ☑**

---

### Step 4: Fill in OAuth Settings

After checking the box, more fields appear:
```
ENABLE OAUTH SETTINGS:
┌──────────────────────────────────────┐
│ * Callback URL:                      │
│   ┌──────────────────────────────┐   │
│   │ http://localhost:5000        │   │
│   └──────────────────────────────┘   │
│                                      │
│ * Selected OAuth Scopes:             │
│   Available:          Selected:      │
│   [api]      →→       [api]          │
│   [web]      →→       [web]          │
│   [full]     →→       [full]         │
│   [other]                           │
│                                      │
│ (Select: api, web, full)             │
└──────────────────────────────────────┘
```

**Fill in:**
- Callback URL: `http://localhost:5000`
- Selected Scopes: Add `api` and `web` and `full`

---

### Step 5: Click [Save]

At the bottom of the form, click:
```
[Save]  or  [Save and Continue]
```

---

### Step 6: Your Keys Appear!

After saving, you'll see:

```
DataGuardian Pro (App Details)
═══════════════════════════════════════

CONSUMER DETAILS
┌──────────────────────────────────────┐
│ Consumer Key                         │
│ 3MVG9d8._XXXXXXXXXXXXXXXXXXXXXXX    │
│ [Copy] ← CLICK THIS                 │
│                                      │
│ Consumer Secret                      │
│ •••••••••••••••••••••••••••         │
│ [Show] [Copy]                       │
│ Click Show → Then Click Copy        │
└──────────────────────────────────────┘
```

---

## ✅ Then Copy Your Keys

1. **Consumer Key:** Click [Copy] → Save it
2. **Consumer Secret:** Click [Show] → Click [Copy] → Save it

---

## 🎯 You Now Have:

```
✓ Consumer Key:     3MVG9d8._XXXXXXXX...
✓ Consumer Secret:  987654321XXXXXXXX...

Now you need:
□ Security Token (from email)
□ Username: vishaal05@agensics.com.sandbox
□ Password: (your password)
```

---

## 📝 Quick Checklist

- [ ] Click "New Connected App" button
- [ ] Fill in Name: DataGuardian Pro
- [ ] Fill in API Name: DataGuardian_Pro
- [ ] Fill in Email: your email
- [ ] ☑ Check "Enable OAuth Settings"
- [ ] Fill in Callback URL: http://localhost:5000
- [ ] Select Scopes: api, web, full
- [ ] Click [Save]
- [ ] Copy Consumer Key
- [ ] Copy Consumer Secret

---

**Do this now and you'll have your keys!** ⚡
