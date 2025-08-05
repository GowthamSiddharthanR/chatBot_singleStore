import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel
import numpy as np
import os
import google.generativeai as genai
from PIL import Image
import io

# 🔑 Load API keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# ✅ Load models
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
text_embedder = SentenceTransformer("all-MiniLM-L6-v2")

clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

# ✅ Extract TEXT from PDF
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

# ✅ Extract IMAGES from PDF (returns list of PIL Images)
def extract_images_from_pdf(pdf_file):
    images = []
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            images.append(image)
    return images

# ✅ Get TEXT embeddings
def get_text_embeddings(text_chunks):
    return text_embedder.encode(text_chunks).tolist()

# ✅ Get IMAGE embedding (single image)
def get_image_embedding(image):
    inputs = clip_processor(images=image, return_tensors="pt")
    image_embedding = clip_model.get_image_features(**inputs)
    return image_embedding[0].detach().numpy().tolist()

# ✅ Get QUERY embedding for image search
def get_query_embedding(query):
    inputs = clip_processor(text=query, return_tensors="pt")
    text_embedding = clip_model.get_text_features(**inputs)
    return text_embedding[0].detach().numpy().tolist()

# ✅ Ask Gemini for response
def ask_gemini(context, query):
    prompt = f"""
    You are a helpful assistant.
    Context:
    {context}

    User Question:
    {query}
    """
    response = gemini_model.generate_content(prompt)
    return response.text
