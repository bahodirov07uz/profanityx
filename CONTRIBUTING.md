# Contributing to ProfanityX 🌍

Thank you for your interest in improving ProfanityX!
All contributions — new wordlists, bug fixes, documentation improvements,
and feature additions — are very welcome.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Adding a New Word to an Existing Wordlist](#adding-a-new-word-to-an-existing-wordlist)
- [Adding a New Language](#adding-a-new-language)
- [JSON Wordlist Format Reference](#json-wordlist-format-reference)
- [Duplicate-Word Policy](#duplicate-word-policy)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Checklist](#pull-request-checklist)

---

## Code of Conduct

By participating in this project, you agree to be respectful and constructive.
Harassment and discrimination of any kind will not be tolerated.

---

## Quick Start

```bash
git clone https://github.com/bahodirov07uz/profanityx.git
cd profanityx
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
pytest          # all tests must pass before opening a PR
```

---

## Development Setup

| Command | Purpose |
|---------|---------|
| `pip install -e ".[dev]"` | Install in editable mode with all dev extras |
| `pytest` | Run the full test suite with coverage |
| `ruff check .` | Lint the codebase |
| `ruff format .` | Format the codebase |
| `mypy profanityx` | Type-check the library |

---

## Running Tests

> [!IMPORTANT]
> **All tests must pass before you open a Pull Request.**
> The CI pipeline (`test.yml`) runs the same suite on every PR across
> 3 operating systems and 4 Python versions (3.9 – 3.12).

```bash
# Run everything
pytest

# Run only a specific language test file
pytest tests/test_lang_en.py -v
pytest tests/test_lang_ru.py -v
pytest tests/test_lang_uz.py -v

# Run with coverage report
pytest --cov=profanityx --cov-report=term-missing
```

---

## Adding a New Word to an Existing Wordlist

### Step 1 — Find the right file

Open `profanityx/wordlists/<lang>.json`.  
Available languages: `en`, `ru`, `uz`.

### Step 2 — Add your entry

```json
{
  "word": "yourword",
  "severity": "mild",
  "variants": ["y0urword", "your-word"]
}
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `word` | `string` | ✅ | The canonical, lowercase form of the profane word |
| `severity` | `"mild"` or `"strong"` | ✅ | How offensive the word is |
| `variants` | `array[string]` | ✅ (may be `[]`) | Known obfuscated spellings |

> [!WARNING]
> Use **lowercase** for all `word` and `variant` values.
> Duplicate words (same `word` value appearing twice) are rejected by the
> automated wordlist validator CI check.

### Step 3 — Verify JSON is valid

```bash
python -c "import json; json.load(open('profanityx/wordlists/en.json', encoding='utf-8')); print('OK')"
```

### Step 4 — Add a test

Add at least one test to the corresponding `tests/test_lang_<lang>.py` file:

```python
def test_yourword_detected(self, en: ProfanityDetector) -> None:
    assert en.contains_profanity("yourword here")
```

### Step 5 — Run the tests

```bash
pytest tests/test_lang_en.py -v
```

All existing tests must still pass.

---

## Adding a New Language

> [!IMPORTANT]
> Follow every step below carefully. Incomplete submissions will be
> asked to make corrections before merging.

### Step 1 — Create the wordlist file

Create `profanityx/wordlists/<lang-code>.json` using the
[JSON format](#json-wordlist-format-reference) below.

Use the ISO 639-1 two-letter code for `<lang-code>` (e.g. `de`, `fr`, `tr`).

```json
{
  "language": "de",
  "words": [
    {"word": "scheiße", "severity": "strong", "variants": ["scheisse", "sch3i0e"]},
    {"word": "mist",    "severity": "mild",   "variants": []}
  ]
}
```

### Step 2 — Register the language in the detector

Open [`profanityx/detector.py`](profanityx/detector.py) and add the new
code to `SUPPORTED_LANGUAGES`:

```python
SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"en", "uz", "ru", "de"})
```

### Step 3 — Create a language test file

Create `tests/test_lang_<lang>.py` modelled after `tests/test_lang_en.py`.
It **must** contain at minimum:

| Test class | What it tests |
|---|---|
| `TestXxPlainWords` | ≥ 5 parametrized plain-word detections |
| `TestXxVariants` | ≥ 2 variant forms |
| `TestXxCaseInsensitive` | ≥ 3 upper-case inputs |
| `TestXxFalsePositives` | ≥ 3 clean sentences that must NOT fire |
| `TestXxSeverity` | severity field in `explain()` output |

### Step 4 — Update documentation

- Add the language to the table in `README.md`:

```markdown
| `de` | German | `profanityx/wordlists/de.json` |
```

- Add a short section to `CONTRIBUTING.md` notes if the language has
  special considerations (e.g. right-to-left script, character normalization).

### Step 5 — Run the full test suite

```bash
pytest
```

### Step 6 — Open a Pull Request

Fill in the PR template and make sure the automated wordlist validator
CI check passes (it validates JSON schema and duplicate-free words).

---

## JSON Wordlist Format Reference

Every file in `profanityx/wordlists/` must follow this exact schema:

```json
{
  "language": "<iso-639-1 code>",
  "words": [
    {
      "word":     "<lowercase canonical form>",
      "severity": "mild" | "strong",
      "variants": ["<obfuscated form 1>", "..."]
    }
  ]
}
```

### Rules

1. **`language`** must match the filename stem (e.g. file `uz.json` → `"language": "uz"`).
2. **`word`** must be lowercase and at least 2 characters long.
3. **`severity`** must be exactly `"mild"` or `"strong"`.
4. **`variants`** must be a JSON array (may be empty `[]`).
5. **No duplicates** — no two entries may share the same `word` value.
6. **All strings must be UTF-8** — Cyrillic, Arabic, CJK etc. are fully supported.

### Automated Validation

Every Pull Request triggers `.github/workflows/validate-wordlist.yml`, which:

- Validates every `wordlists/*.json` against the schema above.
- Checks that no `word` value appears twice in the same file.

If the check fails, the PR cannot be merged.

---

## Duplicate-Word Policy

- If a word you want to add already exists, add new variant forms to the
  **existing** entry rather than creating a second entry.
- If you disagree with the current `severity` rating, open an issue to
  discuss it before changing it in a PR.

---

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>
```

| Type | When to use |
|------|------------|
| `feat` | New word, new language, new feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `chore` | CI, tooling, dependencies |
| `refactor` | Code restructuring without behaviour change |

**Examples**

```
feat(wordlists): add German wordlist (de)
fix(detector): word boundary in Arabic script
test(lang-en): add false-positive cases for 'scunthorpe'
chore(ci): cache pip in test workflow
```

---

## Pull Request Checklist

Before submitting, verify every item:

- [ ] `pytest` passes locally with **zero failures**
- [ ] `ruff check .` reports **no errors**
- [ ] `mypy profanityx` reports **no errors**
- [ ] All new wordlist entries use **lowercase** and follow the JSON schema
- [ ] No **duplicate words** in the wordlist file
- [ ] A **test** is added or updated for every behaviour change
- [ ] `README.md` updated if a new language was added
- [ ] PR description explains *why* the change is needed

---

Thank you for making ProfanityX better! 🚀
