# Disable press-and-hold for keys in favor of key repeat.
/usr/bin/defaults write -g ApplePressAndHoldEnabled -bool false

# Always use list view for Finder
/usr/bin/defaults write com.apple.Finder FXPreferredViewStyle Nlsv

# When performing a search, search the current folder by default
/usr/bin/defaults write com.apple.finder FXDefaultSearchScope -string 'SCcf'

# Disable the warning when changing a file extension
/usr/bin/defaults write com.apple.finder FXEnableExtensionChangeWarning -bool false

# Disable .DS_Store files
/usr/bin/defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true

# Automatically expand "Save As..." dialogue boxes
/usr/bin/defaults write -g NSNavPanelExpandedStateForSaveMode -bool true
/usr/bin/defaults write -g NSNavPanelExpandedStateForSaveMode2 -bool true

# Show all filename extensions (e.g. example.txt)
/usr/bin/defaults write -g AppleShowAllExtensions -bool true

# Disable the “Are you sure you want to open this application?” dialog
/usr/bin/defaults write com.apple.LaunchServices LSQuarantine -bool false

# Disable bouncing icons
defaults write com.apple.dock no-bouncing -bool TRUE

# Show hidden files in Finder
/usr/bin/defaults write com.apple.finder AppleShowAllFiles -bool true

# Show the ~/Library folder
/usr/bin/chflags nohidden ~/Library
/usr/bin/killall Finder