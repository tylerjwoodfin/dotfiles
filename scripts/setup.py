"""
setup.py

this is intended to set up any of my devices with proper repos and dotfile aliases
"""

from os import system as cmd
from time import sleep


def add_alias(alias):
    """
    adds the phone, desktop, or pi aliases to .bashrc
    """
    response = ""
    while response not in ['y', 'n']:
        response = input(
            f"Do you want to link the {alias} alias to bashrc? y/n\n")

        if response == 'y':
            cmd_bashrc = f"""printf "\n# added by dotfiles/setup.py\n"""\
                f"""if [ -f ~/git/dotfiles/alias/{alias} ]; then\n"""\
                f"""    source ~/git/dotfiles/alias/{alias}\nfi\n" >> ~/.bashrc """

            cmd(cmd_bashrc)
            print("Done")


print("Welcome! Let's get you set up.\n")

# device type
IS_PHONE = ""
while IS_PHONE not in ['y', 'n']:
    IS_PHONE = input("Is this a phone? y/n\n")

# create SSH key
RESPONSE = ""
while RESPONSE not in ['y', 'n']:
    RESPONSE = input(
        "Do you need an SSH key? (this will overwrite any existing keys!) y/n\n")

if RESPONSE == 'y':
    if IS_PHONE == 'n':
        cmd("ssh-keygen -f ~/.ssh/id_rsa -N ''")
    else:
        print("Trying `pkg install openssh`...")
        print("You may get a 500 error once or twice. Re-run the script if this happens.\n")
        sleep(5)
        cmd("pkg install openssh -y")

    print("\n\nIf this was successful, you should see a key above.")
    print("Copy `~/.ssh/id_rsa.pub` and go to your Github Profile -> Settings -> SSH Keys")

    if IS_PHONE == 'y':
        print("Trying to copy this to your clipboard... one sec")
        sleep(1)
        print("pkg install termux-api -y; cat ~/.ssh/id_rsa.pub | termux-clipboard-set")
        sleep(1)
        print("It should be in your clipboard.")
        print("If not, run `cat ~/.ssh/id_rsa.pub` and copy it manually.")
        print("Paste it in your Github Profile -> Settings -> SSH Keys")

print("At this point, you should have an SSH key from this device added to Github.")

# clone repos
RESPONSE = ""
while RESPONSE not in ['y', 'n']:
    RESPONSE = input("Do you want to clone all public repos? y/n\n")

    if RESPONSE == 'y':
        CLONE_CMD = """
        CNTX=users; NAME=tylerjwoodfin; PAGE=1
        curl "https://api.github.com/$CNTX/$NAME/repos?page=$PAGE&per_page=100" |
        grep -e 'ssh_url*' |
        cut -d \" -f 4 |
        xargs -L1 git clone
        """

        cmd("mkdir -p ~/git; cd ~/git")
        print(f"Paste the following after the script has finished:\n\n{CLONE_CMD}")

# add alias to bashrc:
for i in ['common', 'desktop', 'pi']:
    add_alias(i)

# add .vimrc
RESPONSE = ""
while RESPONSE not in ['y', 'n']:
    RESPONSE = input("Do you want to link dotfiles.vim to .vimrc? y/n\n")

    if RESPONSE == 'y':
        cmd("printf \"\n\\\" added by dotfiles/setup.py\nso ~/git/dotfiles/dotfiles.vim\n\" >> ~/.vimrc")
        print("Done")
