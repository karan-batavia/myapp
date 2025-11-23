# 🔑 Get Consumer Key & Consumer Secret - From Your Current Page

## You're Here Now ✓
You can see the "Connected apps" page with a dropdown that says **"DataGuardianPro"**

---

## 🎯 Option 1: If "DataGuardianPro" Already Exists (Easiest)

### Step 1: Click on the Dropdown
```
At the top, you see:
┌─────────────────────────────────┐
│ To display: DataGuardianPro ▼   │ ← CLICK ON THIS
│           [Edit] [Create New View]
└─────────────────────────────────┘
```

**Click on "DataGuardianPro"** dropdown arrow (▼)

### Step 2: You'll See Options
```
Dropdown appears:
├─ DataGuardianPro  ← Click this to select it
└─ All Connected Apps
```

**Click "DataGuardianPro"**

### Step 3: Click the App Name to Open It
After selecting from dropdown, look for the app name in the table below and **click it**:

```
Connected Apps Table:
┌────────────────────────────────────────┐
│ Main label │ Application version │ ... │
├────────────────────────────────────────┤
│ DataGuardianPro  ← CLICK THIS TEXT    │
└────────────────────────────────────────┘
```

**Click "DataGuardianPro"** text (it's a link)

---

## 🎯 Option 2: If "DataGuardianPro" Doesn't Exist (Create New)

### Step 1: Click "Create New Connected App"
On the Connected apps page, look for a button:

```
You might see at the top:
┌──────────────────────────────────────────┐
│ "New Connected App"  ← Click this button │
│ or "Create New Connected App"            │
└──────────────────────────────────────────┘
```

**Or use the "Create New View" link and look for a Create button**

### Step 2: Fill in the Form
```
New Connected App Form:
┌────────────────────────────────────┐
│ Connected App Name: │ DataGuardian Pro │
│ API Name: │ DataGuardian_Pro │
│ Contact Email: │ [your email] │
│ ☑ Enable OAuth Settings │
└────────────────────────────────────┘
```

### Step 3: Enable OAuth Settings Section
Check the box: **☑ Enable OAuth Settings**

This will show:
```
OAuth Settings:
┌────────────────────────────────────┐
│ Callback URL: │ http://localhost:5000 │
│ Selected OAuth Scopes: │ [full] [api] │
└────────────────────────────────────┘
```

### Step 4: Save
Click **[Save]** button

### Step 5: You'll See Your Keys
After saving, you'll see:

```
OAuth Client Identifier
┌────────────────────────────────────┐
│ Consumer Key:                      │
│ 3MVG9d8...[long code]  [Copy]    │
│                                    │
│ Consumer Secret:                   │
│ ••••••••••••••••  [Show] [Copy]  │
└────────────────────────────────────┘
```

---

## ✅ Final Step: Copy Your Keys

After you can see the app details (either from Option 1 or Option 2), you'll see this section:

```
OAuth Client Identifier (or OAuth Settings)
┌──────────────────────────────────────────────────────┐
│ Consumer Key                                         │
│ 3MVG9d8._XXXXXX-XXXXXXXXXXXXXXXXXXXXX                │ ← This whole code
│ [Copy Button]                                        │
│                                                      │
│ Consumer Secret                                      │
│ ••••••••••••••••••••••••••••••••                    │
│ [Show] [Copy]                                       │
└──────────────────────────────────────────────────────┘
```

### Action:
1. ✅ **Click "Copy"** next to Consumer Key → Save it somewhere safe
2. ✅ **Click "Show"** next to Consumer Secret (reveals the hidden code)
3. ✅ **Click "Copy"** next to Consumer Secret → Save it somewhere safe

---

## 📝 What You're Looking For

Your values will look like this:

```
Consumer Key:
3MVG9d8._XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
(Starts with "3MVG", about 80+ characters)

Consumer Secret:
987654321ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789
(Random alphanumeric, about 40+ characters)
```

---

## 🎯 Then You Have All 5 Credentials:

```
☑ Salesforce Username: vishaal05@agensics.com.sandbox
☑ Salesforce Password: [your password]
☑ Consumer Key: 3MVG9d8...[from above]
☑ Consumer Secret: 987654321...[from above]
☑ Security Token: [from email - follow separate guide]
```

---

## 🚀 What's Next?

Once you have all 5 values:

1. **Open DataGuardian Pro:** http://localhost:5000
2. **Navigate to:** Scan Manager → Enterprise Connector → Salesforce CRM tab
3. **Fill in the form** with your 5 credentials
4. **Click "Connect to Salesforce"**
5. **Let it scan for PII!**

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Don't see "DataGuardianPro" in dropdown | You need to create a new Connected App (Option 2 above) |
| Consumer Secret shows asterisks | Click **[Show]** button first to reveal it |
| Can't find where to create new app | Look for "New" button at top of page, or check if there's a "+" icon |
| Page looks different | You might be on a different Salesforce version - look for "Connected Apps" menu item |

---

## 💡 Pro Tip

**Once you get these values:**
- Save them in a safe text file or notes
- You'll only need to generate them once
- Reuse them every time you want to scan Salesforce
- DataGuardian Pro can save them encrypted for future use

---

**Ready? Go to your Salesforce page and:**
1. Find DataGuardianPro in the dropdown (or create it)
2. Click on it to open the app details
3. Look for "Consumer Key" and "Consumer Secret"
4. Click Copy for each one
5. Come back here with the values! 🎉**
