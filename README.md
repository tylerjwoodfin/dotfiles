# dotfiles

Configuration files meant to make my life easier- maybe yours, too!

# automatic setup

- run `python3 scripts/setup.py`

# manual setup

- Add to .zshrc:

## common (all devices)

```
if [ -f ~/git/dotfiles/zsh/common ]; then
    source ~/git/dotfiles/zsh/common
fi
```

## desktop

```
if [ -f ~/git/dotfiles/zsh/desktop ]; then
    source ~/git/dotfiles/zsh/desktop
fi
```

# pi

```
if [ -f ~/git/dotfiles/zsh/pi ]; then
    source ~/git/dotfiles/zsh/pi
fi
```

# neovim

- In your `~/.config/nvim/init.lua` file, add `so ~/git/dotfiles/vim.lua`
