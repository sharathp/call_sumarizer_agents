# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Call Center Assistant application that uses multi-agent systems to convert call center interactions (audio/transcripts) into structured summaries and quality assessments. The system implements a modular multi-agent architecture using LLMs, transcription APIs, and orchestration tools.

## Key Technologies

- **Package Manager**: uv for fast Python package and project management
- **Multi-Agent Framework**: LangGraph
- **LLMs**: GPT-4, Claude for language understanding and generation
- **Transcription**: Whisper API
- **UI Framework**: Streamlit for web interface
- **Validation**: Pydantic for structured outputs
- **Python Version**: 3.12

## Agent Architecture

The system consists of 5 specialized agents:
1. **Call Intake Agent**: Validates input formats and extracts metadata
2. **Transcription Agent**: Converts audio to text
3. **Summarization Agent**: Generates summaries and key points
4. **Quality Scoring Agent**: Evaluates tone, professionalism, and resolution
5. **Routing Agent**: Handles fallback and conditional flow

## Project Structure

```
call_summarizer_agents/
├── agents/               # Individual agent implementations
│   ├── intake_agent.py
│   ├── transcription_agent.py
│   ├── summarization_agent.py
│   ├── quality_score_agent.py
│   └── routing_agent.py
├── ui/                  # Streamlit web interface
│   └── streamlit_app.py
├── utils/               # Validation and helper functions
│   └── validation.py
├── data/                # Sample transcripts and test data
│   └── sample_transcripts/
├── config/              # Configuration files
│   └── mcp.yaml
├── docker-compose.yml   # Docker deployment configuration
└── main.py             # Entry point
```

## Development Commands

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Add a new dependency
uv add <package-name>

# Install all dependencies from pyproject.toml
uv sync

# Run the Streamlit UI
uv run streamlit run ui/streamlit_app.py

# Run the main application
uv run python main.py

# Run tests (when implemented)
uv run pytest tests/

# Format code (when configured)
uv run ruff format .
uv run ruff check .

# Type checking (when configured)
uv run mypy .
```

## Implementation Guidelines

1. **Agent Design**: Each agent should be modular with clear input/output contracts using Pydantic models
2. **Error Handling**: Implement fallback logic in the Routing Agent for failed operations
3. **Structured Outputs**: Use Pydantic models for all agent outputs to ensure consistency
4. **Memory Management**: Use LangGraph Memory or Redis/Postgres for call context retention
5. **Function Calling**: Implement QA scoring with structured rubrics using function calling

## Key Features to Implement

- Audio file upload and transcription
- JSON transcript processing
- Structured summary generation with key points
- Quality scoring with empathy, resolution, and tone metrics
- Streamlit UI with sections for transcript, summary, scores, and highlights
- Fallback routing logic for error handling
- Memory layer for context retention across calls

## Dependencies Management

All dependencies are tracked in `pyproject.toml` (not requirements.txt). The project uses `uv` for fast, reliable package management.

Core packages:
- langchain / langgraph
- openai / anthropic
- streamlit
- pydantic
- openai-whisper
- redis (optional for memory)

To add dependencies:
```bash
# Add to main dependencies in pyproject.toml
uv add langchain langgraph openai anthropic streamlit pydantic
uv add openai-whisper  # For transcription

# Add optional dependencies
uv add redis --optional  # For memory layer

# Add development dependencies
uv add --dev pytest ruff mypy
```

**Note**: Do NOT use requirements.txt for dependency management. All dependencies should be defined in pyproject.toml.

## Testing Approach

- Unit tests for individual agents
- Integration tests for multi-agent flows
- Sample transcripts in data/sample_transcripts/ for testing
- Mock LLM responses for consistent testing

## Deployment

- Docker containerization support via docker-compose.yml
- Streamlit Cloud deployment option
- Environment variables for API keys and configuration

**Note on requirements.txt**: This project uses pyproject.toml for dependency management. If a deployment platform requires requirements.txt, generate it with:
```bash
uv pip compile pyproject.toml -o requirements.txt
```
However, never manually edit requirements.txt - always update dependencies in pyproject.toml.