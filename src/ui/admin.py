import streamlit as st
from src.database import DatabaseManager

def render_admin_dashboard(db: DatabaseManager):
    st.markdown("<h1>👑 Dasbor Analitik Admin</h1>", unsafe_allow_html=True)
    
    if st.button("⬅️ Kembali ke Chat Utama", type="primary"):
        st.session_state.view = "chat"
        st.rerun()
        
    st.markdown("---")
    
    sessions = db.get_all_sessions_admin()
    
    # Menghitung metrik (KPIs)
    total_sessions = len(sessions)
    unique_users = len(set(s["user_id"] for s in sessions))
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
        
    # Mengelompokkan berdasarkan pengguna agar rapi (Gestalt: Proximity)
    grouped_sessions = {}
    for s in sessions:
        uid = s["user_id"]
        if uid not in grouped_sessions:
            grouped_sessions[uid] = []
        grouped_sessions[uid].append(s)
        
    for uid, user_sessions in grouped_sessions.items():
        with st.expander(f"👤 User ID: {uid} | 💬 {len(user_sessions)} Topik Obrolan"):
            for s in user_sessions:
                st.markdown(f"**Topik:** {s['title']} *(Tgl: {s['created_at'][:10]})*")
                if st.button("Lihat Transkrip Pesan", key=f"admin_btn_{s['id']}"):
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
