#!/usr/bin/env python3
"""
scripts/validate_wordlists.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate all JSON wordlist files in profanityx/wordlists/ against the
expected schema and policy rules.

Rules checked
-------------
1.  File is valid UTF-8 JSON.
2.  Top-level structure is ``{"language": str, "words": list}``.
3.  ``language`` field matches the file stem (e.g. ``uz.json`` → ``"uz"``).
4.  Every entry in ``words`` is an object with required keys.
5.  ``word`` is a non-empty string of at least 2 characters, lowercase.
6.  ``severity`` is exactly ``"mild"`` or ``"strong"``.
7.  ``variants`` is a list of strings.
8.  No duplicate ``word`` values within the same file.
9.  All ``word`` and ``variant`` strings are non-empty after stripping
    whitespace.

Exit code
---------
0 — all files valid.
1 — one or more validation errors found.

Usage
-----
    python scripts/validate_wordlists.py
    python scripts/validate_wordlists.py profanityx/wordlists/en.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

WORDLIST_DIR = Path(__file__).parent.parent / "profanityx" / "wordlists"
VALID_SEVERITIES = {"mild", "strong"}

# ── Helpers ──────────────────────────────────────────────────────────────────


def error(path: Path, msg: str) -> str:
    return f"[ERROR] {path.name}: {msg}"


def warn(path: Path, msg: str) -> str:
    return f"[WARN]  {path.name}: {msg}"


# ── Core validator ───────────────────────────────────────────────────────────


def validate_file(path: Path) -> list[str]:
    """Validate a single wordlist file. Returns a list of error messages."""
    issues: list[str] = []

    # 1. Parse JSON
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [error(path, f"Invalid UTF-8 JSON: {exc}")]

    # 2. Top-level structure
    if not isinstance(data, dict):
        return [error(path, "Root must be a JSON object, not an array or scalar.")]

    missing_keys = {"language", "words"} - data.keys()
    if missing_keys:
        return [error(path, f"Missing required top-level keys: {sorted(missing_keys)}")]

    # 3. 'language' must match file stem
    lang_field = data["language"]
    if not isinstance(lang_field, str):
        issues.append(error(path, "'language' must be a string."))
    elif lang_field != path.stem:
        issues.append(
            error(
                path,
                f"'language' field is '{lang_field}' but filename stem is '{path.stem}'. "
                "They must match.",
            )
        )

    # 4. 'words' must be a list
    words_list = data["words"]
    if not isinstance(words_list, list):
        return issues + [error(path, "'words' must be a JSON array.")]

    seen_words: set[str] = set()

    for idx, entry in enumerate(words_list):
        prefix = f"words[{idx}]"

        # Must be a dict
        if not isinstance(entry, dict):
            issues.append(error(path, f"{prefix}: entry must be a JSON object."))
            continue

        # Required keys
        for key in ("word", "severity", "variants"):
            if key not in entry:
                issues.append(error(path, f"{prefix}: missing required key '{key}'."))

        # 5. Validate 'word'
        word = entry.get("word", "")
        if not isinstance(word, str):
            issues.append(error(path, f"{prefix}: 'word' must be a string."))
        else:
            word_stripped = word.strip()
            if len(word_stripped) < 2:
                issues.append(
                    error(path, f"{prefix}: 'word' is too short (min 2 chars): {word!r}")
                )
            if word != word.lower():
                issues.append(
                    error(path, f"{prefix}: 'word' must be lowercase, got: {word!r}")
                )
            if word_stripped == "":
                issues.append(error(path, f"{prefix}: 'word' is empty or whitespace-only."))

            # 8. Duplicate detection
            word_lower = word.lower()
            if word_lower in seen_words:
                issues.append(
                    error(path, f"{prefix}: duplicate word '{word_lower}' found.")
                )
            else:
                seen_words.add(word_lower)

        # 6. Validate 'severity'
        severity = entry.get("severity")
        if severity is None:
            pass  # already caught by missing-key check above
        elif severity not in VALID_SEVERITIES:
            issues.append(
                error(
                    path,
                    f"{prefix}: 'severity' must be 'mild' or 'strong', got: {severity!r}",
                )
            )

        # 7. Validate 'variants'
        variants = entry.get("variants")
        if variants is None:
            pass  # already caught above
        elif not isinstance(variants, list):
            issues.append(error(path, f"{prefix}: 'variants' must be a JSON array."))
        else:
            for vi, v in enumerate(variants):
                if not isinstance(v, str):
                    issues.append(
                        error(path, f"{prefix}.variants[{vi}]: must be a string, got {type(v).__name__}.")
                    )
                elif v.strip() == "":
                    issues.append(
                        error(path, f"{prefix}.variants[{vi}]: empty/whitespace string.")
                    )

    return issues


# ── Entry point ──────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    if argv:
        paths = [Path(p) for p in argv]
    else:
        paths = sorted(WORDLIST_DIR.glob("*.json"))

    if not paths:
        print("No wordlist files found to validate.", file=sys.stderr)
        return 1

    all_issues: list[str] = []
    file_count = 0

    for path in paths:
        if not path.exists():
            all_issues.append(f"[ERROR] {path}: file not found.")
            continue

        file_issues = validate_file(path)
        if file_issues:
            all_issues.extend(file_issues)
            print(f"  FAIL  {path.name} ({len(file_issues)} issue(s))")
            for issue in file_issues:
                print(f"        {issue}")
        else:
            word_count = len(json.loads(path.read_bytes().decode())["words"])
            print(f"  OK    {path.name} ({word_count} words)")
        file_count += 1

    print()
    if all_issues:
        print(f"Validation FAILED: {len(all_issues)} issue(s) across {file_count} file(s).")
        return 1

    print(f"All {file_count} wordlist file(s) passed validation (PASSED)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or None))
