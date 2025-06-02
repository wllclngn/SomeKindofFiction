import os
import json
import requests

# Secrets from GitHub Actions environment variables
client_id = os.environ.get('ONEDRIVE_CLIENT_ID')
client_secret = os.environ.get('ONEDRIVE_CLIENT_SECRET')
tenant_id = os.environ.get('ONEDRIVE_TENANT_ID')
from_address = os.environ.get('ONEDRIVE_EMAIL')
to_addresses = os.environ.get('MAIL_TO_ADDRESSES').split(',') # Assuming comma-separated

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

# 2. Send Email using Microsoft Graph API
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

headers = {
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json'
}

response = requests.post(send_mail_url, headers=headers, data=json.dumps(email_msg))

if response.status_code == 202: # 202 Accepted
    print("Email sent successfully!")
else:
    print(f"Failed to send email: {response.status_code}")
    print(response.json())
    exit(1)