import streamlit as st
from supabase import Client

def render_login(supabase: Client):
    # Menggunakan proporsi [1, 2, 1] agar lebih lebar dan lega di desktop
    # Total lebar aplikasi 900px, jadi kolom tengah akan mendapat ~450px (Ukuran standar login card)
    _, col, _ = st.columns([1.2, 2, 1.2])
    
    with col:
        # Title & Subtitle di luar kotak form agar terlihat seperti Header
        st.markdown("<h1 style='text-align: center; font-size: 3.5rem; color: #ffffff; margin-bottom: 5px;'>Djembar AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #b4b4b4; margin-bottom: 30px; font-size: 1rem;'>Kecerdasan Buatan dalam Genggaman Anda</p>", unsafe_allow_html=True)
        
        # Form Container agar terlihat seperti Card yang rapi
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; margin-bottom: 25px;'>Masuk / Daftar</h3>", unsafe_allow_html=True)
            
            email = st.text_input("Email Address", placeholder="nama@email.com")
            password = st.text_input("Password", type="password", placeholder="Minimal 6 karakter")
            
            st.markdown("<br>", unsafe_allow_html=True) # Spacer
            
            # Tombol ditumpuk agar ukurannya memanjang penuh (full width)
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

            # Separator di DALAM kotak agar menyatu
            st.markdown("""
                <div style='display: flex; align-items: center; margin: 25px 0;'>
                    <hr style='flex-grow: 1; border: none; border-top: 1px solid #3f4147;'>
                    <span style='padding: 0 15px; color: #8e8e8e; font-size: 0.85rem;'>ATAU</span>
                    <hr style='flex-grow: 1; border: none; border-top: 1px solid #3f4147;'>
                </div>
            """, unsafe_allow_html=True)
            
            # Google OAuth Button di DALAM kotak
            try:
                oauth_res = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {"skip_browser_redirect": True}
                })
                
                st.markdown(f"""
                <a href="{oauth_res.url}" target="_self" style="text-decoration: none;">
                    <button style="
                        width: 100%; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        background-color: #ffffff; 
                        color: #3c4043; 
                        border: 1px solid #dadce0; 
                        padding: 10px; 
                        border-radius: 8px; 
                        cursor: pointer; 
                        font-size: 1rem;
                        font-weight: 500;
                        font-family: inherit;
                        transition: background-color 0.2s;
                    " onmouseover="this.style.backgroundColor='#f1f1f1'" onmouseout="this.style.backgroundColor='#ffffff'">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" style="width: 20px; margin-right: 12px;" alt="Google">
                        Lanjutkan dengan Google
                    </button>
                </a>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Google Login error: {e}")
