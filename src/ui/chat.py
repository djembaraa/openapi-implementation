import streamlit as st
from typing import Callable, Any
from src.database import DatabaseManager
from src.ai import AIAssistant
from src.config import get_admin_email

def render_sidebar(db: DatabaseManager, ai: AIAssistant):
    with st.sidebar:
        st.markdown("### 👤 Akun Anda")
        st.write(f"Masuk sebagai: **{st.session_state.user_email}**")
        
        if st.session_state.user_email == get_admin_email():
            if st.button("👑 Dasbor Admin", use_container_width=True):
                st.session_state.view = "admin"
                st.rerun()

        if st.button("Keluar (Logout)", use_container_width=True):
            db.client.auth.sign_out()
            st.session_state.clear()
            st.rerun()
            
        st.divider()
        st.markdown("### 💡 Bantuan Prompt")
        with st.popover("Pilih Template Prompt", use_container_width=True):
            templates = db.get_prompt_templates()
            if not templates:
                st.info("Template belum tersedia di Supabase.")
            else:
                for t in templates:
                    if st.button(f"{t.get('icon', '📌')} {t['title']}", use_container_width=True, key=f"tpl_{t['id']}"):
                        st.session_state.chat_input_key = t['prompt_text']
        
        st.divider()
        if st.button("➕ Obrolan Baru", type="primary", use_container_width=True):
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
    # Inisialisasi FAISS Index dari memory jika ada
    faiss_index = None
    if "embeddings" in st.session_state and len(st.session_state.embeddings) > 0:
        faiss_index = ai.build_faiss_index(st.session_state.embeddings)
        
    current_messages = []
    if st.session_state.current_session_id:
        msgs = db.get_messages(st.session_state.current_session_id)
        current_messages = [{"role": m["role"], "content": m["content"]} for m in msgs]

    if len(current_messages) == 0:
        st.markdown("<h1 class='center-text' style='font-size: 4rem; margin-top:5vh; margin-bottom: 2rem; font-weight:700;'>Ai Chat</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        def render_clean_card(icon, title, prompt):
            if st.button(f"{icon} {title}", use_container_width=True):
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

    if prompt_obj:
        # 1. Jika ada file (PDF, TXT, JPG, PNG)
        if getattr(prompt_obj, "files", None):
            with st.spinner("Memproses file..."):
                for uploaded_file in prompt_obj.files:
                    fname = uploaded_file.name.lower()
                    if fname.endswith(".pdf") or fname.endswith(".txt"):
                        text = ai.extract_text_from_upload(uploaded_file)
                        if text:
                            chunks = ai.chunk_text(text)
                            embeddings = ai.generate_embeddings(chunks)
                            if len(embeddings) > 0:
                                st.session_state.document_text = text
                                st.session_state.chunks = chunks
                                st.session_state.embeddings = embeddings
                                faiss_index = ai.build_faiss_index(embeddings)
                                st.success(f"Berhasil mengindeks dokumen {uploaded_file.name} ke FAISS Vector DB!")
                    elif fname.endswith(".png") or fname.endswith(".jpg") or fname.endswith(".jpeg"):
                        uploaded_image_base64 = ai.encode_image(uploaded_file)
                        st.success(f"Gambar {uploaded_file.name} siap dianalisis!")

        # 2. Jika ada Voice Note (Microphone) -> Konversi Speech to Text (STT)
        if getattr(prompt_obj, "audio", None):
            with st.spinner("Mengubah suara menjadi teks..."):
                transcribed_text = ai.transcribe_audio(prompt_obj.audio)
                if transcribed_text:
                    prompt_to_process = transcribed_text

        # 3. Jika ada teks yang diketik manual (atau melengkapi gambar/suara)
        if getattr(prompt_obj, "text", None):
            # Gabungkan dengan hasil STT jika ada (walau jarang terjadi bersamaan)
            if prompt_to_process:
                prompt_to_process += " " + prompt_obj.text
            else:
                prompt_to_process = prompt_obj.text
                
        # Fallback jika hanya unggah gambar tanpa ketik apa-apa
        if not prompt_to_process and uploaded_image_base64:
            prompt_to_process = "Tolong analisis dan jelaskan apa yang ada di gambar ini."

    if prompt_to_process:
        with st.chat_message("user"):
            st.markdown(prompt_to_process)
            
        if not st.session_state.current_session_id:
            title = prompt_to_process[:30] + "..." if len(prompt_to_process) > 30 else prompt_to_process
            sess_id = db.create_session(st.session_state.user_id, title)
            st.session_state.current_session_id = sess_id
            
        db.add_message(st.session_state.current_session_id, "user", prompt_to_process)
        current_messages.append({"role": "user", "content": prompt_to_process})
        
        # Gunakan FAISS index untuk RAG
        context = ""
        if "chunks" in st.session_state and faiss_index is not None:
            context = ai.get_relevant_context(prompt_to_process, st.session_state.chunks, faiss_index)
        
        with st.chat_message("assistant"):
            with st.spinner("Berpikir..."):
                answer, r_time, tokens = ai.get_response(
                    prompt=prompt_to_process, 
                    context=context, 
                    history=current_messages,
                    base64_image=uploaded_image_base64
                )
                st.markdown(answer)
                st.caption(f"⏱️ {r_time} dtk | 🪙 {tokens} tokens")
                
                # Hasilkan audio (Text-to-Speech)
                with st.spinner("Menghasilkan suara..."):
                    audio_fp = ai.generate_speech(answer)
                    if audio_fp:
                        st.audio(audio_fp, format="audio/mp3")

                db.add_message(st.session_state.current_session_id, "assistant", answer)

    st.markdown("<p class='footer-text'>AI can make mistakes. Check important info. Privacy Policy | Legal Notice</p>", unsafe_allow_html=True)
