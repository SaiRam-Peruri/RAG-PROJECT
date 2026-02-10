"""
Centralized configuration — single source of truth.
All settings are env-var driven with sensible defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # ── Paths ──────────────────────────────────────
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    federal_contracting_dir: Optional[Path] = None
    chroma_db_path: Optional[Path] = None

    # ── OpenAI ─────────────────────────────────────
    openai_api_key: str = Field(default="")
    embedding_model: str = Field(default="text-embedding-3-large")
    llm_model: str = Field(default="gpt-4.1-mini")
    llm_model_hq: str = Field(default="gpt-4.1")

    # ── Retrieval ──────────────────────────────────
    top_k: int = Field(default=12, ge=1, le=100)
    max_context_chars: int = Field(default=14000, ge=1000)
    chunk_max_chars: int = Field(default=3500, ge=500)
    chunk_overlap: int = Field(default=300, ge=0)

    # ── Collections ────────────────────────────────
    coll_auth: str = "authoritative"
    coll_draft: str = "drafting"

    # ── API Server ─────────────────────────────────
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_key: str = Field(default="")  # API auth key
    rate_limit_rpm: int = Field(default=60, ge=1)  # requests per minute
    cors_origins: str = Field(default="*")

    # ── Company Info (parameterized) ───────────────
    company_name: str = Field(default="Your Company")
    company_address: str = Field(default="123 Main St")
    company_city_state: str = Field(default="City, State ZIP")
    company_phone: str = Field(default="000-000-0000")
    company_email: str = Field(default="contact@company.com")
    company_website: str = Field(default="www.company.com")

    # ── Logging ────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = None

    model_config = {"extra": "ignore"}

    def model_post_init(self, __context) -> None:
        if self.federal_contracting_dir is None:
            self.federal_contracting_dir = self.project_root / "Federal_Contracting"
        if self.chroma_db_path is None:
            self.chroma_db_path = self.project_root / "chroma_db"

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def _validate_key(cls, v: str) -> str:
        return v  # allow empty for healthcheck; require_api_key() enforces at runtime

    def require_api_key(self) -> str:
        if not self.openai_api_key:
            raise SystemExit(
                "OPENAI_API_KEY not set.\n"
                "  export OPENAI_API_KEY='sk-...'"
            )
        return self.openai_api_key

    @property
    def allowed_extensions(self) -> set:
        return {".pdf", ".docx", ".xlsx"}

    @property
    def stage_priority(self) -> dict:
        return {
            "amendment_or_qa": 0,
            "solicitation": 1,
            "context": 2,
            "rfi": 3,
            "other": 4,
        }


def load_settings() -> Settings:
    """Load settings from environment variables (with .env support)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv optional

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-large"),
        llm_model=os.getenv("RAG_LLM_MODEL", "gpt-4.1-mini"),
        llm_model_hq=os.getenv("RAG_LLM_MODEL_HQ", "gpt-4.1"),
        top_k=int(os.getenv("RAG_TOP_K", "12")),
        max_context_chars=int(os.getenv("RAG_MAX_CONTEXT", "14000")),
        api_host=os.getenv("RAG_API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("RAG_API_PORT", "8000")),
        api_key=os.getenv("RAG_API_KEY", ""),
        rate_limit_rpm=int(os.getenv("RAG_RATE_LIMIT_RPM", "60")),
        cors_origins=os.getenv("RAG_CORS_ORIGINS", "*"),
        company_name=os.getenv("COMPANY_NAME", "Your Company"),
        company_address=os.getenv("COMPANY_ADDRESS", "123 Main St"),
        company_city_state=os.getenv("COMPANY_CITY_STATE", "City, State ZIP"),
        company_phone=os.getenv("COMPANY_PHONE", "000-000-0000"),
        company_email=os.getenv("COMPANY_EMAIL", "contact@company.com"),
        company_website=os.getenv("COMPANY_WEBSITE", "www.company.com"),
        log_level=os.getenv("RAG_LOG_LEVEL", "INFO"),
        log_file=os.getenv("RAG_LOG_FILE"),
        federal_contracting_dir=Path(p) if (p := os.getenv("RAG_FED_DIR")) else None,
        chroma_db_path=Path(p) if (p := os.getenv("RAG_CHROMA_PATH")) else None,
    )


# Singleton
settings = load_settings()
