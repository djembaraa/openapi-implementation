import streamlit as st
from typing import Callable, Any
from src.database import DatabaseManager
from src.ai import AIAssistant
from src.config import get_admin_email

def render_sidebar(db: DatabaseManager, ai: AIAssistant):
    with st.sidebar:
        st.markdown("### 👤 Akun Anda")
        st.write(f"Logged in as: **{st.session_state.user_email}**")
        
        # Tampilkan link ke Admin Dashboard jika user ini adalah admin
        if st.session_state.user_email == get_admin_email():
            st.success("👑 Anda adalah Admin")
            if st.button("Masuk Admin Dashboard", use_container_width=True):
                st.session_state.view = "admin"
                st.rerun()

        if st.button("Logout", use_container_width=True):
            db.client.auth.sign_out()
            st.session_state.clear()
            st.rerun()
            
        st.divider()
        if st.button("➕ Sesi Obrolan Baru", type="primary", use_container_width=True):
            st.session_state.current_session_id = None
            st.rerun()
            
        st.markdown("### 💬 Riwayat Obrolan")
        sessions = db.get_user_sessions(st.session_state.user_id)
        for s in sessions:
            if st.button(f"📝 {s['title']}", key=f"sess_{s['id']}", use_container_width=True):
                st.session_state.current_session_id = s['id']
                st.rerun()
                
        st.divider()
        st.markdown("### 📄 Unggah Konteks (RAG)")
        uploaded_file = st.file_uploader("", type=["pdf", "txt"])
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
                            st.success(f"Berhasil memproses dokumen!")

def render_chat(db: DatabaseManager, ai: AIAssistant):
    # Fetch Messages
    current_messages = []
    if st.session_state.current_session_id:
        msgs = db.get_messages(st.session_state.current_session_id)
        current_messages = [{"role": m["role"], "content": m["content"]} for m in msgs]

    # Empty State (Cards)
    if len(current_messages) == 0:
        st.markdown("<div class='main-title'>Djembar AI</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        def card(col, icon, title, subtitle, prompt):
            with col:
                if st.button(f"{icon} {title}\n\n{subtitle}", use_container_width=True, key=title):
                    st.session_state.preset_prompt = prompt
                    st.rerun()

        card(col1, "📄", "Ringkas Dokumen", "Unggah dokumen di kiri lalu klik ini.", "Tolong buatkan ringkasan eksekutif dari dokumen yang baru saja saya unggah.")
        card(col2, "😊", "Analisis Sentimen", "Cek sentimen dari sebuah teks.", "Tolong analisis sentimen dari kalimat berikut ini:\n[Ketik kalimat Anda di sini]")
        card(col3, "💡", "Bantu Pemrograman", "Tanyakan seputar kode Python.", "Buatkan saya fungsi Python untuk menghitung deret Fibonacci.")

    # Display chat
    for msg in current_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    prompt_to_process = None
    if st.session_state.preset_prompt:
        prompt_to_process = st.session_state.preset_prompt
        st.session_state.preset_prompt = None
    elif prompt := st.chat_input("How can I help you?"):
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

    st.markdown("<p class='footer-text'>Djembar AI can make mistakes. Check important info.</p>", unsafe_allow_html=True)
