import os
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to Python path for importing newsletter.py
# This allows `from scripts.newsletter ...`
sys.path.append(str(Path(__file__).resolve().parent.parent))

def load_test_config():
    """Load test configuration from JSON file."""
    # Assuming test_config.json is in a 'config' subdirectory relative to this test file
    config_path = Path(__file__).parent / 'config' / 'test_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    print("DEBUG: Loaded test config:", {k: ('<REDACTED>' if 'secret' in k or 'key' in k else v) for k, v in config.items()})
    return config

def setup_test_environment():
    """Setup test environment variables from config."""
    config = load_test_config()
    os.environ['ONEDRIVE_CLIENT_ID'] = config['client_id']
    os.environ['ONEDRIVE_CLIENT_SECRET'] = config['client_secret']
    os.environ['ONEDRIVE_TENANT_ID'] = config['tenant_id']
    os.environ['ONEDRIVE_EMAIL'] = config['from_address']
    print("DEBUG: Environment variables set:")
    print(f"  ONEDRIVE_CLIENT_ID: {os.environ.get('ONEDRIVE_CLIENT_ID')}")
    print(f"  ONEDRIVE_CLIENT_SECRET length: {len(os.environ.get('ONEDRIVE_CLIENT_SECRET')) if os.environ.get('ONEDRIVE_CLIENT_SECRET') else None}")
    print(f"  ONEDRIVE_TENANT_ID: {os.environ.get('ONEDRIVE_TENANT_ID')}")
    print(f"  ONEDRIVE_EMAIL: {os.environ.get('ONEDRIVE_EMAIL')}")
    return config

def test_single_recipient():
    """Test sending newsletter to a single recipient."""
    config = setup_test_environment()
    # Import here, after env vars are set, and path is appended.
    try:
        from scripts.newsletter import send_newsletter
    except ImportError:
        print("ERROR: Failed to import 'send_newsletter' from 'scripts.newsletter'.")
        print("Ensure 'scripts/newsletter.py' exists, defines this function, and is in the Python path.")
        print(f"sys.path includes: {Path(__file__).resolve().parent.parent}")
        return

    try:
        template_file_path = Path(__file__).parent / 'templates' / 'test_email_template.html'
        with open(template_file_path, 'r', encoding='utf-8') as f:
            email_html_content = f.read()
        
        # If your test_email_template.html contains placeholders like {timestamp}
        # and {recipient_name} that you format in `test_template_rendering`,
        # you might need to format it here too before sending.
        # For example:
        # email_html_content = email_html_content.format(
        #     timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        #     recipient_name=config.get('test_recipient_name', "Test User") # Example
        # )

        # UPDATED: Call send_newsletter, passing HTML content directly.
        # Assumed parameter name 'html_body'. Change if your function expects a different name.

        # def send_newsletter(access_token, subject, content_html, recipients=None, from_address=None):
        send_newsletter(
            access_token=[config['test_recipient']],
            subject="Test Newsletter",
            html_body=email_html_content,
        )
        print("SUCCESS: Single recipient test completed successfully")
    except TypeError as te:
        print(f"ERROR: Single recipient test failed due to TypeError: {str(te)}")
        print("This likely means the 'send_newsletter' function in 'scripts/newsletter.py' does not expect 'html_body'.")
        print("Please check the function definition in your local 'scripts/newsletter.py' for the correct parameter name for the HTML content.")
        print("Common alternatives could be: 'body', 'content', 'message_html'.")
    except Exception as e:
        print(f"ERROR: Single recipient test failed: {str(e)}")

def test_multiple_recipients():
    """Test sending newsletter to multiple recipients from file."""
    config = setup_test_environment()
    try:
        from scripts.newsletter import send_newsletter
    except ImportError:
        print("ERROR: Failed to import 'send_newsletter' from 'scripts.newsletter'.")
        return

    recipients_path = Path(__file__).parent / 'config' / 'test_recipients.txt'
    try:
        with open(recipients_path, 'r') as f:
            recipients = [line.strip() for line in f if line.strip()]
        
        template_file_path = Path(__file__).parent / 'templates' / 'test_email_template.html'
        with open(template_file_path, 'r', encoding='utf-8') as f:
            email_html_content = f.read()

        # Potentially format email_html_content here too if needed.

        # UPDATED: Call send_newsletter, passing HTML content directly
        send_newsletter(
            recipients=recipients,
            subject="Test Newsletter - Multiple Recipients",
            html_body=email_html_content  # CHANGED from template_path
        )
        print("SUCCESS: Multiple recipients test completed successfully")
    except TypeError as te:
        print(f"ERROR: Multiple recipients test failed due to TypeError: {str(te)}")
        print("This likely means the 'send_newsletter' function in 'scripts/newsletter.py' does not expect 'html_body'.")
        print("Please check the function definition for the correct parameter name.")
    except Exception as e:
        print(f"ERROR: Multiple recipients test failed: {str(e)}")

def test_template_rendering():
    """Test template rendering with different variables."""
    setup_test_environment() # May not be needed if template doesn't use env vars
    template_path = Path(__file__).parent / 'templates' / 'test_email_template.html'
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Ensure all expected placeholders are provided for formatting
        rendered = template_content.format(
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            recipient_name="Test User" 
            # Add any other placeholders your template expects here
        )
        print("SUCCESS: Template rendering test completed successfully")
        print("Preview of rendered template:")
        print("-" * 50)
        print(rendered)
        print("-" * 50)
    except KeyError as ke:
        print(f"ERROR: Template rendering test failed due to missing placeholder: {str(ke)}")
        print("Ensure your template file 'test_email_template.html' only uses placeholders provided here.")
    except Exception as e:
        print(f"ERROR: Template rendering test failed: {str(e)}")

if __name__ == "__main__":
    print("Starting newsletter tests...")
    print("\n1. Testing single recipient delivery...")
    test_single_recipient()
    print("\n2. Testing multiple recipients delivery...")
    test_multiple_recipients()
    print("\n3. Testing template rendering...")
    test_template_rendering()
