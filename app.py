import os
import json
from typing import Dict, Any, List, Optional
import chainlit as cl
from chainlit.types import ThreadDict
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
import asyncio
from chainlit_app import TOOL_LABELS
from profile_analyzer import profile_analyzer
from utils import get_name_from_profile

SAMPLE_PROFILE_PATH = os.getenv("SAMPLE_PROFILE_PATH", "data/sample_profile.json")

TOOLS: Dict[str, Dict[str, Any]] = {
    "profile_analyzer": {
        "name": "profile_analyzer",
        "payload": {},
        "icon": "public/settings.svg",
        "label": "Analyze my profile",
        "tooltip": "Analyze my profile to assess completeness, missing/insufficient sections"
    },
    "ask_jd_qa": {
        "name": "ask_jd_qa",
        "payload": {},
        "icon": "public/question.svg",
        "label": "Ask about a job posting",
        "tooltip": "Q&A over a selected job posting"
    },
    "update_profile": {
        "name": "update_profile",
        "payload": {},
        "icon": "public/settings.svg",
        "label": "Update my profile",
        "tooltip": "Update a profile field"
    },
    "infer_skills": {
        "name": "infer_skills",
        "payload": {},
        "icon": "public/brain.svg",
        "label": "Suggest skills from my profile",
        "tooltip": "Suggest skills from my profile, return primary/additional lists"
    },
    "get_matches": {
        "name": "get_matches",
        "payload": {},
        "icon": "public/search.svg",
        "label": "Find matching jobs",
        "tooltip": "Find matching jobs based on my profile"
    },
    "draft_email": {
        "name": "draft_email",
        "payload": {},
        "icon": "public/email.svg",
        "label": "Draft a message",
        "tooltip": "Draft a message to Hiring Manager or Recruiter"
    },
}

session_state: Dict[str, Any] = {
    "user_id": None,
    "profile": None,
    "last_result": None
}

@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///./data/data.db")

@cl.password_auth_callback
def auth(username: str, password: str):
    if username == os.getenv("CL_ADMIN_USER", "admin") and password == os.getenv("CL_ADMIN_PASS", "admin"):
        return cl.User(identifier=username, metadata={"role": "admin"})
    return None

def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _get_profile() -> Dict[str, Any]:
    return _load_json(SAMPLE_PROFILE_PATH)


async def _render_profile_analysis_result(result: Dict[str, Any]) -> None:
    score = result.get("completionScore")
    missing = result.get("missingSections", [])
    insights = result.get("insights", [])
    next_actions = result.get("nextActions", [])

    md_lines: List[str] = [f"### Profile Analysis", f"**Completion Score:** {score}%"]
    if missing:
        md_lines.append(f"\n**Missing Sections:** {', '.join(missing)}")
    if insights:
        md_lines.append("\n**Insights:**")
        for i in insights:
            area = i.get("area", "").title()
            note = i.get("note", "")
            md_lines.append(f"- *{area}*: {note}")
    if next_actions:
        md_lines.append("\n**Suggested Next Steps:**")
        for a in next_actions:
            label = TOOL_LABELS.get(a, a)
            md_lines.append(f"- {label}")

    await cl.Message(content="\n".join(md_lines)).send()

    actions = [cl.Action(name=a, label=TOOL_LABELS.get(a, a), payload={}) for a in next_actions]
    if actions:
        await cl.Message(content="Choose a next step:", actions=actions).send()

async def get_matches(profile: Dict[str, Any]) -> None:
    async with cl.Step("Talent Profile to find matching jobs"):
        await asyncio.sleep(1)  
        matches = [
            {"role": "Senior Data Scientist, NLP", "job_id": "2144332", "score": 88},
            {"role": "ML Engineer, RAG Systems", "job_id": "2037913", "score": 84},
        ]
        md = ["### Top Job Matches"]
        for m in matches:
            md.append(f"- **{m['role']}**  \n  ID: `{m['job_id']}`  •  Score: **{m['score']}%**")
        await cl.Message(content="\n".join(md)).send()
        actions = [
            cl.Action(name=TOOLS["ask_jd_qa"]["name"], label=TOOLS["ask_jd_qa"]["label"], payload={"job_ids": [m['job_id'] for m in matches]}),
            cl.Action(name=TOOLS["draft_email"]["name"], label=TOOLS["draft_email"]["label"], payload={})
        ]
        await cl.Message(content="Choose the next step:", actions=actions).send()

def load_profile() -> Dict[str, Any]:
    """Load profile JSON"""
    try:
        with open(SAMPLE_PROFILE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "core": {
                "experience": {},
                "qualification": {},
                "skills": {},
                "language": {}
            }
        }

# Actions
@cl.action_callback("analyze_profile")
async def on_analyze_profile(action: cl.Action):
    profile = cl.user_session.get("profile") or _get_profile()
    result = profile_analyzer(profile)
    cl.user_session.set("profile_analysis_result", result)
    await _render_profile_analysis_result(result)

@cl.action_callback("get_matches")
async def on_get_matches(action: cl.Action):
    profile = cl.user_session.get("profile") or _get_profile()
    await get_matches(profile)

@cl.action_callback("ask_jd_qa")
async def on_ask_jd_qa(action: cl.Action):
    #create a list of actions for the job ids
    job_ids = action.payload.get("job_ids")
    actions = [cl.Action(name=job_id, label=f"Ask about job id: {job_id}", payload={"job_id": job_id}) for job_id in job_ids]
    await cl.Message(content="Choose a job to ask about:", actions=actions).send()

@cl.action_callback("draft_email")
async def on_draft_hm_email(action: cl.Action):
    profile = cl.user_session.get("profile") or _get_profile()
    name = get_name_from_profile(profile)
    md = (
        "### Draft Email to Hiring Manager\n"
        f"Subject: Application - {name}\n\n"
        "Hello Hiring Manager,\n\n"
        "I am excited about the opportunity and believe my background aligns well with the role.\n"
        "I would welcome a chance to discuss how I can contribute.\n\n"
        f"Best regards,\n{name}"
    )
    await cl.Message(content=md).send()
    await cl.Message(
        "Would you like to see internal matches now?",
        actions=[cl.Action(name="present_matches", label=TOOL_LABELS["present_matches"], payload={})],
    ).send()

@cl.action_callback("infer_skills")
async def on_infer_skills(action):
    await cl.Message(content="Inferring skills based on your profile...").send()
    session_state["profile"]["core"]["skills"] = {
        "topSkills": ["Leadership", "Java", "Compliance"]
    }
    result = profile_analyzer(session_state["profile"])
    await _render_profile_analysis_result(result)

@cl.action_callback("set_preferences")
async def on_set_preferences(action):
    await cl.Message(content="Setting career preferences...").send()
    core = session_state["profile"]["core"]
    core["careerAspirationPreference"] = {"preferredAspirations": []}
    core["careerLocationPreference"] = {"preferredRelocationRegions": []}
    result = profile_analyzer(session_state["profile"])
    await _render_profile_analysis_result(result)
    
@cl.action_callback("apply_internal_job")
async def on_apply(action):
    await cl.Message(content="✅ Application submitted. Congratulations!").send()
    await cl.Message(content="You can continue exploring other matches or update your profile anytime.").send()

# Chat lifecycle
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Find Matching Jobs",
            message="Can you find matching jobs for me?",
            icon="public/search.svg"
            # command="get_matches"
        ),

        cl.Starter(
            label="Help me update my profile",
            message="Help me update my profile",
            icon="public/write.svg",
        ),
        cl.Starter(
            label="Set my skills in MyProfile",
            message="Set my skills in MyProfile",
            icon="public/skills.svg"
        ),
        cl.Starter(
            label="Show me all actions",
            message="Show me all actions",
            icon="public/list.svg"
        )
    ]


@cl.on_chat_start
async def on_chat_start():
    # await cl.Message(
    #     "Welcome to *MYCareer Agentic Chat*"
    # ).send()
    # Load user profile 
    print("Loading user profile.")
    profile = _get_profile()
    cl.user_session.set("profile", profile)


@cl.on_message
async def on_message(msg: cl.Message):
        content = (msg.content or "").strip()
        if content == "Can you find matching jobs for me?":
            await get_matches(cl.user_session.get("profile"))
        elif content == "Help me update my profile":
            await _render_profile_analysis_result(cl.user_session.get("profile_analysis_result"))
        elif content == "Set my skills in MyProfile":
            await cl.Message(f"Pending Implementation: Set my skills in MyProfile").send()
        elif content == "Show me all actions":
            actions = [cl.Action(name=a, label=TOOLS[a]["label"], payload={}) for a in TOOLS.keys()]
            await cl.Message(content="Here are all the actions you can take:", actions=actions).send()
        else:
            await cl.Message(f"Pending Implementation: {content}").send()

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    await cl.Message("Welcome back. You can continue where you left off.").send()
