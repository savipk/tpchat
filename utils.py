from typing import Dict, Any

def get_name_from_profile(profile: Dict[str, Any]) -> str:
    core = profile.get("core") or {}
    name = core.get("name")
    if isinstance(name, dict):
        first = name.get("businessFirstName") or name.get("legalFirstName")
        last = name.get("businessLastName") or name.get("legalLastName")
        if first and last:
            return f"{first} {last}"
        if first:
            return first
    if isinstance(name, str) and name.strip():
        return name.strip()
    email = profile.get("email") or (core.get("email") if isinstance(core.get("email"), str) else None)
    return email or "Candidate"