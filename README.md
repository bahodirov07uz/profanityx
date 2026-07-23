# ProfanityX 🚫🗣️

> **The best multilingual profanity detection library for Python.**

[![PyPI version](https://img.shields.io/pypi/v/profanityx.svg)](https://pypi.org/project/profanityx/)
[![Python versions](https://img.shields.io/pypi/pyversions/profanityx.svg)](https://pypi.org/project/profanityx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/bahodirov07uz/profanityx/actions/workflows/test.yml/badge.svg)](https://github.com/bahodirov07uz/profanityx/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/bahodirov07uz/profanityx/branch/main/graph/badge.svg)](https://codecov.io/gh/bahodirov07uz/profanityx)

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 🌍 **Multilingual** | English, Uzbek, Russian — and you can add more |
| 🔡 **Leet-speak & homoglyph decoding** | Catches `f*ck`, `sh!t`, `5h1t`, Cyrillic look-alikes |
| 🎯 **Whole-word matching** | Avoids false positives (`classic` ≠ `ass`) |
| ✂️ **Censor / redact** | Replace bad words with `****` (preserves length) |
| 💬 **Explain** | Get word, positions, and which language flagged it |
| ⚙️ **Runtime word management** | Add / remove words without recreating the detector |
| 📦 **Zero dependencies** | Pure Python stdlib only |
| 🐍 **Python 3.9+** | Fully type-annotated, `mypy --strict` compliant |

---

## 📦 Installation

```bash
pip install profanityx
```

---

## 🚀 Quick Start

```python
from profanityx import ProfanityDetector

detector = ProfanityDetector()          # loads en + uz + ru
# Or narrow it down:
# detector = ProfanityDetector(languages=["en"])

# ── Detection ──────────────────────────────────────────────────────────────
print(detector.contains_profanity("What the fuck!"))   # True
print(detector.is_clean("Hello, how are you?"))        # True

# ── Find all matches ───────────────────────────────────────────────────────
print(detector.find_profanity("shit and damn"))        # ['shit', 'damn']

# ── Censor ─────────────────────────────────────────────────────────────────
print(detector.censor("What the fuck!"))               # 'what the ****!'
print(detector.censor("shit", preserve_length=True))   # '****'

# ── Explain (with positions) ────────────────────────────────────────────────
for match in detector.explain("shit happens"):
    print(match)
# {'word': 'shit', 'start': 0, 'end': 4, 'languages': ['en']}

# ── Leet-speak & obfuscation ───────────────────────────────────────────────
print(detector.contains_profanity("f*ck"))             # True
print(detector.contains_profanity("5h1t"))             # True

# ── Multilingual ───────────────────────────────────────────────────────────
print(detector.contains_profanity("какой мудак"))      # True  (Russian)
print(detector.contains_profanity("bu axmoq odam"))    # True  (Uzbek)

# ── Runtime word management ────────────────────────────────────────────────
detector.add_words(["badterm"], language="custom")
detector.remove_words(["badterm"])
```

---

## 🌐 Language Support

| Code | Language | Wordlist file |
|------|----------|--------------|
| `en` | English  | `profanityx/wordlists/en.json` |
| `uz` | Uzbek    | `profanityx/wordlists/uz.json` |
| `ru` | Russian  | `profanityx/wordlists/ru.json` |

### Loading a custom wordlist

```python
detector.load_custom_wordlist("/path/to/my_words.json", language="de")
```

The file must be a JSON array of strings.

---

## ⚙️ API Reference

### `ProfanityDetector`

```python
ProfanityDetector(
    languages: Iterable[str] | None = None,  # default: all bundled
    normalizer: Normalizer | None = None,
    whole_word: bool = True,
    censor_char: str = "*",
)
```

| Method | Description |
|--------|-------------|
| `contains_profanity(text)` | Returns `True` if profanity found |
| `is_clean(text)` | Inverse of `contains_profanity` |
| `find_profanity(text)` | Returns list of matched words |
| `censor(text, *, preserve_length=True)` | Redact profanity |
| `explain(text)` | Returns list of dicts with word/position/language |
| `add_words(words, language="custom")` | Add words at runtime |
| `remove_words(words)` | Remove words at runtime |
| `load_language(language)` | Load a bundled language wordlist |
| `load_custom_wordlist(path, language="custom")` | Load external JSON wordlist |

### `Normalizer`

```python
Normalizer(
    leet_decode: bool = True,
    collapse_repeats: bool = True,
    strip_punctuation: bool = True,
    lowercase: bool = True,
)
```

---

## 🧪 Running Tests

```bash
pip install -e ".[dev]"
pytest
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). We welcome PRs for:

- 🌍 New language wordlists
- 🐛 Bug fixes
- ✨ New features
- 📝 Docs improvements

---

## 📜 License

[MIT](LICENSE) © profanityx contributors
