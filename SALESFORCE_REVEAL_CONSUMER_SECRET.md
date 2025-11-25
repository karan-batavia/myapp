# 🔍 How to Reveal Consumer Secret in Salesforce

## The Issue
You see dots `••••••••••••••••` instead of the actual Consumer Secret.

**This is normal!** Salesforce hides the secret for security. You need to click "[Show]" to reveal it.

---

## ✅ Step-by-Step to See Your Secret

### Step 1: Go to Your DataGuardian Pro App
```
Setup → Manage apps → Connected apps → DataGuardian Pro
```

Click on the app name to open it.

---

### Step 2: Look for CONSUMER DETAILS Section

Scroll down until you see:

```
════════════════════════════════════════
CONSUMER DETAILS
════════════════════════════════════════

Consumer Key
┌─────────────────────────────────────────┐
│ 3MVG9d8._[YOUR_KEY_HERE]...             │
│                                         │
│ [Copy]  ← Click to copy                 │
└─────────────────────────────────────────┘

Consumer Secret
┌─────────────────────────────────────────┐
│ ••••••••••••••••••••••••••••••••        │
│                                         │
│ [Show]  [Copy]  ← Click Show FIRST!    │
└─────────────────────────────────────────┘
```

---

### Step 3: Click "[Show]" Button

Click the **[Show]** button next to Consumer Secret.

The dots will disappear and show the actual secret:

```
Before:  ••••••••••••••••••••••••••••••••
After:   8a7b6c5d4e3f2g1h0i9j8k7l6m5n4o3p
```

---

### Step 4: Immediately Click "[Copy]"

After clicking Show, quickly click **[Copy]**

(The secret may hide again after a few seconds for security)

---

## 📋 If Still Not Working

### Possibility 1: Page Not Fully Loaded
- Refresh the page (F5)
- Wait 2-3 seconds for page to fully load
- Try again

### Possibility 2: Need to Scroll Right
Some Salesforce UIs have the buttons on the right side:
- Try scrolling right on the Consumer Secret line
- Look for [Show] and [Copy] buttons

### Possibility 3: Different Salesforce UI (Lightning)
If you're using modern Salesforce (Lightning), the layout might be different:

1. Find "Consumer Details" section
2. Look for a **gear icon ⚙️** or **three-dot menu ⋯**
3. Click it and select "Show"
4. Then "Copy"

---

## 🚀 Once You Have Both Keys

```
3️⃣ CONSUMER KEY:     3MVG9d8._XXXXXXXXXXXXXXXXXXXXXXX
4️⃣ CONSUMER SECRET:  8a7b6c5d4e3f2g1h0i9j8k7l6m5n4o3p
```

Use the Python script to save them:

```bash
python GET_SALESFORCE_OAUTH_KEYS.py
```

---

## ⚠️ Important Notes

- **Consumer Secret is shown only once** - If you close it and need it again, repeat steps 2-4
- **Never share your keys** - Keep them private!
- **Don't paste in chat** - Only paste in the Python script or DataGuardian Pro

---

## 🎯 Next: Use in DataGuardian Pro

Once you have both keys:

1. Open http://localhost:5000
2. Go to: **Scan Manager → Enterprise Connector → Salesforce CRM**
3. Fill in:
   - Username: `vishaal05@agensics.com.sandbox`
   - Password: [your password]
   - Consumer Key: [from above]
   - Consumer Secret: [from above]
   - Security Token: [from email]
4. Click **"Connect to Salesforce"**
5. Start scanning!

---

**Try clicking [Show] next to Consumer Secret now!** 🔍
