---
name: life-ops
description: >-
  Use Tyler's life-ops MCP tools (Cabinet, RemindMail, foodlog, milestone,
  Immich) instead of ad-hoc shell. Trigger when the user asks to get/set Cabinet
  config, save a reminder, log food, add a milestone, or search Immich photos.
---

# Life-ops (Cursor)

Follow `~/git/agents/tools/life-ops.md`.

Discover tools before calling them. Call `GetMcpTools` for server `life-ops` (or pattern `life.?ops|cabinet_get|remind_save`), then `CallMcpTool`.
