"""Browser auth token persistence."""
import json
import streamlit as st
import streamlit.components.v1 as components
from core import get_sb, set_current_user_session
from config import PROFILE_COLS

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
        prof = sb.table("profiles").select(PROFILE_COLS).eq("id", auth_user.id).limit(1).execute()
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
