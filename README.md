# dotfiles

Configuration files meant to make my life easier- maybe yours, too!

Disclaimer: these are unique to my setup; this repo really only exists for my convenience and to inspire others to create their own dotfiles.

## Detailed Setup

```bash
zsh scripts/setup.sh
```

## Quick Setup

Install Stow (macOS):
```bash
brew install stow
```

Install Stow (Linux):
```bash
sudo apt install stow
```

Symlink all dotfiles:
```bash
cd ~/git/dotfiles
stow --target=$HOME .
```

## AI instructions

Reusable agent instructions live in [`~/git/agents`](https://github.com/tylerjwoodfin/agents). This repo owns local setup: Cursor and OpenClaw adapters, symlinks, shell config, and bootstrap scripts. Adapters point at `agents`. They do not copy the instruction text.

```text
agents → dotfiles installs/adapts → Cursor / OpenClaw
```

Stow cannot adopt the live Cursor and OpenClaw trees, so apply adapters with:

```bash
bash ~/git/dotfiles/scripts/link_ai_markdown.sh
```

That requires `~/git/agents` to be checked out. Or ask Cursor: *symlink the AI markdown files from dotfiles*. Details:
[cursor/README.md](cursor/README.md), [openclaw/README.md](openclaw/README.md).

## uBlock Origin
Custom filter lists are LAN-hosted (not in this public repo).

## zsh
- add to `~/.zshrc`:
```bash
export DOTFILES_OPTS=(common network nnn) # adjust as needed; other options: not-cloud, nnn, network, phone
if [ -f $HOME/git/dotfiles/zsh/common.zsh ]; then
    source $HOME/git/dotfiles/zsh/common.zsh
fi
```

### 🔁 About Zsh Aliases / Env Vars

Many aliases and environment variables are pulled from [Cabinet](https://www.github.com/tylerjwoodfin/cabinet) and injected at shell startup.

Example Cabinet config:

```json
{
  "dotfiles": {
    "alias": {
      "common": {
        "ls": "ls -alh"
      },
      "not-cloud": {
        "plex": "cloud plex"
      }
    },
    "export": {
      "common": {
        "notes": "$HOME/syncthing/notes"
      }
    }
  }
}
```

# launcher.py

Command picker for zsh functions and aliases. With no arguments it opens a Textual TUI. With arguments it prints a command for the shell to run, which works over SSH.

## Features

- Fuzzy search over functions, aliases, descriptions, categories, and host
- Preview pane with the full command and host (`local` or `cloud`)
- Categories: `git`, `life-ops`, `docker`, `network` (`git: status` filters to one)
- Recent commands and favorites (`ctrl+f`)
- `# launcher-hidden` commands stay hidden until `ctrl+h`
- Prompted actions: `remind`, `foodlog`, `milestone`, `diary`, `v` (Vikunja), `cdd` (docker project)
- No match offers an optional cabbie row, labeled as an AI path
- `not-cloud` and `phone` overlays show the cloud wrapper; `network` adds SSH hosts

## Usage

```bash
l
l remind milk tomorrow
l foodlog pizza 800
l v buy milk
l cdd plex
l --cabbie show disk free
```

Or directly:

```bash
python3 ~/git/dotfiles/launcher.py
```

## Controls

- **Type**: search. Prefixes: `git:`, `life-ops:`, `docker:`, `network:`
- **↑/↓**: move the highlight (works while the search box is focused)
- **Enter**: run the command, or prompt for arguments
- **Esc**: back out of a prompt, or quit
- **ctrl+h**: show or hide `# launcher-hidden` commands
- **ctrl+f**: toggle a favorite
- **ctrl+c**: quit

## Installation

```bash
pip install -r ~/git/dotfiles/requirements.txt
```

- `textual` — TUI
- `fuzzywuzzy` — fuzzy search
- `python-Levenshtein` — faster fuzzy scoring

## How it Works

1. Parses `zsh/common.zsh` and every overlay `DOTFILES_OPTS` sources
2. Uses the comment above a function, or the inline comment on an alias, as the description
3. Rewrites `not-cloud` / `phone` commands so the preview shows `cloud <name>`
4. Caches the parse in `~/.cache/launcher_cache.pkl` until any sourced file or the opts change
5. Writes the chosen command to a temp file; `l()` evals it in the current shell

## Notes

- The launcher excludes itself (`l`)
- Favorites and recents live in `~/.cache/launcher_usage.pkl`
- Non-interactive `l <words>` does not call cabbie unless you pass `--cabbie`