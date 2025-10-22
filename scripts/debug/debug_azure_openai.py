#!/usr/bin/env python3
"""
Debug script to test Azure OpenAI connection
Run this to verify your Azure OpenAI configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_openai():
    print("🔍 Testing Azure OpenAI Configuration")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION')
    deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
    
    print("📋 Configuration Check:")
    print(f"  API Key: {'✓ Set' if api_key else '✗ Missing'} ({len(api_key) if api_key else 0} chars)")
    print(f"  Endpoint: {'✓ Set' if endpoint else '✗ Missing'} ({endpoint if endpoint else 'None'})")
    print(f"  API Version: {'✓ Set' if api_version else '✗ Missing'} ({api_version if api_version else 'None'})")
    print(f"  Deployment: {'✓ Set' if deployment_name else '✗ Missing'} ({deployment_name if deployment_name else 'None'})")
    print()
    
    if not all([api_key, endpoint, api_version, deployment_name]):
        print("❌ Missing required configuration. Please check your .env file.")
        return False
    
    # Test OpenAI import
    try:
        from openai import AzureOpenAI
        print("✓ OpenAI package imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import OpenAI package: {e}")
        print("💡 Run: pip install openai")
        return False
    
    # Test Azure OpenAI client initialization
    try:
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        print("✓ Azure OpenAI client created successfully")
    except Exception as e:
        print(f"❌ Failed to create Azure OpenAI client: {e}")
        return False
    
    # Test simple API call
    print("\n🧪 Testing API Connection...")
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, this is a test!'"}
            ],
            max_tokens=50,
            temperature=0
        )
        
        message = response.choices[0].message.content
        print(f"✅ API Test Successful!")
        print(f"📝 Response: {message}")
        return True
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        
        # Provide specific troubleshooting based on error
        error_str = str(e).lower()
        print("\n🔧 Troubleshooting:")
        
        if "401" in error_str or "unauthorized" in error_str:
            print("  • Check if your API key is correct")
            print("  • Verify the key hasn't expired")
            print("  • Make sure you're using the right Azure resource")
            
        elif "404" in error_str or "not found" in error_str:
            print("  • Check if your deployment name is correct")
            print("  • Verify the deployment exists in your Azure resource")
            print("  • Make sure the model is deployed and running")
            
        elif "endpoint" in error_str:
            print("  • Check if your endpoint URL is correct")
            print("  • Make sure it ends with a trailing slash")
            print("  • Verify you're using the right region")
            
        else:
            print("  • Check Azure OpenAI service status")
            print("  • Verify your subscription is active")
            print("  • Try a different API version")
        
        return False

if __name__ == "__main__":
    print("Azure OpenAI Debug Script")
    print("This will test your Azure OpenAI configuration\n")
    
    success = test_azure_openai()
    
    if success:
        print("\n🎉 Configuration is working! Your MMA Query feature should work now.")
    else:
        print("\n❌ Configuration needs to be fixed before MMA Query will work.")
        print("\n💡 Common fixes:")
        print("1. Double-check your API key in the .env file")
        print("2. Verify your Azure OpenAI resource is active")
        print("3. Make sure your deployment name matches exactly")
        print("4. Check that you have the correct endpoint URL")