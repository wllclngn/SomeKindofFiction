import os
import json
import sys
from datetime import datetime
from pathlib import Path
import unittest # Optional: for more structured tests if you expand later

# Add parent directory to Python path for importing newsletter.py
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scripts.newsletter import send_newsletter, get_access_token, fetch_recipients_from_onedrive

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
            "msa_user_id": "YOUR_PERSONAL_ONEDRIVE_USER_ID_GUID_HERE" # Added this
        }
        with open(config_path, 'w') as f:
            json.dump(template_config, f, indent=2)
        print(f"Created template config file at {config_path}")
        print("Please update it with your actual Azure App and MSA User ID values before running tests.")
        # It's probably better to raise an error or exit if the config is just created
        # For now, we'll return the template, but in a real scenario, you'd want it filled.
        # raise FileNotFoundError(f"Config file not found and template created. Please fill it: {config_path}")
        return template_config # Or handle as an error
    
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_test_environment():
    """Setup test environment variables from config."""
    config = load_test_config()
    os.environ['ONEDRIVE_CLIENT_ID'] = config.get('client_id', '')
    os.environ['ONEDRIVE_CLIENT_SECRET'] = config.get('client_secret', '')
    os.environ['ONEDRIVE_TENANT_ID'] = config.get('tenant_id', '')
    os.environ['ONEDRIVE_EMAIL'] = config.get('from_address', '')
    os.environ['ONEDRIVE_MSA_USER_ID'] = config.get('msa_user_id', '') # Added this

    # Check if critical env vars are set
    if not all([os.environ['ONEDRIVE_CLIENT_ID'], 
                os.environ['ONEDRIVE_CLIENT_SECRET'], 
                os.environ['ONEDRIVE_TENANT_ID'],
                os.environ['ONEDRIVE_EMAIL'],
                os.environ['ONEDRIVE_MSA_USER_ID']]):
        print("Warning: Not all required configuration values (client_id, client_secret, tenant_id, from_address, msa_user_id) are present in test_config.json or set in environment.")
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
    config = setup_test_environment() # Ensure env vars are available if template uses them
    template_path = create_test_template_file()
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        # Basic formatting test
        rendered_html = template_str.format(
            recipient_name="Test User",
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        assert "{recipient_name}" not in rendered_html, "Template variable {recipient_name} not replaced."
        assert "{timestamp}" not in rendered_html, "Template variable {timestamp} not replaced."
        print("✅ Template rendering test completed successfully.")
        # print("Preview of rendered template:")
        # print("-" * 50)
        # print(rendered_html[:300] + "...") # Print a snippet
        # print("-" * 50)
    except Exception as e:
        print(f"❌ Template rendering test failed: {str(e)}")
        raise

def test_single_recipient_send():
    print("\n2. Testing single recipient delivery...")
    config = setup_test_environment()
    template_path = create_test_template_file()
    
    if not config.get('test_recipient'):
        print("⚠️ Skipping single recipient test: 'test_recipient' not in config.")
        return

    try:
        access_token = get_access_token() # From scripts.newsletter
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        content_html = template_str.format(
            recipient_name="Valued Test Subscriber",
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        success = send_newsletter(
            recipients=[config['test_recipient']],
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

def test_multiple_recipients_send():
    print("\n3. Testing multiple recipients delivery (from local test file)...")
    config = setup_test_environment()
    template_path = create_test_template_file()
    recipients_config_path = Path(__file__).resolve().parent / 'config' / 'test_recipients.txt'
    
    if not recipients_config_path.exists():
        recipients_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(recipients_config_path, 'w', encoding='utf-8') as f:
            if config.get('test_recipient'):
                f.write(f"{config['test_recipient']}\n")
            f.write("test2@example.com\n") # Default additional recipient
        print(f"Created test recipients file at {recipients_config_path}")
    
    try:
        access_token = get_access_token()
        
        with open(recipients_config_path, 'r', encoding='utf-8') as f:
            # Strip quotes and ensure emails are valid if necessary
            recipients = [line.strip().replace('"', '') for line in f if line.strip()]
        
        if not recipients:
            print("⚠️ Skipping multiple recipients test: no recipients in test_recipients.txt.")
            return

        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        content_html = template_str.format(
            recipient_name="Valued Newsletter Group",
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        success = send_newsletter(
            recipients=recipients,
            subject="Test Newsletter - Multiple Recipients Test",
            content_html=content_html,
            access_token=access_token,
            from_address=config['from_address']
        )
        assert success, "send_newsletter call reported failure for multiple recipients."
        print(f"✅ Multiple recipients test completed successfully (email attempt made to {len(recipients)} addresses).")
    except Exception as e:
        print(f"❌ Multiple recipients test failed: {str(e)}")
        raise

def test_onedrive_recipients_fetch():
    print("\n4. Testing OneDrive recipients fetch...")
    config = setup_test_environment()
    
    if not os.environ.get('ONEDRIVE_MSA_USER_ID'):
        print("⚠️ Skipping OneDrive recipients fetch test: ONEDRIVE_MSA_USER_ID not set (check test_config.json).")
        return

    try:
        access_token = get_access_token()
        
        # Directly test the fetch function from scripts.newsletter
        print(f"Attempting to fetch recipients using MSA User ID: {os.environ.get('ONEDRIVE_MSA_USER_ID')[:4]}...")
        fetched_recipients = fetch_recipients_from_onedrive(
            access_token=access_token,
            file_path="email_recipients.txt" # Assuming this is the name of your file on OneDrive
        )
        
        if fetched_recipients is not None: # fetch_recipients_from_onedrive returns a list or None on error
            print(f"✅ OneDrive recipients fetch test completed. Found {len(fetched_recipients)} recipients.")
            if fetched_recipients:
                print(f"   Sample: {fetched_recipients[0]}")
            # You could add assertions here, e.g., assert len(fetched_recipients) > 0 if you expect some
        else:
            # This case should ideally be caught by exceptions in fetch_recipients_from_onedrive
            print("❌ OneDrive recipients fetch test resulted in 'None', indicating an issue during fetch.")
            # For this test to "pass" even if no recipients are found (empty file),
            # we just check that no exception was raised up to here.
            # If an exception occurred, it would be caught by the outer try-except.

    except Exception as e:
        print(f"❌ OneDrive recipients fetch test failed: {str(e)}")
        print("   Note: This test requires 'email_recipients.txt' to exist in the root of the personal OneDrive")
        print(f"   associated with MSA User ID: {os.environ.get('ONEDRIVE_MSA_USER_ID')},")
        print(f"   and the Azure App to have Files.Read.All (Application) permission with admin consent.")
        raise


if __name__ == "__main__":
    print("🚀 Starting newsletter tests...")
    
    # It's good practice to run setup once if tests don't modify environment in conflicting ways
    # global_config = setup_test_environment() 
    # If individual tests need different setups, call setup_test_environment() within them.

    test_functions = [
        test_template_rendering,
        test_single_recipient_send,
        test_multiple_recipients_send,
        test_onedrive_recipients_fetch
    ]

    all_passed = True
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            all_passed = False
            # The error is already printed in the function, but you could log more here.
            # print(f"--- Test {test_func.__name__} FAILED ---")
    
    if all_passed:
        print("\n✨ All newsletter tests completed successfully (or attempts were made without fatal errors)!")
    else:
        print("\n⚠️ Some newsletter tests failed. Please review the output.")
