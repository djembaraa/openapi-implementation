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
    # Fetch Messages
    current_messages = []
    if st.session_state.current_session_id:
        msgs = db.get_messages(st.session_state.current_session_id)
        current_messages = [{"role": m["role"], "content": m["content"]} for m in msgs]

    # Empty State (Mirip referensi screenshot kedua)
    if len(current_messages) == 0:
        st.markdown("<h1 class='center-text' style='font-size: 3.5rem; margin-top:20px; font-weight:700;'>Ai Chat</h1>", unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        def render_card(icon, title, subtitle, prompt, key_suffix):
            st.markdown(f"<div class='prompt-card'><div class='card-title'>{title}</div><div class='card-subtitle'>{subtitle}</div></div>", unsafe_allow_html=True)
            if st.button("Gunakan", key=f"btn_{key_suffix}", use_container_width=True):
                st.session_state.preset_prompt = prompt
                st.rerun()

        with col1:
            st.markdown("<div class='col-header'>🕒 Recents</div>", unsafe_allow_html=True)
            render_card("📄", "Ringkas Teks", "Buat ringkasan dari artikel atau laporan.", "Buatkan ringkasan eksekutif dari teks berikut:", "c1_1")
            st.write("")
            render_card("💡", "Bantu Pemrograman", "Selesaikan masalah kode dengan efisien.", "Bantu saya memperbaiki error pada kode Python berikut:", "c1_2")
            st.write("")
            render_card("🎨", "Ide Kreatif", "Dapatkan inspirasi untuk proyek baru.", "Berikan saya 3 ide proyek aplikasi AI sederhana:", "c1_3")
            
        with col2:
            st.markdown("<div class='col-header'>🔥 Frequent</div>", unsafe_allow_html=True)
            render_card("😊", "Analisis Sentimen", "Cek emosi dari sebuah kalimat.", "Analisis sentimen dari kalimat ini:", "c2_1")
            st.write("")
            render_card("📝", "Cek Tata Bahasa", "Perbaiki struktur tulisan Anda.", "Perbaiki tata bahasa dari paragraf berikut agar lebih profesional:", "c2_2")
            st.write("")
            render_card("🔍", "Riset Data", "Kumpulkan poin-poin penting.", "Jelaskan konsep dasar tentang Retrieval-Augmented Generation:", "c2_3")
            
        with col3:
            st.markdown("<div class='col-header'>⭐ Recommended</div>", unsafe_allow_html=True)
            render_card("🌍", "Penerjemah", "Terjemahkan teks dengan natural.", "Terjemahkan paragraf berikut ke bahasa Inggris yang kasual:", "c3_1")
            st.write("")
            render_card("📊", "Analisis Data", "Dapatkan insight dari angka.", "Buatkan saya fungsi Python untuk menghitung rata-rata dari list:", "c3_2")
            st.write("")
            render_card("🤖", "Tanya AI", "Diskusikan apa saja dengan AI.", "Siapa penemu bahasa pemrograman Python?", "c3_3")

    # Display chat
    for msg in current_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Bagian Input Prompt dan Unggah Dokumen Berdampingan yang SANGAT RAPI
    # Menggunakan st.popover agar terlihat seperti icon paperclip di pinggir chat input
    st.markdown("<br><br>", unsafe_allow_html=True) 
    
    # Kita menggunakan container agar popover uploader dan chat input terlihat berdampingan
    input_col1, input_col2 = st.columns([1, 15])
    
    with input_col1:
        # Tombol attachment popover yang sejajar
        with st.popover("📎"):
            st.caption("Unggah Dokumen (PDF/TXT) untuk RAG")
            uploaded_file = st.file_uploader("Pilih file", type=["pdf", "txt"], label_visibility="collapsed")
            if uploaded_file:
                if st.button("Proses Dokumen", type="primary", use_container_width=True):
                    with st.spinner("Mengekstrak teks..."):
                        text = ai.extract_text_from_upload(uploaded_file)
                        if text:
                            chunks = ai.chunk_text(text)
                            embeddings = ai.generate_embeddings(chunks)
                            if len(embeddings) > 0:
                                st.session_state.document_text = text
                                st.session_state.chunks = chunks
                                st.session_state.embeddings = embeddings
                                st.success(f"Berhasil membaca dokumen!")

    with input_col2:
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

    st.markdown("<p class='footer-text'>AI can make mistakes. Check important info. Privacy Policy | Legal Notice</p>", unsafe_allow_html=True)
