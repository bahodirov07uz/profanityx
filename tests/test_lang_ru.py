"""
tests/test_lang_ru.py
~~~~~~~~~~~~~~~~~~~~~

Russian-language profanity detection tests.

Covers:
  - Plain Cyrillic word detection
  - Common leet/obfuscated variants
  - Case insensitivity (Cyrillic upper/lower)
  - Word-boundary / false-positive guard
  - Severity metadata
"""

from __future__ import annotations

import pytest

from profanityx import ProfanityDetector

# ── Shared fixture ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def ru() -> ProfanityDetector:
    """Russian-only detector, whole-word mode (default)."""
    return ProfanityDetector(languages=["ru"])


@pytest.fixture(scope="module")
def ru_sub() -> ProfanityDetector:
    """Russian detector with whole_word=False for substring tests."""
    return ProfanityDetector(languages=["ru"], whole_word=False)


# ── 1. Plain Cyrillic word detection ────────────────────────────────────────


class TestRuPlainWords:
    """Canonical Russian profanity must be detected verbatim."""

    @pytest.mark.parametrize(
        "text",
        [
            "какой мудак",
            "это просто пизда",
            "он полный дебил",
            "ты урод",
            "какая сука",
            "он настоящий ублюдок",
            "это полный блядь",
            "иди нахуй",
            "ты конченый",
            "какой придурок",
        ],
    )
    def test_detects_plain_ru_word(self, ru: ProfanityDetector, text: str) -> None:
        assert ru.contains_profanity(text), f"Expected profanity in: {text!r}"

    def test_clean_ru_sentence(self, ru: ProfanityDetector) -> None:
        assert ru.is_clean("Привет, как дела? Всё хорошо!")

    def test_empty_string(self, ru: ProfanityDetector) -> None:
        assert ru.is_clean("")

    def test_clean_common_words(self, ru: ProfanityDetector) -> None:
        """Common Russian words that look similar to profanity are clean."""
        assert ru.is_clean("Мама мыла раму")
        assert ru.is_clean("Книга на столе")
        assert ru.is_clean("Добрый день")


# ── 2. Leet-speak / variant detection ───────────────────────────────────────


class TestRuVariants:
    """Registered variants must be detected."""

    def test_mudila_variant(self, ru: ProfanityDetector) -> None:
        """'мудила' is a registered variant of 'мудак'."""
        assert ru.contains_profanity("полный мудила")

    def test_mudilo_variant(self, ru: ProfanityDetector) -> None:
        assert ru.contains_profanity("вот мудило")

    def test_blyad_variant(self, ru: ProfanityDetector) -> None:
        """'блядина' is a variant of 'блядь'."""
        assert ru.contains_profanity("настоящая блядина")

    def test_blyat_variant(self, ru: ProfanityDetector) -> None:
        """'блять' is a registered variant."""
        assert ru.contains_profanity("блять, опять")

    def test_pidoras_variant(self, ru: ProfanityDetector) -> None:
        assert ru.contains_profanity("полный пидорас")

    def test_sukha_variant(self, ru: ProfanityDetector) -> None:
        assert ru.contains_profanity("сучка бежала")


# ── 3. Case insensitivity ────────────────────────────────────────────────────


class TestRuCaseInsensitive:
    """Cyrillic upper-case must be detected."""

    @pytest.mark.parametrize(
        "text",
        [
            "МУДАК полный",
            "Это ПИЗДА",
            "Какой ДЕБИЛ",
            "Полный УРОД",
            "СУКА рядом",
        ],
    )
    def test_cyrillic_upper(self, ru: ProfanityDetector, text: str) -> None:
        assert ru.contains_profanity(text), f"Expected profanity (upper) in: {text!r}"

    def test_mixed_case(self, ru: ProfanityDetector) -> None:
        assert ru.contains_profanity("МуДаК")


# ── 4. False-positive / word-boundary guard ──────────────────────────────────


class TestRuFalsePositives:
    """Russian words that share substrings with profanity must NOT fire
    when whole_word=True."""

    @pytest.mark.parametrize(
        "clean_text",
        [
            # 'лох' (mild) should not trigger in 'локомотив'
            "Локомотив выиграл матч",
            # 'чмо' should not trigger in 'ничто'
            "Это ничто особенного",
            # General clean sentences
            "Москва — столица России",
            "Я люблю читать книги",
            "Погода сегодня хорошая",
            "Университет находится в центре",
            "Студенты сдали экзамены",
        ],
    )
    def test_no_false_positive(self, ru: ProfanityDetector, clean_text: str) -> None:
        assert ru.is_clean(clean_text), (
            f"False positive on: {clean_text!r}\n"
            f"  Matches: {ru.find_profanity(clean_text)}"
        )

    def test_substring_mode_can_fire(self, ru_sub: ProfanityDetector) -> None:
        """With whole_word=False, substring matches are expected."""
        # 'лох' fires inside 'лоховство' in substring mode
        assert ru_sub.contains_profanity("лоховство")


# ── 5. Severity metadata ─────────────────────────────────────────────────────


class TestRuSeverity:
    def test_mudak_is_strong(self, ru: ProfanityDetector) -> None:
        results = ru.explain("мудак")
        assert results[0]["severity"] == "strong"

    def test_loh_is_mild(self, ru: ProfanityDetector) -> None:
        results = ru.explain("лох")
        assert results[0]["severity"] == "mild"

    def test_idiot_is_mild(self, ru: ProfanityDetector) -> None:
        results = ru.explain("идиот")
        assert results[0]["severity"] == "mild"

    def test_explain_language_ru(self, ru: ProfanityDetector) -> None:
        results = ru.explain("мудак")
        assert "ru" in results[0]["languages"]

    def test_find_profanity_returns_list(self, ru: ProfanityDetector) -> None:
        found = ru.find_profanity("какой мудак и дебил")
        assert "мудак" in found
        assert "дебил" in found


# ── 6. Multiple hits ─────────────────────────────────────────────────────────


class TestRuMultipleHits:
    def test_two_words_in_sentence(self, ru: ProfanityDetector) -> None:
        found = ru.find_profanity("мудак и урод пришли")
        assert len(found) >= 2

    def test_censor_russian(self, ru: ProfanityDetector) -> None:
        result = ru.censor("мудак")
        assert "мудак" not in result
        assert "*" in result
