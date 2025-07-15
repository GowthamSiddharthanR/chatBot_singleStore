import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ...
    SINGLESTORE_HOST = os.getenv('SINGLESTORE_HOST')
    SINGLESTORE_USER = os.getenv('SINGLESTORE_USER')
    SINGLESTORE_PASSWORD = os.getenv('SINGLESTORE_PASSWORD')
    SINGLESTORE_DB = os.getenv('SINGLESTORE_DB')
    SINGLESTORE_PORT = int(os.getenv('SINGLESTORE_PORT', 3306))

    # ✅ Match your embedding dimension
    VECTOR_DIM = 384
