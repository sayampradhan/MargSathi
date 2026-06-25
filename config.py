import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try loading from Streamlit secrets as fallback
try:
    import streamlit as st
    SECRETS = st.secrets
except Exception:
    SECRETS = {}

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or SECRETS.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or SECRETS.get("GROQ_API_KEY", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL") or SECRETS.get("DATABASE_URL", "postgresql://postgres:rFxqktXCDTjCA7k1@db.zbamvclwliwpvfigatav.supabase.co:5432/postgres")

# Models
GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_MODEL_LITE = "gemini-2.5-flash-lite"
GROQ_MODEL = "llama-3.3-70b-versatile"
