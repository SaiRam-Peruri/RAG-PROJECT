"""
CLI entry point — unified command-line interface.

Usage:
    python -m rag_project serve          # Start API server
    python -m rag_project ingest         # Ingest documents
    python -m rag_project query          # Interactive query
    python -m rag_project health         # Health check
    python -m rag_project generate       # Generate proposal section
    python -m rag_project compliance     # Generate compliance matrix
"""

from __future__ import annotations

import argparse
import sys


def cmd_serve(args):
    """Start the FastAPI server."""
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
    """Ingest documents."""
    from pathlib import Path
    from .config import settings
    from .logging_config import setup_logging
    setup_logging(settings.log_level)

    from .services.ingestion import ingest
    root = Path(args.root) if args.root else None
    stats = ingest(root_dir=root, clean=args.clean)
    print(f"\nDone: {stats['files']} files → {stats['chunks']} chunks "
          f"(auth={stats['auth_chunks']}, draft={stats['draft_chunks']})")


def cmd_query(args):
    """Interactive query."""
    from .config import settings
    from .logging_config import setup_logging
    setup_logging(settings.log_level)
    settings.require_api_key()

    from .services.generation import answer_question

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
    """Run health check."""
    from .config import settings
    import os

    print("\n🔍 RAG System Health Check\n" + "=" * 50)

    # API key
    key = os.getenv("OPENAI_API_KEY", "")
    print(f"{'✅' if key else '❌'} OPENAI_API_KEY {'set' if key else 'NOT set'}")

    # Dependencies
    missing = []
    for mod in ("openai", "chromadb", "pypdf", "docx", "openpyxl", "tqdm", "watchdog", "fastapi", "uvicorn"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    print(f"{'✅' if not missing else '❌'} Dependencies: {'OK' if not missing else 'Missing: ' + ', '.join(missing)}")

    # Directories
    fed_dir = settings.federal_contracting_dir
    print(f"{'✅' if fed_dir.exists() else '⚠️'} Federal_Contracting: {fed_dir}")

    db_path = settings.chroma_db_path
    print(f"{'✅' if db_path.exists() else '⚠️'} ChromaDB: {db_path}")

    # Collections
    try:
        from .core.chroma_client import get_chroma_manager
        manager = get_chroma_manager()
        collections = manager.list_collections()
        for name in collections:
            coll = manager.client.get_collection(name)
            print(f"  ✅ {name}: {coll.count()} chunks")
    except Exception as e:
        print(f"  ⚠️  Could not check collections: {e}")

    print("=" * 50)


def cmd_generate(args):
    """Generate a proposal section."""
    from .config import settings
    from .logging_config import setup_logging
    setup_logging(settings.log_level)
    settings.require_api_key()

    from .services.generation import generate_section

    opportunity = args.opportunity or input("Opportunity: ").strip()
    section = args.section or input("Section (technical/management/past_performance/executive_summary): ").strip()

    print(f"\nGenerating {section} for {opportunity}...")
    result = generate_section(opportunity=opportunity, section_type=section)
    print(f"\n{'='*60}\n{result['content']}\n{'='*60}")
    print(f"\nCitations: {len(result['citations'])}")


def cmd_compliance(args):
    """Generate compliance matrix."""
    from .config import settings
    from .logging_config import setup_logging
    setup_logging(settings.log_level)
    settings.require_api_key()

    from .services.compliance import generate_compliance_matrix

    opportunity = args.opportunity or input("Opportunity: ").strip()
    print(f"\nGenerating compliance matrix for {opportunity}...")
    result = generate_compliance_matrix(opportunity=opportunity)
    print(f"\n✅ Done: {result['requirements']} requirements → {result['output_file']}")


def main():
    parser = argparse.ArgumentParser(
        prog="rag_project",
        description="RAG Federal Proposal System",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # serve
    sp = subparsers.add_parser("serve", help="Start API server")
    sp.add_argument("--host", type=str, default=None)
    sp.add_argument("--port", type=int, default=None)
    sp.add_argument("--reload", action="store_true")

    # ingest
    sp = subparsers.add_parser("ingest", help="Ingest documents")
    sp.add_argument("--root", type=str, default=None, help="Override root directory")
    sp.add_argument("--clean", action="store_true", default=True, help="Clean collections first")
    sp.add_argument("--no-clean", dest="clean", action="store_false")

    # query
    sp = subparsers.add_parser("query", help="Answer a question via RAG")
    sp.add_argument("question", nargs="?", default=None)
    sp.add_argument("--mode", choices=["auth", "draft"], default="auth")

    # health
    subparsers.add_parser("health", help="Health check")

    # generate
    sp = subparsers.add_parser("generate", help="Generate proposal section")
    sp.add_argument("--opportunity", "-o", type=str, default=None)
    sp.add_argument("--section", "-s", type=str, default=None)

    # compliance
    sp = subparsers.add_parser("compliance", help="Generate compliance matrix")
    sp.add_argument("--opportunity", "-o", type=str, default=None)

    args = parser.parse_args()

    commands = {
        "serve": cmd_serve,
        "ingest": cmd_ingest,
        "query": cmd_query,
        "health": cmd_health,
        "generate": cmd_generate,
        "compliance": cmd_compliance,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
