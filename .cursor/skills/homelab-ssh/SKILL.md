---
name: homelab-ssh
description: >-
  Resolve Tyler's named hosts (rainbow, ice, icecream, cloud) via `which <host>`
  and SSH with that function. Use when the user mentions rainbow, ice,
  icecream, cloud, or asks to run something on those machines.
---

# Homelab SSH hosts

`rainbow`, `ice`, `icecream`, and `cloud` are **zsh functions**, not DNS names
or Tailscale hostnames.

## Resolve access

Always run `which <host>` in zsh before SSHing. Do not hardcode IPs or ports
from memory or an old chat.

```bash
which rainbow
which ice
which icecream
which cloud
```

The function body is the SSH recipe (user, address, port, and any fallback).

## Run commands

Prefer the wrapper that `which` showed:

```bash
rainbow 'hostname'
ice 'systemctl is-active syncthing'
```

Or extract `ssh user@address -p port` from `which` and run it non-interactively.

`ice` and `cloud` try LAN SSH first and fall back to `rainbow` if that check fails.

## Do not

- Invent hostnames or assume Tailscale/mDNS names.
- Skip `which` and reuse an IP from a previous turn.
- Print secrets if a host function file contains tokens.
