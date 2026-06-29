"""Login, register, and password reset."""
import streamlit as st
from PIL import Image
import io, base64
from core import (
    get_sb, check_rate_limit, ensure_user_profile_saved, set_current_user_session,
    session_cache_clear, get_platform_stats,
)
from config import APP_TAGLINE
from ui import logo_img, render_cube
from auth_tokens import clear_auth_tokens_from_browser

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
                    prof = sb.table("profiles").select(PROFILE_COLS).eq("id", auth_res.user.id).execute()
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
