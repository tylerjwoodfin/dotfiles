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
export log=$logpath/cabinet/$(date +%Y-%m-%d)/LOG_DAILY_$(date +%Y-%m-%d).log

# NNN exports
if [[ " ${DOTFILES_OPTS[@]} " =~ " nnn " ]]; then
    export NNN_OPTS="eH"
    export NNN_PLUG="f:fzcd"
    export NNN_OPENER="$HOME/.config/nnn/nvim-opener.sh"
fi

# expand aliases to sudo
alias sudo='sudo '

# Editor configuration
export EDITOR='nvim'

# Git configuration
git config --global push.default current

# show git branch info in prompt
autoload -Uz vcs_info
precmd() { vcs_info } # launcher-hidden

# Format the vcs_info_msg_0_ variable
zstyle ':vcs_info:git:*' formats '%b'

# Set up the prompt (with git branch name)
setopt PROMPT_SUBST

PROMPT='%m -> %1~%F{green}${vcs_info_msg_0_:+(${vcs_info_msg_0_})}%F{white}$ '

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
# change dir and list
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

# git commit with branch name
function gcam() {
    branch=$(git symbolic-ref --short HEAD)
    branch=${branch#*/}
    git add -A && git commit -m "$branch: $*"
}

# git create release branch
function gbr() {
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

# git create and push tag
function gtag() {
  tag="$1"

  # Checkout main or master
  if git rev-parse --verify main >/dev/null 2>&1; then
    git checkout main
  else
    git checkout master
  fi

  git pull

  if [ -z "$tag" ]; then
    if [ -f package.json ]; then
      tag=$(jq -r .version package.json)
    elif [ -f setup.cfg ]; then
      tag=$(grep -E "^version\s*=" setup.cfg | head -n1 | awk -F= "{print \$2}" | xargs)
    else
      echo "No tag provided and neither package.json nor setup.cfg found."
      return 1
    fi
  fi

  git tag -a "$tag" -m "Release $tag"
  git push --tags
}

# if you've committed to the wrong branch, this will help you fix it
function wrong-branch() {
    
    # Get current branch name
    local old_branch=$(git symbolic-ref --short HEAD)
    
    # Check if upstream branch exists
    if git rev-parse --abbrev-ref @{u} >/dev/null 2>&1; then
        # Upstream exists, count commits ahead of upstream
        local unpushed_count=$(git rev-list --count @{u}..HEAD)
        if [[ $unpushed_count -eq 0 ]]; then
            echo "No unpushed commits found on branch '$old_branch'."
            return 1
        else
            echo "Found $unpushed_count unpushed commit(s) on branch '$old_branch'."
            read "correct_branch?Enter the correct branch name: "
        fi
    else
        # No upstream branch - check if there are any commits on this branch
        # by comparing to main/master
        local base_branch=""
        if git rev-parse --verify main >/dev/null 2>&1; then
            base_branch="main"
        elif git rev-parse --verify master >/dev/null 2>&1; then
            base_branch="master"
        fi
        
        if [[ -n "$base_branch" ]]; then
            local commit_count=$(git rev-list --count ${base_branch}..HEAD 2>/dev/null || echo "0")
            if [[ $commit_count -eq 0 ]]; then
                echo "No commits found on branch '$old_branch' (compared to $base_branch)."
                return 1
            else
                echo "Found $commit_count commit(s) on branch '$old_branch' (not on $base_branch)."
                read "correct_branch?Enter the correct branch name: "
            fi
        else
            # Can't determine base branch, just ask
            echo "Branch '$old_branch' has no upstream. Unable to determine commit count."
            read "correct_branch?Enter the correct branch name: "
        fi
    fi
    
    # Validate input
    if [[ -z "$correct_branch" ]]; then
        echo "No branch name provided. Aborting."
        return 1
    fi
    
    # Create new branch with correct name from current position
    echo "Creating new branch '$correct_branch' with your commits..."
    git branch "$correct_branch" || { echo "Error creating branch"; return 1; }
    
    # Switch to new branch
    echo "Switching to '$correct_branch'..."
    git checkout "$correct_branch" || { echo "Error switching branches"; return 1; }
    
    # Ask if user wants to reset the old branch
    echo ""
    read "reset_old?Do you want to reset '$old_branch' to match remote? (y/n): "
    if [[ "$reset_old" == "y" ]]; then
        git checkout "$old_branch" || { echo "Error switching back to old branch"; return 1; }
        git reset --hard @{u} || { echo "Error resetting branch"; return 1; }
        git checkout "$correct_branch"
        echo "Successfully moved commits to '$correct_branch' and reset '$old_branch'."
    else
        echo "Successfully moved commits to '$correct_branch'. Old branch '$old_branch' left unchanged."
    fi
}

# Note editing
# edit note file
vn() {
    [[ $# -eq 0 ]] && return

    filename="$*"
    filename="${filename%%.md}"

    if [[ "$(uname)" == "Darwin" ]]; then
        home_prefix_to_replace="/home/"
        home_prefix_replacement="/Users/"
    else
        home_prefix_to_replace="/Users/"
        home_prefix_replacement="/home/"
    fi

    if [[ "$filename" == /* ]]; then
        local_path="${filename/$home_prefix_to_replace/$home_prefix_replacement}.md"
    else
        local_path="$notes/$filename.md"
    fi

    if [[ -f "$local_path" ]]; then
        nvim "$local_path"
    else
        case "$HOST" in
            cloud)
                fallback="rainbow"
                ;;
            *)
                fallback="cloud"
                ;;
        esac
        echo "Checking $fallback..."
        $fallback vn "$*"
    fi
}

# Utility functions

# learn about a command
cheat() { 
  local query="$*"
  local encoded_query=$(echo "$query" | sed 's/ /%20/g')
  curl "cheat.sh/$encoded_query"
}

# Remind functions
# First unalias all functions that might conflict with aliases
unalias rmm rmmt rmmy rmmty rmml plex shorten 2>/dev/null || true

# reminder
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

# reminder for tomorrow
rmmty() {
    rmm --save --when "tomorrow" --title "$@"
}

# reminder for tomorrow
rmmt() {
    remind --title "$*" --when "tomorrow"
}

# save reminder
rmmy() {
    rmm --save "$@"
}

# reminder for later
rmml() {
    remind --title "$*" --when "later"
}

# download yt to plex
plex() {
    python3 ~/git/tools/youtube/main.py video "$@" -d ~/syncthing/video/YouTube
}

# Ollama
# run llama model
llama() {
  local input="$*"
  ollama run llama3:latest "$input"
}

# URL shortening
# shorten url
shorten() {
  if [ -z "$SHORTEN_TOKEN" ]; then
    echo "Set SHORTEN_TOKEN (export SHORTEN_TOKEN=...)" >&2
    return 1
  fi
  if [ -z "$1" ]; then
    echo "usage: short <url> [slug]" >&2
    return 1
  fi
  local endpoint="https://tyler.cloud/s/api/shorten"
  if [ -n "$2" ]; then
    body="{\"url\":\"$1\",\"slug\":\"$2\"}"
  else
    body="{\"url\":\"$1\"}"
  fi
  curl -fsS -X POST "$endpoint" \
    -H "Authorization: Bearer $SHORTEN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$body"
}

# ----------------------
# ALIASES
# ----------------------

# System aliases
alias ls='ls -hal --color' # list
alias cal='cal -B1 -A1; echo -e "\nUse ncal to display horizontally"' # calendar
alias ncal='cal -3' # calendar horizontal
# use nvim editor
alias vim='nvim' # launcher-hidden
# exit shell
alias x='exit' # launcher-hidden
# clear screen
alias cc='clear' # clear
# go back directory
alias b='cd ../' # back

# Directory navigation aliases
alias cdh='cd ~' # home
alias cdg='cd ~/git' # git
alias cdc='cd ~/git/cabinet' # cabinet
alias cddo='cd ~/git/dotfiles' # dotfiles
alias cdrm='cd ~/git/remindmail' # remindmail
alias cdto='cd ~/git/tools' # tools
alias cdw='cd ~/git/tyler.cloud' # tyler.cloud
alias cdbe='cd ~/git/backend' # backend
alias cds='cd ~/syncthing' # syncthing
alias cdd='cd ~/docker' # docker

# Git aliases
alias glog='git log --graph --pretty=format:"%Cred%h%Creset %an: %s - %Creset %C(yellow)%d%Creset %Cgreen(%cr)%Creset" --abbrev-commit --date=relative' # git log
alias gcm='git commit -m' # git commit
alias gch='git fetch && git checkout' # git fetch/checkout
alias gb='git checkout -b' # git new branch
alias gs='git status' # git status
alias gclean='git branch --merged | egrep -v "(^\*|master|dev|main)" | xargs git branch -d' # remove old branches
alias gd='git diff' # git diff
alias gdd='git diff develop' # git diff develop
alias gp='git pull' # git pull

# Tool script aliases
alias diary='python3 ~/git/tools/diary/main.py' # diary
alias yt='python3 ~/git/tools/youtube/main.py' # youtube downloader
alias pitest='python3 ~/git/testfolder/test.py' # test python
alias notes='nnn ~/syncthing/md/notes' # open notes
alias docs='nnn ~/syncthing/md/docs' # open docs
alias work='nnn ~/syncthing/md/work' # open work
alias lofi='zsh ~/git/tools/lofi.sh' # 🎧
alias bluesky='python3 ~/git/tools/bluesky/main.py' # start post
alias lifelog='python3 ~/git/tools/lifelog/main.py' # log event
alias foodlog='python3 ~/git/tools/foodlog/main.py' # log food
alias cabbie='python3 ~/git/tools/cabbie/main.py' # ai commands

# launcher function
unalias l 2>/dev/null || true
l() {
    # Create a temporary file for the command
    local cmd_file=$(mktemp)
    
    # Run the launcher with the temp file path
    python3 ~/git/dotfiles/launcher.py "$cmd_file"
    
    # Read and execute the command if it exists
    if [[ -f "$cmd_file" && -s "$cmd_file" ]]; then
        command=$(cat "$cmd_file")
        rm "$cmd_file"
        if [[ -n "$command" ]]; then
            eval "$command"
        fi
    else
        rm "$cmd_file"
    fi
}


# These are now functions, not aliases
alias rmmsl='rmm --later' # remind later
alias rmme='remind --edit' # edit reminders
alias rmmst='remind --show-tomorrow' # show tomorrow
alias rmmsw='remind --show-week' # show week
alias one-hour-of-distraction='python3 /home/tyler/git/tools/pihole/one_hour_of_distraction.py' # unblock pihole

# 'not-cloud' aliases
if [[ " ${DOTFILES_OPTS[@]} " =~ " not-cloud " ]]; then
    cloud_commands=(
        "remind" "rmm" "rmmt" "rmmy" "rmmty" "rmml" "rmmsl" "shorten" \
        "diary" "turn" "notes" "docs" "work" "n" "v" "one-hour-of-distraction" \
        "plex" "addjira" "addshopping" "bluesky" "lifelog" "foodlog"
    )

    for cmd in "${cloud_commands[@]}"; do
        alias "$cmd"="cloud $cmd" # launcher-hidden
    done
fi

# 'phone' aliases
if [[ " ${DOTFILES_OPTS[@]} " =~ " phone " ]]; then
    alias cal="cloud cal" # launcher-hidden
    alias llama="cloud llama" # launcher-hidden
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
