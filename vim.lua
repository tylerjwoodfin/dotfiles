-- enable line numbers
vim.opt.number = true

-- enable syntax highlighting
vim.cmd('syntax on')

-- use spaces instead of tabs
vim.opt.expandtab = true

-- set the number of spaces inserted for each indentation
vim.opt.softtabstop = 4

-- set the number of spaces that a <Tab> counts for
vim.opt.tabstop = 4

-- set the number of spaces used for autoindent
vim.opt.shiftwidth = 4

-- ignore case in search patterns
vim.opt.ignorecase = true

-- highlight search matches
vim.opt.hlsearch = true

-- use vertical split for diffs
vim.opt.diffopt:append('vertical')

-- wrap lines at convenient points
vim.opt.linebreak = true

-- syntax highlighting for RemindMail
vim.cmd([[
syntax match dateTokenMatch /\[\zs.\{-}\ze\]/ containedin=ALL contains=dateTokenCommandMatch,dateTokenDeleteMatch
highlight dateTokenMatch ctermfg=10 guifg=green
]])

vim.cmd([[
syntax match dateTokenCommandMatch /\]\zs\([cC]\)\ze/ containedin=dateTokenMatch
highlight dateTokenCommandMatch ctermfg=12 guifg=blue
]])

vim.api.nvim_create_autocmd('BufWinEnter', {
    pattern = '*',
    command = "call matchadd('dateTokenCommandMatch', ']\\zs[cC]\\ze', -1)"
})

vim.cmd([[
syntax match dateTokenDeleteMatch /\]\zs\([dD]\)\ze/ containedin=dateTokenMatch
highlight dateTokenDeleteMatch ctermfg=11 guifg=yellow
]])

vim.api.nvim_create_autocmd('BufWinEnter', {
    pattern = '*',
    command = "call matchadd('dateTokenDeleteMatch', ']\\zs[dD]\\ze', -1)"
})

vim.api.nvim_create_autocmd('BufWinEnter', {
    pattern = '*',
    command = "call matchadd('dateTokenMatch', '\\[\\zs.\\{-}\\ze\\]')"
})

vim.api.nvim_create_autocmd("Syntax", {
    pattern = "*",
    callback = function()
        -- Syntax highlighting for comments
        vim.cmd([[
            syntax match commentMatch /#.*$/
            highlight commentMatch ctermfg=8 guifg=gray
        ]])
    end,
})