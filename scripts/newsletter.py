import os
import json
import requests

# Secrets from GitHub Actions environment variables
client_id = os.environ.get('ONEDRIVE_CLIENT_ID')
client_secret = os.environ.get('ONEDRIVE_CLIENT_SECRET')
tenant_id = os.environ.get('ONEDRIVE_TENANT_ID')
from_address = os.environ.get('ONEDRIVE_EMAIL')

# Newsletter content (can be dynamic)
subject = "Your Awesome Newsletter!"
body_html = """
<html>
    <body>
        <h1>Hello from GitHub Actions!</h1>
        <p>This is your latest newsletter content.</p>
        <p>Delivered by the magic of GitHub Actions and Outlook.</p>
    </body>
</html>
"""

# 1. Get Access Token
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
token_data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': 'https://graph.microsoft.com/.default'
}
token_r = requests.post(token_url, data=token_data)
token_r.raise_for_status() # Raise an exception for bad status codes
access_token = token_r.json().get('access_token')

if not access_token:
    print("Failed to get access token.")
    exit(1)

print("Access token obtained successfully.")

# 2. Fetch Newsletter Recipients from OneDrive
onedrive_file_path = "email_recipients.txt"
# Construct the URL for the Graph API to get file content from the user's OneDrive root
# This assumes the script is run in a context where "/me" refers to the user whose OneDrive is being accessed.
# If using application permissions for a specific drive, the URL might need adjustment (e.g., /users/{user-id}/drive/root:...)
file_content_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{onedrive_file_path}:/content"

headers_onedrive = {
    'Authorization': 'Bearer ' + access_token
}

print(f"Attempting to fetch recipient list from OneDrive: {onedrive_file_path}")
file_r = requests.get(file_content_url, headers=headers_onedrive)

to_addresses = []
if file_r.status_code == 200:
    print("Successfully fetched recipient file from OneDrive.")
    # Assuming the file content is plain text with one email address per line
    recipients_text = file_r.text
    to_addresses = [line.strip() for line in recipients_text.splitlines() if line.strip()]
    if not to_addresses:
        print("Recipient file is empty or contains no valid email addresses.")
        exit(1)
    print(f"Recipients loaded: {', '.join(to_addresses)}")
else:
    print(f"Failed to fetch recipient file from OneDrive: {file_r.status_code}")
    try:
        print(file_r.json()) # Print error details if available
    except json.JSONDecodeError:
        print(file_r.text) # Print raw text if not JSON
    exit(1)


# 3. Send Email using Microsoft Graph API
send_mail_url = f"https://graph.microsoft.com/v1.0/users/{from_address}/sendMail"

email_msg = {
    'message': {
        'subject': subject,
        'body': {
            'contentType': 'HTML',
            'content': body_html
        },
        'toRecipients': [
            {'emailAddress': {'address': addr.strip()}} for addr in to_addresses
        ]
        # You can add ccRecipients, bccRecipients, attachments etc.
    },
    'saveToSentItems': 'true'
}

headers_sendmail = {
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json'
}

print("Attempting to send email...")
response = requests.post(send_mail_url, headers=headers_sendmail, data=json.dumps(email_msg))

if response.status_code == 202: # 202 Accepted
    print("Email sent successfully!")
else:
    print(f"Failed to send email: {response.status_code}")
    try:
        print(response.json())
    except json.JSONDecodeError:
        print(response.text)
    exit(1)
