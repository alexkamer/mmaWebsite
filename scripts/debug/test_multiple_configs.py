#!/usr/bin/env python3
"""
Test multiple Azure OpenAI configurations to find the working one
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_config(endpoint, api_version, deployment_name, description):
    """Test a specific configuration"""
    print(f"\n🧪 Testing: {description}")
    print(f"   Endpoint: {endpoint}")
    print(f"   API Version: {api_version}")
    print(f"   Deployment: {deployment_name}")
    
    try:
        from openai import AzureOpenAI
        
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Test successful!'"}
            ],
            max_tokens=20,
            temperature=0
        )
        
        message = response.choices[0].message.content
        print(f"   ✅ SUCCESS! Response: {message}")
        return True, endpoint, api_version, deployment_name
        
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            print(f"   ❌ 401 Unauthorized")
        elif "404" in error_msg:
            print(f"   ❌ 404 Not Found (check deployment name)")
        elif "429" in error_msg:
            print(f"   ⚠️  Rate Limited")
        else:
            print(f"   ❌ Error: {str(e)[:100]}...")
        return False, None, None, None

def main():
    print("🔍 Testing Multiple Azure OpenAI Configurations")
    print("=" * 60)
    
    # Get the current API key
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found in environment")
        return
    
    print(f"📋 Using API Key: {api_key[:8]}...{api_key[-4:]} ({len(api_key)} chars)")
    
    # Test different configurations
    configs_to_test = [
        # Original config
        ("https://azure-oai-east2.openai.azure.com/", "2024-12-01-preview", "gpt-4-1", "Original Config"),
        
        # Try without trailing slash
        ("https://azure-oai-east2.openai.azure.com", "2024-12-01-preview", "gpt-4-1", "No trailing slash"),
        
        # Try different API versions
        ("https://azure-oai-east2.openai.azure.com/", "2024-02-01", "gpt-4-1", "Stable API version"),
        ("https://azure-oai-east2.openai.azure.com/", "2023-12-01-preview", "gpt-4-1", "Older preview version"),
        ("https://azure-oai-east2.openai.azure.com/", "2024-06-01", "gpt-4-1", "June 2024 version"),
        
        # Try different deployment names (common variations)
        ("https://azure-oai-east2.openai.azure.com/", "2024-02-01", "gpt-4", "Standard gpt-4 deployment"),
        ("https://azure-oai-east2.openai.azure.com/", "2024-02-01", "gpt4", "gpt4 (no dash)"),
        ("https://azure-oai-east2.openai.azure.com/", "2024-02-01", "GPT-4-1", "Uppercase version"),
        
        # Try different endpoint formats
        ("https://azure-oai-east2.openai.azure.com/openai/", "2024-02-01", "gpt-4-1", "With /openai/ path"),
    ]
    
    successful_config = None
    
    for endpoint, api_version, deployment, description in configs_to_test:
        success, working_endpoint, working_version, working_deployment = test_config(
            endpoint, api_version, deployment, description
        )
        
        if success:
            successful_config = (working_endpoint, working_version, working_deployment)
            break
    
    print("\n" + "=" * 60)
    
    if successful_config:
        endpoint, api_version, deployment = successful_config
        print("🎉 FOUND WORKING CONFIGURATION!")
        print(f"   Endpoint: {endpoint}")
        print(f"   API Version: {api_version}")
        print(f"   Deployment: {deployment}")
        
        # Update the .env file with working config
        print("\n📝 Updating .env file with working configuration...")
        
        # Read current .env
        env_lines = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_lines = f.readlines()
        
        # Update the relevant lines
        updated_lines = []
        for line in env_lines:
            if line.startswith('AZURE_OPENAI_ENDPOINT='):
                updated_lines.append(f'AZURE_OPENAI_ENDPOINT={endpoint}\n')
            elif line.startswith('AZURE_OPENAI_API_VERSION='):
                updated_lines.append(f'AZURE_OPENAI_API_VERSION={api_version}\n')
            elif line.startswith('AZURE_OPENAI_DEPLOYMENT_NAME='):
                updated_lines.append(f'AZURE_OPENAI_DEPLOYMENT_NAME={deployment}\n')
            else:
                updated_lines.append(line)
        
        # Write updated .env
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ .env file updated!")
        print("\n🚀 Your MMA Query feature should now work!")
        
    else:
        print("❌ No working configuration found.")
        print("\n🔧 Next steps:")
        print("1. Verify your Azure OpenAI resource is active")
        print("2. Check that the API key is correct in Azure portal")
        print("3. Ensure the deployment exists and is running")
        print("4. Try creating a new API key in Azure portal")

if __name__ == "__main__":
    main()