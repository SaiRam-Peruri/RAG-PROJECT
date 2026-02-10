"""
Centralized configuration for the RAG Proposal System.
All tunable settings in one place.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
FEDERAL_CONTRACTING_DIR = Path(os.getenv(
    "RAG_FED_DIR",
    str(PROJECT_ROOT / "Federal_Contracting")
))
CHROMA_DB_PATH = Path(os.getenv(
    "RAG_CHROMA_PATH",
    str(PROJECT_ROOT / "chroma_db")
))

# ── ChromaDB Collections ───────────────────────────────
COLL_AUTH = "authoritative"
COLL_DRAFT = "drafting"

# ── Embedding Model ────────────────────────────────────
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-large")

# ── LLM Models ─────────────────────────────────────────
# Generation model (drafting, answering)
LLM_MODEL = os.getenv("RAG_LLM_MODEL", "gpt-4.1-mini")
# High-quality model (analysis, refinement)
LLM_MODEL_HQ = os.getenv("RAG_LLM_MODEL_HQ", "gpt-4.1")

# ── Retrieval Settings ─────────────────────────────────
TOP_K = int(os.getenv("RAG_TOP_K", "12"))
MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT", "14000"))
CHUNK_MAX_CHARS = 3500
CHUNK_OVERLAP = 300

# ── Stage Priority (for re-ranking) ───────────────────
STAGE_PRIORITY = {
    "amendment_or_qa": 0,
    "solicitation": 1,
    "context": 2,
    "rfi": 3,
    "other": 4,
}

# ── File Handling ──────────────────────────────────────
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}

# ── Validation ─────────────────────────────────────────
def require_api_key() -> str:
    """Return the OpenAI API key or exit with a helpful message."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit(
            "OPENAI_API_KEY not set.\n"
            "  Linux/macOS: export OPENAI_API_KEY='sk-...'\n"
            "  Windows:     $env:OPENAI_API_KEY='sk-...'"
        )
    return key
