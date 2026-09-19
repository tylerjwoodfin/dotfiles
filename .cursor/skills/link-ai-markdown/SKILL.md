---
name: link-ai-markdown
description: >-
  Symlink Cursor skills/rules and OpenClaw workspace AI markdown from
  ~/git/dotfiles onto this machine. Use when the user says symlink the AI
  markdown files from dotfiles, link AI skills, apply cursor skills from
  dotfiles, wire OpenClaw AGENTS.md, or similar.
---

# Link AI markdown from dotfiles

Canonical sources live in **`~/git/dotfiles`**. Live paths are symlinks.

## Do this

1. Confirm the repo exists (`~/git/dotfiles`). If missing, clone it first (Tyler's GitHub: `tylerjwoodfin/dotfiles`).
2. Run:

```bash
bash ~/git/dotfiles/scripts/link_ai_markdown.sh
```

Optional dry run:

```bash
bash ~/git/dotfiles/scripts/link_ai_markdown.sh --dry-run
```

3. Show the user what was linked (script stdout). Do not invent alternate destinations.

## What it links

| Source in dotfiles | Destination |
|--------------------|-------------|
| `.cursor/skills/*` | `~/.cursor/skills/` |
| `cursor/rules/*.mdc` | `~/git/.cursor/rules/` |
| `openclaw/workspace/{AGENTS,SOUL,IDENTITY,USER}.md` | `~/.openclaw/workspace/` |
| `openclaw/workspace/skills/*` | `~/.openclaw/workspace/skills/` |

Existing **real files** at a destination are moved once under `~/dotfiles-backup/ai-markdown/` before linking. Already-correct symlinks are left alone.

## Do not

- Edit or commit Cursor product skills under `~/.cursor/skills-cursor/`.
- Commit secrets (`openclaw.json`, bot tokens, API keys).
- Copy files instead of running the script (breaks the single-source model).
- Link `DREAMS.md`, `MEMORY.md`, or `memory/` (machine-local / generated).

## After linking

OpenClaw may need a gateway restart only if skills were missing before; usually not required for markdown-only updates:

```bash
~/git/tools/openclaw/openclaw-gateway gateway restart
```

(Only if the user wants a restart.)
