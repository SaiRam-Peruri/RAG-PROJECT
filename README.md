# RAG Federal Proposal Automation System

Production-grade AI system for automating federal government proposal generation using Retrieval-Augmented Generation (RAG).

## Features

- **Document Ingestion** — PDF, DOCX, XLSX with intelligent metadata extraction
- **Semantic Search** — OpenAI embeddings + ChromaDB vector database
- **Proposal Generation** — Section-by-section drafting with citations
- **Compliance Matrix** — Automated requirement extraction and tracking
- **REST API** — FastAPI with OpenAPI docs, auth, and rate limiting
- **Docker Support** — One-command deployment
- **CI/CD** — GitHub Actions pipeline

## Quick Start

### 1. Install

```bash
git clone https://github.com/SaiRam-Peruri/RAG-PROJECT.git
cd RAG-PROJECT
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your OpenAI API key and company info
```

### 3. Run

```bash
# Start API server
python -m rag_project serve

# Or use individual commands
python -m rag_project ingest       # Index documents
python -m rag_project query        # Ask questions
python -m rag_project generate     # Generate sections
python -m rag_project compliance   # Compliance matrix
python -m rag_project health       # System check
```

### 4. Docker

```bash
docker-compose up -d
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health (no auth) |
| GET | `/opportunities` | List available opportunities |
| POST | `/query` | Semantic search |
| POST | `/answer` | RAG question answering |
| POST | `/generate` | Generate proposal section |
| POST | `/compliance` | Generate compliance matrix |
| POST | `/ingest` | Ingest documents |

Interactive docs: `http://localhost:8000/docs`

### Authentication

Set `RAG_API_KEY` in `.env` to enable API key auth. Pass `X-API-Key` header with requests.

## Project Structure

```
RAG-PROJECT/
├── src/rag_project/          # Production package
│   ├── api/                  # FastAPI server
│   │   ├── app.py           # Main application
│   │   ├── auth.py          # API key authentication
│   │   └── rate_limit.py    # Rate limiting
│   ├── core/                 # Core utilities
│   │   ├── chroma_client.py # ChromaDB management
│   │   ├── llm.py           # LLM client with retry
│   │   ├── retry.py         # Exponential backoff
│   │   ├── utils.py         # Shared utilities
│   │   └── validation.py    # Input validation
│   ├── models/               # Pydantic schemas
│   │   └── schemas.py
│   ├── services/             # Business logic
│   │   ├── compliance.py    # Compliance matrix
│   │   ├── generation.py    # Proposal generation
│   │   ├── ingestion.py     # Document ingestion
│   │   └── retrieval.py     # Semantic retrieval
│   ├── cli.py               # CLI entry point
│   └── config.py            # Centralized config
├── tests/                    # Test suite (61 tests)
├── Federal_Contracting/      # Document repository
├── .github/workflows/        # CI/CD
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Configuration

All settings are environment-variable driven. See `.env.example` for full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | required | OpenAI API key |
| `RAG_API_KEY` | (empty) | API authentication key |
| `RAG_LLM_MODEL` | gpt-4.1-mini | LLM model for generation |
| `RAG_RATE_LIMIT_RPM` | 60 | Rate limit (requests/min) |
| `COMPANY_NAME` | Your Company | Company name for proposals |

## Testing

```bash
# Run all tests
PYTHONPATH=src python -m pytest tests/ -v

# Run specific test file
PYTHONPATH=src python -m pytest tests/test_validation.py -v
```

## Legacy Scripts

The original CLI scripts are preserved for backward compatibility:

```bash
python rag_ingest.py           # Document ingestion
python rag_query.py            # Interactive query
python proposal_generator.py   # Section generator
python compliance_matrix.py    # Compliance matrix
python healthcheck.py          # Health check
```

## Architecture

```
Documents → Ingestion → ChromaDB (auth + draft collections)
                              ↓
User Query → Retrieval → Context Building → LLM Generation → Response
                              ↓
                     Retry + Rate Limiting + Validation
```

## License

MIT

## Version

2.0.0 — Production release
