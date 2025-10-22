#!/usr/bin/env python3
"""
Azure OpenAI Configuration Helper
This script will guide you through getting the correct Azure OpenAI configuration
"""

print("""
🔧 Azure OpenAI Configuration Helper
===================================

The 401 error indicates that either:
1. The API key doesn't match the endpoint 
2. The endpoint URL is incorrect
3. The deployment name is wrong
4. The Azure resource isn't properly configured

Let's fix this step by step.

📋 STEP 1: Get Your Azure OpenAI Configuration
==============================================

Follow these steps in the Azure Portal:

1. Go to: https://portal.azure.com
2. Search for "Azure OpenAI" in the top search bar
3. Click on your Azure OpenAI resource (the one you created)
4. In the left sidebar, click "Keys and Endpoint" 

📝 STEP 2: Copy the Exact Information
====================================

You'll see something like:

┌─────────────────────────────────────────────────┐
│ Keys and Endpoint                               │
├─────────────────────────────────────────────────┤
│ KEY 1: [some 32-character string]              │ ← Copy this
│ KEY 2: [another 32-character string]           │
│                                                 │
│ Endpoint: https://YOUR-RESOURCE.openai.azure.com/ │ ← Copy this EXACTLY
├─────────────────────────────────────────────────┤
│ Region: East US 2                              │
└─────────────────────────────────────────────────┘

🚀 STEP 3: Check Your Deployments
=================================

1. In the same Azure OpenAI resource, click "Deployments" in the left sidebar
2. Look for your model deployment
3. Note the EXACT deployment name (it might be different from "gpt-4-1")

Common deployment names:
- gpt-4
- gpt-4-32k  
- gpt-35-turbo
- gpt-4o
- [your-custom-name]

📝 STEP 4: Update Your Configuration
===================================

Once you have the correct information:

1. Open your .env file
2. Replace the values with what you copied from Azure:

AZURE_OPENAI_API_KEY=[paste KEY 1 here]
AZURE_OPENAI_ENDPOINT=[paste the exact endpoint here]  
AZURE_DEPLOYMENT=[paste the exact deployment name here]

⚠️  COMMON MISTAKES TO AVOID:
============================

❌ Wrong endpoint format:
   - Don't use: https://azure-oai-east2.openai.azure.com/
   - Use what's shown in Azure Portal (usually something like):
   - https://your-actual-resource-name.openai.azure.com/

❌ Wrong deployment name:
   - Don't guess the deployment name
   - Use the EXACT name from the Deployments page

❌ Wrong API key:
   - Make sure you're copying from the same resource as the endpoint
   - API keys are 32 characters long (no sk- prefix for Azure)

🔍 STEP 5: Alternative - Find Your Resource Name
==============================================

If you're not sure which resource to use:

1. In Azure Portal, go to "All Resources"
2. Filter by "Azure OpenAI" 
3. Look for resources in "East US 2" region (since your endpoint suggests this)
4. The resource name should match the endpoint URL

Example:
- Resource name: "my-openai-resource"  
- Endpoint should be: "https://my-openai-resource.openai.azure.com/"

🧪 STEP 6: Test Your Configuration
=================================

After updating your .env file:

1. Run: uv run test_agno_setup.py
2. If it works, then run: uv run run.py
3. Visit: http://localhost:5004/query

💡 Still Having Issues?
======================

If you continue getting 401 errors:

1. Try generating a new API key in Azure Portal
2. Make sure your Azure subscription is active
3. Check if you have the right permissions on the resource
4. Verify the resource is in the "East US 2" region
5. Consider creating a new Azure OpenAI resource if needed

📞 Need the Exact Values?
========================

If you can share the following from your Azure Portal, I can help verify:
- Your Azure OpenAI resource name
- The region your resource is in  
- The exact deployment name from the Deployments page

(Don't share your API key - we can regenerate that if needed)
""")

# Check current configuration
import os
from dotenv import load_dotenv

load_dotenv()

print("\n🔍 Current Configuration Analysis:")
print("=" * 40)

api_key = os.getenv('AZURE_OPENAI_API_KEY', '')
endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', '')
deployment = os.getenv('AZURE_DEPLOYMENT', '')

print(f"Current API Key: {api_key[:8]}...{api_key[-4:]} ({len(api_key)} chars)")
print(f"Current Endpoint: {endpoint}")
print(f"Current Deployment: {deployment}")

# Analyze the endpoint to extract resource name
if endpoint:
    if 'azure-oai-east2' in endpoint:
        print(f"\n⚠️  Your endpoint contains 'azure-oai-east2' which might be a placeholder.")
        print(f"   The real resource name should be visible in Azure Portal.")
    
    # Extract potential resource name
    import re
    match = re.search(r'https://([^.]+)\.openai\.azure\.com', endpoint)
    if match:
        resource_name = match.group(1)
        print(f"\n📋 Extracted resource name: '{resource_name}'")
        print(f"   👉 Verify this matches your resource name in Azure Portal")

print(f"\n🔧 Next Steps:")
print(f"1. Follow the steps above to get your Azure Portal information")
print(f"2. Update your .env file with the correct values")
print(f"3. Run: uv run test_agno_setup.py")