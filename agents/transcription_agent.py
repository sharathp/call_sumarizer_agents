"""
Simplified Transcription Agent - Converts audio to text using Deepgram API with diarization.
"""

import logging
import os
import tempfile
from typing import Optional

from deepgram import DeepgramClient
from openai import OpenAI

from utils.validation import AgentState, InputType, SpeakerSegment

logger = logging.getLogger(__name__)


class TranscriptionAgent:
    """Simplified agent for converting audio to text with speaker diarization."""
    
    def __init__(self, deepgram_api_key=None, openai_api_key=None):
        # Primary: Deepgram for diarization
        self.deepgram_api_key = deepgram_api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.deepgram_api_key:
            raise ValueError("Deepgram API key is required for transcription with diarization.")
        self.deepgram_client = DeepgramClient(self.deepgram_api_key)
        
        # Fallback: OpenAI Whisper (optional)
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
    
    def process(self, state: AgentState) -> AgentState:
        """Process audio input and convert to text with diarization."""
        # Skip if not audio input
        if state.input_data.input_type != InputType.AUDIO:
            if isinstance(state.input_data.content, str):
                state.transcript_text = state.input_data.content
            return state
        
        try:
            # Transcribe audio with diarization
            transcript_text, speaker_segments = self._transcribe_with_diarization(state.input_data.content)
            state.transcript_text = transcript_text
            state.speakers = speaker_segments
            logger.info(f"Transcription with diarization completed for call {state.call_id}")
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            state.add_error("transcription", str(e))
            
            # Fallback to basic transcription if available
            if self.openai_client:
                try:
                    text = self._fallback_transcribe_audio(state.input_data.content)
                    state.transcript_text = text
                    logger.info(f"Fallback transcription completed for call {state.call_id}")
                except Exception as fallback_e:
                    logger.error(f"Fallback transcription also failed: {str(fallback_e)}")
                    state.add_error("transcription_fallback", str(fallback_e))
        
        return state
    
    def _transcribe_with_diarization(self, audio_content):
        """Transcribe audio using Deepgram API with speaker diarization."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(audio_content)
            tmp_file_path = tmp_file.name
        
        try:
            logger.info("Starting Deepgram transcription with diarization")
            
            # Read the audio file
            with open(tmp_file_path, "rb") as audio_file:
                buffer_data = audio_file.read()
            
            # Configure Deepgram options for utterance-level diarization
            options = {
                "model": "nova-2",
                "smart_format": True,
                "punctuate": True,
                "diarize": True,
                "utterances": True,  # Get utterance-level segments
                "language": "en-US"
            }
            
            # Create payload with buffer data
            payload = {"buffer": buffer_data}
            
            logger.info("Sending request to Deepgram")
            response = self.deepgram_client.listen.prerecorded.v("1").transcribe_file(
                payload, options
            )
            
            # Extract transcript and speaker segments
            transcript_text, speaker_segments = self._extract_transcript_and_speakers(response)
            
            if not transcript_text:
                raise ValueError("No transcript text extracted from response")
                
            logger.info(f"Transcription completed: {len(transcript_text)} chars, {len(speaker_segments)} segments")
            return transcript_text, speaker_segments
            
        except Exception as e:
            logger.error(f"Deepgram transcription failed: {str(e)}")
            # Fallback to OpenAI if available
            if self.openai_client:
                logger.info("Falling back to OpenAI Whisper")
                transcript = self._fallback_transcribe_audio(audio_content)
                # Create single speaker segment for fallback
                segments = [SpeakerSegment(
                    speaker="Speaker 1",
                    text=transcript,
                    start=0.0,
                    end=10.0,
                    confidence=0.9
                )] if transcript else []
                return transcript, segments
            raise e
            
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def _extract_transcript_and_speakers(self, response):
        """Extract transcript and speaker segments from Deepgram response."""
        transcript_text = ""
        speaker_segments = []
        
        try:
            # Get the transcript text
            if response.results and response.results.channels:
                channel = response.results.channels[0]
                if channel.alternatives:
                    transcript_text = channel.alternatives[0].transcript or ""
            
            # Try to get utterances (pre-grouped by speaker)
            if hasattr(response.results, 'utterances') and response.results.utterances:
                logger.info(f"Found {len(response.results.utterances)} utterances")
                
                for utterance in response.results.utterances:
                    if utterance.transcript:
                        speaker_segments.append(SpeakerSegment(
                            speaker=f"Speaker {utterance.speaker}",
                            text=utterance.transcript,
                            start=utterance.start,
                            end=utterance.end,
                            confidence=utterance.confidence if hasattr(utterance, 'confidence') else 0.9
                        ))
            
            # If no utterances but we have transcript, create single segment
            if transcript_text and not speaker_segments:
                logger.info("No utterances found, creating single speaker segment")
                speaker_segments = [SpeakerSegment(
                    speaker="Speaker 1",
                    text=transcript_text,
                    start=0.0,
                    end=10.0,
                    confidence=0.9
                )]
            
        except Exception as e:
            logger.warning(f"Error extracting speaker segments: {e}")
            # If we at least have transcript text, use it
            if transcript_text:
                speaker_segments = [SpeakerSegment(
                    speaker="Speaker 1",
                    text=transcript_text,
                    start=0.0,
                    end=10.0,
                    confidence=0.9
                )]
        
        return transcript_text, speaker_segments
    
    def _fallback_transcribe_audio(self, audio_content):
        """Fallback transcription using OpenAI Whisper API."""
        if not self.openai_client:
            raise ValueError("OpenAI client not available for fallback transcription")
            
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(audio_content)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        finally:
            os.unlink(tmp_file_path)