"""
Simplified Transcription Agent - Converts audio to text using Deepgram API with diarization.
"""

import logging
import os
import tempfile
from typing import Optional, Tuple, List

from deepgram import DeepgramClient, PrerecordedOptions, FileSource
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
            
            # Try a simpler approach without complex type handling
            logger.info("Creating basic Deepgram request")
            
            # Read the audio file
            with open(tmp_file_path, "rb") as audio_file:
                buffer_data = audio_file.read()
            
            # Use a simpler payload format to avoid Union type issues
            from deepgram import FileSource
            payload = {"buffer": buffer_data}
            
            # Simpler options to avoid potential type issues
            options = {
                "model": "nova-2",
                "smart_format": True,
                "punctuate": True,
                "diarize": True,
                "language": "en-US"
            }
            
            logger.info("Sending request to Deepgram with simplified approach")
            
            # Try the API call with error handling
            try:
                response = self.deepgram_client.listen.rest.v("1").transcribe_file(
                    payload, options
                )
                logger.info("Successfully received Deepgram response")
                
                # Parse response safely
                transcript_text = ""
                speaker_segments = []
                
                if hasattr(response, 'results') and response.results:
                    if hasattr(response.results, 'channels') and response.results.channels:
                        channel = response.results.channels[0]
                        if hasattr(channel, 'alternatives') and channel.alternatives:
                            transcript_text = channel.alternatives[0].transcript or ""
                            logger.info(f"Extracted transcript: {len(transcript_text)} characters")
                
                # Parse speaker diarization if available
                from utils.validation import SpeakerSegment
                if transcript_text:
                    # Try to extract speaker segments from diarized response
                    speaker_segments = self._parse_speaker_segments(response, transcript_text)
                    
                    # Fallback to single speaker if diarization parsing fails
                    if not speaker_segments:
                        logger.info("No speaker segments found, creating single speaker segment")
                        speaker_segments = [
                            SpeakerSegment(
                                speaker="Speaker 0",
                                text=transcript_text,
                                start=0.0,
                                end=10.0,  # Estimated duration
                                confidence=0.9
                            )
                        ]
                    
                return transcript_text, speaker_segments
                
            except Exception as deepgram_error:
                logger.error(f"Deepgram API error: {deepgram_error}")
                # Fall back to OpenAI if available
                if self.openai_client:
                    logger.info("Falling back to OpenAI Whisper")
                    transcript = self._fallback_transcribe_audio(audio_content)
                    # Return with empty speaker segments
                    return transcript, []
                else:
                    raise deepgram_error
            
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def _parse_speaker_segments(self, response, transcript_text):
        """Safely parse speaker segments from Deepgram response."""
        try:
            from utils.validation import SpeakerSegment
            speaker_segments = []
            
            logger.info("Attempting to parse speaker diarization data")
            
            # Navigate response structure safely
            if not (hasattr(response, 'results') and response.results):
                logger.info("No results in response")
                return []
                
            if not (hasattr(response.results, 'channels') and response.results.channels):
                logger.info("No channels in response")
                return []
                
            channel = response.results.channels[0]
            if not (hasattr(channel, 'alternatives') and channel.alternatives):
                logger.info("No alternatives in channel")
                return []
                
            alternative = channel.alternatives[0]
            if not (hasattr(alternative, 'words') and alternative.words):
                logger.info("No words with timing in response")
                return []
            
            logger.info(f"Found {len(alternative.words)} words with timing data")
            
            # Group words by speaker
            current_speaker = None
            current_text = ""
            current_start = None
            current_end = None
            
            for word in alternative.words:
                # Safely get speaker info
                speaker = getattr(word, 'speaker', 0)
                word_text = getattr(word, 'word', '')
                word_start = getattr(word, 'start', 0.0)
                word_end = getattr(word, 'end', 0.0)
                
                if current_speaker is None:
                    # First word
                    current_speaker = speaker
                    current_text = word_text
                    current_start = word_start
                    current_end = word_end
                elif current_speaker == speaker:
                    # Same speaker, continue building segment
                    current_text += " " + word_text
                    current_end = word_end
                else:
                    # Speaker changed, save current segment
                    if current_text.strip():
                        speaker_segments.append(SpeakerSegment(
                            speaker=f"Speaker {current_speaker}",
                            text=current_text.strip(),
                            start=float(current_start),
                            end=float(current_end),
                            confidence=getattr(word, 'confidence', 0.9)
                        ))
                    
                    # Start new segment
                    current_speaker = speaker
                    current_text = word_text
                    current_start = word_start
                    current_end = word_end
            
            # Add final segment
            if current_text and current_text.strip():
                speaker_segments.append(SpeakerSegment(
                    speaker=f"Speaker {current_speaker}",
                    text=current_text.strip(),
                    start=float(current_start),
                    end=float(current_end),
                    confidence=getattr(alternative.words[-1], 'confidence', 0.9)
                ))
            
            logger.info(f"Successfully parsed {len(speaker_segments)} speaker segments")
            return speaker_segments
            
        except Exception as e:
            logger.warning(f"Failed to parse speaker segments: {e}")
            return []
    
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