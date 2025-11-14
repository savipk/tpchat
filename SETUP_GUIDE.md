# MyCareer Assistant - Setup Guide

This guide will help you get the MyCareer Employee Experience Agentic Assistant up and running.

## Prerequisites

- **Python**: Version 3.9 or higher
- **OpenAI API Key**: Required for LLM functionality
- **Terminal/Command Line**: Basic familiarity

## Quick Start (5 Minutes)

### Step 1: Verify Python Installation

```bash
python --version
# or
python3 --version
```

Expected output: `Python 3.9.x` or higher

### Step 2: Install Dependencies

```bash
cd /Users/savikuriakose/projects/tpchat
pip install -r requirements.txt
```

This installs:
- Chainlit 2.8.4
- LangChain 1.0.5
- LangGraph 1.0.3
- OpenAI Python SDK
- Supporting libraries

**Note**: If you encounter permission errors, use:
```bash
pip install --user -r requirements.txt
```

### Step 3: Configure Environment

1. **Create your `.env` file**:
   ```bash
   touch .env
   ```

2. **Choose your LLM provider** and configure accordingly:

   **Option A: OpenAI (Default)**
   ```bash
   # .env file
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-actual-api-key-here
   OPENAI_MODEL=gpt-4o
   CL_ADMIN_USER=admin
   CL_ADMIN_PASS=admin
   SAMPLE_PROFILE_PATH=data/sample_profile.json
   ```

   **Get an OpenAI API Key**:
   - Go to https://platform.openai.com/api-keys
   - Sign in or create account
   - Click "Create new secret key"
   - Copy the key (starts with `sk-`)
   - Paste it in your `.env` file

   **Option B: Azure OpenAI**
   ```bash
   # .env file
   LLM_PROVIDER=azure
   AZURE_OPENAI_API_KEY=your-azure-openai-key
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   CL_ADMIN_USER=admin
   CL_ADMIN_PASS=admin
   SAMPLE_PROFILE_PATH=data/sample_profile.json
   ```

   **Get Azure OpenAI Credentials**:
   - Go to Azure Portal: https://portal.azure.com
   - Create Azure OpenAI resource
   - Deploy a model (e.g., GPT-4o)
   - Get credentials from "Keys and Endpoint"

   📖 **See [LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md) for detailed instructions**

### Step 4: Initialize Database (Optional)

The database auto-creates on first run, but you can initialize it manually:

```bash
python data/init_db.py
```

Expected output: `Initialized /path/to/data/data.db`

### Step 5: Run the Application

```bash
chainlit run app.py
```

Expected output:
```
2024-11-14 - Loaded .env file
2024-11-14 - Your app is available at http://localhost:8000
```

### Step 6: Access the UI

1. Open browser: http://localhost:8000
2. Login with credentials:
   - Username: `admin`
   - Password: `admin`
3. Start chatting!

---

## Detailed Setup

### Virtual Environment (Recommended)

Using a virtual environment keeps dependencies isolated:

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables Explained

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ Yes | - |
| `OPENAI_MODEL` | OpenAI model to use | No | `gpt-4o` |
| `CL_ADMIN_USER` | Chainlit login username | No | `admin` |
| `CL_ADMIN_PASS` | Chainlit login password | No | `admin` |
| `SAMPLE_PROFILE_PATH` | Path to profile JSON | No | `data/sample_profile.json` |

### Alternative Models

You can use different OpenAI models:

```bash
# In .env file:
OPENAI_MODEL=gpt-4-turbo-preview  # GPT-4 Turbo
OPENAI_MODEL=gpt-3.5-turbo        # GPT-3.5 (faster, cheaper)
OPENAI_MODEL=gpt-4                # Standard GPT-4
```

---

## Verification Steps

### 1. Test Profile Loading

```python
python -c "from app import load_profile; print(load_profile()['core']['name'])"
```

Should print: User name from profile

### 2. Test Tool Execution

```python
python -c "from tools import execute_tool; from app import load_profile; print(execute_tool('profile_analyzer', load_profile()))"
```

Should print: Profile analysis results

### 3. Test Agent Initialization

```python
python -c "from agent import get_agent; agent = get_agent(); print('Agent initialized successfully')"
```

Should print: "Agent initialized successfully"

---

## Common Issues & Solutions

### Issue: "OPENAI_API_KEY not set"

**Problem**: Environment variable not loaded

**Solution**:
```bash
# Verify .env file exists
ls -la .env

# Check contents (macOS/Linux)
cat .env

# Chainlit should auto-load, but you can also:
export OPENAI_API_KEY=sk-your-key-here
```

### Issue: "Import Error: No module named 'chainlit'"

**Problem**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt

# If that fails, install individually:
pip install chainlit==2.8.4
pip install langchain==1.0.5
pip install langchain-openai==0.3.5
```

### Issue: "Port 8000 already in use"

**Problem**: Another process using port 8000

**Solution**:
```bash
# Use different port
chainlit run app.py --port 8001

# Or find and kill the process (macOS/Linux)
lsof -ti:8000 | xargs kill -9
```

### Issue: "Profile file not found"

**Problem**: sample_profile.json missing or path incorrect

**Solution**:
```bash
# Verify file exists
ls -la data/sample_profile.json

# If missing, check your SAMPLE_PROFILE_PATH in .env
# Ensure path is relative to project root
```

### Issue: Database errors

**Problem**: Corrupted or incompatible database

**Solution**:
```bash
# Delete and recreate
rm data/data.db
python data/init_db.py
```

### Issue: "Rate limit exceeded" from OpenAI

**Problem**: Too many API requests

**Solution**:
- Check your OpenAI usage limits
- Consider upgrading your OpenAI plan
- Add delays between requests
- Use cheaper model (gpt-3.5-turbo)

---

## Development Mode

### Hot Reload

Chainlit supports auto-reload on file changes:

```bash
chainlit run app.py --watch
```

Changes to Python files will automatically restart the server.

### Debug Mode

Enable verbose logging:

```bash
chainlit run app.py --debug
```

### Custom Port

```bash
chainlit run app.py --port 8080
```

---

## Testing the Application

### Basic Flow Test

1. **Start app**: `chainlit run app.py`
2. **Login**: admin/admin
3. **Welcome screen**: Should show personalized greeting with profile score
4. **Send message**: "Find me matching jobs"
5. **Expect**: Response + 3 action buttons
6. **Click button**: "Find matching jobs"
7. **Expect**: Job matches displayed + 3 next action buttons

### Confidence Level Test

**High Confidence (>0.75)**:
- Input: "Show me job matches"
- Expected: Direct recommendation + get_matches button first

**Medium Confidence (0.45-0.75)**:
- Input: "I need help with something"
- Expected: Clarifying questions + 3 suggested buttons

**Low Confidence (<0.45)**:
- Input: "Hello there"
- Expected: Fallback message + default 3 buttons

### Profile Gating Test

1. Modify `data/sample_profile.json` to have minimal data
2. Restart app
3. Try to find jobs
4. Expected: Blocked with message about improving profile
5. Suggested actions: Analyze profile, Suggest skills, Update profile

---

## Production Deployment

### Environment Security

Never commit `.env` file! It's already in `.gitignore`.

For production:
1. Use environment variables from hosting platform
2. Rotate API keys regularly
3. Use strong passwords for Chainlit auth
4. Consider implementing OAuth

### Database Migration

For production, migrate from SQLite to PostgreSQL:

1. Update `app.py`:
   ```python
   @cl.data_layer
   def get_data_layer():
       return SQLAlchemyDataLayer(
           conninfo="postgresql://user:pass@host:5432/dbname"
       )
   ```

2. Install PostgreSQL driver:
   ```bash
   pip install psycopg2-binary
   ```

### Scaling Considerations

- **Rate Limiting**: Implement request throttling
- **Caching**: Cache profile analysis results
- **Load Balancing**: Use multiple Chainlit instances
- **Monitoring**: Add logging and error tracking

---

## Useful Commands

```bash
# Start app
chainlit run app.py

# Start with hot reload
chainlit run app.py --watch

# Start on different port
chainlit run app.py --port 8080

# Run profile analyzer standalone
python profile_analyzer.py

# Check Python packages
pip list | grep chainlit

# Update dependencies
pip install -r requirements.txt --upgrade

# Generate requirements (if needed)
pip freeze > requirements.txt
```

---

## Next Steps

Once setup is complete:

1. ✅ Review `README.md` for architecture overview
2. ✅ Check `DESIGN_SPEC_VALIDATION.md` for implementation details
3. ✅ Test all conversation flows
4. ✅ Customize prompts in `prompts.py` if needed
5. ✅ Implement real tool integrations (replace mocks)

---

## Support

### Check Logs

Chainlit logs appear in terminal. Look for:
- "Loading user profile" - Profile loaded successfully
- "Intent detection error" - Issue with LLM
- "Tool execution error" - Issue with tool
- "Error processing user input" - General error

### Enable Debug Output

Add to top of `app.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Get Help

- Review error messages in terminal
- Check OpenAI API status: https://status.openai.com
- Verify all dependencies installed: `pip list`
- Check file permissions: `ls -la`

---

## Cleanup

To remove the application:

```bash
# Stop the server (Ctrl+C in terminal)

# Optionally remove virtual environment
deactivate  # if using venv
rm -rf venv

# Remove database (optional)
rm data/data.db

# Keep source code and data files
```

---

**Setup Complete!** 🎉

You now have a fully functional MyCareer Employee Experience Agentic Assistant running locally.

Happy coding! 🚀

