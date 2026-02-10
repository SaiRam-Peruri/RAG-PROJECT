"""
Shared utilities — text processing, dedup, citation formatting.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


def norm(s: str) -> str:
    """Normalize text for cheap dedup."""
    return re.sub(r"\\s+", " ", s.lower()).strip()


def dedup_results(docs: List[str], metas: List[Dict]) -> Tuple[List[str], List[Dict]]:
    """Remove near-duplicate chunks based on first 900 chars."""
    seen: set = set()
    out_docs, out_metas = [], []
    for d, m in zip(docs, metas):
        key = norm(d[:900])
        if key not in seen:
            seen.add(key)
            out_docs.append(d)
            out_metas.append(m)
    return out_docs, out_metas


def format_citation(meta: Dict) -> str:
    """Format citation: filename + page/sheet."""
    fn = meta.get("filename", "unknown")
    sheet = meta.get("sheet")
    page = meta.get("page")
    if sheet:
        return f"{fn} (sheet: {sheet})"
    if page:
        return f"{fn} p.{page}"
    return fn


def build_context(
    docs: List[str],
    metas: List[Dict],
    max_chars: int = 14000,
) -> str:
    """Build a context block with inline citations per chunk."""
    parts: List[str] = []
    total = 0
    for i, (d, m) in enumerate(zip(docs, metas), start=1):
        cite = format_citation(m)
        block = f"[Source {i}: {cite}]\\n{d.strip()}\\n"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\\n".join(parts)


def detect_opportunity_from_query(
    query: str, known_opportunities: List[str]
) -> Optional[str]:
    """Auto-detect opportunity ID from query text."""
    # Explicit ID pattern (e.g. CORHQ-25-R-0450)
    match = re.search(r'[A-Z]+[-_]\\d{2}[-_][A-Z][-_]\\d{4}', query, re.IGNORECASE)
    if match:
        opp_id = match.group(0).upper()
        for opp in known_opportunities:
            if opp_id in opp.upper():
                return opp

    # Fuzzy match
    query_lower = query.lower()
    for opp in known_opportunities:
        opp_normalized = opp.lower().replace('_', ' ').replace('-', ' ')
        if opp_normalized in query_lower or opp.lower() in query_lower:
            return opp

    return None


def chunk_text(text: str, max_chars: int = 3500, overlap: int = 300) -> List[str]:
    """Split text into overlapping chunks."""
    text = re.sub(r"\\s+\\n", "\\n", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + max_chars)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def rerank_by_stage_priority(
    docs: List[str],
    metas: List[Dict],
    top_n: int = 8,
    priority_map: Optional[Dict[str, int]] = None,
) -> Tuple[List[str], List[Dict]]:
    """Re-rank results to prefer amendments over base solicitation."""
    if priority_map is None:
        priority_map = {
            "amendment_or_qa": 0,
            "solicitation": 1,
            "context": 2,
            "rfi": 3,
            "other": 4,
        }
    pairs = list(zip(docs, metas))
    pairs.sort(key=lambda x: priority_map.get(x[1].get("stage", "other"), 999))
    pairs = pairs[:top_n]
    return [p[0] for p in pairs], [p[1] for p in pairs]
