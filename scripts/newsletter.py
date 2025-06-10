import os
import json
import requests
from pathlib import Path
from datetime import datetime

def send_newsletter(recipients=None, subject="Default Subject", template_path=None, body_html_content=None):
    """
    Sends a newsletter.
    Fetches recipients from OneDrive if not provided directly.
    Renders HTML from template_path if provided, otherwise uses body_html_content.
    """
    client_id = os.environ.get('ONEDRIVE_CLIENT_ID')
    client_secret = os.environ.get('ONEDRIVE_CLIENT_SECRET')
    tenant_id = os.environ.get('ONEDRIVE_TENANT_ID')
    from_address = os.environ.get('ONEDRIVE_EMAIL')

    if not all([client_id, client_secret, tenant_id, from_address]):
        raise ValueError("Missing one or more environment variables: ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET, ONEDRIVE_TENANT_ID, ONEDRIVE_EMAIL")

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    access_token = None
    try:
        token_r = requests.post(token_url, data=token_data)
        token_r.raise_for_status()
        token_json = token_r.json()
        access_token = token_json.get('access_token')
        if not access_token:
            print(f"Failed to get access token: 'access_token' not found in response. Response: {token_json}")
            raise Exception("Failed to get access token: 'access_token' not found in response.")
        print("Access token obtained successfully.")
    except requests.exceptions.HTTPError as e:
        print(f"Failed to get access token (HTTPError): {e}")
        print(f"Response status: {e.response.status_code}, Response text: {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Failed to get access token (RequestException): {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Failed to parse access token response as JSON: {e}")
        if 'token_r' in locals() and token_r is not None:
            print(f"Response text: {token_r.text}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during token acquisition: {e}")
        raise

    final_recipients = []
    if recipients and isinstance(recipients, list) and len(recipients) > 0:
        print(f"Using {len(recipients)} provided recipient(s).")
        final_recipients = [str(r).strip() for r in recipients if str(r).strip()]
    else:
        print("No recipients provided directly. Attempting to fetch from OneDrive.")
        onedrive_file_path = "email_recipients.txt"
        file_content_url = f"https://graph.microsoft.com/v1.0/users/{from_address}/drive/root:/{onedrive_file_path}:/content"
        headers_onedrive = {'Authorization': 'Bearer ' + access_token}

        print(f"Attempting to fetch recipient list from OneDrive user {from_address}, path: {onedrive_file_path}")
        print(f"Request URL: {file_content_url}")
        
        try:
            file_r = requests.get(file_content_url, headers=headers_onedrive)
            file_r.raise_for_status()
            
            print("Successfully fetched recipient file from OneDrive.")
            recipients_text = file_r.text
            onedrive_recipients_list = [line.strip() for line in recipients_text.splitlines() if line.strip()]
            
            if not onedrive_recipients_list:
                print("Recipient file from OneDrive is empty or contains no valid email addresses.")
                raise ValueError("Recipient file from OneDrive is empty.")
            
            final_recipients = onedrive_recipients_list
            print(f"Recipients loaded from OneDrive: {len(final_recipients)} address(es).")

        except requests.exceptions.HTTPError as e:
            error_message = f"Failed to fetch recipient file from OneDrive: {e.response.status_code}"
            try:
                error_details = e.response.json()
                error_message += f" - {error_details}"
                print(error_details)
            except json.JSONDecodeError:
                error_text = e.response.text
                error_message += f" - {error_text}"
                print(error_text)
            raise Exception(error_message) from e
        except requests.exceptions.RequestException as e:
            print(f"Network error while fetching recipient file from OneDrive: {e}")
            raise Exception(f"Network error while fetching recipient file from OneDrive: {e}") from e

    if not final_recipients:
        print("No recipients to send to. Aborting.")
        raise ValueError("No recipients specified or found. Cannot send newsletter.")

    current_body_html = ""
    if template_path:
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
            current_body_html = template_content.format(
                timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                recipient_name="Valued Subscriber"
            )
            print(f"Loaded and rendered email body from template: {template_path}")
        except FileNotFoundError:
            print(f"Error: Template file not found at {template_path}")
            raise
        except KeyError as e:
            print(f"Error: Missing key '{e}' in template '{template_path}'. Ensure all placeholders are provided or handled.")
            raise
    elif body_html_content:
        current_body_html = body_html_content
        print("Using provided HTML content for email body.")
    else:
        raise ValueError("Email body content is missing. Provide template_path or body_html_content.")

    send_mail_url = f"https://graph.microsoft.com/v1.0/users/{from_address}/sendMail"
    email_msg = {
        'message': {
            'subject': subject,
            'body': {'contentType': 'HTML', 'content': current_body_html},
            'toRecipients': [{'emailAddress': {'address': addr}} for addr in final_recipients]
        },
        'saveToSentItems': 'true'
    }
    headers_sendmail = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }

    print(f"Attempting to send email titled '{subject}' to {len(final_recipients)} recipient(s)...")
    try:
        response = requests.post(send_mail_url, headers=headers_sendmail, data=json.dumps(email_msg))
        response.raise_for_status()
        print("Email sent successfully!")
    except requests.exceptions.HTTPError as e:
        error_message = f"Failed to send email: {e.response.status_code}"
        try:
            error_details = e.response.json()
            error_message += f" - {error_details}"
            print(error_details)
        except json.JSONDecodeError:
            error_text = e.response.text
            error_message += f" - {error_text}"
            print(error_text)
        raise Exception(error_message) from e
    except requests.exceptions.RequestException as e:
        print(f"Network error while sending email: {e}")
        raise Exception(f"Network error while sending email: {e}") from e

if __name__ == "__main__":
    print("Running newsletter.py script directly...")
    
    if not all(os.environ.get(var) for var in ['ONEDRIVE_CLIENT_ID', 'ONEDRIVE_CLIENT_SECRET', 'ONEDRIVE_TENANT_ID', 'ONEDRIVE_EMAIL']):
        print("Critical environment variables for OneDrive/Email are not set. Exiting direct run.")
        print("Please set ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET, ONEDRIVE_TENANT_ID, ONEDRIVE_EMAIL.")
        exit(1)

    default_subject = "Newsletter (Direct Run)"
    default_template = Path(__file__).parent.parent / 'tests' / 'templates' / 'test_email_template.html'
    
    try:
        print("Attempting to send newsletter using default settings for direct run (will fetch recipients from OneDrive).")
        send_newsletter(
            recipients=None,
            subject=default_subject,
            template_path=str(default_template) if default_template.exists() else None,
            body_html_content="<h1>Direct Run Test</h1><p>If template not found.</p><p>Sent at {timestamp}</p>" if not default_template.exists() else None
        )
        print("Direct script run completed successfully.")
    except Exception as e:
        print(f"Error during direct script run: {str(e)}")
        exit(1)
