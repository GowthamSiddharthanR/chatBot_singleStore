from flask import Flask
from app.extension import socketio
from config import Config
import singlestoredb

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    socketio.init_app(app)

    # Create table if needed
    with app.app_context():
        try:
            conn = singlestoredb.connect(
                host=Config.SINGLESTORE_HOST,
                user=Config.SINGLESTORE_USER,
                password=Config.SINGLESTORE_PASSWORD,
                database=Config.SINGLESTORE_DB,
                port=Config.SINGLESTORE_PORT
            )
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS pdf_chunks (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    text TEXT,
                    embedding VECTOR({Config.VECTOR_DIM})
                );
            """)
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ SingleStore connected & table ready")
        except Exception as e:
            print("❌ SingleStore setup failed:", str(e))

    from app.routes.chat_routes import chat_bp
    from app.routes.pdf_routes import pdf_bp
    app.register_blueprint(chat_bp)
    app.register_blueprint(pdf_bp)

    return app
