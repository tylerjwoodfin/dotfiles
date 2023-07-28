#!/usr/bin/env python

"""
setup.py

This script sets up devices with proper repos and dotfile bash configurations.
"""

import subprocess
import time

CMD_CLONE = """
UserName=tylerjwoodfin; \
curl -s https://api.github.com/users/$UserName/repos?per_page=1000 | \
jq -r '.[]|.ssh_url' | \
xargs -L1 git clone
"""


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
            config_path = f"~/git/dotfiles/bash/{config}"
            if config == 'network':
                config_path = "~/syncthing/docs/network/alias"
                print(
                    "\nOK, this requires Tyler's bash config file in syncthing/docs/network.")

            cmd_bashrc = f"""printf "\n# added by dotfiles/setup.py\n""" \
                f"""if [ -f {config_path} ]; then\n""" \
                f"""    source {config_path}\nfi\n" >> ~/.bashrc """

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
            subprocess.run("ssh-keygen -f ~/.ssh/id_rsa -N ''",
                           shell=True, check=True)
        else:
            print("Trying `pkg install openssh`...")
            print(
                "You may get a 500 error once or twice. Re-run the script if this happens.\n")
            time.sleep(5)
            subprocess.run("pkg install openssh -y", shell=True, check=True)

        print("\n")
        ssh_key = subprocess.check_output(
            "cat ~/.ssh/id_rsa.pub", shell=True, text=True)
        print(ssh_key)

        if is_phone == 'y':
            print("Trying to copy this to your clipboard... one sec")
            time.sleep(1)
            print(
                "pkg install termux-api -y; cat ~/.ssh/id_rsa.pub | termux-clipboard-set")
            time.sleep(1)
            print("It should be in your clipboard.")
            print("If not, run `cat ~/.ssh/id_rsa.pub` and copy it manually.")
        print("Paste this in your Github Profile -> Settings -> SSH Keys")

    print("At this point, you should have an SSH key from this device added to Github.")


def clone_repos():
    """
    Clones all public repos.
    """
    response = validate_yes_no_input(
        "Do you want to clone all public repos? (y/n)\n"
        "Do not press 'y' if the SSH key is not linked to your Github account)\n")

    if response == 'y':
        print("Cloning...")
        subprocess.run(
            f"mkdir -p ~/git; cd ~/git; {CMD_CLONE}", shell=True, check=True)
        print("Done")


def install_tools():
    """
    Install universal tools
    """

    brave_browser = """
sudo apt install curl
sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main"|sudo tee /etc/apt/sources.list.d/brave-browser-release.list
sudo apt update
sudo apt install brave-browser
"""

    # brave browser
    response = validate_yes_no_input(
        "Do you want to install Brave Browser? (y/n)\n")
    if response == 'y':
        subprocess.run("mkdir -p ~/git && cd ~/git", shell=True, check=True)
        subprocess.run(
            brave_browser, shell=True, check=True)

    # fff
    response = validate_yes_no_input("Do you want to install fff? (y/n)\n")
    if response == 'y':
        subprocess.run("mkdir -p ~/git && cd ~/git", shell=True, check=True)
        subprocess.run(
            "git clone https://github.com/dylanaraps/fff.git", shell=True, check=True)
        subprocess.run("cd fff && make install && rm -rf .",
                       shell=True, check=True)

    # syncthing
    response = validate_yes_no_input(
        "Do you want to install syncthing? (y/n)\n")
    if response == 'y':
        subprocess.run("sudo apt install apt-transport-https",
                       shell=True, check=True)
        signed_by = "signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg"
        command = (
            "curl -s https://syncthing.net/release-key.txt | "
            "gpg --dearmor | "
            "sudo tee /usr/share/keyrings/syncthing-archive-keyring.gpg >/dev/null |"
            f'echo "deb [{signed_by}] https://apt.syncthing.net/ syncthing stable" |'
            'sudo tee /etc/apt/sources.list.d/syncthing.list | '
            "sudo apt update && sudo apt install syncthing"
        )
        subprocess.run(command, shell=True, check=True)

        print("\nTo complete Syncthing setup:")
        print("visit: https://pimylifeup.com/raspberry-pi-syncthing/\n")

    # input-remapper
    response = validate_yes_no_input(
        "Do you want to install input-remapper? (y/n)\n")
    if response == 'y':
        commands = [
            "sudo apt install git python3-setuptools gettext",
            "git clone https://github.com/sezanzeb/input-remapper.git",
            "cd input-remapper && ./scripts/build.sh",
            "sudo apt install -f ./dist/input-remapper-2.0.0.deb"
        ]

    # signal
    response = validate_yes_no_input(
        "Do you want to install Signal? (y/n)\n")
    if response == 'y':
        commands = [
            "wget -O- https://updates.signal.org/desktop/apt/keys.asc | gpg --dearmor > signal-desktop-keyring.gpg",
            "cat signal-desktop-keyring.gpg | sudo tee /usr/share/keyrings/signal-desktop-keyring.gpg > /dev/null",
            "echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/signal-desktop-keyring.gpg] https://updates.signal.org/desktop/apt xenial main' |\\",
            "sudo tee /etc/apt/sources.list.d/signal-xenial.list",
            "sudo apt update && sudo apt install signal-desktop"
        ]

        for command in commands:
            subprocess.run(command, shell=True, check=True)

    # copyq
    response = validate_yes_no_input(
        "Do you want to install CopyQ (clipboard manager)? (y/n)"
    )

    if response == 'y':
        commands = [
            "sudo add-apt-repository ppa:hluk/copyq",
            "sudo apt update",
            "sudo apt install copyq"
        ]

    for command in commands:
        subprocess.run(command, shell=True, check=True)


def link_vimrc():
    """
    Links dotfiles.vim to .vimrc.
    """
    response = validate_yes_no_input(
        "Do you want to link dotfiles.vim to .vimrc? (y/n)\n")

    cmd_source_dotfile = "printf \"\n\\\" added by dotfiles/setup.py\nso \
~/git/dotfiles/dotfiles.vim\n\" >> ~/.vimrc"

    if response == 'y':
        subprocess.run(
            cmd_source_dotfile,
            shell=True, check=True)
        print("Done")


def install_pihole():
    """
    Installs Pihole.
    """
    response = validate_yes_no_input("Do you want to install Pihole? (y/n)\n")

    if response == 'y':
        subprocess.run(
            "curl -sSL https://install.pi-hole.net | bash", shell=True, check=True)
        print("Done")


def install_cabinet_remindmail():
    """
    Installs cabinet and remindmail from Pip
    """

    response = validate_yes_no_input("Do you want to install Cabinet? (y/n)\n")

    if response == 'y':
        subprocess.run("pip install cabinet", shell=True, check=True)

    response = validate_yes_no_input(
        "Do you want to install RemindMail? (y/n)\n")

    if response == 'y':
        subprocess.run("pip install remindmail", shell=True, check=True)


def apply_pre_push():
    """
    Runs apply_pre-push.sh
    """
    response = validate_yes_no_input(
        "Do you want to apply pre-push hooks to all repos? (y/n)\n")

    if response == 'y':
        subprocess.run(
            "bash ~/git/tools/githooks/apply_pre-push.sh", shell=True, check=True)
        print("Done")


def main():
    """
    Main entry point of the script.
    """
    print("Welcome! Let's get you set up.\n")

    install_tools()
    create_ssh_key()
    clone_repos()

    # Add bash config files to bashrc:
    for config in ['common', 'not-cloud', 'network', 'phone', 'fff']:
        add_bashconfig(config)

    link_vimrc()
    install_pihole()
    apply_pre_push()

    print("\n\nComplete! See ~/syncthing/ubuntu/setup.md for next steps.")


if __name__ == "__main__":
    main()
