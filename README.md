# AI Call Center Assistant

A sophisticated multi-agent system for call center analysis with automated transcription, summarization, and quality assessment. Built with LangGraph, OpenAI, and Deepgram APIs.

## Features

- **Multi-Agent Architecture**: Specialized agents for transcription, summarization, and quality scoring
- **Speaker Diarization**: Advanced audio processing with speaker identification using Deepgram
- **Quality Assessment**: Structured rubric-based evaluation of tone, professionalism, and resolution
- **Modern UI**: Professional Streamlit interface with real-time progress tracking
- **Robust Error Handling**: Comprehensive retry logic and fallback mechanisms
- **Flexible Input**: Supports both audio files and text transcripts

## Quick Start

### Prerequisites
- Python 3.12+
- OpenAI API key (required)
- Deepgram API key (required for audio transcription)

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd call_summarizer_agents

# Install with uv (recommended)
uv sync

# Or install dependencies manually
pip install -e .
```

### Configuration

Create a `.env` file with your API keys:

```bash
OPENAI_API_KEY=your_openai_key_here
DEEPGRAM_API_KEY=your_deepgram_key_here
LANGCHAIN_API_KEY=your_langsmith_key_here  # Optional, for debugging traces
```

### Usage

#### CLI Interface

```bash
# Process a transcript file
uv run python main.py data/sample_transcripts/customer_support.txt

# Process an audio file
uv run python main.py audio.mp3

# Launch web interface
uv run python main.py --ui

# Show help
uv run python main.py --help
```

#### Web Interface

```bash
# Launch Streamlit UI
uv run streamlit run ui/streamlit_app.py
```

The web interface provides:
- File upload for audio (.mp3, .wav, .m4a) and text (.txt) files
- Real-time processing progress
- Interactive results with speaker-segmented transcripts
- Quality score visualizations with gauge charts
- Detailed feedback and analysis

## Architecture

### Agent System
- **Base Agent**: Common functionality and error handling
- **Transcription Agent**: Deepgram + OpenAI Whisper fallback with speaker diarization
- **Summarization Agent**: GPT-4 powered analysis with speaker-aware context
- **Quality Scoring Agent**: Structured rubric evaluation (tone, professionalism, resolution)

### Workflow
- **LangGraph**: Orchestrates agent execution with intelligent routing
- **Retry Logic**: Automatic retry on failures with configurable limits
- **State Management**: Persistent state across agent interactions
- **Error Recovery**: Graceful handling of partial failures

### Configuration
- **Centralized Settings**: Environment-based configuration management
- **Model Selection**: Configurable LLM providers and models
- **Validation**: Comprehensive input validation and error reporting

## Project Structure

```
call_summarizer_agents/
├── agents/                 # Agent implementations
│   ├── base_agent.py      # Common agent functionality
│   ├── transcription_agent.py
│   ├── summarization_agent.py
│   └── quality_score_agent.py
├── config/                # Configuration management
│   └── settings.py
├── ui/                    # Web interface
│   ├── streamlit_app.py
│   └── styles.py
├── utils/                 # Utilities and validation
│   ├── constants.py
│   ├── exceptions.py
│   ├── helpers.py
│   └── validation.py
├── data/                  # Sample data
│   └── sample_transcripts/
├── main.py               # CLI entry point
├── workflow.py           # LangGraph workflow
└── pyproject.toml        # Dependencies and metadata
```

## Development

### Dependencies
This project uses `uv` for fast, reliable dependency management:

```bash
# Add new dependency
uv add package-name

# Add development dependency  
uv add --dev package-name

# Sync dependencies
uv sync
```

### Code Quality
- **Linting**: `uv run ruff check .`
- **Formatting**: `uv run ruff format .`
- **Type Checking**: `uv run mypy .`

### Testing
```bash
# Run tests (when implemented)
uv run pytest tests/
```

## API Keys

### Required APIs
- **OpenAI**: For LLM operations (summarization and quality scoring)
- **Deepgram**: For audio transcription with speaker diarization

### Optional APIs  
- **LangSmith**: For debugging and tracing workflow execution

## Supported File Types

### Audio Files
- `.mp3` - MP3 audio
- `.wav` - WAV audio  
- `.m4a` - M4A audio
- `.ogg` - OGG audio
- `.webm` - WebM audio

### Text Files
- `.txt` - Plain text transcripts
- `.json` - JSON formatted transcripts

## Example Output

```
📞 CALL PROCESSING RESULTS
==================================================
File: customer_support.txt
Status: SUCCESS
Processing Time: 12.33s

📝 Summary:
The call was regarding a customer experiencing an 'Invalid request' error...

🔑 Key Points:
• Customer faced password reset error
• Agent identified temporary system issue  
• New reset link sent successfully
• Customer satisfied with resolution

Sentiment: positive
Outcome: resolved

📊 Quality Scores:
Tone: 8.0/10
Professionalism: 7.5/10
Resolution: 9.0/10

💬 Feedback: The agent demonstrated excellent customer service...
==================================================
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the existing code style
4. Add tests for new functionality
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Check the documentation in `CLAUDE.md`
- Review sample files in `data/sample_transcripts/`
- Open an issue on GitHub