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
from utils.helpers import parse_llm_json_response
from utils.validation import AgentState, QualityScore


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
                temperature=0,  # Lower temperature for more consistent scoring
                api_key=api_key
            )
        else:
            raise QualityScoringError(f"Unsupported model provider: {self.model_provider}")
    
    def process(self, state: AgentState) -> AgentState:
        """Evaluate call quality from transcript text."""
        if not state.transcript_text:
            state.add_error(self.agent_name, "No transcript text available")
            return state
        
        try:
            # Evaluate quality from transcript
            quality_score = self._evaluate_quality(state.transcript_text)
            self.log_success(state, "Quality evaluation completed")
                
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

Respond in JSON format only. Do not use code blocks, backticks, or any markdown formatting. Your response must be pure JSON that starts with { and ends with }.

IMPORTANT: The "feedback" field must be a single string (not an object or dictionary), providing a brief summary of strengths and areas for improvement.

Example format:
{
    "tone_score": 8.0,
    "professionalism_score": 7.5,
    "resolution_score": 9.0,
    "feedback": "Agent demonstrated excellent empathy and patience when handling customer frustration. Successfully resolved the password reset issue. Could improve by offering additional self-service options for future reference."
}"""
    
    
    
    @staticmethod
    def _get_fallback_score() -> dict:
        """Get a fallback quality score structure."""
        return {
            "tone_score": 0.0,
            "professionalism_score": 0.0,
            "resolution_score": 0.0,
            "feedback": "Unable to evaluate quality due to processing error."
        }