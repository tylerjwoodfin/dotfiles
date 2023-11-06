#!/usr/bin/env python

"""
setup.py

This script sets up devices with proper repos and dotfile bash configurations.
"""

import subprocess
import os

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
        if response in ["y", "n"]:
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

        if response == "y":
            config_path = f"~/git/dotfiles/bash/{config}"
            if config == "network":
                config_path = "~/syncthing/docs/network/alias"
                print(
                    "\nOK, this requires Tyler's bash config file in syncthing/docs/network."
                )

            cmd_bashrc = (
                f"""printf "\n# added by dotfiles/setup.py\n"""
                f"""if [ -f {config_path} ]; then\n"""
                f"""    source {config_path}\nfi\n" >> ~/.bashrc """
            )

            subprocess.run(cmd_bashrc, shell=True, check=True)
            print("Done")
            break
        if response == "n":
            break


def create_ssh_key():
    """
    Creates an SSH key.
    """
    response = validate_yes_no_input(
        "Do you need an SSH key? (this will overwrite any existing keys!) (y/n)\n"
    )

    if response == "y":
        subprocess.run("brew install jq", shell=True, check=True)
        subprocess.run("ssh-keygen -f ~/.ssh/id_rsa -N ''", shell=True, check=True)

        print("\n")
        ssh_key = subprocess.check_output(
            "cat ~/.ssh/id_rsa.pub", shell=True, text=True
        )
        print(ssh_key)
        print("Paste this in your Github Profile -> Settings -> SSH Keys")

    print("At this point, you should have an SSH key from this device added to Github.")


def clone_repos():
    """
    Clones all public repos.
    """
    response = validate_yes_no_input(
        (
            "Do you want to clone all public repos? (y/n)\n",
            "Do not press 'y' if the SSH key is not linked to your Github account)\n",
        )
    )

    if response == "y":
        print("Cloning...")
        subprocess.run(f"mkdir -p ~/git; cd ~/git; {CMD_CLONE}", shell=True, check=True)
        print("Done")


def link_vimrc():
    """
    Links dotfiles.vim to .vimrc.
    """
    response = validate_yes_no_input(
        "Do you want to link dotfiles.vim to .vimrc? (y/n)\n"
    )

    cmd_source_dotfile = 'printf "\n\\" added by dotfiles/setup.py\nso \
~/git/dotfiles/dotfiles.vim\n" >> ~/.vimrc'

    if response == "y":
        subprocess.run(cmd_source_dotfile, shell=True, check=True)
        print("Done")


def install_pihole():
    """
    Installs Pihole.
    """
    response = validate_yes_no_input("Do you want to install Pihole? (y/n)\n")

    if response == "y":
        subprocess.run(
            "curl -sSL https://install.pi-hole.net | bash", shell=True, check=True
        )
        print("Done")


def install_cabinet_remindmail():
    """
    Installs cabinet and remindmail from Pip
    """

    response = validate_yes_no_input("Do you want to install Cabinet? (y/n)\n")

    if response == "y":
        subprocess.run("pip install cabinet", shell=True, check=True)

    response = validate_yes_no_input("Do you want to install RemindMail? (y/n)\n")

    if response == "y":
        subprocess.run("pip install remindmail", shell=True, check=True)


def apply_pre_push():
    """
    Runs apply_pre-push.sh
    """
    response = validate_yes_no_input(
        "Do you want to apply pre-push hooks to all repos? (y/n)\n"
    )

    if response == "y":
        subprocess.run(
            "bash ~/git/tools/githooks/apply_pre-push.sh", shell=True, check=True
        )
        print("Done")


def apply_hostname():
    """
    Changes the system name to the user input
    """

    response = validate_yes_no_input("Do you want to rename your system? (y/n)\n")

    if response == "y":
        new_hostname = input("Enter the new computer name:\n")

        # Update hostname for MacOS
        subprocess.run(f"scutil --set ComputerName {new_hostname}", shell=True, check=True)

        # Update hostname in /etc/hosts
        with open("/etc/hosts", "r", encoding="utf-8") as hosts_file:
            hosts_lines = hosts_file.readlines()
        
        print("Done")


def main():
    """
    Main entry point of the script.
    """
    print("Welcome! Let's get you set up.\n")

    # check environment
    shell_env = os.environ.get("SHELL")
    if shell_env:
        if "bash" in shell_env:
            print("Bash is the default shell.")
        elif "zsh" in shell_env:
            # runs chsh -s /bin/bash and restart script
            os.system("chsh -s /bin/bash")
            print("Bash is now the default shell. Please re-run this script.")
            exit()
    
    # check if homebrew is installed
    if not os.path.exists("/usr/local/bin/brew"):
        print("Installing Brew...")
        os.system(
            '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        )
        exit()

    create_ssh_key()
    clone_repos()

    # Add bash config files to bashrc:
    for config in ["common", "not-cloud", "network", "fff"]:
        add_bashconfig(config)

    link_vimrc()
    install_pihole()
    apply_pre_push()
    apply_hostname()

    print("\n\nComplete! Have a nice day.")


if __name__ == "__main__":
    main()
