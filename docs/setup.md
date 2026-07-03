# Panduan Setup Djembar AI

## 1. Persiapan Lingkungan

Pastikan Anda memiliki Python 3.9+ terinstal.

```bash
# Instalasi pustaka
pip install -r requirements.txt
```

## 2. Pengaturan Variabel Lingkungan (.env)

Buat file `.env` di akar (*root*) proyek dan isi dengan variabel berikut:

```env
OPENAI_API_KEY=your_gemini_or_openai_key
SUPABASE_URL=https://your_project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
ADMIN_EMAIL=email_admin_anda@gmail.com
```

**Keterangan:**
- `OPENAI_API_KEY`: Kunci API. Proyek ini dikonfigurasi untuk rute Gemini via kompatibilitas OpenAI.
- `ADMIN_EMAIL`: Email yang Anda jadikan sebagai Admin tunggal. Email ini harus cocok dengan salah satu email yang Anda daftarkan di menu Auth Supabase.

## 3. Konfigurasi Google Login (Opsional)
Jika Anda mengaktifkan Google Login:
1. Buat **OAuth Client ID** di Google Cloud Console.
2. Atur Redirect URI ke: `https://<your_supabase_id>.supabase.co/auth/v1/callback`
3. Masukkan Client ID dan Secret ke **Authentication > Providers > Google** di Supabase.

## 4. Menjalankan Aplikasi

Jalankan perintah berikut di terminal:

```bash
streamlit run main.py
```
