"""
Test Environment Loading
Verifies that .env file is properly loaded and all credentials are available
"""

import os
from pathlib import Path

print("=" * 70)
print("Environment Variable Loading Test")
print("=" * 70)

# Check .env file exists
env_file = Path('.env')
print(f"\n1. Checking .env file...")
print(f"   Location: {env_file.absolute()}")
print(f"   Exists: {'✓ Yes' if env_file.exists() else '✗ No'}")

if env_file.exists():
    print(f"   Size: {env_file.stat().st_size} bytes")
    print(f"\n   Contents preview:")
    with open(env_file, 'r') as f:
        for i, line in enumerate(f, 1):
            if not line.strip().startswith('#') and '=' in line:
                key = line.split('=')[0]
                print(f"   - {key}")

# Test loading with python-dotenv
print(f"\n2. Loading .env with python-dotenv...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("   ✓ dotenv loaded successfully")
except ImportError:
    print("   ✗ python-dotenv not installed")

# Check critical environment variables
print(f"\n3. Checking environment variables...")

critical_vars = {
    'GEMINI_API_KEY': 'Gemini API Key',
    'GOOGLE_API_KEY': 'Google API Key (alias)',
    'GOOGLE_APPLICATION_CREDENTIALS': 'Google Cloud Credentials',
    'NEO4J_PASSWORD': 'Neo4j Password'
}

for var, description in critical_vars.items():
    value = os.getenv(var)
    if value:
        # Mask sensitive data
        if 'KEY' in var or 'PASSWORD' in var:
            masked = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
            print(f"   ✓ {var}: {masked}")
        else:
            print(f"   ✓ {var}: {value}")
    else:
        print(f"   ✗ {var}: Not set")

# Test if credentials file exists
print(f"\n4. Validating Google Cloud credentials file...")
creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if creds_path:
    creds_file = Path(creds_path)
    if creds_file.exists():
        print(f"   ✓ File exists: {creds_file.name}")
        print(f"   Size: {creds_file.stat().st_size} bytes")
    else:
        print(f"   ✗ File not found: {creds_path}")
else:
    print(f"   ✗ GOOGLE_APPLICATION_CREDENTIALS not set")

# Test config.py loading
print(f"\n5. Testing app.config.Settings...")
try:
    from app.config import settings
    print(f"   ✓ Settings loaded")
    print(f"   GEMINI_API_KEY set: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    print(f"   Google Vision enabled: {settings.google_vision_enabled}")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
except Exception as e:
    print(f"   ✗ Failed to load settings: {e}")

# Test OSINTAnalyzer initialization
print(f"\n6. Testing OSINTAnalyzer initialization...")
try:
    from core.osint_analyzer import OSINTAnalyzer
    analyzer = OSINTAnalyzer()
    print(f"   ✓ OSINTAnalyzer initialized")
    print(f"   LLM configured: {'Yes' if analyzer.llm.model else 'No'}")
    print(f"   Google Vision enabled: {'Yes' if analyzer.vision.is_enabled() else 'No'}")
except Exception as e:
    print(f"   ✗ Failed to initialize: {e}")

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)
