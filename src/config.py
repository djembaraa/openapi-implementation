import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client, ClientOptions

@st.cache_resource
def get_openai_client() -> OpenAI:
    """
    Menginisialisasi dan mengembalikan klien OpenAI (atau Gemini API dengan wrapper OpenAI).
    Hasilnya di-cache oleh Streamlit (st.cache_resource) agar tidak dibuat berulang kali.
    
    Returns:
        OpenAI: Objek klien OpenAI yang siap digunakan untuk pemanggilan API.
    """
    # Memuat variabel lingkungan dari file .env (seperti API key)
    load_dotenv()
    
    # Mengambil kunci API OpenAI dari file .env
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Validasi: Pastikan kunci API tidak kosong dan bukan nilai bawaan
    if not api_key or api_key == "your_openai_api_key_here":
        # Jika salah, tampilkan pesan error merah di layar dan hentikan aplikasi
        st.error("OpenAI API key is missing or invalid. Please add your valid OPENAI_API_KEY in the .env file.")
        st.stop()
        
    # Mengembalikan instance client OpenAI. Di sini kita memanipulasi base_url
    # agar mengarah ke server Gemini (Gratis) alih-alih server asli OpenAI (Berbayar).
    return OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        max_retries=5,
        timeout=30.0
    )

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Menginisialisasi dan mengembalikan klien database Supabase.
    Menggunakan flow PKCE untuk kapabilitas autentikasi yang aman.
    Hasilnya di-cache oleh Streamlit (st.cache_resource).
    
    Returns:
        Client: Objek klien Supabase.
    """
    # Memuat variabel lingkungan
    load_dotenv()
    
    # Menarik URL dan Key dari Supabase
    url = os.getenv("SUPABASE_URL")
    # Memprioritaskan SERVICE_ROLE_KEY agar bebas dari masalah keamanan RLS database
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    # Validasi: Jika tidak ada URL atau Key, hentikan aplikasi agar tidak error panjang
    if not url or not key:
        st.error("Supabase URL atau Key belum disetup di .env")
        st.stop()
        
    # Membuat koneksi ke Supabase dengan mode PKCE (Proof Key for Code Exchange)
    # Ini adalah standar keamanan tinggi untuk autentikasi OAuth (seperti Google Login)
    return create_client(url, key, options=ClientOptions(flow_type="pkce"))

def get_admin_email() -> str:
    """
    Mengambil alamat email admin utama dari environment variables (.env).
    
    Returns:
        str: Email admin yang berhak mengakses Dasbor Admin.
    """
    # Memuat variabel lingkungan
    load_dotenv()
    
    # Mengambil email admin. Jika tidak disetel di .env, kita pakai default: admin@djembar.ai
    return os.getenv("ADMIN_EMAIL", "admin@djembar.ai")
