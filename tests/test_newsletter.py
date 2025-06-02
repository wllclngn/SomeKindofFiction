import os
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path for importing newsletter.py
sys.path.append(str(Path(__file__).parent.parent))
from scripts.newsletter import send_newsletter

def load_test_config():
    """Load test configuration from JSON file."""
    config_path = Path(__file__).parent / 'config' / 'test_config.json'
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_test_environment():
    """Setup test environment variables from config."""
    config = load_test_config()
    os.environ['ONEDRIVE_CLIENT_ID'] = config['client_id']
    os.environ['ONEDRIVE_CLIENT_SECRET'] = config['client_secret']
    os.environ['ONEDRIVE_TENANT_ID'] = config['tenant_id']
    os.environ['ONEDRIVE_EMAIL'] = config['from_address']
    return config

def test_single_recipient():
    """Test sending newsletter to a single recipient."""
    config = setup_test_environment()
    try:
        send_newsletter(
            recipients=[config['test_recipient']],
            subject="Test Newsletter",
            template_path=str(Path(__file__).parent / 'templates' / 'test_email_template.html')
        )
        print("✅ Single recipient test completed successfully")
    except Exception as e:
        print(f"❌ Single recipient test failed: {str(e)}")

def test_multiple_recipients():
    """Test sending newsletter to multiple recipients from file."""
    setup_test_environment()
    recipients_path = Path(__file__).parent / 'config' / 'test_recipients.txt'
    try:
        with open(recipients_path, 'r') as f:
            recipients = [line.strip() for line in f if line.strip()]
        send_newsletter(
            recipients=recipients,
            subject="Test Newsletter - Multiple Recipients",
            template_path=str(Path(__file__).parent / 'templates' / 'test_email_template.html')
        )
        print("✅ Multiple recipients test completed successfully")
    except Exception as e:
        print(f"❌ Multiple recipients test failed: {str(e)}")

def test_template_rendering():
    """Test template rendering with different variables."""
    setup_test_environment()
    template_path = Path(__file__).parent / 'templates' / 'test_email_template.html'
    try:
        with open(template_path, 'r') as f:
            template = f.read()
        rendered = template.format(
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            recipient_name="Test User"
        )
        print("✅ Template rendering test completed successfully")
        print("Preview of rendered template:")
        print("-" * 50)
        print(rendered)
        print("-" * 50)
    except Exception as e:
        print(f"❌ Template rendering test failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting newsletter tests...")
    print("\n1. Testing single recipient delivery...")
    test_single_recipient()
    print("\n2. Testing multiple recipients delivery...")
    test_multiple_recipients()
    print("\n3. Testing template rendering...")
    test_template_rendering()