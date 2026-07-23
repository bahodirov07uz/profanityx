"""
tests/conftest.py
~~~~~~~~~~~~~~~~~

Shared pytest fixtures for the profanityx test suite.
"""

from __future__ import annotations

import pytest

from profanityx.detector import ProfanityDetector
from profanityx.normalizer import Normalizer


@pytest.fixture
def normalizer() -> Normalizer:
    """Default Normalizer instance."""
    return Normalizer()


@pytest.fixture
def default_detector() -> ProfanityDetector:
    """ProfanityDetector with all default bundled languages (en, uz, ru)."""
    return ProfanityDetector()


@pytest.fixture
def en_detector() -> ProfanityDetector:
    """ProfanityDetector loaded with English only."""
    return ProfanityDetector(languages=["en"])


@pytest.fixture
def ru_detector() -> ProfanityDetector:
    """ProfanityDetector loaded with Russian only."""
    return ProfanityDetector(languages=["ru"])


@pytest.fixture
def uz_detector() -> ProfanityDetector:
    """ProfanityDetector loaded with Uzbek only."""
    return ProfanityDetector(languages=["uz"])


@pytest.fixture
def multi_lang_detector() -> ProfanityDetector:
    """ProfanityDetector loaded with Uzbek and Russian."""
    return ProfanityDetector(languages=["uz", "ru"])
