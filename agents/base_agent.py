"""
Base agent class with common functionality for all agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from utils.validation import AgentState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all processing agents."""
    
    def __init__(self, agent_name: str):
        """Initialize base agent with common properties."""
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
    
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """Process the state - must be implemented by subclasses."""
        pass
    
    def handle_error(self, state: AgentState, error: Exception, context: str = "") -> AgentState:
        """Standardized error handling across all agents."""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(f"{self.agent_name} error: {error_msg}")
        state.add_error(self.agent_name, error_msg)
        return state
    
    def log_success(self, state: AgentState, message: str) -> None:
        """Log successful operation."""
        self.logger.info(f"{message} for call {state.call_id}")