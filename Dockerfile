FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY src/ src/
COPY config.py utils.py ./

# Legacy scripts (backward compat)
COPY rag_ingest.py rag_query.py rag_answer.py rag_section_query.py ./
COPY proposal_generator.py compliance_matrix.py requirement_tracker.py ./
COPY template_filler.py refinement_workflow.py auto_proposal_service.py ./
COPY check_opportunities.py analyze_sam_format.py healthcheck.py ./

# Create data dirs
RUN mkdir -p Federal_Contracting chroma_db

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "rag_project", "serve"]
