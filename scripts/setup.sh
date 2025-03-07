#!/bin/zsh

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

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

# Ensure setup.yml exists
SETUP_YML="$SCRIPT_DIR/setup.yml"
if [ ! -f "$SETUP_YML" ]; then
    echo "Error: setup.yml not found in $SCRIPT_DIR"
    exit 1
fi

# Create selection using whiptail
SELECTED=$(whiptail --title "Select Setup Options" --checklist \
"Choose items to install (use Space to select, Enter to confirm):" 20 78 15 \
"homebrew" "Install Homebrew (MacOS)" OFF \
"cli" "Install CLI tools (git, docker, etc.)" OFF \
"gui" "Install GUI apps (Browsers, VS Code, Syncthing)" OFF \
"ssh" "Create SSH key if nonexistent" OFF \
"ssh_keys" "Apply shared authorized_keys file" OFF \
"git" "Setup Git (user email, .gitignore, etc.)" OFF \
"pihole" "Install Pihole" OFF \
"python" "Install Python tools (Cabinet, RemindMail)" OFF \
"copyq" "Install CopyQ (clipboard manager)" OFF \
"hostname" "Change system hostname" OFF \
"downloads" "Open external app download links" OFF \
"clone" "Clone all GitHub repositories" OFF 3>&1 1>&2 2>&3)

# Check if anything was selected
if [ -z "$SELECTED" ]; then
    echo "No options selected. Exiting."
    exit 1
fi

# Convert selected tags to comma-separated list for Ansible
# Remove unnecessary quotes around tags
SELECTED_TAGS=$(echo "$SELECTED" | tr ' ' ',' | tr -d '"')

# Debug output
echo "Running Ansible with tags: $SELECTED_TAGS"

# Run Ansible playbook with selected tags
echo "Running command: ansible-playbook $SETUP_YML --tags=\"$SELECTED_TAGS\" --ask-become-pass --check"
ansible-playbook "$SETUP_YML" --tags="$SELECTED_TAGS" --ask-become-pass