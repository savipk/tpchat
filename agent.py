"""
LangGraph-based agent implementation for MyCareer Agentic Assistant.
Handles intent detection, tool mapping, confidence scoring, and response generation.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
import json

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from context_manager import AgentContext
from tool_ranker import get_tool_ranker
from tools import execute_tool, get_tool_definitions
import prompts


def _initialize_llm(model_name: str, temperature: float = 0.7):
    """
    Initialize LLM based on configuration.
    Supports both OpenAI and Azure OpenAI with easy switching.
    
    Args:
        model_name: Model name or deployment name
        temperature: LLM temperature
    
    Returns:
        Configured LLM instance (ChatOpenAI or AzureChatOpenAI)
    
    Environment Variables:
        LLM_PROVIDER: "openai" or "azure" (default: "openai")
        
        For OpenAI:
            OPENAI_API_KEY: OpenAI API key
        
        For Azure OpenAI:
            AZURE_OPENAI_API_KEY: Azure OpenAI API key
            AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
            AZURE_OPENAI_API_VERSION: API version (default: "2024-02-15-preview")
            AZURE_OPENAI_DEPLOYMENT_NAME: Deployment name (overrides model_name)
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "azure":
        # Azure OpenAI configuration
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", model_name)
        
        if not api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable not set")
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable not set")
        
        print(f"Initializing Azure OpenAI with deployment: {deployment_name}")
        
        return AzureChatOpenAI(
            azure_deployment=deployment_name,
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            temperature=temperature
        )
    
    else:
        # Standard OpenAI configuration
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        print(f"Initializing OpenAI with model: {model_name}")
        
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key
        )


class MyCareerAgent:
    """
    Main agent class that orchestrates the conversation flow.
    Uses LangChain for LLM interactions and manages the complete workflow.
    Supports both OpenAI and Azure OpenAI.
    """
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.7):
        """
        Initialize the agent with LLM configuration.
        
        Args:
            model_name: Model name (OpenAI) or deployment name (Azure)
            temperature: LLM temperature (default: 0.7)
        """
        self.llm = _initialize_llm(model_name, temperature)
        self.tool_ranker = get_tool_ranker()
        self.tool_definitions = get_tool_definitions()
    
    def process_user_input(
        self,
        user_input: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user text input.
        
        Flow: User input → Intent detection → Tool mapping → Tool ranking → Response generation
        
        Args:
            user_input: User's message
            context: Current agent context
        
        Returns:
            Dict containing response text and action buttons
        """
        # Step 1: Detect intent and map to tools
        intent_result = self._detect_intent(user_input, context)
        
        primary_tool = intent_result.get("primary_tool")
        confidence = intent_result.get("confidence", 0.0)
        extracted_params = intent_result.get("parameters", {})
        
        # Update context
        context.current_intent = primary_tool
        context.last_confidence = confidence
        
        # Step 2: Determine response strategy based on confidence
        if confidence < 0.45:
            # Fallback: Cannot map to tool
            return self._generate_fallback_response(user_input, context)
        
        elif 0.45 <= confidence < 0.75:
            # Medium confidence: Ask clarifying questions
            context.pending_clarification = True
            return self._generate_clarifying_response(user_input, intent_result, context)
        
        else:
            # High confidence: Recommend tool action
            context.pending_clarification = False
            return self._generate_tool_recommendation_response(
                user_input,
                primary_tool,
                confidence,
                extracted_params,
                context
            )
    
    def execute_tool_action(
        self,
        tool_name: str,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool and generate response with results.
        
        Flow: Tool execution → Results → Response generation → Next best actions
        
        Args:
            tool_name: Name of tool to execute
            context: Current agent context
            params: Optional parameters for the tool
        
        Returns:
            Dict containing results, response text, and action buttons
        """
        # Execute the tool
        params = params or {}
        result = execute_tool(tool_name, context.profile, **params)
        
        # Record action in context
        context.add_action(tool_name, params, result)
        
        # Special handling for profile analyzer
        if tool_name == "profile_analyzer":
            context.update_profile_analysis(result)
        
        # Generate response with results
        return self._generate_tool_result_response(tool_name, result, context)
    
    def _detect_intent(
        self,
        user_input: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Detect user intent and map to appropriate tool.
        Returns primary tool, confidence score, and extracted parameters.
        """
        # Build prompt for intent detection
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompts.INTENT_DETECTION_SYSTEM_PROMPT),
            ("human", prompts.INTENT_DETECTION_USER_TEMPLATE)
        ])
        
        # Prepare context information
        session_summary = context.get_session_summary()
        previous_action = context.last_tool_executed or "None"
        completion_score = context.profile_completion_score
        
        # Format prompt
        messages = prompt_template.format_messages(
            user_input=user_input,
            completion_score=completion_score,
            previous_action=previous_action,
            session_summary=session_summary
        )
        
        # Call LLM for intent detection
        try:
            response = self.llm.invoke(messages)
            analysis = self._parse_intent_response(response.content)
            return analysis
        
        except Exception as e:
            print(f"Intent detection error: {e}")
            # Fallback to keyword matching
            return self._fallback_intent_detection(user_input)
    
    def _parse_intent_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response for intent detection.
        Extracts tool name, confidence, and parameters.
        """
        # Try to extract structured information from LLM response
        response_lower = response_text.lower()
        
        # Map keywords to tools and confidence
        tool_keywords = {
            "get_matches": ["match", "job", "find", "search", "opportunity", "role", "position"],
            "profile_analyzer": ["analyze", "profile", "complete", "check", "score", "missing"],
            "infer_skills": ["skill", "suggest", "infer", "recommend skill", "add skill"],
            "update_profile": ["update", "change", "modify", "edit", "add to profile"],
            "ask_jd_qa": ["ask about", "question about", "tell me about", "job posting", "jd"],
            "draft_email": ["email", "message", "write", "draft", "contact", "reach out"]
        }
        
        # Score each tool based on keyword presence
        tool_scores = {}
        for tool, keywords in tool_keywords.items():
            score = sum(1 for keyword in keywords if keyword in response_lower)
            tool_scores[tool] = score
        
        # Get highest scoring tool
        if tool_scores:
            primary_tool = max(tool_scores, key=tool_scores.get)
            max_score = tool_scores[primary_tool]
            
            # Convert score to confidence (normalize)
            confidence = min(0.95, 0.4 + (max_score * 0.15))
        else:
            primary_tool = None
            confidence = 0.0
        
        return {
            "primary_tool": primary_tool,
            "confidence": confidence,
            "parameters": {},
            "reasoning": response_text[:200]  # First 200 chars as reasoning
        }
    
    def _fallback_intent_detection(self, user_input: str) -> Dict[str, Any]:
        """
        Fallback keyword-based intent detection when LLM fails.
        """
        user_lower = user_input.lower()
        
        # Simple keyword matching
        if any(word in user_lower for word in ["job", "match", "find", "search", "opportunity"]):
            return {"primary_tool": "get_matches", "confidence": 0.65, "parameters": {}}
        
        elif any(word in user_lower for word in ["profile", "analyze", "check", "complete"]):
            return {"primary_tool": "profile_analyzer", "confidence": 0.65, "parameters": {}}
        
        elif any(word in user_lower for word in ["skill", "suggest", "recommend"]):
            return {"primary_tool": "infer_skills", "confidence": 0.60, "parameters": {}}
        
        elif any(word in user_lower for word in ["update", "change", "edit"]):
            return {"primary_tool": "update_profile", "confidence": 0.60, "parameters": {}}
        
        elif any(word in user_lower for word in ["email", "message", "draft", "write"]):
            return {"primary_tool": "draft_email", "confidence": 0.60, "parameters": {}}
        
        elif any(word in user_lower for word in ["ask", "question", "tell me about"]):
            return {"primary_tool": "ask_jd_qa", "confidence": 0.55, "parameters": {}}
        
        else:
            return {"primary_tool": None, "confidence": 0.0, "parameters": {}}
    
    def _generate_fallback_response(
        self,
        user_input: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Generate response when intent cannot be mapped to any tool.
        Shows available capabilities and default action buttons.
        """
        # Use LLM to generate polite fallback message
        try:
            prompt = prompts.FALLBACK_RESPONSE_PROMPT.format(user_input=user_input)
            messages = [
                SystemMessage(content=prompts.RESPONSE_GENERATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            response_text = response.content
        
        except Exception as e:
            print(f"Fallback response generation error: {e}")
            response_text = (
                "I'd be happy to help you with your career! Here are the actions I can assist with:\n\n"
                "Find matching jobs based on your profile\n"
                "Analyze your profile for completeness\n"
                "Suggest skills from your experience\n"
                "Update your profile information\n"
                "Answer questions about job postings\n"
                "Draft messages to recruiters\n\n"
                "What would you like to do?"
            )
        
        # Get default ranked tools
        ranked_tools = self.tool_ranker.rank_tools(
            completion_score=context.profile_completion_score,
            missing_sections=context.missing_sections
        )
        
        action_buttons = self._create_action_buttons(ranked_tools)
        
        return {
            "response_text": response_text,
            "action_buttons": action_buttons,
            "confidence": 0.0,
            "mapped_tool": None
        }
    
    def _generate_clarifying_response(
        self,
        user_input: str,
        intent_result: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Generate response with clarifying questions for medium confidence.
        """
        primary_tool = intent_result.get("primary_tool")
        confidence = intent_result.get("confidence", 0.0)
        
        # Generate clarifying question
        try:
            prompt = prompts.CLARIFYING_QUESTIONS_PROMPT.format(
                user_input=user_input,
                possible_tools=[primary_tool] if primary_tool else [],
                confidence_scores={"primary": confidence}
            )
            messages = [
                SystemMessage(content=prompts.RESPONSE_GENERATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            response_text = response.content
        
        except Exception as e:
            print(f"Clarifying response error: {e}")
            response_text = (
                "I want to make sure I help you with the right action. "
                f"Are you looking to {self._get_tool_description(primary_tool)}?"
            )
        
        # Rank tools with primary tool first
        ranked_tools = self.tool_ranker.rank_tools(
            primary_tool=primary_tool,
            confidence=confidence,
            completion_score=context.profile_completion_score,
            missing_sections=context.missing_sections
        )
        
        action_buttons = self._create_action_buttons(ranked_tools)
        
        return {
            "response_text": response_text,
            "action_buttons": action_buttons,
            "confidence": confidence,
            "mapped_tool": primary_tool
        }
    
    def _generate_tool_recommendation_response(
        self,
        user_input: str,
        primary_tool: str,
        confidence: float,
        extracted_params: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Generate response recommending a tool action (high confidence).
        """
        # Check special conditions
        if primary_tool == "get_matches" and not context.can_show_matches():
            # Profile too incomplete for matches
            return self._generate_profile_improvement_suggestion(context)
        
        # Check if should suggest profile improvement (consecutive low matches)
        if context.should_suggest_profile_improvement():
            return self._generate_profile_improvement_suggestion(context)
        
        # Generate response text
        guidelines = prompts.get_response_guidelines(confidence, len(context.missing_sections) > 0)
        
        try:
            prompt = prompts.RESPONSE_TEXT_TEMPLATE.format(
                user_input=user_input,
                mapped_tool=primary_tool,
                confidence=confidence,
                tool_rank=1,
                completion_score=context.profile_completion_score,
                profile_issues=", ".join(context.missing_sections) if context.missing_sections else "None",
                response_guidelines=guidelines
            )
            messages = [
                SystemMessage(content=prompts.RESPONSE_GENERATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            response_text = response.content
        
        except Exception as e:
            print(f"Response generation error: {e}")
            tool_desc = self._get_tool_description(primary_tool)
            response_text = f"I can help you {tool_desc}. Click the button below to proceed."
        
        # Rank tools
        ranked_tools = self.tool_ranker.rank_tools(
            primary_tool=primary_tool,
            confidence=confidence,
            completion_score=context.profile_completion_score,
            recent_action=context.last_tool_executed,
            missing_sections=context.missing_sections
        )
        
        action_buttons = self._create_action_buttons(ranked_tools, extracted_params if primary_tool == ranked_tools[0] else None)
        
        return {
            "response_text": response_text,
            "action_buttons": action_buttons,
            "confidence": confidence,
            "mapped_tool": primary_tool
        }
    
    def _generate_tool_result_response(
        self,
        tool_name: str,
        result: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Generate response after tool execution with results.
        """
        # Check for tool execution error
        if not result.get("success", True) and "error" in result:
            return self._generate_error_response(tool_name, result, context)
        
        # Format results based on tool type
        result_text = self._format_tool_results(tool_name, result)
        
        # Rank next best actions
        ranked_tools = self.tool_ranker.rank_tools(
            completion_score=context.profile_completion_score,
            recent_action=tool_name,
            last_match_scores=context.get_last_match_scores(),
            missing_sections=context.missing_sections
        )
        
        action_buttons = self._create_action_buttons(ranked_tools)
        
        # Generate response text with results
        try:
            prompt = prompts.RESPONSE_WITH_RESULTS_TEMPLATE.format(
                tool_name=tool_name,
                tool_results=str(result)[:500],  # Truncate for prompt
                success=result.get("success", True),
                next_actions=", ".join(ranked_tools)
            )
            messages = [
                SystemMessage(content=prompts.RESPONSE_GENERATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            response_text = response.content + "\n\n" + result_text
        
        except Exception as e:
            print(f"Result response generation error: {e}")
            response_text = f"Here are your results:\n\n{result_text}\n\nWhat would you like to do next?"
        
        return {
            "response_text": response_text,
            "action_buttons": action_buttons,
            "tool_result": result,
            "formatted_result": result_text
        }
    
    def _generate_profile_improvement_suggestion(
        self,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Generate response suggesting profile improvement.
        Triggered when profile score < 50 or consecutive low matches.
        """
        try:
            prompt = prompts.PROFILE_IMPROVEMENT_SUGGESTION_PROMPT.format(
                completion_score=context.profile_completion_score,
                missing_sections=", ".join(context.missing_sections),
                insufficient_sections="To be analyzed"
            )
            messages = [
                SystemMessage(content=prompts.RESPONSE_GENERATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            response_text = response.content
        
        except Exception as e:
            print(f"Profile improvement response error: {e}")
            response_text = (
                "I notice your profile could use some enhancements to get better job matches. "
                f"Your current completion score is {context.profile_completion_score}%. "
                "Let's improve it together!"
            )
        
        # Prioritize profile improvement tools
        ranked_tools = ["profile_analyzer", "infer_skills", "update_profile"]
        action_buttons = self._create_action_buttons(ranked_tools)
        
        return {
            "response_text": response_text,
            "action_buttons": action_buttons,
            "suggestion_type": "profile_improvement"
        }
    
    def _generate_error_response(
        self,
        tool_name: str,
        result: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Generate user-friendly error response.
        """
        error_msg = result.get("error", "Unknown error")
        
        try:
            prompt = prompts.ERROR_RECOVERY_PROMPT.format(
                tool_name=tool_name,
                error_message=error_msg
            )
            messages = [
                SystemMessage(content=prompts.RESPONSE_GENERATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            response_text = response.content
        
        except Exception as e:
            print(f"Error response generation error: {e}")
            response_text = (
                "I encountered an issue completing that action. "
                "Let's try something else. What would you like to do?"
            )
        
        # Default action buttons
        ranked_tools = self.tool_ranker.rank_tools(
            completion_score=context.profile_completion_score
        )
        action_buttons = self._create_action_buttons(ranked_tools)
        
        return {
            "response_text": response_text,
            "action_buttons": action_buttons,
            "error": True
        }
    
    def _format_tool_results(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format tool results for display."""
        if tool_name == "profile_analyzer":
            return self._format_profile_analysis(result)
        elif tool_name == "get_matches":
            return self._format_matches(result)
        elif tool_name == "infer_skills":
            return self._format_skills(result)
        elif tool_name == "ask_jd_qa":
            return self._format_qa_answer(result)
        elif tool_name == "draft_email":
            return self._format_email(result)
        else:
            return json.dumps(result, indent=2)
    
    def _format_profile_analysis(self, result: Dict[str, Any]) -> str:
        """Format profile analysis results."""
        score = result.get("completionScore", 0)
        missing = result.get("missingSections", [])
        insights = result.get("insights", [])
        
        text = f"### Profile Analysis\n\n**Completion Score:** {score}%\n\n"
        
        if missing:
            text += f"**Missing Sections:** {', '.join(missing)}\n\n"
        
        if insights:
            text += "**Insights:**\n"
            for insight in insights[:3]:
                area = insight.get("area", "").title()
                note = insight.get("note", insight.get("observation", ""))
                text += f"- *{area}*: {note}\n"
        
        return text
    
    def _format_matches(self, result: Dict[str, Any]) -> str:
        """Format job matches."""
        matches = result.get("matches", [])
        
        if not matches:
            return "No matching jobs found. Try updating your profile or adjusting filters."
        
        text = "### Top Job Matches\n\n"
        for i, match in enumerate(matches, 1):
            title = match.get("title", "Unknown")
            job_id = match.get("jobId", "N/A")
            score = match.get("score", 0)
            location = match.get("location", "")
            why = match.get("why", [])
            
            text += f"**{i}. {title}**\n"
            text += f"   📍 {location} | ID: `{job_id}` | Match: **{score}%**\n"
            if why:
                text += f"   Why: {why[0]}\n"
            text += "\n"
        
        return text
    
    def _format_skills(self, result: Dict[str, Any]) -> str:
        """Format inferred skills."""
        top = result.get("topSkills", [])
        additional = result.get("additionalSkills", [])
        
        text = "### Suggested Skills\n\n"
        if top:
            text += f"**Top Skills:** {', '.join(top)}\n\n"
        if additional:
            text += f"**Additional Skills:** {', '.join(additional)}\n\n"
        
        text += result.get("message", "Review and add these skills to your profile.")
        return text
    
    def _format_qa_answer(self, result: Dict[str, Any]) -> str:
        """Format Q&A answer."""
        return f"**Answer:** {result.get('answer', 'No answer available')}"
    
    def _format_email(self, result: Dict[str, Any]) -> str:
        """Format drafted email."""
        subject = result.get("subject", "")
        body = result.get("body", "")
        
        return f"### Draft Email\n\n**Subject:** {subject}\n\n{body}"
    
    def _create_action_buttons(
        self,
        tool_names: List[str],
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Create action button definitions from tool names."""
        buttons = []
        for tool_name in tool_names[:3]:  # Max 3 buttons
            tool_info = self.tool_ranker.get_tool_display_info(tool_name)
            button = {
                "name": tool_name,
                "label": tool_info["label"],
                "icon": tool_info.get("icon", "🔧"),
                "tooltip": tool_info.get("tooltip", ""),
                "payload": params if tool_name == tool_names[0] and params else {}
            }
            buttons.append(button)
        return buttons
    
    def _get_tool_description(self, tool_name: Optional[str]) -> str:
        """Get human-readable description of a tool."""
        descriptions = {
            "profile_analyzer": "analyze your profile for completeness",
            "update_profile": "update your profile information",
            "infer_skills": "suggest skills based on your experience",
            "get_matches": "find matching job opportunities",
            "ask_jd_qa": "answer questions about a job posting",
            "draft_email": "draft a message to a recruiter"
        }
        return descriptions.get(tool_name, "assist you")


# Singleton instance
_agent_instance = None

def get_agent(model_name: str = "gpt-4o") -> MyCareerAgent:
    """Returns the singleton agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = MyCareerAgent(model_name=model_name)
    return _agent_instance

