#!/usr/bin/env python3
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

def main():
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

if __name__ == "__main__":
    main()
