-- Jalankan script SQL ini di menu "SQL Editor" pada dashboard Supabase Anda.

-- 1. Membuat tabel 'users' untuk data login
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- 2. Membuat tabel 'chat_sessions' untuk daftar sesi obrolan (sidebar)
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Membuat tabel 'chat_messages' untuk menyimpan isi pesan
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Membuat 1 user dummy untuk testing awal (Silakan ganti passwordnya nanti)
INSERT INTO users (username, password) 
VALUES ('djembar', 'rahasia123');
