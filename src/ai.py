import time
import numpy as np
import PyPDF2
from typing import List, Dict, Tuple, Optional
from openai import OpenAI
import streamlit as st

class AIAssistant:
    def __init__(self, client: OpenAI):
        self.client = client
        self.system_prompt = (
            "Anda adalah AI Assistant bernama 'Djembar AI' yang cerdas, sopan, dan membantu. "
            "Anda dilarang keras menjawab pertanyaan atau permintaan yang mengandung unsur SARA "
            "(Suku, Agama, Ras, dan Antargolongan), ujaran kebencian, atau melanggar etika. "
            "Jika pengguna mengunggah dokumen (RAG), bantu mereka meringkas atau menjawab pertanyaan "
            "berdasarkan dokumen tersebut."
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

    def generate_embeddings(self, chunks: List[str]) -> np.ndarray:
        try:
            response = self.client.embeddings.create(input=chunks, model="gemini-embedding-2")
            return np.array([item.embedding for item in response.data])
        except Exception as e:
            st.error(f"Gagal menghasilkan embeddings: {e}")
            return np.array([])

    def get_relevant_context(self, query: str, chunks: List[str], embeddings: np.ndarray, top_k: int = 3) -> str:
        if len(chunks) == 0 or len(embeddings) == 0:
            return ""
        try:
            query_response = self.client.embeddings.create(input=query, model="gemini-embedding-2")
            query_embedding = np.array(query_response.data[0].embedding)
            
            dot_products = np.dot(embeddings, query_embedding)
            norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
            similarities = dot_products / norms
            
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            return "\n\n".join([chunks[i] for i in top_indices])
        except Exception:
            return ""

    def get_response(self, prompt: str, context: str, history: List[Dict[str, str]]) -> Tuple[str, float, int]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append({
                "role": "system",
                "content": f"Gunakan informasi berikut dari dokumen untuk menjawab jika relevan:\n{context}"
            })
        messages.extend(history[-5:])
        
        start_time = time.time()
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
