"""Application pages."""
import time, io, base64, re as _re
from datetime import datetime, date, timedelta, timezone
from PIL import Image
import streamlit as st
from postgrest.types import ReturnMethod
from config import GROQ_API_KEY, MAP_LAT, MAP_LON, MAP_ZOOM, get_config
from core import (
    get_sb, session_cache_get, session_cache_clear, check_rate_limit,
    escape_html, safe_multiline, linkify_mentions, avatar_html, avatar_wrap_html,
    get_profiles_map, record_mentions, mark_mentions_read, create_notification,
    is_following, follow_counts, get_unread_counts, set_typing, is_other_typing,
    file_to_data_uri, render_attachment_html, ago, call_groq, get_profile_page_stats,
    user_activity_counts,
)
from ui import sh_header, card, verified_badge_html

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

            col1, col2 = st.columns([6, 1])
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

                # Reactions row
                counts = reaction_counts.get(p["id"], {})
                mine_reactions = my_reactions.get(p["id"], set())
                rcols = st.columns(len(REACTION_EMOJIS) + 1)
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
                            "role": "owner",
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

def profile_page():
    sb = get_sb()
    sh_header("👤", "My Profile")

    u = st.session_state.user
    initials = u["username"][:2].upper()
    safe_username = escape_html(u.get("username", "user"))
    safe_bio = safe_multiline(u.get("bio") or "No bio yet.")
    badge_html = verified_badge_html() if u.get("is_verified") else ""

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
          <h2 style="margin:0;font-family:'Space Grotesk',sans-serif;background:linear-gradient(135deg,var(--primary),var(--secondary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;">@{safe_username}{badge_html}</h2>
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
                session_cache_clear(f"profile_page_stats_{st.session_state.user_id}")
                st.success("✅ Profile updated!")
                st.rerun()

        if canceled:
            st.session_state.ep = False
            st.rerun()

    st.markdown("---")
    followers, following, post_count, habit_count, message_count, _ = get_profile_page_stats(sb, st.session_state.user_id)
    stats_html = "".join(
        f'<div class="metric"><div class="val">{v}</div><div class="lbl">{l}</div></div>'
        for v, l in [
            (followers, "Followers"), (following, "Following"), (post_count, "Posts"),
            (habit_count, "Habits"), (message_count, "Messages"),
        ]
    )
    st.markdown(f'<div class="profile-stats">{stats_html}</div>', unsafe_allow_html=True)

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
