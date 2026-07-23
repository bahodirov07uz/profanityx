"""
profanityx.detector
~~~~~~~~~~~~~~~~~~~

Core profanity detection engine.

Features
--------
* Multi-language support (en, uz, ru, and any custom JSON wordlist).
* Rich wordlist format: {language, words:[{word, severity, variants}]}.
* Configurable matching: whole-word, substring, or regex.
* Censor / redact matching words.
* Async-friendly (pure Python, no blocking I/O at detection time).
* Extensible: add words/languages at runtime.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, NamedTuple

from profanityx.normalizer import Normalizer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_WORDLIST_DIR = Path(__file__).parent / "wordlists"

# Languages bundled with the library
SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"en", "uz", "ru"})

# Valid severity levels
SEVERITY_LEVELS: frozenset[str] = frozenset({"mild", "strong"})


class WordEntry(NamedTuple):
    """A single entry loaded from a rich wordlist."""

    word: str
    severity: str  # "mild" | "strong"
    variants: list[str]
    language: str


def _load_wordlist(language: str) -> list[WordEntry]:
    """Load a bundled wordlist JSON file by language code.

    Supports two formats:

    **Rich format** (preferred)::

        {
          "language": "en",
          "words": [
            {"word": "...", "severity": "mild"|"strong", "variants": ["..."]}
          ]
        }

    **Legacy format** (plain array, for backward-compatibility)::

        ["word1", "word2", ...]
    """
    path = _WORDLIST_DIR / f"{language}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No bundled wordlist for language '{language}'. "
            f"Available: {sorted(SUPPORTED_LANGUAGES)}"
        )
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    # ── Rich format ────────────────────────────────────────────────────────
    if isinstance(data, dict):
        raw_words = data.get("words")
        if not isinstance(raw_words, list):
            raise ValueError(
                f"Wordlist at {path}: 'words' key must be a JSON array."
            )
        entries: list[WordEntry] = []
        for item in raw_words:
            if not isinstance(item, dict) or "word" not in item:
                raise ValueError(
                    f"Wordlist at {path}: each entry must be an object with a 'word' key."
                )
            word = str(item["word"]).lower()
            severity = str(item.get("severity", "strong"))
            if severity not in SEVERITY_LEVELS:
                severity = "strong"
            variants = [str(v).lower() for v in item.get("variants", [])]
            entries.append(WordEntry(word=word, severity=severity, variants=variants, language=language))
        return entries

    # ── Legacy format: plain array of strings ─────────────────────────────
    if isinstance(data, list):
        return [
            WordEntry(word=str(w).lower(), severity="strong", variants=[], language=language)
            for w in data
        ]

    raise ValueError(
        f"Wordlist at {path} must be either a JSON object (rich format) "
        "or a JSON array (legacy format)."
    )


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

        # canonical_word → WordEntry  (variants also point here)
        self._words: dict[str, WordEntry] = {}

        langs = list(languages) if languages is not None else list(SUPPORTED_LANGUAGES)
        for lang in langs:
            self.load_language(lang)

        self._build_pattern()

    # ------------------------------------------------------------------
    # Public helpers — wordlist management
    # ------------------------------------------------------------------

    def load_language(self, language: str) -> None:
        """Load (or reload) a bundled wordlist for *language*."""
        entries = _load_wordlist(language)
        self._register_entries(entries)
        self._build_pattern()

    def load_custom_wordlist(
        self, path: str | Path, *, language: str = "custom"
    ) -> None:
        """
        Load an external JSON wordlist file.

        Supports both the **rich format**::

            {
              "language": "custom",
              "words": [{"word": "...", "severity": "mild", "variants": [...]}]
            }

        and the **legacy format** (plain JSON array of strings).

        Parameters
        ----------
        path:
            Filesystem path to the JSON file.
        language:
            An arbitrary label used in :meth:`explain` (used for legacy format).
        """
        # Reuse the same parser used for bundled wordlists.
        path = Path(path)
        # Temporarily copy file to a temp-named path and call _load_wordlist
        # would be awkward — instead replicate the logic inline.
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        if isinstance(data, dict):
            # Rich format — language field comes from the file itself.
            lang_label = data.get("language", language)
            raw_words = data.get("words", [])
            entries = [
                WordEntry(
                    word=str(item["word"]).lower(),
                    severity=str(item.get("severity", "strong")),
                    variants=[str(v).lower() for v in item.get("variants", [])],
                    language=str(lang_label),
                )
                for item in raw_words
                if isinstance(item, dict) and "word" in item
            ]
        elif isinstance(data, list):
            entries = [
                WordEntry(word=str(w).lower(), severity="strong", variants=[], language=language)
                for w in data
            ]
        else:
            raise ValueError("Custom wordlist must be a JSON object (rich) or array (legacy).")

        self._register_entries(entries)
        self._build_pattern()

    def add_words(
        self,
        words: Iterable[str],
        *,
        language: str = "custom",
        severity: str = "strong",
    ) -> None:
        """Add individual words to the active word set at runtime.

        Parameters
        ----------
        words:
            Iterable of word strings to add.
        language:
            Language label attached to the words.
        severity:
            ``"mild"`` or ``"strong"`` (default).
        """
        entries = [
            WordEntry(word=w.lower(), severity=severity, variants=[], language=language)
            for w in words
        ]
        self._register_entries(entries)
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

        * ``word`` (str) — normalized matched word
        * ``start`` (int) — start offset in normalized text
        * ``end`` (int) — end offset in normalized text
        * ``languages`` (list[str]) — language(s) that flag this word
        * ``severity`` (str) — ``"mild"`` or ``"strong"``
        * ``variants`` (list[str]) — known obfuscation variants
        """
        if not self._pattern:
            return []
        normalized = self._normalizer.normalize(text)
        results: list[dict[str, object]] = []
        for match in self._pattern.finditer(normalized):
            matched = match.group(0).lower()
            entry = self._words.get(matched)
            results.append(
                {
                    "word": matched,
                    "start": match.start(),
                    "end": match.end(),
                    "languages": [entry.language] if entry else [],
                    "severity": entry.severity if entry else "strong",
                    "variants": entry.variants if entry else [],
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
        return sorted({entry.language for entry in self._words.values()})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register_entries(self, entries: list[WordEntry]) -> None:
        """Register *entries* into the internal word table.

        Both the canonical word and all its variants are registered,
        each pointing to the same ``WordEntry`` object so that
        :meth:`explain` can look up severity/variants for any match.

        Variants are passed through the normalizer before registration so that
        obfuscated strings like ``a$$`` don't degenerate into single-char keys
        that would cause false positives.
        """
        for entry in entries:
            self._words[entry.word] = entry
            for raw_variant in entry.variants:
                # Normalize the variant the same way incoming text is normalized.
                normalized_variant = self._normalizer.normalize(raw_variant)
                # Skip degenerate results: empty string or single non-word char.
                if len(normalized_variant) < 2:
                    continue
                if normalized_variant not in self._words:
                    self._words[normalized_variant] = entry

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
