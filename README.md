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