#!/bin/zsh

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure playbook.yml exists
PLAYBOOK="$SCRIPT_DIR/playbook.yml"
if [ ! -f "$PLAYBOOK" ]; then
    echo "Error: playbook.yml not found in $SCRIPT_DIR"
    exit 1
fi

# Function to install Ansible if missing
install_ansible() {
    echo "Ansible is not installed."
    
    if whiptail --yesno "Ansible is required to run this setup. Do you want to install it now?" 10 60; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "Installing Ansible via Homebrew..."
            brew install ansible || { echo "Failed to install Ansible."; exit 1; }
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "Installing Ansible via APT..."
            sudo apt update && sudo apt install -y ansible || { echo "Failed to install Ansible."; exit 1; }
        else
            echo "Unsupported OS. Please install Ansible manually."
            exit 1
        fi
    else
        echo "Ansible is required. Exiting."
        exit 1
    fi
}

# Check if Ansible is installed, install if missing
if ! command -v ansible-playbook &> /dev/null; then
    install_ansible
fi

# Determine system info
OS_FAMILY=$(uname)
if [[ "$OS_FAMILY" == "Darwin" ]]; then
    ANSIBLE_OS_FAMILY="Darwin"
elif [[ -f "/etc/os-release" ]]; then
    ANSIBLE_OS_FAMILY=$(grep -oP '^ID=\K.*' /etc/os-release | tr -d '"')
    [[ "$ANSIBLE_OS_FAMILY" == "ubuntu" || "$ANSIBLE_OS_FAMILY" == "debian" ]] && ANSIBLE_OS_FAMILY="Debian"
else
    echo "Unsupported OS."
    exit 1
fi

# Extract tag-name pairs while handling Zsh syntax
declare -A TAGS_MAP
CURRENT_TAGS=()
CURRENT_NAME=""
SKIP_TASK=false

while IFS= read -r LINE; do
    # Extract task name
    if echo "$LINE" | grep -qE '^\s*- name:'; then
        CURRENT_NAME=$(echo "$LINE" | sed -E 's/^\s*- name:\s*//')
        SKIP_TASK=false  # Reset skip flag

    # Extract tags
    elif echo "$LINE" | grep -qE '^\s*tags:'; then
        TAG_LINE=$(echo "$LINE" | sed -E 's/^\s*tags:\s*//')
        TAG_LINE=$(echo "$TAG_LINE" | tr -d '[]')  # Remove square brackets
        CURRENT_TAGS=("${(@s/, /)TAG_LINE}")  # Zsh-specific array splitting

    # Check "when" condition
    elif echo "$LINE" | grep -qE '^\s*when:'; then
        CONDITION=$(echo "$LINE" | sed -E 's/^\s*when:\s*//')
        if echo "$CONDITION" | grep -qE 'ansible_os_family\s*==\s*"([^"]+)"'; then
            REQUIRED_OS=$(echo "$CONDITION" | sed -E 's/.*ansible_os_family\s*==\s*"([^"]+)".*/\1/')
            [[ "$REQUIRED_OS" != "$ANSIBLE_OS_FAMILY" ]] && SKIP_TASK=true
        fi
    fi

    # If we have both name and tags, store them unless skipped
    if [[ -n "$CURRENT_NAME" && "${#CURRENT_TAGS[@]}" -gt 0 && "$SKIP_TASK" == false ]]; then
        for TAG in "${CURRENT_TAGS[@]}"; do
            TAGS_MAP[$TAG]+="$CURRENT_NAME"$'\n'
        done
        CURRENT_NAME=""
        CURRENT_TAGS=()
    fi
done < "$PLAYBOOK"

# Build whiptail checklist
CHECKLIST=()
for TAG in "${(@k)TAGS_MAP}"; do  # Iterate over keys in Zsh associative array
    NAME="${TAGS_MAP[$TAG]}"
    NAME="${NAME%$'\n'}"  # Trim trailing newline
    CHECKLIST+=("$TAG" "$NAME" "OFF")
done

# Run whiptail selection menu
SELECTED=$(whiptail --title "Select Setup Options" --checklist \
"Choose items to install (use Space to select, Enter to confirm):" \
20 78 15 "${CHECKLIST[@]}" 3>&1 1>&2 2>&3)

# Check if anything was selected
if [ -z "$SELECTED" ]; then
    echo "No options selected. Exiting."
    exit 1
fi

# Convert selected tags to comma-separated list for Ansible
SELECTED_TAGS=$(echo "$SELECTED" | tr ' ' ',' | tr -d '"')

# Debug output
echo "Running Ansible with tags: $SELECTED_TAGS"

# Run Ansible playbook with selected tags
echo "Running command: ansible-playbook $PLAYBOOK --tags=\"$SELECTED_TAGS\" --ask-become-pass --check"
ansible-playbook "$PLAYBOOK" --tags="$SELECTED_TAGS" --ask-become-pass
