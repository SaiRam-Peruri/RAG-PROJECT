"""
Unit tests for core RAG system functions.
Run: python -m pytest tests/ -v
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── rag_ingest tests ───────────────────────────────────

class TestIngestion:
    def test_should_index_pdf(self):
        from rag_ingest import should_index
        assert should_index(Path("doc.pdf")) is True

    def test_should_index_docx(self):
        from rag_ingest import should_index
        assert should_index(Path("doc.docx")) is True

    def test_reject_txt(self):
        from rag_ingest import should_index
        assert should_index(Path("readme.txt")) is False

    def test_reject_structure_file(self):
        from rag_ingest import should_index
        assert should_index(Path("structure")) is False

    def test_reject_signed_path(self):
        from rag_ingest import should_index
        assert should_index(Path("/data/Signed/contract.pdf")) is False

    def test_chunk_text_empty(self):
        from rag_ingest import chunk_text
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_chunk_text_short(self):
        from rag_ingest import chunk_text
        result = chunk_text("Hello world")
        assert len(result) == 1
        assert result[0] == "Hello world"

    def test_chunk_text_splits_long(self):
        from rag_ingest import chunk_text
        text = "A" * 10000
        chunks = chunk_text(text, max_chars=3500, overlap=300)
        assert len(chunks) > 1
        # All chunks ≤ max_chars
        for c in chunks:
            assert len(c) <= 3500

    def test_extract_metadata_active(self):
        from rag_ingest import extract_metadata
        p = Path("Federal_Contracting/01_Active_Pursuits/PROJ-001/01_Government_Issued/Final_Solicitations/rfp.pdf")
        meta = extract_metadata(p)
        assert meta["bucket"] == "active"
        assert meta["opportunity"] == "PROJ-001"
        assert meta["authority"] == "government"
        assert meta["stage"] == "solicitation"

    def test_choose_collection_gov(self):
        from rag_ingest import choose_collection
        meta = {"authority": "government", "stage": "solicitation"}
        assert choose_collection(meta) == "authoritative"

    def test_choose_collection_vendor(self):
        from rag_ingest import choose_collection
        meta = {"authority": "vendor", "stage": "proposal"}
        assert choose_collection(meta) == "drafting"

    def test_choose_collection_award(self):
        from rag_ingest import choose_collection
        meta = {"authority": "government", "stage": "award"}
        assert choose_collection(meta) == "drafting"


# ── utils tests ────────────────────────────────────────

class TestUtils:
    def test_norm(self):
        from utils import norm
        assert norm("  Hello   World  ") == "hello world"

    def test_dedup_results(self):
        from utils import dedup_results
        docs = ["hello world", "hello world", "different"]
        metas = [{"a": 1}, {"a": 2}, {"a": 3}]
        d, m = dedup_results(docs, metas)
        assert len(d) == 2

    def test_format_citation_page(self):
        from utils import format_citation
        assert format_citation({"filename": "rfp.pdf", "page": 5}) == "rfp.pdf p.5"

    def test_format_citation_sheet(self):
        from utils import format_citation
        assert format_citation({"filename": "data.xlsx", "sheet": "Sheet1"}) == "data.xlsx (sheet: Sheet1)"

    def test_detect_opportunity_explicit(self):
        from utils import detect_opportunity_from_query
        opps = ["CORHQ-25-R-0450", "OTHER-01-A-9999"]
        assert detect_opportunity_from_query("Tell me about CORHQ-25-R-0450", opps) == "CORHQ-25-R-0450"

    def test_detect_opportunity_none(self):
        from utils import detect_opportunity_from_query
        assert detect_opportunity_from_query("generic question", ["OPP-01-A-1234"]) is None

    def test_build_context_truncation(self):
        from utils import build_context
        docs = ["A" * 5000] * 10
        metas = [{"filename": f"f{i}.pdf", "page": 1} for i in range(10)]
        ctx = build_context(docs, metas, max_chars=8000)
        assert len(ctx) <= 8500  # some overhead from citations


# ── compliance_matrix tests ────────────────────────────

class TestCompliance:
    def test_extract_requirements_shall(self):
        from compliance_matrix import extract_requirements
        text = "The contractor shall provide daily reports. The system must support 100 users."
        reqs = extract_requirements(text)
        assert len(reqs) == 2
        assert reqs[0]["type"] == "Mandatory"

    def test_extract_requirements_should(self):
        from compliance_matrix import extract_requirements
        text = "The contractor should consider cloud hosting for scalability."
        reqs = extract_requirements(text)
        assert len(reqs) >= 1
        assert reqs[0]["type"] == "Desirable"

    def test_extract_requirements_empty(self):
        from compliance_matrix import extract_requirements
        assert extract_requirements("No requirements here.") == []

    def test_categorize_requirements(self):
        from compliance_matrix import categorize_requirements
        reqs = [
            {"text": "The system shall use cloud architecture with APIs", "type": "Mandatory"},
            {"text": "The contractor shall obtain ATO for all environments", "type": "Mandatory"},
        ]
        cats = categorize_requirements(reqs)
        assert len(cats["Technical"]) >= 1
        assert len(cats["Security"]) >= 1


# ── config tests ───────────────────────────────────────

class TestConfig:
    def test_config_imports(self):
        import config
        assert config.COLL_AUTH == "authoritative"
        assert config.COLL_DRAFT == "drafting"
        assert config.TOP_K > 0
        assert config.CHUNK_MAX_CHARS > 0
