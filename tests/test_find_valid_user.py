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

def find_users_in_tenant():
    """Find users in the tenant that could be used as from_address."""
    print("🔍 Searching for users in your tenant...")
    
    try:
        access_token = get_access_token()
        
        # Get all users
        users_url = "https://graph.microsoft.com/v1.0/users"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(users_url, headers=headers)
        
        if response.status_code == 200:
            users_data = response.json()
            users = users_data.get('value', [])
            
            print(f"✅ Found {len(users)} users in your tenant:")
            print("-" * 60)
            
            valid_users = []
            for user in users:
                email = user.get('mail') or user.get('userPrincipalName')
                display_name = user.get('displayName', 'N/A')
                enabled = user.get('accountEnabled', False)
                
                status = "✅ Enabled" if enabled else "❌ Disabled"
                print(f"{email}")
                print(f"  Name: {display_name}")
                print(f"  Status: {status}")
                print()
                
                if enabled and email:
                    valid_users.append(email)
            
            print("=" * 60)
            print("📧 VALID EMAIL ADDRESSES FOR from_address:")
            for email in valid_users:
                print(f"  {email}")
            
            if valid_users:
                print(f"\n💡 Recommendation: Use one of these emails in your test_config.json")
                print(f"Current from_address: somekindoffiction@outlook.onmicrosoft.com")
                print(f"Try replacing with: {valid_users[0]}")
                
                # Offer to update config automatically
                update_config = input(f"\nWould you like me to update your config to use '{valid_users[0]}'? (y/n): ")
                if update_config.lower() == 'y':
                    update_config_file(valid_users[0])
            else:
                print("\n⚠️  No enabled users found. You may need to:")
                print("1. Create a user account in Azure AD")
                print("2. Assign appropriate licenses")
                
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

def update_config_file(new_from_address):
    """Update the config file with a new from_address."""
    config_path = Path(__file__).parent / 'config' / 'test_config.json'
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        old_address = config['from_address']
        config['from_address'] = new_from_address
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated config file!")
        print(f"Changed from_address: {old_address} → {new_from_address}")
        
    except Exception as e:
        print(f"❌ Failed to update config: {e}")

if __name__ == "__main__":
    print("👥 User Discovery Tool")
    print("="*50)
    find_users_in_tenant()
