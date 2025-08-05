import os
import io
import fitz
from PIL import Image
from flask import Blueprint, request, jsonify, current_app
from app.utils.pdf_ai import extract_text_from_pdf, get_text_embeddings, get_image_embedding, np
from config import Config
import singlestoredb

pdf_bp = Blueprint('pdf_bp', __name__)

@pdf_bp.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files.get("file")
    if not file or not file.filename.endswith('.pdf'):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        # ✅ Extract text chunks
        pdf_text = extract_text_from_pdf(file)
        chunks = [pdf_text[i:i+500] for i in range(0, len(pdf_text), 500)]
        vectors = get_text_embeddings(chunks)
        print(f"✅ Extracted {len(chunks)} text chunks")

        # ✅ Extract images & save under /static
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        image_data = []

        for page in doc:
            images = page.get_images(full=True)
            for idx, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                image = Image.open(io.BytesIO(image_bytes))
                filename = f"page_{page.number}_img_{idx}.png"
                
                # ✅ SAVE TO STATIC FOLDER
                save_folder = os.path.join("static", "uploads", "images")
                os.makedirs(save_folder, exist_ok=True)
                save_path = os.path.join(save_folder, filename)
                image.save(save_path)

                # ✅ Store only the RELATIVE URL path for HTML
                relative_url = f"/static/uploads/images/{filename}"

                vec = get_image_embedding(image)
                image_data.append((page.number, relative_url, vec))

        print(f"✅ Extracted & embedded {len(image_data)} images")

        # ✅ Store to DB
        conn = singlestoredb.connect(
            host=Config.SINGLESTORE_HOST,
            user=Config.SINGLESTORE_USER,
            password=Config.SINGLESTORE_PASSWORD,
            database=Config.SINGLESTORE_DB,
            port=Config.SINGLESTORE_PORT
        )
        cursor = conn.cursor()

        for chunk, vector in zip(chunks, vectors):
            vec_literal = "[" + ",".join(map(str, vector)) + "]"
            cursor.execute("""
                INSERT INTO pdf_chunks (text, embedding) VALUES (%s, %s)
            """, (chunk, vec_literal))

        for page_number, relative_url, vector in image_data:
            vec_literal = "[" + ",".join(map(str, vector)) + "]"
            cursor.execute("""
                INSERT INTO pdf_images (page_number, file_path, embedding) VALUES (%s, %s, %s)
            """, (page_number, relative_url, vec_literal))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "uploaded"})

    except Exception as e:
        current_app.logger.error(f"❌ Upload failed: {str(e)}")
        return jsonify({"error": "Upload failed", "details": str(e)}), 500
