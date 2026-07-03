# Djembar Arafat (21SA1156)

import streamlit as st
import os
import time
import json
import numpy as np
import PyPDF2
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client, ClientOptions

# UI Setup & Styling
st.set_page_config(page_title="Djembar AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #212121; color: #ececec; }
    .block-container { padding-top: 3rem; max-width: 800px; }
    header {visibility: hidden;}
    .main-title { text-align: center; font-size: 3rem; font-weight: 600; margin-bottom: 3rem; color: #ffffff; }
    .prompt-card { background-color: #2f2f2f; padding: 15px; border-radius: 12px; border: 1px solid #424242; cursor: pointer; height: 100%; transition: background-color 0.2s; }
    .prompt-card:hover { background-color: #424242; }
    .card-title { font-weight: 600; font-size: 0.9rem; margin-bottom: 5px; color: #ececec; }
    .card-subtitle { font-size: 0.8rem; color: #b4b4b4; }
    .stChatMessage { background-color: transparent; }
    .stChatMessage[data-testid="chat-message-user"] { background-color: #2f2f2f; border-radius: 15px; padding: 15px 20px; max-width: 80%; margin-left: auto; }
    .stChatMessage[data-testid="chat-message-assistant"] { padding: 15px 0px; }
    .stChatInputContainer { border: 1px solid #424242 !important; border-radius: 20px !important; background-color: #2f2f2f !important; padding: 5px 15px !important; }
    .footer-text { text-align: center; font-size: 0.75rem; color: #b4b4b4; margin-top: 10px; }
    
    /* Login Form Styles */
    .login-container { max-width: 400px; margin: auto; padding-top: 50px; }
    .google-btn { display: flex; align-items: center; justify-content: center; width: 100%; background-color: #ffffff; color: #757575; border: 1px solid #ddd; padding: 10px; border-radius: 5px; font-weight: 500; cursor: pointer; margin-top: 15px; transition: 0.3s; text-decoration: none; }
    .google-btn:hover { background-color: #f1f1f1; }
    .google-btn img { width: 18px; margin-right: 10px; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_openai_client():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        st.error("OpenAI API key is missing or invalid. Please add your valid OPENAI_API_KEY in the .env file.")
        st.stop()
    return OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

@st.cache_resource
def get_supabase_client() -> Client:
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("Supabase URL atau Key belum disetup di .env")
        st.stop()
    # Gunakan PKCE Flow agar token masuk via query param (?code=...) bukan hash fragment (#access_token=...)
    return create_client(url, key, options=ClientOptions(flow_type="pkce"))

client = get_openai_client()
supabase = get_supabase_client()

# --- State Management Initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    
# Cek apakah ada redirect code dari Google OAuth di URL
if "code" in st.query_params:
    code = st.query_params["code"]
    try:
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        st.session_state.logged_in = True
        st.session_state.user_id = res.user.id
        st.session_state.user_email = res.user.email
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Gagal memproses kode autentikasi: {e}")

# --- Utility Functions ---
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def extract_text_from_upload(uploaded_file) -> str:
    text = ""
    try:
        if uploaded_file.name.lower().endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        elif uploaded_file.name.lower().endswith(".txt"):
            text = uploaded_file.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
    return text

def generate_embeddings(chunks: List[str]) -> np.ndarray:
    try:
        response = client.embeddings.create(input=chunks, model="gemini-embedding-2")
        return np.array([item.embedding for item in response.data])
    except Exception as e:
        st.error(f"Gagal menghasilkan embeddings: {e}")
        return np.array([])

def get_relevant_context(query: str, chunks: List[str], embeddings: np.ndarray, top_k: int = 3) -> str:
    if len(chunks) == 0 or len(embeddings) == 0:
        return ""
    try:
        query_response = client.embeddings.create(input=query, model="gemini-embedding-2")
        query_embedding = np.array(query_response.data[0].embedding)
        
        dot_products = np.dot(embeddings, query_embedding)
        norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
        similarities = dot_products / norms
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        relevant_chunks = [chunks[i] for i in top_indices]
        return "\n\n".join(relevant_chunks)
    except Exception as e:
        return ""

# --- Login Screen ---
def login_screen():
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title' style='margin-bottom:1rem;'>Djembar AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#b4b4b4; margin-bottom:2rem;'>Masuk untuk melanjutkan</p>", unsafe_allow_html=True)
    
    email = st.text_input("Email Address")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    if col1.button("Log in", use_container_width=True, type="primary"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.logged_in = True
            st.session_state.user_id = res.user.id
            st.session_state.user_email = res.user.email
            st.rerun()
        except Exception as e:
            st.error("Login gagal! Pastikan email dan password benar.")
            
    if col2.button("Sign up", use_container_width=True):
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            st.success("Registrasi berhasil! Silakan cek email Anda untuk konfirmasi (jika diaktifkan), atau langsung login.")
        except Exception as e:
            st.error(f"Sign up gagal: {e}")

    st.markdown("<div style='text-align:center; margin: 20px 0; color:#b4b4b4;'>ATAU</div>", unsafe_allow_html=True)
    
    try:
        # Menggunakan PKCE flow agar return URL tidak menggunakan fragment '#'
        # Redirect kembali ke domain Streamlit saat ini
        # URL untuk lokal biasanya http://localhost:8501, untuk cloud sesuaikan.
        oauth_res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "skip_browser_redirect": True,
            }
        })
        google_url = oauth_res.url
        # Render Google Login button
        st.markdown(f"""
        <a href="{google_url}" target="_self" style="text-decoration:none;">
            <div class="google-btn">
                <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google">
                Continue with Google
            </div>
        </a>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Google Login error: {e}")
        
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

if not st.session_state.logged_in:
    login_screen()

# --- Main Application Initialization ---
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "document_text" not in st.session_state:
    st.session_state.document_text = ""
    st.session_state.chunks = []
    st.session_state.embeddings = np.array([])
if "preset_prompt" not in st.session_state:
    st.session_state.preset_prompt = None

# Sidebar: Chat Sessions & RAG
with st.sidebar:
    st.markdown("### 👤 Akun Anda")
    st.write(f"Logged in as: **{st.session_state.user_email}**")
    if st.button("Logout", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()
        
    st.divider()
    
    if st.button("➕ Sesi Obrolan Baru", type="primary", use_container_width=True):
        st.session_state.current_session_id = None
        st.rerun()
        
    st.markdown("### 💬 Riwayat Obrolan")
    
    # Fetch user's sessions from DB
    try:
        sessions_resp = supabase.table("chat_sessions").select("*").eq("user_id", st.session_state.user_id).order("created_at", desc=True).execute()
        for s in sessions_resp.data:
            if st.button(f"📝 {s['title']}", key=f"sess_{s['id']}", use_container_width=True):
                st.session_state.current_session_id = s['id']
                st.rerun()
    except Exception as e:
        st.error("Gagal memuat sesi obrolan. (Pastikan tabel chat_sessions ada dan RLS disetup benar)")
        
    st.divider()
    st.markdown("### 📄 Unggah Konteks (RAG)")
    st.caption("Unggah dokumen PDF/TXT agar AI bisa menjawab berdasarkan isi dokumen tersebut.")
    uploaded_file = st.file_uploader("", type=["pdf", "txt"])
    
    if uploaded_file:
        if st.button("Proses Dokumen", use_container_width=True):
            with st.spinner("Mengekstrak teks..."):
                text = extract_text_from_upload(uploaded_file)
                if text:
                    chunks = chunk_text(text)
                    embeddings = generate_embeddings(chunks)
                    if len(embeddings) > 0:
                        st.session_state.document_text = text
                        st.session_state.chunks = chunks
                        st.session_state.embeddings = embeddings
                        st.success(f"Berhasil memproses {len(chunks)} potong teks!")

SYSTEM_PROMPT = (
    "Anda adalah AI Assistant bernama 'Djembar AI' yang cerdas, sopan, dan membantu. "
    "Anda dilarang keras menjawab pertanyaan atau permintaan yang mengandung unsur SARA "
    "(Suku, Agama, Ras, dan Antargolongan), ujaran kebencian, atau melanggar etika. "
    "Jika pengguna mengunggah dokumen (RAG), bantu mereka meringkas atau menjawab pertanyaan "
    "berdasarkan dokumen tersebut."
)

# Fetch Messages for current session
current_messages = []
if st.session_state.current_session_id:
    try:
        msgs_resp = supabase.table("chat_messages").select("*").eq("session_id", st.session_state.current_session_id).order("created_at").execute()
        current_messages = [{"role": m["role"], "content": m["content"]} for m in msgs_resp.data]
    except Exception as e:
        st.error("Gagal memuat pesan.")

# Empty State (No Messages)
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
    card(col3, "💡", "Bantu Pemrograman", "Tanyakan seputar kode Python.", "Buatkan saya fungsi Python untuk menghitung deret Fibonacci beserta penjelasannya.")

# Display chat messages
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
# Determine what prompt to process
prompt_to_process = None
if st.session_state.preset_prompt:
    prompt_to_process = st.session_state.preset_prompt
    st.session_state.preset_prompt = None
elif prompt := st.chat_input("How can I help you?"):
    prompt_to_process = prompt

if prompt_to_process:
    # Display user msg
    with st.chat_message("user"):
        st.markdown(prompt_to_process)
        
    # Create session if it doesn't exist
    if not st.session_state.current_session_id:
        title = prompt_to_process[:30] + "..." if len(prompt_to_process) > 30 else prompt_to_process
        new_sess = supabase.table("chat_sessions").insert({
            "user_id": st.session_state.user_id,
            "title": title
        }).execute()
        st.session_state.current_session_id = new_sess.data[0]["id"]
        
    # Save user message to DB
    supabase.table("chat_messages").insert({
        "session_id": st.session_state.current_session_id,
        "role": "user",
        "content": prompt_to_process
    }).execute()
    current_messages.append({"role": "user", "content": prompt_to_process})
    
    # Prepare context
    context = get_relevant_context(prompt_to_process, st.session_state.chunks, st.session_state.embeddings)
    
    messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context:
        messages_to_send.append({
            "role": "system",
            "content": f"Gunakan informasi berikut dari dokumen untuk menjawab jika relevan:\n{context}"
        })
        
    # Add history
    messages_to_send.extend(current_messages[-5:])
    
    # Call API
    with st.chat_message("assistant"):
        with st.spinner("Berpikir..."):
            try:
                start_time = time.time()
                response = client.chat.completions.create(
                    model="gemini-2.5-flash",
                    messages=messages_to_send,
                    temperature=0.7
                )
                end_time = time.time()
                
                answer = response.choices[0].message.content
                tokens = response.usage.total_tokens
                r_time = round(end_time - start_time, 2)
                
                st.markdown(answer)
                st.caption(f"⏱️ Waktu respons: {r_time} dtk | 🪙 Token: {tokens}")
                
                # Save assistant message to DB
                supabase.table("chat_messages").insert({
                    "session_id": st.session_state.current_session_id,
                    "role": "assistant",
                    "content": answer
                }).execute()
                
            except Exception as e:
                st.error(f"[Error] API Call Failed: {e}")

st.markdown("<p class='footer-text'>Djembar AI can make mistakes. Check important info.</p>", unsafe_allow_html=True)
