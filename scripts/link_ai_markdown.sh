#!/usr/bin/env bash
# Symlink Cursor + OpenClaw AI skills/rules/workspace markdown from ~/git/dotfiles.
#
# Usage (any machine with the repo checked out):
#   bash ~/git/dotfiles/scripts/link_ai_markdown.sh
#   DOTFILES=~/git/dotfiles bash ~/git/dotfiles/scripts/link_ai_markdown.sh --dry-run
#
# Cursor agents: when Tyler asks to "symlink the AI markdown files from
# dotfiles", run this script (see .cursor/skills/link-ai-markdown).
set -euo pipefail

DOTFILES="${DOTFILES:-$HOME/git/dotfiles}"
GIT_ROOT="${GIT_ROOT:-$HOME/git}"
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
BACKUP_DIR="${AI_MARKDOWN_BACKUP:-$HOME/dotfiles-backup/ai-markdown}"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: link_ai_markdown.sh [--dry-run] [--help]

Symlinks versioned AI markdown from DOTFILES into the live Cursor/OpenClaw paths.

  Cursor skills   $DOTFILES/.cursor/skills/*  ->  ~/.cursor/skills/
  Cursor rules    $DOTFILES/cursor/rules/*.mdc ->  $GIT_ROOT/.cursor/rules/
  OpenClaw docs   $DOTFILES/openclaw/workspace/{AGENTS,SOUL,IDENTITY,USER}.md
                  ->  ~/.openclaw/workspace/
  OpenClaw skills $DOTFILES/openclaw/workspace/skills/*  ->  ~/.openclaw/workspace/skills/

Env:
  DOTFILES           default: ~/git/dotfiles
  GIT_ROOT           default: ~/git
  OPENCLAW_HOME      default: ~/.openclaw
  AI_MARKDOWN_BACKUP default: ~/dotfiles-backup/ai-markdown
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -d "$DOTFILES" ]]; then
  echo "error: DOTFILES not found: $DOTFILES" >&2
  exit 1
fi

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "dry-run: $*"
  else
    "$@"
  fi
}

backup_if_real() {
  # If path exists and is not already a symlink, move it aside once.
  local path="$1"
  if [[ -e "$path" || -L "$path" ]]; then
    if [[ -L "$path" ]]; then
      return 0
    fi
    local stamp
    stamp="$(date +%Y%m%d-%H%M%S)"
    local dest="$BACKUP_DIR/${stamp}-$(basename "$path")"
    run mkdir -p "$BACKUP_DIR"
    echo "backup $path -> $dest"
    run mv "$path" "$dest"
  fi
}

link_path() {
  local src="$1" dest="$2"
  if [[ ! -e "$src" ]]; then
    echo "skip missing source: $src" >&2
    return 0
  fi
  run mkdir -p "$(dirname "$dest")"
  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ -L "$dest" ]]; then
      local current
      current="$(readlink "$dest" || true)"
      if [[ "$current" == "$src" ]]; then
        echo "ok $dest"
        return 0
      fi
    else
      backup_if_real "$dest"
    fi
  fi
  run ln -sfn "$src" "$dest"
  echo "linked $dest -> $src"
}

link_children() {
  local src_dir="$1" dest_dir="$2" label="$3"
  if [[ ! -d "$src_dir" ]]; then
    echo "skip $label: missing $src_dir" >&2
    return 0
  fi
  run mkdir -p "$dest_dir"
  local linked=0
  local item name
  for item in "$src_dir"/*; do
    [[ -e "$item" ]] || continue
    name="$(basename "$item")"
    # Skip hidden / backup noise
    [[ "$name" == .* ]] && continue
    link_path "$item" "$dest_dir/$name"
    linked=$((linked + 1))
  done
  if [[ "$linked" -eq 0 ]]; then
    echo "no entries to link under $src_dir" >&2
  fi
}

echo "==> Cursor skills"
link_children "$DOTFILES/.cursor/skills" "$HOME/.cursor/skills" "cursor skills"

echo "==> Cursor workspace rules"
if [[ -d "$DOTFILES/cursor/rules" ]]; then
  run mkdir -p "$GIT_ROOT/.cursor/rules"
  for rule in "$DOTFILES/cursor/rules"/*.mdc; do
    [[ -f "$rule" ]] || continue
    name="$(basename "$rule")"
    link_path "$rule" "$GIT_ROOT/.cursor/rules/$name"
  done
fi

echo "==> OpenClaw workspace markdown"
OC_SRC="$DOTFILES/openclaw/workspace"
OC_DEST="$OPENCLAW_HOME/workspace"
if [[ -d "$OC_SRC" ]]; then
  run mkdir -p "$OC_DEST"
  for name in AGENTS.md SOUL.md IDENTITY.md USER.md; do
    if [[ -f "$OC_SRC/$name" ]]; then
      link_path "$OC_SRC/$name" "$OC_DEST/$name"
    fi
  done
  echo "==> OpenClaw workspace skills"
  link_children "$OC_SRC/skills" "$OC_DEST/skills" "openclaw skills"
else
  echo "skip openclaw: missing $OC_SRC" >&2
fi

echo "done."
