from flask import Blueprint, render_template
from app.extension import socketio
from flask_socketio import emit, join_room
from app.utils.pdf_ai import get_text_embeddings, ask_gemini, get_query_embedding
from config import Config
import singlestoredb

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route("/")
def index():
    return render_template("chat.html")

@socketio.on('join')
def handle_join(data):
    user_id = data.get('user_id')
    room = f"user_{user_id}"
    join_room(room)
    emit('joined', {'room': room, 'user_id': user_id}, room=room)

@socketio.on('send_message')
def handle_message(data):
    conn = cursor = None
    try:
        user_id = data.get('sender')
        user_query = data.get('message')

        if not user_query:
            emit("receive_message", {"message": "Empty", "sender": "bot"}, room=f"user_{user_id}")
            return

        # ➜ Get TEXT embedding
        embedding = get_text_embeddings([user_query])[0]
        vec_literal = "[" + ",".join(map(str, embedding)) + "]"

        conn = singlestoredb.connect(
            host=Config.SINGLESTORE_HOST,
            user=Config.SINGLESTORE_USER,
            password=Config.SINGLESTORE_PASSWORD,
            database=Config.SINGLESTORE_DB,
            port=Config.SINGLESTORE_PORT
        )
        cursor = conn.cursor()

        # ➜ TEXT similarity: take top 3 text chunks
        cursor.execute("""
            SELECT text, embedding <*> (%s :> VECTOR(384)) AS score
            FROM pdf_chunks
            ORDER BY score DESC
            LIMIT 3
        """, (vec_literal,))
        text_results = cursor.fetchall()

        context = "\n\n".join([row[0] for row in text_results]) if text_results else ""
        reply = ask_gemini(context, user_query)

        # ➜ IMAGE similarity: take top 1 image only
        query_vec = get_query_embedding(user_query)
        vec_literal_img = "[" + ",".join(map(str, query_vec)) + "]"

        cursor.execute("""
            SELECT file_path, embedding <*> (%s :> VECTOR(512)) AS score
            FROM pdf_images
            ORDER BY score DESC
            LIMIT 1
        """, (vec_literal_img,))
        top_image = cursor.fetchone()

        # ➜ Apply threshold to avoid irrelevant images
        images = []
        if top_image:
            file_path, score = top_image
            print(f"Top image score: {score}")
            if score > 0.3:  # ← adjust as needed
                images.append(file_path)

        # ➜ Send back text reply + one (relevant) image (or none)
        emit("receive_message", {
            "message": reply,
            "images": images,
            "sender": "bot"
        }, room=f"user_{user_id}")

    except Exception as e:
        emit("receive_message", {"message": f"Error: {e}", "sender": "bot"}, room=f"user_{user_id}")

    finally:
        if cursor: cursor.close()
        if conn: conn.close()
