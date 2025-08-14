"""
Simplified Quality Scoring Agent - Evaluates call quality.
"""

import json
import logging
import os
from typing import Optional, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from utils.validation import AgentState, QualityScore, SpeakerSegment

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
        """Evaluate call quality using speaker segments when available."""
        if not state.transcript_text and not state.speakers:
            state.add_error("quality_scoring", "No transcript or speaker data available")
            return state
        
        try:
            # Use speaker segments for enhanced analysis if available
            if state.speakers:
                quality_score = self._evaluate_quality_with_speakers(state.speakers, state.transcript_text)
                logger.info(f"Quality evaluation with speaker analysis completed for call {state.call_id}")
            else:
                # Fallback to transcript-only analysis
                quality_score = self._evaluate_quality(state.transcript_text)
                logger.info(f"Quality evaluation with transcript fallback completed for call {state.call_id}")
                
            state.quality_score = quality_score
            
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

Respond in JSON format only. Do not use code blocks, backticks, or any markdown formatting. Your response must be pure JSON that starts with { and ends with }:
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
    
    def _evaluate_quality_with_speakers(self, speakers: List[SpeakerSegment], transcript_fallback: str) -> QualityScore:
        """Evaluate call quality using speaker segments for enhanced analysis."""
        # Format conversation with speaker labels
        conversation = self._format_speaker_conversation(speakers)
        
        # Identify agent utterances for focused evaluation
        agent_utterances = self._identify_agent_utterances(speakers)
        
        system_prompt = (
            "You are an expert call center quality analyst. Evaluate this call using speaker-identified dialogue "
            "to provide more accurate agent performance assessment."
        """

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
}""")

        human_prompt = f"""Evaluate this call using the speaker-identified dialogue below:

CONVERSATION FLOW:
{conversation}

AGENT UTTERANCES (for focused evaluation):
{agent_utterances}

Full transcript (if needed for context): {transcript_fallback[:500]}..."""

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
            logger.error("JSON parsing error in speaker evaluation: %s, Content: %s", str(e), content[:200])
            # Fallback to transcript-only evaluation
            logger.info("Falling back to transcript-only evaluation")
            return self._evaluate_quality(transcript_fallback)
        except Exception as e:
            logger.error("Speaker-aware quality evaluation error: %s", str(e))
            # Fallback to transcript-only evaluation
            logger.info("Falling back to transcript-only evaluation")
            return self._evaluate_quality(transcript_fallback)
    
    def _format_speaker_conversation(self, speakers: List[SpeakerSegment]) -> str:
        """Format speaker segments into a readable conversation."""
        conversation_lines = []
        for segment in speakers:
            timestamp = f"[{segment.start:.1f}s-{segment.end:.1f}s]"
            conversation_lines.append(f"{segment.speaker} {timestamp}: {segment.text}")
        return "\n".join(conversation_lines)
    
    def _identify_agent_utterances(self, speakers: List[SpeakerSegment]) -> str:
        """Extract and format agent utterances for focused evaluation."""
        # Simple heuristic: assume Speaker 0 is often the agent (can be improved with role detection)
        agent_utterances = []
        
        # Count speakers to make intelligent guess about agent
        speaker_counts = {}
        for segment in speakers:
            speaker_counts[segment.speaker] = speaker_counts.get(segment.speaker, 0) + 1
        
        # Assume agent is the speaker who talks most (typical in call centers)
        if speaker_counts:
            likely_agent = max(speaker_counts.items(), key=lambda x: x[1])[0]
            
            for segment in speakers:
                if segment.speaker == likely_agent:
                    timestamp = f"[{segment.start:.1f}s]"
                    agent_utterances.append(f"{timestamp} {segment.text}")
        
        return "\n".join(agent_utterances) if agent_utterances else "Agent utterances could not be identified."