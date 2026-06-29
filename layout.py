"""Sidebar navigation and profile overlay."""
from datetime import datetime, timedelta, timezone
import streamlit as st
from postgrest.types import ReturnMethod
from core import (
    get_sb, escape_html, avatar_wrap_html, get_sidebar_badges, check_rate_limit,
    get_user_profile, get_profile_page_stats, is_following,
    session_cache_clear, create_notification, report_target, safe_multiline,
    get_platform_stats, avatar_html,
)
from ui import logo_small, verified_badge_html

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
    followers, following, post_total, habit_total, _, event_total = get_profile_page_stats(sb, user["id"])
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
          <h2 style="margin:0;font-family:'Space Grotesk',sans-serif;color:var(--primary);">@{safe_username}{verified_badge_html() if user.get('is_verified') else ""}</h2>
          <div style="color:var(--text-muted);font-size:.78rem;margin-top:.2rem;">
            {'Admin · ' if user.get('is_admin') else ''}{escape_html(user.get('profile_badge') or 'Member')}
          </div>
          <div style="color:{'var(--primary)' if is_online else 'var(--text-muted)'};font-size:.9rem;margin:.2rem 0;">
            {'<span class="online"></span>Online now' if is_online else '⚫ Offline'}
          </div>
          <p style="color:var(--text-secondary);margin:.3rem 0 0;">{safe_bio}</p>
          <p style="color:var(--text-muted);font-size:.8rem;margin-top:.3rem;">Joined {user.get('created_at','')[:10]}</p>
        </div>
      </div>
      
      <div class="profile-stats">
        <div class="metric"><div class="val">{post_total}</div><div class="lbl">Posts</div></div>
        <div class="metric"><div class="val">{habit_total}</div><div class="lbl">Habits</div></div>
        <div class="metric"><div class="val">{event_total}</div><div class="lbl">Events</div></div>
        <div class="metric"><div class="val">{followers}</div><div class="lbl">Followers</div></div>
        <div class="metric"><div class="val">{following}</div><div class="lbl">Following</div></div>
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
                    session_cache_clear(f"profile_page_stats_{user['id']}")
                    session_cache_clear(f"profile_page_stats_{st.session_state.user_id}")
                else:
                    sb.table("user_follows").insert({
                        "follower_id": st.session_state.user_id,
                        "following_id": user["id"],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }, returning=ReturnMethod.minimal).execute()
                    create_notification(sb, user["id"], st.session_state.user_id, "follow", "New follower", f"@{st.session_state.username} followed you.", "user", st.session_state.user_id)
                    session_cache_clear(f"profile_page_stats_{user['id']}")
                    session_cache_clear(f"profile_page_stats_{st.session_state.user_id}")
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

def sidebar():
    sb = get_sb()
    with st.sidebar:
        logo_html = logo_small(40)
        st.markdown(f"""
        <div class="brand-chip">
          {logo_html}
          <div>
            <div class="brand-name">LifeHub</div>
            <div style="color:var(--text-muted);font-size:0.68rem;">Professional Workspace</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        unread_dms, unread_mentions, unread_notifications = get_sidebar_badges(sb, st.session_state.user_id)
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
                if not check_rate_limit("page_nav", limit=12, seconds=30, warn=False):
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
