"""
tests/test_detector.py
~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for ProfanityDetector class.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from profanityx.detector import ProfanityDetector


class TestDetectorBasicFunctionality:
    """Test basic detection and clean text checks across languages."""

    def test_contains_profanity_english(self, en_detector: ProfanityDetector) -> None:
        assert en_detector.contains_profanity("What the fuck!") is True

    def test_contains_profanity_uzbek(self, uz_detector: ProfanityDetector) -> None:
        assert uz_detector.contains_profanity("bu axmoq odam") is True

    def test_contains_profanity_russian(self, ru_detector: ProfanityDetector) -> None:
        assert ru_detector.contains_profanity("какой мудак") is True

    def test_clean_text_returns_false(self, default_detector: ProfanityDetector) -> None:
        assert default_detector.contains_profanity("Hello world, this is clean text.") is False
        assert default_detector.is_clean("Hello world, this is clean text.") is True

    def test_empty_string_is_clean(self, default_detector: ProfanityDetector) -> None:
        assert default_detector.contains_profanity("") is False
        assert default_detector.is_clean("") is True


class TestDetectorFalsePositives:
    """CRITICAL: Test that word boundaries prevent false positives on innocent words."""

    @pytest.mark.parametrize(
        "clean_word_sentence",
        [
            "I need an assistant for this assignment.",
            "We are attending a computer science class today.",
            "He lives in Scunthorpe, England.",
            "Please pass me the salt.",
            "She ordered a fruit cocktail at the restaurant.",
            "The assassin was apprehended quickly.",
            "The compass points north.",
            "Charles Dickens wrote many famous novels.",
            "She was very punctual for the meeting.",
        ],
    )
    def test_false_positive_guard_english(
        self, en_detector: ProfanityDetector, clean_word_sentence: str
    ) -> None:
        assert en_detector.is_clean(clean_word_sentence), (
            f"False positive triggered on: {clean_word_sentence!r}, "
            f"matches: {en_detector.find_profanity(clean_word_sentence)}"
        )

    @pytest.mark.parametrize(
        "clean_uzbek_sentence",
        [
            "Itoat qilish eng yaxshi fazilatdir.",
            "Pastor shamol shimoldan esmoqda.",
            "Moliya vazirligi yangi hisobotni e'lon qildi.",
            "Toshkent O'zbekistonning poytaxtidir.",
            "The assistant helped us complete the task.",
        ],
    )
    def test_false_positive_guard_uzbek(
        self, uz_detector: ProfanityDetector, clean_uzbek_sentence: str
    ) -> None:
        assert uz_detector.is_clean(clean_uzbek_sentence), (
            f"False positive triggered on: {clean_uzbek_sentence!r}, "
            f"matches: {uz_detector.find_profanity(clean_uzbek_sentence)}"
        )

    @pytest.mark.parametrize(
        "clean_russian_sentence",
        [
            "Локомотив выиграл очередной футбольный матч.",
            "Это ничто по сравнению с прошлым годом.",
            "Москва — красивый город.",
        ],
    )
    def test_false_positive_guard_russian(
        self, ru_detector: ProfanityDetector, clean_russian_sentence: str
    ) -> None:
        assert ru_detector.is_clean(clean_russian_sentence), (
            f"False positive triggered on: {clean_russian_sentence!r}, "
            f"matches: {ru_detector.find_profanity(clean_russian_sentence)}"
        )


class TestDetectorCensor:
    """Test censorship functionality."""

    def test_censor_default_preserve_length(self, en_detector: ProfanityDetector) -> None:
        result = en_detector.censor("shit happens")
        assert "shit" not in result
        assert "****" in result
        assert len(result) == len("shit happens")

    def test_censor_fixed_length(self, en_detector: ProfanityDetector) -> None:
        result = en_detector.censor("shit", preserve_length=False)
        assert result == "****"

    def test_censor_custom_char(self) -> None:
        det = ProfanityDetector(languages=["en"], censor_char="#")
        result = det.censor("shit")
        assert "#" in result
        assert "*" not in result

    def test_censor_clean_text_unchanged(self, en_detector: ProfanityDetector) -> None:
        clean = "hello world"
        assert en_detector.censor(clean) == clean


class TestDetectorAnalyzeAndExplain:
    """Test analyze() and explain() metadata extraction."""

    def test_analyze_returns_word_language_and_severity(
        self, default_detector: ProfanityDetector
    ) -> None:
        results = default_detector.analyze("what the fuck is this shit")
        assert isinstance(results, list)
        assert len(results) == 2

        matched_words = [item["word"] for item in results]
        assert "fuck" in matched_words
        assert "shit" in matched_words

        for entry in results:
            assert "word" in entry
            assert "start" in entry
            assert "end" in entry
            assert "languages" in entry
            assert "severity" in entry
            assert entry["severity"] in ("mild", "strong")

    def test_explain_alias_matches_analyze(
        self, default_detector: ProfanityDetector
    ) -> None:
        text = "bu axmoq odam"
        explain_res = default_detector.explain(text)
        analyze_res = default_detector.analyze(text)
        assert explain_res == analyze_res


class TestDetectorMultiLanguageAndMultipleHits:
    """Test multi-language loading and multiple hits per text."""

    def test_multi_language_detector_uz_ru(
        self, multi_lang_detector: ProfanityDetector
    ) -> None:
        # Uzbek match
        assert multi_lang_detector.contains_profanity("bu axmoq odam") is True
        # Russian match
        assert multi_lang_detector.contains_profanity("какой мудак") is True
        # English should NOT match in multi_lang_detector (loaded uz+ru only)
        assert multi_lang_detector.contains_profanity("fuck") is False

    def test_multiple_hits_in_single_text(
        self, default_detector: ProfanityDetector
    ) -> None:
        text = "shit and fuck and damn"
        found = default_detector.find_profanity(text)
        assert len(found) >= 3
        assert "shit" in found
        assert "fuck" in found
        assert "damn" in found


class TestDetectorFuzzyBoundaryThreshold:
    """Test fuzzy boundary limits to prevent false positive explosions."""

    def test_slight_spelling_variation_registered_variants(
        self, en_detector: ProfanityDetector
    ) -> None:
        # Registered variant (sh1t) fires
        assert en_detector.contains_profanity("sh1t") is True

    def test_distant_innocent_words_do_not_trigger_fuzzy_matches(
        self, en_detector: ProfanityDetector
    ) -> None:
        # Innocent words like 'shirt', 'shift', 'shut', 'fact', 'duck' must NOT trigger false positives
        clean_words = ["shirt", "shift", "shut", "fact", "duck", "frock", "flock"]
        for w in clean_words:
            assert en_detector.is_clean(w), f"Innocent word {w!r} triggered false positive!"


class TestDetectorWordlistManagementAndEdgeCases:
    """Test runtime word management and initialization edge cases."""

    def test_add_and_remove_words(self, en_detector: ProfanityDetector) -> None:
        en_detector.add_words(["custombadword"], language="custom", severity="mild")
        assert en_detector.contains_profanity("custombadword here") is True

        en_detector.remove_words(["custombadword"])
        assert en_detector.contains_profanity("custombadword here") is False

    def test_empty_languages_warning(self) -> None:
        with pytest.warns(UserWarning, match="No languages specified"):
            det = ProfanityDetector(languages=[])
            assert det.word_count == 0
            assert det.contains_profanity("fuck") is False

    def test_nonexistent_language_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError):
            ProfanityDetector(languages=["nonexistent_lang_xx"])

    def test_custom_wordlist_loading(
        self, tmp_path: Path, en_detector: ProfanityDetector
    ) -> None:
        import json

        custom_file = tmp_path / "custom.json"
        custom_file.write_text(
            json.dumps(
                {
                    "language": "custom_lang",
                    "words": [
                        {"word": "testbad", "severity": "mild", "variants": ["t3stbad"]}
                    ],
                }
            ),
            encoding="utf-8",
        )
        en_detector.load_custom_wordlist(custom_file)
        assert en_detector.contains_profanity("testbad") is True
        assert en_detector.contains_profanity("t3stbad") is True
