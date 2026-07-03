# Djembar Arafat (21SA1156)

import os
import sys
import time
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
import PyPDF2

class ConfigManager:
    """Manages configuration and API keys."""
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("[Error] OpenAI API key is missing or invalid.")
            print("Please add your valid OPENAI_API_KEY in the .env file.")
            sys.exit(1)
        self.client = OpenAI(api_key=self.api_key)

class DocumentProcessor:
    """Handles loading and processing of TXT and PDF files."""
    @staticmethod
    def load_document(filepath: str) -> str:
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File '{filepath}' not found.")
            
            text = ""
            if filepath.lower().endswith(".pdf"):
                with open(filepath, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            elif filepath.lower().endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            else:
                raise ValueError("Unsupported file format. Please provide a PDF or TXT file.")
            
            if not text.strip():
                raise ValueError("The document appears to be empty.")
                
            return text
        except Exception as e:
            print(f"[Error] Failed to load document: {e}")
            return ""

class RAGSystem:
    """Retrieval-Augmented Generation using NumPy and OpenAI Embeddings."""
    def __init__(self, client: OpenAI):
        self.client = client
        self.document_text = ""
        self.chunks: List[str] = []
        self.embeddings: np.ndarray = np.array([])
        
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
        return chunks

    def process_document(self, text: str):
        print("\n[Info] Processing document and generating embeddings... Please wait.")
        self.document_text = text
        self.chunks = self.chunk_text(text)
        
        try:
            response = self.client.embeddings.create(
                input=self.chunks,
                model="text-embedding-3-small"
            )
            embeddings_list = [item.embedding for item in response.data]
            self.embeddings = np.array(embeddings_list)
            print("[Info] Document processed successfully.")
        except Exception as e:
            print(f"[Error] Failed to generate embeddings: {e}")
            self.chunks = []

    def get_relevant_context(self, query: str, top_k: int = 3) -> str:
        if len(self.chunks) == 0:
            return ""
            
        try:
            query_response = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_embedding = np.array(query_response.data[0].embedding)
            
            # Cosine similarity
            dot_products = np.dot(self.embeddings, query_embedding)
            norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
            similarities = dot_products / norms
            
            # Get top k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            relevant_chunks = [self.chunks[i] for i in top_indices]
            
            return "\n\n".join(relevant_chunks)
        except Exception as e:
            print(f"[Error] Context retrieval failed: {e}")
            return ""

class HistoryManager:
    """Manages saving chat history to JSON."""
    def __init__(self, filepath: str = "chat_history.json"):
        self.filepath = filepath
        self.history = self.load_history()

    def load_history(self) -> List[Dict[str, str]]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to load history: {e}")
                return []
        return []

    def add_interaction(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        self.save_history()

    def save_history(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"[Warning] Failed to save history: {e}")

    def display_history(self):
        if not self.history:
            print("\n[Info] No chat history available.")
            return
            
        print("\n--- Riwayat Percakapan ---")
        for entry in self.history:
            role = "Anda" if entry["role"] == "user" else "AI"
            print(f"[{role}]: {entry['content']}")
        print("--------------------------\n")

class AIAssistant:
    """Core AI operations handling chatting, summarizing, and sentiment analysis."""
    def __init__(self, client: OpenAI, rag_system: RAGSystem, history_manager: HistoryManager):
        self.client = client
        self.rag = rag_system
        self.history = history_manager
        
        # System prompt with strict SARA filter
        self.system_prompt = (
            "Anda adalah AI Assistant yang cerdas, sopan, dan membantu. "
            "Anda dilarang keras menjawab pertanyaan atau permintaan yang mengandung unsur SARA "
            "(Suku, Agama, Ras, dan Antargolongan), ujaran kebencian, atau melanggar etika. "
            "Jika pengguna menanyakan hal tersebut, Anda wajib menolaknya dengan tegas dan "
            "menyertakan alasan penolakannya secara sopan."
        )

    def _call_api(self, messages: List[Dict[str, str]]) -> Tuple[Optional[str], float, int]:
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7
            )
            end_time = time.time()
            
            content = response.choices[0].message.content
            total_tokens = response.usage.total_tokens
            response_time = round(end_time - start_time, 2)
            
            return content, response_time, total_tokens
        except Exception as e:
            print(f"\n[Error] API Call Failed: {e}")
            if "Connection" in str(e):
                print("[Info] Please check your internet connection.")
            return None, 0.0, 0

    def print_metrics(self, response_time: float, total_tokens: int):
        print(f"\n[Metrics] Waktu proses: {response_time} detik | Total token: {total_tokens}")

    def chat(self, user_input: str):
        self.history.add_interaction("user", user_input)
        
        # Get context from document
        context = self.rag.get_relevant_context(user_input)
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        if context:
            messages.append({
                "role": "system", 
                "content": f"Gunakan informasi berikut dari dokumen untuk menjawab jika relevan:\n{context}"
            })
            
        # Add recent history (last 5 messages) for conversational context
        recent_history = self.history.history[-5:]
        messages.extend(recent_history)
        
        print("\nMemproses jawaban...")
        content, r_time, tokens = self._call_api(messages)
        
        if content:
            print(f"\n[AI]: {content}")
            self.print_metrics(r_time, tokens)
            self.history.add_interaction("assistant", content)

    def summarize(self):
        if not self.rag.document_text:
            print("\n[Info] Harap load dokumen terlebih dahulu sebelum meringkas.")
            return
            
        print("\nMemproses ringkasan...")
        # Truncate text if too long for standard model context
        text_to_summarize = self.rag.document_text[:12000] 
        
        messages = [
            {"role": "system", "content": "Anda adalah asisten AI yang bertugas membuat ringkasan komprehensif dari teks yang diberikan. Buatlah ringkasan dalam bahasa Indonesia yang terstruktur dan mudah dipahami."},
            {"role": "user", "content": f"Tolong ringkas dokumen berikut:\n\n{text_to_summarize}"}
        ]
        
        content, r_time, tokens = self._call_api(messages)
        if content:
            print(f"\n[Ringkasan Dokumen]:\n{content}")
            self.print_metrics(r_time, tokens)

    def analyze_sentiment(self, text: str):
        print("\nMemproses analisis sentimen...")
        messages = [
            {"role": "system", "content": "Anda adalah penganalisis sentimen. Klasifikasikan teks pengguna menjadi 'Positif', 'Negatif', atau 'Netral'. Hanya berikan label tersebut beserta penjelasan singkat."},
            {"role": "user", "content": text}
        ]
        
        content, r_time, tokens = self._call_api(messages)
        if content:
            print(f"\n[Hasil Analisis Sentimen]:\n{content}")
            self.print_metrics(r_time, tokens)


def main():
    print("="*50)
    print("Inisialisasi Sistem AI Assistant...")
    
    config = ConfigManager()
    doc_processor = DocumentProcessor()
    rag_system = RAGSystem(config.client)
    history_manager = HistoryManager()
    ai_assistant = AIAssistant(config.client, rag_system, history_manager)
    
    print("Sistem berhasil diinisialisasi.")
    
    # Optional document loading at startup
    doc_path = input("Masukkan path dokumen PDF/TXT untuk konteks (kosongkan jika tidak ada): ").strip()
    if doc_path:
        text = doc_processor.load_document(doc_path)
        if text:
            rag_system.process_document(text)

    while True:
        print("\n" + "="*50)
        print("Menu AI Assistant CLI:")
        print("1. Chat AI")
        print("2. Ringkas Dokumen")
        print("3. Analisis Sentimen")
        print("4. Riwayat Percakapan")
        print("5. Keluar")
        print("="*50)
        
        pilihan = input("Pilih menu (1-5): ").strip()
        
        if pilihan == '1':
            user_input = input("\nMasukkan pertanyaan Anda: ").strip()
            if user_input:
                ai_assistant.chat(user_input)
        elif pilihan == '2':
            ai_assistant.summarize()
        elif pilihan == '3':
            user_input = input("\nMasukkan teks untuk dianalisis: ").strip()
            if user_input:
                ai_assistant.analyze_sentiment(user_input)
        elif pilihan == '4':
            history_manager.display_history()
        elif pilihan == '5':
            print("\nTerima kasih telah menggunakan AI Assistant. Sampai jumpa!")
            break
        else:
            print("\n[Warning] Pilihan tidak valid, silakan pilih 1-5.")

if __name__ == "__main__":
    main()
