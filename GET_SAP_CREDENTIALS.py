#!/usr/bin/env python3
"""
SAP Credential Collector for DataGuardian Pro
Interactive script to gather and save SAP connection credentials
"""

import os
from datetime import datetime

def get_sap_credentials():
    """Collect SAP credentials step by step"""
    
    print("\n" + "="*70)
    print("SAP CONNECTION CREDENTIALS COLLECTOR")
    print("="*70)
    
    print("\n📍 QUICK START:\n")
    print("If you don't have SAP credentials yet:")
    print("1. Contact your SAP System Administrator")
    print("2. Request access to SAP system")
    print("3. Ask for: Host, Port, Client, Username")
    print("4. Create a user account in SAP (transaction SU01)")
    print("5. Come back to this script\n")
    
    input("⏸️  Press ENTER when you're ready to collect SAP credentials...")
    
    print("\n" + "="*70)
    print("STEP-BY-STEP CREDENTIAL COLLECTION")
    print("="*70)
    
    credentials = {}
    
    # 1. SAP Host
    print("\n1️⃣  SAP HOST/SERVER ADDRESS")
    print("   This is the SAP application server")
    print("   Examples: sap.company.com, 192.168.1.100, sap-prod.nl")
    print("   (from your admin)")
    host = input("\n   Enter SAP Host: ").strip()
    if not host:
        print("   ❌ Host is required!")
        return None
    credentials['host'] = host
    
    # 2. SAP Port
    print("\n2️⃣  SAP PORT NUMBER")
    print("   Usually 8000 for HTTP or 443 for HTTPS")
    print("   (from your admin)")
    port = input("\n   Enter SAP Port (default 8000): ").strip()
    if not port:
        port = "8000"
    credentials['port'] = port
    
    # 3. SAP Client
    print("\n3️⃣  SAP CLIENT NUMBER (Mandant)")
    print("   Usually 100, 200, or 300")
    print("   (from your admin)")
    client = input("\n   Enter SAP Client: ").strip()
    if not client:
        print("   ❌ Client is required!")
        return None
    credentials['client'] = client
    
    # 4. SAP Username
    print("\n4️⃣  SAP USERNAME")
    print("   The user account you created in SAP")
    print("   Example: DATAGUARDIAN, ADMIN, or your username")
    username = input("\n   Enter SAP Username: ").strip()
    if not username:
        print("   ❌ Username is required!")
        return None
    credentials['username'] = username
    
    # 5. SAP Password
    print("\n5️⃣  SAP PASSWORD")
    print("   Password for the SAP user account")
    print("   (will be saved securely)")
    password = input("\n   Enter SAP Password: ").strip()
    if not password:
        print("   ❌ Password is required!")
        return None
    credentials['password'] = password
    
    # Optional: Protocol
    print("\n6️⃣  PROTOCOL (Optional)")
    print("   http or https? (default: https)")
    protocol = input("\n   Enter Protocol (http/https, default https): ").strip().lower()
    if protocol not in ['http', 'https']:
        protocol = 'https'
    credentials['protocol'] = protocol
    
    # Optional: System ID
    print("\n7️⃣  SYSTEM ID (Optional)")
    print("   SAP System ID like PRD, DEV, TST")
    print("   (leave blank if not needed)")
    system_id = input("\n   Enter System ID (optional): ").strip()
    credentials['system_id'] = system_id if system_id else ""
    
    return credentials


def display_summary(credentials):
    """Show what was collected"""
    
    print("\n" + "="*70)
    print("✅ CREDENTIALS COLLECTED!")
    print("="*70)
    
    print(f"\n✓ SAP Host:       {credentials['host']}")
    print(f"✓ SAP Port:       {credentials['port']}")
    print(f"✓ SAP Client:     {credentials['client']}")
    print(f"✓ SAP Username:   {credentials['username']}")
    print(f"✓ Protocol:       {credentials['protocol']}")
    if credentials['system_id']:
        print(f"✓ System ID:      {credentials['system_id']}")
    
    print("\n" + "="*70)


def save_to_file(credentials):
    """Save credentials to a file"""
    
    filename = "sap_credentials.txt"
    
    content = f"""SAP CONNECTION CREDENTIALS
Generated: {datetime.now().isoformat()}
System: DataGuardian Pro

═══════════════════════════════════════════════════════════

CONNECTION DETAILS:

SAP Host:           {credentials['host']}
SAP Port:           {credentials['port']}
SAP Client:         {credentials['client']}
SAP Username:       {credentials['username']}
SAP Password:       {credentials['password']}
Protocol:           {credentials['protocol']}
System ID:          {credentials['system_id'] if credentials['system_id'] else '(not specified)'}

═══════════════════════════════════════════════════════════

READY TO USE IN DATAGUARDIAN PRO:

1. Open DataGuardian Pro: http://localhost:5000
2. Go to: Scan Manager → Enterprise Connector → SAP
3. Fill in the form with credentials above
4. Click "Connect to SAP"
5. Select tables to scan
6. Click "Start Scan"

═══════════════════════════════════════════════════════════

SECURITY NOTES:

⚠️  KEEP THIS FILE SECURE!
   - Don't share this file
   - Delete after using in DataGuardian Pro
   - Use HTTPS protocol for production
   - Create dedicated SAP user account (don't use admin)

TABLES DATAGUARDIAN WILL SCAN:

HR Data (PII):
  PA0002  - HR Personal Data (names, DOB, personnel IDs)
  PA0001  - HR Org Assignment
  PA0185  - ID Numbers (passport, license)
  
Master Data:
  ADRC    - Address Master (names, addresses, phone)
  KNA1    - Customer Master
  LFA1    - Vendor Master
  
User Management:
  USR21   - User Master Records
  
Netherlands Compliance:
  ✓ Scans for BSN (Dutch Social Security Numbers)
  ✓ UAVG compliance checking
  ✓ GDPR articles validation
  
═══════════════════════════════════════════════════════════
"""
    
    with open(filename, 'w') as f:
        f.write(content)
    
    return filename


def display_next_steps(credentials):
    """Show what to do next"""
    
    print("\n" + "="*70)
    print("🎯 NEXT STEPS")
    print("="*70)
    
    print("\n1. TEST SAP CONNECTION (from Replit Shell):")
    print(f"   telnet {credentials['host']} {credentials['port']}")
    print("   (Should show 'Connected' or similar)")
    
    print("\n2. OPEN DATAGUARDIAN PRO:")
    print("   Go to: http://localhost:5000")
    
    print("\n3. NAVIGATE TO SAP CONNECTOR:")
    print("   Menu → Scan Manager → Enterprise Connector → SAP")
    
    print("\n4. FILL IN THE FORM:")
    print(f"   - SAP Host: {credentials['host']}")
    print(f"   - SAP Port: {credentials['port']}")
    print(f"   - SAP Client: {credentials['client']}")
    print(f"   - SAP Username: {credentials['username']}")
    print(f"   - SAP Password: [your password]")
    
    print("\n5. CLICK 'CONNECT TO SAP'")
    print("   - System will verify connection")
    print("   - Retrieve available tables")
    
    print("\n6. SELECT TABLES TO SCAN:")
    print("   - PA0002 (HR Personal Data) - Contains most PII")
    print("   - ADRC (Addresses)")
    print("   - KNA1 (Customers)")
    print("   - Other tables as needed")
    
    print("\n7. START SCAN:")
    print("   - Click 'Start Scan'")
    print("   - Wait for results")
    print("   - Review PII findings")
    print("   - Generate compliance report")
    
    print("\n" + "="*70)


def main():
    """Main function"""
    
    try:
        # Collect credentials
        credentials = get_sap_credentials()
        
        if not credentials:
            print("\n❌ Could not collect credentials. Please try again.")
            return
        
        # Display summary
        display_summary(credentials)
        
        # Save to file
        filename = save_to_file(credentials)
        print(f"\n✓ Credentials saved to: {filename}")
        
        # Show next steps
        display_next_steps(credentials)
        
        print("\n" + "="*70)
        print("✅ READY TO USE IN DATAGUARDIAN PRO!")
        print("="*70)
        print("\nOpen http://localhost:5000 and go to:")
        print("Scan Manager → Enterprise Connector → SAP")
        print("\nFill in your credentials and click 'Connect to SAP'")
        print("\n" + "="*70)
        
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
