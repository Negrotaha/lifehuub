"""Inline CSS theme."""
import streamlit as st
from config import CSS_VERSION

def inject_css():
    if st.session_state.get("_css_version") == CSS_VERSION:
        return
    st.session_state["_css_version"] = CSS_VERSION
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
  --primary-glow: rgba(99, 102, 241, 0.35);
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

.auth-hero{text-align:center;padding:.5rem 0 1.25rem;animation:fadeUp .5s ease both}
.auth-copy{color:var(--text-secondary);font-size:.88rem;padding:.55rem .75rem;margin-bottom:.65rem;border-left:3px solid var(--primary);background:rgba(99,102,241,.08);border-radius:0 var(--radius) var(--radius) 0}
.auth-tagline{color:var(--text-secondary)} .auth-subtagline{color:var(--text-muted);font-size:.85rem}
.auth-panel{background:linear-gradient(145deg,rgba(15,23,42,.95),rgba(30,41,59,.88));border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.25rem 1.35rem;box-shadow:0 20px 50px rgba(0,0,0,.25)}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.hero-title{font-family:'Space Grotesk',sans-serif;font-size:2.75rem;font-weight:800;background:linear-gradient(135deg,#fff,var(--primary-light),var(--secondary));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.brand-chip{display:flex;align-items:center;gap:.75rem;padding:.85rem 1rem;background:linear-gradient(135deg,rgba(99,102,241,.12),rgba(6,182,212,.06));border:1px solid var(--border);border-radius:var(--radius-lg);margin-bottom:.35rem}
.verified-badge{display:inline-flex;width:1.05rem;height:1.05rem;margin-left:.2rem;border-radius:50%;background:#0095f6;align-items:center;justify-content:center;vertical-align:middle}
.profile-stats{display:grid;grid-template-columns:repeat(5,1fr);gap:.55rem;margin:1rem 0}
@media(max-width:900px){.profile-stats{grid-template-columns:repeat(3,1fr)}}
.stat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.65rem}
.stat-pill{text-align:center;padding:.85rem;background:rgba(99,102,241,.08);border:1px solid var(--border);border-radius:var(--radius)}
.stat-pill .num{font-size:1.5rem;font-weight:900;color:var(--primary-light);font-family:'Space Grotesk',sans-serif}
.stat-pill .cap{font-size:.65rem;text-transform:uppercase;color:var(--text-muted)}
.sh{position:relative;overflow:hidden}.sh-glow{position:absolute;top:-50%;right:-5%;width:180px;height:180px;background:radial-gradient(circle,var(--primary-glow),transparent 70%);pointer-events:none}
.stApp::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.2;background-image:radial-gradient(rgba(148,163,184,.12) 1px,transparent 1px);background-size:26px 26px}
.user-profile-card{padding:1.5rem;border-radius:var(--radius-lg);background:linear-gradient(145deg,rgba(15,23,42,.92),rgba(30,41,59,.85));border:1px solid var(--border);box-shadow:0 16px 40px rgba(0,0,0,.22)}
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
