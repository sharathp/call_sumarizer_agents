"""
Simplified Summarization Agent - Generates summaries using GPT-4/Claude.
"""

import json
import logging
import os
from typing import Optional, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from utils.validation import AgentState, CallSummary, SpeakerSegment

logger = logging.getLogger(__name__)


class SummarizationAgent:
    """Simplified agent for generating call summaries."""
    
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
            self.llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.3, api_key=api_key)
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")
    
    def process(self, state: AgentState) -> AgentState:
        """Generate summary using speaker segments when available."""
        if not state.transcript_text and not state.speakers:
            state.add_error("summarization", "No transcript or speaker data available")
            return state
        
        try:
            # Use speaker segments for enhanced analysis if available
            if state.speakers:
                summary = self._generate_summary_with_speakers(state.speakers, state.transcript_text)
                self.log_success(state, "Summary generation with speaker analysis completed")
            else:
                # Fallback to transcript-only analysis
                summary = self._generate_summary(state.transcript_text)
                self.log_success(state, "Summary generation with transcript fallback completed")
                
            state.summary = summary
            
        except Exception as e:
            return self.handle_error(state, e, "Summarization failed")
        
        return state
    
    def _generate_summary(self, transcript: str) -> CallSummary:
        """Generate summary using LLM."""
        system_prompt = """You are a call center analyst. Create a structured summary of this call transcript.

Respond in JSON format only. Do not use code blocks, backticks, or any markdown formatting. Your response must be pure JSON that starts with { and ends with }:
{
    "summary": "Brief executive summary (1-2 sentences)",
    "key_points": ["List of 3-5 key discussion points"],
    "sentiment": "positive|neutral|negative", 
    "outcome": "resolved|escalated|follow_up|unresolved"
}"""

        human_prompt = f"Analyze this call transcript:\n\n{transcript}"

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
            summary_dict = json.loads(content)
            return CallSummary(**summary_dict)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}, Content: {content[:200]}")
            # Return basic summary as fallback
            return CallSummary(
                summary="Call transcript processed.",
                key_points=["Call completed"],
                sentiment="neutral",
                outcome="unresolved"
            )
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            # Return basic summary as fallback
            return CallSummary(
                summary="Call transcript processed.",
                key_points=["Call completed"],
                sentiment="neutral",
                outcome="unresolved"
            )
    
    def _generate_summary_with_speakers(self, speakers: List[SpeakerSegment], transcript_fallback: str) -> CallSummary:
        """Generate summary using speaker segments for enhanced analysis."""
        # Format conversation with speaker labels
        conversation = self._format_speaker_conversation(speakers)
        
        # Analyze conversation flow
        conversation_flow = self._analyze_conversation_flow(speakers)
        
        system_prompt = """You are a call center analyst. Create a structured summary using speaker-identified dialogue to provide more accurate analysis of the conversation flow and outcomes.

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

        human_prompt = f"""Analyze this call using the speaker-identified dialogue below:

CONVERSATION FLOW:
{conversation}

CONVERSATION ANALYSIS:
{conversation_flow}

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
            summary_dict = json.loads(content)
            return CallSummary(**summary_dict)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in speaker summarization: {str(e)}, Content: {content[:200]}")
            # Fallback to transcript-only summarization
            logger.info("Falling back to transcript-only summarization")
            return self._generate_summary(transcript_fallback)
        except Exception as e:
            logger.error(f"Speaker-aware summarization error: {str(e)}")
            # Fallback to transcript-only summarization
            logger.info("Falling back to transcript-only summarization")
            return self._generate_summary(transcript_fallback)
    
    def _format_speaker_conversation(self, speakers: List[SpeakerSegment]) -> str:
        """Format speaker segments into a readable conversation."""
        conversation_lines = []
        for segment in speakers:
            timestamp = f"[{segment.start:.1f}s-{segment.end:.1f}s]"
            conversation_lines.append(f"{segment.speaker} {timestamp}: {segment.text}")
        return "\n".join(conversation_lines)
    
    def _analyze_conversation_flow(self, speakers: List[SpeakerSegment]) -> str:
        """Analyze conversation patterns and flow."""
        if not speakers:
            return "No speaker data available for flow analysis."
        
        # Count speakers
        speaker_counts = {}
        speaker_word_counts = {}
        for segment in speakers:
            speaker_counts[segment.speaker] = speaker_counts.get(segment.speaker, 0) + 1
            word_count = len(segment.text.split())
            speaker_word_counts[segment.speaker] = speaker_word_counts.get(segment.speaker, 0) + word_count
        
        # Calculate conversation metrics
        total_segments = len(speakers)
        total_duration = speakers[-1].end - speakers[0].start if speakers else 0
        
        # Identify likely roles
        if speaker_counts:
            likely_agent = max(speaker_counts.items(), key=lambda x: x[1])[0]
            other_speakers = [s for s in speaker_counts.keys() if s != likely_agent]
            likely_customer = other_speakers[0] if other_speakers else "Unknown"
        else:
            likely_agent = "Unknown"
            likely_customer = "Unknown"
        
        analysis = [
            f"Conversation Duration: {total_duration:.1f} seconds",
            f"Total Exchanges: {total_segments}",
            f"Speakers: {list(speaker_counts.keys())}",
            f"Likely Agent: {likely_agent} ({speaker_counts.get(likely_agent, 0)} segments, {speaker_word_counts.get(likely_agent, 0)} words)",
            f"Likely Customer: {likely_customer} ({speaker_counts.get(likely_customer, 0)} segments, {speaker_word_counts.get(likely_customer, 0)} words)"
        ]
        
        return "\n".join(analysis)