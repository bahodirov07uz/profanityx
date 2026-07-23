"""
tests/test_lang_uz.py
~~~~~~~~~~~~~~~~~~~~~

Uzbek-language profanity detection tests.

Covers:
  - Plain word detection
  - Registered variant forms
  - Case insensitivity
  - Word-boundary / false-positive guard
  - Severity metadata
"""

from __future__ import annotations

import pytest

from profanityx import ProfanityDetector

# ── Shared fixture ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def uz() -> ProfanityDetector:
    """Uzbek-only detector, whole-word mode (default)."""
    return ProfanityDetector(languages=["uz"])


@pytest.fixture(scope="module")
def uz_sub() -> ProfanityDetector:
    """Uzbek detector with whole_word=False for substring tests."""
    return ProfanityDetector(languages=["uz"], whole_word=False)


# ── 1. Plain word detection ──────────────────────────────────────────────────


class TestUzPlainWords:
    """Canonical Uzbek profanity must be detected verbatim."""

    @pytest.mark.parametrize(
        "text",
        [
            "bu axmoq odam",
            "u harom bola",
            "sen besharm odam",
            "u yaramas",
            "bu iflos joy",
            "razil odam",
            "u vahshiy",
            "najas narsa",
            "bu tuban ish",
            "u nomard",
        ],
    )
    def test_detects_plain_uz_word(self, uz: ProfanityDetector, text: str) -> None:
        assert uz.contains_profanity(text), f"Expected profanity in: {text!r}"

    def test_clean_uz_sentence(self, uz: ProfanityDetector) -> None:
        assert uz.is_clean("Assalomu alaykum, qanday yashayapsiz?")

    def test_empty_string(self, uz: ProfanityDetector) -> None:
        assert uz.is_clean("")

    def test_clean_common_uz_words(self, uz: ProfanityDetector) -> None:
        assert uz.is_clean("Kitob stolda turibdi")
        assert uz.is_clean("Maktabga boring")
        assert uz.is_clean("Bugun ob-havo yaxshi")


# ── 2. Registered variant forms ──────────────────────────────────────────────


class TestUzVariants:
    """Wordlist variants must be detected."""

    def test_axmoqlik_variant(self, uz: ProfanityDetector) -> None:
        """'axmoqlik' is a registered variant of 'axmoq'."""
        assert uz.contains_profanity("axmoqlik qilma")

    def test_haromzoda_variant(self, uz: ProfanityDetector) -> None:
        """'haromzoda' is a variant of 'harom'."""
        assert uz.contains_profanity("u haromzoda")

    def test_besharmlik_variant(self, uz: ProfanityDetector) -> None:
        assert uz.contains_profanity("besharmlik")

    def test_buzuqchi_variant(self, uz: ProfanityDetector) -> None:
        assert uz.contains_profanity("u buzuqchi")

    def test_ifloslik_variant(self, uz: ProfanityDetector) -> None:
        assert uz.contains_profanity("ifloslik")

    def test_razillik_variant(self, uz: ProfanityDetector) -> None:
        assert uz.contains_profanity("razillik qildi")


# ── 3. Case insensitivity ────────────────────────────────────────────────────


class TestUzCaseInsensitive:
    """Detection must be case-insensitive for Latin-script Uzbek."""

    @pytest.mark.parametrize(
        "text",
        [
            "Bu AXMOQ odam",
            "HAROM narsa",
            "Sen BESHARM",
            "U YARAMAS bola",
            "IFLOS joy",
            "AxMoQ kishi",
        ],
    )
    def test_uppercase_uz(self, uz: ProfanityDetector, text: str) -> None:
        assert uz.contains_profanity(text), f"Expected profanity (upper) in: {text!r}"


# ── 4. False-positive / word-boundary guard ──────────────────────────────────


class TestUzFalsePositives:
    """Common Uzbek words that share substrings with profanity must NOT fire."""

    @pytest.mark.parametrize(
        "clean_text",
        [
            # 'it' (mild, 'dog') should NOT fire in 'itoat' (obedience)
            "Itoat qilish muhim",
            # 'past' (mild, 'low') should NOT fire in 'pastki' or 'pastor'
            "Pastor shimoliy tarafda joylashgan",
            # 'mol' (mild, 'cattle') should not fire in 'moliya' (finance)
            "Moliya vazirligi qaror qabul qildi",
            # general clean sentences
            "Toshkent Oʻzbekistonning poytaxti",
            "Bugun yaxshi kun",
            "Universitet binosida koʻpchilik bor",
            "Iqtisodiyot rivojlanmoqda",
            "Menga yordam bering",
            "Yangi yil bilan",
        ],
    )
    def test_no_false_positive_uz(self, uz: ProfanityDetector, clean_text: str) -> None:
        assert uz.is_clean(clean_text), (
            f"False positive on: {clean_text!r}\n"
            f"  Matches: {uz.find_profanity(clean_text)}"
        )

    def test_substring_mode_can_fire(self, uz_sub: ProfanityDetector) -> None:
        """With whole_word=False, substring match of 'it' fires inside 'itoat'."""
        assert uz_sub.contains_profanity("itoat")

    def test_assistant_word_boundary(self, uz: ProfanityDetector) -> None:
        """Regression: 'assistant' must not trigger any Uzbek profanity."""
        assert uz.is_clean("The assistant helped me today")


# ── 5. Severity metadata ─────────────────────────────────────────────────────


class TestUzSeverity:
    def test_fohisha_is_strong(self, uz: ProfanityDetector) -> None:
        results = uz.explain("fohisha")
        assert results[0]["severity"] == "strong"

    def test_axmoq_is_mild(self, uz: ProfanityDetector) -> None:
        results = uz.explain("axmoq")
        assert results[0]["severity"] == "mild"

    def test_harom_is_strong(self, uz: ProfanityDetector) -> None:
        results = uz.explain("harom")
        assert results[0]["severity"] == "strong"

    def test_explain_language_uz(self, uz: ProfanityDetector) -> None:
        results = uz.explain("axmoq")
        assert "uz" in results[0]["languages"]

    def test_find_multiple(self, uz: ProfanityDetector) -> None:
        found = uz.find_profanity("axmoq va harom odam")
        assert "axmoq" in found
        assert "harom" in found


# ── 6. Censor ─────────────────────────────────────────────────────────────────


class TestUzCensor:
    def test_censor_uz_word(self, uz: ProfanityDetector) -> None:
        result = uz.censor("axmoq odam")
        assert "axmoq" not in result
        assert "*" in result

    def test_clean_text_unchanged(self, uz: ProfanityDetector) -> None:
        assert uz.censor("yaxshi kun") == "yaxshi kun"
