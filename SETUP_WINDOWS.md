# Windows Setup

## 1. Upload to GitHub

Extract the ZIP.

Open the extracted folder and upload the contents, not the ZIP itself, to the selected
GitHub repository. Commit them.

The repository root must show `pyproject.toml`, `CLAUDE.md`, `src`, `tests`, `docs`,
`charter`, and `config`.

## 2. Local verification

```powershell
git clone https://github.com/OVERLORDNO1/First.git
cd First

py -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev]"

python scripts\verify_repository.py
python -m pytest -q
```

Expected baseline before Claude changes:

```text
7 passed
```

## 3. Claude Code web

Create a new Claude Code task and select the repository containing the sentinel files.

Paste the complete contents of:

`CLAUDE_CODE_WEB_START.md`

## 4. Secrets

Do not put `ANTHROPIC_API_KEY` into GitHub, Claude Chat, documentation, screenshots, or
commits.

The key belongs only in the local environment or an approved secret store.
