#!/usr/bin/env python3
"""
Apply stow configuration and sync BetterTouchTool settings.

This script manages dotfiles using GNU stow, handles conflicts by moving
them to a backup directory, and syncs BetterTouchTool settings bidirectionally.
"""
import subprocess
import re
import os
from pathlib import Path

# Config
HOME = Path.home()
DOTFILES = HOME / "git" / "dotfiles"
BACKUP_DIR = HOME / "dotfiles-backup"

STOW_CMD = [
    "stow",
    "-v",
    "--dotfiles",
    f"--target={HOME}",
    "--restow",
    "--ignore=^\\.git(ignore|config)?$",
    "--ignore=BetterTouchTool",
    ".",
]

# Ensure backup directory exists
BACKUP_DIR.mkdir(exist_ok=True)


def run_stow():
    """Run stow and return its stdout+stderr text."""
    result = subprocess.run(
        STOW_CMD,
        cwd=DOTFILES,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.stdout


def parse_conflicts(output):
    """Extract conflicted file paths from stow output."""
    pattern = re.compile(r"over existing target ([^ ]+)")
    return pattern.findall(output)


def move_conflicts(conflicts):
    """Move conflicting files to backup dir, preserving relative paths."""
    moved = []
    for rel_path in conflicts:
        src = HOME / rel_path
        dest = BACKUP_DIR / rel_path
        if src.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dest)
            moved.append(rel_path)
    return moved


def get_newest_mtime(directory):
    """Get the newest modification time from files in a directory."""
    if not directory.exists():
        return 0

    newest = 0
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = Path(root) / file
            try:
                mtime = filepath.stat().st_mtime
                if mtime > newest:
                    newest = mtime
            except (OSError, FileNotFoundError):
                pass
    return newest


def sync_bettertouchtool():
    """Bidirectionally sync BetterTouchTool settings based on which is newer."""
    hostname = os.uname().nodename
    if hostname != "icecream":
        return None

    library_dir = HOME / "Library" / "Application Support" / "BetterTouchTool"
    repo_dir = DOTFILES / "Library" / "Application Support" / "BetterTouchTool"

    if not library_dir.exists():
        print("BetterTouchTool directory not found in Library, skipping sync.")
        return None

    # Ensure repo directory parent exists
    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    # Get newest modification times
    library_mtime = get_newest_mtime(library_dir)
    repo_mtime = get_newest_mtime(repo_dir)

    # Determine sync direction
    if library_mtime > repo_mtime:
        source = library_dir
        dest = repo_dir
        direction = "Library → Repo"
    else:
        source = repo_dir
        dest = library_dir
        direction = "Repo → Library"

    # If repo doesn't exist yet, always sync from Library
    if not repo_dir.exists():
        source = library_dir
        dest = repo_dir
        direction = "Library → Repo (initial)"

    cmd = ["rsync", "-avh", "--delete", "--progress", f"{source}/", f"{dest}/"]

    try:
        print(f"Syncing BetterTouchTool settings: {direction}")
        result = subprocess.run(cmd, text=True, check=False)
        if result.returncode == 0:
            print(f"✓ BetterTouchTool settings synced: {direction}")
            return True
        print(
            f"✗ Failed to sync BetterTouchTool settings (exit code: {result.returncode})"
        )
        return False
    except FileNotFoundError:
        print("✗ rsync command not found")
        return False
    except OSError as e:
        print(f"✗ Error syncing BetterTouchTool: {e}")
        return False


def main():
    """Main function to apply stow and handle conflicts."""
    all_moved = []
    while True:
        output = run_stow()
        conflicts = parse_conflicts(output)
        if not conflicts:
            break
        moved = move_conflicts(conflicts)
        all_moved.extend(moved)

    if all_moved:
        print("Moved the following conflicting files to ~/dotfiles-backup:\n")
        for f in all_moved:
            print(f"  {f}")
    else:
        print("No conflicts found. Stow completed cleanly.")

    # Sync BetterTouchTool settings if on icecream
    sync_bettertouchtool()


if __name__ == "__main__":
    main()
