#!/bin/zsh

# Generate NNN_BMS variable from the file with $HOME expansion
if [[ -f "$BOOKMARKS_FILE" ]]; then
    export NNN_BMS=$(awk -F':' -v HOME="$HOME" '{
        gsub("\\$HOME", HOME, $2);          # Replace $HOME with actual home path
        gsub("^~", HOME, $2);              # Replace ~ with home path
        printf("%s:%s;", $1, $2);
    }' "$BOOKMARKS_FILE")
else
    echo "Bookmarks file not found: $BOOKMARKS_FILE"
fi
