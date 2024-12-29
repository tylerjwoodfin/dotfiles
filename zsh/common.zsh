#!/bin/zsh

# folders
setopt cdablevars

# aliases and exports, coming from `cabinet`- https://www.github.com/tylerjwoodfin/cabinet
autoload -Uz add-zsh-hook

# hardcode the cabinet alias to `cloud cabinet`` if device is phone
for file in "${DOTFILES_OPTS[@]}"; do
  if [[ "$file" == "phone" ]]; then
    alias cabinet='cloud cabinet'
    break
  fi
done

parse_aliases_and_exports_from_cabinet() {
  # Check if the setup has already been run in this session
  if [[ -n $CABINET_SETUP_DONE ]]; then
    return
  fi

  local cabinet_output

  # Fetch the entire JSON output from cabinet
  cabinet_output=$(cabinet -g dotfiles)

  if [[ -z $cabinet_output ]]; then
    echo "Error: No data returned from cabinet."
    return 1
  fi

  # Process Cabinet data for a specific type (alias or export)
  process_cabinet_data() {
    local type=$1 command_prefix jq_filter commands

    case $type in
      alias)
        command_prefix="alias"
        jq_filter='.alias'
        ;;
      export)
        command_prefix="export"
        jq_filter='.export'
        ;;
      *)
        echo "Error: Invalid type $type. Use 'alias' or 'export'."
        return 1
        ;;
    esac

    # Generate aliases or exports, filtering by DOTFILES_OPTS from .zshrc
    commands=$(printf '%s\n' "$cabinet_output" | jq -r --argjson files "$(printf '%s\n' "${DOTFILES_OPTS[@]}" | jq -Rsc 'split("\n")[:-1]')" "
      $jq_filter | to_entries[] | select(.key as \$k | \$files | index(\$k)) | .value | to_entries[] | 
      select(.key != null and .value != null) |
      \"$command_prefix \" + (.key | @sh) + \"=\" + (.value | @sh)
    ")

    # Execute commands
    if [[ -n $commands ]]; then
      eval "$commands"
    else
      echo "Warning: No $type entries found for provided source files in Cabinet."
    fi
  }

  # Process aliases and exports
  process_cabinet_data alias
  process_cabinet_data export

  # Mark setup as done for this session
  CABINET_SETUP_DONE=1
}

# Delay execution using precmd
add-zsh-hook precmd parse_aliases_and_exports_from_cabinet

# personal sprints
if [ -d "$HOME/syncthing/md/docs/sprints" ]; then
  export sprint=$(find "$sprints" -type f -name "sprint [0-9]*.md" | sort -V | tail -n 1)
fi

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

# Function: Edit a file in $notes with nvim
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

# cheat
function cheat() {
  local query="$*"
  local encoded_query=$(echo "$query" | sed 's/ /%20/g')
  curl "cheat.sh/$encoded_query"
}

# Enable Colors 🎨
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Git functions

# Block certain flags and patterns in git commands
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

git config --global push.default current

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

# remindmail - see https://github.com/tylerjwoodfin/remindmail
rmm() {
    local save=""
    if [[ "$1" == "--save" ]]; then
        save="--save"
        shift
    fi

    # Join all arguments with spaces to process the comma
    local full_input="$*"
    local when=""
    local title=""
    local extra_args=()
    local current_flag=""

    # Split on first comma if it exists
    if [[ "$full_input" == *,* ]]; then
        when="${full_input%%,*}"           # Get everything before first comma
        full_input="${full_input#*,}"      # Get everything after first comma
        # Trim spaces from when
        when="${when#"${when%%[![:space:]]*}"}"
        when="${when%"${when##*[![:space:]]}"}"
    fi

    # Convert the full input string into an array of words
    local -a words
    local current_word=""
    local in_quotes=false

    # Split the input into words, preserving quoted strings
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

    # Process the words array
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
                    # Append to the last argument if no new flag
                    extra_args[-1]="${extra_args[-1]%\"} $word\""
                fi
            fi
        fi
    done

    # Add the last flag if it exists
    if [[ -n "$current_flag" ]]; then
        extra_args+=("$current_flag")
    fi

    # Trim spaces from title
    title="${title#"${title%%[![:space:]]*}"}"
    title="${title%"${title##*[![:space:]]}"}"

    # Build the command with explicit quoting for multi-word arguments
    local cmd=("remind")
    [[ -n $save ]] && cmd+=("$save")
    [[ -n $when ]] && cmd+=("--when" "\"$when\"")
    [[ -n $title ]] && cmd+=("--title" "\"$title\"")

    # Add the extra arguments
    cmd+=("${extra_args[@]}")

    # Convert command array to a single string for printing and execution
    local cmd_string="${cmd[@]}"

    # Run the command
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

worka() {
    # adds to work todo list
    local file_path="$HOME/syncthing/md/work/todo.md"
    local new_task="- [ ] # $*"
    
    # insert the new task below the "## to do" header
    awk -v task="$new_task" '
    BEGIN {added = 0} # Flag to check if task is added
    {
        if ($0 ~ /^## to do/ && added == 0) { # Find the "## to do" header
            print $0 # Print the header
            print task # Print the new task right after the header
            added = 1 # Set the flag to avoid adding task again
        } else {
            print $0 # Print other lines as they are
        }
    }' "$file_path" > tmpfile && mv tmpfile "$file_path"
}

plex() {
    python3 ~/git/tools/youtube/main.py video "$@" -d ~/syncthing/video/YouTube
}

cdl() { 
    cd "$a"; ls; 
}

# atlas-man
addjira() {
    # Initialize arrays for the title and for additional arguments
    local title_args=()
    local extra_args=()
    local reading_flag_value=false
    local current_flag=""

    # Loop through each argument
    while [[ $# -gt 0 ]]; do
        if $reading_flag_value; then
            # This is a value for a flag
            extra_args+=("$current_flag" "$1")
            reading_flag_value=false
            current_flag=""
        elif [[ "$1" =~ ^-[-]?[a-zA-Z] ]]; then
            # If argument starts with - or --, it's a flag
            if [[ "$current_flag" != "" ]]; then
                # Previous flag had no value, add it alone
                extra_args+=("$current_flag")
            fi
            current_flag="$1"
            reading_flag_value=true
        else
            # Not a flag or flag value, add to title
            title_args+=("$1")
        fi
        shift
    done

    # Handle any remaining flag
    if [[ "$current_flag" != "" ]]; then
        extra_args+=("$current_flag")
    fi

    # Join title arguments into a single string
    local title="${title_args[*]}"

    # Call atlasman with the title and extra arguments
    atlasman --jira --add-issue "$title" "${extra_args[@]}"
}

addshopping() {
    atlasman --trello --add-card "shopping" "$*"
}

# ollama
function llama() {
  local input="$*"
  ollama run llama3:latest "$input"
}

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

[ -z "$PS1" ] && return

# Aliases below this line won't be called during interactive sessions (e.g., scripts)
