from typing import List, Dict, Any
from supabase import Client

class DatabaseManager:
    def __init__(self, client: Client):
        self.client = client

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.client.table("chat_sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return res.data
        except Exception:
            return []

    def create_session(self, user_id: str, title: str, user_email: str = None) -> str:
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
        try:
            res = self.client.table("chat_messages").select("*").eq("session_id", session_id).order("created_at").execute()
            return res.data
        except Exception:
            return []

    def add_message(self, session_id: int, role: str, content: str):
        self.client.table("chat_messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content
        }).execute()
        
    def get_all_sessions_admin(self) -> List[Dict[str, Any]]:
        """Admin only: fetch all sessions. Requires Admin RLS policy."""
        try:
            # We select user_email or auth.users info if joined, but joining cross schema in Supabase is tricky.
            # RLS policy must allow admin to read all.
            res = self.client.table("chat_sessions").select("*").order("created_at", desc=True).execute()
            return res.data
        except Exception as e:
            print(e)
            return []

    def get_prompt_templates(self) -> List[Dict[str, Any]]:
        try:
            res = self.client.table("prompt_templates").select("*").order("id").execute()
            return res.data
        except Exception:
            return []
