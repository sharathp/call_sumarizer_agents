"""
Simplified Summarization Agent - Generates summaries using GPT-4/Claude.
"""

import json
import logging
import os
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from utils.validation import AgentState, CallSummary

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
        """Generate summary from transcript."""
        if not state.transcript_text:
            state.add_error("summarization", "No transcript available")
            return state
        
        try:
            summary = self._generate_summary(state.transcript_text)
            state.summary = summary
            logger.info(f"Summary generated for call {state.call_id}")
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            state.add_error("summarization", str(e))
        
        return state
    
    def _generate_summary(self, transcript: str) -> CallSummary:
        """Generate summary using LLM."""
        system_prompt = """You are a call center analyst. Create a structured summary of this call transcript.

Respond in JSON format:
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