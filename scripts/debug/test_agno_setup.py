#!/usr/bin/env python3
"""
Test script for Agno-based MMA Query Service
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_agno_setup():
    print("🤖 Testing Agno MMA Query Setup")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    deployment = os.getenv('AZURE_DEPLOYMENT')
    
    print("📋 Environment Variables Check:")
    print(f"  AZURE_OPENAI_API_KEY: {'✓ Set' if api_key else '✗ Missing'} ({len(api_key) if api_key else 0} chars)")
    print(f"  AZURE_OPENAI_ENDPOINT: {'✓ Set' if endpoint else '✗ Missing'} ({endpoint if endpoint else 'None'})")
    print(f"  AZURE_DEPLOYMENT: {'✓ Set' if deployment else '✗ Missing'} ({deployment if deployment else 'None'})")
    print()
    
    if not all([api_key, endpoint, deployment]):
        print("❌ Missing required Agno configuration. Please check your .env file.")
        return False
    
    # Test Agno import
    try:
        from agno.agent import Agent
        from agno.models.azure import AzureOpenAI
        print("✓ Agno packages imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Agno packages: {e}")
        print("💡 Run: pip install -U agno openai")
        return False
    
    # Test Azure OpenAI model creation
    try:
        azure_model = AzureOpenAI(
            id=deployment,
            api_version="2024-12-01-preview",
            azure_endpoint=endpoint,
            api_key=api_key
        )
        print("✓ Azure OpenAI model created successfully")
    except Exception as e:
        print(f"❌ Failed to create Azure OpenAI model: {e}")
        return False
    
    # Test agent creation
    try:
        test_agent = Agent(
            model=azure_model,
            name="Test Agent",
            description="Simple test agent",
            instructions="You are a helpful assistant. Always respond with 'Test successful!'",
            markdown=False
        )
        print("✓ Agno agent created successfully")
    except Exception as e:
        print(f"❌ Failed to create Agno agent: {e}")
        return False
    
    # Test simple agent interaction
    print("\n🧪 Testing Agent Interaction...")
    try:
        response = test_agent.run("Say hello")
        message = response.content
        print(f"✅ Agent Test Successful!")
        print(f"📝 Agent Response: {message}")
        return True
        
    except Exception as e:
        print(f"❌ Agent Test Failed: {e}")
        
        # Provide specific troubleshooting based on error
        error_str = str(e).lower()
        print("\n🔧 Troubleshooting:")
        
        if "401" in error_str or "unauthorized" in error_str:
            print("  • Check if your Azure OpenAI API key is correct")
            print("  • Verify the key hasn't expired")
            print("  • Make sure you're using the right Azure resource")
            
        elif "404" in error_str or "not found" in error_str:
            print("  • Check if your deployment name is correct")
            print("  • Verify the deployment exists in your Azure resource")
            print("  • Make sure the model is deployed and running")
            
        elif "endpoint" in error_str:
            print("  • Check if your endpoint URL is correct")
            print("  • Verify you're using the right region")
            
        else:
            print("  • Check Azure OpenAI service status")
            print("  • Verify your subscription is active")
            print("  • Check network connectivity to Azure")
        
        return False

def test_mma_service():
    """Test the actual MMA query service"""
    print("\n🥊 Testing MMA Query Service")
    print("=" * 40)
    
    try:
        from mma_website.services.mma_query_service_agno import mma_query_service
        
        print("✓ MMA Query Service imported successfully")
        
        # Check if agents are initialized
        if mma_query_service.sql_agent and mma_query_service.response_agent:
            print("✅ Both SQL and Response agents are initialized")
        else:
            print("❌ Agents not properly initialized")
            return False
        
        # Test a simple query
        print("\n🧪 Testing simple MMA question...")
        test_question = "How many fighters are in the database?"
        
        result = mma_query_service.process_query(test_question)
        
        if result.get('success'):
            print("✅ MMA Query Test Successful!")
            print(f"📊 SQL Generated: {result.get('sql_query', 'N/A')}")
            print(f"📈 Results Found: {result.get('row_count', 0)}")
            print(f"💬 Response Preview: {result.get('response', 'N/A')[:100]}...")
            return True
        else:
            print(f"❌ MMA Query Test Failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing MMA service: {e}")
        return False

if __name__ == "__main__":
    print("Agno MMA Query Setup Test")
    print("This will test your Agno configuration with Azure OpenAI\n")
    
    # Test basic Agno setup
    agno_success = test_agno_setup()
    
    if agno_success:
        # Test MMA-specific service
        mma_success = test_mma_service()
        
        if mma_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("Your Agno-based MMA Query feature is ready to use!")
            print("\n🚀 Next steps:")
            print("1. Start your Flask app: uv run run.py")
            print("2. Visit: http://localhost:5004/query")
            print("3. Ask questions like: 'What is Jon Jones UFC record?'")
        else:
            print("\n⚠️  Agno setup works, but MMA service needs attention.")
    else:
        print("\n❌ Agno setup failed. Please fix the configuration first.")
        print("\n💡 Common fixes:")
        print("1. Install agno: pip install -U agno openai")
        print("2. Check your Azure OpenAI credentials")
        print("3. Verify your deployment name is correct")
        print("4. Ensure your Azure resource is active")