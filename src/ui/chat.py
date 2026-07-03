import streamlit as st
from typing import Callable, Any
from src.database import DatabaseManager
from src.ai import AIAssistant
from src.config import get_admin_email

def render_sidebar(db: DatabaseManager, ai: AIAssistant):
    """
    Me-render sidebar (navigasi samping) dari aplikasi obrolan.
    Menampilkan profil pengguna, akses dasbor admin, riwayat obrolan, dan opsi obrolan baru.
    
    Args:
        db (DatabaseManager): Instansi pengelola database.
        ai (AIAssistant): Instansi pengelola AI.
    """
    with st.sidebar:
        st.markdown("### 👤 Akun Anda")
        # Menampilkan email pengguna aktif
        st.write(f"Masuk sebagai: **{st.session_state.user_email}**")
        
        # Mengecek apakah email yang sedang aktif sama dengan email admin rahasia
        if st.session_state.user_email == get_admin_email():
            # Jika iya, munculkan tombol rahasia untuk masuk ke Dasbor Admin
            if st.button("👑 Dasbor Admin", use_container_width=True):
                # Mengubah state view menjadi 'admin' untuk memicu perubahan rute di main.py
                st.session_state.view = "admin"
                st.rerun() # Refresh paksa halaman

        # Tombol untuk keluar dari aplikasi
        if st.button("Keluar (Logout)", use_container_width=True):
            # Memanggil fungsi logout bawaan dari Supabase
            db.client.auth.sign_out()
            # Membersihkan seluruh memori sesi lokal Streamlit
            st.session_state.clear()
            st.rerun()
            
        # Pemisah garis horizontal
        st.divider()
        st.markdown("### 💡 Bantuan Prompt")
        
        # Menggunakan fitur popover (menu pop-up kecil) untuk menghemat tempat di sidebar
        with st.popover("Pilih Template Prompt", use_container_width=True):
            # Mengambil template dari database Supabase
            templates = db.get_prompt_templates()
            if not templates:
                st.info("Template belum tersedia di Supabase.")
            else:
                # Lakukan iterasi (loop) untuk merender setiap template menjadi tombol
                for t in templates:
                    # Menambahkan key unik agar tidak bentrok (id template)
                    if st.button(f"{t.get('icon', '📌')} {t['title']}", use_container_width=True, key=f"tpl_{t['id']}"):
                        # Menyimpan isi prompt ke state 'chat_input_key' agar nanti masuk ke kolom input
                        st.session_state.chat_input_key = t['prompt_text']
        
        st.divider()
        st.markdown("### ⚙️ Pengaturan")
        # Sakelar (toggle) untuk mengaktifkan atau menonaktifkan suara Text-To-Speech (TTS)
        st.session_state.tts_enabled = st.toggle("🔊 Mode Suara (TTS)", value=False, help="Aktifkan untuk membiarkan AI membacakan balasan.")
        
        st.divider()
        # Tombol untuk memulai percakapan kosong baru
        if st.button("➕ Obrolan Baru", type="primary", use_container_width=True):
            # Mengosongkan ID sesi saat ini agar halaman utama kembali ke tampilan awal (Empty State)
            st.session_state.current_session_id = None
            st.session_state.view = "chat"
            st.rerun()
            
        st.markdown("### 💬 Riwayat")
        sessions = db.get_user_sessions(st.session_state.user_id)
        for s in sessions:
            if st.button(f"{s['title']}", key=f"sess_{s['id']}", use_container_width=True):
                st.session_state.current_session_id = s['id']
                st.session_state.view = "chat"
                st.rerun()

def render_chat(db: DatabaseManager, ai: AIAssistant):
    """
    Me-render jendela obrolan utama.
    Menangani status memori (history), input pengguna (teks, gambar, audio, PDF),
    proses Retrieval-Augmented Generation (RAG), pemanggilan AI, dan Text-to-Speech (TTS).
    
    Args:
        db (DatabaseManager): Instansi pengelola database.
        ai (AIAssistant): Instansi pengelola AI.
    """
    # --- PERSIAPAN AWAL (STATE & DATABASE) ---
    # 1. Inisialisasi FAISS Index dari memory jika ada (digunakan untuk RAG PDF/Dokumen)
    faiss_index = None
    if "embeddings" in st.session_state and len(st.session_state.embeddings) > 0:
        faiss_index = ai.build_faiss_index(st.session_state.embeddings)
        
    # 2. Tarik riwayat pesan dari database berdasarkan sesi aktif (current_session_id)
    current_messages = []
    if st.session_state.current_session_id:
        msgs = db.get_messages(st.session_state.current_session_id)
        # Saring dan bentuk ulang (reformat) struktur pesan agar sesuai standar API AI
        current_messages = [{"role": m["role"], "content": m["content"]} for m in msgs]

    # --- TAMPILAN KOSONG (EMPTY STATE) ---
    # Jika tidak ada pesan (percakapan baru), render UI interaktif dengan kartu saran
    if len(current_messages) == 0:
        st.markdown("<h1 class='center-text' style='font-size: 4rem; margin-top:5vh; margin-bottom: 2rem; font-weight:700;'>Rayn.AI ✨</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        # Fungsi pembantu internal untuk merender kartu interaktif (clickable cards)
        def render_clean_card(icon, title, prompt):
            if st.button(f"{icon} {title}", use_container_width=True):
                # Jika diklik, masukkan saran teks ke dalam memori input chat utama
                st.session_state.chat_input_key = prompt

        with col1:
            st.markdown("<div class='center-text' style='color:#a0a0a0; margin-bottom:10px;'>🕒 Recents</div>", unsafe_allow_html=True)
            render_clean_card("📄", "Ringkas Artikel Panjang", "Buatkan ringkasan eksekutif dari teks berikut:")
            render_clean_card("💡", "Bantu Pemrograman", "Bantu saya memperbaiki error pada kode Python berikut:")
        with col2:
            st.markdown("<div class='center-text' style='color:#a0a0a0; margin-bottom:10px;'>🔥 Frequent</div>", unsafe_allow_html=True)
            render_clean_card("😊", "Analisis Sentimen Teks", "Analisis sentimen dari kalimat ini:")
            render_clean_card("📝", "Perbaiki Tata Bahasa", "Perbaiki tata bahasa dari paragraf berikut agar lebih profesional:")
        with col3:
            st.markdown("<div class='center-text' style='color:#a0a0a0; margin-bottom:10px;'>⭐ Recommended</div>", unsafe_allow_html=True)
            render_clean_card("🌍", "Penerjemah Bahasa", "Terjemahkan paragraf berikut ke bahasa Inggris yang kasual:")
            render_clean_card("🤖", "Tanya Seputar AI", "Jelaskan konsep dasar tentang Retrieval-Augmented Generation:")

    # --- TAMPILAN RIWAYAT (MESSAGES) ---
    # Looping seluruh riwayat pesan yang ada di memori dan render bubble chat-nya ke layar
    for msg in current_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Input Area dengan Fitur Native Streamlit 1.38+ (Super Rapi & Sejajar!)
    prompt_obj = st.chat_input(
        "Tanyakan sesuatu, unggah dokumen (PDF/TXT), foto (JPG/PNG), atau gunakan Suara (Microphone)...", 
        accept_file=True, 
        file_type=["pdf", "txt", "png", "jpg", "jpeg"],
        accept_audio=True,
        key="chat_input_key"
    )
    
    prompt_to_process = None
    uploaded_image_base64 = None

    # Jika pengguna berinteraksi dengan widget input (mengetik, ngomong, upload)
    if prompt_obj:
        # SKENARIO 1: Pengguna mengunggah dokumen (PDF/TXT) atau gambar (JPG/PNG)
        if getattr(prompt_obj, "files", None):
            # Animasi loading (spinner) agar pengguna tahu sistem sedang memproses
            with st.spinner("Memproses file..."):
                for uploaded_file in prompt_obj.files:
                    fname = uploaded_file.name.lower()
                    
                    # Logika Dokumen/Teks (FAISS RAG)
                    if fname.endswith(".pdf") or fname.endswith(".txt"):
                        # Ekstrak seluruh teks dari file
                        text = ai.extract_text_from_upload(uploaded_file)
                        if text:
                            # Potong teks dan buat embedding (vektor), lalu masukkan ke FAISS DB
                            chunks = ai.chunk_text(text)
                            embeddings = ai.generate_embeddings(chunks)
                            if len(embeddings) > 0:
                                # Simpan data tersebut secara persisten (permanen di memori lokal st)
                                st.session_state.document_text = text
                                st.session_state.chunks = chunks
                                st.session_state.embeddings = embeddings
                                faiss_index = ai.build_faiss_index(embeddings)
                                st.success(f"Berhasil mengindeks dokumen {uploaded_file.name} ke FAISS Vector DB!")
                                
                    # Logika Gambar (Computer Vision Base64)
                    elif fname.endswith(".png") or fname.endswith(".jpg") or fname.endswith(".jpeg"):
                        uploaded_image_base64 = ai.encode_image(uploaded_file)
                        st.success(f"Gambar {uploaded_file.name} siap dianalisis!")

        # SKENARIO 2: Pengguna menekan logo Mikrofon dan merekam suara (Speech-To-Text / STT)
        if getattr(prompt_obj, "audio", None):
            with st.spinner("Mengubah suara menjadi teks..."):
                # Kirim sinyal mentah audio ke recognizer Google
                transcribed_text = ai.transcribe_audio(prompt_obj.audio)
                if transcribed_text:
                    prompt_to_process = transcribed_text

        # SKENARIO 3: Pengguna mengetik teks di keyboard secara manual
        if getattr(prompt_obj, "text", None):
            # Terkadang pengguna ngomong (STT) lalu menambah teks manual. Gabungkan keduanya!
            if prompt_to_process:
                prompt_to_process += " " + prompt_obj.text
            else:
                prompt_to_process = prompt_obj.text
                
        # SKENARIO 4: Pengguna HANYA mengunggah gambar TANPA memberi intruksi / pertanyaan
        if not prompt_to_process and uploaded_image_base64:
            # Berikan pertanyaan bawaan agar AI tahu harus berbuat apa dengan gambar itu
            prompt_to_process = "Tolong analisis dan jelaskan apa yang ada di gambar ini."

    # --- PROSES EKSEKUSI AI & DATABASE ---
    # Bagian ini akan berjalan jika ada prompt yang berhasil didapatkan (dari teks, suara, atau paksaan gambar)
    if prompt_to_process:
        # 1. Tampilkan teks pengguna (bubble user) ke layar UI
        with st.chat_message("user"):
            st.markdown(prompt_to_process)
            
        # 2. Jika ini percakapan kosong (belum punya ID di database), buat rekaman baru
        if not st.session_state.current_session_id:
            # Pangkas prompt hingga 30 karakter untuk dijadikan judul navigasi di Sidebar
            title = prompt_to_process[:30] + "..." if len(prompt_to_process) > 30 else prompt_to_process
            sess_id = db.create_session(st.session_state.user_id, title)
            st.session_state.current_session_id = sess_id
            
        # 3. Simpan teks yang ditanyakan oleh user ke Database Supabase
        db.add_message(st.session_state.current_session_id, "user", prompt_to_process)
        # Menambahkan pesan ke state sementara (biar tidak perlu reload web)
        current_messages.append({"role": "user", "content": prompt_to_process})
        
        # 4. Pencarian Konteks Dokumen (RAG)
        context = ""
        # Jika indeks FAISS ada dan punya data, carikan paragraf PDF yang paling relevan
        if "chunks" in st.session_state and faiss_index is not None:
            context = ai.get_relevant_context(prompt_to_process, st.session_state.chunks, faiss_index)
        
        # 5. Render gelembung jawaban (bubble assistant)
        with st.chat_message("assistant"):
            # Tampilkan animasi "berpikir" selama jaringan AI bekerja
            with st.spinner("Berpikir..."):
                # Lempar semua beban kerja kompleks (prompt, RAG, history, Vision) ke fungsi AIAssistant.py
                answer, r_time, tokens = ai.get_response(
                    prompt=prompt_to_process, 
                    context=context, 
                    history=current_messages,
                    base64_image=uploaded_image_base64
                )
                
                # Tampilkan teks balasan AI ke layar
                st.markdown(answer)
                # Tampilkan indikator telemetri (waktu render dan token usage) di paling bawah
                st.caption(f"⏱️ {r_time} dtk | 🪙 {tokens} tokens")
                
                # 6. Fitur Bonus: Konversi Teks-Ke-Suara (TTS)
                # Hasilkan audio MP3 hanya jika mode sakelar (TTS) di-aktifkan pengguna
                if st.session_state.get("tts_enabled", False):
                    with st.spinner("Menghasilkan suara..."):
                        audio_fp = ai.generate_speech(answer)
                        if audio_fp:
                            # Render pemutar musik MP3 di dalam kolom chat
                            st.audio(audio_fp, format="audio/mp3")

                # 7. Simpan jawaban akhir si AI ke dalam Supabase Database
                db.add_message(st.session_state.current_session_id, "assistant", answer)

    st.markdown("<p class='footer-text'>AI can make mistakes. Check important info. Privacy Policy | Legal Notice</p>", unsafe_allow_html=True)
