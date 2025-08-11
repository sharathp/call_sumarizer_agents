"""
Simplified Transcription Agent - Converts audio to text using Whisper API.
"""

import logging
import os
import tempfile
from typing import Optional

from openai import OpenAI

from utils.validation import AgentState, InputType

logger = logging.getLogger(__name__)


class TranscriptionAgent:
    """Simplified agent for converting audio to text."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required for transcription.")
        self.client = OpenAI(api_key=self.api_key)
    
    def process(self, state: AgentState) -> AgentState:
        """Process audio input and convert to text."""
        # Skip if not audio input
        if state.input_data.input_type != InputType.AUDIO:
            if isinstance(state.input_data.content, str):
                state.transcript_text = state.input_data.content
            return state
        
        try:
            # Transcribe audio
            text = self._transcribe_audio(state.input_data.content)
            state.transcript_text = text
            logger.info(f"Transcription completed for call {state.call_id}")
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            state.add_error("transcription", str(e))
        
        return state
    
    def _transcribe_audio(self, audio_content: bytes) -> str:
        """Transcribe audio using Whisper API."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(audio_content)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        finally:
            os.unlink(tmp_file_path)