"""
Refactored LangGraph workflow with simplified routing.
"""

import logging
import os
import time
import uuid
from typing import Optional, Dict, Literal

from langgraph.graph import END, StateGraph

from agents import TranscriptionAgent
from agents.summarization_agent_refactored import SummarizationAgent
from agents.quality_score_agent_refactored import QualityScoringAgent
from config.settings import config
from utils.constants import DEFAULT_MAX_RETRIES, STATUS_SUCCESS, STATUS_PARTIAL, STATUS_FAILED
from utils.exceptions import WorkflowError
from utils.validation import AgentState, ProcessingResult, CallInput, InputType

logger = logging.getLogger(__name__)

# Enable LangSmith tracing if configured
if config.enable_langsmith:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"


class CallCenterWorkflow:
    """Refactored workflow for call processing with simplified routing."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        deepgram_api_key: Optional[str] = None
    ):
        # Use config if keys not provided
        openai_api_key = openai_api_key or config.api.openai_api_key
        deepgram_api_key = deepgram_api_key or config.api.deepgram_api_key
        
        # Initialize agents
        self.transcription_agent = TranscriptionAgent(
            deepgram_api_key=deepgram_api_key,
            openai_api_key=openai_api_key
        )
        self.summarization_agent = SummarizationAgent(
            model_provider=config.model.llm_provider,
            api_key=openai_api_key
        )
        self.quality_agent = QualityScoringAgent(
            model_provider=config.model.llm_provider,
            api_key=openai_api_key
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build simplified LangGraph workflow."""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("transcription", self._run_agent("transcription"))
        graph.add_node("summarization", self._run_agent("summarization"))
        graph.add_node("quality_scoring", self._run_agent("quality_scoring"))
        
        # Set entry point
        graph.set_entry_point("transcription")
        
        # Add conditional routing for each agent
        for agent_name, next_agent in [
            ("transcription", "summarization"),
            ("summarization", "quality_scoring"),
            ("quality_scoring", None)
        ]:
            graph.add_conditional_edges(
                agent_name,
                lambda state, agent=agent_name, next_node=next_agent: self._route_agent(
                    state, agent, next_node
                ),
                {
                    "retry": agent_name,
                    "continue": next_agent if next_agent else END,
                    "end": END
                }
            )
        
        return graph.compile()
    
    def _run_agent(self, agent_name: str):
        """Create a node function for running an agent."""
        agent_map = {
            "transcription": self.transcription_agent,
            "summarization": self.summarization_agent,
            "quality_scoring": self.quality_agent
        }
        
        def run_node(state: AgentState) -> AgentState:
            """Execute the agent and handle errors."""
            try:
                agent = agent_map[agent_name]
                return agent.process(state)
            except Exception as e:
                logger.error(f"{agent_name} failed: {str(e)}")
                state.add_error(agent_name, str(e))
                return state
        
        return run_node
    
    def _route_agent(
        self,
        state: AgentState,
        agent_name: str,
        next_agent: Optional[str]
    ) -> Literal["retry", "continue", "end"]:
        """
        Unified routing logic for all agents.
        
        Args:
            state: Current agent state
            agent_name: Name of the current agent
            next_agent: Name of the next agent in the flow
            
        Returns:
            Routing decision: "retry", "continue", or "end"
        """
        # Check if retry is needed
        if self._should_retry(state, agent_name):
            return "retry"
        
        # Check agent-specific continuation conditions
        can_continue = self._check_continuation(state, agent_name)
        
        if can_continue and next_agent:
            return "continue"
        
        return "end"
    
    def _should_retry(
        self,
        state: AgentState,
        agent_name: str,
        max_retries: Optional[int] = None
    ) -> bool:
        """
        Check if an agent should retry based on errors and retry count.
        
        Args:
            state: Current agent state
            agent_name: Name of the agent
            max_retries: Maximum retry attempts (uses config default if not specified)
            
        Returns:
            True if retry should be attempted
        """
        max_retries = max_retries or config.model.max_retries or DEFAULT_MAX_RETRIES
        
        # Get errors for this agent
        agent_errors = [e for e in state.errors if e["agent"] == agent_name]
        current_retries = state.retry_counts.get(agent_name, 0)
        
        logger.debug(
            f"Retry check for {agent_name}: {len(agent_errors)} errors, "
            f"{current_retries}/{max_retries} retries"
        )
        
        if agent_errors and current_retries < max_retries:
            state.retry_counts[agent_name] = current_retries + 1
            logger.warning(
                f"Retrying {agent_name} (attempt {state.retry_counts[agent_name]}/{max_retries})"
            )
            return True
        
        if agent_errors and current_retries >= max_retries:
            logger.error(f"Max retries exceeded for {agent_name}")
        
        return False
    
    def _check_continuation(self, state: AgentState, agent_name: str) -> bool:
        """
        Check if workflow can continue after the given agent.
        
        Args:
            state: Current agent state
            agent_name: Name of the current agent
            
        Returns:
            True if workflow can continue
        """
        if agent_name == "transcription":
            # Continue if we have text from transcription or original input
            return bool(
                state.transcript_text or 
                state.input_data.input_type == InputType.TRANSCRIPT
            )
        
        elif agent_name == "summarization":
            # Continue if summary was generated
            return bool(state.summary)
        
        elif agent_name == "quality_scoring":
            # Quality scoring is the last step
            return False
        
        return False
    
    def process_call(self, input_data: CallInput) -> ProcessingResult:
        """Process a call through the workflow."""
        start_time = time.time()
        
        try:
            # Create initial state
            state = AgentState(
                call_id=str(uuid.uuid4())[:8],
                input_data=input_data
            )
            
            # Run the workflow graph
            result = self.graph.invoke(state)
            
            # Convert result back to AgentState
            final_state = AgentState(**result)
            
            # Determine processing status
            status = self._determine_status(final_state)
            
            # Create and return result
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
                status=STATUS_FAILED,
                errors=[{
                    "agent": "workflow",
                    "error": str(e),
                    "timestamp": ""
                }],
                processing_time_seconds=time.time() - start_time
            )
    
    def _determine_status(self, state: AgentState) -> str:
        """
        Determine the overall processing status.
        
        Args:
            state: Final agent state
            
        Returns:
            Status string: "success", "partial", or "failed"
        """
        has_summary = bool(state.summary)
        has_quality = bool(state.quality_score)
        has_errors = bool(state.errors)
        
        if has_summary and has_quality and not has_errors:
            return STATUS_SUCCESS
        elif has_summary or has_quality:
            return STATUS_PARTIAL
        else:
            return STATUS_FAILED