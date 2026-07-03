# Djembar Arafat (21SA1156)
import streamlit as st
import numpy as np
from src.config import get_openai_client, get_supabase_client
from src.database import DatabaseManager
from src.ai import AIAssistant
from src.ui.auth import render_login, handle_oauth_redirect
from src.ui.chat import render_sidebar, render_chat
from src.ui.admin import render_admin_dashboard

# --- Inisialisasi Klien ---
supabase_client = get_supabase_client()
openai_client = get_openai_client()

db = DatabaseManager(supabase_client)
ai = AIAssistant(openai_client)

# --- State Management ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "view" not in st.session_state:
    st.session_state.view = "chat"
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "document_text" not in st.session_state:
    st.session_state.document_text = ""
    st.session_state.chunks = []
    st.session_state.embeddings = np.array([])
if "preset_prompt" not in st.session_state:
    st.session_state.preset_prompt = None

# --- Routing Utama ---
# 1. Cek apakah ada redirect dari Google OAuth
handle_oauth_redirect(supabase_client)

# 2. Jika belum login, paksa ke halaman login
if not st.session_state.logged_in:
    render_login(supabase_client)
else:
    # 3. Jika sudah login, tentukan apakah melihat Chat atau Dashboard Admin
    if st.session_state.view == "admin":
        render_admin_dashboard(db)
    else:
        render_sidebar(db, ai)
        render_chat(db, ai)
