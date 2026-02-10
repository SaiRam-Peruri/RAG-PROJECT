"""
FastAPI application — production-ready API for the RAG Proposal System.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .. import __version__
from ..config import settings
from ..logging_config import setup_logging
from ..core.chroma_client import get_chroma_manager
from ..core.utils import format_citation
from ..models.schemas import (
    AnswerRequest, AnswerResponse,
    ComplianceRequest, ComplianceResponse,
    GenerateSectionRequest, GenerateSectionResponse,
    HealthResponse,
    IngestRequest, IngestResponse,
    OpportunitiesResponse,
    QueryRequest, QueryResponse,
)
from .auth import verify_api_key
from .rate_limit import rate_limiter

# ── App setup ──────────────────────────────────────────

setup_logging(settings.log_level, settings.log_file)

app = FastAPI(
    title="RAG Federal Proposal System",
    description="AI-powered federal proposal generation using Retrieval-Augmented Generation",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Rate limiting middleware ───────────────────────────

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health and docs
    if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)
    rate_limiter.check(request)
    return await call_next(request)


# ── Health ─────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """System health check — no auth required."""
    collections = []
    try:
        manager = get_chroma_manager()
        collections = manager.list_collections()
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        api_key_set=bool(settings.openai_api_key),
        chroma_path=str(settings.chroma_db_path),
        collections=collections,
        version=__version__,
    )


# ── Opportunities ──────────────────────────────────────

@app.get("/opportunities", response_model=OpportunitiesResponse, tags=["Data"])
async def list_opportunities(_: str = Depends(verify_api_key)):
    """List all available opportunities in the database."""
    from ..services.retrieval import get_available_opportunities
    opps = get_available_opportunities()
    return OpportunitiesResponse(opportunities=opps, count=len(opps))


# ── Query / Search ─────────────────────────────────────

@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query_documents(req: QueryRequest, _: str = Depends(verify_api_key)):
    """Semantic search across document collections."""
    from ..services.retrieval import query
    docs, metas = query(
        question=req.question,
        mode=req.mode,
        opportunities=req.opportunities,
        top_k=req.top_k,
    )
    return QueryResponse(
        documents=docs,
        citations=[format_citation(m) for m in metas],
        count=len(docs),
    )


# ── Answer ─────────────────────────────────────────────

@app.post("/answer", response_model=AnswerResponse, tags=["RAG"])
async def answer_question(req: AnswerRequest, _: str = Depends(verify_api_key)):
    """Answer a question using RAG (retrieve + generate)."""
    from ..services.generation import answer_question
    result = answer_question(
        question=req.question,
        mode=req.mode,
        opportunities=req.opportunities,
    )
    return AnswerResponse(
        answer=result["answer"],
        citations=result["citations"],
        sources_used=result["docs"],
    )


# ── Generate Section ───────────────────────────────────

@app.post("/generate", response_model=GenerateSectionResponse, tags=["Generation"])
async def generate_section(req: GenerateSectionRequest, _: str = Depends(verify_api_key)):
    """Generate a proposal section for a specific opportunity."""
    from ..services.generation import generate_section
    result = generate_section(
        opportunity=req.opportunity,
        section_type=req.section_type,
    )
    return GenerateSectionResponse(
        content=result["content"],
        citations=result["citations"],
        section_type=req.section_type,
        opportunity=req.opportunity,
    )


# ── Compliance Matrix ──────────────────────────────────

@app.post("/compliance", response_model=ComplianceResponse, tags=["Generation"])
async def generate_compliance(req: ComplianceRequest, _: str = Depends(verify_api_key)):
    """Generate a compliance matrix for an opportunity."""
    from ..services.compliance import generate_compliance_matrix
    result = generate_compliance_matrix(opportunity=req.opportunity)
    return ComplianceResponse(**result)


# ── Ingest ─────────────────────────────────────────────

@app.post("/ingest", response_model=IngestResponse, tags=["System"])
async def ingest_documents(req: IngestRequest, _: str = Depends(verify_api_key)):
    """Ingest documents from Federal_Contracting into ChromaDB."""
    from ..services.ingestion import ingest
    root = Path(req.root_dir) if req.root_dir else None
    stats = ingest(root_dir=root, clean=req.clean, show_progress=False)
    return IngestResponse(**stats)
