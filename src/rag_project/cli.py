"""Command line interface for the RAG Federal Proposal System."""

from __future__ import annotations

import argparse
import sys


def cmd_serve(args):
    import uvicorn
    from .config import settings

    uvicorn.run(
        "rag_project.api.app:app",
        host=args.host or settings.api_host,
        port=args.port or settings.api_port,
        reload=args.reload,
        log_level=settings.log_level.lower(),
    )


def cmd_ingest(args):
    from pathlib import Path
    from .config import settings
    from .logging_config import setup_logging
    from .services.ingestion import ingest

    setup_logging(settings.log_level)
    root = Path(args.root) if args.root else None
    stats = ingest(root_dir=root, clean=args.clean)
    print(
        f"\nDone: {stats['files']} files → {stats['chunks']} chunks "
        f"(auth={stats['auth_chunks']}, draft={stats['draft_chunks']})"
    )


def cmd_query(args):
    from .config import settings
    from .logging_config import setup_logging
    from .services.generation import answer_question

    setup_logging(settings.log_level)
    settings.require_api_key()

    question = args.question or input("Ask: ").strip()
    if not question:
        print("No question provided.")
        return

    result = answer_question(question=question, mode=args.mode)
    print(f"\nAnswer ({result['docs']} sources):\n")
    print(result["answer"])
    print("\nCitations:")
    for i, c in enumerate(result["citations"], 1):
        print(f"  {i}. {c}")


def cmd_health(args):
    import os
    from .config import settings

    print("\n🔍 RAG System Health Check\n" + "=" * 50)

    key = os.getenv("OPENAI_API_KEY", "")
    print(f"{'✅' if key else '❌'} OPENAI_API_KEY {'set' if key else 'NOT set'}")

    missing = []
    for mod in ("openai", "chromadb", "pypdf", "docx", "openpyxl", "tqdm", "watchdog", "fastapi", "uvicorn"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    print(f"{'✅' if not missing else '❌'} Dependencies: {'OK' if not missing else 'Missing: ' + ', '.join(missing)}")

    fed_dir = settings.federal_contracting_dir
    print(f"{'✅' if fed_dir.exists() else '⚠️'} Federal_Contracting: {fed_dir}")

    db_path = settings.chroma_db_path
    print(f"{'✅' if db_path.exists() else '⚠️'} ChromaDB: {db_path}")

    try:
        from .core.chroma_client import get_chroma_manager

        manager = get_chroma_manager()
        collections = manager.list_collections()
        for name in collections:
            coll = manager.client.get_collection(name)
            print(f"  ✅ {name}: {coll.count()} chunks")
    except Exception as exc:
        print(f"  ⚠️  Could not check collections: {exc}")

    print("=" * 50)


def cmd_generate(args):
    from .config import settings
    from .logging_config import setup_logging
    from .services.generation import generate_section

    setup_logging(settings.log_level)
    settings.require_api_key()

    opportunity = args.opportunity or input("Opportunity: ").strip()
    section = args.section or input("Section (technical/management/past_performance/executive_summary): ").strip()

    print(f"\nGenerating {section} for {opportunity}...")
    result = generate_section(opportunity=opportunity, section_type=section)
    print(f"\n{'='*60}\n{result['content']}\n{'='*60}")
    print(f"\nCitations: {len(result['citations'])}")


def cmd_compliance(args):
    from .config import settings
    from .logging_config import setup_logging
    from .services.compliance import generate_compliance_matrix

    setup_logging(settings.log_level)
    settings.require_api_key()

    opportunity = args.opportunity or input("Opportunity: ").strip()
    print(f"\nGenerating compliance matrix for {opportunity}...")
    result = generate_compliance_matrix(opportunity=opportunity)
    print(f"\n✅ Done: {result['requirements']} requirements → {result['output_file']}")


def cmd_sam_sync(args):
    from .config import settings
    from .logging_config import setup_logging
    from .services.sam_pipeline import run_pipeline

    setup_logging(settings.log_level)
    naics = args.naics if args.naics else settings.target_naics
    print(f"\nFetching SAM.gov {args.mode} opportunities (NAICS={naics or 'ALL'})...")
    result = run_pipeline(
        mode=args.mode,
        days_back=args.days,
        naics=naics,
        limit=args.limit,
        run_ingest=args.ingest,
    )
    print(f"\nProcessed {result['count']} opportunities")
    for entry in result["results"][:5]:
        status = "skipped" if entry.get("skipped") else f"downloaded {entry.get('downloaded',0)} files"
        print(f"  - {entry['notice_id']}: {entry['title']} ({status})")


def cmd_sam_watch(args):
    from .config import settings
    from .logging_config import setup_logging
    from .watchers.sam_watcher import watch

    setup_logging(settings.log_level)
    naics = args.naics if args.naics else settings.target_naics
    print(
        f"\nStarting SAM watcher: mode={args.mode}, interval={args.interval}min, "
        f"NAICS={naics or 'ALL'}"
    )
    watch(
        interval_minutes=args.interval,
        mode=args.mode,
        naics=naics,
        days_back=args.days,
        limit=args.limit,
        run_ingest=not args.no_ingest,
        max_cycles=args.cycles,
    )


def cmd_opp_watch(args):
    from .config import settings
    from .logging_config import setup_logging
    from .watchers.opportunity_watcher import watch_triggers

    setup_logging(settings.log_level)
    stages = args.stages
    if stages:
        print(f"\nWatching trigger folders for stages: {', '.join(stages)}")
    if args.once:
        watch_triggers(once=True, stages=stages)
    else:
        watch_triggers(once=False, stages=stages)


def cmd_job_run(args):
    from .config import settings
    from .logging_config import setup_logging
    from .services.job_runner import run_pending_jobs, run_single_job

    setup_logging(settings.log_level)

    if args.notice_id:
        stage = args.stage or "rfp"
        print(f"\nRunning job: {args.notice_id} ({stage})")
        success = run_single_job(args.notice_id, stage)
        print("✅ Success" if success else "❌ Failed")
    else:
        print(f"\nProcessing up to {args.limit} pending job(s)...")
        completed = run_pending_jobs(limit=args.limit, dry_run=args.dry_run)
        print(f"✅ Completed {completed} job(s)")


def cmd_job_list(args):
    from .services.job_manager import list_jobs

    jobs = list_jobs(status=args.status)
    if not jobs:
        print(f"No jobs{' with status ' + args.status if args.status else ''}")
        return

    print("=" * 80)
    print(f"Jobs{' (' + args.status + ')' if args.status else ''}:")
    print("=" * 80)
    for job in jobs:
        print(f"Notice ID: {job.notice_id}")
        print(f"Stage: {job.stage}")
        print(f"Status: {job.status}")
        print(f"Path: {job.path}")
        print(f"Created: {job.created_at}")
        print("=" * 80)
    print(f"Total: {len(jobs)} job(s)")


def cmd_job_cancel(args):
    from .services.job_manager import update_job_status

    print(f"\nCancelling job: {args.notice_id} ({args.stage})")
    update_job_status(args.notice_id, args.stage, "cancelled")
    print("✅ Job cancelled")


def cmd_job_daemon(args):
    import time
    from .config import settings
    from .logging_config import setup_logging
    from .services.job_runner import run_pending_jobs

    setup_logging(settings.log_level)
    print(f"\nStarting job daemon (interval={args.interval}s, limit={args.limit} jobs/cycle)")
    print("Press Ctrl+C to stop ✋")

    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"\n{'='*70}\nDaemon cycle {cycle}\n{'='*70}")
            completed = run_pending_jobs(limit=args.limit)
            if completed == 0:
                print(f"No jobs processed. Sleeping {args.interval}s...")
            else:
                print(f"✅ Completed {completed} job(s). Next check in {args.interval}s...")
            if args.cycles and cycle >= args.cycles:
                print(f"Reached max cycles ({args.cycles}). Exiting.")
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nDaemon stopped by user")


def main():
    parser = argparse.ArgumentParser(
        prog="rag_project",
        description="RAG Federal Proposal System",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    sp = subparsers.add_parser("serve", help="Start API server")
    sp.add_argument("--host", type=str, default=None)
    sp.add_argument("--port", type=int, default=None)
    sp.add_argument("--reload", action="store_true")

    sp = subparsers.add_parser("ingest", help="Ingest documents")
    sp.add_argument("--root", type=str, default=None, help="Override root directory")
    sp.add_argument("--clean", action="store_true", default=True, help="Clean collections first")
    sp.add_argument("--no-clean", dest="clean", action="store_false")

    sp = subparsers.add_parser("query", help="Answer a question via RAG")
    sp.add_argument("question", nargs="?", default=None)
    sp.add_argument("--mode", choices=["auth", "draft"], default="auth")

    subparsers.add_parser("health", help="Health check")

    sp = subparsers.add_parser("generate", help="Generate proposal section")
    sp.add_argument("--opportunity", "-o", type=str, default=None)
    sp.add_argument("--section", "-s", type=str, default=None)

    sp = subparsers.add_parser("compliance", help="Generate compliance matrix")
    sp.add_argument("--opportunity", "-o", type=str, default=None)

    sp = subparsers.add_parser("sam-sync", help="Fetch SAM.gov opportunities")
    sp.add_argument("--mode", choices=["active", "archived"], default="active")
    sp.add_argument("--days", type=int, default=7, help="Look back N days")
    sp.add_argument("--limit", type=int, default=50, help="Max opportunities")
    sp.add_argument("--naics", nargs="*", help="Override NAICS filter")
    sp.add_argument("--ingest", action="store_true", help="Run ingest after download")

    sp = subparsers.add_parser("sam-watch", help="Continuously poll SAM.gov")
    sp.add_argument("--mode", choices=["active", "archived"], default="active")
    sp.add_argument("--interval", type=int, default=60, help="Minutes between polls")
    sp.add_argument("--days", type=int, default=7, help="Look back window per poll")
    sp.add_argument("--limit", type=int, default=50, help="Max opportunities per poll")
    sp.add_argument("--naics", nargs="*", help="Override NAICS codes")
    sp.add_argument("--no-ingest", action="store_true", help="Skip ingestion after download")
    sp.add_argument("--cycles", type=int, default=None, help="Stop after N cycles (for testing)")

    sp = subparsers.add_parser("opp-watch", help="Watch RFI/RFP trigger folders")
    sp.add_argument("--once", action="store_true", help="Run single scan and exit")
    sp.add_argument("--poll", type=int, default=5, help="Polling interval when --once is used")
    sp.add_argument("--stages", nargs="*", choices=["rfi", "rfp"], help="Limit to specific stages")

    sp = subparsers.add_parser("job-run", help="Run pending jobs")
    sp.add_argument("--limit", type=int, default=1, help="Max jobs to process")
    sp.add_argument("--notice-id", type=str, help="Run specific job by notice ID")
    sp.add_argument("--stage", choices=["rfi", "rfp"], help="Stage for specific job")
    sp.add_argument("--dry-run", action="store_true", help="Show what would run without executing")

    sp = subparsers.add_parser("job-list", help="List jobs in queue")
    sp.add_argument("--status", choices=["pending", "running", "complete", "error", "cancelled"], help="Filter by status")

    sp = subparsers.add_parser("job-cancel", help="Cancel a job")
    sp.add_argument("notice_id", help="Notice ID")
    sp.add_argument("stage", choices=["rfi", "rfp"], help="Stage (rfi or rfp)")

    sp = subparsers.add_parser("job-daemon", help="Run job processing daemon")
    sp.add_argument("--interval", type=int, default=30, help="Seconds between queue checks")
    sp.add_argument("--limit", type=int, default=1, help="Max jobs per cycle")
    sp.add_argument("--cycles", type=int, help="Stop after N cycles (for testing)")

    args = parser.parse_args()

    commands = {
        "serve": cmd_serve,
        "ingest": cmd_ingest,
        "query": cmd_query,
        "health": cmd_health,
        "generate": cmd_generate,
        "compliance": cmd_compliance,
        "sam-sync": cmd_sam_sync,
        "sam-watch": cmd_sam_watch,
        "opp-watch": cmd_opp_watch,
        "job-run": cmd_job_run,
        "job-list": cmd_job_list,
        "job-cancel": cmd_job_cancel,
        "job-daemon": cmd_job_daemon,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
