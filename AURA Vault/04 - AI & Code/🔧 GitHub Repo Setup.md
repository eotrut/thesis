# 🔧 GitHub Repo Setup

**Date:** 2026-07-04
**Status:** ✅ Complete

## Repo
- **Name:** `thesis`
- **Visibility:** Private
- **Owner:** kurtrobynmanabat
- **Local path:** `C:\Users\Roehl\Claude\Projects\thesis`
- **Default branch:** `main`

## Tooling
- **Git** (already installed)
- **GitHub CLI (`gh`)** — installed via `winget install --id GitHub.cli -e`
- **Shell:** Git Bash (MinTTY — required `winpty` prefix for `gh auth login`)

## Auth
- Method: `gh auth login` → GitHub.com → HTTPS → web browser
- Git credentials configured through gh (no separate PAT stored)

## Initial commit contents
- `README.md` — project overview
- `.gitignore` — Python + Obsidian workspace state + OS + LaTeX
- `AURA Vault/` — Obsidian knowledge base
- `create_vault.py`

## Daily workflow
```bash
cd "/c/Users/Roehl/Claude/Projects/thesis"
git add .
git commit -m "message"
git push
```

## Branching (for experiments)
```bash
git checkout -b feature-name
# ...work...
git push -u origin feature-name
```

## Useful commands
- Open repo in browser: `gh repo view --web`
- Add collaborator: `gh repo edit --add-collaborator <username>`
- Untrack a file already committed: `git rm --cached <file>` then commit

## Notes
- `.obsidian/workspace.json` is gitignored — it's local UI state, not content
- If ever seeing "MinTTY without pseudo terminal" from `gh`, prefix with `winpty`

## Related
- [[📋 Master Task Tracker]]
