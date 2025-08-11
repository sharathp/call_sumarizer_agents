"""
Simplified LangGraph workflow for call processing.
"""

import logging
import time
from typing import Optional

from langgraph.graph import END, StateGraph

from agents import (
    QualityScoringAgent,
    SummarizationAgent,
    TranscriptionAgent,
)
from utils.validation import AgentState, ProcessingResult, CallInput, InputType
import uuid

logger = logging.getLogger(__name__)


class CallCenterWorkflow:
    """Simplified workflow for call processing."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None
    ):
        # Initialize all agents with OpenAI
        self.transcription_agent = TranscriptionAgent(api_key=openai_api_key)
        self.summarization_agent = SummarizationAgent(
            model_provider="openai",
            api_key=openai_api_key
        )
        self.quality_agent = QualityScoringAgent(
            model_provider="openai",
            api_key=openai_api_key
        )
        
        # Build the workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build simplified LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("transcription", self._run_transcription)
        workflow.add_node("summarization", self._run_summarization)
        workflow.add_node("quality_scoring", self._run_quality_scoring)
        
        # Simple linear flow with retry logic
        workflow.set_entry_point("transcription")
        
        workflow.add_conditional_edges(
            "transcription",
            self._route_after_transcription,
            {
                "retry": "transcription",
                "continue": "summarization",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "summarization",
            self._route_after_summarization,
            {
                "retry": "summarization",
                "continue": "quality_scoring",
                "end": END
            }
        )
        
        workflow.add_edge("quality_scoring", END)
        
        return workflow.compile()
    
    def _run_transcription(self, state: AgentState) -> AgentState:
        """Run transcription with validation."""
        try:
            return self.transcription_agent.process(state)
        except Exception as e:
            state.add_error("transcription", str(e))
            return state
    
    def _run_summarization(self, state: AgentState) -> AgentState:
        """Run summarization."""
        return self.summarization_agent.process(state)
    
    def _run_quality_scoring(self, state: AgentState) -> AgentState:
        """Run quality scoring."""
        return self.quality_agent.process(state)
    
    def _route_after_transcription(self, state: AgentState) -> str:
        """Route after transcription with simple retry logic."""
        transcription_errors = [e for e in state.errors if e["agent"] == "transcription"]
        
        if transcription_errors and state.retry_count < 2:
            state.retry_count += 1
            return "retry"
        
        # Continue if we have text (from transcription or original input)
        if state.transcript_text or state.input_data.input_type == InputType.TRANSCRIPT:
            return "continue"
        
        return "end"  # Can't proceed without text
    
    def _route_after_summarization(self, state: AgentState) -> str:
        """Route after summarization with simple retry logic."""
        summarization_errors = [e for e in state.errors if e["agent"] == "summarization"]
        
        if summarization_errors and state.retry_count < 2:
            state.retry_count += 1
            return "retry"
        
        return "continue" if state.summary else "end"
    
    def process_call(self, input_data: CallInput) -> ProcessingResult:
        """Process a call through the simplified workflow."""
        start_time = time.time()
        
        try:
            # Create state
            state = AgentState(
                call_id=str(uuid.uuid4())[:8],
                input_data=input_data
            )
            
            # Run workflow
            result = self.workflow.invoke(state)
            
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
                summary=final_state.summary,
                quality_score=final_state.quality_score,
                errors=final_state.errors,
                processing_time_seconds=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            return ProcessingResult(
                call_id="error",
                status="failed",
                errors=[{"agent": "workflow", "error": str(e), "timestamp": ""}],
                processing_time_seconds=time.time() - start_time
            )