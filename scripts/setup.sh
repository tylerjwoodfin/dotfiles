#!/bin/zsh

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detect OS type
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="MacOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Ubuntu"
else
    PLATFORM="Unknown"
fi

# Function to install Ansible if missing
install_ansible() {
    echo "Ansible is not installed."
    
    if whiptail --yesno "Ansible is required to run this setup. Do you want to install it now?" 10 60; then
        if [[ "$PLATFORM" == "MacOS" ]]; then
            echo "Installing Ansible via Homebrew..."
            brew install ansible || { echo "Failed to install Ansible."; exit 1; }
        elif [[ "$PLATFORM" == "Ubuntu" ]]; then
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

# Ensure playbook.yml exists
SETUP_YML="$SCRIPT_DIR/playbook.yml"
if [ ! -f "$SETUP_YML" ]; then
    echo "Error: playbook.yml not found in $SCRIPT_DIR"
    exit 1
fi

# Define checklist items with filtering based on PLATFORM
OPTIONS=()

[[ "$PLATFORM" == "MacOS" ]] && OPTIONS+=("homebrew" "MacOS: Install Homebrew" OFF)
[[ "$PLATFORM" == "MacOS" ]] && OPTIONS+=("mac_defaults" "MacOS: Set defaults" OFF)
OPTIONS+=("cli" "Install CLI tools (git, docker, etc.)" OFF)
OPTIONS+=("gui" "Install GUI apps (Browsers, VS Code, Syncthing)" OFF)
OPTIONS+=("ssh" "Setup SSH (does not overwrite existing keys)" OFF)
OPTIONS+=("git" "Setup Git (user email, .gitignore, etc.)" OFF)
OPTIONS+=("pihole" "Install Pihole (overwrites!)" OFF)
OPTIONS+=("python" "Install Cabinet and Remindmail via Pipx" OFF)
[[ "$PLATFORM" == "Ubuntu" ]] && OPTIONS+=("copyq" "Ubuntu: Install CopyQ (clipboard manager)" OFF)
OPTIONS+=("hostname" "Change system hostname" OFF)
OPTIONS+=("downloads" "Open external app download links" OFF)
OPTIONS+=("borg" "Set BorgBackup passphrase" OFF)
OPTIONS+=("clone" "Clone all GitHub repositories (run SEPARATELY after SSH!)" OFF)
OPTIONS+=("vim" "Link vim.lua to Neovim init.lua" OFF)
OPTIONS+=("zsh" "Set the default shell to ZSH" OFF)
OPTIONS+=("zshrc" "Add common.zsh to .zshrc" OFF)

SELECTED=$(whiptail --title "Select Setup Options" --checklist \
"Choose items to install (use Space to select, Enter to confirm):" 20 78 15 \
"${OPTIONS[@]}" 3>&1 1>&2 2>&3)

# Check if anything was selected
if [ -z "$SELECTED" ]; then
    echo "No options selected. Exiting."
    exit 1
fi

# Convert selected tags to comma-separated list for Ansible
SELECTED_TAGS=$(echo "$SELECTED" | tr ' ' ',' | tr -d '"')

# Debug output
echo "Running Ansible with tags: $SELECTED_TAGS"
echo "If this script fails, please run the following command manually:"
echo "ansible-playbook $SETUP_YML --tags=$SELECTED_TAGS --ask-become-pass -vvv"

# Check if SSH is configured for Git
if [[ "$SELECTED" == *"clone"* ]]; then
    whiptail --title "Git Clone Notice" --yesno "The SSH key must have been configured and uploaded to Github. Did you do this?" 10 78
fi

if [ $? -ne 0 ]; then
    echo "Setup canceled by user."
    exit 1
fi

# Run Ansible playbook with selected tags
ansible-playbook "$SETUP_YML" --tags="$SELECTED_TAGS" --ask-become-pass

echo "Ansible Setup complete ✅"

# 'downloads' -> open_bookmarks_linux.sh
if [[ "$SELECTED" == *"downloads"* ]]; then
    echo "Opening download links in browser..."
    "$SCRIPT_DIR/open_bookmarks.sh"
fi

# 'borg' -> borg_passphrase.sh
if [[ "$SELECTED" == *"borg"* ]]; then
    echo "Setting up Borg passphrase..."
    "$SCRIPT_DIR/borg_passphrase.sh"
fi