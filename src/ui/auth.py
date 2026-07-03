import streamlit as st
from supabase import Client

def render_login(supabase: Client):
    """
    Me-render halaman login dan registrasi.
    Memungkinkan pengguna untuk masuk menggunakan Email/Password atau Google OAuth.
    
    Args:
        supabase (Client): Klien Supabase yang sudah diinisialisasi untuk autentikasi.
    """
    # Spacer atas
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Kolom tengah untuk form
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Teks rata tengah (Center Aligned)
        st.markdown("<h1 style='text-align: center; font-size: 3rem; margin-bottom: 0px;'>Rayn.AI ✨</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #b4b4b4; margin-bottom: 25px;'>Masuk ke akun Anda</p>", unsafe_allow_html=True)
        
        # Kotak Login (Card)
        with st.container(border=True):
            # Menggunakan st.form agar pengguna bisa menekan tombol 'Enter' di keyboard untuk submit
            with st.form("login_form", clear_on_submit=False):
                # Input email biasa
                email = st.text_input("Email", placeholder="contoh@email.com")
                # Input password dengan tipe 'password' agar diketik menjadi titik-titik rahasia (***)
                password = st.text_input("Password", type="password", placeholder="Minimal 6 karakter")
                
                st.write("") # Sedikit jarak
                
                # Mendeklarasikan 2 tombol submit dalam 1 form
                login_btn = st.form_submit_button("Log in", use_container_width=True, type="primary")
                signup_btn = st.form_submit_button("Sign up (Buat Akun)", use_container_width=True, type="secondary")
                
                # Jika tombol Log in ditekan (atau pengguna menekan tombol Enter)
                if login_btn:
                    try:
                        # Panggil API Supabase Auth untuk masuk menggunakan email dan sandi
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        
                        # Jika berhasil, simpan status login dan data profil pengguna ke memori Streamlit
                        st.session_state.logged_in = True
                        st.session_state.user_id = res.user.id
                        st.session_state.user_email = res.user.email
                        
                        # Refresh halaman untuk menerapkan perubahan status login
                        st.rerun()
                    except Exception:
                        st.error("Login gagal! Pastikan email dan password benar.")
                        
                # Jika tombol Sign up ditekan
                if signup_btn:
                    try:
                        # Panggil API Supabase Auth untuk mendaftarkan akun baru
                        supabase.auth.sign_up({"email": email, "password": password})
                        # Jika konfigurasi Supabase membutuhkan konfirmasi email, user harus cek inbox mereka
                        st.success("Registrasi berhasil! Silakan cek email atau langsung masuk.")
                    except Exception as e:
                        # Jika email sudah terdaftar atau password terlalu pendek
                        st.error(f"Sign up gagal: {e}")

            # Pemisah kustom yang presisi (Margin sangat rapat)
            st.markdown("""
                <div style='display: flex; align-items: center; margin: 10px 0;'>
                    <hr style='flex-grow: 1; border: none; border-top: 1px solid #3f4147;'>
                    <span style='padding: 0 15px; color: #8e8e8e; font-size: 0.85rem;'>ATAU</span>
                    <hr style='flex-grow: 1; border: none; border-top: 1px solid #3f4147;'>
                </div>
            """, unsafe_allow_html=True)
            
            # Tombol Google OAuth Button (SSO)
            try:
                # Meminta URL redirect OAuth dari Supabase (Provider: Google)
                oauth_res = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {"skip_browser_redirect": True} # Kita akan menangani redirect URL secara manual via tag <a>
                })
                
                # Tombol Google dengan display block agar full-width sempurna
                st.markdown(f"""
                <a href="{oauth_res.url}" target="_self" style="text-decoration: none; display: block; width: 100%;">
                    <div style="
                        width: 100%;
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
                
                # SPACER PENUTUP: Mencegah bug Streamlit di mana elemen markdown terakhir bocor keluar dari border
                st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Google Login error: {e}")

def handle_oauth_redirect(supabase: Client):
    """
    Menangani redirect URL setelah pengguna berhasil login menggunakan Google OAuth.
    Mengambil kode autentikasi dari parameter URL dan menukarnya dengan sesi pengguna aktif.
    
    Args:
        supabase (Client): Klien Supabase untuk menukar kode autentikasi.
    """
    # Cek jika ada query parameter 'code' di URL bar browser
    if "code" in st.query_params:
        # Ambil nilainya
        code = st.query_params["code"]
        try:
            # Tukarkan 'code' rahasia tersebut ke Supabase untuk mendapatkan Token Sesi valid
            res = supabase.auth.exchange_code_for_session({"auth_code": code})
            
            # Daftarkan status login pengguna ke memori Streamlit
            st.session_state.logged_in = True
            st.session_state.user_id = res.user.id
            st.session_state.user_email = res.user.email
            
            # Bersihkan query parameter panjang di URL bar agar rapi (aesthetic)
            st.query_params.clear()
            
            # Refresh halaman ke layar Chat Utama
            st.rerun()
        except Exception as e:
            # Token mungkin kedaluwarsa atau sudah dipakai
            st.error(f"Gagal memproses kode autentikasi: {e}")
