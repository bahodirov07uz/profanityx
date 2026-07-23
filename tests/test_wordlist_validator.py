"""
tests/test_wordlist_validator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests for scripts/validate_wordlists.py.

Ensures the validator correctly accepts valid wordlists and rejects
invalid ones (wrong structure, duplicates, bad severity, etc.).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make scripts/ importable from tests/
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from validate_wordlists import validate_file  # noqa: E402


# ── Helpers ──────────────────────────────────────────────────────────────────


def _write(tmp_path: Path, name: str, content: object) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(content), encoding="utf-8")
    return p


def _valid_entry(word: str = "badword", severity: str = "strong") -> dict:
    return {"word": word, "severity": severity, "variants": ["b4dword"]}


# ── Valid wordlists ───────────────────────────────────────────────────────────


class TestValidWordlists:
    def test_bundled_en_passes(self) -> None:
        path = Path("profanityx/wordlists/en.json")
        assert validate_file(path) == []

    def test_bundled_ru_passes(self) -> None:
        path = Path("profanityx/wordlists/ru.json")
        assert validate_file(path) == []

    def test_bundled_uz_passes(self) -> None:
        path = Path("profanityx/wordlists/uz.json")
        assert validate_file(path) == []

    def test_minimal_valid(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [_valid_entry()]
        })
        assert validate_file(p) == []

    def test_empty_words_list_ok(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {"language": "xx", "words": []})
        assert validate_file(p) == []

    def test_empty_variants_ok(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [{"word": "test", "severity": "mild", "variants": []}]
        })
        assert validate_file(p) == []

    def test_mild_severity_ok(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [_valid_entry(severity="mild")]
        })
        assert validate_file(p) == []


# ── Invalid: top-level structure ─────────────────────────────────────────────


class TestInvalidStructure:
    def test_plain_array_rejected(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", ["word1", "word2"])
        issues = validate_file(p)
        assert any("Root must be a JSON object" in i for i in issues)

    def test_missing_language_key(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {"words": []})
        issues = validate_file(p)
        assert any("language" in i for i in issues)

    def test_missing_words_key(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {"language": "xx"})
        issues = validate_file(p)
        assert any("words" in i for i in issues)

    def test_language_mismatch(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "en.json", {
            "language": "ru",   # mismatch: file is en.json
            "words": []
        })
        issues = validate_file(p)
        assert any("match" in i.lower() for i in issues)

    def test_words_is_not_array(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {"language": "xx", "words": "oops"})
        issues = validate_file(p)
        assert any("array" in i.lower() for i in issues)


# ── Invalid: entry-level rules ────────────────────────────────────────────────


class TestInvalidEntries:
    def test_missing_word_key(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [{"severity": "strong", "variants": []}]
        })
        issues = validate_file(p)
        assert any("'word'" in i for i in issues)

    def test_missing_severity_key(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [{"word": "bad", "variants": []}]
        })
        issues = validate_file(p)
        assert any("'severity'" in i for i in issues)

    def test_missing_variants_key(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [{"word": "bad", "severity": "strong"}]
        })
        issues = validate_file(p)
        assert any("'variants'" in i for i in issues)

    def test_word_too_short(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [{"word": "x", "severity": "strong", "variants": []}]
        })
        issues = validate_file(p)
        assert any("too short" in i for i in issues)

    def test_word_not_lowercase(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [{"word": "BadWord", "severity": "strong", "variants": []}]
        })
        issues = validate_file(p)
        assert any("lowercase" in i for i in issues)

    def test_invalid_severity(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [{"word": "bad", "severity": "extreme", "variants": []}]
        })
        issues = validate_file(p)
        assert any("mild" in i or "strong" in i for i in issues)

    def test_variants_not_array(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [{"word": "bad", "severity": "strong", "variants": "oops"}]
        })
        issues = validate_file(p)
        assert any("array" in i.lower() for i in issues)

    def test_empty_variant_string(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [{"word": "bad", "severity": "strong", "variants": [""]}]
        })
        issues = validate_file(p)
        assert any("empty" in i.lower() or "whitespace" in i.lower() for i in issues)


# ── Duplicate word detection ──────────────────────────────────────────────────


class TestDuplicateDetection:
    def test_duplicate_word_rejected(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [
                {"word": "dup", "severity": "strong", "variants": []},
                {"word": "dup", "severity": "mild",   "variants": []},
            ]
        })
        issues = validate_file(p)
        assert any("duplicate" in i.lower() for i in issues)

    def test_no_false_duplicate(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [
                {"word": "word1", "severity": "strong", "variants": []},
                {"word": "word2", "severity": "mild",   "variants": []},
            ]
        })
        assert validate_file(p) == []

    def test_multiple_duplicates_all_reported(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "xx.json", {
            "language": "xx",
            "words": [
                {"word": "a", "severity": "strong", "variants": []},   # too short too
                {"word": "abc", "severity": "strong", "variants": []},
                {"word": "abc", "severity": "strong", "variants": []},  # dup
                {"word": "xyz", "severity": "strong", "variants": []},
                {"word": "xyz", "severity": "strong", "variants": []},  # dup
            ]
        })
        issues = validate_file(p)
        dup_issues = [i for i in issues if "duplicate" in i.lower()]
        assert len(dup_issues) == 2   # abc and xyz
