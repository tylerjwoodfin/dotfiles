# dotfiles

Configuration files meant to make my life easier- maybe yours, too!

# automatic setup

- run `python3 scripts/setup.py`

# manual setup

- Add to .bashrc:

## common (all devices)

```
if [ -f ~/git/dotfiles/alias/common ]; then
    source ~/git/dotfiles/alias/common
fi
```

## desktop

```
if [ -f ~/git/dotfiles/alias/desktop ]; then
    source ~/git/dotfiles/alias/desktop
fi
```

# pi

```
if [ -f ~/git/dotfiles/alias/pi ]; then
    source ~/git/dotfiles/alias/pi
fi
```

# vim

- In your .vimrc file, add `so ~/git/dotfiles/dotfiles.vim`
