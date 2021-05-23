# dotfiles
Configuration files meant to make my life easier- maybe yours, too!

# Setup- Aliases
- Add to .bashrc:

## Common (All devices)
```
if [ -f ~/Git/dotfiles/alias/common ]; then
    source ~/Git/dotfiles/alias/common
fi
```

## Windows
```
if [ -f ~/Git/dotfiles/alias/windows ]; then
    source ~/Git/dotfiles/alias/windows
fi
```

# Vim
- In your .vimrc file, add `so ~/Git/dotfiles/vimrc`
