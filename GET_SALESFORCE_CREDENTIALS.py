#!/usr/bin/env python3
"""
Script to organize and save your Salesforce OAuth credentials
Run this in Python to create a safe file with all your credentials
"""

import json
import os
from datetime import datetime

def get_salesforce_credentials():
    """Collect all 5 Salesforce credentials from user input"""
    
    print("\n" + "="*60)
    print("SALESFORCE CREDENTIALS GATHERER")
    print("="*60)
    print("\nThis script will help you collect all 5 credentials needed")
    print("for DataGuardian Pro Salesforce testing.\n")
    
    credentials = {}
    
    # Credential 1: Username
    print("\n1️⃣  SALESFORCE USERNAME")
    print("   This should be your email with .sandbox")
    print("   Example: vishaal05@agensics.com.sandbox")
    username = input("   Enter your username: ").strip()
    credentials['username'] = username
    
    # Credential 2: Password
    print("\n2️⃣  SALESFORCE PASSWORD")
    print("   Your account password")
    password = input("   Enter your password: ").strip()
    credentials['password'] = password
    
    # Credential 3: Consumer Key
    print("\n3️⃣  CONSUMER KEY")
    print("   From Salesforce: Setup → Connected apps → Your app")
    print("   Starts with '3MVG9d8._' and is ~80 characters long")
    consumer_key = input("   Paste your Consumer Key: ").strip()
    credentials['consumer_key'] = consumer_key
    
    # Credential 4: Consumer Secret
    print("\n4️⃣  CONSUMER SECRET")
    print("   From Salesforce: Click [Show] then [Copy]")
    print("   Is ~40+ alphanumeric characters")
    consumer_secret = input("   Paste your Consumer Secret: ").strip()
    credentials['consumer_secret'] = consumer_secret
    
    # Credential 5: Security Token
    print("\n5️⃣  SECURITY TOKEN")
    print("   From email sent by Salesforce after Reset Security Token")
    print("   Is 24 alphanumeric characters")
    security_token = input("   Paste your Security Token: ").strip()
    credentials['security_token'] = security_token
    
    return credentials


def validate_credentials(creds):
    """Validate that all credentials are provided"""
    
    required_fields = [
        'username',
        'password', 
        'consumer_key',
        'consumer_secret',
        'security_token'
    ]
    
    print("\n" + "="*60)
    print("VALIDATING CREDENTIALS")
    print("="*60)
    
    all_valid = True
    for field in required_fields:
        if field in creds and creds[field]:
            print(f"✓ {field.upper().replace('_', ' ')}: Provided")
        else:
            print(f"✗ {field.upper().replace('_', ' ')}: MISSING")
            all_valid = False
    
    return all_valid


def save_credentials(creds):
    """Save credentials to a Python file for easy use"""
    
    filename = "salesforce_credentials.py"
    
    content = '''"""
Salesforce OAuth Credentials for DataGuardian Pro
Generated: ''' + datetime.now().isoformat() + '''
"""

SALESFORCE_CONFIG = {
    "username": "''' + creds['username'] + '''",
    "password": "''' + creds['password'] + '''",
    "consumer_key": "''' + creds['consumer_key'] + '''",
    "consumer_secret": "''' + creds['consumer_secret'] + '''",
    "security_token": "''' + creds['security_token'] + '''",
    "sandbox": True,
    "api_version": "v58.0"
}

# Usage in Python:
# from salesforce_credentials import SALESFORCE_CONFIG
# from services.salesforce_connector import SalesforceConnector, SalesforceConfig
#
# config = SalesforceConfig(**SALESFORCE_CONFIG)
# connector = SalesforceConnector(config)
# if connector.authenticate():
#     print("✓ Connected to Salesforce!")
'''
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"\n✓ Credentials saved to: {filename}")
    return filename


def display_credentials_summary(creds):
    """Display a summary of the credentials"""
    
    print("\n" + "="*60)
    print("CREDENTIALS SUMMARY")
    print("="*60)
    print(f"\nUsername:          {creds['username']}")
    print(f"Password:          {'*' * len(creds['password'])}")
    print(f"Consumer Key:      {creds['consumer_key'][:20]}...{creds['consumer_key'][-10:]}")
    print(f"Consumer Secret:   {creds['consumer_secret'][:20]}...{creds['consumer_secret'][-10:]}")
    print(f"Security Token:    {creds['security_token'][:10]}...{creds['security_token'][-5:]}")
    
    print("\n" + "="*60)
    print("READY FOR TESTING!")
    print("="*60)
    print("\nNext steps:")
    print("1. Open DataGuardian Pro at http://localhost:5000")
    print("2. Go to: Scan Manager → Enterprise Connector → Salesforce CRM")
    print("3. Fill in the form with these credentials")
    print("4. Click 'Connect to Salesforce'")
    print("5. Select objects to scan (Accounts, Contacts, Leads)")
    print("6. Run the PII scan!")


def main():
    """Main function"""
    
    try:
        # Collect credentials
        credentials = get_salesforce_credentials()
        
        # Validate
        if not validate_credentials(credentials):
            print("\n❌ Some credentials are missing. Please run the script again.")
            return
        
        # Save
        save_credentials(credentials)
        
        # Display summary
        display_credentials_summary(credentials)
        
        print("\n✓ Script complete!")
        
    except KeyboardInterrupt:
        print("\n\n❌ Script interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
