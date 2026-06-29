"""LifeHub configuration and constants."""
import os
import base64
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_config(name: str, default=""):
    """Read settings locally from .env and in Streamlit Cloud from Secrets."""
    value = os.getenv(name)
    if value not in (None, ""):
        return value
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def load_logo_b64() -> str:
    logo_path = Path(__file__).parent / "lifehub.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


GROQ_API_KEY = get_config("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
APP_NAME = get_config("APP_NAME", "LifeHub")
APP_TAGLINE = "A professional workspace for community, focus, and productivity"
PROFILE_COLS = "id,username,email,bio,avatar_url,is_admin,is_banned,is_verified,profile_badge,created_at,last_seen"
MAP_LAT = float(get_config("DEFAULT_MAP_LAT", 33.5731))
MAP_LON = float(get_config("DEFAULT_MAP_LON", -7.5898))
MAP_ZOOM = int(get_config("DEFAULT_MAP_ZOOM", 12))
LOGO_B64 = load_logo_b64()
LOGO_SRC = f"data:image/png;base64,{LOGO_B64}" if LOGO_B64 else ""
GROQ_MODEL_CANDIDATES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
]
CSS_VERSION = "pro-v10"
