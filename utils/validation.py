"""
Simplified Pydantic models for data validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class InputType(str, Enum):
    """Supported input types for call data."""
    AUDIO = "audio"
    TRANSCRIPT = "transcript"


class CallInput(BaseModel):
    """Input model for call data validation."""
    
    input_type: InputType
    content: Any  # bytes for audio, str for text transcripts
    file_name: Optional[str] = None


class CallSummary(BaseModel):
    """Simplified summary of a call."""
    
    summary: str
    key_points: List[str]
    sentiment: Literal["positive", "neutral", "negative"]
    outcome: Literal["resolved", "escalated", "follow_up", "unresolved"]




class QualityScore(BaseModel):
    """Simplified quality assessment."""
    
    tone_score: float = Field(ge=1.0, le=10.0)
    professionalism_score: float = Field(ge=1.0, le=10.0)
    resolution_score: float = Field(ge=1.0, le=10.0)
    feedback: str


class AgentState(BaseModel):
    """Shared state for LangGraph workflow."""
    
    call_id: str
    input_data: CallInput
    transcript_text: Optional[str] = None
    summary: Optional[CallSummary] = None
    quality_score: Optional[QualityScore] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    
    def add_error(self, agent: str, error: str) -> None:
        """Add an error to the state."""
        self.errors.append({
            "agent": agent,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })


class ProcessingResult(BaseModel):
    """Final result of call processing."""
    
    call_id: str
    status: Literal["success", "partial", "failed"]
    transcript_text: Optional[str] = None
    summary: Optional[CallSummary] = None
    quality_score: Optional[QualityScore] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time_seconds: float
    timestamp: datetime = Field(default_factory=datetime.now)