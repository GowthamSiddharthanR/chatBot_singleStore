from flask import Blueprint, render_template
from app.extension import socketio
from flask_socketio import emit, join_room
from app.utils.pdf_ai import get_embeddings, ask_gemini
from config import Config
import singlestoredb

chat_bp = Blueprint("chat_bp", __name__)

@chat_bp.route("/")
def index():
    return render_template("chat.html")

@socketio.on("join")
def handle_join(data):
    user_id = data.get("user_id")
    room = f"user_{user_id}"
    join_room(room)
    emit("joined", {"room": room, "user_id": user_id}, room=room)

@socketio.on("send_message")
def handle_message(data):
    conn = cursor = None
    try:
        user_id = data.get("sender")
        user_query = data.get("message")
        if not user_query:
            emit("receive_message", {"message": "Empty message", "sender": "bot"}, room=f"user_{user_id}")
            return

        embedding = get_embeddings([user_query])[0]
        vec_literal = "[" + ",".join(map(str, embedding)) + "]"

        conn = singlestoredb.connect(
            host=Config.SINGLESTORE_HOST,
            user=Config.SINGLESTORE_USER,
            password=Config.SINGLESTORE_PASSWORD,
            database=Config.SINGLESTORE_DB,
            port=Config.SINGLESTORE_PORT,
        )
        cursor = conn.cursor()

        sql = f"""
            SELECT text,
                   embedding <*> ('{vec_literal}' :> VECTOR({Config.VECTOR_DIM})) AS score
            FROM pdf_chunks
            ORDER BY score DESC
            LIMIT 3
        """

        cursor.execute(sql)
        results = cursor.fetchall()

        if results:
            context = "\n\n".join(f"Context {i+1}:\n{row[0]}" for i, row in enumerate(results))
            reply = ask_gemini(context, user_query)
        else:
            reply = ask_gemini("", user_query)

        emit("receive_message", {"message": reply, "sender": "bot"}, room=f"user_{user_id}")

    except Exception as e:
        emit("receive_message", {"message": f"Error: {e}", "sender": "bot"}, room=f"user_{user_id}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
