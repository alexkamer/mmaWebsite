#!/usr/bin/env python3
"""
Diagnose API Key format and Azure resource issues
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()

def diagnose_api_key():
    print("🔍 Azure OpenAI API Key Diagnosis")
    print("=" * 50)
    
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No API key found in environment")
        return
    
    print(f"📋 API Key Analysis:")
    print(f"   Length: {len(api_key)} characters")
    print(f"   First 8 chars: {api_key[:8]}")
    print(f"   Last 4 chars: ...{api_key[-4:]}")
    print(f"   Format: {''.join(['X' if c.isalnum() else c for c in api_key])}")
    
    # Check common Azure OpenAI key patterns
    patterns = {
        "Standard Azure Key": r"^[a-f0-9]{32}$",
        "Azure Key with Prefix": r"^sk-[a-zA-Z0-9]{48}$",
        "Microsoft Cognitive Services": r"^[a-zA-Z0-9]{32}$",
        "Base64-like": r"^[A-Za-z0-9+/]{40,}={0,2}$"
    }
    
    print(f"\n🔍 Pattern Matching:")
    matches = []
    for name, pattern in patterns.items():
        if re.match(pattern, api_key):
            print(f"   ✅ {name}: Match")
            matches.append(name)
        else:
            print(f"   ❌ {name}: No match")
    
    if not matches:
        print(f"\n⚠️  Key doesn't match common Azure OpenAI patterns")
        print(f"   Raw key (first 20 chars): {api_key[:20]}...")
        
        # Check for common issues
        issues = []
        if ' ' in api_key:
            issues.append("Contains spaces")
        if '\n' in api_key or '\r' in api_key:
            issues.append("Contains newline characters")
        if api_key != api_key.strip():
            issues.append("Has leading/trailing whitespace")
        
        if issues:
            print(f"   🚨 Potential issues: {', '.join(issues)}")
        
    # Check if it looks like a different type of key
    if api_key.startswith('sk-'):
        print(f"\n🤔 This looks like an OpenAI API key, not Azure OpenAI")
        print(f"   Azure OpenAI keys usually don't start with 'sk-'")
    
    if len(api_key) == 51 and api_key.startswith('sk-'):
        print(f"   This appears to be a regular OpenAI key")
    
    print(f"\n💡 Common Azure OpenAI Key Sources:")
    print(f"   1. Azure Portal > Your OpenAI Resource > Keys and Endpoint")
    print(f"   2. Should be labeled as 'KEY 1' or 'KEY 2'")
    print(f"   3. Usually 32 hex characters (no 'sk-' prefix)")
    
    # Test with cleaned key
    cleaned_key = api_key.strip().replace(' ', '').replace('\n', '').replace('\r', '')
    if cleaned_key != api_key:
        print(f"\n🧹 Cleaned key would be: {cleaned_key[:8]}...{cleaned_key[-4:]}")
        print(f"   Length: {len(cleaned_key)} characters")
        
        # Update .env with cleaned key
        print(f"   💾 Updating .env with cleaned key...")
        
        # Read and update .env
        env_lines = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_lines = f.readlines()
        
        updated_lines = []
        for line in env_lines:
            if line.startswith('AZURE_OPENAI_API_KEY='):
                updated_lines.append(f'AZURE_OPENAI_API_KEY={cleaned_key}\n')
            else:
                updated_lines.append(line)
        
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print(f"   ✅ Updated .env file")
        return True
    
    return False

if __name__ == "__main__":
    key_updated = diagnose_api_key()
    
    if key_updated:
        print(f"\n🔄 Key was cleaned. Please run the test again:")
        print(f"   uv run debug_azure_openai.py")
    else:
        print(f"\n📞 If the key format looks correct, the issue might be:")
        print(f"   1. Wrong Azure resource (key from different resource)")
        print(f"   2. Expired or inactive key") 
        print(f"   3. Resource not properly deployed")
        print(f"   4. Billing/subscription issue")
        print(f"\n🔧 Try:")
        print(f"   1. Generate a new key in Azure Portal")
        print(f"   2. Verify the resource name matches the endpoint")
        print(f"   3. Check if the deployment 'gpt-4-1' exists")