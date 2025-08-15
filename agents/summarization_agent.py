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
from utils.helpers import (
    parse_llm_json_response,
    format_speaker_conversation,
    calculate_speaker_statistics,
    identify_likely_agent_from_stats
)
from utils.validation import AgentState, CallSummary, SpeakerSegment


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
        """Generate summary using speaker segments when available."""
        if not state.transcript_text and not state.speakers:
            state.add_error(self.agent_name, "No transcript or speaker data available")
            return state
        
        try:
            # Use speaker segments for enhanced analysis if available
            if state.speakers:
                summary = self._generate_summary_with_speakers(
                    state.speakers,
                    state.transcript_text
                )
                self.log_success(state, "Summary generation with speaker analysis completed")
            else:
                # Fallback to transcript-only analysis
                summary = self._generate_summary(state.transcript_text)
                self.log_success(state, "Summary generation with transcript fallback completed")
                
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
    
    def _generate_summary_with_speakers(
        self,
        speakers: List[SpeakerSegment],
        transcript_fallback: str
    ) -> CallSummary:
        """Generate enhanced summary using speaker segments."""
        # Use helper functions for formatting and analysis
        conversation = format_speaker_conversation(speakers)
        stats = calculate_speaker_statistics(speakers)
        conversation_flow = self._format_conversation_analysis(stats)
        
        system_prompt = self._get_speaker_aware_system_prompt()
        human_prompt = self._build_speaker_aware_prompt(
            conversation,
            conversation_flow,
            transcript_fallback
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            summary_dict = parse_llm_json_response(content)
            return CallSummary(**summary_dict)
                
        except (LLMResponseError, Exception) as e:
            self.logger.warning(
                f"Speaker-aware summarization failed: {e}, falling back to transcript-only"
            )
            return self._generate_summary(transcript_fallback)
    
    def _format_conversation_analysis(self, stats: dict) -> str:
        """Format conversation statistics for analysis."""
        if not stats["speaker_stats"]:
            return "No speaker data available for flow analysis."
        
        # Identify likely roles using statistics
        likely_agent = identify_likely_agent_from_stats(stats["speaker_stats"])
        
        analysis = [
            f"Conversation Duration: {stats['total_duration']:.1f} seconds",
            f"Total Speakers: {stats['total_speakers']}",
            f"Speakers: {list(stats['speaker_stats'].keys())}",
        ]
        
        # Add speaker details
        for speaker, data in stats["speaker_stats"].items():
            role = "(Likely Agent)" if speaker == likely_agent else ""
            analysis.append(
                f"{speaker} {role}: {data['segment_count']} segments, "
                f"{data['word_count']} words, {data['duration_percentage']:.1f}% talk time"
            )
        
        return "\n".join(analysis)
    
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
    def _get_speaker_aware_system_prompt() -> str:
        """Get the enhanced system prompt for speaker-aware summarization."""
        return """You are a call center analyst. Create a structured summary using speaker-identified dialogue to provide more accurate analysis of the conversation flow and outcomes.

ANALYSIS APPROACH:
- Analyze the dialogue between different speakers
- Identify customer concerns and agent responses
- Track conversation progression and resolution steps
- Focus on interaction quality and customer journey

Respond in JSON format only. Do not use code blocks, backticks, or any markdown formatting. Your response must be pure JSON that starts with { and ends with }:
{
    "summary": "Brief executive summary capturing the conversation flow and outcome (1-2 sentences)",
    "key_points": ["List of 3-5 key discussion points including speaker interactions"],
    "sentiment": "positive|neutral|negative", 
    "outcome": "resolved|escalated|follow_up|unresolved"
}"""
    
    @staticmethod
    def _build_speaker_aware_prompt(
        conversation: str,
        conversation_flow: str,
        transcript_fallback: str
    ) -> str:
        """Build the human prompt for speaker-aware analysis."""
        return f"""Analyze this call using the speaker-identified dialogue below:

CONVERSATION FLOW:
{conversation}

CONVERSATION ANALYSIS:
{conversation_flow}

Full transcript (if needed for context): {transcript_fallback[:500]}..."""
    
    @staticmethod
    def _get_fallback_summary() -> dict:
        """Get a fallback summary structure."""
        return {
            "summary": "Unable to process transcript.",
            "key_points": ["Failed to process transcript."],
            "sentiment": "unknown",
            "outcome": "unknown"
        }