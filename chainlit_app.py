"""
chainlit_app.py
---------------
Prototype chat integrating `profile_analyzer` tool.
Chainlit 2.8.3 compatible.
Uses in-memory state (no Redis) and shows agentic next-step suggestions
with human-readable button labels.
"""

import chainlit as cl
import json
from typing import Dict, Any
from profile_analyzer import profile_analyzer

# -----------------------------
# Mock state (in-memory)
# -----------------------------
session_state: Dict[str, Any] = {
    "user_id": None,
    "profile": None,
    "last_result": None
}

# -----------------------------
# Helper functions
# -----------------------------
def load_profile() -> Dict[str, Any]:
    """Load mock profile JSON for demo."""
    try:
        with open("sample_profile.json", "r") as f:
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

# Map tool → user-facing label
TOOL_LABELS = {
    "infer_skills": "🧠 Add Missing Skills",
    "set_preferences": "🎯 Set Career Preferences",
    "get_matches": "🔍 Find Matching Jobs",
    "ask_jd_qa": "💬 Ask About This Job",
    "draft_hm_email": "✉️ Draft Email to Hiring Manager",
    "apply_internal_job": "✅ Apply for This Job",
    "update_profile_field": "✏️ Update Profile Field"
}

# -----------------------------
# Renderer
# -----------------------------
async def render_result(result: Dict[str, Any]):
    """Render profile analysis and next-step buttons."""
    score = result["completionScore"]
    missing = result["missingSections"]
    insights = result["insights"]
    next_actions = result["nextActions"]

    md = f"### Profile Analysis\n**Completion Score:** {score}%\n"
    if missing:
        md += f"\n**Missing Sections:** {', '.join(missing)}\n"
    if insights:
        md += "\n**Insights:**\n"
        for i in insights:
            md += f"- *{i['area'].title()}*: {i['observation']}\n"

    await cl.Message(content=md).send()

    # Proper label rendering (Chainlit 2.8.3)
    buttons = []
    for a in next_actions:
        label = TOOL_LABELS.get(a["tool"], a["title"])
        buttons.append(
            cl.Action(
                name=a["tool"],          # callback ID
                label=label,             # text shown on button
                value=a["tool"],         # backend ID
                payload={}               # required field in 2.8.3
            )
        )

    if buttons:
        await cl.Message(content="What would you like to do next?", actions=buttons).send()

# -----------------------------
# Chat lifecycle
# -----------------------------
@cl.on_chat_start
async def start():
    await cl.Message(content="Welcome to *MyCareer Agentic Chat*!").send()
    profile = load_profile()
    session_state["profile"] = profile
    result = profile_analyzer(profile)
    session_state["last_result"] = result
    await render_result(result)

# -----------------------------
# Action callbacks
# -----------------------------
@cl.action_callback("infer_skills")
async def on_infer_skills(action):
    await cl.Message(content="Inferring skills based on your profile...").send()
    session_state["profile"]["core"]["skills"] = {
        "topSkills": ["Leadership", "Java", "Compliance"]
    }
    result = profile_analyzer(session_state["profile"])
    await render_result(result)

@cl.action_callback("set_preferences")
async def on_set_preferences(action):
    await cl.Message(content="Setting career preferences...").send()
    core = session_state["profile"]["core"]
    core["careerAspirationPreference"] = {"preferredAspirations": []}
    core["careerLocationPreference"] = {"preferredRelocationRegions": []}
    result = profile_analyzer(session_state["profile"])
    await render_result(result)

@cl.action_callback("get_matches")
async def on_get_matches(action):
    await cl.Message(content="Finding top job matches...").send()
    matches = [
        {
            "jobId": "3286618BR",
            "title": "Java Technical Lead",
            "location": "Weehawken, NJ",
            "score": 0.87,
            "why": ["Skills overlap: Java, leadership", "Director-level alignment"]
        }
    ]
    md = "### Top Job Match\n"
    for m in matches:
        md += f"**{m['title']}** ({m['location']}) — match score {int(m['score']*100)}%\n"
        md += f"_Why_: {', '.join(m['why'])}\n\n"
    await cl.Message(content=md).send()

    buttons = [
        cl.Action(name="ask_jd_qa", label=TOOL_LABELS["ask_jd_qa"], payload={}),
        cl.Action(name="draft_hm_email", label=TOOL_LABELS["draft_hm_email"], payload={})
    ]
    await cl.Message(content="Next steps:", actions=buttons).send()

@cl.action_callback("ask_jd_qa")
async def on_jd_qa(action):
    await cl.Message(
        content="You can ask any question about the job. Example: *What tech stack does this team use?*"
    ).send()

@cl.action_callback("draft_hm_email")
async def on_hm_email(action):
    md = (
        "**Subject:** Interest in Java Technical Lead role\n\n"
        "**Body:**\n"
        "Dear Hiring Manager,\n\n"
        "I came across the Java Technical Lead opening and found a strong alignment with my background in compliance and technology leadership.\n"
        "I'd be delighted to discuss how I can contribute to your team.\n\n"
        "Best regards,\nTravis Wilson"
    )
    await cl.Message(content=md).send()

    buttons = [
        cl.Action(name="apply_internal_job", label=TOOL_LABELS["apply_internal_job"], payload={})
    ]
    await cl.Message(content="Would you like to apply?", actions=buttons).send()

@cl.action_callback("apply_internal_job")
async def on_apply(action):
    await cl.Message(content="✅ Application submitted. Congratulations!").send()
    await cl.Message(content="You can continue exploring other matches or update your profile anytime.").send()
