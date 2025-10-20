#!/usr/bin/env python3
"""
Apply stow configuration and sync BetterTouchTool settings.

This script manages dotfiles using GNU stow, handles conflicts by moving
them to a backup directory, and syncs BetterTouchTool settings bidirectionally.
"""
import subprocess
import re
import os
import shutil
from pathlib import Path

# Config
HOME = Path.home()
DOTFILES = HOME / "git" / "dotfiles"
BACKUP_DIR = HOME / "dotfiles-backup"

# Find stow in common locations (needed for cron jobs with limited PATH)
STOW_PATHS = [
    "/opt/homebrew/bin/stow",  # Apple Silicon Mac (Homebrew)
    "/usr/local/bin/stow",      # Intel Mac (Homebrew)
    "/usr/bin/stow",            # Linux (apt/yum/dnf)
    "stow",                     # Fallback to PATH
]

def get_stow_path():
    """Find the stow executable in common locations."""
    for path in STOW_PATHS:
        if path == "stow":
            # Check if it's in PATH
            found = shutil.which("stow")
            if found:
                return found
        elif os.path.exists(path):
            return path
    return None

STOW_EXECUTABLE = get_stow_path()
STOW_CMD = [
    STOW_EXECUTABLE if STOW_EXECUTABLE else "stow",
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


def check_stow_available():
    """Check if stow command is available."""
    return STOW_EXECUTABLE is not None


def run_stow():
    """Run stow and return its stdout+stderr text."""
    try:
        result = subprocess.run(
            STOW_CMD,
            cwd=DOTFILES,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        return result.stdout
    except FileNotFoundError:
        return None


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
    # Check if stow is available
    if not check_stow_available():
        print("✗ Error: stow command not found")
        print("Please install GNU stow:")
        print("  - macOS: brew install stow")
        print("  - Ubuntu/Debian: sudo apt-get install stow")
        print("  - Fedora: sudo dnf install stow")
        return 1
    
    all_moved = []
    while True:
        output = run_stow()
        if output is None:
            print("✗ Error: Failed to run stow command")
            return 1
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
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
