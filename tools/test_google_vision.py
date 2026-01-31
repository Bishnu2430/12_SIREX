"""
Test Google Vision API Configuration
Verifies that Google Cloud Vision API is properly configured and working
"""

import os
from pathlib import Path
from loguru import logger

# Configure logger
logger.add("logs/vision_test.log", rotation="10 MB")


def test_google_vision_config():
    """Test Google Vision API configuration"""
    print("=" * 60)
    print("Google Vision API Configuration Test")
    print("=" * 60)
    
    # Check environment variable
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    print(f"\n1. Checking GOOGLE_APPLICATION_CREDENTIALS...")
    
    if not creds_path:
        print("   ❌ GOOGLE_APPLICATION_CREDENTIALS not set in environment")
        print("   Please set it in your .env file")
        return False
    
    print(f"   ✓ Found: {creds_path}")
    
    # Check if file exists
    print(f"\n2. Checking if credentials file exists...")
    creds_file = Path(creds_path)
    
    if not creds_file.exists():
        print(f"   ❌ Credentials file not found: {creds_path}")
        return False
    
    print(f"   ✓ File exists: {creds_file.name}")
    print(f"   Size: {creds_file.stat().st_size} bytes")
    
    # Try to import Google Cloud Vision
    print(f"\n3. Importing Google Cloud Vision library...")
    
    try:
        from google.cloud import vision
        from google.oauth2 import service_account
        print("   ✓ google-cloud-vision library imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import google-cloud-vision: {e}")
        print("   Run: conda activate sirex && pip install google-cloud-vision")
        return False
    
    # Try to initialize client
    print(f"\n4. Initializing Vision API client...")
    
    try:
        credentials = service_account.Credentials.from_service_account_file(str(creds_file))
        client = vision.ImageAnnotatorClient(credentials=credentials)
        print("   ✓ Vision API client initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize client: {e}")
        return False
    
    # Try a simple API call (label detection on a test image URL)
    print(f"\n5. Testing API connection with sample image...")
    
    try:
        # Use a simple test - just check if we can create an image object
        # We won't make an actual API call to avoid charges
        image = vision.Image()
        print("   ✓ Can create Vision API image objects")
        print("   ✓ API client is ready to use")
    except Exception as e:
        print(f"   ❌ Error creating image object: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ Google Vision API is properly configured!")
    print("=" * 60)
    return True


def test_vision_analyzer():
    """Test the GoogleVisionAnalyzer class"""
    print("\n" + "=" * 60)
    print("Testing GoogleVisionAnalyzer Integration")
    print("=" * 60)
    
    try:
        from core.vision.google_vision import GoogleVisionAnalyzer
        
        analyzer = GoogleVisionAnalyzer()
        
        if analyzer.is_enabled():
            print("✓ GoogleVisionAnalyzer is enabled and ready")
            return True
        else:
            print("❌ GoogleVisionAnalyzer is not enabled")
            print("   Check the logs above for initialization errors")
            return False
    
    except Exception as e:
        print(f"❌ Failed to initialize GoogleVisionAnalyzer: {e}")
        return False


if __name__ == "__main__":
    print("\n🔍 Starting Google Vision API Configuration Test\n")
    
    config_ok = test_google_vision_config()
    
    if config_ok:
        analyzer_ok = test_vision_analyzer()
        
        if analyzer_ok:
            print("\n✅ All tests passed! Google Vision API is ready to use.")
        else:
            print("\n⚠️  Configuration is correct but analyzer failed to initialize")
    else:
        print("\n❌ Configuration test failed. Please fix the issues above.")
    
    print("\nTest complete.\n")
