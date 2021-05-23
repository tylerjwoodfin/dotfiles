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

# Pi
```
if [ -f ~/Git/dotfiles/alias/pi ]; then
    source ~/Git/dotfiles/alias/pi
fi
```

# Vim
- In your .vimrc file, add `so ~/Git/dotfiles/vimrc`
