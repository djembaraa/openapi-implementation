import streamlit as st
import numpy as np
from src.config import get_openai_client, get_supabase_client
from src.database import DatabaseManager
from src.ai import AIAssistant
from src.ui.auth import render_login, handle_oauth_redirect
from src.ui.chat import render_sidebar, render_chat
from src.ui.admin import render_admin_dashboard

# Konfigurasi Halaman
st.set_page_config(page_title="Djembar AI", page_icon="✨", layout="wide")

# CSS Global (Dirombak untuk matching dengan referensi)
st.markdown("""
<style>
    /* Global Reset & Colors */
    .stApp { background-color: #1e2024; color: #ececec; }
    
    /* Typography */
    h1, h2, h3, h4 { color: #ffffff !important; }
    
    /* Tombol Utama menggunakan warna request User #1c1c84 */
    .stButton > button[kind="primary"] { 
        background-color: #1c1c84 !important; 
        color: white !important; 
        border: none !important; 
    }
    .stButton > button[kind="primary"]:hover { 
        background-color: #2a2a9e !important; 
    }
    
    /* Prompt Cards (Mirip referensi) */
    .prompt-card-wrapper {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .prompt-card { 
        background-color: #2b2d31; 
        padding: 15px; 
        border-radius: 8px; 
        border: 1px solid #3f4147; 
        cursor: pointer; 
        transition: all 0.2s ease; 
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .prompt-card:hover { 
        background-color: #35373c; 
        border-color: #1c1c84; 
    }
    .card-title { font-weight: 600; font-size: 0.95rem; margin-bottom: 4px; color: #ffffff; }
    .card-subtitle { font-size: 0.8rem; color: #a0a0a0; line-height: 1.3; }
    
    /* Kolom Header */
    .col-header {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 15px;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Chat Bubbles */
    .stChatMessage { background-color: transparent; }
    .stChatMessage[data-testid="chat-message-user"] { 
        background-color: #2b2d31; 
        border-radius: 15px; 
        padding: 15px 20px; 
        max-width: 85%; 
        margin-left: auto; 
        border: 1px solid #3f4147; 
    }
    .stChatMessage[data-testid="chat-message-assistant"] { padding: 15px 0px; }
    
    /* Input Styling */
    .stChatInputContainer { 
        border: 1px solid #3f4147 !important; 
        border-radius: 12px !important; 
        background-color: #2b2d31 !important; 
        padding: 5px 15px !important; 
    }
    
    /* Layout Helpers */
    .center-text { text-align: center; }
    .footer-text { text-align: center; font-size: 0.75rem; color: #8e8e8e; margin-top: 15px; }
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
