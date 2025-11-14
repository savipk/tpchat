"""
Tool ranking and next best actions selection logic.
Determines which 3 tools to show as action buttons based on context.
"""

from typing import Dict, Any, List, Optional, Tuple


# Default tool priority ranking (as per design spec)
DEFAULT_TOOL_RANKING = [
    "get_matches",
    "profile_analyzer",
    "infer_skills",
    "update_profile",
    "ask_jd_qa",
    "draft_email"
]


class ToolRanker:
    """
    Handles tool ranking and next best action selection based on context.
    """
    
    def __init__(self):
        self.default_ranking = DEFAULT_TOOL_RANKING
    
    def rank_tools(
        self,
        primary_tool: Optional[str] = None,
        confidence: float = 0.0,
        completion_score: int = 100,
        recent_action: Optional[str] = None,
        last_match_scores: Optional[List[float]] = None,
        missing_sections: Optional[List[str]] = None,
        session_history: Optional[List[str]] = None
    ) -> List[str]:
        """
        Ranks tools and returns top 3 to display as action buttons.
        
        Args:
            primary_tool: The tool mapped from user intent (if any)
            confidence: Confidence score of the primary tool mapping
            completion_score: Profile completion score (0-100)
            recent_action: Most recent action taken
            last_match_scores: List of recent match scores
            missing_sections: List of missing profile sections
            session_history: List of recent actions in session
        
        Returns:
            List of 3 tool names in priority order
        """
        # Calculate context factors
        has_profile_issues = completion_score < 80 or (missing_sections and len(missing_sections) > 0)
        low_match_scores = self._has_low_match_scores(last_match_scores)
        just_showed_matches = recent_action == "get_matches"
        missing_skills = missing_sections and "skills" in missing_sections
        
        # Determine ranking strategy based on context
        if completion_score < 50:
            # Critical profile issues - prioritize profile improvement
            ranked_tools = self._get_profile_improvement_ranking(missing_sections)
        
        elif low_match_scores:
            # Low match scores - suggest profile improvement
            ranked_tools = self._get_low_match_ranking(missing_sections)
        
        elif just_showed_matches:
            # Just showed matches - prioritize follow-up actions
            ranked_tools = self._get_post_match_ranking()
        
        elif has_profile_issues and confidence < 0.75:
            # Profile needs work and no strong intent - suggest improvement
            ranked_tools = self._get_profile_focus_ranking(missing_sections)
        
        elif primary_tool and confidence >= 0.75:
            # Strong intent mapping - use primary tool first
            ranked_tools = self._get_intent_based_ranking(primary_tool, completion_score, missing_sections)
        
        else:
            # Default ranking
            ranked_tools = self.default_ranking.copy()
        
        # Ensure primary tool is first if provided and confidence is reasonable
        if primary_tool and confidence >= 0.45 and primary_tool in ranked_tools:
            ranked_tools.remove(primary_tool)
            ranked_tools.insert(0, primary_tool)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tools = []
        for tool in ranked_tools:
            if tool not in seen:
                seen.add(tool)
                unique_tools.append(tool)
        
        # Return top 3
        return unique_tools[:3]
    
    def _has_low_match_scores(self, scores: Optional[List[float]]) -> bool:
        """Check if recent match scores are below threshold (60)."""
        if not scores or len(scores) == 0:
            return False
        recent_scores = scores[-3:]  # Last 3 match sessions
        return len(recent_scores) >= 2 and sum(recent_scores) / len(recent_scores) < 60
    
    def _get_profile_improvement_ranking(self, missing_sections: Optional[List[str]]) -> List[str]:
        """Ranking when profile completion is critical (<50%)."""
        ranking = ["profile_analyzer"]
        
        if missing_sections:
            if "skills" in missing_sections:
                ranking.append("infer_skills")
                ranking.append("update_profile")
            else:
                ranking.append("update_profile")
                ranking.append("infer_skills")
        else:
            ranking.extend(["infer_skills", "update_profile"])
        
        # Add remaining tools
        for tool in self.default_ranking:
            if tool not in ranking:
                ranking.append(tool)
        
        return ranking
    
    def _get_low_match_ranking(self, missing_sections: Optional[List[str]]) -> List[str]:
        """Ranking when match scores are consistently low."""
        ranking = ["profile_analyzer", "infer_skills"]
        
        if missing_sections and "skills" in missing_sections:
            ranking.append("update_profile")
        else:
            ranking.append("get_matches")
        
        # Add remaining tools
        for tool in self.default_ranking:
            if tool not in ranking:
                ranking.append(tool)
        
        return ranking
    
    def _get_post_match_ranking(self) -> List[str]:
        """Ranking after showing job matches."""
        ranking = ["ask_jd_qa", "draft_email", "get_matches"]
        
        # Add remaining tools
        for tool in self.default_ranking:
            if tool not in ranking:
                ranking.append(tool)
        
        return ranking
    
    def _get_profile_focus_ranking(self, missing_sections: Optional[List[str]]) -> List[str]:
        """Ranking when profile has issues but not critical."""
        ranking = ["profile_analyzer"]
        
        if missing_sections and "skills" in missing_sections:
            ranking.extend(["infer_skills", "update_profile"])
        else:
            ranking.extend(["get_matches", "infer_skills"])
        
        # Add remaining tools
        for tool in self.default_ranking:
            if tool not in ranking:
                ranking.append(tool)
        
        return ranking
    
    def _get_intent_based_ranking(
        self,
        primary_tool: str,
        completion_score: int,
        missing_sections: Optional[List[str]]
    ) -> List[str]:
        """Ranking based on strong intent mapping."""
        ranking = [primary_tool]
        
        # Add contextually relevant follow-up tools
        if primary_tool == "get_matches":
            ranking.extend(["ask_jd_qa", "draft_email"])
        
        elif primary_tool == "profile_analyzer":
            if missing_sections and "skills" in missing_sections:
                ranking.extend(["infer_skills", "update_profile"])
            else:
                ranking.extend(["update_profile", "get_matches"])
        
        elif primary_tool == "infer_skills":
            ranking.extend(["update_profile", "profile_analyzer"])
        
        elif primary_tool == "update_profile":
            ranking.extend(["profile_analyzer", "get_matches"])
        
        elif primary_tool == "ask_jd_qa":
            ranking.extend(["draft_email", "get_matches"])
        
        elif primary_tool == "draft_email":
            ranking.extend(["ask_jd_qa", "get_matches"])
        
        # Add remaining tools
        for tool in self.default_ranking:
            if tool not in ranking:
                ranking.append(tool)
        
        return ranking
    
    def get_tool_display_info(self, tool_name: str) -> Dict[str, str]:
        """
        Returns display information for a tool (label, icon, tooltip).
        """
        tool_info = {
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
        
        return tool_info.get(tool_name, {
            "label": tool_name.replace("_", " ").title(),
            "icon": "🔧",
            "tooltip": f"Execute {tool_name}"
        })
    
    def should_show_clarifying_questions(self, confidence: float) -> bool:
        """
        Determines if clarifying questions should be shown based on confidence.
        """
        return 0.45 <= confidence < 0.75
    
    def should_use_fallback(self, confidence: float) -> bool:
        """
        Determines if fallback behavior should be used.
        """
        return confidence < 0.45


# Singleton instance
_ranker_instance = None

def get_tool_ranker() -> ToolRanker:
    """Returns the singleton ToolRanker instance."""
    global _ranker_instance
    if _ranker_instance is None:
        _ranker_instance = ToolRanker()
    return _ranker_instance

