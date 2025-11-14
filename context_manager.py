"""
Context and session state management for MyCareer Agentic Assistant.
Handles short-term memory, session state, and context tracking.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class AgentContext:
    """
    Manages context and state for a chat session.
    Provides access to profile, chat history, and previous actions.
    """
    
    def __init__(self, user_id: str, profile: Optional[Dict[str, Any]] = None):
        """
        Initialize agent context for a session.
        
        Args:
            user_id: Unique identifier for the user
            profile: User's talent profile data
        """
        self.user_id = user_id
        self.profile = profile or {}
        self.session_start = datetime.now()
        
        # Short-term memory
        self.chat_history: List[Dict[str, Any]] = []
        self.action_history: List[Dict[str, Any]] = []
        self.tool_results: Dict[str, Any] = {}
        
        # Context tracking
        self.current_intent: Optional[str] = None
        self.last_tool_executed: Optional[str] = None
        self.last_confidence: float = 0.0
        self.pending_clarification: bool = False
        
        # Match tracking for low score detection
        self.match_history: List[Dict[str, Any]] = []
        self.consecutive_low_matches = 0
        
        # Profile analysis tracking
        self.profile_analysis_result: Optional[Dict[str, Any]] = None
        self.profile_completion_score: int = 0
        self.missing_sections: List[str] = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a message to chat history.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (tool info, confidence, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.chat_history.append(message)
    
    def add_action(self, tool_name: str, params: Dict[str, Any], result: Any):
        """
        Record a tool execution action.
        
        Args:
            tool_name: Name of the tool executed
            params: Parameters passed to the tool
            result: Tool execution result
        """
        action = {
            "tool": tool_name,
            "params": params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.action_history.append(action)
        self.last_tool_executed = tool_name
        
        # Store latest result for this tool
        self.tool_results[tool_name] = result
        
        # Track matches for low score detection
        if tool_name == "get_matches" and isinstance(result, dict):
            self._track_match_result(result)
    
    def _track_match_result(self, match_result: Dict[str, Any]):
        """Track match results for detecting low quality matches."""
        avg_score = match_result.get("averageScore", 0)
        
        self.match_history.append({
            "average_score": avg_score,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check for consecutive low matches
        recent_matches = self.match_history[-2:]
        if len(recent_matches) >= 2:
            if all(m["average_score"] < 60 for m in recent_matches):
                self.consecutive_low_matches = len(recent_matches)
            else:
                self.consecutive_low_matches = 0
    
    def update_profile_analysis(self, analysis_result: Dict[str, Any]):
        """
        Store profile analysis result in context.
        
        Args:
            analysis_result: Result from profile_analyzer tool
        """
        self.profile_analysis_result = analysis_result
        self.profile_completion_score = analysis_result.get("completionScore", 0)
        self.missing_sections = analysis_result.get("missingSections", [])
    
    def get_recent_messages(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent messages."""
        return self.chat_history[-count:]
    
    def get_recent_actions(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get the most recent actions."""
        return self.action_history[-count:]
    
    def get_session_summary(self) -> str:
        """
        Generate a summary of the current session for context.
        """
        summary_parts = []
        
        # Session duration
        duration = (datetime.now() - self.session_start).seconds // 60
        summary_parts.append(f"Session duration: {duration} minutes")
        
        # Messages exchanged
        summary_parts.append(f"Messages: {len(self.chat_history)}")
        
        # Tools used
        tools_used = set(action["tool"] for action in self.action_history)
        if tools_used:
            summary_parts.append(f"Tools used: {', '.join(tools_used)}")
        
        # Recent focus
        if self.last_tool_executed:
            summary_parts.append(f"Last action: {self.last_tool_executed}")
        
        return " | ".join(summary_parts)
    
    def should_suggest_profile_improvement(self) -> bool:
        """
        Determine if profile improvement should be suggested.
        Based on consecutive low match scores.
        """
        return self.consecutive_low_matches >= 2
    
    def can_show_matches(self) -> bool:
        """
        Determine if job matches can be shown based on profile quality.
        """
        return self.profile_completion_score >= 50
    
    def get_last_match_scores(self) -> List[float]:
        """Get list of recent match average scores."""
        return [m["average_score"] for m in self.match_history]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize context to dictionary for storage.
        """
        return {
            "user_id": self.user_id,
            "session_start": self.session_start.isoformat(),
            "profile_completion_score": self.profile_completion_score,
            "missing_sections": self.missing_sections,
            "last_tool_executed": self.last_tool_executed,
            "consecutive_low_matches": self.consecutive_low_matches,
            "chat_history_count": len(self.chat_history),
            "action_history_count": len(self.action_history)
        }
    
    def get_context_for_llm(self) -> str:
        """
        Generate a context summary for LLM prompts.
        """
        context_items = []
        
        # Profile status
        context_items.append(f"Profile completion: {self.profile_completion_score}%")
        if self.missing_sections:
            context_items.append(f"Missing sections: {', '.join(self.missing_sections)}")
        
        # Recent activity
        if self.last_tool_executed:
            context_items.append(f"Recent action: {self.last_tool_executed}")
        
        # Match quality
        if self.match_history:
            recent_avg = self.match_history[-1]["average_score"]
            context_items.append(f"Last match score: {recent_avg}")
        
        # Pending items
        if self.should_suggest_profile_improvement():
            context_items.append("⚠️ Low match quality detected - suggest profile improvement")
        
        if self.pending_clarification:
            context_items.append("⚠️ Awaiting user clarification")
        
        return " | ".join(context_items)


class ContextManager:
    """
    Manages multiple user contexts and session storage.
    """
    
    def __init__(self):
        """Initialize context manager."""
        self.active_contexts: Dict[str, AgentContext] = {}
    
    def get_or_create_context(
        self,
        user_id: str,
        profile: Optional[Dict[str, Any]] = None
    ) -> AgentContext:
        """
        Get existing context or create new one for a user.
        
        Args:
            user_id: User identifier
            profile: User's profile data
        
        Returns:
            AgentContext for the user
        """
        if user_id not in self.active_contexts:
            self.active_contexts[user_id] = AgentContext(user_id, profile)
        elif profile and not self.active_contexts[user_id].profile:
            # Update profile if it wasn't set before
            self.active_contexts[user_id].profile = profile
        
        return self.active_contexts[user_id]
    
    def get_context(self, user_id: str) -> Optional[AgentContext]:
        """Get context for a user if it exists."""
        return self.active_contexts.get(user_id)
    
    def clear_context(self, user_id: str):
        """Clear context for a user (e.g., on session end)."""
        if user_id in self.active_contexts:
            del self.active_contexts[user_id]
    
    def get_all_active_sessions(self) -> List[str]:
        """Get list of all active user sessions."""
        return list(self.active_contexts.keys())


# Singleton instance
_context_manager_instance = None

def get_context_manager() -> ContextManager:
    """Returns the singleton ContextManager instance."""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
    return _context_manager_instance

