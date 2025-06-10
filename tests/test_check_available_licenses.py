import os
import json
import requests
from pathlib import Path

def load_config():
    """Load the test configuration."""
    config_path = Path(__file__).parent / 'config' / 'test_config.json'
    with open(config_path, 'r') as f:
        return json.load(f)

def get_access_token():
    """Get access token for Microsoft Graph API."""
    config = load_config()
    
    token_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    response = requests.post(token_url, data=token_data)
    response.raise_for_status()
    return response.json().get('access_token')

def check_available_licenses():
    """Check what licenses are available in the tenant."""
    
    try:
        access_token = get_access_token()
        
        # Get organization info
        org_url = "https://graph.microsoft.com/v1.0/organization"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        org_response = requests.get(org_url, headers=headers)
        
        if org_response.status_code == 200:
            org_data = org_response.json()
            if org_data.get('value'):
                org_info = org_data['value'][0]
                print("🏢 Organization Info:")
                print(f"  Display Name: {org_info.get('displayName')}")
                print(f"  Domain: {org_info.get('verifiedDomains', [{}])[0].get('name', 'N/A')}")
        
        # Check subscribedSkus (available licenses)
        skus_url = "https://graph.microsoft.com/v1.0/subscribedSkus"
        
        skus_response = requests.get(skus_url, headers=headers)
        
        if skus_response.status_code == 200:
            skus_data = skus_response.json()
            skus = skus_data.get('value', [])
            
            print(f"\n📋 Available Licenses in Your Tenant:")
            print("-" * 60)
            
            if not skus:
                print("❌ No licenses found in your tenant")
                print("\n💡 This means:")
                print("1. You're using a free Azure AD tenant")
                print("2. No paid Office 365/Microsoft 365 subscriptions")
                print("3. Users won't have Exchange Online mailboxes")
                return False
            
            free_licenses = []
            paid_licenses = []
            
            for sku in skus:
                sku_part_number = sku.get('skuPartNumber', 'Unknown')
                consumed_units = sku.get('consumedUnits', 0)
                enabled_units = sku.get('prepaidUnits', {}).get('enabled', 0)
                
                service_plans = sku.get('servicePlans', [])
                has_exchange = any('EXCHANGE' in plan.get('servicePlanName', '') for plan in service_plans)
                
                license_info = {
                    'name': sku_part_number,
                    'consumed': consumed_units,
                    'available': enabled_units - consumed_units,
                    'has_exchange': has_exchange
                }
                
                if 'FREE' in sku_part_number.upper() or enabled_units == 0:
                    free_licenses.append(license_info)
                else:
                    paid_licenses.append(license_info)
                
                status = "✅ Available" if license_info['available'] > 0 else "❌ No units available"
                exchange_status = "📧 Email" if has_exchange else "❌ No Email"
                
                print(f"{sku_part_number}")
                print(f"  {status} ({license_info['available']} units)")
                print(f"  {exchange_status}")
                print()
            
            if paid_licenses:
                print("💰 You have paid licenses available!")
                print("Assign one to your user for email functionality.")
                return True
            else:
                print("💸 No paid licenses found.")
                print("Email functionality will likely not work without Exchange Online.")
                return False
                
        else:
            print(f"❌ Failed to get license info: {skus_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def suggest_free_alternatives():
    """Suggest free alternatives for newsletter functionality."""
    
    print("\n" + "="*60)
    print("🆓 FREE ALTERNATIVES FOR NEWSLETTER")
    print("="*60)
    
    print("\n1. 🎯 Use a Free Email Service API:")
    print("   - SendGrid (100 emails/day free)")
    print("   - Mailgun (100 emails/day free)")
    print("   - Amazon SES (with AWS free tier)")
    
    print("\n2. 🔄 Switch to Personal Microsoft Account:")
    print("   - Use your personal @outlook.com account")
    print("   - Register a new app in personal tenant")
    print("   - Limited to personal use")
    
    print("\n3. 📧 Use SMTP with Free Email:")
    print("   - Gmail SMTP (with app passwords)")
    print("   - Outlook.com SMTP")
    print("   - Yahoo SMTP")
    
    print("\n4. 🆓 Try Microsoft 365 Developer Program:")
    print("   - Get free Microsoft 365 E5 license for 90 days")
    print("   - Visit: developer.microsoft.com/microsoft-365/dev-program")
    print("   - Renewable if actively developing")
    
    print("\n5. 💡 Test Without License (Sometimes Works):")
    print("   - Try sending email anyway")
    print("   - Some basic functionality might work")

if __name__ == "__main__":
    print("🔍 License Availability Checker")
    print("="*50)
    
    has_licenses = check_available_licenses()
    
    if not has_licenses:
        suggest_free_alternatives()
        
        print("\n🧪 Want to try sending email without a license?")
        test_anyway = input("Test email functionality anyway? (y/n): ")
        
        if test_anyway.lower() == 'y':
            print("\nRunning basic email test...")
            import subprocess
            try:
                subprocess.run(['python3', 'test_final_check.py'], cwd='tests')
            except:
                print("Run: python3 tests/test_final_check.py")
