# USER.md - User Model

Store stable user preferences and profile facts as directives that can guide future sessions.

Use one directive per entry:

```md
<!-- observed: YYYY-MM-DD | status: active -->

- Prefer concise progress updates during implementation work.
```

- Begin each directive with an imperative such as `Always`, `Never`, or `Prefer`.
- Record the observation date and either `active` or `superseded` on the metadata line.
- When a preference changes, mark the old entry `superseded` and rewrite the active directive in place. Never append a contradictory active directive.
- Keep stable communication style, relationships, and active-project context here. Put durable non-profile facts and decisions in `MEMORY.md`.

## Directives

<!-- observed: 2026-09-02 | status: active -->

- Treat a direct request to message an unambiguous recipient as permission to send without a redundant confirmation, including when I delegate the wording or creative details; still ask when required for safety, ambiguity, privacy, destructive actions, or public posts.

## Related

- [Agent workspace](/concepts/agent-workspace)
