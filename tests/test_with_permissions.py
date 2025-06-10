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

def test_email_with_confirmed_permissions():
    """Test email sending with confirmed permissions."""
    config = load_config()
    
    print("🧪 Testing Email with Confirmed Permissions")
    print("="*60)
    print("Your app has all the right permissions granted!")
    
    try:
        access_token = get_access_token()
        print("✅ Access token obtained")
        
        # Check user details first
        user_url = f"https://graph.microsoft.com/v1.0/users/{config['from_address']}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        user_response = requests.get(user_url, headers=headers)
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print(f"✅ User found: {config['from_address']}")
            print(f"   Display Name: {user_data.get('displayName')}")
            print(f"   Account Enabled: {user_data.get('accountEnabled')}")
            print(f"   Mail Enabled: {user_data.get('mailEnabled')}")
            print(f"   License Count: {len(user_data.get('assignedLicenses', []))}")
            
            # Try to send email
            print("\n📧 Attempting to send test email...")
            
            email_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #28a745;">🎉 Success! Microsoft Graph Email Working</h2>
                    <p>Your newsletter system is now working with Microsoft Graph API!</p>
                    
                    <h3>📋 Test Details:</h3>
                    <ul>
                        <li><strong>From:</strong> {config['from_address']}</li>
                        <li><strong>Method:</strong> Microsoft Graph API</li>
                        <li><strong>Permissions:</strong> Application-level (Mail.Send)</li>
                        <li><strong>Time:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                    </ul>
                    
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">🚀 Your Newsletter System is Ready!</h3>
                        <p>You can now send newsletters using Microsoft Graph API with your Azure setup.</p>
                    </div>
                </body>
            </html>
            """
            
            email_msg = {
                'message': {
                    'subject': '🧪 Microsoft Graph Newsletter Test - SUCCESS!',
                    'body': {
                        'contentType': 'HTML',
                        'content': email_content
                    },
                    'toRecipients': [
                        {'emailAddress': {'address': config['test_recipient']}}
                    ]
                },
                'saveToSentItems': 'false'
            }
            
            send_url = f"https://graph.microsoft.com/v1.0/users/{config['from_address']}/sendMail"
            
            send_response = requests.post(send_url, headers=headers, data=json.dumps(email_msg))
            
            if send_response.status_code == 202:
                print("🎉 EMAIL SENT SUCCESSFULLY!")
                print(f"📬 Check {config['test_recipient']} for the test email")
                print("\n✅ Your Microsoft Graph newsletter system is working!")
                return True
            else:
                print(f"❌ Email send failed: {send_response.status_code}")
                
                if send_response.status_code == 403:
                    print("   → Forbidden: User may need Exchange Online license")
                elif send_response.status_code == 404:
                    print("   → Not found: User or mailbox may not exist")
                
                try:
                    error_data = send_response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Raw error: {send_response.text}")
                
                return False
        else:
            print(f"❌ User not found: {user_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def suggest_next_steps():
    """Suggest next steps based on test results."""
    
    print("\n" + "="*60)
    print("📋 NEXT STEPS")
    print("="*60)
    
    print("\n🔍 If email sending failed:")
    print("1. Check if user has Exchange Online license")
    print("2. Run: python3 tests/assign_license.py")
    print("3. Wait 5-10 minutes for mailbox provisioning")
    
    print("\n✅ If email sending worked:")
    print("1. Your Microsoft Graph newsletter system is ready!")
    print("2. Edit email_recipients.txt with subscriber emails")
    print("3. Run the full newsletter system")
    
    print("\n🆓 Free alternatives if licensing is an issue:")
    print("1. Microsoft 365 Trial (30 days free)")
    print("2. Simple SMTP newsletter (completely free)")
    print("3. Developer Program (when approved)")

if __name__ == "__main__":
    print("🔧 Testing with Confirmed Permissions")
    print("="*60)
    print("All required app permissions are granted!")
    
    success = test_email_with_confirmed_permissions()
    
    if not success:
        suggest_next_steps()
        
        print("\n🤔 Want to run the license check/assignment?")
        choice = input("Check and assign licenses now? (y/n): ")
        
        if choice.lower() == 'y':
            print("Running license assignment...")
            import subprocess
            try:
                subprocess.run(['python3', 'assign_license.py'], cwd='tests')
            except:
                print("Run: python3 tests/assign_license.py")
