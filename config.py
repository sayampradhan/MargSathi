import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/margsathi")

# Models
GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_MODEL_LITE = "gemini-2.5-flash-lite"
GROQ_MODEL = "llama-3.3-70b-versatile"
