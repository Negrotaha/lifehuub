-- ============================================================
-- LifeHub - Optimized Supabase Schema
-- Run this in Supabase SQL Editor for a clean install.
--
-- Warning: this drops LifeHub app tables. It does not delete auth.users.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

DROP TABLE IF EXISTS mentions CASCADE;
DROP TABLE IF EXISTS typing_status CASCADE;
DROP TABLE IF EXISTS post_reactions CASCADE;
DROP TABLE IF EXISTS channel_messages CASCADE;
DROP TABLE IF EXISTS channel_members CASCADE;
DROP TABLE IF EXISTS channels CASCADE;
DROP TABLE IF EXISTS habit_logs CASCADE;
DROP TABLE IF EXISTS habits CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS posts CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;

DROP TRIGGER IF EXISTS on_auth_user_created_lifehub ON auth.users;
DROP FUNCTION IF EXISTS public.handle_lifehub_new_user();

-- Profiles are keyed by Supabase Auth user id. app.py signs users in
-- through Supabase Auth, then reads this table by auth user id.
CREATE TABLE profiles (
    id           UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username     TEXT UNIQUE NOT NULL CHECK (username ~ '^[A-Za-z0-9_]{3,24}$'),
    email        TEXT UNIQUE NOT NULL,
    bio          TEXT DEFAULT '',
    avatar_url   TEXT,
    avatar_color TEXT DEFAULT '#5865F2',
    latitude     DOUBLE PRECISION DEFAULT 33.5731,
    longitude    DOUBLE PRECISION DEFAULT -7.5898,
    is_admin     BOOLEAN DEFAULT FALSE,
    is_banned    BOOLEAN DEFAULT FALSE,
    last_seen    TIMESTAMPTZ DEFAULT NOW(),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE posts (
    id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id    UUID REFERENCES profiles(id) ON DELETE CASCADE,
    username   TEXT NOT NULL,
    content    TEXT NOT NULL CHECK (char_length(content) <= 500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE post_reactions (
    id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    post_id    UUID REFERENCES posts(id) ON DELETE CASCADE,
    user_id    UUID REFERENCES profiles(id) ON DELETE CASCADE,
    emoji      TEXT NOT NULL CHECK (emoji IN ('❤️', '👍', '😂', '🔥')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(post_id, user_id, emoji)
);

CREATE TABLE messages (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    sender_id   UUID REFERENCES profiles(id) ON DELETE CASCADE,
    receiver_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    is_read     BOOLEAN DEFAULT FALSE,
    file_url    TEXT,
    file_name   TEXT,
    file_type   TEXT CHECK (file_type IS NULL OR file_type IN ('image', 'file')),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    CHECK (sender_id <> receiver_id)
);

CREATE TABLE typing_status (
    id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id    UUID REFERENCES profiles(id) ON DELETE CASCADE,
    target_id  UUID REFERENCES profiles(id) ON DELETE CASCADE,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, target_id),
    CHECK (user_id <> target_id)
);

CREATE TABLE events (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     UUID REFERENCES profiles(id) ON DELETE CASCADE,
    title       TEXT NOT NULL CHECK (char_length(title) <= 120),
    description TEXT DEFAULT '' CHECK (char_length(description) <= 300),
    event_date  TIMESTAMPTZ NOT NULL,
    color       TEXT DEFAULT 'blurple',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE habits (
    id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id    UUID REFERENCES profiles(id) ON DELETE CASCADE,
    username   TEXT NOT NULL,
    name       TEXT NOT NULL CHECK (char_length(name) <= 80),
    emoji      TEXT DEFAULT '⭐',
    frequency  TEXT DEFAULT 'Daily' CHECK (frequency IN ('Daily', 'Weekly')),
    is_shared  BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE habit_logs (
    id        UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    habit_id  UUID REFERENCES habits(id) ON DELETE CASCADE,
    user_id   UUID REFERENCES profiles(id) ON DELETE CASCADE,
    log_date  DATE NOT NULL,
    logged_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(habit_id, user_id, log_date)
);

CREATE TABLE channels (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL CHECK (name ~ '^[a-z0-9][a-z0-9_-]{1,31}$'),
    description TEXT DEFAULT '' CHECK (char_length(description) <= 200),
    created_by  UUID REFERENCES profiles(id) ON DELETE SET NULL,
    is_public   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE channel_members (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    channel_id   UUID REFERENCES channels(id) ON DELETE CASCADE,
    user_id      UUID REFERENCES profiles(id) ON DELETE CASCADE,
    joined_at    TIMESTAMPTZ DEFAULT NOW(),
    last_read_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(channel_id, user_id)
);

CREATE TABLE channel_messages (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    channel_id      UUID REFERENCES channels(id) ON DELETE CASCADE,
    sender_id       UUID REFERENCES profiles(id) ON DELETE CASCADE,
    sender_username TEXT NOT NULL,
    content         TEXT NOT NULL,
    file_url        TEXT,
    file_name       TEXT,
    file_type       TEXT CHECK (file_type IS NULL OR file_type IN ('image', 'file')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE mentions (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    mentioned_user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    source_type       TEXT NOT NULL CHECK (source_type IN ('post', 'direct_message', 'channel_message')),
    source_id         UUID NOT NULL,
    created_by        UUID REFERENCES profiles(id) ON DELETE CASCADE,
    is_read           BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION public.handle_lifehub_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    desired_username TEXT;
    final_username TEXT;
BEGIN
    desired_username := lower(regexp_replace(coalesce(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1), 'user'), '[^a-zA-Z0-9_]', '_', 'g'));
    desired_username := substring(desired_username from 1 for 24);

    IF desired_username !~ '^[A-Za-z0-9_]{3,24}$' THEN
        desired_username := 'user_' || substring(replace(NEW.id::text, '-', '') from 1 for 8);
    END IF;

    final_username := desired_username;
    IF EXISTS (SELECT 1 FROM profiles WHERE username = final_username) THEN
        final_username := substring(desired_username from 1 for 15) || '_' || substring(replace(NEW.id::text, '-', '') from 1 for 8);
    END IF;

    INSERT INTO profiles (id, username, email, bio)
    VALUES (
        NEW.id,
        final_username,
        coalesce(NEW.email, ''),
        coalesce(NEW.raw_user_meta_data->>'bio', '')
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created_lifehub
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_lifehub_new_user();

INSERT INTO profiles (id, username, email, bio, created_at)
SELECT
    u.id,
    CASE
        WHEN base_name ~ '^[A-Za-z0-9_]{3,15}$'
            THEN base_name || '_' || substring(replace(u.id::text, '-', '') from 1 for 8)
        ELSE 'user_' || substring(replace(u.id::text, '-', '') from 1 for 8)
    END,
    coalesce(u.email, ''),
    coalesce(u.raw_user_meta_data->>'bio', ''),
    coalesce(u.created_at, now())
FROM (
    SELECT
        au.*,
        substring(lower(regexp_replace(coalesce(au.raw_user_meta_data->>'username', split_part(au.email, '@', 1), 'user'), '[^a-zA-Z0-9_]', '_', 'g')) from 1 for 15) AS base_name
    FROM auth.users au
) u
ON CONFLICT (id) DO NOTHING;

INSERT INTO channels (name, description, is_public)
VALUES ('general', 'Welcome to LifeHub! Chat with everyone here.', TRUE)
ON CONFLICT (name) DO NOTHING;

CREATE OR REPLACE FUNCTION public.is_lifehub_admin(check_user_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT coalesce((SELECT is_admin FROM profiles WHERE id = check_user_id), FALSE);
$$;

-- Row Level Security policies. app.py stores the Supabase Auth session
-- tokens after login, so table queries run as the authenticated user.
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_reactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE typing_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE habit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE channel_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE channel_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE mentions ENABLE ROW LEVEL SECURITY;

CREATE POLICY profiles_read_authenticated
ON profiles FOR SELECT TO authenticated
USING (TRUE);

CREATE POLICY profiles_update_self_or_admin
ON profiles FOR UPDATE TO authenticated
USING (id = auth.uid() OR public.is_lifehub_admin(auth.uid()))
WITH CHECK (id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY posts_read_authenticated
ON posts FOR SELECT TO authenticated
USING (TRUE);

CREATE POLICY posts_insert_own
ON posts FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY posts_delete_owner_or_admin
ON posts FOR DELETE TO authenticated
USING (user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY post_reactions_read_authenticated
ON post_reactions FOR SELECT TO authenticated
USING (TRUE);

CREATE POLICY post_reactions_insert_own
ON post_reactions FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY post_reactions_delete_owner_or_admin
ON post_reactions FOR DELETE TO authenticated
USING (user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY messages_read_participant_or_admin
ON messages FOR SELECT TO authenticated
USING (sender_id = auth.uid() OR receiver_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY messages_insert_sender
ON messages FOR INSERT TO authenticated
WITH CHECK (sender_id = auth.uid());

CREATE POLICY messages_update_participant_or_admin
ON messages FOR UPDATE TO authenticated
USING (sender_id = auth.uid() OR receiver_id = auth.uid() OR public.is_lifehub_admin(auth.uid()))
WITH CHECK (sender_id = auth.uid() OR receiver_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY messages_delete_participant_or_admin
ON messages FOR DELETE TO authenticated
USING (sender_id = auth.uid() OR receiver_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY typing_status_read_participant
ON typing_status FOR SELECT TO authenticated
USING (user_id = auth.uid() OR target_id = auth.uid());

CREATE POLICY typing_status_insert_own
ON typing_status FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY typing_status_update_own
ON typing_status FOR UPDATE TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

CREATE POLICY events_read_authenticated
ON events FOR SELECT TO authenticated
USING (TRUE);

CREATE POLICY events_insert_own
ON events FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY events_delete_owner_or_admin
ON events FOR DELETE TO authenticated
USING (user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY habits_read_authenticated
ON habits FOR SELECT TO authenticated
USING (TRUE);

CREATE POLICY habits_insert_own
ON habits FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY habits_delete_owner_or_admin
ON habits FOR DELETE TO authenticated
USING (user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY habit_logs_read_authenticated
ON habit_logs FOR SELECT TO authenticated
USING (TRUE);

CREATE POLICY habit_logs_insert_own
ON habit_logs FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY habit_logs_delete_owner_or_admin
ON habit_logs FOR DELETE TO authenticated
USING (user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY channels_read_public_member_or_admin
ON channels FOR SELECT TO authenticated
USING (
    is_public
    OR public.is_lifehub_admin(auth.uid())
    OR EXISTS (
        SELECT 1 FROM channel_members cm
        WHERE cm.channel_id = channels.id AND cm.user_id = auth.uid()
    )
);

CREATE POLICY channels_insert_authenticated
ON channels FOR INSERT TO authenticated
WITH CHECK (created_by = auth.uid() OR created_by IS NULL);

CREATE POLICY channels_delete_creator_or_admin
ON channels FOR DELETE TO authenticated
USING (created_by = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY channel_members_read_authenticated
ON channel_members FOR SELECT TO authenticated
USING (TRUE);

CREATE POLICY channel_members_insert_self_or_admin
ON channel_members FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY channel_members_update_self_or_admin
ON channel_members FOR UPDATE TO authenticated
USING (user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()))
WITH CHECK (user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY channel_members_delete_self_or_admin
ON channel_members FOR DELETE TO authenticated
USING (user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY channel_messages_read_member_or_admin
ON channel_messages FOR SELECT TO authenticated
USING (
    public.is_lifehub_admin(auth.uid())
    OR EXISTS (
        SELECT 1 FROM channel_members cm
        WHERE cm.channel_id = channel_messages.channel_id AND cm.user_id = auth.uid()
    )
);

CREATE POLICY channel_messages_insert_member
ON channel_messages FOR INSERT TO authenticated
WITH CHECK (
    sender_id = auth.uid()
    AND EXISTS (
        SELECT 1 FROM channel_members cm
        WHERE cm.channel_id = channel_messages.channel_id AND cm.user_id = auth.uid()
    )
);

CREATE POLICY channel_messages_delete_sender_or_admin
ON channel_messages FOR DELETE TO authenticated
USING (sender_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY mentions_read_related_or_admin
ON mentions FOR SELECT TO authenticated
USING (
    mentioned_user_id = auth.uid()
    OR created_by = auth.uid()
    OR public.is_lifehub_admin(auth.uid())
);

CREATE POLICY mentions_insert_creator
ON mentions FOR INSERT TO authenticated
WITH CHECK (created_by = auth.uid());

CREATE POLICY mentions_update_mentioned_or_admin
ON mentions FOR UPDATE TO authenticated
USING (mentioned_user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()))
WITH CHECK (mentioned_user_id = auth.uid() OR public.is_lifehub_admin(auth.uid()));

CREATE POLICY mentions_delete_admin
ON mentions FOR DELETE TO authenticated
USING (public.is_lifehub_admin(auth.uid()));

CREATE INDEX idx_profiles_username ON profiles(username);
CREATE INDEX idx_profiles_last_seen ON profiles(last_seen DESC);
CREATE INDEX idx_posts_created ON posts(created_at DESC);
CREATE INDEX idx_posts_user_created ON posts(user_id, created_at DESC);
CREATE INDEX idx_post_reactions_post ON post_reactions(post_id);
CREATE INDEX idx_messages_pair_created ON messages(sender_id, receiver_id, created_at DESC);
CREATE INDEX idx_messages_receiver_unread ON messages(receiver_id, is_read, created_at DESC);
CREATE INDEX idx_messages_content_trgm ON messages USING gin (content gin_trgm_ops);
CREATE INDEX idx_typing_status_target ON typing_status(target_id, updated_at DESC);
CREATE INDEX idx_events_user_date ON events(user_id, event_date);
CREATE INDEX idx_habits_user ON habits(user_id, created_at DESC);
CREATE INDEX idx_habit_logs_habit_date ON habit_logs(habit_id, log_date DESC);
CREATE INDEX idx_channels_created ON channels(created_at);
CREATE INDEX idx_channel_members_user ON channel_members(user_id);
CREATE INDEX idx_channel_messages_channel_created ON channel_messages(channel_id, created_at DESC);
CREATE INDEX idx_channel_messages_content_trgm ON channel_messages USING gin (content gin_trgm_ops);
CREATE INDEX idx_mentions_user_unread ON mentions(mentioned_user_id, is_read, created_at DESC);

-- After your first signup, grant yourself admin:
-- UPDATE profiles SET is_admin = true WHERE username = 'your_username';