import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import google.generativeai as genai

# ✅ Load Gemini API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# ✅ Load Gemini model (use gemini-1.5-flash or gemini-1.5-pro)
model = genai.GenerativeModel("gemini-1.5-flash")

# ✅ Load embedding model
model_embedder = SentenceTransformer("all-MiniLM-L6-v2")


def extract_text_from_pdf(pdf_file):
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        print("❌ PDF extraction failed:", e)
        return ""


def get_embeddings(text_chunks):
    return model_embedder.encode(text_chunks).tolist()


def ask_gemini(context, query):
    prompt = f"""You are a helpful assistant.
Use the following context to answer the user's question.

Context:
{context}

User Question:
{query}
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response from Gemini: {str(e)}"
