set number
syntax on
set expandtab
set softtabstop=4
set tabstop=4
set shiftwidth=4
set ignorecase
set hls
set diffopt+=vertical

" remind.md syntax highlight
syntax match dateTokenMatch /\[\zs.\{-}\ze\]/ containedin=ALL contains=dateTokenCommandMatch,dateTokenDeleteMatch
hi dateTokenMatch ctermfg=10 guifg=green

syntax match dateTokenCommandMatch /\]\zs\([cC]\)\ze/ containedin=dateTokenMatch
hi dateTokenCommandMatch ctermfg=12 guifg=blue
autocmd BufWinEnter * call matchadd('dateTokenCommandMatch', ']\zs[cC]\ze', -1)

syntax match dateTokenDeleteMatch /\]\zs\([dD]\)\ze/ containedin=dateTokenMatch
hi dateTokenDeleteMatch ctermfg=11 guifg=yellow
autocmd BufWinEnter * call matchadd('dateTokenDeleteMatch', ']\zs[dD]\ze', -1)

autocmd BufWinEnter * call matchadd('dateTokenMatch', '\[\zs.\{-}\ze\]')

