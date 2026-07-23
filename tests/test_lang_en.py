"""
tests/test_lang_en.py
~~~~~~~~~~~~~~~~~~~~~

English-language profanity detection tests.

Covers:
  - Plain word detection
  - Leet-speak / obfuscated variants  (f*ck, sh1t, …)
  - Case insensitivity
  - Word-boundary / false-positive guard
  - Severity metadata
  - Censor output
"""

from __future__ import annotations

import pytest

from profanityx import ProfanityDetector

# ── Shared fixture ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def en() -> ProfanityDetector:
    """English-only detector, whole-word mode (default)."""
    return ProfanityDetector(languages=["en"])


@pytest.fixture(scope="module")
def en_sub() -> ProfanityDetector:
    """English detector with whole_word=False for substring tests."""
    return ProfanityDetector(languages=["en"], whole_word=False)


# ── 1. Plain word detection ──────────────────────────────────────────────────


class TestEnPlainWords:
    """Canonical words must be detected verbatim."""

    @pytest.mark.parametrize(
        "text",
        [
            "What the fuck is this",
            "This is bullshit",
            "He is such a bastard",
            "That was a shitty move",
            "You dumbass!",
            "Stop being a jerk",
            "What a scumbag",
            "He called her a whore",
            "Don't be a prick",
            "Absolute dickhead",
        ],
    )
    def test_detects_plain_word(self, en: ProfanityDetector, text: str) -> None:
        assert en.contains_profanity(text), f"Expected profanity in: {text!r}"

    def test_clean_sentence_not_flagged(self, en: ProfanityDetector) -> None:
        assert en.is_clean("Hello, how are you today?")

    def test_empty_string(self, en: ProfanityDetector) -> None:
        assert en.is_clean("")

    def test_only_whitespace(self, en: ProfanityDetector) -> None:
        assert en.is_clean("   \t\n  ")


# ── 2. Leet-speak / obfuscated variants ─────────────────────────────────────


class TestEnLeetSpeak:
    """Obfuscated variants listed in the wordlist must be detected."""

    @pytest.mark.parametrize(
        "text",
        [
            "f*ck this",       # asterisk between letters
            "f**k you",        # double asterisk
            "sh1t happens",    # digit 1 → i
            "sh*t show",       # asterisk obfuscation
            "b*tch please",    # bitch variant
            "a**hole behavior",# asshole variant
        ],
    )
    def test_detects_leet_variant(self, en: ProfanityDetector, text: str) -> None:
        assert en.contains_profanity(text), f"Expected profanity (leet) in: {text!r}"

    def test_digit_leet_sh1t(self, en: ProfanityDetector) -> None:
        """Digit substitution: 1 → i."""
        assert en.contains_profanity("That is sh1t")

    def test_star_obfuscation_removed_between_chars(self, en: ProfanityDetector) -> None:
        """Punctuation between word chars is stripped before detection."""
        assert en.contains_profanity("f*ck off")


# ── 3. Case insensitivity ────────────────────────────────────────────────────


class TestEnCaseInsensitive:
    """Detection must be case-insensitive."""

    @pytest.mark.parametrize(
        "text",
        [
            "FUCK this",
            "Shit Happens",
            "What A BITCH",
            "BULLSHIT detector",
            "You JERK",
            "BuLlShIt",
        ],
    )
    def test_case_insensitive(self, en: ProfanityDetector, text: str) -> None:
        assert en.contains_profanity(text), f"Expected profanity (case) in: {text!r}"


# ── 4. False-positive / word-boundary guard ──────────────────────────────────


class TestEnFalsePositives:
    """Words that merely *contain* a profane substring must NOT be flagged
    when ``whole_word=True`` (the default)."""

    @pytest.mark.parametrize(
        "clean_text",
        [
            # 'ass' inside innocent words
            "I need assistance with my assignment",
            "She is a classical musician",
            "The assassin was caught",
            "Pass the basket please",
            # 'dick' inside innocent words
            "Charles Dickens wrote Oliver Twist",
            "The verdict was delivered",
            # 'piss' inside innocent words
            "The compass is broken",
            # 'shit' should NOT fire in 'sushi tasting'
            "I love sushi tonight",
            # 'cunt' should NOT fire in 'punctual'
            "She is very punctual",
            # 'cock' should NOT fire in 'cocktail'
            "He ordered a cocktail",
            # 'twat' should NOT fire inside 'twitter' (not in list, sanity)
            "Check my Twitter profile",
            # 'damn' should NOT fire in 'Amsterdam'
            "I visited Amsterdam last summer",
        ],
    )
    def test_no_false_positive_whole_word(
        self, en: ProfanityDetector, clean_text: str
    ) -> None:
        assert en.is_clean(clean_text), (
            f"False positive triggered on: {clean_text!r}\n"
            f"  Matches: {en.find_profanity(clean_text)}"
        )

    def test_substring_mode_fires_on_classical(self, en_sub: ProfanityDetector) -> None:
        """With whole_word=False, 'ass' DOES fire inside 'classical'."""
        assert en_sub.contains_profanity("classical music")


# ── 5. Severity metadata ─────────────────────────────────────────────────────


class TestEnSeverity:
    """explain() must return correct severity for known words."""

    def test_fuck_is_strong(self, en: ProfanityDetector) -> None:
        results = en.explain("fuck")
        assert results[0]["severity"] == "strong"

    def test_damn_is_mild(self, en: ProfanityDetector) -> None:
        results = en.explain("damn")
        assert results[0]["severity"] == "mild"

    def test_jerk_is_mild(self, en: ProfanityDetector) -> None:
        results = en.explain("jerk")
        assert results[0]["severity"] == "mild"

    def test_explain_has_language_en(self, en: ProfanityDetector) -> None:
        results = en.explain("shit")
        assert "en" in results[0]["languages"]

    def test_explain_has_variants(self, en: ProfanityDetector) -> None:
        results = en.explain("fuck")
        assert isinstance(results[0]["variants"], list)
        assert len(results[0]["variants"]) > 0


# ── 6. Censor output ─────────────────────────────────────────────────────────


class TestEnCensor:
    """Censor must replace profane words without touching clean words."""

    def test_censor_replaces_strong_word(self, en: ProfanityDetector) -> None:
        result = en.censor("What the fuck!")
        assert "fuck" not in result
        assert "*" in result

    def test_censor_preserves_surrounding_text(self, en: ProfanityDetector) -> None:
        result = en.censor("Hello shit world")
        # Non-profane words survive
        assert "hello" in result.lower()
        assert "world" in result.lower()

    def test_censor_preserve_length(self, en: ProfanityDetector) -> None:
        original = "shit"
        result = en.censor(original, preserve_length=True)
        assert len(result) == len(original)

    def test_censor_fixed_length(self, en: ProfanityDetector) -> None:
        result = en.censor("shit", preserve_length=False)
        assert result == "****"

    def test_clean_text_unchanged(self, en: ProfanityDetector) -> None:
        clean = "hello world"
        assert en.censor(clean) == clean
