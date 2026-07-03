import streamlit as st
from src.database import DatabaseManager

def render_admin_dashboard(db: DatabaseManager):
    """
    Me-render halaman Dasbor Analitik Admin.
    Hanya bisa diakses jika email pengguna yang login cocok dengan ADMIN_EMAIL.
    Menampilkan metrik seperti pengguna aktif, sesi obrolan, dan total interaksi.
    
    Args:
        db (DatabaseManager): Instansi DatabaseManager untuk melakukan query analitik.
    """
    st.markdown("<h1>👑 Dasbor Analitik Admin</h1>", unsafe_allow_html=True)
    
    if st.button("⬅️ Kembali ke Chat Utama", type="primary"):
        st.session_state.view = "chat"
        st.rerun()
        
    st.markdown("---")
    
    # Memanggil database untuk mengambil seluruh sesi obrolan (chat_sessions) dari SEMUA pengguna
    sessions = db.get_all_sessions_admin()
    
    # --- MENGHITUNG METRIK (KPIs) ---
    # 1. Total Sesi Obrolan: Sama dengan jumlah baris yang didapatkan dari database
    total_sessions = len(sessions)
    
    # 2. Total Pengguna Aktif: Menggunakan set() untuk menghilangkan duplikat ID user
    unique_users = len(set(s["user_id"] for s in sessions))
    
    # 3. Total Interaksi (Pesan): Lakukan iterasi pada setiap sesi, ambil pesannya, dan jumlahkan
    total_messages = 0
    for s in sessions:
        msgs = db.get_messages(s["id"])
        total_messages += len(msgs)

    # Gestalt: Grouping via Columns (Metric Cards)
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{unique_users}</div><div class='kpi-label'>Pengguna Aktif</div></div>", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{total_sessions}</div><div class='kpi-label'>Sesi Obrolan</div></div>", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{total_messages}</div><div class='kpi-label'>Total Interaksi</div></div>", unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### Daftar Riwayat Pengguna")
    
    if not sessions:
        st.info("Belum ada aktivitas di sistem.")
        return
        
    # Mengelompokkan riwayat percakapan berdasarkan UUID Pengguna (Gestalt: Proximity)
    # Tujuannya agar admin tidak bingung melihat tabel yang acak
    grouped_sessions = {}
    for s in sessions:
        uid = s["user_id"]
        # Jika UUID ini belum ada di dictionary, buatkan wadah array (list) baru
        if uid not in grouped_sessions:
            grouped_sessions[uid] = []
        # Tambahkan data sesi ke dalam wadah milik UUID tersebut
        grouped_sessions[uid].append(s)
        
    # Lakukan perulangan untuk merender setiap pengguna ke layar
    for uid, user_sessions in grouped_sessions.items():
        # st.expander() membuat tampilan kotak yang bisa di-klik untuk membuka/menutup isi (accordion)
        with st.expander(f"👤 User ID: {uid} | 💬 {len(user_sessions)} Topik Obrolan"):
            # Lakukan perulangan untuk merender semua sesi milik pengguna tersebut
            for s in user_sessions:
                st.markdown(f"**Topik:** {s['title']} *(Tgl: {s['created_at'][:10]})*")
                
                # Tombol untuk melihat isi pesan secara detail (Transcript)
                if st.button("Lihat Transkrip Pesan", key=f"admin_btn_{s['id']}"):
                    # Ambil daftar pesannya dari database
                    msgs = db.get_messages(s['id'])
                    if not msgs:
                        st.warning("Percakapan kosong.")
                    else:
                        st.markdown("<div style='background-color:#1e1e1e; padding:15px; border-radius:8px; border:1px solid #3f4147;'>", unsafe_allow_html=True)
                        for m in msgs:
                            role_icon = "🧑‍💻" if m["role"] == "user" else "🤖"
                            st.markdown(f"**{role_icon} {m['role'].upper()}:** {m['content']}")
                        st.markdown("</div>", unsafe_allow_html=True)
                st.write("") # Spacer
