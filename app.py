# ============================================================
# LifeHub — Premium Social Platform (Discord-Inspired Dark + Blurple)
# Streamlit + Supabase + Groq AI
# ============================================================

import os, time, hashlib, base64, requests, io, html, random
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs
from PIL import Image

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client
from postgrest.types import ReturnMethod
import json

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

# --- Groq AI Setup (OpenAI-compatible) ---
GROQ_API_KEY  = get_config("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

APP_NAME = get_config("APP_NAME", "LifeHub")
APP_TAGLINE = "A professional workspace for community, focus, and productivity"
MAP_LAT  = float(get_config("DEFAULT_MAP_LAT", 33.5731))
MAP_LON  = float(get_config("DEFAULT_MAP_LON", -7.5898))
MAP_ZOOM = int(get_config("DEFAULT_MAP_ZOOM", 12))

# ── Load logo as base64 ──────────────────────────────────────
def load_logo_b64() -> str:
    logo_path = Path(__file__).parent / "lifehub.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = load_logo_b64()
LOGO_SRC = f"data:image/png;base64,{LOGO_B64}" if LOGO_B64 else ""

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS — Discord-Inspired Dark + Blurple Theme
# ============================================================
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');

:root {
  --primary: #6366f1;
  --primary-light: #818cf8;
  --secondary: #06b6d4;
  --accent: #f472b6;
  --bg0: #020617;
  --bg1: #0f172a;
  --bg2: #1e293b;
  --card: rgba(15, 23, 42, 0.88);
  --card-hover: rgba(30, 41, 59, 0.92);
  --border: rgba(148, 163, 184, 0.22);
  --border-light: rgba(148, 163, 184, 0.1);
  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
  --radius: 16px;
  --radius-lg: 24px;
  --radius-xl: 32px;
}

*, *::before, *::after {
  box-sizing: border-box;
}

html, body, .stApp {
  background: radial-gradient(circle at 12% 8%, rgba(99, 102, 241, 0.3), transparent 32%), 
              radial-gradient(circle at 88% 24%, rgba(6, 182, 212, 0.25), transparent 30%), 
              linear-gradient(135deg, #020617 0%, #0f172a 45%, #020617 100%) !important;
  color: var(--text-primary) !important;
  font-family: 'Inter', sans-serif !important;
  scroll-behavior: smooth !important;
}

/* Animated background */
.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at 20% 20%, rgba(99, 102, 241, 0.08), transparent 40%),
              radial-gradient(circle at 80% 80%, rgba(6, 182, 212, 0.06), transparent 45%);
  animation: bgShift 12s ease-in-out infinite;
  pointer-events: none;
  z-index: 0;
}

@keyframes bgShift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(10px, -10px) scale(1.02); }
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(2, 6, 23, 0.98), rgba(15, 23, 42, 0.95)) !important;
  border-right: 1px solid rgba(148, 163, 184, 0.15) !important;
  box-shadow: 8px 0 40px rgba(0, 0, 0, 0.4) !important;
  backdrop-filter: blur(20px);
}

/* Main container */
.main .block-container {
  padding: 1.75rem 2.5rem 2.75rem !important;
  max-width: 1440px !important;
}

/* Input styling */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stSelectbox [data-baseweb="select"],
.stDateInput input,
.stTimeInput input {
  background: rgba(15, 23, 42, 0.92) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  font-family: 'Inter', sans-serif !important;
  transition: all 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28) !important;
  padding: 0.85rem 1.1rem !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox [data-baseweb="select"]:focus-within,
.stDateInput input:focus,
.stTimeInput input:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.15), 0 0 40px rgba(99, 102, 241, 0.18) !important;
  background: rgba(15, 23, 42, 0.98) !important;
  transform: translateY(-2px);
}

/* Button styling - Professional Upgrade */
.stButton > button {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
  color: white !important;
  border: none !important;
  border-radius: var(--radius) !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em !important;
  transition: all 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28) !important;
  box-shadow: 0 12px 38px rgba(99, 102, 241, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
  padding: 0.8rem 2rem !important;
  min-height: 48px !important;
}

.stButton > button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent);
  transition: left 0.6s ease-in-out;
}

.stButton > button:hover::before {
  left: 100%;
}

.stButton > button:hover {
  transform: translateY(-4px) scale(1.02) !important;
  box-shadow: 0 20px 55px rgba(99, 102, 241, 0.4), 0 0 35px rgba(6, 182, 212, 0.25) !important;
}

.stButton > button:active {
  transform: translateY(0) scale(0.97) !important;
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.25) !important;
  transition-duration: 0.1s;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
  justify-content: flex-start !important;
  text-align: left !important;
  background: rgba(15, 23, 42, 0.78) !important;
  border: 1px solid rgba(148, 163, 184, 0.15) !important;
  box-shadow: none !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.24), rgba(6, 182, 212, 0.18)) !important;
  border-color: rgba(129, 140, 248, 0.4) !important;
  transform: translateX(6px) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(15, 23, 42, 0.78) !important;
  border: 1px solid rgba(148, 163, 184, 0.18) !important;
  border-radius: var(--radius-lg) !important;
  padding: 0.5rem !important;
  gap: 0.6rem !important;
}

.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-muted) !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  transition: all 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28) !important;
  padding: 0.7rem 1.3rem !important;
}

.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.28), rgba(6, 182, 212, 0.22)) !important;
  color: white !important;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.3) inset, 0 8px 25px rgba(99, 102, 241, 0.2) !important;
  transform: translateY(-2px);
}

/* Cards */
.card, .post, .metric, .ev-card, .user-profile-card,
.member-panel, div[data-testid="stForm"] {
  background: linear-gradient(145deg, var(--card), rgba(30, 41, 59, 0.72)) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-xl) !important;
  box-shadow: 0 20px 65px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(18px);
  transition: all 0.35s cubic-bezier(0.18, 0.89, 0.32, 1.28) !important;
  transform-style: preserve-3d;
  position: relative;
}

.card:hover, .post:hover, .metric:hover, .ev-card:hover,
.user-profile-card:hover, .member-panel:hover, div[data-testid="stForm"]:hover {
  transform: translateY(-7px) scale(1.015) !important;
  border-color: rgba(99, 102, 241, 0.45) !important;
  box-shadow: 0 30px 95px rgba(0, 0, 0, 0.52), 0 0 45px rgba(99, 102, 241, 0.18) !important;
}

/* Metrics */
.metric {
  padding: 1.6rem 1.8rem !important;
  text-align: center;
}

.metric .val {
  font-size: 2.6rem;
  font-weight: 900;
  color: var(--text-primary);
  font-family: 'Space Grotesk', sans-serif;
  transition: transform 0.3s ease;
}

.metric:hover .val {
  transform: scale(1.05);
}

.metric .lbl {
  font-size: 0.82rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  margin-top: 0.5rem;
}

/* Section header */
.sh {
  width: 100%;
  min-height: 120px;
  margin: 0 0 1.7rem !important;
  padding: 1.6rem 2rem;
  border-radius: var(--radius-xl);
  border: 1px solid rgba(129, 140, 248, 0.25);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(8, 47, 73, 0.7)),
              radial-gradient(circle at 10% 0%, rgba(6, 182, 212, 0.25), transparent 40%),
              radial-gradient(circle at 90% 40%, rgba(99, 102, 241, 0.28), transparent 38%);
  box-shadow: 0 30px 85px rgba(2, 6, 23, 0.48), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1.3rem;
  align-items: center;
}

.sh-icon {
  width: 72px;
  height: 72px;
  border-radius: 22px;
  display: grid;
  place-items: center;
  color: white;
  font-size: 2rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.98), rgba(6, 182, 212, 0.9));
  box-shadow: 0 20px 45px rgba(6, 182, 212, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.22);
  transition: all 0.3s ease;
}

.sh:hover .sh-icon {
  transform: rotate(8deg) scale(1.1);
}

.sh-title {
  margin: 0;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2rem;
  font-weight: 900;
  color: var(--text-primary);
  letter-spacing: -0.04em;
}

.sh-sub {
  margin-top: 0.45rem;
  color: var(--text-secondary);
  font-size: 0.98rem;
  line-height: 1.55;
}

/* Chat bubbles */
.bme {
  background: linear-gradient(135deg, var(--primary), #4f46e5) !important;
  color: white !important;
  padding: 1.1rem 1.5rem;
  border-radius: 24px 24px 6px 24px;
  margin: 0.7rem 0;
  max-width: 75%;
  margin-left: auto;
  box-shadow: 0 14px 40px rgba(99, 102, 241, 0.35) !important;
  transition: transform 0.25s ease;
}

.bme:hover {
  transform: translateX(-4px) scale(1.01);
}

.bother {
  background: rgba(15, 23, 42, 0.96) !important;
  color: var(--text-primary) !important;
  padding: 1.1rem 1.5rem;
  border-radius: 24px 24px 24px 6px;
  margin: 0.7rem 0;
  max-width: 75%;
  border: 1px solid rgba(148, 163, 184, 0.22) !important;
  transition: transform 0.25s ease;
}

.bother:hover {
  transform: translateX(4px) scale(1.01);
}

/* Avatar */
.av, .member-row .av-sm {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  font-weight: 800;
  color: white;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  box-shadow: 0 12px 34px rgba(99, 102, 241, 0.3);
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.av:hover, .member-row .av-sm:hover {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 16px 40px rgba(99, 102, 241, 0.4);
}

.av-lg {
  width: 110px;
  height: 110px;
  font-size: 2.8rem;
}

/* Branding */
.brand {
  padding: 1.5rem 1.2rem 1.2rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
}

.brand-name {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.7rem;
  font-weight: 900;
  background: linear-gradient(135deg, #f8fafc, #818cf8 45%, #06b6d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  transition: transform 0.2s ease;
}

.brand:hover .brand-name {
  transform: scale(1.02);
}

/* Hero */
.hero-title {
  font-size: 3.8rem;
  font-weight: 900;
  font-family: 'Space Grotesk', sans-serif;
  background: linear-gradient(135deg, #6366f1, #06b6d4, #f472b6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0.6rem 0;
  line-height: 1.03;
  animation: heroPulse 6s ease-in-out infinite;
}

@keyframes heroPulse {
  0%, 100% { filter: drop-shadow(0 0 25px rgba(99,102,241,0.25)); }
  50% { filter: drop-shadow(0 0 40px rgba(6,182,212,0.35)); }
}

/* Badge */
.badge {
  display: inline-block;
  background: rgba(6, 182, 212, 0.2);
  color: #a5f3fc;
  border: 1px solid rgba(6, 182, 212, 0.35);
  padding: 0.2rem 0.8rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  transition: all 0.25s ease;
}

.badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(6, 182, 212, 0.25);
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 9px;
  height: 9px;
}

::-webkit-scrollbar-track {
  background: rgba(2, 6, 23, 0.7);
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #6366f1, #06b6d4);
  border-radius: 999px;
  transition: all 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  transform: scale(1.1);
  background: linear-gradient(180deg, #818cf8, #22d3ee);
}

/* Header */
header[data-testid="stHeader"] {
  background: transparent !important;
  height: auto !important;
}

button[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarCollapsedControl"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] button {
  visibility: visible !important;
  display: flex !important;
  opacity: 1 !important;
  background: rgba(15, 23, 42, 0.85) !important;
  border: 1px solid rgba(148, 163, 184, 0.28) !important;
  border-radius: 14px !important;
  box-shadow: 0 10px 30px rgba(2, 6, 23, 0.45) !important;
  color: #a5b4fc !important;
  z-index: 999999 !important;
  transition: all 0.3s ease;
}

button[data-testid="stSidebarCollapseButton"]:hover,
button[data-testid="stSidebarCollapsedControl"]:hover {
  transform: scale(1.1);
  box-shadow: 0 14px 40px rgba(99,102,241,0.25);
}

/* File uploader */
.stFileUploader > div > div > div > div {
  background: rgba(15, 23, 42, 0.85) !important;
  border: 2px dashed rgba(148, 163, 184, 0.3) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--text-secondary) !important;
  transition: all 0.3s ease;
}

.stFileUploader > div > div > div > div:hover {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.16), 0 10px 35px rgba(99, 102, 241, 0.12) !important;
  transform: translateY(-2px);
}

/* Cube animation */
.cube-stage {
  width: 100%;
  height: 270px;
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 1400px;
  margin: 1rem 0 1.6rem;
}

.cube {
  position: relative;
  width: 150px;
  height: 150px;
  transform-style: preserve-3d;
  animation: cubeSpin 16s linear infinite;
}

@keyframes cubeSpin {
  0% { transform: rotateX(-22deg) rotateY(0deg); }
  100% { transform: rotateX(-22deg) rotateY(360deg); }
}

.cube-face {
  position: absolute;
  width: 150px;
  height: 150px;
  background: linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.94));
  border: 1px solid rgba(129, 140, 248, 0.35);
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 9px;
  box-shadow: 0 0 50px rgba(99, 102, 241, 0.18), inset 0 0 0 1px rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}

.cube-face .ico {
  font-size: 2.6rem;
  filter: drop-shadow(0 0 12px rgba(6, 182, 212, 0.6));
}

.cube-face .lbl {
  font-size: 0.74rem;
  color: #a5f3fc;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-weight: 700;
}

.cube-face.front  { transform: translateZ(75px); }
.cube-face.back   { transform: rotateY(180deg) translateZ(75px); }
.cube-face.right  { transform: rotateY(90deg) translateZ(75px); }
.cube-face.left   { transform: rotateY(-90deg) translateZ(75px); }
.cube-face.top    { transform: rotateX(90deg) translateZ(75px); }
.cube-face.bottom { transform: rotateX(-90deg) translateZ(75px); }

/* Radio group */
div[role="radiogroup"] {
  background: rgba(15, 23, 42, 0.78);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 20px;
  padding: 0.6rem;
  margin-bottom: 1rem;
}

div[role="radiogroup"] label {
  border-radius: 14px;
  padding: 0.6rem 1rem;
  transition: all 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
}

div[role="radiogroup"] label:hover {
  background: rgba(99, 102, 241, 0.22);
  transform: translateY(-2px);
}

/* Expander */
div[data-testid="stExpander"] {
  background: rgba(15, 23, 42, 0.75) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  border-radius: var(--radius-lg) !important;
  transition: all 0.3s ease;
}

div[data-testid="stExpander"]:hover {
  border-color: rgba(99,102,241,0.3);
  transform: translateY(-2px);
}

/* Post border */
.post {
  cursor: default;
}

.post::before {
  width: 4px;
  background: linear-gradient(180deg, var(--primary), var(--secondary));
  border-radius: 4px 0 0 4px;
  left: 0;
  top: 0;
  bottom: 0;
  content: '';
  position: absolute;
}

/* Hide Streamlit default elements */
#MainMenu, footer, .stDeployButton {
  visibility: hidden !important;
  display: none !important;
}

/* Responsive */
@media (max-width: 900px) {
  .main .block-container {
    padding: 1.4rem 1rem 2.3rem !important;
  }
  
  .sh {
    padding: 1.3rem 1.2rem;
  }
  
  .sh-title {
    font-size: 1.6rem;
  }
  
  .stTabs [data-baseweb="tab-list"] {
    grid-template-columns: 1fr !important;
  }
  
  .hero-title {
    font-size: 2.4rem;
  }
}

/* ============================================================
   PREMIUM UPGRADE LAYER — adds missing component styles and a
   deep layer of polish on top of the base theme above. Nothing
   from the original design is removed; everything here enhances
   or completes it.
   ============================================================ */

/* Crisper global typography rendering */
html, body, .stApp {
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
  text-rendering: optimizeLegibility !important;
}

/* Elegant text selection */
::selection {
  background: rgba(99, 102, 241, 0.38);
  color: #ffffff;
}

/* Gentle entrance for the whole main view */
.main .block-container {
  animation: viewFadeIn 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes viewFadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Second animated aurora layer for extra depth */
.stApp::after {
  content: '';
  position: fixed;
  inset: -20%;
  background:
    radial-gradient(circle at 65% 15%, rgba(244, 114, 182, 0.07), transparent 40%),
    radial-gradient(circle at 25% 85%, rgba(99, 102, 241, 0.07), transparent 42%);
  animation: bgShift 18s ease-in-out infinite reverse;
  pointer-events: none;
  z-index: 0;
}

/* Make sure real content sits above the animated background */
.main .block-container, section[data-testid="stSidebar"] {
  position: relative;
  z-index: 1;
}

/* ---- Animated gradient border halo on cards ---- */
.card, .post, .metric, .ev-card, .user-profile-card,
.member-panel, div[data-testid="stForm"] {
  isolation: isolate;
}

.card::after, .post::after, .metric::after, .ev-card::after,
.user-profile-card::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(135deg, rgba(129, 140, 248, 0.55), rgba(6, 182, 212, 0.0) 40%, rgba(244, 114, 182, 0.0) 60%, rgba(6, 182, 212, 0.45));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.4s ease;
  pointer-events: none;
}

.card:hover::after, .post:hover::after, .metric:hover::after,
.ev-card:hover::after, .user-profile-card:hover::after {
  opacity: 1;
}

/* Richer metric value with gradient text + glow */
.metric .val {
  background: linear-gradient(135deg, #f8fafc, #818cf8 55%, #22d3ee);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 4px 18px rgba(99, 102, 241, 0.25));
}

/* Stronger button gradient + glow polish. The gradient only animates
   on hover (not continuously on every button) to keep the page light. */
.stButton > button {
  background-size: 180% 180% !important;
  background-image: linear-gradient(135deg, #6366f1, #06b6d4 55%, #818cf8) !important;
}

.stButton > button:hover {
  animation: btnGradient 4s ease infinite;
}

@keyframes btnGradient {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* Section header subtle animated shimmer line */
.sh {
  overflow: hidden;
}

.sh::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(129, 140, 248, 0.9), rgba(34, 211, 238, 0.9), transparent);
  background-size: 200% 100%;
  animation: shShimmer 4s linear infinite;
}

@keyframes shShimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ============================================================
   AVATAR WRAPPER + ONLINE / OFFLINE STATUS BADGES
   ============================================================ */
.av-wrap {
  position: relative;
  display: inline-flex;
  flex-shrink: 0;
}

.status-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 2.5px solid #0f172a;
  box-sizing: border-box;
  z-index: 2;
}

.status-badge.on {
  background: var(--success);
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.25), 0 0 10px rgba(16, 185, 129, 0.7);
  animation: statusPulse 2s ease-in-out infinite;
}

.status-badge.off {
  background: #64748b;
}

@keyframes statusPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.55), 0 0 10px rgba(16, 185, 129, 0.7); }
  50% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0), 0 0 14px rgba(16, 185, 129, 0.9); }
}

/* Inline "online now" pulsing dot used on profiles */
.online {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--success);
  margin-right: 0.45rem;
  box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6);
  animation: statusPulse 2s ease-in-out infinite;
}

.av-clickable {
  cursor: pointer;
}

.av-clickable:hover {
  transform: scale(1.08) rotate(4deg);
}

/* ============================================================
   MEMBER LIST + SIDEBAR LABELS / STATS
   ============================================================ */
.member-category {
  margin: 1.1rem 0 0.5rem;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--text-muted);
  padding-left: 0.2rem;
  border-left: 3px solid rgba(99, 102, 241, 0.5);
  padding-left: 0.6rem;
}

.sb-eyebrow {
  margin: 0.4rem 0 0.7rem;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--text-muted);
}

.sb-stat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.85rem;
  margin: 0.4rem 0;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(148, 163, 184, 0.12);
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
}

.sb-stat:hover {
  transform: translateX(4px);
  border-color: rgba(99, 102, 241, 0.4);
  background: rgba(30, 41, 59, 0.8);
}

.sb-stat .n {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 800;
  font-size: 1rem;
  background: linear-gradient(135deg, #818cf8, #22d3ee);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ============================================================
   AI CHAT BUBBLE META
   ============================================================ */
.bmeta, .bmeta-other {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-top: 0.45rem;
  opacity: 0.75;
}

.bmeta {
  color: rgba(255, 255, 255, 0.85);
}

.bmeta-other {
  color: var(--text-muted);
}

/* Animated typing-style entrance for AI bubbles */
.bme, .bother {
  animation: bubbleIn 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes bubbleIn {
  from { opacity: 0; transform: translateY(8px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ============================================================
   DISCORD-STYLE GROUPED CHAT MESSAGES
   ============================================================ */
.msg-group {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin: 0.55rem 0;
  padding: 0.35rem 0.4rem;
  border-radius: 16px;
  transition: background 0.25s ease;
  animation: bubbleIn 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.msg-group:hover {
  background: rgba(99, 102, 241, 0.05);
}

.msg-group.mine {
  flex-direction: row-reverse;
}

.msg-group-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
  max-width: 78%;
}

.msg-group.mine .msg-group-body {
  align-items: flex-end;
}

.msg-group-head {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.2rem;
}

.msg-group.mine .msg-group-head {
  flex-direction: row-reverse;
}

.msg-group-name {
  font-weight: 800;
  font-size: 0.9rem;
  color: var(--primary-light);
}

.msg-group.mine .msg-group-name {
  color: #c7d2fe;
}

.msg-group-time {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.msg-line {
  position: relative;
  padding: 0.6rem 0.95rem;
  margin: 0.18rem 0;
  border-radius: 18px 18px 18px 6px;
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.16);
  color: var(--text-primary);
  font-size: 0.92rem;
  line-height: 1.55;
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  box-shadow: 0 6px 20px rgba(2, 6, 23, 0.28);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.msg-line:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(2, 6, 23, 0.4);
}

.msg-group.mine .msg-line {
  background: linear-gradient(135deg, var(--primary), #4f46e5);
  border-color: transparent;
  border-radius: 18px 18px 6px 18px;
  color: #ffffff;
  box-shadow: 0 10px 30px rgba(99, 102, 241, 0.32);
}

.msg-time-hover {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  left: -3.4rem;
  font-size: 0.64rem;
  color: var(--text-muted);
  opacity: 0;
  transition: opacity 0.2s ease;
  white-space: nowrap;
  pointer-events: none;
}

.msg-group.mine .msg-time-hover {
  left: auto;
  right: -3.4rem;
}

.msg-line:hover .msg-time-hover {
  opacity: 1;
}

/* ============================================================
   HABIT PROGRESS BARS
   ============================================================ */
.hbar {
  margin-top: 0.75rem;
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: rgba(2, 6, 23, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.14);
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.4);
}

.hfill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--primary), var(--secondary), var(--primary-light));
  background-size: 200% 100%;
  animation: hfillShimmer 3s linear infinite;
  box-shadow: 0 0 14px rgba(99, 102, 241, 0.55);
  transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes hfillShimmer {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

/* ============================================================
   AUTH PAGE POLISH
   ============================================================ */
.auth-copy {
  color: var(--text-secondary);
  font-size: 0.92rem;
  line-height: 1.6;
  margin: 0.2rem 0 1rem;
  padding: 0.75rem 1rem;
  border-radius: 14px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.18);
  border-left: 3px solid var(--primary);
}

.auth-hero .hero-logo-img,
.hero-logo-img {
  filter: drop-shadow(0 12px 40px rgba(99, 102, 241, 0.45));
  animation: logoFloat 5s ease-in-out infinite;
}

.hero-logo-emoji {
  font-size: 3.2rem;
  display: inline-block;
  filter: drop-shadow(0 10px 30px rgba(99, 102, 241, 0.5));
  animation: logoFloat 5s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-8px) rotate(-2deg); }
}

.auth-product-card {
  position: relative;
  overflow: hidden;
}

.auth-product-card::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: conic-gradient(from 0deg, transparent, rgba(99, 102, 241, 0.12), transparent 30%);
  animation: cardSweep 9s linear infinite;
  pointer-events: none;
}

@keyframes cardSweep {
  to { transform: rotate(360deg); }
}

/* Code blocks (profile share link, invite codes) */
.stCode, pre, code {
  border-radius: 12px !important;
}

/* Radio (auth mode + filters) selected pill glow */
div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(6, 182, 212, 0.2));
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.25);
}

/* Spinner accent */
.stSpinner > div {
  border-top-color: var(--primary) !important;
}

/* Toast / alert refinements */
div[data-testid="stNotification"] {
  border-radius: var(--radius) !important;
  backdrop-filter: blur(14px);
  border: 1px solid rgba(148, 163, 184, 0.18) !important;
}

/* Container border refinement (sidebar user card etc.) */
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: var(--radius-lg) !important;
}

/* Caption polish */
.stCaption, [data-testid="stCaptionContainer"] {
  color: var(--text-muted) !important;
}

/* Slightly nicer markdown links */
.main a {
  color: var(--primary-light);
  text-decoration: none;
  transition: color 0.2s ease;
}

.main a:hover {
  color: var(--secondary);
  text-decoration: underline;
}

/* Reduced motion accessibility — only soften hover transitions.
   Signature looping visuals (the 3D cube, hero glow, floating logo,
   animated backgrounds and progress shimmers) are intentionally kept
   so the experience still feels alive. */
@media (prefers-reduced-motion: reduce) {
  .stButton > button,
  .card, .post, .metric, .ev-card, .user-profile-card,
  .av, .badge, .sb-stat, .msg-line, .msg-group {
    transition-duration: 0.001ms !important;
  }
}

/* Guarantee the 3D login cube always spins, regardless of any
   global motion overrides. */
.cube {
  animation: cubeSpin 16s linear infinite !important;
  transform-style: preserve-3d !important;
}

.cube-stage {
  perspective: 1400px !important;
}

/* ============================================================
   ✦ CREATIVE LAYER ✦ — bold, expressive flourishes layered on
   top of everything above. Pure aesthetics; no layout removed.
   ============================================================ */

/* Shifting multi-color gradient text for big headings */
.sh-title, .brand-name, .hero-title {
  background-size: 220% auto !important;
  background-image: linear-gradient(110deg, #818cf8, #22d3ee 30%, #f472b6 55%, #818cf8 80%) !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  animation: textFlow 8s linear infinite;
}

@keyframes textFlow {
  to { background-position: 220% center; }
}

/* Living gradient halo around posts + the form. Static (no animation)
   at rest; the flowing animation only kicks in on hover so dozens of
   posts don't each run a perpetual animation. */
.post::after, div[data-testid="stForm"]::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1.5px;
  background: linear-gradient(130deg, rgba(129,140,248,0.7), rgba(6,182,212,0.0) 35%, rgba(244,114,182,0.0) 65%, rgba(244,114,182,0.6));
  background-size: 250% 250%;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0.4;
  transition: opacity 0.4s ease;
  pointer-events: none;
}

.post:hover::after, div[data-testid="stForm"]:hover::after {
  opacity: 1;
  animation: haloFlow 7s ease infinite;
}

@keyframes haloFlow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* Rotating conic glow ring behind avatars */
.av-wrap::before {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #6366f1, #06b6d4, #f472b6, #6366f1);
  filter: blur(5px);
  opacity: 0;
  z-index: 0;
  transition: opacity 0.35s ease;
}

/* Spin only while hovered so the blur effect isn't composited for
   every avatar on the page continuously. */
.av-wrap:hover::before {
  opacity: 0.85;
  animation: ringSpin 6s linear infinite;
}

/* Keep the avatar itself above its glow ring */
.av-wrap .av {
  position: relative;
  z-index: 1;
}

@keyframes ringSpin {
  to { transform: rotate(360deg); }
}

/* Post images: framed, rounded, with a playful hover zoom + glow */
.post img, .msg-line img, .bother img, .bme img {
  border-radius: 16px !important;
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 14px 45px rgba(2, 6, 23, 0.5);
  transition: transform 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28), box-shadow 0.4s ease;
  cursor: zoom-in;
}

/* Let post media fill the card width (responsive) instead of sitting
   small on the left and leaving a large empty area. */
.post img {
  width: 100% !important;
  max-width: 520px !important;
  max-height: 460px !important;
  height: auto !important;
  object-fit: cover;
  margin-top: 0.6rem;
}

.post img:hover, .msg-line img:hover {
  transform: scale(1.04) rotate(-0.6deg);
  box-shadow: 0 22px 70px rgba(99, 102, 241, 0.4);
}

/* Animated gradient underline under markdown section subheadings */
.main h3 {
  position: relative;
  display: inline-block;
  padding-bottom: 0.25rem;
}

.main h3::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  height: 3px;
  width: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--primary), var(--secondary), transparent);
  background-size: 200% 100%;
  animation: hfillShimmer 4s linear infinite;
  transform-origin: left;
  transform: scaleX(0.4);
  transition: transform 0.4s ease;
}

.main h3:hover::after {
  transform: scaleX(1);
}

/* Reaction / small action buttons get a neon pop on hover */
.stButton > button:hover {
  filter: saturate(1.25) brightness(1.06);
}

/* Badge ("You", "New", "Verified") — glassy glow pill */
.badge {
  background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(6,182,212,0.25)) !important;
  color: #e0e7ff !important;
  border: 1px solid rgba(129,140,248,0.45) !important;
  box-shadow: 0 0 16px rgba(99,102,241,0.25);
  backdrop-filter: blur(6px);
}

/* Expander headers feel like interactive chips */
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] details > summary {
  font-weight: 700 !important;
  transition: color 0.25s ease, letter-spacing 0.25s ease;
}

div[data-testid="stExpander"]:hover summary {
  color: var(--primary-light) !important;
  letter-spacing: 0.01em;
}

/* Sidebar nav buttons: animated active glow bar */
section[data-testid="stSidebar"] .stButton > button {
  position: relative;
  overflow: hidden;
}

section[data-testid="stSidebar"] .stButton > button::after {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--primary), var(--secondary));
  transform: scaleY(0);
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
  border-radius: 0 4px 4px 0;
}

section[data-testid="stSidebar"] .stButton > button:hover::after {
  transform: scaleY(1);
}

/* Tabs: glowing animated indicator on the selected tab */
.stTabs [aria-selected="true"] {
  position: relative;
  box-shadow: 0 0 0 1px rgba(99,102,241,0.4) inset, 0 10px 30px rgba(99,102,241,0.28) !important;
}

/* Metric value: gentle breathing glow */
.metric:hover .val {
  filter: drop-shadow(0 4px 26px rgba(34, 211, 238, 0.55));
}

/* Chat bubbles: subtle floating sheen, animated on hover only */
.bme::after, .bother::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(120deg, transparent 40%, rgba(255,255,255,0.06) 50%, transparent 60%);
  background-size: 250% 100%;
  pointer-events: none;
}
.bme:hover::after, .bother:hover::after {
  animation: haloFlow 6s ease infinite;
}
.bme, .bother { position: relative; overflow: hidden; }

/* Event cards: animated colored accent bar pulse */
.ev-card {
  position: relative;
  overflow: hidden;
}

.ev-card::after {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
  background: inherit;
  filter: brightness(1.6);
  animation: accentPulse 2.6s ease-in-out infinite;
}

@keyframes accentPulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* Inputs get a soft inner glow when focused (extra creative pop) */
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.16),
              0 0 45px rgba(6, 182, 212, 0.22),
              inset 0 0 18px rgba(99, 102, 241, 0.12) !important;
}

/* Logout button — distinct danger-tinted treatment */
section[data-testid="stSidebar"] .stButton > button[kind],
section[data-testid="stSidebar"] .stButton:last-of-type > button {
  /* kept subtle to avoid overriding nav buttons unintentionally */
}
</style>
""", unsafe_allow_html=True)


def inject_theme_css():
    theme = st.session_state.get("theme_mode", "Midnight")
    if theme == "Ocean":
        st.markdown("""
        <style>
        :root{
          --primary: #06b6d4;
          --primary-light: #22d3ee;
          --bg0: #030712;
          --bg1: #0f172a;
          --card: rgba(15, 23, 42, 0.88);
        }
        </style>
        """, unsafe_allow_html=True)


def get_recovery_tokens_from_url():
    from streamlit_javascript import st_javascript
    raw_hash = st_javascript("window.parent.location.hash")
    if not isinstance(raw_hash, str):
        return "pending", None, None
    if "type=recovery" not in raw_hash:
        return "none", None, None
    from urllib.parse import parse_qs
    params = parse_qs(raw_hash.lstrip("#"))
    access_token = params.get("access_token", [None])[0]
    refresh_token = params.get("refresh_token", [None])[0]
    if not access_token:
        return "none", None, None
    return "found", access_token, refresh_token


def get_saved_auth_tokens_from_browser():
    from streamlit_javascript import st_javascript
    raw = st_javascript("""
    (() => {
        try {
            return window.parent.localStorage.getItem("lifehub_auth_tokens") || "";
        } catch (e) {
            return "";
        }
    })()
    """)
    if not isinstance(raw, str):
        return "pending", None, None
    if not raw:
        return "none", None, None
    try:
        import json
        data = json.loads(raw)
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        if access_token and refresh_token:
            return "found", access_token, refresh_token
    except Exception:
        pass
    return "none", None, None


def save_auth_tokens_to_browser():
    access_token = st.session_state.get("sb_access_token")
    refresh_token = st.session_state.get("sb_refresh_token")
    if not access_token or not refresh_token:
        return
    auth_key = f"{access_token[:16]}|{refresh_token[:16]}"
    if st.session_state.get("_browser_auth_saved_key") == auth_key:
        return
    import json
    payload = json.dumps({
        "access_token": access_token,
        "refresh_token": refresh_token,
    })
    st.components.v1.html(
        f"""
        <script>
        try {{
            window.parent.localStorage.setItem("lifehub_auth_tokens", {json.dumps(payload)});
        }} catch (e) {{}}
        </script>
        """,
        height=0,
    )
    st.session_state["_browser_auth_saved_key"] = auth_key


def clear_auth_tokens_from_browser():
    st.components.v1.html(
        """
        <script>
        try {
            window.parent.localStorage.removeItem("lifehub_auth_tokens");
        } catch (e) {}
        </script>
        """,
        height=0,
    )


def restore_login_from_saved_tokens() -> str:
    status, access_token, refresh_token = get_saved_auth_tokens_from_browser()
    if status != "found":
        return status
    try:
        st.session_state.sb_access_token = access_token
        st.session_state.sb_refresh_token = refresh_token
        sb = get_sb()
        user_res = sb.auth.get_user()
        auth_user = getattr(user_res, "user", None)
        if not auth_user:
            return "invalid"
        prof = sb.table("profiles").select("*").eq("id", auth_user.id).limit(1).execute()
        if not prof.data:
            return "invalid"
        user = prof.data[0]
        if user.get("is_banned"):
            return "invalid"
        set_current_user_session(user)
        st.session_state.viewing_user = None
        st.session_state["_auth_transition"] = False
        return "restored"
    except Exception:
        return "invalid"


def get_user_profile(user_id):
    def load():
        sb = get_sb()
        result = sb.table("profiles").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None
    return session_cache_get(f"profile_{user_id}", 30, load)


def get_user_by_username(username):
    if not username:
        return None
    def load():
        try:
            sb = get_sb()
            result = sb.table("profiles").select("*").eq("username", username).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    return session_cache_get(f"profile_username_{username}", 30, load)


GROQ_MODEL_CANDIDATES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
]


def call_groq(messages, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_error = None
    for model in GROQ_MODEL_CANDIDATES:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        try:
            resp = requests.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=headers, json=payload, timeout=30,
            )
        except requests.RequestException as e:
            last_error = f"Network error contacting Groq ({model}): {e}"
            continue
        if resp.status_code == 200:
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return "Error: Could not parse response content from Groq."
        if resp.status_code in (404, 400):
            last_error = f"Groq API Error ({resp.status_code}) for model '{model}': {resp.text}"
            continue
        return f"Groq API Error ({resp.status_code}): {resp.text}"
    return f"Groq API Error: all model candidates failed. Last error: {last_error}"


PAGE_SUBTITLES = {
    "Home Feed": "Publish updates, discover your community, react to posts, and jump into member profiles.",
    "Discover": "Search members, follow people, open public profiles, and grow your workspace network.",
    "Notifications": "Review follows, mentions, comments, reactions, messages, and workspace alerts.",
    "AI Assistant": "Ask questions, draft ideas, and get fast help without leaving your workspace.",
    "Live Chat": "Private conversations with unread badges, attachments, mentions, search, and typing status.",
    "Calendar": "Plan upcoming events, meetings, reminders, and personal schedules in one clean view.",
    "Channels": "Team spaces for group chat, file sharing, mentions, and public community rooms.",
    "Habit Tracker": "Track streaks, weekly progress, shared habits, and personal routines.",
    "My Profile": "Control your identity, avatar, bio, posts, and account presence.",
    "Admin Panel": "Moderate members, posts, channels, bans, and workspace access from one control center.",
}


def sh_header(icon, title):
    subtitle = PAGE_SUBTITLES.get(title, APP_TAGLINE)
    st.markdown(
        f"""
        <section class="sh">
          <div class="sh-icon">{icon}</div>
          <div>
            <h1 class="sh-title">{escape_html(title)}</h1>
            <div class="sh-sub">{escape_html(subtitle)}</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def card(html):
    st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)


def logo_img(size=80, css_class="hero-logo-img"):
    if LOGO_SRC:
        return f'<img src="{LOGO_SRC}" width="{size}" height="{size}" class="{css_class}" style="border-radius:20%;object-fit:contain;">'
    return f'<span class="hero-logo-emoji">🌙</span>'


def logo_small(size=32):
    if LOGO_SRC:
        return f'<img src="{LOGO_SRC}" width="{size}" height="{size}" style="border-radius:8px;object-fit:contain;vertical-align:middle;">'
    return "🌙"


def render_cube():
    faces = [
        ("front",  "🤖", "AI Chat"),
        ("back",   "💬", "Live Chat"),
        ("right",  "📅", "Calendar"),
        ("left",   "🏠", "Home"),
        ("top",    "✅", "Habits"),
        ("bottom", "👤", "Profile"),
    ]
    faces_html = "".join(
        f'<div class="cube-face {cls}"><span class="ico">{ico}</span><span class="lbl">{lbl}</span></div>'
        for cls, ico, lbl in faces
    )
    st.markdown(f"""
    <div class="cube-stage">
      <div class="cube">{faces_html}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# DB + Helpers
# ============================================================
def hp(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

import re as _re

def extract_mentions(text: str) -> list:
    return list(set(_re.findall(r'@(\w+)', text)))

def escape_html(value) -> str:
    return html.escape(str(value or ""), quote=True)

def safe_multiline(value) -> str:
    return escape_html(value).replace("\n", "<br>")

def avatar_html(username, avatar_url=None, size=36, extra_class=""):
    safe_initials = escape_html((username or "user")[:2].upper())
    cls = f"av {extra_class}".strip()
    style = f"width:{size}px;height:{size}px;font-size:{max(size * 0.24, 10):.0f}px;"
    if avatar_url and str(avatar_url).startswith("data:image"):
        safe_url = escape_html(avatar_url)
        inner = f'<img src="{safe_url}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">'
    else:
        inner = safe_initials
    return f'<div class="{cls}" style="{style}">{inner}</div>'

def avatar_wrap_html(username, avatar_url=None, size=36, online=None, extra_class=""):
    status = ""
    if online is not None:
        status_cls = "on" if online else "off"
        status = f'<span class="status-badge {status_cls}"></span>'
    return f'<div class="av-wrap">{avatar_html(username, avatar_url, size, extra_class)}{status}</div>'

def get_profiles_map(sb, user_ids):
    ids = list({uid for uid in user_ids if uid})
    if not ids:
        return {}
    cache_key = f"profiles_map_{hash(tuple(sorted(ids)))}"
    def load():
        try:
            rows = sb.table("profiles").select("id,username,avatar_url,is_verified,profile_badge").in_("id", ids).execute()
            return {row["id"]: row for row in (rows.data or [])}
        except Exception:
            return {}
    return session_cache_get(cache_key, 30, load)

def record_mentions(sb, text: str, source_type: str, source_id: str, created_by: str):
    usernames = extract_mentions(text)
    if not usernames:
        return
    try:
        matched = sb.table("profiles").select("id,username").in_("username", usernames).execute()
        for u in (matched.data or []):
            if u["id"] == created_by:
                continue
            sb.table("mentions").insert({
                "mentioned_user_id": u["id"],
                "source_type": source_type,
                "source_id": source_id,
                "created_by": created_by,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }, returning=ReturnMethod.minimal).execute()
            create_notification(
                sb,
                u["id"],
                created_by,
                "mention",
                "You were mentioned",
                f"Someone mentioned you in a {source_type.replace('_', ' ')}.",
                source_type,
                source_id,
            )
    except Exception:
        pass

def linkify_mentions(text: str) -> str:
    escaped = safe_multiline(text)
    return _re.sub(r'@(\w+)', r'<span style="color:var(--primary);font-weight:600;">@\1</span>', escaped)

def get_unread_mention_count(sb, user_id, source_type=None) -> int:
    def load():
        try:
            q = sb.table("mentions").select("id", count="exact").eq("mentioned_user_id", user_id).eq("is_read", False)
            if source_type:
                q = q.eq("source_type", source_type)
            r = q.execute()
            return r.count or 0
        except Exception:
            return 0
    return session_cache_get(f"mention_count_{user_id}_{source_type or 'all'}", 20, load)

def mark_mentions_read(sb, user_id, source_type=None):
    try:
        q = sb.table("mentions").update({"is_read": True}).eq("mentioned_user_id", user_id).eq("is_read", False)
        if source_type:
            q = q.eq("source_type", source_type)
        q.execute()
        session_cache_clear(f"mention_count_{user_id}")
    except Exception:
        pass

def check_rate_limit(action: str, limit: int = 6, seconds: int = 60) -> bool:
    key = f"rate_{action}"
    now = time.time()
    hits = [t for t in st.session_state.get(key, []) if now - t < seconds]
    if len(hits) >= limit:
        st.warning(f"Slow down a little. Try again in {int(seconds - (now - hits[0]))}s.")
        st.session_state[key] = hits
        return False
    hits.append(now)
    st.session_state[key] = hits
    return True

def create_notification(sb, user_id, actor_id, kind, title, body="", source_type=None, source_id=None):
    if not user_id or user_id == actor_id:
        return
    try:
        sb.table("notifications").insert({
            "user_id": user_id,
            "actor_id": actor_id,
            "kind": kind,
            "title": title,
            "body": body,
            "source_type": source_type,
            "source_id": source_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, returning=ReturnMethod.minimal).execute()
        session_cache_clear(f"notification_count_{user_id}")
        session_cache_clear(f"notifications_page_{user_id}")
    except Exception:
        pass

def get_unread_notification_count(sb, user_id) -> int:
    def load():
        try:
            r = sb.table("notifications").select("id", count="exact").eq("user_id", user_id).eq("is_read", False).execute()
            return r.count or 0
        except Exception:
            return 0
    return session_cache_get(f"notification_count_{user_id}", 20, load)

def follow_counts(sb, user_id):
    def load():
        try:
            followers = sb.table("user_follows").select("id", count="exact").eq("following_id", user_id).execute().count or 0
            following = sb.table("user_follows").select("id", count="exact").eq("follower_id", user_id).execute().count or 0
            return followers, following
        except Exception:
            return 0, 0
    return session_cache_get(f"follow_counts_{user_id}", 30, load)

def is_following(sb, follower_id, following_id) -> bool:
    try:
        r = sb.table("user_follows").select("id").eq("follower_id", follower_id).eq("following_id", following_id).limit(1).execute()
        return bool(r.data)
    except Exception:
        return False

def user_activity_counts(sb, user_id):
    def load():
        try:
            posts = sb.table("posts").select("id", count="exact").eq("user_id", user_id).execute().count or 0
            habits = sb.table("habits").select("id", count="exact").eq("user_id", user_id).execute().count or 0
            events = sb.table("events").select("id", count="exact").eq("user_id", user_id).execute().count or 0
            return posts, habits, events
        except Exception:
            return 0, 0, 0
    return session_cache_get(f"user_activity_counts_{user_id}", 30, load)

def user_sent_message_count(sb, user_id):
    def load():
        try:
            return sb.table("messages").select("id", count="exact").eq("sender_id", user_id).execute().count or 0
        except Exception:
            return 0
    return session_cache_get(f"user_sent_message_count_{user_id}", 30, load)

def report_target(sb, target_type, target_id, reason):
    if not reason or not reason.strip():
        st.error("Please enter a short reason.")
        return
    if not check_rate_limit("report", limit=3, seconds=120):
        return
    try:
        sb.table("reports").insert({
            "reporter_id": st.session_state.user_id,
            "target_type": target_type,
            "target_id": target_id,
            "reason": reason.strip()[:300],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        st.success("Report sent to admins.")
    except Exception as e:
        st.error(f"Could not send report: {e}")

def render_attachment_preview(url, name, file_type):
    if not url:
        return ""
    return render_attachment_html(url, name, file_type)

def ago(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z","+00:00")).replace(tzinfo=None)
        d  = datetime.now(timezone.utc).replace(tzinfo=None) - dt
        if d.seconds < 60: return "just now"
        if d.seconds < 3600: return f"{d.seconds//60}m ago"
        if d.days < 1: return f"{d.seconds//3600}h ago"
        return f"{d.days}d ago"
    except: return ""

def set_typing(sb, user_id, target_id):
    key = f"typing_heartbeat_{target_id}"
    now = time.time()
    if now - st.session_state.get(key, 0) < 2:
        return
    try:
        sb.table("typing_status").upsert({
            "user_id": user_id, "target_id": target_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="user_id,target_id").execute()
        st.session_state[key] = now
    except Exception:
        pass

def is_other_typing(sb, other_id, my_id):
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=4)).isoformat()
        r = sb.table("typing_status").select("updated_at").eq("user_id", other_id).eq("target_id", my_id).gte("updated_at", cutoff).execute()
        return bool(r.data)
    except Exception:
        return False

def file_to_data_uri(uploaded_file, max_dim=640) -> dict:
    try:
        name = uploaded_file.name
        ext = name.split(".")[-1].lower()
        if ext in ("png", "jpg", "jpeg", "gif", "webp"):
            img = Image.open(uploaded_file)
            img.thumbnail((max_dim, max_dim))
            buf = io.BytesIO()
            fmt = "PNG" if ext in ("png", "gif") else "JPEG"
            save_kwargs = {"optimize": True}
            if fmt == "JPEG":
                save_kwargs["quality"] = 75
            img.convert("RGB" if fmt == "JPEG" else "RGBA").save(buf, format=fmt, **save_kwargs)
            b64 = base64.b64encode(buf.getvalue()).decode()
            mime = "image/png" if fmt == "PNG" else "image/jpeg"
            return {"url": f"data:{mime};base64,{b64}", "name": name, "type": "image"}
        else:
            raw = uploaded_file.read()
            if len(raw) > 2 * 1024 * 1024:
                st.error("File too large — 2MB max.")
                return None
            b64 = base64.b64encode(raw).decode()
            return {"url": f"data:application/octet-stream;base64,{b64}", "name": name, "type": "file"}
    except Exception as e:
        st.error(f"Could not process file: {e}")
        return None

def render_attachment_html(file_url, file_name, file_type):
    if not file_url:
        return ""
    safe_name = escape_html(file_name or "attachment")
    if file_type == "image":
        return f'<img src="{file_url}" style="max-width:280px;max-height:280px;border-radius:10px;margin-top:.4rem;display:block;">'
    return (f'<a href="{file_url}" download="{safe_name}" '
            f'style="display:inline-flex;align-items:center;gap:.4rem;margin-top:.4rem;'
            f'background:rgba(99,102,241,0.12);padding:.4rem .8rem;border-radius:8px;'
            f'color:var(--primary);text-decoration:none;font-size:.85rem;">📎 {safe_name}</a>')

def get_unread_counts(sb, user_id):
    def load():
        try:
            rows = sb.table("messages").select("sender_id").eq("receiver_id", user_id).eq("is_read", False).execute()
            counts = {}
            for r in (rows.data or []):
                counts[r["sender_id"]] = counts.get(r["sender_id"], 0) + 1
            return counts
        except Exception:
            return {}
    return session_cache_get(f"dm_unread_{user_id}", 20, load)

def session_cache_get(key: str, ttl: int, loader):
    """Tiny per-user TTL cache; avoids cross-user RLS leaks from global caching."""
    now = time.time()
    cache = st.session_state.setdefault("_ttl_cache", {})
    # Periodically clean up old items (10% chance per call)
    if len(cache) > 50 and random.random() < 0.1:
        _cleanup_cache(cache, now)
    item = cache.get(key)
    if item and now - item["time"] < ttl:
        return item["value"]
    value = loader()
    cache[key] = {"time": now, "value": value}
    return value


def _cleanup_cache(cache, now):
    """Remove all expired items from cache."""
    expired_keys = [k for k, v in cache.items() if now - v["time"] > 300]  # Remove anything older than 5 mins
    for k in expired_keys:
        cache.pop(k, None)


def session_cache_clear(prefix: str = ""):
    cache = st.session_state.get("_ttl_cache", {})
    for k in list(cache.keys()):
        if not prefix or k.startswith(prefix):
            cache.pop(k, None)

def init_session_state():
    defaults = {
        "logged_in": False,
        "user": None,
        "user_id": None,
        "username": "",
        "page": "home",
        "viewing_user": None,
        "chat_target": None,
        "_ttl_cache": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

def set_current_user_session(user: dict):
    st.session_state.update({
        "user": user,
        "user_id": user["id"],
        "username": user.get("username", "user"),
        "logged_in": True,
        "_profile_loaded_at": time.time(),
    })
    session_cache_clear(f"profile_{user['id']}")
    session_cache_clear(f"profile_username_{user.get('username', '')}")

def refresh_current_user_session(sb, ttl: int = 300) -> bool:
    """Keep auth/profile info in session_state without querying every rerun."""
    if not st.session_state.get("logged_in") or not st.session_state.get("user_id"):
        return False
    if time.time() - st.session_state.get("_profile_loaded_at", 0) < ttl and st.session_state.get("user"):
        return True
    try:
        prof = sb.table("profiles").select("*").eq("id", st.session_state.user_id).limit(1).execute()
        if not prof.data:
            return False
        user = prof.data[0]
        if user.get("is_banned"):
            return False
        set_current_user_session(user)
        return True
    except Exception:
        return bool(st.session_state.get("user"))

def ensure_user_profile_saved(sb, auth_user_id, username, email, bio=""):
    """Fallback for new accounts if the Supabase trigger has not created profiles yet."""
    try:
        sb.table("profiles").upsert({
            "id": auth_user_id,
            "username": username,
            "email": email,
            "bio": (bio or "")[:200],
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="id", returning=ReturnMethod.minimal).execute()
        session_cache_clear("member_list_profiles")
        session_cache_clear("platform_stats")
    except Exception:
        pass

def get_sb() -> Client:
    url = get_config("SUPABASE_URL")
    key = get_config("SUPABASE_ANON_KEY") or get_config("SUPABASE_KEY")
    if not url or not key:
        st.error("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY. Add them to .env locally or Streamlit Secrets in the cloud.")
        st.stop()
    client_key = f"{url}|{key[:8]}"
    sb = st.session_state.get("_sb_client")
    if sb is None or st.session_state.get("_sb_client_key") != client_key:
        sb = create_client(url, key)
        st.session_state["_sb_client"] = sb
        st.session_state["_sb_client_key"] = client_key

    access_token = st.session_state.get("sb_access_token")
    refresh_token = st.session_state.get("sb_refresh_token")
    auth_key = f"{access_token[:16] if access_token else ''}|{refresh_token[:16] if refresh_token else ''}"
    if access_token and refresh_token and st.session_state.get("_sb_auth_key") != auth_key:
        try:
            session_res = sb.auth.set_session(access_token, refresh_token)
            if getattr(session_res, "session", None):
                st.session_state.sb_access_token = session_res.session.access_token
                st.session_state.sb_refresh_token = session_res.session.refresh_token
                auth_key = f"{session_res.session.access_token[:16]}|{session_res.session.refresh_token[:16]}"
            st.session_state["_sb_auth_key"] = auth_key
        except Exception:
            pass
    return sb

def get_platform_stats():
    """
    Lightweight counters used on the login page and sidebar.
    Kept uncached because RLS means anonymous and authenticated users can
    legitimately see different counts in the same browser session.
    """
    def load():
        sb = get_sb()
        member_count = post_count = msg_count = 0
        # Query each table independently so one blocked-by-RLS table
        # (e.g. messages for anonymous visitors) doesn't zero out the
        # others. A short fallback select is used when the exact count
        # header isn't returned for the current role.
        for table, attr in (("profiles", "member"), ("posts", "post"), ("messages", "msg")):
            try:
                res = sb.table(table).select("id", count="exact").execute()
                value = res.count
                if value is None:
                    value = len(res.data or [])
            except Exception:
                value = 0
            if attr == "member":
                member_count = value
            elif attr == "post":
                post_count = value
            else:
                msg_count = value
        return member_count, post_count, msg_count
    # Cache per-identity so the anonymous login-page counts never leak
    # into the authenticated sidebar (and vice versa).
    cache_id = st.session_state.get("user_id") or "anon"
    return session_cache_get(f"platform_stats_{cache_id}", 120, load)

def hp(p: str) -> str:
    # Deprecated: password hashing is now handled entirely by Supabase
    # Auth (see migrate_to_auth.sql). Kept only in case any legacy data
    # still references it; no longer called by login/register.
    return hashlib.sha256(p.encode()).hexdigest()

import re as _re

def extract_mentions(text: str) -> list:
    """Returns a list of usernames mentioned via @username in `text`."""
    return list(set(_re.findall(r'@(\w+)', text)))

def escape_html(value) -> str:
    return html.escape(str(value or ""), quote=True)

def safe_multiline(value) -> str:
    return escape_html(value).replace("\n", "<br>")

def avatar_html(username, avatar_url=None, size=36, extra_class=""):
    safe_initials = escape_html((username or "user")[:2].upper())
    cls = f"av {extra_class}".strip()
    style = f"width:{size}px;height:{size}px;font-size:{max(size * 0.24, 10):.0f}px;"
    if avatar_url and str(avatar_url).startswith("data:image"):
        safe_url = escape_html(avatar_url)
        inner = f'<img src="{safe_url}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">'
    else:
        inner = safe_initials
    return f'<div class="{cls}" style="{style}">{inner}</div>'

def avatar_wrap_html(username, avatar_url=None, size=36, online=None, extra_class=""):
    status = ""
    if online is not None:
        status_cls = "on" if online else "off"
        status = f'<span class="status-badge {status_cls}"></span>'
    return f'<div class="av-wrap">{avatar_html(username, avatar_url, size, extra_class)}{status}</div>'

def get_profiles_map(sb, user_ids):
    ids = list({uid for uid in user_ids if uid})
    if not ids:
        return {}
    cache_key = f"profiles_map_{hash(tuple(sorted(ids)))}"
    def load():
        try:
            rows = sb.table("profiles").select("id,username,avatar_url,is_verified,profile_badge").in_("id", ids).execute()
            return {row["id"]: row for row in (rows.data or [])}
        except Exception:
            return {}
    return session_cache_get(cache_key, 30, load)

def record_mentions(sb, text: str, source_type: str, source_id: str, created_by: str):
    """
    Looks up @username mentions in `text` against real profiles and
    inserts a `mentions` row for each match, so the mentioned user can
    see a "you were mentioned" notification.
    """
    usernames = extract_mentions(text)
    if not usernames:
        return
    try:
        matched = sb.table("profiles").select("id,username").in_("username", usernames).execute()
        for u in (matched.data or []):
            if u["id"] == created_by:
                continue  # don't notify yourself for self-mentions
            sb.table("mentions").insert({
                "mentioned_user_id": u["id"],
                "source_type": source_type,
                "source_id": source_id,
                "created_by": created_by,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }, returning=ReturnMethod.minimal).execute()
            create_notification(
                sb,
                u["id"],
                created_by,
                "mention",
                "You were mentioned",
                f"Someone mentioned you in a {source_type.replace('_', ' ')}.",
                source_type,
                source_id,
            )
    except Exception:
        pass

def linkify_mentions(text: str) -> str:
    """Escapes text, then wraps @username occurrences in a styled span."""
    escaped = safe_multiline(text)
    return _re.sub(r'@(\w+)', r'<span style="color:var(--primary);font-weight:600;">@\1</span>', escaped)

def get_unread_mention_count(sb, user_id, source_type=None) -> int:
    def load():
        try:
            q = sb.table("mentions").select("id", count="exact").eq("mentioned_user_id", user_id).eq("is_read", False)
            if source_type:
                q = q.eq("source_type", source_type)
            r = q.execute()
            return r.count or 0
        except Exception:
            return 0
    return session_cache_get(f"mention_count_{user_id}_{source_type or 'all'}", 20, load)

def mark_mentions_read(sb, user_id, source_type=None):
    try:
        q = sb.table("mentions").update({"is_read": True}).eq("mentioned_user_id", user_id).eq("is_read", False)
        if source_type:
            q = q.eq("source_type", source_type)
        q.execute()
        session_cache_clear(f"mention_count_{user_id}")
    except Exception:
        pass

def check_rate_limit(action: str, limit: int = 6, seconds: int = 60) -> bool:
    """Small per-session rate limiter for costly writes."""
    key = f"rate_{action}"
    now = time.time()
    hits = [t for t in st.session_state.get(key, []) if now - t < seconds]
    if len(hits) >= limit:
        st.warning(f"Slow down a little. Try again in {int(seconds - (now - hits[0]))}s.")
        st.session_state[key] = hits
        return False
    hits.append(now)
    st.session_state[key] = hits
    return True

def create_notification(sb, user_id, actor_id, kind, title, body="", source_type=None, source_id=None):
    if not user_id or user_id == actor_id:
        return
    try:
        sb.table("notifications").insert({
            "user_id": user_id,
            "actor_id": actor_id,
            "kind": kind,
            "title": title,
            "body": body,
            "source_type": source_type,
            "source_id": source_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, returning=ReturnMethod.minimal).execute()
        session_cache_clear(f"notification_count_{user_id}")
        session_cache_clear(f"notifications_page_{user_id}")
    except Exception:
        pass

def get_unread_notification_count(sb, user_id) -> int:
    def load():
        try:
            r = sb.table("notifications").select("id", count="exact").eq("user_id", user_id).eq("is_read", False).execute()
            return r.count or 0
        except Exception:
            return 0
    return session_cache_get(f"notification_count_{user_id}", 20, load)

def follow_counts(sb, user_id):
    def load():
        try:
            followers = sb.table("user_follows").select("id", count="exact").eq("following_id", user_id).execute().count or 0
            following = sb.table("user_follows").select("id", count="exact").eq("follower_id", user_id).execute().count or 0
            return followers, following
        except Exception:
            return 0, 0
    return session_cache_get(f"follow_counts_{user_id}", 30, load)

def is_following(sb, follower_id, following_id) -> bool:
    try:
        r = sb.table("user_follows").select("id").eq("follower_id", follower_id).eq("following_id", following_id).limit(1).execute()
        return bool(r.data)
    except Exception:
        return False

def user_activity_counts(sb, user_id):
    def load():
        try:
            posts = sb.table("posts").select("id", count="exact").eq("user_id", user_id).execute().count or 0
            habits = sb.table("habits").select("id", count="exact").eq("user_id", user_id).execute().count or 0
            events = sb.table("events").select("id", count="exact").eq("user_id", user_id).execute().count or 0
            return posts, habits, events
        except Exception:
            return 0, 0, 0
    return session_cache_get(f"user_activity_counts_{user_id}", 30, load)

def user_sent_message_count(sb, user_id):
    def load():
        try:
            return sb.table("messages").select("id", count="exact").eq("sender_id", user_id).execute().count or 0
        except Exception:
            return 0
    return session_cache_get(f"user_sent_message_count_{user_id}", 30, load)

def report_target(sb, target_type, target_id, reason):
    if not reason or not reason.strip():
        st.error("Please enter a short reason.")
        return
    if not check_rate_limit("report", limit=3, seconds=120):
        return
    try:
        sb.table("reports").insert({
            "reporter_id": st.session_state.user_id,
            "target_type": target_type,
            "target_id": target_id,
            "reason": reason.strip()[:300],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        st.success("Report sent to admins.")
    except Exception as e:
        st.error(f"Could not send report: {e}")

def render_attachment_preview(url, name, file_type):
    if not url:
        return ""
    return render_attachment_html(url, name, file_type)

def ago(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z","+00:00")).replace(tzinfo=None)
        d  = datetime.now(timezone.utc).replace(tzinfo=None) - dt
        if d.seconds < 60: return "just now"
        if d.seconds < 3600: return f"{d.seconds//60}m ago"
        if d.days < 1: return f"{d.seconds//3600}h ago"
        return f"{d.days}d ago"
    except: return ""

PAGE_SUBTITLES = {
    "Home Feed": "Publish updates, discover your community, react to posts, and jump into member profiles.",
    "Discover": "Search members, follow people, open public profiles, and grow your workspace network.",
    "Notifications": "Review follows, mentions, comments, reactions, messages, and workspace alerts.",
    "AI Assistant": "Ask questions, draft ideas, and get fast help without leaving your workspace.",
    "Live Chat": "Private conversations with unread badges, attachments, mentions, search, and typing status.",
    "Calendar": "Plan upcoming events, meetings, reminders, and personal schedules in one clean view.",
    "Channels": "Team spaces for group chat, file sharing, mentions, and public community rooms.",
    "Habit Tracker": "Track streaks, weekly progress, shared habits, and personal routines.",
    "My Profile": "Control your identity, avatar, bio, posts, and account presence.",
    "Admin Panel": "Moderate members, posts, channels, bans, and workspace access from one control center.",
}

def sh_header(icon, title):
    subtitle = PAGE_SUBTITLES.get(title, APP_TAGLINE)
    st.markdown(
        f"""
        <section class="sh">
          <div class="sh-icon">{icon}</div>
          <div>
            <h1 class="sh-title">{escape_html(title)}</h1>
            <div class="sh-sub">{escape_html(subtitle)}</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

def card(html):
    st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)

def logo_img(size=80, css_class="hero-logo-img"):
    if LOGO_SRC:
        return f'<img src="{LOGO_SRC}" width="{size}" height="{size}" class="{css_class}" style="border-radius:20%;object-fit:contain;">'
    return f'<span class="hero-logo-emoji">🌙</span>'

def logo_small(size=32):
    if LOGO_SRC:
        return f'<img src="{LOGO_SRC}" width="{size}" height="{size}" style="border-radius:8px;object-fit:contain;vertical-align:middle;">'
    return "🌙"

def render_cube():
    """
    Render the signature 3D rotating cube for the login page.
    Six faces, each representing a core LifeHub module.
    Pure CSS — no canvas/WebGL, so it renders reliably inside
    Streamlit's HTML sandbox with no extra dependencies.
    """
    faces = [
        ("front",  "🤖", "AI Chat"),
        ("back",   "💬", "Live Chat"),
        ("right",  "📅", "Calendar"),
        ("left",   "🏠", "Home"),
        ("top",    "✅", "Habits"),
        ("bottom", "👤", "Profile"),
    ]
    faces_html = "".join(
        f'<div class="cube-face {cls}"><span class="ico">{ico}</span><span class="lbl">{lbl}</span></div>'
        for cls, ico, lbl in faces
    )
    st.markdown(f"""
    <div class="cube-stage">
      <div class="cube">{faces_html}</div>
    </div>
    """, unsafe_allow_html=True)

def inject_theme_css():
    theme = st.session_state.get("theme_mode", "Midnight")
    if theme == "Ocean":
        st.markdown("""
        <style>
        :root{
          --bg:#031525; --bg2:#082f49; --card:rgba(8,47,73,.82);
          --primary:#38bdf8; --primary-light:#0ea5e9; --primary-light:#0284c7; --secondary:#7dd3fc;
          --primary:rgba(14,165,233,.32);
        }
        html, body, .stApp {
          background:
            radial-gradient(circle at 12% 8%, rgba(14,165,233,.28), transparent 28%),
            radial-gradient(circle at 88% 12%, rgba(59,130,246,.20), transparent 30%),
            linear-gradient(135deg, #031525, #082f49 48%, #0f172a 100%) !important;
        }
        section[data-testid="stSidebar"] {
          background: linear-gradient(180deg, rgba(3,21,37,.98), rgba(8,47,73,.96)) !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        :root{
          --bg:#070b18; --bg2:#0f172a; --card:rgba(15,23,42,.78);
          --primary:#5865F2; --primary-light:#4752C4; --primary-light:#3C45A5; --secondary:#7C83FF;
          --primary:rgba(88,101,242,.30);
        }
        html, body, .stApp {
          background:
            radial-gradient(circle at 12% 8%, rgba(88,101,242,.20), transparent 28%),
            radial-gradient(circle at 88% 12%, rgba(124,58,237,.16), transparent 30%),
            linear-gradient(135deg, #070b18, #0f172a 55%, #050816 100%) !important;
        }
        section[data-testid="stSidebar"] {
          background: linear-gradient(180deg, rgba(5,8,22,.98), rgba(8,13,31,.96)) !important;
        }
        </style>
        """, unsafe_allow_html=True)

def get_recovery_tokens_from_url():
    """
    Supabase's password-reset email link redirects the browser with
    the session tokens in the URL *fragment*
    (#access_token=...&type=recovery), which only JavaScript can read
    — a Python/Streamlit server never sees it (browsers don't send
    URL fragments in HTTP requests at all). That's why the app was
    previously falling through to the normal login page instead of
    showing a reset form: nothing ever looked at the fragment.

    Uses streamlit-javascript's st_javascript(), which runs JS in the
    browser and returns the result directly back into this Python
    script run (no reload/redirect race, unlike the earlier approach
    that tried to rewrite the URL and force a reload — that round-trip
    never reliably fired).

    Returns one of:
      ("pending", None, None)   — JS hasn't returned a result yet;
                                   caller should show a brief loading
                                   state and let the component's own
                                   rerun resolve this on the next pass.
      ("none", None, None)      — confirmed not a recovery link visit.
      ("found", access, refresh) — recovery tokens extracted.
    """
    from streamlit_javascript import st_javascript

    raw_hash = st_javascript("window.parent.location.hash")

    # st_javascript returns 0 (not a string) while the JS call is
    # still in flight on the browser side.
    if not isinstance(raw_hash, str):
        return "pending", None, None

    if "type=recovery" not in raw_hash:
        return "none", None, None

    params = parse_qs(raw_hash.lstrip("#"))
    access_token = params.get("access_token", [None])[0]
    refresh_token = params.get("refresh_token", [None])[0]

    if not access_token:
        return "none", None, None

    return "found", access_token, refresh_token

def get_saved_auth_tokens_from_browser():
    """Read persisted Supabase tokens from browser localStorage."""
    from streamlit_javascript import st_javascript

    raw = st_javascript("""
    (() => {
      try {
        return window.parent.localStorage.getItem("lifehub_auth_tokens") || "";
      } catch (e) {
        return "";
      }
    })()
    """)
    if not isinstance(raw, str):
        return "pending", None, None
    if not raw:
        return "none", None, None
    try:
        data = json.loads(raw)
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        if access_token and refresh_token:
            return "found", access_token, refresh_token
    except Exception:
        pass
    return "none", None, None

def save_auth_tokens_to_browser():
    """Persist current Supabase tokens so refresh/reopen keeps the user logged in."""
    access_token = st.session_state.get("sb_access_token")
    refresh_token = st.session_state.get("sb_refresh_token")
    if not access_token or not refresh_token:
        return
    auth_key = f"{access_token[:16]}|{refresh_token[:16]}"
    if st.session_state.get("_browser_auth_saved_key") == auth_key:
        return

    from streamlit_javascript import st_javascript

    payload = json.dumps({
        "access_token": access_token,
        "refresh_token": refresh_token,
    })
    st.components.v1.html(
        f"""
        <script>
        try {{
          window.parent.localStorage.setItem("lifehub_auth_tokens", {json.dumps(payload)});
        }} catch (e) {{}}
        </script>
        """,
        height=0,
    )
    st.session_state["_browser_auth_saved_key"] = auth_key

def clear_auth_tokens_from_browser():
    st.components.v1.html(
        """
        <script>
        try {
          window.parent.localStorage.removeItem("lifehub_auth_tokens");
        } catch (e) {}
        </script>
        """,
        height=0,
    )

def restore_login_from_saved_tokens() -> str:
    """Return pending/restored/none/invalid for persisted browser login."""
    status, access_token, refresh_token = get_saved_auth_tokens_from_browser()
    if status != "found":
        return status
    try:
        st.session_state.sb_access_token = access_token
        st.session_state.sb_refresh_token = refresh_token
        sb = get_sb()
        user_res = sb.auth.get_user()
        auth_user = getattr(user_res, "user", None)
        if not auth_user:
            return "invalid"
        prof = sb.table("profiles").select("*").eq("id", auth_user.id).limit(1).execute()
        if not prof.data:
            return "invalid"
        user = prof.data[0]
        if user.get("is_banned"):
            return "invalid"
        set_current_user_session(user)
        st.session_state.viewing_user = None
        st.session_state["_auth_transition"] = False
        return "restored"
    except Exception:
        return "invalid"

def get_user_profile(user_id):
    def load():
        sb = get_sb()
        result = sb.table("profiles").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None
    return session_cache_get(f"profile_{user_id}", 30, load)

def get_user_by_username(username):
    if not username:
        return None
    def load():
        try:
            sb = get_sb()
            result = sb.table("profiles").select("*").eq("username", username).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    return session_cache_get(f"profile_username_{username}", 30, load)

# ── Groq AI ──────────────────────────────────────────────
# ── Groq Chat Completions Helper (OpenAI-compatible) ────────

# Groq retires/renames models periodically — try the best one first,
# fall back automatically so chat never hard-fails on a stale model id.
GROQ_MODEL_CANDIDATES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
]

def call_groq(messages, api_key):
    """
    Sends a chat-style message list to Groq's OpenAI-compatible endpoint.
    `messages` is a list of {"role": "user"|"assistant"|"system", "content": str}.
    Tries each candidate model in order until one succeeds.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = None
    for model in GROQ_MODEL_CANDIDATES:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        try:
            resp = requests.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=headers, json=payload, timeout=30,
            )
        except requests.RequestException as e:
            last_error = f"Network error contacting Groq ({model}): {e}"
            continue

        if resp.status_code == 200:
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return "Error: Could not parse response content from Groq."

        if resp.status_code in (404, 400):
            # Model retired/invalid — try next candidate.
            last_error = f"Groq API Error ({resp.status_code}) for model '{model}': {resp.text}"
            continue

        # Auth/quota/other errors — no point trying other models.
        return f"Groq API Error ({resp.status_code}): {resp.text}"

    return f"Groq API Error: all model candidates failed. Last error: {last_error}"


# ============================================================
# AUTH PAGE — Premium Design
# ============================================================
def reset_password_page():
    """
    Dedicated page shown when the user arrives via the email recovery
    link. Tokens were extracted client-side from the URL fragment by
    get_recovery_tokens_from_url() and stashed in session_state by
    main(). Establishes the short-lived recovery session Supabase
    issued, then lets the user set a new password — this is the
    actual "click link -> type new password" flow.
    """
    sb = get_sb()

    st.markdown(f"""
    <div style="text-align:center;padding:2rem 0 1rem;">
      {logo_img(80)}
      <h2 style="font-family:'Space Grotesk',sans-serif;color:var(--primary);margin:.5rem 0;">Set a new password</h2>
      <p style="color:var(--text-secondary);">You're verified — choose a new password below.</p>
    </div>
    """, unsafe_allow_html=True)

    access_token  = st.session_state.get("recovery_access_token", "")
    refresh_token = st.session_state.get("recovery_refresh_token", "")

    def _back_to_login():
        for k in ("recovery_access_token", "recovery_refresh_token", "recovery_check_done"):
            st.session_state.pop(k, None)
        st.rerun()

    if not access_token:
        st.error("This reset link is invalid or missing required data. Please request a new one.")
        if st.button("← Back to login"):
            _back_to_login()
        return

    col = st.columns([1, 2, 1])[1]
    with col:
        try:
            sb.auth.set_session(access_token, refresh_token)
        except Exception as e:
            st.error(f"This reset link is invalid or has expired. Please request a new one. ({e})")
            if st.button("← Back to login"):
                _back_to_login()
            return

        with st.form("set_new_pw_f"):
            new_pw  = st.text_input("New password", type="password", placeholder="Minimum 6 characters")
            new_pw2 = st.text_input("Confirm new password", type="password")
            submitted = st.form_submit_button("🔓 Update Password", use_container_width=True)

        if submitted:
            if not new_pw:
                st.error("Please enter a new password.")
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_pw != new_pw2:
                st.error("Passwords do not match.")
            else:
                try:
                    sb.auth.update_user({"password": new_pw})
                    sb.auth.sign_out()
                    st.success("✅ Password updated! You can now sign in with your new password.")
                    if st.button("Continue to Sign In →", use_container_width=True):
                        _back_to_login()
                except Exception as e:
                    st.error(f"Could not update password: {e}")


def auth_page():
    sb = get_sb()

    if st.session_state.get("_auth_transition"):
        st.markdown(f"""
        <div style="text-align:center;padding:4rem 0;">
          {logo_img(70)}
          <p style="color:var(--text-muted);margin-top:1rem;">Opening your workspace...</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Full width hero with logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="auth-hero" style="text-align:center;padding:1rem 0 1.5rem;">
          {logo_img(100)}
          <h1 class="hero-title" style="font-size:3.5rem;font-weight:900;font-family:'Space Grotesk',sans-serif;
            background:linear-gradient(135deg, #5865F2, #3C45A5);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            margin:0.5rem 0;">
            LifeHub
          </h1>
          <p style="color:var(--text-secondary);font-size:1.05rem;margin:0;">{APP_TAGLINE}</p>
          <p style="color:var(--text-muted);font-size:0.85rem;margin-top:0.3rem;">Secure social tools, AI support, habits, events, and team channels</p>
        </div>
        """, unsafe_allow_html=True)

    # Two column layout with better styling
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        auth_mode = st.radio(
            "Account action",
            ["Sign In", "Create Account", "Forgot Password"],
            horizontal=True,
            label_visibility="collapsed",
            key="auth_mode_selector",
        )

        if auth_mode == "Sign In":
            st.markdown("<div class='auth-copy'>Welcome back. Sign in securely with Supabase Auth.</div>", unsafe_allow_html=True)
            with st.form("lf", clear_on_submit=False):
                u = st.text_input("Email", placeholder="you@email.com", key="login_user")
                p = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
                ok = st.form_submit_button(
                    "Sign In",
                    use_container_width=True,
                    disabled=st.session_state.get("_auth_busy", False),
                )

            if ok:
                st.session_state["_auth_busy"] = True
                if not check_rate_limit("login", limit=8, seconds=120):
                    st.session_state["_auth_busy"] = False
                    return
                if not u or not p:
                    st.session_state["_auth_busy"] = False
                    st.error("Please fill all fields.")
                    st.stop()
                try:
                    auth_res = sb.auth.sign_in_with_password({"email": u.strip(), "password": p})
                except Exception:
                    st.session_state["_auth_busy"] = False
                    st.error("Invalid email or password.")
                    st.stop()
                if auth_res and auth_res.user:
                    if getattr(auth_res, "session", None):
                        st.session_state.sb_access_token = auth_res.session.access_token
                        st.session_state.sb_refresh_token = auth_res.session.refresh_token
                        try:
                            sb.auth.set_session(auth_res.session.access_token, auth_res.session.refresh_token)
                        except Exception:
                            pass
                    prof = sb.table("profiles").select("*").eq("id", auth_res.user.id).execute()
                    if not prof.data:
                        st.session_state["_auth_busy"] = False
                        st.error("Account exists but has no profile yet. Run the latest schema.sql in Supabase.")
                        st.stop()
                    user = prof.data[0]
                    if user.get("is_banned"):
                        sb.auth.sign_out()
                        st.session_state["_auth_busy"] = False
                        st.error("Your account has been banned. Contact support if you believe this is an error.")
                        st.stop()
                    set_current_user_session(user)
                    st.session_state.viewing_user = None
                    sb.table("profiles").update({"last_seen": datetime.now(timezone.utc).isoformat()}).eq("id", user["id"]).execute()
                    session_cache_clear("member_list_profiles")
                    save_auth_tokens_to_browser()
                    st.session_state["_auth_transition"] = True
                    st.session_state["_auth_busy"] = False
                    st.rerun()
                else:
                    st.session_state["_auth_busy"] = False
                    st.error("Invalid email or password.")
                    st.stop()

        elif auth_mode == "Create Account":
            st.markdown("<div class='auth-copy'>Create a workspace identity. Your account is managed by Supabase Auth.</div>", unsafe_allow_html=True)
            with st.form("rf", clear_on_submit=True):
                nu = st.text_input("Choose a username", placeholder="cool_username", key="reg_user")
                ne = st.text_input("Email address", placeholder="you@email.com", key="reg_email")
                nb = st.text_area("Tell us about yourself", placeholder="Write a short bio...", max_chars=200, key="reg_bio")
                np1 = st.text_input("Create password", type="password", placeholder="Minimum 6 characters", key="reg_pass1")
                np2 = st.text_input("Confirm password", type="password", placeholder="Repeat your password", key="reg_pass2")
                rok = st.form_submit_button("Create Account", use_container_width=True)

            if rok:
                if not check_rate_limit("signup", limit=3, seconds=300):
                    return
                if not nu or not ne or not np1:
                    st.error("Please fill all required fields.")
                    return
                if len(np1) < 6:
                    st.error("Password must be at least 6 characters.")
                    return
                if np1 != np2:
                    st.error("Passwords do not match.")
                    return
                clean_username = _re.sub(r"[^A-Za-z0-9_]", "_", nu.strip())[:24]
                if not _re.match(r"^[A-Za-z0-9_]{3,24}$", clean_username):
                    st.error("Username must be 3-24 characters using letters, numbers, or underscores.")
                    return
                try:
                    auth_res = sb.auth.sign_up({
                        "email": ne.strip(),
                        "password": np1,
                        "options": {"data": {"username": clean_username, "bio": nb}},
                    })
                    if auth_res and getattr(auth_res, "session", None):
                        st.session_state.sb_access_token = auth_res.session.access_token
                        st.session_state.sb_refresh_token = auth_res.session.refresh_token
                        try:
                            sb.auth.set_session(auth_res.session.access_token, auth_res.session.refresh_token)
                        except Exception:
                            pass
                        save_auth_tokens_to_browser()
                    if auth_res and getattr(auth_res, "user", None):
                        ensure_user_profile_saved(sb, auth_res.user.id, clean_username, ne.strip(), nb)
                    st.success("Account created. Check your email to confirm, then sign in.")
                except Exception as e:
                    msg = str(e)
                    if "already" in msg.lower() or "duplicate" in msg.lower():
                        st.error("That email or username is already used.")
                    else:
                        st.error(f"Could not create account: {e}")

        else:
            st.markdown("<div class='auth-copy'>Enter your email and we’ll send a secure Supabase reset link.</div>", unsafe_allow_html=True)
            with st.form("reset_request_f"):
                re_email = st.text_input("Email", placeholder="you@email.com", key="reset_email_input")
                send_link = st.form_submit_button("Send Reset Link", use_container_width=True)

            if send_link and re_email:
                try:
                    app_url = get_config("APP_URL", "http://localhost:8501")
                    sb.auth.reset_password_for_email(re_email.strip(), {"redirect_to": app_url})
                    st.success("Reset link sent. Check your inbox and spam folder.")
                except Exception as e:
                    st.error(f"Could not send reset email: {e}")

    with col_right:
        member_count, post_count, msg_count = get_platform_stats()

        render_cube()

        st.markdown(f"""
        <div class="card auth-product-card" style="text-align:center;">
          <h3 style="color:var(--primary);font-family:'Space Grotesk',sans-serif;font-size:1.4rem;margin:0;">
            Everything your community needs in one place.
          </h3>
          <p style="color:var(--text-secondary);font-size:0.92rem;margin:0.4rem 0 1.3rem;">
            A refined dashboard for posts, AI assistance, live messaging, planning, habits, and profiles.
          </p>
          
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem;margin:0.5rem 0 1rem;">
            <div style="background:var(--bg2);border-radius:12px;padding:1rem 0.5rem;border:1px solid rgba(88,101,242,0.05);">
              <div style="font-size:1.8rem;font-weight:900;color:var(--primary);">{member_count}</div>
              <div style="color:var(--text-muted);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">Members</div>
            </div>
            <div style="background:var(--bg2);border-radius:12px;padding:1rem 0.5rem;border:1px solid rgba(88,101,242,0.05);">
              <div style="font-size:1.8rem;font-weight:900;color:var(--primary);">{post_count}</div>
              <div style="color:var(--text-muted);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">Posts</div>
            </div>
            <div style="background:var(--bg2);border-radius:12px;padding:1rem 0.5rem;border:1px solid rgba(88,101,242,0.05);">
              <div style="font-size:1.8rem;font-weight:900;color:var(--primary);">{msg_count}</div>
              <div style="color:var(--text-muted);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">Messages</div>
            </div>
          </div>
          
          <div style="margin-top:0.5rem;padding-top:1rem;border-top:1px solid rgba(88,101,242,0.06);">
            <p style="color:var(--text-muted);font-size:0.7rem;margin:0;">AI assistant powered by Taha</p>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# VIEW USER PROFILE
# ============================================================
def view_user_profile(user_id):
    sb = get_sb()
    user = get_user_profile(user_id)
    if not user:
        st.error("User not found")
        return
    
    fa = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    is_online = (user.get("last_seen") or "") > fa
    safe_username = escape_html(user.get("username", "user"))
    safe_bio = safe_multiline(user.get("bio") or "No bio yet.")
    followers, following = follow_counts(sb, user["id"])
    post_total, habit_total, event_total = user_activity_counts(sb, user["id"])
    following_this_user = is_following(sb, st.session_state.user_id, user["id"]) if user["id"] != st.session_state.user_id else False
    
    if st.button("✕ Close Profile", use_container_width=True):
        st.session_state.viewing_user = None
        try:
            if "profile" in st.query_params:
                del st.query_params["profile"]
        except Exception:
            pass
        st.rerun()
    
    st.markdown(f"""
    <div class="user-profile-card">
      <div style="display:flex;align-items:center;gap:1.5rem;margin-bottom:1.5rem;">
        {avatar_html(user.get('username', 'user'), user.get('avatar_url'), 80, 'av-lg')}
        <div>
          <h2 style="margin:0;font-family:'Space Grotesk',sans-serif;color:var(--primary);">@{safe_username}</h2>
          <div style="color:var(--text-muted);font-size:.78rem;margin-top:.2rem;">
            {'✓ Verified · ' if user.get('is_verified') else ''}{'Admin · ' if user.get('is_admin') else ''}{escape_html(user.get('profile_badge') or 'Member')}
          </div>
          <div style="color:{'var(--primary)' if is_online else 'var(--text-muted)'};font-size:.9rem;margin:.2rem 0;">
            {'<span class="online"></span>Online now' if is_online else '⚫ Offline'}
          </div>
          <p style="color:var(--text-secondary);margin:.3rem 0 0;">{safe_bio}</p>
          <p style="color:var(--text-muted);font-size:.8rem;margin-top:.3rem;">Joined {user.get('created_at','')[:10]}</p>
        </div>
      </div>
      
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:1rem 0;">
        <div class="metric" style="padding:1rem;">
          <div class="val" style="font-size:1.8rem;">{post_total}</div>
          <div class="lbl">Posts</div>
        </div>
        <div class="metric" style="padding:1rem;">
          <div class="val" style="font-size:1.8rem;">{habit_total}</div>
          <div class="lbl">Habits</div>
        </div>
        <div class="metric" style="padding:1rem;">
          <div class="val" style="font-size:1.8rem;">{event_total}</div>
          <div class="lbl">Events</div>
        </div>
        <div class="metric" style="padding:1rem;">
          <div class="val" style="font-size:1.8rem;">{followers}</div>
          <div class="lbl">Followers</div>
        </div>
        <div class="metric" style="padding:1rem;">
          <div class="val" style="font-size:1.8rem;">{following}</div>
          <div class="lbl">Following</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if user["id"] != st.session_state.user_id:
        c_follow, c_msg, c_report = st.columns(3)
        with c_follow:
            follow_label = "Unfollow" if following_this_user else "Follow"
            if st.button(follow_label, key=f"follow_{user['id']}", use_container_width=True):
                if not check_rate_limit("follow", limit=20, seconds=60):
                    return
                if following_this_user:
                    sb.table("user_follows").delete().eq("follower_id", st.session_state.user_id).eq("following_id", user["id"]).execute()
                else:
                    sb.table("user_follows").insert({
                        "follower_id": st.session_state.user_id,
                        "following_id": user["id"],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }).execute()
                    create_notification(sb, user["id"], st.session_state.user_id, "follow", "New follower", f"@{st.session_state.username} followed you.", "user", st.session_state.user_id)
                session_cache_clear(f"follow_counts_{user['id']}")
                session_cache_clear(f"follow_counts_{st.session_state.user_id}")
                st.rerun()
        with c_msg:
            if st.button(f"Message @{user['username']}", key=f"profile_dm_{user['id']}", use_container_width=True):
                st.session_state.page = "live_chat"
                st.session_state.chat_target = user["username"]
                st.session_state.viewing_user = None
                st.rerun()
        with c_report:
            with st.expander("Report"):
                reason = st.text_input("Reason", key=f"report_user_{user['id']}", label_visibility="collapsed", placeholder="Why report this user?")
                if st.button("Send report", key=f"send_report_user_{user['id']}"):
                    report_target(sb, "user", user["id"], reason)
        profile_url = f"{get_config('APP_URL', '').rstrip('/')}/?profile={user['username']}" if get_config("APP_URL") else f"?profile={user['username']}"
        st.code(profile_url, language="text")
    
    st.markdown("### 📝 User's Posts")
    posts = sb.table("posts").select("*").eq("user_id", user["id"]).order("created_at", desc=True).limit(10).execute()
    if not posts.data:
        st.markdown("<p style='color:var(--text-muted);'>No posts yet.</p>", unsafe_allow_html=True)
    else:
        for p in posts.data:
            st.markdown(f"""
            <div class="post">
              <p style="margin:0;color:var(--text-primary);">{linkify_mentions(p['content'])}</p>
              <small style="color:var(--text-muted);">{ago(p['created_at'])}</small>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("### ✅ User's Habits")
    habits = sb.table("habits").select("*").eq("user_id", user["id"]).limit(10).execute()
    if not habits.data:
        st.markdown("<p style='color:var(--text-muted);'>No habits yet.</p>", unsafe_allow_html=True)
    else:
        for h in habits.data:
            safe_habit = escape_html(h.get("name", "Habit"))
            safe_emoji = escape_html(h.get("emoji", "⭐"))
            st.markdown(f"""
            <div class="card" style="padding:0.8rem 1.2rem;">
              <span style="font-size:1rem;font-weight:700;color:var(--primary);">{safe_emoji} {safe_habit}</span>
              <span style="color:var(--text-muted);font-size:.8rem;margin-left:.5rem;">{h['frequency']}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("### 📅 User's Events")
    events = sb.table("events").select("*").eq("user_id", user["id"]).gte("event_date", datetime.now(timezone.utc).isoformat()).order("event_date").limit(10).execute()
    if not events.data:
        st.markdown("<p style='color:var(--text-muted);'>No upcoming events.</p>", unsafe_allow_html=True)
    else:
        for ev in events.data:
            dt = ev["event_date"][:16].replace("T"," ")
            safe_title = escape_html(ev.get("title", "Event"))
            st.markdown(f"""
            <div class="ev-card" style="border-left-color:var(--primary);padding:0.8rem 1.2rem;">
              <div style="font-weight:700;color:var(--primary);">{safe_title}</div>
              <div style="color:var(--text-muted);font-size:.8rem;">📅 {dt}</div>
            </div>
            """, unsafe_allow_html=True)
    
    if user["id"] == st.session_state.user_id:
        st.info("This is your public profile preview.")


# ============================================================
# HOME FEED
# ============================================================
def render_member_list():
    """
    Member list with real buttons so every username can open a profile.
    """
    sb = get_sb()
    five_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    users = session_cache_get(
        "member_list_profiles",
        20,
        lambda: (sb.table("profiles").select("id,username,last_seen,avatar_url").execute().data or [])
    )

    online = [u for u in users if (u.get("last_seen") or "") > five_ago]
    offline = [u for u in users if (u.get("last_seen") or "") <= five_ago]

    def render_user_button(u, is_online):
        is_me = u["id"] == st.session_state.user_id
        status_cls = "on" if is_online else "off"
        label = f'@{escape_html(u["username"])}' + (" (you)" if is_me else "")
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(
                f'<div class="av-wrap">{avatar_html(u.get("username", "user"), u.get("avatar_url"), 30, "av-sm")}'
                f'<span class="status-badge {status_cls}" style="width:10px;height:10px;border-width:2px;"></span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            if st.button(label, key=f"member_profile_{u['id']}", use_container_width=True):
                st.session_state.viewing_user = u["id"]
                st.rerun()

    st.markdown('<div class="member-category">Online — {}</div>'.format(len(online)), unsafe_allow_html=True)
    for u in online:
        render_user_button(u, True)
    if offline:
        st.markdown('<div class="member-category">Offline — {}</div>'.format(len(offline)), unsafe_allow_html=True)
        for u in offline:
            render_user_button(u, False)


def get_post_reactions(sb, post_id):
    """Returns {emoji: count} and whether the current user has reacted with each."""
    try:
        rows = sb.table("post_reactions").select("emoji,user_id").eq("post_id", post_id).execute()
        counts = {}
        mine = set()
        for r in (rows.data or []):
            counts[r["emoji"]] = counts.get(r["emoji"], 0) + 1
            if r["user_id"] == st.session_state.user_id:
                mine.add(r["emoji"])
        return counts, mine
    except Exception:
        return {}, set()

REACTION_EMOJIS = ["❤️", "👍", "😂", "🔥"]

def get_home_feed_data(sb, user_id):
    """Batch-load home feed data to avoid per-post Supabase queries."""
    def load():
        try:
            posts = sb.table("posts")\
                .select("id,user_id,username,content,created_at,file_url,file_name,file_type,is_pinned")\
                .order("is_pinned", desc=True).order("created_at", desc=True).limit(15).execute().data or []
            post_ids = [p["id"] for p in posts]
            if not post_ids:
                return [], {}, {}, {}, {}

            reaction_rows = sb.table("post_reactions").select("post_id,emoji,user_id").in_("post_id", post_ids).execute().data or []
            comment_rows = sb.table("post_comments").select("post_id,user_id,username,content,created_at")\
                .in_("post_id", post_ids).order("created_at").limit(120).execute().data or []
            profile_ids = [p.get("user_id") for p in posts] + [c.get("user_id") for c in comment_rows]
            profiles = get_profiles_map(sb, profile_ids)

            reaction_counts = {}
            my_reactions = {}
            for r in reaction_rows:
                pid = r["post_id"]
                reaction_counts.setdefault(pid, {})
                reaction_counts[pid][r["emoji"]] = reaction_counts[pid].get(r["emoji"], 0) + 1
                if r["user_id"] == user_id:
                    my_reactions.setdefault(pid, set()).add(r["emoji"])

            comments_by_post = {}
            for c in comment_rows:
                bucket = comments_by_post.setdefault(c["post_id"], [])
                if len(bucket) < 30:
                    bucket.append(c)

            return posts, reaction_counts, my_reactions, comments_by_post, profiles
        except Exception:
            return [], {}, {}, {}, {}
    return session_cache_get(f"home_feed_{user_id}", 8, load)

def home_page():
    sb = get_sb()
    sh_header("🏠", "Home Feed")

    col_feed, col_members = st.columns([3, 1], gap="medium")

    with col_members:
        render_member_list()

        # Mention notifications
        sb2 = get_sb()
        mention_count = get_unread_mention_count(sb2, st.session_state.user_id)
        if mention_count > 0:
            st.markdown(f"""
            <div style="background:rgba(242,63,66,0.08);border:1px solid rgba(242,63,66,0.2);
              border-radius:var(--radius);padding:.75rem 1rem;margin-top:.8rem;">
              <div style="color:var(--danger);font-weight:700;font-size:.85rem;">🔔 {mention_count} Mention{"s" if mention_count>1 else ""}</div>
            </div>
            """, unsafe_allow_html=True)
            mentions = sb2.table("mentions").select("id").eq("mentioned_user_id", st.session_state.user_id).eq("is_read", False).eq("source_type", "post").order("created_at", desc=True).limit(5).execute()
            if mentions.data:
                mark_mentions_read(sb2, st.session_state.user_id, "post")
            if st.button("Clear mentions", key="clear_mentions"):
                mark_mentions_read(sb2, st.session_state.user_id)
                st.rerun()

    with col_feed:
        with st.expander("✍️  Write a post...", expanded=False):
            with st.form("pf", clear_on_submit=True):
                c = st.text_area("Write your thoughts...", placeholder="What's on your mind? Use @username to mention someone 🤔", max_chars=500, label_visibility="collapsed")
                post_upload = st.file_uploader("Attach image or file", type=None, key="post_upload")
                ai_polish = st.checkbox("Polish this post with AI before publishing")
                if st.form_submit_button("Publish", use_container_width=True) and c and c.strip():
                    if not check_rate_limit("post", limit=5, seconds=60):
                        return
                    content_to_post = c.strip()
                    if ai_polish and get_config("GROQ_API_KEY"):
                        with st.spinner("Polishing post..."):
                            improved = call_groq([
                                {"role": "system", "content": "Rewrite the user's post to be clear, friendly, and concise. Keep mentions like @username unchanged. Return only the rewritten post."},
                                {"role": "user", "content": content_to_post},
                            ], get_config("GROQ_API_KEY"))
                        if improved and not improved.startswith("Groq API Error"):
                            content_to_post = improved.strip()[:500]
                    payload = {
                        "user_id": st.session_state.user_id,
                        "username": st.session_state.username,
                        "content": content_to_post,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    if post_upload:
                        att = file_to_data_uri(post_upload)
                        if att:
                            payload["file_url"] = att["url"]
                            payload["file_name"] = att["name"]
                            payload["file_type"] = att["type"]
                    result = sb.table("posts").insert({
                        **payload
                    }).execute()
                    if result.data:
                        record_mentions(sb, content_to_post, "post", result.data[0]["id"], st.session_state.user_id)
                    session_cache_clear("home_feed_")
                    session_cache_clear("platform_stats")
                    session_cache_clear(f"profile_posts_{st.session_state.user_id}")
                    session_cache_clear(f"user_activity_counts_{st.session_state.user_id}")
                    st.rerun()

        posts, reaction_counts, my_reactions, comments_by_post, profile_map = get_home_feed_data(sb, st.session_state.user_id)
        if not posts:
            card("""
            <div style="text-align:center;padding:4rem 0;">
              <div style="font-size:5rem;margin-bottom:1.5rem;">🚀</div>
              <p style="color:var(--text-secondary);font-size:1.2rem;">No posts yet — be the first!</p>
              <p style="color:var(--text-muted);font-size:.9rem;">Share your thoughts with the community</p>
            </div>
            """)
            return

        for p in posts:
            mine = p["user_id"] == st.session_state.user_id
            profile = profile_map.get(p.get("user_id"), {})
            post_avatar = avatar_html(p.get("username", "user"), profile.get("avatar_url"), 40, "av-clickable")
            safe_username = escape_html(p.get("username", "user"))
            content_html = linkify_mentions(p["content"])

            col1, col2 = st.columns([5, 2])
            with col1:
                st.markdown(f"""
                <div class="post">
                  <div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.8rem;">
                    {post_avatar}
                    <div>
                      <div style="font-weight:700;color:{'var(--primary)' if mine else 'var(--text-primary)'};font-size:1rem;">
                        @{safe_username} {'<span class="badge">You</span>' if mine else ''}
                      </div>
                      <div style="font-size:.75rem;color:var(--text-muted);">{ago(p['created_at'])}</div>
                    </div>
                  </div>
                  <p style="margin:0;color:var(--text-primary);line-height:1.7;font-size:.95rem;">{content_html}</p>
                  {render_attachment_preview(p.get('file_url'), p.get('file_name'), p.get('file_type'))}
                </div>
                """, unsafe_allow_html=True)

                # Reactions row — kept compact on the left instead of
                # stretching one button across each full-width column.
                counts = reaction_counts.get(p["id"], {})
                mine_reactions = my_reactions.get(p["id"], set())
                rcols = st.columns([1] * len(REACTION_EMOJIS) + [len(REACTION_EMOJIS) + 2])
                for i, emoji in enumerate(REACTION_EMOJIS):
                    n = counts.get(emoji, 0)
                    label = f"{emoji} {n}" if n else emoji
                    with rcols[i]:
                        if st.button(label, key=f"react_{p['id']}_{emoji}"):
                            if not check_rate_limit("reaction", limit=40, seconds=60):
                                return
                            if emoji in mine_reactions:
                                sb.table("post_reactions").delete().eq("post_id", p["id"]).eq("user_id", st.session_state.user_id).eq("emoji", emoji).execute()
                            else:
                                sb.table("post_reactions").insert({
                                    "post_id": p["id"], "user_id": st.session_state.user_id, "emoji": emoji,
                                    "created_at": datetime.now(timezone.utc).isoformat(),
                                }).execute()
                                create_notification(sb, p["user_id"], st.session_state.user_id, "reaction", "New reaction", f"@{st.session_state.username} reacted {emoji} to your post.", "post", p["id"])
                            session_cache_clear("home_feed_")
                            st.rerun()

                with st.expander("Comments and moderation", expanded=False):
                    comments = comments_by_post.get(p["id"], [])
                    if comments:
                        for cm in comments:
                            cm_profile = profile_map.get(cm.get("user_id"), {})
                            cm_avatar = avatar_html(cm.get("username", "user"), cm_profile.get("avatar_url"), 26)
                            st.markdown(
                                f'<div style="display:flex;gap:.55rem;align-items:flex-start;margin:.45rem 0;">'
                                f'{cm_avatar}<div><strong>@{escape_html(cm["username"])}</strong> '
                                f'<span style="color:var(--text-muted);font-size:.75rem;">· {ago(cm["created_at"])}</span><br>'
                                f'{linkify_mentions(cm["content"])}</div></div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("No comments yet.")

                    with st.form(f"comment_form_{p['id']}", clear_on_submit=True):
                        comment = st.text_input("Add a comment", key=f"comment_{p['id']}", label_visibility="collapsed", placeholder="Write a reply...")
                        sent_comment = st.form_submit_button("Comment", use_container_width=True)
                    if sent_comment and comment.strip():
                        if check_rate_limit("comment", limit=10, seconds=60):
                            res = sb.table("post_comments").insert({
                                "post_id": p["id"],
                                "user_id": st.session_state.user_id,
                                "username": st.session_state.username,
                                "content": comment.strip()[:300],
                                "created_at": datetime.now(timezone.utc).isoformat(),
                            }).execute()
                            if res.data:
                                create_notification(sb, p["user_id"], st.session_state.user_id, "comment", "New comment", f"@{st.session_state.username} commented on your post.", "post", p["id"])
                            session_cache_clear("home_feed_")
                            st.rerun()

                    mod_cols = st.columns(3)
                    with mod_cols[0]:
                        if (mine or st.session_state.user.get("is_admin")) and st.button("Unpin" if p.get("is_pinned") else "Pin", key=f"pin_post_{p['id']}"):
                            sb.table("posts").update({"is_pinned": not p.get("is_pinned", False)}).eq("id", p["id"]).execute()
                            session_cache_clear("home_feed_")
                            st.rerun()
                    with mod_cols[1]:
                        reason = st.text_input("Report reason", key=f"report_post_reason_{p['id']}", label_visibility="collapsed", placeholder="Report reason")
                    with mod_cols[2]:
                        if st.button("Report", key=f"report_post_{p['id']}"):
                            report_target(sb, "post", p["id"], reason)

            with col2:
                if not mine:
                    if st.button("👤 View", key=f"view_{p['id']}"):
                        st.session_state.viewing_user = p["user_id"]
                        st.rerun()


def notifications_page():
    sb = get_sb()
    sh_header("🔔", "Notifications")
    rows_data = session_cache_get(
        f"notifications_page_{st.session_state.user_id}",
        8,
        lambda: (sb.table("notifications").select("*").eq("user_id", st.session_state.user_id)
                 .order("created_at", desc=True).limit(50).execute().data or [])
    )

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("Mark all read", use_container_width=True):
            sb.table("notifications").update({"is_read": True}).eq("user_id", st.session_state.user_id).eq("is_read", False).execute()
            session_cache_clear(f"notification_count_{st.session_state.user_id}")
            session_cache_clear(f"notifications_page_{st.session_state.user_id}")
            st.rerun()

    if not rows_data:
        card("<p style='color:var(--text-muted);text-align:center;'>No notifications yet.</p>")
        return

    actor_profiles = get_profiles_map(sb, [n.get("actor_id") for n in rows_data])
    for n in rows_data:
        status = "" if n.get("is_read") else "<span class='badge'>New</span>"
        actor = actor_profiles.get(n.get("actor_id"), {})
        actor_avatar = avatar_html(actor.get("username", "user"), actor.get("avatar_url"), 34)
        st.markdown(f"""
        <div class="card" style="padding:1rem 1.2rem;">
          <div style="display:flex;justify-content:space-between;gap:1rem;">
            <div style="display:flex;gap:.75rem;align-items:flex-start;">
              {actor_avatar}
            <div>
              <div style="font-weight:800;color:var(--primary);">{escape_html(n.get('title', 'Notification'))} {status}</div>
              <div style="color:var(--text-secondary);font-size:.9rem;margin-top:.25rem;">{safe_multiline(n.get('body', ''))}</div>
            </div>
            </div>
            <div style="color:var(--text-muted);font-size:.75rem;white-space:nowrap;">{ago(n.get('created_at', ''))}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)


def discover_page():
    sb = get_sb()
    sh_header("🔎", "Discover")
    q = st.text_input("Search members", placeholder="Search by username or bio...", key="discover_q")
    if q and q.strip():
        term = f"%{q.strip()}%"
        users_data = sb.table("profiles").select("id,username,bio,last_seen,avatar_url,is_admin,is_verified,profile_badge")\
            .neq("id", st.session_state.user_id).or_(f"username.ilike.{term},bio.ilike.{term}")\
            .order("last_seen", desc=True).limit(40).execute().data or []
    else:
        users_data = session_cache_get(
            f"discover_users_{st.session_state.user_id}",
            30,
            lambda: (sb.table("profiles").select("id,username,bio,last_seen,avatar_url,is_admin,is_verified,profile_badge")
                     .neq("id", st.session_state.user_id).order("last_seen", desc=True).limit(40).execute().data or [])
        )

    if not users_data:
        card("<p style='color:var(--text-muted);text-align:center;'>No members found.</p>")
        return

    user_ids = [u["id"] for u in users_data]
    def load_discover_social():
        if not user_ids:
            return {}, set()
        try:
            rows = sb.table("user_follows").select("follower_id,following_id").in_("following_id", user_ids).execute().data or []
            follower_counts = {}
            following_set = set()
            for row in rows:
                following_id = row["following_id"]
                follower_counts[following_id] = follower_counts.get(following_id, 0) + 1
                if row["follower_id"] == st.session_state.user_id:
                    following_set.add(following_id)
            return follower_counts, following_set
        except Exception:
            return {}, set()
    follower_counts, following_set = session_cache_get(
        f"discover_social_{st.session_state.user_id}_{hash(tuple(user_ids))}",
        20,
        load_discover_social,
    )

    for u in users_data:
        followers = follower_counts.get(u["id"], 0)
        following = u["id"] in following_set
        safe_username = escape_html(u.get("username", "user"))
        safe_bio = safe_multiline(u.get("bio") or "No bio yet.")
        c_avatar, c_info, c_follow, c_view = st.columns([1, 4, 1, 1])
        with c_avatar:
            st.markdown(avatar_html(u.get("username", "user"), u.get("avatar_url"), 42), unsafe_allow_html=True)
        with c_info:
            badge = "✓ Verified" if u.get("is_verified") else (u.get("profile_badge") or "Member")
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.2rem;margin-bottom:.35rem;">
              <div style="font-weight:900;color:var(--primary);">@{safe_username}</div>
              <div style="color:var(--text-muted);font-size:.76rem;">{escape_html(badge)} · {followers} followers</div>
              <div style="color:var(--text-secondary);font-size:.88rem;margin-top:.35rem;">{safe_bio}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_follow:
            if st.button("Unfollow" if following else "Follow", key=f"discover_follow_{u['id']}", use_container_width=True):
                if not check_rate_limit("follow", limit=20, seconds=60):
                    return
                if following:
                    sb.table("user_follows").delete().eq("follower_id", st.session_state.user_id).eq("following_id", u["id"]).execute()
                else:
                    sb.table("user_follows").insert({
                        "follower_id": st.session_state.user_id,
                        "following_id": u["id"],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }).execute()
                    create_notification(sb, u["id"], st.session_state.user_id, "follow", "New follower", f"@{st.session_state.username} followed you.", "user", st.session_state.user_id)
                session_cache_clear(f"follow_counts_{u['id']}")
                session_cache_clear(f"follow_counts_{st.session_state.user_id}")
                session_cache_clear(f"discover_social_{st.session_state.user_id}")
                st.rerun()
        with c_view:
            if st.button("Profile", key=f"discover_profile_{u['id']}", use_container_width=True):
                st.session_state.viewing_user = u["id"]
                st.rerun()


# ============================================================
# AI CHAT — GROQ
# ============================================================

def ai_chat_page():
    sh_header("🤖", "AI Assistant")

    api_key = get_config("GROQ_API_KEY")
    if not api_key:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2.5rem;">
          <div style="font-size:2.5rem;margin-bottom:.8rem;">🔑</div>
          <h3 style="margin:0 0 .5rem;color:var(--primary);">Groq API key missing</h3>
          <p style="color:var(--text-secondary);">Add <code style="color:var(--primary);">GROQ_API_KEY</code> to Streamlit Secrets or your local <code style="color:var(--primary);">.env</code> file to enable AI chat.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    if "ai_msgs" not in st.session_state:
        st.session_state.ai_msgs = [
            {"role": "assistant", "content": f"Hey @{st.session_state.username}! I'm your LifeHub AI assistant, running on Groq. Ask me anything ⚡"}
        ]

    # ── Chat history ──
    for m in st.session_state.ai_msgs:
        cls   = "bme" if m["role"] == "user" else "bother"
        align = "text-align:right;" if m["role"] == "user" else ""
        who   = "You" if m["role"] == "user" else "⚡ Groq AI"
        meta  = "bmeta" if m["role"] == "user" else "bmeta-other"
        content = safe_multiline(m["content"])
        st.markdown(f'<div class="{cls}">{content}<div class="{meta}" style="{align}">{who}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Input ──
    with st.form("aif", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            prompt = st.text_input("Message", placeholder="Ask anything...", key="ai_input", label_visibility="collapsed")
        with c2:
            sent = st.form_submit_button("Send ⚡", use_container_width=True)

    if st.button("🗑️ Clear chat", key="clr_ai"):
        st.session_state.ai_msgs = []
        st.rerun()

    if sent and prompt and prompt.strip():
        if not check_rate_limit("ai_prompt", limit=12, seconds=300):
            return
        st.session_state.ai_msgs.append({"role": "user", "content": prompt.strip()})

        # Build a proper chat-format request (system + recent history)
        groq_messages = [
            {"role": "system", "content": f"You are a friendly, concise AI assistant inside LifeHub, a social app. The user's name is @{st.session_state.username}."}
        ]
        groq_messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.ai_msgs[-10:]]

        with st.spinner("Thinking..."):
            reply = call_groq(groq_messages, api_key)
        st.session_state.ai_msgs.append({"role": "assistant", "content": reply})
        st.rerun()

# ============================================================
# LIVE CHAT — PERSISTENT
# ============================================================
def get_unread_counts(sb, user_id):
    """
    Returns {sender_id: unread_count} for all unread DMs addressed to
    the current user. Used to show badges in the chat-partner selector.
    """
    def load():
        try:
            rows = sb.table("messages").select("sender_id").eq("receiver_id", user_id).eq("is_read", False).execute()
            counts = {}
            for r in (rows.data or []):
                counts[r["sender_id"]] = counts.get(r["sender_id"], 0) + 1
            return counts
        except Exception:
            return {}
    return session_cache_get(f"dm_unread_{user_id}", 20, load)


def set_typing(sb, user_id, target_id):
    """Upserts a 'typing' heartbeat row, read by the other party's fragment."""
    key = f"typing_heartbeat_{target_id}"
    now = time.time()
    if now - st.session_state.get(key, 0) < 2:
        return
    try:
        sb.table("typing_status").upsert({
            "user_id": user_id, "target_id": target_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="user_id,target_id").execute()
        st.session_state[key] = now
    except Exception:
        pass


def is_other_typing(sb, other_id, my_id):
    """True if `other_id` had a typing heartbeat aimed at me in the last 4s."""
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=4)).isoformat()
        r = sb.table("typing_status").select("updated_at").eq("user_id", other_id).eq("target_id", my_id).gte("updated_at", cutoff).execute()
        return bool(r.data)
    except Exception:
        return False


def file_to_data_uri(uploaded_file, max_dim=640) -> dict:
    """
    Converts an uploaded file to a base64 data URI, same storage
    pattern already used for avatars. Images are resized to cap size;
    non-image files are stored as-is (small files only — this is a
    base64-in-DB approach, not real object storage, so keep it light).
    Returns {"url":..., "name":..., "type": "image"|"file"} or None.
    """
    try:
        name = uploaded_file.name
        ext = name.split(".")[-1].lower()
        if ext in ("png", "jpg", "jpeg", "gif", "webp"):
            img = Image.open(uploaded_file)
            img.thumbnail((max_dim, max_dim))
            buf = io.BytesIO()
            fmt = "PNG" if ext in ("png", "gif") else "JPEG"
            save_kwargs = {"optimize": True}
            if fmt == "JPEG":
                save_kwargs["quality"] = 75
            img.convert("RGB" if fmt == "JPEG" else "RGBA").save(buf, format=fmt, **save_kwargs)
            b64 = base64.b64encode(buf.getvalue()).decode()
            mime = "image/png" if fmt == "PNG" else "image/jpeg"
            return {"url": f"data:{mime};base64,{b64}", "name": name, "type": "image"}
        else:
            raw = uploaded_file.read()
            if len(raw) > 2 * 1024 * 1024:
                st.error("File too large — 2MB max.")
                return None
            b64 = base64.b64encode(raw).decode()
            return {"url": f"data:application/octet-stream;base64,{b64}", "name": name, "type": "file"}
    except Exception as e:
        st.error(f"Could not process file: {e}")
        return None


def render_attachment_html(file_url, file_name, file_type):
    if not file_url:
        return ""
    safe_name = escape_html(file_name or "attachment")
    if file_type == "image":
        return f'<img src="{file_url}" style="max-width:280px;max-height:280px;border-radius:10px;margin-top:.4rem;display:block;">'
    return (f'<a href="{file_url}" download="{safe_name}" '
            f'style="display:inline-flex;align-items:center;gap:.4rem;margin-top:.4rem;'
            f'background:rgba(88,101,242,0.12);padding:.4rem .8rem;border-radius:8px;'
            f'color:var(--primary);text-decoration:none;font-size:.85rem;">📎 {safe_name}</a>')


@st.fragment(run_every=2)
def render_live_messages_fragment(sb, tid, sel, target_avatar):
    """
    Auto-refreshing message list, isolated in its own fragment so only
    this part of the page re-executes every 3 seconds — the rest of
    the page (sidebar, selectbox, send form) stays untouched.
    """
    # Keep receive polling fast: read-status writes are throttled and
    # do not run on every 1s fragment refresh.
    read_key = f"dm_read_marked_{tid}"
    if time.time() - st.session_state.get(read_key, 0) > 12:
        try:
            sb.table("messages").update({"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}).eq("sender_id", tid).eq("receiver_id", st.session_state.user_id).eq("is_read", False).execute()
            session_cache_clear(f"dm_unread_{st.session_state.user_id}")
            st.session_state[read_key] = time.time()
        except Exception:
            pass

    msgs = sb.table("messages").select("id,sender_id,receiver_id,content,created_at,file_url,file_name,file_type")\
        .or_(f"and(sender_id.eq.{st.session_state.user_id},receiver_id.eq.{tid}),and(sender_id.eq.{tid},receiver_id.eq.{st.session_state.user_id})")\
        .order("created_at", desc=True).limit(50).execute()
    msg_rows = list(reversed(msgs.data or []))

    typing = is_other_typing(sb, tid, st.session_state.user_id)

    if not msg_rows and not typing:
        st.markdown("<p style='color:var(--text-muted);text-align:center;padding:2rem;'>Start the conversation 👋</p>", unsafe_allow_html=True)
        return

    my_avatar_inner = avatar_html(st.session_state.username, st.session_state.user.get("avatar_url"), 36)
    their_avatar_inner = avatar_html(sel, target_avatar, 36)

    # Discord pattern: group consecutive messages from the same
    # sender — avatar + name shown once per group, follow-up lines
    # render flush beneath with a hover-only timestamp.
    groups = []
    for m in msg_rows:
        mine = m["sender_id"] == st.session_state.user_id
        if groups and groups[-1]["mine"] == mine:
            groups[-1]["msgs"].append(m)
        else:
            groups.append({"mine": mine, "msgs": [m]})

    for g in groups:
        mine = g["mine"]
        avatar_inner_g = my_avatar_inner if mine else their_avatar_inner
        name = "You" if mine else f"@{escape_html(sel)}"
        first_time = ago(g["msgs"][0]["created_at"])
        lines_html = "".join(
            f'<div class="msg-line"><span class="msg-time-hover">{ago(m["created_at"])}</span>{linkify_mentions(m["content"])}'
            f'{render_attachment_html(m.get("file_url"), m.get("file_name"), m.get("file_type"))}</div>'
            for m in g["msgs"]
        )
        cls = "msg-group mine" if mine else "msg-group"
        st.markdown(f"""
        <div class="{cls}">
          <div class="av-wrap">{avatar_inner_g}</div>
          <div class="msg-group-body">
            <div class="msg-group-head"><span class="msg-group-name">{name}</span><span class="msg-group-time">{first_time}</span></div>
            {lines_html}
          </div>
        </div>
        """, unsafe_allow_html=True)
        if not mine:
            if st.button(f"View @{sel}", key=f"dm_view_profile_{tid}_{g['msgs'][0]['id']}"):
                st.session_state.viewing_user = tid
                st.rerun()

    if typing:
        st.markdown(f"""
        <div class="msg-group">
          <div class="av-wrap">{their_avatar_inner}</div>
          <div class="msg-group-body">
            <div class="msg-line" style="color:var(--text-muted);font-style:italic;">@{sel} is typing...</div>
          </div>
        </div>
        """, unsafe_allow_html=True)


def live_chat_page():
    sb = get_sb()
    sh_header("💬", "Live Chat")
    dm_mentions_key = "dm_mentions_marked"
    if time.time() - st.session_state.get(dm_mentions_key, 0) > 30:
        mark_mentions_read(sb, st.session_state.user_id, "direct_message")
        st.session_state[dm_mentions_key] = time.time()

    user_rows = session_cache_get(
        f"dm_users_{st.session_state.user_id}",
        20,
        lambda: (sb.table("profiles").select("id,username,last_seen,avatar_url").neq("id", st.session_state.user_id).execute().data or [])
    )
    if not user_rows:
        card("<p style='color:var(--text-muted);text-align:center;'>No other users yet.</p>")
        return

    unread = get_unread_counts(sb, st.session_state.user_id)
    umap = {u["username"]: u for u in user_rows}

    def fmt_user(username):
        u = umap[username]
        badge = f" 🔴{unread[u['id']]}" if unread.get(u["id"]) else ""
        return f"@{username}{badge}"

    default_user = st.session_state.get("chat_target", list(umap.keys())[0] if umap else None)
    sel = st.selectbox("Chat with", list(umap.keys()), index=list(umap.keys()).index(default_user) if default_user in umap else 0, format_func=fmt_user)
    if not sel: return

    target = umap[sel]
    tid = target["id"]

    with st.expander("🔍 Search this conversation", expanded=False):
        search_q = st.text_input("Search messages", placeholder="Search...", key=f"search_{tid}", label_visibility="collapsed")
        if search_q and search_q.strip():
            results = sb.table("messages").select("*")\
                .or_(f"and(sender_id.eq.{st.session_state.user_id},receiver_id.eq.{tid}),and(sender_id.eq.{tid},receiver_id.eq.{st.session_state.user_id})")\
                .ilike("content", f"%{search_q.strip()}%")\
                .order("created_at", desc=True).limit(20).execute()
            if results.data:
                st.caption(f"{len(results.data)} result(s)")
                for r in results.data:
                    who = "You" if r["sender_id"] == st.session_state.user_id else f"@{sel}"
                    st.markdown(f"<div class='msg-line' style='padding:.3rem .5rem;'><b style='color:var(--primary);'>{escape_html(who)}:</b> {linkify_mentions(r['content'])} <span style='color:var(--text-muted);font-size:.7rem;'>· {ago(r['created_at'])}</span></div>", unsafe_allow_html=True)
            else:
                st.caption("No matches.")

    five_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    is_onl = (target.get("last_seen") or "") > five_ago

    if st.session_state.get("chat_target"):
        st.session_state.chat_target = None

    target_avatar = target.get("avatar_url")
    status_cls = "on" if is_onl else "off"
    head_col, action_col = st.columns([4, 1])
    with head_col:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:.8rem;margin-bottom:1.2rem;
          padding:1rem 1.4rem;background:var(--card);border-radius:var(--radius-lg);border:1px solid rgba(88,101,242,0.12);">
          <div class="av-wrap">{avatar_html(sel, target_avatar, 42)}<span class="status-badge {status_cls}"></span></div>
          <div>
            <div style="font-weight:700;font-size:1rem;">@{escape_html(sel)}</div>
            <div style="font-size:.78rem;color:{'var(--primary)' if is_onl else 'var(--text-muted)'};">
              {'Online' if is_onl else 'Offline'}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with action_col:
        if st.button("View profile", key=f"dm_header_profile_{tid}", use_container_width=True):
            st.session_state.viewing_user = tid
            st.rerun()

    render_live_messages_fragment(sb, tid, sel, target_avatar)

    st.markdown("---")

    with st.expander("📎 Attach a file or image", expanded=False):
        uploaded = st.file_uploader("Choose a file", type=None, key=f"upload_{tid}", label_visibility="collapsed")

    col1, col2 = st.columns([5, 1])
    with col1:
        nm = st.text_input(f"Message @{sel}...", placeholder="Type your message...", key=f"chat_input_{tid}")
    with col2:
        st.write("")
        sbtn = st.button("Send", key=f"send_dm_{tid}", use_container_width=True)

    if not sbtn and st.session_state.get(f"chat_input_{tid}"):
        set_typing(sb, st.session_state.user_id, tid)

    if sbtn and (nm and nm.strip() or uploaded):
        if not check_rate_limit("dm_send", limit=30, seconds=60):
            return
        payload = {
            "sender_id": st.session_state.user_id, "receiver_id": tid,
            "content": (nm or "").strip() or "📎 Sent an attachment",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_read": False,
        }
        if uploaded:
            att = file_to_data_uri(uploaded)
            if not att:
                return
            payload["file_url"] = att["url"]
            payload["file_name"] = att["name"]
            payload["file_type"] = att["type"]
        result = sb.table("messages").insert(payload).execute()
        if result.data and nm:
            record_mentions(sb, nm.strip(), "direct_message", result.data[0]["id"], st.session_state.user_id)
            create_notification(sb, tid, st.session_state.user_id, "message", "New direct message", f"@{st.session_state.username} sent you a message.", "direct_message", result.data[0]["id"])
        session_cache_clear(f"dm_unread_{tid}")
        session_cache_clear(f"user_sent_message_count_{st.session_state.user_id}")
        st.rerun()


# ============================================================
# CALENDAR
# ============================================================
def calendar_page():
    sb = get_sb()
    sh_header("📅", "Calendar")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### ➕ Add Event")
        with st.form("ef", clear_on_submit=True):
            t = st.text_input("Title *", placeholder="Meeting, workout...")
            d = st.text_area("Description", placeholder="Notes...", max_chars=300)
            ed = st.date_input("Date", value=date.today())
            et = st.time_input("Time")
            co = st.selectbox(
                "Color",
                ["blurple", "pink", "teal", "green", "red"],
                format_func=lambda x: x.capitalize(),
            )
            if st.form_submit_button("✨ Add Event", use_container_width=True) and t:
                sb.table("events").insert({
                    "user_id": st.session_state.user_id, "title": t, "description": d,
                    "event_date": datetime.combine(ed, et).isoformat(),
                    "color": co, "created_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
                st.success("Added!")
                session_cache_clear(f"calendar_events_{st.session_state.user_id}")
                session_cache_clear(f"user_activity_counts_{st.session_state.user_id}")
                st.rerun()

    with col2:
        st.markdown("### 📆 Upcoming")
        fil = st.radio("Show", ["This Week", "This Month", "All"], horizontal=True)
        def load_events():
            now = datetime.now(timezone.utc)
            q = sb.table("events").select("id,title,description,event_date,color").eq("user_id", st.session_state.user_id)
            if fil == "This Week":
                q = q.gte("event_date", now.isoformat()).lte("event_date", (now + timedelta(days=7)).isoformat())
            elif fil == "This Month":
                q = q.gte("event_date", now.replace(day=1).isoformat())
            return q.order("event_date").execute().data or []
        evs_data = session_cache_get(f"calendar_events_{st.session_state.user_id}_{fil}", 30, load_events)
        # Backward-compatible: old events stored before this palette
        # switch used "yellow"/"gold"/"orange" — still mapped here so
        # existing rows in the DB don't render with a missing color.
        cmap = {
            "blurple": "#5865F2", "pink": "#EB459E", "teal": "#23A55A",
            "green": "#23A55A", "red": "#F23F42",
            "yellow": "#5865F2", "gold": "#4752C4", "orange": "#3C45A5",
        }

        if not evs_data:
            card("<p style='color:var(--text-muted);text-align:center;'>No events. Add one! 🗓️</p>")
        else:
            for ev in evs_data:
                acc = cmap.get(ev.get("color", "blurple"), "#5865F2")
                dt = ev["event_date"][:16].replace("T", " ")
                safe_title = escape_html(ev.get("title", "Event"))
                safe_description = safe_multiline(ev.get("description", ""))
                ce, cd = st.columns([5, 1])
                with ce:
                    st.markdown(f"""
                    <div class="ev-card" style="border-left-color:{acc};padding:1.2rem;">
                      <div style="font-weight:700;color:{acc};">{safe_title}</div>
                      <div style="color:var(--text-muted);font-size:.8rem;margin-top:.2rem;">📅 {dt}</div>
                      {f"<p style='margin:.5rem 0 0;color:var(--text-secondary);font-size:.9rem;'>{safe_description}</p>" if ev.get('description') else ''}
                    </div>
                    """, unsafe_allow_html=True)
                with cd:
                    if st.button("🗑️", key=f"de{ev['id']}"):
                        sb.table("events").delete().eq("id", ev["id"]).execute()
                        session_cache_clear(f"calendar_events_{st.session_state.user_id}")
                        session_cache_clear(f"user_activity_counts_{st.session_state.user_id}")
                        st.rerun()


# ============================================================
# GROUP CHANNELS
# ============================================================
def get_user_channels(sb, user_id):
    """Channels the user has joined, plus all public channels not yet joined."""
    def load():
        try:
            joined = sb.table("channel_members").select("channel_id,last_read_at,role").eq("user_id", user_id).execute()
            joined_ids = [r["channel_id"] for r in (joined.data or [])]
            last_read = {r["channel_id"]: r.get("last_read_at") for r in (joined.data or [])}
            all_channels = sb.table("channels").select("id,name,description,created_by,is_public,invite_code,created_at").order("created_at").execute()
            return all_channels.data or [], set(joined_ids), last_read
        except Exception:
            return [], set(), {}
    return session_cache_get(f"user_channels_{user_id}", 30, load)


def get_channel_unread(sb, channel_id, user_id, last_seen_at):
    """Count of channel messages newer than the user's last-viewed timestamp."""
    if not last_seen_at:
        return 0
    def load():
        try:
            r = sb.table("channel_messages").select("id", count="exact").eq("channel_id", channel_id).gt("created_at", last_seen_at).neq("sender_id", user_id).execute()
            return r.count or 0
        except Exception:
            return 0
    return session_cache_get(f"channel_unread_{user_id}_{channel_id}_{last_seen_at}", 20, load)

def get_channel_role(sb, channel_id, user_id):
    def load():
        try:
            r = sb.table("channel_members").select("role").eq("channel_id", channel_id).eq("user_id", user_id).limit(1).execute()
            return (r.data or [{}])[0].get("role", "member")
        except Exception:
            return "member"
    return session_cache_get(f"channel_role_{user_id}_{channel_id}", 20, load)


@st.fragment(run_every=3)
def render_channel_messages_fragment(sb, channel_id, channel_name):
    """Auto-refreshing channel message feed, same pattern as DM chat."""
    mark_mentions_read(sb, st.session_state.user_id, "channel_message")
    msgs = sb.table("channel_messages").select("*").eq("channel_id", channel_id)\
        .order("is_pinned", desc=True).order("created_at", desc=False).limit(75).execute()
    my_channel_role = get_channel_role(sb, channel_id, st.session_state.user_id)

    if not msgs.data:
        st.markdown(f"<p style='color:var(--text-muted);text-align:center;padding:2rem;'>No messages in #{escape_html(channel_name)} yet. Say hello! 👋</p>", unsafe_allow_html=True)
        return
    sender_profiles = get_profiles_map(sb, [m.get("sender_id") for m in (msgs.data or [])])

    groups = []
    for m in msgs.data:
        mine = m["sender_id"] == st.session_state.user_id
        if groups and groups[-1]["sender_id"] == m["sender_id"]:
            groups[-1]["msgs"].append(m)
        else:
            groups.append({"sender_id": m["sender_id"], "username": m["sender_username"], "mine": mine, "msgs": [m]})

    for g in groups:
        profile = sender_profiles.get(g["sender_id"], {})
        avatar_inner = avatar_html(g["username"], profile.get("avatar_url"), 36)
        name = "You" if g["mine"] else f"@{escape_html(g['username'])}"
        first_time = ago(g["msgs"][0]["created_at"])
        lines_html = "".join(
            f'<div class="msg-line"><span class="msg-time-hover">{ago(m["created_at"])}</span>{linkify_mentions(m["content"])}'
            f'{render_attachment_html(m.get("file_url"), m.get("file_name"), m.get("file_type"))}</div>'
            for m in g["msgs"]
        )
        cls = "msg-group mine" if g["mine"] else "msg-group"
        st.markdown(f"""
        <div class="{cls}">
          <div class="av-wrap">{avatar_inner}</div>
          <div class="msg-group-body">
            <div class="msg-group-head"><span class="msg-group-name">{name}</span><span class="msg-group-time">{first_time}</span></div>
            {lines_html}
          </div>
        </div>
        """, unsafe_allow_html=True)
        if not g["mine"]:
            if st.button(f"View @{g['username']}", key=f"channel_view_profile_{channel_id}_{g['sender_id']}_{g['msgs'][0]['id']}"):
                st.session_state.viewing_user = g["sender_id"]
                st.rerun()
        if g["mine"] or my_channel_role in ("owner", "moderator") or st.session_state.user.get("is_admin"):
            first_msg = g["msgs"][0]
            if st.button("Unpin" if first_msg.get("is_pinned") else "Pin message", key=f"pin_channel_msg_{first_msg['id']}"):
                sb.table("channel_messages").update({"is_pinned": not first_msg.get("is_pinned", False)}).eq("id", first_msg["id"]).execute()
                st.rerun()


def channels_page():
    sb = get_sb()
    sh_header("📡", "Channels")

    channels, joined_ids, last_read = get_user_channels(sb, st.session_state.user_id)

    with st.expander("🔗 Join by invite", expanded=False):
        invite_code = st.text_input("Invite code", key="join_invite_code", placeholder="Paste invite code")
        if st.button("Join invite", use_container_width=True) and invite_code.strip():
            invite = sb.table("channels").select("*").eq("invite_code", invite_code.strip()).limit(1).execute()
            if not invite.data:
                st.error("Invalid invite code.")
            else:
                channel = invite.data[0]
                sb.table("channel_members").insert({
                    "channel_id": channel["id"],
                    "user_id": st.session_state.user_id,
                    "role": "member",
                    "joined_at": datetime.now(timezone.utc).isoformat(),
                    "last_read_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
                st.session_state.active_channel = channel["id"]
                session_cache_clear(f"user_channels_{st.session_state.user_id}")
                session_cache_clear(f"channel_role_{st.session_state.user_id}_{channel['id']}")
                st.rerun()

    with st.expander("➕ Create a channel", expanded=False):
        with st.form("new_channel_f", clear_on_submit=True):
            cn = st.text_input("Channel name", placeholder="general, gaming, study-group...")
            cd = st.text_area("Description", placeholder="What's this channel about?", max_chars=200)
            if st.form_submit_button("Create Channel", use_container_width=True) and cn.strip():
                if not check_rate_limit("channel_create", limit=4, seconds=300):
                    return
                clean_name = _re.sub(r"[^a-z0-9_-]+", "-", cn.strip().lower()).strip("-_")[:32]
                if not _re.match(r"^[a-z0-9][a-z0-9_-]{1,31}$", clean_name or ""):
                    st.error("Use 2-32 letters, numbers, dashes, or underscores for channel names.")
                    return
                exists = sb.table("channels").select("id").eq("name", clean_name).execute()
                if exists.data:
                    st.error("A channel with that name already exists.")
                else:
                    result = sb.table("channels").insert({
                        "name": clean_name, "description": cd.strip(),
                        "created_by": st.session_state.user_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }).execute()
                    if result.data:
                        sb.table("channel_members").insert({
                            "channel_id": result.data[0]["id"], "user_id": st.session_state.user_id,
                            "role": "member",
                            "joined_at": datetime.now(timezone.utc).isoformat(),
                            "last_read_at": datetime.now(timezone.utc).isoformat(),
                        }, returning=ReturnMethod.minimal).execute()
                    st.success(f"#{clean_name} created!")
                    session_cache_clear(f"user_channels_{st.session_state.user_id}")
                    st.rerun()

    if not channels:
        card("<p style='color:var(--text-muted);text-align:center;'>No channels yet — create the first one!</p>")
        return

    col_list, col_chat = st.columns([1, 3], gap="medium")

    with col_list:
        st.markdown('<div class="sb-eyebrow"># All Channels</div>', unsafe_allow_html=True)
        for ch in channels:
            is_joined = ch["id"] in joined_ids
            unread = get_channel_unread(sb, ch["id"], st.session_state.user_id, last_read.get(ch["id"])) if is_joined else 0
            active_mark = "● " if st.session_state.get("active_channel") == ch["id"] else ""
            label = f"{active_mark}# {ch['name']}" + (f" 🔴{unread}" if unread else (" ✓" if is_joined else " (join)"))
            if st.button(label, key=f"ch_{ch['id']}", use_container_width=True):
                if not is_joined:
                    sb.table("channel_members").insert({
                        "channel_id": ch["id"], "user_id": st.session_state.user_id,
                        "role": "member",
                        "joined_at": datetime.now(timezone.utc).isoformat(),
                        "last_read_at": datetime.now(timezone.utc).isoformat(),
                    }).execute()
                    session_cache_clear(f"user_channels_{st.session_state.user_id}")
                    session_cache_clear(f"channel_role_{st.session_state.user_id}_{ch['id']}")
                st.session_state.active_channel = ch["id"]
                st.rerun()

    with col_chat:
        active_id = st.session_state.get("active_channel")
        if not active_id and channels:
            active_id = channels[0]["id"]
            st.session_state.active_channel = active_id

        active_channel = next((c for c in channels if c["id"] == active_id), None)
        if not active_channel:
            st.info("Select a channel to start chatting.")
            return

        if active_channel["id"] not in joined_ids:
            st.info(f"Join #{active_channel['name']} to participate — click it in the list to join.")
            return

        last_seen_key = f"channel_read_marked_{active_channel['id']}"
        now_bucket = int(time.time() // 30)
        if st.session_state.get(last_seen_key) != now_bucket:
            try:
                sb.table("channel_members").update({"last_read_at": datetime.now(timezone.utc).isoformat()})\
                    .eq("channel_id", active_channel["id"]).eq("user_id", st.session_state.user_id).execute()
                st.session_state[last_seen_key] = now_bucket
                session_cache_clear(f"user_channels_{st.session_state.user_id}")
                session_cache_clear(f"channel_unread_{st.session_state.user_id}_{active_channel['id']}")
            except Exception:
                pass

        safe_channel_name = escape_html(active_channel.get("name", "channel"))
        safe_channel_desc = safe_multiline(active_channel.get("description", ""))
        my_role = get_channel_role(sb, active_channel["id"], st.session_state.user_id)
        st.markdown(f"""
        <div style="margin-bottom:1rem;">
          <div style="font-weight:800;font-size:1.2rem;color:var(--primary);">#{safe_channel_name}</div>
          <div style="color:var(--text-muted);font-size:.82rem;">{safe_channel_desc}</div>
          <div style="color:var(--text-muted);font-size:.76rem;margin-top:.3rem;">Role: {escape_html(my_role)} · Invite: <code>{escape_html(active_channel.get('invite_code', ''))}</code></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Leave channel", key=f"leave_{active_channel['id']}"):
            sb.table("channel_members").delete().eq("channel_id", active_channel["id"]).eq("user_id", st.session_state.user_id).execute()
            st.session_state.active_channel = None
            session_cache_clear(f"user_channels_{st.session_state.user_id}")
            session_cache_clear(f"channel_role_{st.session_state.user_id}_{active_channel['id']}")
            st.rerun()

        render_channel_messages_fragment(sb, active_channel["id"], active_channel["name"])

        st.markdown("---")
        with st.expander("📎 Attach a file or image", expanded=False):
            uploaded = st.file_uploader("Choose a file", type=None, key=f"chupload_{active_channel['id']}", label_visibility="collapsed")

        with st.form("channel_send_f", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                msg = st.text_input(f"Message #{active_channel['name']}", placeholder="Type a message... use @username to mention", key="channel_input", label_visibility="collapsed")
            with col2:
                sbtn = st.form_submit_button("Send", use_container_width=True)

        if sbtn and (msg and msg.strip() or uploaded):
            if not check_rate_limit("channel_send", limit=40, seconds=60):
                return
            payload = {
                "channel_id": active_channel["id"],
                "sender_id": st.session_state.user_id,
                "sender_username": st.session_state.username,
                "content": (msg or "").strip() or "📎 Sent an attachment",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if uploaded:
                att = file_to_data_uri(uploaded)
                if not att:
                    return
                payload["file_url"] = att["url"]
                payload["file_name"] = att["name"]
                payload["file_type"] = att["type"]
            result = sb.table("channel_messages").insert(payload).execute()
            if result.data and msg:
                record_mentions(sb, msg.strip(), "channel_message", result.data[0]["id"], st.session_state.user_id)
            session_cache_clear("channel_unread_")
            st.rerun()


# ============================================================
# HABITS
# ============================================================
def compute_habit_streak(sb, habit_id) -> int:
    """
    Computes the current consecutive-day streak for a habit by walking
    backward from today through habit_logs.log_date. Stops at the
    first gap. Returns 0 if not logged today (streak only counts if
    still active as of today).
    """
    try:
        logs = sb.table("habit_logs").select("log_date").eq("habit_id", habit_id)\
            .order("log_date", desc=True).limit(400).execute()
        log_dates = {row["log_date"] for row in (logs.data or [])}
        if not log_dates:
            return 0
        today = date.today()
        today_str = today.isoformat()
        if today_str not in log_dates:
            # Allow the streak to still show if yesterday was logged
            # (today not done yet doesn't reset an active streak display)
            cursor = today - timedelta(days=1)
        else:
            cursor = today
        streak = 0
        while cursor.isoformat() in log_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak
    except Exception:
        return 0

def compute_streak_from_log_dates(log_dates) -> int:
    log_dates = set(log_dates or [])
    if not log_dates:
        return 0
    today = date.today()
    cursor = today if today.isoformat() in log_dates else today - timedelta(days=1)
    streak = 0
    while cursor.isoformat() in log_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def habits_page():
    sb = get_sb()
    sh_header("✅", "Habit Tracker")
    
    if st.session_state.get("viewing_user"):
        view_user_profile(st.session_state.viewing_user)
        return
    
    t1, t2, t3 = st.tabs(["📊 My Habits", "🌍 Community", "🏆 Leaderboard"])

    with t1:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("### ➕ New Habit")
            with st.form("hf", clear_on_submit=True):
                nm = st.text_input("Habit", placeholder="Read, Exercise...")
                em = st.text_input("Emoji", value="⭐", max_chars=2)
                fr = st.selectbox("Frequency", ["Daily", "Weekly"])
                sh2 = st.checkbox("Share with community")
                if st.form_submit_button("✨ Create", use_container_width=True) and nm:
                    sb.table("habits").insert({
                        "user_id": st.session_state.user_id, "username": st.session_state.username,
                        "name": nm, "emoji": em or "⭐", "frequency": fr,
                        "is_shared": sh2, "created_at": datetime.now(timezone.utc).isoformat(),
                    }).execute()
                    session_cache_clear(f"community_habits_{st.session_state.user_id}")
                    session_cache_clear("habit_leaderboard_habits")
                    session_cache_clear(f"user_activity_counts_{st.session_state.user_id}")
                    st.rerun()

        with col2:
            st.markdown("### 📊 Progress")
            hbs = sb.table("habits").select("id,user_id,username,name,emoji,frequency,is_shared,created_at").eq("user_id", st.session_state.user_id).execute()
            today = date.today().isoformat()
            week_ago = (date.today() - timedelta(days=7)).isoformat()

            if not hbs.data:
                card("<p style='color:var(--text-muted);'>No habits yet! Create your first one ✨</p>")
            else:
                habit_ids = [h["id"] for h in hbs.data]
                log_rows = []
                if habit_ids:
                    log_rows = sb.table("habit_logs").select("habit_id,log_date")\
                        .in_("habit_id", habit_ids)\
                        .gte("log_date", (date.today() - timedelta(days=400)).isoformat())\
                        .execute().data or []
                logs_by_habit = {}
                for row in log_rows:
                    logs_by_habit.setdefault(row["habit_id"], set()).add(row["log_date"])

                for h in hbs.data:
                    habit_logs = logs_by_habit.get(h["id"], set())
                    week_count = sum(1 for log_date in habit_logs if log_date >= week_ago)
                    is_done = today in habit_logs
                    prog = min(week_count / 7, 1.0)
                    streak = compute_streak_from_log_dates(habit_logs)
                    streak_html = f'<span style="color:var(--primary);font-weight:700;">🔥 {streak}d</span>' if streak > 0 else ''
                    safe_habit = escape_html(h.get("name", "Habit"))
                    safe_emoji = escape_html(h.get("emoji", "⭐"))
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        st.markdown(f"""
                        <div class="card" style="padding:1.2rem;">
                          <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:1.1rem;font-weight:700;color:var(--primary);">{safe_emoji} {safe_habit} {'🌍' if h.get('is_shared') else ''}</span>
                            <span style="color:{'var(--primary)' if is_done else 'var(--text-muted)'};">{'✅ Done' if is_done else '⬜ Pending'}</span>
                          </div>
                          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.4rem;">
                            <div style="color:var(--text-muted);font-size:.8rem;">{week_count}/7 days this week</div>
                            {streak_html}
                          </div>
                          <div class="hbar"><div class="hfill" style="width:{int(prog * 100)}%;"></div></div>
                        </div>
                        """, unsafe_allow_html=True)
                    with cc2:
                        st.write("")
                        if not is_done:
                            if st.button("✓", key=f"ck{h['id']}"):
                                sb.table("habit_logs").insert({"habit_id": h["id"], "user_id": st.session_state.user_id,
                                                                "log_date": today, "logged_at": datetime.now(timezone.utc).isoformat()}).execute()
                                session_cache_clear("habit_leaderboard_habits")
                                st.rerun()
                        if st.button("🗑️", key=f"dh{h['id']}"):
                            sb.table("habits").delete().eq("id", h["id"]).execute()
                            session_cache_clear(f"community_habits_{st.session_state.user_id}")
                            session_cache_clear("habit_leaderboard_habits")
                            session_cache_clear(f"user_activity_counts_{st.session_state.user_id}")
                            st.rerun()

    with t2:
        st.markdown("### 🌍 Community Habits")
        shared = session_cache_get(
            f"community_habits_{st.session_state.user_id}",
            45,
            lambda: (sb.table("habits").select("id,user_id,username,name,emoji,frequency,created_at")
                     .eq("is_shared", True).neq("user_id", st.session_state.user_id)
                     .order("created_at", desc=True).limit(20).execute().data or [])
        )
        if not shared:
            card("<p style='color:var(--text-muted);'>No shared habits yet.</p>")
        else:
            for h in shared:
                safe_habit = escape_html(h.get("name", "Habit"))
                safe_emoji = escape_html(h.get("emoji", "⭐"))
                safe_username = escape_html(h.get("username", "user"))
                st.markdown(f"""
                <div class="card" style="padding:1.2rem;">
                  <strong style="color:var(--primary);font-size:1.05rem;">{safe_emoji} {safe_habit}</strong>
                  <span style="color:var(--text-muted);"> by @{safe_username}</span>
                  <div style="color:var(--text-muted);font-size:.8rem;margin-top:.2rem;">{h['frequency']}</div>
                </div>
                """, unsafe_allow_html=True)

    with t3:
        st.markdown("### 🏆 Habit Leaderboard")
        shared = session_cache_get(
            "habit_leaderboard_habits",
            45,
            lambda: (sb.table("habits").select("id,username,name,emoji").eq("is_shared", True).limit(60).execute().data or [])
        )
        habit_ids = [h["id"] for h in shared]
        log_rows = []
        if habit_ids:
            log_rows = sb.table("habit_logs").select("habit_id,log_date")\
                .in_("habit_id", habit_ids)\
                .gte("log_date", (date.today() - timedelta(days=400)).isoformat())\
                .execute().data or []
        logs_by_habit = {}
        for row in log_rows:
            logs_by_habit.setdefault(row["habit_id"], set()).add(row["log_date"])
        leaderboard = []
        for h in shared:
            leaderboard.append({
                "username": h.get("username", "user"),
                "habit": h.get("name", "Habit"),
                "emoji": h.get("emoji", "⭐"),
                "streak": compute_streak_from_log_dates(logs_by_habit.get(h["id"], set())),
            })
        leaderboard = sorted(leaderboard, key=lambda x: x["streak"], reverse=True)[:15]
        if not leaderboard:
            card("<p style='color:var(--text-muted);'>No shared streaks yet.</p>")
        for i, row in enumerate(leaderboard, start=1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.2rem;display:flex;justify-content:space-between;align-items:center;">
              <div><strong style="color:var(--primary);">{medal} @{escape_html(row['username'])}</strong>
              <div style="color:var(--text-secondary);font-size:.88rem;">{escape_html(row['emoji'])} {escape_html(row['habit'])}</div></div>
              <div style="font-size:1.2rem;font-weight:900;color:var(--primary);">🔥 {row['streak']}d</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# PROFILE
# ============================================================
def profile_page():
    sb = get_sb()
    sh_header("👤", "My Profile")

    u = st.session_state.user
    initials = u["username"][:2].upper()
    safe_username = escape_html(u.get("username", "user"))
    safe_bio = safe_multiline(u.get("bio") or "No bio yet.")

    avatar_url = u.get("avatar_url")

    col_av, col_inf, col_ed = st.columns([1, 4, 1])
    with col_av:
        if avatar_url and avatar_url.startswith("data:image"):
            st.markdown(f'<img src="{avatar_url}" style="width:100px;height:100px;border-radius:50%;border:3px solid var(--primary);box-shadow:0 0 60px var(--primary);object-fit:cover;">', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="av av-lg" style="margin:auto;">{initials}</div>', unsafe_allow_html=True)

    with col_inf:
        st.markdown(f"""
        <div style="padding-left:.5rem;">
          <h2 style="margin:0;font-family:'Space Grotesk',sans-serif;background:linear-gradient(135deg,var(--primary),var(--secondary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;">@{safe_username}</h2>
          <p style="color:var(--text-secondary);margin:.3rem 0 0;">{safe_bio}</p>
          <p style="color:var(--text-muted);font-size:.8rem;margin-top:.3rem;">Joined {u.get('created_at', '')[:10]}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_ed:
        if st.button("✏️ Edit Profile"):
            st.session_state.ep = not st.session_state.get("ep", False)
            st.rerun()

    if st.session_state.get("ep"):
        with st.form("epf"):
            uploaded_file = st.file_uploader("🖼️ Upload Avatar", type=["png", "jpg", "jpeg", "gif"])
            nb = st.text_area("Bio", value=u.get("bio", ""), max_chars=200)

            sv, cn = st.columns(2)
            saved = sv.form_submit_button("💾 Save", use_container_width=True)
            canceled = cn.form_submit_button("❌ Cancel", use_container_width=True)

            if saved:
                update_data = {"bio": nb}

                if uploaded_file:
                    try:
                        img = Image.open(uploaded_file)
                        img = img.resize((200, 200))
                        buffered = io.BytesIO()
                        img.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        update_data["avatar_url"] = f"data:image/png;base64,{img_str}"
                    except Exception as e:
                        st.error(f"Error uploading image: {e}")

                sb.table("profiles").update(update_data).eq("id", st.session_state.user_id).execute()
                st.session_state.user.update(update_data)
                st.session_state.ep = False
                st.success("✅ Profile updated!")
                st.rerun()

        if canceled:
            st.session_state.ep = False
            st.rerun()

    st.markdown("---")
    post_count, habit_count, _ = user_activity_counts(sb, st.session_state.user_id)
    message_count = user_sent_message_count(sb, st.session_state.user_id)

    cols = st.columns(3)
    metrics = [(post_count, "Posts"), (habit_count, "Habits"), (message_count, "Messages")]
    for col, (v, l) in zip(cols, metrics):
        col.markdown(f'<div class="metric"><div class="val">{v}</div><div class="lbl">{l}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📝 My Posts")
    my_posts = session_cache_get(
        f"profile_posts_{st.session_state.user_id}",
        20,
        lambda: (sb.table("posts").select("id,content,created_at").eq("user_id", st.session_state.user_id)
                 .order("created_at", desc=True).limit(10).execute().data or [])
    )
    if not my_posts:
        st.markdown("<p style='color:var(--text-muted);'>No posts yet.</p>", unsafe_allow_html=True)
    else:
        for p in my_posts:
            ca, cb = st.columns([5, 1])
            with ca:
                st.markdown(f"""
                <div class="post" style="padding:1.2rem 1.5rem;">
                  <p style="margin:0;color:var(--text-primary);">{linkify_mentions(p['content'])}</p>
                  <small style="color:var(--text-muted);">{ago(p['created_at'])}</small>
                </div>
                """, unsafe_allow_html=True)
            with cb:
                if st.button("🗑️", key=f"dp{p['id']}"):
                    sb.table("posts").delete().eq("id", p["id"]).execute()
                    session_cache_clear(f"profile_posts_{st.session_state.user_id}")
                    session_cache_clear(f"user_activity_counts_{st.session_state.user_id}")
                    session_cache_clear("home_feed_")
                    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================
def sidebar():
    sb = get_sb()
    with st.sidebar:
        logo_html = logo_small(40)
        st.markdown(f"""
        <div class="brand">
          <div style="display:flex;align-items:center;justify-content:center;gap:.8rem;margin-bottom:.3rem;">
            {logo_html}
            <span class="brand-name">LifeHub</span>
          </div>
          <div style="color:var(--text-muted);font-size:.7rem;">Professional Workspace</div>
        </div>
        """, unsafe_allow_html=True)

        # Unread counts for badge display
        try:
            unread_dms = sum(get_unread_counts(sb, st.session_state.user_id).values())
        except Exception:
            unread_dms = 0
        try:
            unread_mentions = get_unread_mention_count(sb, st.session_state.user_id)
        except Exception:
            unread_mentions = 0
        try:
            unread_notifications = get_unread_notification_count(sb, st.session_state.user_id)
        except Exception:
            unread_notifications = 0
        is_admin = st.session_state.user.get("is_admin", False)

        with st.container(border=True):
            c_av, c_meta = st.columns([1, 3])
            with c_av:
                st.markdown(
                    avatar_wrap_html(
                        st.session_state.username,
                        st.session_state.user.get("avatar_url"),
                        46,
                        online=True,
                    ),
                    unsafe_allow_html=True,
                )
            with c_meta:
                total_alerts = unread_mentions + unread_notifications
                alert_html = (
                    f'<span style="background:var(--danger);color:white;border-radius:99px;'
                    f'padding:.05rem .35rem;font-size:.65rem;font-weight:700;margin-left:.3rem;">{total_alerts}</span>'
                    if total_alerts else ""
                )
                st.markdown(
                    f'<div style="font-weight:700;font-size:.9rem;color:var(--primary);">@{escape_html(st.session_state.username)}</div>'
                    f'<div style="font-size:.7rem;color:var(--primary);">Active now {alert_html}</div>',
                    unsafe_allow_html=True,
                )

        if "page" not in st.session_state:
            st.session_state.page = "home"

        def nav_btn(icon, label, key, badge=0):
            badge_text = f" 🔴{badge}" if badge else ""
            active_mark = "● " if st.session_state.page == key else ""
            full_label = f"{active_mark}{icon}  {label}{badge_text}"
            if st.button(full_label, key=f"nav_{key}", use_container_width=True):
                if st.session_state.page == key:
                    return
                st.session_state.page = key
                st.session_state.viewing_user = None
                st.rerun()

        st.markdown('<div class="sb-eyebrow">Workspace</div>', unsafe_allow_html=True)
        nav_btn("🏠", "Home", "home", badge=unread_mentions)
        nav_btn("🔔", "Notifications", "notifications", badge=unread_notifications)
        nav_btn("🔎", "Discover", "discover")
        nav_btn("📡", "Channels", "channels")
        nav_btn("🤖", "AI Chat", "ai_chat")
        nav_btn("💬", "Live Chat", "live_chat", badge=unread_dms)
        nav_btn("📅", "Calendar", "calendar")
        nav_btn("✅", "Habits", "habits")
        nav_btn("👤", "Profile", "profile")
        if is_admin:
            nav_btn("🛡️", "Admin", "admin")

        st.markdown("---")
        theme_before = st.session_state.get("theme_mode", "Midnight")
        theme = st.radio("Theme", ["Midnight", "Ocean"], horizontal=True, key="theme_mode")
        if theme != theme_before:
            st.rerun()

        member_count, post_count, msg_count = get_platform_stats()
        st.markdown(f"""
        <div>
          <div class="sb-stat"><span>👥 Members</span><span class="n">{member_count}</span></div>
          <div class="sb-stat"><span>📝 Posts</span><span class="n">{post_count}</span></div>
          <div class="sb-stat"><span>💬 Messages</span><span class="n">{msg_count}</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪  Logout", use_container_width=True):
            try:
                get_sb().auth.sign_out()
            except Exception:
                pass
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    return st.session_state.page


# ============================================================
# ADMIN / MODERATION
# ============================================================
def admin_page():
    """
    Visible only to users with `is_admin = true` in their profile row.
    Run: UPDATE profiles SET is_admin = true WHERE username = 'your_username';
    in Supabase SQL Editor to grant access.
    """
    sb = get_sb()
    if not st.session_state.user.get("is_admin"):
        st.error("🛡️ Access denied — admin only.")
        return

    sh_header("🛡️", "Admin Panel")

    tab_users, tab_posts, tab_channels, tab_reports = st.tabs(["👥 Users", "📝 Posts", "📡 Channels", "🚩 Reports"])

    with tab_users:
        st.markdown("### All Members")
        users_data = session_cache_get(
            "admin_users",
            30,
            lambda: (sb.table("profiles").select("id,username,email,is_admin,is_banned,is_verified,profile_badge,created_at,last_seen")
                     .order("created_at", desc=True).execute().data or [])
        )
        for u in users_data:
            is_me = u["id"] == st.session_state.user_id
            five_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
            is_onl = (u.get("last_seen") or "") > five_ago
            safe_username = escape_html(u.get("username", "user"))
            safe_email = escape_html(u.get("email", ""))
            col_i, col_a, col_b, col_v, col_ba = st.columns([3, 1, 1, 1, 1])
            with col_i:
                st.markdown(f"""
                <div style="padding:.5rem;background:var(--card);border-radius:var(--radius);margin-bottom:.3rem;">
                  <span style="color:var(--primary);font-weight:700;">@{safe_username}</span>
                  {'<span style="color:var(--text-muted);font-size:.75rem;"> (you)</span>' if is_me else ''}
                  {'<span style="color:var(--success);font-size:.75rem;"> 🟢</span>' if is_onl else ''}
                  {'<span style="color:var(--danger);font-size:.75rem;"> BANNED</span>' if u.get("is_banned") else ''}
                  {'<span style="color:var(--primary);font-size:.75rem;"> ADMIN</span>' if u.get("is_admin") else ''}
                  <div style="color:var(--text-muted);font-size:.72rem;">{safe_email}</div>
                </div>
                """, unsafe_allow_html=True)
            if not is_me:
                with col_a:
                    action = "Unban" if u.get("is_banned") else "Ban"
                    if st.button(action, key=f"ban_{u['id']}"):
                        sb.table("profiles").update({"is_banned": not u.get("is_banned", False)}).eq("id", u["id"]).execute()
                        session_cache_clear("admin_users")
                        st.rerun()
                with col_b:
                    admin_action = "Remove Admin" if u.get("is_admin") else "Make Admin"
                    if st.button(admin_action, key=f"adm_{u['id']}"):
                        sb.table("profiles").update({"is_admin": not u.get("is_admin", False)}).eq("id", u["id"]).execute()
                        session_cache_clear("admin_users")
                        st.rerun()
                with col_v:
                    verify_action = "Unverify" if u.get("is_verified") else "Verify"
                    if st.button(verify_action, key=f"ver_{u['id']}"):
                        sb.table("profiles").update({
                            "is_verified": not u.get("is_verified", False),
                            "profile_badge": "Verified" if not u.get("is_verified", False) else "",
                        }).eq("id", u["id"]).execute()
                        session_cache_clear("admin_users")
                        st.rerun()
                with col_ba:
                    if st.button("Del Posts", key=f"delpost_{u['id']}"):
                        sb.table("posts").delete().eq("user_id", u["id"]).execute()
                        st.success(f"Deleted all posts by @{u['username']}")
                        session_cache_clear("admin_posts")
                        session_cache_clear("home_feed_")
                        st.rerun()

    with tab_posts:
        st.markdown("### Recent Posts (All Users)")
        posts_data = session_cache_get(
            "admin_posts",
            20,
            lambda: (sb.table("posts").select("id,username,content,created_at").order("created_at", desc=True).limit(50).execute().data or [])
        )
        for p in posts_data:
            safe_username = escape_html(p.get("username", "user"))
            safe_content = linkify_mentions((p.get("content") or "")[:200])
            col_p, col_d = st.columns([5, 1])
            with col_p:
                st.markdown(f"""
                <div style="background:var(--card);border-radius:var(--radius);padding:.8rem 1rem;margin-bottom:.3rem;border-left:3px solid var(--primary);">
                  <span style="color:var(--primary);font-weight:700;">@{safe_username}</span>
                  <span style="color:var(--text-muted);font-size:.72rem;"> · {ago(p['created_at'])}</span>
                  <p style="margin:.3rem 0 0;color:var(--text-primary);font-size:.88rem;">{safe_content}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_d:
                if st.button("🗑️", key=f"admdelp_{p['id']}"):
                    sb.table("posts").delete().eq("id", p["id"]).execute()
                    session_cache_clear("admin_posts")
                    session_cache_clear("home_feed_")
                    st.rerun()

    with tab_channels:
        st.markdown("### Manage Channels")
        channels_data = session_cache_get(
            "admin_channels",
            30,
            lambda: (sb.table("channels").select("id,name,description,created_at").order("created_at").execute().data or [])
        )
        channel_ids = [ch["id"] for ch in channels_data]
        def load_channel_member_counts():
            if not channel_ids:
                return {}
            try:
                rows = sb.table("channel_members").select("channel_id").in_("channel_id", channel_ids).execute().data or []
                counts = {}
                for row in rows:
                    counts[row["channel_id"]] = counts.get(row["channel_id"], 0) + 1
                return counts
            except Exception:
                return {}
        channel_member_counts = session_cache_get("admin_channel_member_counts", 30, load_channel_member_counts)
        for ch in channels_data:
            safe_channel_name = escape_html(ch.get("name", "channel"))
            safe_channel_desc = safe_multiline(ch.get("description", ""))
            col_c, col_dc = st.columns([4, 1])
            with col_c:
                member_count = channel_member_counts.get(ch["id"], 0)
                st.markdown(f"""
                <div style="background:var(--card);border-radius:var(--radius);padding:.8rem 1rem;margin-bottom:.3rem;">
                  <span style="color:var(--primary);font-weight:700;"># {safe_channel_name}</span>
                  <span style="color:var(--text-muted);font-size:.75rem;"> · {member_count} members</span>
                  <p style="margin:.2rem 0 0;color:var(--text-secondary);font-size:.82rem;">{safe_channel_desc}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_dc:
                if st.button("🗑️", key=f"admdelch_{ch['id']}"):
                    sb.table("channels").delete().eq("id", ch["id"]).execute()
                    session_cache_clear("admin_channels")
                    session_cache_clear("admin_channel_member_counts")
                    session_cache_clear("user_channels_")
                    st.rerun()

    with tab_reports:
        st.markdown("### Open Reports")
        reports_data = session_cache_get(
            "admin_reports",
            20,
            lambda: (sb.table("reports").select("id,target_type,target_id,reason,status,created_at")
                     .order("created_at", desc=True).limit(80).execute().data or [])
        )
        if not reports_data:
            st.caption("No reports yet.")
        for r in reports_data:
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.2rem;">
              <div style="display:flex;justify-content:space-between;gap:1rem;">
                <div>
                  <strong style="color:var(--primary);">{escape_html(r.get('target_type'))}</strong>
                  <span style="color:var(--text-muted);font-size:.75rem;"> · {escape_html(r.get('status'))} · {ago(r.get('created_at', ''))}</span>
                  <p style="color:var(--text-secondary);margin:.35rem 0 0;">{safe_multiline(r.get('reason', ''))}</p>
                </div>
                <code style="color:var(--text-muted);font-size:.68rem;">{escape_html(r.get('target_id'))}</code>
              </div>
            </div>
            """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Mark reviewed", key=f"review_report_{r['id']}", use_container_width=True):
                    sb.table("reports").update({"status": "reviewed"}).eq("id", r["id"]).execute()
                    session_cache_clear("admin_reports")
                    st.rerun()
            with c2:
                if st.button("Dismiss", key=f"dismiss_report_{r['id']}", use_container_width=True):
                    sb.table("reports").update({"status": "dismissed"}).eq("id", r["id"]).execute()
                    session_cache_clear("admin_reports")
                    st.rerun()


# ============================================================
# MAIN
# ============================================================
def main():
    init_session_state()
    inject_css()
    inject_theme_css()

    # Check the URL fragment for a Supabase recovery link exactly once
    # per browser session (not on every rerun — st_javascript has to
    # round-trip to the browser, and after the first determination
    # there's no reason to keep asking).
    if "recovery_check_done" not in st.session_state:
        status, access_token, refresh_token = get_recovery_tokens_from_url()

        if status == "found":
            st.session_state.recovery_access_token = access_token
            st.session_state.recovery_refresh_token = refresh_token
            st.session_state.recovery_check_done = True
        else:
            st.session_state.recovery_check_done = True

    if st.session_state.get("recovery_access_token"):
        reset_password_page()
        return

    if not st.session_state.get("recovery_check_done"):
        st.markdown(f"""
        <div style="text-align:center;padding:4rem 0;">
          {logo_img(70)}
          <p style="color:var(--text-muted);margin-top:1rem;">Loading...</p>
        </div>
        """, unsafe_allow_html=True)
        return

    if not st.session_state.get("logged_in"):
        if not st.session_state.get("_saved_login_checked"):
            restore_state = restore_login_from_saved_tokens()
            st.session_state["_saved_login_checked"] = True
            if restore_state == "restored":
                st.rerun()
            if restore_state == "invalid":
                clear_auth_tokens_from_browser()
        auth_page()
        return

    sb = get_sb()
    if not refresh_current_user_session(sb):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.username = ""
        clear_auth_tokens_from_browser()
        st.error("Your session expired or your profile could not be loaded. Please sign in again.")
        return

    try:
        profile_param = st.query_params.get("profile")
        if profile_param and not st.session_state.get("viewing_user"):
            profile_user = get_user_by_username(profile_param)
            if profile_user:
                st.session_state.viewing_user = profile_user["id"]
    except Exception:
        pass

    page = sidebar()

    # Profile overlay takes priority over the active page, but never
    # blocks the sidebar — clicking any nav button clears it (see sidebar()).
    if st.session_state.get("viewing_user"):
        view_user_profile(st.session_state.viewing_user)
        return

    pages = {
        "home": home_page,
        "notifications": notifications_page,
        "discover": discover_page,
        "channels": channels_page,
        "ai_chat": ai_chat_page,
        "live_chat": live_chat_page,
        "calendar": calendar_page,
        "habits": habits_page,
        "profile": profile_page,
        "admin": admin_page,
    }
    pages.get(page, home_page)()


if __name__ == "__main__":
    main()
