#!/usr/bin/env python

"""
setup.py

This script sets up devices with proper repos and dotfile bash configurations.
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

def install_things():
    """
    Installs selected software from a set of options.
    """

    install_options = {
        "install Pihole": "curl -sSL https://install.pi-hole.net | bash",
        "install Cabinet": "pip install cabinet",
        "install RemindMail": "pip install remindmail",
        "apply Pre-push hooks": "bash ~/git/tools/githooks/apply_pre-push.sh",
        "link Syncthing's authorized_keys file to your SSH": 
            "ln ~/syncthing/docs/network/authorized_keys.md ~/.ssh/authorized_keys",
        "link dotfiles.vim to .vimrc": 'printf "\n\\" added by dotfiles/setup.py\nso \
~/git/dotfiles/dotfiles.vim\n" >> ~/.vimrc',
        "link global .gitignore to your Git configuration":
            "git config --global core.excludesfile ~/git/dotfiles/.gitignore"
    }

    for option, command in install_options.items():
        response = ask(f"Do you want to install {option}")

        if response == "y":
            subprocess.run(command, shell=True, check=True)
            print(f"{option} installation complete.")

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

def add_bashconfig(config, user_os):
    """
    Adds bash configs in ../bash to .bashrc.
    """

    config_path_prefix = "/Users/tyler" if user_os == "m" else "/home/tyler"
    while True:
        response = ask(f"Do you want to link the {config} config file to .bashrc")

        if response == 'y':
            config_path = f"{config_path_prefix}/git/dotfiles/bash/{config}"
            if config == 'network':
                config_path = f"{config_path_prefix}/syncthing/docs/network/alias"
                print(
                    "\nOK, this requires Tyler's bash config file in ~/syncthing/docs/network.")

            cmd_bashrc = f"""printf "\n# added by dotfiles/setup.py\n""" \
                f"""if [ -f {config_path} ]; then\n""" \
                f"""    source {config_path}\nfi\n" >> {config_path_prefix}/.bashrc """

            subprocess.run(cmd_bashrc, shell=True, check=True)
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
            subprocess.run("ssh-keygen -f /home/tyler/.ssh/id_rsa -N ''",
                            shell=True, check=True)
        else:
            print("Trying `pkg install openssh`...")
            print(
                "You may get a 500 error once or twice. Re-run the script if this happens.\n")
            time.sleep(5)
            subprocess.run("pkg install openssh -y", shell=True, check=True)

        print("\n")
        ssh_key_path = "~/.ssh/id_rsa.pub" if user_os == "m" else "/home/tyler/.ssh/id_rsa.pub"
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
    print("Before running, make sure you've installed Syncthing")

    if user_os == "m":
        # check environment
        shell_env = os.environ.get("SHELL")
        if shell_env:
            if "bash" in shell_env:
                print("Bash is the default shell.")
            elif "zsh" in shell_env:
                # sets shell to bash
                os.system("chsh -s /bin/bash")
                print("Bash is now the default shell. Please re-run this script.")
                exit()

        # check if homebrew is installed
        if not os.path.exists("/usr/local/bin/brew"):
            print("Installing Brew...")
            brew_install_cmd = (
                '/bin/bash -c "$(curl -fsSL '
                'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            )
            os.system(brew_install_cmd)
            exit()
    else:
        apply_hostname()

    create_ssh_key(user_os)
    install_things()

    # Add bash config files to bashrc or bash_profile depending on the OS:
    configs = ['common', 'not-cloud', 'network', 'phone', 'fff']
    for config in configs:
        add_bashconfig(config, user_os)

    print("\n\nComplete! See ~/syncthing/docs for next steps.")


if __name__ == "__main__":
    main()
