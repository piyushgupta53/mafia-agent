import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError(
        "DEEPSEEK_API_KEY environment variable is required. "
        "Please set it in your .env file or environment variables."
    )
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# Game Configuration
GAME_CONFIG = {
    "total_players": 13,
    "mafia_count": 3,
    "detective_count": 1,
    "doctor_count": 1,
    "civilian_count": 7,
    "discussion_time": 60,  # seconds (reduced from 120)
    "voting_time": 30,  # seconds (reduced from 60)
    "max_discussion_rounds": 6,  # maximum discussion rounds per phase
    "response_timeout": 15,  # seconds timeout for agent responses
}

# Agent Colors for Frontend
AGENT_COLORS = {
    "mafia": "#8B0000",  # Dark Red
    "detective": "#0066CC",  # Blue
    "doctor": "#228B22",  # Forest Green
    "civilian": "#696969",  # Dim Gray
    "narrator": "#800080",  # Purple
}

# Flask Configuration
FLASK_CONFIG = {"host": "0.0.0.0", "port": 5001, "debug": True}

# Chat Configuration
MAFIA_CHAT_COLOR = "#FF4444"  # Bright Red for mafia-only communications
PUBLIC_CHAT_COLOR = "#333333"  # Dark Gray for public discussions
