---
name: media
description: >-
  Request movies, TV seasons, and music through Radarr, Sonarr, qBittorrent,
  and Sockseek. Use when Tyler asks Cherry to download, add, or check a movie,
  show, season, song, album, or Spotify link.
user-invocable: false
metadata:
  {
    "openclaw":
      {
        "emoji": "🎬",
        "requires": { "bins": ["python3"] },
      },
  }
---

# Media requests

Cherry does not open Radarr, Sonarr, qBittorrent, or Sockseek. Call the CLI and
repeat its `outcome` to Tyler.

```bash
python3 ~/git/tools/openclaw/media/scripts/media_cli.py --json search-series "The Simpsons"
python3 ~/git/tools/openclaw/media/scripts/media_cli.py --json add-series "The Simpsons" --season current
python3 ~/git/tools/openclaw/media/scripts/media_cli.py --json add-movie "Interstellar"
python3 ~/git/tools/openclaw/media/scripts/media_cli.py --json add-music "Artist - Title" --song
python3 ~/git/tools/openclaw/media/scripts/media_cli.py --json add-music "Artist - Album" --album
python3 ~/git/tools/openclaw/media/scripts/media_cli.py --json status
python3 ~/git/tools/openclaw/media/scripts/media_cli.py --json health
```

## Which backend

- A movie title goes to Radarr (`add-movie`).
- A show, season, or episode goes to Sonarr (`add-series`). Current season is `--season current`.
- A song, album, or Spotify link goes to Sockseek (`add-music`). Use `--album` for albums and playlists, `--song` for a track.
- Download progress is `status` (qBittorrent plus the Sonarr/Radarr queues).

## Outcomes

Say the outcome word from the JSON: `added`, `already_monitored`, `downloading`, `completed`, `no_results`, `backend_unavailable`, `vpn_unavailable`.

Do not claim a download started unless the CLI returned `added` or `downloading`.
