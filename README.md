# 🌟 Rayn.AI - Asisten AI Pribadi Berbasis Web

**Oleh:** Djembar Arafat (21SA1156)

Ini adalah proyek aplikasi **Web Asisten AI (Rayn.AI)** yang dikembangkan menggunakan antarmuka **Streamlit**, pemrosesan bahasa alami (NLP), dan arsitektur database modern berbasis Cloud. Proyek ini awalnya dirancang sebagai CLI, namun telah **di-upgrade total (Over-engineered)** untuk memenuhi standar industri.

---

## ✨ Fitur Utama (Edisi Bonus Maksimal)

1. **Autentikasi Aman (Supabase Auth)**
   - Login menggunakan Email & Password.
   - **Google Single Sign-On (SSO)** menggunakan OAuth (PKCE Flow).
2. **Obrolan AI Berbasis Gemini (OpenAI Wrapper)**
   - Menggunakan model `gemini-2.5-flash` yang super cepat melalui wrapper OpenAI API.
   - Dilengkapi *System Prompt* ketat untuk menolak instruksi berbau SARA dan menjaga etika.
   - Setiap respon akan menampilkan **metrik performa** (Waktu respons & Token yang digunakan).
3. **Retrieval-Augmented Generation (RAG) dengan FAISS**
   - Mendukung unggahan dokumen `.pdf` dan `.txt`.
   - Dokumen dipotong (chunking), diubah menjadi vektor (embedding), dan disimpan di **FAISS Vector DB** (sepenuhnya berjalan lokal/gratis tanpa perlu API berbayar tambahan).
4. **Computer Vision (Analisis Gambar)**
   - Mendukung unggahan gambar `.png`, `.jpg`, `.jpeg`.
   - Mengonversi gambar ke `Base64` untuk dianalisis dan dijelaskan oleh AI.
5. **Dukungan Audio Multi-arah (Gratis 100%)**
   - **Speech-to-Text (STT):** Anda dapat menekan ikon mikrofon untuk merekam *Voice Note*, yang akan dikonversi menjadi teks menggunakan *Google Web Speech API* (`SpeechRecognition`).
   - **Text-to-Speech (TTS):** Memiliki sakelar "Mode Suara" di menu Pengaturan. Jika diaktifkan, AI akan membacakan jawabannya menggunakan `gTTS`.
6. **Dasbor Analitik Admin**
   - Khusus untuk akun dengan email yang didaftarkan sebagai Admin, akan muncul tombol masuk ke Dasbor Analitik.
   - Menampilkan metrik *Total Pengguna*, *Sesi Obrolan*, *Interaksi*, dan dapat melihat transkrip percakapan pengguna (Diawasi RLS).

---

## 🛠️ Arsitektur & Teknologi

Aplikasi ini dikembangkan dengan gaya Pemrograman Berorientasi Objek (OOP) secara sangat modular:
- `main.py` : Entri utama aplikasi dan logika perutean (Routing).
- `src/config.py` : Mengelola kunci rahasia (*Environment Variables*) dan inisialisasi API.
- `src/database.py` : Mengelola interaksi CRUD ke PostgreSQL (Supabase).
- `src/ai.py` : Pusat "Otak" aplikasi yang menangani Text, Vision, RAG (FAISS), dan Audio.
- `src/ui/` : Memisahkan antarmuka pengguna menjadi komponen modular (Auth, Chat, Admin).

Seluruh kode Python di dalamnya memiliki **Inline Comments** yang sangat rinci seperti buku tutorial untuk mempermudah penjelasan saat presentasi/responsi.

---

## 🚀 Persyaratan Sistem & Instalasi (Lokal)

Tidak perlu bingung, instalasi di lokal komputer Anda sangatlah mudah!

### 1. Persiapan
Pastikan Anda sudah menginstal **Python 3.8** atau lebih baru.
Buka Terminal / Command Prompt / PowerShell, lalu arahkan (*cd*) ke folder proyek ini.

### 2. Instalasi Dependensi
Jalankan perintah berikut untuk menginstal semua pustaka pendukung (Streamlit, PyPDF2, Faiss, SpeechRecognition, gTTS, Supabase, dll):
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Rahasia (Environment Variables)
Anda wajib membuat sebuah file bernama **`.env`** di dalam folder proyek ini (sejajar dengan `main.py`). Buka file `.env` tersebut dengan *Notepad* atau *VS Code*, lalu isikan konfigurasi berikut:

```env
# Gunakan API Key Gemini milik Google (Bukan OpenAI sungguhan agar 100% GRATIS)
# Dapatkan gratis di: https://aistudio.google.com/
OPENAI_API_KEY=AIzaSy_masukkan_api_key_gemini_anda_di_sini

# Konfigurasi Supabase (Dapatkan di Project Settings > API)
SUPABASE_URL=https://xxxxxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5...

# Email yang akan diberikan akses sebagai Super Admin
ADMIN_EMAIL=djembar@email_anda.com
```

### 4. Menjalankan Aplikasi
Setelah dependensi terinstal dan file `.env` sudah diatur, ketik perintah berikut di terminal:
```bash
streamlit run main.py
```
Browser akan otomatis terbuka dan mengarah ke `http://localhost:8501`.

Selamat! Aplikasi Rayn.AI Anda sudah siap digunakan.
