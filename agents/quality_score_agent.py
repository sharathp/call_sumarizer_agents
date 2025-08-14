"""
Simplified Quality Scoring Agent - Evaluates call quality.
"""

import json
import logging
import os
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from utils.validation import AgentState, QualityScore

logger = logging.getLogger(__name__)


class QualityScoringAgent:
    """Simplified agent for evaluating call quality."""
    
    def __init__(
        self,
        model_provider: str = "openai",
        api_key: Optional[str] = None
    ):
        self.model_provider = model_provider
        
        if model_provider == "openai":
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key is required.")
            self.llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.2, api_key=api_key)
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")
    
    def process(self, state: AgentState) -> AgentState:
        """Evaluate call quality."""
        if not state.transcript_text:
            state.add_error("quality_scoring", "No transcript available")
            return state
        
        try:
            quality_score = self._evaluate_quality(state.transcript_text)
            state.quality_score = quality_score
            logger.info(f"Quality evaluation completed for call {state.call_id}")
            
        except Exception as e:
            logger.error(f"Quality scoring failed: {str(e)}")
            state.add_error("quality_scoring", str(e))
        
        return state
    
    def _evaluate_quality(self, transcript: str) -> QualityScore:
        """Evaluate call quality using LLM with structured rubric."""
        system_prompt = (
            "You are an expert call center quality analyst. Evaluate this call transcript "
            "using the following structured rubric."
"""

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

Respond in JSON format:
{
    "tone_score": 8.0,
    "professionalism_score": 7.5,
    "resolution_score": 9.0,
    "feedback": "Brief summary highlighting specific strengths and areas for improvement based on the rubric"
}""")

        human_prompt = f"Evaluate this call transcript using the structured rubric:\n\n{transcript}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)

            # Clean content and try to extract JSON
            content = content.strip()

            # Try to find JSON in the response
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()

            # Parse JSON response
            quality_dict = json.loads(content)
            return QualityScore(**quality_dict)

        except json.JSONDecodeError as e:
            logger.error("JSON parsing error: %s, Content: %s", str(e), content[:200])
            # Return default scores as fallback
            return QualityScore(
                tone_score=5.0,
                professionalism_score=5.0,
                resolution_score=5.0,
                feedback="Unable to evaluate quality due to processing error."
            )
        except Exception as e:
            logger.error("Quality evaluation error: %s", str(e))
            # Return default scores as fallback
            return QualityScore(
                tone_score=5.0,
                professionalism_score=5.0,
                resolution_score=5.0,
                feedback="Unable to evaluate quality due to processing error."
            )