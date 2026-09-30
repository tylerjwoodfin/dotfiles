# Cursor + OpenClaw AI config (versioned in dotfiles)

## Layout

| Path in dotfiles | Installed to | Purpose |
|------------------|--------------|---------|
| `.cursor/skills/` | `~/.cursor/skills/` | Cursor Agent skills |
| `cursor/rules/` | `~/git/.cursor/rules/` | Workspace rules (when root is `~/git`) |
| `openclaw/workspace/` | `~/.openclaw/workspace/` | OpenClaw agent markdown + skills |

Operator docs for the homelab live outside this repo at
`~/syncthing/notes/docs/selfhosted/`. The **selfhosted-docs** Cursor rule
(and OpenClaw `AGENTS.md`) tell agents to consult that folder.

## Install

**One command (any machine):**

```bash
bash ~/git/dotfiles/scripts/link_ai_markdown.sh
```

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
backloggist tjw-242
```

or `implement TJW-242` → **vikunja-ticket** skill.

```text
symlink the AI markdown files from dotfiles
```

→ **link-ai-markdown** skill.
