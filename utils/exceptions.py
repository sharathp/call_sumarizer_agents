"""
Custom exceptions for better error handling.
"""


class CallProcessingError(Exception):
    """Base exception for call processing errors."""
    pass


class TranscriptionError(CallProcessingError):
    """Error during audio transcription."""
    pass


class SummarizationError(CallProcessingError):
    """Error during call summarization."""
    pass


class QualityScoringError(CallProcessingError):
    """Error during quality assessment."""
    pass


class ConfigurationError(CallProcessingError):
    """Error in configuration or missing requirements."""
    pass


class LLMResponseError(CallProcessingError):
    """Error parsing or processing LLM responses."""
    pass


class WorkflowError(CallProcessingError):
    """Error in workflow execution."""
    pass