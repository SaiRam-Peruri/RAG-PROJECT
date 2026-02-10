"""
SAM.gov pipeline:
- Fetch opportunities via SAM API
- Filter by NAICS codes
- Download attachments into Federal_Contracting structure
- Track processed notice IDs to avoid duplicates
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

from ..config import settings
from ..logging_config import get_logger
from .ingestion import ingest

logger = get_logger("sam")

SAM_API_URL = "https://api.sam.gov/prod/opportunities/v1/search"


@dataclass
class SamOpportunity:
    notice_id: str
    title: str
    agency: str
    naics_list: List[str]
    due_date: Optional[str]
    url: str
    attachments: List[Dict]
    data: Dict


class SamPipeline:
    def __init__(self, state_path: Optional[Path] = None):
        self.api_key = settings.sam_api_key
        if not self.api_key:
            raise RuntimeError("SAM_API_KEY not configured. Add to .env")
        self.naics = settings.target_naics
        self.state_path = state_path or (settings.project_root / "sam_state.json")
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except Exception as e:
                logger.warning("Failed to read state file: %s", e)
        return {"processed": []}

    def _save_state(self):
        try:
            self.state_path.write_text(json.dumps(self.state, indent=2))
        except Exception as e:
            logger.error("Failed to write state file: %s", e)

    def fetch(self, mode: str = "active", days_back: int = 7, limit: int = 50) -> List[SamOpportunity]:
        """Fetch opportunities from SAM.gov."""
        posted_from = (datetime.utcnow() - timedelta(days=days_back)).strftime("%m/%d/%Y")
        params = {
            "api_key": self.api_key,
            "limit": limit,
            "offset": 0,
            "postedFrom": posted_from,
            "sort": "-modifiedDate",
        }
        # SAM uses status=Active/Archived
        params["status"] = "active" if mode == "active" else "archived"
        if self.naics:
            params["naics"] = ",".join(self.naics)

        logger.info("Fetching SAM.gov %s opportunities (NAICS=%s)", mode, self.naics or "ALL")
        resp = requests.get(SAM_API_URL, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"SAM API error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        notices = data.get("opportunitiesData", [])

        results: List[SamOpportunity] = []
        for notice in notices:
            naics_list = notice.get("naicsCodes", [])
            if self.naics and not any(n in self.naics for n in naics_list):
                continue
            results.append(
                SamOpportunity(
                    notice_id=notice.get("noticeId"),
                    title=notice.get("title", ""),
                    agency=notice.get("department", ""),
                    naics_list=naics_list,
                    due_date=notice.get("responseDate"),
                    url=notice.get("uiLink", ""),
                    attachments=notice.get("attachments", []),
                    data=notice,
                )
            )
        logger.info("Found %d opportunities matching NAICS filter", len(results))
        return results

    def _opportunity_dir(self, opp: SamOpportunity) -> Path:
        base = settings.federal_contracting_dir / "01_Active_Pursuits" / opp.notice_id / "01_Government_Issued"
        base.mkdir(parents=True, exist_ok=True)
        return base

    def download(self, opp: SamOpportunity) -> List[Path]:
        """Download attachments for an opportunity."""
        target_dir = self._opportunity_dir(opp)
        saved_files: List[Path] = []
        for attachment in opp.attachments:
            url = attachment.get("url") or attachment.get("fileUrl")
            filename = attachment.get("fileName") or attachment.get("title") or f"{opp.notice_id}.dat"
            if not url:
                continue
            path = target_dir / filename
            if path.exists():
                saved_files.append(path)
                continue
            try:
                logger.info("Downloading %s -> %s", filename, path)
                with requests.get(url, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                saved_files.append(path)
                time.sleep(0.5)
            except Exception as e:
                logger.error("Failed to download %s: %s", url, e)
        # Save metadata
        meta_path = target_dir / "sam_metadata.json"
        meta_path.write_text(json.dumps(opp.data, indent=2))
        saved_files.append(meta_path)
        return saved_files

    def process(self, opp: SamOpportunity, run_ingest: bool = False) -> Dict:
        if opp.notice_id in self.state["processed"]:
            logger.info("Skipping %s (already processed)", opp.notice_id)
            return {"skipped": True}
        files = self.download(opp)
        self.state["processed"].append(opp.notice_id)
        self._save_state()
        stats = {"downloaded": len(files)}
        if run_ingest:
            ingest(clean=False, show_progress=False)
            stats["ingested"] = True
        return stats


def run_pipeline(
    mode: str = "active",
    days_back: int = 7,
    naics: Optional[List[str]] = None,
    limit: int = 50,
    run_ingest: bool = False,
) -> Dict:
    """Fetch + download opportunities from SAM.gov."""
    if naics:
        settings.target_naics = naics
    pipeline = SamPipeline()
    opportunities = pipeline.fetch(mode=mode, days_back=days_back, limit=limit)
    results = []
    for opp in opportunities:
        stats = pipeline.process(opp, run_ingest=run_ingest)
        stats.update({"notice_id": opp.notice_id, "title": opp.title})
        results.append(stats)
    return {"count": len(results), "results": results}
