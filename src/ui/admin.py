import streamlit as st
from src.database import DatabaseManager

def render_admin_dashboard(db: DatabaseManager):
    st.markdown("<h1>👑 Admin Dashboard</h1>", unsafe_allow_html=True)
    
    if st.button("⬅️ Kembali ke Chat"):
        st.session_state.view = "chat"
        st.rerun()
        
    st.markdown("### Daftar Seluruh Obrolan Pengguna")
    st.caption("Karena Anda adalah admin, Anda memiliki akses RLS untuk melihat semua riwayat.")
    
    sessions = db.get_all_sessions_admin()
    
    if not sessions:
        st.info("Belum ada sesi obrolan dari siapapun.")
        return
        
    # Group sessions by user_id
    grouped_sessions = {}
    for s in sessions:
        uid = s["user_id"]
        if uid not in grouped_sessions:
            grouped_sessions[uid] = []
        grouped_sessions[uid].append(s)
        
    for uid, user_sessions in grouped_sessions.items():
        with st.expander(f"Pengguna: {uid} ({len(user_sessions)} obrolan)"):
            for s in user_sessions:
                st.markdown(f"**Sesi:** {s['title']} *(Tgl: {s['created_at'][:10]})*")
                # When admin clicks on a session, show messages
                if st.button(f"Lihat Pesan", key=f"admin_btn_{s['id']}"):
                    msgs = db.get_messages(s['id'])
                    if not msgs:
                        st.warning("Pesan kosong.")
                    for m in msgs:
                        with st.chat_message(m["role"]):
                            st.write(m["content"])
                st.divider()
