"""Tests for profanityx.detector."""

from pathlib import Path

import pytest

from profanityx.detector import ProfanityDetector


@pytest.fixture
def en_detector() -> ProfanityDetector:
    return ProfanityDetector(languages=["en"])


@pytest.fixture
def all_detector() -> ProfanityDetector:
    return ProfanityDetector()


class TestContainsProfanity:
    def test_clean_text(self, en_detector: ProfanityDetector) -> None:
        assert en_detector.contains_profanity("Hello, how are you?") is False

    def test_single_profane_word(self, en_detector: ProfanityDetector) -> None:
        assert en_detector.contains_profanity("What the fuck!") is True

    def test_leet_speak(self, en_detector: ProfanityDetector) -> None:
        # f*ck → after normalisation 'fuck' should be detected
        assert en_detector.contains_profanity("f*ck this") is True

    def test_case_insensitive(self, en_detector: ProfanityDetector) -> None:
        assert en_detector.contains_profanity("SHIT happens") is True

    def test_russian(self, all_detector: ProfanityDetector) -> None:
        assert all_detector.contains_profanity("какой мудак") is True

    def test_uzbek(self, all_detector: ProfanityDetector) -> None:
        assert all_detector.contains_profanity("bu axmoq odam") is True

    def test_empty_string(self, en_detector: ProfanityDetector) -> None:
        assert en_detector.contains_profanity("") is False


class TestIsClean:
    def test_clean(self, en_detector: ProfanityDetector) -> None:
        assert en_detector.is_clean("Everything is fine") is True

    def test_not_clean(self, en_detector: ProfanityDetector) -> None:
        assert en_detector.is_clean("bullshit") is False


class TestFindProfanity:
    def test_finds_words(self, en_detector: ProfanityDetector) -> None:
        found = en_detector.find_profanity("shit and damn")
        assert "shit" in found
        assert "damn" in found

    def test_no_false_positives(self, en_detector: ProfanityDetector) -> None:
        found = en_detector.find_profanity("classic classic classic")
        assert found == []

    def test_empty(self, en_detector: ProfanityDetector) -> None:
        assert en_detector.find_profanity("") == []


class TestCensor:
    def test_replaces_with_stars(self, en_detector: ProfanityDetector) -> None:
        result = en_detector.censor("shit happens")
        assert "shit" not in result
        assert "*" in result

    def test_preserves_length(self, en_detector: ProfanityDetector) -> None:
        result = en_detector.censor("shit", preserve_length=True)
        assert len(result) == len("shit")

    def test_fixed_length(self, en_detector: ProfanityDetector) -> None:
        result = en_detector.censor("shit", preserve_length=False)
        assert result == "****"

    def test_clean_text_unchanged(self, en_detector: ProfanityDetector) -> None:
        clean = "hello world"
        assert en_detector.censor(clean) == clean

    def test_custom_censor_char(self) -> None:
        d = ProfanityDetector(languages=["en"], censor_char="#")
        result = d.censor("shit")
        assert "#" in result
        assert "*" not in result


class TestExplain:
    def test_returns_metadata(self, en_detector: ProfanityDetector) -> None:
        results = en_detector.explain("what the fuck is this shit")
        words = [r["word"] for r in results]
        assert "fuck" in words
        assert "shit" in words

    def test_positions(self, en_detector: ProfanityDetector) -> None:
        text = "fuck"
        results = en_detector.explain(text)
        assert len(results) == 1
        entry = results[0]
        assert entry["start"] == 0
        assert entry["end"] == 4

    def test_languages_field(self, en_detector: ProfanityDetector) -> None:
        results = en_detector.explain("fuck")
        assert len(results) == 1
        assert "en" in results[0]["languages"]

    def test_severity_field(self, en_detector: ProfanityDetector) -> None:
        results = en_detector.explain("fuck")
        assert results[0]["severity"] in ("mild", "strong")

    def test_variants_field(self, en_detector: ProfanityDetector) -> None:
        results = en_detector.explain("fuck")
        assert isinstance(results[0]["variants"], list)

    def test_multilang_explain(self, all_detector: ProfanityDetector) -> None:
        results = all_detector.explain("мудак")
        assert len(results) == 1
        assert results[0]["languages"] == ["ru"]


class TestWordlistManagement:
    def test_add_words(self, en_detector: ProfanityDetector) -> None:
        en_detector.add_words(["myword"])
        assert en_detector.contains_profanity("myword is here") is True

    def test_remove_words(self, en_detector: ProfanityDetector) -> None:
        en_detector.add_words(["tempword"])
        assert en_detector.contains_profanity("tempword") is True
        en_detector.remove_words(["tempword"])
        assert en_detector.contains_profanity("tempword") is False

    def test_word_count(self, en_detector: ProfanityDetector) -> None:
        initial = en_detector.word_count
        en_detector.add_words(["uniqueword123"])
        assert en_detector.word_count == initial + 1

    def test_loaded_languages(self, all_detector: ProfanityDetector) -> None:
        langs = all_detector.loaded_languages
        assert "en" in langs
        assert "ru" in langs
        assert "uz" in langs

    def test_custom_wordlist_file(self, tmp_path: Path, en_detector: ProfanityDetector) -> None:
        import json

        # Test rich format
        custom_file = tmp_path / "custom.json"
        custom_file.write_text(json.dumps({
            "language": "test",
            "words": [
                {"word": "banana", "severity": "mild", "variants": ["b4nana"]},
                {"word": "customword", "severity": "strong", "variants": []},
            ]
        }), encoding="utf-8")
        en_detector.load_custom_wordlist(custom_file, language="test")
        assert en_detector.contains_profanity("I love banana pie") is True
        # Variant should also match
        assert en_detector.contains_profanity("b4nana") is True

    def test_custom_wordlist_legacy(self, tmp_path: Path, en_detector: ProfanityDetector) -> None:
        import json

        legacy_file = tmp_path / "legacy.json"
        legacy_file.write_text(json.dumps(["legacyword", "anotherword"]), encoding="utf-8")
        en_detector.load_custom_wordlist(legacy_file, language="legacy")
        assert en_detector.contains_profanity("legacyword here") is True

    def test_add_words_severity(self, en_detector: ProfanityDetector) -> None:
        en_detector.add_words(["mildword"], language="custom", severity="mild")
        results = en_detector.explain("mildword")
        assert results[0]["severity"] == "mild"


class TestWholeWord:
    def test_whole_word_no_partial(self) -> None:
        """'ass' should NOT trigger inside 'class'."""
        d = ProfanityDetector(languages=["en"], whole_word=True)
        assert d.contains_profanity("this is a classic") is False

    def test_substring_mode(self) -> None:
        """With whole_word=False, partial matches fire."""
        d = ProfanityDetector(languages=["en"], whole_word=False)
        assert d.contains_profanity("classic") is True
