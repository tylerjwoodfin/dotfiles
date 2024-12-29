# dotfiles

Configuration files meant to make my life easier- maybe yours, too!

Disclaimer: these are unique to my setup; this repo really only exists for my convenience and to inspire others to create their own dotfiles.

# automatic setup

- run `python3 scripts/setup.py`

# manual setup

## zsh
- add to `~/.zshrc`:
```bash
export DOTFILES_OPTS=(common network nnn) # adjust as needed; other options: not-cloud, nnn, network, phone
if [ -f $HOME/git/dotfiles/zsh/common.zsh ]; then
    source $HOME/git/dotfiles/zsh/common.zsh
fi
```

## neovim
- In your `~/.config/nvim/init.lua` file, add `so ~/git/dotfiles/vim.lua`

# about zsh aliases/environment variables
- Specific aliases and environment variables are stored in [Cabinet](https://www.github.com/tylerjwoodfin/cabinet) and are loaded into the shell at startup.
- Example in Cabinet:
```json
{
    "dotfiles": {
            "alias": {
                "common": {
                    "ls": "ls -alh"
                },
                "not-cloud": {
                    "plex": "cloud plex",
                }
            },
            "export": {
                "common": {
                    "notes": "$HOME/syncthing/md/notes",
                }
            }
    }
}
```