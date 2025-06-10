import os
import json
import requests
from datetime import datetime, timezone
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

def try_direct_email_send():
    """Try sending email with your existing setup using different methods."""
    config = load_config()
    
    print("🔧 Fixing Your Current Setup")
    print("="*40)
    print("No new signups, no trials, just making what you have work.")
    
    try:
        access_token = get_access_token()
        
        # Method 1: Try sending without specifying from address
        print("\n📧 Method 1: Application-level sending...")
        
        email_msg = {
            'message': {
                'subject': 'Newsletter Test - Working Now',
                'body': {
                    'contentType': 'HTML',
                    'content': '<h2>Success!</h2><p>Your newsletter system is working.</p>'
                },
                'toRecipients': [
                    {'emailAddress': {'address': config['test_recipient']}}
                ]
            }
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Try different endpoints
        endpoints = [
            f"https://graph.microsoft.com/v1.0/users/{config['from_address']}/sendMail",
            f"https://graph.microsoft.com/beta/users/{config['from_address']}/sendMail"
        ]
        
        for endpoint in endpoints:
            print(f"Trying: {endpoint.split('/')[-2]}...")
            response = requests.post(endpoint, headers=headers, data=json.dumps(email_msg))
            
            if response.status_code == 202:
                print("✅ SUCCESS! Email sent!")
                return True
            elif response.status_code == 401:
                print("❌ 401 - Authentication issue")
            elif response.status_code == 403:
                print("❌ 403 - Permission issue")
            else:
                print(f"❌ {response.status_code}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_app_permissions():
    """Check what permissions your app actually has."""
    
    print("\n🔍 Checking Your App Permissions...")
    
    try:
        access_token = get_access_token()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Check what we can access
        me_response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        print(f"Can access /me: {me_response.status_code}")
        
        users_response = requests.get("https://graph.microsoft.com/v1.0/users", headers=headers)
        print(f"Can access /users: {users_response.status_code}")
        
        if users_response.status_code == 200:
            users_data = users_response.json()
            users = users_data.get('value', [])
            print(f"Found {len(users)} users in tenant")
            
            for user in users:
                upn = user.get('userPrincipalName')
                mail_enabled = user.get('mailEnabled')
                account_enabled = user.get('accountEnabled')
                print(f"  {upn}: mailEnabled={mail_enabled}, accountEnabled={account_enabled}")
        
    except Exception as e:
        print(f"Permission check failed: {e}")

def simple_working_solution():
    """Provide the simplest working solution."""
    
    print("\n🎯 SIMPLE SOLUTION")
    print("="*30)
    print("Your setup should work. The issue might be:")
    print("1. User needs to be mail-enabled")
    print("2. App permissions need adjustment")
    print("3. Or we use a different approach")
    
    print("\n💡 Let's check your app registration permissions:")
    print("Go to Azure Portal → App registrations → Your app → API permissions")
    print("Make sure you have:")
    print("- Mail.Send (Application)")
    print("- User.Read.All (Application)")
    print("- Mail.ReadWrite (Application)")
    
    print("\nThen click 'Grant admin consent'")
    
    print("\n🔄 Or we can use your personal Outlook account directly")
    print("This requires NO additional setup - just use existing email")

if __name__ == "__main__":
    print("🛠️ FIXING YOUR EXISTING SETUP")
    print("="*50)
    print("Let's make what you already have work!")
    
    # Check permissions first
    check_app_permissions()
    
    # Try to send email
    success = try_direct_email_send()
    
    if not success:
        simple_working_solution()
        
        print("\n🤔 Want me to just make this work with your @outlook.com account?")
        print("This avoids all the Azure complexity and just works.")
        
        choice = input("Use simple Outlook.com approach? (y/n): ")
        if choice.lower() == 'y':
            print("\n✅ I'll create a simple version using your Outlook account...")
            print("This will be completely free and work immediately.")
