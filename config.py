import os
import streamlit as st

# Try loading from dotenv for local script testing if needed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_secret(key, default=""):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

# API Keys
GEMINI_API_KEY = get_secret("GEMINI_API_KEY", "")
GROQ_API_KEY = get_secret("GROQ_API_KEY", "")

# Database
DATABASE_URL = get_secret("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/margsathi")

# Models
GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_MODEL_LITE = "gemini-2.5-flash-lite"
GROQ_MODEL = "llama-3.3-70b-versatile"
