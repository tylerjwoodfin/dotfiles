# OpenClaw workspace (versioned in dotfiles)

Agent-facing OpenClaw markdown lives here and is **symlinked** into
`~/.openclaw/workspace/` by `scripts/link_ai_markdown.sh`.

## Layout

| Path | Linked to | Notes |
|------|-----------|-------|
| `workspace/AGENTS.md` | `~/.openclaw/workspace/AGENTS.md` | Behavior / diary / food / heartbeat |
| `workspace/SOUL.md` | `~/.openclaw/workspace/SOUL.md` | Persona |
| `workspace/IDENTITY.md` | `~/.openclaw/workspace/IDENTITY.md` | Name / vibe |
| `workspace/USER.md` | `~/.openclaw/workspace/USER.md` | Stable user directives |
| `workspace/skills/*` | `~/.openclaw/workspace/skills/*` | OpenClaw skills (diary, food, amazon-grocery, …) |

**Not versioned here:** `DREAMS.md`, `MEMORY.md`, `memory/`, runtime config under
`~/.openclaw/openclaw.json` (secrets).

Plugin **code** stays in `~/git/tools/openclaw/` (diary, food). After a plugin
install, re-run `link_ai_markdown.sh` so workspace skills stay pointed at
dotfiles.

## Apply

```bash
bash ~/git/dotfiles/scripts/link_ai_markdown.sh
```

Or in Cursor: *“symlink the AI markdown files from dotfiles”* (skill
`link-ai-markdown`).
