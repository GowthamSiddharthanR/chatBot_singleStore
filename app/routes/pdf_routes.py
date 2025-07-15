from flask import Blueprint, request, jsonify, current_app
from app.utils.pdf_ai import extract_text_from_pdf, get_embeddings
from config import Config
import singlestoredb

pdf_bp = Blueprint("pdf_bp", __name__)

@pdf_bp.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".pdf"):
        return jsonify({"error": "Invalid file type. Only PDFs allowed."}), 400

    try:
        pdf_text = extract_text_from_pdf(file)
        chunks = [pdf_text[i:i+500] for i in range(0, len(pdf_text), 500)]
        vectors = get_embeddings(chunks)

        # Debug: Check dimensions
        print(f"✅ Extracted {len(chunks)} chunks with vector size: {len(vectors[0])}")

        conn = singlestoredb.connect(
            host=Config.SINGLESTORE_HOST,
            user=Config.SINGLESTORE_USER,
            password=Config.SINGLESTORE_PASSWORD,
            database=Config.SINGLESTORE_DB,
            port=Config.SINGLESTORE_PORT,
        )
        cursor = conn.cursor()

        try:
            for chunk, vector in zip(chunks, vectors):
                vec_literal = "[" + ",".join(map(str, vector)) + "]"
                cursor.execute(
                    "INSERT INTO pdf_chunks (text, embedding) VALUES (%s, %s)",
                    (chunk, vec_literal)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("❌ DB insert failed:", e)
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            conn.close()

        return jsonify({"status": "uploaded", "chunks": len(chunks)})

    except Exception as e:
        current_app.logger.error(f"❌ Upload failed: {str(e)}")
        return jsonify({"error": "Upload failed", "details": str(e)}), 500
