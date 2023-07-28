#!/bin/bash
# a supplemental file to setup Linux devices

# check if the script is being run with root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo."
    exit
fi

# fix sudoers permissions
echo "tyler ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Function to validate yes/no input
function validate_yes_no_input() {
    while true; do
        read -p "$1" response
        case $response in
            [Yy]* ) echo "y"; break;;
            [Nn]* ) echo "n"; break;;
            * ) echo "Please answer 'yes' or 'no'.";;
        esac
    done
}

# Prompt for renaming the system
response=$(validate_yes_no_input "Do you want to rename your system? (y/n) ")

if [[ $response == "y" ]]; then
    read -p "Enter the new computer name: " new_hostname

    # Update hostname in /etc/hostname
    sudo hostnamectl set-hostname "$new_hostname"

    # Update hostname in /etc/hosts
    hosts_file="/etc/hosts"
    hosts_lines=()
    while IFS= read -r line; do
        if [[ $line == *127.0.1.1* ]]; then
            line_parts=($line)
            line_parts[1]=$new_hostname
            new_line="${line_parts[@]}""$'\n'"
            hosts_lines+=("$new_line")
        else
            hosts_lines+=("$line")
        fi
    done < "$hosts_file"

    printf "%s" "${hosts_lines[@]}" | sudo tee "$hosts_file" > /dev/null

    echo "Saved; please reboot afterwards."
fi