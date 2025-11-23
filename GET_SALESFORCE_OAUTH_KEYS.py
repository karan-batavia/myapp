#!/usr/bin/env python3
"""
Simple script to collect Consumer Key & Secret from Salesforce Connected App
Run this script and follow the prompts to get your OAuth credentials
"""

def get_consumer_key_and_secret():
    """Collect Consumer Key and Consumer Secret"""
    
    print("\n" + "="*70)
    print("SALESFORCE CONSUMER KEY & SECRET EXTRACTOR")
    print("="*70)
    
    print("\n📍 STEP-BY-STEP GUIDE TO GET YOUR OAUTH CREDENTIALS:\n")
    
    print("1. Go to your Salesforce account: https://login.salesforce.com")
    print("2. Click 'Setup' (top right)")
    print("3. In left menu, click: Manage apps → Connected apps")
    print("4. Find your 'DataGuardian Pro' app")
    print("5. Click on the app name to open it")
    print("6. Scroll down to find 'CONSUMER DETAILS' section")
    print("7. You'll see:")
    print("   - Consumer Key (starts with 3MVG9d8._)")
    print("   - Consumer Secret (hidden with dots)")
    print("8. For Consumer Secret, click [Show] to reveal it")
    print("\n" + "="*70)
    
    input("\n⏸️  Press ENTER when you're ready to paste your credentials...")
    
    print("\n")
    
    # Get Consumer Key
    print("3️⃣  CONSUMER KEY")
    print("   Look for the field labeled 'Consumer Key' in CONSUMER DETAILS section")
    print("   It looks like: 3MVG9d8._P1ZBa3nnHu2W8.Hm1tUqyb4CJ...")
    print("   Copy it and paste below:\n")
    
    consumer_key = input("   Paste Consumer Key: ").strip()
    
    if not consumer_key:
        print("   ❌ Consumer Key is empty!")
        return None, None
    
    if not consumer_key.startswith("3MVG"):
        print("   ⚠️  Warning: Consumer Key might be incorrect (should start with 3MVG)")
    
    # Get Consumer Secret
    print("\n4️⃣  CONSUMER SECRET")
    print("   Look for the field labeled 'Consumer Secret' in CONSUMER DETAILS section")
    print("   First, click the [Show] button to reveal the hidden code")
    print("   Then copy it and paste below:\n")
    
    consumer_secret = input("   Paste Consumer Secret: ").strip()
    
    if not consumer_secret:
        print("   ❌ Consumer Secret is empty!")
        return None, None
    
    return consumer_key, consumer_secret


def save_to_file(consumer_key, consumer_secret):
    """Save credentials to a simple text file"""
    
    filename = "salesforce_oauth_keys.txt"
    
    content = f"""SALESFORCE OAUTH CREDENTIALS
Generated: {__import__('datetime').datetime.now().isoformat()}

CONSUMER KEY:
{consumer_key}

CONSUMER SECRET:
{consumer_secret}

═══════════════════════════════════════════════════════════

READY TO USE IN DATAGUARDIAN PRO:

1. Open DataGuardian Pro: http://localhost:5000
2. Go to: Scan Manager → Enterprise Connector → Salesforce CRM
3. Fill in the form:
   - Username: vishaal05@agensics.com.sandbox
   - Password: [your password]
   - Consumer Key: {consumer_key[:50]}...
   - Consumer Secret: {consumer_secret[:50]}...
   - Security Token: [from email]
4. Click "Connect to Salesforce"
5. Select objects to scan and run PII analysis!

═══════════════════════════════════════════════════════════
"""
    
    with open(filename, 'w') as f:
        f.write(content)
    
    return filename


def display_summary(consumer_key, consumer_secret):
    """Display what was collected"""
    
    print("\n" + "="*70)
    print("✅ CREDENTIALS COLLECTED!")
    print("="*70)
    
    print(f"\n✓ Consumer Key:")
    print(f"  {consumer_key[:30]}...{consumer_key[-20:]}")
    
    print(f"\n✓ Consumer Secret:")
    print(f"  {consumer_secret[:30]}...{consumer_secret[-20:]}")
    
    print("\n" + "="*70)
    print("SAVED TO: salesforce_oauth_keys.txt")
    print("="*70)
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Get your Security Token from Salesforce email")
    print("   2. Open DataGuardian Pro at http://localhost:5000")
    print("   3. Go to: Scan Manager → Enterprise Connector → Salesforce CRM")
    print("   4. Fill in all 5 fields:")
    print("      - Username: vishaal05@agensics.com.sandbox")
    print("      - Password: [your password]")
    print("      - Consumer Key: (from above)")
    print("      - Consumer Secret: (from above)")
    print("      - Security Token: (from email)")
    print("   5. Click 'Connect to Salesforce'")
    print("   6. Start scanning for PII!")


def main():
    """Main function"""
    
    try:
        # Collect credentials
        consumer_key, consumer_secret = get_consumer_key_and_secret()
        
        if not consumer_key or not consumer_secret:
            print("\n❌ Could not get credentials. Please try again.")
            return
        
        # Save to file
        filename = save_to_file(consumer_key, consumer_secret)
        
        # Display summary
        display_summary(consumer_key, consumer_secret)
        
        print("\n✓ DONE! Credentials saved to:", filename)
        
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
