#!/bin/zsh
echo "Setting up Borg passphrase..."
read -s -p "Enter Borg passphrase: " BORG_PASSPHRASE
echo ""
echo "export BORG_PASSPHRASE='$BORG_PASSPHRASE'" >> ~/.zshrc
source ~/.zshrc
echo "Borg passphrase saved. Restart your shell for changes to take effect."