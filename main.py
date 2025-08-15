#!/usr/bin/env python3
"""
Simplified CLI for AI Call Center Assistant.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from utils.validation import CallInput, InputType
from workflow import CallCenterWorkflow

# Load environment variables
load_dotenv()

# Configure logging
from config.settings import setup_logging
setup_logging()


def process_file(file_path: str) -> None:
    """Process a single file."""
    try:
        # Load file
        path = Path(file_path)
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return
        
        # Determine input type and load content
        if path.suffix.lower() in ['.mp3', '.wav', '.m4a']:
            input_type = InputType.AUDIO
            content = path.read_bytes()
        else:
            input_type = InputType.TRANSCRIPT  
            content = path.read_text()
        
        # Create input
        call_input = CallInput(
            input_type=input_type,
            content=content,
            file_name=path.name
        )
        
        # Create workflow and process
        workflow = CallCenterWorkflow(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        result = workflow.process_call(call_input)
        
        # Print results
        print(f"\n{'='*50}")
        print(f"📞 CALL PROCESSING RESULTS")
        print(f"{'='*50}")
        print(f"File: {path.name}")
        print(f"Status: {result.status.upper()}")
        print(f"Processing Time: {result.processing_time_seconds:.2f}s")
        
        if result.summary:
            print(f"\n📝 Summary:")
            print(f"{result.summary.summary}")
            print(f"\n🔑 Key Points:")
            for point in result.summary.key_points:
                print(f"• {point}")
            print(f"\nSentiment: {result.summary.sentiment}")
            print(f"Outcome: {result.summary.outcome}")
        
        if result.quality_score:
            print(f"\n📊 Quality Scores:")
            print(f"Tone: {result.quality_score.tone_score:.1f}/10")
            print(f"Professionalism: {result.quality_score.professionalism_score:.1f}/10")
            print(f"Resolution: {result.quality_score.resolution_score:.1f}/10")
            print(f"\n💬 Feedback: {result.quality_score.feedback}")
        
        if result.errors:
            print(f"\n⚠️ Issues:")
            for error in result.errors:
                print(f"• {error['agent']}: {error['error']}")
        
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")


def run_ui():
    """Launch Streamlit UI."""
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/streamlit_app.py"])
    except Exception as e:
        print(f"❌ Failed to launch UI: {e}")


def show_help():
    """Show help information."""
    print("""
📞 AI Call Center Assistant

Usage:
  python main.py <file>     Process a single audio file or transcript
  python main.py --ui       Launch web interface
  python main.py --help     Show this help

Examples:
  python main.py data/sample_transcripts/customer_support.txt
  python main.py audio.mp3
  python main.py --ui

Supported file types:
  • Audio: .mp3, .wav, .m4a
  • Text: .txt, .json

Environment variables:
  • OPENAI_API_KEY     (required for all LLM operations)
""")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    arg = sys.argv[1]
    
    if arg in ["--help", "-h"]:
        show_help()
    elif arg in ["--ui", "-u"]:
        run_ui()
    else:
        # Assume it's a file path
        process_file(arg)


if __name__ == "__main__":
    main()