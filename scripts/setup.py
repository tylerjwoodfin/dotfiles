"""
setup.py

this is intended to set up any of my devices with proper repos and dotfile aliases
"""

from os import system as cmd
from time import sleep

CMD_CLONE = """
UserName=tylerjwoodfin; \
curl -s https://api.github.com/users/$UserName/repos?per_page=1000 |\
jq -r '.[]|.ssh_url' |\
xargs -L1 git clone
"""


def add_alias(alias):
    """
    adds the phone, desktop, or pi aliases to .bashrc
    """
    response = ""
    while response not in ['y', 'n']:
        response = input(
            f"Do you want to link the {alias} alias to bashrc? y/n\n")

        if response == 'y':
            alias_path = f"~/git/dotfiles/alias/{alias}"
            if alias == 'network':
                alias_path = f"~/syncthing/docs/network/alias"
                print("OK- this requires Tyler's alias file in syncthing/docs/network.")

            cmd_bashrc = f"""printf "\n# added by dotfiles/setup.py\n"""\
                f"""if [ -f {alias_path} ]; then\n"""\
                f"""    source {alias_path}\nfi\n" >> ~/.bashrc """

            cmd(cmd_bashrc)
            print("Done")


print("Welcome! Let's get you set up.\n")

# create SSH key
RESPONSE = ""
while RESPONSE not in ['y', 'n']:
    RESPONSE = input(
        "Do you need an SSH key? (this will overwrite any existing keys!) y/n\n")

if RESPONSE == 'y':
    # device type
    IS_PHONE = ""
    while IS_PHONE not in ['y', 'n']:
        IS_PHONE = input(
            "Is this a phone? This determines how your key is generated. y/n\n")

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
        print("Cloning...")
        cmd(f"mkdir -p ~/git; cd ~/git; {CMD_CLONE}")

# add alias to bashrc:
for i in ['common', 'desktop', 'pi', 'network']:
    add_alias(i)

# add .vimrc
RESPONSE = ""
while RESPONSE not in ['y', 'n']:
    RESPONSE = input("Do you want to link dotfiles.vim to .vimrc? y/n\n")

    if RESPONSE == 'y':
        cmd("printf \"\n\\\" added by dotfiles/setup.py\nso ~/git/dotfiles/dotfiles.vim\n\" >> ~/.vimrc")
        print("Done")
