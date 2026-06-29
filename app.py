"""LifeHub entry point — Streamlit Community Cloud runs this file."""
import streamlit as st
from config import APP_NAME, CSS_VERSION
from theme import inject_css, inject_theme_css
from core import init_session_state, get_sb, refresh_current_user_session, touch_last_seen, get_user_by_username
from auth_tokens import get_recovery_tokens_from_url, restore_login_from_saved_tokens, clear_auth_tokens_from_browser
from auth_pages import auth_page, reset_password_page
from layout import sidebar, view_user_profile
from ui import logo_img
from pages import (
    home_page, notifications_page, discover_page, channels_page,
    ai_chat_page, live_chat_page, calendar_page, habits_page, profile_page, admin_page,
)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    touch_last_seen(sb, st.session_state.user_id)
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
