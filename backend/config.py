import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SQLite is used for zero-setup local execution
    # Databases are stored in the UPLOAD_FOLDER as .db files
    
    # Ollama Configuration
    OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:1.5b')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', True)
    
    # Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'txt', 'mp3', 'wav', 'png', 'jpg', 'jpeg', 'webp'}
