#!/usr/bin/env python
"""
Test script to verify LLM configuration (OpenAI or Azure OpenAI).
Run this to check if your .env configuration is correct before starting the app.
"""

import os
import sys
from dotenv import load_dotenv

def test_llm_configuration():
    """Test LLM configuration and connection."""
    
    print("=" * 60)
    print("MyCareer Assistant - LLM Configuration Test")
    print("=" * 60)
    print()
    
    # Load environment variables
    load_dotenv()
    
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    print(f"📋 Provider: {provider.upper()}")
    print()
    
    # Check configuration
    config_ok = True
    
    if provider == "azure":
        print("🔍 Checking Azure OpenAI configuration...")
        print()
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        if not api_key:
            print("❌ AZURE_OPENAI_API_KEY not set")
            config_ok = False
        else:
            print(f"✅ AZURE_OPENAI_API_KEY: {'*' * 20}...{api_key[-4:]}")
        
        if not endpoint:
            print("❌ AZURE_OPENAI_ENDPOINT not set")
            config_ok = False
        else:
            print(f"✅ AZURE_OPENAI_ENDPOINT: {endpoint}")
        
        if not deployment:
            print("⚠️  AZURE_OPENAI_DEPLOYMENT_NAME not set (will use OPENAI_MODEL)")
            deployment = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        print(f"✅ AZURE_OPENAI_DEPLOYMENT_NAME: {deployment}")
        print(f"✅ AZURE_OPENAI_API_VERSION: {api_version}")
    
    else:
        print("🔍 Checking OpenAI configuration...")
        print()
        
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        if not api_key:
            print("❌ OPENAI_API_KEY not set")
            config_ok = False
        else:
            # Show first few and last few characters
            if api_key.startswith("sk-"):
                masked_key = f"sk-...{api_key[-4:]}"
            else:
                masked_key = f"{'*' * 20}...{api_key[-4:]}"
            print(f"✅ OPENAI_API_KEY: {masked_key}")
        
        print(f"✅ OPENAI_MODEL: {model}")
    
    print()
    
    if not config_ok:
        print("=" * 60)
        print("❌ Configuration incomplete!")
        print()
        print("Please check your .env file and ensure all required")
        print("variables are set for your chosen provider.")
        print()
        print("See LLM_PROVIDER_GUIDE.md for detailed setup instructions.")
        print("=" * 60)
        return False
    
    # Try to initialize LLM
    print("🔄 Testing LLM initialization...")
    print()
    
    try:
        from agent import _initialize_llm
        
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        llm = _initialize_llm(model_name, temperature=0.7)
        
        print(f"✅ LLM initialized successfully!")
        print(f"   Type: {type(llm).__name__}")
        print()
        
    except Exception as e:
        print(f"❌ Error initializing LLM:")
        print(f"   {str(e)}")
        print()
        print("=" * 60)
        print("Please check:")
        if provider == "azure":
            print("  1. API key is valid")
            print("  2. Endpoint URL is correct (no trailing path)")
            print("  3. Deployment name matches your Azure deployment")
            print("  4. API version is supported")
        else:
            print("  1. API key is valid")
            print("  2. You have access to the specified model")
        print()
        print("See LLM_PROVIDER_GUIDE.md for troubleshooting.")
        print("=" * 60)
        return False
    
    # Try a simple test call
    print("🔄 Testing LLM call (this may take a few seconds)...")
    print()
    
    try:
        from langchain_core.messages import HumanMessage
        
        response = llm.invoke([HumanMessage(content="Say 'Hello, I am working!' and nothing else.")])
        
        print("✅ LLM call successful!")
        print(f"   Response: {response.content}")
        print()
        
    except Exception as e:
        print(f"❌ Error calling LLM:")
        print(f"   {str(e)}")
        print()
        print("=" * 60)
        print("Common issues:")
        if provider == "azure":
            print("  - Deployment not found: Check deployment name")
            print("  - 401 Unauthorized: Invalid API key")
            print("  - Connection timeout: Check network/firewall")
        else:
            print("  - 401 Unauthorized: Invalid API key")
            print("  - Rate limit exceeded: Wait and try again")
            print("  - Model access: Check if you have access to the model")
        print()
        print("See LLM_PROVIDER_GUIDE.md for troubleshooting.")
        print("=" * 60)
        return False
    
    # Success!
    print("=" * 60)
    print("✅ All tests passed!")
    print()
    print("Your LLM configuration is working correctly.")
    print("You can now run: chainlit run app.py")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_llm_configuration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)

