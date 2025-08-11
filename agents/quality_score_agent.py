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
        """Evaluate call quality using LLM."""
        system_prompt = """You are a call center quality analyst. Evaluate this call transcript on quality dimensions.

Rate each dimension 1-10 and provide feedback. Respond in JSON format:
{
    "overall_score": 7.5,
    "empathy_score": 8.0,
    "resolution_score": 7.0,
    "feedback": "Brief summary of strengths and areas for improvement"
}"""

        human_prompt = f"Evaluate this call transcript:\n\n{transcript}"

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
            logger.error(f"JSON parsing error: {str(e)}, Content: {content[:200]}")
            # Return default scores as fallback
            return QualityScore(
                overall_score=5.0,
                empathy_score=5.0,
                resolution_score=5.0,
                feedback="Unable to evaluate quality due to processing error."
            )
        except Exception as e:
            logger.error(f"Quality evaluation error: {str(e)}")
            # Return default scores as fallback
            return QualityScore(
                overall_score=5.0,
                empathy_score=5.0,
                resolution_score=5.0,
                feedback="Unable to evaluate quality due to processing error."
            )