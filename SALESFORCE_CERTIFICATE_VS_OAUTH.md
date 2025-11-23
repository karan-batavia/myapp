# 📋 Certificate vs Consumer Key/Secret - Which Do You Have?

## 🔍 What Did You Download?

### Option 1: You Downloaded a Certificate File (.cer, .pem, .pfx)
```
If you see files like:
- certificate.cer
- server.key
- salesforce.pem
- certificate.p12
```

**This is for CERTIFICATE-based authentication** (more complex)

### Option 2: You Copied Consumer Key & Secret (Text Codes)
```
If you have:
- Consumer Key: 3MVG9d8._XXXXXXXXXXXX... (80+ chars)
- Consumer Secret: 987654321XXXXXXXX... (40+ chars)
```

**This is for OAUTH authentication** (what DataGuardian Pro uses)

---

## ✅ Which One Do You Have?

**Answer these questions:**

1. Did you download a **FILE**? (certificate, key, etc.)
   - YES → You downloaded a certificate
   - NO → You have text credentials

2. Did you see a page with **[Show] [Copy] buttons**?
   - YES → You have OAuth credentials (Consumer Key/Secret)
   - NO → You have a certificate

3. Is what you got **text you can paste** or a **file on your computer**?
   - Text → OAuth credentials
   - File → Certificate

---

## 🎯 For DataGuardian Pro Testing

**You need: OAuth Credentials (Consumer Key & Secret)**

**NOT a certificate file**

---

## 📝 What to Do Next

### If You Have a Certificate File ❌
1. Go back to Salesforce
2. Create a NEW Connected App with OAuth enabled (not certificate)
3. Copy the Consumer Key & Secret (not download a file)
4. Use those text codes in DataGuardian Pro

### If You Have Consumer Key & Secret ✅
1. You're good!
2. Also get your Security Token from email
3. Come back ready to test

---

## 🔑 What DataGuardian Pro Needs

For Salesforce testing in DataGuardian Pro, you need:

```
✓ Username: vishaal05@agensics.com.sandbox
✓ Password: [your password]
✓ Consumer Key: [text code from OAuth, NOT a file]
✓ Consumer Secret: [text code from OAuth, NOT a file]
✓ Security Token: [24-char code from email]
```

**NOT a certificate file**

---

## ⚡ Quick Answer

**Did you get text like "3MVG9d8._XXXX..." and "987654321XXX..."?**
- YES → Perfect! That's what you need
- NO → You got the wrong thing, need to create OAuth app

---

**Tell me: What exactly did you download? (File or text credentials?)**
