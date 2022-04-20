from os import system as cmd
from time import sleep

# Setup.py
#
# this is intended for setting up any of my devices
# (phones, laptops, desktops, Pis... anything with a terminal!)


def add_alias(str):
    response = ""
    while response not in ['y', 'n']:
        response = input(
            f"Do you want to link the {str} alias to bashrc? y/n\n")

        if response == 'y':
            cmd(
                f"""printf "\n# added by dotfiles/setup.py\nif [ -f ~/git/dotfiles/alias/{str} ]; then\n    source ~/git/dotfiles/alias/{str}\nfi\n" >> ~/.bashrc """)
            print("Done")


print("Welcome! Let's get you set up.\n")

# device type
is_phone = ""
while is_phone not in ['y', 'n']:
    is_phone = input(f"Is this a phone? y/n\n")

# create SSH key
response = ""
while response not in ['y', 'n']:
    response = input(
        f"Do you need an SSH key? (this will overwrite any existing keys!) y/n\n")

if response == 'y':
    if is_phone == 'n':
        cmd("ssh-keygen -f ~/.ssh/id_rsa -N ''")
    else:
        print("Trying `pkg install openssh`...")
        print("You may get a 500 error once or twice. Re-run the script if this happens.\n")
        sleep(5)
        cmd(f"pkg install openssh -y")

    print("\n\nIf this was successful, you should see a key above.")
    print("Copy `id_rsa.pub` and go to your Github Profile -> Settings -> SSH Keys")

print("At this point, you should have an SSH key from this device added to Github.")

# clone repos
response = ""
while response not in ['y', 'n']:
    response = input(
        f"Do you want to clone all public repositories? y/n\n")

    if response == 'y':
        command = """
        CNTX=users; NAME=tylerjwoodfin; PAGE=1
        curl "https://api.github.com/$CNTX/$NAME/repos?page=$PAGE&per_page=100" |
        grep -e 'clone_url*' |
        cut -d \" -f 4 |
        xargs -L1 git clone
        """

        cmd(f"mkdir ~/git; cd ~/git; {command}")

# clone backend
response = ""
while response not in ['y', 'n']:
    response = input(
        f"Do you want to clone the backend repo? y/n\n")

    if response == 'y':
        cmd("mkdir ~/git; cd ~/git; git clone https://github.com/tylerjwoodfin/backend.git")

# add alias to bashrc:
for i in ['common', 'desktop', 'pi']:
    add_alias(i)

# add .vimrc
response = ""
while response not in ['y', 'n']:
    response = input(
        f"Do you want to link dotfiles.vim to .vimrc? y/n\n")

    if response == 'y':
        cmd("printf \"\n\\\" added by dotfiles/setup.py\nso ~/git/dotfiles/dotfiles.vim\n\" >> ~/.vimrc")
        print("Done")
