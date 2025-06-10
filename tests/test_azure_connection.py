import os
import json
import requests
from pathlib import Path

def load_config():
    """Load the test configuration."""
    config_path = Path(__file__).parent / 'config' / 'test_config.json'
    with open(config_path, 'r') as f:
        return json.load(f)

def test_token_acquisition():
    """Test getting an access token."""
    config = load_config()
    
    print("🔍 Testing Azure Authentication...")
    print(f"Client ID: {config['client_id']}")
    print(f"Tenant ID: {config['tenant_id']}")
    print(f"From Address: {config['from_address']}")
    
    token_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    print(f"\n📞 Making token request to: {token_url}")
    
    try:
        response = requests.post(token_url, data=token_data)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            print("✅ Successfully obtained access token!")
            print(f"Token type: {token_data.get('token_type')}")
            print(f"Expires in: {token_data.get('expires_in')} seconds")
            print(f"Scope: {token_data.get('scope')}")
            return access_token
        else:
            print("❌ Failed to get access token")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
                
                # Common error interpretations
                if 'invalid_client' in str(error_data):
                    print("\n🔧 This usually means:")
                    print("- Client ID or Client Secret is incorrect")
                    print("- App registration doesn't exist or is disabled")
                
                elif 'unauthorized_client' in str(error_data):
                    print("\n🔧 This usually means:")
                    print("- App doesn't have permission for client_credentials flow")
                    print("- App registration needs 'Application permissions' not 'Delegated permissions'")
                
            except:
                print(f"Raw response: {response.text}")
            
            return None
            
    except Exception as e:
        print(f"❌ Exception during token request: {e}")
        return None

def test_user_exists(access_token):
    """Test if the from_address user exists and is accessible."""
    config = load_config()
    
    print(f"\n🔍 Testing user existence: {config['from_address']}")
    
    user_url = f"https://graph.microsoft.com/v1.0/users/{config['from_address']}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(user_url, headers=headers)
        print(f"User lookup status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User found!")
            print(f"Display Name: {user_data.get('displayName')}")
            print(f"User Principal Name: {user_data.get('userPrincipalName')}")
            print(f"Mail: {user_data.get('mail')}")
            return True
        else:
            print("❌ User not found or not accessible")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
                
                if response.status_code == 404:
                    print("\n🔧 This usually means:")
                    print("- The email address doesn't exist in your tenant")
                    print("- The user account is disabled")
                    print("- You don't have permission to read user information")
                
                elif response.status_code == 403:
                    print("\n🔧 This usually means:")
                    print("- Your app needs 'User.Read.All' permission")
                    print("- Admin consent hasn't been granted")
                
            except:
                print(f"Raw response: {response.text}")
            
            return False
            
    except Exception as e:
        print(f"❌ Exception during user lookup: {e}")
        return False

def test_permissions(access_token):
    """Test what permissions the token actually has."""
    print(f"\n🔍 Testing token permissions...")
    
    # Try to access the Graph API to see what we can do
    me_url = "https://graph.microsoft.com/v1.0/me"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(me_url, headers=headers)
        print(f"Graph API /me endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Can access Graph API with application permissions")
        else:
            print("⚠️  Cannot access /me endpoint (this is normal for app-only tokens)")
            
    except Exception as e:
        print(f"Exception: {e}")

def suggest_fixes():
    """Suggest potential fixes based on common issues."""
    print("\n" + "="*60)
    print("🔧 TROUBLESHOOTING GUIDE")
    print("="*60)
    
    print("\n1. Azure App Registration Setup:")
    print("   - Go to Azure Portal > App registrations")
    print("   - Find your app: 48b70c39-b77e-4c73-a490-e2d86e1bd02b")
    print("   - Check 'API permissions' section")
    
    print("\n2. Required Permissions (Application type, not Delegated):")
    print("   ✓ Microsoft Graph > Mail.Send")
    print("   ✓ Microsoft Graph > Files.Read.All")
    print("   ✓ Microsoft Graph > User.Read.All")
    
    print("\n3. Grant Admin Consent:")
    print("   - In API permissions, click 'Grant admin consent for [tenant]'")
    print("   - All permissions should show green checkmarks")
    
    print("\n4. Check User Account:")
    print("   - Verify somekindoffiction@outlook.onmicrosoft.com exists")
    print("   - Check if it's enabled and has a mailbox")
    print("   - Try logging in with this account manually")
    
    print("\n5. Alternative from_address options:")
    print("   - Try your own email if it's in the same tenant")
    print("   - For @outlook.onmicrosoft.com, the user must exist in Azure AD")

if __name__ == "__main__":
    print("🚀 Azure Connection Diagnostic Tool")
    print("="*50)
    
    # Test 1: Get access token
    access_token = test_token_acquisition()
    
    if access_token:
        # Test 2: Check if user exists
        user_exists = test_user_exists(access_token)
        
        # Test 3: Check permissions
        test_permissions(access_token)
        
        if not user_exists:
            print("\n💡 Since the user doesn't exist, try updating your config:")
            print("Replace 'from_address' with an email that exists in your tenant")
    
    # Always show troubleshooting guide
    suggest_fixes()
