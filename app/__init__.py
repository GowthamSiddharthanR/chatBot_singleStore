from flask import Flask
from app.extension import socketio
from config import Config
import singlestoredb

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    socketio.init_app(app)

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

            # ✅ Create pdf_chunks table for text chunks
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS pdf_chunks (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    text TEXT,
                    embedding VECTOR(384)
                );
            """)

            # ✅ Create pdf_images table for extracted images
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS pdf_images (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    page_number INT,
                    file_path TEXT,
                    embedding VECTOR(512)
                );
            """)

            conn.commit()
            cursor.close()
            conn.close()
            print("✅ SingleStore connected & tables ready")

        except Exception as e:
            print("❌ SingleStore setup failed:", str(e))

    from app.routes.chat_routes import chat_bp
    from app.routes.pdf_routes import pdf_bp
    app.register_blueprint(chat_bp)
    app.register_blueprint(pdf_bp)

    return app
