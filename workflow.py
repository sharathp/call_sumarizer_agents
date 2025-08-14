"""
Simplified LangGraph workflow for call processing.
"""

import logging
import os
import time
import uuid
from typing import Optional

from langgraph.graph import END, StateGraph

from agents import (
    QualityScoringAgent,
    SummarizationAgent,
    TranscriptionAgent,
)
from utils.validation import AgentState, ProcessingResult, CallInput, InputType


logger = logging.getLogger(__name__)
# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"

class CallCenterWorkflow:
    """Simplified workflow for call processing."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        deepgram_api_key: Optional[str] = None
    ):
        # Initialize transcription agent with Deepgram and OpenAI fallback
        self.transcription_agent = TranscriptionAgent(
            deepgram_api_key=deepgram_api_key,
            openai_api_key=openai_api_key
        )
        self.summarization_agent = SummarizationAgent(
            model_provider="openai",
            api_key=openai_api_key
        )
        self.quality_agent = QualityScoringAgent(
            model_provider="openai",
            api_key=openai_api_key
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build simplified LangGraph workflow."""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("transcription", self._run_transcription)
        graph.add_node("summarization", self._run_summarization)
        graph.add_node("quality_scoring", self._run_quality_scoring)
        
        # Simple linear flow with retry logic
        graph.set_entry_point("transcription")
        
        # retry twice, before going to summarization
        graph.add_conditional_edges(
            "transcription",
            self._route_after_transcription,
            {
                "retry": "transcription",
                "continue": "summarization",
                "end": END
            }
        )
        
        # retry twice, before going to quality scoring
        graph.add_conditional_edges(
            "summarization",
            self._route_after_summarization,
            {
                "retry": "summarization",
                "continue": "quality_scoring",
                "end": END
            }
        )
        
        # retry twice, and then end
        graph.add_conditional_edges(
            "quality_scoring",
            self._route_after_quality_scoring,
            {
                "retry": "quality_scoring",
                "end": END
            }
        )
        
        return graph.compile()
    
    def _run_transcription(self, state: AgentState) -> AgentState:
        """Run transcription with validation."""
        try:
            return self.transcription_agent.process(state)
        except Exception as e:
            state.add_error("transcription", str(e))
            return state
    
    def _run_summarization(self, state: AgentState) -> AgentState:
        """Run summarization."""
        try:
            return self.summarization_agent.process(state)
        except Exception as e:
            state.add_error("summarization", str(e))
            return state
    
    def _run_quality_scoring(self, state: AgentState) -> AgentState:
        """Run quality scoring."""
        try:
            return self.quality_agent.process(state)
        except Exception as e:
            state.add_error("quality_scoring", str(e))
            return state
    
    def _should_retry(self, state: AgentState, agent_name: str, max_retries: int = 2) -> bool:
        """Check if an agent should retry based on errors and per-agent retry count."""
        # Get current retry count BEFORE incrementing
        current_retries = state.retry_counts.get(agent_name, 0)
        
        # Only consider the LATEST error for this agent (not accumulated errors from previous retries)
        agent_errors = [e for e in state.errors if e["agent"] == agent_name]
        
        # Check if there's a NEW error (errors list grew since last check)
        # We need to detect if this is a fresh error, not from a previous attempt
        has_new_error = len(agent_errors) > current_retries
        
        logger.info(f"Checking retry for {agent_name}: {len(agent_errors)} total errors, {current_retries} retries so far, new error: {has_new_error}")
        
        if has_new_error and current_retries < max_retries:
            state.retry_counts[agent_name] = current_retries + 1
            latest_error = agent_errors[-1]['error'] if agent_errors else 'Unknown'
            logger.warning(f"Retrying {agent_name} (attempt {state.retry_counts[agent_name]}/{max_retries}) due to error: {latest_error[:100]}")
            return True
        elif has_new_error and current_retries >= max_retries:
            logger.error(f"Max retries ({max_retries}) exceeded for {agent_name}. Final error: {agent_errors[-1]['error'] if agent_errors else 'Unknown'}")
        
        return False
    
    def _route_after_transcription(self, state: AgentState) -> str:
        """Route after transcription with simple retry logic."""
        if self._should_retry(state, "transcription"):
            return "retry"
        
        # Continue if we have text (from transcription or original input)
        if state.transcript_text or state.input_data.input_type == InputType.TRANSCRIPT:
            return "continue"
        
        return "end"  # Can't proceed without text
    
    def _route_after_summarization(self, state: AgentState) -> str:
        """Route after summarization with simple retry logic."""
        if self._should_retry(state, "summarization"):
            return "retry"
        
        return "continue" if state.summary else "end"
    
    def _route_after_quality_scoring(self, state: AgentState) -> str:
        """Route after quality scoring with simple retry logic."""
        if self._should_retry(state, "quality_scoring"):
            return "retry"
        
        return "end"  # Always end after quality scoring (success or final failure)
    
    def process_call(self, input_data: CallInput) -> ProcessingResult:
        """Process a call through the simplified graph."""
        start_time = time.time()
        
        try:
            # Create state
            state = AgentState(
                call_id=str(uuid.uuid4())[:8],
                input_data=input_data
            )
            
            # Run graph
            result = self.graph.invoke(state)
            
            # LangGraph returns a dict, convert back to AgentState
            final_state = AgentState(**result)
            
            # Determine status
            if final_state.summary and final_state.quality_score and not final_state.errors:
                status = "success"
            elif final_state.summary or final_state.quality_score:
                status = "partial"
            else:
                status = "failed"
            
            # Create result
            return ProcessingResult(
                call_id=final_state.call_id,
                status=status,
                transcript_text=final_state.transcript_text,
                speakers=final_state.speakers,
                summary=final_state.summary,
                quality_score=final_state.quality_score,
                errors=final_state.errors,
                processing_time_seconds=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return ProcessingResult(
                call_id="error",
                status="failed",
                errors=[{"agent": "worflow", "error": str(e), "timestamp": ""}],
                processing_time_seconds=time.time() - start_time
            )