import os
import json
import requests

# "There isn't anything to compare..."
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
onedrive_file_path = "email_recipients.txt" # Ensure this is the correct path in the root of the specified user's OneDrive

# IMPORTANT: Use the specific user's UPN (from_address) instead of /me
if not from_address:
    print("MAIL_FROM_ADDRESS environment variable is not set. Cannot determine target OneDrive user.")
    exit(1)

file_content_url = f"https://graph.microsoft.com/v1.0/users/{from_address}/drive/root:/{onedrive_file_path}:/content"

headers_onedrive = {
    'Authorization': 'Bearer ' + access_token
}

print(f"Attempting to fetch recipient list from OneDrive user {from_address}, path: {onedrive_file_path}")
print(f"Request URL: {file_content_url}") # Adding this for debugging
file_r = requests.get(file_content_url, headers=headers_onedrive)

to_addresses = []
if file_r.status_code == 200:
    print("Successfully fetched recipient file from OneDrive.")
    recipients_text = file_r.text
    to_addresses = [line.strip() for line in recipients_text.splitlines() if line.strip()]
    if not to_addresses:
        print("Recipient file is empty or contains no valid email addresses.")
        exit(1) # Or handle as a non-fatal error if sending to no one is acceptable
    print(f"Recipients loaded: {len(to_addresses)} address(es).")
else:
    print(f"Failed to fetch recipient file from OneDrive: {file_r.status_code}")
    try:
        print(file_r.json())
    except json.JSONDecodeError:
        print(file_r.text)
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
    },
    'saveToSentItems': 'true'
}

headers_sendmail = {
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json'
}

print("Attempting to send email...")
response = requests.post(send_mail_url, headers=headers_sendmail, data=json.dumps(email_msg))

if response.status_code == 202:
    print("Email sent successfully!")
else:
    print(f"Failed to send email: {response.status_code}")
    try:
        print(response.json())
    except json.JSONDecodeError:
        print(response.text)
    exit(1)