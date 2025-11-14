"""
MyCareer Employee Experience Agentic Assistant
Chainlit-based conversational UI with LLM-powered intent detection and tool orchestration.
"""

import os
import json
from typing import Dict, Any, List, Optional
import chainlit as cl
from chainlit.types import ThreadDict
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

# Import our modules
from agent import get_agent
from context_manager import get_context_manager, AgentContext
from tools import execute_tool
from utils import get_name_from_profile
import prompts


# ============================================================================
# CONFIGURATION
# ============================================================================

SAMPLE_PROFILE_PATH = os.getenv("SAMPLE_PROFILE_PATH", "data/sample_profile.json")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Tool display information
TOOL_DISPLAY_INFO = {
    "profile_analyzer": {
        "label": "Analyze my profile",
        "icon": "📊",
        "tooltip": "Analyze profile completeness and get improvement suggestions"
    },
    "update_profile": {
        "label": "Update my profile",
        "icon": "✏️",
        "tooltip": "Update profile sections (skills, experience, etc.)"
    },
    "infer_skills": {
        "label": "Suggest skills",
        "icon": "🧠",
        "tooltip": "Get AI-suggested skills based on your experience"
    },
    "get_matches": {
        "label": "Find matching jobs",
        "icon": "🔍",
        "tooltip": "Find job opportunities that match your profile"
    },
    "ask_jd_qa": {
        "label": "Ask about a job",
        "icon": "❓",
        "tooltip": "Ask questions about a specific job posting"
    },
    "draft_email": {
        "label": "Draft a message",
        "icon": "✉️",
        "tooltip": "Draft an email to hiring manager or recruiter"
    }
}


# ============================================================================
# DATA LAYER AND AUTH
# ============================================================================

@cl.data_layer
def get_data_layer():
    """Configure SQLite data layer for chat history."""
    return SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///./data/data.db")


@cl.password_auth_callback
def auth(username: str, password: str):
    """Simple password authentication."""
    if username == os.getenv("CL_ADMIN_USER", "admin") and password == os.getenv("CL_ADMIN_PASS", "admin"):
        return cl.User(identifier=username, metadata={"role": "admin"})
    return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_profile() -> Dict[str, Any]:
    """Load user profile from JSON file."""
    try:
        with open(SAMPLE_PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Profile file not found at {SAMPLE_PROFILE_PATH}")
        return {
            "core": {
                "name": {"businessFirstName": "User"},
                "experience": {},
                "qualification": {},
                "skills": {},
                "language": {}
            }
        }


def get_user_context() -> AgentContext:
    """Get or create agent context for current user session."""
    context_manager = get_context_manager()
    user = cl.user_session.get("user")
    user_id = user.identifier if user else "default_user"
    
    # Get or create context
    context = cl.user_session.get("agent_context")
    if not context:
        profile = cl.user_session.get("profile")
        context = context_manager.get_or_create_context(user_id, profile)
        cl.user_session.set("agent_context", context)
    
    return context


async def send_response_with_actions(
    response_text: str,
    action_buttons: List[Dict[str, Any]],
    show_buttons_separately: bool = True
):
    """
    Send response text and action buttons to the user.
    
    Args:
        response_text: Text response to display
        action_buttons: List of action button definitions
        show_buttons_separately: If True, show buttons in a separate message
    """
    # Send main response
    await cl.Message(content=response_text).send()
    
    # Create Chainlit action objects
    if action_buttons:
        cl_actions = []
        for btn in action_buttons:
            action = cl.Action(
                name=btn["name"],
                label=btn["label"],
                payload=btn.get("payload", {}),
                description=btn.get("tooltip", "")
            )
            cl_actions.append(action)
        
        # Send actions
        if show_buttons_separately:
            await cl.Message(
                content="**Choose your next action:**",
                actions=cl_actions
            ).send()
        else:
            # Attach to last message (not currently supported in Chainlit)
            await cl.Message(content="", actions=cl_actions).send()


# ============================================================================
# CHAINLIT LIFECYCLE HOOKS
# ============================================================================

@cl.set_starters
async def set_starters():
    """Set starter prompts for new chat sessions."""
    return [
        cl.Starter(
            label="Find Matching Jobs",
            message="Can you find matching jobs for me?",
            icon="🔍"
        ),
        cl.Starter(
            label="Analyze My Profile",
            message="Analyze my profile",
            icon="📊"
        ),
        cl.Starter(
            label="Suggest Skills",
            message="What skills should I add to my profile?",
            icon="🧠"
        ),
        cl.Starter(
            label="Show All Actions",
            message="What can you help me with?",
            icon="❓"
        )
    ]


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session."""
    # Load user profile
    print("Loading user profile...")
    profile = load_profile()
    cl.user_session.set("profile", profile)
    
    # Initialize agent context
    context = get_user_context()
    
    # Get user name
    user_name = get_name_from_profile(profile)
    
    # Run initial profile analysis
    try:
        agent = get_agent(OPENAI_MODEL)
        analysis_result = execute_tool("profile_analyzer", profile)
        context.update_profile_analysis(analysis_result)
        
        # Generate welcome message
        try:
            prompt = prompts.WELCOME_MESSAGE_PROMPT.format(
                completion_score=context.profile_completion_score,
                user_name=user_name,
                missing_sections=", ".join(context.missing_sections) if context.missing_sections else "None"
            )
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=prompts.RESPONSE_GENERATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            response = agent.llm.invoke(messages)
            welcome_text = response.content
        except Exception as e:
            print(f"Welcome message generation error: {e}")
            welcome_text = (
                f"Welcome to **MyCareer Assistant**, {user_name}! 👋\n\n"
                f"Your profile is {context.profile_completion_score}% complete. "
                "I'm here to help you find great job opportunities and improve your profile.\n\n"
                "What would you like to do today?"
            )
        
        # Determine initial actions based on profile state
        if context.profile_completion_score < 50:
            # Profile needs critical improvement
            initial_actions = ["profile_analyzer", "infer_skills", "update_profile"]
        else:
            # Profile is reasonable, show default actions
            initial_actions = ["get_matches", "profile_analyzer", "infer_skills"]
        
        # Create action buttons
        action_buttons = []
        for tool_name in initial_actions:
            tool_info = TOOL_DISPLAY_INFO.get(tool_name, {})
            action_buttons.append({
                "name": tool_name,
                "label": tool_info.get("label", tool_name),
                "icon": tool_info.get("icon", "🔧"),
                "tooltip": tool_info.get("tooltip", "")
            })
        
        # Send welcome message and actions
        await send_response_with_actions(welcome_text, action_buttons)
    
    except Exception as e:
        print(f"Error during chat initialization: {e}")
        await cl.Message(
            content="Welcome to MyCareer Assistant! I'm here to help you with your career. What would you like to do?"
        ).send()


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """Resume previous chat session."""
    # Reload profile and context
    profile = load_profile()
    cl.user_session.set("profile", profile)
    
    context = get_user_context()
    
    # Generate resume message
    try:
        agent = get_agent(OPENAI_MODEL)
        prompt = prompts.SESSION_RESUME_PROMPT.format(
            last_action=context.last_tool_executed or "None",
            pending_items="None"
        )
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=prompts.RESPONSE_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        response = agent.llm.invoke(messages)
        resume_text = response.content
    except Exception as e:
        print(f"Resume message generation error: {e}")
        resume_text = "Welcome back! You can continue where you left off."
    
    await cl.Message(content=resume_text).send()


# ============================================================================
# MESSAGE HANDLER (Main conversation flow)
# ============================================================================

@cl.on_message
async def on_message(msg: cl.Message):
    """
    Handle user text input.
    
    Flow: User input → Intent detection → Tool mapping → Response with action buttons
    """
    user_input = (msg.content or "").strip()
    
    if not user_input:
        await cl.Message(content="Please enter a message.").send()
        return
    
    # Get context
    context = get_user_context()
    
    # Add message to context
    context.add_message("user", user_input)
    
    # Show thinking indicator
    async with cl.Step(name="Analyzing your request", type="tool") as step:
        try:
            # Get agent and process input
            agent = get_agent(OPENAI_MODEL)
            result = agent.process_user_input(user_input, context)
            
            step.output = f"Mapped to: {result.get('mapped_tool', 'N/A')} (confidence: {result.get('confidence', 0):.2f})"
        
        except Exception as e:
            print(f"Error processing user input: {e}")
            result = {
                "response_text": "I encountered an issue processing your request. Please try again or choose an action below.",
                "action_buttons": [
                    {"name": "get_matches", "label": TOOL_DISPLAY_INFO["get_matches"]["label"], "icon": "🔍", "tooltip": ""},
                    {"name": "profile_analyzer", "label": TOOL_DISPLAY_INFO["profile_analyzer"]["label"], "icon": "📊", "tooltip": ""},
                    {"name": "infer_skills", "label": TOOL_DISPLAY_INFO["infer_skills"]["label"], "icon": "🧠", "tooltip": ""}
                ],
                "confidence": 0.0
            }
    
    # Add assistant response to context
    context.add_message("assistant", result["response_text"], {
        "confidence": result.get("confidence", 0.0),
        "mapped_tool": result.get("mapped_tool")
    })
    
    # Send response and action buttons
    await send_response_with_actions(
        result["response_text"],
        result.get("action_buttons", [])
    )


# ============================================================================
# ACTION CALLBACKS (Button click handlers)
# ============================================================================

@cl.action_callback("profile_analyzer")
async def on_profile_analyzer(action: cl.Action):
    """Execute profile analyzer tool."""
    await execute_tool_action("profile_analyzer", {})


@cl.action_callback("get_matches")
async def on_get_matches(action: cl.Action):
    """Execute get matches tool."""
    # Extract any parameters from payload
    filters = action.payload.get("filters")
    search_text = action.payload.get("search_text")
    
    params = {}
    if filters:
        params["filters"] = filters
    if search_text:
        params["search_text"] = search_text
    
    await execute_tool_action("get_matches", params)


@cl.action_callback("infer_skills")
async def on_infer_skills(action: cl.Action):
    """Execute infer skills tool."""
    await execute_tool_action("infer_skills", {})


@cl.action_callback("update_profile")
async def on_update_profile(action: cl.Action):
    """Execute update profile tool."""
    # For now, just update skills section
    params = action.payload or {"section": "skills"}
    await execute_tool_action("update_profile", params)


@cl.action_callback("ask_jd_qa")
async def on_ask_jd_qa(action: cl.Action):
    """Execute ask JD Q&A tool."""
    # Check if job_id is in payload
    job_id = action.payload.get("job_id")
    question = action.payload.get("question")
    
    if job_id and question:
        # Execute directly
        await execute_tool_action("ask_jd_qa", {"job_id": job_id, "question": question})
    else:
        # Ask user for job ID and question
        await cl.Message(
            content="Please provide the job ID and your question. For example:\n\n"
                    "\"Tell me about the salary for job 3286618BR\""
        ).send()
        
        # Set context to expect Q&A input
        context = get_user_context()
        context.pending_clarification = True
        context.current_intent = "ask_jd_qa"


@cl.action_callback("draft_email")
async def on_draft_email(action: cl.Action):
    """Execute draft email tool."""
    params = action.payload or {}
    await execute_tool_action("draft_email", params)


# ============================================================================
# TOOL EXECUTION HELPER
# ============================================================================

async def execute_tool_action(tool_name: str, params: Dict[str, Any]):
    """
    Execute a tool and display results.
    
    Flow: Tool execution → Results → Response generation → Next action buttons
    """
    context = get_user_context()
    
    # Check special conditions
    if tool_name == "get_matches" and not context.can_show_matches():
        await cl.Message(
            content=f"⚠️ Your profile completion score is {context.profile_completion_score}%, "
                    "which is below the minimum threshold for job matching.\n\n"
                    "Let's improve your profile first to get better matches!"
        ).send()
        
        # Show profile improvement actions
        action_buttons = [
            {"name": "profile_analyzer", "label": TOOL_DISPLAY_INFO["profile_analyzer"]["label"], "icon": "📊", "tooltip": ""},
            {"name": "infer_skills", "label": TOOL_DISPLAY_INFO["infer_skills"]["label"], "icon": "🧠", "tooltip": ""},
            {"name": "update_profile", "label": TOOL_DISPLAY_INFO["update_profile"]["label"], "icon": "✏️", "tooltip": ""}
        ]
        await send_response_with_actions("Choose an action:", action_buttons, show_buttons_separately=False)
        return
    
    # Show execution progress
    async with cl.Step(name=f"Executing: {tool_name}", type="tool") as step:
        try:
            # Get agent
            agent = get_agent(OPENAI_MODEL)
            
            # Execute tool
            result = agent.execute_tool_action(tool_name, context, params)
            
            step.output = "✅ Completed"
        
        except Exception as e:
            print(f"Tool execution error: {e}")
            step.output = f"❌ Error: {str(e)}"
            
            await cl.Message(
                content="I encountered an issue executing that action. Please try again or choose another action."
            ).send()
            return
    
    # Send results and next actions
    response_text = result.get("response_text", "Action completed.")
    action_buttons = result.get("action_buttons", [])
    
    await send_response_with_actions(response_text, action_buttons)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # This is for development/testing
    # Production will use: chainlit run app.py
    print("MyCareer Agentic Assistant")
    print("Run with: chainlit run app.py")
