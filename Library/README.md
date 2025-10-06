# Dotfiles are Managed by Stow
## Tyler, 2025-10-05.

This directory is **symlinked into `~/Library`** using [GNU Stow](https://www.gnu.org/software/stow/).  

Do **not** remove files from this folder without understanding the effects; changes should happen through the source files in the dotfiles repo or via the relevant app’s settings UI.


## What Is Stow?

GNU **Stow** is a simple symlink manager. It lets you organize configuration files (dotfiles) inside a Git repo (like `~/git/dotfiles`) and then *“stow”* them into your home directory or other locations.

For example:
```bash
cd ~/git/dotfiles && stow .
```
will automatically add/update files in ~/Library.

See https://tamerlan.dev/how-i-manage-my-dotfiles-using-gnu-stow/.
