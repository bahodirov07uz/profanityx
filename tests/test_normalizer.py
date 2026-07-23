"""
tests/test_normalizer.py
~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for Normalizer class.
"""

from __future__ import annotations

import pytest

from profanityx.normalizer import Normalizer


class TestNormalizerLeetspeak:
    """Test leetspeak decoding and symbol substitutions."""

    @pytest.mark.parametrize(
        ("input_text", "expected_contains"),
        [
            ("sh1t", "shit"),
            ("s.h.i.t", "shit"),
            ("s-h-i-t", "shit"),
            ("f*ck", "fck"),
            ("f**k", "fk"),
            ("5hit", "shit"),
            ("h3ll0", "hello"),
            ("b4stard", "bastard"),
        ],
    )
    def test_leetspeak_and_punctuation_normalization(
        self, normalizer: Normalizer, input_text: str, expected_contains: str
    ) -> None:
        normalized = normalizer.normalize(input_text)
        assert expected_contains in normalized


class TestNormalizerRepeatedChars:
    """Test character deduplication / repeat collapsing."""

    @pytest.mark.parametrize(
        ("input_text", "expected"),
        [
            ("shiiiit", "shiit"),
            ("fuuuuck", "fuuck"),
            ("hellooo", "helloo"),
            ("aaaaaa", "aa"),
        ],
    )
    def test_collapse_repeats(
        self, normalizer: Normalizer, input_text: str, expected: str
    ) -> None:
        assert normalizer.normalize(input_text) == expected

    def test_collapse_repeats_disabled(self) -> None:
        norm = Normalizer(collapse_repeats=False)
        assert norm.normalize("fuuuuck") == "fuuuuck"


class TestNormalizerCaseConversion:
    """Test casing normalization."""

    @pytest.mark.parametrize("input_text", ["SHIT", "ShIt", "sHiT", "SHiT"])
    def test_lowercase(self, normalizer: Normalizer, input_text: str) -> None:
        assert normalizer.normalize(input_text) == "shit"

    def test_lowercase_disabled(self) -> None:
        norm = Normalizer(lowercase=False, leet_decode=False, strip_punctuation=False)
        assert norm.normalize("ShIt") == "ShIt"


class TestNormalizerUnicodeAndMixedScripts:
    """Test Unicode NFC normalization and Cyrillic/Uzbek script handling."""

    def test_unicode_nfc_decomposition(self, normalizer: Normalizer) -> None:
        # Composed vs decomposed 'é'
        composed = "\u00e9"
        decomposed = "e\u0301"
        assert normalizer.normalize(composed) == normalizer.normalize(decomposed)

    def test_uzbek_okina_and_apostrophe(self, normalizer: Normalizer) -> None:
        # Uzbek words with modifier letter apostrophe / okina
        word1 = "oʻzbek"
        word2 = "o'zbek"
        # Normalization handles whitespace/punctuation gracefully without throwing errors
        assert len(normalizer.normalize(word1)) > 0
        assert len(normalizer.normalize(word2)) > 0

    def test_cyrillic_normalization(self, normalizer: Normalizer) -> None:
        assert normalizer.normalize("МУДАК") == "мудак"
        assert normalizer.normalize("ПИЗДЕЦ!!!") == "пиздец"


class TestNormalizerEdgeCases:
    """Test edge cases: empty strings, whitespace only, digits only, etc."""

    def test_empty_string(self, normalizer: Normalizer) -> None:
        assert normalizer.normalize("") == ""

    def test_only_whitespace(self, normalizer: Normalizer) -> None:
        assert normalizer.normalize("   \t\n   ") == ""

    def test_only_numbers(self, normalizer: Normalizer) -> None:
        # Leet decode converts 0->o, 1->i, 3->e, 4->a, 5->s, 6->g, 7->t, 8->b
        result = normalizer.normalize("1234567890")
        assert isinstance(result, str)

    def test_only_pure_punctuation(self, normalizer: Normalizer) -> None:
        assert normalizer.normalize("!#%^&*()_+-=[]{}|;:,.<>?") == ""

    def test_tokenize_method(self, normalizer: Normalizer) -> None:
        tokens = normalizer.tokenize("Hello, World! 123")
        assert isinstance(tokens, list)
        assert len(tokens) > 0
