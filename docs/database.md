# Arsitektur Database & RLS

Proyek ini menggunakan **Supabase PostgreSQL** sebagai pusat data. Ada dua tabel utama selain tabel rahasia `auth.users` milik Supabase Auth.

## 1. Skema Tabel

**`chat_sessions`**
- `id`: Integer (Primary Key, Auto Increment)
- `user_id`: UUID (Foreign Key ke `auth.users`)
- `title`: Teks (Judul obrolan, diambil dari pesan pertama)
- `created_at`: Timestamp dengan zona waktu

**`chat_messages`**
- `id`: Integer (Primary Key)
- `session_id`: Integer (Foreign Key ke `chat_sessions.id`)
- `role`: Teks ('user' atau 'assistant')
- `content`: Teks (Isi pesan)
- `created_at`: Timestamp

## 2. Row Level Security (RLS)

Keamanan per-baris diaktifkan agar pengguna tidak bisa melihat obrolan pengguna lain.

- **User Biasa:** Hanya bisa memuat sesi dan pesan jika `auth.uid()` miliknya cocok dengan kolom `user_id`.
- **Admin:** Memiliki pengecualian RLS (Bypass). RLS mengecek ekstrak JSON JWT Token: `auth.jwt() ->> 'email' = 'admin@email.com'`. Jika cocok, Admin diberikan akses melihat seluruh riwayat (SELECT) untuk keperluan pemantauan di *Dashboard Admin*.

Untuk skrip SQL lengkapnya, silakan merujuk ke file `database.sql` di *root* proyek.
