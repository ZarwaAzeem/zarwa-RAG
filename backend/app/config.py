"""Central configuration. Every value can be overridden from the environment or backend/.env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

# --- Data acquisition -------------------------------------------------------
# The resume is the primary source. Anything dropped into EXTRA_DOCS_DIR
# (.pdf / .txt / .md) is indexed alongside it.
RESUME_PATH = Path(os.getenv("RESUME_PATH", PROJECT_DIR / "ZarwaAzeem-Resume.pdf"))
EXTRA_DOCS_DIR = Path(os.getenv("EXTRA_DOCS_DIR", BACKEND_DIR / "data"))
# Resumes replaced from the admin page are copied here first.
RESUME_BACKUP_DIR = Path(os.getenv("RESUME_BACKUP_DIR", BACKEND_DIR / "resume-backups"))
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}
MAX_CHUNK_WORDS = 180
CHUNK_OVERLAP_WORDS = 30

# --- Embeddings + vector DB -------------------------------------------------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", BACKEND_DIR / "storage"))
TOP_K = int(os.getenv("TOP_K", "5"))
# Cosine similarity below this means "the resume doesn't cover it".
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.22"))
# A message scoring below this on its own is retried with the previous question for context.
FOLLOW_UP_SCORE = float(os.getenv("FOLLOW_UP_SCORE", "0.3"))

# --- Freshness --------------------------------------------------------------
# How often the watcher checks the source documents for changes.
WATCH_INTERVAL_SECONDS = float(os.getenv("WATCH_INTERVAL_SECONDS", "3"))

# --- Answer generation ------------------------------------------------------
PERSON_NAME = os.getenv("PERSON_NAME", "Zarwa Azeem")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
LLM_ENABLED = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))

# --- Visitor sessions -------------------------------------------------------
# Each visitor's chat history is held in memory under their own session id.
SESSION_TTL_SECONDS = float(os.getenv("SESSION_TTL_SECONDS", str(2 * 60 * 60)))
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "5000"))
MAX_CONVERSATIONS = 50  # per session
MAX_HISTORY_TURNS = 16  # messages remembered per conversation

# --- HTTP -------------------------------------------------------------------
PORT = int(os.getenv("PORT", "8080"))
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
