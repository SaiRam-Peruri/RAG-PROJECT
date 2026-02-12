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
python -m rag_project ingest         # Index documents
python -m rag_project query          # Ask questions
python -m rag_project generate       # Generate sections
python -m rag_project compliance     # Compliance matrix
python -m rag_project sam-sync       # SAM.gov pipeline
python -m rag_project health         # System check
```

### 4. Docker

```bash
docker-compose up -d
```

## SAM.gov Pipeline

Fetch new opportunities automatically based on NAICS codes.

```bash
python -m rag_project sam-sync --mode active --days 3 --naics 541512 541513 --ingest
```

- Downloads matching opportunities into `Federal_Contracting/01_Active_Pursuits/<NOTICE_ID>/`
- Saves SAM metadata (`sam_metadata.json`)
- Optional `--ingest` flag re-indexes ChromaDB after download
- Configure defaults via `.env`:
  - `SAM_API_KEY=...`
  - `TARGET_NAICS=541512,541513`

## Automated Proposal Pipeline

Three-stage automation workflow with multi-agent review and Telegram notifications.

### Stage 1: Monitoring & Queueing

**Watchers** monitor folder triggers and queue opportunities:

```bash
# Watch for RFI/RFP folders to process
python -m rag_project opp-watch                    # Continuous monitoring
python -m rag_project opp-watch --once             # Single scan

# Auto-fetch from SAM.gov on schedule
python -m rag_project sam-watch                    # Poll every 60min
python -m rag_project sam-watch --interval 30      # Poll every 30min
```

**Folder Structure:**
```
Federal_Contracting/01_Active_Pursuits/
├── RFI_READY/          ← Place RFI folders here for processing
├── RFI_COMPLETE/       ← Completed RFIs moved here
├── RFP_READY/          ← Place RFP folders here for processing
├── RFP_COMPLETE/       ← Completed RFPs moved here
└── HOLD/               ← Cancel processing (move folders here)
```

### Stage 2: Orchestration & Execution

**Job Runner** processes queued opportunities:

```bash
# Run pending jobs (default: 1 job)
python -m rag_project job-run --limit 3

# Run specific job by ID
python -m rag_project job-run --notice-id CORHQ-25-R-0450 --stage rfp

# Run daemon (continuous processing)
python -m rag_project job-daemon --interval 30 --limit 1

# Job management
python -m rag_project job-list                     # View queue
python -m rag_project job-list --status pending
python -m rag_project job-cancel NOTICE-ID rfp     # Cancel job
```

**Pipeline Steps:** Ingest → Compliance Analysis → Section Generation → Multi-Agent Review

### Stage 3: Multi-Agent Review & Notifications

**Five specialized review agents** evaluate generated proposals:

| Agent | Emoji | Focus | Threshold |
|-------|-------|-------|-----------|
| **ComplianceBot** | 📋 | Requirement coverage, completeness | 0.70 |
| **TechArchitectBot** | 🔧 | Technical accuracy, feasibility | 0.75 |
| **NarrativeWriterBot** | ✍️ | Writing quality, clarity | 0.60 |
| **RiskAssessorBot** | ⚠️ | Risk language, uncertainty | 0.80 |
| **PolicyAnalystBot** | 📊 | Federal compliance, policy | 0.70 |

**Review Behavior:**
- ✅ **All agents pass** → Move folder to `*_COMPLETE`
- ❌ **Any agent fails** → Keep in `*_READY`, set status `review_failed`
- 🔄 **Re-run failed reviews** → `job-run --notice-id NOTICE-ID --stage rfp`

**Telegram Notifications** post results to your channel:
- Each agent posts individual analysis (score, issues, recommendations)
- Summary message aggregates overall pass/fail status
- Error notifications via PolicyAnalystBot

### CLI Flags

```bash
# Skip review (useful for testing)
python -m rag_project job-run --no-review

# Disable notifications
python -m rag_project job-run --no-notify

# Combine flags
python -m rag_project job-daemon --no-review --no-notify --interval 60
```

### Environment Variables

**Telegram Integration:**
```bash
TELEGRAM_CHAT_ID=-1003626628455                      # Your channel ID
TELEGRAM_BOT_COMPLIANCE=bot_token_here               # ComplianceBot
TELEGRAM_BOT_TECH=bot_token_here                     # TechArchitectBot
TELEGRAM_BOT_NARRATIVE=bot_token_here                # NarrativeWriterBot
TELEGRAM_BOT_RISK=bot_token_here                     # RiskAssessorBot
TELEGRAM_BOT_POLICY=bot_token_here                   # PolicyAnalystBot
ENABLE_NOTIFICATIONS=true                            # Toggle notifications
```

**Review Thresholds:**
```bash
REVIEW_THRESHOLD_POLICY=0.7                          # ComplianceBot & PolicyAnalystBot
REVIEW_THRESHOLD_TECHNICAL=0.75                      # TechArchitectBot
REVIEW_THRESHOLD_NARRATIVE=0.6                       # NarrativeWriterBot
REVIEW_THRESHOLD_RISK=0.8                            # RiskAssessorBot
```

**Example .env snippet:**
```bash
# Stage 3: Multi-Agent Review + Notifications
TELEGRAM_CHAT_ID=-1003626628455
TELEGRAM_BOT_COMPLIANCE=7234567890:AAHexampleTokenComplianceBot123
TELEGRAM_BOT_TECH=7234567891:AAHexampleTokenTechArchitectBot456
TELEGRAM_BOT_NARRATIVE=7234567892:AAHexampleTokenNarrativeBot789
TELEGRAM_BOT_RISK=7234567893:AAHexampleTokenRiskAssessorBot012
TELEGRAM_BOT_POLICY=7234567894:AAHexampleTokenPolicyAnalystBot345
ENABLE_NOTIFICATIONS=true

REVIEW_THRESHOLD_POLICY=0.7
REVIEW_THRESHOLD_TECHNICAL=0.75
REVIEW_THRESHOLD_NARRATIVE=0.6
REVIEW_THRESHOLD_RISK=0.8
```

### Pipeline Workflow Diagram

```
SAM.gov / Manual Drop
         ↓
    [Watchers]
         ↓
   Queue (SQLite)
         ↓
   [Job Runner]
         ↓
   Orchestrator →→→ [Ingest → Compliance → Sections]
         ↓
   [Review Loop] → 5 Agents evaluate in parallel
         ↓
   📊 Score Aggregation
         ↓
    Pass? ───Yes──→ Move to *_COMPLETE + Telegram ✅
      │
      No
      ↓
   Stay in *_READY + Telegram ❌ + Status: review_failed
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

# Stage 3 tests (multi-agent review + notifications)
PYTHONPATH=src python -m pytest tests/test_review_agents.py -v
PYTHONPATH=src python -m pytest tests/test_notifications.py -v
PYTHONPATH=src python -m pytest tests/test_job_runner.py -v
```

**Test Coverage:**
- `test_review_agents.py` — Individual agent thresholds, run_review_loop aggregation
- `test_notifications.py` — Message formatting, mocked Telegram API calls
- `test_job_runner.py` — Folder gating with review_passed=False, status transitions

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
