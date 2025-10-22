#!/usr/bin/env python3
"""
Try to find the correct Azure OpenAI endpoint by testing common patterns
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_endpoint(endpoint_url, description):
    """Test a specific endpoint"""
    try:
        from openai import AzureOpenAI
        
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-02-01",  # Use stable version
            azure_endpoint=endpoint_url
        )
        
        # Try a simple completion
        response = client.chat.completions.create(
            model="gpt-4-1",  # Try the deployment name provided
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print(f"✅ SUCCESS: {description}")
        print(f"   Endpoint: {endpoint_url}")
        return True, endpoint_url
        
    except Exception as e:
        error_str = str(e)
        if "401" in error_str:
            status = "❌ 401 Unauthorized"
        elif "404" in error_str:
            status = "⚠️  404 Not Found (endpoint exists, deployment might not)"
        elif "403" in error_str:
            status = "⚠️  403 Forbidden (endpoint exists, permission issue)"
        else:
            status = f"❌ {str(e)[:50]}..."
            
        print(f"{status}: {description}")
        
        # Return True for 404/403 as it means the endpoint exists
        return "404" in error_str or "403" in error_str, endpoint_url if "404" in error_str or "403" in error_str else None

def main():
    print("🔍 Searching for Correct Azure OpenAI Endpoint")
    print("=" * 55)
    
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    # Common Azure OpenAI endpoint patterns
    patterns_to_test = [
        # Current pattern
        ("https://azure-oai-east2.openai.azure.com/", "Provided endpoint"),
        
        # Common resource naming patterns
        ("https://azure-oai-east.openai.azure.com/", "Without '2' suffix"),
        ("https://azure-oai.openai.azure.com/", "Base name without region"),
        ("https://azure-openai-east2.openai.azure.com/", "With full 'openai' name"),
        ("https://azure-openai.openai.azure.com/", "Standard naming"),
        
        # Different regions
        ("https://azure-oai-west2.openai.azure.com/", "West US 2 region"),
        ("https://azure-oai-central.openai.azure.com/", "Central US region"),
        ("https://azure-oai-north.openai.azure.com/", "North Central region"),
        
        # Try some generic patterns (common resource names)
        ("https://mma-ai.openai.azure.com/", "MMA-focused resource"),
        ("https://openai-east.openai.azure.com/", "Simple east region"),
        ("https://openai-resource.openai.azure.com/", "Generic resource name"),
    ]
    
    working_endpoints = []
    
    for endpoint, description in patterns_to_test:
        print(f"\n🧪 Testing: {description}")
        print(f"   URL: {endpoint}")
        
        success, working_endpoint = test_endpoint(endpoint, description)
        if success and working_endpoint:
            working_endpoints.append((working_endpoint, description))
    
    print(f"\n" + "=" * 55)
    
    if working_endpoints:
        print(f"🎉 Found {len(working_endpoints)} working endpoint(s):")
        
        for endpoint, desc in working_endpoints:
            print(f"   ✅ {endpoint} ({desc})")
        
        # Use the first working endpoint
        best_endpoint = working_endpoints[0][0]
        
        print(f"\n📝 Updating .env with best endpoint: {best_endpoint}")
        
        # Update .env file
        env_lines = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_lines = f.readlines()
        
        updated_lines = []
        for line in env_lines:
            if line.startswith('AZURE_OPENAI_ENDPOINT='):
                updated_lines.append(f'AZURE_OPENAI_ENDPOINT={best_endpoint}\n')
            else:
                updated_lines.append(line)
        
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Updated .env file!")
        print(f"\n🧪 Test the connection:")
        print(f"   uv run debug_azure_openai.py")
        
    else:
        print(f"❌ No working endpoints found.")
        print(f"\n🔧 The issue might be:")
        print(f"   1. API key is from a different Azure subscription")
        print(f"   2. Resource name is completely different")
        print(f"   3. Resource is in a different region")
        print(f"   4. Resource is not properly configured")
        
        print(f"\n📋 Please check in Azure Portal:")
        print(f"   1. Go to your Azure OpenAI resource")
        print(f"   2. Click 'Keys and Endpoint' in the left menu")
        print(f"   3. Copy the exact 'Endpoint' URL shown there")
        print(f"   4. Verify the deployment name under 'Deployments'")

if __name__ == "__main__":
    main()