import streamlit as st
from supabase import Client

def render_login(supabase: Client):
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
        except Exception:
            st.error("Login gagal! Pastikan email dan password benar.")
            
    if col2.button("Sign up", use_container_width=True):
        try:
            supabase.auth.sign_up({"email": email, "password": password})
            st.success("Registrasi berhasil! Silakan cek email Anda atau langsung login.")
        except Exception as e:
            st.error(f"Sign up gagal: {e}")

    st.markdown("<div style='text-align:center; margin: 20px 0; color:#b4b4b4;'>ATAU</div>", unsafe_allow_html=True)
    
    try:
        oauth_res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"skip_browser_redirect": True}
        })
        st.markdown(f"""
        <a href="{oauth_res.url}" target="_self" style="text-decoration:none;">
            <div class="google-btn">
                <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google">
                Continue with Google
            </div>
        </a>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Google Login error: {e}")
        
    st.markdown("</div>", unsafe_allow_html=True)

def handle_oauth_redirect(supabase: Client):
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
