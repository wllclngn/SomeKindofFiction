import os
import json
from pathlib import Path
from datetime import datetime, timezone
import unittest
import sys

# Add the script directory to the Python path to allow direct import
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.append(str(SCRIPT_DIR))

# Now import the functions from newsletter.py
from newsletter import get_access_token, send_newsletter, render_template

# Configuration - Load from a JSON file or environment variables
# For this example, assuming a config.json in the tests directory
# In a real CI environment, these would be environment variables
CONFIG_FILE = Path(__file__).resolve().parent / "test_config.json"
TEMPLATES_DIR = Path(__file__).resolve().parent / "test_templates"
DEFAULT_TEMPLATE = TEMPLATES_DIR / "test_email_template.html"

def load_test_config():
    """Loads test configuration."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    else:
        # Fallback to environment variables if config file doesn't exist
        config = {
            "client_id": os.getenv("ONEDRIVE_CLIENT_ID"),
            "client_secret": os.getenv("ONEDRIVE_CLIENT_SECRET"),
            "tenant_id": os.getenv("ONEDRIVE_TENANT_ID"),
            "from_address": os.getenv("ONEDRIVE_EMAIL"),
            "test_recipient": os.getenv("TEST_RECIPIENT_EMAIL", "test@example.com"),
            "test_recipient_2": os.getenv("TEST_RECIPIENT_EMAIL_2", "test2@example.com")
        }
    
    missing_keys = [key for key, value in config.items() if value is None and key not in ["test_recipient_2"]] # test_recipient_2 is optional for single test
    if missing_keys:
        raise ValueError(f"Missing configuration for: {', '.join(missing_keys)}. Check {CONFIG_FILE} or environment variables.")
    
    print(f"DEBUG: Loaded test config: {{'client_id': '{config['client_id']}', 'client_secret': '<REDACTED>', 'tenant_id': '{config['tenant_id']}', 'from_address': '{config['from_address']}', 'test_recipient': '{config['test_recipient']}'}}")
    return config

def set_env_vars_from_config(config):
    """Sets environment variables that the newsletter script expects."""
    os.environ['CLIENT_ID'] = config['client_id']
    os.environ['CLIENT_SECRET'] = config['client_secret']
    os.environ['TENANT_ID'] = config['tenant_id']
    os.environ['ONEDRIVE_EMAIL'] = config['from_address']
    # RECIPIENT_FILE_PATH is not used if recipients are passed directly
    # os.environ['RECIPIENT_FILE_PATH'] = "test_recipients.txt" 
    
    print("DEBUG: Environment variables set:")
    print(f"  CLIENT_ID: {os.getenv('CLIENT_ID')}")
    print(f"  CLIENT_SECRET length: {len(os.getenv('CLIENT_SECRET')) if os.getenv('CLIENT_SECRET') else 0}")
    print(f"  TENANT_ID: {os.getenv('TENANT_ID')}")
    print(f"  ONEDRIVE_EMAIL: {os.getenv('ONEDRIVE_EMAIL')}")


class TestNewsletter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = load_test_config()
        set_env_vars_from_config(cls.config)
        
        # Create a dummy template file if it doesn't exist
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        if not DEFAULT_TEMPLATE.exists():
            with open(DEFAULT_TEMPLATE, "w") as f:
                f.write("<html><body><h1>{{title}}</h1><p>Sent at: {{date}}</p><p>Hello {{name}}!</p><p>{{body_content}}</p></body></html>")
            print(f"DEBUG: Created dummy template at {DEFAULT_TEMPLATE}")

        try:
            cls.access_token = get_access_token()
        except Exception as e:
            print(f"FATAL: Could not obtain access token during setUpClass: {e}")
            cls.access_token = None # Ensure it's None if fetching fails

    defassertTrue(self.access_token, "Access token must be obtained for email tests.")

        # 1. Define template context for this email test
    current_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        email_subject = f"Test Email - Single Recipient - {current_time_utc}"
        email_context = {
            "title": "Single Recipient Test",
            "date": current_time_utc,
            "name": "Test User Alpha",
            "body_content": "This is a test email for a single recipient."
        }

        # 2. Render the HTML content using the template
        # Assuming DEFAULT_TEMPLATE is the correct template to use
        html_for_email = render_template(template_path=str(DEFAULT_TEMPLATE), context=email_context)
        self.assertTrue(html_for_email, "HTML content should be rendered.")

        # 3. Call send_newsletter with the rendered HTML
        send_newsletter(
            access_token=self.access_token,
            subject=email_subject,
            content_html=html_for_email, # Pass the rendered HTML string
            recipients=[self.config['test_recipient']],
            from_address=self.config['from_address']
        )
        print(f"SUCCESS: Single recipient test passed (or at least did not raise an immediate error for send_newsletter).")

    def test_02_multiple_recipients(self):
        print("\n2. Testing multiple recipients delivery...")
        self.assertTrue(self.access_token, "Access token must be obtained for email tests.")

        recipients_list = [self.config['test_recipient']]
        if self.config.get('test_recipient_2'): # Add second recipient if configured
            recipients_list.append(self.config['test_recipient_2'])
        
        if len(recipients_list) < 2:
            print("SKIPPING: Multiple recipients test needs at least two configured test recipients (test_recipient, test_recipient_2).")
            self.skipTest("Not enough recipients configured for multiple recipients test.")
            return

        current_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        email_subject = f"Test Email - Multiple Recipients - {current_time_utc}"
        email_context = {
            "title": "Multiple Recipients Test",
            "date": current_time_utc,
            "name": "Test Users Group",
            "body_content": "This is a test email for multiple recipients."
        }
        html_for_email = render_template(template_path=str(DEFAULT_TEMPLATE), context=email_context)
        self.assertTrue(html_for_email, "HTML content should be rendered.")

        send_newsletter(
            access_token=self.access_token,
            subject=email_subject,
            content_html=html_for_email, # Pass the rendered HTML string
            recipients=recipients_list,
            from_address=self.config['from_address']
        )
        print(f"SUCCESS: Multiple recipients test passed (or at least did not raise an immediate error for send_newsletter).")

    def test_03_template_rendering(self):
        print("\n3. Testing template rendering...")
        # This test seemed to be working for you, so keeping its logic similar
        test_context = {
            "title": "Test Newsletter",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "name": "Test User",
            "body_content": "Test content goes here."
        }
        
        rendered_html = render_template(template_path=str(DEFAULT_TEMPLATE), context=test_context)
        self.assertIn("Test Newsletter", rendered_html)
        self.assertIn("Test User", rendered_html)
        self.assertIn("Test content goes here", rendered_html)
        
        print("SUCCESS: Template rendering test completed successfully")
        print("Preview of rendered template:")
        print("--------------------------------------------------")
        print(rendered_html)
        print("--------------------------------------------------")


if __name__ == "__main__":
    print("Starting newsletter tests (unittest framework)...")
    # This allows running tests with `python tests/test_newsletter.py`
    # The functions test_01_single_recipient etc. will be run by the unittest runner
    unittest.main()
