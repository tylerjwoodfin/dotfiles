# iTerm2 Preferences

iTerm2 loads preferences from this folder (configured via *Preferences → General → Load preferences from a custom folder or URL*).

- **No symlink**: `~/Library/Preferences/com.googlecode.iterm2.plist` is a small bootstrap file (not from this repo) that points iTerm2 here.
- **Settings persist**: iTerm2 reads and writes directly to this folder.
- **Tracked in git**: Changes to iTerm2 settings appear as changes in this repo.

## First-time setup (or migration from old symlinked plist)

Run `apply_stow.py`—it configures the bootstrap automatically on macOS:

```bash
python3 ~/git/dotfiles/scripts/apply_stow.py
```

Or run setup with the "iterm2" option. You may need to restart iTerm2 after the first run.
