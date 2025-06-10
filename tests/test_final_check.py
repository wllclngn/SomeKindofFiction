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

def test_new_user():
    """Test the newly created internal user."""
    config = load_config()
    
    print("🔍 Testing newly created user...")
    print(f"User: {config['from_address']}")
    
    try:
        access_token = get_access_token()
        print("✅ Access token obtained")
        
        # First, verify the user exists and get details
        user_url = f"https://graph.microsoft.com/v1.0/users/{config['from_address']}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print("🔍 Checking user details...")
        user_response = requests.get(user_url, headers=headers)
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print("✅ User found!")
            print(f"  Display Name: {user_data.get('displayName')}")
            print(f"  Account Enabled: {user_data.get('accountEnabled')}")
            print(f"  Mail Enabled: {user_data.get('mailEnabled')}")
            print(f"  User Type: {user_data.get('userType')}")
            
            # Now test sending email
            return test_send_email(access_token, config)
            
        else:
            print(f"❌ User not found: {user_response.status_code}")
            if user_response.status_code == 404:
                print("🔧 The user doesn't exist yet. Please create it manually in Azure Portal.")
            try:
                error_data = user_response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {user_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_send_email(access_token, config):
    """Test sending an email with the new user."""
    
    print("\n📧 Testing email sending...")
    
    try:
        send_mail_url = f"https://graph.microsoft.com/v1.0/users/{config['from_address']}/sendMail"
        
        email_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #28a745;">🎉 Newsletter System Test - SUCCESS!</h2>
                    <p>Congratulations! Your newsletter system is now working correctly.</p>
                    
                    <h3>✅ What was tested:</h3>
                    <ul>
                        <li>Azure App Registration authentication</li>
                        <li>Microsoft Graph API access</li>
                        <li>Email sending permissions</li>
                        <li>User account configuration</li>
                    </ul>
                    
                    <h3>📧 Email Details:</h3>
                    <ul>
                        <li><strong>From:</strong> {config['from_address']}</li>
                        <li><strong>To:</strong> {config['test_recipient']}</li>
                        <li><strong>Sent:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                    </ul>
                    
                    <p style="background-color: #d4edda; padding: 10px; border-radius: 4px;">
                        <strong>🚀 Your newsletter system is ready!</strong><br>
                        You can now run: <code>python3 test_newsletter.py</code>
                    </p>
                </div>
                
                <hr style="margin: 30px 0;">
                <p style="font-size: 12px; color: #6c757d;">
                    This email was sent by the SomeKindofFiction newsletter system test suite.
                </p>
            </body>
        </html>
        """
        
        email_msg = {
            'message': {
                'subject': '🎉 Newsletter System Test - SUCCESS!',
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
        
        response = requests.post(send_mail_url, headers=headers, data=json.dumps(email_msg))
        
        if response.status_code == 202:
            print("🎉 EMAIL SENT SUCCESSFULLY!")
            print(f"📬 Check {config['test_recipient']} for the success email")
            print("\n✅ Your newsletter system is working!")
            print("✅ You can now run your original tests:")
            print("   python3 test_newsletter.py")
            return True
        else:
            print(f"❌ Failed to send email: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
                
                if 'MailboxNotEnabledForRESTAPI' in str(error_data):
                    print("\n🔧 User needs a mailbox. Assign an Office 365 license.")
                elif 'MailboxNotFound' in str(error_data):
                    print("\n🔧 User mailbox not ready yet. Wait a few minutes and try again.")
                
            except:
                print(f"Raw error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception sending email: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Final Newsletter System Test")
    print("="*50)
    print("This test assumes you've created the internal user manually.")
    print("If not, please create it first in Azure Portal.\n")
    
    success = test_new_user()
    
    if success:
        print("\n" + "="*60)
        print("🎊 CONGRATULATIONS! 🎊")
        print("="*60)
        print("Your newsletter system is fully functional!")
        print("\nNext steps:")
        print("1. Run: python3 test_newsletter.py")
        print("2. Create your OneDrive email_recipients.txt file")
        print("3. Start using your newsletter system!")
        
    else:
        print("\n" + "="*60)
        print("🔧 NEXT STEPS")
        print("="*60)
        print("1. Create user manually in Azure Portal:")
        print("   - User: somekindoffiction@somekindoffictionoutlook.onmicrosoft.com")
        print("   - Assign Office 365 license")
        print("2. Wait 5-10 minutes for mailbox provisioning")
        print("3. Run this test again")
