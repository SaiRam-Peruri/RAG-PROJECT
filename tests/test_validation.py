"""Tests for input validation."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag_project.core.validation import (
    ValidationError,
    sanitize_opportunity_name,
    validate_mode,
    validate_section_type,
    validate_positive_int,
)


class TestSanitizeOpportunity:
    def test_valid_name(self):
        assert sanitize_opportunity_name("CORHQ-25-R-0450") == "CORHQ-25-R-0450"

    def test_strips_whitespace(self):
        assert sanitize_opportunity_name("  test  ") == "test"

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            sanitize_opportunity_name("")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValidationError):
            sanitize_opportunity_name("../../../etc/passwd")

    def test_rejects_slashes(self):
        with pytest.raises(ValidationError):
            sanitize_opportunity_name("foo/bar")

    def test_rejects_backslashes(self):
        with pytest.raises(ValidationError):
            sanitize_opportunity_name("foo\\bar")

    def test_rejects_special_chars(self):
        with pytest.raises(ValidationError):
            sanitize_opportunity_name("foo;rm -rf /")

    def test_rejects_too_long(self):
        with pytest.raises(ValidationError):
            sanitize_opportunity_name("A" * 201)

    def test_allows_underscores_hyphens(self):
        assert sanitize_opportunity_name("DMS_Support-Phase2") == "DMS_Support-Phase2"


class TestValidateMode:
    def test_auth(self):
        assert validate_mode("auth") == "auth"

    def test_draft(self):
        assert validate_mode("draft") == "draft"

    def test_invalid(self):
        with pytest.raises(ValidationError):
            validate_mode("invalid")

    def test_strips_whitespace(self):
        assert validate_mode("  AUTH  ") == "auth"


class TestValidateSectionType:
    def test_valid_types(self):
        for t in ("technical", "management", "past_performance", "executive_summary",
                   "staffing", "quality_assurance", "security", "transition", "cost"):
            assert validate_section_type(t) == t

    def test_invalid(self):
        with pytest.raises(ValidationError):
            validate_section_type("invalid_section")


class TestValidatePositiveInt:
    def test_valid(self):
        assert validate_positive_int(5, "test") == 5

    def test_zero(self):
        with pytest.raises(ValidationError):
            validate_positive_int(0, "test")

    def test_negative(self):
        with pytest.raises(ValidationError):
            validate_positive_int(-1, "test")

    def test_too_large(self):
        with pytest.raises(ValidationError):
            validate_positive_int(99999, "test", max_val=100)
