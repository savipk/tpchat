# LLM Provider Configuration Guide

This guide explains how to switch between OpenAI and Azure OpenAI for the MyCareer Agentic Assistant.

## Quick Switch Guide

### Use OpenAI (Default)

```bash
# In your .env file:
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4o
```

### Use Azure OpenAI

```bash
# In your .env file:
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-azure-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

---

## Detailed Configuration

### Option 1: OpenAI (Standard)

**When to use:**
- Development and testing
- No Azure subscription
- Quick setup
- Pay-per-use pricing

**Setup:**

1. **Get an OpenAI API Key:**
   - Go to https://platform.openai.com/api-keys
   - Create an account or sign in
   - Create a new secret key
   - Copy the key (starts with `sk-`)

2. **Configure .env:**
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
   OPENAI_MODEL=gpt-4o
   ```

3. **Available Models:**
   - `gpt-4o` - Latest GPT-4 Omni (recommended)
   - `gpt-4-turbo-preview` - GPT-4 Turbo
   - `gpt-4` - Standard GPT-4
   - `gpt-3.5-turbo` - Faster, cheaper option

4. **Start the app:**
   ```bash
   chainlit run app.py
   ```

**Expected output:**
```
2025-11-14 - Loaded .env file
Initializing OpenAI with model: gpt-4o
2025-11-14 - Your app is available at http://localhost:8000
```

---

### Option 2: Azure OpenAI

**When to use:**
- Enterprise deployments
- Data residency requirements
- Existing Azure infrastructure
- Corporate compliance needs
- Private network access

**Setup:**

1. **Create Azure OpenAI Resource:**
   - Go to Azure Portal: https://portal.azure.com
   - Create a new "Azure OpenAI" resource
   - Note your resource name
   - Deploy a model (e.g., GPT-4o)

2. **Get Configuration Details:**

   **API Key:**
   - Go to your Azure OpenAI resource
   - Navigate to "Keys and Endpoint"
   - Copy "KEY 1" or "KEY 2"

   **Endpoint:**
   - In "Keys and Endpoint", copy the "Endpoint" URL
   - Format: `https://your-resource-name.openai.azure.com/`

   **Deployment Name:**
   - Go to "Model deployments" or Azure OpenAI Studio
   - Note the deployment name you created (e.g., "gpt-4o", "gpt-4-turbo")

3. **Configure .env:**
   ```bash
   LLM_PROVIDER=azure
   AZURE_OPENAI_API_KEY=1234567890abcdef1234567890abcdef
   AZURE_OPENAI_ENDPOINT=https://mycompany-openai.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

4. **Start the app:**
   ```bash
   chainlit run app.py
   ```

**Expected output:**
```
2025-11-14 - Loaded .env file
Initializing Azure OpenAI with deployment: gpt-4o
2025-11-14 - Your app is available at http://localhost:8000
```

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | `openai` | Provider: `openai` or `azure` |
| `OPENAI_MODEL` | No | `gpt-4o` | Model/deployment name |

#### OpenAI Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key (starts with `sk-`) |

*Required when `LLM_PROVIDER=openai`

#### Azure OpenAI Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | Yes* | - | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Yes* | - | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | No | Uses `OPENAI_MODEL` | Deployment name in Azure |
| `AZURE_OPENAI_API_VERSION` | No | `2024-02-15-preview` | API version |

*Required when `LLM_PROVIDER=azure`

---

## Switching Between Providers

### Quick Switch (One Variable)

Just change `LLM_PROVIDER` in your `.env` file:

```bash
# Switch to Azure
LLM_PROVIDER=azure

# Switch back to OpenAI
LLM_PROVIDER=openai
```

Make sure you have the required credentials for the selected provider.

### Using Multiple .env Files

For easier switching, you can maintain separate environment files:

**.env.openai:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
```

**.env.azure:**
```bash
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

Then copy the one you need:
```bash
# Use OpenAI
cp .env.openai .env

# Use Azure OpenAI
cp .env.azure .env
```

---

## Troubleshooting

### Error: "OPENAI_API_KEY environment variable not set"

**Problem:** Missing OpenAI API key when `LLM_PROVIDER=openai`

**Solution:**
```bash
# Add to .env file:
OPENAI_API_KEY=sk-your-actual-key-here
```

### Error: "AZURE_OPENAI_API_KEY environment variable not set"

**Problem:** Missing Azure credentials when `LLM_PROVIDER=azure`

**Solution:**
```bash
# Add to .env file:
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

### Error: "The API deployment for this resource does not exist"

**Problem:** Deployment name doesn't match Azure deployment

**Solution:**
1. Go to Azure OpenAI Studio
2. Check your deployment name under "Deployments"
3. Update `.env`:
   ```bash
   AZURE_OPENAI_DEPLOYMENT_NAME=your-actual-deployment-name
   ```

### Error: "401 Unauthorized"

**Problem:** Invalid or expired API key

**Solution:**
- **OpenAI:** Generate a new key at https://platform.openai.com/api-keys
- **Azure:** Check "Keys and Endpoint" in Azure Portal, regenerate if needed

### Error: "Connection timeout"

**Problem:** Network or endpoint issue

**Solution for Azure:**
1. Verify endpoint URL format: `https://name.openai.azure.com/`
2. Don't include `/openai/` or version in endpoint
3. Check firewall/network settings

---

## Best Practices

### Development vs Production

**Development:**
```bash
# Use OpenAI for development
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-3.5-turbo  # Cheaper for testing
```

**Production:**
```bash
# Use Azure OpenAI for production
LLM_PROVIDER=azure
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

### Security

1. **Never commit .env files** to version control
2. **Use different keys** for dev/prod
3. **Rotate keys regularly**
4. **Use Azure Key Vault** for production credentials
5. **Set up billing alerts** (OpenAI) or cost management (Azure)

### Performance

- **OpenAI:** Generally faster response times
- **Azure:** Better for private networks, data residency
- **Model selection:**
  - `gpt-4o` - Best quality, slower, more expensive
  - `gpt-4-turbo` - Good balance
  - `gpt-3.5-turbo` - Fastest, cheapest, lower quality

---

## Testing Your Configuration

### 1. Check Environment Variables

```bash
# Print loaded config (be careful not to expose keys!)
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'Provider: {os.getenv(\"LLM_PROVIDER\")}')"
```

### 2. Test LLM Initialization

```python
# test_llm.py
from agent import _initialize_llm

try:
    llm = _initialize_llm("gpt-4o")
    print("✅ LLM initialized successfully")
    print(f"   Type: {type(llm).__name__}")
except Exception as e:
    print(f"❌ Error: {e}")
```

Run:
```bash
python test_llm.py
```

### 3. Test Full Application

```bash
chainlit run app.py
```

Look for initialization message:
- OpenAI: `Initializing OpenAI with model: gpt-4o`
- Azure: `Initializing Azure OpenAI with deployment: gpt-4o`

---

## Cost Comparison

### OpenAI Pricing (as of 2024)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-4o | $5.00 | $15.00 |
| GPT-4-turbo | $10.00 | $30.00 |
| GPT-3.5-turbo | $0.50 | $1.50 |

### Azure OpenAI Pricing

- Similar to OpenAI pricing
- Billed through Azure subscription
- Can use Azure credits
- Enterprise discounts available

**Typical conversation cost:**
- Average conversation: 2,000-5,000 tokens
- GPT-4o cost: ~$0.05 - $0.15 per conversation
- GPT-3.5-turbo cost: ~$0.002 - $0.005 per conversation

---

## Advanced Configuration

### Custom API Versions (Azure)

```bash
# Use specific API version
AZURE_OPENAI_API_VERSION=2023-12-01-preview
```

Available versions: https://learn.microsoft.com/en-us/azure/ai-services/openai/reference

### Temperature Control

Temperature is set in `app.py` when initializing the agent:

```python
# app.py
agent = get_agent(OPENAI_MODEL, temperature=0.7)
```

Or set via environment:
```bash
OPENAI_TEMPERATURE=0.7  # 0.0 = deterministic, 1.0 = creative
```

### Multiple Deployments (Azure)

You can use different deployments for different purposes:

```bash
# .env
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o  # Default
AZURE_OPENAI_FAST_DEPLOYMENT=gpt-35-turbo  # For quick responses
AZURE_OPENAI_SMART_DEPLOYMENT=gpt-4-turbo  # For complex tasks
```

---

## Support

### OpenAI
- Docs: https://platform.openai.com/docs
- Status: https://status.openai.com
- Support: https://help.openai.com

### Azure OpenAI
- Docs: https://learn.microsoft.com/azure/ai-services/openai/
- Support: Azure Portal → Support + troubleshooting
- Status: https://status.azure.com

---

## Summary

✅ **Easy switching** - Just change `LLM_PROVIDER` variable  
✅ **No code changes** - All configuration via environment variables  
✅ **Same API** - Both providers use LangChain's unified interface  
✅ **Flexible** - Works for development and production  

**Quick Start:**
1. Choose provider (OpenAI or Azure)
2. Set environment variables in `.env`
3. Run `chainlit run app.py`
4. Check initialization message confirms correct provider

Happy chatting! 🚀

