import os
import re
from typing import Dict, List, Tuple, Optional

import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI


COLL_AUTH = "authoritative"
COLL_DRAFT = "drafting"

# Tune these
TOP_K = 12         # retrieve more for re-ranking (prefer amendments over base RFP)
MAX_CONTEXT_CHARS = 14000  # keep prompt size reasonable

# Stage priority for re-ranking (lower = higher priority)
STAGE_PRIORITY = {
    "amendment_or_qa": 0,
    "solicitation": 1,
    "context": 2,
    "rfi": 3,
    "other": 4
}


def detect_opportunity_from_query(query: str, client_chroma) -> Optional[str]:
    """
    Auto-detect opportunity ID from query text.
    
    Patterns:
    - CORHQ-25-R-0450 (explicit ID)
    - "DMS Support" → matches DMS_Support or DMS_Support_CORHQ-25-R-0450
    """
    # Pattern 1: Explicit opportunity ID (e.g., CORHQ-XX-X-XXXX)
    pattern = r'[A-Z]+[-_]\d{2}[-_][A-Z][-_]\d{4}'
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        opp_id = match.group(0).upper()
        # Verify this opportunity exists
        coll = client_chroma.get_collection("authoritative")
        result = coll.get()
        opportunities = set(m.get('opportunity', 'unknown') for m in result['metadatas'])
        
        # Find exact or partial match
        for opp in opportunities:
            if opp_id in opp.upper():
                return opp
        return None
    
    # Pattern 2: Fuzzy match against known opportunities
    coll = client_chroma.get_collection("authoritative")
    result = coll.get()
    opportunities = [m.get('opportunity', 'unknown') for m in result['metadatas']]
    opportunities = sorted(set(opp for opp in opportunities if opp != 'unknown'))
    
    query_lower = query.lower()
    for opp in opportunities:
        # Normalize for matching
        opp_normalized = opp.lower().replace('_', ' ').replace('-', ' ')
        if opp_normalized in query_lower or opp.lower() in query_lower:
            return opp
    
    return None


def norm(s: str) -> str:
    """Normalize text for cheap dedup."""
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def dedup_results(docs: List[str], metas: List[Dict]) -> Tuple[List[str], List[Dict]]:
    """Remove near-duplicate chunks (common with repeated Section M pages)."""
    seen = set()
    out_docs, out_metas = [], []
    for d, m in zip(docs, metas):
        key = norm(d[:900])  # first ~900 chars is usually enough to detect repeats
        if key in seen:
            continue
        seen.add(key)
        out_docs.append(d)
        out_metas.append(m)
    return out_docs, out_metas


def rerank_by_stage_priority(docs: List[str], metas: List[Dict], top_n: int = 8) -> Tuple[List[str], List[Dict]]:
    """Re-rank results to prefer amendments over base solicitation."""
    pairs = list(zip(docs, metas))
    # Sort by stage priority (amendments first)
    pairs.sort(key=lambda x: STAGE_PRIORITY.get(x[1].get("stage", "other"), 999))
    # Keep top N after re-ranking
    pairs = pairs[:top_n]
    return [p[0] for p in pairs], [p[1] for p in pairs]


def format_citation(meta: Dict) -> str:
    """Format citation in human-friendly way: filename + page."""
    fn = meta.get("filename", "unknown")
    page = meta.get("page")
    sheet = meta.get("sheet")
    
    if sheet:
        return f"{fn} (sheet: {sheet})"
    if page:
        return f"{fn} p.{page}"
    return fn

def maybe_add_matrix(coll, question: str):
    trigger = any(k in question.lower() for k in [
        "technical acceptability", "acceptability", "attachment 3", "matrix", "pass/fail"
    ])
    if not trigger:
        return [], []

    extra = coll.query(
        query_texts=["Attachment 3 Technical Acceptability Matrix constraints pass fail"],
        n_results=2,
        where={"filename": {"$eq": "DMS_Support_RFP_Technical_Acceptability_Matrix_2025-11-14.xlsx"}},
    )
    return extra["documents"][0], extra["metadatas"][0]


def build_context(docs: List[str], metas: List[Dict]) -> str:
    """Build a context block with inline citations per chunk."""
    parts = []
    total = 0
    for i, (d, m) in enumerate(zip(docs, metas), start=1):
        cite = format_citation(m)
        snippet = d.strip()
        block = f"[Source {i}: {cite}]\n{snippet}\n"
        if total + len(block) > MAX_CONTEXT_CHARS:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)


def get_collection(client_chroma, mode: str, embedder):
    name = COLL_AUTH if mode.startswith("a") else COLL_DRAFT
    return client_chroma.get_collection(name, embedding_function=embedder)


def query_chroma(coll, question: str, mode: str, doc_roles: List[str] = None, opportunities: List[str] = None):
    """
    Pull top chunks.
    In auth mode we exclude award docs & keep it gov-focused.
    
    Args:
        coll: ChromaDB collection
        question: User question
        mode: 'auth' or 'draft'
        doc_roles: Optional list of semantic roles to filter by
                   e.g., ['evaluation_criteria', 'technical_requirements']
        opportunities: Optional list of opportunity names to filter by
                      e.g., ['CORHQ-25-R-0450', 'DMS_Support']
                      If None, searches all opportunities
    """
    where = {}
    if mode.startswith("a"):
        # Base filter: exclude award stage
        conditions = [{"stage": {"$ne": "award"}}]
        
        # Add opportunity filtering if specified
        if opportunities:
            conditions.append({"opportunity": {"$in": opportunities}})
        
        # Add role-based filtering if specified
        if doc_roles:
            conditions.append({"doc_role": {"$in": doc_roles}})
        
        where = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    # Query expansion: focus on Section M for evaluation questions
    query_text = question
    if mode.startswith("a") and any(kw in question.lower() for kw in ["evaluation", "factor", "best value"]):
        query_text = question + " Section M Evaluation Factors Best Value 7.3.2-17"

    res = coll.query(
        query_texts=[query_text],
        n_results=TOP_K,
        where=where if where else None,
    )
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    
    # Re-rank to prefer amendments over base RFP, keep best 6 chunks
    if mode.startswith("a"):
        docs, metas = rerank_by_stage_priority(docs, metas, top_n=6)
    
    # Special handling: if question is about evaluation/acceptability, also retrieve the matrix
    if mode.startswith("a") and any(kw in question.lower() for kw in ["evaluation", "acceptability", "factor", "technical matrix"]):
        try:
            extra = coll.query(
                query_texts=["Technical Acceptability Matrix Attachment 3 constraints pass fail"],
                n_results=3,
                where={"filename": "DMS_Support_RFP_Technical_Acceptability_Matrix_2025-11-14.xlsx"}
            )
            extra_docs = extra["documents"][0]
            extra_metas = extra["metadatas"][0]
            # Merge with existing results, avoiding duplicates
            for edoc, emeta in zip(extra_docs, extra_metas):
                if edoc not in docs:
                    docs.append(edoc)
                    metas.append(emeta)
        except Exception as e:
            print(f"Note: Could not retrieve Technical Acceptability Matrix: {e}")
    
    return docs, metas


# ========== Section-Specific Query Functions ==========
# These functions enable intelligent retrieval for specific proposal sections


def query_for_evaluation_criteria(coll, question: str = None, opportunities: List[str] = None) -> Tuple[List[str], List[Dict]]:
    """
    Retrieve evaluation criteria (Section M, factors, ratings, best value).
    Use for: Understanding how the government will evaluate proposals.
    
    Args:
        opportunities: Optional list of opportunity names to filter.
                      If None, searches all opportunities.
    """
    if not question:
        question = "evaluation factors criteria ratings best value technical acceptability"
    return query_chroma(
        coll, 
        question, 
        mode="auth",
        doc_roles=["evaluation_criteria", "amendment_qa"],
        opportunities=opportunities
    )


def query_for_technical_approach(coll, question: str, include_internal: bool = False, opportunities: List[str] = None) -> Tuple[List[str], List[Dict]]:
    """
    Retrieve technical requirements AND optionally internal technical approaches.
    Use for: Drafting Technical Approach section.
    
    Args:
        include_internal: If True, also pulls from past awarded technical proposals
        opportunities: Optional list of opportunity names to filter
    """
    # Get government requirements
    gov_docs, gov_metas = query_chroma(
        coll,
        question,
        mode="auth",
        doc_roles=["technical_requirements", "evaluation_criteria"],
        opportunities=opportunities
    )
    
    if include_internal:
        # Get internal best practices (from draft collection)
        # Note: This requires switching collections - implement based on your workflow
        pass
    
    return gov_docs, gov_metas


def query_for_past_performance(coll, question: str = None, opportunities: List[str] = None) -> Tuple[List[str], List[Dict]]:
    """
    Retrieve past performance requirements AND internal past performance content.
    Use for: Drafting Past Performance section.
    
    Args:
        opportunities: Optional list of opportunity names to filter
    """
    if not question:
        question = "past performance confidence ratings relevant experience"
    
    # This retrieves both government evaluation criteria and internal past perf content
    return query_chroma(
        coll,
        question,
        mode="draft",  # Use draft to access internal content
        doc_roles=["past_performance", "evaluation_criteria"],
        opportunities=opportunities
    )


def query_for_management_plan(coll, question: str, opportunities: List[str] = None) -> Tuple[List[str], List[Dict]]:
    """
    Retrieve management requirements and organizational approach requirements.
    Use for: Drafting Management Plan, Org Chart, Staffing sections.
    
    Args:
        opportunities: Optional list of opportunity names to filter
    """
    return query_chroma(
        coll,
        question,
        mode="auth",
        doc_roles=["technical_requirements", "instructions", "evaluation_criteria"],
        opportunities=opportunities
    )


def query_for_instructions(coll, question: str = None, opportunities: List[str] = None) -> Tuple[List[str], List[Dict]]:
    """
    Retrieve Section L (proposal preparation instructions).
    Use for: Understanding format, page limits, submission requirements.
    
    Args:
        opportunities: Optional list of opportunity names to filter
    """
    if not question:
        question = "proposal preparation instructions format page limit submission volume"
    return query_chroma(
        coll,
        question,
        mode="auth",
        doc_roles=["instructions", "amendment_qa"],
        opportunities=opportunities
    )


def query_for_pricing(coll, question: str = None, opportunities: List[str] = None) -> Tuple[List[str], List[Dict]]:
    """
    Retrieve pricing instructions, CLINs, and cost evaluation criteria.
    Use for: Understanding pricing structure and cost evaluation.
    
    Args:
        opportunities: Optional list of opportunity names to filter
    """
    if not question:
        question = "pricing cost CLIN price evaluation basis of estimate"
    return query_chroma(
        coll,
        question,
        mode="auth",
        doc_roles=["pricing", "evaluation_criteria", "instructions"],
        opportunities=opportunities
    )


def answer_with_openai(question: str, mode: str, context: str, citations: List[str]) -> str:
    client = OpenAI()

    if mode.startswith("a"):
        system = (
            "You are a federal solicitation analyst. You MUST ONLY use the provided sources. "
            "DO NOT invent factor names, letter labels, or requirements. "
            "If a factor list is not explicitly present in the sources, say: "
            "'The factor list is not fully visible in the retrieved excerpts.' "
            "When listing evaluation factors, copy the factor names exactly as written in the sources. "
            "When the solicitation lists 'Factors A–E' or similar, present those as the primary evaluation factors. "
            "Present Pass/Fail items like Technical Acceptability and Financial Capability under a separate 'Pass/Fail screenings' heading. "
            "Do not state relationships between factors unless explicitly written in the sources. "
            "Do not claim a factor maps to another factor unless the source states the mapping explicitly. "
            "Do not state that one factor is 'related to' another unless the sources explicitly say so. "
            "Prefer amendments/Q&A language if it conflicts with the base solicitation."
        )
    else:
        system = (
            "You are a proposal writer. Use the provided sources to draft content. "
            "Clearly separate REQUIREMENTS (government) from PROPOSED RESPONSE (vendor). "
            "Use citations in parentheses like (Source 3) when referencing provided text."
        )

    user = (
        f"QUESTION:\n{question}\n\n"
        f"SOURCES:\n{context}\n\n"
        "INSTRUCTIONS:\n"
        "- Use only the SOURCES above.\n"
        "- Cite claims with (Source N).\n"
        "- If you infer something, label it as an inference.\n"
    )

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",  # good default; change to gpt-4.1 for higher quality
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0 if mode.startswith("a") else 0.5,  # Zero temp for auth = no guessing
    )
    return resp.choices[0].message.content


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set. In PowerShell: $env:OPENAI_API_KEY='...'\n")

    question = input("Ask: ").strip()
    mode = input("Mode (auth/draft): ").strip().lower()
    if mode not in ("auth", "draft"):
        raise SystemExit("Mode must be 'auth' or 'draft'.")

    # Chroma setup
    client_chroma = chromadb.PersistentClient(path="chroma_db")
    embedder = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-3-large",
    )
    coll = get_collection(client_chroma, mode, embedder)
    
    # Auto-detect opportunity from question
    detected_opp = detect_opportunity_from_query(question, client_chroma)
    
    if detected_opp:
        print(f"✓ Auto-detected opportunity: {detected_opp}")
        opportunities = [detected_opp]
    else:
        # Fallback: ask user
        opp = input("Filter by opportunity (press Enter for all): ").strip()
        opportunities = [opp] if opp else None

    # Retrieve
    docs, metas = query_chroma(coll, question, mode, opportunities=opportunities)
    docs, metas = dedup_results(docs, metas)

    # Build context with citations
    context = build_context(docs, metas)

    # Debug: Print the exact context sent to the model
    print("\n=== CONTEXT SENT TO MODEL ===")
    print(context[:12000])  # Show first 12k chars
    print("\n=== END CONTEXT ===\n")

    # Answer
    answer = answer_with_openai(
        question=question,
        mode=mode,
        context=context,
        citations=[format_citation(m) for m in metas],
    )

    print("\nANSWER:\n")
    print(answer)

    print("\nCITATION KEY (Source N → file/page):")
    # Show unique opportunities
    unique_opps = set(m.get('opportunity', 'unknown') for m in metas)
    print(f"Opportunities: {', '.join(sorted(unique_opps))}\n")
    
    for i, m in enumerate(metas, start=1):
        print(f"Source {i}: {format_citation(m)}")


if __name__ == "__main__":
    main()
