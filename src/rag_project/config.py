"""
Centralized configuration for the RAG Proposal System.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    federal_contracting_dir: Optional[Path] = None
    chroma_db_path: Optional[Path] = None

    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-large"
    llm_model: str = "gpt-4.1-mini"
    llm_model_hq: str = "gpt-4.1"

    top_k: int = 12
    max_context_chars: int = 14000
    chunk_max_chars: int = 3500
    chunk_overlap: int = 300

    coll_auth: str = "authoritative"
    coll_draft: str = "drafting"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = ""
    rate_limit_rpm: int = 60
    cors_origins: str = "*"

    company_name: str = "Your Company"
    company_address: str = "123 Main St"
    company_city_state: str = "City, State ZIP"
    company_phone: str = "000-000-0000"
    company_email: str = "contact@company.com"
    company_website: str = "www.company.com"

    log_level: str = "INFO"
    log_file: Optional[str] = None

    sam_api_key: str = ""
    target_naics: List[str] = Field(default_factory=list)

    # Review agent thresholds (0-1 scale)
    review_threshold_policy: float = 0.7
    review_threshold_technical: float = 0.75
    review_threshold_narrative: float = 0.6
    review_threshold_risk: float = 0.8

    model_config = {"extra": "ignore"}

    def model_post_init(self, __context) -> None:
        if self.federal_contracting_dir is None:
            self.federal_contracting_dir = self.project_root / "Federal_Contracting"
        if self.chroma_db_path is None:
            self.chroma_db_path = self.project_root / "chroma_db"

    @field_validator("target_naics", mode="before")
    @classmethod
    def _split_naics(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    def require_api_key(self) -> str:
        if not self.openai_api_key:
            raise SystemExit("OPENAI_API_KEY not set. export OPENAI_API_KEY='sk-...' ")
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
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

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
        sam_api_key=os.getenv("SAM_API_KEY", ""),
        target_naics=os.getenv("TARGET_NAICS", ""),
        review_threshold_policy=float(os.getenv("REVIEW_THRESHOLD_POLICY", "0.7")),
        review_threshold_technical=float(os.getenv("REVIEW_THRESHOLD_TECHNICAL", "0.75")),
        review_threshold_narrative=float(os.getenv("REVIEW_THRESHOLD_NARRATIVE", "0.6")),
        review_threshold_risk=float(os.getenv("REVIEW_THRESHOLD_RISK", "0.8")),
    )


settings = load_settings()
