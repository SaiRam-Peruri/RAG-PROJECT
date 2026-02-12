#!/bin/bash
# Rebuild ChromaDB on server deployment (if chroma_db/ doesn't exist)
# Run this ONCE on first deployment to Render/Fly.io

echo "Checking ChromaDB status..."

if [ -d "chroma_db" ] && [ "$(ls -A chroma_db)" ]; then
    echo "✓ ChromaDB already exists, skipping rebuild"
    exit 0
fi

echo "Building ChromaDB from source documents..."

if [ ! -f "rag_ingest.py" ]; then
    echo "✗ rag_ingest.py not found!"
    exit 1
fi

# Check if source documents exist (you'll need to upload these separately)
if [ ! -d "Federal_Contracting" ]; then
    echo "✗ Federal_Contracting/ not found!"
    echo "Please upload source documents to persistent storage first"
    exit 1
fi

# Run ingestion
python rag_ingest.py

if [ $? -eq 0 ]; then
    echo "✓ ChromaDB built successfully!"
else
    echo "✗ ChromaDB build failed"
    exit 1
fi
