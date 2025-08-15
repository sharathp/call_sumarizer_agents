"""
Helper utilities for common operations.
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def parse_llm_json_response(content: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling common formatting issues.
    
    Args:
        content: Raw LLM response content
        fallback: Optional fallback dictionary if parsing fails
        
    Returns:
        Parsed dictionary or fallback if provided
    """
    if not content:
        return fallback or {}
    
    # Clean content
    content = content.strip()
    
    # Remove common markdown code block wrappers
    if content.startswith('```json'):
        content = content.replace('```json', '').replace('```', '').strip()
    elif content.startswith('```'):
        content = content.replace('```', '').strip()
    
    # Remove any potential backticks
    content = content.replace('`', '')
    
    try:
        result = json.loads(content)
        
        # Special handling for feedback field if it's a dictionary
        if isinstance(result, dict) and 'feedback' in result:
            if isinstance(result['feedback'], dict):
                # Convert dictionary feedback to string
                feedback_dict = result['feedback']
                feedback_parts = []
                for key, value in feedback_dict.items():
                    if isinstance(value, str):
                        feedback_parts.append(f"{key.title()}: {value}")
                    elif isinstance(value, (list, dict)):
                        feedback_parts.append(f"{key.title()}: {json.dumps(value)}")
                result['feedback'] = " ".join(feedback_parts)
                logger.warning("Converted dictionary feedback to string format")
        
        return result
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}, Content preview: {content[:200]}...")
        if fallback:
            logger.info("Using fallback response")
            return fallback
        raise


def format_speaker_conversation(speakers: list) -> str:
    """
    Format speaker segments into readable conversation format.
    
    Args:
        speakers: List of SpeakerSegment objects
        
    Returns:
        Formatted conversation string
    """
    if not speakers:
        return "No speaker data available"
    
    conversation_lines = []
    for segment in speakers:
        timestamp = f"[{segment.start:.1f}s-{segment.end:.1f}s]"
        conversation_lines.append(f"{segment.speaker} {timestamp}: {segment.text}")
    
    return "\n".join(conversation_lines)


def calculate_speaker_statistics(speakers: list) -> Dict[str, Any]:
    """
    Calculate statistics from speaker segments.
    
    Args:
        speakers: List of SpeakerSegment objects
        
    Returns:
        Dictionary with speaker statistics
    """
    if not speakers:
        return {"total_speakers": 0, "total_duration": 0, "speaker_stats": {}}
    
    speaker_stats = {}
    total_duration = 0
    
    for segment in speakers:
        speaker = segment.speaker
        duration = segment.end - segment.start
        word_count = len(segment.text.split())
        
        if speaker not in speaker_stats:
            speaker_stats[speaker] = {
                "segment_count": 0,
                "total_duration": 0,
                "word_count": 0
            }
        
        speaker_stats[speaker]["segment_count"] += 1
        speaker_stats[speaker]["total_duration"] += duration
        speaker_stats[speaker]["word_count"] += word_count
        total_duration = max(total_duration, segment.end)
    
    # Calculate percentages
    for speaker, stats in speaker_stats.items():
        stats["duration_percentage"] = (stats["total_duration"] / total_duration * 100) if total_duration > 0 else 0
    
    return {
        "total_speakers": len(speaker_stats),
        "total_duration": total_duration,
        "speaker_stats": speaker_stats
    }


def identify_likely_agent(speakers: list) -> Optional[str]:
    """
    Identify the likely agent from speaker segments using heuristics.
    
    Args:
        speakers: List of SpeakerSegment objects
        
    Returns:
        Speaker identifier of likely agent or None
    """
    if not speakers:
        return None
    
    # Count segments per speaker
    speaker_counts = {}
    for segment in speakers:
        speaker_counts[segment.speaker] = speaker_counts.get(segment.speaker, 0) + 1
    
    # Agent typically speaks more frequently in call centers
    if speaker_counts:
        return max(speaker_counts.items(), key=lambda x: x[1])[0]
    
    return None


def identify_likely_agent_from_stats(speaker_stats: dict) -> Optional[str]:
    """
    Identify the likely agent from speaker statistics.
    
    Args:
        speaker_stats: Dictionary with speaker statistics
        
    Returns:
        Speaker identifier of likely agent or None
    """
    if not speaker_stats:
        return None
    
    # Agent typically has more segments (speaks more frequently)
    speakers_by_segments = sorted(
        speaker_stats.items(),
        key=lambda x: x[1].get("segment_count", 0),
        reverse=True
    )
    
    return speakers_by_segments[0][0] if speakers_by_segments else None