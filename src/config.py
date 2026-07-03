import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client, ClientOptions

@st.cache_resource
def get_openai_client() -> OpenAI:
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
    # PKCE flow for OAuth
    return create_client(url, key, options=ClientOptions(flow_type="pkce"))

def get_admin_email() -> str:
    load_dotenv()
    # Default admin if not set in .env
    return os.getenv("ADMIN_EMAIL", "admin@djembar.ai")
