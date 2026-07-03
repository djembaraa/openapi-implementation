-- HAPUS TABEL LAMA JIKA ADA
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;

-- 1. Membuat tabel 'chat_sessions' yang terhubung dengan 'auth.users'
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Membuat tabel 'chat_messages'
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Menyiapkan Row Level Security (RLS)
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- 4. Kebijakan untuk User biasa (Hanya melihat milik sendiri)
CREATE POLICY "Users can see their own sessions" ON chat_sessions
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can see their own messages" ON chat_messages
    FOR ALL USING (
        session_id IN (SELECT id FROM chat_sessions WHERE user_id = auth.uid())
    );

-- 5. Kebijakan untuk Admin (Melihat semuanya)
-- Ganti 'admin@djembar.ai' dengan email admin yang sebenarnya
CREATE POLICY "Admin can see all sessions" ON chat_sessions
    FOR ALL USING (auth.jwt() ->> 'email' = 'admin@djembar.ai');

CREATE POLICY "Admin can see all messages" ON chat_messages
    FOR ALL USING (auth.jwt() ->> 'email' = 'admin@djembar.ai');
