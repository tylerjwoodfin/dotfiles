#!/usr/bin/env bash
# Link dotfiles-managed Cursor skills and workspace rules.
set -euo pipefail

DOTFILES="${DOTFILES:-$HOME/git/dotfiles}"
GIT_ROOT="${GIT_ROOT:-$HOME/git}"
SKILLS_SRC="$DOTFILES/.cursor/skills"
SKILLS_DEST="$HOME/.cursor/skills"
RULES_SRC="$DOTFILES/cursor/rules"
RULES_DEST="$GIT_ROOT/.cursor/rules"

link_dir_links() {
  local src="$1" dest="$2" label="$3"
  if [[ ! -d "$src" ]]; then
    echo "skip $label: missing $src" >&2
    return 0
  fi
  mkdir -p "$dest"
  local linked=0
  for item in "$src"/*; do
    [[ -e "$item" ]] || continue
    local name
    name="$(basename "$item")"
    ln -sfn "$item" "$dest/$name"
    echo "linked $dest/$name -> $item"
    linked=$((linked + 1))
  done
  if [[ "$linked" -eq 0 ]]; then
    echo "no entries to link under $src" >&2
  fi
}

link_dir_links "$SKILLS_SRC" "$SKILLS_DEST" "skills"

if [[ -d "$RULES_SRC" ]]; then
  mkdir -p "$RULES_DEST"
  for rule in "$RULES_SRC"/*.mdc; do
    [[ -f "$rule" ]] || continue
    name="$(basename "$rule")"
    ln -sfn "$rule" "$RULES_DEST/$name"
    echo "linked $RULES_DEST/$name -> $rule"
  done
fi
