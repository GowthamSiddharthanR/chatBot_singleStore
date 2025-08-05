import singlestoredb
from config import Config

def create_pdf_chunks_table():
    conn = singlestoredb.connect(
        host=Config.SINGLESTORE_HOST,
        user=Config.SINGLESTORE_USER,
        password=Config.SINGLESTORE_PASSWORD,
        database=Config.SINGLESTORE_DB,
        port=Config.SINGLESTORE_PORT
    )
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pdf_chunks (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        text TEXT,
        embedding VECTOR(384)
    );
    """)
    cursor.execute("""
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
    print("✅ Tables ready.")
