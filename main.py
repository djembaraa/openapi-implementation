import streamlit as st
import numpy as np
from src.config import get_openai_client, get_supabase_client
from src.database import DatabaseManager
from src.ai import AIAssistant
from src.ui.auth import render_login, handle_oauth_redirect
from src.ui.chat import render_sidebar, render_chat
from src.ui.admin import render_admin_dashboard

# Konfigurasi Halaman (Harus dipanggil paling pertama)
st.set_page_config(page_title="Djembar AI", page_icon="✨", layout="wide")

# CSS Global yang Diperbaiki
st.markdown("""
<style>
    /* Global Reset & Colors */
    .stApp { background-color: #1e1e1e; color: #ececec; }
    .block-container { padding-top: 3rem; max-width: 900px; }
    
    /* Typography */
    h1, h2, h3 { color: #ffffff !important; }
    
    /* Prompt Cards */
    .prompt-card { background-color: #2b2d31; padding: 20px; border-radius: 12px; border: 1px solid #3f4147; cursor: pointer; height: 100%; transition: all 0.2s ease; margin-bottom: 10px; }
    .prompt-card:hover { background-color: #3f4147; transform: translateY(-2px); }
    .card-title { font-weight: 600; font-size: 1rem; margin-bottom: 8px; color: #10a37f; }
    .card-subtitle { font-size: 0.85rem; color: #b4b4b4; }
    
    /* Chat Bubbles */
    .stChatMessage { background-color: transparent; }
    .stChatMessage[data-testid="chat-message-user"] { background-color: #2b2d31; border-radius: 15px; padding: 15px 20px; max-width: 85%; margin-left: auto; border: 1px solid #3f4147; }
    .stChatMessage[data-testid="chat-message-assistant"] { padding: 15px 0px; }
    
    /* Inputs */
    .stChatInputContainer { border: 1px solid #3f4147 !important; border-radius: 20px !important; background-color: #2b2d31 !important; padding: 5px 15px !important; }
    
    /* Layout Helpers */
    .center-text { text-align: center; }
    .footer-text { text-align: center; font-size: 0.75rem; color: #8e8e8e; margin-top: 15px; }
    
    /* Admin KPI Cards */
    .kpi-card { background-color: #2b2d31; padding: 20px; border-radius: 10px; border-left: 4px solid #10a37f; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .kpi-value { font-size: 2rem; font-weight: bold; color: #ffffff; }
    .kpi-label { font-size: 0.9rem; color: #b4b4b4; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

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
handle_oauth_redirect(supabase_client)

if not st.session_state.logged_in:
    render_login(supabase_client)
else:
    if st.session_state.view == "admin":
        render_admin_dashboard(db)
    else:
        render_sidebar(db, ai)
        render_chat(db, ai)
