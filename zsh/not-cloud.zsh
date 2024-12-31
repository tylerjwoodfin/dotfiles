# for all devices that aren't my server

## run on cloud or rainbow - see 'common'
cloud_commands=(
    "remind" "rmm" "rmmt" "rmmy" "rmmty" "rmml" "rmmsl" "shorten" \
    "diary" "turn" "notes" "docs" "work" "vn" "n" "v" "one-more-hour" \
    "plex" "bike" "addjira" "addshopping" "bluesky" "lifelog"
)

for cmd in "${cloud_commands[@]}"; do
    alias "$cmd"="cloud $cmd"
done

## desktop-specific
alias duplicate="./git/dotfiles/display/monitors-duplicate.sh"
alias duplicate4k="./git/dotfiles/display/monitors-duplicate4k.sh"
alias extend="./git/dotfiles/display/monitors-extend.sh"
alias steamdeck="./git/dotfiles/display/monitors-steamdeck.sh"
