import json
import requests
from datetime import datetime

def test_personal_account_permissions():
    """Test if your personal Outlook account can send emails"""
    
    print("🧪 Testing Personal Outlook Account Setup")
    print("="*60)
    print(f"📧 From: somekindoffiction@outlook.com")
    print(f"🕒 Test Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    # First, let's check what permissions your app has
    print("Step 1: Checking app registration permissions...")
    
    # You'll need to update these with your actual values
    config = {
        "client_id": "YOUR_CLIENT_ID",  # From your Azure app registration
        "client_secret": "YOUR_CLIENT_SECRET", 
        "tenant_id": "YOUR_TENANT_ID",
        "from_address": "somekindoffiction@outlook.com"
    }
    
    # Test authentication with personal account scope
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    print("🔑 Testing authentication...")
    response = requests.post(token_url, data=token_data)
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        print("✅ Authentication successful!")
        
        # Test if we can access the user's mailbox
        headers = {'Authorization': f'Bearer {token}'}
        user_url = "https://graph.microsoft.com/v1.0/me"
        
        user_response = requests.get(user_url, headers=headers)
        if user_response.status_code == 200:
            user_info = user_response.json()
            print(f"✅ Can access mailbox for: {user_info.get('mail', 'No email found')}")
            return True, token
        else:
            print(f"❌ Cannot access mailbox: {user_response.status_code}")
            print("🔧 Need to grant personal account permissions")
            return False, None
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(response.text)
        return False, None

def test_send_permission(token):
    """Test if we can send an email"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Simple test email
    email_data = {
        "message": {
            "subject": "Newsletter System Test",
            "body": {
                "contentType": "HTML",
                "content": "<h2>🎉 Success!</h2><p>Your personal Outlook account can send newsletters!</p>"
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": "somekindoffiction@outlook.com"  # Send to yourself
                    }
                }
            ]
        }
    }
    
    send_url = "https://graph.microsoft.com/v1.0/me/sendMail"
    print("📧 Testing email send...")
    
    response = requests.post(send_url, headers=headers, json=email_data)
    
    if response.status_code == 202:
        print("✅ Email sent successfully!")
        print("📬 Check your inbox for the test email")
        return True
    else:
        print(f"❌ Send failed: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    success, token = test_personal_account_permissions()
    
    if success and token:
        print("\n" + "="*60)
        send_success = test_send_permission(token)
        
        if send_success:
            print("\n🎉 PERFECT! Your personal account works!")
            print("💡 You can use this for FREE newsletter sending")
            print("📝 Update your config to use: somekindoffiction@outlook.com")
        else:
            print("\n🔧 Need to configure send permissions")
    else:
        print("\n🔄 Let's set up the permissions properly...")
