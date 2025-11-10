from typing import Dict, Any, List

def profile_analyzer(profile: Dict[str, Any],
                     completion_threshold: int = 80) -> Dict[str, Any]:

    core = profile.get("core", {})
    score = 0
    missing_sections: List[str] = []
    insights: List[Dict[str, Any]] = []

    # ---- Experience ----
    exp_ok = bool(core.get("experience", {}).get("experiences"))
    score += 30 if exp_ok else 0
    if not exp_ok:
        missing_sections.append("experience")
        insights.append({
            "area": "experience",
            "observation": "No work experience found",
            "action": "update_profile_field",
            "recommendation": "Add at least one job with title, company, and dates"
        })

    # ---- Qualification ----
    qual_ok = bool(core.get("qualification", {}).get("educations"))
    score += 20 if qual_ok else 0
    if not qual_ok:
        missing_sections.append("qualification")
        insights.append({
            "area": "qualification",
            "observation": "Missing educational or certification details",
            "action": "update_profile_field",
            "recommendation": "Add a degree or certification"
        })

    # ---- Skills ----
    skills = core.get("skills", {})
    skills_ok = bool(skills.get("topSkills") or skills.get("additionalSkills"))
    score += 25 if skills_ok else 0
    if not skills_ok:
        missing_sections.append("skills")
        insights.append({
            "area": "skills",
            "observation": "No top or additional skills detected",
            "action": "infer_skills",
            "recommendation": "Infer or manually add top 5 skills"
        })

    # ---- Preferences ----
    pref_ok = bool(core.get("careerAspirationPreference")
                   and core.get("careerLocationPreference"))
    score += 15 if pref_ok else 0
    if not pref_ok:
        missing_sections.append("preferences")
        insights.append({
            "area": "preferences",
            "observation": "Career aspiration or location preferences missing",
            "action": "set_preferences",
            "recommendation": "Add preferred roles and relocation regions"
        })

    # ---- Languages ----
    lang_ok = bool(core.get("language", {}).get("languages"))
    score += 10 if lang_ok else 0
    if not lang_ok:
        missing_sections.append("languages")
        insights.append({
            "area": "language",
            "observation": "No language proficiency data found",
            "action": "update_profile_field",
            "recommendation": "Add at least one language with proficiency level"
        })

    completion_score = round(score, 2)
    next_actions = []

    if completion_score < completion_threshold:
        for i, insight in enumerate(insights, start=1):
            next_actions.append({
                "title": insight["recommendation"],
                "tool": insight["action"],
                "priority": i
            })
    else:
        next_actions = [
            {"title": "Find Job Matches", "tool": "get_matches", "priority": 1},
            {"title": "Ask about a Job", "tool": "ask_jd_qa", "priority": 2}
        ]

    return {
        "completionScore": completion_score,
        "missingSections": missing_sections,
        "insights": insights,
        "nextActions": next_actions
    }



if __name__ == "__main__":
    import json

    # Load mock profile from file or inline dict
    from pathlib import Path

    # path profile 
    profile_path = Path("data/sample_profile.json")

    if profile_path.exists():
        profile = json.loads(profile_path.read_text())
    else:
        # fallback if no file found
        profile = {"core": {"experience": {}, "qualification": {}}}

    result = profile_analyzer(profile)
    print(json.dumps(result, indent=2))
