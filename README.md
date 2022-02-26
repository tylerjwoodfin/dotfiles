# dotfiles
Configuration files meant to make my life easier- maybe yours, too!

# Setup- Aliases
- Add to .bashrc:

## Common (All devices)
```
if [ -f ~/git/dotfiles/alias/common ]; then
    source ~/git/dotfiles/alias/common
fi
```

## Windows
```
if [ -f ~/git/dotfiles/alias/windows ]; then
    source ~/git/dotfiles/alias/windows
fi
```

# Pi
```
if [ -f ~/git/dotfiles/alias/pi ]; then
    source ~/git/dotfiles/alias/pi
fi
```

# Vim
- In your .vimrc file, add `so ~/git/dotfiles/dotfiles.vim`
