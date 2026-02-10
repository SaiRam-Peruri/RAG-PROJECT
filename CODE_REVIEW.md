# Code Review - RAG Federal Proposal System

**Reviewed by:** mylove 👾  
**Date:** 2026-02-10  
**Files:** 12 Python files (~3,868 lines)

---

## Critical Issues

### 1. Hardcoded Windows Path (`rag_ingest.py:14`)
```python
ROOT = Path(r"C:\Users\ACER\RAG-Project\Federal_Contracting")
```
- **Impact:** System won't work on any other machine
- **Fix:** Use relative path or environment variable

### 2. Bare `except` Clauses (`proposal_generator.py:303`, `auto_proposal_service.py` multiple)
```python
except:
    past_docs, past_metas = [], []
```
- **Impact:** Silently swallows all errors including KeyboardInterrupt
- **Fix:** Use `except Exception as e:` with logging

### 3. No API Key Validation
- OpenAI API key checked at entry but never validated
- ChromaDB embedding function will fail silently with invalid key
- **Fix:** Add upfront key validation with test call

### 4. `analyze_sam_format.py` uses `fitz` (PyMuPDF) — not in dependencies
- Will crash with `ModuleNotFoundError`
- **Fix:** Add to requirements or use pypdf instead

### 5. Inconsistent Model Names
- `rag_answer.py`: `gpt-4.1-mini`
- `proposal_generator.py`: `gpt-4o-mini`
- `refinement_workflow.py`: `gpt-4o-mini`
- **Fix:** Centralize model config

---

## Security Issues

### 1. `sys.path.insert(0, ...)` in multiple files
- `auto_proposal_service.py` inserts workspace path into sys.path at runtime
- Could allow path injection if workspace is writable by others

### 2. No input sanitization on opportunity names
- Opportunity names from folder paths used directly in file operations
- Path traversal possible if folder names contain `..`

### 3. Subprocess call without shell=False validation
- `auto_proposal_service.py:186` runs `subprocess.run(['python', 'rag_ingest.py'])`
- Should use `sys.executable` instead of `'python'`

---

## Code Quality Issues

### 1. Massive `auto_proposal_service.py` (1005 lines)
- Single file handles: file watching, pipeline, document generation, DOCX formatting
- Should be split into modules

### 2. Duplicated Code
- `_add_formatted_text()` duplicated in `auto_proposal_service.py` and `template_filler.py`
- `detect_opportunity_from_query()` duplicated in `rag_answer.py` and `proposal_generator.py`
- `extract_requirements()` logic duplicated between `compliance_matrix.py` and `requirement_tracker.py`

### 3. No Type Hints on Many Functions
- `auto_proposal_service.py` methods lack return types
- Event handlers lack parameter types

### 4. Magic Numbers / Strings
- `TOP_K = 12`, `MAX_CONTEXT_CHARS = 14000` — no explanation
- Hardcoded filenames like `"DMS_Support_RFP_Technical_Acceptability_Matrix_2025-11-14.xlsx"`
- Model names scattered across files

### 5. No Tests
- Zero test coverage
- No assertions or validation

### 6. `check_opportunities.py` — No error handling
- Crashes if ChromaDB doesn't exist yet
- No API key check

---

## Architecture Issues

### 1. No Configuration File
- Settings scattered: model names, paths, chunk sizes, TOP_K values
- Should have a central `config.py` or `.env` pattern

### 2. No Shared Utilities Module
- Common functions (text formatting, citation building, opportunity detection) duplicated
- Need a `utils.py` or `common.py`

### 3. Interactive `input()` Everywhere
- Every script requires manual input — can't be automated or used as library
- Need argparse CLI + importable function API

### 4. ChromaDB Path Hardcoded as `"chroma_db"`
- Relative path means it depends on CWD
- Should be configurable

---

## Recommendations (Priority Order)

1. ✅ Fix hardcoded Windows path → relative/env-based
2. ✅ Create `config.py` for centralized settings
3. ✅ Create `utils.py` for shared functions
4. ✅ Add argparse to all scripts
5. ✅ Fix bare except clauses
6. ✅ Add health check script
7. ✅ Add basic tests
8. ✅ Fix model name inconsistencies
9. ✅ Add requirements.txt
