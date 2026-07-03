# Arsitektur Modular Djembar AI

Aplikasi ini menggunakan pola arsitektur **MVC-like Modular** untuk memastikan skalabilitas, pemisahan tanggung jawab (Separation of Concerns), dan kemudahan pemeliharaan.

## Struktur Direktori

```text
/responsi-psc-djembar-arafat-21sa1156
├── .streamlit/
│   └── config.toml       # Tema gelap ala ChatGPT
├── docs/                 # Dokumentasi sistem
├── src/                  # Kode inti modular
│   ├── ui/               # Lapisan Presentasi (User Interface)
│   │   ├── admin.py      # Tampilan khusus Admin Dashboard
│   │   ├── auth.py       # Tampilan Login/Register & OAuth
│   │   └── chat.py       # Tampilan Chatbot, Sidebar, dan RAG
│   ├── ai.py             # Lapisan Logika AI (RAG, Embeddings, LLM)
│   ├── config.py         # Lapisan Konfigurasi (Load .env, init Client)
│   └── database.py       # Lapisan Data (CRUD ke Supabase)
├── main.py               # Entry point (Router / Controller utama)
├── database.sql          # Skema inisialisasi basis data
├── requirements.txt      # Dependensi Python
```

## Alur Kerja (Workflow)

1. **Routing (`main.py`)** 
   - Mengecek apakah ada parameter `code` dari Google OAuth. Jika ada, tukar kode tersebut dengan sesi (*exchange code for session*).
   - Mengecek *Session State* `logged_in`. Jika salah (False), tampilkan `auth.py`.
   - Jika benar (True), arahkan berdasarkan peran (*role*).
2. **Autentikasi (`src/ui/auth.py`)**
   - Menggunakan `supabase.auth` (Native Auth). Email & Password atau Google OAuth via metode PKCE.
3. **Logika Inti (`src/ai.py` & `src/database.py`)**
   - Saat pengguna berinteraksi di `chat.py`, fungsi UI akan memanggil *DatabaseManager* untuk menyimpan pesan.
   - Panggilan API ke OpenAI dibungkus dengan baik di kelas `AIAssistant` sehingga UI tetap bersih dari kode rumit.
4. **Admin Panel (`src/ui/admin.py`)**
   - Jika `st.session_state.user_email` cocok dengan `ADMIN_EMAIL` di file konfigurasi rahasia (`.env`), pengguna diberikan akses ke tombol "Admin Dashboard".
   - `admin.py` akan menarik seluruh data tanpa batasan (memanfaatkan RLS Policy khusus Admin di database).
