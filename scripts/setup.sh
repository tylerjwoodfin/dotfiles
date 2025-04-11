#!/bin/zsh

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Debug function
debug() {
    echo "DEBUG: $1"
}

# Detect OS type
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="MacOS"
    debug "Detected MacOS platform"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Ubuntu"
    debug "Detected Ubuntu platform"
else
    PLATFORM="Unknown"
    debug "Unknown platform: $OSTYPE"
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to install Homebrew if missing
install_homebrew() {
    if ! command_exists brew; then
        echo "Homebrew is not installed."
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || { echo "Failed to install Homebrew."; exit 1; }
        
        # Add Homebrew to PATH for the current session
        if [[ -x /opt/homebrew/bin/brew ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -x /usr/local/bin/brew ]]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    else
        debug "Homebrew is already installed at $(which brew)"
    fi
}

# Function to install whiptail if missing
install_whiptail() {
    if ! command_exists whiptail; then
        echo "whiptail is not installed."
        
        if [[ "$PLATFORM" == "MacOS" ]]; then
            install_homebrew
            echo "Installing whiptail via Homebrew..."
            brew install newt || { echo "Failed to install whiptail."; exit 1; }
        elif [[ "$PLATFORM" == "Ubuntu" ]]; then
            echo "Installing whiptail via APT..."
            sudo apt update && sudo apt install -y whiptail || { echo "Failed to install whiptail."; exit 1; }
        else
            echo "Unsupported OS. Please install whiptail manually."
            exit 1
        fi
    else
        debug "whiptail is already installed"
    fi
}

# Function to install Ansible if missing
install_ansible() {
    if ! command_exists ansible-playbook; then
        echo "Ansible is not installed."
        
        if [[ "$PLATFORM" == "MacOS" ]]; then
            install_homebrew
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
        debug "Ansible is already installed"
    fi
}

# Check if whiptail is installed, install if missing
install_whiptail

# Check if Ansible is installed, install if missing
install_ansible

# Ensure playbook.yml exists
SETUP_YML="$SCRIPT_DIR/playbook.yml"
if [ ! -f "$SETUP_YML" ]; then
    echo "Error: playbook.yml not found in $SCRIPT_DIR"
    exit 1
fi

# Define checklist items with filtering based on PLATFORM
OPTIONS=()

# Core system setup
[[ "$PLATFORM" == "MacOS" ]] && OPTIONS+=("homebrew" "MacOS: Install Homebrew" OFF)
[[ "$PLATFORM" == "MacOS" ]] && OPTIONS+=("mac_defaults" "MacOS: Set defaults" OFF)
[[ "$PLATFORM" == "MacOS" ]] && OPTIONS+=("iterm2" "MacOS: Install, Configure iTerm2" OFF)

# Package installation
OPTIONS+=("cli" "Install CLI tools (git, docker, etc.)" OFF)
OPTIONS+=("gui" "Install GUI apps (Browsers, VS Code, Syncthing)" OFF)

# Configuration
OPTIONS+=("ssh" "Setup SSH (does not overwrite existing keys)" OFF)
OPTIONS+=("git" "Setup Git (user email, .gitignore, etc.)" OFF)
OPTIONS+=("vim" "Link vim.lua to Neovim init.lua" OFF)
OPTIONS+=("zsh" "Set the default shell to ZSH" OFF)
OPTIONS+=("zshrc" "Add common.zsh to .zshrc" OFF)

# Optional services
OPTIONS+=("pihole" "Install Pihole (overwrites!)" OFF)
OPTIONS+=("python" "Install Cabinet and Remindmail via Pipx" OFF)
[[ "$PLATFORM" == "Ubuntu" ]] && OPTIONS+=("copyq" "Ubuntu: Install CopyQ (clipboard manager)" OFF)

# Additional setup
OPTIONS+=("hostname" "Change system hostname" OFF)
OPTIONS+=("downloads" "Open external app download links" OFF)
OPTIONS+=("borg" "Set BorgBackup passphrase" OFF)
OPTIONS+=("clone" "Clone all GitHub repositories (run SEPARATELY after SSH!)" OFF)

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

# Check for SSH key if SSH setup is selected
if [[ "$SELECTED" == *"ssh"* ]]; then
    if [ ! -f "$HOME/.ssh/id_rsa" ]; then
        echo "No SSH key found. The playbook will generate one for you."
    fi
fi

# Check if SSH is configured for Git
if [[ "$SELECTED" == *"clone"* ]]; then
    if [ ! -f "$HOME/.ssh/id_rsa" ]; then
        whiptail --title "SSH Key Missing" --msgbox "You need to set up SSH first. Please run the setup again with the 'ssh' option selected." 10 78
        exit 1
    fi
    
    whiptail --title "Git Clone Notice" --yesno "The SSH key must have been configured and uploaded to Github. Did you do this?" 10 78
    if [ $? -ne 0 ]; then
        echo "Setup canceled by user."
        exit 1
    fi
fi

# Run Ansible playbook with selected tags
ansible-playbook "$SETUP_YML" --tags="$SELECTED_TAGS" --ask-become-pass

echo "Ansible Setup complete ✅"

# Post-setup tasks
if [[ "$SELECTED" == *"downloads"* ]]; then
    echo "Opening download links in browser..."
    "$SCRIPT_DIR/open_bookmarks.sh"
fi

if [[ "$SELECTED" == *"borg"* ]]; then
    echo "Setting up Borg passphrase..."
    "$SCRIPT_DIR/borg_passphrase.sh"
fi

# Final instructions
if [[ "$SELECTED" == *"ssh"* ]]; then
    echo "🔑 If you just generated a new SSH key, please add it to GitHub:"
    echo "   https://github.com/settings/keys"
    echo "   Then run the setup again with the 'clone' option to clone your repositories."
fi