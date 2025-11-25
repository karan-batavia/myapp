# 🔧 Fix: Enable OAuth to See Consumer Key/Secret

## The Problem
Your app shows "OAuth policies" but NO "Consumer Key/Secret" section.
This means OAuth was checked but not fully configured.

---

## ✅ Solution: Edit the App and Enable OAuth Properly

### Step 1: Click "Edit Policy" Button
On the app details page, look for and click:
```
[Edit Policy]  or  [Edit]
```

---

### Step 2: Scroll Down to OAuth Settings
Find the section with:
```
☑ Enable OAuth Settings  (checkbox)
```

Make sure it's **CHECKED** ☑

---

### Step 3: Fill in the OAuth Settings

```
Enable OAuth Settings:
┌──────────────────────────────────────┐
│ ☑ Enable OAuth Settings (CHECK THIS) │
│                                      │
│ Callback URLs:                       │
│ http://localhost:5000                │
│                                      │
│ Allowed OAuth Scopes:                │
│ Available:    →→    Selected:        │
│ □ api         →→    ☑ api           │
│ □ web         →→    ☑ web           │
│ □ full        →→    ☑ full          │
└──────────────────────────────────────┘
```

**Add these scopes:**
- ☑ api
- ☑ web
- ☑ full

---

### Step 4: Click [Save]

At the bottom of the form:
```
[Save]  ← Click this
```

---

### Step 5: You'll See Consumer Key & Secret

After saving, you'll be back on the app details page.
Now scroll down and you should see:

```
════════════════════════════════════════
CONSUMER DETAILS
════════════════════════════════════════

Consumer Key
3MVG9d8._XXXXXXXXXXXXXXXXXXXXXXXX
[Copy]  ← Click this

Consumer Secret
••••••••••••••••••••••••
[Show] [Copy]  ← Click Show first
```

---

## 🎯 If Still Not Visible

**Try Step 1 Again:**

1. On the app details page, find **"Edit Policy"** button (top of page)
2. Click it
3. Scroll down to **"Enable OAuth Settings"**
4. ☑ **CHECK the box** if unchecked
5. Add Callback URL: `http://localhost:5000`
6. Add Scopes: `api`, `web`, `full`
7. **Click Save**

After saving, refresh the page (F5) if needed.

---

## 🚀 Then Get Your Keys

Once you see **CONSUMER DETAILS**:

1. **Copy Consumer Key** → Click [Copy] button
2. **Copy Consumer Secret** → Click [Show] → Click [Copy]
3. **Run the Python script** to save them
4. **Use in DataGuardian Pro** to scan Salesforce!

---

**Try editing the app now and enabling OAuth properly!** 🔧
