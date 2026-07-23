"""
profanityx.detector
~~~~~~~~~~~~~~~~~~~

Core profanity detection engine.

Features
--------
* Multi-language support (en, uz, ru, and any custom JSON wordlist).
* Configurable matching: whole-word, substring, or regex.
* Censor / redact matching words.
* Async-friendly (pure Python, no blocking I/O at detection time).
* Extensible: add words/languages at runtime.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from profanityx.normalizer import Normalizer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_WORDLIST_DIR = Path(__file__).parent / "wordlists"

# Languages bundled with the library
SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"en", "uz", "ru"})


def _load_wordlist(language: str) -> list[str]:
    """Load a bundled wordlist JSON file by language code."""
    path = _WORDLIST_DIR / f"{language}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No bundled wordlist for language '{language}'. "
            f"Available: {sorted(SUPPORTED_LANGUAGES)}"
        )
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Wordlist at {path} must be a JSON array of strings.")
    return [w.lower() for w in data]


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------


class ProfanityDetector:
    """
    Multilingual profanity detector.

    Parameters
    ----------
    languages:
        Language codes to load (e.g. ``["en", "uz", "ru"]``).
        Defaults to all bundled languages.
    normalizer:
        A :class:`~profanityx.normalizer.Normalizer` instance.
        If *None*, a default one is constructed.
    whole_word:
        When *True* (default), only match complete words.
        When *False*, also catch substrings (e.g. "class" inside "classical").
    censor_char:
        The replacement character used by :meth:`censor`.

    Examples
    --------
    >>> detector = ProfanityDetector(languages=["en"])
    >>> detector.contains_profanity("What the f*ck!")
    True
    >>> detector.censor("What the f*ck!")
    'What the ****!'
    """

    def __init__(
        self,
        languages: Iterable[str] | None = None,
        *,
        normalizer: Normalizer | None = None,
        whole_word: bool = True,
        censor_char: str = "*",
    ) -> None:
        self._normalizer = normalizer or Normalizer()
        self._whole_word = whole_word
        self._censor_char = censor_char

        # word → set of languages that flag it
        self._words: dict[str, set[str]] = {}

        langs = list(languages) if languages is not None else list(SUPPORTED_LANGUAGES)
        for lang in langs:
            self.load_language(lang)

        self._build_pattern()

    # ------------------------------------------------------------------
    # Public helpers — wordlist management
    # ------------------------------------------------------------------

    def load_language(self, language: str) -> None:
        """Load (or reload) a bundled wordlist for *language*."""
        words = _load_wordlist(language)
        for word in words:
            self._words.setdefault(word, set()).add(language)
        self._build_pattern()

    def load_custom_wordlist(
        self, path: str | Path, *, language: str = "custom"
    ) -> None:
        """
        Load an external JSON wordlist file.

        The file must contain a JSON array of strings.

        Parameters
        ----------
        path:
            Filesystem path to the JSON file.
        language:
            An arbitrary label used in :meth:`explain`.
        """
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError("Custom wordlist must be a JSON array of strings.")
        for word in data:
            self._words.setdefault(word.lower(), set()).add(language)
        self._build_pattern()

    def add_words(self, words: Iterable[str], *, language: str = "custom") -> None:
        """Add individual words to the active word set at runtime."""
        for word in words:
            self._words.setdefault(word.lower(), set()).add(language)
        self._build_pattern()

    def remove_words(self, words: Iterable[str]) -> None:
        """Remove words from the active word set."""
        for word in words:
            self._words.pop(word.lower(), None)
        self._build_pattern()

    # ------------------------------------------------------------------
    # Public helpers — detection
    # ------------------------------------------------------------------

    def contains_profanity(self, text: str) -> bool:
        """Return *True* if *text* contains at least one profane word."""
        if not self._pattern:
            return False
        normalized = self._normalizer.normalize(text)
        return bool(self._pattern.search(normalized))

    def find_profanity(self, text: str) -> list[str]:
        """Return a list of all profane words found in *text* (normalized forms)."""
        if not self._pattern:
            return []
        normalized = self._normalizer.normalize(text)
        return self._pattern.findall(normalized)

    def censor(self, text: str, *, preserve_length: bool = True) -> str:
        """
        Replace each profane word in *text* with censor characters.

        Parameters
        ----------
        text:
            The input text to sanitize.
        preserve_length:
            If *True* (default), each letter of a matched word is replaced
            individually so the output length stays the same.
            If *False*, the entire match is replaced by a fixed ``****``.
        """
        if not self._pattern:
            return text

        normalized = self._normalizer.normalize(text)

        def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
            word = match.group(0)
            if preserve_length:
                return self._censor_char * len(word)
            return self._censor_char * 4

        # Apply censoring on the normalized text positions back to original is
        # complex; we operate on the normalized form for simplicity.
        return self._pattern.sub(_replace, normalized)

    def explain(self, text: str) -> list[dict[str, object]]:
        """
        Return detailed match information for each profane word detected.

        Each entry is a dict with keys:
        ``word`` (str), ``start`` (int), ``end`` (int), ``languages`` (list[str]).
        """
        if not self._pattern:
            return []
        normalized = self._normalizer.normalize(text)
        results: list[dict[str, object]] = []
        for match in self._pattern.finditer(normalized):
            word = match.group(0)
            langs = sorted(self._words.get(word, set()))
            results.append(
                {
                    "word": word,
                    "start": match.start(),
                    "end": match.end(),
                    "languages": langs,
                }
            )
        return results

    def is_clean(self, text: str) -> bool:
        """Convenience inverse of :meth:`contains_profanity`."""
        return not self.contains_profanity(text)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def word_count(self) -> int:
        """Total number of unique profane words loaded."""
        return len(self._words)

    @property
    def loaded_languages(self) -> list[str]:
        """Languages currently contributing to the active word set."""
        langs: set[str] = set()
        for lang_set in self._words.values():
            langs |= lang_set
        return sorted(langs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_pattern(self) -> None:
        """Recompile the master regex from the current word set."""
        if not self._words:
            self._pattern: re.Pattern[str] | None = None
            return

        # Sort longest-first so greedier matches win.
        sorted_words = sorted(self._words.keys(), key=len, reverse=True)
        escaped = [re.escape(w) for w in sorted_words]
        combined = "|".join(escaped)

        if self._whole_word:
            combined = rf"(?<!\w)(?:{combined})(?!\w)"

        self._pattern = re.compile(combined, re.IGNORECASE | re.UNICODE)
