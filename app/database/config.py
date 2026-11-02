import os
from dotenv import load_dotenv

load_dotenv()

# database
db_url = os.getenv("DATABASE_URL")

# app
# front-end addresses allowed to call this API from the browser, comma separated
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
default_role = os.getenv("DEFAULT_ROLE", "user")
upload_dir = os.getenv("UPLOAD_DIR", "uploads")
max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "20"))

# auth
algorithm = os.getenv("ALOGORITHM", "HS256")
secret = os.getenv("JWT_SECRET_KEY")
expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRY", "60"))
otp_expire_minutes = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
otp_max_attempts = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))

# mail
smtp_host = os.getenv("SMTP_HOST", "localhost")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_user = os.getenv("SMTP_USER")
smtp_password = os.getenv("SMTP_PASSWORD")
smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
mail_from = os.getenv("MAIL_FROM", smtp_user)

# ollama
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
chat_model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
chat_num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# rag
chroma_dir = os.getenv("CHROMA_DIR", "chroma_db")
chroma_collection = os.getenv("CHROMA_COLLECTION", "product_knowledge")
chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))
retrieval_k = int(os.getenv("RAG_TOP_K", "5"))
history_limit = int(os.getenv("CHAT_HISTORY_LIMIT", "10"))
ocr_dpi = int(os.getenv("OCR_DPI", "300"))
# pypdf stops at 2 million drawing instructions per page; print-ready PDFs (text drawn as shapes) need more
pdf_parsing_limit = int(os.getenv("PDF_PARSING_LIMIT", "50000000"))
