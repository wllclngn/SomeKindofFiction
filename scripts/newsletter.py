import os
import json
import requests
from google.cloud import firestore
import base64

def get_access_token():
    # Get OAuth2 access token from Microsoft Graph API (for sending email).
    client_id = os.environ.get('ONEDRIVE_CLIENT_ID')
    client_secret = os.environ.get('ONEDRIVE_CLIENT_SECRET')
    tenant_id = os.environ.get('ONEDRIVE_TENANT_ID')
    
    if not all([client_id, client_secret, tenant_id]):
        raise ValueError("Missing required environment variables for MS Graph Auth: ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET, ONEDRIVE_TENANT_ID")
    
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
        raise ValueError("Failed to get MS Graph access token")
    
    # Print access token claims for debugging (base64 decode JWT payload)
    # This helps diagnose 401 errors by showing what the token is valid for
    try:
        parts = access_token.split('.')
        if len(parts) > 1:
            claims_json = base64.urlsafe_b64decode(parts[1] + '=' * (-len(parts[1]) % 4)).decode('utf-8')
            claims = json.loads(claims_json)
            print("# DEBUG: Access Token Claims:")
            print(json.dumps(claims, indent=2))
    except Exception as e:
        print(f"# WARNING: Could not decode access token claims: {e}")
    
    return access_token

def fetch_recipients_from_firestore(project_id=None, collection_name="config", document_id="email_recipients", field_name="recipients"):
    # Fetch email recipients from a Firestore document.
    # Assumes GOOGLE_APPLICATION_CREDENTIALS environment variable is set for authentication.
    if not project_id:
        project_id = os.environ.get('FIREBASE_PROJECT_ID')
    if not project_id:
        raise ValueError("Firebase project_id must be provided or set as FIREBASE_PROJECT_ID environment variable.")

    db = firestore.Client(project=project_id)
    print(f"Attempting to fetch recipient list from Firestore project '{project_id}', path: '{collection_name}/{document_id}', field: '{field_name}'")

    doc_ref = db.collection(collection_name).document(document_id)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        to_addresses = data.get(field_name, [])
        
        if not isinstance(to_addresses, list):
            raise ValueError(f"Field '{field_name}' in Firestore document '{collection_name}/{document_id}' is not a list.")
        
        # Filter out empty strings and ensure all are strings
        to_addresses = [str(addr).strip() for addr in to_addresses if isinstance(addr, str) and str(addr).strip()]

        if not to_addresses:
            raise ValueError(f"Recipient list from Firestore ('{collection_name}/{document_id}' field '{field_name}') is empty or contains no valid email addresses.")
        
        print(f"Recipients loaded from Firestore: {len(to_addresses)} address(es).")
        return to_addresses
    else:
        raise Exception(f"Firestore document '{collection_name}/{document_id}' not found in project '{project_id}'. Please ensure it exists and contains the recipient list.")

def load_template(template_path):
    # Load email template from file.
    if template_path and os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def send_newsletter(recipients=None, subject=None, content_html=None, template_path=None, access_token=None, from_address=None):
    # Send newsletter to specified recipients.
    # Fetches recipients from Firestore if not provided.
    if not access_token:
        access_token = get_access_token() # For MS Graph (sending email)
    
    if not from_address:
        from_address = os.environ.get('ONEDRIVE_EMAIL') # This is the SENDER email
        if not from_address:
            raise ValueError("from_address parameter or ONEDRIVE_EMAIL environment variable (sender email) must be set")
    
    if template_path and not content_html:
        template_content = load_template(template_path)
        if template_content:
            content_html = template_content
    
    if not content_html:
        content_html = """
        <html><body><h1>Hello from GitHub Actions!</h1><p>This is your latest newsletter content.</p>
        <p>Delivered by the magic of GitHub Actions and Outlook, with recipients from Firestore.</p></body></html>
        """
    
    if not subject:
        subject = "Your Awesome Newsletter!"
    
    if not recipients:
        print("Recipients not provided directly, attempting to fetch from Firestore...")
        try:
            # project_id will be read from FIREBASE_PROJECT_ID env var by fetch_recipients_from_firestore
            recipients = fetch_recipients_from_firestore() 
        except Exception as e:
            raise ValueError(f"Failed to fetch recipients from Firestore and none were provided: {e}")

    if not recipients:
        raise ValueError("No recipients specified or found in Firestore.")

    send_mail_url = f"https://graph.microsoft.com/v1.0/users/{from_address}/sendMail"
    
    email_msg = {
        'message': {
            'subject': subject,
            'body': {'contentType': 'HTML', 'content': content_html},
            'toRecipients': [{'emailAddress': {'address': addr.strip()}} for addr in recipients]
        },
        'saveToSentItems': 'true'
    }
    
    headers = {
        'Authorization': 'Bearer ' + access_token, # MS Graph Token
        'Content-Type': 'application/json'
    }
    
    print(f"Attempting to send email to {len(recipients)} recipient(s)...")
    response = requests.post(send_mail_url, headers=headers, data=json.dumps(email_msg))
    
    if response.status_code == 202:
        print("Email sent successfully!")
        return True
    else:
        error_msg = f"Failed to send email: {response.status_code}"
        try:
            error_details = response.json()
            error_msg += f" - {json.dumps(error_details, indent=2)}"
        except json.JSONDecodeError:
            error_msg += f" - {response.text}"
        print(f"ERROR: {error_msg}")
        raise Exception(error_msg)

def main():
    # Main function that runs the script logic.
    try:
        from_address = os.environ.get('ONEDRIVE_EMAIL') # Sender email
        if not from_address:
            print("ONEDRIVE_EMAIL environment variable (for sender email) is not set.")
            exit(1)
        
        firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID')
        if not firebase_project_id:
            print("FIREBASE_PROJECT_ID environment variable is not set. This is required for fetching recipients from Firestore.")

        # Get access token for Microsoft Graph API (to send the email)
        ms_graph_access_token = get_access_token()
        print("MS Graph Access token obtained successfully.")
        
        # Call send_newsletter. It will fetch recipients from Firestore.
        send_newsletter(access_token=ms_graph_access_token, from_address=from_address)
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()