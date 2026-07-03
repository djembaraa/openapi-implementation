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
from supabase import create_client, Client

# UI Setup & Styling
st.set_page_config(page_title="Djembar AI", page_icon="💻", layout="wide")

# Hacker/Sleek CSS Injection
st.markdown("""
<style>
    .stApp { background-color: #1a1c23; color: #e2e8f0; font-family: 'Consolas', 'Courier New', monospace; }
    .block-container { padding-top: 2rem; }
    h1, h2, h3 { color: #00ffcc !important; font-weight: 600; letter-spacing: 1px; }
    .stChatMessage { background-color: #23262d; border-radius: 10px; padding: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .stChatInputContainer { border: 1px solid #00ffcc !important; border-radius: 10px !important; background-color: #13151a !important; }
    .stButton>button { border: 1px solid #00ffcc; color: #00ffcc; background-color: transparent; transition: all 0.3s ease; }
    .stButton>button:hover { background-color: #00ffcc; color: #1a1c23; box-shadow: 0 0 10px #00ffcc; }
</style>
""", unsafe_allow_html=True)

# Initialize Configuration
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
    return create_client(url, key)

client = get_openai_client()

# Utility Functions
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
        response = client.embeddings.create(
            input=chunks,
            model="gemini-embedding-2"
        )
        embeddings_list = [item.embedding for item in response.data]
        return np.array(embeddings_list)
    except Exception as e:
        st.error(f"Gagal menghasilkan embeddings: {e}")
        return np.array([])

def get_relevant_context(query: str, chunks: List[str], embeddings: np.ndarray, top_k: int = 3) -> str:
    if len(chunks) == 0 or len(embeddings) == 0:
        return ""
    try:
        query_response = client.embeddings.create(
            input=query,
            model="gemini-embedding-2"
        )
        query_embedding = np.array(query_response.data[0].embedding)
        
        dot_products = np.dot(embeddings, query_embedding)
        norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
        similarities = dot_products / norms
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        relevant_chunks = [chunks[i] for i in top_indices]
        return "\n\n".join(relevant_chunks)
    except Exception as e:
        st.error(f"Gagal mencari konteks: {e}")
        return ""

# Login Authentication
def login_screen():
    st.title("💻 Djembar AI - Login")
    st.caption("Silakan login untuk mengakses AI Assistant")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        supabase = get_supabase_client()
        try:
            response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
            if response.data and len(response.data) > 0:
                st.session_state.logged_in = True
                st.session_state.user_id = response.data[0]["id"]
                st.session_state.username = response.data[0]["username"]
                st.success("Login Berhasil!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Username atau Password salah!")
        except Exception as e:
            st.error(f"Error Database: {e}")
            
    st.stop()

# State Management Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "document_text" not in st.session_state:
    st.session_state.document_text = ""
    st.session_state.chunks = []
    st.session_state.embeddings = np.array([])

supabase = get_supabase_client()

# Sidebar: Chat Sessions & RAG
with st.sidebar:
    st.header(f"👤 Hai, {st.session_state.username}")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
        
    st.divider()
    
    st.header("💬 Sesi Obrolan")
    if st.button("➕ Sesi Baru"):
        st.session_state.current_session_id = None
        st.rerun()
        
    # Fetch user's sessions
    try:
        sessions_resp = supabase.table("chat_sessions").select("*").eq("user_id", st.session_state.user_id).order("created_at", desc=True).execute()
        for s in sessions_resp.data:
            if st.button(f"📝 {s['title']}", key=f"sess_{s['id']}"):
                st.session_state.current_session_id = s['id']
                st.rerun()
    except Exception as e:
        st.error("Gagal memuat sesi obrolan.")
        
    st.divider()
    st.header("📄 Dokumen Konteks (RAG)")
    uploaded_file = st.file_uploader("Unggah PDF atau TXT", type=["pdf", "txt"])
    
    if uploaded_file:
        if st.button("Proses Dokumen"):
            with st.spinner("Mengekstrak dan membuat embeddings..."):
                text = extract_text_from_upload(uploaded_file)
                if text:
                    chunks = chunk_text(text)
                    embeddings = generate_embeddings(chunks)
                    if len(embeddings) > 0:
                        st.session_state.document_text = text
                        st.session_state.chunks = chunks
                        st.session_state.embeddings = embeddings
                        st.success(f"Berhasil memproses {len(chunks)} potong teks!")

# Main Application
st.title("💻 Djembar AI")
st.caption("Responsi Praktik Pemrograman Sistem Cerdas - Djembar Arafat (21SA1156)")

SYSTEM_PROMPT = (
    "Anda adalah AI Assistant yang cerdas, sopan, dan membantu. "
    "Anda dilarang keras menjawab pertanyaan atau permintaan yang mengandung unsur SARA "
    "(Suku, Agama, Ras, dan Antargolongan), ujaran kebencian, atau melanggar etika. "
    "Jika pengguna menanyakan hal tersebut, Anda wajib menolaknya dengan tegas dan "
    "menyertakan alasan penolakannya secara sopan."
)

tab1, tab2, tab3 = st.tabs(["💬 Chat AI", "📝 Ringkas Dokumen", "😊 Analisis Sentimen"])

# Fetch Messages for current session
current_messages = []
if st.session_state.current_session_id:
    try:
        msgs_resp = supabase.table("chat_messages").select("*").eq("session_id", st.session_state.current_session_id).order("created_at").execute()
        current_messages = [{"role": m["role"], "content": m["content"]} for m in msgs_resp.data]
    except Exception as e:
        st.error("Gagal memuat pesan.")

with tab1:
    st.header("Chat AI")
    # Display chat messages from history
    for msg in current_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Tanyakan sesuatu..."):
        # Display user msg
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Create session if it doesn't exist
        if not st.session_state.current_session_id:
            title = prompt[:30] + "..." if len(prompt) > 30 else prompt
            new_sess = supabase.table("chat_sessions").insert({
                "user_id": st.session_state.user_id,
                "title": title
            }).execute()
            st.session_state.current_session_id = new_sess.data[0]["id"]
            
        # Save user message to DB
        supabase.table("chat_messages").insert({
            "session_id": st.session_state.current_session_id,
            "role": "user",
            "content": prompt
        }).execute()
        current_messages.append({"role": "user", "content": prompt})
        
        # Prepare context
        context = get_relevant_context(prompt, st.session_state.chunks, st.session_state.embeddings)
        
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

with tab2:
    st.header("Ringkas Dokumen")
    if not st.session_state.document_text:
        st.info("Silakan unggah dokumen di menu samping kiri terlebih dahulu.")
    else:
        if st.button("Buat Ringkasan Eksekutif", type="primary"):
            with st.spinner("Membaca dan meringkas dokumen..."):
                messages = [
                    {"role": "system", "content": "Anda adalah asisten ahli yang bertugas merangkum dokumen. Buatlah ringkasan eksekutif yang padat, jelas, dan informatif."},
                    {"role": "user", "content": f"Tolong ringkas dokumen berikut ini:\n\n{st.session_state.document_text[:15000]}"}
                ]
                
                try:
                    start_time = time.time()
                    response = client.chat.completions.create(
                        model="gemini-2.5-flash",
                        messages=messages,
                        temperature=0.7
                    )
                    end_time = time.time()
                    
                    summary = response.choices[0].message.content
                    tokens = response.usage.total_tokens
                    r_time = round(end_time - start_time, 2)
                    
                    st.markdown("### Hasil Ringkasan")
                    st.markdown(summary)
                    st.caption(f"⏱️ Waktu respons: {r_time} dtk | 🪙 Token: {tokens}")
                except Exception as e:
                    st.error(f"[Error] Gagal membuat ringkasan: {e}")

with tab3:
    st.header("Analisis Sentimen")
    st.markdown("Ketik teks untuk mengetahui sentimen (Positif, Negatif, Netral).")
    
    sentiment_input = st.text_area("Masukkan teks di sini:", height=100)
    if st.button("Analisis Sentimen"):
        if sentiment_input.strip() == "":
            st.warning("Teks tidak boleh kosong.")
        else:
            with st.spinner("Menganalisis..."):
                messages = [
                    {"role": "system", "content": "Anda adalah penganalisis sentimen. Analisis teks yang diberikan dan balas dengan format:\nSentimen: [Positif/Negatif/Netral]\nAlasan: [Alasan singkat max 2 kalimat]"},
                    {"role": "user", "content": f"Teks:\n{sentiment_input}"}
                ]
                try:
                    start_time = time.time()
                    response = client.chat.completions.create(
                        model="gemini-2.5-flash",
                        messages=messages,
                        temperature=0.7
                    )
                    end_time = time.time()
                    
                    result = response.choices[0].message.content
                    tokens = response.usage.total_tokens
                    r_time = round(end_time - start_time, 2)
                    
                    st.success("Analisis Selesai!")
                    st.markdown(result)
                    st.caption(f"⏱️ Waktu respons: {r_time} dtk | 🪙 Token: {tokens}")
                except Exception as e:
                    st.error(f"[Error] Gagal menganalisis sentimen: {e}")
