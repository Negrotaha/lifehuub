# ============================================================
# LifeHub — Premium Social Platform (Discord-Inspired Dark + Blurple)
# Streamlit + Supabase + Groq AI
# ============================================================

import os, time, hashlib, base64, requests, io, html
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
  --bg0: #000000;
  --bg1: #0a0a0c;
  --bg2: #111114;
  --bg3: #1a1a1f;
  --bg4: #222228;
  --card: #0d0d10;
  --card2: #16161b;
  --border: rgba(88, 101, 242, 0.25);
  --border2: rgba(88, 101, 242, 0.10);
  --yellow: #5865F2;
  --yellow2: #4752C4;
  --yellow3: #6E7CF7;
  --yellow4: #3C45A5;
  --glow: rgba(88, 101, 242, 0.35);
  --glow2: rgba(88, 101, 242, 0.12);
  --glow3: rgba(88, 101, 242, 0.55);
  --t: #f2f3f5;
  --t2: #b5bac1;
  --t3: #6d6f78;
  --green: #23A55A;
  --red: #F23F42;
  --gold: #5865F2;
  --blue: #5865F2;
  --r: 12px;
  --r2: 18px;
  --r3: 24px;
}

*,*::before,*::after{box-sizing:border-box;}
html,body,.stApp{background:var(--bg0)!important;color:var(--t)!important;font-family:'Inter',sans-serif!important;}

/* Animated background with particles */
.stApp::before{
  content:'';position:fixed;inset:0;
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(88,101,242,0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(88,101,242,0.02) 0%, transparent 40%),
    radial-gradient(circle at 50% 80%, rgba(88,101,242,0.03) 0%, transparent 50%);
  pointer-events:none;
  z-index:0;
}

/* Grid overlay (static — animating a full-viewport grid every frame is expensive) */
.stApp::after {
  content: '';
  position: fixed;
  inset: 0;
  background-image: 
    linear-gradient(rgba(88,101,242,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(88,101,242,0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
  z-index: 0;
}

/* Sidebar - Premium */
section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #050505 0%, #0a0a0a 100%)!important;
  border-right: 1px solid rgba(88,101,242,0.12)!important;
  box-shadow: 4px 0 80px rgba(88,101,242,0.05)!important;
}
section[data-testid="stSidebar"]>div{padding-top:0!important;}

.main .block-container{padding:1.5rem 2.5rem!important;max-width:1400px!important;}

/* Premium Inputs */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input{
  background: var(--bg2)!important;
  color: var(--t)!important;
  border: 1px solid rgba(88,101,242,0.1)!important;
  border-radius: var(--r)!important;
  font-family:'Inter',sans-serif!important;
  transition: all 0.4s cubic-bezier(.34,1.56,.64,1)!important;
  padding: 0.75rem 1rem!important;
}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus{
  border-color: var(--yellow)!important;
  box-shadow: 0 0 30px var(--glow), 0 0 60px var(--glow2)!important;
  background: var(--bg3)!important;
  transform: scale(1.02);
}

/* Premium Buttons */
.stButton>button{
  background: linear-gradient(135deg, var(--yellow) 0%, var(--yellow3) 100%)!important;
  color: #000000!important;
  border: none!important;
  border-radius: var(--r)!important;
  font-family:'Inter',sans-serif!important;
  font-weight: 700!important;
  letter-spacing: .03em!important;
  transition: all 0.4s cubic-bezier(.34,1.56,.64,1)!important;
  box-shadow: 0 0 40px var(--glow), 0 0 80px var(--glow2), 0 1px 0 rgba(255,255,255,.2) inset!important;
  position:relative!important;
  overflow:hidden!important;
  padding: 0.6rem 1.5rem!important;
}
.stButton>button:hover{
  transform: translateY(-3px) scale(1.03)!important;
  box-shadow: 0 0 60px var(--glow3), 0 0 100px var(--glow2)!important;
}
.stButton>button:active{
  transform: translateY(0) scale(.97)!important;
}
.stButton>button::after{
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.4s;
}
.stButton>button:hover::after{
  opacity: 1;
}

/* Premium Tabs */
.stTabs [data-baseweb="tab-list"]{
  background: var(--bg2)!important;
  border-radius: var(--r)!important;
  padding: 6px!important;
  gap: 6px!important;
  border: 1px solid rgba(88,101,242,0.08)!important;
}
.stTabs [data-baseweb="tab"]{
  background: transparent!important;
  color: var(--t2)!important;
  border-radius: 10px!important;
  font-weight: 500!important;
  transition: all 0.4s!important;
  padding: 0.6rem 1.2rem!important;
}
.stTabs [aria-selected="true"]{
  background: linear-gradient(135deg, var(--yellow), var(--yellow3))!important;
  color: #000000!important;
  box-shadow: 0 0 40px var(--glow)!important;
  font-weight: 700!important;
  transform: scale(1.05);
}

/* Premium Cards */
.card{
  background: linear-gradient(145deg, var(--card) 0%, var(--card2) 100%);
  border: 1px solid rgba(88,101,242,0.08);
  border-radius: var(--r3);
  padding: 1.8rem;
  margin-bottom: 1rem;
  box-shadow: 0 8px 32px rgba(0,0,0,.6);
  transition: all 0.5s cubic-bezier(.34,1.56,.64,1);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(10px);
}
.card::before{
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--yellow), transparent);
  animation: scanline 4s linear infinite;
}
.card::after{
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 30%, rgba(88,101,242,0.03) 0%, transparent 70%);
  pointer-events: none;
}
@keyframes scanline {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.card:hover{
  transform: translateY(-6px) scale(1.01);
  border-color: rgba(88,101,242,0.3);
  box-shadow: 0 20px 60px rgba(0,0,0,.8), 0 0 60px var(--glow2), 0 0 120px var(--glow2);
}

/* Premium Metrics */
.metric{
  background: linear-gradient(145deg, var(--card) 0%, var(--bg4) 100%);
  border: 1px solid rgba(88,101,242,0.08);
  border-radius: var(--r3);
  padding: 2rem;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,.5);
  transition: all 0.5s cubic-bezier(.34,1.56,.64,1);
}
.metric::after{
  content: '';
  position: absolute;
  bottom: -40px;
  right: -40px;
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, var(--glow2) 0%, transparent 70%);
  pointer-events: none;
  animation: glowPulse 4s ease-in-out infinite;
}
@keyframes glowPulse {
  0%, 100% { opacity: 0.3; transform: scale(1) rotate(0deg); }
  50% { opacity: 1; transform: scale(1.5) rotate(180deg); }
}
.metric:hover{
  transform: translateY(-8px) rotateX(5deg);
  box-shadow: 0 20px 60px rgba(0,0,0,.7), 0 0 80px var(--glow2);
  border-color: rgba(88,101,242,0.3);
}
.metric .val{
  font-size: 3rem;
  font-weight: 900;
  color: var(--yellow);
  font-family:'Space Grotesk',sans-serif;
  text-shadow: 0 0 40px var(--glow);
  animation: numberGlow 2s ease-in-out infinite;
}
@keyframes numberGlow {
  0%, 100% { text-shadow: 0 0 40px var(--glow); }
  50% { text-shadow: 0 0 80px var(--glow3); }
}
.metric .lbl{
  font-size: .8rem;
  color: var(--t3);
  margin-top: .4rem;
  text-transform: uppercase;
  letter-spacing: .15em;
}

/* Section Header */
.sh{
  font-size: 2rem;
  font-weight: 900;
  color: var(--t);
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: .8rem;
  font-family:'Space Grotesk',sans-serif;
  text-shadow: 0 0 60px var(--glow2);
}
.sh::after{
  content: '';
  flex: 1;
  height: 2px;
  background: linear-gradient(90deg, var(--yellow), transparent);
  margin-left: .5rem;
  box-shadow: 0 0 30px var(--glow);
}

/* Chat Bubbles Premium */
.bme{
  background: linear-gradient(135deg, var(--yellow), var(--yellow3))!important;
  color: #000000!important;
  padding: 1rem 1.4rem;
  border-radius: 20px 20px 4px 20px;
  margin: .5rem 0;
  max-width: 75%;
  margin-left: auto;
  box-shadow: 0 8px 30px var(--glow), 0 0 60px var(--glow2);
  font-size: .95rem;
  line-height: 1.6;
  font-weight: 500;
  animation: slideInRight 0.5s cubic-bezier(.34,1.56,.64,1);
}
.bother{
  background: var(--card2)!important;
  color: var(--t)!important;
  padding: 1rem 1.4rem;
  border-radius: 20px 20px 20px 4px;
  margin: .5rem 0;
  max-width: 75%;
  border: 1px solid rgba(88,101,242,0.1);
  font-size: .95rem;
  line-height: 1.6;
  animation: slideInLeft 0.5s cubic-bezier(.34,1.56,.64,1);
}
@keyframes slideInRight {
  from { opacity: 0; transform: translateX(50px) scale(0.9); }
  to { opacity: 1; transform: translateX(0) scale(1); }
}
@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-50px) scale(0.9); }
  to { opacity: 1; transform: translateX(0) scale(1); }
}
.bmeta{
  font-size: .7rem;
  color: rgba(0,0,0,.6);
  margin-top: .3rem;
}
.bmeta-other{
  font-size: .7rem;
  color: var(--t3);
  margin-top: .3rem;
}

/* Premium Posts */
.post{
  background: var(--card);
  border: 1px solid rgba(88,101,242,0.06);
  border-radius: var(--r3);
  padding: 1.5rem 1.8rem;
  margin-bottom: 1rem;
  transition: all 0.5s cubic-bezier(.34,1.56,.64,1);
  position: relative;
  overflow: hidden;
  cursor: pointer;
}
.post:hover{
  border-color: rgba(88,101,242,0.25);
  transform: translateX(8px) scale(1.01);
  box-shadow: 0 0 50px var(--glow2);
}
.post::before{
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, var(--yellow), var(--yellow4));
  border-radius: 4px 0 0 4px;
  box-shadow: 0 0 30px var(--glow);
}

/* Premium Avatar */
.av{
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 800;
  color: #000000;
  background: linear-gradient(135deg, var(--yellow), var(--yellow3));
  box-shadow: 0 0 30px var(--glow);
  flex-shrink: 0;
  transition: all 0.4s;
}
.av:hover {
  transform: scale(1.1) rotate(10deg);
  box-shadow: 0 0 50px var(--glow3);
}
.av-lg{
  width: 100px;
  height: 100px;
  font-size: 2.5rem;
  box-shadow: 0 0 60px var(--glow), 0 0 120px var(--glow2);
}
.av-clickable {
  cursor: pointer;
}

/* Auth Hero Premium */
.hero{
  text-align: center;
  padding: 3rem 0 2rem;
  animation: fadeDown 1s cubic-bezier(.34,1.56,.64,1);
}
@keyframes fadeDown{
  from{ opacity: 0; transform: translateY(-60px) scale(0.9); }
  to{ opacity: 1; transform: translateY(0) scale(1); }
}
.hero-logo-img{
  animation: float 4s ease-in-out infinite;
  display: inline-block;
  filter: drop-shadow(0 0 60px var(--glow));
}
.hero-logo-emoji{
  font-size: 5rem;
  animation: float 4s ease-in-out infinite;
  display: inline-block;
}
@keyframes float{
  0%, 100%{ transform: translateY(0) rotate(-3deg); }
  50%{ transform: translateY(-20px) rotate(3deg); }
}
.hero-title{
  font-size: 4rem;
  font-weight: 900;
  font-family:'Space Grotesk',sans-serif;
  background: linear-gradient(135deg, var(--yellow) 0%, var(--yellow3) 50%, var(--yellow4) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: .6rem 0;
  line-height: 1.1;
  text-shadow: 0 0 80px var(--glow);
  animation: titleGlow 3s ease-in-out infinite;
}
@keyframes titleGlow {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(1.3); }
}
.hero-sub{
  color: var(--t2);
  font-size: 1.1rem;
  margin-top: .3rem;
}

/* Premium Brand */
.brand{
  padding: 1.5rem 1rem 1rem;
  text-align: center;
  border-bottom: 1px solid rgba(88,101,242,0.08);
  margin-bottom: 1rem;
}
.brand-name{
  font-size: 1.8rem;
  font-weight: 900;
  font-family:'Space Grotesk',sans-serif;
  background: linear-gradient(135deg, var(--yellow), var(--yellow4));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 60px var(--glow);
}

/* User Badge Premium */
.ubadge{
  display: flex;
  align-items: center;
  gap: .8rem;
  background: var(--bg2);
  border: 1px solid rgba(88,101,242,0.1);
  border-radius: var(--r2);
  padding: 1rem;
  margin: .5rem 0 1rem;
  box-shadow: 0 0 30px var(--glow2);
  transition: all 0.4s;
}
.ubadge:hover {
  transform: scale(1.02);
  border-color: rgba(88,101,242,0.3);
  box-shadow: 0 0 50px var(--glow2);
}

/* Online Indicator — bold, solid, no animation */
.online{
  display: inline-block;
  width: 9px;
  height: 9px;
  background: var(--green);
  border-radius: 50%;
  margin-right: 6px;
}

/* Scrollbar Premium */
::-webkit-scrollbar{width: 6px;height: 6px;}
::-webkit-scrollbar-track{background: var(--bg0);}
::-webkit-scrollbar-thumb{background: var(--yellow);border-radius: 99px;box-shadow: 0 0 20px var(--glow);}

/* Hide Chrome — but KEEP the sidebar collapse/expand control visible */
#MainMenu, footer, .stDeployButton { visibility:hidden!important; display:none!important; }

/* The header itself must stay (it hosts the sidebar toggle arrow) —
   just make it transparent so it blends with the page instead of
   showing the default Streamlit toolbar background. */
header[data-testid="stHeader"] {
  background: transparent !important;
  height: auto !important;
}

/* Style the sidebar collapse/expand arrow so it's always visible
   and matches the blurple theme, even when sidebar is closed.
   Multiple selectors included as fallbacks across Streamlit versions. */
button[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarCollapsedControl"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] button {
  visibility: visible !important;
  display: flex !important;
  opacity: 1 !important;
  background: var(--bg2) !important;
  border: 1px solid rgba(88,101,242,0.25) !important;
  border-radius: 10px !important;
  box-shadow: 0 0 20px var(--glow2) !important;
  color: var(--yellow) !important;
  z-index: 999999 !important;
}
button[data-testid="stSidebarCollapseButton"]:hover,
button[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="collapsedControl"]:hover {
  box-shadow: 0 0 30px var(--glow) !important;
  border-color: var(--yellow) !important;
}
button[data-testid="stSidebarCollapseButton"] svg,
button[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg {
  fill: var(--yellow) !important;
  stroke: var(--yellow) !important;
}

/* File Uploader Premium */
.stFileUploader>div>div>div>div {
  background: var(--bg2)!important;
  border: 2px dashed rgba(88,101,242,0.2)!important;
  border-radius: var(--r2)!important;
  color: var(--t2)!important;
  transition: all 0.4s!important;
}
.stFileUploader>div>div>div>div:hover {
  border-color: var(--yellow)!important;
  box-shadow: 0 0 40px var(--glow2)!important;
}

/* Badge Premium */
.badge{
  display: inline-block;
  background: var(--yellow);
  color: #000000;
  padding: .15rem .7rem;
  border-radius: 99px;
  font-size: .7rem;
  font-weight: 700;
  margin-left: .4rem;
  box-shadow: 0 0 20px var(--glow);
  animation: badgePulse 2s ease-in-out infinite;
}
@keyframes badgePulse {
  0%, 100% { box-shadow: 0 0 20px var(--glow); }
  50% { box-shadow: 0 0 40px var(--glow3); }
}

/* View User Profile Card */
.user-profile-card {
  background: linear-gradient(145deg, var(--card) 0%, var(--card2) 100%);
  border: 1px solid rgba(88,101,242,0.15);
  border-radius: var(--r3);
  padding: 2rem;
  margin: 1rem 0;
  box-shadow: 0 8px 40px rgba(0,0,0,.6);
}

/* Event Card */
.ev-card{
  background: var(--card);
  border-radius: var(--r);
  padding: 1rem 1.2rem;
  margin-bottom: .6rem;
  border-left: 3px solid var(--yellow);
  transition: all 0.3s ease;
}
.ev-card:hover{
  background: var(--card2);
  transform: translateX(5px);
  box-shadow: 0 0 20px var(--glow2);
}

/* ============================================================
   3D ROTATING CUBE — Login page signature element
   Pure CSS transforms, no JS/WebGL dependency.
   Each face represents a LifeHub module.
   ============================================================ */
.cube-stage {
  width: 100%;
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 1000px;
  margin: 1rem 0 1.5rem;
}
.cube {
  position: relative;
  width: 140px;
  height: 140px;
  transform-style: preserve-3d;
  animation: cubeSpin 16s linear infinite;
}
@keyframes cubeSpin {
  0%   { transform: rotateX(-20deg) rotateY(0deg); }
  100% { transform: rotateX(-20deg) rotateY(360deg); }
}
.cube-face {
  position: absolute;
  width: 140px;
  height: 140px;
  background: linear-gradient(145deg, rgba(20,20,20,0.95), rgba(10,10,10,0.95));
  border: 1px solid rgba(88,101,242,0.35);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  box-shadow: 0 0 40px rgba(88,101,242,0.12), inset 0 0 30px rgba(88,101,242,0.04);
  backdrop-filter: blur(4px);
}
.cube-face .ico { font-size: 2.2rem; filter: drop-shadow(0 0 10px rgba(88,101,242,0.5)); }
.cube-face .lbl { font-size: 0.68rem; color: var(--yellow); text-transform: uppercase; letter-spacing: 0.12em; font-weight: 700; }
.cube-face.front  { transform: translateZ(70px); }
.cube-face.back   { transform: rotateY(180deg) translateZ(70px); }
.cube-face.right  { transform: rotateY(90deg) translateZ(70px); }
.cube-face.left   { transform: rotateY(-90deg) translateZ(70px); }
.cube-face.top    { transform: rotateX(90deg) translateZ(70px); }
.cube-face.bottom { transform: rotateX(-90deg) translateZ(70px); }

/* Soft floor reflection under the cube for depth */
.cube-stage::after {
  content: '';
  position: absolute;
  width: 160px;
  height: 30px;
  margin-top: 200px;
  background: radial-gradient(ellipse, rgba(88,101,242,0.18), transparent 70%);
  filter: blur(4px);
}

@media (prefers-reduced-motion: reduce) {
  .cube { animation: none; transform: rotateX(-20deg) rotateY(35deg); }
}

/* Sidebar nav — active/inactive states (previously unstyled — buttons
   all looked identical regardless of which page was selected) */
.nav-active .stButton>button{
  background: linear-gradient(135deg, var(--yellow), var(--yellow3))!important;
  color: #000000!important;
  font-weight: 800!important;
  box-shadow: 0 0 30px var(--glow), 0 1px 0 rgba(255,255,255,.25) inset!important;
  transform: scale(1.02);
}
.nav-inactive .stButton>button{
  background: var(--bg2)!important;
  color: var(--t2)!important;
  box-shadow: none!important;
  border: 1px solid rgba(88,101,242,0.06)!important;
  font-weight: 500!important;
}
.nav-inactive .stButton>button:hover{
  background: var(--bg3)!important;
  color: var(--yellow)!important;
  border-color: rgba(88,101,242,0.25)!important;
}

/* Sidebar avatar — rotating gradient ring */
.av-ring {
  position: relative;
  width: 42px; height: 42px;
  border-radius: 50%;
  padding: 2px;
  background: conic-gradient(from 0deg, var(--yellow), transparent 40%, var(--yellow));
  animation: ringSpin 4s linear infinite;
  flex-shrink: 0;
}
.av-ring-inner {
  width: 100%; height: 100%;
  border-radius: 50%;
  background: var(--bg1);
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}
@keyframes ringSpin { to { transform: rotate(360deg); } }

/* Sidebar live stat row */
.sb-stat {
  display: flex; justify-content: space-between; align-items: center;
  padding: .35rem .1rem;
  font-size: .78rem;
  color: var(--t2);
}
.sb-stat .n {
  color: var(--yellow);
  font-weight: 700;
  font-family: 'Space Grotesk', sans-serif;
}

/* ============================================================
   DISCORD-STYLE PATTERNS
   (now full Discord-inspired dark + blurple palette)
   ============================================================ */

/* Status badge: a small dot anchored to the avatar's corner —
   bold and simple, no extra animation layered on top of it. */
.av-wrap { position: relative; display: inline-flex; flex-shrink: 0; }
.status-badge {
  position: absolute;
  bottom: -1px; right: -1px;
  width: 15px; height: 15px;
  border-radius: 50%;
  border: 3px solid var(--bg1);
}
.status-badge.on  { background: var(--green); }
.status-badge.off { background: #5c5e66; }

/* Channel-list style sidebar nav — tighter, left-aligned icon+label,
   small uppercase section eyebrow like Discord's "TEXT CHANNELS". */
.sb-eyebrow {
  font-size: .68rem;
  font-weight: 700;
  color: var(--t3);
  text-transform: uppercase;
  letter-spacing: .1em;
  padding: .6rem .3rem .3rem;
}

/* Message grouping — consecutive messages from the same sender
   collapse: avatar+name shown once, follow-up lines sit flush
   under it with just a faint hover-revealed timestamp, exactly
   like Discord's chat log instead of repeating bubbles. */
.msg-group { display: flex; gap: .7rem; margin: .9rem 0 .2rem; }
.msg-group .av-wrap { margin-top: 2px; }
.msg-group-body { flex: 1; min-width: 0; }
.msg-group-head { display: flex; align-items: baseline; gap: .5rem; margin-bottom: .15rem; }
.msg-group-name { font-weight: 700; font-size: .92rem; color: var(--yellow); }
.msg-group-time { font-size: .68rem; color: var(--t3); }
.msg-line {
  color: var(--t);
  font-size: .92rem;
  line-height: 1.5;
  padding: .1rem 0;
  border-radius: 6px;
  transition: background .15s ease;
}
.msg-line:hover { background: rgba(88,101,242,0.03); }
.msg-line .msg-time-hover {
  opacity: 0;
  font-size: .65rem;
  color: var(--t3);
  margin-right: .5rem;
  transition: opacity .15s ease;
}
.msg-line:hover .msg-time-hover { opacity: 1; }
.msg-group.mine .msg-group-name { color: var(--t); }
.msg-group.mine { flex-direction: row-reverse; text-align: right; }
.msg-group.mine .msg-group-head { flex-direction: row-reverse; }

/* ── Member List Panel (Discord's right-side member sidebar) ── */
.member-panel {
  background: var(--bg1);
  border: 1px solid rgba(88,101,242,0.08);
  border-radius: var(--r2);
  padding: 1rem;
}
.member-category {
  font-size: .68rem;
  font-weight: 700;
  color: var(--t3);
  text-transform: uppercase;
  letter-spacing: .08em;
  padding: .5rem .3rem .4rem;
}
.member-row {
  display: flex;
  align-items: center;
  gap: .6rem;
  padding: .4rem .3rem;
  border-radius: 8px;
  transition: background .15s ease;
  cursor: pointer;
}
.member-row:hover { background: rgba(88,101,242,0.08); }
.member-row .name {
  font-size: .85rem;
  font-weight: 500;
  color: var(--t2);
}
.member-row.online .name { color: var(--t); }
.member-row .av-sm {
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: .65rem; font-weight: 800; color: #000;
  background: linear-gradient(135deg, var(--yellow), var(--yellow3));
  flex-shrink: 0;
  overflow: hidden;
}

/* ============================================================
   PROFESSIONAL PRODUCT REDESIGN
   Final override layer: calmer SaaS visual system used across
   every Streamlit page without changing page logic.
   ============================================================ */
:root {
  --bg0: #070a12;
  --bg1: #0b1020;
  --bg2: #111827;
  --bg3: #172033;
  --bg4: #1f2937;
  --card: rgba(15, 23, 42, 0.92);
  --card2: rgba(17, 24, 39, 0.96);
  --border: rgba(148, 163, 184, 0.18);
  --border2: rgba(148, 163, 184, 0.10);
  --yellow: #7c3aed;
  --yellow2: #6d28d9;
  --yellow3: #38bdf8;
  --yellow4: #4f46e5;
  --glow: rgba(124, 58, 237, 0.22);
  --glow2: rgba(56, 189, 248, 0.12);
  --glow3: rgba(124, 58, 237, 0.30);
  --t: #f8fafc;
  --t2: #cbd5e1;
  --t3: #94a3b8;
  --green: #10b981;
  --red: #ef4444;
  --gold: #f59e0b;
  --blue: #38bdf8;
  --r: 10px;
  --r2: 16px;
  --r3: 22px;
}

html, body, .stApp {
  background:
    radial-gradient(circle at 10% 0%, rgba(124,58,237,.16), transparent 34%),
    radial-gradient(circle at 88% 8%, rgba(56,189,248,.12), transparent 32%),
    linear-gradient(135deg, #070a12 0%, #0b1020 42%, #0f172a 100%) !important;
  color: var(--t) !important;
}

.stApp::before {
  background:
    linear-gradient(120deg, rgba(255,255,255,.035), transparent 28%, rgba(255,255,255,.018) 62%, transparent),
    radial-gradient(circle at 50% 100%, rgba(15,23,42,.9), transparent 48%) !important;
}
.stApp::after {
  opacity: .28;
  background-image:
    linear-gradient(rgba(148,163,184,.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148,163,184,.05) 1px, transparent 1px) !important;
  background-size: 72px 72px !important;
}

.main .block-container {
  max-width: 1280px !important;
  padding: 2rem 2.25rem 3rem !important;
}

section[data-testid="stSidebar"] {
  background: rgba(7, 10, 18, .94) !important;
  border-right: 1px solid rgba(148,163,184,.14) !important;
  box-shadow: 12px 0 50px rgba(0,0,0,.24) !important;
  backdrop-filter: blur(18px);
}

.brand {
  text-align: left;
  padding: 1.25rem .8rem 1rem;
  border-bottom: 1px solid var(--border2);
}
.brand > div:first-child {
  justify-content: flex-start !important;
}
.brand-name {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.45rem;
  letter-spacing: -.03em;
  background: linear-gradient(135deg, #f8fafc, #a78bfa 56%, #38bdf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: none;
}

.ubadge, .member-panel, .user-profile-card,
.card, .post, .metric, .ev-card {
  background: linear-gradient(180deg, rgba(15,23,42,.94), rgba(17,24,39,.92)) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 18px 45px rgba(0,0,0,.24) !important;
  backdrop-filter: blur(14px);
}

.card, .post, .metric, .ev-card, .user-profile-card {
  border-radius: var(--r3) !important;
}
.card::before, .card::after, .metric::after {
  display: none !important;
}
.card:hover, .post:hover, .metric:hover, .ev-card:hover, .ubadge:hover {
  transform: translateY(-2px) !important;
  border-color: rgba(124,58,237,.34) !important;
  box-shadow: 0 22px 55px rgba(0,0,0,.30), 0 0 0 1px rgba(124,58,237,.10) inset !important;
}

.sh {
  font-size: 1.8rem;
  font-weight: 800;
  letter-spacing: -.035em;
  margin-bottom: 1.4rem;
  text-shadow: none;
}
.sh::after {
  height: 1px;
  background: linear-gradient(90deg, rgba(124,58,237,.65), rgba(56,189,248,.18), transparent);
  box-shadow: none;
}

.stButton>button {
  background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255,255,255,.10) !important;
  border-radius: 12px !important;
  box-shadow: 0 10px 28px rgba(79,70,229,.22) !important;
  font-weight: 700 !important;
  letter-spacing: -.01em !important;
  transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease, background .16s ease !important;
}
.stButton>button::after {
  display: none !important;
}
.stButton>button:hover {
  transform: translateY(-1px) !important;
  border-color: rgba(255,255,255,.22) !important;
  box-shadow: 0 14px 34px rgba(79,70,229,.28) !important;
}
.stButton>button:active {
  transform: translateY(0) !important;
}

.nav-active .stButton>button {
  background: linear-gradient(135deg, rgba(124,58,237,.98), rgba(56,189,248,.78)) !important;
  color: #fff !important;
  box-shadow: 0 12px 30px rgba(56,189,248,.14), 0 0 0 1px rgba(255,255,255,.08) inset !important;
  transform: none !important;
}
.nav-inactive .stButton>button {
  background: rgba(15,23,42,.72) !important;
  color: var(--t2) !important;
  border: 1px solid rgba(148,163,184,.12) !important;
  box-shadow: none !important;
}
.nav-inactive .stButton>button:hover {
  background: rgba(30,41,59,.9) !important;
  color: #fff !important;
  border-color: rgba(124,58,237,.32) !important;
}

.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input,
.stSelectbox [data-baseweb="select"],
.stDateInput input,
.stTimeInput input {
  background: rgba(15,23,42,.88) !important;
  color: var(--t) !important;
  border: 1px solid rgba(148,163,184,.18) !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 0 rgba(255,255,255,.04) inset !important;
  transition: border-color .16s ease, box-shadow .16s ease, background .16s ease !important;
}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus,
.stNumberInput>div>div>input:focus,
.stDateInput input:focus,
.stTimeInput input:focus {
  background: rgba(15,23,42,.98) !important;
  border-color: rgba(124,58,237,.75) !important;
  box-shadow: 0 0 0 3px rgba(124,58,237,.18) !important;
  transform: none !important;
}

.stTabs [data-baseweb="tab-list"] {
  background: rgba(15,23,42,.72) !important;
  border: 1px solid rgba(148,163,184,.14) !important;
  border-radius: 14px !important;
  padding: 5px !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px !important;
  color: var(--t3) !important;
  font-weight: 700 !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(124,58,237,.18) !important;
  color: #fff !important;
  box-shadow: 0 0 0 1px rgba(124,58,237,.28) inset !important;
  transform: none !important;
}

.post {
  cursor: default;
}
.post::before {
  width: 3px;
  background: linear-gradient(180deg, #7c3aed, #38bdf8);
  box-shadow: none;
}

.metric {
  padding: 1.4rem !important;
}
.metric .val {
  font-size: 2.25rem;
  color: #ffffff;
  text-shadow: none;
  animation: none;
}
.metric .lbl {
  color: var(--t3);
  letter-spacing: .10em;
}

.av, .member-row .av-sm {
  color: #fff !important;
  background: linear-gradient(135deg, #7c3aed, #38bdf8) !important;
  box-shadow: 0 10px 24px rgba(79,70,229,.20) !important;
}
.av:hover {
  transform: none !important;
}

.bme {
  background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
  color: #fff !important;
  box-shadow: 0 12px 30px rgba(79,70,229,.22) !important;
  animation: none !important;
}
.bother {
  background: rgba(15,23,42,.92) !important;
  border: 1px solid rgba(148,163,184,.14) !important;
  animation: none !important;
}
.bmeta {
  color: rgba(255,255,255,.72);
}

.msg-group {
  margin: .8rem 0;
}
.msg-line {
  color: var(--t2);
  padding: .22rem .35rem;
}
.msg-line:hover {
  background: rgba(124,58,237,.08);
}
.msg-group-name {
  color: #a78bfa;
}
.msg-group.mine .msg-group-name {
  color: #38bdf8;
}

.badge {
  background: rgba(56,189,248,.14);
  color: #bae6fd;
  border: 1px solid rgba(56,189,248,.22);
  box-shadow: none;
  animation: none;
}

.sb-eyebrow, .member-category {
  color: var(--t3);
  font-size: .66rem;
  letter-spacing: .12em;
}
.sb-stat {
  padding: .48rem .1rem;
  border-bottom: 1px solid rgba(148,163,184,.07);
}
.sb-stat .n {
  color: #bae6fd;
}

.stFileUploader>div>div>div>div {
  background: rgba(15,23,42,.72) !important;
  border: 1.5px dashed rgba(148,163,184,.28) !important;
}
.stFileUploader>div>div>div>div:hover {
  border-color: rgba(56,189,248,.55) !important;
  box-shadow: 0 0 0 3px rgba(56,189,248,.10) !important;
}

.cube-stage {
  height: 240px;
}
.cube, .hero-logo-img, .hero-logo-emoji {
  animation-duration: 28s !important;
}
.cube-face {
  background: linear-gradient(145deg, rgba(15,23,42,.96), rgba(30,41,59,.94));
  border-color: rgba(148,163,184,.22);
  box-shadow: 0 18px 40px rgba(0,0,0,.30), inset 0 0 0 1px rgba(255,255,255,.04);
}
.cube-face .lbl {
  color: #bae6fd;
}

hr {
  border-color: rgba(148,163,184,.10) !important;
}

div[data-testid="stExpander"] {
  background: rgba(15,23,42,.64) !important;
  border: 1px solid rgba(148,163,184,.14) !important;
  border-radius: var(--r2) !important;
  overflow: hidden;
}

/* ============================================================
   ENTERPRISE BLUE 3D THEME
   Lightweight motion layer. No constant card/avatar animations.
   ============================================================ */
@keyframes appAurora {
  0% { background-position: 0% 0%, 100% 0%, 0% 50%; }
  50% { background-position: 100% 50%, 0% 100%, 100% 50%; }
  100% { background-position: 0% 0%, 100% 0%, 0% 50%; }
}
@keyframes floatOrb {
  0%, 100% { transform: translate3d(0,0,0) scale(1); opacity: .72; }
  50% { transform: translate3d(28px,-22px,0) scale(1.08); opacity: 1; }
}
@keyframes fadeUpSoft {
  from { opacity: 0; transform: translateY(18px); filter: blur(4px); }
  to { opacity: 1; transform: translateY(0); filter: blur(0); }
}
@keyframes pulseBlue {
  0%, 100% { box-shadow: 0 0 0 1px rgba(59,130,246,.18), 0 18px 50px rgba(2,6,23,.32); }
  50% { box-shadow: 0 0 0 1px rgba(56,189,248,.38), 0 22px 70px rgba(37,99,235,.28); }
}
@keyframes borderFlow {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}
@keyframes shimmerText {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}
@keyframes popIn {
  from { opacity: 0; transform: scale(.96) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

html, body, .stApp {
  background:
    radial-gradient(circle at 15% 12%, rgba(37,99,235,.28), transparent 30%),
    radial-gradient(circle at 86% 18%, rgba(14,165,233,.24), transparent 28%),
    radial-gradient(circle at 50% 90%, rgba(30,64,175,.22), transparent 32%),
    linear-gradient(135deg, #020617, #07111f 42%, #0b1730 100%) !important;
  background-size: 100% 100% !important;
  animation: none !important;
}
.stApp::before {
  background:
    radial-gradient(circle at 20% 25%, rgba(56,189,248,.12), transparent 24%),
    radial-gradient(circle at 80% 15%, rgba(59,130,246,.16), transparent 26%),
    linear-gradient(120deg, rgba(255,255,255,.05), transparent 32%, rgba(56,189,248,.04) 64%, transparent) !important;
  animation: none !important;
}
.stApp::after {
  opacity: .42;
  background-image:
    linear-gradient(rgba(96,165,250,.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(96,165,250,.07) 1px, transparent 1px) !important;
}

.main .block-container > div {
  animation: fadeUpSoft .55s ease both;
}

.brand-name, .hero-title {
  background: linear-gradient(90deg, #60a5fa, #38bdf8, #818cf8, #60a5fa) !important;
  background-size: 200% auto !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  animation: none !important;
}

.card, .post, .metric, .ev-card, .user-profile-card,
.member-panel, div[data-testid="stForm"] {
  position: relative;
  overflow: hidden;
}
.card::before, .post::after, .metric::before,
.user-profile-card::before, div[data-testid="stForm"]::before {
  content: "";
  position: absolute;
  inset: 0;
  padding: 1px;
  border-radius: inherit;
  background: linear-gradient(110deg, rgba(37,99,235,.0), rgba(56,189,248,.56), rgba(129,140,248,.38), rgba(37,99,235,.0));
  background-size: 200% 100%;
  animation: none;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

div[data-testid="stForm"] {
  background: linear-gradient(180deg, rgba(8,18,38,.92), rgba(15,23,42,.86)) !important;
  border: 1px solid rgba(96,165,250,.20) !important;
  border-radius: 20px !important;
  padding: 1.15rem !important;
  box-shadow: 0 18px 60px rgba(2,6,23,.42) !important;
}

.stTabs [data-baseweb="tab-list"] {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  width: 100% !important;
  gap: .45rem !important;
  background: rgba(2,6,23,.44) !important;
  border-color: rgba(96,165,250,.18) !important;
  margin-bottom: 1rem !important;
}
.stTabs [data-baseweb="tab"] {
  min-width: 0 !important;
  justify-content: center !important;
  white-space: normal !important;
  min-height: 44px !important;
  font-size: .78rem !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, rgba(37,99,235,.86), rgba(14,165,233,.70)) !important;
  color: #fff !important;
  animation: none !important;
}

.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input {
  min-height: 46px !important;
  background: rgba(2,6,23,.55) !important;
  border-color: rgba(96,165,250,.20) !important;
}
.stTextInput>div>div>input:hover,
.stTextArea>div>div>textarea:hover {
  border-color: rgba(56,189,248,.55) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stDateInput label, .stTimeInput label, .stFileUploader label {
  color: #dbeafe !important;
  font-weight: 700 !important;
}

.stButton>button {
  background: linear-gradient(135deg, #2563eb, #0284c7, #4f46e5) !important;
  background-size: 180% auto !important;
  animation: none !important;
}
.stButton>button:hover {
  transform: translateY(-2px) scale(1.015) !important;
  box-shadow: 0 16px 42px rgba(37,99,235,.38), 0 0 22px rgba(56,189,248,.22) !important;
}

.post:hover, .card:hover, .metric:hover, .ev-card:hover,
.member-panel:hover, .user-profile-card:hover {
  transform: translateY(-5px) scale(1.01) !important;
  border-color: rgba(56,189,248,.45) !important;
  box-shadow: 0 26px 75px rgba(2,6,23,.52), 0 0 34px rgba(37,99,235,.16) !important;
}

.bme, .bother, .msg-group {
  animation: fadeUpSoft .22s ease both !important;
}
.msg-line {
  transition: background .18s ease, transform .18s ease, color .18s ease !important;
}
.msg-line:hover {
  transform: translateX(3px);
  color: #eff6ff !important;
}
.msg-group.mine .msg-line:hover {
  transform: translateX(-3px);
}

.av, .member-row .av-sm {
  animation: none !important;
}
.status-badge.on {
  box-shadow: 0 0 0 4px rgba(16,185,129,.12), 0 0 18px rgba(16,185,129,.52);
}

.auth-copy {
  color: #bfdbfe;
  font-size: .92rem;
  line-height: 1.6;
  margin: .35rem 0 1rem;
  padding: .75rem .9rem;
  border-radius: 14px;
  background: rgba(37,99,235,.10);
  border: 1px solid rgba(96,165,250,.16);
}

.card, .post, .metric, .ev-card, .member-panel,
.user-profile-card, div[data-testid="stForm"], .ubadge {
  transform: translateZ(0);
  will-change: transform;
}

/* ============================================================
   FULL SITE ENTERPRISE REBUILD LAYER
   Applies to every page: dashboard header, sidebar, cards, chat,
   admin rows, channels, auth and forms.
   ============================================================ */
.main .block-container {
  padding-top: 1.25rem !important;
}

.sh {
  width: 100%;
  min-height: 112px;
  margin: 0 0 1.4rem !important;
  padding: 1.35rem 1.55rem;
  border-radius: 28px;
  border: 1px solid rgba(96,165,250,.22);
  background:
    linear-gradient(135deg, rgba(15,23,42,.92), rgba(8,47,73,.58)),
    radial-gradient(circle at 10% 0%, rgba(56,189,248,.18), transparent 34%),
    radial-gradient(circle at 90% 35%, rgba(37,99,235,.20), transparent 32%);
  box-shadow: 0 24px 70px rgba(2,6,23,.34), inset 0 1px 0 rgba(255,255,255,.06);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1rem;
  align-items: center;
  transform-style: preserve-3d;
}
.sh::after {
  display: none !important;
}
.sh-icon {
  width: 58px;
  height: 58px;
  border-radius: 20px;
  display: grid;
  place-items: center;
  color: #eff6ff;
  background: linear-gradient(135deg, rgba(37,99,235,.95), rgba(14,165,233,.82));
  box-shadow: 0 18px 36px rgba(14,165,233,.22), inset 0 1px 0 rgba(255,255,255,.22);
  transform: translateZ(26px);
}
.sh-title {
  margin: 0;
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(1.55rem, 2.4vw, 2.35rem);
  font-weight: 900;
  letter-spacing: -.055em;
  color: #f8fafc;
}
.sh-sub {
  margin-top: .35rem;
  color: #bfdbfe;
  font-size: .92rem;
  line-height: 1.45;
  max-width: 780px;
}

.card, .post, .metric, .ev-card, .user-profile-card,
.member-panel, div[data-testid="stForm"], div[data-testid="stExpander"] {
  background:
    linear-gradient(145deg, rgba(15,23,42,.92), rgba(2,6,23,.72)) !important;
  border: 1px solid rgba(96,165,250,.18) !important;
  box-shadow: 0 18px 54px rgba(2,6,23,.28), inset 0 1px 0 rgba(255,255,255,.045) !important;
}

.card, .post, .metric, .ev-card, .user-profile-card {
  transform-style: preserve-3d;
}
.card:hover, .post:hover, .metric:hover, .ev-card:hover, .user-profile-card:hover {
  transform: perspective(1000px) rotateX(1.2deg) translateY(-4px) !important;
}

.stButton>button {
  min-height: 42px !important;
  border-radius: 14px !important;
  background: linear-gradient(135deg, #2563eb, #0891b2) !important;
  box-shadow: 0 12px 28px rgba(37,99,235,.22), inset 0 1px 0 rgba(255,255,255,.16) !important;
}
.stButton>button p {
  font-weight: 800 !important;
}

section[data-testid="stSidebar"] .stButton>button {
  justify-content: flex-start !important;
  text-align: left !important;
  min-height: 44px !important;
  background: rgba(15,23,42,.72) !important;
  border-color: rgba(96,165,250,.14) !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton>button:hover {
  background: linear-gradient(135deg, rgba(37,99,235,.65), rgba(8,145,178,.45)) !important;
  border-color: rgba(125,211,252,.35) !important;
  transform: translateX(3px) !important;
}

.stTabs [data-baseweb="tab-list"] {
  border-radius: 18px !important;
  padding: .45rem !important;
}
.stTabs [data-baseweb="tab"] {
  min-height: 48px !important;
}

.msg-group {
  padding: .65rem .75rem;
  border-radius: 18px;
}
.msg-group:hover {
  background: rgba(96,165,250,.055);
}

.member-category, .sb-eyebrow {
  color: #93c5fd !important;
}

.brand {
  border-bottom: 1px solid rgba(96,165,250,.14);
}
.brand img {
  box-shadow: 0 12px 30px rgba(14,165,233,.18);
}

.auth-copy {
  background: rgba(8,47,73,.42);
  border-color: rgba(96,165,250,.20);
}

div[role="radiogroup"] {
  background: rgba(2,6,23,.44);
  border: 1px solid rgba(96,165,250,.16);
  border-radius: 18px;
  padding: .45rem;
  margin-bottom: 1rem;
}
div[role="radiogroup"] label {
  border-radius: 12px;
  padding: .45rem .75rem;
  transition: background .16s ease, transform .16s ease;
}
div[role="radiogroup"] label:hover {
  background: rgba(37,99,235,.18);
  transform: translateY(-1px);
}

.auth-hero {
  position: relative;
  padding: 2rem 1rem 1.6rem !important;
}
.auth-hero::before {
  content: "";
  position: absolute;
  left: 50%;
  top: 0;
  width: min(560px, 90vw);
  height: 180px;
  transform: translateX(-50%);
  background: radial-gradient(circle, rgba(56,189,248,.16), transparent 62%);
  pointer-events: none;
  z-index: -1;
}
.auth-product-card {
  margin-top: -1rem;
}
.auth-product-card > div[style*="grid-template-columns"] > div {
  background: rgba(2,6,23,.48) !important;
  border: 1px solid rgba(96,165,250,.16) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
}

.stAlert {
  border-radius: 16px !important;
}

[data-testid="stVerticalBlock"] > [style*="flex-direction: column"] {
  gap: .75rem;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
  }
}

@media (max-width: 900px) {
  .main .block-container {
    padding: 1.25rem 1rem 2rem !important;
  }
  .sh {
    font-size: 1.45rem;
  }
  .metric .val {
    font-size: 1.8rem;
  }
  .stTabs [data-baseweb="tab-list"] {
    grid-template-columns: 1fr !important;
  }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# DB + Helpers
# ============================================================
def session_cache_get(key: str, ttl: int, loader):
    """Tiny per-user TTL cache; avoids cross-user RLS leaks from global caching."""
    now = time.time()
    cache = st.session_state.setdefault("_ttl_cache", {})
    item = cache.get(key)
    if item and now - item["time"] < ttl:
        return item["value"]
    value = loader()
    cache[key] = {"time": now, "value": value}
    return value

def session_cache_clear(prefix: str = ""):
    cache = st.session_state.get("_ttl_cache", {})
    for k in list(cache.keys()):
        if not prefix or k.startswith(prefix):
            cache.pop(k, None)

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
        try:
            member_count = sb.table("profiles").select("id", count="exact").execute().count or 0
            post_count   = sb.table("posts").select("id", count="exact").execute().count or 0
            msg_count    = sb.table("messages").select("id", count="exact").execute().count or 0
        except Exception:
            member_count, post_count, msg_count = 0, 0, 0
        return member_count, post_count, msg_count
    return session_cache_get("platform_stats", 45, load)

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
    return _re.sub(r'@(\w+)', r'<span style="color:var(--yellow);font-weight:600;">@\1</span>', escaped)

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
    return session_cache_get(f"mention_count_{user_id}_{source_type or 'all'}", 8, load)

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
    except Exception:
        pass

def get_unread_notification_count(sb, user_id) -> int:
    def load():
        try:
            r = sb.table("notifications").select("id", count="exact").eq("user_id", user_id).eq("is_read", False).execute()
            return r.count or 0
        except Exception:
            return 0
    return session_cache_get(f"notification_count_{user_id}", 8, load)

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
      <h2 style="font-family:'Space Grotesk',sans-serif;color:var(--yellow);margin:.5rem 0;">Set a new password</h2>
      <p style="color:var(--t2);">You're verified — choose a new password below.</p>
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

    st.markdown("""
    <div style="position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden;">
      <div style="position:absolute;width:800px;height:800px;border-radius:50%;
        background:radial-gradient(circle, rgba(88,101,242,0.06), transparent 70%);
        top:-300px;right:-300px;animation:orbFloat 8s ease-in-out infinite;"></div>
      <div style="position:absolute;width:600px;height:600px;border-radius:50%;
        background:radial-gradient(circle, rgba(88,101,242,0.04), transparent 70%);
        bottom:-200px;left:-200px;animation:orbFloat 10s ease-in-out infinite reverse;"></div>
    </div>
    """, unsafe_allow_html=True)

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
          <p style="color:var(--t2);font-size:1.05rem;margin:0;">{APP_TAGLINE}</p>
          <p style="color:var(--t3);font-size:0.85rem;margin-top:0.3rem;">Secure social tools, AI support, habits, events, and team channels</p>
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
                ok = st.form_submit_button("Sign In", use_container_width=True)

            if ok:
                if not u or not p:
                    st.error("Please fill all fields.")
                    return
                try:
                    auth_res = sb.auth.sign_in_with_password({"email": u.strip(), "password": p})
                except Exception:
                    st.error("Invalid email or password.")
                    return
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
                        st.error("Account exists but has no profile yet. Run the latest schema.sql in Supabase.")
                        return
                    user = prof.data[0]
                    if user.get("is_banned"):
                        sb.auth.sign_out()
                        st.error("Your account has been banned. Contact support if you believe this is an error.")
                        return
                    st.session_state.update({
                        "user": user,
                        "user_id": user["id"],
                        "username": user["username"],
                        "logged_in": True,
                        "viewing_user": None,
                    })
                    sb.table("profiles").update({"last_seen": datetime.now(timezone.utc).isoformat()}).eq("id", user["id"]).execute()
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

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
                    sb.auth.sign_up({
                        "email": ne.strip(),
                        "password": np1,
                        "options": {"data": {"username": clean_username, "bio": nb}},
                    })
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
          <h3 style="color:var(--yellow);font-family:'Space Grotesk',sans-serif;font-size:1.4rem;margin:0;">
            Everything your community needs in one place.
          </h3>
          <p style="color:var(--t2);font-size:0.92rem;margin:0.4rem 0 1.3rem;">
            A refined dashboard for posts, AI assistance, live messaging, planning, habits, and profiles.
          </p>
          
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem;margin:0.5rem 0 1rem;">
            <div style="background:var(--bg2);border-radius:12px;padding:1rem 0.5rem;border:1px solid rgba(88,101,242,0.05);">
              <div style="font-size:1.8rem;font-weight:900;color:var(--yellow);">{member_count}</div>
              <div style="color:var(--t3);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">Members</div>
            </div>
            <div style="background:var(--bg2);border-radius:12px;padding:1rem 0.5rem;border:1px solid rgba(88,101,242,0.05);">
              <div style="font-size:1.8rem;font-weight:900;color:var(--yellow);">{post_count}</div>
              <div style="color:var(--t3);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">Posts</div>
            </div>
            <div style="background:var(--bg2);border-radius:12px;padding:1rem 0.5rem;border:1px solid rgba(88,101,242,0.05);">
              <div style="font-size:1.8rem;font-weight:900;color:var(--yellow);">{msg_count}</div>
              <div style="color:var(--t3);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">Messages</div>
            </div>
          </div>
          
          <div style="margin-top:0.5rem;padding-top:1rem;border-top:1px solid rgba(88,101,242,0.06);">
            <p style="color:var(--t3);font-size:0.7rem;margin:0;">AI assistant powered by Groq</p>
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
    initials = user["username"][:2].upper()
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
        <div class="av av-lg">{initials}</div>
        <div>
          <h2 style="margin:0;font-family:'Space Grotesk',sans-serif;color:var(--yellow);">@{safe_username}</h2>
          <div style="color:var(--t3);font-size:.78rem;margin-top:.2rem;">
            {'✓ Verified · ' if user.get('is_verified') else ''}{'Admin · ' if user.get('is_admin') else ''}{escape_html(user.get('profile_badge') or 'Member')}
          </div>
          <div style="color:{'var(--yellow)' if is_online else 'var(--t3)'};font-size:.9rem;margin:.2rem 0;">
            {'<span class="online"></span>Online now' if is_online else '⚫ Offline'}
          </div>
          <p style="color:var(--t2);margin:.3rem 0 0;">{safe_bio}</p>
          <p style="color:var(--t3);font-size:.8rem;margin-top:.3rem;">Joined {user.get('created_at','')[:10]}</p>
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
        st.markdown("<p style='color:var(--t3);'>No posts yet.</p>", unsafe_allow_html=True)
    else:
        for p in posts.data:
            st.markdown(f"""
            <div class="post">
              <p style="margin:0;color:var(--t);">{linkify_mentions(p['content'])}</p>
              <small style="color:var(--t3);">{ago(p['created_at'])}</small>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("### ✅ User's Habits")
    habits = sb.table("habits").select("*").eq("user_id", user["id"]).limit(10).execute()
    if not habits.data:
        st.markdown("<p style='color:var(--t3);'>No habits yet.</p>", unsafe_allow_html=True)
    else:
        for h in habits.data:
            safe_habit = escape_html(h.get("name", "Habit"))
            safe_emoji = escape_html(h.get("emoji", "⭐"))
            st.markdown(f"""
            <div class="card" style="padding:0.8rem 1.2rem;">
              <span style="font-size:1rem;font-weight:700;color:var(--yellow);">{safe_emoji} {safe_habit}</span>
              <span style="color:var(--t3);font-size:.8rem;margin-left:.5rem;">{h['frequency']}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("### 📅 User's Events")
    events = sb.table("events").select("*").eq("user_id", user["id"]).gte("event_date", datetime.now(timezone.utc).isoformat()).order("event_date").limit(10).execute()
    if not events.data:
        st.markdown("<p style='color:var(--t3);'>No upcoming events.</p>", unsafe_allow_html=True)
    else:
        for ev in events.data:
            dt = ev["event_date"][:16].replace("T"," ")
            safe_title = escape_html(ev.get("title", "Event"))
            st.markdown(f"""
            <div class="ev-card" style="border-left-color:var(--yellow);padding:0.8rem 1.2rem;">
              <div style="font-weight:700;color:var(--yellow);">{safe_title}</div>
              <div style="color:var(--t3);font-size:.8rem;">📅 {dt}</div>
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
        av = u.get("avatar_url")
        initials = u["username"][:2].upper()
        is_me = u["id"] == st.session_state.user_id
        inner = (f'<img src="{av}" style="width:100%;height:100%;object-fit:cover;">'
                  if av and av.startswith("data:image") else initials)
        status_cls = "on" if is_online else "off"
        label = f'@{escape_html(u["username"])}' + (" (you)" if is_me else "")
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(
                f'<span class="av-wrap"><div class="av-sm">{inner}</div>'
                f'<span class="status-badge {status_cls}" style="width:10px;height:10px;border-width:2px;"></span></span>',
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
              border-radius:var(--r);padding:.75rem 1rem;margin-top:.8rem;">
              <div style="color:var(--red);font-weight:700;font-size:.85rem;">🔔 {mention_count} Mention{"s" if mention_count>1 else ""}</div>
            </div>
            """, unsafe_allow_html=True)
            mentions = sb2.table("mentions").select("*").eq("mentioned_user_id", st.session_state.user_id).eq("is_read", False).eq("source_type", "post").order("created_at", desc=True).limit(5).execute()
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
                    st.rerun()

        posts = sb.table("posts").select("*").order("is_pinned", desc=True).order("created_at", desc=True).limit(25).execute()
        if not posts.data:
            card("""
            <div style="text-align:center;padding:4rem 0;">
              <div style="font-size:5rem;margin-bottom:1.5rem;">🚀</div>
              <p style="color:var(--t2);font-size:1.2rem;">No posts yet — be the first!</p>
              <p style="color:var(--t3);font-size:.9rem;">Share your thoughts with the community</p>
            </div>
            """)
            return

        for p in posts.data:
            mine = p["user_id"] == st.session_state.user_id
            initials = p["username"][:2].upper()
            safe_username = escape_html(p.get("username", "user"))
            content_html = linkify_mentions(p["content"])

            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"""
                <div class="post">
                  <div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.8rem;">
                    <div class="av av-clickable">{initials}</div>
                    <div>
                      <div style="font-weight:700;color:{'var(--yellow)' if mine else 'var(--t)'};font-size:1rem;">
                        @{safe_username} {'<span class="badge">You</span>' if mine else ''}
                      </div>
                      <div style="font-size:.75rem;color:var(--t3);">{ago(p['created_at'])}</div>
                    </div>
                  </div>
                  <p style="margin:0;color:var(--t);line-height:1.7;font-size:.95rem;">{content_html}</p>
                  {render_attachment_preview(p.get('file_url'), p.get('file_name'), p.get('file_type'))}
                </div>
                """, unsafe_allow_html=True)

                # Reactions row
                counts, mine_reactions = get_post_reactions(sb, p["id"])
                rcols = st.columns(len(REACTION_EMOJIS) + 1)
                for i, emoji in enumerate(REACTION_EMOJIS):
                    n = counts.get(emoji, 0)
                    label = f"{emoji} {n}" if n else emoji
                    with rcols[i]:
                        if st.button(label, key=f"react_{p['id']}_{emoji}"):
                            if emoji in mine_reactions:
                                sb.table("post_reactions").delete().eq("post_id", p["id"]).eq("user_id", st.session_state.user_id).eq("emoji", emoji).execute()
                            else:
                                sb.table("post_reactions").insert({
                                    "post_id": p["id"], "user_id": st.session_state.user_id, "emoji": emoji,
                                    "created_at": datetime.now(timezone.utc).isoformat(),
                                }).execute()
                                create_notification(sb, p["user_id"], st.session_state.user_id, "reaction", "New reaction", f"@{st.session_state.username} reacted {emoji} to your post.", "post", p["id"])
                            st.rerun()

                with st.expander("Comments and moderation", expanded=False):
                    comments = sb.table("post_comments").select("*").eq("post_id", p["id"]).order("created_at").limit(30).execute()
                    if comments.data:
                        for cm in comments.data:
                            st.markdown(f"**@{escape_html(cm['username'])}** · {ago(cm['created_at'])}<br>{linkify_mentions(cm['content'])}", unsafe_allow_html=True)
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
                            st.rerun()

                    mod_cols = st.columns(3)
                    with mod_cols[0]:
                        if (mine or st.session_state.user.get("is_admin")) and st.button("Unpin" if p.get("is_pinned") else "Pin", key=f"pin_post_{p['id']}"):
                            sb.table("posts").update({"is_pinned": not p.get("is_pinned", False)}).eq("id", p["id"]).execute()
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
    rows = sb.table("notifications").select("*").eq("user_id", st.session_state.user_id)\
        .order("created_at", desc=True).limit(50).execute()

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("Mark all read", use_container_width=True):
            sb.table("notifications").update({"is_read": True}).eq("user_id", st.session_state.user_id).eq("is_read", False).execute()
            session_cache_clear(f"notification_count_{st.session_state.user_id}")
            st.rerun()

    if not rows.data:
        card("<p style='color:var(--t3);text-align:center;'>No notifications yet.</p>")
        return

    for n in rows.data:
        status = "" if n.get("is_read") else "<span class='badge'>New</span>"
        st.markdown(f"""
        <div class="card" style="padding:1rem 1.2rem;">
          <div style="display:flex;justify-content:space-between;gap:1rem;">
            <div>
              <div style="font-weight:800;color:var(--yellow);">{escape_html(n.get('title', 'Notification'))} {status}</div>
              <div style="color:var(--t2);font-size:.9rem;margin-top:.25rem;">{safe_multiline(n.get('body', ''))}</div>
            </div>
            <div style="color:var(--t3);font-size:.75rem;white-space:nowrap;">{ago(n.get('created_at', ''))}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)


def discover_page():
    sb = get_sb()
    sh_header("🔎", "Discover")
    q = st.text_input("Search members", placeholder="Search by username or bio...", key="discover_q")
    query = sb.table("profiles").select("id,username,bio,last_seen,avatar_url,is_admin,is_verified,profile_badge").neq("id", st.session_state.user_id)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.or_(f"username.ilike.{term},bio.ilike.{term}")
    users = query.order("last_seen", desc=True).limit(40).execute()

    if not users.data:
        card("<p style='color:var(--t3);text-align:center;'>No members found.</p>")
        return

    for u in users.data:
        followers, _ = follow_counts(sb, u["id"])
        following = is_following(sb, st.session_state.user_id, u["id"])
        safe_username = escape_html(u.get("username", "user"))
        safe_bio = safe_multiline(u.get("bio") or "No bio yet.")
        c_info, c_follow, c_view = st.columns([4, 1, 1])
        with c_info:
            badge = "✓ Verified" if u.get("is_verified") else (u.get("profile_badge") or "Member")
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.2rem;margin-bottom:.35rem;">
              <div style="font-weight:900;color:var(--yellow);">@{safe_username}</div>
              <div style="color:var(--t3);font-size:.76rem;">{escape_html(badge)} · {followers} followers</div>
              <div style="color:var(--t2);font-size:.88rem;margin-top:.35rem;">{safe_bio}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_follow:
            if st.button("Unfollow" if following else "Follow", key=f"discover_follow_{u['id']}", use_container_width=True):
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
          <h3 style="margin:0 0 .5rem;color:var(--yellow);">Groq API key missing</h3>
          <p style="color:var(--t2);">Add <code style="color:var(--yellow);">GROQ_API_KEY</code> to Streamlit Secrets or your local <code style="color:var(--yellow);">.env</code> file to enable AI chat.</p>
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
    return session_cache_get(f"dm_unread_{user_id}", 6, load)


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


def file_to_data_uri(uploaded_file, max_dim=800) -> dict:
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
            img.convert("RGB" if fmt == "JPEG" else "RGBA").save(buf, format=fmt)
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
            f'color:var(--yellow);text-decoration:none;font-size:.85rem;">📎 {safe_name}</a>')


@st.fragment(run_every=1)
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
        st.markdown("<p style='color:var(--t3);text-align:center;padding:2rem;'>Start the conversation 👋</p>", unsafe_allow_html=True)
        return

    my_avatar = st.session_state.user.get("avatar_url")
    my_initials = st.session_state.username[:2].upper()
    my_avatar_inner = (f'<img src="{my_avatar}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">'
                        if my_avatar and my_avatar.startswith("data:image")
                        else f'<div class="av" style="width:36px;height:36px;font-size:.85rem;">{my_initials}</div>')
    their_avatar_inner = (f'<img src="{target_avatar}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">'
                           if target_avatar and target_avatar.startswith("data:image")
                           else f'<div class="av" style="width:36px;height:36px;font-size:.85rem;">{sel[:2].upper()}</div>')

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
          <span class="av-wrap">{avatar_inner_g}</span>
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
          <span class="av-wrap">{their_avatar_inner}</span>
          <div class="msg-group-body">
            <div class="msg-line" style="color:var(--t3);font-style:italic;">@{sel} is typing...</div>
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
        card("<p style='color:var(--t3);text-align:center;'>No other users yet.</p>")
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
                    st.markdown(f"<div class='msg-line' style='padding:.3rem .5rem;'><b style='color:var(--yellow);'>{escape_html(who)}:</b> {linkify_mentions(r['content'])} <span style='color:var(--t3);font-size:.7rem;'>· {ago(r['created_at'])}</span></div>", unsafe_allow_html=True)
            else:
                st.caption("No matches.")

    five_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    is_onl = (target.get("last_seen") or "") > five_ago

    if st.session_state.get("chat_target"):
        st.session_state.chat_target = None

    target_avatar = target.get("avatar_url")
    if target_avatar and target_avatar.startswith("data:image"):
        avatar_inner = f'<img src="{target_avatar}" style="width:42px;height:42px;border-radius:50%;object-fit:cover;">'
    else:
        avatar_inner = f'<div class="av">{sel[:2].upper()}</div>'

    status_cls = "on" if is_onl else "off"
    head_col, action_col = st.columns([4, 1])
    with head_col:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:.8rem;margin-bottom:1.2rem;
          padding:1rem 1.4rem;background:var(--card);border-radius:var(--r2);border:1px solid rgba(88,101,242,0.12);">
          <span class="av-wrap">{avatar_inner}<span class="status-badge {status_cls}"></span></span>
          <div>
            <div style="font-weight:700;font-size:1rem;">@{escape_html(sel)}</div>
            <div style="font-size:.78rem;color:{'var(--yellow)' if is_onl else 'var(--t3)'};">
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
                st.rerun()

    with col2:
        st.markdown("### 📆 Upcoming")
        fil = st.radio("Show", ["This Week", "This Month", "All"], horizontal=True)
        now = datetime.now(timezone.utc)
        q = sb.table("events").select("*").eq("user_id", st.session_state.user_id)
        if fil == "This Week":
            q = q.gte("event_date", now.isoformat()).lte("event_date", (now + timedelta(days=7)).isoformat())
        elif fil == "This Month":
            q = q.gte("event_date", now.replace(day=1).isoformat())
        evs = q.order("event_date").execute()
        # Backward-compatible: old events stored before this palette
        # switch used "yellow"/"gold"/"orange" — still mapped here so
        # existing rows in the DB don't render with a missing color.
        cmap = {
            "blurple": "#5865F2", "pink": "#EB459E", "teal": "#23A55A",
            "green": "#23A55A", "red": "#F23F42",
            "yellow": "#5865F2", "gold": "#4752C4", "orange": "#3C45A5",
        }

        if not evs.data:
            card("<p style='color:var(--t3);text-align:center;'>No events. Add one! 🗓️</p>")
        else:
            for ev in evs.data:
                acc = cmap.get(ev.get("color", "blurple"), "#5865F2")
                dt = ev["event_date"][:16].replace("T", " ")
                safe_title = escape_html(ev.get("title", "Event"))
                safe_description = safe_multiline(ev.get("description", ""))
                ce, cd = st.columns([5, 1])
                with ce:
                    st.markdown(f"""
                    <div class="ev-card" style="border-left-color:{acc};padding:1.2rem;">
                      <div style="font-weight:700;color:{acc};">{safe_title}</div>
                      <div style="color:var(--t3);font-size:.8rem;margin-top:.2rem;">📅 {dt}</div>
                      {f"<p style='margin:.5rem 0 0;color:var(--t2);font-size:.9rem;'>{safe_description}</p>" if ev.get('description') else ''}
                    </div>
                    """, unsafe_allow_html=True)
                with cd:
                    if st.button("🗑️", key=f"de{ev['id']}"):
                        sb.table("events").delete().eq("id", ev["id"]).execute()
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
            all_channels = sb.table("channels").select("*").order("created_at").execute()
            return all_channels.data or [], set(joined_ids), last_read
        except Exception:
            return [], set(), {}
    return session_cache_get(f"user_channels_{user_id}", 12, load)


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
    return session_cache_get(f"channel_unread_{user_id}_{channel_id}_{last_seen_at}", 8, load)

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
        st.markdown(f"<p style='color:var(--t3);text-align:center;padding:2rem;'>No messages in #{escape_html(channel_name)} yet. Say hello! 👋</p>", unsafe_allow_html=True)
        return

    groups = []
    for m in msgs.data:
        mine = m["sender_id"] == st.session_state.user_id
        if groups and groups[-1]["sender_id"] == m["sender_id"]:
            groups[-1]["msgs"].append(m)
        else:
            groups.append({"sender_id": m["sender_id"], "username": m["sender_username"], "mine": mine, "msgs": [m]})

    for g in groups:
        initials = g["username"][:2].upper()
        avatar_inner = f'<div class="av" style="width:36px;height:36px;font-size:.85rem;">{initials}</div>'
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
          <span class="av-wrap">{avatar_inner}</span>
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
                            "role": "owner",
                            "joined_at": datetime.now(timezone.utc).isoformat(),
                            "last_read_at": datetime.now(timezone.utc).isoformat(),
                        }).execute()
                    st.success(f"#{clean_name} created!")
                    session_cache_clear(f"user_channels_{st.session_state.user_id}")
                    st.rerun()

    if not channels:
        card("<p style='color:var(--t3);text-align:center;'>No channels yet — create the first one!</p>")
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
          <div style="font-weight:800;font-size:1.2rem;color:var(--yellow);">#{safe_channel_name}</div>
          <div style="color:var(--t3);font-size:.82rem;">{safe_channel_desc}</div>
          <div style="color:var(--t3);font-size:.76rem;margin-top:.3rem;">Role: {escape_html(my_role)} · Invite: <code>{escape_html(active_channel.get('invite_code', ''))}</code></div>
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
                    st.rerun()

        with col2:
            st.markdown("### 📊 Progress")
            hbs = sb.table("habits").select("*").eq("user_id", st.session_state.user_id).execute()
            today = date.today().isoformat()
            week_ago = (date.today() - timedelta(days=7)).isoformat()

            if not hbs.data:
                card("<p style='color:var(--t3);'>No habits yet! Create your first one ✨</p>")
            else:
                for h in hbs.data:
                    done = sb.table("habit_logs").select("id").eq("habit_id", h["id"]).eq("log_date", today).execute()
                    wk = sb.table("habit_logs").select("id").eq("habit_id", h["id"]).gte("log_date", week_ago).execute()
                    is_done = bool(done.data)
                    prog = min(len(wk.data or []) / 7, 1.0)
                    streak = compute_habit_streak(sb, h["id"])
                    streak_html = f'<span style="color:var(--yellow);font-weight:700;">🔥 {streak}d</span>' if streak > 0 else ''
                    safe_habit = escape_html(h.get("name", "Habit"))
                    safe_emoji = escape_html(h.get("emoji", "⭐"))
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        st.markdown(f"""
                        <div class="card" style="padding:1.2rem;">
                          <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:1.1rem;font-weight:700;color:var(--yellow);">{safe_emoji} {safe_habit} {'🌍' if h.get('is_shared') else ''}</span>
                            <span style="color:{'var(--yellow)' if is_done else 'var(--t3)'};">{'✅ Done' if is_done else '⬜ Pending'}</span>
                          </div>
                          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.4rem;">
                            <div style="color:var(--t3);font-size:.8rem;">{len(wk.data or [])}/7 days this week</div>
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
                                st.rerun()
                        if st.button("🗑️", key=f"dh{h['id']}"):
                            sb.table("habits").delete().eq("id", h["id"]).execute()
                            st.rerun()

    with t2:
        st.markdown("### 🌍 Community Habits")
        shared = sb.table("habits").select("*").eq("is_shared", True).neq("user_id", st.session_state.user_id) \
            .order("created_at", desc=True).limit(20).execute()
        if not shared.data:
            card("<p style='color:var(--t3);'>No shared habits yet.</p>")
        else:
            for h in shared.data:
                safe_habit = escape_html(h.get("name", "Habit"))
                safe_emoji = escape_html(h.get("emoji", "⭐"))
                safe_username = escape_html(h.get("username", "user"))
                st.markdown(f"""
                <div class="card" style="padding:1.2rem;">
                  <strong style="color:var(--yellow);font-size:1.05rem;">{safe_emoji} {safe_habit}</strong>
                  <span style="color:var(--t3);"> by @{safe_username}</span>
                  <div style="color:var(--t3);font-size:.8rem;margin-top:.2rem;">{h['frequency']}</div>
                </div>
                """, unsafe_allow_html=True)

    with t3:
        st.markdown("### 🏆 Habit Leaderboard")
        shared = sb.table("habits").select("*").eq("is_shared", True).limit(100).execute()
        leaderboard = []
        for h in (shared.data or []):
            leaderboard.append({
                "username": h.get("username", "user"),
                "habit": h.get("name", "Habit"),
                "emoji": h.get("emoji", "⭐"),
                "streak": compute_habit_streak(sb, h["id"]),
            })
        leaderboard = sorted(leaderboard, key=lambda x: x["streak"], reverse=True)[:15]
        if not leaderboard:
            card("<p style='color:var(--t3);'>No shared streaks yet.</p>")
        for i, row in enumerate(leaderboard, start=1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.2rem;display:flex;justify-content:space-between;align-items:center;">
              <div><strong style="color:var(--yellow);">{medal} @{escape_html(row['username'])}</strong>
              <div style="color:var(--t2);font-size:.88rem;">{escape_html(row['emoji'])} {escape_html(row['habit'])}</div></div>
              <div style="font-size:1.2rem;font-weight:900;color:var(--yellow);">🔥 {row['streak']}d</div>
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
            st.markdown(f'<img src="{avatar_url}" style="width:100px;height:100px;border-radius:50%;border:3px solid var(--yellow);box-shadow:0 0 60px var(--glow);object-fit:cover;">', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="av av-lg" style="margin:auto;">{initials}</div>', unsafe_allow_html=True)

    with col_inf:
        st.markdown(f"""
        <div style="padding-left:.5rem;">
          <h2 style="margin:0;font-family:'Space Grotesk',sans-serif;background:linear-gradient(135deg,var(--yellow),var(--yellow4));-webkit-background-clip:text;-webkit-text-fill-color:transparent;">@{safe_username}</h2>
          <p style="color:var(--t2);margin:.3rem 0 0;">{safe_bio}</p>
          <p style="color:var(--t3);font-size:.8rem;margin-top:.3rem;">Joined {u.get('created_at', '')[:10]}</p>
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
    pc = sb.table("posts").select("id", count="exact").eq("user_id", st.session_state.user_id).execute()
    hc = sb.table("habits").select("id", count="exact").eq("user_id", st.session_state.user_id).execute()
    mc = sb.table("messages").select("id", count="exact").eq("sender_id", st.session_state.user_id).execute()

    cols = st.columns(3)
    metrics = [(pc.count or 0, "Posts"), (hc.count or 0, "Habits"), (mc.count or 0, "Messages")]
    for col, (v, l) in zip(cols, metrics):
        col.markdown(f'<div class="metric"><div class="val">{v}</div><div class="lbl">{l}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📝 My Posts")
    mp = sb.table("posts").select("*").eq("user_id", st.session_state.user_id).order("created_at", desc=True).limit(10).execute()
    if not mp.data:
        st.markdown("<p style='color:var(--t3);'>No posts yet.</p>", unsafe_allow_html=True)
    else:
        for p in mp.data:
            ca, cb = st.columns([5, 1])
            with ca:
                st.markdown(f"""
                <div class="post" style="padding:1.2rem 1.5rem;">
                  <p style="margin:0;color:var(--t);">{linkify_mentions(p['content'])}</p>
                  <small style="color:var(--t3);">{ago(p['created_at'])}</small>
                </div>
                """, unsafe_allow_html=True)
            with cb:
                if st.button("🗑️", key=f"dp{p['id']}"):
                    sb.table("posts").delete().eq("id", p["id"]).execute()
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
          <div style="color:var(--t3);font-size:.7rem;">Professional Workspace</div>
        </div>
        """, unsafe_allow_html=True)

        avatar_url = st.session_state.user.get("avatar_url")
        initials = st.session_state.username[:2].upper()
        if avatar_url and avatar_url.startswith("data:image"):
            avatar_inner = f'<img src="{avatar_url}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">'
        else:
            avatar_inner = f'<span style="font-size:.8rem;font-weight:800;color:var(--yellow);">{initials}</span>'

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

        st.markdown(f"""
        <div class="ubadge">
          <span class="av-wrap"><div class="av">{avatar_inner}</div><span class="status-badge on"></span></span>
          <div style="flex:1;">
            <div style="font-weight:700;font-size:.9rem;color:var(--yellow);">@{st.session_state.username}</div>
            <div style="font-size:.7rem;color:var(--yellow);">Active now
              {f'<span style="background:var(--red);color:white;border-radius:99px;padding:.05rem .35rem;font-size:.65rem;font-weight:700;margin-left:.3rem;">{unread_mentions + unread_notifications}</span>' if (unread_mentions + unread_notifications) else ''}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

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
        theme = st.radio("Theme", ["Midnight", "Ocean"], horizontal=True, key="theme_mode")
        if theme == "Ocean":
            st.markdown("""
            <style>
            html, body, .stApp {
              background:
                radial-gradient(circle at 12% 8%, rgba(14,165,233,.28), transparent 28%),
                radial-gradient(circle at 88% 12%, rgba(59,130,246,.20), transparent 30%),
                linear-gradient(135deg, #031525, #082f49 48%, #0f172a 100%) !important;
            }
            </style>
            """, unsafe_allow_html=True)

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
        users = sb.table("profiles").select("id,username,email,is_admin,is_banned,is_verified,profile_badge,created_at,last_seen").order("created_at", desc=True).execute()
        for u in (users.data or []):
            is_me = u["id"] == st.session_state.user_id
            five_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
            is_onl = (u.get("last_seen") or "") > five_ago
            safe_username = escape_html(u.get("username", "user"))
            safe_email = escape_html(u.get("email", ""))
            col_i, col_a, col_b, col_v, col_ba = st.columns([3, 1, 1, 1, 1])
            with col_i:
                st.markdown(f"""
                <div style="padding:.5rem;background:var(--card);border-radius:var(--r);margin-bottom:.3rem;">
                  <span style="color:var(--yellow);font-weight:700;">@{safe_username}</span>
                  {'<span style="color:var(--t3);font-size:.75rem;"> (you)</span>' if is_me else ''}
                  {'<span style="color:var(--green);font-size:.75rem;"> 🟢</span>' if is_onl else ''}
                  {'<span style="color:var(--red);font-size:.75rem;"> BANNED</span>' if u.get("is_banned") else ''}
                  {'<span style="color:var(--yellow);font-size:.75rem;"> ADMIN</span>' if u.get("is_admin") else ''}
                  <div style="color:var(--t3);font-size:.72rem;">{safe_email}</div>
                </div>
                """, unsafe_allow_html=True)
            if not is_me:
                with col_a:
                    action = "Unban" if u.get("is_banned") else "Ban"
                    if st.button(action, key=f"ban_{u['id']}"):
                        sb.table("profiles").update({"is_banned": not u.get("is_banned", False)}).eq("id", u["id"]).execute()
                        st.rerun()
                with col_b:
                    admin_action = "Remove Admin" if u.get("is_admin") else "Make Admin"
                    if st.button(admin_action, key=f"adm_{u['id']}"):
                        sb.table("profiles").update({"is_admin": not u.get("is_admin", False)}).eq("id", u["id"]).execute()
                        st.rerun()
                with col_v:
                    verify_action = "Unverify" if u.get("is_verified") else "Verify"
                    if st.button(verify_action, key=f"ver_{u['id']}"):
                        sb.table("profiles").update({
                            "is_verified": not u.get("is_verified", False),
                            "profile_badge": "Verified" if not u.get("is_verified", False) else "",
                        }).eq("id", u["id"]).execute()
                        st.rerun()
                with col_ba:
                    if st.button("Del Posts", key=f"delpost_{u['id']}"):
                        sb.table("posts").delete().eq("user_id", u["id"]).execute()
                        st.success(f"Deleted all posts by @{u['username']}")
                        st.rerun()

    with tab_posts:
        st.markdown("### Recent Posts (All Users)")
        posts = sb.table("posts").select("*").order("created_at", desc=True).limit(50).execute()
        for p in (posts.data or []):
            safe_username = escape_html(p.get("username", "user"))
            safe_content = linkify_mentions((p.get("content") or "")[:200])
            col_p, col_d = st.columns([5, 1])
            with col_p:
                st.markdown(f"""
                <div style="background:var(--card);border-radius:var(--r);padding:.8rem 1rem;margin-bottom:.3rem;border-left:3px solid var(--yellow);">
                  <span style="color:var(--yellow);font-weight:700;">@{safe_username}</span>
                  <span style="color:var(--t3);font-size:.72rem;"> · {ago(p['created_at'])}</span>
                  <p style="margin:.3rem 0 0;color:var(--t);font-size:.88rem;">{safe_content}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_d:
                if st.button("🗑️", key=f"admdelp_{p['id']}"):
                    sb.table("posts").delete().eq("id", p["id"]).execute()
                    st.rerun()

    with tab_channels:
        st.markdown("### Manage Channels")
        channels = sb.table("channels").select("*").order("created_at").execute()
        for ch in (channels.data or []):
            safe_channel_name = escape_html(ch.get("name", "channel"))
            safe_channel_desc = safe_multiline(ch.get("description", ""))
            col_c, col_dc = st.columns([4, 1])
            with col_c:
                member_count = sb.table("channel_members").select("id", count="exact").eq("channel_id", ch["id"]).execute().count or 0
                st.markdown(f"""
                <div style="background:var(--card);border-radius:var(--r);padding:.8rem 1rem;margin-bottom:.3rem;">
                  <span style="color:var(--yellow);font-weight:700;"># {safe_channel_name}</span>
                  <span style="color:var(--t3);font-size:.75rem;"> · {member_count} members</span>
                  <p style="margin:.2rem 0 0;color:var(--t2);font-size:.82rem;">{safe_channel_desc}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_dc:
                if st.button("🗑️", key=f"admdelch_{ch['id']}"):
                    sb.table("channels").delete().eq("id", ch["id"]).execute()
                    st.rerun()

    with tab_reports:
        st.markdown("### Open Reports")
        reports = sb.table("reports").select("*").order("created_at", desc=True).limit(80).execute()
        if not reports.data:
            st.caption("No reports yet.")
        for r in (reports.data or []):
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.2rem;">
              <div style="display:flex;justify-content:space-between;gap:1rem;">
                <div>
                  <strong style="color:var(--yellow);">{escape_html(r.get('target_type'))}</strong>
                  <span style="color:var(--t3);font-size:.75rem;"> · {escape_html(r.get('status'))} · {ago(r.get('created_at', ''))}</span>
                  <p style="color:var(--t2);margin:.35rem 0 0;">{safe_multiline(r.get('reason', ''))}</p>
                </div>
                <code style="color:var(--t3);font-size:.68rem;">{escape_html(r.get('target_id'))}</code>
              </div>
            </div>
            """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Mark reviewed", key=f"review_report_{r['id']}", use_container_width=True):
                    sb.table("reports").update({"status": "reviewed"}).eq("id", r["id"]).execute()
                    st.rerun()
            with c2:
                if st.button("Dismiss", key=f"dismiss_report_{r['id']}", use_container_width=True):
                    sb.table("reports").update({"status": "dismissed"}).eq("id", r["id"]).execute()
                    st.rerun()


# ============================================================
# MAIN
# ============================================================
def main():
    inject_css()

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
        elif status == "none":
            st.session_state.recovery_check_done = True
        # status == "pending": leave recovery_check_done unset — the
        # st_javascript component triggers its own rerun once the
        # browser responds, which will re-enter this branch with a
        # real "found" or "none" answer.

    if st.session_state.get("recovery_access_token"):
        reset_password_page()
        return

    if not st.session_state.get("recovery_check_done"):
        st.markdown(f"""
        <div style="text-align:center;padding:4rem 0;">
          {logo_img(70)}
          <p style="color:var(--t3);margin-top:1rem;">Loading...</p>
        </div>
        """, unsafe_allow_html=True)
        return

    if not st.session_state.get("logged_in"):
        auth_page()
        return

    try:
        get_sb().table("profiles").select("id").limit(1).execute()
    except Exception as e:
        st.error(f"DB error: {e}")
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
