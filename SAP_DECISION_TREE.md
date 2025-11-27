# 🌳 SAP Setup - Decision Tree

Follow this flowchart to figure out what to do.

---

## START HERE

```
DO YOU HAVE ACCESS TO SAP?
(Can you log into SAP at work?)

├─ YES → Go to: "I Have SAP Access"
├─ NO → Go to: "I Don't Have SAP"  
└─ MAYBE → Go to: "Finding Out"
```

---

## 🟢 "I Have SAP Access"

You can already log into SAP. Great!

```
NEXT QUESTION:
Are you a SAP Administrator or IT person?

├─ YES → You likely already know these details
│        Follow: SAP_CREDENTIALS_BEGINNER_GUIDE.md
│        Section: "I Have Access to SAP"
│
└─ NO → You need to ask IT for details
        Do this:
        
        1. Send email to SAP Admin / IT:
           Subject: SAP server details for PII scanning
           
           "Hi,
            I need SAP connection details for 
            DataGuardian Pro PII compliance scanning.
            
            Can you provide:
            - SAP server address (host/IP)
            - SAP port number
            - SAP client number
            - A technical user account?
            
            Thanks!"
        
        2. Wait for response with 4 details:
           ✓ Host
           ✓ Port
           ✓ Client
           ✓ Username
           
        3. Use your existing SAP password
        
        4. Go to: "I Have All 5 Credentials" section
```

---

## 🔴 "I Don't Have SAP"

You don't use SAP or your company doesn't have it.

```
NEXT QUESTION:
Do you want to set up SAP for testing/learning?

├─ YES → Set up free SAP trial
│        
│        1. Go to: https://www.sap.com/cdc/en/marketing/trial.html
│        2. Click: "Start Your Trial"
│        3. Select: "ERP" or "S/4HANA"
│        4. Create account with your email
│        5. You get demo SAP system:
│           - Host: auto-provided
│           - Port: 443 (HTTPS)
│           - Client: 100
│           - Username: Your email
│           - Password: You create
│        6. Takes 10-15 minutes
│        7. Then follow: "I Have All 5 Credentials"
│
└─ NO → Skip SAP for now
        
        DataGuardian Pro also scans:
        ✓ Databases
        ✓ Code repositories
        ✓ Files and documents
        ✓ Websites
        
        Use these scanners instead
```

---

## ❓ "Finding Out"

You're not sure if you have SAP.

```
DO THIS:

1. Ask your manager or IT:
   "Does our company use SAP?"
   
2. Look for SAP on your computer:
   - SAP Logon Pad (desktop icon?)
   - SAP Fiori (web portal?)
   - Check "All Programs" list
   
3. Check company systems:
   - Finance/HR software
   - Employee portal
   - IT documentation
   
4. Search email:
   - Look for "SAP login" or "SAP credentials"
   - Check onboarding emails
   
ONCE YOU KNOW:

If company has SAP:
  → Go to: "I Have SAP Access"
  
If company doesn't have SAP:
  → Go to: "I Don't Have SAP"
```

---

## ✅ "I Have All 5 Credentials"

Perfect! You're ready.

```
WHAT TO DO NOW:

1. Verify the credentials work:
   
   Open terminal/command prompt:
   telnet [YOUR-SAP-HOST] [YOUR-PORT]
   
   Example:
   telnet sap.company.com 8000
   
   Expected: "Connected"
   Problem: "Connection refused"
   
2. If "Connected" → Continue
   If error → Ask IT to check firewall

3. Collect credentials in Python script:
   
   python GET_SAP_CREDENTIALS.py
   
   The script will:
   - Ask for each of 5 credentials
   - Verify they're correct
   - Save to sap_credentials.txt

4. Open DataGuardian Pro:
   
   http://localhost:5000

5. Go to menu:
   
   Scan Manager 
   → Enterprise Connector 
   → SAP

6. Fill in form with your 5 credentials

7. Click: "Connect to SAP"

8. Select tables to scan

9. Click: "Start Scan"

10. Review PII findings

11. Generate compliance report
```

---

## 🎯 Quick Reference

### If You're a Regular Employee:
```
1. Ask manager: "Who is our SAP admin?"
2. Send email with credential request
3. Wait for response
4. Use credentials in DataGuardian Pro
```

### If You're IT/Admin:
```
1. You probably already know these
2. If not, check SAP system directly
3. Create technical user if needed
4. Provide to requestor
```

### If Company Doesn't Have SAP:
```
1. Either:
   - Set up free SAP trial
   - Skip SAP, use other scanners
   - Come back later if you get SAP
```

### If You Get Stuck:
```
Contact:
- Your SAP Administrator
- IT Helpdesk
- Your Manager
- DataGuardian Pro Support

Email template in: SAP_CREDENTIALS_BEGINNER_GUIDE.md
```

---

## 📊 Credential Checklist

Once you have all 5:

```
☐ SAP Host:           _____________________
☐ SAP Port:           _____________________
☐ SAP Client:         _____________________
☐ SAP Username:       _____________________
☐ SAP Password:       _____________________

TEST:
☐ Telnet works:       Connected / Error
☐ Email to IT sent:   Yes / No
☐ Response received:  Yes / No

READY FOR:
☐ python GET_SAP_CREDENTIALS.py
☐ DataGuardian Pro SAP connector
☐ Start scanning
```

---

## 🚀 Fast Path

### If You Have SAP and Know What to Do:
```
1. python GET_SAP_CREDENTIALS.py
2. Enter your 5 credentials
3. http://localhost:5000
4. Scan Manager → Enterprise Connector → SAP
5. Fill in credentials
6. Connect and scan
```

### If You're New to SAP:
```
1. Ask IT for:
   - SAP host
   - SAP port
   - SAP client
   - SAP username
   - (Use your normal password)
2. Run credential collector
3. Connect in DataGuardian Pro
4. Start scanning
```

### If Your Company Doesn't Have SAP:
```
1. Set up free SAP trial (10 min)
   OR
2. Use other DataGuardian scanners
   (Database, Code, Website, etc.)
```

---

## ❌ Troubleshooting Paths

```
PROBLEM: "Connection refused when testing telnet"
└─ Solution: 
   - Ask IT if SAP server is up
   - Verify port number
   - Check firewall allows your IP
   - Try different port (8001, 8002, etc.)

PROBLEM: "Authentication fails in DataGuardian"
└─ Solution:
   - Verify username is case-sensitive
   - Confirm password is correct
   - Ask IT if user has RFC permissions
   - Try with admin account first

PROBLEM: "Can't find SAP host/port/client"
└─ Solution:
   - Send email to IT
   - Check company wiki/docs
   - Look at SAP Logon Pad properties
   - Ask colleague who uses SAP

PROBLEM: "Company doesn't have SAP"
└─ Solution:
   - Set up free trial
   - Use other scanners
   - Come back later
```

---

## 📞 When to Ask for Help

```
Email IT when:
- You don't know SAP host
- You don't know SAP port
- You don't know SAP client
- You can't create user account
- You get "Connection refused" error

Tell them:
"I need to set up SAP PII compliance scanning.
I need: Host, Port, Client, and a technical user.
Can you help?"

They should give you:
✓ Host: sap.company.com or 192.168.x.x
✓ Port: 8000 or 443
✓ Client: 100
✓ Username: For new account
```

---

**Ready to start? Pick your path above and follow the steps!** 🚀
