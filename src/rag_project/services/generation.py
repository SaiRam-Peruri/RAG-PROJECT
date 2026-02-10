"""
Proposal generation service — generates and answers using RAG context.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..config import settings
from ..core.llm import get_llm_client
from ..core.utils import build_context, format_citation
from ..logging_config import get_logger
from .retrieval import query, query_evaluation_criteria, query_technical, query_past_performance

logger = get_logger("generation")

# ── Section prompts ────────────────────────────────────
SECTION_PROMPTS = {
    "technical": (
        "You are writing the Technical Approach section of a federal proposal. "
        "Address ALL requirements from the GOVERNMENT REQUIREMENTS section. "
        "Structure: (1) Understanding of Requirements, (2) Technical Solution, (3) Implementation Approach. "
        "Cite requirements with [Requirement N]. Be specific, avoid generic statements."
    ),
    "management": (
        "You are writing the Management Plan section of a federal proposal. "
        "Address organizational structure, key personnel roles, quality assurance, and risk management. "
        "Cite requirements with [Requirement N]."
    ),
    "past_performance": (
        "You are writing the Past Performance section of a federal proposal. "
        "Reference specific past contracts that demonstrate relevant experience. "
        "For each example: customer, contract value, dates, relevance, outcomes. "
        "Cite requirements with [Requirement N]."
    ),
    "executive_summary": (
        "You are writing the Executive Summary of a federal proposal. "
        "Synthesize: (1) Understanding of mission, (2) Unique solution advantages, (3) Why we win. "
        "Keep it concise (1-2 pages). Cite requirements with [Requirement N]."
    ),
    "staffing": (
        "You are writing the Staffing Plan section of a federal proposal. "
        "Address: (1) Key personnel qualifications, (2) Org chart, (3) Labor categories, (4) Recruitment strategy. "
        "Cite requirements with [Requirement N]."
    ),
    "quality_assurance": (
        "You are writing the Quality Assurance section of a federal proposal. "
        "Address: (1) QA/QC processes, (2) Quality metrics, (3) Testing procedures, (4) Continuous improvement. "
        "Cite requirements with [Requirement N]."
    ),
    "security": (
        "You are writing the Security and Compliance section of a federal proposal. "
        "Address: (1) Security controls, (2) Compliance frameworks (FedRAMP, FISMA, NIST), (3) Data protection. "
        "Cite requirements with [Requirement N]."
    ),
    "transition": (
        "You are writing the Transition Plan section of a federal proposal. "
        "Address: (1) Transition approach, (2) Knowledge transfer, (3) Risk mitigation, (4) Timeline. "
        "Cite requirements with [Requirement N]."
    ),
    "cost": (
        "You are writing the Cost Proposal section of a federal proposal. "
        "Address: (1) Cost breakdown, (2) Pricing strategy, (3) Cost justification, (4) Value proposition. "
        "Cite requirements with [Requirement N]."
    ),
}

AUTH_SYSTEM_PROMPT = (
    "You are a federal solicitation analyst. You MUST ONLY use the provided sources. "
    "DO NOT invent factor names, letter labels, or requirements. "
    "If a factor list is not explicitly present in the sources, say: "
    "'The factor list is not fully visible in the retrieved excerpts.' "
    "Copy factor names exactly as written in the sources. "
    "Prefer amendments/Q&A language if it conflicts with the base solicitation."
)

DRAFT_SYSTEM_PROMPT = (
    "You are a proposal writer. Use the provided sources to draft content. "
    "Clearly separate REQUIREMENTS (government) from PROPOSED RESPONSE (vendor). "
    "Use citations in parentheses like (Source 3) when referencing provided text."
)


def answer_question(
    question: str,
    mode: str = "auth",
    opportunities: Optional[List[str]] = None,
) -> Dict:
    """
    Answer a question using RAG retrieval + LLM generation.

    Returns:
        {"answer": str, "citations": [str], "docs": int}
    """
    docs, metas = query(question, mode=mode, opportunities=opportunities)
    context = build_context(docs, metas, settings.max_context_chars)
    citations = [format_citation(m) for m in metas]

    system = AUTH_SYSTEM_PROMPT if mode.startswith("a") else DRAFT_SYSTEM_PROMPT
    temperature = 0.0 if mode.startswith("a") else 0.5

    user_prompt = (
        f"QUESTION:\n{question}\n\n"
        f"SOURCES:\n{context}\n\n"
        "INSTRUCTIONS:\n"
        "- Use only the SOURCES above.\n"
        "- Cite claims with (Source N).\n"
        "- If you infer something, label it as an inference.\n"
    )

    llm = get_llm_client()
    answer = llm.generate(system, user_prompt, temperature=temperature)

    logger.info("Answered question (%d sources, mode=%s)", len(docs), mode)
    return {"answer": answer, "citations": citations, "docs": len(docs)}


def generate_section(
    opportunity: str,
    section_type: str,
    requirements_context: Optional[str] = None,
    best_practices_context: Optional[str] = None,
) -> Dict:
    """
    Generate a proposal section for a given opportunity.

    Returns:
        {"content": str, "citations": [str]}
    """
    from .retrieval import get_available_opportunities
    from ..core.validation import validate_section_type, sanitize_opportunity_name

    section_type = validate_section_type(section_type)
    opportunity = sanitize_opportunity_name(opportunity)

    # Retrieve requirements if not provided
    req_docs, req_metas = query(
        f"requirements specifications {section_type}",
        mode="auth",
        doc_roles=["technical_requirements", "evaluation_criteria", "instructions", "amendment_qa"],
        opportunities=[opportunity],
    )

    # Retrieve internal best practices
    try:
        past_docs, past_metas = query(
            f"{section_type} approach best practices",
            mode="draft",
            doc_roles=[section_type, "proposal"],
        )
    except Exception as e:
        logger.warning("Could not retrieve best practices: %s", e)
        past_docs, past_metas = [], []

    # Build context
    context_parts = ["=== GOVERNMENT REQUIREMENTS ===\n"]
    for i, (doc, meta) in enumerate(zip(req_docs, req_metas), 1):
        cite = format_citation(meta)
        context_parts.append(f"[Requirement {i}: {cite}]\n{doc.strip()}\n")

    if past_docs:
        context_parts.append("\n=== INTERNAL BEST PRACTICES (Past Wins) ===\n")
        for i, (doc, meta) in enumerate(zip(past_docs, past_metas), 1):
            cite = format_citation(meta)
            context_parts.append(f"[Best Practice {i}: {cite}]\n{doc.strip()}\n")

    context = "\n".join(context_parts)

    # Generate
    system = SECTION_PROMPTS.get(section_type, SECTION_PROMPTS["technical"])
    user_prompt = (
        f"OPPORTUNITY: {opportunity}\n"
        f"SECTION: {section_type.replace('_', ' ').title()}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "INSTRUCTIONS:\n"
        "- Address every requirement explicitly\n"
        "- Use [Requirement N] citations\n"
        "- Be specific and detailed (not generic)\n"
        "- Show understanding + solution + benefits\n"
        "- Draft 2-3 pages of content\n"
    )

    llm = get_llm_client()
    content = llm.generate(system, user_prompt, temperature=0.3)

    citations = [f"{m.get('filename')} p.{m.get('page')}" for m in req_metas]
    logger.info("Generated %s section for %s (%d chars)", section_type, opportunity, len(content))

    return {"content": content, "citations": citations}
