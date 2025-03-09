#!/bin/zsh

echo "Opening download links in browser..."

# Detect OS type
if [[ "$OSTYPE" == "darwin"* ]]; then
    # MacOS: Use 'open' instead of 'xdg-open'
    open "https://spotify.com/download" >/dev/null 2>&1 &
    open "https://github.com/rustdesk/rustdesk/releases" >/dev/null 2>&1 &
else
    # Debian-based (Ubuntu)
    xdg-open "https://spotify.com/download" >/dev/null 2>&1 &
    xdg-open "https://github.com/rustdesk/rustdesk/releases" >/dev/null 2>&1 &
fi

echo "Done."
exit 0
