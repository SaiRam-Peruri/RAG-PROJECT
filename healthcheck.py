#!/usr/bin/env python3
"""
Health Check — verify the RAG system is properly configured and ready.
"""

import os
import sys
import argparse
from pathlib import Path


def check_api_key() -> bool:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("❌ OPENAI_API_KEY not set")
        return False
    if not key.startswith("sk-"):
        print("⚠️  OPENAI_API_KEY doesn't start with 'sk-' (may be invalid)")
        return True  # warning, not failure
    print(f"✅ OPENAI_API_KEY set ({key[:8]}...)")
    return True


def check_dependencies() -> bool:
    missing = []
    for mod in ["openai", "chromadb", "pypdf", "docx", "openpyxl", "tqdm", "watchdog", "colorama"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print(f"   pip install {' '.join(missing)}")
        return False
    print("✅ All dependencies installed")
    return True


def check_directories() -> bool:
    from config import FEDERAL_CONTRACTING_DIR, CHROMA_DB_PATH

    ok = True
    if FEDERAL_CONTRACTING_DIR.exists():
        subdirs = [d.name for d in FEDERAL_CONTRACTING_DIR.iterdir() if d.is_dir()]
        print(f"✅ Federal_Contracting exists ({len(subdirs)} subdirs)")
    else:
        print(f"⚠️  Federal_Contracting not found at {FEDERAL_CONTRACTING_DIR}")
        ok = False

    if CHROMA_DB_PATH.exists():
        size_mb = sum(f.stat().st_size for f in CHROMA_DB_PATH.rglob("*") if f.is_file()) / 1024 / 1024
        print(f"✅ ChromaDB exists ({size_mb:.1f} MB)")
    else:
        print("⚠️  ChromaDB not initialized (run rag_ingest.py first)")
    return ok


def check_collections() -> bool:
    try:
        import chromadb
        from config import CHROMA_DB_PATH, COLL_AUTH, COLL_DRAFT

        client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        collections = [c.name for c in client.list_collections()]

        for name in [COLL_AUTH, COLL_DRAFT]:
            if name in collections:
                coll = client.get_collection(name)
                count = coll.count()
                print(f"✅ Collection '{name}': {count} chunks")
            else:
                print(f"⚠️  Collection '{name}' not found")
        return True
    except Exception as e:
        print(f"⚠️  Could not check collections: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="RAG System Health Check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    print("\n🔍 RAG Federal Proposal System — Health Check\n" + "=" * 50)

    results = []
    results.append(("API Key", check_api_key()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Directories", check_directories()))
    results.append(("Collections", check_collections()))

    print("\n" + "=" * 50)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print("✅ System ready!")
    else:
        print("⚠️  Some checks failed — see above")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
