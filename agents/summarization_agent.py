"""
Refactored Summarization Agent with improved structure and utilities.
"""

from typing import Optional, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.base_agent import BaseAgent
from config.settings import config, ModelProvider
from utils.constants import DEFAULT_LLM_MODEL, DEFAULT_LLM_TEMPERATURE
from utils.exceptions import SummarizationError, LLMResponseError
from utils.helpers import parse_llm_json_response
from utils.validation import AgentState, CallSummary


class SummarizationAgent(BaseAgent):
    """Refactored agent for generating call summaries."""
    
    def __init__(
        self,
        model_provider: Optional[ModelProvider] = None,
        api_key: Optional[str] = None
    ):
        super().__init__("summarization")
        
        # Use config defaults if not specified
        self.model_provider = model_provider or config.model.llm_provider
        api_key = api_key or config.api.openai_api_key
        
        if self.model_provider == ModelProvider.OPENAI:
            if not api_key:
                raise SummarizationError("OpenAI API key is required.")
            self.llm = ChatOpenAI(
                model=config.model.llm_model or DEFAULT_LLM_MODEL,
                temperature=config.model.llm_temperature or DEFAULT_LLM_TEMPERATURE,
                api_key=api_key
            )
        else:
            raise SummarizationError(f"Unsupported model provider: {self.model_provider}")
    
    def process(self, state: AgentState) -> AgentState:
        """Generate summary from transcript text."""
        if not state.transcript_text:
            state.add_error(self.agent_name, "No transcript text available")
            return state
        
        try:
            # Generate summary from transcript
            summary = self._generate_summary(state.transcript_text)
            self.log_success(state, "Summary generation completed")
                
            state.summary = summary
            return state
            
        except Exception as e:
            return self.handle_error(state, e, "Summarization failed")
    
    def _generate_summary(self, transcript: str) -> CallSummary:
        """Generate summary using LLM."""
        system_prompt = self._get_system_prompt()
        human_prompt = f"Analyze this call transcript:\n\n{transcript}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Use helper function for JSON parsing with fallback
            fallback_summary = self._get_fallback_summary()
            
            try:
                summary_dict = parse_llm_json_response(content)
            except Exception as parse_error:
                self.logger.warning(f"Using fallback summary due to: {parse_error}")
                summary_dict = fallback_summary
            
            return CallSummary(**summary_dict)
                
        except Exception as e:
            raise LLMResponseError(f"Failed to generate summary: {str(e)}")
    
    
    
    @staticmethod
    def _get_system_prompt() -> str:
        """Get the basic system prompt for summarization."""
        return """You are a call center analyst. Create a structured summary of this call transcript.

Respond in JSON format only. Do not use code blocks, backticks, or any markdown formatting. Your response must be pure JSON that starts with { and ends with }:
{
    "summary": "Brief executive summary (1-2 sentences)",
    "key_points": ["List of 3-5 key discussion points"],
    "sentiment": "positive|neutral|negative", 
    "outcome": "resolved|escalated|follow_up|unresolved"
}"""
    
    
    
    @staticmethod
    def _get_fallback_summary() -> dict:
        """Get a fallback summary structure."""
        return {
            "summary": "Unable to process transcript.",
            "key_points": ["Failed to process transcript."],
            "sentiment": "unknown",
            "outcome": "unknown"
        }