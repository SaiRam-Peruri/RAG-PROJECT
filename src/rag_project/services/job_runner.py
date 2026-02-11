"""Job runner that pulls queued opportunities and runs the legacy pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from ..config import settings
from ..logging_config import get_logger
from .job_manager import list_jobs, update_job_status

logger = get_logger("job_runner")

STAGE_TRANSITIONS = {
    "rfi": ("RFI_READY", "RFI_COMPLETE"),
    "rfp": ("RFP_READY", "RFP_COMPLETE"),
}


def run_pending_jobs(limit: int = 1, dry_run: bool = False) -> int:
    jobs = list_jobs(status="pending")
    if not jobs:
        logger.info("No pending jobs")
        return 0

    completed = 0
    for job in jobs[:limit]:
        notice_id = job.notice_id
        stage = job.stage
        opp_path = Path(job.path)

        logger.info("%s Processing job %s (%s) %s", "=" * 10, notice_id, stage, "=" * 10)
        if dry_run:
            logger.info("[DRY RUN] Would process %s at %s", notice_id, opp_path)
            continue

        update_job_status(notice_id, stage, "running")
        try:
            success = _run_pipeline(notice_id, stage, opp_path)
            if success:
                new_path = _move_opportunity_folder(opp_path, stage)
                if new_path:
                    logger.info("Moved folder: %s → %s", opp_path.parent.name, new_path.parent.name)
                update_job_status(notice_id, stage, "complete")
                completed += 1
            else:
                update_job_status(notice_id, stage, "error")
        except Exception as exc:
            logger.exception("Job %s crashed: %s", notice_id, exc)
            update_job_status(notice_id, stage, "error")

    logger.info("Completed %d job(s)", completed)
    return completed


def run_single_job(notice_id: str, stage: str) -> bool:
    jobs = list_jobs()
    job = next((j for j in jobs if j.notice_id == notice_id and j.stage == stage), None)
    if not job:
        logger.error("Job not found: %s (%s)", notice_id, stage)
        return False
    if job.status not in ("pending", "error"):
        logger.warning("Job %s status is %s, skipping", notice_id, job.status)
        return False

    opp_path = Path(job.path)
    update_job_status(notice_id, stage, "running")
    try:
        success = _run_pipeline(notice_id, stage, opp_path)
        if success:
            _move_opportunity_folder(opp_path, stage)
            update_job_status(notice_id, stage, "complete")
            return True
        update_job_status(notice_id, stage, "error")
        return False
    except Exception as exc:
        logger.exception("Job crashed: %s (%s) - %s", notice_id, stage, exc)
        update_job_status(notice_id, stage, "error")
        return False


def _run_pipeline(notice_id: str, stage: str, opp_path: Path) -> bool:
    try:
        import sys

        sys.path.insert(0, str(settings.project_root))
        from auto_proposal_service import ProposalPipeline  # type: ignore

        pipeline = ProposalPipeline(settings.project_root)
        job_type = "new_rfi" if stage == "rfi" else "new_rfp"
        job = {
            "type": job_type,
            "opportunity": notice_id,
            "folder_path": opp_path,
        }

        gov_issued = opp_path / "01_Government_Issued"
        if gov_issued.exists():
            for subdir in ("Final_Solicitations", "Draft_Solicitations"):
                sol_dir = gov_issued / subdir
                if not sol_dir.exists():
                    continue
                for file_path in sol_dir.iterdir():
                    if file_path.suffix.lower() in {".pdf", ".docx", ".doc"}:
                        job["file_path"] = file_path
                        break
                if "file_path" in job:
                    break

        logger.info("Starting legacy pipeline for %s (%s)", notice_id, stage)
        pipeline.process_job(job)
        logger.info("Legacy pipeline finished for %s", notice_id)
        return True
    except Exception as exc:
        logger.exception("Pipeline error for %s: %s", notice_id, exc)
        return False


def _move_opportunity_folder(current_path: Path, stage: str) -> Optional[Path]:
    if stage not in STAGE_TRANSITIONS:
        logger.warning("Unknown stage %s", stage)
        return None

    from_dir, to_dir = STAGE_TRANSITIONS[stage]
    if current_path.parent.name != from_dir:
        logger.warning(
            "Folder %s not in %s (found in %s)",
            current_path.name,
            from_dir,
            current_path.parent.name,
        )
        return None

    base = settings.federal_contracting_dir / "01_Active_Pursuits"
    dest_dir = base / to_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / current_path.name

    if dest_path.exists():
        logger.warning("Destination %s already exists", dest_path)
        return dest_path

    try:
        shutil.move(str(current_path), str(dest_path))
        return dest_path
    except Exception as exc:
        logger.error("Failed to move %s: %s", current_path, exc)
        return None
