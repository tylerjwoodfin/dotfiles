#!/usr/bin/env python

"""
setup.py

This script sets up devices with proper repos and dotfile bash configurations.
"""

import subprocess
import platform
import time
import os

CMD_CLONE = """
UserName=tylerjwoodfin; \
curl -s https://api.github.com/users/$UserName/repos?per_page=1000 | \
jq -r '.[]|.ssh_url' | \
xargs -L1 git clone
"""

if os.geteuid() != 0:
    print("\n\n\nWARNING: this script should be run with 'sudo'.")

def validate_yes_no_input(prompt):
    """
    Validates user input for yes/no questions.
    """
    while True:
        response = input(prompt).lower()
        if response in ['y', 'n']:
            return response
        print("Invalid input. Please enter 'y' or 'n'.")


def add_bashconfig(config):
    """
    Adds bash configs in ../bash to .bashrc.
    """
    while True:
        response = validate_yes_no_input(
            f"Do you want to link the {config} config file to bashrc? (y/n)\n"
        )

        if response == 'y':
            config_path = f"/home/tyler/git/dotfiles/bash/{config}"
            if config == 'network':
                config_path = "/home/tyler/syncthing/docs/network/alias"
                print(
                    "\nOK, this requires Tyler's bash config file in syncthing/docs/network.")

            cmd_bashrc = f"""printf "\n# added by dotfiles/setup.py\n""" \
                f"""if [ -f {config_path} ]; then\n""" \
                f"""    source {config_path}\nfi\n" >> /home/tyler/.bashrc """

            subprocess.run(cmd_bashrc, shell=True, check=True)
            print("Done")
            break
        if response == 'n':
            break


def create_ssh_key():
    """
    Creates an SSH key.
    """
    response = validate_yes_no_input(
        "Do you need an SSH key? (this will overwrite any existing keys!) (y/n)\n")

    if response == 'y':
        is_phone = validate_yes_no_input(
            "Is this an Android phone? This determines how your key is generated. (y/n)\n")

        if is_phone == 'n':
            subprocess.run('sudo apt install git', shell=True, check=True)
            subprocess.run('sudo apt install jq', shell=True, check=True)
            subprocess.run("ssh-keygen -f /home/tyler/.ssh/id_rsa -N ''",
                           shell=True, check=True)
        else:
            print("Trying `pkg install openssh`...")
            print(
                "You may get a 500 error once or twice. Re-run the script if this happens.\n")
            time.sleep(5)
            subprocess.run("pkg install openssh -y", shell=True, check=True)

        print("\n")
        ssh_key = subprocess.check_output(
            "cat /home/tyler/.ssh/id_rsa.pub", shell=True, text=True)
        print(ssh_key)

        if is_phone == 'y':
            print("Trying to copy this to your clipboard... one sec")
            time.sleep(1)
            print(
                "pkg install termux-api -y; cat /home/tyler/.ssh/id_rsa.pub | termux-clipboard-set")
            time.sleep(1)
            print("It should be in your clipboard.")
            print("If not, run `cat /home/tyler/.ssh/id_rsa.pub` and copy it manually.")
        print("Paste this in your Github Profile -> Settings -> SSH Keys")

    print("\nAt this point, you should have an SSH key from this device added to Github.")


def install_tools():
    """
    Install universal tools
    """

    # Check if user is on Ubuntu.
    if platform.system() != 'Linux':
        print("Skipping tool installation (requires Linux)...")
        return

    installers = {
        "install Pip": [
            "sudo apt install python3-pip"
        ],
        "install npm": [
            "sudo apt-get install npm"
        ],
        "install Make": [
            "sudo apt install -y make"
        ],
        "clone all repos (Do not press 'y' if the SSH key is not linked to your Github account)": [
            f"mkdir -p /home/tyler/git; cd /home/tyler/git; {CMD_CLONE}"
        ],
        "set Git email defaults": [
            "git config --global user.email \"14207553+tylerjwoodfin@users.noreply.github.com\"",
            "git config --global user.name \"Tyler Woodfin\""
        ],
        "install Brave Browser": [
            """
            sudo apt install curl
            sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
            echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main"|sudo tee /etc/apt/sources.list.d/brave-browser-release.list
            sudo apt update
            sudo apt install brave-browser
            """
        ],
        "install fff": [
            "mkdir -p /home/tyler/git && cd /home/tyler/git",
            "rm -rf fff && git clone https://github.com/dylanaraps/fff.git",
            "cd fff && make install && cd ../ && rm -rf fff",
        ],
        "install syncthing": [
            "sudo apt install apt-transport-https",
            """
            curl -s https://syncthing.net/release-key.txt | gpg --dearmor | sudo tee /usr/share/keyrings/syncthing-archive-keyring.gpg >/dev/null;
            echo "deb [signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" | sudo tee /etc/apt/sources.list.d/syncthing.list;
            sudo apt update;
            sudo apt install syncthing
            """
        ],
        "install input-remapper": [
            "sudo apt install git python3-setuptools gettext",
            "git -C 'input-remapper' pull || git clone https://github.com/sezanzeb/input-remapper.git",
            "cd input-remapper && ./scripts/build.sh",
            "cd input-remapper/dist && sudo apt install '?name(input-remapper.*)'"
        ],
        "install Signal": [
            """
            wget -O- https://updates.signal.org/desktop/apt/keys.asc | gpg --dearmor > signal-desktop-keyring.gpg;
            cat signal-desktop-keyring.gpg | sudo tee /usr/share/keyrings/signal-desktop-keyring.gpg > /dev/null;
            echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/signal-desktop-keyring.gpg] https://updates.signal.org/desktop/apt xenial main' | sudo tee /etc/apt/sources.list.d/signal-xenial.list;
            sudo apt update;
            sudo apt install signal-desktop
            """
        ],
        "install CopyQ (clipboard manager)": [
            "sudo add-apt-repository ppa:hluk/copyq",
            "sudo apt update",
            "sudo apt install copyq"
        ],
        "install Net Tools (for ifconfig)": [
            "sudo apt install net-tools"
        ],
        "install Chrome Gnome Shell (for Gnome Extensions": [
            "sudo apt-get install chrome-gnome-shell"
        ],
        "install openssh-server (required for enabling SSH)": [
            "sudo apt install openssh-server"
        ],
        "install Pihole": [
            "curl -sSL https://install.pi-hole.net | bash"
        ],
        "fix the path issue on .bashrc": [
            "printf \"\n\\\" added by dotfiles/setup.py\nexport PATH=\$PATH:/home/tyler/.local/bin\n\" >> /home/tyler/.bashrc"
        ],
        "install Cabinet": [
            "pip install pymongo && pip install cabinet"
        ],
        "install RemindMail": [
            "curl https://raw.githubusercontent.com/tylerjwoodfin/remindmail/main/requirements.md | pip install -r /dev/stdin && pip install remindmail"
        ],
        "setup Dashboard": [
            "sudo npm install -g forever",
            "rm -rf /var/www/html/dashboard",
            "ln -s /home/tyler/git/dashboard /var/www/html/dashboard",
            "npm install"
        ],
        "link dotfiles.vim to .vimrc": [
            "printf \"\n\\\" added by dotfiles/setup.py\nso /home/tyler/git/dotfiles/dotfiles.vim\n\" >> /home/tyler/.vimrc"
        ],
        "apply pre-push hooks to all repos (requires repos to exist first)": [
            "bash /home/tyler/git/tools/githooks/apply_pre-push.sh"
        ],
        "link Syncthing's authorized keys to this device's": [
            "ln /home/tyler/syncthing/network/ssh/authorized_keys /home/tyler/.ssh/authorized_keys"
        ]

    }

    for tool, commands in installers.items():
        response = validate_yes_no_input(f"Do you want to {tool}? (y/n)\n")
        if response == 'y':
            for command in commands:
                subprocess.run(command, shell=True, check=True)
                print("Done\n")

def main():
    """
    Main entry point of the script.
    """
    print("Welcome! Let's get you set up.\n")

    create_ssh_key()
    install_tools()

    # Add bash config files to bashrc:
    for config in ['common', 'not-cloud', 'network', 'phone', 'fff']:
        add_bashconfig(config)    

    print("\n\nComplete! See /home/tyler/syncthing/docs/ubuntu/setup.md for next steps.")


if __name__ == "__main__":
    main()
