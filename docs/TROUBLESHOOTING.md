# Troubleshooting Guide

This guide helps resolve common issues encountered when setting up and running the AI Call Center Assistant.

## Installation Issues

### uv Installation Problems

**Problem:** `uv: command not found`
```bash
# Solution: Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

**Problem:** `uv sync` fails with permission errors
```bash
# Solution: Check Python version and permissions
uv python install 3.12
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

**Problem:** Dependencies conflict during `uv sync`
```bash
# Solution: Clear cache and reinstall
uv cache clean
rm -rf .venv
uv venv
uv sync
```

### Python Version Issues

**Problem:** `Python 3.12+ required but 3.x found`
```bash
# Solution: Install Python 3.12
# macOS with Homebrew
brew install python@3.12

# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv

# Use uv to manage Python versions
uv python install 3.12
uv python pin 3.12
```

## API Configuration Issues

### OpenAI API Problems

**Problem:** `Invalid API key` or `401 Unauthorized`
```bash
# Check API key format
echo $OPENAI_API_KEY
# Should start with 'sk-' and be 51 characters long

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**Problem:** `Rate limit exceeded`
```bash
# Solution: Wait and retry, or upgrade OpenAI plan
# Check current usage at https://platform.openai.com/usage

# Add retry delays in .env
MAX_RETRIES=3
RETRY_DELAY=5
```

**Problem:** `Model not found` error
```bash
# Solution: Verify model access
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models | grep gpt-4

# Use alternative model in .env
OPENAI_MODEL=gpt-3.5-turbo
```

### Deepgram API Problems

**Problem:** `Invalid Deepgram API key`
```bash
# Check API key format
echo $DEEPGRAM_API_KEY
# Should be a UUID-like string

# Test Deepgram connectivity  
curl -X GET "https://api.deepgram.com/v1/projects" \
  -H "Authorization: Token $DEEPGRAM_API_KEY"
```

**Problem:** `Audio format not supported`
```bash
# Supported formats: MP3, WAV, M4A, OGG, WebM
# Convert unsupported audio:
ffmpeg -i input.mp4 -acodec libmp3lame output.mp3
```

**Problem:** `Audio file too large`
```bash
# Deepgram limit: 150MB
# Compress audio file:
ffmpeg -i input.wav -b:a 128k output.mp3

# Or split large files:
ffmpeg -i input.wav -f segment -segment_time 300 -c copy output_%03d.wav
```

## Runtime Errors

### Application Startup Issues

**Problem:** `ModuleNotFoundError` for agents or utils
```bash
# Solution: Install in editable mode
uv pip install -e .

# Verify package structure
ls -la agents/ utils/
```

**Problem:** Streamlit not starting on specified port
```bash
# Check if port is in use
lsof -i :8501

# Use different port
uv run streamlit run ui/streamlit_app.py --server.port 8502

# Kill existing processes
pkill -f streamlit
```

**Problem:** `FileNotFoundError` for sample transcripts
```bash
# Verify data directory exists
ls -la data/sample_transcripts/

# Create missing directory
mkdir -p data/sample_transcripts

# Download sample files if missing
# (Add sample transcript content to repo)
```

### Processing Errors

**Problem:** `Audio transcription failed`
```bash
# Check error logs
LOG_LEVEL=DEBUG uv run python main.py audio.mp3

# Common causes:
1. Invalid audio format → Convert to supported format
2. File corrupted → Try different file
3. API timeout → Reduce file size or increase timeout
4. No internet → Check network connectivity
```

**Problem:** `LLM summarization failed`
```bash
# Debug with verbose logging
LOG_LEVEL=DEBUG uv run python main.py transcript.txt

# Check transcript content
head -20 data/sample_transcripts/transcript.txt

# Verify transcript isn't too long (>50k chars)
wc -c data/sample_transcripts/transcript.txt
```

**Problem:** `Quality scoring timeout`
```bash
# Increase timeout in config
echo "OPENAI_TIMEOUT=60" >> .env

# Try smaller transcript
head -100 original_transcript.txt > test_transcript.txt
uv run python main.py test_transcript.txt
```

### Memory and Performance Issues

**Problem:** `Out of memory` during processing
```bash
# Check memory usage
free -h
htop

# Solutions:
1. Reduce audio file size
2. Process files individually instead of batch
3. Add swap space:
   sudo fallocate -l 2G /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
```

**Problem:** Very slow processing times
```bash
# Profile performance
LOG_LEVEL=DEBUG uv run python main.py test_file.txt

# Common causes:
1. Large audio files → Compress or split
2. Network latency → Check internet speed
3. API rate limits → Wait between requests
4. Insufficient resources → Upgrade hardware
```

## Streamlit UI Issues

### UI Not Loading

**Problem:** Streamlit shows blank page
```bash
# Clear browser cache and cookies
# Try in incognito/private mode

# Check JavaScript console for errors
# Chrome: F12 → Console tab

# Restart Streamlit
pkill -f streamlit
uv run streamlit run ui/streamlit_app.py
```

**Problem:** File upload not working
```bash
# Check file size limits (Streamlit default: 200MB)
# Verify file permissions
ls -la uploaded_file.mp3

# Clear Streamlit cache
rm -rf ~/.streamlit
```

**Problem:** Real-time updates not showing
```bash
# Check if session state is corrupted
# Refresh page (F5)
# Clear browser cache

# Enable debugging in Streamlit
uv run streamlit run ui/streamlit_app.py --logger.level debug
```

### UI Performance Issues

**Problem:** Slow page loading
```bash
# Optimize Streamlit configuration
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml << EOF
[server]
enableCORS = false
enableXsrfProtection = false
maxUploadSize = 100

[browser]
gatherUsageStats = false
EOF
```

## Docker Issues

### Container Build Problems

**Problem:** Docker build fails with dependency errors
```bash
# Clear Docker cache
docker system prune -f
docker build --no-cache -t call-assistant .

# Check Python version in container
docker run --rm call-assistant python --version
```

**Problem:** Container runs but service unreachable
```bash
# Check port mapping
docker ps
docker logs container_name

# Verify port binding
docker run -p 8501:8501 call-assistant

# Test inside container
docker exec -it container_name curl localhost:8501
```

### Docker Compose Issues

**Problem:** Services fail to start
```bash
# Check service logs
docker-compose logs call-assistant

# Verify environment variables
docker-compose config

# Start services individually
docker-compose up call-assistant
```

**Problem:** Volume mounting issues
```bash
# Check volume permissions
ls -la data/
chmod -R 755 data/

# Verify mount paths in container
docker-compose exec call-assistant ls -la /app/data/
```

## Network and Connectivity

### API Connectivity Issues

**Problem:** `Connection timeout` to OpenAI/Deepgram
```bash
# Test network connectivity
ping api.openai.com
ping api.deepgram.com

# Check if behind corporate firewall
curl -v https://api.openai.com/v1/models

# Configure proxy if needed
export HTTPS_PROXY=http://proxy.company.com:8080
```

**Problem:** `SSL certificate verification failed`
```bash
# Update certificates
sudo apt update && sudo apt install ca-certificates

# For corporate environments, add custom CA
export REQUESTS_CA_BUNDLE=/path/to/corporate-ca-bundle.crt
```

## Environment Variable Issues

### Missing Environment Variables

**Problem:** Application starts but API calls fail
```bash
# Verify all required variables are set
env | grep -E "(OPENAI|DEEPGRAM)_API_KEY"

# Check .env file is loaded
cat .env
ls -la .env

# Test variable loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY')[:10] if os.getenv('OPENAI_API_KEY') else 'Not found')"
```

### Environment Variable Format Issues

**Problem:** Environment variables not recognized
```bash
# Ensure no extra spaces or quotes
# Correct format:
OPENAI_API_KEY=sk-your-key-here

# Incorrect formats:
OPENAI_API_KEY = sk-your-key-here     # Extra spaces
OPENAI_API_KEY="sk-your-key-here"     # Quotes (depends on shell)
```

## File Processing Issues

### Audio File Problems

**Problem:** `Unsupported audio format`
```bash
# Check file format
file audio_file.xyz

# Convert to supported format
ffmpeg -i input.xyz -acodec libmp3lame output.mp3
```

For complete list of supported formats, see **[API Documentation](API.md#supported-file-formats)**.

**Problem:** `Audio file corrupted`
```bash
# Verify file integrity
ffmpeg -v error -i audio_file.mp3 -f null -

# Try alternative file
cp backup_audio.mp3 test_audio.mp3
uv run python main.py test_audio.mp3
```

### Text File Problems

**Problem:** `Invalid transcript format`
```bash
# Check file encoding
file -I transcript.txt

# Convert to UTF-8 if needed
iconv -f ISO-8859-1 -t UTF-8 transcript.txt > transcript_utf8.txt

# Verify file content
head -10 transcript.txt
```

**Problem:** Transcript too long for processing
```bash
# Check file size
wc -c transcript.txt

# Truncate if over 50k characters
head -c 50000 transcript.txt > truncated_transcript.txt
```

## Debugging Tips

### Enable Debug Logging

```bash
# Maximum verbosity
LOG_LEVEL=DEBUG uv run python main.py your_file.txt

# Monitor logs in real-time
tail -f logs/debug.log  # if logging to file
```

### Test with Sample Data

```bash
# Use provided sample files
uv run python main.py data/sample_transcripts/customer_support.txt

# Verify samples work before testing custom files
ls -la data/sample_transcripts/
```

### Isolated Component Testing

```bash
# Test transcription only
python -c "
from agents.transcription_agent import TranscriptionAgent
from utils.validation import CallInput, InputType, AgentState
# Test individual component
"

# Test API connectivity separately
curl -X POST "https://api.openai.com/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}], "max_tokens": 5}'
```

## Getting Help

### Log Collection for Support

```bash
# Collect system information
uv --version
python --version
cat .env | sed 's/=.*/=***/' # Hide sensitive values

# Collect relevant logs
LOG_LEVEL=DEBUG uv run python main.py problematic_file.txt 2>&1 | tee debug_output.txt

# Check system resources
free -h
df -h
```

### Common Commands for Diagnosis

```bash
# Reset environment completely
rm -rf .venv
uv venv
uv sync

# Test minimal functionality
echo "Hello world" > test.txt
uv run python main.py test.txt

# Verify all dependencies
uv pip list | grep -E "(openai|deepgram|streamlit|langraph)"
```

### When to Contact Support

Contact project maintainers when:

1. **Reproducible bugs** with clear error messages
2. **Performance issues** that persist after optimization
3. **Security concerns** or vulnerability reports
4. **Feature requests** for new functionality

Include in your report:
- Operating system and Python version
- Complete error messages and stack traces
- Steps to reproduce the issue
- Sample files (if not sensitive)
- Debug logs with LOG_LEVEL=DEBUG

## Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| `uv: command not found` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `Python 3.12+ required` | `uv python install 3.12` |
| `Invalid API key` | Check key format and test with curl |
| `Port 8501 in use` | `pkill -f streamlit` or use different port |
| `Module not found` | `uv pip install -e .` |
| `Audio format error` | Convert with ffmpeg to MP3/WAV |
| `File too large` | Compress audio or split file |
| `Memory error` | Add swap space or reduce file size |
| `Streamlit blank page` | Clear browser cache, restart app |
| `API timeout` | Increase timeout or reduce input size |

## Emergency Recovery

### Complete System Reset

```bash
#!/bin/bash
# emergency_reset.sh - Use when everything breaks

echo "🚨 Starting emergency reset..."

# 1. Kill all related processes
pkill -f streamlit
pkill -f "python main.py"

# 2. Clean Python environment
rm -rf .venv __pycache__ **/__pycache__

# 3. Reinstall from scratch
uv venv
uv sync

# 4. Verify installation
uv run python -c "import agents, utils, workflow; print('✅ Installation verified')"

# 5. Test with sample data
uv run python main.py data/sample_transcripts/customer_support.txt

echo "🎉 Emergency reset complete!"
```

### Backup Configuration Recovery

```bash
# Restore from backup
cp .env.backup .env
cp -r data_backup/ data/

# Verify configuration
uv run python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('OpenAI:', 'OK' if os.getenv('OPENAI_API_KEY') else 'MISSING')
print('Deepgram:', 'OK' if os.getenv('DEEPGRAM_API_KEY') else 'MISSING')
"
```

## Prevention Tips

### Regular Maintenance

```bash
# Weekly dependency updates
uv sync --upgrade

# Clean temporary files
rm -rf /tmp/streamlit-*
rm -rf ~/.streamlit/cache

# Monitor disk space
df -h | grep -E "(/$|/tmp)"
```

### Best Practices

1. **Always test with sample data first** before using custom files
2. **Keep backups** of working .env configuration
3. **Monitor logs** during initial deployment
4. **Test API connectivity** before processing large batches
5. **Use version control** for configuration changes
6. **Document custom modifications** for team members

### Health Monitoring

```bash
# Create a health check script
cat > health_check.sh << 'EOF'
#!/bin/bash

echo "🔍 System Health Check"
echo "====================="

# Check Python environment
echo "Python: $(uv python --version 2>/dev/null || echo 'Not found')"
echo "UV: $(uv --version 2>/dev/null || echo 'Not found')"

# Check API connectivity
if curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \
   https://api.openai.com/v1/models > /dev/null; then
    echo "OpenAI API: ✅ Connected"
else
    echo "OpenAI API: ❌ Failed"
fi

if curl -s -H "Authorization: Token $DEEPGRAM_API_KEY" \
   https://api.deepgram.com/v1/projects > /dev/null; then
    echo "Deepgram API: ✅ Connected"
else
    echo "Deepgram API: ❌ Failed"
fi

# Check disk space
echo "Disk Space: $(df -h . | tail -1 | awk '{print $5}') used"

# Check if service is running
if pgrep -f streamlit > /dev/null; then
    echo "Streamlit: ✅ Running"
else
    echo "Streamlit: ❌ Not running"
fi

echo "====================="
EOF

chmod +x health_check.sh
./health_check.sh
```

## Advanced Debugging

### LangSmith Tracing

```bash
# Enable detailed tracing
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_langsmith_key

# View traces at https://smith.langchain.com/
uv run python main.py test_file.txt
```

### Profile Performance

```python
# Add to main.py for performance profiling
import cProfile
import pstats

def profile_main():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your main processing code here
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

if __name__ == "__main__":
    profile_main()
```

### Memory Debugging

```python
# Add memory monitoring
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")

# Call at key points in processing
monitor_memory()
```