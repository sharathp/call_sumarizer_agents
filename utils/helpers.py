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








