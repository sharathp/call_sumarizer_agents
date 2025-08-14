"""
Refactored Quality Scoring Agent with improved structure.
"""

from typing import Optional, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.base_agent import BaseAgent
from config.settings import config, ModelProvider
from utils.constants import DEFAULT_LLM_MODEL, DEFAULT_LLM_TEMPERATURE
from utils.exceptions import QualityScoringError, LLMResponseError
from utils.helpers import (
    parse_llm_json_response,
    format_speaker_conversation,
    identify_likely_agent
)
from utils.validation import AgentState, QualityScore, SpeakerSegment


class QualityScoringAgent(BaseAgent):
    """Refactored agent for evaluating call quality."""
    
    def __init__(
        self,
        model_provider: Optional[ModelProvider] = None,
        api_key: Optional[str] = None
    ):
        super().__init__("quality_scoring")
        
        # Use config defaults if not specified
        self.model_provider = model_provider or config.model.llm_provider
        api_key = api_key or config.api.openai_api_key
        
        if self.model_provider == ModelProvider.OPENAI:
            if not api_key:
                raise QualityScoringError("OpenAI API key is required.")
            self.llm = ChatOpenAI(
                model=config.model.llm_model or DEFAULT_LLM_MODEL,
                temperature=0.2,  # Lower temperature for more consistent scoring
                api_key=api_key
            )
        else:
            raise QualityScoringError(f"Unsupported model provider: {self.model_provider}")
    
    def process(self, state: AgentState) -> AgentState:
        """Evaluate call quality using speaker segments when available."""
        if not state.transcript_text and not state.speakers:
            state.add_error(self.agent_name, "No transcript or speaker data available")
            return state
        
        try:
            # Use speaker segments for enhanced analysis if available
            if state.speakers:
                quality_score = self._evaluate_quality_with_speakers(
                    state.speakers,
                    state.transcript_text
                )
                self.log_success(state, "Quality evaluation with speaker analysis completed")
            else:
                # Fallback to transcript-only analysis
                quality_score = self._evaluate_quality(state.transcript_text)
                self.log_success(state, "Quality evaluation with transcript fallback completed")
                
            state.quality_score = quality_score
            return state
            
        except Exception as e:
            return self.handle_error(state, e, "Quality scoring failed")
    
    def _evaluate_quality(self, transcript: str) -> QualityScore:
        """Evaluate call quality using LLM with structured rubric."""
        system_prompt = self._get_basic_rubric()
        human_prompt = f"Evaluate this call transcript using the structured rubric:\n\n{transcript}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Use helper function for JSON parsing with fallback
            fallback_score = self._get_fallback_score()
            
            try:
                quality_dict = parse_llm_json_response(content)
            except Exception as parse_error:
                self.logger.warning(f"Using fallback score due to: {parse_error}")
                quality_dict = fallback_score
            
            return QualityScore(**quality_dict)
                
        except Exception as e:
            raise LLMResponseError(f"Failed to evaluate quality: {str(e)}")
    
    def _evaluate_quality_with_speakers(
        self,
        speakers: List[SpeakerSegment],
        transcript_fallback: str
    ) -> QualityScore:
        """Evaluate quality using speaker segments for enhanced analysis."""
        # Format conversation and identify agent
        conversation = format_speaker_conversation(speakers)
        agent_utterances = self._extract_agent_utterances(speakers)
        
        system_prompt = self._get_speaker_aware_rubric()
        human_prompt = self._build_speaker_aware_prompt(
            conversation,
            agent_utterances,
            transcript_fallback
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            quality_dict = parse_llm_json_response(content)
            return QualityScore(**quality_dict)
                
        except (LLMResponseError, Exception) as e:
            self.logger.warning(
                f"Speaker-aware evaluation failed: {e}, falling back to transcript-only"
            )
            return self._evaluate_quality(transcript_fallback)
    
    def _extract_agent_utterances(self, speakers: List[SpeakerSegment]) -> str:
        """Extract and format agent utterances for focused evaluation."""
        if not speakers:
            return "Agent utterances could not be identified."
        
        # Use helper to identify likely agent
        speaker_list = [s for s in speakers]
        likely_agent = identify_likely_agent(speaker_list)
        
        if not likely_agent:
            return "Agent utterances could not be identified."
        
        agent_utterances = []
        for segment in speakers:
            if segment.speaker == likely_agent:
                timestamp = f"[{segment.start:.1f}s]"
                agent_utterances.append(f"{timestamp} {segment.text}")
        
        return "\n".join(agent_utterances) if agent_utterances else "No agent utterances found."
    
    @staticmethod
    def _get_basic_rubric() -> str:
        """Get the basic quality evaluation rubric."""
        return """You are an expert call center quality analyst. Evaluate this call transcript using the following structured rubric.

SCORING RUBRIC (1-10 scale for each dimension):

1. TONE SCORE (1-10):
   - 9-10: Exceptionally warm, friendly, patient, and engaging throughout
   - 7-8: Consistently positive and approachable with good clarity
   - 5-6: Generally appropriate but may lack warmth or have occasional lapses
   - 3-4: Often cold, impatient, or unclear in communication
   - 1-2: Hostile, dismissive, or extremely unclear

   Evaluate: Friendliness, patience, clarity of speech, emotional appropriateness

2. PROFESSIONALISM SCORE (1-10):
   - 9-10: Expert knowledge, flawless protocol adherence, exceptional language use
   - 7-8: Strong competence, follows procedures well, professional language
   - 5-6: Adequate knowledge, mostly follows protocols, acceptable language
   - 3-4: Limited knowledge, frequent protocol violations, unprofessional moments
   - 1-2: Severe lack of knowledge, major protocol breaches, highly unprofessional

   Evaluate: Product/service knowledge, adherence to company protocols, language appropriateness, competence

3. RESOLUTION SCORE (1-10):
   - 9-10: Completely resolved issue, exceeded expectations, proactive solutions
   - 7-8: Successfully resolved main issue, customer satisfied
   - 5-6: Partial resolution achieved or escalated appropriately
   - 3-4: Minimal progress on issue, unclear next steps
   - 1-2: Failed to address issue, left customer worse off

   Evaluate: Problem-solving effectiveness, issue closure, customer satisfaction indicators

Respond in JSON format only. Do not use code blocks, backticks, or any markdown formatting. Your response must be pure JSON that starts with { and ends with }:
{
    "tone_score": 8.0,
    "professionalism_score": 7.5,
    "resolution_score": 9.0,
    "feedback": "Brief summary highlighting specific strengths and areas for improvement based on the rubric"
}"""
    
    @staticmethod
    def _get_speaker_aware_rubric() -> str:
        """Get the enhanced speaker-aware quality evaluation rubric."""
        return """You are an expert call center quality analyst. Evaluate this call using speaker-identified dialogue to provide more accurate agent performance assessment.

ENHANCED SCORING RUBRIC (1-10 scale for each dimension):

Focus your evaluation on the AGENT'S performance by analyzing their specific utterances and interactions.

1. TONE SCORE (1-10) - Agent Communication Quality:
   - 9-10: Agent consistently warm, friendly, patient, and engaging
   - 7-8: Agent mostly positive and approachable with good clarity
   - 5-6: Agent generally appropriate but may lack warmth occasionally
   - 3-4: Agent often cold, impatient, or unclear
   - 1-2: Agent hostile, dismissive, or extremely unclear

   Evaluate: Agent's friendliness, patience, active listening, emotional intelligence

2. PROFESSIONALISM SCORE (1-10) - Agent Protocol & Knowledge:
   - 9-10: Expert knowledge, perfect protocol adherence, exceptional language
   - 7-8: Strong competence, follows procedures well, professional language
   - 5-6: Adequate knowledge, mostly follows protocols, acceptable language
   - 3-4: Limited knowledge, frequent protocol violations, unprofessional moments
   - 1-2: Severe knowledge gaps, major protocol breaches, highly unprofessional

   Evaluate: Product knowledge, company protocols, greeting/closing procedures, language appropriateness

3. RESOLUTION SCORE (1-10) - Problem-Solving Effectiveness:
   - 9-10: Completely resolved issue, exceeded expectations, proactive solutions
   - 7-8: Successfully resolved main issue, customer clearly satisfied
   - 5-6: Partial resolution achieved or appropriately escalated with clear next steps
   - 3-4: Minimal progress, unclear resolution path, customer still frustrated
   - 1-2: Failed to address issue, customer left worse off

   Evaluate: Issue identification, solution quality, follow-up, customer satisfaction trajectory

CONVERSATION ANALYSIS:
- Analyze the dialogue flow between speakers
- Focus on agent responses and interaction patterns
- Consider customer sentiment changes throughout the call
- Evaluate agent's ability to handle customer concerns

Respond in JSON format only. Do not use code blocks, backticks, or any markdown formatting. Your response must be pure JSON that starts with { and ends with }:
{
    "tone_score": 8.0,
    "professionalism_score": 7.5,
    "resolution_score": 9.0,
    "feedback": "Detailed feedback highlighting specific agent strengths and areas for improvement based on the speaker-aware analysis"
}"""
    
    @staticmethod
    def _build_speaker_aware_prompt(
        conversation: str,
        agent_utterances: str,
        transcript_fallback: str
    ) -> str:
        """Build the human prompt for speaker-aware quality evaluation."""
        return f"""Evaluate this call using the speaker-identified dialogue below:

CONVERSATION FLOW:
{conversation}

AGENT UTTERANCES (for focused evaluation):
{agent_utterances}

Full transcript (if needed for context): {transcript_fallback[:500]}..."""
    
    @staticmethod
    def _get_fallback_score() -> dict:
        """Get a fallback quality score structure."""
        return {
            "tone_score": 5.0,
            "professionalism_score": 5.0,
            "resolution_score": 5.0,
            "feedback": "Unable to evaluate quality due to processing error."
        }