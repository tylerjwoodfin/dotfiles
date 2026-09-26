# Cursor adapters

Reusable instruction text lives in `~/git/agents`. Files here tell Cursor when to load those instructions and how to call Cursor-only tools (MCP discovery, skill triggers, always-on rules).

## Layout

| Path in dotfiles | Installed to | Purpose |
|------------------|--------------|---------|
| `.cursor/skills/` | `~/.cursor/skills/` | Cursor skill adapters. Each `SKILL.md` points at `~/git/agents` |
| `cursor/rules/` | `~/git/.cursor/rules/` | Always-on Cursor rules that point at `~/git/agents` |
| `openclaw/workspace/` | `~/.openclaw/workspace/` | OpenClaw workspace adapter (see [../openclaw/README.md](../openclaw/README.md)) |

## Install

**One command (any machine):**

```bash
bash ~/git/dotfiles/scripts/link_ai_markdown.sh
```

`~/git/agents` must already be checked out. The linker does not copy instruction text.

**Cursor chat:** *symlink the AI markdown files from dotfiles* (runs the
`link-ai-markdown` skill → same script).

**Ansible:**

```bash
cd ~/git/dotfiles/scripts
ansible-playbook playbook.yml --tags=cursor --ask-become-pass
# stow tag also runs apply_stow.py, which calls the same linker at the end
ansible-playbook playbook.yml --tags=stow --ask-become-pass
```

`link_cursor_rules.sh` is a thin alias for `link_ai_markdown.sh`.

## Why a link script?

`~/.cursor/skills/` and `~/.openclaw/workspace/` already exist with other
content, so GNU stow cannot own those trees. The script symlinks each managed
entry individually and backs up colliding real files under
`~/dotfiles-backup/ai-markdown/`.

Skills load from `~/.cursor/skills/`. Rules apply when the workspace root is
`~/git`. OpenClaw reads `~/.openclaw/workspace/`.

## Usage

```text
implement TJW-242
```

→ **vikunja-ticket** adapter, which follows `~/git/agents/tools/vikunja-ticket.md`.

```text
symlink the AI markdown files from dotfiles
```

→ **link-ai-markdown** skill.
