# Dokumentasi API Terintegrasi

Sistem ini terintegrasi dengan 2 layanan API eksternal utama:

## 1. OpenAI API (Kompatibilitas Gemini)
Meskipun menggunakan pustaka Python `openai`, *Base URL* diarahkan ke Google Gemini API (`https://generativelanguage.googleapis.com/v1beta/openai/`).

**Endpoint yang Digunakan:**
- `client.chat.completions.create`: Untuk logika percakapan AI, ringkasan, dan analisis sentimen. Menggunakan model **gemini-2.5-flash**. Parameter `temperature` diset pada `0.7` untuk memberikan jawaban yang kreatif namun tetap logis.
- `client.embeddings.create`: Digunakan untuk fitur Retrieval-Augmented Generation (RAG). Model yang digunakan adalah **gemini-embedding-2**. Model ini mengubah teks ke dalam vektor multidimensi yang kemudian diukur kedekatannya menggunakan *Cosine Similarity* via `numpy`.

## 2. Supabase API (BaaS)
Berperan sebagai *Backend-as-a-Service* menggunakan pustaka `supabase` Python.

**Modul yang Digunakan:**
- `supabase.auth.sign_up()`: Mendaftarkan akun email/password baru.
- `supabase.auth.sign_in_with_password()`: Melakukan validasi *login*.
- `supabase.auth.sign_in_with_oauth()`: Menghasilkan URL dinamis untuk *login* via Google (menggunakan PKCE flow).
- `supabase.table().select/insert/eq()`: ORM bawaan untuk melakukan *query* ke PostgreSQL (Tabel `chat_sessions` dan `chat_messages`). Terintegrasi erat dengan *Row Level Security* (RLS) di sisi server database.
