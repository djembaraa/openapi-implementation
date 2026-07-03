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
        if st.button("➕ Obrolan Baru", type="primary", use_container_width=True):
            st.session_state.current_session_id = None
            st.rerun()
            
        st.markdown("### 💬 Riwayat")
        sessions = db.get_user_sessions(st.session_state.user_id)
        for s in sessions:
            if st.button(f"{s['title']}", key=f"sess_{s['id']}", use_container_width=True):
                st.session_state.current_session_id = s['id']
                st.rerun()

def render_chat(db: DatabaseManager, ai: AIAssistant):
    # Fetch Messages
    current_messages = []
    if st.session_state.current_session_id:
        msgs = db.get_messages(st.session_state.current_session_id)
        current_messages = [{"role": m["role"], "content": m["content"]} for m in msgs]

    # Empty State (Cards)
    if len(current_messages) == 0:
        st.markdown("<h1 class='center-text' style='font-size: 3.5rem; margin-top:20px;'>Djembar AI</h1>", unsafe_allow_html=True)
        st.markdown("<p class='center-text' style='color:#b4b4b4; margin-bottom: 3rem;'>Apa yang bisa saya bantu hari ini?</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        def card(col, icon, title, subtitle, prompt):
            with col:
                st.markdown(f"<div class='prompt-card'><div class='card-title'>{icon} {title}</div><div class='card-subtitle'>{subtitle}</div></div>", unsafe_allow_html=True)
                if st.button("Gunakan", key=f"btn_{title}", use_container_width=True):
                    st.session_state.preset_prompt = prompt
                    st.rerun()

        card(col1, "📄", "Ringkas Teks", "Buat ringkasan dari artikel atau laporan yang panjang.", "Tolong buatkan ringkasan eksekutif dari teks yang akan saya berikan berikut ini:")
        card(col2, "😊", "Analisis Sentimen", "Cek emosi dan sentimen dari sebuah kalimat.", "Tolong analisis sentimen (Positif/Negatif/Netral) dari kalimat berikut ini:\n[Ketik kalimat Anda]")
        card(col3, "💡", "Bantu Pemrograman", "Selesaikan masalah kode (*debugging*) atau pelajari algoritma.", "Buatkan saya fungsi Python untuk mengurutkan data (*sorting*) beserta penjelasannya.")

    # Display chat
    for msg in current_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Bagian Input Prompt dan Unggah Dokumen Berdampingan
    # Menggunakan container untuk menempelkannya ke bagian bawah
    st.markdown("<br><br>", unsafe_allow_html=True) # Spacer agar tidak menabrak input
    
    # RAG File Uploader in an expander directly above the chat input
    with st.expander("📎 Unggah Dokumen RAG (PDF/TXT)"):
        st.caption("Dokumen yang diunggah akan dibaca AI sebagai konteks jawaban.")
        uploaded_file = st.file_uploader("Pilih file", type=["pdf", "txt"], label_visibility="collapsed")
        if uploaded_file:
            if st.button("Proses Dokumen", use_container_width=True):
                with st.spinner("Mengekstrak teks..."):
                    text = ai.extract_text_from_upload(uploaded_file)
                    if text:
                        chunks = ai.chunk_text(text)
                        embeddings = ai.generate_embeddings(chunks)
                        if len(embeddings) > 0:
                            st.session_state.document_text = text
                            st.session_state.chunks = chunks
                            st.session_state.embeddings = embeddings
                            st.success(f"Berhasil membaca {len(chunks)} bagian teks!")
            
    prompt_to_process = None
    if st.session_state.preset_prompt:
        prompt_to_process = st.session_state.preset_prompt
        st.session_state.preset_prompt = None
    elif prompt := st.chat_input("Tanyakan sesuatu..."):
        prompt_to_process = prompt

    if prompt_to_process:
        with st.chat_message("user"):
            st.markdown(prompt_to_process)
            
        if not st.session_state.current_session_id:
            title = prompt_to_process[:30] + "..." if len(prompt_to_process) > 30 else prompt_to_process
            sess_id = db.create_session(st.session_state.user_id, title)
            st.session_state.current_session_id = sess_id
            
        db.add_message(st.session_state.current_session_id, "user", prompt_to_process)
        current_messages.append({"role": "user", "content": prompt_to_process})
        
        context = ai.get_relevant_context(prompt_to_process, st.session_state.chunks, st.session_state.embeddings)
        
        with st.chat_message("assistant"):
            with st.spinner("Berpikir..."):
                answer, r_time, tokens = ai.get_response(prompt_to_process, context, current_messages)
                st.markdown(answer)
                st.caption(f"⏱️ {r_time} dtk | 🪙 {tokens} tokens")
                db.add_message(st.session_state.current_session_id, "assistant", answer)

    st.markdown("<p class='footer-text'>AI dapat berbuat salah. Harap verifikasi informasi penting.</p>", unsafe_allow_html=True)
