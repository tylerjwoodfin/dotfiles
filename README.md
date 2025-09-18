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

## uBlock Origin
- add `https://raw.githubusercontent.com/tylerjwoodfin/dotfiles/refs/heads/main/uBlock.txt` to uBlock Origin's custom filter list.

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
        "notes": "$HOME/syncthing/md/notes"
      }
    }
  }
}
```

# launcher.py

An interactive TUI launcher for zsh functions and aliases from `common.zsh`.
`
## Features

- **Fuzzy Search**: Type to search through functions and aliases
- **Interactive Navigation**: Use arrow keys to navigate through results
- **Performance Optimized**: Caches parsed commands for fast startup
- **Rich TUI**: Beautiful terminal interface with syntax highlighting

## Usage

Run the launcher with:
```bash
l
```

Or directly:
```bash
python3 ~/git/dotfiles/launcher.py
```

## Controls

- **Type**: Start typing to search for commands
- **↑/↓**: Navigate through results (up to 3 shown)
- **Enter**: Execute the selected command
- **Ctrl+C**: Exit the launcher

## Installation

The launcher requires Python packages that are automatically installed when you run it for the first time:

- `rich` - For the TUI interface
- `fuzzywuzzy` - For fuzzy search
- `python-Levenshtein` - For improved fuzzy search performance

## How it Works

1. Parses `common.zsh` to extract functions and aliases
2. Extracts comments above each function/alias as descriptions
3. Caches the parsed data for fast subsequent launches
4. Provides fuzzy search over command names and descriptions
5. Executes selected commands in the current shell context

## Performance

- **Caching**: Commands are cached in `~/.cache/launcher_cache.pkl`
- **Fast Search**: Uses substring matching first, then fuzzy matching
- **Optimized Parsing**: Only re-parses when the zsh file changes

## Notes

- The launcher excludes itself (`l` alias) from the results
- Commands are executed by sourcing the zsh file and running the function/alias
- The launcher works with both functions and aliases defined in `common.zsh`