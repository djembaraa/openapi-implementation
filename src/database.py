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

    def create_session(self, user_id: str, title: str) -> str:
        res = self.client.table("chat_sessions").insert({
            "user_id": user_id,
            "title": title
        }).execute()
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
