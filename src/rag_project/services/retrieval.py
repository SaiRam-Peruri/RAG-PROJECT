"""
Retrieval service — semantic search across ChromaDB collections.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..config import settings
from ..core.chroma_client import get_chroma_manager
from ..core.utils import dedup_results, rerank_by_stage_priority, build_context, format_citation
from ..logging_config import get_logger

logger = get_logger("retrieval")


def query(
    question: str,
    mode: str = "auth",
    doc_roles: Optional[List[str]] = None,
    opportunities: Optional[List[str]] = None,
    top_k: Optional[int] = None,
    rerank: bool = True,
) -> Tuple[List[str], List[Dict]]:
    """
    Retrieve relevant chunks from ChromaDB.

    Args:
        question: Search query
        mode: 'auth' (authoritative/government) or 'draft' (vendor/internal)
        doc_roles: Filter by semantic roles
        opportunities: Filter by opportunity names
        top_k: Number of results to retrieve
        rerank: Whether to apply stage-based re-ranking

    Returns:
        Tuple of (documents, metadatas)
    """
    k = top_k or settings.top_k
    manager = get_chroma_manager()

    coll_name = settings.coll_auth if mode.startswith("a") else settings.coll_draft
    coll = manager.get_collection(coll_name)

    # Build filter
    where = _build_where(mode, doc_roles, opportunities)

    # Query expansion for evaluation questions
    query_text = question
    if mode.startswith("a") and any(kw in question.lower() for kw in ("evaluation", "factor", "best value")):
        query_text = question + " Section M Evaluation Factors Best Value"

    logger.debug("Querying %s: q='%s...', top_k=%d", coll_name, question[:50], k)

    result = coll.query(
        query_texts=[query_text],
        n_results=k,
        where=where if where else None,
    )

    docs = result["documents"][0]
    metas = result["metadatas"][0]

    if rerank and mode.startswith("a"):
        docs, metas = rerank_by_stage_priority(docs, metas, top_n=6)

    docs, metas = dedup_results(docs, metas)
    logger.debug("Retrieved %d unique chunks", len(docs))

    return docs, metas


def _build_where(
    mode: str,
    doc_roles: Optional[List[str]] = None,
    opportunities: Optional[List[str]] = None,
) -> Optional[Dict]:
    """Build ChromaDB where filter."""
    if not mode.startswith("a"):
        return None

    conditions = [{"stage": {"$ne": "award"}}]

    if opportunities:
        conditions.append({"opportunity": {"$in": opportunities}})
    if doc_roles:
        conditions.append({"doc_role": {"$in": doc_roles}})

    return {"$and": conditions} if len(conditions) > 1 else conditions[0]


# ── Section-specific query functions ───────────────────

def query_evaluation_criteria(
    question: Optional[str] = None,
    opportunities: Optional[List[str]] = None,
) -> Tuple[List[str], List[Dict]]:
    """Retrieve evaluation criteria (Section M)."""
    q = question or "evaluation factors criteria ratings best value technical acceptability"
    return query(q, mode="auth", doc_roles=["evaluation_criteria", "amendment_qa"], opportunities=opportunities)


def query_technical(
    question: str,
    opportunities: Optional[List[str]] = None,
) -> Tuple[List[str], List[Dict]]:
    """Retrieve technical requirements (SOW/PWS)."""
    return query(question, mode="auth", doc_roles=["technical_requirements", "evaluation_criteria"], opportunities=opportunities)


def query_past_performance(
    question: Optional[str] = None,
    opportunities: Optional[List[str]] = None,
) -> Tuple[List[str], List[Dict]]:
    """Retrieve past performance content."""
    q = question or "past performance confidence ratings relevant experience"
    return query(q, mode="draft", doc_roles=["past_performance", "evaluation_criteria"], opportunities=opportunities)


def query_instructions(
    question: Optional[str] = None,
    opportunities: Optional[List[str]] = None,
) -> Tuple[List[str], List[Dict]]:
    """Retrieve proposal preparation instructions (Section L)."""
    q = question or "proposal preparation instructions format page limit submission volume"
    return query(q, mode="auth", doc_roles=["instructions", "amendment_qa"], opportunities=opportunities)


def query_pricing(
    question: Optional[str] = None,
    opportunities: Optional[List[str]] = None,
) -> Tuple[List[str], List[Dict]]:
    """Retrieve pricing instructions and CLINs."""
    q = question or "pricing cost CLIN price evaluation basis of estimate"
    return query(q, mode="auth", doc_roles=["pricing", "evaluation_criteria", "instructions"], opportunities=opportunities)


def query_management(
    question: str,
    opportunities: Optional[List[str]] = None,
) -> Tuple[List[str], List[Dict]]:
    """Retrieve management plan requirements."""
    return query(question, mode="auth", doc_roles=["technical_requirements", "instructions", "evaluation_criteria"], opportunities=opportunities)


def get_available_opportunities() -> List[str]:
    """Get list of all opportunities in the database."""
    manager = get_chroma_manager()
    try:
        coll = manager.get_collection(settings.coll_auth)
        result = coll.get()
        opps = set(m.get("opportunity", "unknown") for m in result["metadatas"])
        opps.discard("unknown")
        return sorted(opps)
    except Exception as e:
        logger.warning("Could not list opportunities: %s", e)
        return []
