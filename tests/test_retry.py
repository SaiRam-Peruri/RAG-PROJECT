"""Tests for retry logic."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag_project.core.retry import retry


class TestRetry:
    def test_succeeds_first_try(self):
        call_count = 0

        @retry(max_retries=3, base_delay=0.01)
        def good_func():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert good_func() == "ok"
        assert call_count == 1

    def test_retries_on_failure(self):
        call_count = 0

        @retry(max_retries=3, base_delay=0.01, retryable_exceptions=(ValueError,))
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("transient")
            return "ok"

        assert flaky_func() == "ok"
        assert call_count == 3

    def test_gives_up_after_max_retries(self):
        @retry(max_retries=2, base_delay=0.01, retryable_exceptions=(ValueError,))
        def bad_func():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            bad_func()

    def test_non_retryable_exception_raises_immediately(self):
        call_count = 0

        @retry(max_retries=3, base_delay=0.01, retryable_exceptions=(ValueError,))
        def type_error_func():
            nonlocal call_count
            call_count += 1
            raise TypeError("not retryable")

        with pytest.raises(TypeError):
            type_error_func()
        assert call_count == 1
