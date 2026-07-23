"""
tests/test_wordlists.py
~~~~~~~~~~~~~~~~~~~~~~~~

Tests validating all bundled JSON wordlists in profanityx/wordlists/.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

WORDLIST_DIR = Path(__file__).parent.parent / "profanityx" / "wordlists"
WORDLIST_FILES = sorted(WORDLIST_DIR.glob("*.json"))
VALID_SEVERITIES = {"mild", "strong"}


class TestWordlistValidation:
    """Validate JSON schema and content constraints of all wordlists."""

    def test_wordlist_directory_not_empty(self) -> None:
        assert len(WORDLIST_FILES) >= 3, "Expected at least 3 bundled wordlists (en, uz, ru)"

    @pytest.mark.parametrize("filepath", WORDLIST_FILES, ids=lambda p: p.name)
    def test_json_file_validity(self, filepath: Path) -> None:
        raw = filepath.read_bytes()
        data = json.loads(raw.decode("utf-8"))

        assert isinstance(data, dict), f"{filepath.name}: root must be a JSON object"
        assert "language" in data, f"{filepath.name}: missing 'language' key"
        assert "words" in data, f"{filepath.name}: missing 'words' key"
        assert data["language"] == filepath.stem, (
            f"{filepath.name}: 'language' field '{data['language']}' != filename stem '{filepath.stem}'"
        )
        assert isinstance(data["words"], list), f"{filepath.name}: 'words' must be a JSON array"

    @pytest.mark.parametrize("filepath", WORDLIST_FILES, ids=lambda p: p.name)
    def test_wordlist_entries(self, filepath: Path) -> None:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        words_list = data["words"]
        seen_words: set[str] = set()

        for idx, entry in enumerate(words_list):
            prefix = f"{filepath.name} words[{idx}]"

            assert isinstance(entry, dict), f"{prefix}: entry must be an object"
            assert "word" in entry, f"{prefix}: missing 'word' key"
            assert "severity" in entry, f"{prefix}: missing 'severity' key"
            assert "variants" in entry, f"{prefix}: missing 'variants' key"

            word = entry["word"]
            assert isinstance(word, str), f"{prefix}: 'word' must be a string"
            word_clean = word.strip()
            assert len(word_clean) >= 2, f"{prefix}: 'word' cannot be empty or < 2 chars: {word!r}"
            assert word == word.lower(), f"{prefix}: 'word' must be lowercase: {word!r}"

            # Check duplicate words
            assert word.lower() not in seen_words, f"{prefix}: duplicate word '{word}' found"
            seen_words.add(word.lower())

            # Check severity
            severity = entry["severity"]
            assert severity in VALID_SEVERITIES, (
                f"{prefix}: 'severity' must be 'mild' or 'strong', got: {severity!r}"
            )

            # Check variants
            variants = entry["variants"]
            assert isinstance(variants, list), f"{prefix}: 'variants' must be a list"
            for vi, variant in enumerate(variants):
                assert isinstance(variant, str), f"{prefix} variant[{vi}] must be string"
                assert len(variant.strip()) > 0, f"{prefix} variant[{vi}] cannot be empty"
