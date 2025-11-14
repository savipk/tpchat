# MyCareer Employee Experience Agentic Assistant

An intelligent conversational AI assistant for career management, built with Chainlit and LangChain. This PoC demonstrates agentic behavior with intent detection, tool orchestration, and context-aware recommendations.

## Features

### Core Capabilities
- 🔍 **Job Matching** - Find opportunities based on your talent profile with optional filters
- 📊 **Profile Analysis** - Assess profile completeness and get improvement suggestions
- 🧠 **Skills Inference** - AI-powered skill recommendations from your experience
- ✏️ **Profile Updates** - Update profile sections (skills implementation complete)
- ❓ **Job Q&A** - Ask questions about specific job postings
- ✉️ **Email Drafting** - Generate professional messages to recruiters

### AI-Powered Features
- **Intent Detection** - Natural language understanding maps user queries to appropriate tools
- **Confidence Scoring** - Adaptive responses based on confidence thresholds (>0.75, 0.45-0.75, <0.45)
- **Context Management** - Session memory tracks conversation history and actions
- **Dynamic Tool Ranking** - Smart next-best-action recommendations based on context
- **Clarifying Questions** - Asks for clarification when intent is ambiguous

### User Experience
- **Conversational Interface** - Natural language interaction via Chainlit
- **Action Buttons** - Always shows 3 contextually relevant action buttons
- **Real-time Feedback** - Visual progress indicators for tool execution
- **Session Continuity** - Persistent chat history and state management

## Architecture

### Component Overview
```
┌─────────────────────────────────────────────────────────────┐
│                     Chainlit UI Layer                        │
│  (app.py - Message handling, action callbacks, rendering)   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Agent Layer (agent.py)                    │
│  - Intent Detection with LLM                                 │
│  - Tool Mapping & Confidence Scoring                         │
│  - Response Generation                                       │
│  - Tool Execution Orchestration                              │
└────┬───────────────┬──────────────────┬─────────────────────┘
     │               │                  │
┌────▼─────┐  ┌─────▼──────┐  ┌───────▼────────┐
│ Tools    │  │  Context   │  │  Tool Ranker   │
│ (tools.py)  │  Manager   │  │ (tool_ranker.py)│
│           │  │ (context_  │  │                │
│ • profile │  │  manager.py)│  │ • Default      │
│   analyzer│  │            │  │   ranking      │
│ • get_    │  │ • Session  │  │ • Context-     │
│   matches │  │   state    │  │   aware logic  │
│ • infer_  │  │ • Chat     │  │ • Next best    │
│   skills  │  │   history  │  │   actions      │
│ • update_ │  │ • Action   │  │                │
│   profile │  │   tracking │  │                │
│ • ask_jd_ │  │ • Match    │  │                │
│   qa      │  │   scoring  │  │                │
│ • draft_  │  │            │  │                │
│   email   │  │            │  │                │
└───────────┘  └────────────┘  └────────────────┘
                     │
            ┌────────▼─────────┐
            │  Prompts Layer   │
            │   (prompts.py)   │
            │                  │
            │ Centralized      │
            │ prompt templates │
            └──────────────────┘
```

### Key Design Patterns
1. **Separation of Concerns** - Clear boundaries between UI, agent logic, tools, and state
2. **Replaceable LLM** - Model configuration via environment variable
3. **Centralized Prompts** - All LLM prompts in `prompts.py`
4. **Context-Aware Routing** - Dynamic tool ranking based on session state
5. **Human-in-the-Loop** - User always triggers tool execution via button clicks

## Project Structure

```
tpchat/
├── app.py                    # Main Chainlit application
├── agent.py                  # LangChain-based agent with intent detection
├── tools.py                  # Tool implementations (1 functional, 5 mocked)
├── tool_ranker.py           # Next-best-actions selection logic
├── context_manager.py       # Session state and memory management
├── prompts.py               # Centralized prompt templates
├── profile_analyzer.py      # Profile analysis logic (functional)
├── utils.py                 # Helper functions
├── requirements.txt         # Python dependencies
├── chainlit.md             # Welcome screen content
├── data/
│   ├── sample_profile.json # User talent profile (JSON)
│   ├── sample_job.json     # Sample job posting
│   ├── data.db            # SQLite database for chat history
│   └── schema.sql         # Database schema
├── public/                 # Static assets (icons)
└── tests/                  # Test files
```

## Installation

### Prerequisites
- Python 3.9+
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   cd /path/to/tpchat
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Create .env file from example
   cp .env.example .env
   
   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-4o
   ```

4. **Initialize database** (optional, auto-creates on first run)
   ```bash
   python data/init_db.py
   ```

5. **Run the application**
   ```bash
   chainlit run app.py
   ```

6. **Access the UI**
   - Open browser to: http://localhost:8000
   - Login with: admin / admin (configurable in .env)

## Usage

### Conversation Flow

1. **Text Input** → Intent Detection → Tool Mapping → Response + 3 Action Buttons
2. **Button Click** → Tool Execution → Results Display → Next 3 Action Buttons

### Example Interactions

**Finding Jobs:**
```
User: "Show me matching jobs"
Assistant: [Analyzes intent, confidence > 0.75]
          "I'll help you find matching jobs based on your profile."
          [Shows buttons: Find Jobs | Ask About Job | Draft Email]
```

**Low Confidence:**
```
User: "Something about my career"
Assistant: [Confidence 0.50]
          "I want to make sure I help with the right action. 
           Are you looking to find jobs, analyze your profile, or something else?"
          [Shows buttons: Find Jobs | Analyze Profile | Suggest Skills]
```

**Profile Too Incomplete:**
```
User: Clicks "Find Jobs"
System: Profile completion < 50%
Assistant: "Your profile needs attention (45% complete). 
           Let's improve it for better job matches!"
          [Shows buttons: Analyze Profile | Suggest Skills | Update Profile]
```

## Configuration

### LLM Provider (OpenAI or Azure OpenAI)

The system supports both **OpenAI** and **Azure OpenAI** with easy switching via environment variables.

**Quick Switch:**
```bash
# Use OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Use Azure OpenAI
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

📖 **See [LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md) for detailed setup instructions**

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider: `openai` or `azure` | openai |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | Model name or deployment name | gpt-4o |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | - |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | - |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure deployment name | Uses `OPENAI_MODEL` |
| `AZURE_OPENAI_API_VERSION` | Azure API version | 2024-02-15-preview |
| `SAMPLE_PROFILE_PATH` | Path to user profile JSON | data/sample_profile.json |
| `CL_ADMIN_USER` | Chainlit admin username | admin |
| `CL_ADMIN_PASS` | Chainlit admin password | admin |

### Tool Priority Ranking (Default)

1. get_matches (Find matching jobs)
2. profile_analyzer (Analyze profile)
3. infer_skills (Suggest skills)
4. update_profile (Update profile)
5. ask_jd_qa (Q&A about job)
6. draft_email (Draft message)

**Context-aware adjustments:**
- Profile < 50%: Prioritize profile_analyzer, infer_skills, update_profile
- After showing matches: Prioritize ask_jd_qa, draft_email
- Low match scores (< 60): Prioritize profile improvement tools

## Design Specifications

This implementation follows the complete design spec including:

✅ **Intent Detection & Tool Mapping** with confidence scoring  
✅ **Three-tier confidence thresholds** (>0.75, 0.45-0.75, <0.45)  
✅ **Always 3 action buttons** with context-aware ranking  
✅ **Profile completion gating** (no matches if < 50%)  
✅ **Consecutive low match detection** (suggests profile improvement)  
✅ **Session state management** with chat and action history  
✅ **Centralized prompt management** in prompts.py  
✅ **Replaceable LLM architecture** via configuration  
✅ **Tool implementations**: 1 functional (profile_analyzer), 5 mocked  

## Implementation Status

### Completed (Must Have)
- ✅ Tool registry with 6 tools
- ✅ Intent detection and mapping
- ✅ Confidence-based routing
- ✅ Next-best-actions selector
- ✅ Profile analyzer (functional)
- ✅ Context management
- ✅ Session memory
- ✅ Action buttons (always 3)
- ✅ Chainlit UI integration
- ✅ LangChain/LangGraph v1 integration
- ✅ Centralized prompts
- ✅ Profile completion gating
- ✅ Low match detection

### Mocked (To Be Implemented)
- 🔜 get_matches (real job database integration)
- 🔜 infer_skills (ML-based skill extraction)
- 🔜 update_profile (full section support)
- 🔜 ask_jd_qa (RAG implementation)
- 🔜 draft_email (advanced personalization)

### Nice to Have (Future)
- 🔜 Multi-language support
- 🔜 Azure Cosmos DB integration
- 🔜 Advanced clarifying questions
- 🔜 User feedback collection
- 🔜 Analytics dashboard

## Testing

### Manual Testing Checklist

1. **Basic Flow**
   - [ ] Start new chat → Welcome message appears
   - [ ] Enter query → Intent mapped → Action buttons shown
   - [ ] Click button → Tool executes → Results displayed

2. **Confidence Levels**
   - [ ] High confidence (>0.75): Direct recommendation
   - [ ] Medium confidence (0.45-0.75): Clarifying questions
   - [ ] Low confidence (<0.45): Fallback with options

3. **Profile Gating**
   - [ ] Profile < 50%: Job matching blocked
   - [ ] Profile ≥ 50%: Job matching allowed

4. **Context Awareness**
   - [ ] After matches: Shows ask_jd_qa, draft_email
   - [ ] Low scores: Suggests profile improvement
   - [ ] Session history tracked correctly

## Troubleshooting

### Common Issues

**"OPENAI_API_KEY not set"**
- Solution: Create `.env` file with your OpenAI API key

**"Profile file not found"**
- Solution: Ensure `data/sample_profile.json` exists or set `SAMPLE_PROFILE_PATH`

**Import errors**
- Solution: Run `pip install -r requirements.txt`

**Database errors**
- Solution: Delete `data/data.db` and restart (auto-recreates)

## Technology Stack

- **UI Framework**: Chainlit 2.8.4
- **Agent Framework**: LangChain 1.0.5, LangGraph 1.0.3
- **LLM**: OpenAI GPT-4o
- **Database**: SQLite (via SQLAlchemy)
- **Language**: Python 3.9+

## Future Enhancements

1. **Real Data Integration**
   - Azure Cosmos DB for profiles and jobs
   - Vector database for semantic search
   - Real-time job feed integration

2. **Advanced Features**
   - Multi-turn tool chaining
   - Agentic loops with feedback
   - User preference learning
   - Resume parsing and upload

3. **Production Readiness**
   - Comprehensive test suite
   - Error monitoring and logging
   - Performance optimization
   - Security hardening

## License

Internal PoC - Not for public distribution

## Support

For issues or questions, contact the development team.

---

**Built with ❤️ using Chainlit and LangChain**

