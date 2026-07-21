# macOS and Linux Setup

```bash
git clone https://github.com/OVERLORDNO1/First.git
cd First

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e '.[dev]'

python scripts/verify_repository.py
python -m pytest -q
```

Expected baseline before Claude changes:

```text
7 passed
```

Start Claude Code in the repository or select the repository in Claude Code web, then
paste `CLAUDE_CODE_WEB_START.md`.

Never commit API keys.
