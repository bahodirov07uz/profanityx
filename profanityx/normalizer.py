"""
profanityx.normalizer
~~~~~~~~~~~~~~~~~~~~~

Text normalization utilities: unicode homoglyph replacement,
leet-speak decoding, whitespace collapsing, etc.
"""

from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Leet-speak / homoglyph character map
# ---------------------------------------------------------------------------
_LEET_MAP: dict[str, str] = {
    # Digit / symbol look-alikes → ASCII letters
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "6": "g",
    "7": "t",
    "8": "b",
    "@": "a",
    "$": "s",
    # NOTE: punctuation characters like !, |, ( are intentionally NOT included
    # here because the strip_punctuation step removes them cleanly.
}

# Pre-compile the pattern that collapses repeated characters  (e.g. "fuuuuck")
_REPEATED_CHARS = re.compile(r"(.)\1{2,}")


class Normalizer:
    """
    Lightweight, configurable text normalizer.

    Parameters
    ----------
    leet_decode:
        Replace leet-speak / homoglyph characters before matching.
    collapse_repeats:
        Collapse runs of 3+ identical characters to 2 (e.g. "fuuuck" → "fuuck").
    strip_punctuation:
        Remove all non-alphanumeric / non-space characters.
    lowercase:
        Convert the string to lowercase.

    Examples
    --------
    >>> n = Normalizer()
    >>> n.normalize("H3llo W0rld!!!")
    'hello world'
    """

    def __init__(
        self,
        *,
        leet_decode: bool = True,
        collapse_repeats: bool = True,
        strip_punctuation: bool = True,
        lowercase: bool = True,
    ) -> None:
        self.leet_decode = leet_decode
        self.collapse_repeats = collapse_repeats
        self.strip_punctuation = strip_punctuation
        self.lowercase = lowercase

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def normalize(self, text: str) -> str:
        """Return a normalized version of *text*.

        The pipeline applied (in order) is:
        1. Unicode NFC normalization.
        2. Lowercase (optional).
        3. Remove punctuation *between* letters (obfuscation: ``f*ck`` → ``fck``).
        4. Strip remaining punctuation to spaces (optional).
        5. Leet / homoglyph decoding (optional).
        6. Collapse repeated chars (optional).
        7. Collapse whitespace.
        """
        text = unicodedata.normalize("NFC", text)
        if self.lowercase:
            text = text.lower()
        # Step 3: drop punctuation *sandwiched between* word chars so that
        # obfuscation like "f*ck" → "fck" (not "f ck") is handled.
        text = re.sub(r"(?<=\w)[^\w\s]+(?=\w)", "", text, flags=re.UNICODE)
        if self.leet_decode:
            text = self._apply_leet(text)
        if self.strip_punctuation:
            text = re.sub(r"[^\w\s]|_", " ", text, flags=re.UNICODE)
        if self.collapse_repeats:
            text = _REPEATED_CHARS.sub(r"\1\1", text)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text: str) -> list[str]:
        """Return whitespace-split tokens of the normalized text."""
        return self.normalize(text).split()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_leet(text: str) -> str:
        return "".join(_LEET_MAP.get(ch, ch) for ch in text)
