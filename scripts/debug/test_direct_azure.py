#!/usr/bin/env python3
"""
Direct Azure OpenAI test (without Agno) to isolate the authentication issue
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_direct_azure():
    print("🔧 Testing Direct Azure OpenAI Connection")
    print("=" * 50)
    
    # Get credentials
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    deployment = os.getenv('AZURE_DEPLOYMENT')
    
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"Endpoint: {endpoint}")
    print(f"Deployment: {deployment}")
    print(f"API Version: 2024-12-01-preview")
    print()
    
    try:
        from openai import AzureOpenAI
        
        # Create client with exact parameters you specified
        client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-12-01-preview",
            azure_endpoint=endpoint
        )
        
        print("✓ Azure OpenAI client created")
        
        # Test simple completion
        response = client.chat.completions.create(
            model="gpt-4-1",  # Using your exact deployment name
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, Azure OpenAI is working!'"}
            ],
            max_tokens=50,
            temperature=0
        )
        
        message = response.choices[0].message.content
        print(f"✅ SUCCESS! Azure OpenAI Response: {message}")
        return True
        
    except Exception as e:
        print(f"❌ Direct Azure OpenAI Test Failed: {e}")
        
        # Check for specific error patterns
        error_str = str(e).lower()
        
        if "401" in error_str:
            print("\n🔧 401 Unauthorized - Possible Issues:")
            print("  • API key doesn't match the endpoint resource")
            print("  • API key has expired or been regenerated")
            print("  • Wrong Azure subscription/resource")
            
        elif "404" in error_str:
            print("\n🔧 404 Not Found - Possible Issues:")
            print("  • Deployment name 'gpt-4-1' doesn't exist")
            print("  • Model not deployed in this resource")
            
        elif "model" in error_str or "deployment" in error_str:
            print("\n🔧 Model/Deployment Issue:")
            print("  • Check if 'gpt-4-1' is the correct deployment name")
            print("  • Verify model is deployed and running")
            
        return False

def test_different_model_names():
    """Test with different common model deployment names"""
    print("\n🔍 Testing Common Deployment Names")
    print("=" * 40)
    
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    
    common_deployments = [
        "gpt-4-1",
        "gpt-4", 
        "gpt-4o",
        "gpt-35-turbo",
        "gpt-4-32k"
    ]
    
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-12-01-preview", 
            azure_endpoint=endpoint
        )
        
        for deployment in common_deployments:
            try:
                print(f"Testing deployment: {deployment}")
                response = client.chat.completions.create(
                    model=deployment,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5,
                    temperature=0
                )
                
                print(f"  ✅ {deployment} works!")
                return deployment
                
            except Exception as e:
                if "404" in str(e):
                    print(f"  ❌ {deployment} - Not found")
                elif "401" in str(e):
                    print(f"  ❌ {deployment} - Unauthorized (auth issue)")
                else:
                    print(f"  ❌ {deployment} - {str(e)[:50]}...")
        
        print("\n❌ No working deployments found")
        return None
        
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        return None

if __name__ == "__main__":
    print("Direct Azure OpenAI Test (No Agno)")
    print("This bypasses Agno to test pure Azure OpenAI connection\n")
    
    # Test direct connection
    success = test_direct_azure()
    
    if not success:
        # If that fails, try different deployment names
        working_deployment = test_different_model_names()
        
        if working_deployment:
            print(f"\n🎉 Found working deployment: {working_deployment}")
            print("Update your AZURE_DEPLOYMENT environment variable to use this name")
        else:
            print("\n💡 Next steps:")
            print("1. Verify your Azure OpenAI resource exists")
            print("2. Check the exact deployment names in Azure Portal")
            print("3. Generate a new API key if needed")
            print("4. Confirm you have the right endpoint URL")