---
name: homeassistant
description: >-
  Access and update Tyler's Home Assistant (dashboards, entities, Lovelace)
  via the REST/WebSocket API. Use when the user mentions Home Assistant, HA,
  Lovelace, dashboards, or homeassistant.local / 192.168.1.25:8123.
---

# Home Assistant

HA runs on a **separate LAN node**, not on `cloud`. Edit it through the API;
there is no SSH to the box from here.

## Reachability

| URL | Notes |
|-----|--------|
| `http://192.168.1.25:8123` | Use this from `cloud` and over WireGuard |
| `http://homeassistant.local:8123` | mDNS only — **fails over VPN** and often on `cloud` |
| `https://…:8123` | Wrong — HA serves **HTTP** on 8123 |

Compose stub on this machine (`~/git/docker/homeassistant`) is not the running
instance; config lives on the HA host.

## Auth (Cabinet)

| Key | Purpose |
|-----|---------|
| `keys.homeassistant` | Long-lived access token |

Read the token with system Python/`cabinet` (life-ops `cabinet_get` **redacts**
secrets). Never print the token in chat.

```bash
export HA_TOKEN="$(python3 -c "from cabinet import Cabinet; print(Cabinet().get('keys','homeassistant'))")"
export HA_URL="http://192.168.1.25:8123"
```

Smoke test: `GET $HA_URL/api/` with `Authorization: Bearer $HA_TOKEN` → 200.

## Editing Lovelace dashboards

REST `/api/lovelace/*` returns 404 on this install. Use the **WebSocket** API:

1. Connect to `ws://192.168.1.25:8123/api/websocket`
2. Auth with the token
3. `lovelace/dashboards/list` → dashboards
4. `lovelace/config` (optional `url_path`) → full config
5. Mutate JSON → `lovelace/config/save` with `config`

Overview dashboard is storage-mode (`url_path` `lovelace` / default). Prefer a
venv with `websockets` if the system Python lacks it (`python3 -m venv …`).

### PoC note

**Humidity Over Time** (`statistics-graph` on the Home view) supports per-entity
`color` (e.g. `yellow` / `white`). Entity entries can be strings or
`{entity, color, name}` objects.

## Rules

- Prefer IP over `.local` unless the user is on the LAN with working mDNS.
- Do not invent SSH/Samba access; API only unless the user opens another path.
- Keep dashboard edits minimal and confirm after `lovelace/config/save`.
