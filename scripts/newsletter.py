import json
import os
import requests # Ensure 'requests' is available, as it was in your original script
from datetime import datetime

# Configuration from environment variables (no dotenv needed)
TENANT_ID = os.getenv('TENANT_ID')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ONEDRIVE_EMAIL = os.getenv('ONEDRIVE_EMAIL') # User whose OneDrive and Mailbox are used
RECIPIENT_FILE_PATH = os.getenv('RECIPIENT_FILE_PATH', 'email_recipients.txt')

# Microsoft Graph API endpoints
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

def get_access_token():
    """Authenticates with Azure AD and retrieves an access token."""
    if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
        missing_vars = []
        if not TENANT_ID: missing_vars.append("TENANT_ID")
        if not CLIENT_ID: missing_vars.append("CLIENT_ID")
        if not CLIENT_SECRET: missing_vars.append("CLIENT_SECRET")
        raise ValueError(f"Missing critical environment variables for authentication: {', '.join(missing_vars)}")

    payload = {
        'client_id': CLIENT_ID,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post(TOKEN_URL, headers=headers, data=payload)
        response.raise_for_status()
        token_data = response.json()
        if 'access_token' not in token_data:
            print(f"DEBUG: Full token response data: {token_data}")
            raise Exception("Access token not found in response.")
        print("Access token obtained successfully.")
        return token_data['access_token']
    except requests.exceptions.HTTPError as e:
        error_text = "Unknown error"
        if e.response is not None:
            error_text = e.response.text
        print(f"Failed to get access token: {e.response.status_code if e.response is not None else 'N/A'} - {error_text}")
        raise Exception(f"Failed to get access token: {e.response.status_code if e.response is not None else 'N/A'} - {error_text}") from e
    except requests.exceptions.RequestException as e:
        print(f"Network error while getting access token: {e}")
        raise Exception(f"Network error while getting access token: {e}") from e
    except KeyError:
        print("Error: 'access_token' not found in the response from token endpoint.")
        raise

def fetch_recipients_from_onedrive(access_token):
    """Fetches the recipient list from a file in OneDrive."""
    if not ONEDRIVE_EMAIL or not RECIPIENT_FILE_PATH:
        raise ValueError("ONEDRIVE_EMAIL and RECIPIENT_FILE_PATH must be set in environment to fetch recipients from OneDrive.")

    graph_url = f"https://graph.microsoft.com/v1.0/users/{ONEDRIVE_EMAIL}/drive/root:/{RECIPIENT_FILE_PATH}:/content"
    
    headers = {'Authorization': f'Bearer {access_token}'}
    print(f"Fetching recipient file from OneDrive: {graph_url}")
    try:
        response = requests.get(graph_url, headers=headers)
        response.raise_for_status()
        content = response.text
        recipients = [line.strip() for line in content.splitlines() if line.strip() and '@' in line.strip()]
        if not recipients:
            print("Warning: No valid email addresses found in the recipient file.")
        else:
            print(f"Successfully fetched {len(recipients)} recipients from OneDrive.")
        return recipients
    except requests.exceptions.HTTPError as e:
        error_text = "Unknown error"
        if e.response is not None:
            error_text = e.response.text
        print(f"Failed to fetch recipient file from OneDrive: {e.response.status_code if e.response is not None else 'N/A'} {error_text}")
        raise Exception(f"Failed to fetch recipient file from OneDrive: {e.response.status_code if e.response is not None else 'N/A'} {error_text}") from e
    except requests.exceptions.RequestException as e:
        print(f"Network error while fetching recipients from OneDrive: {e}")
        raise Exception(f"Network error while fetching recipients from OneDrive: {e}") from e

def send_newsletter(access_token, subject, content_html, recipients=None, from_address=None):
    """
    Sends the newsletter email using Microsoft Graph API.
    If recipients is None, it will try to fetch from OneDrive.
    from_address defaults to ONEDRIVE_EMAIL if not provided.
    """
    if not from_address:
        from_address = ONEDRIVE_EMAIL
    if not from_address:
        raise ValueError("From address for sending email is not configured (ONEDRIVE_EMAIL in environment or as parameter).")

    final_recipients = recipients
    if final_recipients is None:
        print("Recipients list not provided directly, attempting to fetch from OneDrive...")
        final_recipients = fetch_recipients_from_onedrive(access_token)
    
    if not final_recipients:
        print("No recipients specified. Email will not be sent.")
        return

    send_mail_url = f"https://graph.microsoft.com/v1.0/users/{from_address}/sendMail"
    
    email_msg = {
        'message': {
            'subject': subject,
            'body': {
                'contentType': 'HTML',
                'content': content_html
            },
            'toRecipients': [{'emailAddress': {'address': recip}} for recip in final_recipients],
            'from': { # Explicitly set the From header
                'emailAddress': {
                    'address': from_address
                }
            }
        },
        'saveToSentItems': 'true'
    }

    headers_sendmail = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    print(f"Attempting to send email titled '{subject}' to {len(final_recipients)} recipient(s) from {from_address}...")
    try:
        response = requests.post(send_mail_url, headers=headers_sendmail, data=json.dumps(email_msg))
        response.raise_for_status() 
        print("Email sent successfully!")
    except requests.exceptions.HTTPError as e:
        # --- START OF ENHANCED ERROR LOGGING (same as before) ---
        raw_response_text = "No response body"
        error_status_code = "Unknown Status"
        response_headers = {} 

        if e.response is not None:
            raw_response_text = e.response.text
            error_status_code = e.response.status_code
            response_headers = dict(e.response.headers) 
        
        error_message = f"Failed to send email: {error_status_code}. Response: '{raw_response_text}'"
        
        print(f"DEBUG: HTTPError encountered when sending email.")
        print(f"DEBUG: Status Code: {error_status_code}")
        print(f"DEBUG: Headers: {response_headers}") 
        print(f"DEBUG: Raw Response Text (included in main error message too): {raw_response_text}")

        try:
            if e.response is not None and raw_response_text.strip(): 
                error_details_json = e.response.json()
                print(f"DEBUG: Parsed JSON error details: {error_details_json}")
                if 'error' in error_details_json and isinstance(error_details_json['error'], dict) and 'message' in error_details_json['error']:
                    error_message = f"Failed to send email: {error_status_code}. Graph API Error: {error_details_json['error']['message']}. Full Response: '{raw_response_text}'"
                elif 'error_description' in error_details_json: 
                     error_message = f"Failed to send email: {error_status_code}. Error Description: {error_details_json['error_description']}. Full Response: '{raw_response_text}'"
            else:
                print("DEBUG: No response body or empty response body to parse as JSON.")
        except json.JSONDecodeError:
            print("DEBUG: Response content was not valid JSON.")
        except Exception as json_ex: 
            print(f"DEBUG: Error processing JSON response or constructing detailed error message: {json_ex}")
        # --- END OF ENHANCED ERROR LOGGING ---
        raise Exception(error_message) from e 
    except requests.exceptions.RequestException as e: 
        print(f"Network error while sending email: {e}")
        raise Exception(f"Network error while sending email: {e}") from e

def render_template(template_path, context):
    """Renders a simple HTML template with context."""
    print(f"Rendering template: {template_path}")
    try:
        with open(template_path, 'r') as f:
            template_string = f.read()
        for key, value in context.items():
            placeholder = "{{" + key + "}}" # Basic placeholder format
            template_string = template_string.replace(placeholder, str(value))
        print("Template rendered successfully.")
        return template_string
    except FileNotFoundError:
        print(f"Error: Template file not found at {template_path}")
        raise
    except Exception as e:
        print(f"Error rendering template {template_path}: {e}")
        raise

if __name__ == "__main__":
    print("Starting newsletter script...")
    try:
        # Ensure essential environment variables are set
        # The functions called below will raise ValueError if they are missing
        # For local testing, ensure TENANT_ID, CLIENT_ID, CLIENT_SECRET, ONEDRIVE_EMAIL are set in your environment
        if not all([os.getenv('TENANT_ID'), os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'), os.getenv('ONEDRIVE_EMAIL')]):
            print("Error: One or more required environment variables (TENANT_ID, CLIENT_ID, CLIENT_SECRET, ONEDRIVE_EMAIL) are not set.")
            print("Please set them in your environment before running the script directly.")
            exit(1)

        token = get_access_token()

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        template_context = {
            "date": current_date,
            "username": "Valued Subscriber",
            "custom_message": "This is a test newsletter from the script (without dotenv)."
        }
        
        # Ensure template directory and file exist for standalone execution
        template_dir = "templates"
        template_file = os.path.join(template_dir, "newsletter_template.html")
        if not os.path.exists(template_file):
            os.makedirs(template_dir, exist_ok=True)
            with open(template_file, "w") as f_temp:
                f_temp.write("<h1>Hello {{username}}!</h1><p>Today's date is {{date}}.</p><p>{{custom_message}}</p>")
            print(f"Created dummy template: {template_file}")

        html_content = render_template(template_file, template_context)
        email_subject = f"Weekly Newsletter (No-DotEnv) - {current_date}"
        
        send_newsletter(token, email_subject, html_content)
        
        print("Newsletter script finished successfully.")

    except ValueError as ve:
        print(f"Configuration error: {ve}")
    except FileNotFoundError as fnfe:
        print(f"File not found error: {fnfe}")
    except Exception as e:
        print(f"An error occurred: {e}")
        # import traceback # Uncomment for full traceback if needed
        # traceback.print_exc()
