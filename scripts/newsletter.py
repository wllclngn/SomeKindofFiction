import os
import json
import requests

def get_access_token():
    """Get OAuth2 access token from Microsoft Graph API."""
    client_id = os.environ.get('ONEDRIVE_CLIENT_ID')
    client_secret = os.environ.get('ONEDRIVE_CLIENT_SECRET')
    tenant_id = os.environ.get('ONEDRIVE_TENANT_ID')
    
    if not all([client_id, client_secret, tenant_id]):
        raise ValueError("Missing required environment variables: ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET, ONEDRIVE_TENANT_ID")
    
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    token_r = requests.post(token_url, data=token_data)
    token_r.raise_for_status()
    access_token = token_r.json().get('access_token')
    
    if not access_token:
        raise ValueError("Failed to get access token")
    
    return access_token

def fetch_recipients_from_onedrive(access_token, from_address, file_path="email_recipients.txt"):
    """Fetch email recipients from OneDrive file."""
    file_content_url = f"https://graph.microsoft.com/v1.0/users/{from_address}/drive/root:/{file_path}:/content"
    
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    
    print(f"Attempting to fetch recipient list from OneDrive user {from_address}, path: {file_path}")
    file_r = requests.get(file_content_url, headers=headers)
    
    if file_r.status_code == 200:
        print("Successfully fetched recipient file from OneDrive.")
        recipients_text = file_r.text
        to_addresses = [line.strip() for line in recipients_text.splitlines() if line.strip()]
        if not to_addresses:
            raise ValueError("Recipient file is empty or contains no valid email addresses")
        print(f"Recipients loaded: {len(to_addresses)} address(es).")
        return to_addresses
    else:
        error_msg = f"Failed to fetch recipient file from OneDrive: {file_r.status_code}"
        try:
            error_details = file_r.json()
            error_msg += f" - {error_details}"
        except json.JSONDecodeError:
            error_msg += f" - {file_r.text}"
        raise Exception(error_msg)

def load_template(template_path):
    """Load email template from file."""
    if template_path and os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def send_newsletter(recipients=None, subject=None, content_html=None, template_path=None, access_token=None, from_address=None):
    """
    Send newsletter to specified recipients.
    
    Args:
        recipients (list): List of email addresses
        subject (str): Email subject
        content_html (str): HTML content for email body
        template_path (str): Path to HTML template file (optional)
        access_token (str): OAuth2 access token (optional, will get new one if not provided)
        from_address (str): Sender email address (optional, will use env var if not provided)
    """
    # Get access token if not provided
    if not access_token:
        access_token = get_access_token()
    
    # Get from address if not provided
    if not from_address:
        from_address = os.environ.get('ONEDRIVE_EMAIL')
        if not from_address:
            raise ValueError("from_address parameter or ONEDRIVE_EMAIL environment variable must be set")
    
    # Load template if provided
    if template_path and not content_html:
        template_content = load_template(template_path)
        if template_content:
            # You can add template variable substitution here if needed
            content_html = template_content
    
    # Use default content if none provided
    if not content_html:
        content_html = """
        <html>
            <body>
                <h1>Hello from GitHub Actions!</h1>
                <p>This is your latest newsletter content.</p>
                <p>Delivered by the magic of GitHub Actions and Outlook.</p>
            </body>
        </html>
        """
    
    # Use default subject if none provided
    if not subject:
        subject = "Your Awesome Newsletter!"
    
    # Get recipients from OneDrive if not provided
    if not recipients:
        recipients = fetch_recipients_from_onedrive(access_token, from_address)
    
    # Send email using Microsoft Graph API
    send_mail_url = f"https://graph.microsoft.com/v1.0/users/{from_address}/sendMail"
    
    email_msg = {
        'message': {
            'subject': subject,
            'body': {
                'contentType': 'HTML',
                'content': content_html
            },
            'toRecipients': [
                {'emailAddress': {'address': addr.strip()}} for addr in recipients
            ]
        },
        'saveToSentItems': 'true'
    }
    
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }
    
    print("Attempting to send email...")
    response = requests.post(send_mail_url, headers=headers, data=json.dumps(email_msg))
    
    if response.status_code == 202:
        print("Email sent successfully!")
        return True
    else:
        error_msg = f"Failed to send email: {response.status_code}"
        try:
            error_details = response.json()
            error_msg += f" - {error_details}"
        except json.JSONDecodeError:
            error_msg += f" - {response.text}"
        raise Exception(error_msg)

def main():
    """Main function that runs the original script logic."""
    try:
        # Get environment variables
        from_address = os.environ.get('ONEDRIVE_EMAIL')
        
        if not from_address:
            print("ONEDRIVE_EMAIL environment variable is not set.")
            exit(1)
        
        # Get access token
        access_token = get_access_token()
        print("Access token obtained successfully.")
        
        # Send newsletter (will fetch recipients from OneDrive)
        send_newsletter(access_token=access_token, from_address=from_address)
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
