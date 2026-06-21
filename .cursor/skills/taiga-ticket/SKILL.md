---
name: taiga-ticket
description: >-
  Implement Taiga tickets (TJW-###) for Tyler's ~/git workspace: fetch ticket
  from Taiga, pick repo, branch, implement, test, commit, push, open GitHub PR,
  update Taiga. Use when the user says backloggist, tjw-###, TJW-###, implement
  taiga ticket, or fix taiga ticket.
---

# Taiga ticket workflow (Cursor-native)

Replaces the external `backloggist` + Codex CLI pipeline. **You** (the Cursor agent)
implement the ticket directly in the repo.

## When to use

- `backloggist tjw-242` / `backloggist TJW-242`
- `implement TJW-242` / `fix tjw-242`
- Any request to implement a Taiga user story by ref

## Configuration (Cabinet)

Read via `cabinet --get` (never print secrets):

| Key | Purpose |
|-----|---------|
| `taiga.api_root` | Direct API, e.g. `http://172.25.0.8:8000/api/v1` |
| `taiga.auth_token` | Application token (colon-separated) or JWT |
| `backloggist.github_token` | GitHub PAT with `repo` |
| `backloggist.taiga_human_review_status` | Kanban column after fix (default: `Testing`) |

Taiga token auth: JWT uses `Bearer`, application tokens use `Application` (see
`~/git/tools/taiga/main.py`).

## Workflow

### 1. Load the ticket

```bash
python3 <<'PY'
import sys
sys.path.insert(0, "/home/tyler/git/backloggist")
from automation.config import load_config
from automation.taiga_client import TaigaClient
ref = "TJW-242"  # from user message
client = TaigaClient(load_config())
ticket = client.get_ticket(ref)
print(f"ref={ticket.ref}\ntitle={ticket.title}\ndescription=\n{ticket.description}")
PY
```

Download attachments with `TaigaClient.download_attachments(ticket)` when present.

### 2. Choose repository

- If the ticket **explicitly names** a path (`~/git/tyler.cloud`, `github.com/.../repo`), work **only** in that repo.
- Otherwise explore `~/git` and touch only repos the ticket requires.
- Default workspace root: `~/git`.

### 3. Branch

Branch format: `{prefix}/{TJW-###}-{short-slug}`

Infer prefix from ticket text: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, or `task`.
Example: `feat/TJW-242-pointing-showdown-feedback-form`

Create the branch before editing:

```bash
cd <repo> && git checkout -b feat/TJW-242-short-slug
```

### 4. Implement

Follow [ticket-template.md](ticket-template.md) in this skill directory.

- Match existing code style in the target repo.
- Run tests and linting defined by that project.
- Do not scope-creep beyond the ticket.

### 5. Commit

Message format: `TJW-###: short summary` (ticket ref required).

### 6. Push and open PR

Use `gh` when available:

```bash
cd <repo>
git push -u origin HEAD
gh pr create --title "TJW-###: title" --body "## Summary\n...\n\n## Test plan\n- [ ] ..."
```

GitHub owner default: `tylerjwoodfin`. Token from `backloggist.github_token`.

### 7. Update Taiga

Move ticket to human-review column and comment with PR link(s):

```bash
python3 <<'PY'
import sys
sys.path.insert(0, "/home/tyler/git/backloggist")
from automation.config import load_config
from automation.taiga_client import TaigaClient
cfg = load_config()
client = TaigaClient(cfg)
ticket = client.get_ticket("TJW-242")
comment = "Fixed by **Cursor**.\n\nPull requests:\n- https://github.com/..."
client.finish_ticket(ticket, comment)
PY
```

## Dry-run / plan-only

If the user says "plan" or "dry-run", fetch the ticket and outline the approach
without pushing or updating Taiga unless they ask to proceed.

## Do not

- Shell out to `codex exec` (unreliable on headless Linux).
- Skip tests when the repo has them.
- Push or update Taiga without user approval on ambiguous tickets.
