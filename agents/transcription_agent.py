"""
Simplified Transcription Agent - Converts audio to text using OpenAI Whisper API.
"""

import logging
import os
import tempfile
from typing import Optional

from openai import OpenAI

from utils.validation import AgentState, InputType

logger = logging.getLogger(__name__)


class TranscriptionAgent:
    """Simplified agent for converting audio to text using OpenAI Whisper."""
    
    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required for transcription.")
        self.openai_client = OpenAI(api_key=self.openai_api_key)
    
    def process(self, state: AgentState) -> AgentState:
        """Process audio input and convert to text using Whisper."""
        # Skip if not audio input
        if state.input_data.input_type != InputType.AUDIO:
            if isinstance(state.input_data.content, str):
                state.transcript_text = state.input_data.content
            return state
        
        try:
            # Transcribe audio using Whisper
            transcript_text = self._transcribe_audio(state.input_data.content)
            state.transcript_text = transcript_text
            logger.info(f"Transcription completed for call {state.call_id}")
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            state.add_error("transcription", str(e))
        
        return state
    
    def _transcribe_audio(self, audio_content: bytes) -> str:
        """Transcribe audio using OpenAI Whisper API."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(audio_content)
            tmp_file_path = tmp_file.name
        
        try:
            logger.info("Starting Whisper transcription")
            
            with open(tmp_file_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            transcript_text = transcript.text
            
            if not transcript_text:
                raise ValueError("No transcript text returned from Whisper")
                
            logger.info(f"Transcription completed: {len(transcript_text)} characters")
            return transcript_text
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {str(e)}")
            raise e
            
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)