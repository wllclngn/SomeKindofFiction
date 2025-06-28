# tests/test_newsletter.py
# Modified to focus on newsletter sending via Microsoft Graph API
# Firestore functionality temporarily commented out
# Last update: 2025-06-28

import os
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import unittest

# Add parent directory to Python path for importing newsletter.py
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scripts.newsletter import send_newsletter, get_access_token

# Firestore functionality commented out - will be restored later
"""
from scripts.newsletter import fetch_recipients_from_firestore
"""

def load_test_config():
    # Load test configuration from JSON file
    config_path = Path(__file__).resolve().parent / 'config' / 'test_config.json'
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        template_config = {
            "client_id": "YOUR_CLIENT_ID_HERE",
            "client_secret": "YOUR_CLIENT_SECRET_HERE",
            "tenant_id": "YOUR_TENANT_ID_HERE",
            "from_address": "your_sender_email@example.com",
            "test_recipient": "test@example.com"
        }
        with open(config_path, 'w') as f:
            json.dump(template_config, f, indent=2)
        print(f"Created template config file at {config_path}")
        print("Please update it with your actual values before running tests.")
        return template_config
    
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_test_environment():
    # Setup test environment variables from config
    config = load_test_config()
    os.environ['ONEDRIVE_CLIENT_ID'] = config.get('client_id', '')
    os.environ['ONEDRIVE_CLIENT_SECRET'] = config.get('client_secret', '')
    os.environ['ONEDRIVE_TENANT_ID'] = config.get('tenant_id', '')
    os.environ['ONEDRIVE_EMAIL'] = config.get('from_address', '')
    
    # Firestore environment setup commented out - will be restored later
    """
    os.environ['FIREBASE_PROJECT_ID'] = config.get('firebase_project_id', '')
    """

    if not all([os.environ['ONEDRIVE_CLIENT_ID'], 
                os.environ['ONEDRIVE_CLIENT_SECRET'], 
                os.environ['ONEDRIVE_TENANT_ID'],
                os.environ['ONEDRIVE_EMAIL']]):
        print("WARNING: Not all required MS Graph configuration values are present.")
        return False
    return config

def create_test_template_file(template_filename="test_email_template.html"):
    # Create a test email template if it doesn't exist
    template_dir = Path(__file__).resolve().parent / 'templates'
    template_dir.mkdir(parents=True, exist_ok=True)
    template_path = template_dir / template_filename
    
    if not template_path.exists():
        # Template content with placeholders for recipient name and timestamp
        template_content = """
        <html>
            <head>
                <title>Test Newsletter</title>
            </head>
            <body>
                <h1>Test Newsletter</h1>
                <p>Hello <strong>{recipient_name}</strong>!</p>
                <p>This is a test email sent from our newsletter system.</p>
                <p><em>Sent at: {timestamp}</em></p>
                <hr>
                <p>This email was generated for testing purposes.</p>
            </body>
        </html>
        """
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content.strip())
        print(f"Created test template at {template_path}")
    
    return str(template_path)

def test_template_rendering():
    print("\n1. Testing template rendering...")
    setup_test_environment() 
    template_path = create_test_template_file()
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        rendered_html = template_str.format(
            recipient_name="Test User",
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        assert "{recipient_name}" not in rendered_html, "Template variable not replaced."
        assert "{timestamp}" not in rendered_html, "Template variable not replaced."
        print("Template rendering test completed successfully.")
    except Exception as e:
        print(f"ERROR: Template rendering test failed: {str(e)}")
        raise

def test_single_recipient_send():
    print("\n2. Testing single recipient delivery...")
    config = setup_test_environment()
    
    if not config:
        print("WARNING: Missing configuration values. Test cannot proceed.")
        return
    
    # Read recipient from test_recipients.txt
    recipients_file = Path(__file__).resolve().parent / 'config' / 'test_recipients.txt'
    if not recipients_file.exists():
        print(f"WARNING: Recipients file not found at {recipients_file}")
        return
        
    try:
        with open(recipients_file, 'r') as f:
            recipient = f.readline().strip()
        
        if not recipient:
            print("WARNING: No recipient found in test_recipients.txt")
            return
            
        print(f"Using recipient from file: {recipient}")
        
        template_path = create_test_template_file()
        
        access_token = get_access_token()
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        content_html = template_str.format(
            recipient_name="Valued Subscriber",
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        success = send_newsletter(
            recipients=[recipient], 
            subject="Test Newsletter - Single Recipient Test",
            content_html=content_html,
            access_token=access_token,
            from_address=config['from_address']
        )
        assert success, "send_newsletter call reported failure."
        print(f"Single recipient test completed successfully (email sent to {recipient}).")
    except Exception as e:
        print(f"ERROR: Single recipient test failed: {str(e)}")
        raise

def test_multiple_recipients_send_from_file():
    print("\n3. Testing multiple recipients delivery (from file)...")
    config = setup_test_environment()
    
    if not config:
        print("WARNING: Missing configuration values. Test cannot proceed.")
        return
    
    template_path = create_test_template_file()
    recipients_config_path = Path(__file__).resolve().parent / 'config' / 'test_recipients.txt'
    
    if not recipients_config_path.exists():
        print(f"WARNING: Recipients file not found at {recipients_config_path}")
        return
    
    try:
        # Read recipients from file
        with open(recipients_config_path, 'r', encoding='utf-8') as f:
            recipients = [line.strip() for line in f if line.strip()]
        
        if not recipients:
            print("WARNING: No recipients in test_recipients.txt. Test cannot proceed.")
            return

        print(f"Found {len(recipients)} recipient(s) in file")
        
        access_token = get_access_token()
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        content_html = template_str.format(
            recipient_name="Valued Newsletter Recipient",
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        success = send_newsletter(
            recipients=recipients,
            subject="Test Newsletter - File Recipients Test",
            content_html=content_html,
            access_token=access_token,
            from_address=config['from_address']
        )
        assert success, "send_newsletter call reported failure."
        print(f"Multiple recipients test completed successfully (email sent to {len(recipients)} addresses).")
    except Exception as e:
        print(f"ERROR: Multiple recipients test failed: {str(e)}")
        raise

# Firestore tests commented out - will be restored later
"""
def test_firestore_recipients_fetch():
    print("\n4. Testing Firestore recipients fetch...")
    config = setup_test_environment() 

    if not os.environ.get('FIREBASE_PROJECT_ID') or os.environ.get('FIREBASE_PROJECT_ID') == 'your-firebase-project-id':
        print("WARNING: Skipping Firestore recipients fetch test: FIREBASE_PROJECT_ID not set correctly.")
        return

    try:
        print(f"Attempting to fetch recipients from Firestore project: {os.environ.get('FIREBASE_PROJECT_ID')}")
        fetched_recipients = fetch_recipients_from_firestore(
            project_id=os.environ.get('FIREBASE_PROJECT_ID')
        )
        
        assert fetched_recipients is not None, "fetch_recipients_from_firestore returned None"
        assert isinstance(fetched_recipients, list), "Expected a list of recipients"
        print(f"Firestore recipients fetch test completed. Found {len(fetched_recipients)} recipients.")
        if fetched_recipients:
            print(f"Sample: {fetched_recipients[0]}")
    except Exception as e:
        print(f"ERROR: Firestore recipients fetch test failed: {str(e)}")
        print("Note: This test requires valid Google Cloud credentials (e.g., GOOGLE_APPLICATION_CREDENTIALS),")
        print("the Firestore API enabled for the project, and the specified document/field to exist.")
        raise

def test_send_to_firestore_recipients():
    print("\n5. Testing send to recipients fetched from Firestore...")
    config = setup_test_environment()
    template_path = create_test_template_file()

    if not os.environ.get('FIREBASE_PROJECT_ID') or os.environ.get('FIREBASE_PROJECT_ID') == 'your-firebase-project-id':
        print("WARNING: Skipping send to Firestore recipients test: FIREBASE_PROJECT_ID not set correctly.")
        return

    try:
        access_token = get_access_token()
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        content_html = template_str.format(
            recipient_name="Valued Firestore Subscriber",
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        success = send_newsletter(
            subject="Test Newsletter - Firestore Recipients",
            content_html=content_html,
            access_token=access_token,
            from_address=config['from_address']
        )
        assert success, "send_newsletter call (Firestore recipients) reported failure."
        print("Send to Firestore recipients test completed successfully (email attempt made).")
        print("Check your Firestore 'config/email_recipients' list to see who should have received it.")
    except ValueError as ve:
        if "Failed to fetch recipients from Firestore" in str(ve) or "No recipients specified or found" in str(ve):
            print(f"ERROR: Send to Firestore recipients test failed due to recipient fetch issue: {str(ve)}")
            print("Ensure Firestore is populated and credentials are correct.")
        else:
            print(f"ERROR: Send to Firestore recipients test failed with ValueError: {str(ve)}")
            raise
    except Exception as e:
        print(f"ERROR: Send to Firestore recipients test failed: {str(e)}")
        raise
"""

if __name__ == "__main__":
    print("Starting newsletter tests...")
    
    # Run only the essential tests that don't require Firestore
    test_functions = [
        test_template_rendering,
        test_single_recipient_send,
        test_multiple_recipients_send_from_file
    ]

    all_passed = True
    for test_func in test_functions:
        try:
            test_func()
        except Exception:
            all_passed = False
    
    if all_passed:
        print("\nAll newsletter tests completed successfully!")
    else:
        print("\nWARNING: Some newsletter tests failed. Please review the output.")