"""
Constants used throughout the application.
"""

# File size limits
MAX_FILE_SIZE_MB = 100
MAX_TRANSCRIPT_LENGTH = 50000

# Audio file extensions
AUDIO_EXTENSIONS = ['mp3', 'wav', 'm4a', 'ogg', 'webm']
TEXT_EXTENSIONS = ['txt', 'json']

# Quality score thresholds
QUALITY_SCORE_EXCELLENT = 9.0
QUALITY_SCORE_GOOD = 7.0
QUALITY_SCORE_ACCEPTABLE = 5.0
QUALITY_SCORE_POOR = 3.0

# Score ranges for visual indicators
SCORE_RANGES = {
    "excellent": (9, 10),
    "good": (7, 9),
    "acceptable": (5, 7),
    "poor": (3, 5),
    "very_poor": (0, 3)
}

# Sentiment values
SENTIMENT_POSITIVE = "positive"
SENTIMENT_NEUTRAL = "neutral"
SENTIMENT_NEGATIVE = "negative"

# Call outcomes
OUTCOME_RESOLVED = "resolved"
OUTCOME_ESCALATED = "escalated"
OUTCOME_FOLLOW_UP = "follow_up"
OUTCOME_UNRESOLVED = "unresolved"

# Processing status
STATUS_SUCCESS = "success"
STATUS_PARTIAL = "partial"
STATUS_FAILED = "failed"

# Retry configuration
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_DELAY = 1.0

# UI Progress milestones
PROGRESS_INIT = 10
PROGRESS_TRANSCRIPTION = 25
PROGRESS_SUMMARIZATION = 55
PROGRESS_QUALITY = 80
PROGRESS_RETRY = 90
PROGRESS_COMPLETE = 100

# Logging formats
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Model defaults
DEFAULT_LLM_MODEL = "gpt-4-turbo-preview"
DEFAULT_LLM_TEMPERATURE = 0.3
DEFAULT_TRANSCRIPTION_MODEL = "nova-2"

# UI Theme colors
THEME_PRIMARY = "#3b82f6"
THEME_SUCCESS = "#16a34a"
THEME_WARNING = "#f59e0b"
THEME_ERROR = "#dc2626"
THEME_DARK_BG = "#1e293b"
THEME_LIGHT_BG = "#f8fafc"