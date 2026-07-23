"""
tests/test_performance.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

Performance benchmarks and large input stress tests for profanityx.
"""

from __future__ import annotations

import time

import pytest

from profanityx.detector import ProfanityDetector


@pytest.fixture(scope="module")
def large_clean_text() -> str:
    """Generate a 10,000-word clean document."""
    paragraph = (
        "The quick brown fox jumps over the lazy dog. "
        "Programming in Python is fun, productive, and efficient. "
        "Multilingual content moderation requires robust regex patterns and normalizers. "
    )
    # Repeat ~500 times to get > 10,000 words
    return " ".join([paragraph] * 500)


@pytest.fixture(scope="module")
def large_profane_text(large_clean_text: str) -> str:
    """Generate a 10,000-word document containing profanity at the end."""
    return large_clean_text + " What the fuck happened at the end!"


class TestPerformanceAndStress:
    """Stress test and benchmark large texts to ensure fast detection."""

    def test_performance_10k_words_clean(
        self, default_detector: ProfanityDetector, large_clean_text: str
    ) -> None:
        """Detection on 10,000 words clean text must execute in < 150 milliseconds."""
        start = time.perf_counter()
        result = default_detector.contains_profanity(large_clean_text)
        duration_ms = (time.perf_counter() - start) * 1000

        assert result is False
        assert duration_ms < 150.0, f"Performance test took too long: {duration_ms:.2f}ms"

    def test_performance_10k_words_profane(
        self, default_detector: ProfanityDetector, large_profane_text: str
    ) -> None:
        """Detection on 10,000 words profane text must execute quickly (< 150 ms)."""
        start = time.perf_counter()
        result = default_detector.contains_profanity(large_profane_text)
        duration_ms = (time.perf_counter() - start) * 1000

        assert result is True
        assert duration_ms < 150.0, f"Performance test took too long: {duration_ms:.2f}ms"

    def test_censor_performance_large_text(
        self, default_detector: ProfanityDetector, large_profane_text: str
    ) -> None:
        """Censoring a 10,000-word text should complete quickly."""
        start = time.perf_counter()
        censored = default_detector.censor(large_profane_text)
        duration_ms = (time.perf_counter() - start) * 1000

        assert "****" in censored
        assert duration_ms < 250.0, f"Censor performance took too long: {duration_ms:.2f}ms"
