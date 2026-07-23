"""Tests for profanityx.normalizer."""

import pytest

from profanityx.normalizer import Normalizer


@pytest.fixture
def normalizer() -> Normalizer:
    return Normalizer()


class TestNormalizerDefaults:
    def test_lowercase(self, normalizer: Normalizer) -> None:
        assert normalizer.normalize("HELLO WORLD") == "hello world"

    def test_leet_decode_digits(self, normalizer: Normalizer) -> None:
        # 0→o, 3→e, 4→a
        result = normalizer.normalize("h3ll0")
        assert result == "hello"

    def test_collapse_repeats(self, normalizer: Normalizer) -> None:
        # 3+ identical chars collapsed to 2
        result = normalizer.normalize("fuuuuck")
        assert result == "fuuck"

    def test_strip_punctuation(self, normalizer: Normalizer) -> None:
        result = normalizer.normalize("Hello, World!!!")
        assert result == "hello world"

    def test_whitespace_collapse(self, normalizer: Normalizer) -> None:
        result = normalizer.normalize("  hello   world  ")
        assert result == "hello world"

    def test_unicode_nfc(self, normalizer: Normalizer) -> None:
        # Composed vs decomposed 'é'
        composed = "\u00e9"  # é NFC
        decomposed = "e\u0301"  # e + combining acute
        n = Normalizer(leet_decode=False, strip_punctuation=False)
        assert n.normalize(composed) == n.normalize(decomposed)


class TestNormalizerOptions:
    def test_no_leet(self) -> None:
        n = Normalizer(leet_decode=False)
        assert "0" in n.normalize("h3ll0")

    def test_no_collapse(self) -> None:
        n = Normalizer(collapse_repeats=False)
        assert "uuu" in n.normalize("fuuuuck")

    def test_no_strip(self) -> None:
        n = Normalizer(strip_punctuation=False)
        assert "!" in n.normalize("hello!")

    def test_no_lowercase(self) -> None:
        n = Normalizer(lowercase=False)
        assert n.normalize("HELLO") == "HELLO"


class TestTokenize:
    def test_basic(self, normalizer: Normalizer) -> None:
        tokens = normalizer.tokenize("Hello World")
        assert tokens == ["hello", "world"]

    def test_empty(self, normalizer: Normalizer) -> None:
        assert normalizer.tokenize("") == []
