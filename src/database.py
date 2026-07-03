from typing import List, Dict, Any
from supabase import Client

class DatabaseManager:
    """
    Kelas untuk mengelola interaksi dengan Supabase Database (PostgreSQL).
    Bertanggung jawab atas operasi CRUD (Create, Read, Update, Delete) terkait
    sesi obrolan, pesan, dan template prompt.
    """
    def __init__(self, client: Client):
        """
        Inisialisasi DatabaseManager.
        
        Args:
            client (Client): Objek klien Supabase yang sudah terautentikasi.
        """
        self.client = client

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Mengambil semua riwayat sesi obrolan (chat sessions) milik seorang pengguna.
        
        Args:
            user_id (str): UUID dari pengguna (diperoleh dari Supabase Auth).
            
        Returns:
            List[Dict[str, Any]]: Daftar sesi obrolan yang diurutkan dari yang terbaru.
        """
        try:
            res = self.client.table("chat_sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return res.data
        except Exception:
            return []

    def create_session(self, user_id: str, title: str, user_email: str = None) -> str:
        """
        Membuat sesi obrolan baru untuk pengguna.
        Mencoba menyimpan email pengguna jika tabel mendukungnya.
        
        Args:
            user_id (str): UUID pengguna.
            title (str): Judul obrolan.
            user_email (str, optional): Email pengguna untuk keperluan analitik admin.
            
        Returns:
            str: ID (UUID) dari sesi obrolan yang baru dibuat.
        """
        data = {
            "user_id": user_id,
            "title": title
        }
        try:
            if user_email:
                data_with_email = data.copy()
                data_with_email["user_email"] = user_email
                res = self.client.table("chat_sessions").insert(data_with_email).execute()
                return res.data[0]["id"]
        except Exception:
            # Jika kolom user_email belum dibuat oleh pengguna di Supabase, fallback ke standar
            pass
            
        res = self.client.table("chat_sessions").insert(data).execute()
        return res.data[0]["id"]

    def get_messages(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Mengambil semua pesan di dalam satu sesi obrolan.
        
        Args:
            session_id (int): ID dari sesi obrolan (foreign key).
            
        Returns:
            List[Dict[str, Any]]: Daftar pesan obrolan yang diurutkan secara kronologis.
        """
        try:
            res = self.client.table("chat_messages").select("*").eq("session_id", session_id).order("created_at").execute()
            return res.data
        except Exception:
            return []

    def add_message(self, session_id: int, role: str, content: str):
        """
        Menyimpan pesan baru ke dalam database.
        
        Args:
            session_id (int): ID sesi obrolan.
            role (str): Peran pengirim pesan ('user' atau 'assistant').
            content (str): Isi teks pesan.
        """
        self.client.table("chat_messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content
        }).execute()
        
    def get_all_sessions_admin(self) -> List[Dict[str, Any]]:
        """
        Admin only: Mengambil seluruh sesi obrolan dari semua pengguna.
        Membutuhkan kebijakan RLS (Row Level Security) yang mengizinkan Admin membaca semuanya.
        
        Returns:
            List[Dict[str, Any]]: Daftar seluruh sesi obrolan di sistem.
        """
        try:
            # We select user_email or auth.users info if joined, but joining cross schema in Supabase is tricky.
            # RLS policy must allow admin to read all.
            res = self.client.table("chat_sessions").select("*").order("created_at", desc=True).execute()
            return res.data
        except Exception as e:
            print(e)
            return []

    def get_prompt_templates(self) -> List[Dict[str, Any]]:
        """
        Mengambil daftar template prompt interaktif dari tabel 'prompt_templates'.
        
        Returns:
            List[Dict[str, Any]]: Daftar template yang tersedia (icon, title, prompt_text).
        """
        try:
            res = self.client.table("prompt_templates").select("*").order("id").execute()
            return res.data
        except Exception:
            return []
