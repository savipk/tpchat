"""
Tool implementations for MyCareer Agentic Assistant.
Contains both functional and mocked tool implementations as per design spec.
"""

import json
import random
from typing import Dict, Any, List, Optional
from profile_analyzer import profile_analyzer as analyze_profile


# ============================================================================
# TOOL 1: PROFILE ANALYZER (Functional)
# ============================================================================

def profile_analyzer(profile: Dict[str, Any], completion_threshold: int = 80) -> Dict[str, Any]:
    """
    Analyzes the profile to provide a completion score based on missing or insufficient information.
    This is the functional implementation.
    
    Args:
        profile: User's talent profile data
        completion_threshold: Threshold for considering profile complete (default: 80)
    
    Returns:
        Dict containing completionScore, missingSections, insights, and nextActions
    """
    return analyze_profile(profile, completion_threshold)


# ============================================================================
# TOOL 2: UPDATE PROFILE (Mocked - Skills section only for now)
# ============================================================================

def update_profile(
    profile: Dict[str, Any],
    section: str = "skills",
    updates: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Updates a section of the talent profile.
    Currently implements skills section; other sections to be added later.
    
    Args:
        profile: User's talent profile data
        section: Section to update (currently only 'skills' supported)
        updates: Dictionary of updates to apply
    
    Returns:
        Dict containing success status and updated profile snippet
    """
    # MOCKED IMPLEMENTATION
    if section != "skills":
        return {
            "success": False,
            "message": f"Update for section '{section}' will be implemented later.",
            "supported_sections": ["skills"]
        }
    
    if not updates:
        updates = {
            "topSkills": ["Python", "Machine Learning", "Data Analysis"],
            "additionalSkills": ["SQL", "Docker", "Kubernetes"]
        }
    
    # Simulate profile update
    return {
        "success": True,
        "message": "Skills section updated successfully",
        "section": section,
        "updated_fields": updates,
        "previous_completion_score": profile.get("core", {}).get("completionScore", 0),
        "estimated_new_score": min(100, profile.get("core", {}).get("completionScore", 0) + 15)
    }


# ============================================================================
# TOOL 3: INFER SKILLS (Mocked)
# ============================================================================

def infer_skills(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggests candidate skills from the profile based on experience and qualifications.
    Returns top skills and additional skills.
    
    Args:
        profile: User's talent profile data
    
    Returns:
        Dict containing topSkills, additionalSkills, and evidence
    """
    # MOCKED IMPLEMENTATION
    # In real implementation, this would use NLP/ML to extract skills from experience
    
    core = profile.get("core", {})
    experiences = core.get("experience", {}).get("experiences", [])
    educations = core.get("qualification", {}).get("educations", [])
    
    # Mock skill inference based on experience titles
    inferred_top_skills = []
    inferred_additional_skills = []
    evidence = []
    
    # Extract from job titles (mocked logic)
    for exp in experiences[:2]:  # Look at most recent 2 experiences
        title = exp.get("jobTitle", "").lower()
        if "lead" in title or "manager" in title:
            inferred_top_skills.append("Leadership")
            evidence.append(f"Leadership role: {exp.get('jobTitle')}")
        if "java" in title or "technical" in title:
            inferred_top_skills.append("Java")
            evidence.append(f"Technical role: {exp.get('jobTitle')}")
        if "compliance" in title or "risk" in title:
            inferred_top_skills.append("Compliance")
            inferred_additional_skills.append("Risk Management")
            evidence.append(f"Compliance experience: {exp.get('jobTitle')}")
    
    # Extract from education (mocked logic)
    for edu in educations[:2]:
        area = edu.get("areaOfStudy", "").lower()
        if "compliance" in area:
            if "Compliance" not in inferred_top_skills:
                inferred_top_skills.append("Compliance Management")
            evidence.append(f"Education in: {edu.get('areaOfStudy')}")
        if "computer" in area or "software" in area:
            inferred_additional_skills.append("Software Development")
    
    # Add some default skills if none inferred
    if not inferred_top_skills:
        inferred_top_skills = ["Communication", "Problem Solving", "Team Collaboration"]
        evidence.append("Based on professional experience pattern")
    
    if not inferred_additional_skills:
        inferred_additional_skills = ["Project Management", "Analytical Thinking", "Stakeholder Management"]
    
    return {
        "topSkills": inferred_top_skills[:5],
        "additionalSkills": inferred_additional_skills[:5],
        "evidence": evidence,
        "confidence": 0.75,
        "message": "Skills inferred from your experience and education. Review and confirm to add to your profile."
    }


# ============================================================================
# TOOL 4: GET MATCHES (Mocked with multiple argument support)
# ============================================================================

def get_matches(
    profile: Dict[str, Any],
    filters: Optional[Dict[str, Any]] = None,
    search_text: Optional[str] = None,
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Retrieves top job matches based on user's talent profile.
    Supports:
    1. Vanilla: Just profile-based matching
    2. With filters: Apply location, role, or other filters
    3. With search text: Include semantic similarity with user input
    4. Combination of above
    
    Args:
        profile: User's talent profile data
        filters: Optional filters (e.g., {"country": "US", "role": "Engineer"})
        search_text: Optional text for semantic search
        top_k: Number of matches to return (default: 3)
    
    Returns:
        Dict containing matches with scores and explanations
    """
    # MOCKED IMPLEMENTATION
    # In real implementation, this would query a job database with embeddings
    
    # Mock job database
    mock_jobs = [
        {
            "jobId": "3286618BR",
            "title": "Java Technical Lead",
            "location": "Weehawken, New Jersey",
            "country": "United States",
            "division": "Group Functions",
            "rank": "Director",
            "base_score": 88
        },
        {
            "jobId": "2144332",
            "title": "Senior Compliance Manager",
            "location": "Zurich",
            "country": "Switzerland",
            "division": "Personal & Corporate Banking",
            "rank": "Director",
            "base_score": 85
        },
        {
            "jobId": "2037913",
            "title": "Risk Management Lead",
            "location": "Singapore",
            "country": "Singapore",
            "division": "Global Wealth Management",
            "rank": "Director",
            "base_score": 82
        },
        {
            "jobId": "3451287",
            "title": "Financial Crime Prevention Specialist",
            "location": "London",
            "country": "United Kingdom",
            "division": "Investment Bank",
            "rank": "Vice President",
            "base_score": 79
        },
        {
            "jobId": "2983746",
            "title": "Business Risk Analyst",
            "location": "New York",
            "country": "United States",
            "division": "Asset Management",
            "rank": "Associate Director",
            "base_score": 76
        }
    ]
    
    # Apply filters if provided
    filtered_jobs = mock_jobs.copy()
    if filters:
        if "country" in filters:
            filtered_jobs = [j for j in filtered_jobs if j["country"].lower() == filters["country"].lower()]
        if "location" in filters:
            filtered_jobs = [j for j in filtered_jobs if filters["location"].lower() in j["location"].lower()]
        if "role" in filters:
            filtered_jobs = [j for j in filtered_jobs if filters["role"].lower() in j["title"].lower()]
    
    # Adjust scores if search_text provided (mock semantic similarity)
    if search_text:
        search_lower = search_text.lower()
        for job in filtered_jobs:
            if any(word in job["title"].lower() for word in search_lower.split()):
                job["base_score"] = min(95, job["base_score"] + 5)
    
    # Sort by score and take top_k
    filtered_jobs.sort(key=lambda x: x["base_score"], reverse=True)
    top_matches = filtered_jobs[:top_k]
    
    # Generate match explanations
    matches = []
    for job in top_matches:
        why = []
        
        # Mock reasons based on profile
        user_rank = profile.get("core", {}).get("rank", {}).get("description", "")
        if user_rank and user_rank.lower() in job["rank"].lower():
            why.append(f"Matches your current level ({user_rank})")
        
        user_division = profile.get("core", {}).get("gcrs", {}).get("businessDivisionDescription", "")
        if "Banking" in user_division and "Banking" in job["division"]:
            why.append("Similar business division experience")
        
        # Check for skills/experience alignment (mocked)
        title_words = job["title"].lower().split()
        if "compliance" in title_words or "risk" in title_words:
            why.append("Aligns with your compliance and risk management background")
        
        if "lead" in title_words or "manager" in title_words:
            why.append("Leadership role matching your experience level")
        
        if not why:
            why.append("Strong overall profile match")
            why.append("Relevant industry experience")
        
        matches.append({
            "jobId": job["jobId"],
            "title": job["title"],
            "location": job["location"],
            "country": job["country"],
            "division": job["division"],
            "rank": job["rank"],
            "score": job["base_score"],
            "why": why[:3]  # Top 3 reasons
        })
    
    avg_score = sum(m["score"] for m in matches) / len(matches) if matches else 0
    
    return {
        "matches": matches,
        "count": len(matches),
        "averageScore": round(avg_score, 1),
        "filters_applied": filters or {},
        "search_text_used": search_text,
        "message": f"Found {len(matches)} matching opportunities" + 
                   (f" in {filters.get('country', 'your preferred locations')}" if filters else "")
    }


# ============================================================================
# TOOL 5: ASK JD QA (Mocked)
# ============================================================================

def ask_jd_qa(job_id: str, question: str) -> Dict[str, Any]:
    """
    Conducts Q&A over a selected job posting.
    Uses RAG (Retrieval Augmented Generation) to answer questions about the job.
    
    Args:
        job_id: The job reference number
        question: User's question about the job
    
    Returns:
        Dict containing answer and citations
    """
    # MOCKED IMPLEMENTATION
    # In real implementation, this would use RAG over job description
    
    # Mock job descriptions (simplified)
    job_descriptions = {
        "3286618BR": {
            "title": "Java Technical Lead",
            "requirements": "Bachelor's degree, 10+ years Java, ReactJS, .NET experience",
            "salary": "$158,000 to $250,000",
            "location": "Weehawken, NJ",
            "team": "Global Wealth Management Technology"
        },
        "2144332": {
            "title": "Senior Compliance Manager",
            "requirements": "8+ years compliance experience, regulatory knowledge",
            "location": "Zurich",
            "team": "P&C Compliance"
        }
    }
    
    job_info = job_descriptions.get(job_id, {})
    question_lower = question.lower()
    
    # Mock Q&A logic
    if not job_info:
        return {
            "answer": f"I don't have detailed information about job {job_id} loaded yet. Please try another job or load this posting first.",
            "citations": [],
            "confidence": 0.0
        }
    
    # Pattern matching for common questions (mock)
    if "salary" in question_lower or "pay" in question_lower or "compensation" in question_lower:
        answer = f"The salary range for this position is {job_info.get('salary', 'not specified in the posting')}."
        citations = ["Job posting - Compensation section"]
    
    elif "requirement" in question_lower or "qualification" in question_lower or "need" in question_lower:
        answer = f"The key requirements are: {job_info.get('requirements', 'not specified')}."
        citations = ["Job posting - Requirements section"]
    
    elif "location" in question_lower or "where" in question_lower or "remote" in question_lower:
        answer = f"This position is based in {job_info.get('location', 'location not specified')}."
        citations = ["Job posting - Location section"]
    
    elif "team" in question_lower or "department" in question_lower or "division" in question_lower:
        answer = f"You would be joining the {job_info.get('team', 'team not specified')}."
        citations = ["Job posting - Team information"]
    
    else:
        answer = f"For the {job_info.get('title')} role: {job_info.get('requirements', 'Please ask a more specific question about requirements, location, team, or compensation.')}"
        citations = ["Job posting - General information"]
    
    return {
        "answer": answer,
        "citations": citations,
        "confidence": 0.85,
        "job_id": job_id,
        "job_title": job_info.get("title", "Unknown")
    }


# ============================================================================
# TOOL 6: DRAFT EMAIL (Mocked)
# ============================================================================

def draft_email(
    profile: Dict[str, Any],
    job_id: Optional[str] = None,
    recipient_type: str = "hiring_manager",
    tone: str = "formal"
) -> Dict[str, Any]:
    """
    Drafts a message/note to Hiring Manager or Recruiter.
    
    Args:
        profile: User's talent profile data
        job_id: Optional job reference number
        recipient_type: "hiring_manager" or "recruiter"
        tone: "formal", "friendly", or "concise"
    
    Returns:
        Dict containing subject and body of the email
    """
    # MOCKED IMPLEMENTATION
    # In real implementation, this would use LLM to generate personalized email
    
    # Extract user name
    core = profile.get("core", {})
    name = core.get("name", {})
    user_name = f"{name.get('businessFirstName', 'Candidate')} {name.get('businessLastName', '')}"
    user_name = user_name.strip() or "Candidate"
    
    # Extract current title
    current_title = core.get("businessTitle", "Professional")
    
    # Job context
    job_context = f" for the position (Ref: {job_id})" if job_id else ""
    
    # Draft email based on tone
    if tone == "formal":
        subject = f"Application for Position{' - ' + job_id if job_id else ''} - {user_name}"
        body = f"""Dear {recipient_type.replace('_', ' ').title()},

I am writing to express my strong interest in this opportunity{job_context}. With my background as {current_title} and extensive experience in compliance and risk management, I believe I would be a valuable addition to your team.

My experience includes:
- Leadership roles in financial crime prevention and business risk management
- Strong technical and analytical capabilities
- Cross-divisional and international experience

I would welcome the opportunity to discuss how my skills and experience align with your team's needs.

Thank you for your consideration.

Best regards,
{user_name}"""
    
    elif tone == "friendly":
        subject = f"Excited about the opportunity{' - ' + job_id if job_id else ''}!"
        body = f"""Hi there,

I recently came across this position{job_context} and I'm really excited about the possibility of joining your team!

As someone with a background in {current_title}, I've been working on similar challenges and I think I could bring valuable perspective and experience to the role.

I'd love to chat more about the opportunity and how I might contribute to your team's success.

Looking forward to connecting!

Best,
{user_name}"""
    
    else:  # concise
        subject = f"Application{' - ' + job_id if job_id else ''}"
        body = f"""Hello,

I'm interested in this opportunity{job_context}. My background as {current_title} with experience in compliance, risk management, and leadership aligns well with the role requirements.

I'd appreciate the chance to discuss this further.

Best regards,
{user_name}"""
    
    return {
        "subject": subject,
        "body": body,
        "recipient_type": recipient_type,
        "tone": tone,
        "message": "Email draft generated. Review and customize before sending."
    }


# ============================================================================
# TOOL REGISTRY FOR LANGCHAIN
# ============================================================================

def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Returns tool definitions in a format suitable for LangChain tool calling.
    """
    return [
        {
            "name": "profile_analyzer",
            "description": "Analyzes user's profile to detect missing or insufficient sections and provides completion score with recommendations for improvement",
            "parameters": {
                "type": "object",
                "properties": {
                    "completion_threshold": {
                        "type": "integer",
                        "description": "Minimum score to consider profile complete (default: 80)"
                    }
                }
            }
        },
        {
            "name": "update_profile",
            "description": "Updates a section of the user's talent profile. Currently supports updating skills section; other sections coming later",
            "parameters": {
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "enum": ["skills"],
                        "description": "Profile section to update (currently only 'skills' supported)"
                    },
                    "updates": {
                        "type": "object",
                        "description": "Dictionary of updates to apply to the section"
                    }
                },
                "required": ["section"]
            }
        },
        {
            "name": "infer_skills",
            "description": "Analyzes profile experience and education to suggest top skills and additional skills that can be added to the profile",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_matches",
            "description": "Finds top matching job opportunities based on user's profile. Supports optional filters (country, location, role) and text-based semantic search",
            "parameters": {
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "object",
                        "description": "Optional filters like country, location, or role type"
                    },
                    "search_text": {
                        "type": "string",
                        "description": "Optional text to enhance matching with semantic search"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of matches to return (default: 3)"
                    }
                }
            }
        },
        {
            "name": "ask_jd_qa",
            "description": "Answers questions about a specific job posting using the job description. Requires job_id and a question",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "The job reference number"
                    },
                    "question": {
                        "type": "string",
                        "description": "Question about the job posting"
                    }
                },
                "required": ["job_id", "question"]
            }
        },
        {
            "name": "draft_email",
            "description": "Drafts a professional email to hiring manager or recruiter. Can be customized by tone and job reference",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Optional job reference number"
                    },
                    "recipient_type": {
                        "type": "string",
                        "enum": ["hiring_manager", "recruiter"],
                        "description": "Type of recipient (default: hiring_manager)"
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["formal", "friendly", "concise"],
                        "description": "Email tone (default: formal)"
                    }
                }
            }
        }
    ]


# ============================================================================
# TOOL EXECUTION DISPATCHER
# ============================================================================

def execute_tool(tool_name: str, profile: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Central dispatcher for tool execution.
    
    Args:
        tool_name: Name of the tool to execute
        profile: User's profile data
        **kwargs: Tool-specific parameters
    
    Returns:
        Dict containing tool execution results
    """
    try:
        if tool_name == "profile_analyzer":
            return profile_analyzer(profile, kwargs.get("completion_threshold", 80))
        
        elif tool_name == "update_profile":
            return update_profile(profile, kwargs.get("section", "skills"), kwargs.get("updates"))
        
        elif tool_name == "infer_skills":
            return infer_skills(profile)
        
        elif tool_name == "get_matches":
            return get_matches(
                profile,
                filters=kwargs.get("filters"),
                search_text=kwargs.get("search_text"),
                top_k=kwargs.get("top_k", 3)
            )
        
        elif tool_name == "ask_jd_qa":
            return ask_jd_qa(kwargs.get("job_id", ""), kwargs.get("question", ""))
        
        elif tool_name == "draft_email":
            return draft_email(
                profile,
                job_id=kwargs.get("job_id"),
                recipient_type=kwargs.get("recipient_type", "hiring_manager"),
                tone=kwargs.get("tone", "formal")
            )
        
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "available_tools": ["profile_analyzer", "update_profile", "infer_skills", 
                                  "get_matches", "ask_jd_qa", "draft_email"]
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name
        }

