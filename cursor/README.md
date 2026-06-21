# Cursor config (versioned in dotfiles)

## Layout

| Path in dotfiles | Installed to | Purpose |
|------------------|--------------|---------|
| `.cursor/skills/` | `~/.cursor/skills/` | Agent skills (via **link script**) |
| `cursor/rules/` | `~/git/.cursor/rules/` | Workspace rules (via **link script**) |

## Install

**Ansible** (setup script checklist, or directly):

```bash
cd ~/git/dotfiles/scripts
ansible-playbook playbook.yml --tags=cursor --ask-become-pass
# stow tag runs apply_stow.py (includes cursor link at the end)
ansible-playbook playbook.yml --tags=stow --ask-become-pass
```

**Manual:**

```bash
cd ~/git/dotfiles
./scripts/link_cursor_rules.sh
```

Skills load from `~/.cursor/skills/`. Rules apply when the workspace root is `~/git`.

## Usage

In Cursor chat (Agent mode):

```text
backloggist tjw-242
```

or `implement TJW-242`. The **taiga-ticket** skill runs the workflow.

## Why a link script?

`~/.cursor/skills/` already exists (e.g. `save-to-spotify`), so GNU stow cannot adopt
that directory. Each skill under `dotfiles/.cursor/skills/<name>/` is symlinked
individually.

Rules live under `~/git/.cursor/rules/` because Cursor reads project rules from the
workspace root.
