---
name: taiga-ticket
description: >-
  Implement Taiga tickets (TJW-###) for Tyler's ~/git workspace: fetch ticket
  from Taiga, pick repo, branch, implement, test, commit, push, open GitHub PR,
  update Taiga. Use when the user says backloggist, tjw-###, TJW-###, implement
  taiga ticket, or fix taiga ticket.
---

# Taiga ticket workflow (Cursor-native)

You implement the ticket directly in the repo. Do **not** import `backloggist`
or `automation.*` — that package is gone. Use `~/git/tools/taiga/ticket.py`.

## When to use

- `backloggist tjw-242` / `backloggist TJW-242`
- `implement TJW-242` / `fix tjw-242`
- Any request to implement a Taiga user story by ref

## Configuration (Cabinet)

Read via `cabinet --get` / life-ops `cabinet_get` (never print secrets):

| Key | Purpose |
|-----|---------|
| `taiga.api_root` | Direct taiga-back API (`http://<bridge-ip>:8000/api/v1`) |
| `taiga.auth_token` | Application token (colon-separated) or JWT |
| `backloggist.github_token` | GitHub PAT with `repo` (also used by `gh auth`) |
| `backloggist.taiga_human_review_status` | Kanban column after fix (default: `Testing`) |

**Stale Docker IPs:** Bridge IPs change when Taiga containers recreate.
`ticket.py` probes Cabinet `taiga.api_root`, then discovers
`taiga-docker-taiga-back-1` via `docker inspect`, then falls back to
`taiga.base_url`. A working root is written back to Cabinet automatically.
Do **not** hard-code `172.25.0.*` in scripts.

Auth: JWT → `Bearer`; application tokens → `Application` (see
`~/git/tools/taiga/main.py`).

## Workflow

### 1. Load the ticket

```bash
python3 ~/git/tools/taiga/ticket.py get TJW-242
```

If attachments are listed, download them:

```bash
cd ~/git/tools/taiga && python3 -c "
from ticket import TaigaClient
c = TaigaClient()
t = c.get_ticket('TJW-242')
print(c.download_attachments(t, '/tmp/tjw-242'))
"
```

### 2. Choose repository

- If the ticket **explicitly names** a path (`~/git/tyler.cloud`, `github.com/.../repo`), work **only** in that repo.
- Otherwise explore `~/git` and touch only repos the ticket requires.
- Default workspace root: `~/git`.
- If the repo has `AGENTS.md`, follow its branch/PR conventions over the defaults below.

### 3. Branch

Default format: `{prefix}/TJW-###-{short-slug}`

Infer prefix from ticket text: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, or `task`.

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

`gh` lives at `~/.local/bin/gh` (PATH must include `~/.local/bin`).

If `gh auth status` fails or warns about login, sync the Cabinet PAT first
(token may lack `read:org`; **repo** scope is enough for PRs):

```bash
python3 ~/git/tools/github/ensure_gh_auth.py
```

```bash
cd <repo>
git push -u origin HEAD
gh pr create --title "TJW-###: title" --body "$(cat <<'EOF'
## Summary
- ...

## Test plan
- [ ] ...
EOF
)"
```

If the repo's `AGENTS.md` says to target a release branch, set `--base` accordingly.

GitHub owner default: `tylerjwoodfin`.

### 7. Update Taiga

Move ticket to human-review column and comment with PR link(s):

```bash
python3 ~/git/tools/taiga/ticket.py finish TJW-242 --comment "$(cat <<'EOF'
Fixed by **Cursor**.

Pull requests:
- https://github.com/...
EOF
)"
```

## Dry-run / plan-only

If the user says "plan" or "dry-run", fetch the ticket and outline the approach
without pushing or updating Taiga unless they ask to proceed.

## Do not

- Import `backloggist` / `automation` (removed).
- Shell out to `codex exec`.
- Skip tests when the repo has them.
- Hard-code Docker bridge IPs for Taiga.
- Push or update Taiga without user approval on ambiguous tickets.
