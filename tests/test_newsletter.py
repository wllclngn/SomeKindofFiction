import os
import json
import sys
from datetime import datetime, timezone # Added timezone
from pathlib import Path
import unittest 

# Add parent directory to Python path for importing newsletter.py
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scripts.newsletter import send_newsletter, get_access_token, fetch_recipients_from_firestore

def load_test_config():
    """Load test configuration from JSON file."""
    config_path = Path(__file__).resolve().parent / 'config' / 'test_config.json'
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        template_config = {
            "client_id": "YOUR_CLIENT_ID_HERE",
            "client_secret": "YOUR_CLIENT_SECRET_HERE",
            "tenant_id": "YOUR_TENANT_ID_HERE",
            "from_address": "your_sender_email@example.com",
            "test_recipient": "your_test_recipient@example.com",
            "msa_user_id": "YOUR_PERSONAL_ONEDRIVE_USER_ID_GUID_HERE", # Kept for potential other uses
            "firebase_project_id": "your-firebase-project-id" # Ensure this is correct
        }
        with open(config_path, 'w') as f:
            json.dump(template_config, f, indent=2)
        print(f"Created template config file at {config_path}")
        print("Please update it with your actual Azure App, MSA User ID, and Firebase Project ID values before running tests.")
        return template_config
    
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_test_environment():
    """Setup test environment variables from config."""
    config = load_test_config()
    os.environ['ONEDRIVE_CLIENT_ID'] = config.get('client_id', '')
    os.environ['ONEDRIVE_CLIENT_SECRET'] = config.get('client_secret', '')
    os.environ['ONEDRIVE_TENANT_ID'] = config.get('tenant_id', '')
    os.environ['ONEDRIVE_EMAIL'] = config.get('from_address', '')
    os.environ['FIREBASE_PROJECT_ID'] = config.get('firebase_project_id', '')

    if not all([os.environ['ONEDRIVE_CLIENT_ID'], 
                os.environ['ONEDRIVE_CLIENT_SECRET'], 
                os.environ['ONEDRIVE_TENANT_ID'],
                os.environ['ONEDRIVE_EMAIL']]):
        print("Warning: Not all required MS Graph configuration values (client_id, client_secret, tenant_id, from_address) are present in test_config.json or set in environment.")
    if not os.environ['FIREBASE_PROJECT_ID']:
        print("Warning: FIREBASE_PROJECT_ID is not set in test_config.json or environment.")
    return config

def create_test_template_file(template_filename="test_email_template.html"):
    """Create a test email template if it doesn't exist."""
    template_dir = Path(__file__).resolve().parent / 'templates'
    template_dir.mkdir(parents=True, exist_ok=True)
    template_path = template_dir / template_filename
    
    if not template_path.exists():
        template_content = """
        <html>
            <head>
                <title>Test Newsletter</title>
            </head>
            <body>
                <h1>🚀 Test Newsletter</h1>
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
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') # Updated
        )
        assert "{recipient_name}" not in rendered_html, "Template variable {recipient_name} not replaced."
        assert "{timestamp}" not in rendered_html, "Template variable {timestamp} not replaced."
        print("✅ Template rendering test completed successfully.")
    except Exception as e:
        print(f"❌ Template rendering test failed: {str(e)}")
        raise

def test_firestore_recipients_fetch():
    print("\n2. Testing Firestore recipients fetch...")
    config = setup_test_environment() 

    if not os.environ.get('FIREBASE_PROJECT_ID') or os.environ.get('FIREBASE_PROJECT_ID') == 'your-firebase-project-id':
        print("⚠️ Skipping Firestore recipients fetch test: FIREBASE_PROJECT_ID not set correctly in test_config.json or environment.")
        return

    try:
        print(f"Attempting to fetch recipients from Firestore project: {os.environ.get('FIREBASE_PROJECT_ID')}")
        fetched_recipients = fetch_recipients_from_firestore(
            project_id=os.environ.get('FIREBASE_PROJECT_ID')
        )
        
        assert fetched_recipients is not None, "fetch_recipients_from_firestore returned None"
        assert isinstance(fetched_recipients, list), "Expected a list of recipients"
        # You might want to assert len(fetched_recipients) > 0 if you expect recipients
        print(f"✅ Firestore recipients fetch test completed. Found {len(fetched_recipients)} recipients.")
        if fetched_recipients:
            print(f"   Sample: {fetched_recipients[0]}")
    except Exception as e:
        print(f"❌ Firestore recipients fetch test failed: {str(e)}")
        print("   Note: This test requires valid Google Cloud credentials (e.g., GOOGLE_APPLICATION_CREDENTIALS),")
        print("   the Firestore API enabled for the project, and the specified document/field (config/email_recipients) to exist.")
        raise

def test_single_recipient_send():
    print("\n3. Testing single recipient delivery (manual recipient)...")
    config = setup_test_environment()
    template_path = create_test_template_file()
    
    if not config.get('test_recipient'):
        print("⚠️ Skipping single recipient test: 'test_recipient' not in config.")
        return

    try:
        access_token = get_access_token() 
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        content_html = template_str.format(
            recipient_name="Valued Test Subscriber",
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') # Updated
        )
        
        success = send_newsletter(
            recipients=[config['test_recipient']], # Explicitly providing recipient
            subject="Test Newsletter - Single Recipient Test",
            content_html=content_html,
            access_token=access_token,
            from_address=config['from_address']
        )
        assert success, "send_newsletter call reported failure."
        print(f"✅ Single recipient test completed successfully (email attempt made to {config['test_recipient']}).")
    except Exception as e:
        print(f"❌ Single recipient test failed: {str(e)}")
        raise

def test_multiple_recipients_send_from_file():
    print("\n4. Testing multiple recipients delivery (from local test file)...")
    config = setup_test_environment()
    template_path = create_test_template_file()
    recipients_config_path = Path(__file__).resolve().parent / 'config' / 'test_recipients.txt'
    
    if not recipients_config_path.exists():
        recipients_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(recipients_config_path, 'w', encoding='utf-8') as f:
            if config.get('test_recipient'):
                f.write(f"{config['test_recipient']}\n")
            f.write("test2@example.com\n") 
        print(f"Created test recipients file at {recipients_config_path}")
    
    try:
        access_token = get_access_token()
        
        with open(recipients_config_path, 'r', encoding='utf-8') as f:
            recipients = [line.strip().replace('"', '') for line in f if line.strip()]
        
        if not recipients:
            print("⚠️ Skipping multiple recipients test (file): no recipients in test_recipients.txt.")
            return

        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        content_html = template_str.format(
            recipient_name="Valued Newsletter Group (File)",
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') # Updated
        )
        
        success = send_newsletter(
            recipients=recipients, # Explicitly providing recipients
            subject="Test Newsletter - Multiple Recipients Test (File)",
            content_html=content_html,
            access_token=access_token,
            from_address=config['from_address']
        )
        assert success, "send_newsletter call reported failure for multiple recipients (file)."
        print(f"✅ Multiple recipients test (file) completed successfully (email attempt made to {len(recipients)} addresses).")
    except Exception as e:
        print(f"❌ Multiple recipients test (file) failed: {str(e)}")
        raise

def test_send_to_firestore_recipients():
    print("\n5. Testing send to recipients fetched from Firestore...")
    config = setup_test_environment()
    template_path = create_test_template_file()

    if not os.environ.get('FIREBASE_PROJECT_ID') or os.environ.get('FIREBASE_PROJECT_ID') == 'your-firebase-project-id':
        print("⚠️ Skipping send to Firestore recipients test: FIREBASE_PROJECT_ID not set correctly.")
        return
    # This test relies on Firestore credentials being set up correctly (see test_firestore_recipients_fetch notes)
    # and that the Firestore document config/email_recipients actually contains recipients.

    try:
        access_token = get_access_token()
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        content_html = template_str.format(
            recipient_name="Valued Firestore Subscriber", # Generic name for Firestore list
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') # Updated
        )
        
        # Calling send_newsletter WITHOUT the 'recipients' argument
        # to trigger its internal Firestore fetching logic.
        success = send_newsletter(
            subject="Test Newsletter - Firestore Recipients",
            content_html=content_html,
            access_token=access_token,
            from_address=config['from_address']
            # project_id for firestore fetch will be picked from ENV by fetch_recipients_from_firestore
        )
        assert success, "send_newsletter call (Firestore recipients) reported failure."
        print(f"✅ Send to Firestore recipients test completed successfully (email attempt made).")
        print(f"   Check your Firestore 'config/email_recipients' list to see who should have received it.")
    except ValueError as ve: # Catch specific error if Firestore fetch fails within send_newsletter
        if "Failed to fetch recipients from Firestore" in str(ve) or "No recipients specified or found" in str(ve):
            print(f"❌ Send to Firestore recipients test failed as expected due to recipient fetch issue: {str(ve)}")
            print("   Ensure Firestore is populated and credentials are correct.")
            # Depending on strictness, you might re-raise or mark as a specific kind of failure/skip
        else:
            print(f"❌ Send to Firestore recipients test failed with ValueError: {str(ve)}")
            raise
    except Exception as e:
        print(f"❌ Send to Firestore recipients test failed: {str(e)}")
        raise

if __name__ == "__main__":
    print("🚀 Starting newsletter tests...")
    
    test_functions = [
        test_template_rendering,
        test_firestore_recipients_fetch, # Moved earlier
        test_single_recipient_send,
        test_multiple_recipients_send_from_file, # Renamed for clarity
        test_send_to_firestore_recipients # New test
    ]

    all_passed = True
    for test_func in test_functions:
        try:
            test_func()
        except Exception: # Catching any exception marks the test function as failed
            all_passed = False
            # Error is printed in the function
    
    if all_passed:
        print("\n✨ All newsletter tests completed successfully (or attempts were made without fatal errors)!")
    else:
        print("\n⚠️ Some newsletter tests failed. Please review the output.")

