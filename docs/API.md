# API Documentation

This document describes the data models, agent interfaces, and API schemas used in the AI Call Center Assistant system.

## Core Data Models

### CallInput

Input model for call data validation.

```python
class CallInput(BaseModel):
    input_type: InputType  # "audio" or "transcript"
    content: Any          # bytes for audio, str for text transcripts
    file_name: Optional[str] = None
```

**Usage:**
```python
# Audio input
call_input = CallInput(
    input_type=InputType.AUDIO,
    content=audio_bytes,
    file_name="call_recording.mp3"
)

# Transcript input
call_input = CallInput(
    input_type=InputType.TRANSCRIPT,
    content="Customer: Hello, I need help...",
    file_name="transcript.txt"
)
```

### AgentState

Shared state object passed between agents in the workflow.

```python
class AgentState(BaseModel):
    call_id: str
    input_data: CallInput
    transcript_text: Optional[str] = None
    summary: Optional[CallSummary] = None
    quality_score: Optional[QualityScore] = None
    errors: List[Dict[str, Any]] = []
    retry_counts: Dict[str, int] = {}
    
    def add_error(self, agent: str, error: str) -> None:
        """Add an error to the state with timestamp."""
```


### CallSummary

Structured summary output from the summarization agent.

```python
class CallSummary(BaseModel):
    summary: str                   # Main summary of the call
    key_points: List[str]         # Bullet points of important topics
    sentiment: Literal["positive", "neutral", "negative"]
    outcome: Literal["resolved", "escalated", "follow_up", "unresolved"]
```

### QualityScore

Quality assessment scores from the quality scoring agent.

```python
class QualityScore(BaseModel):
    tone_score: float = Field(ge=1.0, le=10.0)           # 1-10 scale
    professionalism_score: float = Field(ge=1.0, le=10.0) # 1-10 scale
    resolution_score: float = Field(ge=1.0, le=10.0)     # 1-10 scale
    feedback: str                                          # Detailed feedback
```

### ProcessingResult

Final result returned after complete workflow execution.

```python
class ProcessingResult(BaseModel):
    call_id: str
    status: Literal["success", "partial", "failed"]
    transcript_text: Optional[str] = None
    summary: Optional[CallSummary] = None
    quality_score: Optional[QualityScore] = None
    errors: List[Dict[str, Any]] = []
    processing_time_seconds: float
    timestamp: datetime
```

## Agent Interfaces

### BaseAgent

All agents inherit from this abstract base class.

```python
class BaseAgent(ABC):
    def __init__(self, agent_name: str)
    
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """Process the state - must be implemented by subclasses."""
        pass
    
    def handle_error(self, state: AgentState, error: Exception, context: str = "") -> AgentState:
        """Standardized error handling across all agents."""
    
    def log_success(self, state: AgentState, message: str) -> None:
        """Log successful operation."""
```

### TranscriptionAgent

Converts audio input to text using OpenAI Whisper.

**Input:** AgentState with audio content in `input_data.content`  
**Output:** AgentState with populated `transcript_text`

**Provider:**
- OpenAI Whisper API

**Key Methods:**
```python
def process(self, state: AgentState) -> AgentState:
    """Convert audio to transcript text."""

def _transcribe_audio(self, audio_content: bytes) -> str:
    """Transcribe using OpenAI Whisper API."""
```

### SummarizationAgent

Generates structured summaries from transcripts.

**Input:** AgentState with `transcript_text`  
**Output:** AgentState with populated `summary`

**Key Methods:**
```python
def process(self, state: AgentState) -> AgentState:
    """Generate summary from transcript."""

def _generate_summary(self, transcript: str) -> CallSummary:
    """Create structured summary from transcript text."""
```

### QualityScoringAgent

Evaluates call quality using structured rubrics.

**Input:** AgentState with `transcript_text` and `summary`  
**Output:** AgentState with populated `quality_score`

**Scoring Rubrics:**
- **Tone Score (1-10)**: Friendliness, empathy, patience
- **Professionalism Score (1-10)**: Language use, protocol adherence
- **Resolution Score (1-10)**: Problem-solving effectiveness

**Key Methods:**
```python
def process(self, state: AgentState) -> AgentState:
    """Evaluate call quality using structured rubrics."""

def _create_scoring_prompt(self, transcript: str, summary: CallSummary) -> str:
    """Create rubric-based scoring prompt."""
```

## Workflow API

### CallCenterWorkflow

Main workflow orchestrator using LangGraph.

```python
class CallCenterWorkflow:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
    )
    
    def process_call(self, call_input: CallInput) -> ProcessingResult:
        """Process a call through the complete workflow."""
```

**Workflow Flow:**
1. `transcription` → (retry up to 2x) → `summarization`
2. `summarization` → (retry up to 2x) → `quality_scoring`  
3. `quality_scoring` → (retry up to 2x) → END

**Retry Logic:**
- Each agent can retry up to 2 times on failure
- Errors are accumulated in `AgentState.errors`
- Partial results are preserved on agent failures

## Error Handling

### Error Structure

```python
{
    "agent": "transcription",
    "error": "API rate limit exceeded",
    "timestamp": "2025-08-14T10:30:45.123456"
}
```

### Status Codes

- **success**: All agents completed successfully
- **partial**: Some agents failed but useful results obtained
- **failed**: Critical failures prevented useful output

## Environment Variables

See `.env.template` for complete configuration options. For setup instructions, see **[Deployment Guide](DEPLOYMENT.md#environment-configuration)**.

## Supported File Formats

### Audio Files
- `.mp3` - MP3 audio files
- `.wav` - WAV audio files
- `.m4a` - M4A audio files
- `.ogg` - OGG audio files
- `.webm` - WebM audio files

### Text Files
- `.txt` - Plain text transcripts
- `.json` - JSON formatted transcripts

## Response Examples

### Successful Processing

```json
{
    "call_id": "call_20250814_103045_abc123",
    "status": "success",
    "transcript_text": "Customer: Hello, I'm having trouble with my password reset...",
    "summary": {
        "summary": "Customer contacted support regarding password reset issues...",
        "key_points": [
            "Customer unable to receive password reset email",
            "Agent identified temporary system issue",
            "New reset link sent successfully"
        ],
        "sentiment": "positive",
        "outcome": "resolved"
    },
    "quality_score": {
        "tone_score": 8.5,
        "professionalism_score": 9.0,
        "resolution_score": 8.0,
        "feedback": "Excellent customer service with clear communication..."
    },
    "errors": [],
    "processing_time_seconds": 12.34,
    "timestamp": "2025-08-14T10:30:45.123456"
}
```

### Partial Failure

```json
{
    "call_id": "call_20250814_103045_xyz789",
    "status": "partial",
    "transcript_text": "Customer: Hello, I need help with...",
    "summary": {
        "summary": "Customer inquiry about account access",
        "key_points": ["Account access issue"],
        "sentiment": "neutral",
        "outcome": "unresolved"
    },
    "quality_score": null,
    "errors": [
        {
            "agent": "quality_scoring",
            "error": "API timeout after 3 retries",
            "timestamp": "2025-08-14T10:31:15.456789"
        }
    ],
    "processing_time_seconds": 45.67,
    "timestamp": "2025-08-14T10:30:45.123456"
}
```