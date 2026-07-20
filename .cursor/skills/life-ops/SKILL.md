---
name: life-ops
description: >-
  Use Tyler's life-ops MCP tools (Cabinet, RemindMail, foodlog, milestone,
  Immich) instead of ad-hoc shell. Trigger when the user asks to get/set Cabinet
  config, save a reminder, log food, add a milestone, or search Immich photos.
---

# Life-ops MCP

Prefer the **life-ops** MCP server tools over inventing `python ~/git/tools/...` or `cabinet` one-liners.

## Discover tools first

Call `GetMcpTools` for server `life-ops` (or pattern `life.?ops|cabinet_get|remind_save`) before `CallMcpTool`.

## Tools

| Tool | When |
|------|------|
| `cabinet_get` | Read config/data by path (`quality.cloud`, `taiga api_root`, …). Secrets are redacted. |
| `cabinet_put` | Write a string value. Do **not** put secrets unless the user explicitly provides them. |
| `remind_save` | Schedule a reminder (`title`, `when`, optional `notes`/`tags`). |
| `foodlog_add` | Log food with known calories (`food`, `calories`). Do not prompt interactively. |
| `milestone_add` | Append to `milestones.md` for current year/month. |
| `immich_search` | Search photos. Requires Cabinet `immich.api_url` + `immich.api_key`. |

## Rules

- Never print Cabinet tokens, passwords, or API keys into chat.
- If Immich is unconfigured, tell the user to set the two Cabinet keys (see `~/git/tools/lifeops-mcp/README.md`) instead of guessing URLs.
- For Taiga ticket implementation, keep using the **taiga-ticket** skill; life-ops does not replace it.
- Foodlog without calories: ask the user for a calorie number (or look up from conversation) — do not run the interactive foodlog CLI.
