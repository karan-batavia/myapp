# 💻 Alternative: Use Salesforce CLI

If the web UI isn't showing your Consumer Secret, you can try using **Salesforce CLI** from the command line.

---

## Option 1: EASIEST - Try Regenerate First

**Before using CLI**, try the easier approach:

1. Go to your DataGuardian Pro app in Salesforce
2. Look for **[Rotate Consumer Secret]** or **[Regenerate Secret]** button
3. Click it to get a new secret you can see
4. Copy the new one

See: **SALESFORCE_REGENERATE_SECRET.md**

---

## Option 2: Use Salesforce CLI

If you have **Salesforce CLI** installed:

```bash
# First, authenticate with your Salesforce org
sf auth web login -o vishaal05@agensics.com.sandbox

# Then list your connected apps to find the app ID
sf force data record get --sobject ConnectedApplication --record-type-id 0

# Or search for your app by name
sf force data query execute -q "SELECT Id, Name, Consumer_Key__c FROM ConnectedApplication WHERE Name = 'DataGuardian Pro'"
```

However, **Consumer Secret is usually NOT available via CLI** for security reasons - it's only shown once in the UI.

---

## Option 3: RECOMMENDED - Regenerate the Secret

This is the **most reliable** method:

### Steps:
1. Open your **DataGuardian Pro** Connected App in Salesforce
2. Find **CONSUMER DETAILS** section
3. Click **[Rotate Consumer Secret]** (or similar button)
4. Confirm the rotation
5. A **NEW secret** will be shown - copy it immediately
6. Use this new secret in DataGuardian Pro

---

## 🎯 Which Method Should You Use?

| Method | Difficulty | Success Rate | Notes |
|--------|-----------|--------------|-------|
| **[Show] Button** | Easy | ❌ Not working for you | Already tried |
| **Regenerate Secret** | Easy | ✅ 95%+ | Recommended! |
| **Salesforce CLI** | Hard | ⚠️ Limited access | Requires installation |
| **Salesforce API** | Very Hard | ⚠️ Complex | Not recommended |

---

## ✅ RECOMMENDATION: Try Regenerate First

1. Go to your app details page
2. Look for buttons like:
   - [Rotate Consumer Secret]
   - [Regenerate Secret]
   - [Reset]
   - [Manage Consumer Details]
3. Click it
4. Confirm
5. Copy your NEW secret

---

## 🚀 After Getting Secret

```bash
python GET_SALESFORCE_OAUTH_KEYS.py
```

Then test in DataGuardian Pro!

---

**Try the Regenerate method - it's the quickest fix!** ✅
