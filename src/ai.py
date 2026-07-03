import time
import numpy as np
import PyPDF2
import base64
import faiss
import io
import speech_recognition as sr
from gtts import gTTS
from typing import List, Dict, Tuple, Optional
from openai import OpenAI
import streamlit as st

class AIAssistant:
    """
    Kelas untuk mengelola interaksi dengan model AI OpenAI/Gemini.
    Menangani berbagai tugas termasuk obrolan, RAG (Retrieval-Augmented Generation),
    Vision (pengolahan gambar), dan integrasi Audio (STT & TTS).
    """
    def __init__(self, client: OpenAI):
        self.client = client
        self.system_prompt = (
            "Anda adalah AI Assistant bernama 'Rayn.AI' yang cerdas, sopan, dan membantu. "
            "Anda dilarang keras menjawab pertanyaan atau permintaan yang mengandung unsur SARA "
            "(Suku, Agama, Ras, dan Antargolongan), ujaran kebencian, atau melanggar etika. "
            "Jika pengguna mengunggah dokumen (RAG), bantu mereka meringkas atau menjawab pertanyaan "
            "berdasarkan dokumen tersebut. Jika diberikan gambar, analisis gambar tersebut dengan cermat."
        )

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Memecah teks panjang menjadi potongan-potongan kecil (chunks) untuk keperluan RAG.
        
        Args:
            text (str): Teks asli yang akan dipisah.
            chunk_size (int): Ukuran maksimal karakter per potongan.
            overlap (int): Jumlah karakter tumpang tindih antar potongan untuk menjaga konteks.
            
        Returns:
            List[str]: Daftar potongan teks.
        """
        # Inisialisasi array kosong untuk menyimpan hasil potongan teks
        chunks = []
        # Menetapkan titik awal (pointer) pembacaan teks
        start = 0
        
        # Lakukan perulangan (loop) selama pointer awal belum mencapai akhir teks
        while start < len(text):
            # Tentukan batas akhir potongan (start + chunk_size)
            end = start + chunk_size
            # Potong teks dari indeks start hingga end, lalu tambahkan ke dalam list
            chunks.append(text[start:end])
            # Geser pointer awal ke depan, dikurangi 'overlap' agar ada teks yang tumpang tindih
            # Tumpang tindih ini penting agar konteks kalimat yang terpotong tidak hilang
            start += (chunk_size - overlap)
            
        # Mengembalikan list berisi potongan teks
        return chunks

    @staticmethod
    def extract_text_from_upload(uploaded_file) -> str:
        """
        Mengekstrak teks dari file yang diunggah pengguna.
        Mendukung format PDF (menggunakan PyPDF2) dan TXT.
        
        Args:
            uploaded_file: Objek file dari Streamlit st.file_uploader/chat_input.
            
        Returns:
            str: Hasil ekstraksi teks dari dokumen.
        """
        # Variabel penampung untuk seluruh teks yang berhasil dibaca
        text = ""
        try:
            # Cek apakah file yang diunggah ber-ekstensi .pdf
            if uploaded_file.name.lower().endswith(".pdf"):
                # Inisialisasi pembaca PDF menggunakan PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                # Lakukan iterasi (loop) membaca setiap halaman dalam file PDF
                for page in pdf_reader.pages:
                    # Ekstrak teks dari halaman tersebut
                    page_text = page.extract_text()
                    # Jika ada teks, gabungkan ke dalam variabel penampung dengan baris baru
                    if page_text:
                        text += page_text + "\n"
                        
            # Cek apakah file ber-ekstensi .txt
            elif uploaded_file.name.lower().endswith(".txt"):
                # Langsung baca isi file sebagai string (menggunakan encoding UTF-8)
                text = uploaded_file.getvalue().decode("utf-8")
        except Exception as e:
            # Jika file korup atau tidak terbaca, tampilkan pesan error UI
            st.error(f"Gagal membaca file: {e}")
            
        # Kembalikan string panjang berisi seluruh teks dokumen
        return text

    @staticmethod
    def encode_image(uploaded_file) -> str:
        """
        Mengonversi gambar yang diunggah menjadi string Base64 yang siap dikirim ke API Vision.
        
        Args:
            uploaded_file: Objek file gambar (JPG/PNG).
            
        Returns:
            str: Data URI Base64 dari gambar tersebut.
        """
        try:
            bytes_data = uploaded_file.getvalue()
            base64_img = base64.b64encode(bytes_data).decode('utf-8')
            mime_type = uploaded_file.type
            return f"data:{mime_type};base64,{base64_img}"
        except Exception as e:
            st.error(f"Gagal memproses gambar: {e}")
            return None

    def generate_embeddings(self, chunks: List[str]) -> np.ndarray:
        """
        Menghasilkan vektor embeddings untuk potongan teks menggunakan API embedding AI.
        
        Args:
            chunks (List[str]): Daftar potongan teks.
            
        Returns:
            np.ndarray: Matriks numpy berukuran (N, dimensi) yang berisi embeddings.
        """
        try:
            # Mengirim potongan-potongan teks ke model embedding (menggunakan Gemini-2)
            # Hasil dari pemanggilan ini adalah sekumpulan angka desimal panjang (vektor)
            response = self.client.embeddings.create(input=chunks, model="gemini-embedding-2")
            
            # Mengonversi hasil respon API menjadi Numpy Array bertipe Float32
            # Numpy Array digunakan agar kalkulasi matematika oleh FAISS nanti berjalan sangat cepat
            return np.array([item.embedding for item in response.data], dtype=np.float32)
        except Exception as e:
            # Tangani error jika koneksi internet terputus atau API bermasalah
            st.error(f"Gagal menghasilkan embeddings: {e}")
            return np.array([])

    def build_faiss_index(self, embeddings: np.ndarray):
        if len(embeddings) == 0:
            return None
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        return index

    def get_relevant_context(self, query: str, chunks: List[str], index, top_k: int = 3) -> str:
        if len(chunks) == 0 or index is None:
            # Jika tidak ada dokumen atau indeks, langsung kembalikan string kosong
            return ""
        try:
            # 1. Konversi teks pertanyaan user menjadi vektor embedding yang sama
            query_response = self.client.embeddings.create(input=query, model="gemini-embedding-2")
            query_embedding = np.array([query_response.data[0].embedding], dtype=np.float32)
            
            # 2. Cari kedekatan (kemiripan/jarak terdekat L2) antara vektor pertanyaan dan vektor dokumen
            distances, indices = index.search(query_embedding, top_k)
            
            # 3. Ambil teks asli dari array chunks berdasarkan nomor indeks (indices) hasil pencarian FAISS
            # Hanya ambil indeks yang valid (!= -1)
            return "\n\n".join([chunks[i] for i in indices[0] if i != -1])
        except Exception:
            # Gagal mencari konteks, fallback agar chat tetap bisa berlanjut meski tanpa RAG
            return ""

    def transcribe_audio(self, audio_file) -> str:
        """
        Mengubah rekaman suara (Speech) menjadi teks (Text) menggunakan Google Web Speech API.
        
        Args:
            audio_file: File audio yang direkam melalui mikrofon.
            
        Returns:
            str: Teks hasil transkripsi.
        """
        r = sr.Recognizer()
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="id-ID")
            return text
        except sr.UnknownValueError:
            st.warning("Suara tidak dapat dikenali.")
        except Exception as e:
            st.error(f"Gagal mentranskripsi audio: {e}")
        return ""

    def generate_speech(self, text: str) -> io.BytesIO:
        """
        Menghasilkan suara dari teks menggunakan gTTS (Google Text-to-Speech) versi gratis.
        """
        try:
            # Inisialisasi gTTS dengan bahasa Indonesia ('id') dan kecepatan baca normal
            tts = gTTS(text=text, lang='id', slow=False)
            
            # Membuat wadah (buffer) di dalam memori RAM (bukan di harddisk)
            fp = io.BytesIO()
            
            # Menulis file MP3 langsung ke dalam buffer RAM tersebut
            tts.write_to_fp(fp)
            
            # Kembalikan posisi pembacaan buffer ke awal (0) agar bisa diputar
            fp.seek(0)
            return fp
        except Exception as e:
            # Jika gagal (misal koneksi Google tertutup), tampilkan error
            st.error(f"Gagal menghasilkan TTS: {e}")
            return None

    def get_response(self, prompt: str, context: str, history: List[Dict[str, str]], base64_image: str = None) -> Tuple[str, float, int]:
        """
        Berkomunikasi dengan model bahasa AI untuk mendapatkan jawaban.
        Fungsi ini menangani percakapan teks, RAG (penyertaan konteks), dan Vision.
        
        Args:
            prompt (str): Pertanyaan dari pengguna.
            context (str): Konteks dari dokumen (jika ada).
            history (List[Dict[str, str]]): Riwayat percakapan sebelumnya.
            base64_image (str, optional): Gambar ter-encode Base64 jika pengguna mengunggah gambar.
            
        Returns:
            Tuple[str, float, int]: (Teks Jawaban AI, Waktu respons dalam detik, Total token yang digunakan)
        """
        # 1. Menyiapkan memori jangka panjang (Pesan Sistem Utama)
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # 2. Injeksi RAG: Jika ada konteks (jawaban pencarian FAISS dari dokumen PDF)
        if context:
            messages.append({
                "role": "system",
                "content": f"Gunakan informasi berikut dari dokumen untuk menjawab jika relevan:\n{context}"
            })
            
        # 3. Pisahkan riwayat masa lalu (history) dari input yang sedang diproses.
        # Ambil 5 pesan terakhir saja agar tidak menghabiskan terlalu banyak token
        past_messages = history[:-1] if len(history) > 0 else []
        messages.extend(past_messages[-5:])
        
        # 4. Siapkan format payload pesan baru.
        # Jika menggunakan Vision (teks + gambar), struktur payloadnya berupa list of dicts.
        user_content = [{"type": "text", "text": prompt}]
        if base64_image:
            user_content.append({"type": "image_url", "image_url": {"url": base64_image}})
            
        messages.append({"role": "user", "content": user_content})
        
        # Catat waktu mulai (untuk fitur Stopwatch)
        start_time = time.time()
        
        try:
            # 5. Panggil API AI untuk menghasilkan jawaban (menggunakan model Flash yang sangat cepat)
            response = self.client.chat.completions.create(
                model="gemini-2.5-flash-lite",
                messages=messages,
                temperature=0.7 # Kreativitas 70%
            )
            
            # Catat waktu selesai
            end_time = time.time()
            
            # 6. Ekstrak data hasil kembalian dari struktur JSON API
            answer = response.choices[0].message.content
            tokens = response.usage.total_tokens
            r_time = round(end_time - start_time, 2)
            
            return answer, r_time, tokens
        except Exception as e:
            # Tangkap semua kemungkinan error: API limit habis, koneksi putus, input tak wajar
            # Kembalikan string yang ramah ke pengguna (jangan crash-kan UI)
            return f"Maaf, terjadi kesalahan teknis (Koneksi terputus / API Key tidak valid):\n{str(e)}", 0.0, 0
