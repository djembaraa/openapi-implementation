# AI Assistant CLI - Responsi Praktik Pemrograman Sistem Cerdas

**Oleh:** Djembar Arafat (21SA1156)

Ini adalah proyek aplikasi *Command Line Interface* (CLI) AI Assistant berbasis Python yang menggunakan **OpenAI API**. Proyek ini dibuat untuk memenuhi tugas responsi Praktik Pemrograman Sistem Cerdas.

## 🌟 Fitur Utama
1. **Chat AI dengan RAG (Retrieval-Augmented Generation)**: Mampu menjawab pertanyaan pengguna berdasarkan konteks dokumen (mendukung format `.pdf` dan `.txt`). Ekstraksi dan pencarian teks menggunakan *embedding* OpenAI dan perhitungan *Cosine Similarity* menggunakan pustaka `numpy`.
2. **Ringkasan Dokumen (Summarization)**: Meringkas seluruh isi dokumen yang telah dimuat secara otomatis dalam bahasa Indonesia yang terstruktur.
3. **Analisis Sentimen**: Mengklasifikasikan teks masukan pengguna ke dalam sentimen "Positif", "Negatif", atau "Netral".
4. **Riwayat Percakapan JSON**: Seluruh histori obrolan antara pengguna dan sistem disimpan secara permanen di dalam format JSON (`chat_history.json`).
5. **Filter Etika & SARA**: AI dilarang dan akan menolak keras secara sopan setiap pertanyaan yang mengandung unsur SARA (Suku, Agama, Ras, dan Antargolongan), ujaran kebencian, atau melanggar pedoman etika, disertai alasannya.
6. **Metrik Performa (Real-time)**: Setiap kali AI menjawab, sistem akan mencetak secara langsung waktu proses respons (dalam hitungan detik) dan total token yang dihabiskan.

## 🛠️ Arsitektur & Desain
Aplikasi ini dikembangkan menggunakan konsep pemrograman Modular (Object-Oriented Programming). Kode dibagi menjadi 5 kelas utama yang menangani setiap tugas secara terpisah untuk mempermudah perawatan kode (Clean Code):
- `ConfigManager`: Menangani inisialisasi API Key dari `.env` dan penanganan error terkait konfigurasi API.
- `DocumentProcessor`: Menangani proses pembacaan file dan ekstrasi teks secara aman, termasuk ekstrak *PDF* lewat `PyPDF2`.
- `RAGSystem`: Sistem inti *Retrieval-Augmented Generation*, yang men-chunk dokumen, mengubahnya menjadi vektor *embeddings*, dan mencari kemiripan berdasarkan pertanyaan user.
- `HistoryManager`: Logika manajemen untuk membaca, menambah, menampilkan, dan menyimpan riwayat JSON.
- `AIAssistant`: Mengelola komunikasi langsung dengan endpoint `chat/completions` OpenAI. Menjalankan filter *System Prompt* serta menghitung waktu *response time* dan metrik penggunaan token.

## 📋 Persyaratan Sistem
- Python 3.8+ (direkomendasikan)
- Koneksi Internet Stabil (untuk mengakses OpenAI API)
- Sebuah OpenAI API Key yang aktif dan memiliki saldo.

## 🚀 Cara Instalasi
1. Buka Terminal (Command Prompt / PowerShell).
2. Arahkan *directory* ke folder proyek ini.
   ```bash
   cd C:\Users\djemb\Desktop\responsi-psc-djembar-arafat-21sa1156
   ```
3. *(Opsional)* Buat Virtual Environment agar instalasi rapi:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
4. Instal semua dependensi yang diperlukan melalui `pip`:
   ```bash
   pip install -r requirements.txt
   ```
5. Siapkan API Key Anda. Buka file `.env` di text editor pilihan Anda (atau buat satu jika belum ada), dan masukkan key Anda seperti di bawah ini:
   ```env
   OPENAI_API_KEY=sk-xxxxxx...
   ```

## 🎮 Panduan Penggunaan
Untuk menjalankan program AI CLI ini, gunakan perintah berikut di dalam terminal Anda:
```bash
python app.py
```

### Langkah demi Langkah di CLI:
1. **Memuat Dokumen (Opsional)**: Saat pertama kali dijalankan, aplikasi akan meminta Anda memasukkan letak file/dokumen (misalnya: `C:\path\to\document.pdf`). Apabila Anda tidak ingin memuat dokumen, tekan `Enter` saja.
2. **Menu Utama**: Aplikasi akan menampilkan menu:
   - **[1] Chat AI**: Tanya apapun! Jika sebelumnya Anda menginput dokumen, AI akan memprioritaskan menjawab berbasis isi dokumen tersebut.
   - **[2] Ringkas Dokumen**: Jika ada dokumen termuat, AI akan menyusun ringkasannya secara rinci.
   - **[3] Analisis Sentimen**: Ketikkan kalimat atau curhatan apapun, dan AI akan menentukan apakah kalimat Anda Positif, Negatif, atau Netral.
   - **[4] Riwayat Percakapan**: Menampilkan jejak rekam chat Anda dari sesi yang lalu.
   - **[5] Keluar**: Mengakhiri dan menutup aplikasi.
