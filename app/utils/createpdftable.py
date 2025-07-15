import singlestoredb
from config import Config

def create_pdf_chunks_table():
    try:
        conn = singlestoredb.connect(
            host=Config.SINGLESTORE_HOST,
            user=Config.SINGLESTORE_USER,
            password=Config.SINGLESTORE_PASSWORD,
            database=Config.SINGLESTORE_DB,
            port=Config.SINGLESTORE_PORT,
        )

        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_chunks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                text TEXT NOT NULL,
                embedding VECTOR(1536) NOT NULL  -- Corrected syntax for SingleStore VECTOR type
            )
        """)
        conn.commit()
        print("✅ Table `pdf_chunks` created successfully.")

    except Exception as e:
        print("❌ Failed to create table:", str(e))

    finally:
        cursor.close()
        conn.close()
