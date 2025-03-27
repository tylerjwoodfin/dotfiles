#!/bin/zsh

# ----------------------
# EXPORTS
# ----------------------

# Directory paths
setopt cdablevars
export notes=$HOME/syncthing/md/notes
export docs=$HOME/syncthing/md/docs
export work=$HOME/syncthing/md/work
export workt=$HOME/syncthing/md/work/todo.md
export logpath=$HOME/syncthing/log
export cabinet=$HOME/syncthing/cabinet/settings.json
export log=$logpath/cabinet/$(date +%Y-%m-%d)/LOG_DAILY_$(date +%Y-%m-%d).log
export sprints=$HOME/syncthing/md/docs/sprints

# NNN exports
if [[ " ${DOTFILES_OPTS[@]} " =~ " nnn " ]]; then
    export NNN_OPTS="eH"
    export NNN_PLUG="f:fzcd"
    export NNN_OPENER="$HOME/.config/nnn/nvim-opener.sh"
fi

# Editor configuration
export EDITOR='nvim'

# Git configuration
git config --global push.default current

# Sprint configuration
if [ -d "$HOME/syncthing/md/docs/sprints" ]; then
  export sprint=$(find "$sprints" -type f -name "sprint [0-9]*.md" | sort -V | tail -n 1)
fi

# NNN configuration
if [[ " ${DOTFILES_OPTS[@]} " =~ " nnn " ]]; then
    BOOKMARKS_FILE="$HOME/.config/nnn/bookmarks.md"

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
fi

# ----------------------
# FUNCTIONS
# ----------------------

# Directory navigation
cdl() { cd "$a"; ls; }

# Git functions
function git() {
    # Check for blocked flags
    function check_flags() {
        for arg in "$@"; do
            if [[ "$arg" == "--no-verify" ]]; then
                echo "The --no-verify flag is blocked."
                return 1
            fi
        done
        return 0
    }

    # Check for prohibited patterns in files being committed
    function check_commit_files() {
        if [[ "$1" == "commit" ]]; then
            # Determine if -a flag is used
            local has_a_flag=false
            for arg in "$@"; do
                if [[ "$arg" == "-a" ]]; then
                    has_a_flag=true
                    break
                fi
            done

            # Get files that would be committed
            if $has_a_flag; then
                # Check all modified and staged files (includes -a behavior)
                files_to_check=$(git diff --name-only)
            else
                # Check only staged files
                files_to_check=$(git diff --cached --name-only)
            fi

            # Check each file for "# DEBUG" or "# debug"
            for file in $files_to_check; do
                if grep -qE '^\s*# DEBUG|^\s*# debug' "$file"; then
                    echo "Commit blocked: '$file' contains '# DEBUG' or '# debug'."
                    return 1
                fi
            done
        fi
        return 0
    }

    # Run all checks
    check_flags "$@" || return 1
    check_commit_files "$@" || return 1

    # Execute the actual git command
    command git "$@"
}

gcam() {
    branch=$(git symbolic-ref --short HEAD)
    branch=${branch#*/}
    git add -A && git commit -m "$branch: $*"
}

gbr() {
  if [ -z "$1" ]; then
    echo "Usage: gbr <release_branch_name>"
    return 1
  fi
  local release_branch="$1"
  echo "Switching to main and pulling latest changes..."
  git checkout main && git pull origin main || { echo "Error updating main"; return 1; }
  echo "Creating and pushing release branch: $release_branch"
  git checkout -b "$release_branch" && git push -u origin "$release_branch" || { echo "Error creating or pushing release branch"; return 1; }
  echo "Release branch '$release_branch' created and pushed successfully."
}

# Sprint management
newsprint() {
    # Extract the current sprint number
    local currentnum=${${sprint:t}//[^0-9]/}
    local nextnum=$((currentnum + 1))
    
    echo "Opening Sprint ${currentnum} to review. Press any key to continue."
    read -k1
    nvim "$sprint"
    
    echo "\nSprint ${currentnum} is closed! Press any key to begin Sprint ${nextnum}."
    read -k1
    
    # Calculate the next sprint number and create the new sprint file path
    local newsprint="$sprints/sprint $nextnum.md"
    
    # Copy the content of the current sprint to the new sprint file
    cp "$sprint" "$newsprint"

    # Generate the new first line and second line content
    local today=$(date "+%B %d, %Y" | tr '[:upper:]' '[:lower:]')
    local twoweeks=$(date -d "+14 days" "+%B %d, %Y" | tr '[:upper:]' '[:lower:]')
    local new_first_line="# sprint ${nextnum}"
    local new_second_line="- ${today} until mid-day ${twoweeks}"

    # Update the first and second lines of the new sprint file
    sed -i "1c\\${new_first_line}" "$newsprint"
    sed -i "2c\\${new_second_line}" "$newsprint"
    
    # Open the new sprint file
    nvim "$newsprint"
    echo "Welcome to Sprint ${nextnum}!"
}

# Note editing
vn() {
    [[ $# -eq 0 ]] && return

    filename="$*"

    if [[ "$(uname)" == "Darwin" ]]; then
        home_prefix_to_replace="/home/"
        home_prefix_replacement="/Users/"
    else
        home_prefix_to_replace="/Users/"
        home_prefix_replacement="/home/"
    fi

    filename="${filename%%.md}"
    
    if [[ "$filename" == /* ]]; then
        nvim "${filename/$home_prefix_to_replace/$home_prefix_replacement}.md"
    else
        nvim "$notes/$filename.md"
    fi
}

# Utility functions
cheat() {
  local query="$*"
  local encoded_query=$(echo "$query" | sed 's/ /%20/g')
  curl "cheat.sh/$encoded_query"
}

# Work todo management
worka() {
    local file_path="$HOME/syncthing/md/work/todo.md"
    local new_task="- [ ] # $*"
    
    awk -v task="$new_task" '
    BEGIN {added = 0}
    {
        if ($0 ~ /^## to do/ && added == 0) {
            print $0
            print task
            added = 1
        } else {
            print $0
        }
    }' "$file_path" > tmpfile && mv tmpfile "$file_path"
}

# Remind functions
rmm() {
    local save=""
    if [[ "$1" == "--save" ]]; then
        save="--save"
        shift
    fi

    local full_input="$*"
    local when=""
    local title=""
    local extra_args=()
    local current_flag=""

    if [[ "$full_input" == *,* ]]; then
        when="${full_input%%,*}"
        full_input="${full_input#*,}"
        when="${when#"${when%%[![:space:]]*}"}"
        when="${when%"${when##*[![:space:]]}"}"
    fi

    local -a words
    local current_word=""
    local in_quotes=false

    for (( i=0; i < ${#full_input}; i++ )); do
        char="${full_input:$i:1}"
        if [[ "$char" == '"' ]]; then
            in_quotes=!$in_quotes
            current_word+="$char"
        elif [[ "$char" == " " && "$in_quotes" == "false" ]]; then
            if [[ -n "$current_word" ]]; then
                words+=("$current_word")
                current_word=""
            fi
        else
            current_word+="$char"
        fi
    done
    if [[ -n "$current_word" ]]; then
        words+=("$current_word")
    fi

    local is_reading_title=true
    for word in "${words[@]}"; do
        if [[ "$word" == --* ]]; then
            is_reading_title=false
            if [[ -n "$current_flag" ]]; then
                extra_args+=("$current_flag")
            fi
            current_flag="$word"
        else
            if $is_reading_title; then
                title+="$word "
            else
                if [[ -n "$current_flag" ]]; then
                    extra_args+=("$current_flag" "\"$word\"")
                    current_flag=""
                else
                    extra_args[-1]="${extra_args[-1]%\"} $word\""
                fi
            fi
        fi
    done

    if [[ -n "$current_flag" ]]; then
        extra_args+=("$current_flag")
    fi

    title="${title#"${title%%[![:space:]]*}"}"
    title="${title%"${title##*[![:space:]]}"}"

    local cmd=("remind")
    [[ -n $save ]] && cmd+=("$save")
    [[ -n $when ]] && cmd+=("--when" "\"$when\"")
    [[ -n $title ]] && cmd+=("--title" "\"$title\"")

    cmd+=("${extra_args[@]}")

    local cmd_string="${cmd[@]}"

    eval $cmd_string
}

rmmty() {
    rmm --save --when "tomorrow" --title "$@"
}

rmmt() {
    remind --title "$*" --when "tomorrow"
}

rmmy() {
    rmm --save "$@"
}

rmml() {
    remind --title "$*" --when "later"
}

# Plex function
plex() {
    python3 ~/git/tools/youtube/main.py video "$@" -d ~/syncthing/video/YouTube
}

# Atlas-man functions
addjira() {
    local title_args=()
    local extra_args=()
    local reading_flag_value=false
    local current_flag=""

    while [[ $# -gt 0 ]]; do
        if $reading_flag_value; then
            extra_args+=("$current_flag" "$1")
            reading_flag_value=false
            current_flag=""
        elif [[ "$1" =~ ^-[-]?[a-zA-Z] ]]; then
            if [[ "$current_flag" != "" ]]; then
                extra_args+=("$current_flag")
            fi
            current_flag="$1"
            reading_flag_value=true
        else
            title_args+=("$1")
        fi
        shift
    done

    if [[ "$current_flag" != "" ]]; then
        extra_args+=("$current_flag")
    fi

    local title="${title_args[*]}"

    atlasman --jira --add-issue "$title" "${extra_args[@]}"
}

addshopping() {
    atlasman --trello --add-card "shopping" "$*"
}

# Ollama function
llama() {
  local input="$*"
  ollama run llama3:latest "$input"
}

# ----------------------
# ALIASES
# ----------------------

# System aliases
alias ls='ls -hal --color'
alias cal='cal -B1 -A1; echo -e "\nUse ncal to display horizontally"'
alias ncal='ncal -B1 -A1'
alias vim='nvim'
alias x='exit'
alias cc='clear'
alias b='cd ../'

# Directory navigation aliases
alias cdh='cd ~'
alias cdg='cd ~/git'
alias cdam='cd ~/git/atlas-man'
alias cdc='cd ~/git/cabinet'
alias cddo='cd ~/git/dotfiles'
alias cdrm='cd ~/git/remindmail'
alias cdto='cd ~/git/tools'
alias cdw='cd ~/git/tyler.cloud'

# Git aliases
alias glog='git log --graph --pretty=format:"%Cred%h%Creset %an: %s - %Creset %C(yellow)%d%Creset %Cgreen(%cr)%Creset" --abbrev-commit --date=relative'
alias gcm='git commit -m'
alias gch='git fetch && git checkout'
alias gb='git checkout -b'
alias gs='git status'
alias gclean='git branch --merged | egrep -v "(^\*|master|dev|main)" | xargs git branch -d'
alias gd='git diff'
alias gdd='git diff develop'
alias gp='git pull'

# Tool script aliases
alias diary='python3 ~/git/tools/diary/main.py'
alias shorten='python3 ~/git/tools/shorten.py'
alias yt='python3 ~/git/tools/youtube/main.py'
alias pitest='python3 ~/git/testfolder/test.py'
alias turn='python3 ~/git/tools/kasalights/main.py'
alias notes='nnn ~/syncthing/md/notes'
alias docs='nnn ~/syncthing/md/docs'
alias work='nnn ~/syncthing/md/work'
alias lofi='bash ~/git/tools/lofi.sh'
alias v='python3 ~/git/voicegpt/main.py'
alias bike='python3 ~/git/tools/bike/price_calculator.py'
alias bluesky='python3 ~/git/tools/bluesky/main.py'
alias lifelog='python3 ~/git/tools/lifelog/main.py'
alias foodlog='python3 ~/git/tools/foodlog/main.py'

# Remind aliases
alias rmmt='rmmt'
alias rmmy='rmmy'
alias rmmty='rmmty'
alias rmml='rmml'
alias rmmsl='rmm --later'
alias rmme='remind --edit'
alias rmmst='remind --show-tomorrow'
alias rmmsw='remind --show-week'
alias one-more-hour='python3 /home/tyler/git/tools/pihole/one_more_hour.py'
alias worka='worka'

# 'not-cloud' aliases
if [[ " ${DOTFILES_OPTS[@]} " =~ " not-cloud " ]]; then
    cloud_commands=(
        "remind" "rmm" "rmmt" "rmmy" "rmmty" "rmml" "rmmsl" "shorten" \
        "diary" "turn" "notes" "docs" "work" "vn" "n" "v" "one-more-hour" \
        "plex" "bike" "addjira" "addshopping" "bluesky" "lifelog" "foodlog"
    )

    for cmd in "${cloud_commands[@]}"; do
        alias "$cmd"="cloud $cmd"
    done

    ## desktop-specific
    alias duplicate="./git/dotfiles/display/monitors-duplicate.sh"
    alias duplicate4k="./git/dotfiles/display/monitors-duplicate4k.sh"
    alias extend="./git/dotfiles/display/monitors-extend.sh"
    alias steamdeck="./git/dotfiles/display/monitors-steamdeck.sh"
fi

# 'phone' aliases
if [[ " ${DOTFILES_OPTS[@]} " =~ " phone " ]]; then
    alias gpt="cloud gpt"
    alias cal="cloud cal"
    alias llama="cloud llama"
fi

# Enable grep colors
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# source other files - keep on the bottom
for opt in "${DOTFILES_OPTS[@]}"; do
    if [[ $opt == "network" ]]; then
        file="$HOME/git/backend/zsh/network.zsh"
    elif [[ "$opt" == "common" ]]; then
        continue
    else
        file="$HOME/git/dotfiles/zsh/$opt"
    fi

    if [[ -f $file ]]; then
        source "$file"
    fi
done