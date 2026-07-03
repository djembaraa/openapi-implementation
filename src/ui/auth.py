import streamlit as st
from supabase import Client

def render_login(supabase: Client):
    # Spacer atas
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Kolom tengah untuk form
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Teks rata tengah (Center Aligned)
        st.markdown("<h1 style='text-align: center; font-size: 3rem; color: #ffffff; margin-bottom: 0px;'>Djembar AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #b4b4b4; margin-bottom: 25px;'>Masuk ke akun Anda</p>", unsafe_allow_html=True)
        
        # Kotak Login (Card)
        with st.container(border=True):
            email = st.text_input("Email", placeholder="contoh@email.com")
            password = st.text_input("Password", type="password", placeholder="Minimal 6 karakter")
            
            st.write("") # Sedikit jarak
            
            if st.button("Log in", use_container_width=True, type="primary"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.logged_in = True
                    st.session_state.user_id = res.user.id
                    st.session_state.user_email = res.user.email
                    st.rerun()
                except Exception:
                    st.error("Login gagal! Pastikan email dan password benar.")
                    
            if st.button("Sign up (Buat Akun)", use_container_width=True, type="secondary"):
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Registrasi berhasil! Silakan cek email atau langsung masuk.")
                except Exception as e:
                    st.error(f"Sign up gagal: {e}")

            # Pemisah kustom yang presisi (Margin sangat rapat, tidak ada whitespace berlebih)
            st.markdown("""
                <div style='display: flex; align-items: center; margin: 15px 0;'>
                    <hr style='flex-grow: 1; border: none; border-top: 1px solid #3f4147;'>
                    <span style='padding: 0 15px; color: #8e8e8e; font-size: 0.85rem;'>ATAU</span>
                    <hr style='flex-grow: 1; border: none; border-top: 1px solid #3f4147;'>
                </div>
            """, unsafe_allow_html=True)
            
            # Google OAuth Button
            try:
                oauth_res = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {"skip_browser_redirect": True}
                })
                
                # Tombol Google dengan hover efek CSS asli Streamlit disiasati via style
                st.markdown(f"""
                <a href="{oauth_res.url}" target="_self" style="text-decoration: none;">
                    <div style="
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        background-color: #ffffff; 
                        color: #3c4043; 
                        border: 1px solid #dadce0; 
                        padding: 10px; 
                        border-radius: 6px; 
                        font-weight: 500;
                        transition: 0.2s;
                    ">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" style="width: 18px; margin-right: 10px;">
                        Lanjutkan dengan Google
                    </div>
                </a>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Google Login error: {e}")

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
