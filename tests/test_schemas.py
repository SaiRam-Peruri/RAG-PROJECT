"""Tests for Pydantic schemas."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic import ValidationError
from rag_project.models.schemas import QueryRequest, AnswerRequest, GenerateSectionRequest


class TestQueryRequest:
    def test_valid(self):
        req = QueryRequest(question="What are the requirements?", mode="auth")
        assert req.question == "What are the requirements?"
        assert req.mode == "auth"

    def test_default_mode(self):
        req = QueryRequest(question="test")
        assert req.mode == "auth"

    def test_invalid_mode(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="test", mode="bad")

    def test_question_too_long(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="x" * 2001)

    def test_top_k_bounds(self):
        req = QueryRequest(question="test", top_k=50)
        assert req.top_k == 50

        with pytest.raises(ValidationError):
            QueryRequest(question="test", top_k=0)

        with pytest.raises(ValidationError):
            QueryRequest(question="test", top_k=101)


class TestGenerateSectionRequest:
    def test_valid(self):
        req = GenerateSectionRequest(opportunity="CORHQ-25-R-0450", section_type="technical")
        assert req.opportunity == "CORHQ-25-R-0450"

    def test_missing_opportunity(self):
        with pytest.raises(ValidationError):
            GenerateSectionRequest(section_type="technical")
