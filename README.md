# AI Call Center Assistant (Simplified)

A streamlined multi-agent system for call center analysis using LangGraph and LLMs.

## Quick Start

```bash
# Install dependencies
uv sync

# Test system
python test_simplified.py

# Process a transcript
python main.py data/sample_transcripts/customer_support.txt

# Launch web interface
python main.py --ui
```

## Configuration

Add your API key to a `.env` file:

```
OPENAI_API_KEY=your_key_here
```

## Architecture

- **3 Agents**: Transcription, Summarization, Quality Scoring
- **LangGraph**: Simple workflow with retry logic
- **Streamlit UI**: Single-page interface
- **CLI**: Simple file processing

## Simplified Features

- Reduced from 10+ data models to 6 essential ones
- Eliminated routing agent complexity
- Single-page UI instead of multiple tabs
- Streamlined CLI with just 3 commands
- 50% less code while keeping core functionality

Status:  Simplified and ready to use!