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

def get_detailed_user_info():
    """Get detailed information about the user."""
    print("🔍 Getting detailed user information...")
    
    try:
        access_token = get_access_token()
        
        # The user we found
        user_email = "somekindoffiction_outlook.com#EXT#@somekindoffictionoutlook.onmicrosoft.com"
        
        # Get detailed user info
        user_url = f"https://graph.microsoft.com/v1.0/users/{user_email}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"Checking user: {user_email}")
        response = requests.get(user_url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            
            print("✅ User found! Details:")
            print(f"  Display Name: {user_data.get('displayName')}")
            print(f"  User Principal Name: {user_data.get('userPrincipalName')}")
            print(f"  Mail: {user_data.get('mail')}")
            print(f"  Account Enabled: {user_data.get('accountEnabled')}")
            print(f"  User Type: {user_data.get('userType')}")
            print(f"  Creation Type: {user_data.get('creationType')}")
            print(f"  External User State: {user_data.get('externalUserState')}")
            print(f"  External User State Change: {user_data.get('externalUserStateChangeDateTime')}")
            
            # Check if user has mailbox
            print(f"  Mailbox Settings:")
            print(f"    Mail Enabled: {user_data.get('mailEnabled')}")
            print(f"    Proxy Addresses: {user_data.get('proxyAddresses', [])}")
            
            return user_data
        else:
            print(f"❌ Failed to get user details: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_email_with_external_user():
    """Test sending email with the external user account."""
    config = load_config()
    user_email = "somekindoffiction_outlook.com#EXT#@somekindoffictionoutlook.onmicrosoft.com"
    
    print(f"\n📧 Testing email send with external user...")
    
    try:
        access_token = get_access_token()
        
        # Try to send email
        send_mail_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/sendMail"
        
        email_content = """
        <html>
            <body>
                <h2>🧪 External User Email Test</h2>
                <p>Testing email from external user account.</p>
                <p>If you receive this, the external user can send emails!</p>
            </body>
        </html>
        """
        
        email_msg = {
            'message': {
                'subject': '🧪 External User Test Email',
                'body': {
                    'contentType': 'HTML',
                    'content': email_content
                },
                'toRecipients': [
                    {'emailAddress': {'address': config['test_recipient']}}
                ]
            },
            'saveToSentItems': 'true'
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"Sending to: {config['test_recipient']}")
        response = requests.post(send_mail_url, headers=headers, data=json.dumps(email_msg))
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 202:
            print("✅ Email sent successfully from external user!")
            print("🎉 Your newsletter system should work!")
            
            # Update config with correct email
            update_config_file(user_email)
            return True
        else:
            print("❌ Failed to send email from external user")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
                
                if 'MailboxNotEnabledForRESTAPI' in str(error_data):
                    print("\n🔧 This user doesn't have a mailbox enabled.")
                    print("External users often can't send emails.")
                elif 'Forbidden' in str(error_data):
                    print("\n🔧 External user may not have email sending permissions.")
                
            except:
                print(f"Raw error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def create_internal_user():
    """Try to create an internal user account."""
    print("\n🔧 Attempting to create internal user...")
    
    try:
        access_token = get_access_token()
        
        # Create user payload
        new_user = {
            "accountEnabled": True,
            "displayName": "Some Kind of Fiction Newsletter",
            "mailNickname": "somekindoffiction",
            "userPrincipalName": "somekindoffiction@somekindoffictionoutlook.onmicrosoft.com",
            "passwordProfile": {
                "forceChangePasswordNextSignIn": False,
                "password": "TempPass123!"
            },
            "usageLocation": "US"
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        create_url = "https://graph.microsoft.com/v1.0/users"
        response = requests.post(create_url, headers=headers, data=json.dumps(new_user))
        
        if response.status_code == 201:
            user_data = response.json()
            new_email = user_data.get('userPrincipalName')
            print(f"✅ Created internal user: {new_email}")
            
            # Update config
            update_config_file(new_email)
            
            print("🎉 Now try sending a test email!")
            return new_email
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
                
                if 'insufficient privileges' in str(error_data).lower():
                    print("🔧 Your app needs User.ReadWrite.All permission to create users")
                elif 'already exists' in str(error_data).lower():
                    print("🔧 User already exists - try the existing one")
                
            except:
                print(f"Raw error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception creating user: {e}")
        return None

def update_config_file(new_from_address):
    """Update the config file with the working email address."""
    config_path = Path(__file__).parent / 'config' / 'test_config.json'
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        old_address = config['from_address']
        config['from_address'] = new_from_address
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated config file:")
        print(f"  from_address: {old_address} → {new_from_address}")
        
    except Exception as e:
        print(f"❌ Failed to update config: {e}")

if __name__ == "__main__":
    print("🔍 Detailed User Analysis")
    print("="*60)
    
    # Step 1: Get detailed user info
    user_data = get_detailed_user_info()
    
    if user_data:
        account_enabled = user_data.get('accountEnabled', False)
        user_type = user_data.get('userType', 'Unknown')
        mail_enabled = user_data.get('mailEnabled', False)
        
        print(f"\n📊 Summary:")
        print(f"  Account Enabled: {account_enabled}")
        print(f"  User Type: {user_type}")
        print(f"  Mail Enabled: {mail_enabled}")
        
        if account_enabled and user_type == 'Guest':
            print("\n🔍 This is an external/guest user.")
            print("External users often can't send emails via Graph API.")
            
            # Try anyway
            success = test_email_with_external_user()
            
            if not success:
                print("\n🔧 External user can't send emails. Creating internal user...")
                create_internal_user()
        
        elif account_enabled and user_type == 'Member':
            print("\n✅ This is an internal user - should work for sending emails!")
            test_email_with_external_user()
        
        else:
            print(f"\n⚠️  User issues detected:")
            print(f"  - Account enabled: {account_enabled}")
            print(f"  - User type: {user_type}")
            print("Creating a new internal user...")
            create_internal_user()
    
    else:
        print("\n🔧 Could not get user details. Creating new internal user...")
        create_internal_user()
