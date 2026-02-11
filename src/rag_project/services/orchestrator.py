"""
Orchestrator: coordinates the full proposal generation workflow.
Replaces legacy ProposalPipeline with modern service-based approach.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from ..config import settings
from ..logging_config import get_logger
from .ingestion import ingest
from .compliance import generate_compliance_matrix
from .generation import generate_section

logger = get_logger("orchestrator")


# Stage-specific section defaults
STAGE_SECTION_DEFAULTS = {
    "rfi": ["executive_summary", "technical"],
    "rfp": ["executive_summary", "technical", "management", "past_performance"],
    "pricing": ["cost", "pricing"],
}


def detect_government_template(opp_path: Path) -> Optional[Path]:
    """
    Check if opportunity has a government-provided template.
    
    Args:
        opp_path: Path to opportunity folder
    
    Returns:
        Path to template file if found, None otherwise
    """
    gov_issued = opp_path / "01_Government_Issued"
    if not gov_issued.exists():
        return None
    
    # Check for templates in various locations
    search_dirs = [
        gov_issued / "Final_Solicitations",
        gov_issued / "Draft_Solicitations",
        gov_issued / "Templates",
    ]
    
    template_indicators = [
        "template",
        "response_matrix",
        "fill_in",
        "contractor_response",
    ]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        for file_path in search_dir.iterdir():
            if file_path.suffix.lower() not in ['.docx', '.doc', '.xlsx']:
                continue
            
            filename_lower = file_path.name.lower()
            if any(indicator in filename_lower for indicator in template_indicators):
                logger.info("📋 Detected government template: %s", file_path.name)
                return file_path
    
    return None


def fetch_live_tech_intel(query: str, context: str = "") -> Optional[str]:
    """
    Fetch live technical intelligence from external sources.
    
    Placeholder for future Kimi/GPT integration to get latest guidance,
    standards, or technical information.
    
    Args:
        query: What to search for (e.g., "latest zero-trust guidance")
        context: Additional context for the query
    
    Returns:
        Retrieved information or None if not available
    
    Examples:
        - "NIST zero-trust architecture latest updates"
        - "FedRAMP moderate baseline changes 2026"
        - "DoD cybersecurity requirements current version"
    """
    # TODO: Implement Kimi/GPT API calls
    # For now, return None to use existing RAG data
    logger.debug("Tech intel stub called for: %s", query)
    return None


def run_opportunity_pipeline(
    notice_id: str,
    opp_path: Path,
    stage: str = "rfp",
    sections: Optional[List[str]] = None,
    use_template: bool = True,
    enable_tech_intel: bool = False,
) -> Dict:
    """
    Execute the complete proposal generation pipeline.
    
    Args:
        notice_id: Opportunity/notice ID
        opp_path: Path to opportunity folder
        stage: 'rfi' or 'rfp' (or custom stage like 'pricing')
        sections: Custom section list (overrides stage defaults)
        use_template: If True, check for government templates
        enable_tech_intel: If True, fetch live technical intelligence
    
    Returns:
        Result dict with success status and details
    """
    logger.info("="*70)
    logger.info("Starting %s pipeline for %s", stage.upper(), notice_id)
    logger.info("Path: %s", opp_path)
    logger.info("="*70)
    
    result = {
        "success": False,
        "notice_id": notice_id,
        "stage": stage,
        "steps": {},
        "template_detected": False,
    }
    
    try:
        # Check for government template first
        template_path = None
        if use_template:
            template_path = detect_government_template(opp_path)
            if template_path:
                result["template_detected"] = True
                result["template_path"] = str(template_path)
                logger.info("📋 Template mode: Will use %s", template_path.name)
                # TODO: Route to template filling service instead of standard generation
        
        # Step 1: Ingest documents
        logger.info("[STEP 1/3] Ingesting documents...")
        try:
            gov_issued = opp_path / "01_Government_Issued"
            if gov_issued.exists():
                ingest_stats = ingest(root_dir=gov_issued, clean=False)
                result["steps"]["ingest"] = {
                    "success": True,
                    "files": ingest_stats.get("files", 0),
                    "chunks": ingest_stats.get("chunks", 0),
                }
                logger.info("✅ Ingested %d files, %d chunks", 
                           ingest_stats.get("files", 0), 
                           ingest_stats.get("chunks", 0))
            else:
                logger.warning("⚠️  No 01_Government_Issued folder found, skipping ingest")
                result["steps"]["ingest"] = {"success": True, "skipped": True}
        except Exception as e:
            logger.error("❌ Ingestion failed: %s", e)
            result["steps"]["ingest"] = {"success": False, "error": str(e)}
            raise
        
        # Step 2: Generate compliance matrix
        logger.info("[STEP 2/3] Generating compliance matrix...")
        try:
            matrix_result = generate_compliance_matrix(opportunity=notice_id)
            result["steps"]["compliance"] = {
                "success": True,
                "requirements": matrix_result.get("requirements", 0),
                "output_file": str(matrix_result.get("output_file", "")),
            }
            logger.info("✅ Compliance matrix: %d requirements", 
                       matrix_result.get("requirements", 0))
        except Exception as e:
            logger.error("❌ Compliance matrix failed: %s", e)
            result["steps"]["compliance"] = {"success": False, "error": str(e)}
            # Continue even if compliance matrix fails
        
        # Optional: Fetch live tech intel
        if enable_tech_intel:
            logger.info("[TECH INTEL] Fetching latest technical guidance...")
            # Example queries based on common federal requirements
            intel_queries = [
                "NIST cybersecurity framework latest updates",
                "FedRAMP security controls changes",
                "Zero trust architecture federal guidance",
            ]
            for query in intel_queries:
                intel_result = fetch_live_tech_intel(query, context=notice_id)
                if intel_result:
                    logger.info("  ✅ Retrieved: %s", query[:50])
                    # TODO: Inject into RAG context or section generation
        
        # Step 3: Generate proposal sections
        logger.info("[STEP 3/3] Generating proposal sections...")
        
        # Use custom sections or stage defaults
        if sections is None:
            sections = STAGE_SECTION_DEFAULTS.get(stage.lower(), ["executive_summary"])
            logger.info("Using stage defaults for %s: %s", stage, sections)
        
        generated_sections = []
        failed_sections = []
        
        for section_type in sections:
            try:
                logger.info("  Generating %s...", section_type)
                section_result = generate_section(
                    opportunity=notice_id,
                    section_type=section_type
                )
                generated_sections.append({
                    "type": section_type,
                    "success": True,
                    "citations": len(section_result.get("citations", [])),
                })
                logger.info("  ✅ %s complete (%d citations)", 
                           section_type, 
                           len(section_result.get("citations", [])))
            except Exception as e:
                # Continue on section failure - capture for reporting
                logger.error("  ❌ %s failed: %s", section_type, e)
                failed_sections.append({
                    "type": section_type, 
                    "error": str(e)
                })
                # Don't raise - allow partial success
        
        result["steps"]["sections"] = {
            "success": len(failed_sections) == 0,
            "total": len(sections),
            "generated": generated_sections,
            "failed": failed_sections,
        }
        
        # Overall success criteria:
        # - Ingestion worked
        # - At least 50% of sections generated successfully
        min_success_threshold = max(1, len(sections) // 2)
        result["success"] = (
            result["steps"]["ingest"]["success"] and
            len(generated_sections) >= min_success_threshold
        )
        
        if result["success"]:
            logger.info("="*70)
            logger.info("✅ Pipeline completed successfully for %s", notice_id)
            logger.info("   Generated %d/%d sections", 
                       len(generated_sections), 
                       len(sections))
            logger.info("="*70)
        else:
            logger.warning("="*70)
            logger.warning("⚠️  Pipeline completed with warnings for %s", notice_id)
            logger.warning("   Generated %d/%d sections", 
                          len(generated_sections), 
                          len(sections))
            logger.warning("="*70)
        
        return result
        
    except Exception as e:
        logger.exception("❌ Pipeline failed for %s: %s", notice_id, e)
        result["success"] = False
        result["error"] = str(e)
        return result


def check_if_cancelled(notice_id: str, opp_path: Path) -> bool:
    """
    Check if opportunity has been moved to HOLD or cancelled.
    
    Args:
        notice_id: Opportunity ID
        opp_path: Current opportunity path
    
    Returns:
        True if cancelled/on hold, False otherwise
    """
    parent_folder = opp_path.parent.name
    
    # Check if in HOLD folder
    if parent_folder == "HOLD":
        logger.warning("⚠️  Opportunity %s is in HOLD - skipping", notice_id)
        return True
    
    # Check if opportunity folder no longer exists (moved/deleted)
    if not opp_path.exists():
        logger.warning("⚠️  Opportunity path no longer exists: %s", opp_path)
        return True
    
    return False
