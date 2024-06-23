#!/usr/bin/env python

"""
setup.py

This script sets up devices with proper repos and dotfile zsh configurations.
"""

import subprocess
import time
import os

CMD_CLONE = """
UserName=tylerjwoodfin; \
curl -s https://api.github.com/users/$UserName/repos?per_page=1000 | \
jq -r '.[]|.ssh_url' | \
xargs -L1 git clone
"""

if os.geteuid() != 0:
    print("\n\n\nWARNING: this script should be run with 'sudo' (not applicable on MacOS).")

def get_user_os():
    """
    Asks the user for their operating system.
    """
    os_type = input("Are you running this on (M)acOS, (L)inux, or a (P)hone? ").lower().strip()
    return os_type

def install_things(user_os):
    """
    Installs selected software from a set of options.
    """

    install_options = {
        "(Linux) install syncthing": [
            "sudo apt install apt-transport-https",
            """
            curl -s https://syncthing.net/release-key.txt | gpg --dearmor |
            sudo tee /usr/share/keyrings/syncthing-archive-keyring.gpg >/dev/null;
            echo "deb [signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg] 
            https://apt.syncthing.net/ syncthing stable" | 
            sudo tee /etc/apt/sources.list.d/syncthing.list;
            sudo apt update;
            sudo apt install syncthing
            """
        ],
        "(MacOS) install syncthing": [
            "brew install syncthing"
        ],
        "(MacOS) install neovim": [
            "brew install neovim"
        ],
        "(Linux) install neovim": [
          "sudo apt install neovim"  
        ],
        "clone all repos (Exit if the SSH key is not linked to your Github account)": [
            f"mkdir -p ~/git && cd ~/git && {CMD_CLONE}"
        ],
        "(MacOS) run mac.sh to set defaults (must have ~/git/dotfiles/mac.sh)": [
            "zsh ~/git/dotfiles/mac.sh"
        ],
        "set Borg passphrase": [
            r'read -s -p "Enter Borg passphrase: " BORG_PASSPHRASE && echo \
                "export BORG_PASSPHRASE=\'$BORG_PASSPHRASE\'" >> ~/.zshrc && source ~/.zshrc'
        ],
        "set Git email defaults": [
            "git config --global user.email \"14207553+tylerjwoodfin@users.noreply.github.com\"",
            "git config --global user.name \"Tyler Woodfin\""
        ],
        "install fff": [
            "mkdir -p ~/git && cd ~/git",
            "rm -rf fff && git clone https://github.com/dylanaraps/fff.git",
            "cd fff && make install && cd ../ && rm -rf fff",
        ],
        "install Pihole": [
            "curl -sSL https://install.pi-hole.net | bash"
        ],
        "install Cabinet": [
            "pip install cabinet"
        ],
        "install RemindMail": [
            "pip install remindmail"
        ],
        "apply Pre-push hooks": [
            "zsh ~/git/tools/githooks/apply_pre-push.sh"
        ],
        "link Syncthing's authorized_keys file to this device's": [
            "ln ~/syncthing/md/docs/network/authorized_keys.md ~/.ssh/authorized_keys"
        ],
        "link dotfiles.vim to .vimrc and ~/.config/nvim/init.vim": [
            'printf "\n\\" added by dotfiles\nso ~/git/dotfiles/dotfiles.vim\n" >> ~/.vimrc',
           "mkdir -p ~/.config/nvim && cp ~/.vimrc ~/.config/nvim/init.vim" 
        ],
        "link global .gitignore to your Git configuration": [
            "git config --global core.excludesfile ~/git/dotfiles/.gitignore"
        ],
        "(Linux) install CopyQ (clipboard manager)": [
            "sudo add-apt-repository ppa:hluk/copyq",
            "sudo apt update",
            "sudo apt install copyq"
        ],
        "(Linux) install Net Tools (for ifconfig)": [
            "sudo apt install net-tools"
        ],
        "(Linux) install Chrome Gnome Shell (for Gnome Extensions": [
            "sudo apt-get install chrome-gnome-shell"
        ],
        "(Linux) install input-remapper": [
            "sudo apt install git python3-setuptools gettext",
            "git -C 'input-remapper' pull || \
            git clone https://github.com/sezanzeb/input-remapper.git",
            "cd input-remapper && ./scripts/build.sh",
            "cd input-remapper/dist && sudo apt install '?name(input-remapper.*)'"
        ],
        "(Linux) fix the path issue on .zshrc": [
            "printf \"\n\\\" added by dotfiles/setup.py\n\
                export PATH=\r$PATH:/home/tyler/.local/bin\n\" >> /home/tyler/.zshrc"
        ],
    }

    for option, commands in install_options.items():
        if user_os != "l" and option.startswith("(Linux)"):
            continue
        if user_os != "m" and option.startswith("(MacOS)"):
            continue
        response = ask(f"Do you want to {option}?")

        if response == "y":
            for command in commands:
                subprocess.run(command, shell=True, check=True)
            print("✅ Done\n")

    # open links to download the rest
    cmd_open = "open"
    if user_os == "l":
        cmd_open = "xdg-open"

    apps = [
        "https://spotify.com/download",
        "https://obsidian.md/download",
        "https://code.visualstudio.com/download",
        "https://www.realvnc.com/en/connect/download/vnc/",
        "https://arc.net/"
    ]

    print("Opening links to download the rest...\n")
    for app in apps:
        subprocess.run(f"{cmd_open} {app}", shell=True, check=True)

def apply_hostname():
    """
    Changes the system name to the user input
    """
    response = ask("Do you want to rename your system")
    err_permission = "Permission denied when trying to update /etc/hosts. Run the script with sudo."

    if response == "y":
        new_hostname = input("Enter the new computer name:\n").strip()

        if os.name == 'posix':
            current_os = os.uname().sysname.lower()
            if 'darwin' in current_os:
                # MacOS
                subprocess.run(f"sudo scutil --set ComputerName '{new_hostname}'",
                               shell=True, check=True)
                subprocess.run(f"sudo scutil --set HostName '{new_hostname}'",
                               shell=True, check=True)
                subprocess.run(f"sudo scutil --set LocalHostName '{new_hostname}'",
                               shell=True, check=True)
                print(f"System name changed to {new_hostname} on MacOS.")
            else:
                # Assuming Linux or other UNIX-like OS
                try:
                    with open("/etc/hostname", "w", encoding="utf-8") as hostname_file:
                        hostname_file.write(new_hostname + "\n")
                    subprocess.run(f"sudo hostnamectl set-hostname {new_hostname}",
                                   shell=True, check=True)
                    print(f"System name changed to {new_hostname}.")
                except PermissionError:
                    print("Permission denied. Try running the script with sudo.")

            # Update hostname in /etc/hosts, common for Unix-like systems including MacOS
            try:
                with open("/etc/hosts", "r", encoding="utf-8") as hosts_file:
                    hosts_lines = hosts_file.readlines()

                with open("/etc/hosts", "w", encoding="utf-8") as hosts_file:
                    for line in hosts_lines:
                        if "localhost" in line:
                            hosts_file.write(line)
                        else:
                            hosts_file.write(line.replace(os.uname().nodename, new_hostname))
                print("Hostname in /etc/hosts updated.")
            except PermissionError:
                print(err_permission)

def ask(prompt):
    """
    Validates user input for yes/no questions.
    """
    while True:
        response = input(f"{prompt}? (y/n)\n").lower()
        if response in ['y', 'n']:
            return response
        print("Invalid input. Please enter 'y' or 'n'.")

def add_zshconfig(config, user_os):
    """
    Adds zsh configs in ../zsh to .zshrc.
    """

    config_path_prefix = "/Users/tyler" if user_os == "m" else "/home/tyler"
    while True:
        response = ask(f"Do you want to link the {config} config file to .zshrc")

        if response == 'y':
            config_path = f"{config_path_prefix}/git/dotfiles/zsh/{config}"
            if config == 'network':
                config_path = f"{config_path_prefix}/syncthing/md/docs/network/alias"
                print(
                    "\nOK, this requires Tyler's zsh config file in ~/syncthing/md/docs/network.")

            cmd_zshrc = f"""printf "\n# added by dotfiles/setup.py\n""" \
                f"""if [ -f {config_path} ]; then\n""" \
                f"""    source {config_path}\nfi\n" >> {config_path_prefix}/.zshrc """

            subprocess.run(cmd_zshrc, shell=True, check=True)
            print("Done")
            break
        if response == 'n':
            break


def create_ssh_key(user_os):
    """
    Creates an SSH key.
    """
    response = ask(
        "Do you need an SSH key? (this will overwrite any existing keys!)")

    if response == 'y':
        subprocess.run('ssh-keygen -f ~/.ssh/id_rsa -N ""', shell=True, check=True)

        cmd_install = "sudo apt"
        if user_os == "m":
            cmd_install = "brew"

        is_phone = ask(
            "Is this an Android phone? This determines how your key is generated. (y/n)\n")

        if is_phone == 'n':
            subprocess.run(f'{cmd_install} install git', shell=True, check=True)
            subprocess.run(f'{cmd_install} install jq', shell=True, check=True)
            subprocess.run("ssh-keygen -f ~/.ssh/id_rsa -N ''",
                            shell=True, check=True)
        else:
            print("Trying `pkg install openssh`...")
            print(
                "You may get a 500 error once or twice. Re-run the script if this happens.\n")
            time.sleep(5)
            subprocess.run("pkg install openssh -y", shell=True, check=True)

        print("\n")
        ssh_key_path = "~/.ssh/id_rsa.pub"
        ssh_key = subprocess.check_output(f"cat {ssh_key_path}", shell=True, text=True)
        print(ssh_key)

        if user_os != "m" and is_phone == 'y':
            print("Trying to copy this to your clipboard... one sec")
            time.sleep(1)
            print(
                "pkg install termux-api -y; cat /home/tyler/.ssh/id_rsa.pub | termux-clipboard-set")
            time.sleep(1)
            print("It should be in your clipboard.")
            print("If not, run `cat /home/tyler/.ssh/id_rsa.pub` and copy it manually.")
        print("Paste this in your Github Profile -> Settings -> SSH Keys")

    print("\nAt this point, you should have an SSH key from this device added to Github.")

def main():
    """
    Main entry point of the script.
    """
    user_os = ""
    while user_os not in ['l', 'm', 'p']:
        user_os = get_user_os().lower()

    print("Welcome! Let's get you set up.\n")

    # check environment
    shell_env = os.environ.get("SHELL")

    if user_os == "p":
        packages = ["zsh", "vim", "curl", "neovim", "openssh"]
        for package in packages:
            os.system(f"apk add {package}")

        sudoers_entry = "tyler ALL=(ALL) NOPASSWD: ALL"
        check_command = f"grep -q '{sudoers_entry}' /etc/sudoers"
        add_command = f"echo '{sudoers_entry}' | sudo EDITOR='tee -a' visudo"

        os.system(f"{check_command} || {add_command}")
    if shell_env:
        if "zsh" in shell_env:
            print("zsh is the default shell.")
        elif "zsh" in shell_env:
            # sets shell to zsh
            os.system("chsh -s /bin/zsh")
            print("zsh is now the default shell. Please re-run this script.")
            exit()

    if user_os == "m":
        # check if homebrew is installed
        if not os.path.exists("/usr/local/bin/brew"):
            print("Installing Brew...")
            brew_install_cmd = (
                '/bin/zsh -c "$(curl -fsSL '
                'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            )
            os.system(brew_install_cmd)
            exit()
    else:
        apply_hostname()

    create_ssh_key(user_os)
    install_things(user_os)

    # Add zsh config files to zshrc or zsh_profile depending on the OS:
    configs = ['common', 'not-cloud', 'network', 'phone', 'fff']
    for config in configs:
        add_zshconfig(config, user_os)

    print("\n\nComplete! See ~/syncthing/md/docs for next steps.")


if __name__ == "__main__":
    main()
