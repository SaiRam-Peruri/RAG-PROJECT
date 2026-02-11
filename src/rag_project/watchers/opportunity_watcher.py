"""
Watch RFI/RFP trigger folders and enqueue jobs for automation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import time

from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent
from watchdog.observers import Observer

from ..config import settings
from ..logging_config import get_logger
from ..services.job_manager import add_job

logger = get_logger("opportunity_watcher")

TRIGGER_MAP: Dict[str, str] = {
    "RFI_READY": "rfi",
    "RFP_READY": "rfp",
}


class OpportunityEventHandler(FileSystemEventHandler):
    def __init__(self, trigger_dir: Path, stage: str):
        super().__init__()
        self.trigger_dir = trigger_dir
        self.stage = stage

    def _handle_path(self, path: Path):
        if not path.is_dir():
            return
        notice_id = path.name
        logger.info("Detected opportunity %s in %s (stage=%s)", notice_id, self.trigger_dir.name, self.stage)
        add_job(notice_id=notice_id, stage=self.stage, path=path)

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            self._handle_path(Path(event.src_path))

    def on_moved(self, event: FileMovedEvent):
        if event.is_directory:
            self._handle_path(Path(event.dest_path))


def watch_triggers(once: bool = False, interval_seconds: int = 5, stages: Optional[List[str]] = None):
    """Watch trigger folders for new opportunities.

    Args:
        once: If True, run a single scan without watchdog.
        interval_seconds: Sleep interval when polling once.
        stages: Optional list of stages to watch ("rfi", "rfp").
    """
    base = settings.federal_contracting_dir / "01_Active_Pursuits"
    observers: List[Observer] = []

    def _scan_once():
        for folder, stage in TRIGGER_MAP.items():
            if stages and stage not in stages:
                continue
            trigger_dir = base / folder
            if not trigger_dir.exists():
                continue
            for child in trigger_dir.iterdir():
                if child.is_dir():
                    add_job(notice_id=child.name, stage=stage, path=child)

    if once:
        logger.info("Running single trigger scan (stages=%s)", stages or list(TRIGGER_MAP.values()))
        _scan_once()
        return

    logger.info("Watching trigger folders under %s", base)
    for folder, stage in TRIGGER_MAP.items():
        if stages and stage not in stages:
            continue
        trigger_dir = base / folder
        trigger_dir.mkdir(parents=True, exist_ok=True)
        handler = OpportunityEventHandler(trigger_dir, stage)
        observer = Observer()
        observer.schedule(handler, path=str(trigger_dir), recursive=False)
        observer.start()
        observers.append(observer)
        logger.info("Watching %s for stage %s", trigger_dir, stage)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping trigger watcher")
    finally:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()
