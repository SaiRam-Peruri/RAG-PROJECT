"""
Pydantic models for API request/response validation.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ── Requests ───────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Search question")
    mode: str = Field(default="auth", pattern="^(auth|draft)$", description="Query mode: auth or draft")
    opportunities: Optional[List[str]] = Field(default=None, description="Filter by opportunities")
    top_k: Optional[int] = Field(default=None, ge=1, le=100, description="Number of results")


class AnswerRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field(default="auth", pattern="^(auth|draft)$")
    opportunities: Optional[List[str]] = None


class GenerateSectionRequest(BaseModel):
    opportunity: str = Field(..., min_length=1, max_length=200)
    section_type: str = Field(..., description="Section type: technical, management, etc.")


class ComplianceRequest(BaseModel):
    opportunity: str = Field(..., min_length=1, max_length=200)


class IngestRequest(BaseModel):
    root_dir: Optional[str] = Field(default=None, description="Override Federal_Contracting directory")
    clean: bool = Field(default=True, description="Delete existing collections first")


# ── Responses ──────────────────────────────────────────

class QueryResponse(BaseModel):
    documents: List[str]
    citations: List[str]
    count: int


class AnswerResponse(BaseModel):
    answer: str
    citations: List[str]
    sources_used: int


class GenerateSectionResponse(BaseModel):
    content: str
    citations: List[str]
    section_type: str
    opportunity: str


class ComplianceResponse(BaseModel):
    requirements: int
    mandatory: int
    desirable: int
    sow: int
    output_file: str


class IngestResponse(BaseModel):
    files: int
    chunks: int
    auth_chunks: int
    draft_chunks: int


class HealthResponse(BaseModel):
    status: str
    api_key_set: bool
    chroma_path: str
    collections: List[str]
    version: str


class OpportunitiesResponse(BaseModel):
    opportunities: List[str]
    count: int


class ErrorResponse(BaseModel):
    detail: str
