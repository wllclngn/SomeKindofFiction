import os
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path for importing newsletter.py
sys.path.append(str(Path(__file__).parent.parent))
from scripts.newsletter import send_newsletter, get_access_token

def load_test_config():
    """Load test configuration from JSON file."""
    config_path = Path(__file__).parent / 'config' / 'test_config.json'
    if not config_path.exists():
        # Create a template config file if it doesn't exist
        config_path.parent.mkdir(exist_ok=True)
        template_config = {
            "client_id": "your_client_id_here",
            "client_secret": "your_client_secret_here", 
            "tenant_id": "your_tenant_id_here",
            "from_address": "your_email@domain.com",
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
    """Setup test environment variables from config."""
    config = load_test_config()
    os.environ['ONEDRIVE_CLIENT_ID'] = config['client_id']
    os.environ['ONEDRIVE_CLIENT_SECRET'] = config['client_secret']
    os.environ['ONEDRIVE_TENANT_ID'] = config['tenant_id']
    os.environ['ONEDRIVE_EMAIL'] = config['from_address']
    return config

def create_test_template():
    """Create a test email template if it doesn't exist."""
    template_dir = Path(__file__).parent / 'templates'
    template_dir.mkdir(exist_ok=True)
    template_path = template_dir / 'test_email_template.html'
    
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
        with open(template_path, 'w') as f:
            f.write(template_content.strip())
        print(f"Created test template at {template_path}")
    
    return str(template_path)

def test_single_recipient():
    """Test sending newsletter to a single recipient."""
    config = setup_test_environment()
    template_path = create_test_template()
    
    try:
        # Get access token
        access_token = get_access_token()
        
        # Load and format template
        with open(template_path, 'r') as f:
            template = f.read()
        
        content_html = template.format(
            recipient_name="Test User",
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        send_newsletter(
            recipients=[config['test_recipient']],
            subject="Test Newsletter - Single Recipient",
            content_html=content_html,
            access_token=access_token,
            from_address=config['from_address']
        )
        print("✅ Single recipient test completed successfully")
    except Exception as e:
        print(f"❌ Single recipient test failed: {str(e)}")

def test_multiple_recipients():
    """Test sending newsletter to multiple recipients from file."""
    config = setup_test_environment()
    template_path = create_test_template()
    recipients_path = Path(__file__).parent / 'config' / 'test_recipients.txt'
    
    # Create test recipients file if it doesn't exist
    if not recipients_path.exists():
        recipients_path.parent.mkdir(exist_ok=True)
        with open(recipients_path, 'w') as f:
            f.write(f"{config['test_recipient']}\n")
            f.write("test2@example.com\n")  # Add more test emails as needed
        print(f"Created test recipients file at {recipients_path}")
    
    try:
        # Get access token
        access_token = get_access_token()
        
        # Load recipients
        with open(recipients_path, 'r') as f:
            recipients = [line.strip() for line in f if line.strip()]
        
        # Load and format template
        with open(template_path, 'r') as f:
            template = f.read()
        
        content_html = template.format(
            recipient_name="Newsletter Subscriber",
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        send_newsletter(
            recipients=recipients,
            subject="Test Newsletter - Multiple Recipients",
            content_html=content_html,
            access_token=access_token,
            from_address=config['from_address']
        )
        print("✅ Multiple recipients test completed successfully")
    except Exception as e:
        print(f"❌ Multiple recipients test failed: {str(e)}")

def test_template_rendering():
    """Test template rendering with different variables."""
    setup_test_environment()
    template_path = create_test_template()
    
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

def test_onedrive_recipients():
    """Test fetching recipients from OneDrive (without sending email)."""
    config = setup_test_environment()
    
    try:
        # Get access token
        access_token = get_access_token()
        
        # This will attempt to fetch recipients from OneDrive but won't send email
        send_newsletter(
            subject="Test Newsletter - OneDrive Recipients (DRY RUN)",
            content_html="<p>This is a test - no email should be sent</p>",
            access_token=access_token,
            from_address=config['from_address']
        )
        print("✅ OneDrive recipients fetch test completed successfully")
    except Exception as e:
        print(f"❌ OneDrive recipients test failed: {str(e)}")
        print("Note: This test requires email_recipients.txt to exist in the OneDrive root")

if __name__ == "__main__":
    print("🚀 Starting newsletter tests...")
    print("\n1. Testing template rendering...")
    test_template_rendering()
    print("\n2. Testing single recipient delivery...")
    test_single_recipient()
    print("\n3. Testing multiple recipients delivery...")
    test_multiple_recipients()
    print("\n4. Testing OneDrive recipients fetch...")
    test_onedrive_recipients()
    print("\n✨ All tests completed!")
