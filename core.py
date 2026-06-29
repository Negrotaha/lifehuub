"""Database client, caching, and shared helpers."""
import os, time, hashlib, base64, requests, io, html, random, re as _re, json
from datetime import datetime, date, timedelta, timezone
from PIL import Image
import streamlit as st
from supabase import create_client, Client
from postgrest.types import ReturnMethod
from config import GROQ_API_KEY, GROQ_BASE_URL, PROFILE_COLS, GROQ_MODEL_CANDIDATES

def get_user_profile(user_id):
    def load():
        sb = get_sb()
        result = sb.table("profiles").select(PROFILE_COLS).eq("id", user_id).execute()
        return result.data[0] if result.data else None
    return session_cache_get(f"profile_{user_id}", 30, load)

def get_user_by_username(username):
    if not username:
        return None
    def load():
        try:
            sb = get_sb()
            result = sb.table("profiles").select(PROFILE_COLS).eq("username", username).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    return session_cache_get(f"profile_username_{username}", 30, load)

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

def hp(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

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

def check_rate_limit(action: str, limit: int = 6, seconds: int = 60, warn: bool = True) -> bool:
    key = f"rate_{action}"
    now = time.time()
    hits = [t for t in st.session_state.get(key, []) if now - t < seconds]
    if len(hits) >= limit:
        if warn:
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
        prof = sb.table("profiles").select(PROFILE_COLS).eq("id", st.session_state.user_id).limit(1).execute()
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
    def load():
        sb = get_sb()
        try:
            r = sb.rpc("get_platform_stats").execute()
            if r.data:
                row = r.data[0]
                return int(row.get("members") or 0), int(row.get("posts") or 0), int(row.get("messages") or 0)
        except Exception:
            pass
        try:
            mc = sb.table("profiles").select("id", count="exact").execute().count or 0
            pc = sb.table("posts").select("id", count="exact").execute().count or 0
            msg = sb.table("messages").select("id", count="exact").execute().count or 0
        except Exception:
            mc, pc, msg = 0, 0, 0
        return mc, pc, msg
    return session_cache_get("platform_stats", 120, load)

def get_sidebar_badges(sb, user_id):
    def load():
        try:
            dm = sb.table("messages").select("sender_id").eq("receiver_id", user_id).eq("is_read", False).execute()
            dm_count = len(dm.data or [])
            ment = sb.table("mentions").select("id", count="exact").eq("mentioned_user_id", user_id).eq("is_read", False).execute()
            notif = sb.table("notifications").select("id", count="exact").eq("user_id", user_id).eq("is_read", False).execute()
            return dm_count, ment.count or 0, notif.count or 0
        except Exception:
            return 0, 0, 0
    return session_cache_get(f"sidebar_badges_{user_id}", 25, load)

def touch_last_seen(sb, user_id):
    if time.time() - st.session_state.get("_last_seen_touch", 0) < 90:
        return
    try:
        sb.table("profiles").update({"last_seen": datetime.now(timezone.utc).isoformat()}).eq("id", user_id).execute()
        st.session_state["_last_seen_touch"] = time.time()
    except Exception:
        pass

def get_profile_page_stats(sb, user_id):
    def load():
        try:
            fol = sb.table("user_follows").select("id", count="exact").eq("following_id", user_id).execute().count or 0
            fing = sb.table("user_follows").select("id", count="exact").eq("follower_id", user_id).execute().count or 0
            posts = sb.table("posts").select("id", count="exact").eq("user_id", user_id).execute().count or 0
            habits = sb.table("habits").select("id", count="exact").eq("user_id", user_id).execute().count or 0
            msgs = sb.table("messages").select("id", count="exact").eq("sender_id", user_id).execute().count or 0
            events = sb.table("events").select("id", count="exact").eq("user_id", user_id).execute().count or 0
            return fol, fing, posts, habits, msgs, events
        except Exception:
            return 0, 0, 0, 0, 0, 0
    return session_cache_get(f"profile_page_stats_{user_id}", 30, load)


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
