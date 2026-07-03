import time
import numpy as np
import PyPDF2
import base64
import faiss
import io
import speech_recognition as sr
from gtts import gTTS
from typing import List, Dict, Tuple, Optional
from openai import OpenAI
import streamlit as st

class AIAssistant:
    def __init__(self, client: OpenAI):
        self.client = client
        self.system_prompt = (
            "Anda adalah AI Assistant bernama 'Rayn.AI' yang cerdas, sopan, dan membantu. "
            "Anda dilarang keras menjawab pertanyaan atau permintaan yang mengandung unsur SARA "
            "(Suku, Agama, Ras, dan Antargolongan), ujaran kebencian, atau melanggar etika. "
            "Jika pengguna mengunggah dokumen (RAG), bantu mereka meringkas atau menjawab pertanyaan "
            "berdasarkan dokumen tersebut. Jika diberikan gambar, analisis gambar tersebut dengan cermat."
        )

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
        return chunks

    @staticmethod
    def extract_text_from_upload(uploaded_file) -> str:
        text = ""
        try:
            if uploaded_file.name.lower().endswith(".pdf"):
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            elif uploaded_file.name.lower().endswith(".txt"):
                text = uploaded_file.getvalue().decode("utf-8")
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
        return text

    @staticmethod
    def encode_image(uploaded_file) -> str:
        try:
            bytes_data = uploaded_file.getvalue()
            base64_img = base64.b64encode(bytes_data).decode('utf-8')
            mime_type = uploaded_file.type
            return f"data:{mime_type};base64,{base64_img}"
        except Exception as e:
            st.error(f"Gagal memproses gambar: {e}")
            return None

    def generate_embeddings(self, chunks: List[str]) -> np.ndarray:
        try:
            response = self.client.embeddings.create(input=chunks, model="gemini-embedding-2")
            return np.array([item.embedding for item in response.data], dtype=np.float32)
        except Exception as e:
            st.error(f"Gagal menghasilkan embeddings: {e}")
            return np.array([])

    def build_faiss_index(self, embeddings: np.ndarray):
        if len(embeddings) == 0:
            return None
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        return index

    def get_relevant_context(self, query: str, chunks: List[str], index, top_k: int = 3) -> str:
        if len(chunks) == 0 or index is None:
            return ""
        try:
            query_response = self.client.embeddings.create(input=query, model="gemini-embedding-2")
            query_embedding = np.array([query_response.data[0].embedding], dtype=np.float32)
            
            distances, indices = index.search(query_embedding, top_k)
            # Ambil indeks yang valid
            return "\n\n".join([chunks[i] for i in indices[0] if i != -1])
        except Exception:
            return ""

    def transcribe_audio(self, audio_file) -> str:
        r = sr.Recognizer()
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="id-ID")
            return text
        except sr.UnknownValueError:
            st.warning("Suara tidak dapat dikenali.")
        except Exception as e:
            st.error(f"Gagal mentranskripsi audio: {e}")
        return ""

    def generate_speech(self, text: str) -> io.BytesIO:
        try:
            tts = gTTS(text=text, lang='id', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp
        except Exception as e:
            st.error(f"Gagal menghasilkan TTS: {e}")
            return None

    def get_response(self, prompt: str, context: str, history: List[Dict[str, str]], base64_image: str = None) -> Tuple[str, float, int]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append({
                "role": "system",
                "content": f"Gunakan informasi berikut dari dokumen untuk menjawab jika relevan:\n{context}"
            })
            
        # Pisahkan history masa lalu dari prompt saat ini (karena chat.py sudah keburu nambahin ke history)
        past_messages = history[:-1] if len(history) > 0 else []
        messages.extend(past_messages[-5:])
        
        user_content = [{"type": "text", "text": prompt}]
        if base64_image:
            user_content.append({"type": "image_url", "image_url": {"url": base64_image}})
            
        messages.append({"role": "user", "content": user_content})
        
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=messages,
                temperature=0.7
            )
            end_time = time.time()
            
            answer = response.choices[0].message.content
            tokens = response.usage.total_tokens
            r_time = round(end_time - start_time, 2)
            
            return answer, r_time, tokens
        except Exception as e:
            return f"Maaf, terjadi kesalahan teknis (Koneksi terputus / API Key tidak valid):\n{str(e)}", 0.0, 0
