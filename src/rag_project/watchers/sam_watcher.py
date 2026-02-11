"""
SAM.gov watcher process.
Periodically polls SAM.gov via the pipeline and auto-ingests new opportunities.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import List, Optional

from ..config import settings
from ..logging_config import get_logger
from ..services.sam_pipeline import run_pipeline

logger = get_logger("sam_watcher")


def watch(
    interval_minutes: int = 60,
    mode: str = "active",
    naics: Optional[List[str]] = None,
    days_back: int = 7,
    limit: int = 50,
    run_ingest: bool = True,
    max_cycles: Optional[int] = None,
) -> None:
    """Continuously poll SAM.gov for new opportunities.

    Args:
        interval_minutes: Wait time between polls.
        mode: "active" or "archived".
        naics: Override NAICS filters (defaults to TARGET_NAICS).
        days_back: Look-back window for SAM API.
        limit: Max opportunities per poll.
        run_ingest: Whether to run ingestion after downloads.
        max_cycles: Optional safety stop after N cycles (useful for tests).
    """
    naics = naics or settings.target_naics
    cycle = 0
    logger.info(
        "Starting SAM watcher: mode=%s, interval=%dmin, days_back=%d, limit=%d, naics=%s",
        mode,
        interval_minutes,
        days_back,
        limit,
        naics or "ALL",
    )

    try:
        while True:
            cycle += 1
            start_ts = datetime.utcnow()
            logger.info("Watcher cycle %d started at %s UTC", cycle, start_ts.strftime("%Y-%m-%d %H:%M:%S"))
            try:
                result = run_pipeline(
                    mode=mode,
                    days_back=days_back,
                    naics=naics,
                    limit=limit,
                    run_ingest=run_ingest,
                )
                new_items = [r for r in result.get("results", []) if not r.get("skipped")]
                logger.info(
                    "Cycle %d complete: %d opportunities processed (%d new)",
                    cycle,
                    result.get("count", 0),
                    len(new_items),
                )
            except Exception as exc:
                logger.exception("SAM watcher cycle failed: %s", exc)

            if max_cycles and cycle >= max_cycles:
                logger.info("Max cycles reached (%d). Stopping watcher.", max_cycles)
                break

            logger.info("Sleeping for %d minutes", interval_minutes)
            time.sleep(max(1, interval_minutes) * 60)
    except KeyboardInterrupt:
        logger.info("SAM watcher stopped by user")
