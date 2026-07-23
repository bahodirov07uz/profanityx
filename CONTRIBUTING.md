# Contributing to ProfanityX

Thank you for your interest in contributing! 🎉

We welcome contributions of all kinds — new wordlists, bug fixes, documentation improvements, and feature additions.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Adding a New Language Wordlist](#adding-a-new-language-wordlist)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

By participating in this project, you agree to be respectful and constructive.
Harassment and discrimination of any kind will not be tolerated.

---

## How to Contribute

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/profanityx.git
   cd profanityx
   ```
3. **Create a branch** for your change:
   ```bash
   git checkout -b feat/my-feature
   ```
4. **Make your changes** following the guidelines below.
5. **Run tests** and linters (see [Development Setup](#development-setup)).
6. **Commit** following the [convention](#commit-message-convention).
7. **Push** and open a Pull Request against `main`.

---

## Development Setup

We recommend a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Lint & format

```bash
ruff check .
ruff format .
```

### Type checking

```bash
mypy profanityx
```

---

## Project Structure

```
profanityx/
├── profanityx/
│   ├── __init__.py       ← public API exports
│   ├── detector.py       ← ProfanityDetector class
│   ├── normalizer.py     ← Normalizer class
│   └── wordlists/
│       ├── en.json       ← English wordlist
│       ├── uz.json       ← Uzbek wordlist
│       └── ru.json       ← Russian wordlist
├── tests/
│   ├── test_detector.py
│   └── test_normalizer.py
├── .github/
│   └── workflows/
│       ├── test.yml      ← CI: run tests on every PR
│       └── publish.yml   ← CD: publish to PyPI on release
├── pyproject.toml
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

---

## Adding a New Language Wordlist

1. Create `profanityx/wordlists/<language-code>.json`.
2. The file must be a **JSON array of lowercase strings**:
   ```json
   ["word1", "word2", "word3"]
   ```
3. Update `SUPPORTED_LANGUAGES` in `profanityx/detector.py`.
4. Add a test case in `tests/test_detector.py`.
5. Mention the language in `README.md`.

---

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>
```

Common types: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`.

Examples:
- `feat(wordlists): add German wordlist`
- `fix(detector): whole-word boundary in Cyrillic text`
- `docs(readme): add badges`

---

## Pull Request Process

1. Ensure **all tests pass** and **coverage stays ≥ 90 %**.
2. Keep PRs focused — one feature or fix per PR.
3. Update `README.md` if you add or change user-facing behaviour.
4. A maintainer will review within a few days.

---

Thank you for making ProfanityX better! 🚀
