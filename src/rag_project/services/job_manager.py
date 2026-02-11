"""
Job manager for automation pipeline.
Tracks pending/active/completed opportunities triggered via folder moves.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..config import settings
from ..logging_config import get_logger

logger = get_logger("job_manager")

STATE_FILE = settings.project_root / "automation_state.json"


@dataclass
class Job:
    notice_id: str
    stage: str  # rfi or rfp
    path: str
    status: str  # pending, running, complete, cancelled
    created_at: str


def _load_state() -> Dict[str, List[Dict]]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception as exc:
            logger.warning("Failed to read state file: %s", exc)
    return {"jobs": []}


def _save_state(state: Dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as exc:
        logger.error("Failed to write state file: %s", exc)


def list_jobs(status: Optional[str] = None) -> List[Job]:
    state = _load_state()
    jobs = [Job(**job) for job in state.get("jobs", [])]
    if status:
        jobs = [job for job in jobs if job.status == status]
    return jobs


def add_job(notice_id: str, stage: str, path: Path, status: str = "pending") -> Job:
    state = _load_state()
    existing = next((job for job in state.get("jobs", []) if job["notice_id"] == notice_id and job["stage"] == stage), None)
    if existing and existing["status"] == status:
        logger.info("Job already queued: %s (%s)", notice_id, stage)
        return Job(**existing)

    job = Job(
        notice_id=notice_id,
        stage=stage,
        path=str(path),
        status=status,
        created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    if existing:
        logger.info("Updating job %s (%s) status -> %s", notice_id, stage, status)
        existing.update(asdict(job))
    else:
        state.setdefault("jobs", []).append(asdict(job))
        logger.info("Queued job: %s (%s)", notice_id, stage)

    _save_state(state)
    return job


def update_job_status(notice_id: str, stage: str, status: str) -> None:
    state = _load_state()
    updated = False
    for job in state.get("jobs", []):
        if job["notice_id"] == notice_id and job["stage"] == stage:
            job["status"] = status
            updated = True
            logger.info("Job %s (%s) status updated to %s", notice_id, stage, status)
            break
    if updated:
        _save_state(state)
    else:
        logger.warning("Job not found to update: %s (%s)", notice_id, stage)
