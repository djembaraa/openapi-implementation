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

def load_chat_history(filepath="chat_history.json") -> List[Dict[str, str]]:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_chat_history(history: List[Dict[str, str]], filepath="chat_history.json"):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        st.error(f"Gagal menyimpan histori: {e}")

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

if "document_text" not in st.session_state:
    st.session_state.document_text = ""
    st.session_state.chunks = []
    st.session_state.embeddings = np.array([])

# UI Setup
st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")
st.title("🤖 AI Assistant Pro")
st.caption("Responsi Praktik Pemrograman Sistem Cerdas - Djembar Arafat (21SA1156)")

# System Prompt
SYSTEM_PROMPT = (
    "Anda adalah AI Assistant yang cerdas, sopan, dan membantu. "
    "Anda dilarang keras menjawab pertanyaan atau permintaan yang mengandung unsur SARA "
    "(Suku, Agama, Ras, dan Antargolongan), ujaran kebencian, atau melanggar etika. "
    "Jika pengguna menanyakan hal tersebut, Anda wajib menolaknya dengan tegas dan "
    "menyertakan alasan penolakannya secara sopan."
)

# Sidebar
with st.sidebar:
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
    
    st.divider()
    if st.button("🗑️ Bersihkan Histori Percakapan"):
        st.session_state.messages = []
        save_chat_history([])
        st.success("Histori dihapus.")
        st.rerun()

# Main Tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat AI", "📝 Ringkas Dokumen", "😊 Analisis Sentimen"])

with tab1:
    st.header("Chat AI")
    # Display chat messages from history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Tanyakan sesuatu..."):
        # Display user msg
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Add to state and save
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_history(st.session_state.messages)
        
        # Prepare context
        context = get_relevant_context(prompt, st.session_state.chunks, st.session_state.embeddings)
        
        messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages_to_send.append({
                "role": "system",
                "content": f"Gunakan informasi berikut dari dokumen untuk menjawab jika relevan:\n{context}"
            })
            
        # Add history
        messages_to_send.extend(st.session_state.messages[-5:])
        
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
                    
                    # Save assistant response
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    save_chat_history(st.session_state.messages)
                except Exception as e:
                    st.error(f"API Error: {e}")

with tab2:
    st.header("Ringkasan Dokumen")
    if not st.session_state.document_text:
        st.info("Silakan unggah dan proses dokumen di bilah samping (sidebar) terlebih dahulu.")
    else:
        if st.button("Buat Ringkasan Sekarang"):
            with st.spinner("Membuat ringkasan..."):
                try:
                    text_to_summarize = st.session_state.document_text[:12000]
                    messages = [
                        {"role": "system", "content": "Anda adalah asisten AI yang bertugas membuat ringkasan komprehensif dari teks yang diberikan. Buatlah ringkasan dalam bahasa Indonesia yang terstruktur dan mudah dipahami."},
                        {"role": "user", "content": f"Tolong ringkas dokumen berikut:\n\n{text_to_summarize}"}
                    ]
                    
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
                    
                    st.success("Selesai!")
                    st.write(summary)
                    st.caption(f"⏱️ Waktu respons: {r_time} dtk | 🪙 Token: {tokens}")
                    
                except Exception as e:
                    st.error(f"API Error: {e}")

with tab3:
    st.header("Analisis Sentimen")
    sentiment_input = st.text_area("Masukkan teks yang ingin dianalisis:")
    if st.button("Analisis"):
        if sentiment_input.strip():
            with st.spinner("Menganalisa..."):
                try:
                    messages = [
                        {"role": "system", "content": "Anda adalah penganalisis sentimen. Klasifikasikan teks pengguna menjadi 'Positif', 'Negatif', atau 'Netral'. Hanya berikan label tersebut beserta penjelasan singkat."},
                        {"role": "user", "content": sentiment_input}
                    ]
                    
                    start_time = time.time()
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        temperature=0.7
                    )
                    end_time = time.time()
                    
                    result = response.choices[0].message.content
                    tokens = response.usage.total_tokens
                    r_time = round(end_time - start_time, 2)
                    
                    st.write(result)
                    st.caption(f"⏱️ Waktu respons: {r_time} dtk | 🪙 Token: {tokens}")
                except Exception as e:
                    st.error(f"API Error: {e}")
        else:
            st.warning("Teks tidak boleh kosong.")
