"""Reusable UI components."""
import streamlit as st
import streamlit.components.v1 as components
from config import APP_TAGLINE, LOGO_SRC
from core import escape_html

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
          <div class="sh-glow"></div>
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
        f'<div class="face {cls}"><span class="ico">{ico}</span><span class="lbl">{lbl}</span></div>'
        for cls, ico, lbl in faces
    )
    components.html(
        f"""
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"><style>
        html, body {{ margin:0; padding:0; background:transparent; overflow:hidden; font-family:Inter,sans-serif; }}
        .stage {{ width:100%; height:250px; display:flex; align-items:center; justify-content:center; perspective:900px; }}
        .cube {{ width:120px; height:120px; position:relative; transform-style:preserve-3d; animation:spin 14s linear infinite; }}
        @keyframes spin {{ from {{ transform:rotateX(-18deg) rotateY(0deg); }} to {{ transform:rotateX(-18deg) rotateY(360deg); }} }}
        .face {{ position:absolute; width:120px; height:120px; display:flex; flex-direction:column; align-items:center; justify-content:center;
          background:rgba(15,23,42,0.92); border:1px solid rgba(99,102,241,0.35); border-radius:14px; box-shadow:0 0 30px rgba(99,102,241,0.2); }}
        .ico {{ font-size:1.6rem; }} .lbl {{ font-size:0.62rem; color:#94a3b8; margin-top:0.25rem; text-transform:uppercase; letter-spacing:0.06em; }}
        .front  {{ transform:rotateY(0deg) translateZ(60px); }}
        .back   {{ transform:rotateY(180deg) translateZ(60px); }}
        .right  {{ transform:rotateY(90deg) translateZ(60px); }}
        .left   {{ transform:rotateY(-90deg) translateZ(60px); }}
        .top    {{ transform:rotateX(90deg) translateZ(60px); }}
        .bottom {{ transform:rotateX(-90deg) translateZ(60px); }}
        </style></head><body><div class="stage"><div class="cube">{faces_html}</div></div></body></html>
        """,
        height=260,
    )


def verified_badge_html():
    return '<span class="verified-badge" title="Verified"><svg width="10" height="10" viewBox="0 0 24 24" fill="white"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></span>'
